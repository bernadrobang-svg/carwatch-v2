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

# 온전한 표의 칸 순서.  ★ 손으로 세지 않는다
COLS = ("R", "요구사항", "출처 · 근거", "규격", "소스", "화면", "검사",
        "테스트", "결함", "상태")
I_R, I_WHAT, I_WHY, I_SPEC, I_SRC, I_UI, I_CHK, I_TEST, I_DEF, I_ST = range(
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
NARROW_COLS = 4          # 좁은 표의 칸 수 — R · 요구사항 · 출처 · 상태
CHECKS_SPEC_COL = 7      # docs/CHECKS.md 의 「규격」 칸 번호

# 못 찾았을 때 적는 말.  ★ 빈 칸과 다르다
NO_SRC = "미구현"
NO_UI = "화면 없음"
NO_UI_NA = "해당 없음"
NO_CHK = "검사 없음"
NO_CHK_SPEC = "검사 없음(규격에만)"

# 코드를 뒤질 디렉터리.  ★ ref/ 는 v1 사본이라 뺀다
CODE_DIRS = ("adapters", "analyze", "collect", "parse", "report", "score",
             "store", "tools", "validate", "web")
SKIP_DIRS = {"__pycache__", "ref", ".git", "node_modules"}


def _tables(path: str) -> list:
    """R 행을 그대로 돌려준다.  [(줄번호, 칸들)]."""
    out = []
    for i, line in enumerate(open(path, encoding="utf-8")):
        if not line.startswith("| R-"):
            continue
        cells = [c.strip() for c in line.rstrip("\n").strip().strip("|").split("|")]
        out.append((i, cells))
    return out


# ── 소스 색인 ────────────────────────────────────────────────────────
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
                if not name.endswith((".py", ".html")):
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


def _mapping() -> dict:
    """챕터 → 디렉터리·파일 (docs/MAPPING.md).  ★ 손으로 적지 않는다."""
    out: dict = {}
    path = os.path.join(ROOT, "docs", "MAPPING.md")
    if not os.path.isfile(path):
        return out
    for line in open(path, encoding="utf-8"):
        got = re.match(r"^\| `([\w./-]+)` \| (.+?) \|", line)
        if not got:
            continue
        where = [x.strip(" `") for x in got.group(2).split("·")]
        out[got.group(1)] = [w for w in where if w and w != "—"]
    return out


def _candidates(spec: str, mapping: dict, texts: dict) -> list:
    """그 챕터가 가리키는 파일들.  없으면 전부 본다.

    ★ 챕터로 좁히면 「같은 낱말이 딴 층에도 있는」 오답이 준다
    """
    where = mapping.get(spec) or []
    got = []
    for w in where:
        w = w.rstrip("/")
        got += [r for r in texts if r == w or r.startswith(w + "/")
                or r == w]
    return got or list(texts)


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


def find_source(what: str, spec: str, mapping: dict, texts: dict,
                by_line: dict, by_name: dict) -> str:
    """요구 하나의 소스 자리.  없으면 빈 문자열.

    순서   ① 백틱 식별자가 함수·클래스 이름과 그대로 같은가
          ② 챕터가 가리키는 파일에서 낱말이 가장 많이 겹치는 줄
          ③ 못 찾으면 빈 문자열 — 부르는 쪽이 「미구현」이라 적는다
    """
    words = tokens(what)
    if not words:
        return ""
    # ① 이름이 그대로 있는가
    for w in words:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", w):
            continue
        hit = by_name.get(w)
        if hit:
            return hit[0]
    # ② 챕터가 가리키는 곳에서 찾는다.
    #   ★ validate/ 는 뺀다 — 검사는 「지키는가」이지 「하는 곳」이 아니다.
    #     Check 선언이 규격 문구를 그대로 인용해서 그냥 두면 늘 검사가 이긴다
    pool = [r for r in _candidates(spec, mapping, texts)
            if not r.startswith(NOT_IMPL)]
    best = _best_in(pool, words, texts)
    # ③ 없으면 전부 뒤진다.  ★ MAPPING 은 대표 디렉터리만 적는다 —
    #   「사이트별 구매비용」은 40-report 인데 report/finance.py 에 있다
    if best[0] < MIN_TOKEN_HIT:          # 챕터 안에서 약하면 전부 뒤진다
        whole = _best_in([r for r in texts if not r.startswith(NOT_IMPL)],
                         words, texts)
        if whole[0] > best[0]:
            best = whole
    # ★ 짧은 요구는 낱말이 둘뿐이다 — 문턱을 그대로 걸면 「Python 3.11 이상」이
    #   미구현이 된다.  있는 것을 없다고 하는 것이라 더 나쁘다 (실측 08-19)
    need = min(MIN_TOKEN_HIT, len(words))
    if best[0] < need:
        return ""
    rel, lineno = best[1], best[2]
    if rel.endswith(".html"):
        return rel
    fn = enclosing(by_line, rel, lineno)
    return f"{rel}::{fn}" if fn else f"{rel}:{lineno}"


def _checks_index() -> dict:
    """docs/CHECKS.md — 코드 → (소스 자리, 코드에 있는가)."""
    out: dict = {}
    path = os.path.join(ROOT, "docs", "CHECKS.md")
    if not os.path.isfile(path):
        return out
    for line in open(path, encoding="utf-8"):
        got = re.match(r"^\| `([VS][\w.-]+)` \| (.*?) \| (.*?) \| (.*?) \|",
                       line)
        if not got:
            continue
        where = got.group(4).strip(" `")
        out[got.group(1)] = {
            "what": got.group(2),
            "src": "" if "없다" in where else where,
            "in_code": "없다" not in where,
        }
    return out


def _check_titles() -> dict:
    """코드 → (무엇, 규격 챕터들, 코드에 있는가).  ★ CHECKS.md 가 정본."""
    out: dict = {}
    path = os.path.join(ROOT, "docs", "CHECKS.md")
    if not os.path.isfile(path):
        return out
    for line in open(path, encoding="utf-8"):
        got = re.match(r"^\| `([VS][\w.-]+)` \| (.*?) \| (.*?) \| (.*?) \|"
                       r" (.*?) \| (.*?) \| (.*?) \|", line)
        if not got:
            continue
        # CHECKS.md 의 마지막 칸이 규격 자리다 — 「코드 · 무엇 · 등급 ·
        # 소스 · 마지막 통과 · 마지막 실패 · 규격」 일곱 칸이다
        chapters = set(re.findall(r"chapters/([\w-]+)",
                                  got.group(CHECKS_SPEC_COL)))
        where = got.group(4).strip(" `")
        out[got.group(1)] = {
            "what": got.group(2).strip(),
            "src": "" if "없다" in where else where,
            "chapters": chapters,
            "in_code": "없다" not in got.group(4),
        }
    return out


def find_check(what: str, spec: str, titles: dict) -> tuple:
    """이 요구를 지키는 검사 번호.  돌려줌 (코드, 코드에 있는가).

    ★ 검사 이름과 요구 문구를 견준다.  같은 말로 쓰여 있다 —
      규격이 「검산 V11-120」 처럼 짝을 지어 두기 때문이다
    ★ 같은 챕터를 근거로 든 검사에 가산점을 준다
    """
    words = set(tokens(what))
    if not words:
        return "", False
    best = (0, "")
    for code, one in titles.items():
        title = one["what"]
        if not title or title == "—":
            continue
        share = len(words & set(tokens(title)))
        if not share:
            continue
        score = share * 2 + (1 if spec in one["chapters"] else 0)
        if score > best[0]:
            best = (score, code)
    if best[0] < 4:
        return "", False
    return best[1], titles[best[1]]["in_code"]


# 소스로 삼지 않는 곳.  ★ 검사는 「지키는가」이지 「하는 곳」이 아니다
NOT_IMPL = ("validate/", "tools/check_", "tools/trace_")

# ── 규격 본문에서 짝을 읽는다 ────────────────────────────────────────
# ★★ 「검산 V11-120」은 규격이 이미 적어 둔 짝이다.
#   낱말이 겹치는 검사를 고르면 V3-56 자리에 V3-57 이 들어간다 (실측 08-19 —
#   맞음 31 · 틀림 22 였다).  추측하지 말고 규격이 적은 것을 읽는다
def spec_pairs() -> list:
    """[(규격 파일, 줄, 그 자리의 검사 코드들, 그 위 문맥)].

    ★ 「검산」 줄 위쪽이 그 검사가 지키는 요구다
    """
    import glob as _g

    out = []
    for path in sorted(_g.glob(os.path.join(ROOT, "docs", "chapters",
                                            "**", "*.md"), recursive=True)):
        rel = os.path.relpath(path, os.path.join(ROOT, "docs"))
        lines = open(path, encoding="utf-8").read().splitlines()
        for i, line in enumerate(lines):
            if not re.match(r"\s*(검산|검증)\s", line):
                continue
            codes = re.findall(r"\b([VS]\d+[\w.-]*)\b", line)
            # ★ 한 줄에 다 안 들어가면 다음 줄로 이어진다
            for nxt in lines[i + 1:i + 4]:
                if re.match(r"\s{4,}[VS]\d", nxt):
                    codes += re.findall(r"\b([VS]\d+[\w.-]*)\b", nxt)
                else:
                    break
            if not codes:
                continue
            lo = max(0, i - CTX_LINES)
            out.append((rel, i + 1, codes, "\n".join(lines[lo:i])))
    return out


def find_check_by_spec(what: str, spec: str, pairs: list) -> str:
    """규격 본문의 「검산」 짝에서 고른다.

    ★ 그 요구 문구가 검산 줄 바로 위 문맥에 있는가를 본다
    """
    words = [w for w in tokens(what) if len(w) >= 2]
    if not words:
        return ""
    best = (0, "")
    for rel, _at, codes, ctx in pairs:
        share = sum(1 for w in words if w in ctx)
        if not share:
            continue
        score = share * 2 + (3 if spec and spec in rel else 0)
        if score > best[0]:
            best = (score, " · ".join(dict.fromkeys(codes)))
    return best[1] if best[0] >= MIN_PAIR_SCORE else ""


def find_check_merged(what: str, spec: str, pairs: list, titles: dict) -> str:
    """규격의 짝 + 검사 이름, 둘을 더해 고른다.

    ★ 하나만 쓰면 이웃 번호가 들어간다 (V3-56 자리에 V3-57).
      둘이 같은 것을 가리킬 때 믿는다
    """
    words = [w for w in tokens(what) if len(w) >= 2]
    if not words:
        return ""
    score: dict = {}
    for rel, _at, codes, ctx in pairs:
        share = sum(1 for w in words if w in ctx)
        if not share:
            continue
        pt = share * 2 + (3 if spec and spec in rel else 0)
        if pt < MIN_PAIR_SCORE:
            continue
        for c in codes:
            score[c] = score.get(c, 0) + pt
    ws = set(words)
    for code, one in titles.items():
        title = one.get("what") or ""
        if not title or title == "—":
            continue
        share = len(ws & set(tokens(title)))
        if share >= 2:
            score[code] = score.get(code, 0) + share * 2 + (
                1 if spec in one.get("chapters", ()) else 0)
    if not score:
        return ""
    top = max(score.values())
    if top < MIN_CHECK_SCORE:
        return ""
    best = sorted(c for c, v in score.items() if v == top)
    return " · ".join(best[:2])


# 화면이 필요 없는 챕터.  ★ 계층 · 이름 · 제약 · 검사 설계는 화면이 없다
NO_UI_SPECS = frozenset({
    "00-standard", "01-arch", "11-store", "12-dict", "13-pipeline",
    "20-verify", "31-registry", "50-multisite",
})
# 화면임을 알리는 말.  ★ 요구 문구에 이것이 있으면 화면이 있어야 한다
# ★ 「낸다」 「표시」 「링크」는 뺐다 — 어디에나 있어 전부 「화면 없음」이 된다.
#   실측 08-19 — 파일 쓰기 규칙까지 「화면 없음」으로 나왔다
UI_WORDS = ("화면", "목록", "추천 화면", "상세", "비교 화면", "관심 목록",
            "딜러", "시세", "카드", "단추", "배지", "팝업", "메뉴", "폼",
            "그린다", "보여 준다", "눌러", "누르면", "쪽 나눔", "툴팁")


def _routes() -> dict:
    """경로 → 템플릿.  ★ web/routes.py 가 정본이다."""
    out: dict = {}
    path = os.path.join(ROOT, "web", "routes.py")
    if not os.path.isfile(path):
        return out
    for m in re.finditer(r'Route\("([^"]+)",\s*\([^)]*\),\s*"(\w+)"', 
                         open(path, encoding="utf-8").read()):
        out[m.group(2)] = m.group(1)
    return out


def find_ui(what: str, spec: str, src: str, routes: dict) -> str:
    """어느 화면 · 어느 자리.

    ★ 「해당 없음」과 「화면 없음」은 다르다 —
      앞은 화면이 필요 없는 규칙이고, 뒤는 있어야 하는데 없는 것이다 (S27)
    """
    # 소스가 화면 쪽이면 그 화면이다
    if src.startswith("web/templates/"):
        name = os.path.basename(src).removesuffix(".html")
        for view, path in routes.items():
            if view.replace("view_", "").replace("_", "-") == name or \
                    path.strip("/").replace("/", "_") == name:
                return f"`{path}`"
        return f"`{name}` 템플릿"
    if src.startswith(("web/views.py", "report/screens/")):
        for view, path in routes.items():
            fn = src.split("::")[-1]
            if fn and (fn in view or view.endswith(fn)):
                return f"`{path}`"
    got = re.findall(r"`(/[\w{}/-]+)`", what)
    if got:
        return " · ".join(dict.fromkeys(got))
    if any(w in what for w in UI_WORDS):
        return ""            # 화면이 있어야 한다 — 부르는 쪽이 「화면 없음」
    if spec in NO_UI_SPECS:
        return NO_UI_NA
    return ""


# 좁은 표(4칸)의 머리말.  ★ 이것도 요구다 — 칸이 없을 뿐이다
NARROW_HEAD = "| R | 요구사항 | 출처 | 상태 |"
WIDE_HEAD = ("| R | 요구사항 | 출처 · 근거 | 규격 | 소스 | 화면 | 검사 "
             "| 테스트 | 결함 | 상태 |")
WIDE_SEP = "|---|---|---|---|---|---|---|---|---|:--:|"
# 질문 표.  ★ 요구가 아니라 마스터께 여쭐 것이다 — 소스가 없다.
#   ★ 머리글로 가린다.  표 머리말은 「왜」 · 「왜 여쭙나」 로 갈린다 —
#     그것으로 가렸더니 하나를 놓쳐 질문 넷이 요구로 넓혀졌다 (실측 08-19)
QUESTION_HEAD_RE = re.compile(r"^#+\s*★?\s*마스터께 여쭐 것")


def widen(cells: list, spec: str) -> list:
    """좁은 표를 온전한 10칸으로 넓힌다.

    ★ 4칸 표도 요구다.  칸이 없다는 이유로 「모른다」로 두지 않는다
    """
    if len(cells) >= N_COLS:
        return cells[:N_COLS]
    if len(cells) == NARROW_COLS:
        r, what, why, st = cells
        return [r, what, why, f"`{spec}`", "", "", "", "", "", st]
    out = list(cells) + [""] * (N_COLS - len(cells))
    return out[:N_COLS]


def _only_in_spec(chk: str, titles: dict) -> bool:
    """그 칸의 검사가 전부 「규격에만 있고 코드에 없다」인가.

    ★ 판정을 한 곳에 둔다.  두 곳에서 각자 기본값을 정하면
      같은 표를 두 번 돌릴 때 답이 갈린다 (실측 08-19 — 표시가 두 번 붙었다)
    ★ CHECKS.md 에 아예 없는 번호는 「모른다」다.  단정하지 않는다
    """
    codes = re.findall(r"[VS]\d+[\w.-]*", chk or "")
    known = [c for c in codes if c in titles]
    if not codes or len(known) != len(codes):
        return False
    return all(not titles[c].get("in_code") for c in known)


def _source_of_check(chk: str, titles: dict, by_line: dict) -> str:
    """검사가 소스인 요구도 있다.

    ★ 「금지 여러 작업을 한 커밋에」 는 구현 파일이 없다.
      그것을 막는 검사(S25)가 그 요구를 지키는 자리다
    """
    for code in re.findall(r"[VS]\d+[\w.-]*", chk or ""):
        one = titles.get(code)
        if not one or not one.get("in_code"):
            continue
        where = one.get("src") or ""
        got = re.match(r"([\w./-]+):(\d+)", where.strip(" `"))
        if not got:
            continue
        rel, at = got.group(1), int(got.group(2))
        fn = enclosing(by_line, rel, at)
        return f"{rel}::{fn}" if fn else f"{rel}:{at}"
    return ""


def restate(cells: list) -> str:
    """S38 — 칸이 채워진 정도로 상태를 다시 매긴다.

    소스 「미구현」   →  ✗
    화면 「화면 없음」 →  ◐
    검사 「검사 없음」 →  ◐
    넷이 다 차면     →  ○  (테스트는 비어도 된다)
    ★ 「!」(결함) · 「?」(확인 필요)는 사람이 적은 것이라 손대지 않는다
    """
    now = cells[I_ST]
    # ★ 사람이 적은 것은 손대지 않는다 (규칙 2).
    #   ○ · ◐ · ✗ 만 다시 매긴다 — 「◐ 오늘」 · 「D-500b」 처럼 가이드가
    #   덧붙인 말을 덮으면 그 판단이 사라진다 (실측 08-19 · 되돌렸다)
    if now.strip("* ") not in ("○", "◐", "✗", ""):
        return now
    if NO_SRC in cells[I_SRC]:
        return "✗"
    if NO_UI in cells[I_UI] or NO_CHK in cells[I_CHK]:
        return "◐"
    if cells[I_SRC] and cells[I_UI] and cells[I_CHK]:
        return "○"
    return now


def fill_file(path: str, spec: str, ctxs: dict, write: bool) -> dict:
    """파일 하나를 채운다.  돌려줌 통계."""
    lines = open(path, encoding="utf-8").read().splitlines()
    out, stat = [], {"행": 0, "소스": 0, "화면": 0, "검사": 0, "넓힘": 0}
    in_question = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            in_question = bool(QUESTION_HEAD_RE.match(stripped))
            out.append(line)
            continue
        if stripped.startswith("| R ") and not in_question:
            out.append(WIDE_HEAD)
            continue
        if (stripped.startswith("|---") and out and out[-1] == WIDE_HEAD
                and not in_question):
            out.append(WIDE_SEP)
            continue
        if not stripped.startswith("| R-") or in_question:
            out.append(line)
            continue

        cells = [c.strip() for c in stripped.strip("|").split("|")]
        was = len(cells)
        cells = widen(cells, spec)
        if was < N_COLS:
            stat["넓힘"] += 1
        stat["행"] += 1

        what = cells[I_WHAT]
        row_spec = cells[I_SPEC].strip(" `") or spec
        # ★ 이미 적힌 것은 그대로 둔다 — 가이드가 적은 판단이다 (규칙 2)
        # ★ 검사를 먼저 찾는다.  「금지」 · 「작업 규칙」은 구현 파일이 없고
        #   그것을 막는 검사가 곧 그 요구를 지키는 자리다 (실측 08-19 —
        #   00-standard 38건이 「미구현」으로 나왔는데 git·커밋 규칙이었다)
        if not cells[I_CHK]:
            got = find_check_merged(what, row_spec, ctxs["pairs"],
                                    ctxs["titles"])
            if got:
                cells[I_CHK] = (f"{got} — {NO_CHK_SPEC}"
                                if _only_in_spec(got, ctxs["titles"]) else got)
            else:
                cells[I_CHK] = NO_CHK
            stat["검사"] += 1
        elif NO_CHK not in cells[I_CHK]:
            # ★ 이미 적힌 검사가 규격에만 있고 코드에 없을 수 있다 (S16 이 42건).
            #   값을 지우지 않고 표시만 단다 — 그것이 만들 목록이다 (지시 §3)
            if _only_in_spec(cells[I_CHK], ctxs["titles"]):
                cells[I_CHK] = f"{cells[I_CHK]} — {NO_CHK_SPEC}"
        if not cells[I_SRC]:
            got = find_source(what, row_spec, ctxs["mapping"], ctxs["texts"],
                              ctxs["by_line"], ctxs["by_name"])
            if not got:
                # ★ 낱말로 못 찾으면 규격의 STEP 을 닻으로 삼는다.
                #   코드 주석이 「STEP 91a」 처럼 근거를 적어 둔다 (1,242곳)
                got = source_by_step(
                    anchor_step(what, row_spec, ctxs["slines"]),
                    ctxs["texts"], ctxs["by_line"])
            if not got:
                got = _source_of_check(cells[I_CHK], ctxs["titles"],
                                       ctxs["by_line"])
            cells[I_SRC] = f"`{got}`" if got else NO_SRC
            stat["소스"] += 1
        if not cells[I_UI]:
            src = cells[I_SRC].strip(" `")
            got = find_ui(what, row_spec, src, ctxs["routes"])
            cells[I_UI] = got or NO_UI
            stat["화면"] += 1
        cells[I_ST] = restate(cells)
        out.append("| " + " | ".join(cells) + " |")

    if write:
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(out) + "\n")
    return stat


