from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from services.security import PasswordScript
from services.security.errors import AuthValidationFailed, InvalidUser
from services.utils import get_class
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from .models import UserMixin


class UserManager:

    def __init__(self, model_class: str, salt: Optional[str] = None):
        self._model: UserMixin = get_class(model_class)
        self._salt = salt

    @staticmethod
    def _verify_password(
        original_password: bytes, *, to_verify: str, salt: Union[bytes, str]
    ) -> bool:
        pm = PasswordScript(salt)
        verified = pm.verify(to_verify, original_password)
        if verified:
            return True
        return False

    @staticmethod
    def _encrypt_password(password, salt: Union[bytes, str]) -> bytes:

        pm = PasswordScript(salt)
        encrypted = pm.encrypt(password)
        return encrypted

    async def authenticate(self, session, *,
                           username: str,
                           password: str) -> UserMixin:


        user = await self.get(session, username)
        if user is None:
            raise AuthValidationFailed()

        is_valid = self._verify_password(
            user.password, to_verify=password, salt=self._salt
        )
        if not is_valid or not user.is_active:
            raise AuthValidationFailed()

        return user

    async def list(self, session, filter_active=True) -> List[UserMixin]:
        stmt = select(self._model)
        if filter_active:
            stmt.where(self._model.is_active == True)
        result = await session.execute(stmt)
        return [r for r in result]

    async def get(self, session, username: str) -> UserMixin:
        stmt = select(self._model).where(self._model.username == username)\
                                  .limit(1)
        rsp = await session.execute(stmt)

        return rsp.scalar_one_or_none()

    async def create(self, session, data: Dict[str, Any]) -> Union[UserMixin, None]:

        data["password"] = self._encrypt_password(data["password"], self._salt)

        um = self._model(**data)
        session.add(um)
        try:
            await session.flush()
            return um
        except IntegrityError:
            pass
        return None

    async def update(self, session, username: str, data: Dict[str, Any]):
        u = await self.get(session, username)
        if not u:
            raise InvalidUser(username)

        for k, v in data.items():
            setattr(u, k, v)
        u.updated_at = datetime.utcnow()
        session.add(u)

    async def delete(self, session, username: str):
        stmt = delete(self._model).where(self._model.username == username)
        await session.execute(stmt)

    async def change_pass_async(self, session, username: str, new_password: str):
        u = await self.get(session, username)
        if not u:
            raise InvalidUser(username)
        pass_ = self._encrypt_password(new_password, salt=self._salt)
        u.password = pass_
        u.updated_at = datetime.utcnow()
        session.add(u)
