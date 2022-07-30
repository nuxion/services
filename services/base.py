from abc import ABC, abstractmethod
from typing import List

from sanic import Sanic

from services.types import Settings
from services.utils import init_blueprints


class WebAppSpec(ABC):
    name: str
    bp_modules: List[str]
    package_dir: str

    @abstractmethod
    def init(self, app: Sanic, settings: Settings):
        pass

    def init_blueprints(self, app: Sanic):
        init_blueprints(app, self.bp_modules, package_dir=self.package_dir)
        


class MigrationSpec(ABC):
    # models: List[str]
    package_dir: str
    version_table: str
