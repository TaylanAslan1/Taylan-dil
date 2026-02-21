import sqlite3
from typing import Any, List, Tuple

__all__ = [
    "sqlite_init",
    "sqlite_register",
    "sqlite_login",
    "sqlite_exec",
    "sqlite_query",
]


def _connect(db_path: str) -> sqlite3.Connection:
    return sqlite3.connect(db_path)


def sqlite_init(db_path: str, table: str) -> str:
    with _connect(db_path) as con:
        con.execute(
            f"CREATE TABLE IF NOT EXISTS {table} ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "username TEXT UNIQUE NOT NULL,"
            "password TEXT NOT NULL"
            ")"
        )
        con.commit()
    return "ok"


def sqlite_register(db_path: str, table: str, username: str, password: str) -> str:
    try:
        with _connect(db_path) as con:
            con.execute(
                f"INSERT INTO {table} (username, password) VALUES (?, ?)",
                (username, password),
            )
            con.commit()
        return "ok"
    except sqlite3.IntegrityError:
        return "exists"


def sqlite_login(db_path: str, table: str, username: str, password: str) -> str:
    with _connect(db_path) as con:
        cur = con.execute(
            f"SELECT password FROM {table} WHERE username = ?",
            (username,),
        )
        row = cur.fetchone()
    if row is None:
        return "nouser"
    return "ok" if row[0] == password else "badpass"


def sqlite_exec(db_path: str, sql: str) -> str:
    with _connect(db_path) as con:
        con.executescript(sql)
        con.commit()
    return "ok"


def sqlite_query(db_path: str, sql: str) -> List[Tuple[Any, ...]]:
    with _connect(db_path) as con:
        cur = con.execute(sql)
        return cur.fetchall()
