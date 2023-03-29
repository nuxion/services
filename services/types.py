import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

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


class TasksBackend(BaseModel):
    uri: str = "sqlite+aiosqlite:///tasks.db"
    backend_class: str = "services.ext.sql.workers.SQLBackend"


class Storage(BaseModel):
    bucket: str = ".storage"
    store_class: str = "services.storage.AsyncLocal"


class SecuritySettings(BaseSettings):
    JWT_PUBLIC: Optional[str] = None
    JWT_PRIVATE: Optional[str] = None
    JWT_SECRET: Optional[str] = None
    JWT_ALG: str = "ES512"
    JWT_EXP: int = 30  # 30 minutes
    JWT_CLAIMS_REQUIRED: List[str] = ["exp"]
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


class KeyPairs(BaseModel):
    public: str
    private: str


class JWTPayload(BaseModel):
    exp: Optional[int] = None
    iat: Optional[int] = None
    iss: Optional[str] = None
    sub: Optional[str] = None
    aud: Optional[str] = None
    custom: Dict[str, Any] = Field(default_factory=dict)


class JWTConfig(BaseModel):
    alg: str
    exp_min: int = 30
    keys: Optional[KeyPairs] = None
    secret: Optional[str] = None
    issuer: Optional[str] = None
    audience: Optional[str] = None
    requires_claims: List[str] = ["exp"]
    ttl_refresh_token: int = 3600 * 168  # 7 days
    allow_refresh_token: bool = False

    class Config:
        extra = "forbid"


class SecurityConfig(BaseModel):
    secret_key: str = Field(default_factory=os.urandom(16).hex)
    jwt: Optional[JWTConfig] = None
    session: Optional[str] = None
    token_store_uri: str = "sqlite+aiosqlite:///:memory:"
    authenticators: List[str] = Field(default_factory=list)
    ttl_refresh_token: int = 3600 * 168  # 7 days
    domain: str = "localhost"


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
    SECURITY2: SecurityConfig = Field(default_factory=SecurityConfig)
    AUTHENTICATORS: List[str] = Field(default_factory=list)
    CUSTOM_COMMANDS: List[str] = Field(default_factory=list)
    USER_ENDPOINTS: bool = True
    USER_DB: str = "default"
    TASKS: Optional[TasksBackend] = None

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

    STORAGE: Optional[Dict[str, Storage]] = None

    # MIGRATIONS: Dict[str, Migration] = {}

    CORS_ORIGINS: Union[List, str] = "*"
    CORS_ALLOW_HEADERS: Union[List, str] = "*"
    SANIC_APP_NAME = defaults.SANIC_APP
    SETTINGS_MODULE: Optional[str] = None

    class Config:
        env_prefix = "SRV_"


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


class DefaultMeta(BaseModel):
    keywords: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    viewport: str = "width=device-width, initial-scale=1.0, maximum-scale=1"


class OGMeta(BaseModel):
    title: str
    description: str
    url: str
    image: str
    type_: str = "website"


class HtmlData(BaseModel):
    # navbar: List[MenuOption]
    ctx: Dict[str, Any]
    title: str
    content: Dict[str, Any] = Field(default_factory=dict)
    lang: str = "en"
    meta: DefaultMeta = Field(default_factory=DefaultMeta)
    og: Optional[OGMeta] = None


class Cookie(BaseModel):
    """
    expires: datetime - The time for the cookie to expire on the client’s browser.

    :param max_age:  Number of seconds the cookie should live for.
    :param path: The subset of URLs to which this cookie applies. Defaults to /.
    :param domain: Specifies the domain for which the cookie is valid.
        An explicitly specified domain must always start with a dot.
    :param max_age: Number of seconds the cookie should live for.
    :param secure: Specifies whether the cookie will only be sent
        via HTTPS.
    :param httponly: Specifies whether the cookie cannot be read by JavaScript.
    :param samesite: Default is browser dependent, specification states
        (Lax, Strict, and None) are valid values.
    """

    value: str
    domain: str
    httponly: bool = True
    path: str = "/"
    secure: bool = True
    samesite: str = "lax"
    max_age: int = Field(alias="max-age", default=60 * 60)


class Bucket(BaseModel):
    name: str
    url: str
    storage_class: str
    location: str
    versioning: bool = False
    labels: Optional[Dict[str, str]] = None
    public: bool = False
    created_at: Optional[datetime] = None

    def __repr__(self):
        return f"<Bucket {self.name}>"

    def __str__(self):
        return f"<Bucket {self.name}>"
