import os

import click
from rich.console import Console

from services.commands.common import create_app
from services.commands.db import dbcli
from services.commands.web import webcli
from services.commands.users import userscli


def init_cli():

    console = Console()

    @click.group()
    def cli():
        """
        Command line tool
        """

    @click.command()
    def version():
        """Actual version"""
        from services.utils import get_version

        ver = get_version("__version__.py")
        console.print(f"[bold magenta]{ver}[/bold magenta]")

    cli.add_command(version)
    cli.add_command(webcli)
    cli.add_command(userscli)
    cli.add_command(dbcli)
    cli.add_command(create_app)
    return cli


cli = init_cli()

if __name__ == "__main__":

    cli()
