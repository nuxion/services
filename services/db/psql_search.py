import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import declarative_mixin, declared_attr


def tsvector_column(fields="title || ' ' || description", lang="english"):
    return sa.Column(
        TSVECTOR,
        sa.Computed(f"to_tsvector('{lang}', {fields})", persisted=True),
    )


def search_stmt(model, text, field="tsvector"):
    col = getattr(model, field)
    stmt = sa.select(model).where(col.bool_op("@@")(sa.func.websearch_to_tsquery(text)))

    return stmt


def search_with_rank_stmt(model, text, field="tsvector"):
    """Returns a tuple with the model and the rank value

    check: https://www.postgresql.org/docs/current/textsearch-controls.html

    used as:

    .. code-block:: python


        stmt = search_with_rank_stmt(PersonModel, "google")
        with db.session() as s:
            res = s.execute(stmt)
            values = list(res)

    """
    col = getattr(model, field)
    stmt = sa.select(
        model, sa.func.ts_rank_cd(col, sa.func.websearch_to_tsquery(text)).label("rank")
    ).where(col.bool_op("@@")(sa.func.websearch_to_tsquery(text)))
    # stmt = sa.select(model.id, sa.func.ts_rank_cd(col, sa.func.websearch_to_tsquery(text), 0).label("rank"))
    # stmt = stmt.order_by(sa.desc(sa.func.ts_rank_cd(col, sa.func.websearch_to_tsquery(text))))
    stmt = stmt.order_by(sa.desc("rank"))

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
