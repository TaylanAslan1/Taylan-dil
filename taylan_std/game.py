__all__ = ["ekran_yaz", "kutu"]


def ekran_yaz(msg: str) -> str:
    print(msg)
    return "ok"


def kutu(w: int, h: int) -> str:
    if w < 2 or h < 2:
        return ""
    top = "+" + "-" * (w - 2) + "+"
    mid = "|" + " " * (w - 2) + "|"
    lines = [top] + [mid for _ in range(h - 2)] + [top]
    return "\n".join(lines)
