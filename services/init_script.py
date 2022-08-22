from rich.console import Console
from rich.prompt import Confirm, Prompt

from services.jtemplates import render_to_file
from services.utils import get_parent_folder, mkdir_p, normalize_name
from rich.panel import Panel
console = Console()
FOLDERS = [
    "server_conf",
]

APP_FOLDERS = [
    "migrations"
]

APP_FILES = [
    {"tpl": "alembic.ini", "dst": "migrations/alembic.ini"},
    {"tpl": "__init__.py", "dst": "__init__.py"},
    {"tpl": "web.py", "dst": "web.py"},
    {"tpl": "models.py", "dst": "models.py"},
    {"tpl": "views_bp.py", "dst": "views_bp.py"},
]


def _empty_file(filename):
    with open(filename, "w", encoding="utf-8") as f:
        pass
    return True


def ask_webapp_name() -> str:
    parent = get_parent_folder()
    _default = normalize_name(parent)
    project_name = Prompt.ask(
        f"Write a name for default web app [yellow]please, avoid spaces and capital "
        "letters[/yellow]: ",
        default=_default,
    )
    name = normalize_name(project_name)
    console.print(
        f"The final name for the project is: [bold magenta]{name}[/bold magenta]"
    )
    return name


def final_words(project_name):
    p = Panel.fit(
        "[bold magenta]:smile_cat: Congrats!!!"
        f" Project [cyan]{project_name}[/cyan] created[/bold magenta]",
        border_style="red",
    )
    console.print(p)

    console.print(
        " [bold magenta]To test if everything is working "
        " you can run the following command:[/]\n"
    )
    console.print("\t[bold] srv web -L -D[/]")


def create_default(root, default_app):

    data = {"app_name": default_app}
    for f in FOLDERS:
        mkdir_p(f)

    _empty_file(f"{root}/server_conf/__init__.py")
    render_to_file(template="settings.py",
                   dst=f"{root}/server_conf/settings.py",
                   data=data)
    render_to_file(template="app/alembic.ini", dst=f"{root}/alembic.ini")
    create_app(root, default_app)

    final_words(default_app)


def create_app(root, app_name):
    dst = f"{root}/{app_name}"
    mkdir_p(dst)
    data = {"app_name": app_name}
    _empty_file(f"{dst}/__init__.py")
    render_to_file(template="app/web.py", dst=f"{dst}/web.py", data=data)
    render_to_file(template="app/views_bp.py",
                   dst=f"{dst}/views_bp.py", data=data)
    render_to_file(template="app/models.py", dst=f"{dst}/models.py", data=data)
    #render_to_file(template="app/migrate.py",
    #               dst=f"{dst}/migrate.py", data=data)

    mkdir_p(f"{dst}/migrations/versions")
    render_to_file(template="alembic/env.py",
                   dst=f"{dst}/migrations/env.py",
                   data=data)
    render_to_file(template="alembic/script.py.mako",
                   dst=f"{dst}/migrations/script.py.mako")
    with open(f"{root}/alembic.ini", "a", encoding="utf-8") as f:
        f.write((
            "\n\n"
            f"[{app_name}]\n"
            "sqlalchemy.url = \n"
            f"script_location = %(here)s/{app_name}/migrations/\n"
            f"models_module = {app_name}.models\n"
            f"version_table = { app_name }_version\n"
        ))
