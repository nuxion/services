from sanic import Sanic
from services.base import WebAppSpec
from services.security import get_app_auth
from services.types import Settings
{% if data.init %}
from services.users import UserManager

class WebApp(WebAppSpec):
    name = "{{ data.app_name }}"
    bp_modules = ["views_bp", "users_bp"]
    package_dir = "{{ data.app_name }}"

    def hook_users(self, app: Sanic):
        """
        delete if you don't want to use the pre-built user system
        """
        settings = self.get_app_settings(app)
        db = self.get_db(app, settings.USER_DB)
        auth = get_app_auth(app)

        app.ctx.users_mg = UserManager(
            auth,
            db=db,
            model_class=settings.USER_MODEL,
            salt=settings.SECURITY.AUTH_SALT,
        )

    def init(self, app: Sanic, settings: Settings):
        """ complete with your own logic """
        app.register_listener(self.hook_users, "before_server_start")

        self.init_blueprints(app)
{% else %}

class WebApp(WebAppSpec):
    name = "{{ data.app_name }}"
    bp_modules = ["views"]
    package_dir = "{{ data.app_name }}"

    def init(self, app: Sanic, settings: Settings):
        """ complete with your own logic """
        pass

{% endif %}
