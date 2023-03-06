import click
from services.db import AsyncSQL
from services.conf import load_conf
from services import defaults


@click.command(name="shell")
@click.option(
    "--settings-module",
    "-s",
    default=defaults.SETTINGS_MODULE,
    help="Fullpath to settings module",
)
def shell_cli(settings_module):
    """starts a IPython REPL console with db objects and models"""
    try:
        from IPython import start_ipython
    except ImportError:
        print("You need to install ipython:\n\t pip install ipython")

    settings = load_conf(settings_module)

    db = AsyncSQL(settings.DATABASES["default"])
    # S = db.sessionmaker()
    start_ipython(
        argv=[],
        user_ns={
            "settings": settings,
            # "Session": S,
            "db": db,
        },
    )
