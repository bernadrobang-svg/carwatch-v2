# -*- coding: utf-8 -*-
"""추적표의 소스 · 화면 · 검사 칸을 기계로 채운다 (`inbox/ORDER_00_trace_fill.md`).

지시서   `docs/trace/*.md` · S34 · S38
근거     마스터 지적 — 「어디에 있는지 모르는데 됐다」가 538건이다
값규칙   ★ 세지 않는다.  채운다
        못 찾으면 「미구현」 · 「화면 없음」 · 「검사 없음」이라 적는다.
        ★ 빈 칸으로 두지 않는다 — 빈 칸은 「모른다」이고 그것이 가장 나쁘다
금지     손으로 고치는 것.  이 도구가 정본을 만든다
사용     python3.11 tools/trace_fill.py          무엇이 바뀌는지만 본다
        python3.11 tools/trace_fill.py --write  실제로 쓴다
"""
from __future__ import annotations

import ast
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACE = os.path.join(ROOT, "docs", "trace")

# 표의 칸 순서 (08-19 가이드가 다시 짰다).  ★ 손으로 세지 않는다
#   ★ R 번호가 SC-001 · WB-001 처럼 층 머리글자로 바뀌었고
#     금지·규칙 227건은 docs/trace/RULES.md 로 빠졌다 — 소스가 없는 게 맞다
COLS = ("R", "층", "요구사항", "출처", "규격", "소스", "화면", "검사", "상태")
I_R, I_LAYER, I_WHAT, I_WHY, I_SPEC, I_SRC, I_UI, I_CHK, I_ST = range(
    len(COLS))
N_COLS = len(COLS)

# 찾기 기준.  ★ 왜 이 값인지 함께 적는다 (V4-13)
MAX_TOKENS = 12          # 요구 하나에서 뽑는 낱말 수.  더 늘리면 흔한 말이 섞인다
MIN_TOKEN_HIT = 3        # 소스로 삼을 최소 겹침.  2 면 우연히 겹친 파일이 이긴다
MIN_CHECK_SCORE = 8      # 검사로 삼을 최소 점수.  낮추면 이웃 번호가 들어온다
MIN_PAIR_SCORE = 6       # 규격의 「검산」 짝을 믿을 최소 점수
MIN_ANCHOR_SCORE = 7     # 요구를 규격의 STEP 절에 붙일 최소 점수
CTX_LINES = 18           # 「검산」 줄 위로 몇 줄을 그 요구의 문맥으로 볼 것인가
SAMPLE = 5               # 보고에 낼 보기 수
RARE_MIN_LEN = 3         # 드문 낱말로 볼 최소 길이.  두 글자는 흔하다
RARE_MAX_FILES = 2       # 이 수 이하의 파일에만 있으면 「드물다」
NARROW_COLS = 4          # 좁은 표의 칸 수 — R · 요구사항 · 출처 · 상태
CHECKS_SPEC_COL = 7      # docs/CHECKS.md 의 「규격」 칸 번호

# 못 찾았을 때 적는 말.  ★ 빈 칸과 다르다
NO_SRC = "미구현"
# 가이드가 「층과 안 맞는다」고 되돌린 표시.  ★ 이것만 다시 찾는다
UNKNOWN = "미확인"

# 층 → 그 층의 디렉터리 (지시 §1).  ★ 층이 정해져 있으니 거기만 본다.
#   ★ 지난번에 층을 안 보고 전부 뒤져 374건이 딴 층으로 갔다
LAYER_DIRS: dict = {
    "수집": ("collect/", "adapters/", "config/endpoints.json",
             "config/targets.json"),
    "저장": ("store/", "sql/ddl/", "config/field_usage.json"),
    "파싱": ("parse/",),
    "사전": ("store/dict.py", "config/dictionaries/", "tools/build_dict.py"),
    # ★ 축 점수는 코드가 아니라 config 에 있다 (지시 §0).
    #   config 를 안 보면 배점 요구가 전부 「미구현」이 된다 — 오판 40건이 그것이다
    "판정": ("analyze/", "score/", "config/scoring.json",
             "config/depreciation.json", "config/sites.json",
             "config/dictionaries/"),
    "화면": ("web/", "report/", "config/labels.json", "config/web.json"),
    "검사": ("validate/", "tools/"),
    "운영": ("store/adminops.py", "store/admin.py", "deploy/", "web/views.py",
             "tools/", "config/admin.json", "config/checks.json"),
}
NO_UI = "화면 없음"
NO_UI_NA = "해당 없음"
NO_CHK = "검사 없음"
NO_CHK_SPEC = "검사 없음(규격에만)"

