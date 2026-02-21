from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple


class NativeCompileError(RuntimeError):
    pass


_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _emit(buf: List[str], indent: int, text: str) -> None:
    buf.append(("    " * indent) + text)


def _strip_colon(text: str) -> str:
    t = text.strip()
    if t.endswith(":"):
        return t[:-1].strip()
    return t


def _split_args(raw: str) -> List[str]:
    s = raw.strip()
    if not s:
        return []
    out: List[str] = []
    cur: List[str] = []
    depth = 0
    in_str = False
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == '"':
            in_str = not in_str
            cur.append(ch)
            i += 1
            continue
        if not in_str:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            elif ch == "," and depth == 0:
                out.append("".join(cur).strip())
                cur = []
                i += 1
                continue
        cur.append(ch)
        i += 1
    if cur:
        out.append("".join(cur).strip())
    return out


def _find_assign_idx(text: str) -> int:
    i = 0
    n = len(text)
    depth = 0
    in_str = False
    while i < n:
        ch = text[i]
        if ch == '"':
            in_str = not in_str
            i += 1
            continue
        if not in_str:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            elif ch == "=" and depth == 0:
                left = text[i - 1] if i > 0 else ""
                right = text[i + 1] if i + 1 < n else ""
                if left not in ("=", "!", "<", ">") and right != "=":
                    return i
        i += 1
    return -1


def _replace_word(expr: str, word: str, new: str) -> str:
    return re.sub(rf"\b{re.escape(word)}\b", new, expr)


def _convert_expr(expr: str) -> str:
    s = expr.strip()
    s = _replace_word(s, "dogru", "1")
    s = _replace_word(s, "doğru", "1")
    s = _replace_word(s, "yanlis", "0")
    s = _replace_word(s, "yanlış", "0")
    s = _replace_word(s, "veya", "||")
    s = _replace_word(s, "ve", "&&")
    s = _replace_word(s, "degil", "!")
    s = _replace_word(s, "değil", "!")
    return s


def _is_print_call(line: str) -> Optional[str]:
    m = re.match(r"^(yazdir|yazdır)\s*\((.*)\)\s*$", line.strip())
    if not m:
        return None
    return m.group(2)


def _print_to_c(line: str) -> str:
    raw_args = _is_print_call(line)
    if raw_args is None:
        raise NativeCompileError(f"Gecersiz yazdir cagrisi: {line}")
    args = _split_args(raw_args)
    if not args:
        return 'printf("\\n");'

    specs: List[str] = []
    values: List[str] = []
    for a in args:
        t = a.strip()
        if len(t) >= 2 and t[0] == '"' and t[-1] == '"':
            specs.append("%s")
            values.append(t)
        else:
            specs.append("%g")
            values.append(_convert_expr(t))
    fmt = " ".join(specs) + "\\n"
    return f'printf("{fmt}", {", ".join(values)});'


def _parse_func_header(line: str) -> Tuple[str, List[str]]:
    cleaned = _strip_colon(line.strip())
    m = re.match(r"^fonksiyon\s+([A-Za-z_][A-Za-z0-9_]*)\s*\((.*)\)$", cleaned)
    if not m:
        raise NativeCompileError(f"Gecersiz fonksiyon tanimi: {line}")
    name = m.group(1)
    params_raw = m.group(2).strip()
    params: List[str] = []
    if params_raw:
        for p in _split_args(params_raw):
            ident = p.strip()
            if not _IDENT_RE.match(ident):
                raise NativeCompileError(f"Gecersiz parametre adi: {ident}")
            params.append(ident)
    return name, params


