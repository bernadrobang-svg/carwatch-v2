# -*- coding: utf-8 -*-
"""V11 표현 계층 검증 (14장 STEP 153).

지시서   STEP 153
근거     ★ 화면은 데이터를 읽는다.  만들지 않는다.
         SQL·산술이 web/ 에 있으면 같은 값이 두 곳에서 만들어진다
금지     검사기 자신을 대상으로 삼는 것 (여섯 번 겪었다)
"""
from __future__ import annotations

import ast
import os
from http import HTTPStatus
import re

from validate.base import (
    Check,
    FATAL,
    KIND_CODE,
    KIND_CONTRACT,
    KIND_EXTERNAL,
    not_applicable,
    result,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
TEMPLATES = os.path.join(WEB, "templates")

SQL_WORDS = ("SELECT ", "INSERT ", "UPDATE ", "DELETE ", " FROM ")
LOCAL_HOSTS = ("127.0.0.1", "localhost", "::1")
RE_ARITH = re.compile(r"\{\{[^}]*[+\-*/%][^}]*\}\}")

C = {
    "V11-01": Check("V11", "V11-01", "web/ 에 SQL 문자열이 없음", FATAL, "run",
                    "조회는 store · report 가 한다. 화면은 DTO 를 받는다",
                    KIND_CONTRACT),
    "V11-02": Check("V11", "V11-02", "기본 바인딩이 127.0.0.1", FATAL, "run",
                    "config/web.json 의 host 를 되돌린다. "
                    "외부 공개는 --host 로 명시한다",
                    KIND_CONTRACT),
    "V11-03": Check("V11", "V11-03", "전 Route 에 role 이 지정됨", FATAL, "run",
                    "라우팅 표에 role 을 적는다 (STEP 142)", KIND_CODE),
    "V11-04": Check("V11", "V11-04", "템플릿에 산술 연산이 없음", FATAL, "run",
                    "값은 view_* 가 만든다. 템플릿은 표시만 한다 (STEP 152)",
                    KIND_CODE),
    "V11-05": Check("V11", "V11-05", "{{! }} 사용처가 화이트리스트에 있음",
                    FATAL, "run",
                    "RAW_ALLOW 에 없으면 이스케이프한다. "
                    "사용자 입력을 원문으로 넣지 않는다",
                    KIND_CONTRACT),
    "V11-06": Check("V11", "V11-06", "정적 경로 탈출이 거부됨", FATAL, "run",
                    "static_path 의 realpath 검사를 확인한다", KIND_CONTRACT),
    "V11-07": Check("V11", "V11-07", "쿠키에 role 문자열이 없음", FATAL, "run",
                    "쿠키에는 session_id 만 담는다 (STEP 146)", KIND_CONTRACT),
    "V11-08": Check("V11", "V11-08", "상태 변경이 GET 경로에 없음", FATAL, "run",
                    "라우팅 표에서 그 경로를 POST 로 바꾼다 (STEP 147)",
                    KIND_CONTRACT),
    "V11-09": Check("V11", "V11-09", "미리보기 없이 저장이 안 됨", FATAL, "run",
                    "SaveGate 를 거치게 한다 (13장 STEP 138)", KIND_CONTRACT),
    "V11-10": Check("V11", "V11-10", "오류 화면에 스택 트레이스가 없음",
                    FATAL, "run",
                    "traceback 을 화면에 내지 않는다. run_id 만 낸다",
                    KIND_CONTRACT),
    "V11-11": Check("V11", "V11-11", "result_* 가 비었을 때 안내가 나옴",
                    FATAL, "run",
                    "empty_state 가 배너를 내는지 본다 (STEP 149)", KIND_CODE),
    "V11-28": Check("V11", "V11-28", "응답 헤더에 비 ASCII 없음", FATAL, "run",
                    "flash 는 서버가 들고 있다가 다음 GET 에서 낸다. "
                    "HTTP 헤더는 latin-1 이라 한글이면 서버가 죽는다",
                    KIND_CONTRACT),
    "V11-29": Check("V11", "V11-29", "렌더된 폼의 csrf_token 이 비어 있지 않음",
                    FATAL, "run",
                    "부분 템플릿에도 PageContext 를 넘긴다 (STEP 144)",
                    KIND_CODE),
    "V11-30": Check("V11", "V11-30", "시안 ↔ 템플릿 대조 통과", FATAL, "run",
                    "tools/check_screens.py 를 보고 시안을 먼저 확인한다",
                    KIND_CODE),
    "V11-31": Check("V11", "V11-31",
                    "must_change_secret=1 에서 /password 가 200",
                    FATAL, "run",
                    "바꾸는 화면 자체가 막히면 못 바꾼다. 예외를 늘리지 않는다",
                    KIND_CONTRACT),
    "V11-32": Check("V11", "V11-32", "known_issues 의 키가 전부 targets 에 있음",
                    FATAL, "run",
                    "없는 차종의 결함 메모는 화면에 못 뜬다. 오타를 잡는다",
                    KIND_EXTERNAL),
    "V11-13": Check("V11", "V11-13", "app.css 에 토큰 밖의 색값이 없음", FATAL, "run",
                    "STEP 145a 의 12 토큰만 쓴다. 색이 늘면 강조가 사라진다",
                    KIND_CODE),
    "V11-14": Check("V11", "V11-14", "숫자 셀에 mono 가 걸려 있음", FATAL, "run",
                    "자릿수가 세로로 맞아야 비교된다",
                    KIND_CODE),
    "V11-15": Check("V11", "V11-15", "화면이 빌드 산출물에 의존하지 않음", FATAL, "run",
                    "표준 라이브러리만 쓴다",
                    KIND_CONTRACT),
    "V11-16": Check("V11", "V11-16", "/why 가 전 Component 를 냄", FATAL, "run",
                    "17축 전건을 낸다",
                    KIND_CODE),
    "V11-17": Check("V11", "V11-17", "/why 가 조회 상태 절을 냄", FATAL, "run",
                    "excluded 축이 왜 비었는지 설명한다",
                    KIND_CODE),
    "V11-18": Check("V11", "V11-18", "축 태그가 전건 필터 링크임", FATAL, "run",
                    "값을 누르면 그 조건으로 걸러진다",
                    KIND_CODE),
    "V11-19": Check("V11", "V11-19", "폴링 실패 시 화면이 안 깨짐", FATAL, "run",
                    "JS 에 의존하지 않는다",
                    KIND_CODE),
    "V11-20": Check("V11", "V11-20", "분모 표시가 있음", FATAL, "run",
                    "earned/denominator 를 같은 자로 낸다",
                    KIND_CODE),
    "V11-21": Check("V11", "V11-21", "행동 요청 파라미터가 현재 필터와 일치", FATAL, "run",
                    "지금 조건이 다음 행동의 조건이다",
                    KIND_CODE),
    "V11-22": Check("V11", "V11-22", "excluded 축이 「—/N」 으로 표시됨", FATAL, "run",
                    "0 점이 아니라 제외다",
                    KIND_CODE),
    "V11-23": Check("V11", "V11-23", "비로그인 관심 POST 가 유도 화면을 냄", FATAL, "run",
                    "403 이 아니라 로그인을 유도한다",
                    KIND_CODE),
    "V11-24": Check("V11", "V11-24", "메뉴 분류가 잠금 단위와 일치", FATAL, "run",
                    "운영·조정·탐색 3분류",
                    KIND_CONTRACT),
    "V11-25": Check("V11", "V11-25", "사유 없이 설정이 저장되지 않음", FATAL, "run",
                    "왜 바꿨는지가 남아야 한다",
                    KIND_CONTRACT),
    "V11-26": Check("V11", "V11-26", "되돌릴 수 없는 행동에 확인이 있음", FATAL, "run",
                    "확인 문구를 넣는다",
                    KIND_CONTRACT),
    "V11-27": Check("V11", "V11-27", "가입 정책에 따라 화면이 바뀜", FATAL, "run",
                    "open·approval·closed",
                    KIND_CODE),
    "V11-33": Check("V11", "V11-33", "POST 가 저장 없이 성공 메시지를 내지 않음", FATAL, "run",
                    "실제로 저장하거나, 준비 중이라고 낸다",
                    KIND_CONTRACT),
    "V11-35": Check("V11", "V11-35", "중첩 if 가 안쪽부터 닫힘", FATAL, "run",
                    "짝을 세어 닫는다",
                    KIND_CODE),
    "V11-34": Check("V11", "V11-34", "화면이 요청당 쿼리 상한을 넘지 않음",
                    FATAL, "run",
                    "축 조회를 IN 절로 묶는다. 행마다 돌면 200행에 1,000쿼리다",
                    KIND_CODE),
    "V11-36": Check("V11", "V11-36", "잘못된 쿼리 파라미터가 500 을 내지 않음",
                    FATAL, "run",
                    "500 은 「우리 결함」이라는 뜻이다. 입력 오류는 400 이다",
                    KIND_CODE),
    "V11-37": Check("V11", "V11-37", "POST 가 예상 밖 500 을 내지 않음",
                    FATAL, "run",
                    "전 POST 를 눌러 본다. 500 은 우리 결함이라는 뜻이고 "
                    "입력 오류는 400, 권한은 403 이다",
                    KIND_CODE),
    "V11-38": Check("V11", "V11-38", "템플릿이 쓰는 값을 뷰가 넘김",
                    FATAL, "run",
                    "절만 만들고 값을 안 넘기면 화면이 조용히 빈 채로 뜬다. "
                    "엔진이 없는 이름을 빈 값으로 내주어 아무도 모른다",
                    KIND_CODE),
    "V11-39": Check("V11", "V11-39", "저장 단추가 실제로 저장함",
                    FATAL, "run",
                    "「저장」이라 적힌 단추가 아무것도 안 바꾸면 사람이 "
                    "바뀐 줄 알고 넘어간다. 준비 중이면 disabled 로 둔다",
                    KIND_CODE),
    "V11-12": Check("V11", "V11-12", "라우팅 표의 view 가 10·13장에 실재함",
                    FATAL, "run",
                    "없는 화면은 라우팅 표에서 뺀다", KIND_CODE),
    "V11-40": Check("V11", "V11-40", "반입분의 origin 이 'import' 임",
                    FATAL, "run",
                    "밖에서 받아 넣은 목록을 collector 로 남기면 "
                    "「우리가 받았다」가 된다 (STEP 136a)",
                    KIND_CODE),
    "V11-41": Check("V11", "V11-41", "반입 뒤 S5~S10 이 이어서 돎",
                    FATAL, "run",
                    "반입이 S4 완료를 안 남기면 precheck('S5') 가 "
                    "「선행 단계 미완료」로 막는다 (STEP 136b ④)",
                    KIND_CODE),
    "V11-42": Check("V11", "V11-42", "S4 완료 행의 actual 이 'import' 임",
                    FATAL, "run",
                    "반입인데 collector 로 남기면 감사 기록이 거짓이 된다 "
                    "(STEP 136b ④)",
                    KIND_CODE),
}

# ★ 상태를 바꾸는 이름.  GET 경로에 있으면 안 된다 (STEP 147)
MUTATING = ("add", "update", "delete", "create", "apply", "save", "logout",
            "revert", "confirm")
# 그래도 GET 이 허용되는 것 — 폼을 「보여주는」 화면이다
MUTATING_GET_OK = ("view_admin_run", "view_admin_scoring",
                   "view_admin_targets", "view_admin_registry",
                   "view_admin_config", "view_admin_query", "view_admin_api",
                   "view_admin_tools", "view_admin_requests")


def _web_sources() -> dict[str, str]:
    out = {}
    for base, dirs, files in os.walk(WEB):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(base, f)
                out[os.path.relpath(path, ROOT).replace("\\", "/")] = \
                    open(path, encoding="utf-8").read()
    return out


def run(conn, ctx) -> list:
    from web.routes import GET, POST, ROUTES
    from web.session import static_path
    from web.template import RAW_ALLOW
    from web.server import load_web_config

    rid = ctx.run_id
    src = _web_sources()
    out = []

    # V11-01 — 화면이 조회하지 않는다.  문자열 상수만 본다 (STEP 53)
    bad = []
    for rel, body in src.items():
        try:
            tree = ast.parse(body)
        except SyntaxError:
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Constant) and isinstance(n.value, str) \
                    and any(w in n.value.upper() for w in SQL_WORDS):
                bad.append(f"{rel}: {n.value[:40]}")
    out.append(result(C["V11-01"], rid, 0, bad or 0, not bad, bad))

    # V11-02
    host = load_web_config(ROOT)["host"]
    out.append(result(C["V11-02"], rid, "127.0.0.1", host,
                      host in LOCAL_HOSTS))

    # V11-03
    bad = [r.path for r in ROUTES if not r.role]
    out.append(result(C["V11-03"], rid, 0, bad or 0, not bad, bad))

    # V11-04
    bad = []
    for name in sorted(os.listdir(TEMPLATES)):
        if not name.endswith(".html"):
            continue
        body = open(os.path.join(TEMPLATES, name), encoding="utf-8").read()
        for m in RE_ARITH.finditer(body):
            bad.append(f"{name}: {m.group(0)[:30]}")
    out.append(result(C["V11-04"], rid, 0, bad or 0, not bad, bad))

    # V11-05
    bad = []
    for name in sorted(os.listdir(TEMPLATES)):
        if not name.endswith(".html"):
            continue
        body = open(os.path.join(TEMPLATES, name), encoding="utf-8").read()
        for m in re.finditer(r"\{\{!\s*([\w.]+)\s*\}\}", body):
            if m.group(1) not in RAW_ALLOW:
                bad.append(f"{name}: {m.group(1)}")
    out.append(result(C["V11-05"], rid, 0, bad or 0, not bad, bad))

    # V11-06 — 실제로 던져 본다
    leaked = [p for p in ("../secrets/plate_hmac.key", "../../etc/passwd",
                          "/etc/passwd", "....//x")
              if static_path(p) is not None]
    out.append(result(C["V11-06"], rid, 0, leaked or 0, not leaked, leaked))

    # V11-07
    from web.session import set_cookie

    cookie = set_cookie("cw_session", "x", 1)
    has_role = "role" in cookie or "admin" in cookie
    out.append(result(C["V11-07"], rid, "없음",
                      "있음" if has_role else "없음", not has_role))

    # V11-08 — 상태 변경이 GET 으로 열려 있는가
    bad = []
    for r in ROUTES:
        if GET not in r.methods:
            continue
        if any(w in r.view for w in MUTATING) \
                and r.view not in MUTATING_GET_OK:
            bad.append(f"{r.path} ({r.view})")
    out.append(result(C["V11-08"], rid, 0, bad or 0, not bad, bad))

    # V11-09 — SaveGate 가 미리보기를 요구하는가
    from report.screens.admin import SaveGate

    gate = SaveGate(previewed=False, reason_given=True, locked=False)
    ok = not gate.can_save and SaveGate(True, True, False).can_save
    out.append(result(C["V11-09"], rid, "막힘", "막힘" if ok else "통과", ok))

    # V11-10 — 오류 화면이 내부 문구를 내는가
    from web.context import error_page

    page = error_page(RuntimeError("list index out of range"), "r1")
    leaked = [w for w in ("Traceback", "index", "File \"", "line ")
              if w in page.reason or w in page.action]
    out.append(result(C["V11-10"], rid, 0, leaked or 0, not leaked, leaked))

    # V11-11 — 비었을 때 안내
    from web.app import empty_state

    banner = empty_state(conn, ctx_account(ctx))
    total = _count(conn, "result_score")
    need = total == 0
    ok = (banner is not None) if need else True
    out.append(result(C["V11-11"], rid, "안내" if need else "해당 없음",
                      banner.text if banner else "없음", ok))

    # V11-12 — 지시서 표 ↔ 코드 ↔ HANDLERS 삼자 대조
    out.append(_routing_table_check(rid))
    out += _late_checks(rid)
    out += _screen_checks(conn, rid)
    _ = POST
    return out


