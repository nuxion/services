import errno
import importlib.util
import os

from jinja2 import Environment, FileSystemLoader, select_autoescape


def get_package_dir(pkg):
    spec = importlib.util.find_spec(pkg)
    return spec.submodule_search_locations[0]


def render(filename, templates_dir=None, *args, **kwargs):
    path = (
        f"{get_package_dir('services')}/templates"
        if templates_dir is None
        else templates_dir
    )
    env = Environment(
        loader=FileSystemLoader(path),
        autoescape=select_autoescape(),
    )
    tpl = env.get_template(filename)
    return tpl.render(*args, **kwargs)


def render_to_file(template, dst, templates_dir=None, *args, **kwargs):
    text = render(template, templates_dir, *args, **kwargs)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(text)
    return text
