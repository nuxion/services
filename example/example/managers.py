from datetime import datetime
from typing import Any, Dict, Union

from services.db.managers import AsyncManagerBase
from services.errors import (
    AuthValidationFailed,
    DBObjectNotFound,
    GroupNotFound,
    UserNotFound,
)
from services.security import PasswordScript

from .users_models import GroupModel, UserModel


class GroupManager(AsyncManagerBase[GroupModel]):
    model_class = "example.users_models.GroupModel"
    lookup_key = "group_name"

    async def assign_user(self, session, group_name, user: UserModel):
        group = await self.get(session, group_name)
        group.users.append(user)
        session.add(group)


class UserManager(AsyncManagerBase[UserModel]):
    model_class = "example.users_models.UserModel"
    lookup_key = "username"

    def __init__(self, salt: str, groups: GroupManager):
        super().__init__()
        self.groups = groups
        self._salt = salt

    async def assign_group(self, session, group_name: str, user: UserModel):
        await self.groups.assign_user(session, group_name, user)

    async def register(
        self, session, data: Dict[str, Any], default_group="users"
    ) -> Union[UserModel, None]:
        _copy = data.copy()
        _copy["password"] = self.encrypt_password(_copy["password"], self._salt)

        um = await self.create(session, _copy, commit=False)
        if default_group and um:
            try:
                await self.groups.assign_user(session, default_group, um)
            except DBObjectNotFound:
                raise GroupNotFound(default_group)

        res = await self._commit_or_rollback(session)
        if not res:
            return None
        return um

    async def create_group(self, session, group_name) -> GroupModel:
        return await self.groups.create(session, {"group_name": group_name})

    async def authenticate(
        self, session, *, username: str, to_verify: str
    ) -> UserModel:
        try:
            user = await self.get(session, username)
            is_valid = self.verify_password(
                user.password, to_verify=to_verify, salt=self._salt
            )
            if not is_valid:
                raise AuthValidationFailed()
            return user

        except DBObjectNotFound:
            raise AuthValidationFailed()

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

    async def change_pass(self, session, username: str, new_password: str):
        u = await self._get_one(session, username)
        if not u:
            raise UserNotFound(username)
        pass_ = self.encrypt_password(new_password, salt=self._salt)
        u.password = pass_
        u.updated_at = datetime.utcnow()
        session.add(u)