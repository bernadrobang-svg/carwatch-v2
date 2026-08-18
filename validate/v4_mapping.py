# -*- coding: utf-8 -*-
"""V4 매핑 검증 — 이름이 아니라 값으로 검증한다.

지시서   6장 STEP 61 · 62 (보정)
근거     v1 은 dealer_shop 에 OfficeCityState 가 들어가 일치율 100% 였다.
         이름으로는 절대 안 보인다.  값 대조로만 잡힌다
금지     80% 를 전 필드에 일괄 적용하는 것.
         돈과 등급을 결정하는 필드가 80% 만 맞으면 20% 는 틀린 점수를 받는다
"""
from __future__ import annotations

import json

from parse.encar.mapping import clean_vin
from store.pii import plate_hash as _plate_hash
from validate.base import (
    Check,
    FATAL,
    KIND_CODE,
    KIND_EXTERNAL,
    WARN,
    _cfg,
    not_applicable,
    result,
)

C = {
    "V4-01": Check("V4", "V4-01", "매핑 일치율 (A 100% · B 99% · C 80%)", FATAL, "run",
                     "파서를 고치고 S6 을 재실행한 뒤 V4 를 다시 돌린다 (STEP 62)",
                    KIND_CODE),
    "V4-03": Check("V4", "V4-03", "오매핑 탐지 — 다른 경로와 더 높은 일치율", FATAL, "run",
                     "매핑표와 파서를 함께 고친다. 이름이 아니라 값으로 확인한다",
                    KIND_CODE),
    "V4-06": Check("V4", "V4-06", "RAW 경로가 등록부에 있는가", FATAL, "run",
                     "config/field_usage.suggested.json 을 확인·수정해 config/field_usage.json 으로 옮긴 뒤 재실행한다",
                    KIND_EXTERNAL),
    "V4-06b": Check("V4", "V4-06b", "등록부에 있는데 RAW 에 없는 유령 경로", WARN, "run",
                     "3회 연속 미관측이면 not_provided 로 전환된다. 유령 경로면 등록을 취소한다",
                    KIND_EXTERNAL),
    "V4-07": Check("V4", "V4-07", "in_use 인데 core_column NULL", FATAL, "run",
                     "config/field_usage.json 에서 그 경로의 core_column 을 채운다",
                    KIND_CODE),
    "V4-08": Check("V4", "V4-08", "blocked 인데 unblock_condition NULL", FATAL, "run",
                     "config/field_usage.json 에서 그 경로의 unblock_condition 을 채운다",
                    KIND_CODE),
    "V4-09": Check("V4", "V4-09", "deferred 인데 use_when NULL", FATAL, "run",
                     "config/field_usage.json 에서 그 경로의 use_when 을 채운다",
                    KIND_CODE),
    "V4-10": Check("V4", "V4-10", "display_only 인데 core_column NULL", FATAL, "run",
                     "config/field_usage.json 에서 그 경로의 core_column 을 채운다",
                    KIND_CODE),
    "V4-11": Check("V4", "V4-11", "unclassified 존재", FATAL, "run",
                     "config/field_usage.suggested.json 의 후보를 확인·수정해 config/field_usage.json 으로 옮긴 뒤 재실행한다",
                    KIND_CODE),
    "V4-11b": Check("V4", "V4-11b", "판정에 안 쓰는 미분류 경로", WARN, "run",
                    "다음 회차에 모아서 분류한다. 파이프라인은 막지 않는다",
                    KIND_EXTERNAL),
    "V4-26": Check("V4", "V4-26", "미분류가 원인별로 갈려 있음",
                   FATAL, "run",
                   "「349건 미분류」라고만 내면 아무도 안 본다. "
                   "② 이름만 다른 것 · ③ 늘 비어 있는 것 · ④ 정말 새로운 것으로 "
                   "가르고, 엔드포인트별·관측 건수와 함께 낸다 (개정 341)",
                   KIND_CODE),
    "V4-27": Check("V4", "V4-27", "판정을 막는 것만 막음",
                   FATAL, "run",
                   "미분류가 전부 판정을 막으면 새 필드 하나에 판정이 영영 "
                   "멈춘다.  판정에 쓰는 경로만 막는다 — 나머지는 등록만 하고 "
                   "진행한다 (개정 341)",
                   KIND_CODE),
    "V4-30": Check("V4", "V4-30", "판정을 막는 것의 목록 파일이 있음",
                   FATAL, "run",
                   "마스터 지시 — 「실제값으로 너랑 나랑 판단해야지」. "
                   "★ 저장소 어디에도 32건의 경로가 없었다 — DB 와 화면에만 "
                   "있었다.  목록이 없으니 아무것도 못 정한다 (개정 390)",
                   KIND_CODE),
    "V4-28": Check("V4", "V4-28", "미분류 항목에 값 분포와 선택지가 있음",
                   FATAL, "run",
                   "마스터 지적 — 「이걸 보고 내가 무엇을 하라는 말이지?  "
                   "뭔지도 모르겠는데」.  경로만 내고 「사람이 봐야 합니다」라 "
                   "하면 아무도 못 정하고 V4-11 이 영영 열려 있다 (개정 367)",
                   KIND_CODE),
    "V4-29": Check("V4", "V4-29", "기본 화면이 판정 막는 것만 냄",
                   FATAL, "run",
                   "120건을 한꺼번에 보라 하면 아무도 안 본다. "
                   "판정을 막는 것부터 낸다 (개정 367)",
                   KIND_CODE),
    "V4-12": Check("V4", "V4-12", "facet 필수 축 집합 존재", FATAL, "run",
                     "facet 을 재수집한다 (S2). 축을 열거해 요청하지 않는다",
                    KIND_CODE),
    "V4-13": Check("V4", "V4-13", "매직 넘버 없음 (tools/check_src.py S7)", FATAL, "run",
                     "python3 tools/check_src.py 로 위치를 확인하고 임계값을 config 로 옮긴다",
                    KIND_CODE),    "V4-24": Check("V4", "V4-24",
                   "축 함수가 target_config 에서 매물 값을 읽지 않음",
                   FATAL, "run",
                   "매물 값은 ListingSnapshot 으로 간다. dict 에 숨기면 "
                   "무엇이 판정에 쓰이는지 시그니처로 알 수 없다 (F-1)",
                   KIND_CODE),
    "V4-25": Check("V4", "V4-25", "판정에 쓰는 축의 사전이 비어 있지 않음",
                   FATAL, "run",
                   "S3 을 돌려 사전을 채운다. 「미검토 0건」과 "
                   "「사전이 없다」는 다르다 (STEP 45)",
                   KIND_CODE),
    "V4-02": Check("V4", "V4-02", "미매핑 경로 목록", WARN, "run",
                   "등록부에서 분류한다. in_use 면 매핑표에 넣는다",
                   KIND_EXTERNAL),
    "V4-04": Check("V4", "V4-04", "매핑표에 없는 CORE 컬럼", WARN, "run",
                   "그 컬럼이 어디서 오는지 매핑표에 적는다", KIND_EXTERNAL),
    "V4-05": Check("V4", "V4-05", "원문 경로 수 변동", WARN, "run",
                   "사이트가 필드를 늘리거나 줄였다. 등록부 후보를 본다",
                   KIND_EXTERNAL),
    "V4-19": Check("V4", "V4-19", "성격(kind)이 없는 Check 가 없음",
                   FATAL, "run",
                   "4분류 중 하나를 정한다 (STEP 54)", KIND_CODE),
    "V4-22": Check("V4", "V4-22", "역방향 · 순환 import 없음", FATAL, "run",
                   "STEP 15a 의존 방향을 보고, 공통은 아래 층으로 내린다",
                   KIND_CODE),
    "V4-23": Check("V4", "V4-23", "모듈 최상위에 I/O · 부작용 없음",
                   FATAL, "run",
                   "import 만으로 아무 일도 안 일어나야 한다. "
                   "실행은 run.py · tools/ 에서만",
                   KIND_CODE),
    "V4-21": Check("V4", "V4-21", "같은 이름의 공개 함수가 두 모듈에 없음",
                   WARN, "run",
                   "역할이 다르면 이름을 바꾼다. 잘못 import 하면 조용히 틀린다",
                   KIND_EXTERNAL),
    "V4-20": Check("V4", "V4-20", "dict_option_code 에 문장(공백·한글)이 없음",
                   FATAL, "run",
                   "options.etc 는 자유 텍스트다. 코드 사전에 넣지 않는다",
                   KIND_CODE),
}

