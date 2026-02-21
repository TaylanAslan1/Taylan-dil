from typing import List

__all__ = ["dizi", "dizi_ekle", "dizi_topla", "dizi_ortalama"]


def dizi(csv_str: str) -> List[float]:
    return [float(x.strip()) for x in csv_str.split(",") if x.strip()]


def dizi_ekle(a: List[float], b: List[float]) -> List[float]:
    if len(a) != len(b):
        raise ValueError("boyut uyusmuyor")
    return [x + y for x, y in zip(a, b)]


def dizi_topla(a: List[float]) -> float:
    return sum(a)


def dizi_ortalama(a: List[float]) -> float:
    return sum(a) / len(a) if a else 0.0


__all__.extend(["tablo_olustur", "tablo_ekle", "tablo_sec", "tablo_filtre", "tablo_csv_yaz", "tablo_csv_oku"])


def tablo_olustur(columns_csv: str) -> dict:
    cols = [c.strip() for c in columns_csv.split(",") if c.strip()]
    if not cols:
        raise ValueError("sutun listesi bos olamaz")
    return {"columns": cols, "rows": []}


def tablo_ekle(tablo: dict, values_csv: str) -> dict:
    values = [v.strip() for v in values_csv.split(",")]
    if len(values) != len(tablo["columns"]):
        raise ValueError("deger sayisi sutun sayisina uymuyor")
    tablo["rows"].append(values)
    return tablo


def tablo_sec(tablo: dict, col: str) -> list:
    if col not in tablo["columns"]:
        raise ValueError("sutun yok: " + col)
    idx = tablo["columns"].index(col)
    return [row[idx] for row in tablo["rows"]]


def tablo_filtre(tablo: dict, col: str, value: str) -> dict:
    if col not in tablo["columns"]:
        raise ValueError("sutun yok: " + col)
    idx = tablo["columns"].index(col)
    rows = [r for r in tablo["rows"] if r[idx] == value]
    return {"columns": list(tablo["columns"]), "rows": rows}


def tablo_csv_yaz(path: str, tablo: dict) -> str:
    import csv
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(tablo["columns"])
        w.writerows(tablo["rows"])
    return path


def tablo_csv_oku(path: str) -> dict:
    import csv
    with open(path, "r", newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        rows = list(r)
    if not rows:
        return {"columns": [], "rows": []}
    return {"columns": rows[0], "rows": rows[1:]}
