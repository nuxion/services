from sanic import Sanic

from services.base import ViewSet, WebAppSpec
from services.security import Authenticator
from services.security.jwtauth import JWTAuth
from services.security.sessionauth import SessionAuth
from services.security.memory_store import MemoryTokenStore
from services.types import Settings
{% if data.tasks -%}
from services import workers
{% endif -%}

{% if data.html -%}
web = ViewSet(
    blueprints=["views"],
    package="{{ data.app_name }}"
)
{% endif -%}
{% if data.users %}
# from services.users import UserManager
from .managers import UserManager, GroupManager

api = ViewSet(
        blueprints=["users", "{{ data.app_name }}"],
        package="{{ data.app_name }}.api"
)


class WebApp(WebAppSpec):
    name = "{{ data.app_name }}"
    {% if data.html -%}
    views = [api, web]
    {% else %}
    views = [api]
    {% endif -%}
    def hook_users(self, app: Sanic):
        """
        delete if you don't want to use the pre-built user system
        """
        settings = self.get_app_settings(app)
        gm = GroupManager()
        um = UserManager(salt=settings.SECURITY.secret_key, groups=gm)
        app.ext.dependency(um)
        db = self.get_db(app, settings.USER_DB)

    def init(self, app: Sanic, settings: Settings):
        """ complete with your own logic """
        app.register_listener(self.hook_users, "before_server_start")
        store = MemoryTokenStore(settings.SECURITY)
        jwtauth = JWTAuth(settings.SECURITY, store)
        session_auth = SessionAuth(settings.SECURITY, secure=False)
        app.config.JWT_ALLOW_REFRESH = settings.SECURITY.jwt.allow_refresh_token
        self.register_auth_validator(app, "jwt", jwtauth)
        self.register_auth_validator(app, "cookie", session_auth)
        {% if data.tasks -%}
        if not settings.SINGLE_PROCESS:
            _q_conf = workers.QueueConfig(
                app_name=self.name, qname="default", backend=settings.TASKS)
            workers.create(app, _q_conf)
            workers.TaskQueue.setup(app, _q_conf)
        {% endif -%}

        # worker = Dummy(proc_name="DummyWorker")
        # worker.init_app(app)

        self.init_blueprints(app)
{% else %}

api = ViewSet(
        blueprints=["{{ data.app_name }}"],
        package="{{ data.app_name }}.api"
)

class WebApp(WebAppSpec):
    name = "{{ data.app_name }}"
    {% if data.html -%}
    views = [api, web]
    {% else %}
    views = [api]
    {% endif -%}

    def init(self, app: Sanic, settings: Settings):
        """ complete with your own logic """

        store = MemoryTokenStore(settings.SECURITY)
        jwtauth = JWTAuth(settings.SECURITY, store)
        app.config.JWT_ALLOW_REFRESH = settings.SECURITY.jwt.allow_refresh_token
        self.register_auth_validator(app, "jwt", jwtauth)
        self.init_blueprints(app)
        {% if data.tasks -%}
        if not settings.SINGLE_PROCESS:
            _q_conf = workers.QueueConfig(
                app_name=self.name, qname="default", backend=settings.TASKS)
            workers.create(app, _q_conf)
            workers.TaskQueue.setup(app, _q_conf)
        {% endif -%}

        

{% endif %}
