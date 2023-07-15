from datetime import datetime
from typing import Any, Dict, Generic, List, TypeVar, Union

from cryptography.fernet import Fernet
from sqlalchemy import delete as sqldelete
from sqlalchemy import desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.attributes import InstrumentedAttribute

from services import types
from services.errors import DBObjectNotFound
from services.utils import get_class

ModelT = TypeVar("ModelT")


class AsyncManagerBase(Generic[ModelT]):
    model_class: str
    lookup_key: str
    active_key: str = "is_active"

    def __init__(self):
        self._model: ModelT = get_class(self.model_class)
        self._key = self.lookup_key
        self._active_key = self.active_key

    @property
    def tablename(self) -> str:
        return self._model.__tablename__

    def _get_column(self, col_name) -> InstrumentedAttribute:
        return getattr(self._model, col_name)

    async def list(
        self, session, order_by=None, is_active=True, offset=0, limit=10
    ) -> List[ModelT]:
        stmt = select(self._model).offset(offset).limit(limit)
        if is_active:
            attr = self._get_column(self._active_key)
            stmt = stmt.where(attr == True)
        if order_by:
            stmt.order_by(order_by, desc(order_by))
        result = await session.execute(stmt)
        return list(result.scalars())

    def _obj_or_raise(self, lookup, obj: Union[ModelT, None], is_active=True) -> ModelT:
        if not obj:
            raise DBObjectNotFound(self.tablename, lookup)
        if is_active:
            attr = self._get_column(self._active_key)
            if not attr:
                raise DBObjectNotFound(self.tablename, lookup)

        return obj

    async def _get_one(self, session, key: str) -> ModelT:
        attr_key = self._get_column(self._key)
        stmt = select(self._model).where(attr_key == key).limit(1)
        rsp = await session.execute(stmt)

        return rsp.scalar_one_or_none()

    async def _commit_or_rollback(self, session) -> bool:
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            return False
        return True

    async def count(self, session, is_active=True) -> int:
        stmt = select(func.count(self._model.__table__.c.id))
        if is_active:
            attr = self._get_column(self.active_key)
            stmt = stmt.where(attr == True)
        res = await session.execute(stmt)
        return res.scalar()

    async def create(
        self, session, data: Dict[str, Any], commit=True
    ) -> Union[ModelT, None]:
        model = self._model(**data)
        session.add(model)
        if commit:
            res = await self._commit_or_rollback(session)
            if not res:
                return None
        return model

    async def get(self, session, key: str, is_active=True) -> ModelT:
        _obj = await self._get_one(session, key)
        return self._obj_or_raise(key, _obj, is_active)

    async def update(self, session, key: str, data: Dict[str, Any]):
        u = await self._get_one(session, key)
        if not u:
            raise DBObjectNotFound(self.tablename, key)

        for k, v in data.items():
            setattr(u, k, v)
        u.updated_at = datetime.utcnow()
        session.add(u)

    async def _delete_hard(self, session, key: str):
        attr_key = self._get_column(self._key)
        stmt = sqldelete(self._model).where(attr_key == key)
        await session.execute(stmt)

    async def _delete_flag(self, session, key: str):
        obj = await self._get_one(session, key)
        setattr(obj, self._active_key, False)
        obj.updated_at = datetime.utcnow()
        session.add(obj)

    async def delete(self, session, key: str, hard=False):
        if hard:
            await self._delete_hard(session, key)
        else:
            await self._delete_flag(session, key)


