# taken from
# https://sqlalchemy-utils.readthedocs.io/en/latest/_modules/sqlalchemy_utils/functions/database.html#create_database
import os
from copy import copy

import sqlalchemy as sa
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm.exc import UnmappedInstanceError
from sqlalchemy.orm.session import object_session


def _get_scalar_result(engine, sql):
    with engine.connect() as conn:
        return conn.scalar(sql)


def _set_url_database(url: sa.engine.url.URL, database):
    """Set the database of an engine URL.

    :param url: A SQLAlchemy engine URL.
    :param database: New database to set.

    """
    if hasattr(url, "_replace"):
        # Cannot use URL.set() as database may need to be set to None.
        ret = url._replace(database=database)
    else:  # SQLAlchemy <1.4
        url = copy(url)
        url.database = database
        ret = url
    assert ret.database == database, ret
    return ret


def _sqlite_file_exists(database):
    if not os.path.isfile(database) or os.path.getsize(database) < 100:
        return False

    with open(database, "rb") as f:
        header = f.read(100)

    return header[:16] == b"SQLite format 3\x00"


def get_bind(obj):
    """
    Return the bind for given SQLAlchemy Engine / Connection / declarative
    model object.

    :param obj: SQLAlchemy Engine / Connection / declarative model object

    ::

        from sqlalchemy_utils import get_bind


        get_bind(session)  # Connection object

        get_bind(user)

    """
    if hasattr(obj, "bind"):
        conn = obj.bind
    else:
        try:
            conn = object_session(obj).bind
        except UnmappedInstanceError:
            conn = obj

    if not hasattr(conn, "execute"):
        raise TypeError(
            "This method accepts only Session, Engine, Connection and "
            "declarative model objects."
        )
    return conn


def quote(mixed, ident):
    """
    Conditionally quote an identifier.
    ::


        from sqlalchemy_utils import quote


        engine = create_engine('sqlite:///:memory:')

        quote(engine, 'order')
        # '"order"'

        quote(engine, 'some_other_identifier')
        # 'some_other_identifier'


    :param mixed: SQLAlchemy Session / Connection / Engine / Dialect object.
    :param ident: identifier to conditionally quote
    """
    if isinstance(mixed, Dialect):
        dialect = mixed
    else:
        dialect = get_bind(mixed).dialect
    return dialect.preparer(dialect).quote(ident)


def database_exists(url):
    """Check if a database exists.

    :param url: A SQLAlchemy engine URL.

    Performs backend-specific testing to quickly determine if a database
    exists on the server. ::

        database_exists('postgresql://postgres@localhost/name')  #=> False
        create_database('postgresql://postgres@localhost/name')
        database_exists('postgresql://postgres@localhost/name')  #=> True

    Supports checking against a constructed URL as well. ::

        engine = create_engine('postgresql://postgres@localhost/name')
        database_exists(engine.url)  #=> False
        create_database(engine.url)
        database_exists(engine.url)  #=> True

    """

    url = make_url(url)
    database = url.database
    dialect_name = url.get_dialect().name
    engine = None
    try:
        if dialect_name == "postgresql":
            text = "SELECT 1 FROM pg_database WHERE datname='%s'" % database
            for db in (database, "postgres", "template1", "template0", None):
                url = _set_url_database(url, database=db)
                engine = sa.create_engine(url)
                try:
                    return bool(_get_scalar_result(engine, sa.text(text)))
                except (ProgrammingError, OperationalError):
                    pass
            return False

        elif dialect_name == "mysql":
            url = _set_url_database(url, database=None)
            engine = sa.create_engine(url)
            text = (
                "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA "
                "WHERE SCHEMA_NAME = '%s'" % database
            )
            return bool(_get_scalar_result(engine, sa.text(text)))

        elif dialect_name == "sqlite":
            url = _set_url_database(url, database=None)
            engine = sa.create_engine(url)
            if database:
                return database == ":memory:" or _sqlite_file_exists(database)
            else:
                # The default SQLAlchemy database is in memory, and :memory: is
                # not required, thus we should support that use case.
                return True
        else:
            text = "SELECT 1"
            try:
                engine = sa.create_engine(url)
                return bool(_get_scalar_result(engine, sa.text(text)))
            except (ProgrammingError, OperationalError):
                return False
    finally:
        if engine:
            engine.dispose()


