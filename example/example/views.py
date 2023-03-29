from sanic import Blueprint, Request
from sanic.response import html, redirect, text
from sanic.views import HTTPMethodView
from sanic_ext import openapi

from services.db.plugin import DBHelper
from services.errors import AuthValidationFailed, WebAuthFailed
from services.security.sessionauth import SessionAuth
from services.shortcuts import async_render
from services.types import HtmlData, UserLogin

from .managers import UserManager

web_bp = Blueprint("web_example")

def new_data(content):
    return HtmlData(ctx={"DEV": True}, title="example", content=content)

@web_bp.get("/")
@openapi.exclude()
async def default_handler(request: Request, auth: SessionAuth):
    user = auth.get_username(request)
    data = new_data(dict(msg="hello", username=user))
    text = await async_render(request, "index.html", data)
    return html(text)


@web_bp.get("/logout")
@openapi.exclude()
async def logout_handler(request: Request, auth: SessionAuth):
    response = redirect("/")
    user = auth.get_username(request)
    if user:
        response = auth.unset_cookie(response)
    return response


class LoginView(HTTPMethodView):
    async def get(self, request):
        data = new_data(dict(msg="hello"))
        text = await async_render(request, "login.html", data)
        return html(text)

    async def post(self, request, auth: SessionAuth, um: UserManager, db: DBHelper):
        try:
            creds = UserLogin(
                username=request.form.get("username"),
                password=request.form.get("password"),
            )
            async with db.session() as session:
                user = await um.authenticate(
                    session, username=creds.username, to_verify=creds.password
                )
        except AuthValidationFailed as exc:
            raise WebAuthFailed() from exc

        response = redirect("/")
        auth.set_cookie(response, user.username)
        return response


class RegisterView(HTTPMethodView):
    async def get(self, request):
        data = new_data(dict(msg="hello"))
        text = await async_render(request, "login.html", data)
        return html(text)

    async def post(self, request, auth: SessionAuth, um: UserManager, db: DBHelper):
        try:
            creds = UserLogin(
                username=request.form.get("username"),
                password=request.form.get("password"),
            )
            async with db.session() as session:
                user = await um.authenticate(
                    session, username=creds.username, to_verify=creds.password
                )
        except AuthValidationFailed as exc:
            raise WebAuthFailed() from exc

        response = redirect("/")
        auth.set_cookie(response, user.username)
        return response


web_bp.add_route(LoginView.as_view(), "/login")
