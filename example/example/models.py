from typing import Any, Dict
from pydantic import BaseModel
from sqlalchemy import BigInteger, Column, String
# from services.db.psql_search import WithSearchField, tsvector_column
from example.users_models import UserModel, GroupModel, user_group_table
from .db import Base


# class SearchExampleModel(Base, WithSearchField):
#     __tablename__ = "example_example"
#     __mapper_args__ = {"eager_defaults": True}
# 
#     id = Column(BigInteger, primary_key=True)
#     name = Column(String())
#     title = Column(String())
#     description = Column(String())
#     tsvector = tsvector_column()

class ExampleModel(Base):
    __tablename__ = "example_example"
    __mapper_args__ = {"eager_defaults": True}

    id = Column(BigInteger, primary_key=True)
    name = Column(String())
    title = Column(String())
    description = Column(String())
