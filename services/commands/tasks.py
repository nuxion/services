import os
import sys
from functools import partial
from typing import List

import click
from rich.console import Console
from rich.table import Table

from services import conf, defaults, types, workers, utils

console = Console()


async def _list_tasks(backend: types.TasksBackend) -> List[workers.Task]:
    back = await workers.init_backend(backend)
    tasks = await back.list_tasks()
    return tasks


async def _failed(backend: types.TasksBackend) -> List[str]:
    back = await workers.init_backend(backend)
    tasks = await back.clean_failed()
    return tasks


async def _delete(backend: types.TasksBackend, taskid: str):
    back = await workers.init_backend(backend)
    await back.delete_task(taskid)


async def _clean(backend: types.TasksBackend):
    back = await workers.init_backend(backend)
    await back.clean()


@click.group(name="tasks")
def tasks_cli():
    """
    Run list and configure tasks
    """
    pass


@tasks_cli.command(name="run")
@click.argument("taskname")
@click.option("--param", "-p", multiple=True, help="define a param as <key>=<value>")
@click.option("--param-from-json", "-j", help="load params from a json file")
@click.option("--param-from-yaml", "-y", help="load params from a yaml file")
@click.option("--timeout", "-t", default=60, help="timeout for the task")
@click.option("--worker-type", "-w", default="io", type=click.Choice(["io", "cpu"]))
@click.option("--package", required=True)
# @click.option("--backend-uri", "-u", default=None)
# @click.option("--backend-class", default="services.ext.sql.workers.SQLBackend")
@click.option(
    "--settings-module",
    "-s",
    default=defaults.SETTINGS_MODULE,
    help="Fullpath to settings module",
)
def run_cli(
    taskname,
    param,
    worker_type,
    timeout,
    package,
    param_from_json,
    param_from_yaml,
    settings_module,
    # backend_uri,
    # backend_class,
):
    """Run a task"""

    settings = conf.load_conf(settings_module)
    if param_from_json:
        console.print("[red bold]json file params is not implemented yet[/]")
        sys.exit(-1)
    if param_from_yaml:
        console.print("[red bold]yaml file params is not implemented yet[/]")
        sys.exit(-1)
    qconf = workers.QueueConfig(app_name=package, backend=settings.TASKS)

    params = {}
    for p in param:
        k, v = p.split("=")
        params[k] = v

    task = workers.Task(name=taskname, timeout=timeout, params=params)
    if worker_type == "io":
        workers.standalone_io_worker(qconf, task)
    else:
        workers.standalone_cpu_worker(qconf, task)


@tasks_cli.command(name="list")
@click.option(
    "--settings-module",
    "-s",
    default=defaults.SETTINGS_MODULE,
    help="Fullpath to settings module",
)
def list_tasks(settings_module):
    """List tasks"""
    settings = conf.load_conf(settings_module)
    if not settings.TASKS:
        console.print("[red bold]Not tasks backend configurated[/]")
        sys.exit(-1)

    table = Table(title="List of tasks")
    table.add_column("id")
    table.add_column("name")
    table.add_column("app_name")
    table.add_column("state")
    table.add_column("elapsed")

    tasks: List[workers.Task] = utils.from_sync2async(_list_tasks, settings.TASKS)
    for t in tasks:
        elapsed = round((t.updated_at - t.created_at).total_seconds())
        if elapsed > 120:
            elapsed = f"~{round(elapsed / 60)}m"
        else:
            elapsed = f"{elapsed}s"

        table.add_row(
            f"{t.id}",
            f"{t.name}",
            f"{t.app_name}",
            f"{t.state}",
            f"{elapsed}",
        )
    console.print(table)


@tasks_cli.command(name="clean-failed")
@click.option(
    "--settings-module",
    "-s",
    default=defaults.SETTINGS_MODULE,
    help="Fullpath to settings module",
)
def clean_failed_tasks(settings_module):
    """Remove tasks in failed state"""
    settings = conf.load_conf(settings_module)
    if not settings.TASKS:
        console.print("[red bold]Not tasks backend configurated[/]")
        sys.exit(-1)

    tasks = utils.from_sync2async(_failed, settings.TASKS)
    for t in tasks:
        console.print(f"[red]=> {t} removed[/]")
    console.print(f"\n [bold]{len(tasks)}[/bold] failed tasks removed.")


@tasks_cli.command(name="delete")
@click.option(
    "--settings-module",
    "-s",
    default=defaults.SETTINGS_MODULE,
    help="Fullpath to settings module",
)
@click.argument("taskid")
def delete_task(settings_module, taskid):
    """Remove a tasks by taksid"""
    settings = conf.load_conf(settings_module)
    if not settings.TASKS:
        console.print("[red bold]Not tasks backend configurated[/]")
        sys.exit(-1)

    utils.from_sync2async(_delete, settings.TASKS, taskid)
    console.print(f"[red]=> {taskid} removed[/]")


@tasks_cli.command(name="clean")
@click.option(
    "--settings-module",
    "-s",
    default=defaults.SETTINGS_MODULE,
    help="Fullpath to settings module",
)
def clean_tasks(settings_module):
    """Clean tasks done"""
    settings = conf.load_conf(settings_module)
    if not settings.TASKS:
        console.print("[red bold]Not tasks backend configurated[/]")
        sys.exit(-1)

    utils.from_sync2async(_clean, settings.TASKS)
    console.print(f"[green]=> Tasks cleaned[/]")
