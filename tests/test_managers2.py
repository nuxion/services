import pytest
from sqlalchemy.engine.result import ChunkedIteratorResult

from services.db import GenericManager

from .common import TestModel


class Manager(GenericManager[TestModel]):
    model_class = "tests.common.TestModel"
    lookup_key = "id"


def test_managers2_generic(db):
    mg = Manager()
    assert isinstance(mg, GenericManager)


def test_managers2_create(db):
    mg = Manager()
    with db.session() as s:
        obj = mg.create(s, {"fullname": "hello"}, commit=True)
        row = mg.get_one(s, obj.id)

    assert isinstance(mg, GenericManager)
    assert isinstance(obj, TestModel)
    assert isinstance(row, TestModel)
    # assert isinstance(row, TestModel)


def test_managers2_list(db):
    mg = Manager()
    with db.session() as s:
        all_ = mg.list(s)
        totals = mg.scalars(all_)

    assert isinstance(all_, ChunkedIteratorResult)
    assert len(totals) > 0
    assert isinstance(totals[0], TestModel)


@pytest.mark.asyncio
async def test_managers2_acreate(adb):
    mg = Manager()
    async with adb.session() as s:
        obj = await mg.acreate(s, {"fullname": "pepe"}, commit=True)
        row = await mg.aget_one(s, obj.id)

    assert isinstance(mg, GenericManager)
    assert isinstance(obj, TestModel)
    assert isinstance(row, TestModel)


@pytest.mark.asyncio
async def test_managers2_alist(adb):
    mg = Manager()
    async with adb.session() as s:
        await mg.acreate(s, {"fullname": "pepe"}, commit=True)
        all_ = await mg.alist(s)
        totals = mg.scalars(all_)

    assert isinstance(all_, ChunkedIteratorResult)
    assert len(totals) > 0
    assert isinstance(totals[0], TestModel)
