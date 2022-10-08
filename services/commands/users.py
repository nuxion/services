import asyncio
import sys
from getpass import getpass
from typing import List

import click
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from services import conf, defaults, types
from services.db.sqlhelper import AsyncSQL
from services.security.authentication import auth_from_settings
from services.users import UserSpec
from services.users.managers import UserManager

console = Console()
loop = asyncio.get_event_loop()


def get_user_manager(settings: types.Settings) -> UserManager:
    db = AsyncSQL(settings.DATABASES[settings.USER_DB])
    auth = auth_from_settings(settings.SECURITY)
    # session = db.sessionmaker()
    manager = UserManager(auth, db=db, model_class=settings.USER_MODEL,
                          salt=settings.SECURITY.AUTH_SALT)
    return manager


async def _create_user(settings: types.Settings, data):
    manager = get_user_manager(settings)
    await manager.db.init()
    user = await manager.register(data)
    return user


async def _list_users(settings: types.Settings, active=True) -> List[UserSpec]:
    manager = get_user_manager(settings)
    await manager.db.init()
    users = await manager.list_users(active)
    return users


@click.group(name="users")
def userscli():
    """
    administration of users
    """
    pass


@userscli.command(name="create")
@click.option("--settings-module", "-s", default=defaults.SETTINGS_MODULE,
              help="Fullpath to settings module")
@click.option("--is-superuser", "-S", default=False, help="Is a superuser")
@click.option("--scopes", "-C", default="user:r:w", help="Scopes for the user")
def user_create(settings_module, is_superuser, scopes):
    settings = conf.load_conf(settings_module)
    name = Prompt.ask("Username")
    password = getpass("Password: ")
    repeat = getpass("Paswword (repeat): ")
    email = Prompt.ask("Email (optional)", default=None)
    if password != repeat:
        console.print("[bold red]Paswords doesn't match[/]")
        sys.exit(-1)
    result = loop.run_until_complete(_create_user(
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


@userscli.command(name="list")
@click.option("--settings-module", "-s", default=defaults.SETTINGS_MODULE,
              help="Fullpath to settings module")
def users_list(settings_module):
    settings = conf.load_conf(settings_module)

    result = loop.run_until_complete(_list_users(
        settings))
    table = Table(title="List of users")
    table.add_column("id")
    table.add_column("username")
    table.add_column("scopes")
    table.add_column("email")
    table.add_column("is_superuser")
    table.add_column("created at")

    for user in result:
        table.add_row(f"{user.id}",
                      user.username,
                      ",".join(user.scopes),
                      f"{user.email}",
                      f"{user.is_superuser}",
                      f"{user.create_at}")

    console.print(table)
