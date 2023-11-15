from typing import Union
from itsdangerous import TimestampSigner
from itsdangerous.exc import BadSignature


class SecureCookie:
    def __init__(
        self, secret_key, domain, cookie_name, secure=True, ttl=3600 * 168
    ):
        """
        It follows best practices to stablish a secure cookie. It prevents
        by default that any js could access to it.
        Also it sign every cookie to verify that the cookie wasn't altered
        on client side

        :param secret_key: Key to sign the cookie.
        :param domain: domain of the site.
        :param cookie_name: how it will be stored in the browser.
        :param secure: secure.
        :para ttl: expire time, in millisecons.
        """
        self.cookie = cookie_name
        self.sign = TimestampSigner(secret_key, salt=cookie_name)
        self._secure = secure
        self._ttl = ttl  # 7 days
        self._domain = domain

    def _get_cookie(self, request) -> Union[str, None]:
        cookie = request.cookies.get(self.cookie)
        return cookie

    def decode_request(self, request) -> Union[str, None]:
        final = None
        value = self._get_cookie(request)
        if not value:
            return None
        try:
            _final = self.sign.unsign(value, max_age=self._ttl)
            final = _final.decode("utf-8")
        except BadSignature:
            pass
        return final

    def get_value(self, request) -> Union[str, None]:
        val = self.decode_request(request)
        return val

    def set_value(self, response, value, ttl=None, httponly=True, samesite="lax"):
        svalue = self.sign.sign(value).decode("utf-8")
        response.add_cookie(
            self.cookie,
            svalue,
            domain=self._domain,
            httponly=httponly,
            secure=self._secure,
            samesite=samesite,
            max_age=ttl or self._ttl,
        )
        return response

    def unset(self, response):
        # response.delete_cookie(self.cookie)
        self.set_value(response, "", ttl=0)

    def setup_app(self, app, name):
        setattr(app.ctx, name, self)
