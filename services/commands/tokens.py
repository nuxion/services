import click
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from services import conf, defaults, errors, types, utils
from services.security import jwtauth
from services.security.memory_store import MemoryTokenStore

console = Console()


@click.group(name="tokens")
def tokens_cli():
    """
    Token generator
    """
    pass


@tokens_cli.command(name="generate")
@click.option(
    "--settings-module",
    "-s",
    default=defaults.SETTINGS_MODULE,
    help="Fullpath to settings module",
)
@click.option("--scopes", "-s", default="user:r:w", help="Scopes for the token")
@click.option("--exp", "-e", default=600, help="Expiration of the token")
@click.option("--username", "-u", default=None, help="Username")
def generate(settings_module, username, scopes, exp):
    settings = conf.load_conf(settings_module)
    custom = {"scopes": scopes}
    if username:
        custom.update({"usr": username})
    payload = types.JWTPayload(custom=custom, exp=exp)

    jwt = jwtauth.JWTAuth(settings.SECURITY)
    token = utils.from_sync2async(jwt.generate_token, payload)

    console.print(token.dict())


@tokens_cli.command(name="decode")
@click.option(
    "--settings-module",
    "-s",
    default=defaults.SETTINGS_MODULE,
    help="Fullpath to settings module",
)
@click.argument("token")
def decode(settings_module, token):
    settings = conf.load_conf(settings_module)
    jwt = jwtauth.JWTAuth(settings.SECURITY)
    decoded = jwt.decode(token)

    console.print(decoded)
