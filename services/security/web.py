from functools import wraps
from inspect import isawaitable
from typing import List, Optional

from sanic import Request, Sanic, json
from services.base import WebAppSpec
from services.security.authentication import auth_from_settings
from services.security.redis_tokens import RedisTokenStore
from services.types import Settings

from .base import AuthSpec
from .errors import (AuthValidationFailed, MissingAuthorizationHeader,
                     WebAuthFailed)


def get_auth(request: Request) -> AuthSpec:
    """a shortcut to get the Auth object from a web context"""

    current_app: Sanic = Sanic.get_app(request.app.name)

    return current_app.ctx.auth


def protected(scopes: Optional[List[str]] = None, require_all=True):
    """verify a token from a request.
    Optionally if a list of scopes is given then will check that scopes
    with the scopes provided by the token.

    :param scopes: a list of scopes
    :param required_all: if true it will check that the all the names provided
    match with the required.

    """

    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            auth = get_auth(request)
            token = request.token
            if not token:
                raise MissingAuthorizationHeader()
            try:
                decoded = auth.validate(token, scopes, require_all)
                request.ctx.token_data = decoded
                response = f(request, *args, **kwargs)
                if isawaitable(response):
                    response = await response
            except AuthValidationFailed:
                raise WebAuthFailed()

            return response

        return decorated_function

    return decorator


def auth_error_handler(request, exception):
    return json({"msg": "Authentication failed"}, status=401)


# def sanic_init_auth(app: Sanic, auth: AuthSpec, settings: Settings):
#     app.ctx.auth = auth
#     app.config.AUTH_SALT = settings.SECURITY.AUTH_SALT
#     app.config.AUTH_ALLOW_REFRESH = settings.SECURITY.AUTH_ALLOW_REFRESH
#     app.config.USERS = UserManager(settings.USER_MODEL)
#     # app.ctx.authenticate = get_class(settings.AUTH_FUNCTION)
#
#     app.error_handler.add(WebAuthFailed, auth_error_handler)
#     app.error_handler.add(MissingAuthorizationHeader, auth_error_handler)


class WebApp(WebAppSpec):
    name = "security"
    package_dir = "services.security"
    bp_modules = []

    def init(self, app: Sanic, settings: Settings):
        store = None
        if settings.SECURITY.AUTH_ALLOW_REFRESH:
            try:
                store = RedisTokenStore(app.ctx.web_redis)
            except AttributeError:
                print("NO redis configuration")

        app.ctx.auth = auth_from_settings(settings.SECURITY, store)
        app.config.AUTH_SALT = settings.SECURITY.AUTH_SALT
        app.config.AUTH_ALLOW_REFRESH = settings.SECURITY.AUTH_ALLOW_REFRESH

        app.error_handler.add(WebAuthFailed, auth_error_handler)
        app.error_handler.add(MissingAuthorizationHeader, auth_error_handler)