def _web_runtime_lines() -> List[str]:
    return [
        "#include <stdlib.h>",
        "#include <string.h>",
        "#include <ctype.h>",
        "#include <unistd.h>",
        "#include <arpa/inet.h>",
        "#include <sys/socket.h>",
        "#include <netinet/in.h>",
        "",
        "static int port_oku(int default_port) {",
        "    const char* p = getenv(\"PORT\");",
        "    if (!p || !*p) return default_port;",
        "    int v = atoi(p);",
        "    return v > 0 ? v : default_port;",
        "}",
        "",
        "static int _json_al(const char* body, const char* key, char* out, size_t out_sz) {",
        "    if (!body || !key || !out || out_sz == 0) return 0;",
        "    char pat[64];",
        "    snprintf(pat, sizeof(pat), \"\\\"%s\\\"\", key);",
        "    const char* p = strstr(body, pat);",
        "    if (!p) return 0;",
        "    p = strchr(p, ':');",
        "    if (!p) return 0;",
        "    p++;",
        "    while (*p && isspace((unsigned char)*p)) p++;",
        "    if (*p == '\"') p++;",
        "    size_t i = 0;",
        "    while (*p && *p != '\"' && *p != '\\n' && *p != '\\r' && i + 1 < out_sz) {",
        "        out[i++] = *p++;",
        "    }",
        "    out[i] = '\\0';",
        "    return i > 0;",
        "}",
        "",
        "static int _kullanici_gecerli(const char* s) {",
        "    if (!s || !*s) return 0;",
        "    for (const char* p = s; *p; ++p) {",
        "        if (*p == '\\t' || *p == '\\n' || *p == '\\r') return 0;",
        "    }",
        "    return 1;",
        "}",
        "",
        "static int _kayit_ekle(const char* db_path, const char* user, const char* pass) {",
        "    FILE* f = fopen(db_path, \"a+\");",
        "    if (!f) return -1;",
        "    rewind(f);",
        "    char line[512];",
        "    while (fgets(line, sizeof(line), f)) {",
        "        char* tab = strchr(line, '\\t');",
        "        if (!tab) continue;",
        "        *tab = '\\0';",
        "        if (strcmp(line, user) == 0) { fclose(f); return 0; }",
        "    }",
        "    fprintf(f, \"%s\\t%s\\n\", user, pass);",
        "    fclose(f);",
        "    return 1;",
        "}",
        "",
        "static int _giris_kontrol(const char* db_path, const char* user, const char* pass, int* found) {",
        "    FILE* f = fopen(db_path, \"r\");",
        "    if (!f) { if (found) *found = 0; return 0; }",
        "    if (found) *found = 0;",
        "    char line[512];",
        "    while (fgets(line, sizeof(line), f)) {",
        "        char* tab = strchr(line, '\\t');",
        "        if (!tab) continue;",
        "        *tab = '\\0';",
        "        char* pwd = tab + 1;",
        "        char* nl = strpbrk(pwd, \"\\r\\n\");",
        "        if (nl) *nl = '\\0';",
        "        if (strcmp(line, user) == 0) {",
        "            if (found) *found = 1;",
        "            int ok = (strcmp(pwd, pass) == 0);",
        "            fclose(f);",
        "            return ok;",
        "        }",
        "    }",
        "    fclose(f);",
        "    return 0;",
        "}",
        "",
        "static char* _dosya_oku(const char* path, size_t* out_len) {",
        "    FILE* f = fopen(path, \"rb\");",
        "    if (!f) return NULL;",
        "    if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return NULL; }",
        "    long n = ftell(f);",
        "    if (n < 0) { fclose(f); return NULL; }",
        "    if (fseek(f, 0, SEEK_SET) != 0) { fclose(f); return NULL; }",
        "    char* buf = (char*)malloc((size_t)n + 1);",
        "    if (!buf) { fclose(f); return NULL; }",
        "    size_t got = fread(buf, 1, (size_t)n, f);",
        "    fclose(f);",
        "    buf[got] = '\\0';",
        "    if (out_len) *out_len = got;",
        "    return buf;",
        "}",
        "",
        "static void _yanit_yaz(int cfd, int status, const char* ctype, const char* body) {",
        "    int blen = (int)strlen(body);",
        "    char hdr[512];",
        "    int n = snprintf(hdr, sizeof(hdr),",
        "        \"HTTP/1.1 %d OK\\r\\nContent-Type: %s\\r\\nContent-Length: %d\\r\\nConnection: close\\r\\n\\r\\n\",",
        "        status, ctype, blen);",
        "    send(cfd, hdr, (size_t)n, 0);",
        "    send(cfd, body, (size_t)blen, 0);",
        "}",
        "",
        "static void _json_yanit(int cfd, int ok, const char* msg) {",
        "    char body[512];",
        "    snprintf(body, sizeof(body), \"{\\\"ok\\\":%s,\\\"message\\\":\\\"%s\\\"}\", ok ? \"true\" : \"false\", msg);",
        "    _yanit_yaz(cfd, 200, \"application/json; charset=utf-8\", body);",
        "}",
        "",
        "static void _yanit_html(int cfd, const char* path) {",
        "    size_t n = 0;",
        "    char* html = _dosya_oku(path, &n);",
        "    if (!html) {",
        "        _yanit_yaz(cfd, 200, \"text/html; charset=utf-8\", \"<h1>Taylan Native Web</h1><p>index.html bulunamadi.</p>\");",
        "        return;",
        "    }",
        "    char hdr[512];",
        "    int h = snprintf(hdr, sizeof(hdr),",
        "        \"HTTP/1.1 200 OK\\r\\nContent-Type: text/html; charset=utf-8\\r\\nContent-Length: %zu\\r\\nConnection: close\\r\\n\\r\\n\",",
        "        n);",
        "    send(cfd, hdr, (size_t)h, 0);",
        "    if (n > 0) send(cfd, html, n, 0);",
        "    free(html);",
        "}",
        "",
        "static int tweb_baslat(int port, const char* html_path) {",
        "    int sfd = socket(AF_INET, SOCK_STREAM, 0);",
        "    if (sfd < 0) { perror(\"socket\"); return 1; }",
        "",
        "    int opt = 1;",
        "    setsockopt(sfd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));",
        "",
        "    struct sockaddr_in addr;",
        "    memset(&addr, 0, sizeof(addr));",
        "    addr.sin_family = AF_INET;",
        "    addr.sin_addr.s_addr = INADDR_ANY;",
        "    addr.sin_port = htons((unsigned short)port);",
        "",
        "    if (bind(sfd, (struct sockaddr*)&addr, sizeof(addr)) != 0) {",
        "        perror(\"bind\");",
        "        close(sfd);",
        "        return 1;",
        "    }",
        "    if (listen(sfd, 64) != 0) {",
        "        perror(\"listen\");",
        "        close(sfd);",
        "        return 1;",
        "    }",
        "",
        "    printf(\"Server running: http://0.0.0.0:%d\\n\", port);",
        "",
        "    while (1) {",
        "        int cfd = accept(sfd, NULL, NULL);",
        "        if (cfd < 0) continue;",
        "",
        "        char req[8192];",
        "        int r = (int)recv(cfd, req, sizeof(req) - 1, 0);",
        "        if (r <= 0) { close(cfd); continue; }",
        "        req[r] = '\\0';",
        "",
        "        char method[16] = {0};",
        "        char path[1024] = {0};",
        "        sscanf(req, \"%15s %1023s\", method, path);",
        "        const char* body = strstr(req, \"\\r\\n\\r\\n\");",
        "        if (body) body += 4; else body = \"\";",
        "",
        "        if (strcmp(method, \"GET\") == 0 && (strcmp(path, \"/\") == 0 || strcmp(path, \"/index.html\") == 0)) {",
        "            _yanit_html(cfd, html_path);",
        "        } else if (strcmp(method, \"GET\") == 0 && (strcmp(path, \"/dashboard\") == 0 || strcmp(path, \"/dashboard.html\") == 0)) {",
        "            _yanit_html(cfd, \"dashboard.html\");",
        "        } else if (strcmp(method, \"GET\") == 0 && strcmp(path, \"/health\") == 0) {",
        "            _yanit_yaz(cfd, 200, \"text/plain; charset=utf-8\", \"ok\");",
        "        } else if (strcmp(method, \"POST\") == 0 && (strcmp(path, \"/api/register\") == 0 || strcmp(path, \"/api/login\") == 0)) {",
        "            char username[128] = {0};",
        "            char password[128] = {0};",
        "            int ok_u = _json_al(body, \"username\", username, sizeof(username));",
        "            int ok_p = _json_al(body, \"password\", password, sizeof(password));",
        "            if (!ok_u || !ok_p || !_kullanici_gecerli(username) || !_kullanici_gecerli(password)) {",
        "                _json_yanit(cfd, 0, \"Kullanici adi ve sifre gerekli\");",
        "            } else if (strcmp(path, \"/api/register\") == 0) {",
        "                int reg = _kayit_ekle(\"users.db\", username, password);",
        "                if (reg == 1) _json_yanit(cfd, 1, \"Kayit basarili\");",
        "                else if (reg == 0) _json_yanit(cfd, 0, \"Bu kullanici zaten var\");",
        "                else _json_yanit(cfd, 0, \"Kayit hatasi\");",
        "            } else {",
        "                int found = 0;",
        "                int login_ok = _giris_kontrol(\"users.db\", username, password, &found);",
        "                if (login_ok) _json_yanit(cfd, 1, \"Giris basarili\");",
        "                else if (!found) _json_yanit(cfd, 0, \"Kullanici bulunamadi\");",
        "                else _json_yanit(cfd, 0, \"Sifre hatali\");",
        "            }",
        "        } else {",
        "            _yanit_yaz(cfd, 404, \"text/plain; charset=utf-8\", \"not found\");",
        "        }",
        "",
        "        close(cfd);",
        "    }",
        "",
        "    close(sfd);",
        "    return 0;",
        "}",
        "",
    ]


