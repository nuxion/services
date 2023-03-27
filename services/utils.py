import asyncio
import codecs
import importlib.util
import json
import os
import re
import secrets
import subprocess
import unicodedata
from enum import Enum
from importlib import import_module
from pathlib import Path
from typing import Callable

import aiofiles
from sanic import Request

from services import __about__
from services.errors import CommandExecutionException

_filename_ascii_strip_re = re.compile(r"[^A-Za-z0-9_.-]")
_windows_device_files = (
    "CON",
    "AUX",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "LPT1",
    "LPT2",
    "LPT3",
    "PRN",
    "NUL",
)


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), "r") as fp:
        return fp.read()


def get_version(rel_path=None):
    # if rel_path:
    #     for line in read(rel_path).splitlines():
    #         if line.startswith("__version__"):
    #             delim = '"' if '"' in line else "'"
    #             return line.split(delim)[1]
    return __about__.__version__


def get_query_param(request, key, default_val=None):
    val = request.args.get(key, default_val)
    return val


def mkdir_p(fp):
    """Make the fullpath
    similar to mkdir -p in unix systems.
    """
    Path(fp).mkdir(parents=True, exist_ok=True)


def open_json(path):
    with open(path, "r", encoding="utf-8") as f:
        data = f.read()
        dict_ = json.loads(data)
    return dict_


def execute_cmd(cmd) -> str:
    """Wrapper around subprocess"""
    with subprocess.Popen(
        cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ) as p:
        out, err = p.communicate()
        if err:
            raise CommandExecutionException(err.decode())

        return out.decode().strip()


def path_norm(fp):
    """Given a  filepath returns a normalized a path"""
    return str(Path(fp))


def get_parent_folder():
    """Get only the name of the parent folder
    commonly used to define the project name
    """
    root = Path(os.getcwd())
    return str(root).rsplit("/", maxsplit=1)[-1]


def get_package_dir(pkg):
    spec = importlib.util.find_spec(pkg)
    return spec.submodule_search_locations[0]


def get_from_module(fullpath):
    splited = fullpath.rsplit(".", maxsplit=1)
    mod_name = splited[0]
    obj_name = splited[1]
    mod = import_module(mod_name)
    obj = getattr(mod, obj_name)
    return obj


def secure_filename(filename: str) -> str:
    r"""Pass it a filename and it will return a secure version of it.  This
    filename can then safely be stored on a regular file system and passed
    to :func:`os.path.join`.  The filename returned is an ASCII only string
    for maximum portability.
    On windows systems the function also makes sure that the file is not
    named after one of the special device files.
    >>> secure_filename("My cool movie.mov")
    'My_cool_movie.mov'
    >>> secure_filename("../../../etc/passwd")
    'etc_passwd'
    >>> secure_filename('i contain cool \xfcml\xe4uts.txt')
    'i_contain_cool_umlauts.txt'
    The function might return an empty filename.  It's your responsibility
    to ensure that the filename is unique and that you abort or
    generate a random filename if the function returned an empty one.
    .. versionadded:: 0.5
    :param filename: the filename to secure
    """
    filename = unicodedata.normalize("NFKD", filename)
    filename = filename.encode("ascii", "ignore").decode("ascii")

    for sep in os.path.sep, os.path.altsep:
        if sep:
            filename = filename.replace(sep, " ")
    filename = str(_filename_ascii_strip_re.sub("", "_".join(filename.split()))).strip(
        "._"
    )

    # on nt a couple of special files are present in each folder.  We
    # have to ensure that the target file is not such a filename.  In
    # this case we prepend an underline
    if (
        os.name == "nt"
        and filename
        and filename.split(".")[0].upper() in _windows_device_files
    ):
        filename = f"_{filename}"

    return filename


def normalize_name(name: str) -> str:
    """used mostly for projects"""
    evaluate = name.lower()
    evaluate = evaluate.replace(" ", "_")
    evaluate = secure_filename(name)
    return evaluate


def get_class(fullclass_path):
    """get a class or object from a module. The fullclass_path should be passed as:
    package.my_module.MyClass
    """
    module, class_ = fullclass_path.rsplit(".", maxsplit=1)
    mod = import_module(module)
    cls = getattr(mod, class_)
    return cls


def init_blueprints_legacy(app, blueprints_allowed, package_dir="services.web"):
    """
    It will import bluprints from modules that ends with "_bp" and belongs
    to the package declared in `package_dir`
    """
    blueprints = set()
    mod = app.__module__
    for mod_name in blueprints_allowed:
        modules = import_module(f"{package_dir}.{mod_name}", mod)
        for el in dir(modules):
            if el.endswith("_bp"):
                bp = getattr(modules, el)
                blueprints.add(bp)

    for bp in blueprints:
        print("Adding blueprint: ", bp.name)
        app.blueprint(bp)


class MimeTypes(Enum):
    """common mime types used
    https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types
    """

    html = "text/html"
    javascript = "text/javascript"
    json = "application/json"
    gz = "application/gzip"
    jpg = "image/jpeg"
    bz2 = "application/x-bzip2"
    css = "text/css"
    csv = "text/csv"
    doc = "application/msword"
    docx = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    gif = "image/gif"


def get_function(fullname) -> Callable:
    mod, name = fullname.rsplit(".", maxsplit=1)
    pkg = mod.split(".", maxsplit=1)[0]
    try:
        module = import_module(mod, pkg)
    except (ModuleNotFoundError, AttributeError):
        raise KeyError(fullname)
    return getattr(module, name)


def secure_random_str(size=12) -> str:
    return secrets.token_urlsafe(size)


async def from_async2sync(func, *args, **kwargs):
    """Run sync functions from async code"""
    loop = asyncio.get_running_loop()
    rsp = await loop.run_in_executor(None, func, *args, **kwargs)
    return rsp


def from_sync2async(func, *args, **kwargs):
    """run async functions from sync code"""
    loop = asyncio.get_event_loop()
    rsp = loop.run_until_complete(func(*args, **kwargs))
    return rsp


async def stream_reader(request: Request):
    """
    It's a wrapper to be used to yield response from a stream
    to another stream.
    it's used with project upload data to stream upload zip directly to
    the fileserver instead of load data in memory.
    """
    while True:
        body = await request.stream.read()
        if body is None:
            break
        yield body


def binary_file_reader(fp: str, chunk_size=1024):
    """
    File reader generator mostly used for projects upload
    """
    with open(fp, "rb") as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            yield data


async def async_binary_reader(fp: str, chunk_size=1024):
    """
    It should be used as:
    async for chunk in async_binary_reader(fp):
        print(chunk)
    """
    async with aiofiles.open(fp, "rb") as f:
        while True:
            data = await f.read(chunk_size)
            if not data:
                break
            yield data
