import logging
from multiprocessing import Manager, Queue
from os import environ, getpid

from sanic import Sanic
from sanic.log import LOGGING_CONFIG_DEFAULTS, logger


def get_queue(request, qname="queue") -> Queue:
    q = getattr(request.app.shared_ctx, qname)
    return q


class WorkerBase:
    def __init__(self, qname="queue", proc_name=None):
        self.qname = qname
        self.q = None
        self.proc_name = proc_name

    def _init_queue(self, app: Sanic):
        q = None
        try:
            q = getattr(app.shared_ctx, self.qname)
            print("QUEUE already exist")
        except AttributeError:
            pass
        if not q:
            print("Setting QUEUE")
            manager = Manager()
            self.q = manager.Queue()
            setattr(app.shared_ctx, self.qname, self.q)
        else:
            self.q = q

    def _init_pm(self, app: Sanic, _):
        app.manager.manage(self.proc_name, self.run, {})

    def init_app(self, app: Sanic) -> Sanic:
        app.register_listener(self._init_queue, "main_process_start")
        app.register_listener(self._init_pm, "main_process_ready")
        app.ctx.worker = self
        return app

    def send(self, msg):
        self.q.put_nowait(msg)

    def get_queue(self, request) -> Queue:
        q = getattr(request.app.shared_ctx, self.qname)
        return q

    def _process(self, msg):
        raise NotImplementedError()

    def run(self):
        print("Stating proc")
        try:
            while True:
                msg = self.q.get()
                print(f"Msg received: {msg}")
                self._process(msg)
        except KeyboardInterrupt:
            print("Process interrupted")


class Dummy(WorkerBase):
    def _process(self, msg):
        print(f"got {msg}")


class Client:
    def __init__(self, queue: Queue) -> None:
        self.queue = queue

    def send(self, msg) -> None:
        self.queue.put_nowait(msg)


def worker(queue: Queue) -> None:
    logging.config.dictConfig(LOGGING_CONFIG_DEFAULTS)
    pid = getpid()
    logger.info("SAJE reporting for duty: %s", pid)
    try:
        while True:
            msg = queue.get()
            print(f"MSG {msg}")
    except KeyboardInterrupt:
        logger.info("Shutting down %s", pid)


def create(app: Sanic) -> None:
    @app.main_process_start
    async def start(app: Sanic):
        manager = Manager()
        app.shared_ctx.queue = manager.Queue()

    @app.main_process_ready
    async def ready(app: Sanic):
        app.manager.manage(
            "Worker",
            worker,
            {"queue": app.shared_ctx.queue},
        )

    @app.after_server_start
    async def setup_client(app: Sanic):
        # app.ctx.saje = SajeClient(app.shared_ctx.queue)
        app.ctx.worker = Client(app.shared_ctx.queue)
        app.ext.dependency(Client(app.shared_ctx.queue))
