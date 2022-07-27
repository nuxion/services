from typing import Any, Dict, List, Optional

from pydantic import BaseModel, BaseSettings


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


class JWTResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str]


class TokenCreds(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None

    class Config:
        extra = "forbid"


class SecuritySettings(BaseSettings):
    JWT_PUBLIC: str
    JWT_PRIVATE: str
    JWT_ALG: str = "ES512"
    JWT_EXP: int = 30  # 30 minutes
    JWT_REQUIRES_CLAIMS: List[str] = ["exp"]
    JWT_SECRET: Optional[str] = None
    JWT_ISS: Optional[str] = None
    JWT_AUD: Optional[str] = None
    REFRESH_TOKEN_TTL: int = 3600 * 168  # 7 days
    TOKEN_STORE_URL: Optional[str] = None
    AUTH_SALT: str = "changeit"
    AUTH_ALLOW_REFRESH: bool = True
    AUTH_CLASS = "services.security.authentication.Auth"
    AUTH_FUNCTION = "services.security.users_mg.authenticate"

    class Config:
        env_prefix = "SEC_"


class UserOrm(BaseModel):
    username: str
    id: Optional[int] = None
    email: Optional[str] = None
    password: Optional[bytes] = None
    scopes: str = "user:r:w"
    is_superuser: bool = False
    is_active: bool = False

    class Config:
        orm_mode = True
