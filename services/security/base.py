from abc import ABCMeta, abstractmethod
from secrets import token_urlsafe
from typing import Generic, List, Optional, TypeVar, Union
from pydantic import BaseModel

from services import types

StoreDriverT = TypeVar("StoreDriverT")
UserAuthT = TypeVar("UserAuthT", bound=BaseModel)


class ITokenStore(Generic[StoreDriverT], metaclass=ABCMeta):
    def __init__(self, conf: types.SecurityConfig, driver: StoreDriverT):
        self.conf = conf
        self.driver = driver

    @classmethod
    @abstractmethod
    async def from_conf(
        cls, conf: types.SecurityConfig, driver: Optional[StoreDriverT] = None
    ) -> "ITokenStore":
        pass

    @abstractmethod
    async def put(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        pass

    @abstractmethod
    async def get(self, key: str) -> Union[str, None]:
        pass

    @abstractmethod
    async def delete(self, key: str):
        pass

    @staticmethod
    def generate(sign: Optional[str] = None) -> str:
        return token_urlsafe(16)


class IAuth(metaclass=ABCMeta):
    @abstractmethod
    def get_username(self, request) -> Union[str, None]:
        pass

    @abstractmethod
    def validate_request(self, request, policies: List[str] = None, require_all=True):
        pass

    @abstractmethod
    def update_response(self, request, response):
        pass
