# -*- coding: utf-8 -*-
"""화면 조립 (14장 STEP 144 · 147 · 149).

지시서   STEP 149 (판정 결과가 없을 때) · 147 (폼) · 152 (경계)
근거     ★ 10장·13장 화면 함수는 그대로다.  14장이 그것을 감싼다
금지     view_* 시그니처를 바꾸는 것
         빈 표를 내는 것 — 「무엇이 없고 무엇을 하면 되는가」를 낸다
"""
from __future__ import annotations

import os
import sqlite3

from contracts import ANONYMOUS, ROLE_ADMIN, ROLE_USER
from web.context import Banner, HTTP_OK, HTTP_SEE_OTHER, PageContext
from web.routes import ROUTES
from web.session import csrf_for, csrf_ok, new_csrf

FLASH_KEY = "flash"


def menu_items(account) -> list[dict]:
    """라우팅 표에서 메뉴를 만든다.  ★ 표가 정본이다 (STEP 142)."""
    from contracts import ROLE_RANK

    rank = ROLE_RANK.get(getattr(account, "role", "anonymous"), 0)
    out = []
    for r in ROUTES:
        # ★ POST 전용 · 경로 변수 · 인증은 메뉴가 아니다
        if r.var or r.path in ("/", "/login", "/logout", "/join",
                               "/password"):
            continue
        if "GET" not in r.methods:
            continue
        if ROLE_RANK[r.role] > rank:
            continue
        out.append({"label": _label(r.path), "path": r.path,
                    "tip": _tip(r.path),
                    "group": r.menu, "locked": False})
    return out


LABELS = {
    "/listings": "매물", "/recommend": "후보", "/compare": "비교",
    "/market": "시세", "/dealers": "딜러", "/watch": "관심",
    "/notready": "미판정", "/admin": "관리",
    "/admin/run": "실행 지시", "/admin/audit": "감사",
    "/admin/scoring": "배점", "/admin/targets": "차종",
    "/admin/registry": "등록부", "/admin/config": "설정",
    "/admin/users": "사용자", "/admin/query": "쿼리", "/admin/api": "API", "/admin/tools": "도구",
    "/admin/docs": "문서", "/admin/requests": "개발 요청",
    # ★ 13장 STEP 138 메뉴표가 정본이다.  표에 있는 이름을 그대로 쓴다 —
    #   빠지면 메뉴에 경로가 그대로 나온다 (실측 08-16 · V11-54)
    "/admin/import": "목록 반입", "/admin/collect": "브라우저 수집",
    "/admin/dict": "사전 확정", "/admin/status": "진행 모니터",
    # ★ 실측 08-19 — 메뉴에 「/reports」가 경로 그대로 떴다.
    #   :53 주석이 이미 경고했는데 또 반복됐다 — V11-54 가 관리 메뉴만 봤다.
    #   이제 STEP 142a 표까지 본다 (개정 396)
    "/reports": "리포트",
}


