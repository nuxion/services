

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
