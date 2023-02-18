from typing import Any, Dict


from services.users.models import UserMixin

from sqlalchemy import BigInteger, Column, String

from .db import Base



class UserModel(UserMixin, Base):
    __tablename__ = "example_user"
    __mapper_args__ = {"eager_defaults": True}

    fullname = Column(String(), nullable=True)

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
            "updated_at": self.updated_at
        }


class ExampleModel(Base):

    __tablename__ = "example_example"
    __mapper_args__ = {"eager_defaults": True}

    id = Column(BigInteger, primary_key=True)
    name = Column(String())