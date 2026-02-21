import os

__all__ = ["ppm_olustur", "ppm_kaydet"]


def ppm_olustur(w: int, h: int, r: int, g: int, b: int) -> str:
    # returns raw PPM string
    header = f"P3\n{w} {h}\n255\n"
    pixel = f"{r} {g} {b} "
    data = pixel * (w * h)
    return header + data


def ppm_kaydet(path: str, ppm_text: str) -> str:
    with open(path, "w", encoding="utf-8") as f:
        f.write(ppm_text)
    return path
