import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import (
    Any,
    AsyncIterator,
    Dict,
    Generator,
    AsyncGenerator,
    List,
    Optional,
    Union,
)

import aiofiles

from services import types
from services.utils import from_async2sync, get_class, mkdir_p
from sanic.log import logger
from sanic import Sanic


def delete_file_or_dir(fpath):
    try:
        Path(fpath).unlink()
    except IsADirectoryError:
        Path(fpath).rmdir()


class KeyReadError(Exception):
    def __init__(self, bucket, key):
        msg = f"Value not found for key {key} in {bucket}"
        super().__init__(msg)


class KeyWriteError(Exception):
    def __init__(self, bucket, key):
        msg = f"Value not written for key {key} in {bucket}"
        super().__init__(msg)


class IStorage(ABC):
    """
    This is a generic KV store mostly use for project data related
    The interface is very simple allowing the common put/get actions
    either loading data in memory or streaming data for big files
    For examples about how to use some of them see tests/test_io_kv.py
    This interface is offered in a sync and async version
    """

    _bucket: str
    opts: Optional[Dict[str, Any]] = None

    @abstractmethod
    def get_bucket(self) -> types.Bucket:
        pass

    @abstractmethod
    def create_bucket(self, opts: Optional[Dict[str, str]] = None) -> types.Bucket:
        pass

    @abstractmethod
    def put(self, key: str, bdata: bytes):
        pass

    @abstractmethod
    def put_stream(self, key: str, generator: Generator[bytes, None, None]) -> bool:
        pass

    @abstractmethod
    def delete(self, key: str):
        pass

    @abstractmethod
    def list(self) -> List[str]:
        pass

    @abstractmethod
    def get(self, key: str) -> Union[bytes, str, None]:
        pass

    @abstractmethod
    def get_stream(
        self, key: str, buffer_size=256 * 1024
    ) -> Generator[bytes, None, None]:
        pass

    @staticmethod
    def create(store_class, bucket, opts: Dict[str, Any] = {}) -> "IStorage":
        Class = get_class(store_class)
        return Class(bucket, opts)

    @abstractmethod
    def download_signed(self, key, minutes=15, bucket=None) -> str:
        pass

    @abstractmethod
    def upload_signed(
        self, key, minutes=15, bucket=None, content_type="application/octed-stream"
    ) -> str:
        pass


class IAsyncStore(ABC):
    """
    This is a generic KV store mostly use for project data related
    The interface is very simple allowing the common put/get actions
    either loading data in memory or streaming data for big files
    For examples about how to use some of them see tests/test_io_kv.py
    This interface is offered in a sync and async version
    """

    _bucket: str
    opts: Optional[Dict[str, Any]] = None

    @abstractmethod
    async def create_bucket(
        self, opts: Optional[Dict[str, str]] = None
    ) -> types.Bucket:
        pass

    @abstractmethod
    async def get_bucket(self) -> types.Bucket:
        pass

    @classmethod
    @abstractmethod
    async def from_uri(
        cls, bucket, opts: Optional[Dict[str, Any]] = None
    ) -> "IAsyncStore":
        pass

    @abstractmethod
    async def put(self, key: str, bdata: bytes):
        pass

    @abstractmethod
    async def put_stream(self, key: str, generator: AsyncIterator) -> bool:
        pass

    @abstractmethod
    async def get(self, key: str) -> Union[bytes, str, None]:
        pass

    @abstractmethod
    async def list(self) -> List[str]:
        pass

    @abstractmethod
    async def delete(self, key: str):
        pass

    @abstractmethod
    async def get_stream(self, key: str, buffer_size=1024):
        pass

    @abstractmethod
    def download_signed(self, key, minutes=15, bucket=None) -> str:
        pass

    @abstractmethod
    def upload_signed(
        self, key, minutes=15, bucket=None, content_type="application/octed-stream"
    ) -> str:
        pass


class Local(IStorage):
    def __init__(self, bucket: str):
        self._opts = None
        self._bucket = bucket

    def create_bucket(self):
        mkdir_p(self._bucket)
        return types.Bucket(
            name=self._bucket,
            url=self._bucket,
            storage_class="filesystem",
            location="local",
            versioning=False,
            created_at=datetime.utcnow(),
        )

    def get_bucket(self) -> types.Bucket:
        return types.Bucket(
            name=self._bucket,
            url=self._bucket,
            storage_class="filesystem",
            location="local",
            versioning=False,
            created_at=datetime.utcnow(),
        )

    def uri(self, key):
        return f"{self._bucket}/{key}"

    def put(self, key: str, bdata: bytes):
        # obj = io.BytesIO(bdata)
        uri = self.uri(key)
        mkdir_p(Path(uri).parent)
        try:
            with open(uri, "wb") as f:
                f.write(bdata)
        except Exception as e:
            raise KeyWriteError(self._bucket, key) from e

    def put_stream(self, key: str, generator: Generator[bytes, None, None]) -> bool:
        uri = self.uri(key)
        mkdir_p(Path(uri).parent)
        try:
            with open(uri, "wb") as f:
                for chunk in generator:
                    f.write(chunk)
        except Exception as e:
            raise KeyWriteError(self._bucket, key) from e

        return True

    def get(self, key: str) -> Union[bytes, None]:
        uri = self.uri(key)
        try:
            with open(uri, "rb") as f:
                obj = f.read()
                return obj
        except Exception as e:
            raise KeyReadError(self._bucket, key) from e

    def _read_chunks(self, fobject, chunk_size=1024):
        while True:
            data = fobject.read(chunk_size)
            if not data:
                break
            yield data

    def get_stream(self, key: str, buffer_size=1024) -> Generator[bytes, None, None]:
        uri = self.uri(key)
        try:
            with open(uri, "rb") as f:
                for chunk in self._read_chunks(f, buffer_size):
                    yield chunk
        except Exception as e:
            raise KeyReadError(self._bucket, key) from e

    def list(self) -> List[str]:
        return os.listdir(self._bucket)

    def delete(self, key: str):
        delete_file_or_dir(f"{self._bucket}/{key}")

    def download_signed(self, key, minutes=15, bucket=None) -> str:
        # _to_sign = f"{self._bucket}/{key}:valid={minutes}"
        # uri = self._sign.dumps(_to_sign)
        # return f"{self._bucket}/{key}?key={uri}"
        raise NotImplementedError()

    def upload_signed(
        self, key, minutes=15, bucket=None, content_type="application/octed-stream"
    ) -> str:
        raise NotImplementedError()


