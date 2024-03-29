from sqlalchemy.ext.mutable import Mutable

# from sqlalchemy.ext.compiler import compiles


# @compiles(JSON, "postgresql")
# def compile_jsonb_postgres(type_, compile, **kw):
#     return "JSONB"
#
#
# @compiles(BINARY, "postgresql")
# def compile_bytea_postgres(type_, compiler, **kw):
#     return "BYTEA"
#
#
# @compiles(BigInteger, "sqlite")
# def compile_integer_sqlite(type_, compiler, **kw):
#     return "Integer"
#

# @compiles(DECIMAL, "sqlite")
# def compile_integer_sqlite(type_, compiler, **kw):
#     return "Text"


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
