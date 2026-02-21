from __future__ import annotations

import os
import sys
from typing import Any, List

__all__ = [
    "dosya_oku",
    "dosya_yaz",
    "klasor_olustur",
    "dizi_olustur",
    "dizi_ekle",
    "dizi_getir",
    "dizi_uzunluk",
    "dizi_yaz",
    "metin",
    "sayi",
    "metin_uzunluk",
    "metin_kirp",
    "metin_bol",
    "metin_birlestir",
    "metin_birlesik",
    "metin_alt",
    "metin_basliyor_mu",
    "metin_biter_mi",
    "metin_iceriyor_mu",
    "metin_degistir",
    "metin_bul",
    "arg_getir",
    "arg_sayisi",
    "satir_sonu",
    "cift_tirnak",
    "tab_karakteri",
    "cr_karakteri",
]


def dosya_oku(path: str) -> str:
    with open(path, "r", encoding="utf-8-sig") as f:
        return f.read()


def dosya_yaz(path: str, content: str) -> str:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(str(content))
    return path


def klasor_olustur(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def dizi_olustur() -> List[Any]:
    return []


def dizi_ekle(arr: List[Any], value: Any) -> int:
    arr.append(value)
    return len(arr)


def dizi_getir(arr: List[Any], index: int) -> Any:
    return arr[int(index)]


def dizi_uzunluk(arr: List[Any]) -> int:
    return len(arr)


def dizi_yaz(arr: List[Any], index: int, value: Any) -> Any:
    arr[int(index)] = value
    return value


def metin(value: Any) -> str:
    return str(value)


def sayi(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    s = str(value).strip()
    return int(float(s))


def metin_uzunluk(value: str) -> int:
    return len(value)


def metin_kirp(value: str) -> str:
    return str(value).strip()


def metin_bol(value: str, sep: str = "\n") -> List[str]:
    return str(value).split(sep)


def metin_birlestir(parts: List[Any], sep: str = "") -> str:
    return str(sep).join(str(x) for x in parts)


def metin_birlesik(a: Any, b: Any) -> str:
    return f"{a}{b}"


def metin_alt(value: str, start: int, end: int) -> str:
    return str(value)[int(start):int(end)]


def metin_basliyor_mu(value: str, prefix: str) -> bool:
    return str(value).startswith(str(prefix))


def metin_biter_mi(value: str, suffix: str) -> bool:
    return str(value).endswith(str(suffix))


def metin_iceriyor_mu(value: str, needle: str) -> bool:
    return str(needle) in str(value)


def metin_degistir(value: str, old: str, new: str) -> str:
    return str(value).replace(str(old), str(new))


def metin_bul(value: str, needle: str) -> int:
    return str(value).find(str(needle))


def arg_getir(index: int, default: str = "") -> str:
    i = int(index)
    if i < 0 or i >= len(sys.argv):
        return default
    return sys.argv[i]


def arg_sayisi() -> int:
    return len(sys.argv)


def satir_sonu() -> str:
    return "\n"


def cift_tirnak() -> str:
    return '"'


def tab_karakteri() -> str:
    return "\t"


def cr_karakteri() -> str:
    return "\r"
