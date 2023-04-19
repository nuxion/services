import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import declarative_mixin, declared_attr


def tsvector_column(fields="title || ' ' || description", lang="english"):
    return sa.Column(
        TSVECTOR,
        sa.Computed(f"to_tsvector('{lang}', {fields})", persisted=True),
    )


def search_stmt(model, text, lang="english", field="tsvector"):
    col = getattr(model, field)
    stmt = sa.select(model).where(col.bool_op("@@")(sa.func.websearch_to_tsquery(text)))

    return stmt


@declarative_mixin
class WithSearchField:
    # searcheable = sa.Column(TSVECTOR, sa.Computed)

    @declared_attr
    def __table_args__(cls):
        return (
            sa.Index(
                f"idx__{cls.__tablename__}__tsvector",
                "tsvector",
                postgresql_using="gin",
            ),
        )

    @classmethod
    def websearch(cls, text, field="tsvector"):
        col = getattr(cls, field)
        stmt = sa.select(cls).where(
            col.bool_op("@@")(sa.func.websearch_to_tsquery(text))
        )
        return stmt


class MixinSearch:
    @classmethod
    def fulltext_search(cls, search_string, field, lang="english"):
        return sa.select(cls).filter(
            sa.func.websearch_to_tsquery(lang, getattr(cls, field)).match(
                search_string, postgresql_regconfig=lang
            )
        )
