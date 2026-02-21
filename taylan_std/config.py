import os

__all__ = ["cfg_oku", "cfg_cev" ]


def cfg_oku(path: str) -> dict:
    data = {}
    if not os.path.exists(path):
        return data
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                data[k.strip()] = v.strip()
    return data


def cfg_cev(key: str, default: str = "") -> str:
    return os.environ.get(key, default)
