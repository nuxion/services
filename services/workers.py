import asyncio
import inspect
import json
import logging
import traceback
from abc import ABC, abstractclassmethod, abstractmethod
from datetime import datetime
from enum import Enum
from functools import partial
from multiprocessing import Manager, Queue
from os import getpid
from queue import Empty
from typing import Any, Callable, Dict, List, Optional, Union

from pydantic import BaseModel, Field
from sanic import Sanic
from sanic.log import LOGGING_CONFIG_DEFAULTS, logger

from services.types import TasksBackend
from services.utils import get_class, get_function, secure_random_str

CTX_PREFIX = "queue_"
WORKER_PREFIX = "Queue-"


class QueueConfig(BaseModel):
    app_name: str
    qname: str = "default"
    backend: Optional[TasksBackend] = None


class TaskStatus(str, Enum):
    created = "CREATED"
    waiting = "WAITING"
    running = "RUNNING"
    cancelled = "CANCELLED"
    failed = "FAILED"
    done = "DONE"


class Task(BaseModel):
    name: str
    params: Dict[str, Any] = Field(default_factory=dict)
    id: str = Field(default_factory=secure_random_str)
    state: str = TaskStatus.created
    app_name: str = "test"
    timeout: int = 10
    result_ttl: int = 120
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True


class _Task(BaseModel):
    task: Task
    future: asyncio.Task

    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True


class IState(ABC):
    @abstractmethod
    async def add_task(self, task: Task):
        raise NotImplementedError()

    @abstractmethod
    async def get_task(self, taskid: str) -> Task:
        raise NotImplementedError()

    @abstractmethod
    async def update_status(self, taskid: str, status: str) -> bool:
        raise NotImplementedError()

    @abstractmethod
    async def list_tasks(self) -> List[Task]:
        raise NotImplementedError()

    @abstractmethod
    async def delete_task(self, taskid: str) -> bool:
        raise NotImplementedError()

    @abstractmethod
    async def get_result(self, taskid: str) -> Dict[str, Any]:
        raise NotImplementedError()

    @abstractmethod
    async def set_result(self, taskid: str, *, result: Dict[str, Any], status: str):
        raise NotImplementedError()

    @abstractclassmethod
    async def from_uri(cls, uri: str, extra: Dict[str, Any] = {}) -> "IState":
        raise NotImplementedError()

    @abstractmethod
    async def clean(self):
        raise NotImplementedError()

    @abstractmethod
    async def clean_failed(self) -> List[str]:
        raise NotImplementedError()


def elapsed_time_from_finish(task: Task):
    n = datetime.utcnow()
    return (n - task.updated_at).total_seconds()


def elapsed_time_from_start(task: Task):
    n = datetime.utcnow()
    return (n - task.created_at).total_seconds()


def _get_kwargs(task: Task, fn: Callable) -> Dict[str, BaseModel]:
    annot = list(fn.__annotations__.keys())
    kwargs = {}
    if annot:
        params_key = annot[0]
        params = fn.__annotations__[params_key](**task.params)
        kwargs = {params_key: params}
    return kwargs


def _get_function(base_package, task: Task) -> Callable:
    _name = task.name
    if "." not in _name:
        fn = get_function(f"{base_package}.tasks.{_name}")
    else:
        fn = get_function(_name)
    return fn


def _exec_task(base_package, task: Task):
    _name = task.name
    logger.info("Starting task %s", _name)
    fn = _get_function(base_package, task)
    kwargs = _get_kwargs(task, fn)
    result = fn(**kwargs)
    logger.info("Finished task %s", _name)
    return result


async def init_backend(conf: TasksBackend) -> IState:
    Cls: IState = get_class(conf.backend_class)
    backend = await Cls.from_uri(conf.uri)
    return backend


class TaskQueue:
    def __init__(
        self, queue: Queue, *, backend: Optional[IState] = None, conf: QueueConfig
    ) -> None:
        self.queue = queue
        self.qname = conf.qname
        self._app_name = conf.app_name
        self.backend = backend

    def send(self, task: Task) -> None:
        self.queue.put_nowait(task.json())

    def receive(self, wait=True) -> Dict[str, Any]:
        if wait:
            rsp = self.queue.get()
            data = json.loads(rsp)
        else:
            try:
                rsp = self.queue.get_nowait()
                data = json.loads(rsp)
            except Empty:
                return {}
        return data

    async def submit(
        self,
        *,
        name: str,
        params: Dict[str, Any],
        timeout: int = 60,
        result_ttl: int = 900,
        debug=False,
    ) -> Task:
        task = Task(
            name=name,
            params=params,
            app_name=self._app_name,
            timeout=timeout,
            result_ttl=result_ttl,
        )
        if self.backend:
            await self.backend.add_task(task)
        if debug:
            _exec_task(self._app_name, task)
        else:
            self.send(task)

        return task

    @classmethod
    def setup(cls, app: Sanic, conf: QueueConfig):
        @app.after_server_start
        async def _setup_taskqueue(app: Sanic):
            back = None
            if conf.backend:
                back = await init_backend(conf.backend)
            q = getattr(app.shared_ctx, f"{CTX_PREFIX}{conf.qname}")
            tq = cls(q, conf=conf, backend=back)
            setattr(app.ctx, f"{CTX_PREFIX}{conf.qname}", tq)

    @staticmethod
    def get_from_request(request, qname: str) -> "TaskQueue":
        q = getattr(request.app.ctx, f"{CTX_PREFIX}{qname}")
        return q