# 등급별 일치율 기준 (STEP 61).  일괄 적용하지 않는다
# ★ plate 는 원본이 CORE 에 없다.  해시로 대조한다 (STEP 35)
GRADE_A_FIELDS = ("source_id", "vin", "plate_hash", "price_current_won",
                  "price_origin_won", "displacement_cc")
# 엔드포인트마다 이만큼씩 본다.  전역 상한이면 종류가 누락된다
SAMPLE_PER_ENDPOINT = 50

RATIOS = _cfg("mapping_ratio")
RATIO_A = RATIOS["A"]


def _paths(node, trail="", out=None):
    """원문의 경로를 전수로 뽑는다.  배열 요소는 [] 로 한 경로로 센다."""
    out = out if out is not None else set()
    if isinstance(node, dict):
        for k, v in node.items():
            p = f"{trail}.{k}" if trail else k
            out.add(p)
            _paths(v, p, out)
    elif isinstance(node, list) and node:
        _paths(node[0], f"{trail}[]", out)
    return out


# ── STEP 15a 의존 방향 ──────────────────────────────────────────────
# 층이 부를 수 있는 것.  ★ analyze 만 store 도 못 부른다 (판정은 순수 함수다)
LAYER_ALLOW: dict[str, frozenset] = {
    # ★ 둘은 같은 「계층 횡단」 층이다.  require_role 이 PolicyError 를 던진다
    "contracts": frozenset({"errors"}),
    "errors": frozenset(),
    "store": frozenset({"contracts", "errors"}),
    "parse": frozenset({"contracts", "errors", "store"}),
    "analyze": frozenset({"contracts", "errors"}),
    "score": frozenset({"contracts", "errors", "analyze"}),
    "report": frozenset({"contracts", "errors", "store", "analyze", "score",
                         "parse"}),
    "web": frozenset({"contracts", "errors", "store", "score", "report"}),
    "adapters": frozenset({"contracts", "errors"}),
    "collect": frozenset({"contracts", "errors", "store", "parse", "adapters",
                          "analyze", "score", "validate", "tools"}),
    "validate": None,          # 전부 (읽기만)
    "tools": None,             # 독립 실행
}

