from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from sqlalchemy import delete as sqldelete
from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.attributes import InstrumentedAttribute

from services.errors import DBObjectNotFound
from services.security import PasswordScript
from services.users2.models import UserMixin

UserT = TypeVar("UserT", bound=UserMixin)


class UserManager(Generic[UserT]):
    def __init__(self, user_model: UserT, group_model: GroupT, salt: str):
        self._model = user_model
        self._group = group_model
        self._salt = salt

    def verify_password(
        self, original_password: bytes, *, to_verify: str, salt: Union[bytes, str]
    ) -> bool:
        pm = PasswordScript(salt)
        verified = pm.verify(to_verify, original_password)
        if verified:
            return True
        return False

    def encrypt_password(self, password, salt: Union[bytes, str]) -> bytes:
        pm = PasswordScript(salt)
        encrypted = pm.encrypt(password)
        return encrypted

    async def list_users(
        self, session, order_by=None, is_active=True, offset=0, limit=10
    ) -> List[UserT]:
        stmt = select(self._model).offset(offset).limit(limit)
        if is_active:
            stmt = stmt.where(self._model.is_active == True)
        if order_by:
            stmt.order_by(order_by, desc(order_by))
        result = await session.execute(stmt)
        return list(result.scalars())

    def _user_or_raise(
        self, username, user_object: Union[UserT, None], is_active=True
    ) -> UserT:
        if not user_object:
            raise UserNotFound(username)
        if is_active:
            if not user_object.is_active:
                raise UserNotFound(username)

        return user_object

    async def get(self, session, username: str, is_active=True) -> UserT:
        stmt = select(self._model).where(self._model.username == username).limit(1)
        rsp = await session.execute(stmt)
        _user = rsp.scalar_one_or_none()
        return self._user_or_raise(username, _user, is_active)

    async def register(
        self, session, data: Dict[str, Any], default_group=None
    ) -> Union[UserT, None]:
        _copy = data.copy()
        _copy["password"] = self.encrypt_password(_copy["password"], self._salt)

        um = self._model(**data)
        if default_group:
            select()

        session.add(um)
        try:
            await session.commit()
            return um
        except IntegrityError:
            await session.rollback()
            return None

    async def _get_user(self, session, username: str) -> UserT:
        stmt = select(self._model).where(self._model.username == username).limit(1)
        rsp = await session.execute(stmt)

        return rsp.scalar_one_or_none()

    async def update(self, session, username: str, data: Dict[str, Any]):
        u = await self._get_user(session, username)
        if not u:
            raise UserNotFound(username)

        for k, v in data.items():
            setattr(u, k, v)
        u.updated_at = datetime.utcnow()
        session.add(u)
        await session.commit()

    async def delete_hard(self, session, username: str):
        stmt = sqldelete(self._model).where(self._model.username == username)
        await session.execute(stmt)

    async def delete(self, session, username: str):
        u = await self._get_user(session, username)
        u.is_active = False
        u.updated_at = datetime.utcnow()
        session.add(u)

    async def change_pass(self, session, username: str, new_password: str):
        u = await self._get_user(session, username)
        if not u:
            raise UserNotFound(username)
        pass_ = self.encrypt_password(new_password, salt=self._salt)
        u.password = pass_
        u.updated_at = datetime.utcnow()
        session.add(u)
