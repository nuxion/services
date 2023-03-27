import json
import os
from datetime import timedelta
from typing import Any, Dict, Generator, List, Union, Optional, AsyncIterator

from google.cloud.storage import Client
from google.cloud.storage.bucket import Bucket as _GoogleBucket
from pydantic import BaseModel
from smart_open import open

from services import defaults, types
from services.storage import IAsyncStore, IStorage
from services.utils import from_async2sync


class BucketConf(BaseModel):
    location: str
    storage_class: str = "STANDARD"
    versioning: bool = False
    labels: Optional[Dict[str, str]] = None


class _GCConf(BaseModel):
    """
    :param CREDENTIALS: credential file open by python
    :param PROJECT: projectid
    :param LOCATION: region/zone
    :param SERVICE_ACCOUNT: client_email
    """

    CREDENTIALS: str
    PROJECT: str
    LOCATION: Optional[str] = None
    SERVICE_ACCOUNT: Optional[str] = None


def get_auth_conf(env_var=defaults.GOOGLE_AUTH_ENV, filepath=None) -> _GCConf:
    """
    https://googleapis.dev/python/google-api-core/latest/auth.html#authentication
    """
    if filepath:
        creds_path = filepath
    else:
        creds_path = os.environ.get(env_var)
    if creds_path:
        with open(creds_path, "r") as f:
            data = json.loads(f.read())
            acc = data["client_email"]
            prj = data["project_id"]
        conf = _GCConf(CREDENTIALS=creds_path, PROJECT=prj, SERVICE_ACCOUNT=acc)
    else:
        conf = _GCConf()
    return conf


class GoogleStore(IStorage):
    """https://googleapis.dev/python/storage/latest/client.html"""

    def __init__(self, bucket: str, opts: Optional[Dict[str, Any]] = None):
        env_var = defaults.GOOGLE_AUTH_ENV
        if opts:
            env_var = opts.get("env_var")

        self._conf = get_auth_conf(env_var=env_var)
        self._bucket = bucket
        self.client = Client.from_service_account_json(self._conf.CREDENTIALS)
        self.bucket: _GoogleBucket = None
        self._params = {"client": self.client}

    @property
    def uri(self):
        return f"gs://{self._bucket}"

    def _current_or_get_bucket(self) -> _GoogleBucket:
        if not self.bucket:
            self.bucket = self.client.get_bucket(self._bucket)
        return self.bucket

    def _to_bucket(self, b: _GoogleBucket) -> types.Bucket:
        _bucket = types.Bucket(
            name=b.name,
            storage_class=b.storage_class,
            location=b.location,
            url=f"gs://{b.name}",
            versioning=b.versioning_enabled,
            labels=b.labels,
            created_at=b.time_created,
        )
        return _bucket

    def get_bucket(self) -> types.Bucket:
        b = self._current_or_get_bucket()
        return self._to_bucket(b)

    def create_bucket(self, opts: Optional[Dict[str, str]] = None) -> types.Bucket:
        conf = BucketConf(**opts)

        _b = self.client.create_bucket(
            name=self._bucket,
            storage_class=conf.storage_class,
            location=conf.location,
            labels=conf.labels,
        )
        _bucket = self._to_bucket(_b)
        self.bucket = _b
        return _bucket

    def put(self, key: str, bdata: bytes):
        # obj = io.BytesIO(bdata)
        blob = self.bucket.blob(key)
        blob.upload_from_string(bdata, content_type="application/octet-stream")

    def _writer(self, key: str, generator: Generator[bytes, None, None]):
        with open(f"{self.uri}/{key}", "wb", transport_params=self._params) as f:
            data = True
            while data:
                try:
                    _data = next(generator)
                    f.write(_data)
                except StopIteration:
                    data = False

    def list(self) -> List[str]:
        # TODO: define a type for objects that include size, name, path etc...
        blobs = [b.name for b in self.bucket.list_blobs()]
        return blobs

    def delete(self, key: str):
        self.bucket.delete_blob(key)

    def put_stream(self, key: str, generator: Generator[bytes, None, None]) -> bool:
        rsp = True
        try:
            self._writer(key, generator)
        except Exception:
            rsp = False
        return rsp

    def get(self, key: str) -> Union[bytes, None]:
        blob = self.bucket.blob(key)
        obj = None
        try:
            obj = blob.download_as_bytes()
        except Exception:
            pass
        return obj

    def get_stream(self, key: str) -> Generator[bytes, None, None]:
        uri = f"{self.uri}/{key}"
        for chunk in open(uri, "rb", transport_params=self._params):
            yield chunk

    def download_signed(self, key, minutes=15, bucket=None) -> str:
        _b = self._current_or_get_bucket()
        blob = _b.blob(key)
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=minutes),
            method="GET",
        )
        return url

    def upload_signed(
        self, key, minutes=15, bucket=None, content_type="application/octed-stream"
    ) -> str:
        """
        curl -X PUT -H 'Content-Type: application/octet-stream' "
        "--upload-file my-file '{url}'
        """

        _b = self._current_or_get_bucket()
        blob = _b.blob(key)
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=minutes),
            method="PUT",
            content_type=content_type,
        )
        return url


class AsyncGoogleStore(IAsyncStore):
    """A hacky solution because thereisn't trustworthy async lib"""

    def __init__(self, bucket: str, client: GoogleStore):
        self._bucket = bucket
        self.client = client
        self.bucket: _GoogleBucket = client.bucket

    @classmethod
    async def from_uri(
        cls, bucket, opts: Optional[Dict[str, Any]] = None
    ) -> "IAsyncStore":
        c = GoogleStore(bucket, opts)
        await from_async2sync(c.get_bucket)
        bucket = c.bucket
        return cls(bucket=bucket, client=c)

    async def get_bucket(self) -> types.Bucket:
        return await from_async2sync(self.client.get_bucket)

    async def create_bucket(
        self, opts: Optional[Dict[str, str]] = None
    ) -> types.Bucket:
        return await from_async2sync(self.client.create_bucket, opts)

    async def _current_or_get_bucket(self) -> _GoogleBucket:
        if not self.bucket:
            self.bucket = await from_async2sync(self.client.get_bucket)
        return self.bucket

    async def put(self, key: str, bdata: bytes):
        await from_async2sync(self.client.put, key, bdata)

    async def put_stream(
        self, key: str, generator: Generator[bytes, None, None]
    ) -> bool:
        rsp = await from_async2sync(self.client.put_stream, key, generator)
        return rsp

    async def get(self, key: str) -> Union[bytes, str, None]:
        rsp = await from_async2sync(self.client.get, key)
        return rsp

    async def get_stream(self, key: str, buffer_size=1024) -> AsyncIterator:
        yield await from_async2sync(self.client.get_stream, key)

    async def list(self) -> List[str]:
        rsp = await from_async2sync(self.client.list)
        return rsp

    async def delete(self, key: str):
        await from_async2sync(self.client.delete, key)

    def download_signed(self, key, minutes=15, bucket=None) -> str:
        _b = self._current_or_get_bucket()
        blob = _b.blob(key)
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=minutes),
            method="GET",
        )
        return url

    def upload_signed(
        self, key, minutes=15, bucket=None, content_type="application/octed-stream"
    ) -> str:
        """
        curl -X PUT -H 'Content-Type: application/octet-stream' "
        "--upload-file my-file '{url}'
        """

        _b = self._current_or_get_bucket()
        blob = _b.blob(key)
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=minutes),
            method="PUT",
            content_type=content_type,
        )
        return url
