import os
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

APP_TITLE = "Taylan Editor"


def _find_taylan_exe() -> str | None:
    # 1) If packaged, look next to taylan_editor.exe
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        cand = os.path.join(exe_dir, "taylan.exe")
        if os.path.exists(cand):
            return cand
        # In case installer nested another "Taylan" folder
        cand = os.path.join(exe_dir, "Taylan", "taylan.exe")
        if os.path.exists(cand):
            return cand

    # 2) If running from source, prefer local dist
    project_root = os.path.abspath(os.path.dirname(__file__))
    cand = os.path.join(project_root, "dist", "taylan.exe")
    if os.path.exists(cand):
        return cand

    # 3) Legacy location (Desktop)
    cand = os.path.join(os.path.expanduser("~"), "Desktop", "taylan.exe")
    if os.path.exists(cand):
        return cand

    return None


def run_taylan(filepath: str) -> str:
    exe = _find_taylan_exe()
    if exe:
        cmd = [exe, "calistir", filepath]
        cwd = os.path.dirname(filepath)
    else:
        # If packaged, don't fall back to launching self with -m
        if getattr(sys, "frozen", False):
            return "Hata: taylan.exe bulunamadi. Kurulumu tekrar kontrol et."
        # Fallback: run from source without EXE
        project_root = os.path.abspath(os.path.dirname(__file__))
        cmd = [sys.executable, "-m", "taylan.cli", "calistir", filepath]
        cwd = project_root
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8")
        out = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
        return out.strip() if out.strip() else "(cikti yok)"
    except Exception as e:
        return f"Hata: {e}"



