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


class WebUnauthorized(SanicJWTException, SanicUnauthorized):
    def __init__(self, message="Auth required.", **kwargs):
        super().__init__(message, scheme="Bearer", **kwargs)


class MissingAuthorizationHeader(SanicJWTException):
    status_code = 400

    def __init__(self, message="Authorization header not present.", **kwargs):
        super().__init__(message, **kwargs)


class CommandExecutionException(Exception):
    def __init__(self, message):
        super().__init__(message)


class BadConfigurationException(Exception):
    def __init__(self, bad_param):
        super().__init__(f"{bad_param} is badly used")


class UserNotFound(Exception):
    def __init__(self, username):
        super().__init__(f"User: {username} not found")


class GroupNotFound(Exception):
    def __init__(self, group):
        super().__init__(f"Group: '{group}' not found")


class DBObjectNotFound(Exception):
    def __init__(self, table, key):
        super().__init__(f"{key} not found in table {table}")


class AuthValidationFailed(Exception):
    pass
