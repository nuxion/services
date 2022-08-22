from abc import ABC, abstractmethod
from typing import List

from sanic import Sanic

from services.types import Settings
from services.utils import init_blueprints


class WebAppSpec(ABC):
    """ Spec whichs define a WebApp.
    A WebApp can have endpoints, or not.
    """
    name: str
    bp_modules: List[str]
    package_dir: str

    @abstractmethod
    def init(self, app: Sanic, settings: Settings):
        pass

    def init_blueprints(self, app: Sanic):
        init_blueprints(app, self.bp_modules, package_dir=self.package_dir)
