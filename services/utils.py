import codecs
import importlib.util
import json
import os
import re
import subprocess
import unicodedata
from importlib import import_module
from pathlib import Path

from sqlalchemy.sql.schema import MetaData

from services import defaults
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


def get_version(rel_path="__version__.py"):
    for line in read(rel_path).splitlines():
        if line.startswith("__version__"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


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


def init_blueprints(app, blueprints_allowed, package_dir="services.web"):
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


def get_meta_from_app(app_name) -> MetaData:
    Base = get_class(f"{app_name}.db.Base")
    return Base.metadata
