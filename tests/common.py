from services.db import AsyncSQL, SQL
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy.ext.compiler import compiles
from services.db import SQL, AsyncSQL
from services.db.mixins import BaseMixinAsDataclass
from sqlalchemy.types import BINARY, JSON, BigInteger

# equivalent to Base = declarative_base()


class Base(DeclarativeBase):
    pass


class TestModel(BaseMixinAsDataclass, Base):
    __test__ = False
    __tablename__ = "testing"
    __mapper_args__ = {"eager_defaults": True}
    fullname: Mapped[str] = mapped_column(String)


async def async_create_all(db: AsyncSQL):
    await db.create_all(Base.metadata)


def create_all(db: SQL):
    db.create_all(Base.metadata)


@compiles(JSON, "postgresql")
def compile_jsonb_postgres(type_, compile, **kw):
    return "JSONB"


@compiles(BINARY, "postgresql")
def compile_bytea_postgres(type_, compiler, **kw):
    return "BYTEA"


@compiles(BigInteger, "sqlite")
def compile_integer_sqlite(type_, compiler, **kw):
    return "Integer"