# 최상위에서 해도 되는 것.  ★ 상수·타입 정의는 부작용이 아니다
# import 만으로 파일·디렉터리를 여는 호출.  ★ 이것이 있으면 cwd 에 매인다
IO_CALLS = frozenset({"open", "load", "listdir", "glob", "iglob", "walk",
                      "connect", "_cfg", "_admin_cfg", "read_text"})
SAFE_TOP_CALLS = frozenset({
    "frozenset", "set", "dict", "list", "tuple", "range", "len", "sorted",
    "compile", "Check", "dataclass", "namedtuple", "Enum", "_cfg",
    "getLogger", "TypeVar", "field", "Path", "abspath", "dirname", "join",
    "insert", "append", "add", "update", "format", "strip", "split", "sub",
    "int", "float", "str", "bool", "_sample_chars", "_our_columns",
    "parser_paths", "_admin_cfg",
})


def _layer_of(rel: str) -> str:
    head = rel.split("/")[0]
    return head[:-3] if head.endswith(".py") else head


def _unclassified_split(conn, rid, blocking: list, pending: list) -> list:
    """V4-26 · V4-27 — 미분류를 원인별로 가르고, 막는 것만 막는가 (개정 341).

    ★ 가이드 지적 — 「349개를 사람이 하나씩 보라는 뜻입니다.  아무도 안 봅니다」
    ★ 「몇 건」이 아니라 「무엇이 왜」를 낸다
    """
    from store.core import classify_unclassified as classify

    total = len(blocking) + len(pending)
    if not total:
        return [not_applicable(C["V4-26"], rid, "미분류가 없다"),
                not_applicable(C["V4-27"], rid, "미분류가 없다")]
    rows = classify(conn)
    kinds: dict = {}
    for one in rows:
        kinds[one["kind"]] = kinds.get(one["kind"], 0) + 1
    need = kinds.get("④ 새로운 것", 0)
    bad26 = []
    if len(rows) != total:
        bad26.append(f"가른 것 {len(rows)}건 != 미분류 {total}건")
    if need == len(rows) and rows:
        bad26.append("전부 「새로운 것」이다 — 가르지 못했다")
    # V4-27 — 막는 것이 전체가 아니어야 한다
    bad27 = []
    if blocking and len(blocking) == total:
        bad27.append(f"미분류 {total}건이 전부 판정을 막는다 — "
                     "판정에 쓰는 경로만 막아야 한다")
    return [
        result(C["V4-26"], rid, f"{total}건",
               " · ".join(f"{k} {n}" for k, n in sorted(kinds.items()))
               + f" · 사람 몫 {need}",
               not bad26, bad26[:4]),
        result(C["V4-27"], rid, f"{total}건 중",
               f"막는 것 {len(blocking)}건 · 진행 {len(pending)}건",
               not bad27, bad27[:4]),
    ]


