import importlib

import click
from sqlalchemy.sql.schema import MetaData

from services import conf, defaults, utils
from services.db import SQL, Migration
from services.db.helpers import delete_table
from services.db.ext import utils as dbutils
from rich.console import Console

console = Console()


def get_meta_from_app(app_name) -> MetaData:
    Base = utils.get_class(f"{app_name}.db.Base")
    return Base.metadata


@click.group(name="db")
def db_cli():
    """
    DB related tasks
    """
    pass


@db_cli.command(name="create-tables")
@click.option("--db", default="default", help="db name in the settings module")
@click.option(
    "--settings-module",
    "-s",
    default=defaults.SETTINGS_MODULE,
    help="Fullpath to settings module",
)
@click.argument("app_name")
def create_tables(app_name, db, settings_module):
    """Creates database schemas.

    Models should be accesible from {app_name}.models"""
    settings = conf.load_conf(settings_module)

    models_module = importlib.import_module(f"{app_name}.models")

    db = SQL.from_conf(settings.DATABASES[db])
    db.create_all(get_meta_from_app(app_name))


@db_cli.command("list-tables")
@click.option("--db", default="default", help="db name in the settings module")
@click.option(
    "--settings-module",
    "-s",
    default=defaults.SETTINGS_MODULE,
    help="Fullpath to settings module",
)
@click.argument("app_name")
def list_tables(app_name, db, settings_module):
    """List tables of a database"""

    settings = conf.load_conf(settings_module)

    _ = importlib.import_module(f"{app_name}.models")

    db = SQL.from_conf(settings.DATABASES[db])
    tables = db.list_tables()
    console.print(tables)


@db_cli.command("drop-table")
@click.option("--db", default="default", help="db name in the settings module")
@click.option(
    "--settings-module",
    "-s",
    default=defaults.SETTINGS_MODULE,
    help="Fullpath to settings module",
)
@click.option(
    "--table",
    "-t",
    help="Name of the table to drop",
)
@click.argument("app_name")
def drop_table(app_name, db, settings_module, table):
    """Delete a table"""

    settings = conf.load_conf(settings_module)

    _ = importlib.import_module(f"{app_name}.models")

    _db = SQL.from_conf(settings.DATABASES[db])
    res = delete_table(_db, table)
    if res:
        console.print(f"[green]Table {table} deleted[/]")
    else:
        console.print(f"[red]Delete of table {table} failed[/]")


@db_cli.command()
@click.option("--db", default="default", help="db name in the settings module")
@click.option(
    "--settings-module",
    "-s",
    default=defaults.SETTINGS_MODULE,
    help="Fullpath to settings module",
)
@click.argument("app_name")
def drop(app_name, db, settings_module):
    """drop database schemas"""
    settings = conf.load_conf(settings_module)

    models_module = importlib.import_module(f"{app_name}.models")

    db = SQL.from_conf(settings.DATABASES[db])
    db.drop_all(get_meta_from_app(app_name), all_=True)


@db_cli.command()
@click.option("--db", default="default", help="db name in the settings module")
@click.option("--alembic", "-a", default="alembic.ini", help="alembic file")
@click.option("--to", "-t", default="head", help="Revision to upgrade or downgrade")
@click.option(
    "--settings-module",
    "-s",
    default=defaults.SETTINGS_MODULE,
    help="Fullpath to settings module",
)
@click.argument("app_name")
def upgrade(app_name, db, settings_module, alembic, to):
    """upgrade a database based on the migrations created. Use as:

    srv db upgrade example_app

    """
    settings = conf.load_conf(settings_module)

    m = Migration(
        settings.DATABASES[db].sync_url, section=app_name, alembic_file=alembic
    )
    m.upgrade(to=to)


@db_cli.command()
@click.option("--db", default="default", help="db name in the settings module")
@click.option("--alembic", "-a", default="alembic.ini", help="alembic file")
@click.option("--to", "-t", default="head", help="Revision to upgrade or downgrade")
@click.option(
    "--settings-module",
    "-s",
    default=defaults.SETTINGS_MODULE,
    help="Fullpath to settings module",
)
@click.argument("app_name")
def downgrade(app_name, db, settings_module, alembic, to):
    """downgrade a database based on the migrations created"""
    settings = conf.load_conf(settings_module)

    m = Migration(
        settings.DATABASES[db].sync_url, section=app_name, alembic_file=alembic
    )
    m.downgrade(to=to)


@db_cli.command()
@click.option("--db", default="default", help="db name in the settings module")
@click.option("--alembic", "-a", default="alembic.ini")
@click.option("--message", "-m", default=None, help="Revision name")
@click.option("--rev-id", "-R", help="Revision id")
@click.option(
    "--head",
    default=None,
    help="Specify head revision or <branchname>@head to base new revision.",
)
@click.option(
    "--branch-label",
    "-b",
    default=None,
    help="Specify a branch label to apply to the new revision",
)
@click.option("--depends-on", "-d", help="list of 'depends on' identifiers")
@click.option(
    "--settings-module",
    "-s",
    default=defaults.SETTINGS_MODULE,
    help="Fullpath to settings module",
)
@click.argument("app_name")
def revision(
    app_name,
    db,
    alembic,
    message,
    rev_id,
    head,
    branch_label,
    depends_on,
    settings_module,
):
    """generates migrations files from models defined in apps. Use as:

    srv db revision example_app -m first -R 0001 -m first
    """

    settings = conf.load_conf(settings_module)

    m = Migration(
        settings.DATABASES[db].sync_url, section=app_name, alembic_file=alembic
    )

    m.revision(
        rev_id=rev_id,
        message=message,
        head=head,
        branch_label=branch_label,
        depends_on=depends_on,
        autogenerate=True,
    )


@db_cli.command(name="create-db")
@click.option("--db", default="default", help="db name in the settings module")
@click.option(
    "--settings-module",
    "-s",
    default=defaults.SETTINGS_MODULE,
    help="Fullpath to settings module",
)
@click.option(
    "--encoding",
    "-e",
    default="utf8",
    help="Encoding",
)
def create_db(db, settings_module, encoding):
    """Creates database"""

    settings = conf.load_conf(settings_module)

    _db = settings.DATABASES[db]
    dbutils.create_databese(_db.sync_url, encoding=encoding)
