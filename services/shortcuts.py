from sanic.request import Request

from services.templates import Render
from services import defaults
from services.conf import load_conf
from services.db import AsyncSQL, SQL


async def async_render(request: Request, tpl_name, data) -> str:
    render: Render = request.app.ctx.render
    tpl = await render.async_render(request, tpl_name, data=data)
    return tpl
    # return html(tpl, status=200)


def get_async_db(
    dbname="default", settings_module=defaults.SETTINGS_MODULE
) -> AsyncSQL:
    settings = load_conf(settings_module)
    _db = AsyncSQL.from_conf(settings.DATABASES[dbname])
    return _db


def get_db(dbname="default", settings_module=defaults.SETTINGS_MODULE) -> SQL:
    settings = load_conf(settings_module)
    _db = SQL.from_conf(settings.DATABASES[dbname])
    return _db