def _layer_checks(rid) -> list:
    """★ import 방향과 부작용을 본다 (STEP 15a)."""
    import ast
    import os

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bad_dep, bad_side = [], []
    edges: dict[str, set] = {}

    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", "ref")]
        for f in files:
            if not f.endswith(".py"):
                continue
            rel = os.path.relpath(os.path.join(base, f), root).replace(
                "\\", "/")
            if rel.startswith("tests/"):
                continue
            layer = _layer_of(rel)
            allow = LAYER_ALLOW.get(layer, None)
            try:
                tree = ast.parse(open(os.path.join(base, f),
                                      encoding="utf-8").read())
            except SyntaxError:
                continue

            for n in ast.walk(tree):
                mod = None
                if isinstance(n, ast.ImportFrom) and n.level == 0:
                    mod = (n.module or "").split(".")[0]
                elif isinstance(n, ast.Import):
                    mod = n.names[0].name.split(".")[0]
                if not mod or mod not in LAYER_ALLOW:
                    continue
                edges.setdefault(layer, set()).add(mod)
                if allow is None or mod == layer:
                    continue
                if mod not in allow:
                    bad_dep.append(f"{rel}: {layer} → {mod}")

            # 모듈 최상위 부작용
            if rel == "run.py" or rel.startswith("tools/"):
                continue
            for n in tree.body:
                # ★ 대입도 본다.  X = _cfg(...) 는 import 만으로 파일을 연다.
                #   Expr 만 보면 실측 45건이 통째로 검사 밖이었다 (A-7)
                if isinstance(n, (ast.Expr, ast.Assign, ast.AnnAssign)):
                    value = getattr(n, "value", None)
                    for call in ast.walk(value) if value is not None else ():
                        if not isinstance(call, ast.Call):
                            continue
                        fn = getattr(call.func, "attr",
                                     getattr(call.func, "id", ""))
                        if fn in SAFE_TOP_CALLS:
                            continue
                        if fn in IO_CALLS:
                            bad_side.append(f"{rel}:{call.lineno} {fn}()")
                        elif isinstance(n, ast.Expr):
                            bad_side.append(f"{rel}:{call.lineno} {fn}()")
                if isinstance(n, ast.If) and any(
                    isinstance(c, ast.Compare)
                    and getattr(c.left, "id", "") == "__name__"
                    for c in ast.walk(n)
                ):
                    bad_side.append(f"{rel}: __main__ 블록")

    # 순환 — 두 층이 서로를 부르는가.
    # ★ validate · tools 는 「전부 읽기」라 순환 대상이 아니다 (STEP 15a 표)
    free = {k for k, v in LAYER_ALLOW.items() if v is None}
    seen_pairs = set()
    for a, deps in edges.items():
        if a in free:
            continue
        for b in deps:
            if b in free or a == b or a not in edges.get(b, set()):
                continue
            pair = " ↔ ".join(sorted((a, b)))
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                bad_dep.append(f"순환 {pair}")

    out = [result(C["V4-22"], rid, 0, len(bad_dep), not bad_dep,
                  sorted(set(bad_dep))[:20])]
    out.append(result(C["V4-23"], rid, 0, len(bad_side), not bad_side,
                      bad_side[:20]))
    return out


# 같은 이름이어도 되는 것 — 계약이 같거나 계층별 구현이다
COLLISION_ALLOW: frozenset[str] = frozenset({
    "run", "main", "check", "db", "setup", "load", "opt", "seed", "base",
})


def _name_collision_check(run_id):
    """★ 이름이 같고 역할이 다르면 잘못 import 해도 안 터진다.

    실측: score.grade.display_points(policy) 와
         report.views.display_points(points, excluded, max) 가 공존했다
    """
    import ast
    import collections
    import os

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    seen: dict = collections.defaultdict(set)
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs
                   if d not in ("__pycache__", ".git", "tests", "tools",
                                "ref")]
        for f in files:
            if not f.endswith(".py"):
                continue
            path = os.path.join(base, f)
            try:
                tree = ast.parse(open(path, encoding="utf-8").read())
            except SyntaxError:
                continue
            rel = os.path.relpath(path, root).replace("\\", "/")
            for n in tree.body:
                if isinstance(n, ast.FunctionDef) and not n.name.startswith("_"):
                    seen[n.name].add(rel)
    bad = [f"{name}: {', '.join(sorted(mods))}"
           for name, mods in sorted(seen.items())
           if len(mods) > 1 and name not in COLLISION_ALLOW]
    return result(C["V4-21"], run_id, 0, len(bad), not bad, bad)


def _key():
    from store.pii import load_key

    return load_key()


