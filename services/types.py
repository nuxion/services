from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, BaseSettings, RedisDsn

from services import defaults


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


class Settings(BaseSettings):
    BASE_PATH: Union[str, Path]
    HOST: str = "localhost"
    PORT: str = "8000"
    DATABASES: Dict[str, Database] = {}
    REDIS: Optional[RedisDsn] = None
    REDIS_POOL_SIZE: int = 10
    TEMPLATES_DIR: Optional[str] = None
    TEMPLATES_PACKAGE_NAME: Optional[str] = None
    DEV_MODE: bool = False
    SECURITY: Optional[SecuritySettings] = None
    CUSTOM_COMMANDS: List[str] = []
    USER_ENDPOINTS: bool = True
    USER_MODEL: Optional[str] = None
    USER_DB: str = "default"
    USER_MANAGER_CLASS = "services.user.managers.UserManager"

    APPS: List[str] = []

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