class AsyncLocal(IAsyncStore):
    """For local usage and testing"""

    def __init__(self, bucket: str):
        self.opts = None
        self._bucket = bucket
        # self._sign = URLSafeTimedSerializer(
        #     secret_key=client_opts.get("secret_key"), salt=b"storage"
        # )

    def uri(self, key):
        return f"{self._bucket}/{key}"

    @classmethod
    async def from_uri(
        cls, bucket, opts: Optional[Dict[str, Any]] = None
    ) -> "IAsyncStore":
        obj = cls(bucket)

        return obj

    async def create_bucket(
        self, opts: Optional[Dict[str, str]] = None
    ) -> types.Bucket:
        await from_async2sync(mkdir_p, self._bucket)
        return types.Bucket(
            name=self._bucket,
            url=self._bucket,
            storage_class="filesystem",
            location="local",
            versioning=False,
            created_at=datetime.utcnow(),
        )

    async def get_bucket(self) -> types.Bucket:
        return types.Bucket(
            name=self._bucket,
            url=self._bucket,
            storage_class="filesystem",
            location="local",
            versioning=False,
            created_at=datetime.utcnow(),
        )

    async def put(self, key: str, bdata: bytes):
        uri = self.uri(key)
        mkdir_p(Path(uri).parent)
        try:
            async with aiofiles.open(uri, mode="wb") as f:
                await f.write(bdata)
        except Exception as e:
            raise KeyWriteError(self._bucket, key) from e

    async def put_stream(self, key: str, generator: AsyncIterator) -> bool:
        uri = self.uri(key)
        # mkdir_p((Path(uri).parent).resolve())
        try:
            async with aiofiles.open(uri, mode="wb") as f:
                async for data in generator:
                    await f.write(data)
        except Exception as e:
            raise KeyWriteError(self._bucket, key) from e

        return True

    async def get(self, key: str) -> Union[bytes, str, None]:
        uri = self.uri(key)
        try:
            async with aiofiles.open(uri, mode="rb") as f:
                data = await f.read()
                return data
        except Exception as e:
            raise KeyReadError(self._bucket, key) from e

    async def get_stream(self, key: str, buffer_size=1024):
        """PEP 0525 for Asynchronous generators"""
        uri = self.uri(key)
        try:
            async with aiofiles.open(uri, mode="rb") as f:
                while True:
                    data = await f.read(buffer_size)
                    if not data:
                        break
                    yield data

        except Exception as e:
            raise KeyReadError(self._bucket, key) from e

    async def list(self) -> List[str]:
        rsp = await from_async2sync(os.listdir, self._bucket)
        return rsp

    async def delete(self, key: str):
        await from_async2sync(delete_file_or_dir, f"{self._bucket}/{key}")

    def download_signed(self, key, minutes=15, bucket=None) -> str:
        # _to_sign = f"{self._bucket}/{key}:valid={minutes}"
        # uri = self._sign.dumps(_to_sign)
        # return f"{self._bucket}/{key}?key={uri}"
        raise NotImplementedError()

    def upload_signed(
        self, key, minutes=15, bucket=None, content_type="application/octed-stream"
    ) -> str:
        raise NotImplementedError()


class Storage:
    def __init__(self, app: Sanic, settings: types.Settings, create_bucket=False):
        self.app = app
        app.config.STORAGE = settings.STORAGE
        self._create_bucket = create_bucket
        # app.ext.dependency(self)

    async def _init_store(self, bucket: str, store_class: str) -> IAsyncStore:
        _Store: IAsyncStore = get_class(store_class)
        obj: IAsyncStore = await _Store.from_uri(bucket)
        if self._create_bucket:
            await obj.create_bucket()
        return obj

    async def init_listener(self, app: Sanic):
        app.ctx.storage = {}
        for k, v in app.config.STORAGE.items():
            obj = await self._init_store(v.bucket, v.store_class)
            app.ctx.storage[k] = obj
            logger.info("%s storage added", k)

    # @classmethod
    # def init_app(cls, app, settings: types.Settings) -> "Storage":
    #     obj = cls(app, settings)
    #     app.register_listener(obj.init_listener, "after_server_start")
    #     app.ext.dependency(obj)
    #     return obj

    def get_storage(self, name="default") -> IAsyncStore:
        return self.app.ctx.storage[name]


def init_app(app, settings: types.Settings, create_bucket=False):
    s = Storage(app, settings, create_bucket=create_bucket)
    app.register_listener(s.init_listener, "after_server_start")
    app.ext.dependency(s)
