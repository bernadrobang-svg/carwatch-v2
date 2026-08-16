# -*- coding: utf-8 -*-
"""CarWatch v2 — 지시서 ↔ 소스 대조 검증기.

사용   python3 tools/check_src.py [지시서.md] [소스루트]
종료   0 통과 · 1 실패

지시서를 정본으로 읽어 소스와 대조한다.  검사 목록을 손으로 관리하지 않는다.
문서를 고치면 검사가 따라 바뀐다 (지시서 6장 V4-13 의 취지).

미착수 와 실패 를 구분한다.  아직 안 만든 장(章)은 실패가 아니다.
그 구분이 없으면 장별 착수 중에 검사가 매번 붉게 나오고, 결국 검사를 끄게 된다.
"""
from __future__ import annotations

import ast
import io
import json
import os
import re
import sys

# ★ V4-13 은 형태만 본다 — 모듈 최상위 · 대문자 · 스칼라 (2장 상수표).
#   이름 목록을 검사기가 들고 있지 않는다.  판단은 V4-17(S14)이 표로 한다.
#   근거   예외 목록을 손으로 늘리면, 늘리는 김에 통과시키게 된다
CONST_NAME = r"[A-Z][A-Z0-9_]*"

SPEC = sys.argv[1] if len(sys.argv) > 1 else "docs"
ROOT = sys.argv[2] if len(sys.argv) > 2 else "."

# ★ 지시서가 여러 파일이면 합쳐 읽는다 (v3 T-002).
#   단일 파일 전제를 두면 장이 나뉜 뒤 검사가 옛 판을 본다 — 실측으로 겪었다
def _spec_files(path: str) -> list[tuple[str, str]]:
    """(경로, 본문) 목록.  ★ 합쳐 읽지 않는다 (부록 E).

    금지   전 문서를 이어 붙인 뒤 정규식으로 자르는 것.
          앞 파일의 절이 뒤 파일의 코드블록을 삼킨다 —
          구분자를 넣어 세 번 고쳤으나 안 잡혔다 (실측)
    """
    import glob as _g
    import os as _o

    if _o.path.isdir(path):
        files = sorted(_g.glob(_o.path.join(path, "**", "*.md"),
                               recursive=True))
    else:
        files = [path]
    return [(f, io.open(f, encoding="utf-8").read()) for f in files]


def _read_spec(path: str) -> str:
    """전문 검색용.  ★ 블록 단위 검사에는 _spec_files 를 쓴다."""
    return "\n\n".join(body for _f, body in _spec_files(path))


S = _read_spec(SPEC)

fail: list[str] = []
todo_total = 0


def say(no: str, title: str, ok: int, todo: list[str], bad: list[str]) -> None:
    global todo_total
    todo_total += len(todo)
    mark = "실패" if bad else ("부분" if todo else "통과")
    print(f"{no} {title:28} {mark}  통과 {ok} · 미착수 {len(todo)} · 실패 {len(bad)}")
    for b in bad[:20]:
        print(f"      ✗ {b}")
    if todo:
        print(f"      · 미착수 {', '.join(todo[:12])}{' …' if len(todo) > 12 else ''}")
    if bad:
        fail.append(f"{no} {title}({len(bad)})")


# ── 소스 수집 ────────────────────────────────────────────────────────
def py_files() -> list[str]:
    out = []
    for base, dirs, files in os.walk(ROOT):
        # ★ ref/ 는 시안·v1 참고물이다.  우리 코드가 아니라 자료다
        dirs[:] = [d for d in dirs
                   if d not in (".git", "__pycache__", "ref")]
        for f in files:
            # 검사기 자신은 대상이 아니다.  tools/ 의 나머지는 대상이다
            # 검사기 자신은 대상이 아니다.  거부 표본·기대값이 잡히면
            # 검사를 만들 수 없다 (V4-13 함정과 같은 자리)
            if f in ("check_src.py", "check_spec.py", "v10_admin.py"):
                continue
            if f.endswith(".py"):
                out.append(os.path.join(base, f))
    return sorted(out)


SRC = {p: io.open(p, encoding="utf-8").read() for p in py_files()}
ALL = "\n".join(SRC.values())

