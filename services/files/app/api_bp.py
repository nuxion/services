from sanic import Blueprint, Request
from sanic.response import json

{{ data.app_name }}_bp = Blueprint("{{ data.app_name }}", url_prefix="{{ data.app_name }}", version="v1")


@{{ data.app_name }}_bp.get("/")
async def json_handler(request: Request):
    return json(dict(msg="hello wolrd! from app {{ data.app_name }}"), 200)
