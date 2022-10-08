from sanic.exceptions import SanicException
from sanic.exceptions import Unauthorized as SanicUnauthorized


class SanicJWTException(SanicException):
    pass


class InvalidToken(SanicJWTException):
    pass


class WebAuthFailed(SanicJWTException):
    status_code = 401
    quiet = True

    def __init__(self, message="Authentication failed.", **kwargs):
        super().__init__(message, **kwargs)


class CommandExecutionException(Exception):
    def __init__(self, message):
        super().__init__(message)


class BadConfigurationException(Exception):
    def __init__(self, bad_param):
        super().__init__(f"{bad_param} is badly used")


class UserNotFound(Exception):

    def __init__(self, username):
        super().__init__(f"{username} not found")


class AuthValidationFailed(Exception):
    pass
