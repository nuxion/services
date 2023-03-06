from typing import Callable, Optional, Union

from itsdangerous import TimestampSigner
from itsdangerous.exc import BadSignature
from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy import delete as sqldelete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from services import types
from services.security.base import ITokenStore

meta = MetaData()


def _create_engine(uri) -> AsyncEngine:
    return create_async_engine(uri)


class SQLTokenStore(ITokenStore[AsyncEngine]):
    """
    TODO: set created time to validate expired token
    """

    tokens = Table(
        "refresh_tokens",
        meta,
        Column("key", String(16), primary_key=True),
        Column("value", String(16)),
    )

    def __init__(self, conf: types.SecurityConfig, driver: AsyncEngine):
        super().__init__(conf, driver)
        self.sign = TimestampSigner(conf.secret_key)

    async def _dispose(self):
        if ":memory:" not in self.conf.token_store_uri:
            await self.driver.dispose()

    @classmethod
    async def from_conf(
        cls, conf: types.SecurityConfig, driver: Optional[AsyncEngine] = None
    ) -> "SQLTokenStore":
        if not driver:
            driver = create_async_engine(conf.token_store_uri)
        async with driver.begin() as conn:
            await conn.run_sync(meta.create_all)

        if ":memory:" not in conf.token_store_uri:
            await driver.dispose()
        return cls(conf, driver)

    async def put(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        svalue = self.sign.sign(value).decode("utf-8")

        async with self.driver.begin() as conn:
            await conn.execute(self.tokens.insert(), [{"key": key, "value": svalue}])

        await self._dispose()
        return True

    async def get(self, key: str) -> Union[str, None]:
        final = None
        invalid = False
        async with self.driver.begin() as conn:
            result = await conn.execute(
                select(self.tokens).where(self.tokens.c.key == key).limit(1)
            )
            row = result.fetchall()
            if row:
                final = row[0][1]
                try:
                    final = self.sign.unsign(final, max_age=self.conf.ttl_refresh_token)
                    final = final.decode()
                except BadSignature:
                    invalid = True

        if invalid:
            final = None
            await self.delete(key)
        await self._dispose()
        return final

    async def delete(self, key: str):
        async with self.driver.begin() as conn:
            await conn.execute(sqldelete(self.tokens).where(self.tokens.c.key == key))

        await self._dispose()
