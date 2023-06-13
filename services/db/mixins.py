import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column
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
