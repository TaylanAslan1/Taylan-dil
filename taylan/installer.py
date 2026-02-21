import os
from typing import Dict, Iterable

from .config import load_registry, save_registry


LIB_SOURCES: Dict[str, str] = {
    "async": "async/asyncio-master",
    "cv": "cv/stb-master",
    "graphics": "graphics/raylib-master",
    "http": "http/libmicrohttpd-1.0.2",
    "ml": "ml/mlpack-master",
    "tiny_dnn": "tiny_dnn/tiny-dnn-master",
    "sql": "sql",
    "viz": "viz/ploticus242",
    "web": "web/simplehtmldom",
}


def resolve_lib_root(project_root: str) -> str:
    env = os.environ.get("TAYLAN_LIB_ROOT")
    if env:
        return os.path.abspath(env)
    # Default: project_root\lib
    return os.path.abspath(os.path.join(project_root, "lib"))


def install_optional_modules(project_root: str, packages_dir: str, names: Iterable[str]) -> Dict[str, dict]:
    lib_root = resolve_lib_root(project_root)
    registry = load_registry(packages_dir)

    for name in names:
        if name not in LIB_SOURCES:
            raise ValueError(f"Unknown module: {name}")
        src = os.path.join(lib_root, LIB_SOURCES[name])
        if not os.path.exists(src):
            raise FileNotFoundError(f"Missing source for {name}: {src}")
        registry[name] = {
            "source": src,
            "installed": True,
        }

    save_registry(packages_dir, registry)
    return registry
