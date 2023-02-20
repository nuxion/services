from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from services import init_script

console = Console()


@click.command()
@click.option("--vite", default=False, is_flag=True, help="Get support for Vite")
@click.option("--users", default=False, is_flag=True, help="Provide the user system")
@click.option(
    "--name",
    default=None,
    help="Name of the project, if empty it will ask you for a name",
)
@click.argument("base_path")
def create_service_project(base_path, name, vite, users):
    """Start a new project"""
    root = Path(base_path).resolve()
    opts = init_script.ScriptOpts(
        base_path=root,
        app_name=name,
        users=users,
        vite_enabled=vite,
    )
    print(opts)

    init_script.create_project(opts)