def _decide_material_check(conn, rid):
    """V4-28 · V4-29 — 미분류에 판단할 재료가 있는가 (개정 367).

    마스터 지적 — 「이걸 보고 내가 무엇을 하라는 말이지?  뭔지도 모르겠는데」
    ★ 경로만 내고 「사람이 봐야 합니다」라 하면 아무도 못 정한다.
      그러면 V4-11 이 영영 열려 있다
    """
    from contracts import ROLE_ADMIN, Account
    from errors import CarWatchError
    from store.core import has_unclassified
    from web.routes import GET, ROUTES
    from web.views import HANDLERS

    if not has_unclassified(conn):
        return [not_applicable(C["V4-28"], rid, "미분류가 없다"),
                not_applicable(C["V4-29"], rid, "미분류가 없다")]
    route = {r.path: r for r in ROUTES}.get("/admin/registry")
    if route is None:
        bad = ["/admin/registry 가 없다"]
        return [result(C["V4-28"], rid, "있다", "없다", False, bad),
                result(C["V4-29"], rid, "있다", "없다", False, bad)]
    try:
        _st, _h, body = HANDLERS[route.view](
            conn, Account(1, ROLE_ADMIN, "마스터"),
            {"query": {}, "form": {}, "method": GET},
            path_vars={}, csrf="t")
    except (CarWatchError, KeyError, ValueError) as e:
        bad = [f"{type(e).__name__}: {e}"[:70]]
        return [result(C["V4-28"], rid, "있다", "못 그렸다", False, bad),
                result(C["V4-29"], rid, "있다", "못 그렸다", False, bad)]
    html = body.decode("utf-8", "replace")
    bad28 = []
    # ① 값 분포 ③ 형제 ⑤ 막히는 것 ④ 단추
    for mark, why in (("① 실제 값", "값 분포가 없다"),
                      ("③ 옆에 있던 것", "형제 필드가 없다"),
                      ("⑤ 안 정하면", "안 정하면 무엇이 막히는지 없다"),
                      ('name="usage" value="in_use"', "고를 단추가 없다")):
        if mark not in html:
            bad28.append(why)
    # ★ 「사람이 봐야 합니다」만 있고 단추가 없으면 선택지가 아니다
    if "class=\"decide\"" not in html:
        bad28.append("판단 재료 자리(.decide)가 없다")
    a = result(C["V4-28"], rid, "다섯", "있다" if not bad28 else "모자라다",
               not bad28, bad28[:5])

    # V4-29 — 기본 화면이 판정 막는 것만 먼저 내는가
    bad29 = []
    first = html.find("판정을 막습니다")
    later = html.find("지금 안 쓰입니다")
    if first < 0:
        bad29.append("판정을 막는 것을 표시하지 않는다")
    elif 0 <= later < first:
        bad29.append("판정을 안 막는 것이 먼저 나온다")
    return [a, result(C["V4-29"], rid, "막는 것 먼저",
                      "그렇다" if not bad29 else "아니다", not bad29, bad29)]


def _blocking_list_check(conn, rid):
    """V4-30 — 판정을 막는 것의 목록 파일이 있고 줄 수가 맞는가 (개정 390).

    마스터 지시 — 「실제값으로 너랑 나랑 판단해야지」
    ★ 「지금 저장소 어디에도 32건의 경로가 없다.  DB 와 화면에만 있다.
      목록이 없으니 가이드도 마스터도 아무것도 못 정한다」
    ★ 줄 수가 V4-11 이 세는 수와 같아야 한다 — 다르면 딴 것을 센 것이다
    """
    import glob as _g
    import os as _o
    import re as _re

    _ROOT = _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__)))

    from store.core import blocking_rows
    from tools.classify_fields import (
        WHOLE_CONTAINERS, parser_lines, parser_paths,
    )

    want = blocking_rows(conn, parser_paths(), WHOLE_CONTAINERS,
                         parser_lines())
    if not want:
        return not_applicable(C["V4-30"], rid, "판정을 막는 것이 없다")
    found = sorted(_g.glob(_o.path.join(_ROOT, "outputs",
                                        "*_registry32_목록.md")))
    if not found:
        return result(C["V4-30"], rid, f"{len(want)}줄", "파일이 없다", False,
                      ["python3.11 tools/classify_unclassified.py "
                       "--blocking --list 로 만든다"])
    body = open(found[-1], encoding="utf-8").read()
    rows = _re.findall(r"^\| *\d+ \|", body, _re.M)
    bad = []
    if len(rows) != len(want):
        bad.append(f"목록 {len(rows)}줄 != 막는 것 {len(want)}건 — "
                   "딴 것을 셌다")
    # ★ 「파서가 읽는 곳」이 비어 있으면 「정말 읽는지」를 못 본다
    blank = body.count("★ 못 찾음")
    if blank:
        bad.append(f"파서가 읽는 곳을 못 찾은 줄 {blank}개")
    for one in want[:5]:
        if f"{one['endpoint']}:{one['path']}" not in body:
            bad.append(f"{one['endpoint']}:{one['path']} 가 목록에 없다")
    return result(C["V4-30"], rid, f"{len(want)}줄", f"{len(rows)}줄",
                  not bad, bad[:4])


