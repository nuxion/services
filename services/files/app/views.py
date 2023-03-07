from sanic import Blueprint, Request
from sanic.response import html
from sanic_ext import openapi
from services.shortcuts import async_render
from services.types import HtmlData
from sanic.views import HTTPMethodView
from services.security.sessionauth import SessionAuth

web_bp = Blueprint("web")


def new_data(content):
    return HtmlData(ctx={"DEV": True}, title="{{ data.app_name }}", content=content)


@web_bp.get("/")
@openapi.exclude()
async def default_handler(request: Request):
    data = new_data(dict(msg="hello"))
    text = await async_render(request, "index.html", data)
    return html(text)


# @web_bp.get("/login")
# @openapi.exclude()
# async def login_handler(request: Request):
#     data = new_data(dict(msg="hello"))
#     text = await async_render(request, "login.html", data)
#     return html(text)


class LoginView(HTTPMethodView):
    async def get(self, request):
        data = new_data(dict(msg="hello"))
        text = await async_render(request, "login.html", data)
        return html(text)

    async def post(self, request, auth: SessionAuth):
        data = new_data(dict(msg="POST ACTION"))
        text = await async_render(request, "login.html", data)
        print(request.body)
        response = html(text)
        auth.set_cookie(response, "test")
        print(response.cookies)
        return response


web_bp.add_route(LoginView.as_view(), "/login")
