from sanic import Sanic

from services.base import ViewSet, WebAppSpec
from services.security import Authenticator
from services.security.jwtauth import JWTAuth
from services.security.sessionauth import SessionAuth
from services.security.memory_store import MemoryTokenStore
from services.types import Settings
web = ViewSet(
    blueprints=["views"],
    package="example"
)

# from services.users import UserManager
from .managers import UserManager, GroupManager

api = ViewSet(
        blueprints=["users", "example"],
        package="example.api"
)


class WebApp(WebAppSpec):
    name = "example"
    views = [api, web]
    def hook_users(self, app: Sanic):
        """
        delete if you don't want to use the pre-built user system
        """
        settings = self.get_app_settings(app)
        gm = GroupManager()
        um = UserManager(salt=settings.SECURITY.secret_key, groups=gm)
        app.ext.dependency(um)
        db = self.get_db(app, settings.USER_DB)

    def init(self, app: Sanic, settings: Settings):
        """ complete with your own logic """
        app.register_listener(self.hook_users, "before_server_start")
        app.register_listener(self.hook_users, "before_server_start")
        store = MemoryTokenStore(settings.SECURITY)
        jwtauth = JWTAuth(settings.SECURITY, store)
        session_auth = SessionAuth(settings.SECURITY, secure=False)
        app.config.JWT_ALLOW_REFRESH = settings.SECURITY.jwt.allow_refresh_token
        self.register_auth_validator(app, "jwt", jwtauth)
        self.register_auth_validator(app, "cookie", session_auth)
        # worker = Dummy(proc_name="DummyWorker")
        # worker.init_app(app)

        self.init_blueprints(app)