def run(conn, ctx) -> list:
    rid = ctx.run_id
    out = []

    # 값 대조 — A등급 필드는 100% 여야 한다
    mism = []
    for lid, sid, body in conn.execute(
        "SELECT r.listing_id, r.source_id, r.body FROM raw_response r "
        "WHERE r.endpoint='detail' AND r.status='ok'"
    ).fetchall():
        doc = json.loads(body)
        row = conn.execute(
            "SELECT vin, plate_hash, price_origin_won, displacement_cc "
            "FROM core_listing WHERE listing_id=?", (lid,)).fetchone()
        if row is None:
            mism.append(f"{lid}: CORE 행 없음")
            continue
        if clean_vin(doc.get("vin")) != row[0]:
            mism.append(f"{lid}.vin")
        if _plate_hash(doc.get("vehicleNo"), _key()) != row[1]:
            mism.append(f"{lid}.plate_hash")
    out.append(result(C["V4-01"], rid, f"A {RATIO_A:.0%}", mism or "일치",
                      not mism, mism))

    # 오매핑 — 선언된 경로보다 다른 경로와 더 잘 맞는 컬럼이 있는가
    # v1 실사고: dealer_shop ← OfficeCityState.  지금은 dealer_region 이 맞다
    wrong = conn.execute(
        "SELECT COUNT(*) FROM core_listing "
        "WHERE dealer_shop IS NOT NULL AND dealer_shop = dealer_region"
    ).fetchone()[0]
    out.append(result(C["V4-03"], rid, 0, wrong, wrong == 0))

    # 등록부 (8장 STEP 87) — 아직 적재 전이면 RAW 경로를 세어 보고만 한다
    # ★ 관측은 endpoint:path 다.  등록부도 같은 형태로 맞춘다 —
    #   json_path 만 읽으면 전건이 어긋난다 (실측: 362건 오탐)
    registered = {f"{e}:{p}" for e, p in conn.execute(
        "SELECT endpoint, json_path FROM meta_field_usage")}
    observed = set()
    for (endpoint, body) in conn.execute(
        # ★ 전역 LIMIT 은 관측 집합을 불완전하게 만든다.
        #   앞 200건이 전부 detail 이면 catalog 경로가 「유령」으로 잡힌다
        #   (실측: V4-06b 가 catalog 20경로를 오탐)
        "SELECT endpoint, body FROM ("
        " SELECT endpoint, body, ROW_NUMBER() OVER"
        "  (PARTITION BY endpoint ORDER BY id DESC) AS rn"
        " FROM raw_response WHERE status='ok') WHERE rn <= ?",
        (SAMPLE_PER_ENDPOINT,)
    ).fetchall():
        try:
            doc = json.loads(body)
        except ValueError:
            continue
        # ★ 오염된 원문을 등록부 기준으로 삼지 않는다 (STEP 87 · sync_registry 와 같은 규칙)
        from tools.sync_registry import shape_ok

        if not shape_ok(endpoint, doc):
            continue
        targets = [doc]
        if endpoint == "list":
            targets = (doc.get("SearchResults") or [])[:1] or [doc]
        for tgt in targets:
            observed |= {f"{endpoint}:{p}" for p in _paths(tgt)}
    unreg = sorted(observed - registered)
    out.append(result(C["V4-06"], rid, 0, len(unreg), not registered or not unreg,
                      unreg))
    # ★ 표본으로 판정하지 않는다.  깊은 중첩·희귀 매물 경로가 「유령」이 된다
    #   (실측: 14건이 전부 오탐이었다 — rent 정보 · inners 3단 하위)
    #   sync_registry 가 전 원문을 훑어 miss_streak 를 이미 센다.  그것을 쓴다
    ghost = [f"{e}:{p} ({n}회 미관측)" for e, p, n in conn.execute(
        "SELECT endpoint, json_path, miss_streak FROM meta_field_usage "
        "WHERE miss_streak > 0 ORDER BY miss_streak DESC")]
    out.append(result(C["V4-06b"], rid, 0, len(ghost), not ghost, ghost))

    for code, usage, col in (
        ("V4-07", "in_use", "core_column"),
        ("V4-08", "blocked", "unblock_condition"),
        ("V4-09", "deferred", "use_when"),
        ("V4-10", "display_only", "core_column"),
    ):
        n = conn.execute(
            f"SELECT COUNT(*) FROM meta_field_usage WHERE usage=? AND "
            f"({col} IS NULL OR {col}='')", (usage,)).fetchone()[0]
        out.append(result(C[code], rid, 0, n, n == 0))

    # ★ 미분류가 전부 멈춤 사유는 아니다.
    #   판정에 쓰는 경로(파서가 읽는 것)가 미분류면 그 판정이 근거 없이 돈다 — fatal.
    #   아무도 안 읽는 새 필드는 등록만 하고 진행한다 — warn.
    #   근거   미분류 필드는 정의상 판정에 안 쓰인다.
    #          그것이 전체를 멈추면 새 차종마다 파이프라인이 죽는다 (실측)
    from tools.classify_fields import WHOLE_CONTAINERS, parser_paths

    used = parser_paths()
    blocking, pending = [], []
    for endpoint, path in conn.execute(
        "SELECT endpoint, json_path FROM meta_field_usage "
        "WHERE usage='unclassified' ORDER BY endpoint, json_path"
    ).fetchall():
        bare = path.replace("[]", "")
        head = path.split("[]")[0]
        # ★ 개정 341 — 잎 이름만 견주면 과하게 막는다.
        #   「MultiView.Badge」가 「Badge」로 걸려 판정이 멈췄다.
        #   파서가 읽는 것은 「Badge」지 「MultiView.Badge」가 아니다.
        #   전체 경로로 견준다 — 막는 것이 100 → 32 로 줄었다 (실측 08-18)
        if bare in used or head in WHOLE_CONTAINERS:
            blocking.append(f"{endpoint}:{path}")
        else:
            pending.append(f"{endpoint}:{path}")
    out.append(result(C["V4-11"], rid, 0, len(blocking), not blocking,
                      blocking))
    out.append(result(C["V4-11b"], rid, "분류 대기", len(pending),
                      not pending, pending))
    out += _unclassified_split(conn, rid, blocking, pending)
    # 판단할 재료 다섯 (개정 367).  ★ 물을 때는 고를 것을 함께 준다
    out += _decide_material_check(conn, rid)
    # 막는 것의 목록 파일 (개정 390)
    out.append(_blocking_list_check(conn, rid))

    from collect.runner import REQUIRED_FACET_AXES, aspect_names

    missing = []
    for tk, kind, body in conn.execute(
        "SELECT target_key, request_kind, body FROM raw_facet"
    ).fetchall():
        # ★ Badge 는 검사하지 않는다.  facet 이 주지 않는다 (STEP 23 정정)
        axes = aspect_names(json.loads(body))
        if kind == "unspecified":
            missing += [f"{tk}:{a}" for a in sorted(REQUIRED_FACET_AXES - axes)]
    out.append(result(C["V4-12"], rid, 0, missing or 0, not missing, missing))

    # V4-13 은 소스 정적 검사다.  tools/check_src.py S7 이 정본이다
    out.append(result(C["V4-13"], rid, "check_src S7", "위임", True))
    out.append(_name_collision_check(rid))
    out += _layer_checks(rid)
    out += _mapping_coverage_checks(conn, rid, registered, observed)
    out.append(_kind_check(rid))
    out.append(_dict_filled_check(conn, rid))
    out.append(_listing_value_scope_check(rid))
    out.append(_option_code_check(conn, rid))
    return out