# 메뉴 설명.  ★ 13장 STEP 138 메뉴표의 「내용」 칸이 정본이다.
#   이름만으로는 무엇을 하는 곳인지 모른다 (STEP 149p · 마스터 지적 ①)
MENU_TIPS = {
    "/listings": "판정한 매물을 표로 봅니다. 값을 누르면 그 조건으로 걸러집니다",
    "/recommend": "E · 미판정을 뺀 후보. 점수순이 아니라 예산·확인 못 한 축을 함께 봅니다",
    "/compare": "고른 매물을 축별로 나란히 놓습니다. 분모가 다르면 총점을 비교하지 않습니다",
    "/market": "차종별 시세 — 가격 분포 · 연식별 중앙값 · 감가 계수 이력",
    "/dealers": "딜러 정직도와 보유 차종. ★ 차량 판정에는 들어가지 않습니다",
    "/watch": "관심으로 담은 매물과 조건 알림",
    "/notready": "아직 판정하지 못한 것과 그 이유",
    "/admin": "관리 현황 · 큐 상태 · 미분류 · 대기 요청",
    "/admin/run": "수집·재계산 실행 지시와 큐 (STEP 132)",
    "/admin/status": "지금 도는 것을 지켜봅니다. 읽기 전용입니다 (STEP 136f)",
    "/admin/audit": "설정 변경 · 쿼리 · 작업 이력 조회 (STEP 138a)",
    "/admin/import": "목록을 파일·붙여넣기로 반입합니다 (STEP 136a · 136b)",
    "/admin/collect": "사용자 회선으로 API 를 부릅니다 (STEP 136c)",
    "/admin/dict": "같은 값을 같은 것으로 인정하는 규칙을 확정합니다 (STEP 136e)",
    "/admin/scoring": "배점 조정 + 미리보기 (STEP 128 · 129)",
    "/admin/targets": "차종 추가 · 수정 (STEP 130)",
    "/admin/registry": "원문 필드 분류 (STEP 131)",
    "/admin/config": "config 전체 편집과 이력 (STEP 127)",
    "/admin/users": "사용자 승인과 역할",
    "/admin/query": "조회 쿼리 (STEP 133)",
    "/admin/api": "API 를 직접 불러 원문을 봅니다 (STEP 134)",
    "/admin/tools": "관리 도구 (STEP 135)",
    "/admin/docs": "지시서 문서 뷰어 (STEP 136)",
    "/admin/requests": "개발 요청 (STEP 137)",
    "/reports": "낸 리포트를 화면에서 읽고 내려받습니다",
}


def _tip(path: str) -> str:
    """메뉴 설명.  ★ 없으면 빈 문자다 — 지어내지 않는다."""
    return MENU_TIPS.get(path, "")


def _label(path: str) -> str:
    """★ 이름이 없으면 경로를 그대로 낸다 — 그것이 눈에 띄어야 고친다.
    검사는 V11-54 가 한다 (13장 STEP 138 메뉴표와 대조)."""
    return LABELS.get(path, path)


# 단위 환산 (2장 상수표 · V4-13)
SECONDS_PER_DAY = 86_400


# ── STEP 149 판정 결과가 없을 때 ────────────────────────────────────
def empty_state(conn: sqlite3.Connection, account) -> Banner | None:
    """★ 빈 표를 내지 않는다.  무엇이 없고 무엇을 하면 되는가를 낸다.

    ★ 조회는 store.state_counts 가 한다.  화면에 SQL 을 두지 않는다 (V11-01)
    """
    from store.core import state_counts

    # ★ 한 요청에 여러 번 부른다 — 부분 템플릿과 뼈대가 각각 부른다.
    #   그때마다 4쿼리를 돌면 화면마다 헛되이 쓴다 (V11-34 · B-2)
    n = getattr(conn, "_cw_state", None)
    if n is None:
        n = state_counts(conn)
        try:
            conn._cw_state = n
        except AttributeError:
            pass
    if n["listings"] == 0:
        act = ("run.py collect --target <차종>" if account.role == ROLE_ADMIN
               else "관리자에게 수집을 요청하십시오")
        return Banner("pending", "아직 수집하지 않았습니다", act)
    # ★ 조용히 옛 목록으로 판정하지 않는다 (STEP 136i · 개정 316).
    #   미분류보다 먼저 낸다 — 목록이 멈추면 그 뒤 숫자가 다 옛것이다
    stale = _list_stale(n.get("list_at"))
    if stale is not None:
        return Banner(
            "stale",
            f"엔카 목록이 {stale:.0f}일째 갱신되지 않았습니다 — "
            "그동안의 가격 변동을 알 수 없습니다",
            "브라우저 수집을 눌러 주십시오  (/admin/collect)")
    if n["unclassified"]:
        return Banner("unclassified", "등록부에 미분류가 있습니다",
                      "판정에 쓰는 경로면 멈춥니다  (/notready)")
    if n["scores"] == 0:
        return Banner("pending", "판정 결과가 아직 없습니다",
                      "S9~S10 을 실행하면 등급이 나옵니다")
    if n["not_rated"] == n["scores"]:
        return Banner("pending", "분모가 부족해 등급을 매기지 않았습니다",
                      "축별 미확정을 확인하십시오  (/notready)")
    return None


