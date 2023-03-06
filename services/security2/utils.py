from datetime import datetime, timedelta

from services import types


def get_delta(delta_min: int) -> int:
    """Returns a timestamp addding a delta_min value to the utc now date."""
    delta = datetime.utcnow() + timedelta(minutes=delta_min)
    return int(delta.timestamp())


def open_keys(pub, priv) -> types.KeyPairs:
    with open(pub, "r") as f:
        pub = f.read()
        pub = pub.strip()
    with open(priv, "r") as f:
        priv = f.read()
        priv = priv.strip()
    return types.KeyPairs(public=pub, private=priv)
