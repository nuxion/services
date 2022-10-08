from functools import wraps
from inspect import isawaitable
from typing import List, Optional

from sanic import Request, Sanic, json
from services.base import WebAppSpec
from services.security import get_app_auth
from services.security.authentication import auth_from_settings
from services.types import Settings

from .managers import UserManager


def get_users_mg(request: Request) -> UserManager:
    """a shortcut to get the Auth object from a web context"""
    current_app: Sanic = Sanic.get_app(request.app.name)

    return current_app.ctx.users_mg
