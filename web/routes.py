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
GROUP_OPS, GROUP_TUNE, GROUP_EXPLORE = "운영", "조정", "탐색"


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
    Route("/recommend", (GET,), "view_recommend", ROLE_ANONYMOUS),
    Route("/why/{listing_id}", (GET,), "view_why", ROLE_ANONYMOUS),
    Route("/compare", (GET,), "view_compare", ROLE_ANONYMOUS),
    Route("/market", (GET,), "view_market", ROLE_ANONYMOUS),
    Route("/dealers", (GET,), "view_dealers", ROLE_ANONYMOUS),
    Route("/notready", (GET,), "view_notready", ROLE_ANONYMOUS),
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
    # 반입은 수집이다 — 탐색(/admin/api)이 아니라 운영이다 (STEP 136a)
    Route("/admin/import", (GET, POST), "view_admin_import", ROLE_ADMIN,
          GROUP_OPS),
    Route("/admin/users", (GET, POST), "view_admin_users", ROLE_ADMIN,
          GROUP_OPS),
    Route("/admin/scoring", (GET, POST), "view_admin_scoring", ROLE_ADMIN,
          GROUP_TUNE),
    Route("/admin/targets", (GET, POST), "view_admin_targets", ROLE_ADMIN,
          GROUP_TUNE),
    Route("/admin/registry", (GET, POST), "view_admin_registry", ROLE_ADMIN,
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
