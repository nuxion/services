import os

import click
from rich.console import Console

console = Console()


@click.command(name="web")
@click.option("--host", "-H", default="0.0.0.0", help="Listening Host")
@click.option("--port", "-p", default="8000", help="Listening Port")
@click.option("--workers", "-w", default=1, help="How many workers start?")
@click.option(
    "--services",
    "-s",
    default=None,
    help="List of services to enable",
)
@click.option(
    "--auto-reload", "-A", default=False, is_flag=True, help="Enable Auto reload"
)
@click.option(
    "--access-log", "-L", default=False, is_flag=True, help="Enable access_log"
)
@click.option(
    "--with-auth-bp", "-E", default=True, is_flag=True, help="Enable authentication endpoints"
)
@click.option("--debug", "-D", default=False, is_flag=True, help="Enable Auto reload")
def webcli(host, port, workers, services, auto_reload, access_log, debug,
           with_auth_bp):
    """Run Web Server"""
    # pylint: disable=import-outside-toplevel
    from services.server import create_app
    from services.types import Settings
    from playpy.web import sanic_init_indexer
    from playpy.types import Settings as PlaySettings

    pwd = os.getcwd()
    settings = Settings(BASE_PATH=pwd)

    host = host or settings.HOST
    port = port or settings.PORT

    console.print(f"BASE_PATH: {settings.BASE_PATH}")
    console.print(f"Debug mode: {debug}")

    services_bp = None
    if services:
        services_bp = services.split(",")

    app = create_app(settings, list_bp=services_bp, package_dir="playpy")
    sett = PlaySettings(BASE_PATH=pwd)
    sanic_init_indexer(app, sett)
    w = int(workers)
    app.run(
        host=host,
        port=int(port),
        access_log=access_log,
        workers=w,
        debug=debug
    )
