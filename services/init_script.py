import shutil

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from services.jt import render_to_file
from services.utils import (get_package_dir, get_parent_folder, mkdir_p,
                            normalize_name)

console = Console()
FOLDERS = [
    "server_conf",
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
    console.print("\t[bold] srv web -L[/]\n")


def create_default(root, default_app, vite_enabled):
    """
    Entrypoint when calling `srv startproject .`
    It will creates all the neccesary for a project to start
    """

    data = {"app_name": default_app, "vite_enabled": vite_enabled}
    for f in FOLDERS:
        mkdir_p(f)

    _empty_file(f"{root}/server_conf/__init__.py")
    render_to_file(
        template="settings.py", dst=f"{root}/server_conf/settings.py", data=data
    )
    render_to_file(template="app/alembic.ini", dst=f"{root}/alembic.ini")
    create_app(root, default_app, init=True, vite_enabled=vite_enabled)

    final_words(default_app)


def alembic_files(root, app_name):
    # alembic specific
    dst = f"{root}/{app_name}"
    mkdir_p(f"{dst}/migrations/versions")
    data = {"app_name": app_name}

    render_to_file(template="alembic/env.py", dst=f"{dst}/migrations/env.py", data=data)
    render_to_file(
        template="alembic/script.py.mako", dst=f"{dst}/migrations/script.py.mako"
    )
    with open(f"{root}/alembic.ini", "a", encoding="utf-8") as f:
        f.write(
            (
                "\n\n"
                f"[{app_name}]\n"
                "sqlalchemy.url = \n"
                f"script_location = %(here)s/{app_name}/migrations/\n"
                f"models_module = {app_name}.models\n"
                f"version_table = { app_name }_version\n"
                f"db_name = default\n"
            )
        )


def create_app(root, app_name, init=False, vite_enabled=False):
    dst = f"{root}/{app_name}"
    mkdir_p(f"{dst}/api")
    mkdir_p(f"{dst}/templates")

    data = {"app_name": app_name, "init": init}
    # creates and generates app's package files
    _empty_file(f"{dst}/__init__.py")
    render_to_file(template="app/web.py", dst=f"{dst}/web.py", data=data)
    render_to_file(template="app/api_bp.py", dst=f"{dst}/api/{app_name}.py", data=data)
    render_to_file(template="app/views.py", dst=f"{dst}/views.py", data=data)
    render_to_file(template="app/models.py", dst=f"{dst}/models.py", data=data)
    render_to_file(template="app/db.py", dst=f"{dst}/db.py", data=data)
    shutil.copy(
        f"{get_package_dir('services')}/files/index.html",
        f"{root}/{app_name}/templates/index.html",
    )
    if vite_enabled:
        shutil.copy(
            f"{get_package_dir('services')}/files/_layout.vite.html",
            f"{root}/{app_name}/templates/_layout.html",
        )
    else:
        shutil.copy(
            f"{get_package_dir('services')}/files/_layout.default.html",
            f"{root}/{app_name}/templates/_layout.html",
        )

    if init:
        render_to_file(template="app/users_bp.py", dst=f"{dst}/api/users.py", data=data)

    alembic_files(root, app_name)
