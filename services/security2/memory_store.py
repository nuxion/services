from secrets import token_urlsafe
from typing import Optional, Union, Dict
from services import types

from services.security2.base import ITokenStore


class MemoryTokenStore(ITokenStore):
    def __init__(self, conf: types.SecurityConfig):
        self.conf = conf
        self.data: Dict[str, str] = {}

    async def put(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        self.data[key] = value
        return True

    async def get(self, key: str) -> Union[str, None]:
        return self.data.get(key)

    async def delete(self, key: str):
        if self.data.get(key):
            del self.data[key]

    @staticmethod
    def generate(sign: Optional[str] = None) -> str:
        return token_urlsafe(16)
