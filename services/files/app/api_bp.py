from sanic import Blueprint, Request
from sanic.response import json
from services.workers import submit_task
from {{ data.app_name }}.models import Person

{{ data.app_name }}_bp = Blueprint("{{ data.app_name }}", url_prefix="{{ data.app_name }}", version="v1")


@{{ data.app_name }}_bp.get("/")
async def json_handler(request: Request):
    return json(dict(msg="hello wolrd! from app {{ data.app_name }}"), 200)


@{{ data.app_name }}_bp.post("/worker")
async def worker_handler(request: Request):
    p = Person(name="Pepe", lastname="Perez")
    task = submit_task(request, name="dummy", payload=p, qname="default")
    return json(task.dict()), 201)
