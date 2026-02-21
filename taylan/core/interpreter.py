from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Dict, Optional
import os
import json
import importlib


def _norm_name(name: str) -> str:
    table = str.maketrans({
        0x131: "i",  # ?
        0x130: "i",  # ?
        0x11F: "g",  # ?
        0x11E: "g",  # ?
        0xFC: "u",   # ?
        0xDC: "u",   # ?
        0x15F: "s",  # ?
        0x15E: "s",  # ?
        0xF6: "o",   # ?
        0xD6: "o",   # ?
        0xE7: "c",   # ?
        0xC7: "c",   # ?
    })
    return name.translate(table)


STDLIB_MODULES = {
    "tsql": "taylan_std.sql",
    "tmath": "taylan_std.math",
    "tml": "taylan_std.ml",
    "tdata": "taylan_std.data",
    "tdate": "taylan_std.date",
    "timg": "taylan_std.img",
    "tgame": "taylan_std.game",
    "thttp": "taylan_std.http",
    "tasync": "taylan_std.async",
    "tjson": "taylan_std.json",
    "tconfig": "taylan_std.config",
    "tlog": "taylan_std.log",
    "tcore": "taylan_std.core",
    "tweb": "taylan_std.web",
    "tauth": "taylan_std.auth",
    "tsqlite": "taylan_std.sqlite",
}

KEYWORDS = {
    "eger", "eğer", "degilse", "değilse", "bitti",
    "dongu", "döngü", "fonksiyon", "don", "dön",
    "dahil", "yazdir", "yazdır", "dogru", "doğru", "yanlis", "yanlış",
    "ve", "veya", "degil", "değil",
}


@dataclass
class Token:
    type: str
    value: Any
    line: int
    col: int


class Lexer:
    def __init__(self, source: str) -> None:
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: List[Token] = []

    def _peek(self) -> str:
        if self.pos >= len(self.source):
            return "\0"
        return self.source[self.pos]

    def _advance(self) -> str:
        ch = self._peek()
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _add(self, type_: str, value: Any, line: int, col: int) -> None:
        self.tokens.append(Token(type_, value, line, col))

    def lex(self) -> List[Token]:
        while self.pos < len(self.source):
            ch = self._peek()
            if ch in " \t\r":
                self._advance()
                continue
            if ch == "#":
                while self._peek() not in "\n\0":
                    self._advance()
                continue
            if ch == "\n":
                line, col = self.line, self.col
                self._advance()
                self._add("NEWLINE", "\n", line, col)
                continue
            if ch.isdigit():
                line, col = self.line, self.col
                num = ""
                while self._peek().isdigit():
                    num += self._advance()
                if self._peek() == ".":
                    num += self._advance()
                    while self._peek().isdigit():
                        num += self._advance()
                    self._add("NUMBER", float(num), line, col)
                else:
                    self._add("NUMBER", int(num), line, col)
                continue
            if ch == '"':
                line, col = self.line, self.col
                self._advance()
                s = ""
                while self._peek() not in "\0\n\"":
                    s += self._advance()
                if self._peek() != '"':
                    raise SyntaxError(f"String kapanmadı (satır {line})")
                self._advance()
                self._add("STRING", s, line, col)
                continue
            if ch.isalpha() or ch == "_":
                line, col = self.line, self.col
                ident = ""
                while self._peek().isalnum() or self._peek() == "_" or self._peek() in "ğüşıöçĞÜŞİÖÇ":
                    ident += self._advance()
                self._add("IDENT", ident, line, col)
                continue
            line, col = self.line, self.col
            two = self.source[self.pos:self.pos + 2]
            if two in ("==", "!=", "<=", ">="):
                self.pos += 2
                self.col += 2
                self._add("OP", two, line, col)
                continue
            if ch in "+-*/%=()<>:,":
                self._advance()
                self._add("OP", ch, line, col)
                continue
            raise SyntaxError(f"Bilinmeyen karakter: {ch} (satır {line})")

        self._add("EOF", None, self.line, self.col)
        return self.tokens


@dataclass
class Node:
    pass


@dataclass
class Program(Node):
    body: List[Node]


@dataclass
class Number(Node):
    value: Any


@dataclass
class String(Node):
    value: str


@dataclass
class Bool(Node):
    value: bool


@dataclass
class Var(Node):
    name: str


