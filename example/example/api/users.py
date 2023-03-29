from sanic import Blueprint, Request
from sanic.response import json
from sanic_ext import openapi

from services.db.plugin import DBHelper
from services.errors import AuthValidationFailed, WebAuthFailed
from services.security import protected
from services.security.jwtauth import JWTAuth
from services.types import JWTPayload, JWTResponse, UserLogin

from ..managers import UserManager

users_bp = Blueprint("users", url_prefix="users", version="v1")


@users_bp.post("/login")
@openapi.response(200, {"application/json": JWTResponse})
@openapi.response(403, dict(msg=str), "Not Found")
@openapi.body(UserLogin)
async def login_handler(request: Request, um: UserManager, auth: JWTAuth, db: DBHelper):
    # session = db.get_session(request)
    try:
        creds = UserLogin(**request.json)
        async with db.session() as session:
            user = await um.authenticate(
                session, username=creds.username, to_verify=creds.password
            )
    except AuthValidationFailed as exc:
        raise WebAuthFailed() from exc

    # jwt = await manager.generate_token(user)
    payload = JWTPayload(custom={"usr": user.username, "scopes": user.scopes})
    tkn = await auth.generate_token(payload)
    return json(tkn.dict(), 200)


@users_bp.get("/verify")
@openapi.response(200, {"application/json": JWTResponse})
@protected(validators=["jwt"])
async def verify_handler(request: Request):
    return json(request.ctx.token_data, 200)


@users_bp.post("/refresh_token")
@openapi.response(200, {"application/json": JWTResponse})
@openapi.body(JWTResponse)
async def refresh_handler(request, auth: JWTAuth):
    if not request.app.config.JWT_ALLOW_REFRESH:
        return json(dict(msg="Not found"), 404)

    at = request.token
    rftkn = request.json.get("refresh_token")
    if not rftkn:
        raise WebAuthFailed()

    old_token = JWTResponse(access_token=at, refresh_token=rftkn)
    # redis = request.ctx.web_redis
    try:
        jwt_res = await auth.refresh_token(
            old_token.access_token, old_token.refresh_token
        )
        return json(jwt_res.dict(), 200)
    except AuthValidationFailed as e:
        raise WebAuthFailed() from e