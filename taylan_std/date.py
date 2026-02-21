import datetime
import time

__all__ = ["tarih", "saat", "tarih_saat", "uyku"]


def tarih() -> str:
    return datetime.date.today().isoformat()


def saat() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S")


def tarih_saat() -> str:
    return datetime.datetime.now().isoformat(sep=" ", timespec="seconds")


def uyku(ms: int) -> str:
    time.sleep(ms / 1000.0)
    return "ok"
