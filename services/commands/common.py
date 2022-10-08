from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from services import init_script

console = Console()


@click.command(name="create-app")
@click.argument("appname")
def create_app(appname):
    """Create the structure of an app"""
    root = Path.cwd()
    init_script.create_app(root, appname)
    console.print(f"[green bold]App {appname} created.[/]")
