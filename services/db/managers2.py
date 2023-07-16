from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from sqlalchemy import delete as sqldelete
from sqlalchemy import desc, func, select
from sqlalchemy.engine.result import ChunkedIteratorResult
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.attributes import InstrumentedAttribute

from services import types
from services.errors import DBObjectNotFound
from services.utils import get_class

ModelT = TypeVar("ModelT")


class GenericManager(Generic[ModelT]):
    model_class: str
    lookup_key: str
    active_key: Optional[str] = None

    def __init__(self):
        self._model: ModelT = get_class(self.model_class)
        self._key = self.lookup_key
        self._active_key = self.active_key

    @property
    def tablename(self) -> str:
        return self._model.__tablename__

    def _get_column(self, col_name) -> InstrumentedAttribute:
        return getattr(self._model, col_name)

    @staticmethod
    def scalars(result) -> List[ModelT]:
        return list(result.scalars())

    async def alist_actives(
        self, session, order_by=None, offset=0, limit=10
    ) -> ChunkedIteratorResult:
        stmt = select(self._model).offset(offset).limit(limit)
        attr = self._get_column(self._active_key)
        stmt = stmt.where(attr == True)
        if order_by:
            stmt.order_by(order_by, desc(order_by))
        result = await session.execute(stmt)
        # return list(result.scalars())
        return result

    def list_actives(
        self, session, order_by=None, offset=0, limit=10
    ) -> ChunkedIteratorResult:
        stmt = select(self._model).offset(offset).limit(limit)
        attr = self._get_column(self._active_key)
        stmt = stmt.where(attr == True)
        if order_by:
            stmt.order_by(order_by, desc(order_by))
        result = session.execute(stmt)
        # return list(result.scalars())
        return result

    def list(self, session, order_by=None, offset=0, limit=10) -> ChunkedIteratorResult:
        stmt = select(self._model).offset(offset).limit(limit)
        if order_by:
            stmt.order_by(order_by, desc(order_by))
        result = session.execute(stmt)
        # return list(result.scalars())
        return result

    async def alist(
        self, session, order_by=None, offset=0, limit=10
    ) -> ChunkedIteratorResult:
        stmt = select(self._model).offset(offset).limit(limit)
        if order_by:
            stmt.order_by(order_by, desc(order_by))
        result = await session.execute(stmt)
        # return list(result.scalars())
        return result

    def _obj_or_raise(self, lookup, obj: Union[ModelT, None]) -> ModelT:
        if not obj:
            raise DBObjectNotFound(self.tablename, lookup)
        return obj

    def _obj_or_raise_active(self, lookup, obj: Union[ModelT, None]) -> ModelT:
        attr = self._get_column(self._active_key)
        if not attr:
            raise DBObjectNotFound(self.tablename, lookup)

        return obj

    def _get_one(self, session, key: str) -> ModelT:
        attr_key = self._get_column(self._key)
        stmt = select(self._model).where(attr_key == key).limit(1)
        rsp = session.execute(stmt)

        return rsp.scalar_one_or_none()

    async def _aget_one(self, session, key: str) -> ModelT:
        attr_key = self._get_column(self._key)
        stmt = select(self._model).where(attr_key == key).limit(1)
        rsp = await session.execute(stmt)

        return rsp.scalar_one_or_none()

    def _commit_or_rollback(self, session) -> bool:
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return False
        return True

    async def _acommit_or_rollback(self, session) -> bool:
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            return False
        return True

    def count(self, session) -> int:
        stmt = select(func.count(self._model.__table__.c.id))
        res = session.execute(stmt)
        return res.scalar()

    async def acount(self, session) -> int:
        stmt = select(func.count(self._model.__table__.c.id))
        res = await session.execute(stmt)
        return res.scalar()

    def count_actives(self, session) -> int:
        stmt = select(func.count(self._model.__table__.c.id))
        attr = self._get_column(self.active_key)
        stmt = stmt.where(attr == True)
        res = session.execute(stmt)
        return res.scalar()

    async def acount_actives(self, session) -> int:
        stmt = select(func.count(self._model.__table__.c.id))
        attr = self._get_column(self.active_key)
        stmt = stmt.where(attr == True)
        res = await session.execute(stmt)
        return res.scalar()

    def create(self, session, data: Dict[str, Any], commit=True) -> Union[ModelT, None]:
        model = self._model(**data)
        session.add(model)
        if commit:
            res = self._commit_or_rollback(session)
            if not res:
                return None
        return model

    async def acreate(
        self, session, data: Dict[str, Any], commit=True
    ) -> Union[ModelT, None]:
        model = self._model(**data)
        session.add(model)
        if commit:
            res = await self._acommit_or_rollback(session)
            if not res:
                return None
        return model

    def get_active(self, session, key: str) -> ModelT:
        _obj = self._get_one(session, key)
        return self._obj_or_raise_active(key, _obj)

    async def aget_active(self, session, key: str) -> ModelT:
        _obj = await self._aget_one(session, key)
        return self._obj_or_raise_active(key, _obj)

    def get_one(self, session, key: str) -> ModelT:
        _obj = self._get_one(session, key)
        return self._obj_or_raise(key, _obj)

    async def aget_one(self, session, key: str) -> ModelT:
        _obj = await self._aget_one(session, key)
        return self._obj_or_raise(key, _obj)

    def update(self, session, key: str, data: Dict[str, Any]):
        u = self._get_one(session, key)
        if not u:
            raise DBObjectNotFound(self.tablename, key)

        for k, v in data.items():
            setattr(u, k, v)
        u.updated_at = datetime.utcnow()
        session.add(u)

    async def aupdate(self, session, key: str, data: Dict[str, Any]):
        u = await self._aget_one(session, key)
        if not u:
            raise DBObjectNotFound(self.tablename, key)

        for k, v in data.items():
            setattr(u, k, v)
        u.updated_at = datetime.utcnow()
        session.add(u)

    def hard_delete(self, session, key: str):
        attr_key = self._get_column(self._key)
        stmt = sqldelete(self._model).where(attr_key == key)
        session.execute(stmt)

    async def ahard_delete(self, session, key: str):
        attr_key = self._get_column(self._key)
        stmt = sqldelete(self._model).where(attr_key == key)
        await session.execute(stmt)

    async def soft_delete(self, session, key: str):
        obj = self._get_one(session, key)
        setattr(obj, self._active_key, False)
        obj.updated_at = datetime.utcnow()
        session.add(obj)

    async def asoft_delete(self, session, key: str):
        obj = await self._aget_one(session, key)
        setattr(obj, self._active_key, False)
        obj.updated_at = datetime.utcnow()
        session.add(obj)
