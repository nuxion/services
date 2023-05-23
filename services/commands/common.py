import sys
from pathlib import Path
from secrets import token_urlsafe

import click
from rich.console import Console

from services import init_script, workers

console = Console()


@click.command(name="create-app")
@click.option(
    "--html/--no-html",
    default=False,
    is_flag=True,
    show_default=True,
    help="Add templates and html view example",
)
@click.option(
    "--vite/--no-vite",
    default=False,
    is_flag=True,
    show_default=True,
    help="Get support for Vite. Html feature should be enabled",
)
@click.option(
    "--users/--no-users",
    default=False,
    is_flag=True,
    show_default=True,
    help="Provide the user system",
)
@click.option(
    "--tasks/--no-tasks",
    default=False,
    is_flag=True,
    show_default=True,
    help="Add a dummy task and the worker as example",
)
@click.option(
    "--sql/--no-sql",
    default=False,
    is_flag=True,
    show_default=True,
    help="Add DB related files",
)
@click.argument("appname")
def create_app_cli(appname, vite, tasks, users, sql, html):
    """Create the structure of an app"""
    root = Path.cwd()
    opts = init_script.ScriptOpts(
        base_path=root,
        secret_key=token_urlsafe(32),
        app_name=appname,
        users=users,
        vite_enabled=vite,
        tasks=tasks,
        sql=sql,
        html=html,
    )
    init_script.create_app(opts)
    console.print(f"[green bold]App {appname} created.[/]")
