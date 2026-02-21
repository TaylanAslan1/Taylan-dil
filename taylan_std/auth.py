import json
import os
from typing import Any, Dict

__all__ = ["auth_handle"]


def _load_users(path: str) -> Dict[str, str]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return {}
    if isinstance(data, dict):
        return {str(k): str(v) for k, v in data.items()}
    return {}


def _save_users(path: str, users: Dict[str, str]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def auth_handle(req_path: str, res_path: str) -> str:
    # Request JSON: {"action":"register"|"login", "username":"...", "password":"..."}
    base_dir = os.path.dirname(os.path.abspath(req_path))
    users_path = os.path.join(base_dir, "users.json")

    try:
        with open(req_path, "r", encoding="utf-8") as f:
            req = json.load(f)
    except Exception as e:
        _write_res(res_path, False, f"Geçersiz istek: {e}")
        return "err"

    action = str(req.get("action", ""))
    username = str(req.get("username", ""))
    password = str(req.get("password", ""))

    if not username or not password:
        _write_res(res_path, False, "Kullanıcı adı ve şifre gerekli")
        return "err"

    users = _load_users(users_path)

    if action == "register":
        if username in users:
            _write_res(res_path, False, "Bu kullanıcı zaten var")
            return "ok"
        users[username] = password
        _save_users(users_path, users)
        _write_res(res_path, True, "Kayıt başarılı")
        return "ok"

    if action == "login":
        if username not in users:
            _write_res(res_path, False, "Kullanıcı bulunamadı")
            return "ok"
        if users[username] != password:
            _write_res(res_path, False, "Şifre hatalı")
            return "ok"
        _write_res(res_path, True, "Giriş başarılı")
        return "ok"

    _write_res(res_path, False, "Bilinmeyen işlem")
    return "err"


def _write_res(path: str, ok: bool, message: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"ok": ok, "message": message}, f, ensure_ascii=False)
