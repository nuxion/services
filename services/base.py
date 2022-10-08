from abc import ABC, abstractmethod
from typing import Callable, List, Optional, Tuple

from pydantic import BaseModel
from sanic import HTTPResponse, Request, Sanic

from services.db.sqlhelper import AsyncSQL
from services.security.base import AuthSpec
from services.types import Settings
from services.utils import init_blueprints


class WebAppSpec(ABC):
    """ Spec whichs define a WebApp.
    A WebApp can have endpoints, or not.
    """
    name: str
    bp_modules: List[str]
    package_dir: str
    # middlewares: List[Tuple[str, Callable]]
    # dependencies: List[Callable]

    @abstractmethod
    def init(self, app: Sanic, settings: Settings):
        pass

    def init_blueprints(self, app: Sanic):
        init_blueprints(app, self.bp_modules, package_dir=self.package_dir)

    def get_db(self, app: Sanic, name="default") -> AsyncSQL:
        return app.ctx.databases[name]

    def get_app_settings(self, app: Sanic) -> Settings:
        return app.config.SETTINGS

    def get_request_settings(self, request: Request) -> Settings:
        return request.app.config.SETTINGS


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
