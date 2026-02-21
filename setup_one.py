import json
import os
import subprocess
import sys
from pathlib import Path
import traceback
import tkinter as tk
from tkinter import messagebox

LIB_SOURCES = {
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

REGISTRY_FILE = "registry.json"


def project_root() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def packages_dir() -> str:
    return os.path.join(project_root(), "taylan_packages")


def registry_path() -> str:
    return os.path.join(packages_dir(), REGISTRY_FILE)


def resolve_lib_root() -> str:
    env = os.environ.get("TAYLAN_LIB_ROOT")
    if env:
        return os.path.abspath(env)
    return os.path.abspath(os.path.join(project_root(), "lib"))


def load_registry() -> dict:
    path = registry_path()
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_registry(data: dict) -> None:
    os.makedirs(packages_dir(), exist_ok=True)
    path = registry_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def install_selected(selected):
    lib_root = resolve_lib_root()
    registry = load_registry()

    for name in selected:
        src = os.path.join(lib_root, LIB_SOURCES[name])
        if not os.path.exists(src):
            raise FileNotFoundError(f"Missing source for {name}: {src}")
        registry[name] = {
            "source": src,
            "installed": True,
        }

    save_registry(registry)


def ensure_pyinstaller() -> bool:
    try:
        subprocess.run(["pyinstaller", "--version"], check=True, capture_output=True)
        return True
    except Exception:
        return False


def build_exe() -> None:
    if not ensure_pyinstaller():
        messagebox.showwarning(
            "PyInstaller yok",
            "PyInstaller bulunamadı. Önce şu komutu çalıştır:\n\n"
            "pip install pyinstaller",
        )
        return
    cmd = [
        "pyinstaller",
        "--onefile",
        "--name",
        "taylan",
        "--icon",
        os.path.join(project_root(), "logo.ico"),
        os.path.join("taylan", "cli.py"),
    ]
    try:
        subprocess.run(cmd, cwd=project_root(), check=True)
    except Exception as e:
        log_path = log_error("PYINSTALLER ERROR", e)
        messagebox.showerror("Hata", f"EXE ?retilemedi. Detaylar: {log_path}")
        return
    src_exe = os.path.join(project_root(), "dist", "taylan.exe")
    dst_exe = os.path.join(os.path.expanduser("~"), "Desktop", "taylan.exe")
    if os.path.exists(src_exe):
        os.makedirs(os.path.dirname(dst_exe), exist_ok=True)
        with open(src_exe, "rb") as fsrc, open(dst_exe, "wb") as fdst:
            fdst.write(fsrc.read())




def log_error(title: str, exc: Exception) -> str:
    log_path = os.path.join(project_root(), "setup_error.log")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write("\n" + "=" * 80 + "\n")
        f.write(title + "\n")
        f.write(traceback.format_exc())
    return log_path


def uninstall_all():
    removed = []
    # Remove registry
    reg = Path(registry_path())
    if reg.exists():
        reg.unlink()
        removed.append(str(reg))
    # Remove empty packages dir
    pkg_dir = Path(packages_dir())
    if pkg_dir.exists() and not any(pkg_dir.iterdir()):
        pkg_dir.rmdir()
        removed.append(str(pkg_dir))
    # Remove desktop exe
    desktop_exe = Path(os.path.join(os.path.expanduser("~"), "Desktop", "taylan.exe"))
    if desktop_exe.exists():
        desktop_exe.unlink()
        removed.append(str(desktop_exe))
    # Remove dist exe (if exists)
    dist_exe = Path(os.path.join(project_root(), "dist", "taylan.exe"))
    if dist_exe.exists():
        dist_exe.unlink()
        removed.append(str(dist_exe))
    return removed

def main():
    root = tk.Tk()
    root.title("Taylan Kurulum")
    root.geometry("520x560")
    root.resizable(False, False)

    title = tk.Label(root, text="Taylan - Kurulum", font=("Segoe UI", 14, "bold"))
    title.pack(pady=12)

    info = tk.Label(
        root,
        text="Seçtiklerini kuracağım. Çekirdek zorunlu. Kütüphane yolu: lib",
        wraplength=480,
        justify="center",
    )
    info.pack(pady=6)

    frame = tk.Frame(root)
    frame.pack(pady=10)

    vars_map = {}
    for name in LIB_SOURCES.keys():
        var = tk.BooleanVar(value=False)
        cb = tk.Checkbutton(frame, text=name, variable=var, onvalue=True, offvalue=False)
        cb.pack(anchor="w")
        vars_map[name] = var

    exe_var = tk.BooleanVar(value=True)
    exe_cb = tk.Checkbutton(root, text="Kurulumdan sonra taylan.exe üret", variable=exe_var)
    exe_cb.pack(pady=8)

    def select_all():
        for v in vars_map.values():
            v.set(True)

    def clear_all():
        for v in vars_map.values():
            v.set(False)

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=8)

    tk.Button(btn_frame, text="Tümünü Seç", width=12, command=select_all).grid(row=0, column=0, padx=6)
    tk.Button(btn_frame, text="Temizle", width=12, command=clear_all).grid(row=0, column=1, padx=6)

    status = tk.Label(root, text="", fg="#444")
    status.pack(pady=6)

    def on_install():
        selected = [name for name, var in vars_map.items() if var.get()]
        try:
            install_selected(selected)
        except Exception as e:
            log_path = log_error("INSTALL ERROR", e)
            messagebox.showerror("Hata", f"Kurulum hatas?. Detaylar: {log_path}")
            return
        status.config(text=f"Kuruldu: {', '.join(selected) if selected else 'opsiyonel yok'}")
        if exe_var.get():
            try:
                build_exe()
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Hata", f"EXE üretilemedi: {e}")
                return
        messagebox.showinfo("Tamam", "Kurulum tamamlandı.")

    btns = tk.Frame(root)
    btns.pack(pady=16)

    tk.Button(btns, text="Kur", width=16, height=2, command=on_install).grid(row=0, column=0, padx=6)

    def on_uninstall():
        removed = uninstall_all()
        if removed:
            messagebox.showinfo("Kald?r?ld?", "Kald?r?lanlar:\n" + "\n".join(removed))
        else:
            messagebox.showinfo("Bilgi", "Kald?r?lacak bir ?ey bulunamad?.")

    tk.Button(btns, text="Kald?r", width=16, height=2, command=on_uninstall).grid(row=0, column=1, padx=6)

    root.mainloop()


if __name__ == "__main__":
    main()