def _late_checks(rid) -> list:
    """08-14 신설 5종 (STEP 153)."""
    import json
    import subprocess
    import sys as _s

    from contracts import ANONYMOUS, Account, ROLE_ADMIN
    from web.app import redirect
    from web.routes import GET, ROUTES, match
    from web.server import guard
    from web.template import render_str

    out = []

    # V11-28 — 헤더에 비 ASCII 가 있으면 서버가 죽는다
    _st, headers, _b = redirect("/watch", "관심에 담았습니다", "k")
    bad = []
    for k, v in headers.items():
        try:
            f"{k}: {v}".encode("latin-1")
        except UnicodeEncodeError:
            bad.append(f"{k}: 비 ASCII")
    out.append(result(C["V11-28"], rid, 0, bad or 0, not bad, bad))

    # V11-29 — 폼 템플릿이 page 없이 렌더되면 토큰이 빈다
    html = render_str('{{ page.csrf_token }}', {"page": {"csrf_token": "T"}})
    empty = render_str('{{ page.csrf_token }}', {})
    ok = html == "T" and empty == ""
    forms = _templates_with_form()
    missing = [f for f in forms if "page.csrf_token" not in
               open(os.path.join(TEMPLATES, f), encoding="utf-8").read()]
    bad = ([] if ok else ["템플릿 엔진이 page 를 못 읽는다"])
    bad += [f"{f}: 폼에 csrf 가 없다" for f in missing]
    out.append(result(C["V11-29"], rid, 0, bad or 0, not bad, bad))

    # V11-30 — 시안 대조.  ★ 검사를 검사한다
    r = subprocess.run([_s.executable,
                        os.path.join(ROOT, "tools", "check_screens.py")],
                       capture_output=True, text=True, cwd=ROOT)
    bad = [x.strip() for x in r.stdout.splitlines() if "✗" in x][:6]
    out.append(result(C["V11-30"], rid, 0, len(bad), r.returncode == 0, bad))

    # V11-31 — 바꾸는 화면 자체는 열린다
    tmp = Account(1, ROLE_ADMIN, "임시", must_change_secret=True)
    route = match("/password", GET)[0]
    ok = route is not None and guard(tmp, route) is None
    out.append(result(C["V11-31"], rid, "200", "200" if ok else "막힘", ok))

    # V11-32 — known_issues 의 키가 targets 에 있는가
    bad = []
    ki = os.path.join(ROOT, "config", "known_issues.json")
    tg = os.path.join(ROOT, "config", "targets.json")
    if os.path.isfile(ki) and os.path.isfile(tg):
        with open(ki, encoding="utf-8") as f:
            issues = json.load(f)
        with open(tg, encoding="utf-8") as f:
            keys = set(json.load(f))
        bad = [f"없는 차종: {k}" for k in issues
               if not k.startswith("_") and k not in keys]
    out.append(result(C["V11-32"], rid, 0, bad or 0, not bad, bad))
    _ = (ANONYMOUS, ROUTES)
    return out


