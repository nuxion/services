from datetime import datetime
from functools import wraps
from inspect import isawaitable
from typing import Any, Dict, List, Optional, Union

from pydantic.error_wrappers import ValidationError
from sanic import Request
from services.security import AuthSpec, PasswordScript, get_delta
from services.utils import get_class
from sqlalchemy import delete
from sqlalchemy import insert as sqlinsert
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from .errors import (AuthValidationFailed, InvalidUser,
                     MissingAuthorizationHeader, WebAuthFailed)
from .models import UserMixin, UserModel
from .types import JWTResponse, UserLogin, UserOrm


class UserManager:

    def __init__(self, model_class: str, salt: Optional[str] = None):
        self._model: UserMixin = get_class(model_class)
        self._salt = salt

    @staticmethod
    def _verify_password(
        original_password: str, *, to_verify: str, salt: Union[bytes, str]
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
                           password: str) -> Dict[str, Any]:

        user = await self.get(session, username)
        if user is None:
            raise AuthValidationFailed()

        is_valid = self._verify_password(
            user.password, to_verify=password, salt=self._salt
        )
        if not is_valid or not user.is_active:
            raise AuthValidationFailed()

        return user.to_dict()

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
            session.flush()
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


# async def authenticate(request: Request, *args, **kwargs) -> UserOrm:
#     try:
#         creds = UserLogin(**request.json)
#     except ValidationError as e:
#         raise AuthValidationFailed()
#
#     session = request.ctx.session
#     async with session.begin():
#         user = await get_user_async(session, creds.username)
#         if user is None:
#             raise AuthValidationFailed()
#
#         is_valid = verify_password(
#             user, creds.password, salt=request.app.config.AUTH_SALT
#         )
#         if not is_valid:
#             raise AuthValidationFailed()
#
#         return UserOrm.from_orm(user)
#
#
# def inject_user(func):
#     """Inject a user"""
#
#     def decorator(f):
#         @wraps(f)
#         async def decorated_function(request, *args, **kwargs):
#             token = request.ctx.token_data
#             session = request.ctx.session
#             user = get_user_async(session, token["usr"])
#             if isawaitable(user):
#                 user = await user
#             if not user:
#                 raise WebAuthFailed("Authentication failed")
#             user_orm = model2orm(user)
#             response = f(request, user=user_orm, *args, **kwargs)
#             if isawaitable(response):
#                 response = await response
#
#             return response
#
#         return decorated_function
#
#     return decorator(func)
