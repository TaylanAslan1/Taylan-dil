import urllib.request

__all__ = ["http_get"]


def http_get(url: str) -> str:
    with urllib.request.urlopen(url) as r:
        return r.read().decode("utf-8", errors="ignore")