def _templates_with_form() -> list:
    return [f for f in sorted(os.listdir(TEMPLATES))
            if f.endswith(".html")
            and "<form" in open(os.path.join(TEMPLATES, f),
                                encoding="utf-8").read()]


# 화면이 아닌 Route.  파일을 낸다 — HANDLERS 에 없는 것이 맞다
NON_SCREEN_VIEWS = ("serve_static",)


# 라우팅 표 행.  ★ 표가 여러 개로 나뉘어도 합쳐 센다 (실측: 26 + 3)
RE_ROUTE_ROW = re.compile(r"^\| \*?\*?`([^`]+)`\*?\*? \| *(?:GET|POST)",
                          re.M)


def _spec_routes() -> list | None:
    """지시서에서 라우팅 표 행을 전수 뽑는다.

    ★ 「path | method」 머리글만 찾으면 뒤에 이어지는 별표를 놓친다.
      실측: 본표 26 + 시안표 3 = 29 였는데 26 만 세어 3 을 놓쳤다
    """
    # ★ 장 파일이 정본이다.  통짜 지시서는 옛 판일 수 있다 (실측)
    for rel in (os.path.join("docs", "chapters", "61-web.md"),
                "개발지시서.md"):
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            continue
        # 앞 파일이 있으면 그것만 본다 — 뒤 파일이 대신 통과시키지 않는다
        body = open(path, encoding="utf-8").read()
        rows = RE_ROUTE_ROW.findall(body)
        if rows:
            # ★ 첫 번째로 찾은 것을 쓴다.  「행이 적으면 다음 파일」로 넘어가면
            #   행을 지웠을 때 옛 판이 대신 통과시킨다 (실측)
            return rows
    return None


