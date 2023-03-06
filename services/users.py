from typing import Any, Dict

from sqlalchemy import BigInteger, Boolean, Column, DateTime, String

# from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.orm import declarative_mixin
from sqlalchemy.sql import functions
from sqlalchemy.types import BINARY


@declarative_mixin
class UserMixin:
    id = Column(BigInteger, primary_key=True)
    username = Column(String(), index=True, unique=True, nullable=False)
    password = Column("password", BINARY, nullable=True)
    email = Column(String(), index=True, nullable=True, unique=True)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    scopes = Column(String(), default="user", nullable=False)

    created_at = Column(
        DateTime(),
        server_default=functions.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(),
        server_default=functions.now(),
        nullable=False,
    )

    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError()

    def __repr__(self):
        return f"<UserModel: {self.id}:{self.username}>"


@declarative_mixin
class GroupMixin:
    id = Column(BigInteger, primary_key=True)
    group_name = Column(String(16), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(),
        server_default=functions.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(),
        server_default=functions.now(),
        nullable=False,
    )

    def __repr__(self):
        return f"<GroupModel: {self.id}:{self.group_name}>"
