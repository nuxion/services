from sqlalchemy import BigInteger, Boolean, Column, DateTime, String

# from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.orm import declarative_mixin
from sqlalchemy.sql import functions
from sqlalchemy.types import BINARY


@declarative_mixin
class SecretMixin:
    id = Column(BigInteger, primary_key=True)
    key = Column(String, unique=True, nullable=False, index=True)
    secret = Column(BINARY, nullable=True)
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

    def __repr__(self):
        return f"<SecretModel: {self.key}>"