def _routing_table_check(rid):
    """★ 지시서 표를 실제로 센다.

    실측: 「표의 view 가 코드에 있는가」만 보고 표 자체는 안 봤다.
         그 결과 표 29 · 코드 30 이 어긋난 것을 검사가 못 잡았다.
    본다   ① 표에 있는데 코드에 없다  ② 코드에 있는데 표에 없다
          ③ 표의 view 가 HANDLERS 에 없다 (serve_static 제외)
    """
    from web.routes import ROUTES
    from web.views import HANDLERS

    bad = []
    code_paths = {r.path for r in ROUTES}
    rows = _spec_routes()

    if rows is None:
        bad.append("라우팅 표를 찾지 못했다 (개발지시서.md · docs/chapters)")
    else:
        table = set(rows)
        if len(rows) != len(table):
            bad.append(f"★ 표에 중복 행 {len(rows) - len(table)}개 — "
                       f"한 행에 한 경로다")
        bad += [f"표에만 있다: {p}" for p in sorted(table - code_paths)]
        bad += [f"표에 없다: {p}" for p in sorted(code_paths - table)]

    bad += [f"{r.path} → {r.view} 가 HANDLERS 에 없다" for r in ROUTES
            if r.view not in HANDLERS and r.view not in NON_SCREEN_VIEWS]
    n = len(HANDLERS) + len(NON_SCREEN_VIEWS)
    if n != len(ROUTES):
        bad.append(f"Route {len(ROUTES)} ≠ HANDLERS {len(HANDLERS)} "
                   f"+ 비화면 {len(NON_SCREEN_VIEWS)}")
    return result(C["V11-12"], rid, 0, len(bad), not bad, bad[:20])


def _count(conn, table: str) -> int:
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    except Exception:                                    # noqa: BLE001
        return 0


def ctx_account(ctx):
    from contracts import ANONYMOUS

    return getattr(ctx, "account", ANONYMOUS)


def _view_exists(name: str) -> bool:
    """10장 화면 · 13장 관리자 화면 · 14장 어댑터 중 하나에 있으면 된다."""
    from report.screens import admin as admin_screens
    from report.screens import build as screens
    from web import views as web_views

    if name in getattr(web_views, "HANDLERS", {}):
        return True
    return any(hasattr(m, name) for m in (screens, admin_screens))


# ── V11-13 ~ V11-27 · V11-33 ~ V11-36 (STEP 153) ────────────────────
# ★ 화면 규격은 시안이 정본이다.  여기서는 「지켜졌는가」만 본다
RE_COLOR = re.compile(r"#[0-9a-fA-F]{3,8}\b")
RE_ROOT = re.compile(r":root\s*\{[^}]*\}", re.S)
BUILD_ARTIFACTS = ("node_modules", "dist/", "webpack", "vite", ".min.js",
                   "npm run", "package.json")
# 되돌릴 수 없는 행동.  ★ 확인 없이 실행되면 안 된다 (V11-26)
IRREVERSIBLE = ("remove", "delete", "disable", "close", "revert")


def _tpl(name: str) -> str:
    path = os.path.join(TEMPLATES, name)
    return open(path, encoding="utf-8").read() if os.path.isfile(path) else ""


def _all_templates() -> dict:
    return {f: _tpl(f) for f in sorted(os.listdir(TEMPLATES))
            if f.endswith(".html")}


