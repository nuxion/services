from sanic import Request, Sanic
from services.base import WebAppSpec
from services.types import Settings

from .managers import UserManager


def get_users_mg(request: Request) -> UserManager:
    """a shortcut to get the Auth object from a web context"""
    current_app: Sanic = Sanic.get_app(request.app.name)

    return current_app.ctx.users_mg


class WebApp(WebAppSpec):
    name = "users"
    bp_modules = ["users_bp"]
    package_dir = "services.users"

    def init(self, app: Sanic, settings: Settings):
        """ complete with your own logic """
        app.ctx.users_mg = UserManager(settings.USER_MODEL,
                                       salt=settings.SECURITY.AUTH_SALT)

        if settings.AUTH_ENDPOINTS:
            self.init_blueprints(app)
