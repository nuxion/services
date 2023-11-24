from services.accept import parse_locale
from services.shortcuts import locale_best_match

ex1 = "fr-CH, fr;q=0.9, en;q=0.8, de;q=0.7, *;q=0.5"
ex2 = "*"
ex3 = "qwepoqweiqer INVALID"
ex4 = "es"


def test_accept_lang():
    """
    https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Accept-Language
    """
    r1 = parse_locale(ex1)
    r2 = parse_locale(ex2)
    r3 = parse_locale(ex3)
    r4 = parse_locale(ex4)

    assert len(r1) == 5
    assert r1[0][0] == "fr_CH"
    assert r2[0][0] == "*"
    assert "INVALID" in r3[0][0]
    assert r4[0][0] == "es"


def test_accept_best_match():
    r = locale_best_match({"accept-language": ex1})
    r2 = locale_best_match({})
    assert r == "fr_CH"
    assert r2 == "en_US"
