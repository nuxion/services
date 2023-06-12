import datetime

from sqlalchemy import DateTime
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column
from sqlalchemy.sql import functions

# from sqlalchemy.types import BINARY, DECIMAL, JSON, BigInteger


# from sqlalchemy.ext.compiler import compiles


class MutableList(Mutable, list):
    """This allow modify an ARRAY custom type
    From https://gist.github.com/kirang89/22d111737af0fca251e3

    """

    def __setitem__(self, key, value):
        list.__setitem__(self, key, value)
        self.changed()

    def __delitem__(self, key):
        list.__delitem__(self, key)
        self.changed()

    def append(self, value):
        list.append(self, value)
        self.changed()

    def pop(self, index=0):
        value = list.pop(self, index)
        self.changed()
        return value

    @classmethod
    def coerce(cls, key, value):
        if not isinstance(value, MutableList):
            if isinstance(value, list):
                return MutableList(value)
            return Mutable.coerce(key, value)
        else:
            return value


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
