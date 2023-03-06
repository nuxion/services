from sanic.request import Request

from services.templates import Render


async def async_render(request: Request, tpl_name, data) -> str:
    render: Render = request.app.ctx.render
    tpl = await render.async_render(request, tpl_name, data=data)
    return tpl
    # return html(tpl, status=200)
