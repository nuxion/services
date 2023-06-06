from sanic.request import Request

from services import conf, defaults, types
from services.db import SQL, AsyncSQL
from services.templates import Render


async def async_render(request: Request, tpl_name, data) -> str:
    """ """
    render: Render = request.app.ctx.render
    tpl = await render.async_render(request, tpl_name, data=data)
    return tpl
    # return html(tpl, status=200)


def get_async_db(
    dbname="default", settings_module=defaults.SETTINGS_MODULE
) -> AsyncSQL:
    settings = conf.load_conf(settings_module)
    _db = AsyncSQL.from_conf(settings.DATABASES[dbname])
    return _db


def get_db(dbname="default", settings_module=defaults.SETTINGS_MODULE) -> SQL:
    settings = conf.load_conf(settings_module)
    _db = SQL.from_conf(settings.DATABASES[dbname])
    return _db


def load_conf(settings_module=defaults.SETTINGS_MODULE) -> types.Settings:
    _c = conf.load_conf(settings_module)
    return _c
