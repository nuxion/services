import sys
from importlib import import_module
from pathlib import Path
from typing import Union

import click
from rich.console import Console

from services import conf, defaults

# from services.commands.common import create_app
# from services.commands.db import dbcli
# from services.commands.shell import shellcli
# from services.commands.users import userscli
# from services.commands.web import webcli


def get_command(fullname_path) -> Union[click.core.Command, click.core.Group]:
    module, class_ = fullname_path.rsplit(".", maxsplit=1)
    mod = import_module(module)
    cls = getattr(mod, class_)
    return cls


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

    # import_cli(cli)
    # import_cli_from_current(cli)
    cli.add_command(version)
    _conf = conf.load_conf(default_module=defaults.SETTINGS_MODULE)
    for cmd in _conf.COMMANDS:
        _cmd = get_command(cmd)
        cli.add_command(_cmd)

    return cli


cli = init_cli()

if __name__ == "__main__":
    cli()