def create_database(url, encoding="utf8", template=None):
    """Issue the appropriate CREATE DATABASE statement.

    :param url: A SQLAlchemy engine URL.
    :param encoding: The encoding to create the database as.
    :param template:
        The name of the template from which to create the new database. At the
        moment only supported by PostgreSQL driver.

    To create a database, you can pass a simple URL that would have
    been passed to ``create_engine``. ::

        create_database('postgresql://postgres@localhost/name')

    You may also pass the url from an existing engine. ::

        create_database(engine.url)

    Has full support for mysql, postgres, and sqlite. In theory,
    other database engines should be supported.
    """

    url = make_url(url)
    database = url.database
    dialect_name = url.get_dialect().name
    dialect_driver = url.get_dialect().driver

    if dialect_name == "postgresql":
        url = _set_url_database(url, database="postgres")
    elif dialect_name == "mssql":
        url = _set_url_database(url, database="master")
    elif dialect_name == "cockroachdb":
        url = _set_url_database(url, database="defaultdb")
    elif not dialect_name == "sqlite":
        url = _set_url_database(url, database=None)

    if (dialect_name == "mssql" and dialect_driver in {"pymssql", "pyodbc"}) or (
        dialect_name == "postgresql"
        and dialect_driver
        in {"asyncpg", "pg8000", "psycopg", "psycopg2", "psycopg2cffi"}
    ):
        engine = sa.create_engine(url, isolation_level="AUTOCOMMIT")
    else:
        engine = sa.create_engine(url)

    if dialect_name == "postgresql":
        if not template:
            template = "template1"

        with engine.begin() as conn:
            text = "CREATE DATABASE {} ENCODING '{}' TEMPLATE {}".format(
                quote(conn, database), encoding, quote(conn, template)
            )
            conn.execute(sa.text(text))

    elif dialect_name == "mysql":
        with engine.begin() as conn:
            text = "CREATE DATABASE {} CHARACTER SET = '{}'".format(
                quote(conn, database), encoding
            )
            conn.execute(sa.text(text))

    elif dialect_name == "sqlite" and database != ":memory:":
        if database:
            with engine.begin() as conn:
                conn.execute(sa.text("CREATE TABLE DB(id int)"))
                conn.execute(sa.text("DROP TABLE DB"))

    else:
        with engine.begin() as conn:
            text = f"CREATE DATABASE {quote(conn, database)}"
            conn.execute(sa.text(text))

    engine.dispose()


def drop_database(url):
    """Issue the appropriate DROP DATABASE statement.

    :param url: A SQLAlchemy engine URL.

    Works similar to the :ref:`create_database` method in that both url text
    and a constructed url are accepted. ::

        drop_database('postgresql://postgres@localhost/name')
        drop_database(engine.url)

    """

    url = make_url(url)
    database = url.database
    dialect_name = url.get_dialect().name
    dialect_driver = url.get_dialect().driver

    if dialect_name == "postgresql":
        url = _set_url_database(url, database="postgres")
    elif dialect_name == "mssql":
        url = _set_url_database(url, database="master")
    elif dialect_name == "cockroachdb":
        url = _set_url_database(url, database="defaultdb")
    elif not dialect_name == "sqlite":
        url = _set_url_database(url, database=None)

    if dialect_name == "mssql" and dialect_driver in {"pymssql", "pyodbc"}:
        engine = sa.create_engine(url, connect_args={"autocommit": True})
    elif dialect_name == "postgresql" and dialect_driver in {
        "asyncpg",
        "pg8000",
        "psycopg",
        "psycopg2",
        "psycopg2cffi",
    }:
        engine = sa.create_engine(url, isolation_level="AUTOCOMMIT")
    else:
        engine = sa.create_engine(url)

    if dialect_name == "sqlite" and database != ":memory:":
        if database:
            os.remove(database)
    elif dialect_name == "postgresql":
        with engine.begin() as conn:
            # Disconnect all users from the database we are dropping.
            version = conn.dialect.server_version_info
            pid_column = "pid" if (version >= (9, 2)) else "procpid"
            text = """
            SELECT pg_terminate_backend(pg_stat_activity.{pid_column})
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{database}'
            AND {pid_column} <> pg_backend_pid();
            """.format(
                pid_column=pid_column, database=database
            )
            conn.execute(sa.text(text))

            # Drop the database.
            text = f"DROP DATABASE {quote(conn, database)}"
            conn.execute(sa.text(text))
    else:
        with engine.begin() as conn:
            text = f"DROP DATABASE {quote(conn, database)}"
            conn.execute(sa.text(text))

    engine.dispose()
