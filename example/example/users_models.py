from typing import Any, Dict

from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import declarative_mixin, declared_attr, relationship
from sqlalchemy.schema import Table

from services.users import GroupMixin, UserMixin

from .db import Base

user_group_table = Table(
    "example_user_group",
    Base.metadata,
    Column(
        "user_id",
        BigInteger,
        ForeignKey(
            "example_user.id",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
    ),
    Column(
        "group_id",
        BigInteger,
        ForeignKey(
            "example_group.id",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
    ),
)


@declarative_mixin
class HasOwnerMixin:
    # pylint: disable=no-self-argument

    @declared_attr
    def owner_id(cls):
        return Column(
            String(16),
            ForeignKey("example_user.id", ondelete="SET NULL"),
            nullable=True,
        )

    @declared_attr
    def owner(cls):
        return relationship("UserModel")


class UserModel(UserMixin, Base):
    __tablename__ = "example_user"
    __mapper_args__ = {"eager_defaults": True}

    fullname = Column(String(), nullable=True)
    groups = relationship(
        "GroupModel",
        secondary=user_group_table,
        back_populates="users",
        lazy="selectin",
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "password": self.password,
            "fullname": self.fullname,
            "email": self.email,
            "is_superuser": self.is_superuser,
            "is_active": self.is_active,
            "scopes": self.scopes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class GroupModel(GroupMixin, Base):
    __tablename__ = "example_group"
    users = relationship(
        "UserModel",
        secondary=user_group_table,
        back_populates="groups",
        lazy="selectin",
    )

    __mapper_args__ = {"eager_defaults": True}