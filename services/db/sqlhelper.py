import contextlib
import logging
from typing import Any, Callable, Coroutine, List, Optional

from sqlalchemy import MetaData, create_engine, event, inspect, text
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio.engine import AsyncEngine

# from sqlalchemy.dialects.postgresql.base import PGInspector
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from services import types

from .utils import drop_everything


def sqlite_async_uri(filename) -> str:
    return f"sqlite+aiosqlite:///{filename}"


async def async_vacuum(engine: AsyncEngine, table: Optional[str] = None) -> bool:
    """https://github.com/sqlalchemy/sqlalchemy/discussions/6959"""
    autocommit = engine.execution_options(isolation_level="AUTOCOMMIT")
    _vacuum = None
    url = str(engine.url)
    if "postgresql" in url and table:
        _vacuum = f"VACUUM ANALYZE {table}"
    elif "sqlite" in url:
        _vacuum = "vacuum"

    if _vacuum:
        async with autocommit.connect() as conn:
            await conn.execute(text(_vacuum))
        await autocommit.dispose()
        return True
    return False


async def async_set_pragma(engine: AsyncEngine, pragma="journal_mode=WAL") -> bool:
    """https://github.com/sqlalchemy/sqlalchemy/discussions/6959"""
    autocommit = engine.execution_options(isolation_level="AUTOCOMMIT")
    _pragma = None
    url = str(engine.url)
    if "sqlite" in url:
        _pragma = f"PRAGMA {pragma}"
    if _pragma:
        async with autocommit.connect() as conn:
            await conn.execute(text(_pragma))
        await autocommit.dispose()
        return True
    return False


def set_pragma(engine: Engine, pragma="journal_mode=WAL") -> bool:
    """https://github.com/sqlalchemy/sqlalchemy/discussions/6959"""
    autocommit = engine.execution_options(isolation_level="AUTOCOMMIT")
    _pragma = None
    url = str(engine.url)
    if "sqlite" in url:
        _pragma = f"PRAGMA {pragma}"

    if _pragma:
        with autocommit.connect() as conn:
            conn.execute(text(_pragma))
        return True
    return False


def vacuum(engine: Engine, table: Optional[str] = None) -> bool:
    """https://github.com/sqlalchemy/sqlalchemy/discussions/6959"""
    autocommit = engine.execution_options(isolation_level="AUTOCOMMIT")
    _vacuum = None
    url = str(engine.url)
    if "postgresql" in url and table:
        _vacuum = f"VACUUM ANALYZE {table}"
    elif "sqlite" in url:
        _vacuum = "vacuum"

    if _vacuum:
        with autocommit.connect() as conn:
            conn.execute(text(_vacuum))
        return True
    return False


class SQL:
    def __init__(
        self, db: types.Database, engine: Engine, autoflush=True, expire_on_commit=False
    ):
        """SQL sync helper to build connections and sessions
        it's prepared to be used with Core and ORM

        :param db: accepts type :class:`services.types.Database`
        :type db: services.types.Database
        """
        self.conf = db
        self._autoflush = autoflush
        self._engine = engine
        self._session = sessionmaker(self._engine, expire_on_commit=expire_on_commit)

    @staticmethod
    def create_engine(conf: types.Database) -> Engine:
        if "sqlite" in conf.sync_url.split("://", maxsplit=1)[0]:
            engine = create_engine(conf.sync_url, echo=conf.debug)
        else:
            engine = create_engine(
                conf.sync_url,
                pool_size=conf.pool_size,
                max_overflow=conf.max_overflow,
                echo=conf.debug,
            )
        return engine

    @property
    def engine(self) -> Engine:
        return self._engine

    @property
    def session(self) -> sessionmaker:
        """
        It's a session factory it should be used as:

        .. code:

            with db.session() as session:
                session.execute(...)

        """
        return self._session

    @classmethod
    def from_uri(cls, uri: str, autoflush=True, expire_on_commit=False) -> "SQL":
        _db = types.Database(async_url=uri)
        engine = cls.create_engine(_db)
        obj = cls(
            _db, engine=engine, autoflush=autoflush, expire_on_commit=expire_on_commit
        )
        # await obj.init()
        return obj

    @classmethod
    def from_conf(
        cls, db: types.Database, autoflush=True, expire_on_commit=False
    ) -> "SQL":
        engine = cls.create_engine(db)
        obj = cls(
            db, engine=engine, autoflush=autoflush, expire_on_commit=expire_on_commit
        )
        return obj

    def create_all(self, meta: MetaData):
        """
        To create a database it's need the MetaData object
        from sqlalchemy
        """
        meta.create_all(self.engine)

    def drop_all(self, meta: Optional[MetaData] = None, all_=True):
        """it drops the content of a database, if all_ is set False
        then it only will drop elementes in meta.

        """

        if all_:
            drop_everything(self.engine)
        elif meta:
            meta.drop_all(self.engine)
        else:
            raise AttributeError("MetaData object or all_ param should be provided")

    def list_tables(self) -> List[str]:
        inspector = inspect(self.engine)
        return inspector.get_table_names()

    def reflect_metadata(self) -> MetaData:
        metadata = MetaData()
        metadata.reflect(bind=self.engine)
        return metadata

    def add_event(self, func: Callable, type_event="connect"):
        event.listen(self.engine, type_event, func)

    def session_factory(self, expire_on_commit=False) -> sessionmaker:
        """it's actually returns a session"""
        return sessionmaker(self.engine, expire_on_commit=expire_on_commit)


