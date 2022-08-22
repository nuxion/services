from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, BaseSettings, RedisDsn

from services import defaults


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
    # DATABASES: Dict[str, Database] = {}
    SQL: str = "sqlite:///db.sqlite"
    ASQL: str = "sqlite+aiosqlite:///db.sqlite"
    REDIS_WEB: Optional[RedisDsn] = None
    REDIS_WEB_POOL_SIZE: int = 10
    TEMPLATES_DIR: Optional[str] = None
    TEMPLATES_PACKAGE_NAME: Optional[str] = None
    DEV_MODE: bool = False
    SECURITY: Optional[SecuritySettings] = None
    AUTH_ENDPOINTS: bool = True
    USER_MODEL: Optional[str] = None

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
