import asyncio
import sys
from getpass import getpass
from typing import Union

import click
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from services import conf, defaults, errors, types
from services.db.sqlhelper import AsyncSQL

from ..managers import GroupManager, UserManager
from ..users_models import GroupModel, UserModel

console = Console()
loop = asyncio.get_event_loop()


def get_user_manager(settings: types.Settings) -> UserManager:
    # auth = auth_from_settings(settings.SECURITY)
    gm = GroupManager()
    um = UserManager(salt=settings.SECURITY2.secret_key, groups=gm)

    return um


def get_db(settings: types.Settings):
    db = AsyncSQL.from_conf(settings.DATABASES[settings.USER_DB])
    return db


async def _create_group(
    settings: types.Settings, group_name
) -> Union[GroupModel, None]:
    db = get_db(settings)
    manager = get_user_manager(settings)
    async with db.session() as session:
        group = await manager.create_group(session, group_name)
    # await db.dispose()
    return group


async def _create_user(settings: types.Settings, data, group) -> Union[UserModel, None]:
    db = get_db(settings)
    manager = get_user_manager(settings)
    try:
        async with db.session() as session:
            user = await manager.register(session, data, default_group=group)
    except errors.GroupNotFound as e:
        console.print(f"[bold red]{e}[/]")
        return None

    return user


async def _delete_user(settings: types.Settings, username, hard=False):
    db = get_db(settings)
    manager = get_user_manager(settings)
    async with db.session() as session:
        await manager.delete(session, username, hard)
        await session.commit()


async def _list_users(settings: types.Settings, is_active=True):
    db = get_db(settings)
    manager = get_user_manager(settings)
    async with db.session() as session:
        users = await manager.list(session, is_active=is_active)
    return users


@click.group(name="users")
def users_cli():
    """
    administration of users
    """
    pass


@users_cli.command(name="create")
@click.option(
    "--settings-module",
    "-s",
    default=defaults.SETTINGS_MODULE,
    help="Fullpath to settings module",
)
@click.option(
    "--is-superuser", "-S", default=False, is_flag=True, help="Is a superuser"
)
@click.option("--group", "-g", default="users", help="Group which belongs")
@click.option(
    "--create-group", default=True, is_flag=True, help="Creates group if not exist"
)
@click.option("--scopes", "-C", default="user:r:w", help="Scopes for the user")
def user_create(settings_module, is_superuser, scopes, group, create_group):
    settings = conf.load_conf(settings_module)
    name = Prompt.ask("Username")
    password = getpass("Password: ")
    repeat = getpass("Paswword (repeat): ")
    email = Prompt.ask("Email (optional)", default=None)
    if password != repeat:
        console.print("[bold red]Paswords doesn't match[/]")
        sys.exit(-1)
    if create_group:
        group_res = loop.run_until_complete(
            _create_group(
                settings,
                group,
            )
        )
        if group_res:
            console.print(f"Group: {group} created")

    result = loop.run_until_complete(
        _create_user(
            settings,
            data={
                "username": name,
                "password": password,
                "email": email,
                "scopes": scopes,
                "is_superuser": is_superuser,
            },
            group=group,
        )
    )
    if result:
        console.print(f"[bold magenta]Congrats!! user {name} created")
    else:
        sys.exit(-1)


@users_cli.command(name="delete")
@click.option(
    "--settings-module",
    "-s",
    default=defaults.SETTINGS_MODULE,
    help="Fullpath to settings module",
)
@click.option("--hard", default=False, is_flag=True, help="Hard delete of the user")
@click.argument("username")
def user_delete(settings_module, hard, username):
    settings = conf.load_conf(settings_module)
    loop.run_until_complete(_delete_user(settings, username, hard=hard))
    console.print(f"[bold magenta]User {username} deleted")


@users_cli.command(name="list")
@click.option(
    "--settings-module",
    "-s",
    default=defaults.SETTINGS_MODULE,
    help="Fullpath to settings module",
)
def users_list(settings_module):
    settings = conf.load_conf(settings_module)

    result = loop.run_until_complete(_list_users(settings))
    table = Table(title="List of users")
    table.add_column("id")
    table.add_column("username")
    table.add_column("scopes")
    table.add_column("email")
    table.add_column("is_superuser")
    table.add_column("created at")

    for user in result:
        table.add_row(
            f"{user.id}",
            user.username,
            user.scopes,
            f"{user.email}",
            f"{user.is_superuser}",
            f"{user.created_at}",
        )

    console.print(table)