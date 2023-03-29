from sanic import Blueprint, Request
from sanic.response import json
{% if data.tasks -%}
from services.workers import get_queue
from services.utils import stream_reader
from {{ data.app_name }}.models import TaskExample
{% endif -%}
{% if data.storage -%}
from services.storage import Storage
{% endif -%}

{{ data.app_name }}_bp = Blueprint("{{ data.app_name }}", url_prefix="{{ data.app_name }}", version="v1")


@{{ data.app_name }}_bp.get("/")
async def json_handler(request: Request):
    return json(dict(msg="hello wolrd! from app {{ data.app_name }}"), 200)


{% if data.tasks -%}
@{{ data.app_name }}_bp.post("/worker")
async def worker_handler(request: Request):
    t = TaskExample(do="web", wait=5)
    q = get_queue(request, qname="default")
    task = await q.submit(name="dummy", params=t.dict())
    return json(task.dict(exclude={'created_at', 'updated_at'}), 201)
{% endif -%}

{% if data.storage -%}
@{{ data.app_name }}_bp.post("/_/upload/<filename:str>", stream=True)
async def upload_example(request, filename, store: Storage):
    _store = store.get_storage(name="default")
    await _store.put_stream(filename, stream_reader(request))
    return json(dict(msg="ok"), 200)
{% endif -%}
