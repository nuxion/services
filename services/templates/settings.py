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

USER_MODEL = "{{ data.app_name }}.models.UserModel"

APPS = [
    # "services.users.web.WebApp",
    "services.security.web.WebApp",
    "{{ data.app_name }}.web.WebApp",
]
