# -*- coding: utf-8 -*-
"""14장 표현 계층 시험 — 템플릿 · 라우팅.

지시서   STEP 142 (라우팅 표) · STEP 143 (템플릿)
사용     python3 tests/test_web.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contracts import ROLE_ADMIN, ROLE_ANONYMOUS, ROLE_USER  # noqa: E402
from web.routes import GET, POST, ROUTES, match  # noqa: E402
from web.template import RAW_ALLOW, render_str  # noqa: E402

FAIL: list[str] = []


def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{'  ' + detail if detail else ''}")
    if not ok:
        FAIL.append(name)


# ── STEP 142 라우팅 ──────────────────────────────────────────────────
def test_routes() -> None:
    check("★ 전 Route 에 role 이 지정됐다 (V11-03)",
          all(r.role in (ROLE_ANONYMOUS, ROLE_USER, ROLE_ADMIN)
              for r in ROUTES))
    check("★ 표에 없는 경로는 404 — 추측하지 않는다",
          match("/없는경로", GET)[0] is None)
    check("메서드가 다르면 404", match("/listings", POST)[0] is None)

    r, var = match("/why/42", GET)
    check("경로 변수 하나", r.view == "view_why" and var == {"listing_id": "42"})
    check("★ 변수 경로는 슬래시를 안 넘는다",
          match("/why/42/extra", GET)[0] is None)
    check("★ {path} 만 슬래시를 품는다 (정적 파일)",
          match("/static/css/app.css", GET)[1] == {"path": "css/app.css"})

    admin = [r for r in ROUTES if r.path.startswith("/admin")]
    check("★ /admin 전건이 admin 권한", all(r.role == ROLE_ADMIN for r in admin),
          str([r.path for r in admin if r.role != ROLE_ADMIN]))
    check("정규식 라우팅을 쓰지 않는다",
          not any("(" in r.path or "*" in r.path for r in ROUTES))

    paths = [r.path for r in ROUTES]
    check("경로가 중복되지 않는다", len(paths) == len(set(paths)))

    # ★ 준비 중을 표에서 빼지 않는다.  빼면 계획이 사라진다 (STEP 142)
    from web.routes import BUILT, PENDING

    built = [r.view for r in ROUTES if r.status == BUILT]
    # ★ 수를 손으로 적지 않는다.  지시서 표가 정본이다 (V11-12)
    from validate.v11_web import _spec_routes

    spec = _spec_routes() or []
    check("★ Route 수 == 지시서 표 행 수",
          len(ROUTES) == len(spec), f"소스 {len(ROUTES)} · 표 {len(spec)}")
    check("★ 전 Route 가 구현됐다 (2026-08-14)",
          len(built) == len(ROUTES), f"{len(built)}/{len(ROUTES)}")
    # ★ 준비 중이 생기면 표에 남는다.  빼면 계획이 사라진다 (STEP 142)
    check("상태는 HANDLERS 가 정본이다 — 표와 코드가 안 어긋난다",
          all(r.status in (BUILT, PENDING) for r in ROUTES))

    from web.views import HANDLERS

    missing = [r.view for r in ROUTES
               if r.status == BUILT and r.view != "serve_static"
               and r.view not in HANDLERS]
    check("★ 「구현」이라 적힌 것은 실제로 있다", not missing, str(missing))


# ── STEP 143 템플릿 ─────────────────────────────────────────────────
def test_template() -> None:
    check("★ {{ }} 는 항상 이스케이프한다",
          render_str("{{ a }}", {"a": "<script>x</script>"})
          == "&lt;script&gt;x&lt;/script&gt;")
    check("없는 값은 빈 문자열", render_str("[{{ x }}]", {}) == "[]")
    check("중첩 경로", render_str("{{ a.b }}", {"a": {"b": 7}}) == "7")

    check("반복", render_str("{% for r in xs %}[{{ r }}]{% endfor %}",
                           {"xs": ["A", "B"]}) == "[A][B]")
    check("빈 목록은 아무것도 안 낸다",
          render_str("{% for r in xs %}X{% endfor %}", {"xs": []}) == "")
    check("조건 · else",
          render_str("{% if v %}Y{% else %}N{% endif %}", {"v": 0}) == "N")
    check("부정 조건", render_str("{% if !v %}N{% endif %}", {"v": 0}) == "N")
    # ★ 중첩 for — 정규식 non-greedy 가 깨졌던 자리 (실측)
    check("★ 중첩 반복 — 안쪽 endfor 를 바깥 것으로 잡지 않는다",
          render_str("{% for r in xs %}A{% for c in r.cs %}[{{ c }}]"
                     "{% endfor %}B{% endfor %}",
                     {"xs": [{"cs": ["x", "y"]}, {"cs": []}]}) == "A[x][y]BAB")
    try:
        render_str("{% for r in xs %}X", {"xs": [1]})
        check("★ 짝 없는 for 는 거부", False)
    except ValueError:
        check("★ 짝 없는 for 는 거부", True)

    check("중첩 반복+조건",
          render_str("{% for r in xs %}{% if r %}[{{ r }}]{% endif %}"
                     "{% endfor %}", {"xs": ["A", "", "B"]}) == "[A][B]")

    # ★ 원문 삽입은 허용 목록 안에서만 (V11-05)
    try:
        render_str("{{! evil }}", {"evil": "<script>"})
        check("★ 허용 목록 밖 원문 삽입은 거부", False)
    except ValueError as e:
        check("★ 허용 목록 밖 원문 삽입은 거부", "허용 목록" in str(e))
    ok = render_str("{{! page.body_html }}",
                    {"page": {"body_html": "<b>x</b>"}})
    check("허용 목록 안은 원문 그대로", ok == "<b>x</b>")
    check("허용 목록이 좁다", len(RAW_ALLOW) <= 3, str(sorted(RAW_ALLOW)))


def test_no_logic_in_template() -> None:
    """★ 템플릿에 산술 연산이 없다 (V11-04)."""
    import glob
    import re

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bad = []
    for path in glob.glob(os.path.join(root, "web", "templates", "*.html")):
        body = open(path, encoding="utf-8").read()
        for m in re.finditer(r"\{\{[^}]*[+\-*/%][^}]*\}\}", body):
            bad.append(f"{os.path.basename(path)}: {m.group(0)[:30]}")
    check("★ 템플릿에 산술 연산이 없다", not bad, str(bad[:2]))


# ── STEP 145~148 세션 · CSRF · 정적 · 오류 ─────────────────────────
def test_static_escape() -> None:
    """★ 경로 탈출로 secrets/ 가 읽히면 안 된다 (V11-06)."""
    from web.session import static_path

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    css = os.path.join(root, "web", "static", "app.css")
    check("정상 파일은 열린다", static_path("app.css") == os.path.realpath(css))
    for bad in ("../secrets/plate_hmac.key", "../../etc/passwd",
                "/etc/passwd", "....//secrets/x", "없는.css"):
        check(f"★ 거부 — {bad[:28]}", static_path(bad) is None)


def test_session_cookie() -> None:
    """★ 쿠키를 고쳐 권한을 올릴 수 있으면 안 된다 (V11-07)."""
    from web.session import csrf_ok, new_csrf, read_cookie, set_cookie

    c = set_cookie("cw_session", "abc123", 3600)
    check("★ 쿠키에 role 이 없다", "role" not in c and "admin" not in c, c)
    check("HttpOnly · SameSite", "HttpOnly" in c and "SameSite=Lax" in c)
    check("Secure 는 HTTPS 일 때만",
          "Secure" not in c and "Secure" in set_cookie("s", "v", 1, True))
    check("쿠키를 읽는다",
          read_cookie("a=1; cw_session=abc123", "cw_session") == "abc123")

    tok = new_csrf()
    check("★ CSRF 일치만 통과", csrf_ok(tok, tok))
    check("불일치 거부", not csrf_ok(tok, "other"))
    check("빈 토큰 거부", not csrf_ok(None, tok) and not csrf_ok(tok, None))


def test_error_page() -> None:
    """★ 스택 트레이스를 화면에 내지 않는다 (V11-10)."""
    from errors import PolicyError, ValidationError
    from web.context import (
        FORBIDDEN, HTTP_BAD_REQUEST, HTTP_FORBIDDEN, HTTP_SERVER_ERROR,
        NOT_FOUND, error_page,
    )

    check("404 에 다음 행동이 있다", "/listings" in NOT_FOUND.action)
    check("403 에 다음 행동이 있다", "/login" in FORBIDDEN.action)

    p = error_page(PolicyError("권한 부족: user < admin", step="STEP 126"))
    check("PolicyError → 403", p.status == HTTP_FORBIDDEN)
    check("★ 내부 표기 [step=] 를 화면에 안 낸다", "step=" not in p.reason,
          p.reason)

    p = error_page(ValidationError("저당 여부를 확인하지 못했습니다",
                                   step="STEP 82"))
    check("도메인 예외 → 400 + 사유", p.status == HTTP_BAD_REQUEST
          and "저당" in p.reason)

    p = error_page(RuntimeError("list index out of range"), "r20260811")
    check("★ 그 외 → 500.  내부 메시지를 안 낸다",
          p.status == HTTP_SERVER_ERROR and "index" not in p.reason, p.reason)
    check("★ 500 에는 run_id 를 낸다", "r20260811" in p.action)


def test_layout() -> None:
    """★ 전 화면이 같은 것을 낸다 (STEP 144)."""
    from web.context import Banner, NOT_FOUND, PageContext
    from web.template import render

    class V:
        role, display_name = "admin", "마스터"
        can_watch = can_admin = True

    page = PageContext(
        title="오류", body_html="", viewer=V(),
        menu=[{"label": "매물", "path": "/listings", "group": None,
               "locked": False}],
        banners=[Banner("unclassified", "미분류 3건", "모아서 분류한다")],
        flashes=["저장했습니다"], calc_version="c1", dict_version="d1",
        parse_version="p1", run_id="r1", generated_at="2026-08-11",
        csrf_token="t")
    h = render("_error.html", {"page": page, "err": NOT_FOUND})

    for must in ("calc c1", "dict d1", "parse p1", "run r1"):
        check(f"★ 꼬리에 버전 — {must}", must in h)
    check("배너는 있을 때만 낸다", "미분류 3건" in h)
    check("flash 를 낸다", "저장했습니다" in h)
    check("본문 블록이 채워진다", "그런 화면이 없습니다" in h)
    check("★ 로그아웃 폼에 CSRF 가 있다",
          'name="csrf"' in h and 'value="t"' in h)


# ── STEP 152 표시 필터 ─────────────────────────────────────────────
def test_filters() -> None:
    """★ 필터는 표시만 한다.  반올림으로 값을 바꾸지 않는다."""
    check("원 → 만", render_str("{{ p | won }}", {"p": 31200000}) == "3,120만")
    check("억 단위", render_str("{{ p | won }}", {"p": 168300000})
          == "1억 6,830만")
    check("None 은 —", render_str("{{ p | won }}", {"p": None}) == "—")
    check("주행", render_str("{{ m | km }}", {"m": 43705}) == "43,705km")
    check("비율", render_str("{{ r | pct }}", {"r": 0.139}) == "13.9%")
    check("날짜는 자르기만",
          render_str("{{ d | date }}", {"d": "2026-08-11T03:11:00Z"})
          == "2026-08-11")
    try:
        render_str("{{ x | 없는필터 }}", {"x": 1})
        check("★ 없는 필터는 거부", False)
    except ValueError:
        check("★ 없는 필터는 거부", True)


# ── STEP 149 판정 결과가 없을 때 ────────────────────────────────────
def test_empty_state() -> None:
    """★ 빈 표를 내지 않는다 (V11-11)."""
    import tempfile

    from contracts import ANONYMOUS, Account
    from store.raw import open_db
    from web.app import empty_state

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    conn = open_db(os.path.join(tempfile.mkdtemp(), "web.db"),
                   os.path.join(root, "sql", "ddl"))
    admin = Account(1, ROLE_ADMIN, "마스터")

    b = empty_state(conn, admin)
    check("★ 빈 DB → 안내가 나온다", b is not None and "수집" in b.text)
    check("관리자에게는 실행 명령", "collect" in b.action, b.action)
    check("비로그인에게는 요청 안내",
          "요청" in empty_state(conn, ANONYMOUS).action)

    conn.execute("INSERT INTO core_listing(site,source_id,status,first_seen,"
                 "last_seen,row_status) VALUES ('encar','1','active','t','t',"
                 "'ok')")
    conn.commit()
    b = empty_state(conn, admin)
    check("수집 후에는 판정 안내", "판정" in b.text, b.text)


def test_menu_by_role() -> None:
    from contracts import ANONYMOUS, Account
    from web.app import menu_items

    n_anon = len(menu_items(ANONYMOUS))
    n_user = len(menu_items(Account(2, ROLE_USER, "u")))
    n_admin = len(menu_items(Account(1, ROLE_ADMIN, "a")))
    check("★ 역할이 오를수록 메뉴가 는다", n_anon < n_user < n_admin,
          f"{n_anon} < {n_user} < {n_admin}")
    check("★ 비로그인 메뉴에 /admin 이 없다",
          not any(m["path"].startswith("/admin")
                  for m in menu_items(ANONYMOUS)))
    check("메뉴는 라우팅 표에서 나온다",
          all(m["path"] for m in menu_items(Account(1, ROLE_ADMIN, "a"))))


# ── STEP 147 · 150 폼과 접근 제어 ───────────────────────────────────
def test_guard_and_csrf() -> None:
    from contracts import ANONYMOUS, Account
    from errors import PolicyError
    from web.app import check_post, redirect
    from web.context import FORBIDDEN, HTTP_SEE_OTHER
    from web.routes import match
    from web.server import guard

    admin_route, _ = match("/admin", GET)
    check("★ anonymous 가 /admin → 403",
          guard(ANONYMOUS, admin_route) is FORBIDDEN)
    check("admin 은 통과",
          guard(Account(1, ROLE_ADMIN, "a"), admin_route) is None)

    watch, _ = match("/watch", GET)
    check("user 가 /watch → 통과",
          guard(Account(2, ROLE_USER, "u"), watch) is None)
    check("anonymous 가 /watch → 403",
          guard(ANONYMOUS, watch) is FORBIDDEN)

    # ★ 임시 비밀번호로는 다른 화면을 못 본다 (STEP 146)
    tmp = Account(1, ROLE_ADMIN, "a", must_change_secret=True)
    check("★ must_change_secret 이면 막힌다",
          guard(tmp, admin_route) is not None)
    check("로그인 화면은 열린다", guard(tmp, match("/login", GET)[0]) is None)
    # ★ 바꾸는 화면 자체가 막히면 못 바꾼다 (실측)
    check("★ 비밀번호 변경 화면은 열린다",
          guard(tmp, match("/password", GET)[0]) is None)

    try:
        check_post({"form": {}}, "tok")
        check("★ CSRF 없는 POST 는 거부", False)
    except PolicyError:
        check("★ CSRF 없는 POST 는 거부", True)
    check("일치하면 통과", check_post({"form": {"csrf": "tok"}}, "tok") is None)

    status, headers, body = redirect("/admin/scoring", "저장했습니다")
    check("★ POST 후 303 리다이렉트", status == HTTP_SEE_OTHER
          and headers["Location"] == "/admin/scoring" and body == b"")


# ── STEP 151 화면 시험 — 서버 함수를 직접 부른다 ────────────────────
def _call(app, route, account, req):
    """guard 를 그 역할로 통과시켜 화면만 부른다."""
    import web.app as _wa

    original = _wa.make_app
    _ = original
    from web.views import HANDLERS as _H
    import sqlite3 as _sq

    conn = _sq.connect(app["db_path"])
    try:
        return _H[route.view](conn, account, req, path_vars={
            "listing_id": "1"}, root=app["root"])
    finally:
        conn.close()


def test_screens_render() -> None:
    """★ 브라우저 자동화를 쓰지 않는다.  서버 함수를 직접 부른다."""
    import sqlite3
    import tempfile

    from contracts import ANONYMOUS, Account
    from store.raw import open_db
    from web.app import make_app
    from web.routes import match
    from web.views import HANDLERS

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db = os.path.join(tempfile.mkdtemp(), "web.db")
    open_db(db, os.path.join(root, "sql", "ddl")).close()
    app = make_app(db, root)

    # 1 · 3  빈 DB 에서도 전 화면이 안내를 낸다 (STEP 149).
    #   ★ 권한이 있는 역할로 부른다 — 없는 역할은 guard 가 막는 것이 정상이다
    from web.app import _Denied

    ok_n = 0
    for view in sorted(HANDLERS):
        route = next((r for r in ROUTES if r.view == view), None)
        if route is None or GET not in route.methods:
            continue
        # ★ 권한이 있는 역할로 부른다.  없는 역할은 guard 가 막는 것이 정상이다
        who = {ROLE_ADMIN: Account(1, ROLE_ADMIN, "마스터"),
               ROLE_USER: Account(2, ROLE_USER, "사용자")}.get(
                   route.role, ANONYMOUS)
        req = {"query": {}, "form": {}, "cookie": None, "method": GET}
        try:
            status, _h, body = _call(app, route, who, req)
        except _Denied as e:
            check(f"{view} — 예상 밖 거부", False, e.page.title)
            continue
        html = body.decode("utf-8")
        # ★ 없는 매물을 짚는 화면은 404 가 정상이다 (E-8).
        #   200 으로 내면 링크가 살아 있는 줄 안다 — 안내는 그대로 나온다
        want = (404,) if "{" in route.path else (200,)
        check(f"★ 빈 DB — {view} 가 뜬다",
              status in want and "<h1>" in html, f"{status}")
        check(f"버전 표시 — {view}", 'class="ver"' in html)
        ok_n += 1
    from web.routes import GET as _G

    want = len([r for r in ROUTES if _G in r.methods
                and r.view in HANDLERS])
    check("★ 전 GET 화면을 돌았다", ok_n == want, f"{ok_n}/{want}")

    # ★ 「준비 중」이 남아 있지 않다 — 전 화면이 구현됐다 (D-3).
    #   빈 자리 표시가 남으면 다음 사람이 「아직 없구나」로 오해한다
    from web.routes import BUILT
    from web.views import HANDLERS

    # serve_static 은 서버가 직접 다룬다 — HANDLERS 에 없는 것이 정상이다
    missing = sorted(r.view for r in ROUTES
                     if r.status == BUILT and r.view not in HANDLERS
                     and r.view != "serve_static")
    check("★ BUILT 로 표시된 화면에 핸들러가 있다", not missing, str(missing))

    # 4  경로 탈출 · 권한

    static_route = next(r for r in ROUTES if r.view == "serve_static")
    try:
        app["resolve"](static_route, {"path": "../secrets/x"},
                       {"query": {}, "form": {}, "cookie": None,
                        "method": GET})
        check("★ 경로 탈출 거부", False)
    except _Denied as e:
        check("★ 경로 탈출 거부", e.page.status == 404)

    admin_route = next(r for r in ROUTES if r.path == "/admin")
    try:
        app["resolve"](admin_route, {}, {"query": {}, "form": {},
                                         "cookie": None, "method": GET})
        check("★ anonymous 가 /admin → 거부", False)
    except _Denied as e:
        check("★ anonymous 가 /admin → 거부", e.page.status == 403)

    _ = (ANONYMOUS, Account, sqlite3, match)


# ── 시안 대조 (ref/screens 가 정본) ─────────────────────────────────
def test_sketch_match() -> None:
    """★ 시안이 화면 규격의 정본이다.  코드가 시안보다 먼저 가지 않는다."""
    import subprocess

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    r = subprocess.run([sys.executable,
                        os.path.join(root, "tools", "check_screens.py")],
                       capture_output=True, text=True, cwd=root)
    ok = r.returncode == 0
    check("★ 화면이 시안 핵심 문구를 담는다", ok,
          " / ".join(x.strip() for x in r.stdout.splitlines()
                     if "✗" in x)[:80])


# ── 계정 정책 (13장 STEP 126) ───────────────────────────────────────
def test_account_policy() -> None:
    """★ 관리자를 0명으로 만들 수 없다.  중지는 삭제가 아니다."""
    import tempfile

    from errors import PolicyError
    from store.admin import (
        account_rows, admin_count, create_account, set_disabled, set_role,
    )
    from store.raw import open_db

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    conn = open_db(os.path.join(tempfile.mkdtemp(), "acc.db"),
                   os.path.join(root, "sql", "ddl"))
    create_account(conn, "마스터", ROLE_ADMIN, "t")
    check("관리자 1명", admin_count(conn) == 1)

    try:
        set_role(conn, 1, ROLE_USER, "t")
        check("★ 마지막 관리자 역할을 못 내린다", False)
    except PolicyError:
        check("★ 마지막 관리자 역할을 못 내린다", True)
    try:
        set_disabled(conn, 1, True, "t")
        check("★ 마지막 관리자를 못 중지한다", False)
    except PolicyError:
        check("★ 마지막 관리자를 못 중지한다", True)

    create_account(conn, "둘째", ROLE_ADMIN, "t")
    set_disabled(conn, 1, True, "t")
    rows = {r["account_id"]: r for r in account_rows(conn)}
    check("관리자가 둘이면 중지된다", rows[1]["disabled"])
    check("★ 중지는 삭제가 아니다 — 행이 남는다", len(rows) == 2)
    check("★ 비밀번호 해시를 화면에 안 낸다",
          all("secret_hash" not in r for r in rows.values()))


if __name__ == "__main__":
    print("14장 표현 계층 — 템플릿 · 라우팅")
    test_routes()
    test_template()
    test_no_logic_in_template()
    test_static_escape()
    test_session_cookie()
    test_error_page()
    test_layout()
    test_filters()
    test_empty_state()
    test_menu_by_role()
    test_guard_and_csrf()
    test_screens_render()
    test_sketch_match()
    test_account_policy()
    print()
    print("결과:", "통과" if not FAIL else "실패 — " + " / ".join(FAIL))
    sys.exit(1 if FAIL else 0)
