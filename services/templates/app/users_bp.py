from sanic import Blueprint, Request
from sanic.response import json
from sanic_ext import openapi
from services.errors import AuthValidationFailed, WebAuthFailed
from services.security import protected
from services.types import JWTResponse, UserLogin
from services.users import get_users_mg

users_bp = Blueprint("users_api", url_prefix="users", version="v1")


@users_bp.post("/login")
@openapi.response(200, {"application/json": JWTResponse})
@openapi.response(403, dict(msg=str), "Not Found")
@openapi.body(UserLogin)
async def login_handler(request: Request):
    manager = get_users_mg(request)
    try:
        creds = UserLogin(**request.json)
        user = await manager.authenticate(username=creds.username,
                                          password=creds.password)
    except AuthValidationFailed as exc:
        raise WebAuthFailed() from exc

    jwt = await manager.generate_token(user)
    return json(jwt.dict(), 200)


@users_bp.get("/verify")
@openapi.response(200, {"application/json": JWTResponse})
@protected()
async def verify_handler(request: Request):
    return json(request.ctx.token_data, 200)


@users_bp.post("/refresh_token")
@openapi.response(200, {"application/json": JWTResponse})
@openapi.body(JWTResponse)
async def refresh_handler(request):
    if not request.app.config.AUTH_ALLOW_REFRESH:
        return json(dict(msg="Not found"), 404)

    at = request.token
    rftkn = request.json.get("refresh_token")
    if not rftkn:
        raise WebAuthFailed()

    old_token = JWTResponse(access_token=at, refresh_token=rftkn)
    manager = get_users_mg(request)
    # redis = request.ctx.web_redis
    try:
        jwt_res = await manager.refresh_token(old_token)
        return json(jwt_res.dict(), 200)
    except AuthValidationFailed as e:
        raise WebAuthFailed() from e
