import datetime

__all__ = ["log_yaz", "log_hata"]


def _stamp() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log_yaz(path: str, msg: str) -> str:
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"[{_stamp()}] {msg}\n")
    return path


def log_hata(path: str, msg: str) -> str:
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"[{_stamp()}] HATA: {msg}\n")
    return path
