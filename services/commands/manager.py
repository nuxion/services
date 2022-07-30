import importlib
import os
import shutil
import subprocess
import sys
from getpass import getpass
from pathlib import Path

import click
from rich.console import Console
from rich.prompt import Confirm, Prompt

from services import conf, init_script, types
from services.base import MigrationSpec
from services.db import SQL
from services.db.migration import Migration
from services.utils import execute_cmd, get_class, mkdir_p

console = Console()


@click.group(name="manager")
def managercli():
    """
    Managment tasks like user creation and db init
    """
    pass


@managercli.command(name="db")
# @click.option("--database", "-d", default="default", help="Database to apply migration")
@click.option("--message", "-m", default=None, help="Revision name")
@click.option("--rev-id", "-R", help="Revision id")
@click.option("--to", "-t", default="head", help="Revision to upgrade or downgrade")
@click.option("--head", default=None, help="Specify head revision or <branchname>@head to base new revision.")
@click.option("--branch-label", "-b", default=None, help="Specify a branch label to apply to the new revision")
@click.option("--name", "-n", default=None, help="package name where migration should be located")
@click.option("--depends-on", "-d", help="list of 'depends on' identifiers")
@click.argument("action", type=click.Choice(["create", "drop", "upgrade", "downgrade", "revision"]))
def dbcli(action, message, rev_id, to, head, branch_label, name, depends_on):
    """Create or Drop tables from a database"""
    settings = conf.load_conf()
    db = SQL(settings.SQL)
    if name:
        m_conf: MigrationSpec = get_class(f"{name}.migrate.Migrate")
        modelds = importlib.import_module(f"{m_conf.package_dir}.models")
    if action == "create":
        db.create_all()
        click.echo("Created...")
    elif action == "drop":
        db.drop_all()
        click.echo("Droped...")
    elif action == "upgrade":
        m_conf: MigrationSpec = get_class(f"{name}.migrate.Migrate")
        m = Migration(settings.SQL,
                      package_dir=m_conf.package_dir,
                      version_table=m_conf.version_table,
                      )
        m.upgrade(
            to=to
        )

    elif action == "downgrade":
        m_conf: MigrationSpec = get_class(f"{name}.migrate.Migrate")
        m = Migration(settings.SQL,
                      package_dir=m_conf.package_dir,
                      version_table=m_conf.version_table,
                      )
        m.downgrade(
            to=to
        )

    elif action == "revision":
        m_conf: MigrationSpec = get_class(f"{name}.migrate.Migrate")
        m = Migration(settings.SQL,
                      package_dir=m_conf.package_dir,
                      version_table=m_conf.version_table,
                      )
        m.revision(
            rev_id=rev_id,
            message=message,
            head=head,
            branch_label=branch_label,
            depends_on=depends_on,
            autogenerate=True)
    else:
        console.print("[red bold]Wrong param...[/]")


@managercli.command(name="create-app")
@click.argument("appname")
def create_app(appname):
    """Create the structure of an app"""
    root = Path.cwd()
    init_script.create_app(root, appname)
    console.print(f"[green bold]App {appname} created.[/]")


@managercli.command(name="users")
# @click.option("--sql", "-s", default=settings.SQL, help="SQL Database")
@click.option("--is-superuser", "-S", default=False, help="Is a superuser")
@click.option("--scopes", "-C", default="user:r:w", help="Is a superuser")
@click.argument("action", type=click.Choice(["create", "disable", "reset"]))
def userscli(action, is_superuser, scopes):
    """Create a user"""
    from services.security import users_mg
    from services.security.types import SecuritySettings, UserOrm

    settings = conf.load_conf()
    db = SQL(settings.SQL)
    S = db.sessionmaker()

    if action == "create":
        security = SecuritySettings()
        name = Prompt.ask("Username")
        password = getpass("Password: ")
        repeat = getpass("Paswword (repeat): ")
        email = Prompt.ask("Email (optional)", default=None)
        if password != repeat:
            console.print("[bold red]Paswords doesn't match[/]")
            sys.exit(-1)
        key = users_mg.encrypt_password(password, salt=security.AUTH_SALT)
        with S() as session:
            obj = UserOrm(
                username=name,
                password=key,
                email=email,
                scopes=scopes,
                is_superuser=is_superuser
            )
            user = users_mg.create(session, obj)
            session.commit()
        console.print(f"[bold magenta]Congrats!! user {name} created")

    elif action == "reset":
        security = SecuritySettings()
        name = Prompt.ask("Username")
        _p = getpass("Password: ")
        with S() as session:
            changed = users_mg.change_pass(
                session, name, _p, salt=security.AUTH_SALT)
            session.commit()
        if changed:
            console.print("[bold magenta]Pasword changed[/]")
        else:
            console.print("[bold red]User may not exist [/]")
    else:
        console.print("[red bold]Wrongs params[/]")
