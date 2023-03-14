# pylint: disable=missing-class-docstring
# pylint: disable=line-too-long
from typing import Any, Callable, Dict, List, Optional, Type, Union

from jinja2 import (
    Environment,
    FileSystemLoader,
    PackageLoader,
    Template,
    select_autoescape,
)
from jinja2.ext import Extension
from sanic import Sanic
from services.types import Settings
from services.utils import open_json

from .static import Static
from .vite import ViteAsset, ViteDev


class Render:
    # inspired by https://community.sanicframework.org/t/using-jinja2-with-sanic/615
    # also see
    # https://github.com/dldevinc/jinja2-simple-tags

    def __init__(
        self,
        package_name: Optional[str] = None,
        folder_name: str = "templates",
        searchpath: Union[str, List] = [],
        enable_async=True,
        encoding="UTF-8",
        extensions=[],
    ):
        """
        Example:
        ``` loader = PackageLoader("project.ui", "pages")```
        :param package_name: Import name of the package that contains the template directory.
        :param folder_name: Folder inside of the package which contains the templates
        :param searchpath:  if provided then a FilesystemLoader will be used instead
        :param enable_async: for async environments, it will return awaitables.
        :param encoding: utf-8 by default
        :param extensions: add extensions to jinja, like vite dev server ext
        """
        self._package = package_name
        self._folder = folder_name
        self.encoding = encoding
        self._loader = self.build_loader(package_name, searchpath)
        self.env: Environment = Environment(
            loader=self._loader,
            autoescape=select_autoescape(),
            enable_async=enable_async,
            extensions=extensions,
        )

    def build_loader(self, package_name, searchpath):
        if package_name:
            loader = PackageLoader(
                package_name=self._package,
                package_path=self._folder,
                encoding=self.encoding,
            )
        elif searchpath:
            loader = FileSystemLoader(
                searchpath,
                encoding=self.encoding,
            )
        else:
            raise AttributeError("searchpath or package_name should be set")
        return loader

    def add_func(self, name: str, func: Callable):
        """it allows to add custom functions"""
        self.env.globals[name] = func

    def add_extension(self, ext: Union[str, Type[Extension]]):
        """
        To add an extension pass a list of extension classes or import paths
        to the extensions parameter of the Environment constructor
        """
        self.env.add_extension(ext)

    def add_static(self, app: Sanic, settings: Settings):
        self.add_extension(Static)
        self.env.static_url = settings.STATIC_URL
        self.env.staticfiles = settings.STATICFILES_DIRS

    def add_vite(self, app: Sanic, settings: Settings):
        conf = settings.VITE_CONFIG
        dev_server = f"{conf.VITE_DEV_SERVER}"
        if conf.VITE_BASE != "/":
            dev_server = f"{conf.VITE_DEV_SERVER}{conf.VITE_BASE}"
        self.add_extension(ViteDev)
        self.add_extension(ViteAsset)
        self.env.vite_dev_server = dev_server
        self.env.vite_dev_mode = conf.VITE_DEV_MODE
        self.env.vite_react_mode = conf.VITE_REACT_MODE

        if conf.VITE_DEV_MODE:
            static_dir = f"{settings.BASE_PATH}/{conf.VITE_STATIC_DIR}"
            app.static(conf.VITE_STATIC_URL_PATH, static_dir, name="vite_dev")
        else:
            static_dir = f"{settings.BASE_PATH}/{conf.VITE_OUTPUT_DIR}{conf.VITE_STATIC_URL_PATH}"
            app.static(conf.VITE_STATIC_URL_PATH, static_dir, name="vite_manifest")
            manifest_json = open_json(
                f"{settings.BASE_PATH}/{conf.VITE_OUTPUT_DIR}/manifest.json"
            )
            self.env.vite_manifest = manifest_json

    def init_app(self, app: Sanic):
        """
        add render as part of the context and add url_for to be used
        inside a tempalte
        """
        app.ctx.render = self
        self.env.globals.update(url_for=app.url_for)

    def _get_app(self, request) -> Sanic:
        return request.app

    async def async_render(self, request, tpl_name, **kwargs) -> str:
        template = self.env.get_template(tpl_name)
        # ctx = {
        #     "request": request.ctx.__dict__,
        # }
        app = self._get_app(request)
        conf = {}
        if app.config.SETTINGS.DEBUG:
            conf = app.config.SETTINGS
        rendered = await template.render_async(conf=conf, **kwargs)
        return rendered

    def get_template(self, tpl_name) -> Template:
        return self.env.get_template(tpl_name)