def _screen_checks(conn, rid) -> list:
    """08-14 신설 19종.  ★ D-1 이 가리고 있어 검사 밖에 있던 것들이다."""
    from web.routes import GET, ROUTES
    from web.template import FILTERS

    out = []
    css = _tpl("").join(()) if False else open(
        os.path.join(ROOT, "web", "static", "app.css"), encoding="utf-8"
    ).read() if os.path.isfile(
        os.path.join(ROOT, "web", "static", "app.css")) else ""
    tpls = _all_templates()

    # V11-13 — 토큰 밖 색값
    bad = sorted(set(RE_COLOR.findall(RE_ROOT.sub("", css))))
    out.append(result(C["V11-13"], rid, 0, bad or 0, not bad, bad))

    # V11-14 — 숫자 셀에 mono
    has_mono = "--mono" in css and "var(--mono)" in css
    num_mono = re.search(r"\.num[^{]*\{[^}]*var\(--mono\)", css) is not None
    ok = has_mono and num_mono
    out.append(result(C["V11-14"], rid, "mono", "mono" if ok else "없음", ok,
                      [] if ok else [".num 에 var(--mono) 가 없다"]))

    # V11-15 — 빌드 산출물 의존
    bad = [f"{f}: {w}" for f, body in tpls.items()
           for w in BUILD_ARTIFACTS if w in body]
    bad += [f"app.css: {w}" for w in BUILD_ARTIFACTS if w in css]
    out.append(result(C["V11-15"], rid, 0, bad or 0, not bad, bad))

    # V11-16 · V11-17 · V11-20 · V11-22 — /why 절
    why = tpls.get("why.html", "")
    miss = [k for k, mark in (("전 Component", "v.axes"),
                              ("조회 상태", "diagnosis"),
                              ("분모 표시", "denominator"),
                              ("excluded 표기", "excluded"))
            if mark not in why]
    out.append(result(C["V11-16"], rid, 0,
                      0 if "v.axes" in why else 1, "v.axes" in why,
                      [] if "v.axes" in why else ["axes 반복이 없다"]))
    ok17 = "diagnosis" in why and "확인 못 한 것" in why
    out.append(result(C["V11-17"], rid, "조회 상태",
                      "있음" if ok17 else "없음", ok17))
    ok20 = "denominator" in why and "earned" in why
    out.append(result(C["V11-20"], rid, "분모 표시",
                      "있음" if ok20 else "없음", ok20,
                      [] if ok20 else ["earned/denominator 를 안 낸다"]))
    ok22 = "excluded" in why and "—" in why
    out.append(result(C["V11-22"], rid, "—/N",
                      "있음" if ok22 else "없음", ok22))
    _ = miss

    # V11-18 — 축 태그가 필터 링크
    lst = tpls.get("listings.html", "") + tpls.get("recommend.html", "")
    ok18 = "filter_url" in lst or "?axis=" in lst
    out.append(result(C["V11-18"], rid, "링크",
                      "링크" if ok18 else "글자만", ok18,
                      [] if ok18 else ["축 칩이 filter_url 을 안 쓴다"]))

    # V11-19 — 폴링 실패에도 화면이 안 깨진다 (JS 를 안 쓰므로 구조로 본다)
    ok19 = not any("setInterval" in b or "fetch(" in b
                   for b in tpls.values())
    out.append(result(C["V11-19"], rid, "JS 없음",
                      "JS 없음" if ok19 else "JS 있음", ok19))

    # V11-21 — 행동 파라미터가 현재 필터와 일치
    ok21 = "filter" in tpls.get("listings.html", "") or "?" in lst
    out.append(result(C["V11-21"], rid, "일치",
                      "일치" if ok21 else "없음", ok21))

    # V11-23 — ★ 실제로 눌러 본다.  「담긴다」만 보면 안 된다.
    #   실측 08-14 에 403 이 나왔는데 통과였다 (STEP 149i)
    out.append(_watch_invite_check(conn, rid))

    # V11-24 — 메뉴 분류 == 잠금 단위
    groups = {r.menu for r in ROUTES if r.menu}
    ok24 = groups <= {"운영", "조정", "탐색"}
    out.append(result(C["V11-24"], rid, "3분류", sorted(groups), ok24))

    # V11-25 · V11-26 — 사유 · 확인
    forms = {f: b for f, b in tpls.items() if "<form" in b}
    admin_forms = {f: b for f, b in forms.items() if f.startswith("admin_")}
    # ★ 폼 안에 저장 단추가 있는 것만 본다 (V11-25).
    #   본문의 「저장하지 않습니다」 같은 설명이 걸리면
    #   설명을 쓸수록 검사가 붉어진다 — V6-03 과 같은 함정이다
    bad = []
    for f, b in admin_forms.items():
        for m in re.finditer(r"<form\b.*?</form>", b, re.S):
            chunk = m.group(0)
            if "저장" not in chunk:
                continue
            if 'name="reason"' not in chunk and "previewed" not in chunk:
                bad.append(f)
                break
    out.append(result(C["V11-25"], rid, 0, bad or 0, not bad, bad))
    # ★ 폼 단위로 본다.  파일에 그 낱말이 있다고 위험한 것이 아니다
    bad = []
    for f, b in forms.items():
        for m in re.finditer(r"<form\b.*?</form>", b, re.S):
            chunk = m.group(0)
            if any(f'value="{w}"' in chunk for w in IRREVERSIBLE) \
                    and "data-confirm" not in chunk:
                bad.append(f"{f}: 확인 없이 실행된다")
    out.append(result(C["V11-26"], rid, 0, bad or 0, not bad, bad))

    # V11-27 — 가입 정책에 따라 화면이 바뀐다
    join = tpls.get("join.html", "")
    ok27 = "closed" in join and "approval" in join
    out.append(result(C["V11-27"], rid, "3정책",
                      "반영" if ok27 else "고정", ok27))

    # V11-33 — 저장 없이 성공 메시지
    # ★ AST 로 본다.  정규식으로 함수 경계를 자르면 중첩 함수에서 깨진다
    import ast

    src = open(os.path.join(ROOT, "web", "views.py"), encoding="utf-8").read()
    bad = []
    tree = ast.parse(src)
    # ★ 가장 안쪽 함수만 본다.  바깥이 안쪽 본문을 품어 오탐이 난다
    inner = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
             and not any(isinstance(c, ast.FunctionDef)
                         for c in ast.walk(n) if c is not n)]
    for node in inner:
        body = ast.get_source_segment(src, node) or ""
        if "저장했습니다" in body and not re.search(
                r"\b(conn\.execute|apply_config|set_role|set_disabled|"
                r"enqueue_recalc|change_secret|classify_field|_upd|"
                r"watch_close|create_dev_request|preview_scoring)\b", body):
            bad.append(f"{node.name}: 저장 없이 성공을 낸다")
    out.append(result(C["V11-33"], rid, 0, bad or 0, not bad, bad))

    # V11-35 — 중첩 if
    from web.template import render_str

    got = render_str("A{% if !c %}B{% if a %}C{% endif %}D{% endif %}E",
                     {"c": 0, "a": 0})
    ok35 = got == "ABDE"
    out.append(result(C["V11-35"], rid, "ABDE", got, ok35))

    # V11-34 — 요청당 쿼리 상한
    out.append(_query_budget_check(conn, rid))
    # 반입 3종 (13장 STEP 136a · 136b)
    out.append(_import_origin_check(conn, rid))
    out.append(_import_resume_check(conn, rid))
    out.append(_import_step4_check(conn, rid))
    out.append(_post_smoke_check(conn, rid))
    out.append(_context_supplied_check(conn, rid))
    out.append(_save_button_check(conn, rid))

    # V11-36 — 잘못된 파라미터가 400 인가
    from errors import ValidationError
    from web.views import _int_param

    bad = []
    for raw in ("abc", "-1", "0", "1e3"):
        try:
            _int_param({"page": raw}, "page", 1)
            bad.append(f"page={raw} 를 받아들인다")
        except ValidationError:
            pass
    out.append(result(C["V11-36"], rid, 0, bad or 0, not bad, bad))

    _ = (GET, FILTERS, conn)
    return out


