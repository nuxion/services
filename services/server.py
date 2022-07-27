from contextvars import ContextVar
from importlib import import_module
from typing import List

from sanic import Sanic
from sanic.response import json
from sanic_ext import Extend

from services import defaults
from services.db.nosync import AsyncSQL
from services.redis_conn import create_pool
from services.security import auth_from_settings, sanic_init_auth
from services.security.redis_tokens import RedisTokenStore
from services.security.types import SecuritySettings
from services.types import Settings
from services.utils import get_class, get_version

version = get_version("__version__.py")


async def status_handler(request):
    return json(dict(msg="We are ok", version=version))


def init_blueprints(app, blueprints_allowed, package_dir="services.web"):
    """
    It will import bluprints from modules that ends with "_bp" and belongs
    to the package declared in `changeme.defaults.SANIC_BLUPRINTS_DIR`
    by default it will be `changeme.services`
    """
    blueprints = set()
    mod = app.__module__
    for mod_name in blueprints_allowed:
        modules = import_module(f"{package_dir}.{mod_name}_bp", mod)
        for el in dir(modules):
            if el.endswith("_bp"):
                bp = getattr(modules, el)
                blueprints.add(bp)

    for bp in blueprints:
        print("Adding blueprint: ", bp.name)
        app.blueprint(bp)


def init_db(app: Sanic, settings: Settings):
    from services.db.web import sanic_init_db
    sanic_init_db(app, settings)


# def init_redis(app: Sanic, settings: Settings):
#     from services.redis import sanic_init_redis
#     sanic_init_redis(app, settings)


class Server:

    def __init__(self, settings: Settings):
        self.settings = settings
        self._app: Sanic = None

    @property
    def app(self) -> Sanic:
        return self._app

    def create_app(self,
                   list_bp: List[str],
                   app_name=defaults.SANIC_APP,
                   create_redis=create_pool,
                   with_auth=True,
                   with_auth_bp=True,
                   with_db=True,
                   ) -> Sanic:
        app = Sanic(app_name)

        app.config.CORS_ORIGINS = "*"
        # app.config.CORS_ALLOW_HEADERS = ["GET", "POST", "DELETE", "PUT"]
        app.config.CORS_METHODS = ["GET", "POST", "DELETE", "PUT"]
        app.config.CORS_AUTOMATIC_OPTIONS = True
        app.config.CORS_SUPPORTS_CREDENTIALS = True

        Extend(app)
        app.ext.openapi.add_security_scheme(
            "token",
            "http",
            scheme="bearer",
            bearer_format="JWT",
        )
        # app.ext.openapi.secured()
        app.ext.openapi.secured("token")

        _base_model_session_ctx = ContextVar("session")

        if list_bp:
            init_blueprints(app, list_bp, package_dir=package_dir)

        web_redis = create_redis(settings.REDIS_WEB)
        if with_auth:
            auth_settings = SecuritySettings()
            _store = RedisTokenStore(web_redis)
            auth = auth_from_settings(auth_settings, _store)
            sanic_init_auth(app, auth, auth_settings)
        if with_auth and with_auth_bp:
            init_blueprints(app, ["auth"], "services.security")
        if with_db:
            init_db(app, settings=settings)

        app.add_route(status_handler, "/status")
        self._app = app
        return app

    def run(self, services_bp: List[str],
            pkg_name: str,
            host=None, port=None,
            workers=1,
            access_log=True,
            debug=False):
        host = host or self.settings.HOST
        port = port or self.settings.PORT
        self._app.run(host=host,
                      port=int(port),
                      access_log=access_log,
                      workers=w,
                      debug=debug)


def create_app(
    settings: Settings,
    list_bp: List[str],
    package_dir="services.web",
    app_name=defaults.SANIC_APP,
    create_redis=create_pool,
    with_auth=True,
    with_auth_bp=True,
    with_db=True,
) -> Sanic:
    """Factory pattern like flask"""

    app = Sanic(app_name)

    app.config.CORS_ORIGINS = "*"

    Extend(app)
    app.ext.openapi.add_security_scheme(
        "token",
        "http",
        scheme="bearer",
        bearer_format="JWT",
    )
    # app.ext.openapi.secured()
    app.ext.openapi.secured("token")

    _base_model_session_ctx = ContextVar("session")

    if list_bp:
        init_blueprints(app, list_bp, package_dir=package_dir)
    web_redis = create_redis(settings.REDIS_WEB)
    if with_auth:
        auth_settings = SecuritySettings()
        _store = RedisTokenStore(web_redis)
        auth = auth_from_settings(auth_settings, _store)
        sanic_init_auth(app, auth, auth_settings)
    if with_auth and with_auth_bp:
        init_blueprints(app, ["auth"], "services.security")
    if with_db:
        init_db(app, settings=settings)

    app.add_route(status_handler, "/status")

    # @app.listener("before_server_start")
    # async def startserver(current_app, loop):
    #     """This function runs one time per worker"""
    #     _db = db_func(settings.ASQL)
    #     _base_model_session_ctx = ContextVar("session")

    #     current_app.ctx.web_redis = web_redis.client()
    #     current_app.ctx.db = _db
    #     await current_app.ctx.db.init()

    # @app.middleware("request")
    # async def inject_session(request):
    #     current_app = Sanic.get_app(defaults.SANIC_APP)

    #     request.ctx.session = current_app.ctx.db.sessionmaker()
    #     request.ctx.session_ctx_token = _base_model_session_ctx.set(
    #         request.ctx.session)
    #     request.ctx.web_redis = current_app.ctx.web_redis
    #     request.ctx.dbconn = current_app.ctx.db.engine

    # @app.middleware("response")
    # async def close_session(request, response):
    #     if hasattr(request.ctx, "session_ctx_token"):
    #         _base_model_session_ctx.reset(request.ctx.session_ctx_token)
    #         await request.ctx.session.close()

    # @app.listener("after_server_stop")
    # async def shutdown(current_app, loop):
    #     await current_app.ctx.db.engine.dispose()
    #     # await current_app.ctx.redis.close()

    return app
