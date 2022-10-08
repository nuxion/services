from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field
from services.db.sqlhelper import AsyncSQL
from services.security import AuthSpec, PasswordScript
from services.types import JWTResponse
from services.utils import get_class


class UserSpec(BaseModel):
    id: int
    username: str
    scopes: List[str] = ["user"]
    email: Optional[str] = None
    is_superuser: bool = False
    is_active: bool = True
    create_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()


class UserManagerSpec(ABC):
    auth: AuthSpec

    @abstractmethod
    async def register(self, data: Dict[str, Any]) -> Union[UserSpec, None]:
        pass

    @abstractmethod
    async def update(self, username: str, data: Dict[str, Any]):
        pass

    @abstractmethod
    async def list_users(self, filter_active=True) -> List[UserSpec]:
        pass

    @abstractmethod
    async def get(self, username: str) -> UserSpec:
        pass

    @abstractmethod
    async def authenticate(self, username: str, *,
                           password: str) -> UserSpec:
        pass

    @abstractmethod
    def verify_password(self,
                        original_password: bytes, *,
                        to_verify: str,
                        salt: Union[bytes, str]
                        ) -> bool:
        pass

    @abstractmethod
    def encrypt_password(self, password, salt: Union[bytes, str]) -> bytes:
        pass

    @abstractmethod
    async def delete(self, username: str):
        pass

    @abstractmethod
    async def change_pass(self, username: str, new_password: str):
        pass

    @abstractmethod
    async def generate_token(self, user: UserSpec, exp=None) -> JWTResponse:
        pass

    @abstractmethod
    async def refresh_token(self, old_token: JWTResponse) -> JWTResponse:
        pass
