from functools import wraps
from inspect import isawaitable
from typing import List, Optional

from sanic import Request, Sanic, json
from services.base import WebAppSpec
from services.security.authentication import auth_from_settings
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

    def hook_users(self, app: Sanic):
        settings = self.get_app_settings(app)
        db = self.get_db(app, settings.USER_DB)
        app.ctx.users_mg = UserManager(db, model_class=settings.USER_MODEL,
                                       salt=settings.SECURITY.AUTH_SALT)

    def init(self, app: Sanic, settings: Optional[Settings] = None):
        """ complete with your own logic """
        settings = settings or self.get_app_settings(app)

        app.register_listener(self.hook_users, "before_server_start")

        if settings.USER_ENDPOINTS:
            self.init_blueprints(app)
