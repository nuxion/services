import os
from contextvars import ContextVar

from sanic import Request, Sanic
from sanic.log import logger
from sanic.response import HTTPResponse
from services import defaults
from services.base import PluginSpec
from services.db.sqlhelper import SQL, AsyncSQL
from services.types import Settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio.engine import AsyncEngine


class AsyncDBHelper:

    async def listener_db(self, app: Sanic):
        for k, v in app.config.DATABASES.items():
            _db = AsyncSQL(v,
                           set_session_factory=True)
            logger.info(f"Starting db {k}")
            await _db.init()
            app.ctx.databases[k] = _db

    def get_db(self, request, *, name="default") -> AsyncSQL:
        return request.app.ctx.databases.get(name)

    def get_session(self, request, *, name="default") -> AsyncSession:
        db = self.get_db(request, name=name)
        return db.session_factory()

    def get_engine(self, request, *, name="default") -> AsyncEngine:
        db = self.get_db(request, name=name)
        return db.engine


def init_db(app: Sanic, settings: Settings):
    app.config.DATABASES = settings.DATABASES
    db_helper = AsyncDBHelper()
    app.register_listener(db_helper.listener_db, "before_server_start")
    app.ext.dependency(db_helper)
