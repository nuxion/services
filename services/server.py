from importlib import import_module
from typing import Callable

from sanic import Request, Sanic
from sanic.response import json

from services import defaults
from services.base import WebAppSpec
from services.db.plugin import init_db
from services.redis_conn import create_pool
from services.types import Settings
from services.utils import get_class, get_version

version = get_version("__version__.py")


async def status_handler(request):
    return json(dict(msg="We are ok", version=version))


# def init_db(app: Sanic, settings: Settings):
#    from services.db.web import sanic_init_db
#    sanic_init_db(app, settings)


# async def after_request(request: Request):
#     current_app = request.app
#     request.ctx.session = current_app.ctx.db.scoped_session()
#
#
# async def before_request(request: Request):
#     request.ctx.session.close()


def create_srv(
    settings: Settings,
    app_name=defaults.SANIC_APP,
    create_redis=create_pool,
    with_status_handler=True,
    auth_enabled=True,
    init_db_func: Callable = init_db,
) -> Sanic:
    """Factory pattern like flask"""

    app = Sanic(app_name)

    app.config.CORS_ORIGINS = settings.CORS_ORIGINS
    app.config.OAS_UI_DEFAULT = "swagger"
    app.config.OAS_UI_REDOC = False
    app.config.SWAGGER_UI_CONFIGURATION = {
        "apisSorter": "alpha",
        "operationsSorter": "alpha",
        "docExpansion": "none",
    }
    app.config.SETTINGS = settings
    if settings.REDIS:
        app.ctx.redis = create_redis(settings.REDIS)
    if settings.DATABASES:
        init_db(app, settings=settings)

    if auth_enabled:
        app.ext.openapi.add_security_scheme(
            "token",
            "http",
            scheme="bearer",
            bearer_format="JWT",
        )
        app.ext.openapi.secured("token")
        secure_app: WebAppSpec = get_class("services.security.web.WebApp")()
        secure_app.init(app, settings)

    app.ctx.databases = {}
    if settings.DATABASES:
        init_db_func(app, settings)

    for wapp in settings.APPS:
        w: WebAppSpec = get_class(wapp)()
        w.init(app, settings)

    if with_status_handler:
        app.add_route(status_handler, "/status")

    return app


def init_app(web_app_name: str, *, app: Sanic, settings: Settings):
    w: WebAppSpec = get_class(web_app_name)()
    w.init(app, settings)
    if w.bp_modules:
        w.init_blueprints(app)
    if w.middlewares:
        w.init_middlewares(app)
