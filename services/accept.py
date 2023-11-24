from typing import List, Tuple


def parse_locale(header_str) -> List[Tuple[str, str]]:
    """ taken from
    https://github.com/siongui/userpages/blob/master/content/articles/2012/10/11/python-parse-accept-language-in-http-request-header%25en.rst
    """
    languages = header_str.split(",")
    locale_q_pairs = []

    for language in languages:
        if language.split(";")[0] == language:
            # no q => q = 1
            loc = language.strip().replace("-", "_")
            locale_q_pairs.append((loc, "1"))
        else:
            locale = language.split(";")[0].strip()
            loc = locale.replace("-", "_")
            q = language.split(";")[1].split("=")[1]
            locale_q_pairs.append((loc, q))

    return locale_q_pairs