# 코드를 뒤질 디렉터리.  ★ ref/ 는 v1 사본이라 뺀다
CODE_DIRS = ("adapters", "analyze", "collect", "config", "parse", "report",
             "score", "sql", "store", "tools", "validate", "web")
SKIP_DIRS = {"__pycache__", "ref", ".git", "node_modules"}



def spec_lines() -> list:
    """[(규격 파일, 줄 내용, 그 줄이 속한 STEP)]."""
    import glob as _g

    out = []
    for path in sorted(_g.glob(os.path.join(ROOT, "docs", "chapters",
                                            "**", "*.md"), recursive=True)):
        rel = os.path.relpath(path, os.path.join(ROOT, "docs"))
        cur = ""
        for line in open(path, encoding="utf-8"):
            got = re.match(r"#{1,4}\s+(STEP [\w.-]+)", line.strip())
            if got:
                cur = got.group(1)
            out.append((rel, line.rstrip("\n"), cur))
    return out



def anchor_step(what: str, spec: str, slines: list) -> str:
    """이 요구가 규격의 어느 STEP 절에 있는가.  ★ 없으면 빈 문자열."""
    words = [w for w in tokens(what) if len(w) >= 2]
    if not words:
        return ""
    best = (0, "")
    for rel, line, step in slines:
        if not step:
            continue
        share = sum(1 for w in words if w in line)
        if share < 2:
            continue
        score = share * 2 + (3 if spec and spec in rel else 0)
        if score > best[0]:
            best = (score, step)
    return best[1] if best[0] >= MIN_ANCHOR_SCORE else ""



def build_symbols() -> tuple[dict, dict]:
    """파일마다 (줄 → 함수 이름) · (이름 → [파일::함수]).

    ★ 한 번만 만든다.  R 마다 소스를 훑으면 865번 훑는다
    """
    by_line: dict = {}
    by_name: dict = {}
    for base in CODE_DIRS:
        top = os.path.join(ROOT, base)
        if not os.path.isdir(top):
            continue
        for dirpath, dirs, files in os.walk(top):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for name in sorted(files):
                if not name.endswith(".py"):
                    continue
                full = os.path.join(dirpath, name)
                rel = os.path.relpath(full, ROOT)
                try:
                    tree = ast.parse(open(full, encoding="utf-8").read())
                except (SyntaxError, UnicodeDecodeError):
                    continue
                spans = []
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                         ast.ClassDef)):
                        end = getattr(node, "end_lineno", node.lineno)
                        spans.append((node.lineno, end, node.name))
                        by_name.setdefault(node.name, []).append(
                            f"{rel}::{node.name}")
                by_line[rel] = sorted(spans)
    return by_line, by_name



def enclosing(by_line: dict, rel: str, lineno: int) -> str:
    """그 줄이 든 가장 안쪽 함수·클래스 이름."""
    best = None
    for start, end, name in by_line.get(rel, ()):
        if start <= lineno <= end and (best is None or start > best[0]):
            best = (start, name)
    return best[1] if best else ""



def build_texts() -> dict:
    """파일마다 (줄 목록).  ★ 낱말이 몇 줄에 있는지까지 본다."""
    out: dict = {}
    for base in CODE_DIRS:
        top = os.path.join(ROOT, base)
        if not os.path.isdir(top):
            continue
        for dirpath, dirs, files in os.walk(top):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for name in sorted(files):
                if not name.endswith((".py", ".html", ".json", ".sql")):
                    continue
                full = os.path.join(dirpath, name)
                rel = os.path.relpath(full, ROOT)
                try:
                    out[rel] = open(full, encoding="utf-8").read().splitlines()
                except UnicodeDecodeError:
                    continue
    return out


# 낱말로 쓰지 않는 말.  ★ 어디에나 있어 변별이 안 된다
STOP = frozenset({
    "금지", "필수", "★", "것", "그것", "이것", "하는", "한다", "않는다", "있다",
    "없다", "된다", "낸다", "본다", "쓴다", "같은", "다른", "전부", "모든",
    "우리", "사람", "화면", "값이", "값을", "때는", "하지", "않고", "이다",
    "아니다", "수", "때", "안", "그", "더", "또", "및", "중", "때문", "위해",
})


