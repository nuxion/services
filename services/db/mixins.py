import datetime

from sqlalchemy import DateTime, BigInteger
from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column, MappedAsDataclass
from sqlalchemy.sql import functions

# from sqlalchemy.types import BINARY, DECIMAL, JSON, BigInteger


@declarative_mixin
class DateTrackMixin:
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(),
        server_default=functions.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(),
        server_default=functions.now(),
        nullable=False,
    )


@declarative_mixin
class DateTrackMixinAsDataclass(MappedAsDataclass):
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(), server_default=functions.now(), nullable=False, init=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(), server_default=functions.now(), nullable=False, init=False
    )


@declarative_mixin
class BaseMixinAsDataclass(MappedAsDataclass):
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, init=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(),
        index=True,
        init=False,
        server_default=functions.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(),
        init=False,
        server_default=functions.now(),
        nullable=False,
    )
