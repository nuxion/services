from abc import ABC, abstractmethod
from importlib import import_module
from typing import Callable, List, Optional, Tuple

from pydantic import BaseModel
from sanic import HTTPResponse, Request, Sanic

from services.db.sqlhelper import AsyncSQL
from services.security import Authenticator, IAuth
from services.types import Settings


def _init_blueprints(app, blueprints_allowed, package_dir="services.web"):
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


class ViewSet(BaseModel):
    blueprints: List[str]
    package: str


class WebAppSpec(ABC):
    """Spec whichs define a WebApp.
    A WebApp can have endpoints, or not.
    """

    name: str
    views: List[ViewSet]
    auth: Authenticator

    #    self.auth: Authenticator = Authenticator()
    def __init__(self, app: Sanic, settings: Settings):
        self.auth: Authenticator = Authenticator()
        app.ctx.auth_beta = self.auth
        self.app = app
        self.init(app, settings)

    @abstractmethod
    def init(self, app: Sanic, settings: Settings):
        pass

    def register_auth_validator(self, app: Sanic, name: str, auth: IAuth):
        app.ext.dependency(auth)
        self.auth.register_validator(name, auth)

    def init_blueprints(self, app: Sanic):
        for view in self.views:
            _init_blueprints(app, view.blueprints, package_dir=view.package)

    def get_db(self, app: Sanic, name="default") -> AsyncSQL:
        return app.ctx.databases[name]

    def get_app_settings(self, app: Sanic) -> Settings:
        return app.config.SETTINGS

    def get_request_settings(self, request: Request) -> Settings:
        return request.app.config.SETTINGS

    def get_request_auth(self, request: Request) -> Authenticator:
        return request.app.ctx.auth_beta


class PluginSpec(ABC):
    name: str
    request_ctx_name: Optional[str] = None
    request_hook_enabled: bool = False
    response_hook_enabled: bool = False

    @abstractmethod
    def init(self, app: Sanic, settings: Settings):
        pass

    def get_from_request(self, request):
        obj = getattr(request.app.ctx, self.name)
        return obj

    @abstractmethod
    async def request_hook(self, request: Request):
        raise NotImplementedError("Response hook not implemented")

    @abstractmethod
    async def response_hook(self, request: Request, response: HTTPResponse):
        raise NotImplementedError("Response hook not implemented")