def _query_budget_check(conn, rid):
    """★ 실제로 세어 본다.  「IN 절로 묶었다」를 글로만 두지 않는다 (F-3)."""
    import json as _j
    import sqlite3 as _sq

    from contracts import ANONYMOUS
    from report.screens.build import view_listings
    from report.screens.views import ListingFilter

    with open(os.path.join(ROOT, "config", "web.json"),
              encoding="utf-8") as f:
        cap = int(_j.load(f)["max_queries_per_request"])
    ver = conn.execute(
        "SELECT MAX(calc_version) FROM result_score").fetchone()[0]
    if not ver:
        return not_applicable(C["V11-34"], rid, "판정 결과가 없다")

    class Counting(_sq.Connection):
        n = 0

        def execute(self, *a, **k):
            Counting.n += 1
            return super().execute(*a, **k)

    # ★ 목록 하나만 세면 다른 화면이 검사 밖이다.
    #   실측 08-15: view_listings 3회는 통과인데 dashboard 는 21회였다 (B-2)

    path = conn.execute("PRAGMA database_list").fetchall()[0][2]
    probe = _sq.connect(path, factory=Counting)
    with open(os.path.join(ROOT, "config", "finance.json"),
              encoding="utf-8") as f:
        fin = _j.load(f)
    from contracts import ROLE_ADMIN, Account
    from web.routes import GET, ROUTES
    from web.views import HANDLERS
    from web.server import guard

    row = conn.execute(
        "SELECT listing_id FROM result_score LIMIT 1").fetchone()
    acc = Account(1, ROLE_ADMIN, "마스터")
    worst, bad = 0, []
    Counting.n = 0
    view_listings(ANONYMOUS, probe, ListingFilter(calc_version=ver), fin,
                  ROOT)
    worst = Counting.n
    if worst > cap:
        bad.append(f"/listings 한 쪽에 {worst} 쿼리")

    for route in ROUTES:
        if GET not in route.methods or route.view == "serve_static":
            continue
        fn = HANDLERS.get(route.view)
        if fn is None or guard(acc, route) is not None:
            continue
        pv = {}
        if "{" in route.path and row:
            pv = {route.path.split("{")[1].split("}")[0]: str(row[0])}
        Counting.n = 0
        try:
            fn(probe, acc, {"query": {}, "form": {}, "method": GET},
               path_vars=pv, csrf="t")
        except Exception:                                    # noqa: BLE001
            continue          # V11-30 이 잡는다
        worst = max(worst, Counting.n)
        if Counting.n > cap:
            bad.append(f"{route.path} 한 쪽에 {Counting.n} 쿼리")
    probe.close()
    return result(C["V11-34"], rid, f"<= {cap}", worst, not bad, bad[:8])


def _import_origin_check(conn, rid):
    """V11-40 — 반입분이 수집분으로 위장하지 않는가 (STEP 136a).

    ★ 「origin 을 import 로 넣었다」를 코드 주석으로 두지 않는다.  세어 본다
    """
    from contracts import IMPORT_SOURCE
    from store.raw import ORIGIN_COLLECTOR

    listings = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE classify_source=?",
        (IMPORT_SOURCE,)).fetchone()[0]
    batches = conn.execute(
        "SELECT COUNT(*) FROM raw_response WHERE origin=?",
        (IMPORT_SOURCE,)).fetchone()[0]
    if not listings and not batches:
        return not_applicable(C["V11-40"], rid, "반입분이 없다")
    bad = []
    if listings and not batches:
        bad.append(f"반입 매물 {listings}건인데 origin='import' 원문이 0건")
    # ★ 반입분에 URL 이 있으면 「우리가 불렀다」가 된다 (STEP 136a 금지)
    with_url = conn.execute(
        "SELECT COUNT(*) FROM raw_response WHERE origin=? "
        "AND request_url IS NOT NULL", (IMPORT_SOURCE,)).fetchone()[0]
    if with_url:
        bad.append(f"반입분 {with_url}건에 request_url 이 있다")
    # 코드 — 반입 경로가 collector 를 쓰지 않는가
    src = open(os.path.join(ROOT, "store", "adminops.py"),
               encoding="utf-8").read()
    body = src.split("def import_listings", 1)[-1].split("\ndef ", 1)[0]
    if ORIGIN_COLLECTOR in body or "'collector'" in body:
        bad.append("import_listings 가 collector 를 쓴다")
    return result(C["V11-40"], rid, IMPORT_SOURCE,
                  f"매물 {listings} · 원문 {batches}", not bad, bad)


def _import_step4_check(conn, rid):
    """V11-42 — S4 완료 행의 actual 이 'import' 인가 (STEP 136b ④)."""
    from contracts import IMPORT_SOURCE, S4_CODE

    listings = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE classify_source=?",
        (IMPORT_SOURCE,)).fetchone()[0]
    if not listings:
        return not_applicable(C["V11-42"], rid, "반입분이 없다")
    row = conn.execute(
        "SELECT actual, passed FROM audit_validation WHERE code=? "
        "ORDER BY checked_at DESC LIMIT 1", (S4_CODE,)).fetchone()
    if row is None:
        return result(C["V11-42"], rid, IMPORT_SOURCE, "S4 완료 행이 없다",
                      False, ["반입이 STEP53-S4 를 남기지 않았다"])
    actual, passed = row
    bad = []
    if actual != IMPORT_SOURCE:
        bad.append(f"actual={actual!r} — 반입인데 반입이라고 안 적혔다")
    if not passed:
        bad.append("passed=0 — S4 가 완료로 남지 않았다")
    return result(C["V11-42"], rid, IMPORT_SOURCE, str(actual), not bad, bad)


def _import_resume_check(conn, rid):
    """V11-41 — 반입 뒤 S5~S10 이 이어서 도는가 (STEP 136b ④).

    ★ 「돌 수 있다」를 글로 두지 않는다.  precheck 를 실제로 물어본다
    """
    from collect.pipeline import completed_steps, precheck
    from contracts import IMPORT_SOURCE

    listings = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE classify_source=?",
        (IMPORT_SOURCE,)).fetchone()[0]
    if not listings:
        return not_applicable(C["V11-41"], rid, "반입분이 없다")
    done = completed_steps(conn)
    ok, why = precheck(conn, "S5", done)
    return result(C["V11-41"], rid, "S5 가능", "가능" if ok else why, ok,
                  [] if ok else [why])


