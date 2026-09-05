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
INDEX_MD = os.path.join(ROOT, "docs", "INDEX.md")
SCHEMA_MD = os.path.join(ROOT, "docs", "SCHEMA.md")
DDL_DIR = os.path.join(ROOT, "sql", "ddl")
# 지시서 한 파일이 이보다 길면 폴더로 쪼갠다 (개정 342 · S28-9).
# ★ 아래 BIG_FILE_LINES(200)와 다른 값이다 — 그것은 소스 색인에서
#   「무엇이 어디에」를 적는 기준이다.  같은 이름을 두 번 쓰면 뒤가 이긴다
#   (실측 08-18 — 800줄 넘는 것이 4개인데 38개로 나왔다)
DOC_SPLIT_LINES = 800
# 단위 환산 (2장 상수표 · V4-13)
BYTES_PER_KB = 1_024
# 색인이 스스로를 세지 않는다 — 기계가 만드는 넷
MADE_BY_MACHINE = ("INDEX.md", "SCHEMA.md", "CHECKS.md", "SOURCE.md",
                   "MAPPING.md")
# 이 줄 수를 넘으면 「무엇이 어디에」를 적는다 (규칙 11 ②)
BIG_FILE_LINES = 200
# 소스 색인에서 건너뛸 곳.  ★ 우리가 쓴 것이 아니다
SKIP_DIRS = {".git", "__pycache__", ".render_root", "ref", "outputs",
             "inbox", "docs", "web/static"}
# ★ V 는 하이픈이 있고 S 는 없다 (S24 · V3-41).  둘을 같은 무늬로 찾으면
#   S 가 통째로 안 걸린다 — 실측 08-17: S1~S27 이 「규격에 없다」로 나왔다
RE_V_CODE = re.compile(r"\bV\d+-\d+[a-z]?\b")


def guide_check_owners() -> str:
    """★★★★★★ 09-05 — ★ **가이드 검사를 ★ 누구 몫인지 갈라 적는다** (마스터 지시).

    ★ 마스터 — 「★ 검사 중에 ★ **너를 위한 것 · 개발을 위한 것**을 구분해」 · 「그래」
    ★ ★ 갈래는 ★ **그 검사가 무엇을 읽는가**로 정한다 —
      ★ `docs/`·`ref/screens/`·지시문·이력·사전 → ★ **가이드**
      ★ `collect/`·`store/`·`web/`·`score/`·`parse/`·`run.py` → ★ **개발측**
      ★ 배포를 열어 잰 수(`hidden_text.json`·`encar_collect.json`·`/admin/…`) → ★ **배포·값**
    ★ ★ ★ 이러면 ★ **개발측이 제 몫만 골라** 볼 수 있다
    """
    import io as _io
    import sys as _sys

    _sys.path.insert(0, ROOT)
    try:
        import validate.v0_guide as V
    except Exception:  # noqa: BLE001
        return ""
    import os as _os
    src = _io.open(_os.path.join(ROOT, "validate", "v0_guide.py"),
                   encoding="utf-8").read()
    GUIDE = ("docs/", "ref/screens", "outputs/ORDER", "03_이력", "00_버전",
             "06_오판", "07_밀린", "config/dictionaries", "config/targets",
             "RULES.md", "SOURCE.md", "INDEX.md")
    DEV = ("collect/", "store/", "web/", "score/", "parse/", "adapters/",
           "run.py", "tools/")
    out = {"가이드": [], "개발측": [], "배포·값": [], "둘 다": []}
    for row in V.CHECKS:
        code, name, fn = row[0], row[1], row[2]
        i = src.find("def " + fn.__name__)
        body = src[i:i + 3000] if i > 0 else ""
        g = any(k in body for k in GUIDE)
        d = any(k in body for k in DEV)
        key = "둘 다" if (g and d) else "가이드" if g else "개발측" if d else "배포·값"
        out[key].append((code, name))
    lines = ["", "## ★ 가이드 검사는 ★ **누구 몫인가** (09-05 · 마스터 지시)", "",
             "| 갈래 | 몇 개 | 무엇을 보나 | 누가 고치나 |",
             "|---|--:|---|---|",
             f"| ★ **가이드** | **{len(out['가이드'])}** | `docs/` · 시안 · 지시문 · 이력 · 사전 | ★ 가이드 |",
             f"| ★ **개발측** | **{len(out['개발측'])}** | `collect/` · `store/` · `web/` · `score/` · `parse/` | ★ 개발측 |",
             f"| ★ **배포·값** | **{len(out['배포·값'])}** | 배포를 열어 잰 수 | ★ 개발측이 고치고 ★ 가이드가 잰다 |",
             f"| 둘 다 | {len(out['둘 다'])} | 규격과 코드를 함께 | 둘 |", ""]
    for key in ("개발측", "배포·값", "가이드", "둘 다"):
        lines.append(f"### {key} ({len(out[key])})")
        lines.append("")
        for code, name in out[key]:
            lines.append(f"- `{code}` {name}")
        lines.append("")
    return "\n".join(lines)


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


