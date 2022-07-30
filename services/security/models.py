# pylint: disable=too-few-public-methods
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict

from services.db.common import Base
from sqlalchemy import (BigInteger, Boolean, Column, DateTime, Float,
                        ForeignKey, Integer, String, UniqueConstraint)
# from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.orm import declarative_mixin, declared_attr, relationship
from sqlalchemy.schema import Table
from sqlalchemy.sql import functions
from sqlalchemy.types import BINARY


@declarative_mixin
class UserMixin:

    id = Column(BigInteger, primary_key=True)
    username = Column(String(), index=True, unique=True, nullable=False)
    _password = Column("passwowrd", BINARY, nullable=True)
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


class UserModel(UserMixin, Base):
    __tablename__ = "srv_user"
    __mapper_args__ = {"eager_defaults": True}

    email = Column(String(), index=True, nullable=True, unique=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "password": self.password,
            "email": self.email,
            "is_superuser": self.is_superuser,
            "is_active": self.is_active,
            "scopes": self.scopes,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
