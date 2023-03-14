from typing import List, Union

from itsdangerous import TimestampSigner
from itsdangerous.exc import BadSignature

from services import types
from services.security import IAuth


class SessionAuth(IAuth):
    def __init__(self, conf: types.SecurityConfig, cookie_name="SSID", secure=True):
        self.conf = conf
        # self.store = store
        self.cookie = cookie_name
        self.sign = TimestampSigner(conf.secret_key, salt=cookie_name)
        self._secure = secure

    def _get_cookie(self, request) -> Union[str, None]:
        cookie = request.cookies.get(self.cookie)
        return cookie

    def get_username(self, request) -> Union[str, None]:
        username = self.decode_request(request)
        return username

    def encode(self, username):
        svalue = self.sign.sign(username).decode("utf-8")
        return svalue

    def set_cookie(self, response, username):
        svalue = self.sign.sign(username).decode("utf-8")
        response.cookies[self.cookie] = svalue
        response.cookies[self.cookie]["domain"] = self.conf.domain
        response.cookies[self.cookie]["httponly"] = True
        response.cookies[self.cookie]["secure"] = self._secure
        response.cookies[self.cookie]["samesite"] = "lax"
        response.cookies[self.cookie]["max-age"] = self.conf.ttl_refresh_token
        return response

    def unset_cookie(self, response):
        response.cookies[self.cookie] = "expired"
        response.cookies[self.cookie]["max-age"] = 0
        return response

    def decode_request(self, request) -> Union[str, None]:
        final = None
        value = self._get_cookie(request)
        if not value:
            return None
        try:
            _final = self.sign.unsign(value, max_age=self.conf.ttl_refresh_token)
            final = _final.decode("utf-8")
        except BadSignature:
            pass
        return final

    def validate_request(self, request, policies: List[str] = None, require_all=True):
        decoded = self.decode_request(request)
        if decoded:
            request.ctx.username = decoded
            request.ctx.is_authenticated = True
            request.ctx.is_authorized = True

    def update_response(self, request, response):
        decoded = self.decode_request(request)
        res = self.set_cookie(response, decoded)
        return res
