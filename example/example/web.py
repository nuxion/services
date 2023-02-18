from sanic import Sanic
from services.base import ViewSet, WebAppSpec
from services.security import get_app_auth
from services.types import Settings


from services.users import UserManager

api = ViewSet(
        blueprints=["users", "example"],
        package="example.api"
)

web = ViewSet(
    blueprints=["views"],
    package="example"
)


class WebApp(WebAppSpec):
    name = "example"
    views = [api, web]

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