# ★ `say(...)` 를 ★ 검사로 세는 자리 (아래 `_checks_in_code`).
#   ★★ `say` 는 ★ 세 파일에서 ★ 뜻이 다르다 —
#     `tools/check_src.py` · `tools/check_screens.py` → ★ 검사 한 줄이다
#     `report/screens/build.py:2495`                  → ★ 화면 문구다 (tone, head, …)
#   ★ 화면 쪽 `say("", …)` 의 첫 인자는 ★ 빈 문자열이라 ★ 코드로 읽으면 터진다
#   ★ 실측 08-24 — ★ `build_index.py` 가 ★ 194행 `head[0]` 에서 IndexError 로 죽어
#     ★ INDEX·CHECKS 가 ★ 낡은 채 굳어 있었다 (줄 수 29곳 어긋남)
SAY_DIRS = ("tools",)


def _checks_in_code() -> dict:
    """validate/ 의 Check(...) 와 ★ tools/ 의 say(...) 를 뽑는다.

    ★ 정규식으로 긁지 않는다.  AST 로 읽어야 인자 위치가 확실하다
    ★★ `say` 는 ★ `tools/` 것만 본다 — ★ 이 함수의 뜻이 처음부터 그것이었다.
       ★ `report/screens/` 의 `say` 는 ★ 화면 문구라 ★ 검사가 아니다
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
            elif (name == "say" and len(args) >= 2
                  and rel.split(os.sep)[0] in SAY_DIRS):
                found.setdefault(args[0], {
                    "code": args[0], "phase": args[0].split("-")[0],
                    "title": args[1], "severity": "fatal",
                    "source": rel, "line": node.lineno})
        found.update(_guide_checks(tree, rel))
    return found


# ★★★ `validate/v0_guide.py` 는 ★ `Check(...)` 를 안 쓴다 —
#   ★ `CHECKS = (("S46-75", "제목", 함수, "warn"), …)` 꼴의 ★ **튜플 표**다.
#   ★★ 그래서 ★ 이 색인이 ★ S43~S46 ★ 예순 몇 개를 ★ **한 번도 못 봤다**
#     (실측 08-26 — ★ `docs/CHECKS.md` 에 ★ `S46-` 이 ★ 0건이다).
#   ★ ★ 규칙 11 은 ★ 「검사를 더하거나 고치면 다시 돌린다」인데
#     ★ ★ 다시 돌려도 ★ 안 들어오니 ★ 색인이 ★ **거짓말을 하고 있었다**
#   ★ 손으로 적지 않는다 — ★ 기계가 읽게 한다 (규칙 11 「손으로 고치는 것 금지」)
GUIDE_CHECK_FILE = os.path.join("validate", "v0_guide.py")


def _guide_checks(tree, rel: str) -> dict:
    """`CHECKS = ((코드, 제목, 함수[, 등급]), …)` 표를 읽는다.

    ★ 함수 이름으로 ★ 그 함수가 정의된 줄을 찾아 ★ 소스 자리를 적는다 —
      ★ 표가 있는 줄이 아니라 ★ **검사가 사는 줄**이 쓸모 있다
    """
    if rel != GUIDE_CHECK_FILE:
        return {}
    at = {n.name: n.lineno for n in ast.walk(tree)
          if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    out: dict = {}
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Assign)
                and any(getattr(t, "id", "") == "CHECKS" for t in node.targets)
                and isinstance(node.value, ast.Tuple)):
            continue
        for row in node.value.elts:
            if not (isinstance(row, ast.Tuple) and len(row.elts) >= 3):
                continue
            code = getattr(row.elts[0], "value", None)
            title = getattr(row.elts[1], "value", None)
            fn = getattr(row.elts[2], "id", "")
            if not (isinstance(code, str) and isinstance(title, str)):
                continue
            kind = (getattr(row.elts[3], "value", "fatal")
                    if len(row.elts) > 3 else "fatal")
            out[code] = {"code": code, "phase": code.split("-")[0],
                         "title": title,
                         "severity": kind if isinstance(kind, str) else "fatal",
                         "source": rel, "line": at.get(fn, row.lineno)}
    return out


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


def last_runs() -> dict:
    """검사마다 마지막 통과 · 마지막 실패 (개정 344).

    ★ 「한 번도 안 돈 검사」가 드러난다 — 있는 줄 알았는데 안 도는 것이
      가장 위험하다.  checked_at 이 빈 행이 있어 run_id 로도 잰다
    """
    import sqlite3

    path = os.path.join(ROOT, "carwatch.db")
    if not os.path.isfile(path):
        return {}
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    out: dict = {}
    try:
        for code, passed, at, run in conn.execute(
            "SELECT code, passed, checked_at, run_id FROM audit_validation"
        ):
            when = (at or "")[:19] or _run_time(run)
            got = out.setdefault(code, {"pass": "", "fail": ""})
            key = "pass" if passed else "fail"
            if when > got[key]:
                got[key] = when
    except sqlite3.Error:
        return {}
    finally:
        conn.close()
    return out


def _run_time(run_id: str) -> str:
    """run_id 에서 시각을 뽑는다 (20260817T032131 · browser-20260816T065502)."""
    got = re.search(r"(\d{8})T(\d{6})", str(run_id or ""))
    if not got:
        return ""
    day, clock = got.group(1), got.group(2)
    return (f"{day[:4]}-{day[4:6]}-{day[6:]}T"
            f"{clock[:2]}:{clock[2:4]}:{clock[4:]}")


def sort_checks(code: dict, spec: dict, seen: dict) -> dict:
    """다섯 갈래 (개정 344).

    ② 죽은 검사    통과도 실패도 한 적 없다
    ④ 규격 없는 검사 코드에 있는데 근거가 없다
    ⑤ 검사 없는 규격 규격에 적었는데 코드에 없다  ★ 가장 위험하다
    ★ ① 중복 · ③ 못 잡는 검사는 기계가 못 가른다 — 가이드·테스터 몫이다
    """
    dead = sorted(c for c in code if not seen.get(c))
    return {
        "죽은 검사": dead,
        "규격 없는 검사": sorted(c for c in code if c not in spec),
        "검사 없는 규격": sorted(c for c in spec
                            if c not in code and spec[c]["asked"]),
    }


def build_checks() -> tuple:
    code = _checks_in_code()
    spec = _checks_in_docs(set(code))
    seen = last_runs()
    kinds = sort_checks(code, spec, seen)
    only_spec = kinds["검사 없는 규격"]
    only_code = kinds["규격 없는 검사"]

    def key(c: str):
        head, _, tail = c.partition("-")
        if not head:
            raise ValueError(
                f"검사 코드가 비어 있다: {c!r} — ★ `say(...)` 를 검사로 잘못 센 것이다. "
                "★ SAY_DIRS 를 보라 (tools/ 것만 세야 한다)")
        # ★★ 마지막에 ★ 코드 자체를 둔다 — ★ 키가 동률이면 ★ 차례가 안 정해진다.
        #   ★ `sorted` 는 안정 정렬이라 ★ 동률은 ★ 들어온 차례를 지키는데,
        #   ★ 들어오는 것이 ★ `set` 이라 ★ 실행마다 차례가 바뀐다 (해시 시드).
        #   ★ 실측 08-24 — ★ 같은 입력에 ★ 줄 차례가 달라져
        #     ★ 「생성물이 낡았다」가 ★ 늘 뜬다 (V1-08 · V2-10b · V4-06 …)
        return (head[0], int(head[1:] or 0),
                int(re.sub(r"\D", "", tail) or 0), c)

    lines = [
        "# 검사 색인 — 규격 ↔ 코드",
        "",
        "**`python3.11 tools/build_index.py` 가 만든다. 손으로 고치지 않는다.**",
        "",
        f"검사 **{len(code)}개**",
        "",
        "| 갈래 | 몇 개 | 누가 |",
        "|---|--:|---|",
        f"| ② 죽은 검사 — 통과도 실패도 한 적 없다 | **{len(kinds['죽은 검사'])}** | 개발측 |",
        f"| ④ 규격에 근거가 없는 검사 | **{len(only_code)}** | 가이드가 판단 |",
        f"| ⑤ ★ 규격에 있는데 코드에 없는 검사 | **{len(only_spec)}** | 개발측 |",
        "",
        "★ ① 중복 · ③ 못 잡는 검사는 기계가 못 가릅니다 — "
        "가이드·테스터 몫입니다 (개정 344).",
        "",
        "| 코드 | 무엇 | 등급 | 소스 | 마지막 통과 | 마지막 실패 | 규격 |",
        "|---|---|---|---|---|---|---|",
    ]
    for c in sorted(set(code) | set(spec), key=key):
        got, doc = code.get(c), spec.get(c, {})
        where = " · ".join(doc.get("where", [])) or "—"
        ran = seen.get(c) or {}
        ok = (ran.get("pass") or "").replace("T", " ")[:16] or "**★ 없음**"
        no = (ran.get("fail") or "").replace("T", " ")[:16] or "없음"
        if got:
            lines.append(f"| `{c}` | {got['title']} | {got['severity']} | "
                         f"`{got['source']}:{got['line']}` | {ok} | {no} | "
                         f"{where} |")
        elif doc.get("asked"):
            lines.append(f"| `{c}` | — | — | **★ 코드에 없다** | — | — | "
                         f"{where} |")
    if kinds["죽은 검사"]:
        lines += ["", "## ② 죽은 검사 — 한 번도 안 돌았다", "",
                  "★ 「있다」와 「돈다」는 다릅니다. "
                  "안 도는 검사는 지키는 척만 합니다.", ""]
        lines += [f"- `{c}` {code[c]['title']} — `{code[c]['source']}`"
                  for c in kinds["죽은 검사"]]
    if only_spec:
        lines += ["", "## ⑤ ★ 규격이 요구했는데 코드에 없는 검사", ""]
        lines += [f"- `{c}` — {' · '.join(spec[c]['where'])}" for c in only_spec]
    if only_code:
        lines += ["", "## ④ 코드에 있는데 규격에 안 적힌 검사", ""]
        lines += [f"- `{c}` {code[c]['title']} — `{code[c]['source']}`"
                  for c in only_code]
    # ★★★ 09-05 — ★ **누구 몫인지 갈래를 함께 낸다** (마스터 지시)
    lines.append(guide_check_owners())
    with open(CHECKS_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return len(code), only_spec, only_code, kinds


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


def build_schema() -> int:
    """DDL 에서 표 색인을 만든다 (개정 343 · S28-10).

    ★ 손으로 적으면 표가 늘 때 빠진다.  DDL 이 정본이다
    """
    if not os.path.isdir(DDL_DIR):
        return 0
    lines = [
        "# SCHEMA — DB 색인",
        "",
        "**`python3.11 tools/build_index.py` 가 만든다. 손으로 고치지 않는다.**",
        "",
        "```",
        "읽는 법   이 표에서 찾고 sql/ddl/*.sql 을 연다",
        "검산     S28-10  DDL 의 표가 이 파일과 같은가",
        "```",
        "",
    ]
    total = 0
    for name in sorted(os.listdir(DDL_DIR)):
        if not name.endswith(".sql"):
            continue
        body = open(os.path.join(DDL_DIR, name), encoding="utf-8").read()
        head = [x.lstrip("- ").strip() for x in body.splitlines()
                if x.startswith("--")][:2]
        tables = re.findall(
            r"CREATE TABLE(?: IF NOT EXISTS)? (\w+)\s*\((.*?)\n\);",
            body, re.S)
        if not tables:
            continue
        lines += [f"## `sql/ddl/{name}` — 표 {len(tables)}개", ""]
        if head:
            lines += ["> " + " / ".join(head), ""]
        lines += ["| 표 | 열 | 무엇 |", "|---|--:|---|"]
        for table, cols in tables:
            n = len([x for x in cols.splitlines()
                     if re.match(r"\s+\w+\s+(TEXT|INTEGER|REAL|BLOB|NUM)",
                                 x)])
            # ★ 그 CREATE TABLE 바로 위의 주석이 「무엇」이다.
            #   표 이름을 body.index 로 찾으면 앞쪽 주석에 먼저 걸린다
            at = re.search(rf"CREATE TABLE(?: IF NOT EXISTS)? {table}\b",
                           body)
            note = ""
            if at:
                for one in body[:at.start()].splitlines()[::-1]:
                    if one.startswith("--"):
                        note = one.lstrip("- ").strip()
                        break
                    if one.strip():
                        break
            lines.append(f"| `{table}` | {n} | {note[:60]} |")
            total += 1
        lines.append("")
    lines += [f"**표 {total}개.**", ""]
    with open(SCHEMA_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return total


def build_doc_index() -> tuple:
    """지시서 파일 색인 (개정 343 · S28-11).

    ★ 800줄을 넘으면 폴더로 쪼갠다 (개정 342 · S28-9) — 표시해 둔다
    """
    docs = os.path.join(ROOT, "docs")
    rows, big = [], []
    for base, dirs, files in os.walk(docs):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for name in sorted(files):
            if not name.endswith(".md"):
                continue
            path = os.path.join(base, name)
            rel = os.path.relpath(path, docs).replace("\\", "/")
            # ★★ 이름이 아니라 ★ 경로로 가른다 (실측 08-24) —
            #   ★ 이름으로 가르면 ★ `trace/INDEX.md` 가 ★ 생성물로 오해돼 빠진다.
            #   ★ 그것은 ★ 사람이 쓴 지시서다
            # ★ 생성물 넷(CHECKS·SOURCE·SCHEMA·MAPPING)은 ★ 함께 싣는다 —
            #   ★ 규칙 11 이 ★ 「개발측이 쓰는 docs 파일」이라 못 박았다
            # ★ 자기 자신(INDEX.md)만 뺀다 — ★ 실으면 줄 수가 스스로 바뀌어
            #   ★ 생성기가 ★ 결정적이지 않게 된다 (S46-32 가 늘 빨간불이 된다)
            if rel == "INDEX.md":
                continue
            with open(path, encoding="utf-8") as f:
                body = f.read()
            n = body.count("\n") + 1
            rows.append((rel, n, len(body.encode("utf-8")) // BYTES_PER_KB))
            if n > DOC_SPLIT_LINES:
                big.append(f"{rel} {n:,}줄")
    rows.sort()
    lines = [
        "# INDEX — 지시서 색인",
        "",
        "**`python3.11 tools/build_index.py` 가 만든다. 손으로 고치지 않는다.**",
        "",
        "```",
        "읽는 법   1  이 표에서 파일을 고른다",
        "         2  소스를 고칠 때는 MAPPING.md 로 챕터를 찾는다",
        "         3  검사를 고칠 때는 CHECKS.md · DB 는 SCHEMA.md",
        "금지     docs/ 전체를 읽는 것",
        "```",
        "",
        f"**{len(rows)}파일 · {sum(r[1] for r in rows):,}줄 · "
        f"{sum(r[2] for r in rows):,}KB**",
        "",
    ]
    if big:
        lines += [f"★ {DOC_SPLIT_LINES}줄을 넘는 파일 {len(big)}개 — "
                  "폴더로 쪼갭니다 (개정 342 · S28-9)", ""]
        lines += [f"- {x}" for x in big] + [""]
    lines += ["| 파일 | 줄 | KB |", "|---|--:|--:|"]
    for rel, n, kb in rows:
        mark = "  ★" if n > DOC_SPLIT_LINES else ""
        lines.append(f"| `{rel}`{mark} | {n:,} | {kb:,} |")
    lines.append("")
    with open(INDEX_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return len(rows), big


# ★★ 생성물 — ★ 손으로 고치지 않는다.  ★ 생성기가 정본이다 (규칙 11)
GENERATED = ("docs/CHECKS.md", "docs/SOURCE.md", "docs/SCHEMA.md",
             "docs/INDEX.md")


def check_fresh() -> int:
    """★ 생성물이 ★ 낡았는가 (명령서 29장 ② · 검사 S46-32).

    ★ 생성기를 돌려 ★ 결과가 ★ 파일과 같은지 본다.  ★ 다르면 낡은 것이다
    ★ 실측 08-24 — ★ 생성기가 죽어 있는 동안 ★ 줄 수가 29곳 어긋나 있었다.
      ★ 이 검사가 있었으면 ★ 죽은 날 바로 잡혔다
    ★ 파일을 ★ 고치지 않는다 — ★ 재 보고 되돌린다
    """
    before = {}
    for rel in GENERATED:
        q = os.path.join(ROOT, rel)
        before[rel] = open(q, encoding="utf-8").read() if os.path.isfile(q) else None
    try:
        build_checks(); build_source(); build_schema(); build_doc_index()
        stale = []
        for rel in GENERATED:
            q = os.path.join(ROOT, rel)
            now = open(q, encoding="utf-8").read() if os.path.isfile(q) else None
            if now != before[rel]:
                stale.append(rel)
    finally:
        # ★ 재 보기만 한다.  ★ 있던 그대로 되돌린다
        for rel, said in before.items():
            if said is not None:
                open(os.path.join(ROOT, rel), "w", encoding="utf-8").write(said)
    if stale:
        print("★ 생성물이 낡았다 — " + " · ".join(stale))
        print("  고치는 법 — python3.11 tools/build_index.py")
        return 1
    print(f"생성물 {len(GENERATED)}개가 ★ 최신이다")
    return 0


def main() -> int:
    if "--check" in sys.argv:
        return check_fresh()
    n, only_spec, only_code, kinds = build_checks()
    files = build_source()
    print(f"검사 {n}개 → docs/CHECKS.md")
    print(f"  ② 죽은 검사 {len(kinds['죽은 검사'])}개 · "
          f"④ 규격 없는 검사 {len(kinds['규격 없는 검사'])}개 · "
          f"⑤ 검사 없는 규격 {len(kinds['검사 없는 규격'])}개")
    print(f"  규격이 요구했는데 코드에 없다  {len(only_spec)}개"
          + (f"  {', '.join(only_spec[:12])}" if only_spec else ""))
    print(f"  코드에 있는데 규격에 없다     {len(only_code)}개"
          + (f"  {', '.join(only_code[:12])}" if only_code else ""))
    print(f"소스 {files}개 → docs/SOURCE.md")
    tables = build_schema()
    print(f"DB 표 {tables}개 → docs/SCHEMA.md")
    docs_n, big = build_doc_index()
    print(f"지시서 {docs_n}파일 → docs/INDEX.md"
          + (f" · ★ 800줄 넘는 것 {len(big)}개" if big else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
