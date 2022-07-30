import importlib
import logging
import logging.config
import os
import subprocess
import sys

from services import defaults
from services.types import Settings

GLOBAL_MODULE = "services.global_settings"
ENVIRONMENT_VARIABLE = "SRV_SETTINGS_MODULE"
DEFAULT_MODULE = os.environ.get(ENVIRONMENT_VARIABLE, GLOBAL_MODULE)


def _get_level(level):
    return getattr(logging, level)


def _execute_cmd(cmd) -> str:
    """Wrapper around subprocess"""
    with subprocess.Popen(
        cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ) as p:

        out, err = p.communicate()
        if err:
            raise AttributeError(err.decode())

        return out.decode().strip()


def define_base_path() -> str:
    """
    It tries to determine a base path for BASE_PATH in settings.
    If a environment var exist for this, then it will use that, else
    it will use git, if fail it will go to an upper level.
    """
    root_dir = os.getcwd()
    base_path = root_dir

    base_var = os.environ.get(defaults.BASE_PATH_ENV)
    # is_interactive = _is_interactive_shell()
    if not base_var:
        try:
            base_path = _execute_cmd("git rev-parse --show-toplevel")
        except:
            # base_path = str(Path(root_dir).parents[0])
            pass
    elif base_var:
        base_path = base_var

    return base_path


def load_conf(settings_module=None) -> Settings:
    settings_module = settings_module or DEFAULT_MODULE
    module_loaded = settings_module
    base_path = define_base_path()
    sys.path.append(base_path)

    try:
        mod = importlib.import_module(settings_module)
    except ModuleNotFoundError:
        mod = importlib.import_module(GLOBAL_MODULE)
        module_loaded = GLOBAL_MODULE

    settings_dict = {}
    for m in dir(mod):
        if m.isupper():
            # sets.add(m)
            value = getattr(mod, m)
            settings_dict[m] = value

    bp = settings_dict.get("BASE_PATH")
    if bp:
        base_path = bp
    else:
        settings_dict["BASE_PATH"] = base_path
    cfg = Settings(**settings_dict)
    cfg.SETTINGS_MODULE = module_loaded

    if not cfg.DEBUG:
        _level = _get_level(cfg.LOGLEVEL)
    else:
        _level = logging.DEBUG

    # set BASE_PATH
    # os.environ[defaults.BASE_PATH_ENV] = cfg.BASE_PATH
    # logging.config.dictConfig(cfg.LOGCONFIG)
    return cfg