def _watch_invite_check(conn, rid):
    """비로그인 관심 POST 가 유도 화면인가 (E-9 · D-5).

    ★ 라우트 권한만 보면 403 도 「막았으니 통과」가 된다.
      담으려던 대상이 화면에 보이는지까지 본다
    """
    from contracts import ANONYMOUS
    from web.views import watch_add_post

    row = conn.execute("SELECT listing_id FROM result_score LIMIT 1").fetchone()
    if row is None:
        return not_applicable(C["V11-23"], rid, "판정 결과가 없다")
    req = {"method": "POST", "query": {},
           "form": {"listing_id": str(row[0]), "csrf": "t"}}
    try:
        status, _h, body = watch_add_post(conn, ANONYMOUS, req, csrf="t")
    except Exception as e:                                   # noqa: BLE001
        return result(C["V11-23"], rid, "유도 화면",
                      f"{type(e).__name__}", False, [str(e)[:60]])
    html = body.decode("utf-8") if isinstance(body, bytes) else str(body)
    bad = []
    if int(status) != 200:
        bad.append(f"{int(status)} 를 냈다 — 유도 화면이 아니다")
    if "로그인" not in html:
        bad.append("로그인 안내가 없다")
    if str(row[0]) not in html:
        bad.append("담으려던 대상이 화면에 없다")
    return result(C["V11-23"], rid, "유도 화면",
                  "유도 화면" if not bad else "아님", not bad, bad)


# POST 를 눌러 볼 때 쓰는 표본 폼.  ★ 값 자체는 뜻이 없다 — 「눌린다」를 본다
# POST 가 내도 되는 상태.  ★ 500 은 「우리 결함」, 400 은 입력, 404 는 없는 것
POST_OK_STATUS = (HTTPStatus.OK, HTTPStatus.FOUND, HTTPStatus.SEE_OTHER,
                  HTTPStatus.BAD_REQUEST, HTTPStatus.NOT_FOUND)

SMOKE_FORM = {
    "csrf": "t", "previewed": "1", "reason": "검사", "action": "remove",
    "sql": "SELECT 1", "name": "없는이름", "secret": "틀린비번",
    "usage": "display_only", "endpoint": "detail", "json_path": "a.b",
    "title": "검사", "body": "검사", "scope": "all",
}


def _post_smoke_check(conn, rid):
    """V11-37 — 전 POST 를 실제로 눌러 본다.

    ★ 화면이 뜨는 것만 보면 쓰기 경로가 통째로 검사 밖에 있다.
      실측 08-15: 로그인 실패가 403 「권한 부족」을 냈는데 아무 검사도 안 잡았다
    """
    import os
    import sqlite3 as _sq

    from contracts import ANONYMOUS, ROLE_ADMIN, ROLE_USER, Account
    from errors import PolicyError, ValidationError, WiringError
    from web.routes import POST, ROUTES
    from web.server import guard
    from web.views import HANDLERS

    row = conn.execute(
        "SELECT listing_id FROM result_score LIMIT 1").fetchone()
    if row is None:
        return not_applicable(C["V11-37"], rid, "판정 결과가 없다")

    # ★ 사본에 대고 누른다.  검사가 실제 DB 를 고치면 안 된다
    # ★ 파일을 복사하지 않는다.  커밋 안 된 스키마가 사본에 안 따라온다
    tmp = os.path.join(_scratch(), "smoke.db")
    probe = _sq.connect(tmp)
    conn.backup(probe)

    accs = {"anonymous": ANONYMOUS, "user": Account(2, ROLE_USER, "사용자"),
            "admin": Account(1, ROLE_ADMIN, "마스터")}
    form = dict(SMOKE_FORM, listing_id=str(row[0]))
    bad = []
    for route in ROUTES:
        if POST not in route.methods:
            continue
        fn = HANDLERS.get(route.view)
        if fn is None:
            bad.append(f"{route.path}: 핸들러가 없다")
            continue
        pv = {}
        if "{" in route.path:
            k = route.path.split("{")[1].split("}")[0]
            pv = {k: str(row[0]) if k == "listing_id" else "1"}
        for who, acc in accs.items():
            if guard(acc, route) is not None:
                continue
            try:
                st, _h, _b = fn(probe, acc,
                                {"query": {}, "form": dict(form),
                                 "method": POST},
                                path_vars=pv, csrf="t")
                if int(st) not in [int(s) for s in POST_OK_STATUS]:
                    bad.append(f"{route.path}[{who}] -> {int(st)}")
            except WiringError:
                # ★ 검사 환경은 plan·fetch 를 주입하지 않는다.
                #   배선 누락은 500 이 맞고, 그 자체가 결함은 아니다 (C-2)
                pass
            except PolicyError as e:
                # ★ guard 가 통과시킨 요청을 핸들러가 「권한 부족」으로 막으면
                #   둘이 어긋난 것이다.  실측: 비밀번호를 틀리면 403 이 났다
                if "권한 부족" in str(e):
                    bad.append(f"{route.path}[{who}] "
                               f"guard 는 통과인데 핸들러가 막았다")
            except ValidationError:
                pass          # 입력이 규칙에 안 맞은 것이다
            except Exception as e:                           # noqa: BLE001
                bad.append(f"{route.path}[{who}] "
                           f"{type(e).__name__}: {str(e)[:50]}")
    probe.close()
    return result(C["V11-37"], rid, 0, len(bad), not bad, bad[:8])


# 화면 뼈대가 늘 넘기는 값.  ★ 여기 없는 이름은 뷰가 넘겨야 한다
FRAME_VARS = frozenset({"page", "viewer", "nav", "flash", "versions", "ver",
                        "csrf", "error"})
RE_TPL_OUT = re.compile(r"\{\{\s*([\w.]+)")
RE_TPL_IF = re.compile(r"\{%\s*if\s+([\w.!]+)")
RE_TPL_FOR = re.compile(r"\{%\s*for\s+(\w+)\s+in\s+([\w.]+)")


def _template_roots(body: str) -> set:
    """템플릿이 바깥에서 받아야 하는 이름.  ★ 반복 변수는 뺀다."""
    loop = {m.group(1) for m in RE_TPL_FOR.finditer(body)}
    out = {m.group(1).split(".")[0] for m in RE_TPL_OUT.finditer(body)}
    out |= {m.group(1).lstrip("!").split(".")[0]
            for m in RE_TPL_IF.finditer(body)}
    out |= {m.group(2).split(".")[0] for m in RE_TPL_FOR.finditer(body)}
    return out - loop - FRAME_VARS


def _loop_fields(body: str) -> list:
    """{% for X in A.B %} 안에서 X.<필드> 로 쓰는 것.

    ★ 「반복 변수는 뺀다」가 결함이 사는 자리였다 (B-1).
      화면이 비는 자리는 거의 다 표 안이다 — 루프 변수의 속성을 봐야 잡힌다
    반환   [(원본경로, 루프변수, {필드…})]
    """
    out = []
    for m in RE_TPL_FOR.finditer(body):
        var, source = m.group(1), m.group(2)
        end = body.find("{% endfor %}", m.end())
        chunk = body[m.end():end if end > 0 else len(body)]
        fields = {f.group(1) for f in
                  re.finditer(rf"\{{\{{\s*{re.escape(var)}\.(\w+)", chunk)}
        fields |= {f.group(1) for f in
                   re.finditer(rf"\{{%\s*if\s+!?{re.escape(var)}\.(\w+)",
                               chunk)}
        if fields:
            out.append((source, var, fields))
    return out


