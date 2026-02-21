import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Tuple

from taylan_std.sqlite import sqlite_init, sqlite_register, sqlite_login

__all__ = ["tweb_baslat"]


def _abs(path: str) -> str:
    if os.path.isabs(path):
        return path
    return os.path.abspath(path)


def _parse_json(body: bytes) -> dict:
    try:
        return json.loads(body.decode("utf-8"))
    except Exception:
        return {}


def _response(ok: bool, message: str) -> bytes:
    return json.dumps({"ok": ok, "message": message}, ensure_ascii=False).encode("utf-8")


class _Handler(BaseHTTPRequestHandler):
    html_path: str = ""
    db_path: str = ""
    table: str = "users"

    def _send(self, status: int, body: bytes, content_type: str = "text/plain") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            with open(self.html_path, "rb") as f:
                data = f.read()
            self._send(200, data, "text/html; charset=utf-8")
            return
        self._send(404, b"not found")

    def do_POST(self) -> None:
        if self.path not in ("/api/register", "/api/login"):
            self._send(404, b"not found")
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        data = _parse_json(body)

        username = str(data.get("username", "")).strip()
        password = str(data.get("password", "")).strip()
        if not username or not password:
            self._send(200, _response(False, "Kullanıcı adı ve şifre gerekli"), "application/json; charset=utf-8")
            return

        if self.path == "/api/register":
            res = sqlite_register(self.db_path, self.table, username, password)
            if res == "ok":
                self._send(200, _response(True, "Kayıt başarılı"), "application/json; charset=utf-8")
                return
            self._send(200, _response(False, "Bu kullanıcı zaten var"), "application/json; charset=utf-8")
            return

        res = sqlite_login(self.db_path, self.table, username, password)
        if res == "ok":
            self._send(200, _response(True, "Giriş başarılı"), "application/json; charset=utf-8")
            return
        if res == "nouser":
            self._send(200, _response(False, "Kullanıcı bulunamadı"), "application/json; charset=utf-8")
            return
        self._send(200, _response(False, "Şifre hatalı"), "application/json; charset=utf-8")


def tweb_baslat(host: str, port: int, html_path: str, db_path: str, table: str = "users") -> str:
    html_path = _abs(html_path)
    db_path = _abs(db_path)

    sqlite_init(db_path, table)

    _Handler.html_path = html_path
    _Handler.db_path = db_path
    _Handler.table = table

    httpd = HTTPServer((host, int(port)), _Handler)
    print(f"Server running: http://{host}:{port}")
    httpd.serve_forever()
    return "ok"
