# -*- coding: utf-8 -*-
"""검사 색인 · 소스 색인을 만든다 (규칙 11).

지시서   RULE_11_source_check_index (가이드 요청 08-16)
근거     ★ 「V11-79 를 고쳐라」가 2,104줄을 읽으라는 뜻이면 안 된다.
         그리고 227개 검사가 규격과 맞는지 아무도 확인한 적이 없다.
필수     기계로 만든다.  손으로 적지 않는다
금지     docs/CHECKS.md · docs/SOURCE.md 를 손으로 고치는 것
         ★ 이 둘은 개발측이 쓰는 유일한 docs/ 파일이다 (가이드 지시).
           나머지 docs/ 는 규칙 2 대로 건드리지 않는다
사용     python3.11 tools/build_index.py
"""
from __future__ import annotations

import ast
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

CHECKS_MD = os.path.join(ROOT, "docs", "CHECKS.md")
SOURCE_MD = os.path.join(ROOT, "docs", "SOURCE.md")
# 이 줄 수를 넘으면 「무엇이 어디에」를 적는다 (규칙 11 ②)
BIG_FILE_LINES = 200
# 소스 색인에서 건너뛸 곳.  ★ 우리가 쓴 것이 아니다
SKIP_DIRS = {".git", "__pycache__", ".render_root", "ref", "outputs",
             "inbox", "docs", "web/static"}
# ★ V 는 하이픈이 있고 S 는 없다 (S24 · V3-41).  둘을 같은 무늬로 찾으면
#   S 가 통째로 안 걸린다 — 실측 08-17: S1~S27 이 「규격에 없다」로 나왔다
RE_V_CODE = re.compile(r"\bV\d+-\d+[a-z]?\b")


def _py_files() -> list:
    out = []
    for base, dirs, files in os.walk(ROOT):
        rel = os.path.relpath(base, ROOT)
        dirs[:] = [d for d in dirs
                   if d not in SKIP_DIRS
                   and os.path.join(rel, d).lstrip("./") not in SKIP_DIRS]
        if any(p in SKIP_DIRS for p in rel.split(os.sep)):
            continue
        for f in sorted(files):
            if f.endswith(".py"):
                out.append(os.path.join(base, f))
    return sorted(out)


def _checks_in_code() -> dict:
    """validate/ 의 Check(...) 와 tools/ 의 say(...) 를 뽑는다.

    ★ 정규식으로 긁지 않는다.  AST 로 읽어야 인자 위치가 확실하다
    """
    found: dict = {}
    for path in _py_files():
        rel = os.path.relpath(path, ROOT)
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = getattr(node.func, "id", None) or getattr(
                node.func, "attr", None)
            args = [a.value for a in node.args
                    if isinstance(a, ast.Constant) and isinstance(a.value, str)]
            if name == "Check" and len(args) >= 3:
                found[args[1]] = {
                    "code": args[1], "phase": args[0], "title": args[2],
                    "severity": args[3] if len(args) > 3 else "",
                    "source": rel, "line": node.lineno}
            elif name == "say" and len(args) >= 2:
                found.setdefault(args[0], {
                    "code": args[0], "phase": args[0].split("-")[0],
                    "title": args[1], "severity": "fatal",
                    "source": rel, "line": node.lineno})
    return found


def _checks_in_docs(known: set | None = None) -> dict:
    """docs/ 에서 검사 코드가 나온 자리를 모은다.

    ★ 「검산 V3-41」 처럼 규격이 요구한 곳을 먼저 본다.
      표(부록 A)에만 있는 것과 규격 본문이 요구한 것을 가른다
    """
    out: dict = {}
    base = os.path.join(ROOT, "docs")
    for cur, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in sorted(files):
            if not f.endswith(".md") or f in ("CHECKS.md", "SOURCE.md"):
                continue
            path = os.path.join(cur, f)
            rel = os.path.relpath(path, base)
            for i, line in enumerate(
                    open(path, encoding="utf-8").read().splitlines(), 1):
                codes = set(RE_V_CODE.findall(line))
                # S 코드는 하이픈이 없어 무늬로 못 찾는다 — 아는 이름만 짚는다
                for s_code in (known or set()):
                    if not s_code.startswith("S"):
                        continue
                    if re.search(r"\b" + re.escape(s_code) + r"\b", line):
                        codes.add(s_code)
                for code in codes:
                    got = out.setdefault(code, {"where": [], "asked": False})
                    if len(got["where"]) < 3:
                        got["where"].append(f"{rel}:{i}")
                    if "검산" in line:
                        got["asked"] = True
    return out