# 조사.  ★ 주석은 「총액을」 「총액이」 처럼 어미가 달라진다 —
#   줄기로 잘라야 같은 말로 걸린다
_JOSA = ("으로써", "에서는", "이라는", "으로", "에서", "에게", "라고", "부터",
         "까지", "보다", "처럼", "만큼", "이나", "거나", "을", "를", "이",
         "가", "은", "는", "에", "의", "로", "와", "과", "도", "만", "고")



def _stem(word: str) -> str:
    """조사를 뗀 줄기.  ★ 두 글자 아래로 줄면 떼지 않는다 — 딴 말이 된다."""
    for j in _JOSA:
        if word.endswith(j) and len(word) - len(j) >= 2:
            return word[: -len(j)]
    return word



def tokens(text: str) -> list:
    """요구 문구에서 코드에서 찾을 만한 낱말을 뽑는다.

    ★ 백틱 안의 식별자가 가장 셈 — `VersionStamp` · `parse_version`
    ★ 그다음이 한글 낱말.  이 저장소는 주석이 한글이라 잘 걸린다
    """
    out = []
    for m in re.findall(r"`([^`]+)`", text):
        for part in re.split(r"[\s·,]+", m):
            part = part.strip("()[]{}.:「」")
            if len(part) >= 3 and re.search(r"[A-Za-z_]", part):
                out.append(part)
    plain = re.sub(r"`[^`]*`", " ", text)
    plain = re.sub(r"\*\*|\*", " ", plain)
    for w in re.findall(r"[가-힣]{2,}", plain):
        w = _stem(w)
        if w and w not in STOP:
            out.append(w)
    for w in re.findall(r"\b[A-Za-z_][A-Za-z0-9_]{3,}\b", plain):
        out.append(w)
    # 순서를 지키며 중복만 뺀다 — 앞의 것이 더 특징적이다
    seen, uniq = set(), []
    for w in out:
        if w not in seen:
            seen.add(w)
            uniq.append(w)
    return uniq[:MAX_TOKENS]



def _best_in(pool: list, words: list, texts: dict) -> tuple:
    """파일을 먼저 고르고 그 안에서 줄을 고른다.

    ★ 줄만 보고 고르면 낱말 하나가 우연히 몰린 엉뚱한 파일이 이긴다.
      파일이 그 요구를 「얼마나 아는가」가 먼저다 (실측 08-19 —
      「⑤ 사이트 보증」이 analyze/axes.py 로 갔다.  정답은 analyze/axis/site.py 다)
    """
    best_file = (0, 0, "")
    for rel in pool:
        lines = texts.get(rel) or []
        if not lines:
            continue
        joined = "\n".join(lines)
        have = [w for w in words if w in joined]
        if len(have) < 2:
            continue
        dense = max((sum(1 for w in have if w in ln) for ln in lines),
                    default=0)
        # ★ 이름이 요구의 낱말을 품으면 그 파일이 그 일을 하는 파일이다
        bonus = sum(1 for w in words if w.lower() in rel.lower())
        key = (len(have) + bonus, dense, rel)
        if key > best_file:
            best_file = key
    if not best_file[2]:
        return (0, "", 0)
    rel = best_file[2]
    lines = texts[rel]
    have = [w for w in words if w in "\n".join(lines)]
    n, at = 0, 1
    for i, line in enumerate(lines, 1):
        got = sum(1 for w in have if w in line)
        if got > n:
            n, at = got, i
    return (best_file[0], rel, at)