def _list_stale(at: str | None) -> float | None:
    """엔카 목록이 며칠째 안 들어왔나 (STEP 136i).

    ★ 엔카 목록은 407 이라 자동이 아니다.  마스터가 눌러야 한다 —
      그러니 오래되면 말해야 한다.  조용히 옛것으로 판정하지 않는다
    """
    import json as _json
    from datetime import datetime as _dt

    if not at:
        return None
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, "config", "web.json"),
              encoding="utf-8") as f:
        limit = float(_json.load(f)["list_stale_days"])
    try:
        then = _dt.fromisoformat(at)
    except ValueError:
        return None
    days = (_dt.now(then.tzinfo) - then).total_seconds() / SECONDS_PER_DAY
    return days if days > limit else None


_STATIC_VERSION: dict[str, str] = {}


def static_version(name: str = "app.css") -> str:
    """정적 파일의 내용 지문 (V11-82).

    ★ run_id 를 쓰지 않는다 — 수집할 때마다 바뀌어 CSS 가 그대로여도
      전부 다시 받게 된다.  내용이 바뀔 때만 바뀌어야 한다.
    ★ 한 번 읽고 기억한다.  화면마다 파일을 여는 것은 낭비다
    """
    import hashlib
    import json as _j
    import os as _o

    got = _STATIC_VERSION.get(name)
    if got is None:
        root = _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__)))
        try:
            # 지문 길이는 표시 정책이라 config 에 둔다 (S14).
            # ★ 충돌만 안 나면 된다 — 주소를 짧게 둔다
            with open(_o.path.join(root, "config", "web.json"),
                      encoding="utf-8") as f:
                n = int(_j.load(f)["static_fingerprint_chars"])
            with open(_o.path.join(root, "web", "static", name), "rb") as f:
                got = hashlib.sha256(f.read()).hexdigest()[:n]
        except (OSError, KeyError, ValueError):
            got = ""          # 못 읽어도 화면은 떠야 한다
        _STATIC_VERSION[name] = got
    return got


def build_page(conn, account, title: str, body_html: str, *,
               csrf: str = "", flashes=None, run_id: str = "",
               calc_version: str = "", dict_version: str = "",
               parse_version: str = "", refresh_sec: int = 0,
               screen: str = "") -> PageContext:
    """전 화면이 같은 것을 낸다 (STEP 144)."""
    from report.screens.build import viewer_state

    banner = empty_state(conn, account)
    return PageContext(
        title=title, body_html=body_html, viewer=viewer_state(account),
        menu=menu_items(account), banners=[banner] if banner else [],
        flashes=list(flashes or []), calc_version=calc_version,
        dict_version=dict_version, parse_version=parse_version,
        run_id=run_id,
        generated_at=_display_now(),
        csrf_token=csrf, refresh_sec=refresh_sec, screen=screen,
        static_version=static_version())


# ── STEP 147 폼 ─────────────────────────────────────────────────────
def check_post(req: dict, expected_csrf: str | None) -> None:
    """★ 전 POST 에 CSRF 를 요구한다.  불일치면 403 (STEP 147)."""
    from errors import PolicyError

    got = req.get("form", {}).get("csrf")
    if not csrf_ok(expected_csrf, got):
        # ★ 「저장 403」만 내면 원인을 모른다 (개정 308).  무엇이 어긋났는지 밝힌다
        why = ("폼에 토큰이 없습니다" if not got
               else "토큰이 이 세션의 것이 아닙니다 — "
                    "다른 계정으로 로그인했거나 로그아웃됐습니다")
        raise PolicyError(
            f"요청을 확인하지 못했습니다 ({why}). 화면을 새로 열어 주십시오",
            step="STEP 147")


# 응답에 새 토큰을 실을 헤더 이름 (개정 307 · AD-096)
CSRF_HEADER = "X-CSRF-Token"

# 다음 GET 에서 낼 알림.  ★ HTTP 헤더에 담지 않는다 — 한글이 안 들어간다
_FLASH: dict[str, list] = {}


