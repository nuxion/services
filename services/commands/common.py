import sys
from pathlib import Path
from secrets import token_urlsafe

import click
from rich.console import Console

from services import init_script, workers

console = Console()


@click.command(name="create-app")
@click.option(
    "--vite",
    default=False,
    is_flag=True,
    show_default=True,
    help="Get support for Vite",
)
@click.option(
    "--users",
    default=False,
    is_flag=True,
    show_default=True,
    help="Provide the user system",
)
@click.option(
    "--tasks",
    default=False,
    is_flag=True,
    show_default=True,
    help="Add a dummy task and the worker as example",
)
@click.argument("appname")
def create_app_cli(appname, vite, tasks, users):
    """Create the structure of an app"""
    root = Path.cwd()
    opts = init_script.ScriptOpts(
        base_path=root,
        secret_key=token_urlsafe(32),
        app_name=appname,
        users=users,
        vite_enabled=vite,
        tasks=tasks,
    )
    init_script.create_app(opts)
    console.print(f"[green bold]App {appname} created.[/]")


@click.command(name="run")
@click.argument("taskname")
@click.option("--param", "-p", multiple=True, help="define a param as <key>=<value>")
@click.option("--param-from-json", "-j", help="load params from a json file")
@click.option("--param-from-yaml", "-y", help="load params from a yaml file")
@click.option("--timeout", "-t", default=60, help="timeout for the task")
@click.option("--worker-type", "-w", default="io", type=click.Choice(["io", "cpu"]))
@click.option("--package", required=True)
def run_task_cli(
    taskname, param, worker_type, timeout, package, param_from_json, param_from_yaml
):
    """Run a task"""
    if param_from_json:
        console.print("[red bold]json file params is not implemented yet[/]")
        sys.exit(-1)
    if param_from_yaml:
        console.print("[red bold]yaml file params is not implemented yet[/]")
        sys.exit(-1)

    params = {}
    for p in param:
        k, v = p.split("=")
        params[k] = v

    task = workers.Task(name=taskname, timeout=timeout, params=params)
    if worker_type == "io":
        workers.standalone_io_worker(package, task)
    else:
        workers.standalone_cpu_worker(package, task)
