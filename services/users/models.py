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

