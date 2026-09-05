# -*- coding: utf-8 -*-
"""라우팅 표 (14장 STEP 142).

지시서   STEP 142
근거     ★ 라우팅이 코드에 흩어지면 권한 검사를 빠뜨린다.  한 표로 고정한다
금지     정규식 라우팅.  경로 변수는 {name} 하나만
         표에 없는 경로는 404 — 추측으로 처리하지 않는다
"""
from __future__ import annotations

from dataclasses import dataclass

from contracts import ROLE_ADMIN, ROLE_ANONYMOUS, ROLE_USER

GET, POST = "GET", "POST"
# ★★★ 08-27 — ★ 분류가 ★ **넷**이 됐다 (`61-web.md` STEP 149j · 개정 765).
#   ★ 「계정」은 ★ **잠금 단위가 다르다** — ★ 실행 중에도 ★ 계정은 만질 수 있다.
#   ★ ★ 그래서 ★ 운영에 두면 ★ 잠금 단위와 메뉴가 어긋난다 (V11-24 가 그것을 본다)
#   ★ 금지 — ★ **다섯째 분류를 만드는 것**.  ★ 화면이 늘면 ★ 넷 중 하나에 넣는다
GROUP_OPS, GROUP_TUNE, GROUP_EXPLORE = "운영", "조정", "탐색"
GROUP_ACCOUNT = "계정"


# 구현 상태 (STEP 142).  ★ 준비 중을 표에서 빼면 계획이 사라진다
BUILT, PENDING = "구현", "준비 중"

# 실제로 화면이 있는 view.  나머지는 「준비 중」을 정직하게 낸다
# ★ 전 화면을 시안대로 만들었다 (2026-08-14).  준비 중은 없다
BUILT_VIEWS: frozenset[str] = frozenset()   # 아래 _fill 이 채운다


@dataclass(frozen=True)
class Route:
    path: str
    methods: tuple[str, ...]
    view: str
    role: str                 # 최소 권한.  guard() 가 서버에서 막는다
    menu: str | None = None

    @property
    def status(self) -> str:
        """구현 여부는 HANDLERS 가 정본이다.  표와 코드가 어긋나지 않는다."""
        from web.views import HANDLERS

        return BUILT if (self.view in HANDLERS
                         or self.view == "serve_static") else PENDING

    @property
    def var(self) -> str | None:
        """경로 변수 이름.  없으면 None."""
        if "{" not in self.path:
            return None
        return self.path.split("{", 1)[1].split("}", 1)[0]


