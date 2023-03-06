from sanic import Sanic

from services.base import ViewSet, WebAppSpec
from services.security import get_app_auth
from services.security2 import Authenticator
from services.security2.jwtauth import JWTAuth
from services.security2.memory_store import MemoryTokenStore
from services.types import Settings

web = ViewSet(
    blueprints=["views"],
    package="{{ data.app_name }}"
)

{% if data.users %}
# from services.users import UserManager
from .managers import UserManager, GroupManager

api = ViewSet(
        blueprints=["users2", "{{ data.app_name }}"],
        package="{{ data.app_name }}.api"
)


class WebApp(WebAppSpec):
    name = "{{ data.app_name }}"
    views = [api, web]

    def hook_users(self, app: Sanic):
        """
        delete if you don't want to use the pre-built user system
        """
        settings = self.get_app_settings(app)
        gm = GroupManager()
        um = UserManager(salt=settings.SECURITY2.secret_key, groups=gm)
        app.ext.dependency(um)
        db = self.get_db(app, settings.USER_DB)
        # auth = get_app_auth(app)

        # app.ctx.users_mg = UserManager(
        #     auth,
        #     db=db,
        #     model_class=settings.USER_MODEL,
        #     salt=settings.SECURITY.AUTH_SALT,
        # )

    def init(self, app: Sanic, settings: Settings):
        """ complete with your own logic """
        app.register_listener(self.hook_users, "before_server_start")
        store = MemoryTokenStore(settings.SECURITY2)
        jwtauth = JWTAuth(settings.SECURITY2, store)
        self.register_auth_validator(app, "jwt", jwtauth)


        self.init_blueprints(app)
{% else %}

api = ViewSet(
        blueprints=["{{ data.app_name }}"],
        package="{{ data.app_name }}.api"
)

class WebApp(WebAppSpec):
    name = "{{ data.app_name }}"
    views = [api, web]

    def init(self, app: Sanic, settings: Settings):
        """ complete with your own logic """

        store = MemoryTokenStore(settings.SECURITY2)
        jwtauth = JWTAuth(settings.SECURITY2, store)
        self.register_auth_validator("jwt", jwtauth)
        self.init_blueprints(app)
        

{% endif %}
