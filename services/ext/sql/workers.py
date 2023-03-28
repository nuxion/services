import asyncio
import contextlib
from typing import Any, List, Dict
from datetime import datetime
from functools import partial

from sqlalchemy import JSON, Column, DateTime, Integer, MetaData, String, Table, text
from sqlalchemy import delete as sqldelete
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.sql import functions

from services.db import async_vacuum, async_set_pragma
from services.workers import (
    IState,
    Task,
    elapsed_time_from_finish,
    TaskStatus,
    elapsed_time_from_start,
)


class SQLBackend(IState):
    def __init__(
        self,
        engine: AsyncEngine,
        meta=MetaData(),
        table_state="tasks_state",
        # table_history="tasks_history",
    ):
        self.meta = meta
        self._tasks = self._create_tasks_table(table_state)
        # self._history = self._create_tasks_table(table_history)
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
    async def from_uri(cls, uri: str, extra: Dict[str, Any] = {}) -> IState:
        _echo = extra.get("echo", False)
        _table = extra.get("table_state", "tasks_state")
        _wal = extra.get("wal", True)
        engine = create_async_engine(uri, echo=_echo)
        if _wal:
            await async_set_pragma(engine)

        obj = cls(engine, table_state=_table)
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
                .values(state=status, updated_at=now)
            )
            await conn.execute(stmt)

        return True

    async def delete_task(self, taskid: str) -> bool:
        async with self.begin() as conn:
            r = await self._delete(conn, taskid)
        return r

    async def _delete(self, conn, taskid: str) -> bool:
        stmt = sqldelete(self._tasks).where(self._tasks.c.id == taskid)
        await conn.execute(stmt)
        return True

    async def get_result(self, taskid: str) -> Dict[str, Any]:
        async with self.conn() as conn:
            stmt = select(self._tasks).where(self._tasks.c.id == taskid).limit(1)
            res = await conn.execute(stmt)
            row = res.fetchone()
            task_dict = dict(row)
        return task_dict["result"]

    async def set_result(self, taskid: str, *, result: Dict[str, Any], status: str):
        async with self.begin() as conn:
            await self._set_result(conn, taskid, result, status)

    async def _set_result(
        self,
        conn,
        taskid: str,
        result: Dict[str, Any],
        status: str,
    ):
        now = datetime.utcnow()
        stmt = (
            update(self._tasks)
            .where(self._tasks.c.id == taskid)
            .values(result=result, updated_at=now, state=status)
        )
        await conn.execute(stmt)

    async def _vacuum(self):
        await async_vacuum(self.engine, self._tasks.name)

    async def clean_failed(self) -> List[str]:
        async with self.conn() as conn:
            stmt = select(self._tasks).where(
                self._tasks.c.state == TaskStatus.failed.value
            )
            res = await conn.execute(stmt)
            rows = res.fetchall()
            tasks = [Task(**dict(r)) for r in rows]
        # futures = []
        tasks_ids = []
        async with self.begin() as conn:
            for t in tasks:
                elapsed = elapsed_time_from_finish(t)
                if elapsed > t.result_ttl:
                    # futures.append(self.delete_task(t.id))
                    await self._delete(conn, t.id)
                    tasks_ids.append(t.id)

        # await asyncio.gather(*futures, return_exceptions=True)
        return tasks_ids

    async def _clean_done(self):
        async with self.conn() as conn:
            stmt = select(self._tasks).where(
                self._tasks.c.state == TaskStatus.done.value
            )
            res = await conn.execute(stmt)
            rows = res.fetchall()
            tasks = [Task(**dict(r)) for r in rows]

        # futures = []
        async with self.begin() as conn:
            for t in tasks:
                elapsed = elapsed_time_from_finish(t)
                if elapsed > t.result_ttl:
                    await self._delete(conn, t.id)
                # futures.append(self.delete_task(t.id))
        # await asyncio.gather(*futures, return_exceptions=False)

    async def _move_to_failed(self):
        async with self.conn() as conn:
            stmt = select(self._tasks).where(
                self._tasks.c.state == TaskStatus.created.value
            )
            res = await conn.execute(stmt)
            rows = res.fetchall()
            tasks = [Task(**dict(r)) for r in rows]

        # futures = []
        async with self.begin() as conn:
            for t in tasks:
                elapsed = elapsed_time_from_start(t)
                if elapsed > t.timeout:
                    _res = {"error": "timeout, could be running"}
                    # futures.append(
                    #    self.set_result(t.id, result=_res, status=TaskStatus.failed.value)
                    # )
                    await self._set_result(
                        conn, t.id, result=_res, status=TaskStatus.failed.value
                    )
            # await asyncio.gather(*futures, return_exceptions=True)

    async def clean(self):
        await self._clean_done()
        await self._move_to_failed()
