from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from services import init_script

console = Console()


@click.command()
@click.argument("base_path")
def create_service_project(base_path):
    """ Start a new project """
    root = Path(base_path).resolve()

    p = Panel.fit(
        "[bold magenta]:smile_cat: Hello and welcome to "
        " AI services [/bold magenta]",
        border_style="red",
    )
    console.print(p)

    default_app = init_script.ask_webapp_name()
    init_script.create_default(root, default_app)
