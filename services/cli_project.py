import sys
from pathlib import Path
from secrets import token_urlsafe

import click
from rich.console import Console

from services import init_script

console = Console()


@click.command()
@click.option(
    "--vite/--no-vite",
    default=False,
    is_flag=True,
    show_default=True,
    help="Get support for Vite, HTML feature should be enabled",
)
@click.option(
    "--html/--no-html",
    default=False,
    is_flag=True,
    show_default=True,
    help="Add a index view example and templates",
)
@click.option(
    "--web/--no-web",
    default=True,
    is_flag=True,
    show_default=True,
    help="Add sanic web server",
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
@click.option(
    "--storage/--no-storage",
    default=False,
    is_flag=True,
    show_default=True,
    help="Add a default storage",
)
@click.option(
    "--name",
    default=None,
    help="Name of the project, if empty it will ask you for a name",
)
@click.argument("base_path")
def create_service_project(
    base_path, web, name, vite, html, users, tasks, sql, storage
):
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
        html=html,
        web=web,
    )
    print(opts)
    if opts.tasks and not opts.web:
        console.print("[red] To use tasks feature you should enable [cyan]web[/][/]")
        sys.exit(-1)
    if opts.vite_enabled and not opts.web:
        console.print("[red] To use vite feature you should enable [cyan]web[/][/]")
        sys.exit(-1)
    if opts.html and not opts.web:
        console.print("[red] To use html feature you should enable [cyan]web[/][/]")
        sys.exit(-1)
    init_script.create_project(opts)
