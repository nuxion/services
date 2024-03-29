from importlib import import_module
from typing import Callable

from sanic import Request, Sanic
from sanic.response import json

from services import defaults, storage
from services.base import WebAppSpec
from services.db.web import init_db
from services.redis_conn import create_pool
from services.templates import Render
from services.types import Settings
from services.utils import get_class, get_version

version = get_version()


async def stream_reader(request: Request):
    """
    It's a wrapper to be used to yield response from a stream
    to another stream.
    it's used with project upload data to stream upload zip directly to
    the fileserver instead of load data in memory.
    """
    while True:
        body = await request.stream.read()
        if body is None:
            break
        yield body


async def status_handler(request):
    return json(dict(msg="We are ok", version=version))


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
    app.config.SERVER_NAME = settings.BASE_URL
    if settings.REDIS:
        app.ctx.redis = create_redis(settings.REDIS)
    if settings.DATABASES:
        init_db_func(app, settings=settings)

    if auth_enabled:
        app.ext.openapi.add_security_scheme(
            "token",
            "http",
            scheme="bearer",
            bearer_format="JWT",
        )
        app.ext.openapi.secured("token")
        # secure_app: WebAppSpec = get_class("services.security.web.WebApp")()
        # secure_app.init(app, settings)
        # Authenticator(app)

    for sd in settings.STATICFILES_DIRS:
        app.static(sd.uripath, sd.localdir, name=sd.name)

    render: Render = Render(searchpath=settings.TEMPLATES_DIR)
    render.init_app(app)
    render.add_static(app, settings)
    if settings.VITE_ENABLED:
        render.add_vite(app, settings)

    app.ctx.databases = {}
    if settings.DATABASES:
        init_db_func(app, settings)

    for wapp in settings.APPS:
        WebAppClass: WebAppSpec = get_class(wapp)
        WebAppClass(app, settings)

    if with_status_handler:
        app.add_route(status_handler, "/status", name="status")

    if settings.STORAGE:
        storage.init_app(app, settings)

    return app