class AsyncSQL:
    """
    As example checks:
    https://docs.sqlalchemy.org/en/14/_modules/examples/asyncio/async_orm.html

    scoped_session, useful in thread environments is removed in Async,
    AsyncSession is prefered insted: https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html#using-asyncio-scoped-session
    """

    # Meta = MetaData()

    def __init__(
        self,
        db: types.Database,
        engine: AsyncEngine,
        autoflush=True,
        expire_on_commit=False,
    ):
        self.conf = db
        self._autoflush = autoflush
        self._engine = engine
        self._async_session = async_sessionmaker(
            self._engine, expire_on_commit=expire_on_commit
        )

    @property
    def async_session(self) -> async_sessionmaker[AsyncSession]:
        """
        It's a session factory it should be used as:

        .. code:

            async with db.async_session() as session:
                await session.execute(...)

        """
        return self._async_session

    @staticmethod
    def create_engine(conf: types.Database) -> AsyncEngine:
        if "sqlite" in conf.async_url.split("://", maxsplit=1)[0]:
            engine = create_async_engine(conf.async_url, echo=conf.debug)
        else:
            engine = create_async_engine(
                conf.async_url,
                pool_size=conf.pool_size,
                max_overflow=conf.max_overflow,
                echo=conf.debug,
            )

        return engine

    @classmethod
    def from_uri(cls, uri: str, autoflush=True, expire_on_commit=False) -> "AsyncSQL":
        _db = types.Database(async_url=uri)
        engine = cls.create_engine(_db)
        obj = cls(
            _db, engine=engine, autoflush=autoflush, expire_on_commit=expire_on_commit
        )
        # await obj.init()
        return obj

    @classmethod
    def from_conf(
        cls, db: types.Database, autoflush=True, expire_on_commit=False
    ) -> "AsyncSQL":
        engine = cls.create_engine(db)
        obj = cls(
            db, engine=engine, autoflush=autoflush, expire_on_commit=expire_on_commit
        )
        return obj

    @contextlib.asynccontextmanager
    async def conn(self):
        try:
            async with self._engine.connect() as conn:
                yield conn
        finally:
            await self._engine.dispose()

    @contextlib.asynccontextmanager
    async def begin(self):
        try:
            async with self._engine.begin() as conn:
                yield conn
        finally:
            await self._engine.dispose()

    @contextlib.asynccontextmanager
    async def session(self):
        try:
            async with self.async_session() as session:
                yield session
        finally:
            await self._engine.dispose()

    def session_factory(
        self, autoflush=True, expire_on_commit=False
    ) -> async_sessionmaker:
        """
        expire_on_commit=False will prevent attributes from being expired
        after commit
        """
        return async_sessionmaker(
            self._engine,
            autoflush=autoflush,
            expire_on_commit=expire_on_commit,
        )

    def add_event(self, func: Callable, type_event="connect"):
        event.listen(self.engine.sync_engine, type_event, func)

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    @property
    def sync_engine(self) -> Engine:
        return self._engine.sync_engine

    async def create_all(self, meta: MetaData):
        async with self._engine.begin() as conn:
            await conn.run_sync(meta.create_all)

    async def drop_all(self, meta: Optional[MetaData] = None, all_=True):
        async with self._engine.begin() as conn:
            if all_:
                await conn.run_sync(drop_everything, self.engine)
            elif meta:
                await conn.run_sync(meta.drop_all)
            else:
                raise AttributeError("MetaData object or all_ param should be provided")

    async def list_tables(self) -> Coroutine[Any, Any, List[str]]:
        async with self._engine.connect() as conn:
            tables = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_table_names()
            )
        return tables

    async def dispose(self):
        # for AsyncEngine created in function scope, close and
        # clean-up pooled connections
        await self._engine.dispose()
