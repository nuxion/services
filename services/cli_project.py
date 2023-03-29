from pathlib import Path

import click
from rich.console import Console
from secrets import token_urlsafe

from services import init_script

console = Console()


@click.command()
@click.option(
    "--vite",
    default=False,
    is_flag=True,
    show_default=True,
    help="Get support for Vite",
)
@click.option(
    "--users",
    default=False,
    is_flag=True,
    show_default=True,
    help="Provide the user system",
)
@click.option(
    "--tasks",
    default=False,
    is_flag=True,
    show_default=True,
    help="Add a dummy task and the worker as example",
)
@click.option(
    "--sql",
    default=True,
    is_flag=True,
    show_default=True,
    help="Add DB related files",
)
@click.option(
    "--storage",
    default=False,
    is_flag=True,
    show_default=True,
    help="Add default storage",
)
@click.option(
    "--name",
    default=None,
    help="Name of the project, if empty it will ask you for a name",
)
@click.argument("base_path")
def create_service_project(base_path, name, vite, users, tasks, sql, storage):
    """Start a new project"""
    root = Path(base_path).resolve()
    opts = init_script.ScriptOpts(
        base_path=root,
        secret_key=token_urlsafe(32),
        app_name=name,
        users=users,
        vite_enabled=vite,
        tasks=tasks,
        sql=sql,
        storage=storage,
    )
    print(opts)

    init_script.create_project(opts)
