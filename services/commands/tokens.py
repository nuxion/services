import sys
from pathlib import Path

import click
from rich.console import Console

from services import conf, defaults, errors, types, utils
from services.security import jwtauth

# from services.security.memory_store import MemoryTokenStore

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
@click.option("--scopes", "-S", default="user:r:w", help="Scopes for the token")
@click.option("--exp", "-e", default=600, help="Expiration of the token")
@click.option("--username", "-u", default=None, help="Username")
def generate(settings_module, username, scopes, exp):
    """Generates a JWT token"""
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
    """Decodes a given token"""
    settings = conf.load_conf(settings_module)
    jwt = jwtauth.JWTAuth(settings.SECURITY)
    decoded = jwt.decode(token)

    console.print(decoded)


@tokens_cli.command(name="validate")
@click.option(
    "--settings-module",
    "-s",
    default=defaults.SETTINGS_MODULE,
    help="Fullpath to settings module",
)
@click.option("--scopes", "-S", default=None, help="Scopes for the token: user:r:w")
@click.argument("token")
def validate(settings_module, token, scopes):
    """Validates a given token"""
    settings = conf.load_conf(settings_module)
    jwt = jwtauth.JWTAuth(settings.SECURITY)
    try:
        _ = jwt.validate(token, required_scopes=scopes)
    except errors.AuthValidationFailed:
        console.print("[red bold]Invalid token[/]")
        sys.exit(-1)

    console.print("[green bold]Valid token[/]")


@tokens_cli.command(name="es512")
@click.argument("directory")
def es512(directory):
    """Generates the ES512 keys using openssl under the hood"""
    path = Path(directory)
    utils.mkdir_p(path)

    console.print(f">> private key into {path.resolve()}/private.key")
    utils.execute_cmd(
        f"openssl ecparam -name prime256v1 -genkey -out {path.resolve()}/private.key"
    )
    console.print(f">> public key into {path.resolve()}/public.key")
    try:
        utils.execute_cmd(
            f"openssl ec -in {path.resolve()}/private.key -pubout -out {path.resolve()}/public.key"
        )
    except errors.CommandExecutionException:
        pass
