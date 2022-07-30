
class CommandExecutionException(Exception):
    def __init__(self, message):
        super().__init__(message)


class BadConfigurationException(Exception):
    def __init__(self, bad_param):
        super().__init__(f"{bad_param} is badly used")