def _spec_of(name: str) -> str:
    """파일 이름 → 규격 챕터.  ★ 손으로 표를 두지 않는다."""
    return name.removesuffix(".md")


def survey() -> dict:
    """지금 채움 상태.  ★ 전·후를 같은 자로 잰다."""
    got = {"행": 0, "소스": 0, "화면": 0, "검사": 0, "테스트": 0, "상태": {}}
    for name in sorted(os.listdir(TRACE)):
        if not name.endswith(".md") or name == "INDEX.md":
            continue
        for _i, cells in _tables(os.path.join(TRACE, name)):
            got["행"] += 1
            if len(cells) < N_COLS:
                st = cells[-1] if len(cells) == NARROW_COLS else ""
            else:
                st = cells[I_ST]
                for i, k in ((I_SRC, "소스"), (I_UI, "화면"),
                             (I_CHK, "검사"), (I_TEST, "테스트")):
                    if cells[i]:
                        got[k] += 1
            key = st.strip("* ") or "—"
            got["상태"][key] = got["상태"].get(key, 0) + 1
    return got


def lists() -> dict:
    """§6 — 마스터가 볼 셋."""
    out = {"미구현": [], "화면 없음": [], "검사 없음": []}
    for name in sorted(os.listdir(TRACE)):
        if not name.endswith(".md") or name == "INDEX.md":
            continue
        for _i, cells in _tables(os.path.join(TRACE, name)):
            if len(cells) < N_COLS:
                continue
            row = (cells[I_R], cells[I_WHAT][:60], _spec_of(name))
            if NO_SRC in cells[I_SRC]:
                out["미구현"].append(row)
            if NO_UI in cells[I_UI]:
                out["화면 없음"].append(row)
            if NO_CHK in cells[I_CHK]:
                out["검사 없음"].append(row)
    return out


