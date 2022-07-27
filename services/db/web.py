import os
from contextvars import ContextVar

from services import defaults
from services.db.nosync import AsyncSQL
from services.types import Settings
from sanic import Request, Sanic
from sanic.response import HTTPResponse

_base_model_session_ctx = ContextVar("session")


def create_db_instance(url) -> AsyncSQL:
    return AsyncSQL(url)


async def inject_session_req(request: Request):
    current_app = request.app
    request.ctx.session = current_app.ctx.db.sessionmaker()
    request.ctx.session_ctx_token = _base_model_session_ctx.set(
        request.ctx.session)


async def close_session_res(request: Request, response: HTTPResponse):
    if hasattr(request.ctx, "session_ctx_token"):
        _base_model_session_ctx.reset(request.ctx.session_ctx_token)
        await request.ctx.session.close()


async def listener_db(app: Sanic):
    _db = create_db_instance(app.config.ASQL)
    app.ctx.db = _db
    await app.ctx.db.init()


def sanic_init_db(app: Sanic, settings: Settings):
    app.config.ASQL = settings.ASQL
    app.register_listener(listener_db, "before_server_start")
    app.register_middleware(inject_session_req, "request")
    app.register_middleware(close_session_res, "response")
