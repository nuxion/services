import contextlib
from typing import AsyncIterator
from sanic import Sanic
from sanic.log import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio.engine import AsyncEngine

from services.db.sqlhelper import AsyncSQL
from services.types import Settings

# from typing import AsyncContextManager


class DBHelper:
    def __init__(self, app: Sanic):
        self.app = app

    async def listener_db(self, app: Sanic):
        for k, v in app.config.DATABASES.items():
            _db = AsyncSQL.from_conf(v)
            logger.info("Starting db %s", k)
            # await _db.init()
            app.ctx.databases[k] = _db

    def get_db(self, *, name="default") -> AsyncSQL:
        return self.app.ctx.databases.get(name)

    def get_engine(self, *, name="default") -> AsyncEngine:
        db = self.get_db(name=name)
        return db.engine

    async def dispose(self, *, name="default"):
        db = self.get_db(name=name)
        await db.dispose()

    @contextlib.asynccontextmanager
    async def session(self, *, name="default") -> AsyncIterator[AsyncSession]:
        """
        To be used for ORM implementation
        """
        db = self.get_db(name=name)
        try:
            async with db.async_session() as session:
                yield session
        finally:
            await self.dispose()

    @contextlib.asynccontextmanager
    async def conn(self, *, name="default") -> AsyncIterator[AsyncSession]:
        """
        To be used as the core part
        """
        db = self.get_db(name=name)
        try:
            async with db.conn() as conn:
                yield conn
        finally:
            await self.dispose()

    @contextlib.asynccontextmanager
    async def begin(self, *, name="default") -> AsyncIterator[AsyncSession]:
        """
        To be used as the core part
        """
        db = self.get_db(name=name)
        try:
            async with db.begin() as conn:
                yield conn
        finally:
            await self.dispose()


def init_db(app: Sanic, settings: Settings):
    app.config.DATABASES = settings.DATABASES
    db_helper = DBHelper(app)
    app.register_listener(db_helper.listener_db, "before_server_start")
    app.ext.dependency(db_helper)
