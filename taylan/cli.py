import argparse
import os
import importlib

from taylan.core.interpreter import Interpreter
from taylan.installer import install_optional_modules, LIB_SOURCES
from taylan.native_compiler import build_native, NativeCompileError



def _load_stdlib():
    modules = [
        "taylan_std.sql",
        "taylan_std.math",
        "taylan_std.ml",
        "taylan_std.data",
        "taylan_std.date",
        "taylan_std.img",
        "taylan_std.game",
        "taylan_std.http",
        "taylan_std.async",
        "taylan_std.json",
        "taylan_std.config",
        "taylan_std.log",
        "taylan_std.core",
    ]
    for m in modules:
        importlib.import_module(m)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="taylan", description="Taylan dil yorumlayicisi")
    sub = p.add_subparsers(dest="cmd")

    run = sub.add_parser("calistir", help=".tay dosyasini calistir")
    run.add_argument("file", help="Calistirilacak dosya")

    inst = sub.add_parser("kur", help="Opsiyonel modul kur")
    inst.add_argument("--all", action="store_true", help="Tum modulleri kur")
    for name in LIB_SOURCES.keys():
        inst.add_argument(f"--with-{name}", action="store_true", help=f"Modul: {name}")

    selfhost = sub.add_parser("selfhost", help="Taylan ile yazilmis transpiler calistir")
    selfhost.add_argument("file", help="Derlenecek .tay dosyasi")
    selfhost.add_argument("-o", "--out", default="", help="Uretilecek Python dosyasi")
    selfhost.add_argument(
        "--transpiler",
        default=os.path.join("selfhost", "transpiler_v0.tay"),
        help="Taylan transpiler yolu",
    )

    native = sub.add_parser("native", help="Taylan kodunu C ve native binary'ye derle (MVP)")
    native.add_argument("file", help="Derlenecek .tay dosyasi")
    native.add_argument("-o", "--out", default="", help="Cikacak binary yolu (vars: dosya adi)")
    native.add_argument("--c-out", default="", help="Uretilecek C dosyasi yolu")
    native.add_argument("--cc", default="gcc", help="C derleyicisi komutu (vars: gcc)")
    native.add_argument("--emit-c-only", action="store_true", help="Sadece C kodu uret")

    return p.parse_args()


def cmd_run(path: str) -> int:
    if not os.path.exists(path):
        print(f"Dosya yok: {path}")
        return 1
    with open(path, "r", encoding="utf-8-sig") as f:
        src = f.read()
    interp = Interpreter(base_dir=os.getcwd())
    interp.run(src)
    return 0


def cmd_selfhost(args: argparse.Namespace) -> int:
    if not os.path.exists(args.file):
        print(f"Dosya yok: {args.file}")
        return 1
    if not os.path.exists(args.transpiler):
        print(f"Transpiler yok: {args.transpiler}")
        return 1

    out_path = args.out
    if not out_path:
        base, _ = os.path.splitext(args.file)
        out_path = base + ".py"

    with open(args.transpiler, "r", encoding="utf-8-sig") as f:
        transpiler_src = f.read()

    interp = Interpreter(base_dir=os.getcwd())
    interp.run(transpiler_src)
    result = interp.call_function("selfhost_derle", [args.file, out_path])
    if result:
        print(result)
    print(f"Selfhost derleme tamamlandi: {out_path}")
    return 0


def cmd_native(args: argparse.Namespace) -> int:
    if not os.path.exists(args.file):
        print(f"Dosya yok: {args.file}")
        return 1
    try:
        c_path, bin_path = build_native(
            input_path=args.file,
            output_bin=args.out or None,
            c_out=args.c_out or None,
            cc=args.cc,
            emit_c_only=bool(args.emit_c_only),
        )
    except NativeCompileError as e:
        print(f"Native derleme hatasi: {e}")
        return 1

    print(f"C dosyasi: {c_path}")
    if bin_path:
        print(f"Binary: {bin_path}")
    return 0


def cmd_install(args: argparse.Namespace) -> int:
    project_root = os.getcwd()
    packages_dir = os.path.join(project_root, "taylan_packages")
    selected = []
    if args.all:
        selected = list(LIB_SOURCES.keys())
    else:
        for name in LIB_SOURCES.keys():
            if getattr(args, f"with_{name}"):
                selected.append(name)
    if not selected:
        print("Secim yok. (ornek: taylan kur --with-sql)")
        return 0
    install_optional_modules(project_root, packages_dir, selected)
    print("Kuruldu:")
    for name in selected:
        print(f"- {name}")
    return 0


def main() -> int:
    args = parse_args()
    if args.cmd == "calistir":
        return cmd_run(args.file)
    if args.cmd == "kur":
        return cmd_install(args)
    if args.cmd == "selfhost":
        return cmd_selfhost(args)
    if args.cmd == "native":
        return cmd_native(args)

    print("Kullanim:")
    print("  taylan calistir dosya.tay")
    print("  taylan kur --with-sql")
    print("  taylan selfhost dosya.tay -o dosya.py")
    print("  taylan native dosya.tay -o uygulama")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
