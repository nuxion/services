import sys

from services import defaults, types
# WARNING:
# We do our best effort to keep sensible information private
# but in the scenario of an intrusion into the network or machines
# where servers are hosted, then it represents a risk for the information
# stored in those machines.


# General Folders for the server
SECURITY = types.SecuritySettings(
    JWT_SECRET="Changeme",
    JWT_ALG="HS256",
    AUTH_SALT="Changeme",
)
APPS = [
    "services.users.web.WebApp",
]

# Logs
# LOGLEVEL = "INFO"
# LOGCONFIG = dict(  # no cov
#     version=1,
#     # disable_existing_loggers=True,
#     loggers={
#         defaults.LOGGER: {
#             "level": LOGLEVEL,
#             "handlers": ["console"],
#         },
#     },
#     handlers={
#         "console": {
#             "class": "logging.StreamHandler",
#             "formatter": "generic",
#             "stream": sys.stdout,
#         },
#         "error_console": {
#             "class": "logging.StreamHandler",
#             "formatter": "generic",
#             "stream": sys.stderr,
#         },
#     },
#     formatters={
#         "generic": {
#             # "format": "%(asctime)s [%(process)d] [%(levelname)s] %(message)s",
#             "format": "[%(levelname)s] %(message)s",
#             "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
#             "class": "logging.Formatter",
#         },
#     },
# )
