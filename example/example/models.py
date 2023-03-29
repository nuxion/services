from typing import Any, Dict
from pydantic import BaseModel
from sqlalchemy import BigInteger, Column, String
from example.users_models import UserModel, GroupModel, user_group_table
from .db import Base


class ExampleModel(Base):
    __tablename__ = "example_example"
    __mapper_args__ = {"eager_defaults": True}

    id = Column(BigInteger, primary_key=True)
    name = Column(String())

class TaskExample(BaseModel):
    do: str
    wait: int