def redirect(path: str, flash: str = "", key: str = "-",
             csrf: str = "") -> tuple:
    """★ POST → 처리 → 303 → GET.  새로고침이 같은 변경을 두 번 하지 않는다.

    flash 는 서버가 들고 있다가 다음 GET 에서 낸다.
    헤더에 넣으면 latin-1 로 인코딩돼 한글에서 서버가 죽는다 (실측)

    csrf   ★ 갱신이 필요하면 응답에 새 토큰을 실어 보낸다 (개정 307 · AD-096).
           JS 가 그것으로 갈아 끼운다 — 한 화면에서 수십 번 POST 하는
           브라우저 수집이 토큰 만료로 통째로 막히지 않게 한다.
           ★ 토큰은 ASCII 다.  헤더에 넣어도 한글 문제가 없다
    """
    if flash:
        _FLASH.setdefault(key, []).append(flash)
    head = {"Location": path}
    if csrf:
        head[CSRF_HEADER] = csrf
    return HTTP_SEE_OTHER, head, b""


def take_flashes(key: str = "-") -> list:
    """한 번만 낸다.  읽으면 사라진다."""
    return _FLASH.pop(key, [])


__all__ = ["build_page", "check_post", "empty_state", "menu_items",
           "redirect", "new_csrf", "ANONYMOUS", "ROLE_USER", "HTTP_OK"]


# ── 요청 처리 (STEP 141 · 150) ──────────────────────────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _display_now(root: str | None = None) -> str:
    """화면에 낼 지금 시각.

    ★ 저장은 UTC · 표시는 로컬이다 (C-1).
      DTZ005 를 고치면서 화면 표시까지 UTC 로 바꿨더니
      한국 사용자에게 9시간 어긋났다 — 실측 08-15
    """
    import datetime as _dt
    import json as _j
    import os as _o
    import zoneinfo

    name = "Asia/Seoul"
    # ★ 뿌리 기준이다.  cwd 에 기대면 서비스로 띄울 때 못 찾는다 (A-7)
    path = _o.path.join(root or _ROOT, "config", "web.json")
    if _o.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            name = _j.load(f).get("display_timezone", name)
    try:
        tz = zoneinfo.ZoneInfo(name)
    except Exception:                                        # noqa: BLE001
        tz = _dt.timezone.utc
    return _dt.datetime.now(_dt.timezone.utc).astimezone(tz).strftime(
        "%Y-%m-%d %H:%M")


