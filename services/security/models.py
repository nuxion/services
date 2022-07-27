# pylint: disable=too-few-public-methods
from datetime import datetime

from services.db.common import Base
from sqlalchemy import (BigInteger, Boolean, Column, DateTime, Float,
                        ForeignKey, Integer, String, UniqueConstraint)
# from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import declarative_mixin, declared_attr, relationship
from sqlalchemy.schema import Table
from sqlalchemy.sql import functions
from sqlalchemy.types import BINARY


@declarative_mixin
class UserMixin:

    id = Column(BigInteger, primary_key=True)
    password = Column(BINARY, nullable=True)
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


class UserModel(UserMixin, Base):
    __tablename__ = "user"
    __mapper_args__ = {"eager_defaults": True}

    username = Column(String(), index=True, unique=True, nullable=False)
    email = Column(String(), index=True, nullable=True)
