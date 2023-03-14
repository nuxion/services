from functools import wraps
from inspect import isawaitable
from typing import Dict, List, Optional

from sanic import Request, json

from services import errors
from services.security.base import IAuth


class Authenticator:
    def __init__(
        self,
        app=None,
    ):
        self._scopes = None
        self._require_all = False
        self._validators: Dict[str, IAuth] = {}
        self._validators_list = set()
        if app:
            self.init_app(app)

    def register_validator(self, name: str, validator: IAuth):
        if name not in self._validators_list:
            self._validators.update({name: validator})
            self._validators_list.add(name)

    def list_validators(self) -> List[str]:
        return list(self._validators_list)

    def init_app(self, app):
        app.ctx.auth_beta = self
        app.error_handler.add(errors.WebAuthFailed, self.auth_error_handler)
        app.error_handler.add(
            errors.MissingAuthorizationHeader, self.auth_error_handler
        )

    def bp_middleware(self, request):
        valid = self.validate(
            self._validators, request, self._scopes, self._require_all
        )
        if not valid:
            raise errors.WebAuthFailed()

    def init_bp(
        self,
        bp,
        validators: Dict[str, IAuth],
        scopes: Optional[List[str]] = None,
        require_all=False,
    ):
        self._validators = validators
        self._scopes = scopes
        self._require_all = require_all
        bp.on_request(self.bp_middleware)

    def auth_error_handler(self, request, exception):
        """TODO: move to WebSpec"""
        return json({"msg": "Authentication failed"}, status=401)

    def validate(
        self,
        validators: List[str],
        request,
        policies: List[str] = None,
        require_all=True,
    ) -> bool:
        valid = False
        request.ctx.is_authenticated = False
        request.ctx.is_authorized = False
        request.ctx.user_id = None
        for v in validators:
            auth = self._validators.get(v)
            if auth:
                auth.validate_request(request, policies, require_all)

        if request.ctx.is_authenticated and request.ctx.is_authenticated:
            valid = True
        return valid

    def update_response(self, validators: List[str], request: Request, response):
        for v in validators:
            auth = self._validators.get(v)
            if auth:
                auth.update_response(request, response)


def get_authenticator(request) -> Authenticator:
    return request.app.ctx.auth_beta


def protected(
    validators: List[str], scopes: Optional[List[str]] = None, require_all=True
):
    """verify a token from a request.
    Optionally if a list of scopes is given then will check that scopes
    with the scopes provided by the token.

    :param scopes: a list of scopes
    :param required_all: if true it will check that the all the names provided
    match with the required.

    """

    def decorator(f):
        @wraps(f)
        async def decorated_function(request: Request, *args, **kwargs):
            # auth = get_req_auth(request)
            auth = get_authenticator(request)
            is_valid = auth.validate(validators, request, scopes, require_all)

            if not is_valid:
                raise errors.WebAuthFailed(msg="Authentication failed")
            response = f(request, *args, **kwargs)
            if isawaitable(response):
                response = await response

            auth.update_response(validators, request, response)
            return response

        return decorated_function

    return decorator