@dataclass
class _FnCtx:
    name: str
    params: List[str]
    lines: List[str] = field(default_factory=list)
    indent: int = 1
    stack: List[dict] = field(default_factory=list)


def compile_taylan_to_c(source: str) -> str:
    functions: List[_FnCtx] = []
    current_fn: Optional[_FnCtx] = None
    fn_phase = True

    main_lines: List[str] = []
    main_indent = 1
    main_stack: List[dict] = []

    assigned_vars: set[str] = set()
    fn_param_names: set[str] = set()
    uses_web_runtime = False

    for raw in source.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue

        if "tweb_baslat(" in line or "port_oku(" in line:
            uses_web_runtime = True

        if current_fn is None and (line.startswith("fonksiyon ") or line.startswith("function ")):
            if not fn_phase:
                raise NativeCompileError("Fonksiyonlar top-level ifade/komutlardan once tanimlanmali.")
            name, params = _parse_func_header(line)
            ctx = _FnCtx(name=name, params=params)
            sig = ", ".join(f"double {p}" for p in params) if params else "void"
            ctx.lines.append(f"double {name}({sig}) {{")
            functions.append(ctx)
            current_fn = ctx
            for p in params:
                fn_param_names.add(p)
            continue

        if current_fn is not None:
            out = current_fn.lines
            stack = current_fn.stack
            indent = current_fn.indent
            in_func = True
        else:
            fn_phase = False
            out = main_lines
            stack = main_stack
            indent = main_indent
            in_func = False

        if line == "bitti":
            if in_func:
                if stack:
                    current_fn.indent -= 1
                    _emit(out, current_fn.indent, "}")
                    stack.pop()
                else:
                    out.append("}")
                    current_fn = None
            else:
                if not stack:
                    raise NativeCompileError("Beklenmeyen 'bitti'.")
                main_indent -= 1
                _emit(out, main_indent, "}")
                stack.pop()
            continue

        if line.startswith("degilse") or line.startswith("değilse"):
            if not stack or stack[-1]["kind"] != "if" or stack[-1]["else"]:
                raise NativeCompileError("'degilse' sadece 'eger' blogundan sonra gelebilir.")
            if in_func:
                current_fn.indent -= 1
                _emit(out, current_fn.indent, "} else {")
                current_fn.indent += 1
            else:
                main_indent -= 1
                _emit(out, main_indent, "} else {")
                main_indent += 1
            stack[-1]["else"] = True
            continue

        if line.startswith("eger ") or line.startswith("eğer "):
            cond = _strip_colon(line.split(" ", 1)[1])
            cond_c = _convert_expr(cond)
            _emit(out, indent, f"if ({cond_c}) {{")
            stack.append({"kind": "if", "else": False})
            if in_func:
                current_fn.indent += 1
            else:
                main_indent += 1
            continue

        if line.startswith("dongu ") or line.startswith("döngü "):
            cond = _strip_colon(line.split(" ", 1)[1])
            cond_c = _convert_expr(cond)
            _emit(out, indent, f"while ({cond_c}) {{")
            stack.append({"kind": "while"})
            if in_func:
                current_fn.indent += 1
            else:
                main_indent += 1
            continue

        if line.startswith("dahil "):
            _emit(out, indent, f"/* {line} */")
            continue

        if line == "don" or line == "dön":
            _emit(out, indent, "return 0;")
            continue
        if line.startswith("don ") or line.startswith("dön "):
            expr = line.split(" ", 1)[1]
            _emit(out, indent, f"return {_convert_expr(expr)};")
            continue

        raw_print = _is_print_call(line)
        if raw_print is not None:
            _emit(out, indent, _print_to_c(line))
            continue

        eq = _find_assign_idx(line)
        if eq > 0:
            name = line[:eq].strip()
            expr = line[eq + 1 :].strip()
            if not _IDENT_RE.match(name):
                raise NativeCompileError(f"Gecersiz degisken adi: {name}")
            if name not in fn_param_names:
                assigned_vars.add(name)
            _emit(out, indent, f"{name} = {_convert_expr(expr)};")
            continue

        _emit(out, indent, f"{_convert_expr(line)};")

    if current_fn is not None:
        raise NativeCompileError("Fonksiyon blogu 'bitti' ile kapanmamis.")
    if main_stack:
        raise NativeCompileError("Top-level bloklardan bazisi kapanmamis.")

    out: List[str] = []
    out.append("#include <stdio.h>")
    if uses_web_runtime:
        out.extend(_web_runtime_lines())
    else:
        out.append("")

    out.append("/* generated by taylan native compiler (mvp) */")
    if assigned_vars:
        out.append("")
        for v in sorted(assigned_vars):
            out.append(f"static double {v} = 0;")

    if functions:
        out.append("")
        for fn in functions:
            out.extend(fn.lines)
            out.append("")

    out.append("int main(void) {")
    out.extend(main_lines)
    out.append("    return 0;")
    out.append("}")
    out.append("")
    return "\n".join(out)


