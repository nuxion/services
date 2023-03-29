import shutil
from pathlib import Path
from typing import Optional

from pydantic import BaseModel
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from services.jt import render_to_file
from services.utils import get_package_dir, get_parent_folder, mkdir_p, normalize_name
from services.errors import CommandExecutionException


class ScriptOpts(BaseModel):
    base_path: Path
    secret_key: str
    app_name: Optional[str] = None
    vite_enabled: bool = False
    users: bool = True
    tasks: bool = False
    storage: bool = False
    sql: bool = True


console = Console()


def _welcome_message():
    p = Panel.fit(
        "[bold magenta]:smile_cat: Hello and welcome to "
        " AI services [/bold magenta]",
        border_style="red",
    )
    console.print(p)


def _empty_file(filename):
    with open(filename, "w", encoding="utf-8") as f:
        pass
    return True


def ask_webapp_name(project_name: Optional[str] = None) -> str:
    if not project_name:
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


def final_words(opts: ScriptOpts):
    p = Panel.fit(
        "[bold magenta]:smile_cat: Congrats!!!"
        f" Project [cyan]{opts.app_name}[/cyan] created[/bold magenta]",
        border_style="red",
    )
    console.print(p)

    console.print(
        " [bold magenta]To test if everything is working "
        " you can run the following command:[/]\n"
    )
    console.print("\t[bold] srv web -L[/]\n")

    if opts.vite_enabled:
        console.print(
            " To start using Vite, you can init the svelte template, into the front folder: \n"
        )
        console.print(
            "\t[bold]degit https://github.com/nuxion/services-front-svelte front[/]\n"
        )


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


def create_app(opts: ScriptOpts):
    """
    It creates an app. Similar to django apps.
    """
    dst = f"{opts.base_path}/{opts.app_name}"
    mkdir_p(f"{dst}/api")
    mkdir_p(f"{dst}/templates")
    mkdir_p(f"{dst}/commands")

    data = opts.dict()
    # creates and generates app's package files
    _empty_file(f"{dst}/__init__.py")
    render_to_file(template="app/web.py", dst=f"{dst}/web.py", data=data)
    render_to_file(
        template="app/api_bp.py", dst=f"{dst}/api/{opts.app_name}.py", data=data
    )
    render_to_file(template="app/views.py", dst=f"{dst}/views.py", data=data)

    shutil.copy(
        f"{get_package_dir('services')}/files/index.html",
        f"{opts.base_path}/{opts.app_name}/templates/index.html",
    )
    if opts.vite_enabled:
        shutil.copy(
            f"{get_package_dir('services')}/files/_layout.vite.html",
            f"{opts.base_path}/{opts.app_name}/templates/_layout.html",
        )
    else:
        shutil.copy(
            f"{get_package_dir('services')}/files/_layout.default.html",
            f"{opts.base_path}/{opts.app_name}/templates/_layout.html",
        )

    if opts.sql:
        add_sql_files(opts)

    if opts.tasks:
        render_to_file(template="app/tasks.py", dst=f"{dst}/tasks.py", data=data)

    if opts.users and opts.sql:
        users_feature(opts)
    elif opts.users and not opts.sql:
        raise CommandExecutionException(
            "To use the users feature you have to enable the sql feature."
        )


def users_feature(opts: ScriptOpts):
    dst = f"{opts.base_path}/{opts.app_name}"
    data = opts.dict()
    render_to_file(template="app/users_bp.py", dst=f"{dst}/api/users.py", data=data)
    render_to_file(
        template="app/users_models.py", dst=f"{dst}/users_models.py", data=data
    )

    render_to_file(template="app/managers.py", dst=f"{dst}/managers.py", data=data)
    render_to_file(
        template="app/commands/users.py", dst=f"{dst}/commands/users.py", data=data
    )

    shutil.copy(
        f"{get_package_dir('services')}/files/login.html",
        f"{opts.base_path}/{opts.app_name}/templates/login.html",
    )


def create_settings(opts: ScriptOpts):
    mkdir_p(f"{opts.base_path}/server_conf")
    _empty_file(f"{opts.base_path}/server_conf/__init__.py")
    render_to_file(
        template="settings.py",
        dst=f"{opts.base_path}/server_conf/settings.py",
        data=opts.dict(),
    )


def add_command(name, opts: ScriptOpts):
    dst = f"{opts.base_path}/{opts.app_name}"
    data = opts.dict()
    render_to_file(
        template=f"app/commands/{name}.py", dst=f"{dst}/commands/{name}.py", data=data
    )


def add_sql_files(opts: ScriptOpts):
    dst = f"{opts.base_path}/{opts.app_name}"
    data = opts.dict()

    if not Path(f"{opts.base_path}/alembic.ini").is_file():
        render_to_file(template="app/alembic.ini", dst=f"{opts.base_path}/alembic.ini")
    render_to_file(template="app/models.py", dst=f"{dst}/models.py", data=data)
    render_to_file(template="app/db.py", dst=f"{dst}/db.py", data=data)
    alembic_files(str(opts.base_path), opts.app_name)


def create_project(opts: ScriptOpts):
    """
    Entrypoint when calling `srv startproject .`
    It will creates all the neccesary for a project to start
    """

    _welcome_message()

    default_app = ask_webapp_name(opts.app_name)
    opts.app_name = default_app

    if not Path(f"{opts.base_path}/server_conf").is_dir():
        create_settings(opts)

    if opts.sql:
        render_to_file(template="app/alembic.ini", dst=f"{opts.base_path}/alembic.ini")

    create_app(opts)

    add_command("shell", opts)

    final_words(opts)
