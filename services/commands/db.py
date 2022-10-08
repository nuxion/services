import click
from rich.console import Console
from rich.prompt import Prompt
from services import conf, defaults, types, utils
from services.db import Migration
from services.db.sqlhelper import SQL


@click.group(name="db")
def dbcli():
    """
    DB related tasks
    """
    pass


@dbcli.command()
@click.option("--db", default="default", help="db name in the settings module")
@click.option("--settings-module", "-s",
              default=defaults.SETTINGS_MODULE,
              help="Fullpath to settings module")
@click.argument("app_name")
def create(app_name, db, settings_module):
    """creates database schemas """
    settings = conf.load_conf(settings_module)

    db = SQL(settings.DATABASES[db])
    db.create_all(utils.get_meta_from_app(app_name))


@dbcli.command()
@click.option("--db", default="default", help="db name in the settings module")
@click.option("--settings-module", "-s",
              default=defaults.SETTINGS_MODULE,
              help="Fullpath to settings module")
@click.argument("app_name")
def drop(app_name, db, settings_module):
    """drop database schemas """
    settings = conf.load_conf(settings_module)

    db = SQL(settings.DATABASES[db])
    db.drop_all(utils.get_meta_from_app(app_name))


@dbcli.command()
@click.option("--db", default="default", help="db name in the settings module")
@click.option("--alembic", "-a", default="alembic.ini",
              help="alembic file")
@click.option("--to", "-t", default="head", help="Revision to upgrade or downgrade")
@click.option("--settings-module", "-s",
              default=defaults.SETTINGS_MODULE,
              help="Fullpath to settings module")
@click.argument("app_name")
def upgrade(app_name, db, settings_module, alembic, to):
    """upgrade a database based on the migrations created"""
    settings = conf.load_conf(settings_module)

    m = Migration(settings.DATABASES[db].sync_url,
                  section=app_name,
                  alembic_file=alembic)
    m.upgrade(
        to=to
    )


@dbcli.command()
@click.option("--db", default="default", help="db name in the settings module")
@click.option("--alembic", "-a", default="alembic.ini",
              help="alembic file")
@click.option("--to", "-t", default="head", help="Revision to upgrade or downgrade")
@click.option("--settings-module", "-s",
              default=defaults.SETTINGS_MODULE,
              help="Fullpath to settings module")
@click.argument("app_name")
def downgrade(app_name, db, settings_module, alembic, to):
    """downgrade a database based on the migrations created"""
    settings = conf.load_conf(settings_module)

    m = Migration(settings.DATABASES[db].sync_url,
                  section=app_name,
                  alembic_file=alembic)
    m.downgrade(
        to=to
    )


@dbcli.command()
@click.option("--db", default="default", help="db name in the settings module")
@click.option("--alembic", "-a", default="alembic.ini")
@click.option("--message", "-m", default=None, help="Revision name")
@click.option("--rev-id", "-R", help="Revision id")
@click.option("--head", default=None, help="Specify head revision or <branchname>@head to base new revision.")
@click.option("--branch-label", "-b", default=None, help="Specify a branch label to apply to the new revision")
@click.option("--depends-on", "-d", help="list of 'depends on' identifiers")
@click.option("--settings-module", "-s", default=defaults.SETTINGS_MODULE, help="Fullpath to settings module")
@click.argument("app_name")
def revision(app_name, db, alembic,
             message,
             rev_id, head, branch_label, depends_on,
             settings_module):
    """ generates migrations files from models defined in apps """

    settings = conf.load_conf(settings_module)

    m = Migration(settings.DATABASES[db].sync_url,
                  section=app_name,
                  alembic_file=alembic)

    m.revision(
        rev_id=rev_id,
        message=message,
        head=head,
        branch_label=branch_label,
        depends_on=depends_on,
        autogenerate=True)
