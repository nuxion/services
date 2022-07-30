from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from services import init_script


@click.command()
@click.option(
    "--create-dirs",
    "-C",
    is_flag=True,
    default=True,
    help="Create outpus and workflows dir",
)
@click.argument("base_path")
def startproject(create_dirs, base_path):
    root = Path(base_path).resolve()
    console = Console()

    p = Panel.fit(
        "[bold magenta]:smile_cat: Hello and welcome to "
        " AI services [/bold magenta]",
        border_style="red",
    )
    console.print(p)

    default_app = init_script.ask_webapp_name()
    init_script.create_default(root, default_app)