@dataclass
class Assign(Node):
    name: str
    value: Node


@dataclass
class BinOp(Node):
    left: Node
    op: str
    right: Node


@dataclass
class UnaryOp(Node):
    op: str
    expr: Node


@dataclass
class Call(Node):
    name: str
    args: List[Node]


@dataclass
class If(Node):
    cond: Node
    then_body: List[Node]
    else_body: Optional[List[Node]]


@dataclass
class While(Node):
    cond: Node
    body: List[Node]


@dataclass
class FuncDef(Node):
    name: str
    params: List[str]
    body: List[Node]


@dataclass
class Return(Node):
    value: Optional[Node]


@dataclass
class Import(Node):
    name: str


@dataclass
class ExprStmt(Node):
    expr: Node


class Parser:
    def __init__(self, tokens: List[Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _advance(self) -> Token:
        tok = self._peek()
        self.pos += 1
        return tok

    def _match(self, type_: str, value: Optional[str] = None) -> bool:
        tok = self._peek()
        if tok.type != type_:
            return False
        if value is not None and tok.value != value:
            return False
        self._advance()
        return True

    def _expect(self, type_: str, value: Optional[str] = None) -> Token:
        tok = self._peek()
        if tok.type != type_ or (value is not None and tok.value != value):
            raise SyntaxError(f"Beklenen {type_} {value} (satır {tok.line})")
        return self._advance()

    def parse(self) -> Program:
        body = self._parse_block(end_keywords=None)
        return Program(body)

    def _parse_block(self, end_keywords: Optional[set]) -> List[Node]:
        body: List[Node] = []
        while True:
            tok = self._peek()
            if tok.type == "EOF":
                break
            if tok.type == "NEWLINE":
                self._advance()
                continue
            if tok.type == "IDENT" and end_keywords and tok.value in end_keywords:
                break
            body.append(self._statement())
        return body

    def _statement(self) -> Node:
        tok = self._peek()
        if tok.type == "IDENT":
            val = tok.value
            if val in ("eger", "eğer"):
                return self._if_stmt()
            if val in ("degilse", "değilse", "bitti"):
                raise SyntaxError(f"Beklenmeyen '{val}' (satır {tok.line})")
            if val in ("dongu", "döngü"):
                return self._while_stmt()
            if val == "fonksiyon":
                return self._func_def()
            if val in ("don", "dön"):
                self._advance()
                if self._peek().type == "NEWLINE":
                    return Return(None)
                return Return(self._expr())
            if val == "dahil":
                self._advance()
                name_tok = self._peek()
                if name_tok.type == "STRING":
                    name = self._advance().value
                elif name_tok.type == "IDENT":
                    name = self._advance().value
                else:
                    raise SyntaxError(f"dahil için modül adı bekleniyor (satır {name_tok.line})")
                return Import(name)

            if self._lookahead_is_assign():
                name = self._advance().value
                self._expect("OP", "=")
                expr = self._expr()
                return Assign(name, expr)
            expr = self._expr()
            return ExprStmt(expr)

        raise SyntaxError(f"Beklenmeyen token (satır {tok.line})")

    def _lookahead_is_assign(self) -> bool:
        if self._peek().type != "IDENT":
            return False
        if self.tokens[self.pos + 1].type == "OP" and self.tokens[self.pos + 1].value == "=":
            return True
        return False

    def _if_stmt(self) -> If:
        self._advance()
        cond = self._expr()
        if self._match("OP", ":"):
            pass
        self._expect("NEWLINE")
        then_body = self._parse_block({"degilse", "değilse", "bitti"})
        else_body = None
        if self._peek().type == "IDENT" and self._peek().value in ("degilse", "değilse"):
            self._advance()
            if self._match("OP", ":"):
                pass
            self._expect("NEWLINE")
            else_body = self._parse_block({"bitti"})
        end = self._expect("IDENT")
        if end.value != "bitti":
            raise SyntaxError(f"bitti bekleniyordu (satır {end.line})")
        if self._peek().type == "NEWLINE":
            self._advance()
        return If(cond, then_body, else_body)

    def _while_stmt(self) -> While:
        self._advance()
        cond = self._expr()
        if self._match("OP", ":"):
            pass
        self._expect("NEWLINE")
        body = self._parse_block({"bitti"})
        end = self._expect("IDENT")
        if end.value != "bitti":
            raise SyntaxError(f"bitti bekleniyordu (satır {end.line})")
        if self._peek().type == "NEWLINE":
            self._advance()
        return While(cond, body)

    def _func_def(self) -> FuncDef:
        self._advance()
        name = self._expect("IDENT").value
        self._expect("OP", "(")
        params = []
        if not self._match("OP", ")"):
            while True:
                params.append(self._expect("IDENT").value)
                if self._match("OP", ","):
                    continue
                self._expect("OP", ")")
                break
        if self._match("OP", ":"):
            pass
        self._expect("NEWLINE")
        body = self._parse_block({"bitti"})
        end = self._expect("IDENT")
        if end.value != "bitti":
            raise SyntaxError(f"bitti bekleniyordu (satır {end.line})")
        if self._peek().type == "NEWLINE":
            self._advance()
        return FuncDef(name, params, body)

    def _expr(self) -> Node:
        return self._or()

    def _or(self) -> Node:
        expr = self._and()
        while self._peek().type == "IDENT" and self._peek().value == "veya":
            self._advance()
            right = self._and()
            expr = BinOp(expr, "veya", right)
        return expr

    def _and(self) -> Node:
        expr = self._not()
        while self._peek().type == "IDENT" and self._peek().value == "ve":
            self._advance()
            right = self._not()
            expr = BinOp(expr, "ve", right)
        return expr

    def _not(self) -> Node:
        if self._peek().type == "IDENT" and self._peek().value in ("degil", "değil"):
            self._advance()
            return UnaryOp("degil", self._not())
        return self._comparison()

    def _comparison(self) -> Node:
        expr = self._term()
        while self._peek().type == "OP" and self._peek().value in ("==", "!=", "<", ">", "<=", ">="):
            op = self._advance().value
            right = self._term()
            expr = BinOp(expr, op, right)
        return expr

    def _term(self) -> Node:
        expr = self._factor()
        while self._peek().type == "OP" and self._peek().value in ("+", "-"):
            op = self._advance().value
            right = self._factor()
            expr = BinOp(expr, op, right)
        return expr

    def _factor(self) -> Node:
        expr = self._unary()
        while self._peek().type == "OP" and self._peek().value in ("*", "/", "%"):
            op = self._advance().value
            right = self._unary()
            expr = BinOp(expr, op, right)
        return expr

    def _unary(self) -> Node:
        if self._peek().type == "OP" and self._peek().value in ("+", "-"):
            op = self._advance().value
            return UnaryOp(op, self._unary())
        return self._primary()

    def _primary(self) -> Node:
        tok = self._peek()
        if tok.type == "NUMBER":
            self._advance()
            return Number(tok.value)
        if tok.type == "STRING":
            self._advance()
            return String(tok.value)
        if tok.type == "IDENT":
            val = tok.value
            if val in ("dogru", "doğru"):
                self._advance()
                return Bool(True)
            if val in ("yanlis", "yanlış"):
                self._advance()
                return Bool(False)
            name = self._advance().value
            if self._match("OP", "("):
                args = []
                if not self._match("OP", ")"):
                    while True:
                        args.append(self._expr())
                        if self._match("OP", ","):
                            continue
                        self._expect("OP", ")")
                        break
                return Call(name, args)
            return Var(name)
        if self._match("OP", "("):
            expr = self._expr()
            self._expect("OP", ")")
            return expr
        raise SyntaxError(f"Beklenmeyen ifade (satır {tok.line})")


class ReturnSignal(Exception):
    def __init__(self, value: Any) -> None:
        self.value = value


class Interpreter:
    def __init__(self, base_dir: Optional[str] = None) -> None:
        self.globals: Dict[str, Any] = {}
        self.functions: Dict[str, FuncDef] = {}
        self.builtins: Dict[str, Any] = {}
        self.base_dir = base_dir or os.getcwd()

    def run(self, source: str) -> None:
        tokens = Lexer(source).lex()
        program = Parser(tokens).parse()
        self._exec_block(program.body, self.globals)

    def call_function(self, name: str, args: List[Any]) -> Any:
        if name not in self.functions:
            raise NameError(f"Bilinmeyen fonksiyon: {name}")
        func = self.functions[name]
        if len(args) != len(func.params):
            raise TypeError(f"{func.name} parametre sayisi uyusmuyor")
        local_env = dict(self.globals)
        for p, a in zip(func.params, args):
            local_env[p] = a
        try:
            self._exec_block(func.body, local_env)
        except ReturnSignal as rs:
            return rs.value
        return None

    def _exec_block(self, body: List[Node], env: Dict[str, Any]) -> Any:
        for stmt in body:
            self._exec(stmt, env)

    def _exec(self, node: Node, env: Dict[str, Any]) -> Any:
        if isinstance(node, Assign):
            env[node.name] = self._eval(node.value, env)
            return None
        if isinstance(node, ExprStmt):
            return self._eval(node.expr, env)
        if isinstance(node, If):
            if self._eval(node.cond, env):
                self._exec_block(node.then_body, env)
            elif node.else_body is not None:
                self._exec_block(node.else_body, env)
            return None
        if isinstance(node, While):
            while self._eval(node.cond, env):
                self._exec_block(node.body, env)
            return None
        if isinstance(node, FuncDef):
            self.functions[node.name] = node
            return None
        if isinstance(node, Return):
            value = self._eval(node.value, env) if node.value else None
            raise ReturnSignal(value)
        if isinstance(node, Import):
            self._import_module(node.name, env)
            return None
        raise RuntimeError("Bilinmeyen ifade")

    def _eval(self, node: Node, env: Dict[str, Any]) -> Any:
        if isinstance(node, Number):
            return node.value
        if isinstance(node, String):
            return node.value
        if isinstance(node, Bool):
            return node.value
        if isinstance(node, Var):
            if node.name in env:
                return env[node.name]
            raise NameError(f"Tanımsız değişken: {node.name}")
        if isinstance(node, UnaryOp):
            val = self._eval(node.expr, env)
            if node.op == "-":
                return -val
            if node.op == "+":
                return +val
            if node.op == "degil":
                return not bool(val)
        if isinstance(node, BinOp):
            left = self._eval(node.left, env)
            right = self._eval(node.right, env)
            op = node.op
            if op == "+":
                return left + right
            if op == "-":
                return left - right
            if op == "*":
                return left * right
            if op == "/":
                return left / right
            if op == "%":
                return left % right
            if op == "==":
                return left == right
            if op == "!=":
                return left != right
            if op == "<":
                return left < right
            if op == ">":
                return left > right
            if op == "<=":
                return left <= right
            if op == ">=":
                return left >= right
            if op == "ve":
                return bool(left) and bool(right)
            if op == "veya":
                return bool(left) or bool(right)
        if isinstance(node, Call):
            return self._call(node, env)
        raise RuntimeError("Bilinmeyen ifade")

    def _call(self, node: Call, env: Dict[str, Any]) -> Any:
        norm = _norm_name(node.name)
        if norm == "yazdir":
            args = [self._eval(a, env) for a in node.args]
            print(*args)
            return None
        if norm in self.builtins:
            args = [self._eval(a, env) for a in node.args]
            return self.builtins[norm](*args)
        if node.name in self.functions:
            func = self.functions[node.name]
            if len(node.args) != len(func.params):
                raise TypeError(f"{func.name} parametre sayisi uyusmuyor")
            local_env = dict(self.globals)
            for p, a in zip(func.params, node.args):
                local_env[p] = self._eval(a, env)
            try:
                self._exec_block(func.body, local_env)
            except ReturnSignal as rs:
                return rs.value
            return None
        raise NameError(f"Bilinmeyen fonksiyon: {node.name}")

    def _import_module(self, name: str, env: Dict[str, Any]) -> None:
        if name in STDLIB_MODULES:
            mod = importlib.import_module(STDLIB_MODULES[name])
            if hasattr(mod, "__all__"):
                for fname in mod.__all__:
                    self.builtins[_norm_name(fname)] = getattr(mod, fname)
            env[name] = {
                "name": name,
                "builtin": True,
            }
            return

        packages_dir = os.path.join(self.base_dir, "taylan_packages")
        registry_file = os.path.join(packages_dir, "registry.json")
        if not os.path.exists(registry_file):
            raise FileNotFoundError("Paket kaydi yok. Once kurulum yap.")
        with open(registry_file, "r", encoding="utf-8") as f:
            reg = json.load(f)
        if name not in reg:
            raise ImportError(f"Modul kurulu degil: {name}")
        env[name] = {
            "name": name,
            "source": reg[name]["source"],
        }
