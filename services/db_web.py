from services.base import WebAppSpec

from sanic import Sanic
from services.base import WebAppSpec
from services.types import Settings


class DBApp(WebAppSpec):
    name = "db_app"
    bp_modules = []
    package_dir = None

    def init(self, app: Sanic, settings: Settings):
        """ complete with your own logic """
        pass


    


