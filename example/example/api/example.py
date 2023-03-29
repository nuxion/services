from sanic import Blueprint, Request
from sanic.response import json
from services.workers import get_queue
from services.utils import stream_reader
from example.models import TaskExample
from services.storage import Storage
example_bp = Blueprint("example", url_prefix="example", version="v1")


@example_bp.get("/")
async def json_handler(request: Request):
    return json(dict(msg="hello wolrd! from app example"), 200)


@example_bp.post("/worker")
async def worker_handler(request: Request):
    t = TaskExample(do="web", wait=5)
    q = get_queue(request, qname="default")
    task = await q.submit(name="dummy", params=t.dict())
    return json(task.dict(exclude={'created_at', 'updated_at'}), 201)
@example_bp.post("/_/upload/<filename:str>", stream=True)
async def upload_example(request, filename, store: Storage):
    _store = store.get_storage(name="default")
    await _store.put_stream(filename, stream_reader(request))
    return json(dict(msg="ok"), 200)