class Scheduler:
    STOP = "__STOP__"
    backend: Optional[IState] = None

    def __init__(
        self,
        queue: TaskQueue,
        loop,
        base_package,
        timeout=60,
        max_jobs=5,
        backend: Optional[TasksBackend] = None,
    ):
        self.queue = queue
        self._loop = loop
        self._base_package = base_package
        self.timeout = timeout
        # self.sem = asyncio.BoundedSemaphore(max_jobs)
        self.sem = None
        self._max_jobs = max_jobs
        self.tasks: Dict[str, _Task] = {}
        self._backend = backend
        self.backend: Optional[IState] = None

    async def add_task(self, task: Task):
        if self._backend:
            logger.info("Adding task %s [%s]", task.name, task.id)
            await self.backend.add_task(task)

    async def _update_status(self, task: Task, status: str):
        task.updated_at = datetime.utcnow()
        task.state = status
        if self.backend:
            await self.backend.update_status(task.id, status=status)

    async def _set_result(self, task: Task, *, result, status: str):
        task.updated_at = datetime.utcnow()
        task.state = status
        if self.backend:
            logger.info("BACKEND SET RESULT")
            await self.backend.set_result(task.id, result=result, status=status)

    async def _delete_task(self, task: Task):
        if self.backend and task.state == TaskStatus.done.value:
            await self.backend.delete_task(task.id)

    async def exec_task(self, task: Task):
        # ctx = get_context("fork")
        # with concurrent.futures.ProcessPoolExecutor(mp_context=ctx) as pool:
        logger.info("Executing task %s [%s]", task.name, task.id)
        result = None
        fn = _get_function(self._base_package, task)
        kwargs = _get_kwargs(task, fn)
        status = TaskStatus.running.value
        result = None
        try:
            await self._update_status(task, status)
            if inspect.iscoroutinefunction(fn):
                result = await fn(**kwargs)
            else:
                result = await self._loop.run_in_executor(None, partial(fn, **kwargs))
            status = TaskStatus.done.value
        except asyncio.exceptions.TimeoutError as e:
            err = traceback.format_exc()
            logger.error("Task timeout error %s [%s]: %s", task.name, task.id, e)
            result = {"error": err}
            status = TaskStatus.failed.value
        except Exception as e:
            err = traceback.format_exc()
            logger.error("Task error %s [%s]: %s", task.name, task.id, e)
            result = {"error": err}
        finally:
            logger.info("SETTING RESULT")
            await self._set_result(task, result=result, status=status)

        return result

    def start_task(self, task: Task) -> asyncio.Task:
        _task = self._loop.create_task(self.exec_task(task))
        self.tasks[task.id] = _Task(task=task, future=_task)
        return _task

    async def _sentinel(self):
        logger.debug("> Cleaning")
        to_delete = []
        for k, task in self.tasks.items():
            if task.future.done():
                to_delete.append(k)
        for x in to_delete:
            del self.tasks[x]
        if self.backend:
            await self.backend.clean()

    async def init_backend(self):
        if self._backend:
            Cls: IState = get_class(self._backend.backend_class)
            self.backend = await Cls.from_uri(self._backend.uri)

    async def run(self):
        logger.info("> Starting scheduler")
        await self.init_backend()
        print("BACKEND CONF: ", self._backend)
        print("BACKEND OBJ: ", self.backend)
        sem = asyncio.Semaphore(self._max_jobs)
        while True:
            async with sem:
                task_dict = self.queue.receive(wait=False)
                if not task_dict:
                    await self._sentinel()
                    await asyncio.sleep(0.8)
                else:
                    task = Task(**task_dict)
                    await sem.acquire()
                    _task = self.start_task(task)
                    logger.info("task %s [%s] added", task.name, task.id)
                    _task.add_done_callback(lambda _: sem.release())

    def finish_pending_tasks(self):
        if self.tasks:
            tasks = [t.future for t in self.tasks.values()]
            drain = asyncio.wait_for(asyncio.gather(*tasks), timeout=60)
            self._loop.run_until_complete(drain)


