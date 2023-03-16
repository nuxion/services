import asyncio
import inspect
import json
import logging
from abc import ABC, abstractmethod
from functools import partial, wraps
from multiprocessing import Manager, Queue
from os import getpid
from queue import Empty
from typing import Any, Callable, Dict

from pydantic import BaseModel, Field
from sanic import Sanic
from sanic.log import LOGGING_CONFIG_DEFAULTS, logger

from services.utils import get_function, secure_random_str

CTX_PREFIX = "queue_"
WORKER_PREFIX = "Queue-"


# class WorkerType(str, Enum):
#     cpu: "cpu-bound"
#     io: "io-bound"


# def task(name: str, timeout=60, raise_on_error=True):
#     def decorator(f):
#         @wraps(f)
#         def decorated_function(*args, **kwargs):
#             return result
#
#         return decorated_function
#
#     return decorator


class Task(BaseModel):
    name: str
    params: Dict[str, Any] = Field(default_factory=dict)
    id: str = Field(default_factory=secure_random_str)
    timeout: int = 10


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
    fn(**kwargs)
    logger.info("Finished task %s", _name)


class IState(ABC):
    @abstractmethod
    async def add_task(self, task: Task):
        raise NotImplementedError()

    @abstractmethod
    async def get_task(self, taskid: str) -> Task:
        raise NotImplementedError()

    @abstractmethod
    async def delete_task(self, taskid: str) -> bool:
        raise NotImplementedError()

    @abstractmethod
    async def get_result(self, taskid: str) -> Any:
        raise NotImplementedError()

    @abstractmethod
    async def set_result(self, taskid: str, result: Any) -> Any:
        raise NotImplementedError()


class MemoryState(IState):
    def __init__(self):
        self.tasks = {}
        self.results = {}

    async def add_task(self, task: Task):
        self.tasks[task.id] = task

    async def get_task(self, taskid: str) -> Task:
        t = self.tasks.get(taskid)
        if not t:
            raise KeyError(f"task {taskid} doesn't exist")
        return t

    async def delete_task(self, taskid: str) -> bool:
        del self.tasks[taskid]
        return True

    async def get_result(self, taskid: str) -> Any:
        return self.results[taskid]

    async def set_result(self, taskid: str, result: Any):
        self.results[taskid] = result


class TaskQueue:
    def __init__(self, qname: str, queue: Queue) -> None:
        self.queue = queue
        self.qname = qname

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

    @classmethod
    def setup(cls, app: Sanic, qname="default"):
        @app.after_server_start
        async def _setup_taskqueue(app: Sanic):
            q = getattr(app.shared_ctx, f"{CTX_PREFIX}{qname}")
            tq = cls(qname, q)
            setattr(app.ctx, f"{CTX_PREFIX}{qname}", tq)


class Scheduler:
    STOP = "__STOP__"

    def __init__(self, queue: TaskQueue, loop, base_package, timeout=60, max_jobs=3):
        self.queue = queue
        self._loop = loop
        self._base_package = base_package
        self.timeout = timeout
        # self.sem = asyncio.BoundedSemaphore(max_jobs)
        self.sem = None
        self._max_jobs = max_jobs
        self.tasks: Dict[str, asyncio.Task] = {}
        self.results: Dict[str, Any] = {}

    async def _exec_task(self, task: Task):
        # ctx = get_context("fork")
        # with concurrent.futures.ProcessPoolExecutor(mp_context=ctx) as pool:
        logger.info("Executing task %s [%s]", task.name, task.id)
        result = None
        fn = _get_function(self._base_package, task)
        kwargs = _get_kwargs(task, fn)
        if inspect.iscoroutinefunction(fn):
            coro = self._loop.run_in_executor(None, partial(fn, **kwargs))
        else:
            coro = fn(**kwargs)
        try:
            await coro()
        except asyncio.exceptions.TimeoutError:
            logger.error("Task error %s [%s]", task.name, task.id)

        return result

    def start_task(self, task: Task) -> asyncio.Task:
        _task = self._loop.create_task(self._exec_task(task))
        self.tasks[task.id] = _task
        return _task

    def _sentinel(self):
        logger.debug("> Cleaning")
        to_delete = []
        for k, task in self.tasks.items():
            if task.done():
                # r = task.result()
                # self.results[k] = r
                to_delete.append(k)
        for x in to_delete:
            del self.tasks[x]

    async def run(self):
        logger.info("> Starting scheduler")
        sem = asyncio.Semaphore(self._max_jobs)
        while True:
            async with sem:
                task_dict = self.queue.receive(wait=False)
                if not task_dict:
                    self._sentinel()
                    await asyncio.sleep(1)
                else:
                    task = Task(**task_dict)
                    await sem.acquire()
                    _task = self.start_task(task)
                    logger.info("task %s [%s] added", task.name, task.id)
                    _task.add_done_callback(lambda _: sem.release())


def _worker(base_package, qname, queue: Queue) -> None:
    """based on https://amhopkins.com/background-job-worker"""
    logging.config.dictConfig(LOGGING_CONFIG_DEFAULTS)
    pid = getpid()
    logger.info(">> CPU Bound worker reporting for duty: %s", pid)
    tq = TaskQueue(qname=qname, queue=queue)

    try:
        while True:
            task_dict = tq.receive()
            task = Task(**task_dict)
            _exec_task(base_package, task)

    except KeyboardInterrupt:
        logger.info("Shutting down %s", pid)


def _async_worker(base_package, qname, queue: Queue) -> None:
    """based on https://amhopkins.com/background-job-worker"""
    logging.config.dictConfig(LOGGING_CONFIG_DEFAULTS)
    pid = getpid()
    logger.info(">> IO Bound worker reporting for duty: %s", pid)
    tq = TaskQueue(qname=qname, queue=queue)
    loop = asyncio.new_event_loop()
    scheduler = Scheduler(tq, loop, base_package=base_package)

    try:
        loop.create_task(scheduler.run())
        loop.run_forever()
        # loop.run_until_complete(scheduler.run())
        logger.info("FINISH UNTIL")

    except KeyboardInterrupt:
        logger.info("Shutting down %s", pid)
    finally:
        if scheduler.tasks:
            drain = asyncio.wait_for(
                asyncio.gather(*list(scheduler.tasks.values())), timeout=60
            )
            loop.run_until_complete(drain)
    logger.info("Stopping IO bound worker [%s]. Goodbye", pid)


def create(app: Sanic, app_name, qname="default", fn: Callable = _async_worker) -> None:
    @app.main_process_start
    async def start(app: Sanic):
        manager = Manager()
        q = manager.Queue()
        setattr(app.shared_ctx, f"{CTX_PREFIX}{qname}", q)
        # app.shared_ctx.queue = manager.Queue()

    @app.main_process_ready
    async def ready(app: Sanic):
        app.manager.manage(
            f"{WORKER_PREFIX}{qname}",
            fn,
            {
                "base_package": app_name,
                "qname": qname,
                "queue": getattr(app.shared_ctx, f"{CTX_PREFIX}{qname}"),
            },
        )


def _get_queue(request, qname="default") -> TaskQueue:
    q = getattr(request.app.ctx, f"{CTX_PREFIX}{qname}")
    return q


def submit_task(
    request,
    *,
    name: str,
    payload: BaseModel,
    qname: str = "default",
    debug=False,
    base_package=None,
) -> Task:
    t = Task(name=name, params=payload.dict())
    if debug:
        _exec_task(base_package, t)
    else:
        q = _get_queue(request, qname)
        q.send(t)
    return t
