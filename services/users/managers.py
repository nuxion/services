from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from services.db.sqlhelper import AsyncSQL
from services.errors import UserNotFound, AuthValidationFailed
from services.security import AuthSpec, PasswordScript
from services.types import JWTConfig, JWTResponse
from services.utils import get_class
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from .base import UserManagerSpec, UserSpec
from .models import UserMixin


class UserManager(UserManagerSpec):

    def __init__(self, auth: AuthSpec,
                 *,
                 db: AsyncSQL,
                 model_class: str,
                 salt: Optional[str] = None):
        self._model: UserMixin = get_class(model_class)
        self._salt = salt
        self.db = db
        self.auth = auth

    def verify_password(self,
                        original_password: bytes, *,
                        to_verify: str,
                        salt: Union[bytes, str]
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

    async def authenticate(self, username: str, *,
                           password: str) -> UserSpec:

        async with self.db.session_factory() as session:
            user = await self._get(session, username)
            if user is None:
                raise AuthValidationFailed()

            is_valid = self.verify_password(
                user.password, to_verify=password, salt=self._salt
            )
            if not is_valid or not user.is_active:
                raise AuthValidationFailed()

            return self._to_spec(user)

    def _to_spec(self, user: UserMixin) -> UserSpec:
        return UserSpec(
            id=user.id,
            username=user.username,
            email=user.email,
            is_superuser=user.is_superuser,
            is_active=user.is_active,
            scopes=user.scopes.split(","),
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    def _user_or_raise(self, username,
                       user_object: Union[UserMixin, None]) -> UserSpec:
        if not user_object:
            raise UserNotFound(username)
        return self._to_spec(user_object)

    async def list_users(self, filter_active=True) -> List[UserSpec]:
        stmt = select(self._model)
        if filter_active:
            stmt.where(self._model.is_active == True)
        async with self.db.session_factory() as session:
            result = await session.execute(stmt)
            return [self._to_spec(r[0]) for r in result]

    async def get(self, username: str) -> UserSpec:

        stmt = select(self._model)\
            .where(self._model.username == username)\
            .limit(1)

        async with self.db.session_factory() as session:
            rsp = await session.execute(stmt)

            _user = rsp.scalar_one_or_none()
        return self._user_or_raise(username, _user)

    async def _get(self, session, username: str) -> UserMixin:
        stmt = select(self._model)\
            .where(self._model.username == username)\
            .limit(1)

        rsp = await session.execute(stmt)

        return rsp.scalar_one_or_none()

    async def register(self, data: Dict[str, Any]) -> Union[UserSpec, None]:

        data["password"] = self.encrypt_password(data["password"], self._salt)

        um = self._model(**data)

        async with self.db.session_factory() as session:
            session.add(um)
            try:
                await session.commit()
                return self._to_spec(um)
            except IntegrityError:
                await session.rollback()
            return None

    async def update(self, username: str, data: Dict[str, Any]):
        async with self.db.session_factory() as session:
            u = await self._get(session, username)
            if not u:
                raise UserNotFound(username)

            for k, v in data.items():
                setattr(u, k, v)
            u.updated_at = datetime.utcnow()
            session.add(u)

    async def delete(self, username: str):

        async with self.db.session_factory() as session:
            stmt = delete(self._model).where(self._model.username == username)
            await session.execute(stmt)

    async def change_pass(self, session, username: str, new_password: str):
        async with self.db.session_factory() as session:
            u = await self._get(session, username)
            if not u:
                raise UserNotFound(username)
            pass_ = self.encrypt_password(new_password, salt=self._salt)
            u.password = pass_
            u.updated_at = datetime.utcnow()
            session.add(u)

    async def generate_token(self, user: UserSpec, exp=None) -> JWTResponse:

        payload = {
            "usr": user.username, "scopes": user.scopes
        }
        encoded = self.auth.encode(payload)
        rftkn = None
        if self.auth.store:
            rftkn = await self.auth.store_refresh_token(user.username)
        return JWTResponse(
            access_token=encoded,
            refresh_token=rftkn
        )

    async def refresh_token(self, old_token: JWTResponse) -> JWTResponse:
        new_jwt = await self.auth.refresh_token(
            old_token.access_token, old_token.refresh_token)
        return new_jwt
