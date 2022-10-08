import asyncio
import importlib
import sys
from getpass import getpass
from pathlib import Path

import click
from rich.console import Console
from rich.prompt import Prompt
from services import conf, defaults, init_script, types
from services.db import SQL, AsyncSQL, Migration
from services.db.sqlhelper import AsyncSQL as AsyncSQL2
from services.users.managers import UserManager
from services.utils import get_class, mkdir_p

console = Console()


async def create_user(settings: types.Settings, data):
    db = AsyncSQL2(settings.DATABASES[settings.USER_DB])
    await db.init()
    # session = db.sessionmaker()
    manager = UserManager(db, model_class=settings.USER_MODEL,
                          salt=settings.SECURITY.AUTH_SALT)
    user = await manager.create(data)
    return user


@click.group(name="manager")
def managercli():
    """
    Managment tasks like user creation and db init
    """
    pass


@managercli.command(name="db")
# @click.option("--database", "-d", default="default", help="Database to apply migration")
@click.option("--message", "-m", default=None, help="Revision name")
@click.option("--rev-id", "-R", help="Revision id")
@click.option("--to", "-t", default="head", help="Revision to upgrade or downgrade")
@click.option("--head", default=None, help="Specify head revision or <branchname>@head to base new revision.")
@click.option("--branch-label", "-b", default=None, help="Specify a branch label to apply to the new revision")
@click.option("--name", "-n", default=None, help="package name where migration is located")
@click.option("--depends-on", "-d", help="list of 'depends on' identifiers")
@click.argument("action", type=click.Choice(["create", "drop", "upgrade", "downgrade", "revision"]))
@click.option("--settings-module", "-s", default=defaults.SETTINGS_MODULE, help="Fullpath to settings module")
def dbcli(action, message, rev_id, to, head, branch_label, name, depends_on, settings_module):
    """Create or Drop tables from a database"""
    settings = conf.load_conf(settings_module)
    db = SQL(settings.SQL)
    if action == "create":
        db.create_all()
        click.echo("Created...")
    elif action == "drop":
        db.drop_all()
        click.echo("Droped...")
    elif action == "upgrade":
        m = Migration(settings.SQL,
                      section=name,
                      alembic_file="alembic.ini")
        m.upgrade(
            to=to
        )

    elif action == "downgrade":
        m = Migration(settings.SQL,
                      section=name,
                      alembic_file="alembic.ini")

        m.downgrade(
            to=to
        )

    elif action == "revision":
        m = Migration(settings.SQL,
                      section=name,
                      alembic_file="alembic.ini")

        m.revision(
            rev_id=rev_id,
            message=message,
            head=head,
            branch_label=branch_label,
            depends_on=depends_on,
            autogenerate=True)
    else:
        console.print("[red bold]Wrong param...[/]")


@managercli.command(name="users")
@click.option("--settings-module", "-s", default=defaults.SETTINGS_MODULE, help="Fullpath to settings module")
@click.option("--is-superuser", "-S", default=False, help="Is a superuser")
@click.option("--scopes", "-C", default="user:r:w", help="Scopes for the user")
@click.argument("action", type=click.Choice(["create", "disable", "reset"]))
def userscli(action, is_superuser, scopes, settings_module):
    """Create a user"""

    settings = conf.load_conf(settings_module)
    if action == "create":
        name = Prompt.ask("Username")
        password = getpass("Password: ")
        repeat = getpass("Paswword (repeat): ")
        email = Prompt.ask("Email (optional)", default=None)
        if password != repeat:
            console.print("[bold red]Paswords doesn't match[/]")
            sys.exit(-1)

        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(create_user(
            settings, data={
                "username": name,
                "password": password,
                "email": email,
                "scopes": scopes,
                "is_superuser": is_superuser,
            }))
        if result:
            console.print(f"[bold magenta]Congrats!! user {name} created")
        else:
            console.print(f"[bold red]Something went wrong[/]")
            sys.exit(-1)

    # elif action == "reset":
    #     security = SecuritySettings()
    #     name = Prompt.ask("Username")
    #     _p = getpass("Password: ")
    #     with S() as session:
    #         changed = users_mg.change_pass(
    #             session, name, _p, salt=security.AUTH_SALT)
    #         session.commit()
    #     if changed:
    #         console.print("[bold magenta]Pasword changed[/]")
    #     else:
    #         console.print("[bold red]User may not exist [/]")
    # else:
    #     console.print("[red bold]Wrongs params[/]")
