from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, BaseSettings, Field, RedisDsn

from services import defaults


class StaticDir(BaseModel):
    name: str
    uripath: str
    localdir: str


class Database(BaseModel):
    """
    Database configuration object to be used with
    :class:`services.db.sqlhelper.SQL` and
    :class:`services.db.sqlhelper.AsyncSQL`

    Examples:

    .. highlight:: python
    .. code-block:: python

        from services.types import Database
        dbconf = Database(uri="sqlite:////tmp/test.db")


    :param uri: full dsl url sqlite:////tmp/test.db
    :type uri: str
    :param name: optional value to identify a database
    :type name: str
    :param pool_size: size of the pool
    :type pool_size: int
    :param max_overflow: TODO
    :type max_overflow: int
    :param debug: maps with echo param in sqlalachemy
    :param description: optional value for metadata info about the database

    """

    async_url: Optional[str] = None
    sync_url: Optional[str] = None
    name: str = "default"
    pool_size: int = 20
    max_overflow: int = 0
    debug: bool = False  # debug
    # metadata
    description: Optional[str] = None


class MigrationType(BaseModel):
    models: List[str]
    package_dir: str
    version_table: str


class SecuritySettings(BaseSettings):
    JWT_PUBLIC: Optional[str] = None
    JWT_PRIVATE: Optional[str] = None
    JWT_SECRET: Optional[str] = None
    JWT_ALG: str = "ES512"
    JWT_EXP: int = 30  # 30 minutes
    JWT_CLAIMS_REQUIRED: List[str] = ["exp"]
    JWT_SECRET: Optional[str] = None
    JWT_ISS: Optional[str] = None
    JWT_AUD: Optional[str] = None
    REFRESH_TOKEN_TTL: int = 3600 * 168  # 7 days
    AUTH_SALT: str = "changeit"
    AUTH_ALLOW_REFRESH: bool = True
    AUTH_CLASS = "services.security.authentication.Auth"

    class Config:
        env_prefix = "SRV_"


class ViteConfig(BaseModel):
    """
    Vite configuration to be integrated into the backend.
    See: https://vitejs.dev/guide/backend-integration.html

    as an example, a base configuration in the front could be:

    .. code-block:: javascript

        export default defineConfig({
            root: resolve('./src'),
            base: '/',
            plugins: [svelte()],
            build: {
                manifest: true,
                outDir: resolve('./dist/vite'),
                emptyOutDir: true,
                target: 'es2015',
                rollupOptions: {
                input: {
                    main: resolve('./src/main.js'),
                        // explore: resolve('./theme/static/src/explore/main.js'),

                }
                }
            }
            })



    where the the python app is in: `test_app/test_app`
    and the frontend is in `test_app/front`
    With that in mind then:

    :param VITE_STATIC_URL_PATH: Where dynamic assets in vite are configurated.
    :param VITE_STATIC_DIR: Local path from the python app where the vite
        dynamic assets lives, in our example: "front/src/assets"
    :param VITE_OUTPUT_DIR: Where Vite generates the build,
        in our case: "front/dist/"
    :param VITE_DEV_SERVER: Where vite dev server is listening.
        By default it listen on "http://localhost:5173"
    :param VITE_DEV_MODE: if dev mode is true, the it will render the hmr script tag
    :param VITE_REACT_MODE: Enable if you are developing with REACT
    :param VITE_BASE: Base url in the vite server. Is  the same as
        https://vitejs.dev/config/server-options.html#server-base
        by default: "/"

    """

    # Where dynamic assets in vite are configurated
    VITE_STATIC_URL_PATH: str = "assets"
    # Local path from the python app where the vite dynamic assets are
    VITE_STATIC_DIR: str = "front/src/assets"
    # where vite put the buil
    VITE_OUTPUT_DIR: str = "fron/dist"
    # where vite dev server is listening
    VITE_DEV_SERVER: str = "http://localhost:5173"
    # if dev mode is true, the it will render the hmr script tag
    VITE_DEV_MODE: bool = True
    # special case for react
    VITE_REACT_MODE: bool = False
    # base url in the vite server the same as
    #    https://vitejs.dev/config/server-options.html#server-base
    VITE_BASE: str = "/"


class Settings(BaseSettings):
    BASE_PATH: Union[str, Path]
    HOST: str = "localhost"
    PORT: str = "8000"
    DATABASES: Dict[str, Database] = {}
    REDIS: Optional[RedisDsn] = None
    REDIS_POOL_SIZE: int = 10
    TEMPLATES_DIR: List[str] = Field(default_factory=list)
    TEMPLATES_PACKAGE_NAME: Optional[str] = None
    DEV_MODE: bool = False
    SECURITY: Optional[SecuritySettings] = None
    CUSTOM_COMMANDS: List[str] = []
    USER_ENDPOINTS: bool = True
    USER_MODEL: Optional[str] = None
    USER_DB: str = "default"
    USER_MANAGER_CLASS = "services.user.managers.UserManager"

    APPS: List[str] = []

    # web
    STATIC_URL: str = ""
    STATICFILES_DIRS: List[StaticDir] = Field(default_factory=list)
    VITE_ENABLED: bool = False
    VITE_CONFIG: ViteConfig = ViteConfig()
    # logs
    LOGLEVEL: str = "INFO"
    LOGCONFIG: Dict[str, Any] = {}
    DEBUG: bool = False

    # MIGRATIONS: Dict[str, Migration] = {}

    CORS_ORIGINS: Union[List, str] = "*"
    CORS_ALLOW_HEADERS: Union[List, str] = "*"
    SANIC_APP_NAME = defaults.SANIC_APP
    SETTINGS_MODULE: Optional[str] = None

    class Config:
        env_prefix = "SRV_"


class KeyPairs(BaseModel):
    public: str
    private: str


class JWTConfig(BaseModel):
    alg: str
    exp_min: int = 30
    keys: Optional[KeyPairs] = None
    secret: Optional[str] = None
    issuer: Optional[str] = None
    audience: Optional[str] = None
    requires_claims: List[str] = ["exp"]
    ttl_refresh_token: int = 3600 * 168  # 7 days

    class Config:
        extra = "forbid"


class UserLogin(BaseModel):
    username: str
    password: str

    class Config:
        extra = "forbid"


class JWTResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None


class TokenCreds(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None

    class Config:
        extra = "forbid"


class HtmlData(BaseModel):
    # navbar: List[MenuOption]
    ctx: Dict[str, Any]
    title: str
    content: Dict[str, Any]
    meta: Optional[Dict[str, str]] = None