ROUTES: tuple[Route, ...] = (
    Route("/", (GET,), "view_dashboard", ROLE_ANONYMOUS),
    Route("/listings", (GET,), "view_listings", ROLE_ANONYMOUS),
    # ★★ 08-30 (`61-web.md:193` · `UI_REVIEW` 30장) — ★ 팔린 차.
    #   ★ 목록에서 뺀 것을 ★ 여기서 따로 본다 (마스터 확정 08-29 요구 134)
    Route("/sold", (GET,), "view_sold", ROLE_ANONYMOUS),
    Route("/recommend", (GET,), "view_recommend", ROLE_ANONYMOUS),
    # ★★ 개정 427 — 상세 신설.  /why 를 흡수한다.  ★ /why 주소는 살린다
    Route("/detail/{listing_id}", (GET,), "view_detail", ROLE_ANONYMOUS),
    Route("/why/{listing_id}", (GET,), "view_why", ROLE_ANONYMOUS),
    Route("/compare", (GET,), "view_compare", ROLE_ANONYMOUS),
    # ★★ 추적 — ★ 같은 차가 여러 사이트에 (마스터 허락 08-24 · 명령서 1-2)
    Route("/track", (GET,), "view_track", ROLE_ANONYMOUS),
    Route("/market", (GET,), "view_market", ROLE_ANONYMOUS),
    Route("/dealers", (GET,), "view_dealers", ROLE_ANONYMOUS),
    Route("/notready", (GET,), "view_notready", ROLE_ANONYMOUS),
    # 리포트 — ★ 목록만 내고 내용을 못 보게 하지 않는다 (개정 357 · V11-122).
    #   /reports?open=… 이 팝업이다.  JS 없이 닫힌다 — 별도 경로다
    Route("/reports", (GET,), "view_reports", ROLE_USER),
    Route("/reports/{name}", (GET,), "view_report_download", ROLE_USER),
    # ★★★★★ 09-06 r1184 A-5 — ★ 분석 (추천 탭 3) · 규격 `61-web` 194~196행.
    #   ★ 규격 표는 `drop` 을 POST 라 적었는데 ★ 가이드가 지으신 틀은
    #   ★ ★ `<a href>` 곧 GET 이다 — ★ 틀이 그대로 돌게 ★ 둘 다 받는다 (회차에 적었다)
    # ★ 규격 표(61-web 194~196)가 ★ 셋 다 `anonymous` 다 — ★ 그대로 따른다.
    #   ★ 로그인 안 한 분은 ★ 담을 자리가 없으니 ★ 담기지 않는다 (화면이 그리 말한다)
    Route("/analyze", (GET,), "view_analyze", ROLE_ANONYMOUS),
    # ★★ `V11-08` — ★ **상태를 바꾸는 길은 GET 에 두지 않는다.**
    #   ★ 가이드가 지으신 틀은 ★ `<a href>` 곧 GET 이라 ★ 이대로는 405 다 —
    #   ★ ★ **작은 폼(POST)으로 바꿔 주셔야 한다.**  ★ 회차에 적어 여쭙는다.
    #   ★ 규격 표(61-web 196)도 ★ `drop` 을 POST 라 적었다 — ★ 그것을 따른다
    Route("/analyze/add/{listing_id}", (POST,), "view_analyze_add",
          ROLE_ANONYMOUS),
    Route("/analyze/drop/{listing_id}", (POST,), "view_analyze_drop",
          ROLE_ANONYMOUS),
    Route("/analyze/copy/{listing_id}", (GET,), "view_analyze_copy",
          ROLE_ANONYMOUS),
    Route("/watch", (GET,), "view_watch", ROLE_USER),
    Route("/watch/add", (POST,), "watch_add", ROLE_USER),
    Route("/watch/{watch_id}", (POST,), "watch_update", ROLE_USER),
    Route("/login", (GET, POST), "view_login", ROLE_ANONYMOUS),
    Route("/join", (GET, POST), "view_join", ROLE_ANONYMOUS),
    Route("/password", (GET, POST), "view_password", ROLE_USER),
    Route("/logout", (POST,), "view_logout", ROLE_USER),
    Route("/admin", (GET,), "view_admin", ROLE_ADMIN),
    Route("/admin/run", (GET, POST), "view_admin_run", ROLE_ADMIN, GROUP_OPS),
    Route("/admin/audit", (GET,), "view_admin_audit", ROLE_ADMIN, GROUP_OPS),
    # ★ 지켜보는 곳.  실행하는 곳(/admin/run)과 나눈다 — 보다가 또 누르면
    #   10,000 호출이 도는 중에 다시 시작된다 (STEP 136f · 개정 272)
    Route("/admin/status", (GET,), "view_admin_status", ROLE_ADMIN, GROUP_OPS),
    # 반입은 수집이다 — 탐색(/admin/api)이 아니라 운영이다 (STEP 136a)
    Route("/admin/import", (GET, POST), "view_admin_import", ROLE_ADMIN,
          GROUP_OPS),
    # 브라우저가 사용자 회선으로 부른다 — 서버 IP 가 막힌 자리다 (STEP 136c)
    Route("/admin/collect", (GET, POST), "view_admin_collect", ROLE_ADMIN,
          GROUP_OPS),
    Route("/admin/users", (GET, POST), "view_admin_users", ROLE_ADMIN,
          GROUP_ACCOUNT),
    Route("/admin/scoring", (GET, POST), "view_admin_scoring", ROLE_ADMIN,
          GROUP_TUNE),
    Route("/admin/targets", (GET, POST), "view_admin_targets", ROLE_ADMIN,
          GROUP_TUNE),
    Route("/admin/registry", (GET, POST), "view_admin_registry", ROLE_ADMIN,
          GROUP_TUNE),
    # 사전 확정 — 사람이 검토할 자리다 (STEP 136e).  자동으로 하지 않는다
    Route("/admin/dict", (GET, POST), "view_admin_dict", ROLE_ADMIN,
          GROUP_TUNE),
    Route("/admin/config", (GET, POST), "view_admin_config", ROLE_ADMIN,
          GROUP_TUNE),
    Route("/admin/query", (GET, POST), "view_admin_query", ROLE_ADMIN,
          GROUP_EXPLORE),
    Route("/admin/api", (GET, POST), "view_admin_api", ROLE_ADMIN,
          GROUP_EXPLORE),
    Route("/admin/tools", (GET, POST), "view_admin_tools", ROLE_ADMIN,
          GROUP_EXPLORE),
    Route("/admin/docs", (GET,), "view_admin_docs", ROLE_ADMIN, GROUP_EXPLORE),
    Route("/admin/requests", (GET, POST), "view_admin_requests", ROLE_ADMIN,
          GROUP_EXPLORE),
    Route("/static/{path}", (GET,), "serve_static", ROLE_ANONYMOUS),
)

# ★ 화면이 아닌 것 — 파일을 준다.  <h1> 도 시안도 없다 (V11-30 · V11-12).
#   ★ 여기 한 곳이 정본이다.  검사와 도구가 각자 목록을 들면 갈린다
NON_SCREEN_VIEWS: tuple = (
    "serve_static",       # 정적 파일
    "view_report_download",  # 리포트 내려받기 (개정 357)
    # ★ 09-06 r1184 A-5 — ★ 「타 AI 요청」은 ★ 화면이 아니다.
    #   ★ 그 차의 ★ **원문을 하나의 글월**로 준다 (`text/plain`) — ★ `<h1>` 이 없다
    "view_analyze_copy",
)


def match(path: str, method: str) -> tuple[Route | None, dict]:
    """반환   (Route, 경로 변수).  표에 없으면 (None, {}) — 404 다.

    ★ 정확 일치를 먼저 본다.  변수 경로는 그다음이다
    """
    for r in ROUTES:
        if r.path == path:
            return (r if method in r.methods else None), {}
    for r in ROUTES:
        name = r.var
        if not name:
            continue
        head = r.path.split("{", 1)[0]
        if not path.startswith(head) or len(path) <= len(head):
            continue
        rest = path[len(head):]
        if name != "path" and "/" in rest:
            continue          # {path} 만 슬래시를 품는다 (정적 파일)
        return (r if method in r.methods else None), {name: rest}
    return None, {}


def resolve_route(path: str, method: str) -> Route | None:
    """규격 이름 (STEP 142).  경로 변수가 필요하면 match 를 쓴다."""
    return match(path, method)[0]
