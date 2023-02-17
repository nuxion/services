from sanic import HTTPResponse, Sanic
from sanic.request import Request
from sanic.response import html

from services.templates import Render
from services.utils import MimeTypes


async def async_render(request: Request, tpl_name, data) -> str:
    render: Render = request.app.ctx.render
    tpl = await render.async_render(request, tpl_name, data=data)
    return tpl
    # return html(tpl, status=200)
