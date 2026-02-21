import csv
import json
import os
from typing import List

__all__ = [
    "sql_db_olustur",
    "sql_tablo_olustur",
    "sql_ekle",
    "sql_sec",
    "sql_tablo_sil",
]


def _db_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def _table_path(db_path: str, table: str) -> str:
    return os.path.join(db_path, f"{table}.csv")


def sql_db_olustur(path: str) -> str:
    return _db_dir(path)


def sql_tablo_olustur(db_path: str, table: str, columns_csv: str) -> str:
    db_path = _db_dir(db_path)
    cols = [c.strip() for c in columns_csv.split(",") if c.strip()]
    if not cols:
        raise ValueError("Sutun listesi bos olamaz")
    p = _table_path(db_path, table)
    if os.path.exists(p):
        return p
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
    return p


def sql_ekle(db_path: str, table: str, values_csv: str) -> str:
    p = _table_path(db_path, table)
    if not os.path.exists(p):
        raise FileNotFoundError("Tablo yok: " + table)
    values = [v.strip() for v in values_csv.split(",")]
    with open(p, "r", newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        header = next(r, None)
    if header is None:
        raise ValueError("Tablo bozuk")
    if len(values) != len(header):
        raise ValueError("Deger sayisi sutun sayisina uymuyor")
    with open(p, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(values)
    return "ok"


def sql_sec(db_path: str, table: str) -> str:
    p = _table_path(db_path, table)
    if not os.path.exists(p):
        raise FileNotFoundError("Tablo yok: " + table)
    rows: List[List[str]] = []
    with open(p, "r", newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        for row in r:
            rows.append(row)
    # Return JSON string for now
    return json.dumps(rows, ensure_ascii=False)


def sql_tablo_sil(db_path: str, table: str) -> str:
    p = _table_path(db_path, table)
    if os.path.exists(p):
        os.remove(p)
        return "ok"
    return "yok"
