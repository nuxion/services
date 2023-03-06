from sqlalchemy.orm import registry as sql_registry
from sqlalchemy.ext.compiler import compiles
from services.db import SQL, AsyncSQL
from sqlalchemy.types import BINARY, JSON, BigInteger

# equivalent to Base = declarative_base()

registry = sql_registry()
Base = registry.generate_base()


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
