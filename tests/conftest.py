import pytest
import pytest_asyncio
from services import types, utils
from services.db import AsyncSQL, SQL
from services.db.helpers import drop_everything
from tests.common import async_create_all, create_all, Base

_db_name = "test.db"
testdb = types.Database(
    name="testing",
    async_url=f"sqlite+aiosqlite:///{_db_name}",
    sync_url=f"sqlite:///{_db_name}",
    description="Dataproc database",
)


@pytest_asyncio.fixture()
async def adb():
    _db = AsyncSQL.from_conf(testdb)

    await async_create_all(_db)

    yield _db
    # await utils.from_async2sync(drop_everything, _db.engine)
    await _db.drop_all(Base.metadata, all_=False)

    # await _db.drop_all(Base.metadata)
    # await _db.drop_all()


@pytest.fixture(scope="module")
def db():
    _db = SQL.from_conf(testdb)
    create_all(_db)
    yield _db
    _db.drop_all()
    # await _db.drop_all(Base.metadata)
