import logging
from typing import Any, Callable, Coroutine, Dict, List, Optional, Union

from services import types
from sqlalchemy import MetaData, create_engine, event, inspect
from sqlalchemy.engine.base import Engine
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.ext.asyncio import (AsyncSession, async_scoped_session,
                                    create_async_engine)
from sqlalchemy.ext.asyncio.engine import AsyncEngine
# from sqlalchemy.dialects.postgresql.base import PGInspector
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from .utils import drop_everything


class SQL:

    def __init__(self, db: types.Database,
                 set_session_factory=True,
                 autoflush=True,
                 init_engine=True,
                 future=True):
        """ SQL sync helper to build connections and sessions
        it's prepared to be used with Core and ORM

        :param db: accepts type :class:`services.types.Database`
        :type db: services.types.Database
        """
        self.conf = db
        self._future = future
        self._autoflush = autoflush
        if init_engine:
            self._init(session_factory=set_session_factory)

    @classmethod
    def from_uri(cls, uri: str, init_engine=True) -> "SQL":
        _db = types.Database(sync_url=uri)
        return cls(_db, init_engine=init_engine)

    def _init(self, session_factory=True):
        if "sqlite" in self.conf.sync_url.split("://", maxsplit=1)[0]:
            self._engine = create_engine(self.conf.sync_url,
                                         echo=self.conf.debug)
        else:
            self._engine = create_engine(
                self.conf.sync_url,
                pool_size=self.conf.pool_size,
                max_overflow=self.conf.max_overflow,
                echo=self.conf.debug
            )

        if session_factory:
            self._factory = self.sessionmaker(
                autoflush=self._autoflush, future=self._future)

    @property
    def engine(self) -> Engine:
        return self._engine

    def create_all(self, meta: MetaData):
        """
        To create a database it's need the MetaData object
        from sqlalchemy
        """
        meta.create_all(self.engine)

    def drop_all(self, meta: Optional[MetaData] = None, all_=True):
        """ it drops the content of a database, if all_ is set False
        then it only will drop elementes in meta.

        """

        if all_:
            drop_everything(self.engine)
        elif meta:
            meta.drop_all(self.engine)
        else:
            raise AttributeError(
                "MetaData object or all_ param should be provided")

    def list_tables(self) -> List[str]:
        inspector = inspect(self.engine)
        return inspector.get_table_names()

    def reflect_metadata(self) -> MetaData:
        metadata = MetaData()
        metadata.reflect(bind=self.engine)
        return metadata

    def add_event(self, func: Callable, type_event="connect"):
        event.listen(self.engine, type_event, func)

    def sessionmaker(self, autoflush=True, future=True) -> sessionmaker:
        """ wrapper around SqlAlchemy sessionmaker

        :param future: default True then Query 2.0 style
        """
        return sessionmaker(bind=self.engine,
                            autoflush=autoflush,
                            future=future)

    def session_factory(self) -> Session:
        """ it's actually returns a session """
        return self._factory()

    def scoped_session(self, autoflush=True, future=True) -> Session:
        """ wrapper around SqlAlchemy session_scoped

        Create a single scoped_session registry when the web application
        first starts, ensuring that this object is accessible by the
        rest of the application.

        ensures that scoped_session.remove() is called when the web
        request ends.

        :param future: default True then Query 2.0 style
        """
        return scoped_session(sessionmaker(bind=self.engine,
                                           autoflush=autoflush,
                                           future=future))


class AsyncSQL:
    """
    As example checks:
    https://docs.sqlalchemy.org/en/14/_modules/examples/asyncio/async_orm.html

    scoped_session, useful in thread environments is removed in Async,
    AsyncSession is prefered insted: https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html#using-asyncio-scoped-session
    """

    # Meta = MetaData()

    def __init__(self, db: types.Database,
                 set_session_factory=True,
                 autoflush=True,
                 future=True):
        self.conf = db
        self._future = future
        self._autoflush = autoflush
        self._set_session_factory = set_session_factory

    async def init(self):
        if "sqlite" in self.conf.async_url.split("://", maxsplit=1)[0]:
            self._engine = create_async_engine(self.conf.async_url,
                                               echo=self.conf.debug)
        else:
            self._engine = create_async_engine(
                self.conf.async_url,
                pool_size=self.conf.pool_size,
                max_overflow=self.conf.max_overflow,
                echo=self.conf.debug
            )

        if self._set_session_factory:
            self._factory = self.sessionmaker(
                autoflush=self._autoflush, future=self._future)

    @classmethod
    def from_uri(cls, uri: str, init_engine=False) -> "AsyncSQL":
        _db = types.Database(async_url=uri)
        return cls(_db)

    def sessionmaker(self,
                     autoflush=True,
                     future=True,
                     expire_on_commit=False) -> sessionmaker:
        """
        expire_on_commit=False will prevent attributes from being expired
        after commit
        """
        return sessionmaker(
            self._engine,
            future=future,
            autoflush=autoflush,
            expire_on_commit=expire_on_commit, class_=AsyncSession
        )

    def session_factory(self) -> AsyncSession:
        """ it's actually returns a session """
        return self._factory()

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
                await conn.run_sync(
                    lambda sync_conn: drop_everything(sync_conn)
                )
            elif meta:
                await conn.run_sync(
                    lambda sync_conn: meta.drop_all(sync_conn)
                )
            else:
                raise AttributeError(
                    "MetaData object or all_ param should be provided")

    async def list_tables(self) -> Coroutine[Any, Any, List[str]]:
        async with self._engine.connect() as conn:
            tables = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_table_names()
            )
        return tables
