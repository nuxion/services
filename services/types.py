from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseSettings, RedisDsn, BaseModel

from services import defaults


class Migration(BaseModel):
    models: List[str]
    migrations_module: str
    version_table: str


class Settings(BaseSettings):
    BASE_PATH: Union[str, Path]
    HOST: str = "localhost"
    PORT: str = "8000"

    SQL: str = "sqlite:///db.sqlite"
    ASQL: str = "sqlite+aiosqlite:///db.sqlite"
    REDIS_WEB: RedisDsn = "redis://localhost:6379/0"
    REDIS_WEB_POOL_SIZE: int = 10
    TEMPLATES_DIR: Optional[str] = None
    TEMPLATES_PACKAGE_NAME: Optional[str] = None
    DEV_MODE: bool = False

    MIGRATIONS: Dict[str, Migration] = {}

    CORS_ORIGINS: Union[List, str] = "*"
    CORS_ALLOW_HEADERS: Union[List, str] = "*"
    SANIC_APP_NAME = defaults.SANIC_APP
    SETTINGS_MODULE: Optional[str] = None

    class Config:
        env_prefix = "SRV_"
