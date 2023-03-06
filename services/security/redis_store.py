from typing import Optional, Union

import redis.asyncio as redis

from services import types
from services.security.base import ITokenStore


class RedisTokenStore(ITokenStore[redis.client.Redis]):
    ns = "rtk"

    @classmethod
    async def from_conf(
        cls, conf: types.SecurityConfig, driver: Optional[redis.client.Redis] = None
    ) -> "RedisTokenStore":
        if not driver:
            driver = await redis.from_url(conf.token_store_uri)

        return cls(conf, driver)

    async def put(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        await self.driver.set(f"{self.ns}:{key}", value)
        return True

    async def get(self, key: str) -> str:
        val = await self.driver.get(f"{self.ns}:{key}")
        value = val
        if not isinstance(val, str) and val:
            value = val.decode("utf-8")

        return value

    async def delete(self, key: str):
        await self.driver.delete(f"{self.ns}:{key}")
