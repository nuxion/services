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

DATABASES = {
    "default": types.Database(
        name="default",
        async_url="sqlite+aiosqlite:///db.sqlite",
        sync_url="sqlite:///db.sqlite",
        description="Default database",
    )
}

APPS = [
    # "services.users.web.WebApp",
    # "services.security.web.WebApp",
    "{{ data.app_name }}.web.WebApp",
]

SECURITY2 = types.SecurityConfig(
    secret_key="{{ data.secret_key }}",
    jwt=types.JWTConfig(
        alg="HS256",
        secret="{{ data.secret_key }}"
    )
)

{% if data.vite_enabled %}

VITE_ENABLED = True
VITE_CONFIG = types.ViteConfig(
    # Where dynamic assets in vite are configurated
    VITE_STATIC_URL_PATH="assets",
    # Local path from the python app where the vite dynamic assets are
    VITE_STATIC_DIR="front/src/assets",
    # where vite put the buil
    VITE_OUTPUT_DIR="front/dist",
    # where vite dev server is listening
    VITE_DEV_SERVER="http://localhost:5173",
    # if dev mode is true, the it will render the hmr script tag
    VITE_DEV_MODE=True,
    # special case for react
    VITE_REACT_MODE=False,
    # base url in the vite server the same as
    #    https://vitejs.dev/config/server-options.html#server-base
    VITE_BASE="/"
)

STATICFILES_DIRS = [
        types.StaticDir(
            name="public",
            uripath="",
            localdir="front/public/"
        )
]
{% endif %}

TEMPLATES_DIR = [
    "{{ data.app_name }}/templates"
]