class ManagerBase(Generic[ModelT]):
    model_class: str
    lookup_key: str
    active_key: str = "is_active"

    def __init__(self):
        self._model: ModelT = get_class(self.model_class)
        self._key = self.lookup_key
        self._active_key = self.active_key

    @property
    def tablename(self) -> str:
        return self._model.__tablename__

    def _get_column(self, col_name) -> InstrumentedAttribute:
        return getattr(self._model, col_name)

    async def list(
        self, session, order_by=None, is_active=True, offset=0, limit=10
    ) -> List[ModelT]:
        stmt = select(self._model).offset(offset).limit(limit)
        if is_active:
            attr = self._get_column(self._active_key)
            stmt = stmt.where(attr == True)
        if order_by:
            stmt.order_by(order_by, desc(order_by))
        result = await session.execute(stmt)
        return list(result.scalars())

    def _obj_or_raise(self, lookup, obj: Union[ModelT, None], is_active=True) -> ModelT:
        if not obj:
            raise DBObjectNotFound(self.tablename, lookup)
        if is_active:
            attr = self._get_column(self._active_key)
            if not attr:
                raise DBObjectNotFound(self.tablename, lookup)

        return obj

    def _get_one(self, session, key: str) -> ModelT:
        attr_key = self._get_column(self._key)
        stmt = select(self._model).where(attr_key == key).limit(1)
        rsp = session.execute(stmt)

        return rsp.scalar_one_or_none()

    def _commit_or_rollback(self, session) -> bool:
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return False
        return True

    def count(self, session, is_active=True) -> int:
        stmt = select(func.count(self._model.__table__.c.id))
        if is_active:
            attr = self._get_column(self.active_key)
            stmt = stmt.where(attr == True)
        res = session.execute(stmt)
        return res.scalar()

    def create(self, session, data: Dict[str, Any], commit=True) -> Union[ModelT, None]:
        model = self._model(**data)
        session.add(model)
        if commit:
            res = self._commit_or_rollback(session)
            if not res:
                return None
        return model

    def get(self, session, key: str, is_active=True) -> ModelT:
        _obj = self._get_one(session, key)
        return self._obj_or_raise(key, _obj, is_active)

    def update(self, session, key: str, data: Dict[str, Any]):
        u = self._get_one(session, key)
        if not u:
            raise DBObjectNotFound(self.tablename, key)

        for k, v in data.items():
            setattr(u, k, v)
        u.updated_at = datetime.utcnow()
        session.add(u)

    def _delete_hard(self, session, key: str):
        attr_key = self._get_column(self._key)
        stmt = sqldelete(self._model).where(attr_key == key)
        session.execute(stmt)

    def _delete_flag(self, session, key: str):
        obj = self._get_one(session, key)
        setattr(obj, self._active_key, False)
        obj.updated_at = datetime.utcnow()
        session.add(obj)

    def delete(self, session, key: str, hard=False):
        if hard:
            self._delete_hard(session, key)
        else:
            self._delete_flag(session, key)


class AsyncSecretBase(Generic[ModelT]):
    model_class: str
    lookup_key: str

    def __init__(self, private_key: str):
        self._private_key = private_key
        self._f = Fernet(self._private_key)
        self._model: ModelT = get_class(self.model_class)
        self._key = self.lookup_key

    def decrypt(self, encrypted: bytes) -> str:
        e = self._f.decrypt(encrypted).decode("utf-8")
        return e

    def encrypt(self, text: str) -> bytes:
        _hash = self._f.encrypt(text.encode("utf-8"))
        return _hash

    def _get_column(self, col_name) -> InstrumentedAttribute:
        return getattr(self._model, col_name)

    async def _get_one(self, session, key: str) -> ModelT:
        attr_key = self._get_column(self._key)
        stmt = select(self._model).where(attr_key == key).limit(1)
        rsp = await session.execute(stmt)

        return rsp.scalar_one_or_none()

    @property
    def tablename(self) -> str:
        return self._model.__tablename__

    async def delete(self, session, key: str):
        attr_key = self._get_column(self._key)
        stmt = sqldelete(self._model).where(attr_key == key)
        await session.execute(stmt)

    def _obj_or_raise(self, lookup, obj: Union[ModelT, None]) -> ModelT:
        if not obj:
            raise DBObjectNotFound(self.tablename, lookup)
        return obj

    async def get(self, session, key: str) -> str:
        _obj = await self._get_one(session, key)
        encrypted = self._obj_or_raise(key, _obj)
        return self.decrypt(encrypted)

    def write(self, session, key: str, data: str) -> ModelT:
        enc = self.encrypt(data)
        model = self._model(key=key, secret=enc)
        session.add(model)
        return model


class SecretBase(Generic[ModelT]):
    model_class: str
    lookup_key: str

    def __init__(self, settings: types.Settings):
        self._private_key = settings.SECURITY.secret_key
        self._f = Fernet(self._private_key)
        self._model: ModelT = get_class(self.model_class)
        self._key = self.lookup_key

    def decrypt(self, encrypted: bytes) -> str:
        e = self._f.decrypt(encrypted).decode("utf-8")
        return e

    def encrypt(self, text: str) -> bytes:
        _hash = self._f.encrypt(text.encode("utf-8"))
        return _hash

    def _get_column(self, col_name) -> InstrumentedAttribute:
        return getattr(self._model, col_name)

    def _get_one(self, session, key: str) -> ModelT:
        attr_key = self._get_column(self._key)
        stmt = select(self._model).where(attr_key == key).limit(1)
        rsp = session.execute(stmt)

        return rsp.scalar_one_or_none()

    @property
    def tablename(self) -> str:
        return self._model.__tablename__

    def delete(self, session, key: str):
        attr_key = self._get_column(self._key)
        stmt = sqldelete(self._model).where(attr_key == key)
        session.execute(stmt)

    def _obj_or_raise(self, lookup, obj: Union[ModelT, None]) -> ModelT:
        if not obj:
            raise DBObjectNotFound(self.tablename, lookup)
        return obj

    def get(self, session, key: str) -> str:
        _obj = self._get_one(session, key)
        encrypted = self._obj_or_raise(key, _obj)
        return self.decrypt(encrypted)

    def write(self, session, key: str, data: str) -> ModelT:
        enc = self.encrypt(data)
        model = self._model(key=key, secret=enc)
        session.add(model)
        return model
