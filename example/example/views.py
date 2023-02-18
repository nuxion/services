from sanic import Blueprint, Request
from sanic.response import html
from sanic_ext import openapi
from services.shortcuts import async_render
from services.types import HtmlData

web_bp = Blueprint("web")


def new_data(content):
    return HtmlData(ctx={"DEV": True}, title="example", content=content)


@web_bp.get("/")
@openapi.exclude()
async def default_handler(request: Request):
    data = new_data(dict(msg="hello"))
    text = await async_render(request, "index.html", data)
    return html(text)