def _mapping_coverage_checks(conn, rid, registered, observed) -> list:
    """매핑 누락을 양쪽에서 본다 — 원문 → 컬럼, 컬럼 → 원문."""
    out = []
    unmapped = sorted(observed - registered)
    out.append(result(C["V4-02"], rid, 0, len(unmapped), True, unmapped[:20]))

    # CORE 컬럼 중 등록부가 근거를 못 대는 것
    mapped_cols = {r[0] for r in conn.execute(
        "SELECT core_column FROM meta_field_usage "
        "WHERE core_column IS NOT NULL")}
    orphan = []
    for table in ("core_listing", "core_inspection", "core_record"):
        for r in conn.execute(f"PRAGMA table_info({table})"):
            col = r[1]
            if col in OUR_COLUMNS or col in mapped_cols:
                continue
            orphan.append(f"{table}.{col}")
    out.append(result(C["V4-04"], rid, 0, len(orphan), True, orphan[:20]))

    # 원문 경로 수 — 전 실행 대비 변동
    now = conn.execute("SELECT COUNT(*) FROM meta_field_usage").fetchone()[0]
    ghost = conn.execute(
        "SELECT COUNT(*) FROM meta_field_usage WHERE miss_streak > 0"
    ).fetchone()[0]
    out.append(result(C["V4-05"], rid, now, f"{now}경로 · 미관측 {ghost}", True,
                      [] if not ghost else [f"{ghost}경로가 이번에 안 왔다"]))
    return out


# ★ 매핑표 없이도 되는 컬럼 — 우리가 만드는 값이다 (STEP 31a 와 같은 집합)
def _our_columns() -> frozenset:
    from validate.v2_load import OUR_COLUMNS as _c

    return _c


OUR_COLUMNS = _our_columns()


