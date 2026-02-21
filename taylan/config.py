import json
import os
from typing import Dict

REGISTRY_FILE = "registry.json"


def registry_path(base_dir: str) -> str:
    return os.path.join(base_dir, REGISTRY_FILE)


def load_registry(base_dir: str) -> Dict[str, dict]:
    path = registry_path(base_dir)
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_registry(base_dir: str, data: Dict[str, dict]) -> None:
    os.makedirs(base_dir, exist_ok=True)
    path = registry_path(base_dir)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
