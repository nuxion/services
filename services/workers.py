import asyncio
import json
import logging
from importlib import import_module
from multiprocessing import Manager, Queue
from os import getpid
from typing import Callable, Dict, Optional, Any

from pydantic import BaseModel, Field
from sanic import Sanic
from sanic.log import LOGGING_CONFIG_DEFAULTS, logger
from enum import Enum
from services.utils import get_function, secure_random_str

CTX_PREFIX = "queue_"
WORKER_PREFIX = "Queue-"


class WorkerType(str, Enum):
    cpu: "cpu-bound"
    io: "io-bound"


class Task(BaseModel):
    name: str
    id: str = Field(default_factory=secure_random_str)
    payload: BaseModel


class TaskQueue:
    def __init__(self, qname: str, queue: Queue) -> None:
        self.queue = queue
        self.qname = qname

    def send(self, task: Task) -> None:
        self.queue.put_nowait(task.json())

    def receive(self) -> Dict[str, Any]:
        rsp = self.queue.get()
        data = json.loads(rsp)
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

    def __init__(self, queue, loop):
        self.queue = queue
        self._loop = loop

    async def run(self):
        logger.info("> Starting scheduler")


def _get_kwargs(task: Dict[str, Any], fn: Callable) -> Dict[str, BaseModel]:
    payload_key = list(fn.__annotations__.keys())[0]
    payload = fn.__annotations__[payload_key](**task["payload"])
    kwargs = {payload_key: payload}
    return kwargs


def _get_function(base_package, task: Dict[str, Any]) -> Callable:
    _name = task["name"]
    if "." not in _name:
        fn = get_function(f"{base_package}.tasks.{_name}")
    else:
        fn = get_function(_name)
    return fn


def _get_queue(request, qname="default") -> TaskQueue:
    q = getattr(request.app.ctx, f"{CTX_PREFIX}{qname}")
    return q


def _exec_task(base_package, task: Dict[str, Any]):
    _name = task["name"]
    logger.info("Starting task %s", _name)
    fn = _get_function(base_package, task)
    kwargs = _get_kwargs(task, fn)
    fn(**kwargs)
    logger.info("Finished task %s", _name)


def _worker(base_package, qname, queue: Queue) -> None:
    """based on https://amhopkins.com/background-job-worker"""
    logging.config.dictConfig(LOGGING_CONFIG_DEFAULTS)
    pid = getpid()
    logger.info(">> Worker reporting for duty: %s", pid)
    tq = TaskQueue(qname=qname, queue=queue)

    try:
        while True:
            task_dict = tq.receive()
            _exec_task(base_package, task_dict)

    except KeyboardInterrupt:
        logger.info("Shutting down %s", pid)


def create(app: Sanic, app_name, qname="default", fn: Callable = _worker) -> None:
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


def submit_task(
    request,
    *,
    name: str,
    payload: BaseModel,
    qname: str = "default",
    debug=False,
    base_package=None,
) -> Task:
    t = Task(name=name, payload=payload)
    if debug:
        _exec_task(base_package, t.dict())
    else:
        q = _get_queue(request, qname)
        q.send(t)
    return t
