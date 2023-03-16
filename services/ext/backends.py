import contextlib
from typing import Any, List
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Integer, MetaData, String, Table
from sqlalchemy import delete as sqldelete
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.sql import functions

from services.workers import IState, Task


class SQLBackend(IState):
    def __init__(
        self,
        engine: AsyncEngine,
        meta=MetaData(),
        table_state="tasks_state",
        table_history="tasks_history",
    ):
        self.meta = meta
        self._tasks = self._create_tasks_table(table_state)
        self._history = self._create_tasks_table(table_history)
        self.engine = engine

    async def _dispose(self):
        await self.engine.dispose()

    @contextlib.asynccontextmanager
    async def conn(self):
        try:
            async with self.engine.connect() as conn:
                yield conn
        finally:
            await self.engine.dispose()

    @contextlib.asynccontextmanager
    async def begin(self):
        try:
            async with self.engine.begin() as conn:
                yield conn
        finally:
            await self.engine.dispose()

    async def create_all(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(self.meta.create_all)

    @classmethod
    async def from_uri(
        cls,
        uri,
        table_state="tasks_state",
        table_history="tasks_history",
        meta=MetaData(),
        echo=True,
    ) -> "SQLBackend":
        engine = create_async_engine(uri, echo=echo)
        obj = cls(
            engine, meta=meta, table_state=table_state, table_history=table_history
        )
        await obj.create_all()
        return obj

    def _create_tasks_table(self, name):
        tbl = Table(
            name,
            self.meta,
            Column("id", String(), primary_key=True),
            Column("name", String()),
            Column("params", JSON(), nullable=True),
            Column("state", String(), index=True),
            Column("app_name", String(), index=True),
            Column("result", JSON, nullable=True),
            Column("timeout", Integer()),
            Column("result_ttl", Integer()),
            Column(
                "created_at",
                DateTime(),
                index=True,
                server_default=functions.now(),
                nullable=False,
            ),
            Column(
                "updated_at",
                DateTime(),
                server_default=functions.now(),
                nullable=False,
            ),
            extend_existing=True,
        )
        return tbl

    def _create_history_table(self, name):
        tbl = Table(
            name,
            self.meta,
            Column("id", String(), primary_key=True),
            Column("name", String()),
            Column("app_name", String(), index=True),
            Column("state", String()),
            Column(
                "created_at",
                DateTime(),
                index=True,
                server_default=functions.now(),
                nullable=False,
            ),
            extend_existing=True,
        )
        return tbl

    async def add_task(self, task: Task):
        async with self.begin() as conn:
            await conn.execute(self._tasks.insert(), [task.dict()])
            # await conn.commit()

    async def get_task(self, taskid: str) -> Task:
        async with self.conn() as conn:
            stmt = select(self._tasks).where(self._tasks.c.id == taskid).limit(1)
            res = await conn.execute(stmt)
            row = res.fetchone()
            task = Task(**dict(row))
        return task

    async def list_tasks(self) -> List[Task]:
        async with self.conn() as conn:
            stmt = select(self._tasks)
            res = await conn.execute(stmt)
            rows = res.fetchall()
            tasks = [Task(**dict(r)) for r in rows]
        return tasks

    async def update_status(self, taskid: str, status: str) -> bool:
        now = datetime.utcnow()
        async with self.begin() as conn:
            stmt = (
                update(self._tasks)
                .where(self._tasks.c.id == taskid)
                .values(status=status, updated_at=now)
            )
            await conn.execute(stmt)
        return True

    async def delete_task(self, taskid: str) -> bool:
        async with self.begin() as conn:
            stmt = sqldelete(self._tasks).where(self._tasks.c.id == taskid)
            await conn.execute(stmt)
        return True

    async def get_result(self, taskid: str) -> Any:
        async with self.conn() as conn:
            stmt = select(self._tasks).where(self._tasks.c.id == taskid).limit(1)
            res = await conn.execute(stmt)
            row = res.fetchone()
            task_dict = dict(row)
        return task_dict["result"]

    async def set_result(self, taskid: str, result: Any):
        now = datetime.utcnow()
        async with self.begin() as conn:
            stmt = (
                update(self._tasks)
                .where(self._tasks.c.id == taskid)
                .values(result=result, updated_at=now)
            )
            await conn.execute(stmt)