def cpu_worker(name, queue: Queue, conf: QueueConfig, max_jobs=1) -> None:
    """based on https://amhopkins.com/background-job-worker"""
    logging.config.dictConfig(LOGGING_CONFIG_DEFAULTS)
    pid = getpid()
    logger.debug("max_jobs=%s unused variable", max_jobs)
    logger.info(">> CPU Bound worker reporting for duty: %s [%s]", name, pid)
    tq = TaskQueue(queue, conf=conf)

    try:
        while True:
            task_dict = tq.receive()
            task = Task(**task_dict)
            _exec_task(conf.app_name, task)

    except KeyboardInterrupt:
        logger.info("Shutting down %s", pid)
    finally:
        logger.info("Stopping CPU bound worker [%s]. Goodbye", pid)


def io_worker(name: str, queue: Queue, conf: QueueConfig, max_jobs=5) -> None:
    """based on https://amhopkins.com/background-job-worker"""
    logging.config.dictConfig(LOGGING_CONFIG_DEFAULTS)
    pid = getpid()
    logger.info(">> IO Bound worker reporting for duty: %s [%s]", name, pid)
    tq = TaskQueue(queue, conf=conf)
    loop = asyncio.new_event_loop()
    scheduler = Scheduler(
        tq,
        loop,
        base_package=conf.app_name,
        max_jobs=max_jobs,
        backend=conf.backend,
    )

    try:
        loop.create_task(scheduler.run())
        loop.run_forever()
        # loop.run_until_complete(scheduler.run())
    except KeyboardInterrupt:
        logger.info("Shutting down %s", pid)
    finally:
        scheduler.finish_pending_tasks()
    logger.info("Stopping IO bound worker [%s]. Goodbye", pid)


def standalone_cpu_worker(conf: QueueConfig, task: Task):
    logging.config.dictConfig(LOGGING_CONFIG_DEFAULTS)
    pid = getpid()
    logger.info(">> CPU Bound worker reporting for duty: %s", pid)
    loop = asyncio.new_event_loop()
    result = None
    status = task.state
    if conf.backend:
        backend = loop.run_until_complete(init_backend(conf.backend))
        loop.run_until_complete(backend.add_task(task))
    try:
        result = _exec_task(conf.app_name, task)
        status = TaskStatus.done.value

    except KeyboardInterrupt:
        result = {"error": "cancelled task"}
        status = TaskStatus.failed.value
        logger.error("Task [%s] cancelled", task.id)
        logger.info("Shutting down %s", pid)
    except Exception as e:
        result = {"error": str(e)}
        status = TaskStatus.failed.value
        logger.error("Task [%s] failed, msg: %s", task.id, e)
    finally:
        if conf.backend:
            loop.run_until_complete(
                backend.set_result(task.id, result=result, status=status)
            )

        logger.info("Stopping CPU bound worker [%s]. Goodbye", pid)


def standalone_io_worker(conf: QueueConfig, task: Task):
    logging.config.dictConfig(LOGGING_CONFIG_DEFAULTS)
    pid = getpid()
    logger.info(">> IO Bound worker reporting for duty: %s", pid)
    loop = asyncio.new_event_loop()
    tq = TaskQueue(Queue(), conf=conf)
    scheduler = Scheduler(tq, loop, base_package=conf.app_name, backend=conf.backend)
    if conf.backend:
        loop.run_until_complete(scheduler.init_backend())
        loop.run_until_complete(scheduler.add_task(task))
    try:
        # loop.create_task(scheduler.exec_task(task))
        loop.run_until_complete(scheduler.exec_task(task))
    except KeyboardInterrupt:
        logger.info("Shutting down %s", pid)
    finally:
        scheduler.finish_pending_tasks()
    logger.info("Stopping IO bound worker [%s]. Goodbye", pid)


def _get_queue_from_app(app, qname) -> Union[Queue, None]:
    try:
        q = getattr(app.shared_ctx, f"{CTX_PREFIX}{qname}")
    except AttributeError:
        return None
    return q


def create(
    app: Sanic,
    conf: QueueConfig,
    max_jobs: int = 1,
    jobs_per_worker: int = 5,
    wk: Callable = io_worker,
) -> None:
    @app.main_process_start
    async def start(app: Sanic):
        manager = Manager()
        if not _get_queue_from_app(app, conf.qname):
            q = manager.Queue()
            setattr(app.shared_ctx, f"{CTX_PREFIX}{conf.qname}", q)
        # app.shared_ctx.queue = manager.Queue()

    @app.main_process_ready
    async def ready(app: Sanic):
        q = _get_queue_from_app(app, qname=conf.qname)
        for ix in range(0, max_jobs):
            _name = f"{WORKER_PREFIX}{conf.qname}-{ix}"
            app.manager.manage(
                _name,
                wk,
                {
                    "name": _name,
                    "queue": q,
                    "conf": conf,
                    "max_jobs": jobs_per_worker,
                },
            )


def get_queue(request, qname="default") -> TaskQueue:
    q = getattr(request.app.ctx, f"{CTX_PREFIX}{qname}")
    return q
