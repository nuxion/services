import importlib
from typing import List

from alembic import command
from alembic.config import Config as AlembicConfig
from services import defaults
from services.types import Migration
from services.utils import get_package_dir


def alembic_config(dburi: str,
                   version_table: str,
                   models_name: List[str],
                   migrations_module=defaults.MIGRATIONS_PKG) -> AlembicConfig:
    dir_ = get_package_dir(defaults.MIGRATIONS_PKG)
    alembic_file = f"{dir_}/alembic.ini"
    models = [importlib.import_module(mod) for mod in models_name]

    alembic_cfg = AlembicConfig(alembic_file)
    alembic_cfg.set_main_option("script_locations", migrations_module)
    alembic_cfg.set_main_option("version_table", version_table)
    alembic_cfg.set_main_option("sqlalchemy.url", dburi)
    return alembic_cfg


def alembic_ugprade(dburi: str,
                    migration: Migration,
                    to="head"):

    cfg = alembic_config(
        dburi,
        migration.version_table,
        migration.models,
        migrations_module=migration.migrations_module)
    command.upgrade(cfg, to)


def alembic_revision(dburi: str,
                     rev_id: str,
                     message: str,
                     migration: Migration,
                     autogenerate=True):
    cfg = alembic_config(dburi, migration.version_table, migration.models,
                         migrations_module=migration.migrations_module)

    command.revision(
        cfg,
        message=message,
        rev_id=rev_id,
        autogenerate=autogenerate)


def drop_everything(engine):
    """(On a live db) drops all foreign key constraints before dropping all tables.
    Workaround for SQLAlchemy not doing DROP ## CASCADE for drop_all()
    (https://github.com/pallets/flask-sqlalchemy/issues/722)
    """
    from sqlalchemy.engine.reflection import Inspector
    from sqlalchemy.schema import (DropConstraint, DropTable,
                                   ForeignKeyConstraint, MetaData, Table)

    con = engine.connect()
    trans = con.begin()
    # inspector = Inspector.from_engine(engine)
    inspector = inspect(engine)

    # We need to re-create a minimal metadata with only the required things to
    # successfully emit drop constraints and tables commands for postgres (based
    # on the actual schema of the running instance)
    meta = MetaData()
    tables = []
    all_fkeys = []

    for table_name in inspector.get_table_names():
        fkeys = []

        for fkey in inspector.get_foreign_keys(table_name):
            if not fkey["name"]:
                continue

            fkeys.append(ForeignKeyConstraint((), (), name=fkey["name"]))

        tables.append(Table(table_name, meta, *fkeys))
        all_fkeys.extend(fkeys)

    for fkey in all_fkeys:
        con.execute(DropConstraint(fkey))

    for table in tables:
        con.execute(DropTable(table))

    trans.commit()


def running_in_greenlet():
    return isinstance(greenlet.getcurrent(), _AsyncIoGreenlet)


def sync_as_async(fn):
    """https://github.com/sqlalchemy/sqlalchemy/discussions/5923
    It runs a session from the sync world into async functions"""

    def go(*arg, **kw):
        if running_in_greenlet():
            return await_only(fn(*arg, **kw))
        else:
            # no greenlet, assume no event loop and blocking IO backend
            coro = fn(*arg, **kw)
            try:
                coro.send(None)
            except StopIteration as err:
                return err.value

    return go