def write_index(before: dict, after: dict) -> str:
    """docs/trace/INDEX.md — ★ 기계로 만든다 (지시 §7)."""
    rows = []
    for name in sorted(os.listdir(TRACE)):
        if not name.endswith(".md") or name == "INDEX.md":
            continue
        n = {"행": 0, "소스": 0, "화면": 0, "검사": 0}
        st: dict = {}
        for _i, cells in _tables(os.path.join(TRACE, name)):
            n["행"] += 1
            if len(cells) >= N_COLS:
                for i, k in ((I_SRC, "소스"), (I_UI, "화면"), (I_CHK, "검사")):
                    if cells[i]:
                        n[k] += 1
                st[cells[I_ST].strip("* ")] = st.get(
                    cells[I_ST].strip("* "), 0) + 1
        rows.append((name, n, st))
    now = after
    body = [
        "# 추적표 색인",
        "",
        "**`python3.11 tools/trace_fill.py --write` 가 만든다. "
        "손으로 고치지 않는다.**",
        "",
        f"요구 **{now['행']}건**",
        "",
        "## 칸별 채움",
        "",
        "★ 지금 상태다.  「전 → 후」는 그때그때 달라지므로 적지 않는다 —",
        "  옮긴 기록은 `outputs/` 가 갖는다",
        "",
        "| 칸 | 찬 것 | 빈 것 | 채움률 |",
        "|---|--:|--:|--:|",
    ]
    for k in ("소스", "화면", "검사", "테스트"):
        pct = (now[k] / now["행"] * 100) if now["행"] else 0
        body.append(f"| {k} | {now[k]} | {now['행'] - now[k]} | {pct:.0f}% |")
    del before
    body += ["", "## 상태", "", "| 상태 | 몇 개 |", "|---|--:|"]
    for k in sorted(now["상태"]):
        body.append(f"| {k} | {now['상태'][k]} |")
    body += ["", "## 장별", "",
             "| 표 | 요구 | 소스 | 화면 | 검사 | 상태 |",
             "|---|--:|--:|--:|--:|---|"]
    for name, n, st in rows:
        shown = " · ".join(f"{k} {v}" for k, v in sorted(st.items()) if k)
        body.append(f"| [{name}]({name}) | {n['행']} | {n['소스']} "
                    f"| {n['화면']} | {n['검사']} | {shown} |")
    body += ["", "```",
             "★ 「미구현」 · 「화면 없음」 · 「검사 없음」은 빈 칸이 아니다.",
             "  빈 칸은 「모른다」이고 그것이 가장 나쁘다",
             "",
             "★ 소스 · 화면 · 검사 칸은 기계가 찾은 것이다 — 추정이다.",
             "  ① 요구 문구의 낱말이 겹치는 코드",
             "  ② 못 찾으면 규격의 STEP 번호를 인용한 코드",
             "  ③ 그래도 없으면 「미구현」",
             "  ★ 단정인 것은 「미구현」 · 「화면 없음」 · 「검사 없음」 뿐이다 —",
             "    그것은 「기계가 못 찾았다」는 사실이고, 그것이 만들 목록이다",
             "★ 가이드가 이미 적어 둔 칸은 그대로 두었다 (규칙 2)",
             "```", ""]
    text = "\n".join(body)
    with open(os.path.join(TRACE, "INDEX.md"), "w", encoding="utf-8") as f:
        f.write(text)
    return text


