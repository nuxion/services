import math
from dataclasses import dataclass

from sqlalchemy import Table, func, select
from sqlalchemy.sql.selectable import Select


@dataclass
class NextPage:
    offset: int
    limit: int
    page: int
    next_page: int
    total: int
    total_pages: int


@dataclass
class Pagination:
    total: int
    limit: int = 100

    def calculate(self, page: int) -> NextPage:
        """ agnostic pagination, if it's the end it will returns
        -1 as the last page
        """
        total_pages = int(math.ceil(self.total/self.limit))
        _offset = self.limit * (page - 1)
        next_page = page + 1
        next_offset = self.limit * page
        if next_offset >= self.total:
            next_page = -1
        # print(
        #     f"limit: {self.limit}, offset: {_offset}, next_page: {next_page}")
        return NextPage(offset=_offset,
                        page=page,
                        next_page=next_page,
                        limit=self.limit,
                        total=self.total,
                        total_pages=total_pages)


async def get_total_async(session, Model):
    """Should be made in a context manager"""
    stmt = select(func.count(Model.id))
    _total = await session.execute(stmt)
    total = _total.scalar()

    return total


def get_total(session, Model):
    """Should be made in a context manager"""
    stmt = select(func.count(Model.id))
    _total = session.execute(stmt)
    total = _total.scalar()

    return total


def get_total_table(session, table: Table) -> int:
    stmt = select([func.count()]).select_from(table)
    res = session.execute(stmt).scalar()
    return res


async def get_total_table_async(session, table: Table) -> int:
    stmt = select([func.count()]).select_from(table)
    res = await session.execute(stmt)
    return res.scalar()
