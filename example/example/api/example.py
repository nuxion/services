from sanic import Blueprint, Request
from sanic.response import json

example_bp = Blueprint("example", url_prefix="example", version="v1")


@example_bp.get("/")
async def json_handler(request: Request):
    return json(dict(msg="hello wolrd! from app example"), 200)