def make_app(db_path: str, root: str = ".", plan=None,
             reason_rows=None, fetch=None, resume=None,
             collect_urls=None) -> dict:
    """서버가 쓰는 처리기.  ★ 요청마다 연결을 연다 — 스레드 공유를 피한다.

    plan · reason_rows   재처리 결정표.  ★ run.py 가 주입한다.
                         web 이 collect 를 부르면 층이 거꾸로 간다 (STEP 15a)
    collect_urls         차종 → 조회 URL.  ★ 어댑터가 만든다 —
                         web 은 adapters 를 못 부른다 (STEP 136c · V4-22)
    """
    import sqlite3 as _sq

    from contracts import ANONYMOUS
    from web.context import HTTP_OK, NOT_FOUND, ErrorPage
    from web.server import guard, load_web_config
    from web.session import content_type, read_cookie, static_path
    from web.views import HANDLERS

    cfg = load_web_config(root)
    csrf_by_session: dict[str, str] = {}
    # ★ 토큰을 세션 키에서 만든다 (개정 308).  재시작·워커 증설에 견딘다
    try:
        from store.pii import load_key

        _csrf_secret = load_key(os.path.join(root, "secrets", "plate_hmac.key"))
    except (FileNotFoundError, ValueError):
        _csrf_secret = b""

    def account_of(req) -> object:
        from datetime import datetime, timezone

        sid = read_cookie(req.get("cookie"), cfg["session_cookie"])
        if not sid:
            return ANONYMOUS
        conn = _sq.connect(db_path)
        try:
            from store.admin import session_account

            return session_account(conn, sid, datetime.now(timezone.utc))
        finally:
            conn.close()

    def blank_page(title: str, req=None):
        """오류 화면의 머리말.

        ★ 요청의 세션을 읽는다.  ANONYMOUS 로 고정하면 로그인해 둔 사람이
          413·400·403·404 를 만날 때마다 「비로그인」으로 보인다 —
          로그아웃된 줄 알고 다시 로그인하게 된다 (실측 08-16 · 마스터 보고)
        """
        account = account_of(req) if req is not None else ANONYMOUS
        conn = _sq.connect(db_path)
        try:
            return build_page(conn, account, title, "")
        finally:
            conn.close()

    def _csrf_for(req) -> str:
        """세션당 토큰 1개 (STEP 147 · 개정 308).

        ★ 세션이 없어도 토큰이 필요하다 — 로그인 폼도 POST 다.
          그때는 요청 쿠키를 키로 쓰고, 없으면 익명 키를 쓴다
        ★ 세션 키에서 만든다.  서버에 쌓지 않는다 —
          실측 08-17: 메모리 dict 라 재시작하면 전부 무효가 됐고,
          마스터의 전 차종 수집이 첫 묶음만 되고 나머지 7개가 403 이었다
        """
        key = read_cookie(req.get("cookie"), cfg["session_cookie"]) or "-"
        if _csrf_secret:
            return csrf_for(key, _csrf_secret)
        # 키가 없으면(설치 전) 옛 방식으로 돈다.  ★ 조용히 막지 않는다
        if key not in csrf_by_session:
            csrf_by_session[key] = new_csrf()
        return csrf_by_session[key]

    def resolve(route, path_vars, req):
        account = account_of(req)
        denied = guard(account, route)
        if denied is not None:
            raise _Denied(denied)

        if route.view == "serve_static":
            target = static_path(path_vars.get("path", ""),
                                 os.path.join(root, "web", "static"))
            if target is None:
                raise _Denied(NOT_FOUND)
            with open(target, "rb") as f:
                return HTTP_OK, {
                    "Content-Type": content_type(target),
                    "Cache-Control": f"max-age={cfg['static_max_age_sec']}",
                }, f.read()

        handler = HANDLERS.get(route.view)
        if handler is None:
            raise _Denied(ErrorPage(NOT_FOUND.status, "준비 중입니다",
                                    f"{route.path} 화면은 아직 없습니다.",
                                    "매물 목록으로 돌아간다  (/listings)"))
        conn = _sq.connect(db_path)
        try:
            key = read_cookie(req.get("cookie"),
                              cfg["session_cookie"]) or "-"
            return handler(conn, account, req, path_vars=path_vars,
                           root=root, csrf=_csrf_for(req),
                           flash_key=key, plan=plan,
                           reason_rows=reason_rows, fetch=fetch,
                           resume=resume, collect_urls=collect_urls)
        finally:
            conn.close()

    return {"resolve": resolve, "blank_page": blank_page,
            "max_form_bytes": cfg["max_form_bytes"], "run_id": "",
            "csrf": csrf_by_session, "db_path": db_path, "root": root}


class _Denied(Exception):
    """guard · 404 를 오류 화면으로 넘긴다."""

    def __init__(self, page):
        super().__init__(page.title)
        self.page = page


def build_context(route, request: dict, conn, account, title: str = "",
                  **kw) -> PageContext:
    """규격 이름 (STEP 144).  Route · 요청 → 공통 문맥.

    ★ 화면마다 다른 문구를 쓰지 않는다.  전 화면이 같은 것을 낸다
    """
    return build_page(conn, account, title or _title_of(route), "",
                      csrf=kw.get("csrf", ""),
                      flashes=take_flashes(kw.get("flash_key", "-")),
                      run_id=kw.get("run_id", ""),
                      calc_version=kw.get("calc_version", ""),
                      dict_version=kw.get("dict_version", ""),
                      parse_version=kw.get("parse_version", ""))


def _title_of(route) -> str:
    return LABELS.get(getattr(route, "path", ""), "")