def build_checks() -> tuple:
    code = _checks_in_code()
    spec = _checks_in_docs(set(code))
    only_spec = sorted(c for c in spec if c not in code and spec[c]["asked"])
    only_code = sorted(c for c in code if c not in spec)

    def key(c: str):
        head, _, tail = c.partition("-")
        return (head[0], int(head[1:] or 0), int(re.sub(r"\D", "", tail) or 0))

    lines = [
        "# 검사 색인 — 규격 ↔ 코드",
        "",
        "**`python3.11 tools/build_index.py` 가 만든다. 손으로 고치지 않는다.**",
        "",
        f"검사 {len(code)}개 · 규격이 요구했는데 코드에 없는 것 **{len(only_spec)}개** · "
        f"코드에 있는데 규격에 없는 것 **{len(only_code)}개**",
        "",
        "| 코드 | 무엇 | 등급 | 소스 | 규격 |",
        "|---|---|---|---|---|",
    ]
    for c in sorted(set(code) | set(spec), key=key):
        got, doc = code.get(c), spec.get(c, {})
        where = " · ".join(doc.get("where", [])) or "—"
        if got:
            lines.append(f"| `{c}` | {got['title']} | {got['severity']} | "
                         f"`{got['source']}:{got['line']}` | {where} |")
        elif doc.get("asked"):
            lines.append(f"| `{c}` | — | — | **★ 코드에 없다** | {where} |")
    if only_spec:
        lines += ["", "## ★ 규격이 요구했는데 코드에 없는 검사", ""]
        lines += [f"- `{c}` — {' · '.join(spec[c]['where'])}" for c in only_spec]
    if only_code:
        lines += ["", "## 코드에 있는데 규격에 안 적힌 검사", ""]
        lines += [f"- `{c}` {code[c]['title']} — `{code[c]['source']}`"
                  for c in only_code]
    with open(CHECKS_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return len(code), only_spec, only_code


def _outline(path: str) -> list:
    """파일 안에서 「무엇이 어디에」.  ★ 최상위 def · class 만 낸다."""
    try:
        tree = ast.parse(open(path, encoding="utf-8").read())
    except SyntaxError:
        return []
    return [f"{n.name}:{n.lineno}" for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                              ast.ClassDef))]


def build_source() -> int:
    rows = []
    for path in _py_files():
        rel = os.path.relpath(path, ROOT)
        n = sum(1 for _ in open(path, encoding="utf-8"))
        doc = ast.get_docstring(ast.parse(
            open(path, encoding="utf-8").read())) or ""
        rows.append((rel, n, doc.splitlines()[0] if doc else "—",
                     _outline(path)))
    rows.sort(key=lambda r: -r[1])
    lines = [
        "# 소스 색인",
        "",
        "**`python3.11 tools/build_index.py` 가 만든다. 손으로 고치지 않는다.**",
        "",
        f"파일 {len(rows)}개 · 총 {sum(r[1] for r in rows):,}줄",
        "",
        "| 파일 | 줄 | 무엇 |",
        "|---|--:|---|",
    ]
    lines += [f"| `{rel}` | {n:,} | {what} |" for rel, n, what, _o in rows]
    big = [r for r in rows if r[1] >= BIG_FILE_LINES]
    lines += ["", f"## 큰 파일 — 무엇이 어디에 ({BIG_FILE_LINES}줄 이상 "
                  f"{len(big)}개)", ""]
    for rel, n, _what, outline in big:
        lines += [f"### `{rel}` — {n:,}줄", "", "```",
                  "  ".join(outline) or "(최상위 정의 없음)", "```", ""]
    with open(SOURCE_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return len(rows)


def main() -> int:
    n, only_spec, only_code = build_checks()
    files = build_source()
    print(f"검사 {n}개 → docs/CHECKS.md")
    print(f"  규격이 요구했는데 코드에 없다  {len(only_spec)}개"
          + (f"  {', '.join(only_spec[:12])}" if only_spec else ""))
    print(f"  코드에 있는데 규격에 없다     {len(only_code)}개"
          + (f"  {', '.join(only_code[:12])}" if only_code else ""))
    print(f"소스 {files}개 → docs/SOURCE.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
