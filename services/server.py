from importlib import import_module

from sanic import Sanic
from sanic.response import json

from services import defaults
from services.base import WebAppSpec
from services.redis_conn import create_pool
from services.types import Settings
from services.utils import get_class, get_version

version = get_version("__version__.py")


async def status_handler(request):
    return json(dict(msg="We are ok", version=version))


def init_db(app: Sanic, settings: Settings):
    from services.db.web import sanic_init_db
    sanic_init_db(app, settings)


def create_srv(
    settings: Settings,
    app_name=defaults.SANIC_APP,
    create_redis=create_pool,
    with_auth=True,
    with_status_handler=True,
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
    if settings.REDIS_WEB:
        app.ctx.web_redis = create_redis(settings.REDIS_WEB)
    if settings.ASQL:
        init_db(app, settings=settings)

    if with_auth:
        app.ext.openapi.add_security_scheme(
            "token",
            "http",
            scheme="bearer",
            bearer_format="JWT",
        )
        app.ext.openapi.secured("token")
        secure_app: WebAppSpec = get_class("services.security.web.WebApp")()
        secure_app.init(app, settings)

        # _store = None
        # if web_redis:
        #    _store = RedisTokenStore(web_redis)
        # auth = auth_from_settings(settings.SECURITY, _store)
        # sanic_init_auth(app, auth, settings.SECURITY)
        # if with_auth_bp:
        #    init_blueprints(app, ["users_bp"], "services.users")

    for wapp in settings.APPS:
        w: WebAppSpec = get_class(wapp)()
        w.init(app, settings)

    if with_status_handler:
        app.add_route(status_handler, "/status")

    return app
