import logging
from typing import Callable, List

from sqlalchemy import MetaData, create_engine, event, inspect
# from sqlalchemy.dialects.postgresql.base import PGInspector
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from .common import Base
from .utils import drop_everything


class SQL:
    def __init__(self, sqluri: str, pool_size=20, max_overflow=0, inspector=False):
        """
        :param sqluri: 'postgresql://postgres:secret@localhost:5432/twitter'
        """
        self._uri = sqluri
        if "sqlite" in sqluri.split("://", maxsplit=1)[0]:
            self.engine = create_engine(sqluri)
        else:
            self.engine = create_engine(
                sqluri, pool_size=pool_size, max_overflow=max_overflow
            )

        self.inspector = None
        if inspector:
            self.inspector = inspect(self.engine)
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(logging.NullHandler())

    def create_all(self):
        Sess = self.scoped_session()
        with Sess() as session:
            with session.begin():
                Base.metadata.create_all(self.engine)

    def drop_all(self):
        drop_everything(self.engine)

    def list_tables(self) -> List[str]:
        if not self.inspector:
            self.inspector = inspect(self.engine)
        return self.inspector.get_table_names()

    def reflect_metadata(self) -> MetaData:
        metadata = MetaData()
        metadata.reflect(bind=self.engine)
        return metadata

    def sessionmaker(self, autoflush=True):
        """Session could be used as context manager
        Autocommit will be deprecated in SQLAlchemy 2.0
        Session.begin() method may be used to explicitly start transactions

        :param autoflush: When True, all query operations will issue a Session.
        flush() call to this Session before proceeding. Flush
        """

        session = sessionmaker(
            bind=self.engine, autoflush=autoflush, future=True)
        return session

    def scoped_session(self, autoflush=True) -> Session:
        """Scoped session return a Session object that could be used
        with a context manager

        https://docs.sqlalchemy.org/en/14/orm/session_basics.html#opening-and-closing-a-session

        """
        SSession = scoped_session(sessionmaker(
            autoflush=autoflush, bind=self.engine))

        return SSession

    def add_event(self, func: Callable, type_event="connect"):
        event.listen(self.engine, type_event, func)
