from sanic import Blueprint, Request
from sanic.response import json
{% if data.tasks -%}
from services.workers import submit_task
from {{ data.app_name }}.models import TaskExample
{% endif -%}

{{ data.app_name }}_bp = Blueprint("{{ data.app_name }}", url_prefix="{{ data.app_name }}", version="v1")


@{{ data.app_name }}_bp.get("/")
async def json_handler(request: Request):
    return json(dict(msg="hello wolrd! from app {{ data.app_name }}"), 200)


{% if data.tasks -%}
@{{ data.app_name }}_bp.post("/worker")
async def worker_handler(request: Request):
    t = TaskExample(do="web", wait=5)
    task = submit_task(request, name="dummy", payload=t, qname="default")
    return json(task.dict(), 201)
{% endif -%}