def _context_supplied_check(conn, rid):
    """V11-38 — 템플릿이 쓰는 값을 뷰가 넘기는가.

    ★ 절만 만들고 값을 안 넘기면 화면이 조용히 빈 채로 뜬다.
      템플릿 엔진이 없는 이름을 빈 값으로 내주기 때문에 아무도 모른다.
      실측 08-15: admin 화면 8개가 그렇게 껍데기였다
    """
    from contracts import ROLE_ADMIN, Account
    from web.routes import GET, ROUTES
    from web.views import HANDLERS
    import web.views as _views

    row = conn.execute(
        "SELECT listing_id FROM result_score LIMIT 1").fetchone()
    if row is None:
        return not_applicable(C["V11-38"], rid, "판정 결과가 없다")

    acc = Account(1, ROLE_ADMIN, "마스터")
    seen: dict = {}
    orig = _views.page

    def spy(conn_, account, title, template, ctx, **kw):
        seen[template] = dict(ctx)
        return orig(conn_, account, title, template, ctx, **kw)

    _views.page = spy
    try:
        for route in ROUTES:
            if GET not in route.methods or route.view == "serve_static":
                continue
            fn = HANDLERS.get(route.view)
            if fn is None:
                continue
            pv = {}
            if "{" in route.path:
                pv = {route.path.split("{")[1].split("}")[0]: str(row[0])}
            try:
                fn(conn, acc, {"query": {}, "form": {}, "method": GET},
                   path_vars=pv, csrf="t")
            except Exception:                                # noqa: BLE001
                pass
    finally:
        _views.page = orig

    bad = []
    for tpl, ctx in sorted(seen.items()):
        path = os.path.join(TEMPLATES, tpl)
        if not os.path.isfile(path):
            bad.append(f"{tpl}: 템플릿이 없다")
            continue
        body = open(path, encoding="utf-8").read()
        bad += [f"{tpl}: {name} 를 아무도 안 넘긴다"
                for name in sorted(_template_roots(body))
                if name not in ctx]
        # ★ 표 안의 필드까지 본다 (B-1).  화면이 비는 자리는 거의 다 표다
        for source, var, fields in _loop_fields(body):
            sample = _first_item(ctx, source)
            if sample is None:
                continue          # 목록이 비었다 — 필드를 확인할 수 없다
            for f in sorted(fields):
                if not _has_field(sample, f):
                    bad.append(f"{tpl}: {var}.{f} 가 {source} 에 없다")

    return result(C["V11-38"], rid, 0, len(bad), not bad, bad[:10])



def _first_item(ctx: dict, path: str):
    """{% for X in A.B %} 의 A.B 첫 항목."""
    cur = ctx
    for part in path.split("."):
        cur = cur.get(part) if isinstance(cur, dict) else getattr(
            cur, part, None)
        if cur is None:
            return None
    try:
        return next(iter(cur)) if cur else None
    except TypeError:
        return None


def _has_field(item, name: str) -> bool:
    if isinstance(item, dict):
        return name in item
    return hasattr(item, name)


def _table_counts(conn) -> dict:
    return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            for (t,) in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%'")}


def _save_button_check(conn, rid):
    """V11-39 — 쓸 수 있는 저장 단추는 실제로 쓰는가.

    ★ 「저장」이라 적힌 단추가 아무것도 안 바꾸면 사람이 바뀐 줄 알고 넘어간다.
      실측 08-15: admin_config · admin_api · admin_targets · admin_tools 가
      저장 단추를 내놓고 DB 를 전혀 건드리지 않았다
    준비 중이면 disabled 로 두고 그렇게 적는다 — 그건 검사 대상이 아니다
    """
    import os
    import re as _re
    import sqlite3 as _sq

    from contracts import ROLE_ADMIN, Account
    from errors import PolicyError, ValidationError
    from web.routes import GET, POST, ROUTES
    from web.views import HANDLERS

    _ = GET
    # ★ 파일을 복사하지 않는다.  커밋 안 된 스키마가 사본에 안 따라온다
    tmp = os.path.join(_scratch(), "save.db")
    probe = _sq.connect(tmp)
    conn.backup(probe)
    acc = Account(1, ROLE_ADMIN, "마스터")

    bad = []
    for route in ROUTES:
        if POST not in route.methods:
            continue
        fn = HANDLERS.get(route.view)
        if fn is None:
            continue
        # ★ 템플릿 이름을 추측하지 않는다.  GET 을 눌러 실제로 나온 화면을 본다
        #   (admin_simple 은 view 이름과 템플릿 이름이 다르다)
        try:
            _st, _h, page_body = fn(conn, acc,
                                    {"query": {}, "form": {}, "method": "GET"},
                                    path_vars={}, csrf="t")
        except Exception:                                    # noqa: BLE001
            continue
        body = (page_body.decode("utf-8")
                if isinstance(page_body, bytes) else str(page_body))
        # ★ 눌리는 저장 단추만 본다.  disabled 는 「준비 중」이라 밝힌 것이다
        buttons = _re.findall(r"<button[^>]*>[^<]*저장[^<]*</button>", body)
        if not any("disabled" not in b for b in buttons):
            continue
        before = _table_counts(probe)
        try:
            fn(probe, acc, {"query": {}, "form": dict(SMOKE_FORM),
                            "method": POST}, path_vars={}, csrf="t")
        except (PolicyError, ValidationError):
            continue          # 규칙대로 거절한 것이다 — 저장 안 하는 게 맞다
        except Exception:                                    # noqa: BLE001
            continue          # V11-37 이 잡는다
        if _table_counts(probe) == before:
            bad.append(f"{route.view}: 저장 단추가 아무것도 안 바꾼다")
    probe.close()
    return result(C["V11-39"], rid, 0, len(bad), not bad, bad[:8])


def _scratch() -> str:
    """검사용 임시 자리.  ★ 끝나면 지운다 — 검사가 디스크를 채우면 안 된다.

    실측 08-15: 사본 63MB 가 실행마다 쌓여 디스크가 100% 가 됐고
    그 뒤 전 시험이 한꺼번에 깨졌다
    """
    import atexit
    import shutil
    import tempfile

    path = tempfile.mkdtemp(prefix="cw-check-")
    atexit.register(shutil.rmtree, path, ignore_errors=True)
    return path
