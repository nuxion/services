import sys
from services import defaults, types

# WARNING:
# We do our best effort to keep sensible information private
# but in the scenario of an intrusion into the network or machines
# where servers are hosted, then it represents a risk for the information
# stored in those machines.

# General Folders for the server
DATABASES = {
    "default": types.Database(
        name="default",
        async_url="sqlite+aiosqlite:///db.sqlite",
        sync_url="sqlite:///db.sqlite",
        description="Default database",
    )
}

APPS = [
    "example.web.WebApp",
]

SECURITY = types.SecurityConfig(
    secret_key="ZXigJdqSQXwPqy7XTCAb1ztgM0_dynZT8i21g2JtjLk",
    jwt=types.JWTConfig(
        alg="HS256",
        secret="ZXigJdqSQXwPqy7XTCAb1ztgM0_dynZT8i21g2JtjLk"
    )
)

TASKS = types.TasksBackend(
    uri="sqlite+aiosqlite:///tasks.sqlite",
    backend_class="services.ext.sql.workers.SQLBackend"

)
STORAGE = {
    "default": types.Storage(
        bucket=".storage", store_class="services.storage.AsyncLocal"
    )
}
TEMPLATES_DIR = [
    "example/templates"
]