def main():
    root = tk.Tk()
    root.title(APP_TITLE)
    root.geometry("1080x720")
    root.minsize(900, 600)

    colors = {
        "bg": "#0f1218",
        "panel": "#151a22",
        "panel2": "#10141b",
        "accent": "#d4b26a",
        "text": "#e8e6e3",
        "muted": "#8a92a6",
        "editor_bg": "#0c0f14",
        "output_bg": "#0a0d12",
        "btn_bg": "#1c2330",
        "btn_hover": "#273145",
        "border": "#242b38",
    }

    root.configure(bg=colors["bg"])

    current_path = {"value": None}

    def set_title(path: str | None):
        if path:
            root.title(f"{APP_TITLE} - {path}")
            title_path.config(text=path)
        else:
            root.title(APP_TITLE)
            title_path.config(text="Yeni dosya")

    def style_button(btn: tk.Button):
        btn.configure(
            bg=colors["btn_bg"],
            fg=colors["text"],
            activebackground=colors["btn_hover"],
            activeforeground=colors["text"],
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=14,
            pady=8,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
        )

    # Top bar
    topbar = tk.Frame(root, bg=colors["panel"], height=56)
    topbar.pack(fill="x", side="top")

    title = tk.Label(
        topbar,
        text=APP_TITLE,
        bg=colors["panel"],
        fg=colors["accent"],
        font=("Segoe UI", 14, "bold"),
    )
    title.pack(side="left", padx=18)

    title_path = tk.Label(
        topbar,
        text="Yeni dosya",
        bg=colors["panel"],
        fg=colors["muted"],
        font=("Segoe UI", 10),
    )
    title_path.pack(side="left", padx=8)

    # Layout frames
    body = tk.Frame(root, bg=colors["bg"])
    body.pack(fill="both", expand=True, padx=12, pady=12)

    sidebar = tk.Frame(body, bg=colors["panel2"], width=170)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    main = tk.Frame(body, bg=colors["bg"])
    main.pack(side="left", fill="both", expand=True, padx=(12, 0))

    # Sidebar content
    tk.Label(
        sidebar,
        text="KOMUTLAR",
        bg=colors["panel2"],
        fg=colors["muted"],
        font=("Segoe UI", 9, "bold"),
    ).pack(anchor="w", padx=16, pady=(16, 8))

    btn_new = tk.Button(sidebar, text="Yeni")
    style_button(btn_new)
    btn_new.pack(fill="x", padx=12, pady=6)

    btn_open = tk.Button(sidebar, text="Ac")
    style_button(btn_open)
    btn_open.pack(fill="x", padx=12, pady=6)

    btn_save = tk.Button(sidebar, text="Kaydet")
    style_button(btn_save)
    btn_save.pack(fill="x", padx=12, pady=6)

    btn_run = tk.Button(sidebar, text="Calistir")
    style_button(btn_run)
    btn_run.configure(bg=colors["accent"], fg="#1a1a1a", activebackground="#e2c27a")
    btn_run.pack(fill="x", padx=12, pady=10)

    # Editor frame
    editor_frame = tk.Frame(main, bg=colors["border"], bd=1, relief="solid")
    editor_frame.pack(fill="both", expand=True)

    text = tk.Text(
        editor_frame,
        wrap="none",
        font=("Cascadia Code", 12),
        bg=colors["editor_bg"],
        fg=colors["text"],
        insertbackground=colors["accent"],
        selectbackground="#2b3a55",
        bd=0,
        highlightthickness=0,
        padx=12,
        pady=12,
    )
    text.pack(fill="both", expand=True)

    # Output panel
    output_frame = tk.Frame(main, bg=colors["border"], bd=1, relief="solid")
    output_frame.pack(fill="x", pady=(10, 0))

    output_header = tk.Frame(output_frame, bg=colors["panel2"], height=28)
    output_header.pack(fill="x")

    tk.Label(
        output_header,
        text="CIKTI",
        bg=colors["panel2"],
        fg=colors["muted"],
        font=("Segoe UI", 9, "bold"),
    ).pack(side="left", padx=10)

    output = tk.Text(
        output_frame,
        height=8,
        wrap="none",
        font=("Cascadia Code", 10),
        bg=colors["output_bg"],
        fg=colors["text"],
        bd=0,
        highlightthickness=0,
        padx=10,
        pady=8,
    )
    output.pack(fill="x")

    status = tk.Label(
        root,
        text="Hazir",
        bg=colors["panel"],
        fg=colors["muted"],
        font=("Segoe UI", 9),
        anchor="w",
        padx=12,
        pady=6,
    )
    status.pack(fill="x", side="bottom")

    def new_file():
        text.delete("1.0", "end")
        current_path["value"] = None
        set_title(None)
        status.config(text="Yeni dosya")

    def open_file(path: str | None = None):
        if path is None:
            path = filedialog.askopenfilename(
                title="Dosya Ac",
                filetypes=[("Taylan", "*.taylan"), ("All", "*.*")],
            )
        if not path:
            return
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text.delete("1.0", "end")
            text.insert("1.0", f.read())
        current_path["value"] = path
        set_title(path)
        status.config(text="Dosya acildi")

    def save_file():
        path = current_path["value"]
        if not path:
            path = filedialog.asksaveasfilename(
                title="Kaydet",
                defaultextension=".taylan",
                filetypes=[("Taylan", "*.taylan"), ("All", "*.*")],
            )
            if not path:
                return
        with open(path, "w", encoding="utf-8") as f:
            f.write(text.get("1.0", "end-1c"))
        current_path["value"] = path
        set_title(path)
        status.config(text="Kaydedildi")

    def run_file():
        path = current_path["value"]
        if not path:
            messagebox.showinfo("Bilgi", "Once dosyayi kaydet.")
            return
        save_file()
        status.config(text="Calistiriliyor...")
        out = run_taylan(path)
        output.delete("1.0", "end")
        output.insert("1.0", out)
        status.config(text="Calistirma tamamlandi")

    btn_new.configure(command=new_file)
    btn_open.configure(command=open_file)
    btn_save.configure(command=save_file)
    btn_run.configure(command=run_file)

    root.bind("<Control-n>", lambda e: new_file())
    root.bind("<Control-o>", lambda e: open_file())
    root.bind("<Control-s>", lambda e: save_file())
    root.bind("<F5>", lambda e: run_file())

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        # Ignore flags like -m; only open if path exists
        if not arg.startswith("-") and os.path.exists(arg):
            open_file(arg)

    root.mainloop()


if __name__ == "__main__":
    main()
