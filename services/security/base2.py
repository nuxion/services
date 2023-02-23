import abc
from .errors import AuthValidationFailed, MissingAuthorizationHeader, WebAuthFailed


class AuthInterface(metaclass=abc.ABCMeta):

    def get_user_id(self, request) -> str:
        pass

    def validate_request(self, request, policies: List[str] = None,
                 require_all=True):
        pass
    

class Authenticator:

    def __init__(self, app=None, interfaces: List[AuthInterface]=None):
        self.interfaces = interfaces
        if not app:
            self.init_app(app)

    def init_app(self, app):
        app.ctx.auth_beta = self

    def validate(self, request, policies: List[str] = None,
                 require_all=True):
        request.ctx.is_authenticated = False
        request.ctx.is_authorized = False
        request.ctx.user_id = None
        for i in self.interfaces:
            i.validate_request(request, policies. require_all)



def get_req_auth(request: Request) -> Authenticator:
    """a shortcut to get the Auth object from a web context"""

    return request.app.ctx.auth_beta



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
            auth = get_req_auth(request)
            auth.validate(request, scopes. require_all)
            if request.ctx.is_authenticated and request.ctx.is_authenticated:
                response = f(request, *args, **kwargs)
                if isawaitable(response):
                    response = await response
            elif not request.ctx.is_authenticated:
                raise WebAuthFailed(msg="Authentication failed")
            elif not request.ctx.is_authorized:
                raise WebAuthFailed(msg="Authorization failed")
            else:
                raise WebAuthFailed()
            return response

        return decorated_function

    return decorator



    
