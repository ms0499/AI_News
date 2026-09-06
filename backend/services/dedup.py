import re


def normalize_url(url: str) -> str:
    """Strip tracking params and trailing slashes so the same article from
    different feeds/sources maps to the same key."""
    url = url.strip()
    url = re.sub(r"[?&](utm_[^=]+|ref|source)=[^&]*", "", url)
    url = url.rstrip("/?&")
    return url


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", title.lower())
