import time

__all__ = ["bekle", "sayac"]


def bekle(ms: int) -> str:
    time.sleep(ms / 1000.0)
    return "ok"


def sayac(n: int) -> str:
    for i in range(int(n)):
        time.sleep(0.1)
    return "ok"