def main() -> int:
    write = "--write" in sys.argv
    before = survey()
    ctxs = {}
    ctxs["by_line"], ctxs["by_name"] = build_symbols()
    ctxs["texts"] = build_texts()
    ctxs["mapping"] = _mapping()
    ctxs["titles"] = _check_titles()
    ctxs["pairs"] = spec_pairs()
    ctxs["routes"] = _routes()
    ctxs["slines"] = spec_lines()
    total = {"행": 0, "소스": 0, "화면": 0, "검사": 0, "넓힘": 0}
    for name in sorted(os.listdir(TRACE)):
        if not name.endswith(".md") or name == "INDEX.md":
            continue
        got = fill_file(os.path.join(TRACE, name), _spec_of(name), ctxs, write)
        for k in total:
            total[k] += got[k]
    after = survey()
    print(f"{'쓰기' if write else '미리보기'} — 채운 칸 "
          f"소스 {total['소스']} · 화면 {total['화면']} · 검사 {total['검사']}"
          f" · 넓힌 행 {total['넓힘']}\n")
    print("| 칸 | 전 | 후 |")
    print("|---|--:|--:|")
    for k in ("소스", "화면", "검사", "테스트"):
        print(f"| {k} | {before[k]} | {after[k]} |")
    print("\n| 상태 | 전 | 후 |")
    print("|---|--:|--:|")
    for k in sorted(set(before["상태"]) | set(after["상태"])):
        print(f"| {k} | {before['상태'].get(k, 0)} | {after['상태'].get(k, 0)} |")
    if write:
        write_index(before, after)
        got = lists()
        for k, v in got.items():
            print(f"\n★ {k} {len(v)}건")
            for r in v[:SAMPLE]:
                print(f"  {r[0]} {r[1]}")
    return 0