def _rows(path: str) -> list:
    """[(줄 번호, 칸들)].  ★ 표는 이제 한 형식이다 (9칸)."""
    out = []
    for i, line in enumerate(open(path, encoding="utf-8").read().splitlines()):
        if not re.match(r"^\| [A-Z]{2}-\d", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == len(COLS):
            out.append((i, cells))
    return out



def layers_of(cell: str) -> list:
    """「`[수집·화면]`」 → ["수집", "화면"].  ★ 층이 둘이면 둘 다 본다."""
    got = cell.strip("`[] ")
    return [x for x in re.split(r"[·,/]", got) if x.strip()]



def layer_pool(cell: str, texts: dict) -> list:
    """그 층의 디렉터리만.  ★ 층이 정해져 있으니 거기만 본다 (지시 §2)."""
    want: list = []
    for name in layers_of(cell):
        want += list(LAYER_DIRS.get(name.strip(), ()))
    if not want:
        return []
    return [r for r in texts
            if any(r == w or r.startswith(w) for w in want)]



def _rare_hit(words: list, pool: list, texts: dict, by_line: dict) -> str:
    """드문 낱말이 있는 자리.

    ★ 「연락함」 · 「보러 감」 처럼 그 요구에만 쓰는 말은 저장소에 한두 곳뿐이다.
      겹친 낱말 수만 세면 그 한 곳이 문턱에 걸려 「미구현」이 된다
    ★ 두 글자 낱말은 뺀다 — 흔해서 드물어 보일 뿐이다
    """
    best = (RARE_MAX_FILES + 1, "", 0)
    for w in words:
        if len(w) < RARE_MIN_LEN:
            continue
        where = [r for r in pool if w in "\n".join(texts.get(r) or ())]
        if not where or len(where) > RARE_MAX_FILES:
            continue
        rel = where[0]
        for i, ln in enumerate(texts[rel], 1):
            if w in ln and len(where) < best[0]:
                best = (len(where), rel, i)
                break
    if not best[1]:
        return ""
    return _place(best[1], best[2], by_line, texts)


def axis_words() -> dict:
    """한글 축 이름 → 축 키 (config/labels.json AXIS_LABELS).

    ★ 「사고 회수 40점」의 「사고」가 코드에는 `state.accident` 로 있다.
      한글만으로는 못 잇는다 — 정본이 이 표를 이미 갖고 있다
    """
    import json as _j

    path = os.path.join(ROOT, "config", "labels.json")
    if not os.path.isfile(path):
        return {}
    got = _j.load(open(path, encoding="utf-8")).get("AXIS_LABELS") or {}
    out: dict = {}
    for key, name in got.items():
        for part in re.split(r"[\s·]+", str(name)):
            part = part.strip()
            if len(part) >= 2:
                out.setdefault(part, []).append(key)
    return out


def json_key_at(lines: list, at: int) -> str:
    """그 줄이 속한 JSON 키 경로 (지시 §0).

    ★ `config/scoring.json:120` 은 「그 파일 어딘가」다.
      `config/scoring.json::components.warranty.site` 라야 짚은 것이다
    """
    path: list = []
    depth_of: list = []
    depth = 0
    for i, line in enumerate(lines[:at], 1):
        key = re.match(r'\s*"([^"]+)"\s*:', line)
        opens = line.count("{") + line.count("[")
        closes = line.count("}") + line.count("]")
        if key and opens > closes:
            path.append(key.group(1))
            depth_of.append(depth)
        elif key and i == at:
            path.append(key.group(1))
            depth_of.append(depth)
        depth += opens - closes
        while depth_of and depth <= depth_of[-1] and i != at:
            path.pop()
            depth_of.pop()
    got = [p for p in path if not p.startswith("_")]
    return ".".join(got[:4])


def _place(rel: str, at: int, by_line: dict, texts: dict) -> str:
    """찾은 자리를 사람이 읽을 꼴로.  ★ 형식마다 짚는 법이 다르다."""
    if rel.endswith(".json"):
        key = json_key_at(texts.get(rel) or [], at)
        return f"{rel}::{key}" if key else rel
    if rel.endswith((".html", ".sql")):
        return rel
    fn = enclosing(by_line, rel, at)
    return f"{rel}::{fn}" if fn else f"{rel}:{at}"


def find_in_layer(what: str, cell: str, texts: dict, by_line: dict,
                  by_name: dict, slines: list, spec: str = "") -> str:
    """그 층 안에서 소스를 찾는다.

    ★ 층 밖으로 나가지 않는다.  나가면 지난번처럼 딴 층으로 간다
    """
    pool = layer_pool(cell, texts)
    if not pool:
        return ""
    words = tokens(what)
    if not words:
        return ""
    # ★ 한글 축 이름을 축 키로 바꿔 함께 찾는다 —
    #   「사고」는 코드에 `state.accident` 로 있다 (config/labels.json)
    amap = axis_words()
    for w in list(words):
        for key in amap.get(w, ()):
            if key not in words:
                words.append(key)
    # ① 이름이 그대로 있는가 — ★ 그 층의 파일에 있는 것만
    inpool = set(pool)
    for w in words:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", w):
            continue
        for hit in by_name.get(w, ()):
            if hit.split("::")[0] in inpool:
                return hit
    # ② 낱말이 겹치는 자리
    # ★ 드문 낱말은 하나로 충분하다.  「연락함」은 저장소에 한 곳뿐이다 —
    #   개수만 세면 그 한 곳을 놓친다 (실측 08-19 — 진행 메모 셋을 다 놓쳤다)
    rare = _rare_hit(words, pool, texts, by_line)
    if rare:
        return rare
    best = _best_in(pool, words, texts)
    # ★ 낱말이 많은 요구는 더 많이 겹쳐야 믿는다.  열 낱말 중 셋은 우연이다
    need = max(min(MIN_TOKEN_HIT, len(words)), (len(words) + 2) // 3)
    if best[0] >= need:
        return _place(best[1], best[2], by_line, texts)
    # ③ 규격의 STEP 을 닻으로 — ★ 그래도 그 층 안에서만
    step = anchor_step(what, spec, slines)
    if step:
        got = _best_step_in(step, pool, texts, by_line, words)
        if got:
            return got
    return ""



def _best_step_in(step: str, pool: list, texts: dict, by_line: dict,
                  words: list) -> str:
    """그 STEP 을 인용한 자리 — ★ 주어진 층 안에서만.

    ★ STEP 을 많이 인용한다고 그 요구를 하는 파일은 아니다.
      요구의 낱말이 하나도 없으면 거절한다 —
      「SQL 은 표준 문법 우선」이 sync_registry 로 갔다 (실측 08-19)
    """
    best = (0, "")
    for rel in pool:
        lines = texts.get(rel) or []
        n = sum(1 for ln in lines if step in ln)
        if not n:
            continue
        if words and not any(w in "\n".join(lines) for w in words):
            continue
        if n > best[0]:
            best = (n, rel)
    if not best[1]:
        return ""
    rel = best[1]
    for i, ln in enumerate(texts[rel], 1):
        if step not in ln:
            continue
        fn = enclosing(by_line, rel, i)
        if fn:
            return f"{rel}::{fn}"
    return rel



def fill_file(path: str, ctxs: dict, write: bool,
              recheck: bool = False) -> dict:
    """「미확인」인 소스 칸만 다시 찾는다.

    ★ 가이드가 적어 둔 것은 손대지 않는다 (규칙 2 · S35-1).
      되돌린 것은 「미확인」이라 적혀 있다 — 그것만 내 몫이다
    """
    lines = open(path, encoding="utf-8").read().splitlines()
    stat = {"봄": 0, "찾음": 0, "못 찾음": 0}
    out = []
    for line in lines:
        if not re.match(r"^\| [A-Z]{2}-\d", line):
            out.append(line)
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        # ★ 「미구현」도 다시 본다 (--recheck).  층·config 를 넓히면
        #   전에 못 찾던 것이 잡힌다 — 지시 §0 의 「오판 40건」이 그것이다
        redo = (cells[I_SRC] == UNKNOWN
                or (recheck and NO_SRC in cells[I_SRC]))
        if len(cells) != len(COLS) or not redo:
            out.append(line)
            continue
        stat["봄"] += 1
        got = find_in_layer(cells[I_WHAT], cells[I_LAYER], ctxs["texts"],
                            ctxs["by_line"], ctxs["by_name"], ctxs["slines"],
                            cells[I_SPEC].strip(" `"))
        if got:
            cells[I_SRC] = f"`{got}`"
            stat["찾음"] += 1
        else:
            cells[I_SRC] = NO_SRC
            stat["못 찾음"] += 1
        out.append("| " + " | ".join(cells) + " |")
    if write:
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(out) + "\n")
    return stat



def survey() -> dict:
    """지금 상태.  층별 · 소스별 · 상태별."""
    from collections import Counter

    got = {"행": 0, "층": Counter(), "소스": Counter(), "상태": Counter(),
           "층별상태": {}}
    for name in sorted(os.listdir(TRACE)):
        if not name.endswith(".md") or name in ("INDEX.md", "RULES.md"):
            continue
        for _i, cells in _rows(os.path.join(TRACE, name)):
            got["행"] += 1
            lay = cells[I_LAYER].strip("`[] ") or "?"
            st = cells[I_ST].strip("* ")
            src = cells[I_SRC]
            kind = (UNKNOWN if src == UNKNOWN
                    else NO_SRC if NO_SRC in src
                    else "있음" if src and src != "—" else "없음")
            got["층"][lay] += 1
            got["소스"][kind] += 1
            got["상태"][st] += 1
            got["층별상태"].setdefault(lay, Counter())[st] += 1
            got["층별상태"][lay][f"소스:{kind}"] += 1
    return got



def lists() -> dict:
    """§5-③ · §6 — 마스터가 볼 목록."""
    out = {"미구현": [], "화면 없음": [], "미확인": [], "층 모름": []}
    for name in sorted(os.listdir(TRACE)):
        if not name.endswith(".md") or name in ("INDEX.md", "RULES.md"):
            continue
        for _i, cells in _rows(os.path.join(TRACE, name)):
            lay = cells[I_LAYER].strip("`[] ") or "?"
            row = (cells[I_R], cells[I_WHAT][:56], lay)
            if cells[I_SRC] == UNKNOWN:
                out["미확인"].append(row)
            elif NO_SRC in cells[I_SRC]:
                out["미구현"].append(row)
            if cells[I_UI] in ("화면 없음",):
                out["화면 없음"].append(row)
            if lay in ("?", ""):
                out["층 모름"].append(row)
    return out



def write_index(now: dict) -> None:
    """docs/trace/INDEX.md — ★ 기계로 만든다 (지시 §7 · 층별 요약)."""
    body = [
        "# 추적표 색인",
        "",
        "**`python3.11 tools/trace_fill.py --write` 가 만든다. "
        "손으로 고치지 않는다.**",
        "",
        f"요구 **{now['행']}건** · 금지·규칙 227건은 "
        "[RULES.md](RULES.md) 로 뺐다 — 소스가 없는 게 맞다",
        "",
        "## 층별",
        "",
        "| 층 | R | ○ | ◐ | ✗ | 소스 있음 | 미구현 | 미확인 |",
        "|---|--:|--:|--:|--:|--:|--:|--:|",
    ]
    for lay in sorted(now["층"], key=lambda k: -now["층"][k]):
        c = now["층별상태"].get(lay, {})
        body.append(
            f"| {lay} | {now['층'][lay]} | {c.get('○', 0)} | {c.get('◐', 0)}"
            f" | {c.get('✗', 0)} | {c.get('소스:있음', 0)}"
            f" | {c.get('소스:미구현', 0)} | {c.get('소스:미확인', 0)} |")
    body += ["", "## 소스 칸", "", "| 무엇 | 몇 개 |", "|---|--:|"]
    for k in sorted(now["소스"]):
        body.append(f"| {k} | {now['소스'][k]} |")
    body += ["", "## 상태", "", "| 상태 | 몇 개 |", "|---|--:|"]
    for k in sorted(now["상태"]):
        body.append(f"| {k} | {now['상태'][k]} |")
    body += ["", "```",
             "★ 소스 칸은 기계가 그 층의 디렉터리에서 찾은 것이다.",
             "  층 밖으로 나가지 않는다 — 나가면 딴 층의 코드가 들어온다",
             "★ 단정인 것은 「미구현」뿐이다 — 「그 층에서 못 찾았다」는 사실이다",
             "★ 가이드가 적어 둔 칸은 손대지 않는다 (S35-1)",
             "```", ""]
    with open(os.path.join(TRACE, "INDEX.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(body) + "\n")



def main() -> int:
    write = "--write" in sys.argv
    before = survey()
    ctxs = {}
    ctxs["by_line"], ctxs["by_name"] = build_symbols()
    ctxs["texts"] = build_texts()
    ctxs["slines"] = spec_lines()
    total = {"봄": 0, "찾음": 0, "못 찾음": 0}
    for name in sorted(os.listdir(TRACE)):
        if not name.endswith(".md") or name in ("INDEX.md", "RULES.md"):
            continue
        got = fill_file(os.path.join(TRACE, name), ctxs, write,
                        "--recheck" in sys.argv)
        for k in total:
            total[k] += got[k]
    after = survey()
    print(f"{'쓰기' if write else '미리보기'} — 미확인 {total['봄']}건 중 "
          f"찾음 {total['찾음']} · 못 찾음 {total['못 찾음']}\n")
    print("| 소스 칸 | 전 | 후 |")
    print("|---|--:|--:|")
    for k in sorted(set(before["소스"]) | set(after["소스"])):
        print(f"| {k} | {before['소스'].get(k, 0)} | {after['소스'].get(k, 0)} |")
    print("\n| 층 | R | ○ | ◐ | ✗ | 소스 있음 | 미구현 |")
    print("|---|--:|--:|--:|--:|--:|--:|")
    for lay in sorted(after["층"], key=lambda k: -after["층"][k]):
        c = after["층별상태"].get(lay, {})
        print(f"| {lay} | {after['층'][lay]} | {c.get('○', 0)} "
              f"| {c.get('◐', 0)} | {c.get('✗', 0)} "
              f"| {c.get('소스:있음', 0)} | {c.get('소스:미구현', 0)} |")
    if write:
        write_index(after)
    return 0


if __name__ == "__main__":
    sys.exit(main())


if __name__ == "__main__":
    sys.exit(main())
