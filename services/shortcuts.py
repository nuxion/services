from sanic.request import Request

from services import conf, defaults, types
from services.db import SQL, AsyncSQL
from services.templates import Render
from services.accept import parse_locale


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


def locale_best_match(headers, default_locale="en-US") -> str:
    loc = headers.get("accept-language")
    best = default_locale.replace("-", "_")
    if not loc:
        loc = default_locale
    parsed = parse_locale(loc)
    if parsed[0][0] != "*":
        best = parsed[0][0]

    return best
