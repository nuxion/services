from typing import Any, Dict
from pydantic import BaseModel
from sqlalchemy import BigInteger, Column, String
from services.db.psql_search import WithSearchField, tsvector_column
{% if data.users -%}
from {{ data.app_name}}.users_models import UserModel, GroupModel, user_group_table
{% endif -%}

from .db import Base


class ExampleModel(Base, WithSearchField):
    __tablename__ = "{{ data.app_name }}_example"
    __mapper_args__ = {"eager_defaults": True}

    id = Column(BigInteger, primary_key=True)
    name = Column(String())
    title = Column(String())
    description = Column(String())
    tsvector = tsvector_column()

{% if data.tasks -%}
class TaskExample(BaseModel):
    do: str
    wait: int
{% endif -%}