# ── 규격의 STEP 을 닻으로 삼는다 ─────────────────────────────────────
# ★★ 코드 주석이 「STEP 91a」 처럼 규격 번호를 적어 둔다 (1,242곳).
#   요구 문구를 규격에서 찾아 그 절의 STEP 을 알면, 그 번호를 인용한
#   코드가 곧 그 요구를 하는 곳이다.  낱말만으로 고르는 것보다 훨씬 낫다
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


def source_by_step(step: str, texts: dict, by_line: dict) -> str:
    """그 STEP 을 인용한 코드 자리.  ★ 주석이 근거를 적어 둔 덕이다."""
    if not step:
        return ""
    needle = step.replace("STEP ", "STEP ")
    best = (0, "", 0)
    for rel, lines in texts.items():
        if rel.startswith(NOT_IMPL):
            continue
        hits = [i for i, ln in enumerate(lines, 1) if needle in ln]
        if not hits:
            continue
        # ★ 여러 곳이 같은 STEP 을 인용한다.  가장 많이 인용한 파일이 본체다
        if len(hits) > best[0]:
            best = (len(hits), rel, hits[0])
    if not best[1]:
        return ""
    rel = best[1]
    lines = texts[rel]
    # ★ 첫 인용은 파일 첫머리 주석인 때가 많다.  함수 안에 있는 인용을 고른다 —
    #   「export.py:4」는 「그 파일 어딘가」라는 말밖에 안 된다 (실측 08-19)
    for i, ln in enumerate(lines, 1):
        if needle not in ln:
            continue
        fn = enclosing(by_line, rel, i)
        if fn:
            return f"{rel}::{fn}"
    return rel


if __name__ == "__main__":
    sys.exit(main())
