from sanic import Sanic
from services.base import MigrationSpec, WebAppSpec
from services.types import Settings


class WebApp(WebAppSpec):
    name = "{{ data.app_name }}"
    bp_modules = ["views"]
    package_dir = "{{ data.app_name }}"

    def init(self, app: Sanic, settings: Settings):
        """ complete with your own logic """
        pass
