from cryptography.fernet import Fernet
from services import types
from typing import TypeVar, Generic

from services.utils import get_class


ModelT = TypeVar("ModelT")


def generate_private_key() -> str:
    key = Fernet.generate_key()
    return key.decode("utf-8")


def decrypt(private_key: bytes, encrypted: str) -> str:
    f = Fernet(private_key)
    return f.decrypt(encrypted.encode("utf-8")).decode("utf-8")


def encrypt(private_key: str, text: str) -> bytes:
    f = Fernet(private_key)
    _hash = f.encrypt(text.encode("utf-8"))
    return _hash