# 판정에 쓰는 사전 축 (dict_enum.axis).  ★ 비면 미분류인 채로 점수가 나온다.
#   ★ result_axis.axis 와 이름이 다르다 — 사전은 원문 값 집합이다
# ★ 정본은 store/dictionary.py 다.  두 곳에 두면 갈린다 (V4-21)
from store.dictionary import JUDGING_AXES  # noqa: E402


# target_config 가 담아도 되는 것.  ★ 차종·실행 단위 값만이다
TARGET_CONFIG_KEYS = ("as_of", "depreciation", "SPEC_DEFAULT_ON",
                      "SPEC_DEFAULT_OFF",
                      # 차종 단위 — 트림 신차가 사다리 · 옵션가 P90 (F-scoring ④)
                      "trim_ladder", "option_base",
                      # 실행 단위 — 사용자가 끈 취향 · 고른 옵션 (개정 292 ④)
                      "taste_off", "picked_options",
                      # 사이트 단위 — 그 사이트의 우수등급 규칙 (개정 306)
                      # 개정 365 — 「우수등급 하나」가 「항목 여럿의 합」이 됐다.
                      # ★ 사이트 설정이지 매물 값이 아니다
                      "site_warranty")


def _listing_value_scope_check(rid):
    """★ 매물 값이 차종 설정에 섞이지 않았는가 (F-1)."""
    import os
    import re

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bad = []
    for base, dirs, files in os.walk(os.path.join(root, "analyze")):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in sorted(files):
            if not f.endswith(".py"):
                continue
            body = open(os.path.join(base, f), encoding="utf-8").read()
            for m in re.finditer(
                    r'target_config(?:\.get\(|\[)["\'](\w+)["\']', body):
                if m.group(1) not in TARGET_CONFIG_KEYS:
                    bad.append(f"{f}: target_config[{m.group(1)}]")
    return result(C["V4-24"], rid, 0, bad or 0, not bad, sorted(set(bad))[:8])


def _dict_filled_check(conn, rid):
    """★ v1 이 accident_type 전건 unknown 이 된 자리다 (A-4)."""
    empty = [a for a in JUDGING_AXES if not conn.execute(
        "SELECT COUNT(*) FROM dict_enum WHERE axis = ?", (a,)).fetchone()[0]]
    has_score = conn.execute(
        "SELECT COUNT(*) FROM result_score").fetchone()[0]
    bad = empty if has_score else []
    return result(C["V4-25"], rid, 0, bad or 0, not bad,
                  [f"{a}: 사전 0행인데 판정이 돌았다" for a in bad])


def _kind_check(rid):
    """★ 성격 없는 Check 가 있으면 등급이 손으로 정해진다 (STEP 54)."""
    import importlib

    bad = []
    for mod in ("v1_collect", "v2_load", "v3_logic", "v4_mapping", "v5_value",
                "v10_admin"):
        for code, chk in importlib.import_module(
                f"validate.{mod}").C.items():
            if not getattr(chk, "kind", ""):
                bad.append(f"{mod}:{code}")
    return result(C["V4-19"], rid, 0, bad or 0, not bad, bad)


def propose_fix(results: list) -> list[str]:
    """보정은 재파싱으로 한다.  재수집이 아니다.  원문은 그대로다 (STEP 62)."""
    fixes = []
    for r in results:
        if r.passed:
            continue
        if r.check.code in ("V4-01", "V4-03"):
            fixes.append(f"{r.check.code}: 파서 수정 → 재파싱(S6) → V4 재실행")
        elif r.check.code.startswith("V4-0"):
            fixes.append(f"{r.check.code}: 등록부에 사유와 함께 등록 (8장 STEP 87)")
        elif r.check.code == "V4-12":
            fixes.append("V4-12: facet 재수집 (S2). 축을 열거해 요청하지 않는다")
    return fixes


def _option_code_check(conn, rid):
    """V4-20 — dict_option_code 에 문장이 없는가.

    ★ code 는 식별자다.  화면에 낼 말은 display 가 갖는다.
      code 자리에 문장이 들어가면 사이트가 표기를 바꿀 때 전건이 새 코드가 된다
    실측 08-15: 검사가 선언만 있고 안 돌아 62행 전부 문장이었다 (B-4)
    """
    has = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' "
        "AND name='dict_option_code'").fetchone()[0]
    if not has:
        return not_applicable(C["V4-20"], rid, "사전 표가 없다")
    bad = [f"{code!r}" for (code,) in conn.execute(
        "SELECT code FROM dict_option_code") if _is_sentence(code)]
    return result(C["V4-20"], rid, 0, len(bad), not bad, bad[:8])


def _is_sentence(code) -> bool:
    """식별자가 아니라 사람 말인가.  ★ 공백이나 한글이 있으면 말이다."""
    import re

    if not isinstance(code, str):
        return False
    return bool(re.search(r"[\s가-힣]", code))
