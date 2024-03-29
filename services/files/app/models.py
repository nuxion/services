from typing import Any, Dict
from pydantic import BaseModel
from sqlalchemy import BigInteger, Column, String
# from services.db.psql_search import WithSearchField, tsvector_column
{% if data.users -%}
from {{ data.app_name}}.users_models import UserModel, GroupModel, user_group_table
{% endif -%}
from services.db.secrets import SecretMixin

from .db import Base


# class SearchExampleModel(Base, WithSearchField):
#     __tablename__ = "{{ data.app_name }}_example"
#     __mapper_args__ = {"eager_defaults": True}
# 
#     id = Column(BigInteger, primary_key=True)
#     name = Column(String())
#     title = Column(String())
#     description = Column(String())
#     tsvector = tsvector_column()

class ExampleModel(Base):
    __tablename__ = "{{ data.app_name }}_example"
    __mapper_args__ = {"eager_defaults": True}

    id = Column(BigInteger, primary_key=True)
    name = Column(String())
    title = Column(String())
    description = Column(String())


class SecretsModel(Base, SecretMixin):
    __tablename__ = "{{ data.app_name }}_secrets"
    __mapper_args__ = {"eager_defaults": True}