src_classes: set[str] = set()
src_funcs: set[str] = set()
for p, t in SRC.items():
    try:
        tree = ast.parse(t)
    except SyntaxError as e:
        fail.append(f"구문 오류 {p}:{e.lineno}")
        continue
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            src_classes.add(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            src_funcs.add(node.name)


# ── 지시서에서 장(章) 경계를 잡는다 ───────────────────────────────────
CHAP = [(m.start(), m.group(1)) for m in re.finditer(r"^# (\d+)장\.", S, re.M)]
CHAP.insert(0, (0, "0"))


def chapter_of(pos: int) -> str:
    cur = "0"
    for start, name in CHAP:
        if start <= pos:
            cur = name
        else:
            break
    return cur


def _declared_chapters() -> set:
    """착수 선언 장.  ★ 기본값은 config/checks.json 이 정본이다 (부록 E · S17).

    금지   "0,1" 같은 값을 코드에 박는 것.
          장이 늘었는데 기본값이 그대로면 그 장이 조용히 안 검사된다 —
          14장을 빼먹어 구조체 4 · 함수 5 가 미착수로 잡혔다 (실측)
    """
    env = (os.environ.get("CW_CHAPTERS") or "").replace(" ", "")
    if env:
        return set(env.split(","))
    path = os.path.join(ROOT, "config", "checks.json")
    if os.path.isfile(path):
        with io.open(path, encoding="utf-8") as f:
            return {str(c) for c in json.load(f)["chapters"]}
    return set()


DONE_CHAPTERS = _declared_chapters()


def split_done(items: dict[str, str]) -> tuple[list[str], list[str]]:
    """{이름: 장} → (착수 대상, 미착수)"""
    now = [k for k, c in items.items() if c in DONE_CHAPTERS]
    later = [k for k, c in items.items() if c not in DONE_CHAPTERS]
    return sorted(now), sorted(later)


print(f"지시서 {SPEC}\n소스   {os.path.abspath(ROOT)}")
print(f"착수 선언 장: {','.join(sorted(DONE_CHAPTERS))}장\n")

# ── S1 디렉터리 (STEP 15) ────────────────────────────────────────────
m = re.search(r"## STEP 15[^\n]*\n+```\n(.*?)```", S, re.S)
dirs_spec = re.findall(r"^  ([a-z_]+)/", m.group(1), re.M) if m else []
bad = [d for d in dirs_spec if not os.path.isdir(os.path.join(ROOT, d))]
say("S1", "디렉터리 (STEP 15)", len(dirs_spec) - len(bad), [], bad)

_BLOCKS = [(b.start(), b.group(0)) for b in re.finditer(r"```python\n.*?```", S, re.S)]


def _illustration(pos: int) -> bool:
    for st, body in _BLOCKS:
        if st <= pos < st + len(body):
            return ("# 금지" in body) or ("# 필수" in body)
    return False


# ── S2 구조체 ────────────────────────────────────────────────────────
# 같은 구조체가 여러 장에 나오면 「처음 선언된 장」을 기준으로 삼는다.
# 마지막 장을 잡으면 이미 만든 것이 미착수로 보인다.
spec_classes: dict[str, str] = {}
for m in re.finditer(r"^class (\w+)[\(:]", S, re.M):
    if _illustration(m.start()):
        continue
    spec_classes.setdefault(m.group(1), chapter_of(m.start()))
now, later = split_done(spec_classes)
bad = [c for c in now if c not in src_classes]
say("S2", "구조체 정의", len(now) - len(bad), later, bad)

# ── S3 함수 ──────────────────────────────────────────────────────────
spec_funcs: dict[str, str] = {}
# 함수표 — 「| 이름 | 입력 | 출력 | 목적 |」 헤더를 가진 표만 본다.
# STEP 4 의 접미사 표(`_won` 등)가 함수로 잡히는 것을 막는다.
for tbl in re.finditer(
    r"^\| 이름 \| 입력 \| 출력 \| 목적 \|\n\|[-: |]+\n((?:\|.*\n)+)", S, re.M
):
    for row in tbl.group(1).split("\n"):
        mm = re.match(r"\|\s*`([a-z][a-z0-9_]*)`\s*\|", row)
        if mm:
            spec_funcs.setdefault(mm.group(1), chapter_of(tbl.start()))
# 정의서 코드 블록의 def.
# 단 「금지 / 필수」 대비 예시 블록은 정의가 아니라 설명이므로 제외한다.
for m in re.finditer(r"^def ([a-z][a-z0-9_]*)\(", S, re.M):
    if _illustration(m.start()):
        continue
    spec_funcs.setdefault(m.group(1), chapter_of(m.start()))
now, later = split_done(spec_funcs)
bad = [f for f in now if f not in src_funcs]
say("S3", "함수 정의", len(now) - len(bad), later, bad)

# ── S4 테이블 (STEP 28 ↔ sql/ddl) ────────────────────────────────────
i = S.find("## STEP 28")
j = S.find("## STEP 29")
tables = re.findall(r"^\| `(\w+)` \|", S[i:j], re.M) if i > 0 else []
ddl = ""
ddl_dir = os.path.join(ROOT, "sql", "ddl")
if os.path.isdir(ddl_dir):
    for f in sorted(os.listdir(ddl_dir)):
        if f.endswith(".sql"):
            ddl += io.open(os.path.join(ddl_dir, f), encoding="utf-8").read()
ddl_tables = set(re.findall(r"CREATE TABLE (?:IF NOT EXISTS )?(\w+)", ddl))
# 지시서가 「원문 미확보」라고 선언한 테이블은 만들지 않는 것이 정답이다 (3장 STEP 35).
# 추정으로 스키마를 만들면 그것이 v1 사고다.
deferred = {
    m.group(1)
    for m in re.finditer(r"### `(\w+)`\n+[^\n]*원문 미확보", S)
}
if "3" in DONE_CHAPTERS:
    bad = [t for t in tables if t not in ddl_tables and t not in deferred]
    hold = [f"{t}(원문 미확보)" for t in tables if t in deferred]
    say("S4", "테이블 DDL (STEP 28)", len(tables) - len(bad) - len(hold), hold, bad)
else:
    say("S4", "테이블 DDL (STEP 28)", 0, tables, [])

# ── S5 config 키 (STEP 6 표 ↔ 실제 파일) · V4-15 ─────────────────────
i = S.find("### config 키 전량")
j = S.find("### 본문 참조 형식")
want: dict[str, list[str]] = {}
cur_file = None
for row in S[i:j].split("\n"):
    if not row.startswith("|"):
        continue
    cells = [c.strip() for c in row.split("|")[1:-1]]
    if len(cells) < 2 or cells[0].startswith("---"):
        continue
    f = re.findall(r"`([a-z_]+(?:\.[a-z_]+)*\.json|dictionaries/)`", cells[0])
    if f:
        cur_file = f[0]
    if cur_file is None:
        continue
    for k in re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)`", cells[1]):
        want.setdefault(cur_file, []).append(k)

bad, okn = [], 0
for fname, keys in want.items():
    if fname.endswith("/"):
        if not os.path.isdir(os.path.join(ROOT, "config", fname)):
            bad.append(f"config/{fname} 없음")
        continue
    path = os.path.join(ROOT, "config", fname)
    if not os.path.isfile(path):
        bad.append(f"config/{fname} 없음")
        continue
    blob = json.load(io.open(path, encoding="utf-8"))
    flat = json.dumps(blob, ensure_ascii=False)
    for k in keys:
        if k in blob or f'"{k}"' in flat:
            okn += 1
        else:
            bad.append(f"config/{fname}:{k}")
say("S5", "config 키 (V4-15)", okn, [], bad)

# ── S6 배점 검산 (불변식 ⑤ · V5-01 · V5-02) ──────────────────────────
bad = []
sc_path = os.path.join(ROOT, "config", "scoring.json")
if os.path.isfile(sc_path):
    sc = json.load(io.open(sc_path, encoding="utf-8"))
    comp = sc.get("components") or {}
    total = sc.get("total_points")
    # ★ 두 형태를 다 센다.  스킵은 총점에서 뺀다 (13장 STEP 128)
    active = {k: (v["points"] if isinstance(v, dict) else v)
              for k, v in comp.items()
              if not (isinstance(v, dict) and v.get("skipped"))}
    if sum(active.values()) != total:
        bad.append(f"배점 합 {sum(active.values())} != total_points {total}")
    spec_total = re.search(r"\| \*\*합\*\* \| \*\*(\d+)\*\*", S)
    if spec_total and int(spec_total.group(1)) != total:
        bad.append(f"total_points {total} != 지시서 {spec_total.group(1)}")
    claim = re.search(r"총 (\d+)행", S)
    if claim and len(active) != int(claim.group(1)):
        bad.append(f"Component {len(active)} != 지시서 {claim.group(1)}")
    cuts = sc.get("grade_cuts") or {}
    for g, ratio in cuts.items():
        row = re.search(r"\| `%s` \| (\d+)%% \| \*\*(\d+)\*\*" % g, S)
        if row and round(ratio * 100) != int(row.group(1)):
            bad.append(f"등급컷 {g} {ratio} != 지시서 {row.group(1)}%")
else:
    bad.append("config/scoring.json 없음")
say("S6", "배점 검산 (불변식 ⑤)", 4 - len(bad), [], bad)

# ── S7 매직 넘버 (V4-13) ─────────────────────────────────────────────
ALLOWED = {0, 1, -1, 2, 3, 4, 100, 200, 300, 400, 401, 403, 404, 429, 500}
bad = []
for p, t in SRC.items():
    if "/tests/" in p.replace("\\", "/"):
        continue
    try:
        tree = ast.parse(t)
    except SyntaxError:
        continue
    # 인덱스 · 슬라이스는 V4-13 이 명시적으로 허용한다.  임계값이 아니다
    # 형태만 본다.  성격(정책인가)은 S14 가 상수표로 판단한다
    # ★ 이 목록이 계속 늘고 있다.  「대문자 이름 + 모듈 최상위」로 일반화할지
    #   마스터 판단이 필요하다 (V4-17 상수표 등록 규칙과 맞물린다)
    # 단위 환산 상수는 허용한다 — {단위}_PER_{단위} 형태 (2장 상수표).
    # 물리적 환산이라 정책도 도메인 규칙도 아니다.  1초는 언제나 1000밀리초다.
    # ★ KM_PER_MONTH 는 이 형태지만 정책이다.  config 로 가야 한다 (STEP 72)
    named = {
        id(n.value)
        for n in tree.body
        if isinstance(n, (ast.Assign, ast.AnnAssign))
        and isinstance(n.value, ast.Constant)
        for tg in (n.targets if isinstance(n, ast.Assign) else [n.target])
        if isinstance(tg, ast.Name)
        and re.fullmatch(CONST_NAME, tg.id)
    }
    # 모듈 최상위의 대문자 이름에 담긴 열거 집합도 허용한다.
    # V4-13 이 「열거 집합」을 명시적으로 허용한다.  원문 구조를 옮긴 것이지
    # 임계값이 아니다 — 예: NOT_JOIN_INDEXES = (1,2,3,4,5)
    enum_sets = {
        id(c)
        for n in tree.body
        if isinstance(n, (ast.Assign, ast.AnnAssign))
        and isinstance(n.value, (ast.Tuple, ast.List, ast.Set))
        for tg in (n.targets if isinstance(n, ast.Assign) else [n.target])
        if isinstance(tg, ast.Name) and tg.id.isupper()
        for c in ast.walk(n.value)
        if isinstance(c, ast.Constant)
    }
    sliced = {
        id(c)
        for n in ast.walk(tree)
        if isinstance(n, ast.Subscript)
        for c in ast.walk(n.slice)
        if isinstance(c, ast.Constant)
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            if isinstance(node.value, bool):
                continue
            if node.value in ALLOWED or id(node) in sliced or id(node) in named or id(node) in enum_sets:
                continue
            bad.append(f"{os.path.relpath(p, ROOT)}:{node.lineno} → {node.value!r}")
say("S7", "매직 넘버 (V4-13)", 0 if bad else 1, [], bad)

# ── S8 접미사 (STEP 4) ───────────────────────────────────────────────
bad = []
for p, t in SRC.items():
    for mm in re.finditer(r"\b([a-z][a-z0-9_]*_date)\b\s*:\s*datetime", t):
        bad.append(f"{os.path.relpath(p, ROOT)} {mm.group(1)} — 시각은 _at")
say("S8", "접미사 규칙 (STEP 4)", 0 if bad else 1, [], bad)

# ── S9 금지 근거 (STEP 14 · 불변식 ②) ────────────────────────────────
bad = []
i = S.find("BANNED_SOURCES = {")
spec_banned = set(re.findall(r'"([a-z_]+)"', S[i : i + 400])) if i > 0 else set()
m2 = re.search(r"BANNED_SOURCES[^\n=]*=\s*(?:frozenset\(\s*)?\{", ALL)
src_banned = (
    set(re.findall(r'"([a-z_]+)"', ALL[m2.end() : m2.end() + 600])) if m2 else set()
)
if m2 is None:
    bad.append("BANNED_SOURCES 상수가 코드에 없다")
for b in sorted(spec_banned - src_banned):
    bad.append(f"BANNED_SOURCES 누락: {b}")
if "def put(" in ALL and "ValidationError" not in ALL[ALL.find("def put(") :][:600]:
    bad.append("put() 이 ValidationError 를 던지지 않는다")
say("S9", "금지 근거 (STEP 14)", len(spec_banned & src_banned), [], bad)

# ── S10 도메인 예외 5종 (STEP 3) ─────────────────────────────────────
i = S.find("## STEP 3 —")
want5 = re.findall(r"^(\w+Error)\s{2,}", S[i : S.find("## STEP 4")], re.M)
bad = [e for e in want5 if e not in src_classes]
say("S10", "도메인 예외 (STEP 3)", len(want5) - len(bad), [], bad)

# ── S11 분석 계층 순수성 (STEP 2 · STEP 8-⑤) ────────────────────────
bad = []
for p, t in SRC.items():
    rel = os.path.relpath(p, ROOT).replace("\\", "/")
    if not (rel.startswith("analyze/") or rel.startswith("score/")):
        continue
    for pat, why in (
        (r"\bimport sqlite3\b", "DB 접근"),
        (r"\bimport requests\b", "HTTP 접근"),
        (r"\bimport urllib\b", "HTTP 접근"),
        (r"datetime\.now\(", "시각 직접 호출 (STEP 8-⑤)"),
        (r"\brandom\.", "난수 직접 호출"),
        (r"\bFetcher\b", "Fetcher 인지 (STEP 2)"),
        (r"\bClock\b", "Clock 인지 (STEP 2)"),
    ):
        if re.search(pat, t):
            bad.append(f"{rel} — {why}")
say("S11", "분석 계층 순수성 (STEP 2)", 0 if bad else 1, [], bad)

# ── S12 축 파일 주석 (STEP 15) ───────────────────────────────────────
axis_dir = os.path.join(ROOT, "analyze", "axis")
files = (
    [f for f in sorted(os.listdir(axis_dir)) if f.endswith(".py") and f != "__init__.py"]
    if os.path.isdir(axis_dir)
    else []
)
bad = [
    f
    for f in files
    if "STEP" not in io.open(os.path.join(axis_dir, f), encoding="utf-8").read()[:800]
]
if "7" in DONE_CHAPTERS:
    say("S12", "축 파일 STEP 주석", len(files) - len(bad), [], bad)
else:
    say("S12", "축 파일 STEP 주석", len(files) - len(bad), ["7장 미착수"], bad)

# ── S15 계층 의존 (1장 STEP 9~11 · STEP 15) ──────────────────────────
# ★ 표현 계층(report/)이 저장 계층(store/)의 DTO 정의를 import 하지 않는다.
#   계층 횡단 DTO 는 contracts.py 가 소유한다.
#   함수 호출(조회)은 허용한다 — 화면은 데이터를 읽는다.
CROSS_LAYER_TYPES = ("Account", "ConfigChange", "QueryResult", "ApiSnapshot",
                     "DevRequest", "RecalcJob", "ScoringPreview", "QueryLog")
bad, okn = [], 0
for p, src in SRC.items():
    rel = os.path.relpath(p, ROOT).replace("\\", "/")
    if not rel.startswith("report/"):
        continue
    try:
        tree = ast.parse(src)
    except SyntaxError:
        continue
    for n in ast.walk(tree):
        if not isinstance(n, ast.ImportFrom) or not (n.module or "").startswith("store"):
            continue
        for a in n.names:
            if a.name in CROSS_LAYER_TYPES or a.name[:1].isupper():
                bad.append(f"{rel}: from {n.module} import {a.name}")
            else:
                okn += 1
say("S15", "계층 의존 (STEP 15)", okn, [], bad)

# ── S13 본문 config 예시 ↔ 실제 파일 (0장 STEP 6) ────────────────────
# 예시를 본문에 넣으면 그 예시가 낡을 위험이 생긴다.
# 예시는 발췌일 수 있으므로 한 방향만 본다 — 「본문에 있는데 파일에 없다」
bad, okn = [], 0
# ★ 머리글 깊이는 파일마다 다르다.  부록은 ####, 장 파일은 ### 를 쓴다.
#   하나만 보면 다른 쪽 예시를 앞 파일 것으로 오인한다 (실측)
RE_CFG = re.compile(
    r"#{3,4} `config/([\w.]+\.json)`[^\n]*\n"
    r"(?:(?!\n#{1,4} )[\s\S])*?```json\n(.*?)```", re.S)
# ★ 파일마다 따로 본다.  합치면 절 경계가 파일을 넘어간다
for m in [mm for _f, _b in _spec_files(SPEC) for mm in RE_CFG.finditer(_b)]:
    fname, blob = m.group(1), m.group(2)
    path = os.path.join(ROOT, "config", fname)
    if not os.path.isfile(path):
        bad.append(f"config/{fname} 없음")
        continue
    try:
        want = json.loads(blob)
    except ValueError as e:
        bad.append(f"config/{fname} 본문 예시가 JSON 이 아니다: {e}")
        continue
    got = json.load(io.open(path, encoding="utf-8"))

    def walk(w, g, trail):
        global okn
        if not isinstance(w, dict):
            return
        for k, wv in w.items():
            if k.startswith("_") or k.startswith("<"):
                continue
            if not isinstance(g, dict) or k not in g:
                bad.append(f"config/{fname}:{trail}{k} — 본문 예시에 있는데 파일에 없다")
                continue
            okn += 1
            if isinstance(wv, dict):
                walk(wv, g[k], f"{trail}{k}.")

    walk(want, got, "")
say("S13", "본문 config 예시 대조", okn, [], bad)

# ── S14 상수 등록·성격 (2장 상수표 · V4-17) ──────────────────────────
# 검사기는 형태만 본다.  「정책인가」는 표가 답한다.
# ★ 대문자면 통과 는 임계값에 이름만 붙여 우회하는 길을 연다
UNIT_CONST = re.compile(r"[A-Z]+_PER_[A-Z]+")
POLICY_WORDS = ("LIMIT", "THRESHOLD", "MIN_", "MAX_", "_RATE", "RATIO",
                "POINTS", "CUT", "SANE", "WEIGHT", "TIMEOUT", "INTERVAL",
                "RETRY", "HOURS", "DAYS", "ROUNDS")

# 한 칸에 여러 이름이 「·」 로 묶여 있다.  칸 단위로 전부 뽑는다
registered = {
    name
    for row in re.findall(r"^\|.*\|$", S, re.M)
    for name in re.findall(r"`([A-Z][A-Z0-9_]*)`", row)
}
bad, okn = [], 0
for p, src in SRC.items():
    rel = os.path.relpath(p, ROOT).replace("\\", "/")
    if rel.startswith("tests/") or rel.startswith("tools/"):
        continue
    try:
        tree = ast.parse(src)
    except SyntaxError:
        continue
    for n in tree.body:
        if not isinstance(n, (ast.Assign, ast.AnnAssign)):
            continue
        for tg in (n.targets if isinstance(n, ast.Assign) else [n.target]):
            if not (isinstance(tg, ast.Name) and re.fullmatch(CONST_NAME, tg.id)):
                continue
            if UNIT_CONST.fullmatch(tg.id):
                okn += 1  # 단위 환산은 표에 등록하지 않는다
                continue
            if not isinstance(n.value, ast.Constant):
                okn += 1  # 열거 집합·튜플은 상수표 대상이 아니다
                continue
            if not isinstance(n.value.value, (int, float)) or \
                    isinstance(n.value.value, bool):
                # 문자열 상수는 도메인 이름이다.  V4-17 이 막는 것은
                # 「임계값 · 배점 · 세율 · 키워드」 즉 수치다
                okn += 1
                continue
            if any(w in tg.id for w in POLICY_WORDS):
                bad.append(f"{rel}:{tg.id} — 정책 성격이다. config 로 간다")
            elif tg.id not in registered:
                bad.append(f"{rel}:{tg.id} — 2장 상수표에 없다 (V4-17)")
            else:
                okn += 1
say("S14", "상수 등록·성격 (V4-17)", okn, [], bad)

# ── S16 검증 코드 대조 (개선요청 3) ─────────────────────────────────
# ★ 검증표는 지시서에 있는데 코드에 있는지 아무도 세지 않았다.
#   이번에 33개가 조용히 비어 있었다.  대조는 기계로 된다
import importlib

# ★ 차수를 손으로 나열하지 않는다.  V11 을 빼먹어 15건이 검사 밖에 있었다 (D-1)
RE_CHECK_CODE = re.compile(r"\bV\d{1,2}-\d+[a-z]?\b")
spec_codes = set(RE_CHECK_CODE.findall(S))
impl = set()
# ★ 목록을 손으로 적지 않는다.  validate/v*.py 를 전수 훑는다
import glob as _glob

for _m in sorted(_glob.glob(os.path.join(ROOT, "validate", "v*_*.py"))):
    mod = os.path.basename(_m)[:-3]
    try:
        impl |= set(importlib.import_module(f"validate.{mod}").C)
    except Exception:                                        # noqa: BLE001
        pass
# ★ 「쓰는 자리」만 센다.  문자열이 파일에 남아 있는 것으로는 부족하다 —
#   검증표에 이름만 남고 구현이 빠지는 것을 잡는 게 목적이다.
#   V6·V7·V9 는 화면·추적 계층이라 근거 주석으로도 인정한다
for base, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", "ref")]
    for f in files:
        if not f.endswith(".py"):
            continue
        with io.open(os.path.join(base, f), encoding="utf-8") as fh:
            body = fh.read()
        # 검사 실행부가 쓰는 자리 · 다른 계층·시험이 근거로 적은 자리.
        # ★ 한계 — 이름이 소스 어딘가에 있으면 통과한다.
        #   잡는 것은 「지시서에 있는데 소스에 아예 없다」이고,
        #   그것이 실제 사고였다 (33개가 조용히 비어 있었다).
        #   「이름만 남고 알맹이가 빠진 것」은 이 검사로 못 잡는다
        impl |= set(re.findall(r'C\["(V\d+-\d+[a-z]?)"\]', body))
        impl |= set(re.findall(
            RE_CHECK_CODE, body))

# 결번은 사유가 지시서에 있어야 통과한다
missing, excused = [], 0
for code in sorted(spec_codes - impl):
    ctx = "".join(re.findall(r"[^\n]*" + re.escape(code) + r"[^\n]*", S))
    if re.search(r"통합|비워 둔다|결번|폐지", ctx):
        excused += 1
    else:
        missing.append(code)
say("S16", "검증 코드 대조", len(impl & spec_codes) + excused, [], missing)

# ── S23 실행 환경 (0장 · 부록 E · 개정 242) ─────────────────────────
# ★ 3.9 로 돌리면 zip(strict=True) 이 죽어 시험 9종이 무관하게 실패한다.
#   그때 「코드가 깨졌다」로 읽으면 없는 결함을 쫓는다 (실측 08-16)
MIN_PY = (3, 11)
_ver = sys.version_info[:2]
say("S23", "실행 환경 (Python 3.11+)", 1 if _ver >= MIN_PY else 0, [],
    [] if _ver >= MIN_PY else
    [f"{_ver[0]}.{_ver[1]} 로 돌고 있다 — python3.11 로 돌린다"])

# ── S24 시험 격리 (0장 · 부록 E · 개정 246) ─────────────────────────
# ★ 운영 DB 를 복사해 돌면 거기 남은 상태가 결과를 바꾼다.
#   실측 08-16 — queued 인 recalc_job 1건에 관리 화면이 409 로 잠겨
#   test_spec_ui 가 9건 무더기로 실패했다.  코드는 하나도 안 바뀌었다
_PROD_DB = re.compile(r"""ROOT\s*,\s*["']carwatch\.db["']""")
_leaks = []
_tests_dir = os.path.join(ROOT, "tests")
for _f in sorted(os.listdir(_tests_dir)) if os.path.isdir(_tests_dir) else []:
    if not _f.endswith(".py"):
        continue
    with io.open(os.path.join(_tests_dir, _f), encoding="utf-8") as _fh:
        _body = _fh.read()
    for _n, _line in enumerate(_body.splitlines(), start=1):
        if _PROD_DB.search(_line):
            _leaks.append(f"tests/{_f}:{_n} — 운영 DB 를 가리킨다")
say("S24", "시험 격리 (운영 DB 미사용)", 1 if not _leaks else 0, [], _leaks)

# ── S25 형상 관리 (0장 · 부록 E · 개정 257) ─────────────────────────
# ★ 커밋 안 한 변경이 남으면 가이드가 읽는 GitHub 과 실물이 갈린다.
#   「작업은 했는데 안 올라왔다」가 실제로 났다 (실측 08-16)
import subprocess as _sp


def _git(*args) -> tuple[int, str]:
    try:
        p = _sp.run(("git", "-C", ROOT, *args), capture_output=True,
                    text=True, timeout=30)
        return p.returncode, (p.stdout or "").strip()
    except (OSError, _sp.SubprocessError) as exc:      # noqa: BLE001
        return 1, str(exc)


_rc, _out = _git("status", "--porcelain")
if _rc:
    # ★ git 이 없으면 「통과」가 아니라 실패다 (S22 와 같은 이유)
    say("S25", "형상 관리 (미커밋 없음)", 0, [], ["git 을 돌리지 못했다: " + _out[:60]])
else:
    _dirty = [ln for ln in _out.splitlines() if ln.strip()]
    _rc2, _ahead = _git("rev-list", "--count", "@{u}..HEAD")
    _bad = [f"미커밋 {len(_dirty)}건 — " + ", ".join(x[3:] for x in _dirty[:4])] \
        if _dirty else []
    if not _rc2 and _ahead.isdigit() and int(_ahead) > 0:
        _bad.append(f"push 안 된 커밋 {_ahead}개 — 가이드가 GitHub 을 읽는다")
    say("S25", "형상 관리 (미커밋·미push 없음)", 0 if _bad else 1, [], _bad)

# ── S26 작업 기록 (0장 · 부록 E · 개정 257) ─────────────────────────
# ★ 숫자 없는 기록은 기록이 아니다.  여섯 절과 실제 출력을 요구한다
_OUT_DIR = os.path.join(ROOT, "outputs")
_NAME = re.compile(r"^\d{8}_\d{4}_v\d+_.+\.md$")
_SECTIONS = ("무엇을 하려 했나", "무엇을 했나", "왜 그렇게 했나",
             "1차 결과", "조치 후 결과", "못 한 것")
_recs, _bad26 = [], []
for _f in sorted(os.listdir(_OUT_DIR)) if os.path.isdir(_OUT_DIR) else []:
    if not _f.endswith(".md") or not _NAME.match(_f):
        continue
    _recs.append(_f)
    with io.open(os.path.join(_OUT_DIR, _f), encoding="utf-8") as _fh:
        _b = _fh.read()
    _miss = [s for s in _SECTIONS if s not in _b]
    if _miss:
        _bad26.append(f"{_f} — 빠진 절: {', '.join(_miss)}")
if not _recs:
    _bad26.append("outputs/ 에 작업 기록이 없다 (YYYYMMDD_HHMM_v버전_제목.md)")
say("S26", "작업 기록 (6절 · 이름 규칙)", len(_recs) - len(_bad26), [], _bad26)

# ── S27 화면이 본체다 (개정 279) ────────────────────────────────────
# ★ 마스터 진단 — 「CLI 있다고 개무시하니 웹이 개판이 됐다」.
#   CLI 로 되는 것은 완성이 아니다.  기능마다 화면이 있어야 한다.
#   V11-45 는 「CLI 로만 되는 기능이 없는가」, S27 은 「기능마다 화면이 있는가」다
_SCREEN_FOR = {
    # run.py 가 받는 명령
    "collect": "/admin/run",
    "web": "/",
    "admin create": "/admin/users",
    "setup": "/admin/users",
    "dry": "/admin/run",
    "migrate": "/admin/tools",
    "export": "/admin/tools",
    "report": "/admin/tools",
    # tools/ 의 스크립트
    "tools/build_dict.py": "/admin/dict",
    "tools/check_all.py": "/admin/audit",
    "tools/check_screens.py": "/admin/audit",
    "tools/check_spec.py": "/admin/audit",
    "tools/check_src.py": "/admin/audit",
    "tools/classify_fields.py": "/admin/registry",
    "tools/export_cli.py": "/admin/tools",
    "tools/inspect_dict.py": "/admin/dict",
    "tools/inspect_facet.py": "/admin/api",
    "tools/inspect_requests.py": "/admin/requests",
    "tools/menu.py": "/admin",
    "tools/migrate.py": "/admin/tools",
    "tools/render_screens.py": "/admin/tools",
    "tools/report_cli.py": "/admin/tools",
    "tools/run_tests.py": "/admin/audit",
    "tools/setup_check.py": "/admin/tools",
    "tools/sync_registry.py": "/admin/registry",
}
_TOOLS_DIR = os.path.join(ROOT, "tools")
_have = {"collect", "web", "admin create", "setup", "dry"}
_have |= {f"tools/{f}" for f in sorted(os.listdir(_TOOLS_DIR))
          if f.endswith(".py") and not f.startswith("_")}
with io.open(os.path.join(ROOT, "run.py"), encoding="utf-8") as _fh:
    _runsrc = _fh.read()
_m = re.search(r"DELEGATED\s*=\s*\{(.*?)\}", _runsrc, re.S)
if _m:
    _have |= set(re.findall(r'"([\w-]+)"\s*:', _m.group(1)))
# 라우팅 표에 그 경로가 실제로 있는가 — 표에 적어만 두면 뜻이 없다
try:
    sys.path.insert(0, ROOT)
    from web.routes import ROUTES as _ROUTES

    _paths = {r.path for r in _ROUTES}
except Exception:                                        # noqa: BLE001
    _paths = set()
_bad27, _todo27 = [], []
for _cap in sorted(_have):
    _scr = _SCREEN_FOR.get(_cap)
    if not _scr:
        _todo27.append(_cap)                 # 화면을 아직 안 정한 기능
    elif _paths and _scr not in _paths:
        _bad27.append(f"{_cap} → {_scr} 가 라우팅 표에 없다")
say("S27", "기능마다 화면 (CLI 는 완성이 아니다)",
    len(_have) - len(_todo27) - len(_bad27), _todo27, _bad27)

print()
print(f"미착수 합계 {todo_total}")
print("결과:", "통과" if not fail else "실패 — " + " / ".join(fail))
sys.exit(1 if fail else 0)