def _run(cmd: Sequence[str]) -> None:
    try:
        p = subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError as e:
        raise NativeCompileError(f"Derleyici bulunamadi: {cmd[0]}") from e
    except subprocess.CalledProcessError as e:
        err = (e.stderr or "").strip()
        out = (e.stdout or "").strip()
        msg = err or out or "Bilinmeyen derleme hatasi"
        raise NativeCompileError(msg) from e
    if p.stderr.strip():
        print(p.stderr.strip())


def build_native(
    input_path: str,
    output_bin: Optional[str] = None,
    c_out: Optional[str] = None,
    cc: str = "gcc",
    emit_c_only: bool = False,
) -> Tuple[str, Optional[str]]:
    if not os.path.exists(input_path):
        raise NativeCompileError(f"Dosya yok: {input_path}")

    with open(input_path, "r", encoding="utf-8-sig") as f:
        source = f.read()
    c_code = compile_taylan_to_c(source)

    stem, _ = os.path.splitext(input_path)
    if emit_c_only:
        c_path = c_out or output_bin or (stem + ".c")
        with open(c_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(c_code)
        return c_path, None

    bin_path = output_bin or stem
    c_path = c_out or (bin_path + ".c")
    with open(c_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(c_code)

    cmd = [cc, c_path, "-O2", "-std=c11", "-o", bin_path]
    _run(cmd)
    return c_path, bin_path
