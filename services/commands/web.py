import os

import click
from services import defaults


@click.command(name="web")
@click.option("--host", "-H", default="127.0.0.1", help="Listening Host")
@click.option("--port", "-p", default="8000", help="Listening Port")
@click.option("--workers", "-w", default=1, help="How many workers start?")
@click.option(
    "--reload", "-r", default=False, is_flag=True, help="Enable Auto reload"
)
@click.option(
    "--access-log", "-L", default=False, is_flag=True, help="Enable access_log"
)
@click.option("--debug", "-D", default=False, is_flag=True, help="Enable Auto reload")
@click.option("--settings-module", "-s", default=defaults.SETTINGS_MODULE,
              help="Fullpath to settings module")
def webcli(host, port, workers, reload, access_log, debug, settings_module):
    """Run Web Server"""
    # pylint: disable=import-outside-toplevel
    from services.conf import load_conf
    from services.server import create_srv

    # from playpy.web import sanic_init_indexer
    # from playpy.types import Settings as PlaySettings
    pwd = os.getcwd()


    settings = load_conf(settings_module)

    host = host or settings.HOST
    port = port or settings.PORT
    w = int(workers)

    print(f"BASE_PATH: {settings.BASE_PATH}")
    print(f"SETTINGS_MODULE: {settings.SETTINGS_MODULE}")
    print(f"Debug mode: {debug}")
    print(f"Access log: {access_log}")
    print(f"Autoreload: {reload}")
    print(f"Workers: {w}")
    print(f"Listening: {host}:{port}")

    srv = create_srv(settings)
    srv.run(
        host=host,
        port=int(port),
        access_log=access_log,
        workers=w,
        debug=debug,
        auto_reload=reload,
    )
