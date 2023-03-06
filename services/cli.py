import sys
from importlib import import_module
from pathlib import Path

import click
from rich.console import Console

# from services.commands.common import create_app
# from services.commands.db import dbcli
# from services.commands.shell import shellcli
# from services.commands.users import userscli
# from services.commands.web import webcli


def import_cli(cli_app, package_dir="services.commands"):
    mod = import_module(package_dir)
    for el in dir(mod):
        if el.endswith("_cli"):
            cmd = getattr(mod, el)
            cli_app.add_command(cmd)


def from_path_to_module_str(fp) -> str:
    """experimental:
    from "examples/model.py" it should return
    "example.model"
    """
    return fp.rsplit(".", maxsplit=1)[0].replace("/", ".")


def import_cli_from_current(cli_app):
    sys.path.append(str(Path(".")))
    for path in Path(".").rglob("commands/*.py"):
        if path.is_file():
            if str(path).split("/")[1] == "commands":
                _module = from_path_to_module_str(str(path))
                # mod = import_module(_module)
                import_cli(cli_app, _module)


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

        ver = get_version()
        console.print(f"[bold magenta]{ver}[/bold magenta]")

    # cli.add_command(version)
    # cli.add_command(webcli)
    # cli.add_command(userscli)
    # cli.add_command(dbcli)
    # cli.add_command(create_app)
    # cli.add_command(shellcli)
    import_cli(cli)
    import_cli_from_current(cli)
    return cli


cli = init_cli()

if __name__ == "__main__":
    cli()
