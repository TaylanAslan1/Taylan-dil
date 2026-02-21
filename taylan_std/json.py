import json
from typing import Any

__all__ = ["json_yukle", "json_yaz", "json_parse", "json_dok"]


def json_yukle(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def json_yaz(path: str, obj: Any) -> str:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    return path


def json_parse(text: str) -> Any:
    return json.loads(text)


def json_dok(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False)
