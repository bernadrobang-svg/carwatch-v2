# -*- coding: utf-8 -*-
"""HTTP 서버 (14장 STEP 141 · 150).

지시서   STEP 141 (서버와 실행) · 150 (접근 제어) · 148 (오류)
근거     ★ 표준 라이브러리로 간다.  의존이 없다 — pip install 없이 뜬다.
         v1 이 Flask 였고 그것이 이식을 어렵게 했다 (0장 STEP 1)
금지     0.0.0.0 바인딩을 기본값으로 두는 것
         GET 으로 상태를 바꾸는 것
사용     run.py web  이 부른다.  직접 실행하지 않는다 (STEP 15a 진입점)
"""
from __future__ import annotations

import json
import os
import urllib.parse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer

from contracts import ANONYMOUS, ROLE_ANONYMOUS, ROLE_PENDING, ROLE_RANK
from web.context import (
    FORBIDDEN, PENDING_WAIT, HTTP_NOT_FOUND, HTTP_OK, HTTP_SEE_OTHER, NOT_FOUND, ErrorPage,
    error_page,
)
from web.routes import GET, POST, match
from web.session import (
    content_type, csrf_ok, new_csrf, parse_form, read_cookie, set_cookie,
    static_path,
)
from web.template import render

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 폼 본문 상한은 정책이다 → config.web.max_form_bytes
EXTERNAL_WARN = (
    "★ 외부에 열립니다.  관리자 비밀번호를 확인하십시오.\n"
    "   HTTPS 는 앞단(리버스 프록시)에 맡깁니다 — 자체 TLS 를 두지 않습니다")


def load_web_config(root: str = ROOT) -> dict:
    with open(os.path.join(root, "config", "web.json"), encoding="utf-8") as f:
        return json.load(f)


# 로그인만 하면 되는 자리.  ★ 403 이 아니라 유도 화면을 낸다 (STEP 149i).
# 「로그인하세요」만 내면 무엇을 하려 했는지 잊는다 — 담으려던 대상을 보여 준다
# ★ 「담으려던 것」이 있는 자리만이다 (STEP 149i).
#   /watch/{watch_id} 는 고칠 항목 자체가 비로그인에게 없다 — 여기 넣으면
#   account_id 가 None 인 채로 핸들러에 들어간다 (실측 08-15)
INVITE_PATHS = frozenset({"/watch/add"})


def guard(account, route) -> ErrorPage | None:
    """★ 서버가 막는다.  화면 숨김은 권한이 아니다 (STEP 126 · 150)."""
    if ROLE_RANK.get(getattr(account, "role", ROLE_ANONYMOUS), 0) \
            < ROLE_RANK[route.role]:
        # ★ 비로그인이 관심을 누른 것은 「권한 없음」이 아니라 「아직 로그인 안 함」이다.
        #   403 을 내면 누른 것이 사라진다 (E-9 · V11-23)
        role = getattr(account, "role", ROLE_ANONYMOUS)
        if route.path in INVITE_PATHS and role == ROLE_ANONYMOUS:
            return None
        # ★ 승인 대기자에게 「관리자로 로그인하라」고 하면 이미 로그인했으니
        #   무엇을 할지 모른다.  기다리는 중임을 알린다 (STEP 126)
        if role == ROLE_PENDING:
            return PENDING_WAIT
        return FORBIDDEN
    # ★ must_change_secret 이면 비밀번호 변경 화면 외로 못 간다 (STEP 146)
    # ★ 비밀번호를 바꾸는 화면 자체는 열려야 한다.  아니면 못 바꾼다
    if getattr(account, "must_change_secret", False) \
            and route.path not in ("/login", "/logout", "/password",
                                   "/static/{path}"):
        return ErrorPage(HTTP_SEE_OTHER, "비밀번호를 바꿔야 합니다",
                         "임시 비밀번호로는 다른 화면을 볼 수 없습니다.",
                         "비밀번호를 변경한다  (/password)")
    return None


# 상한 초과 본문을 비울 때 한 번에 읽는 양.  ★ 안 읽으면 연결이 끊긴다.
#   폼 상한과 같은 값을 쓴다 — 따로 두면 갈린다 (V4-17)
def _drain_chunk(app) -> int:
    return int(app["max_form_bytes"])


def TOO_LARGE(cap: int, got: int) -> ErrorPage:
    """폼이 상한을 넘었다 (STEP 147 · Q-1)."""
    return ErrorPage(
        HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "보낸 내용이 너무 깁니다",
        f"한 번에 보낼 수 있는 크기는 {cap:,}바이트입니다 "
        f"(보낸 것 {got:,}바이트).",
        "내용을 나눠서 보내거나 줄인 뒤 다시 시도한다", "")


def make_handler(app):
    """app  = {"resolve": (route, vars, req) -> (status, headers, body)}"""

    class Handler(BaseHTTPRequestHandler):
        server_version = "CarWatch"

        def log_message(self, fmt, *args):           # noqa: N802
            pass                                      # 접속 로그는 안 남긴다

        def _send(self, status, body: bytes, ctype: str, extra=None):
            self.send_response(int(status))
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def _handle(self, method: str):
            parsed = urllib.parse.urlparse(self.path)
            route, path_vars = match(parsed.path, method)
            if route is None:
                return self._error(NOT_FOUND)

            body = b""
            if method == POST:
                # ★ 상한을 넘으면 400 이다.  조용히 자르면 사용자는 저장된 줄
                #   알고 뒷부분은 사라진다 — 사유 · 쿼리 · 요청 본문이
                #   잘려도 아무도 모른다 (Q-1 · 실측 08-15)
                declared = int(self.headers.get("Content-Length") or 0)
                cap = app["max_form_bytes"]
                if declared > cap:
                    # 보낸 것을 다 읽어 비운다 — 안 읽으면 연결이 끊긴다
                    self._drain(declared)
                    return self._error(TOO_LARGE(cap, declared))
                body = self.rfile.read(declared) if declared else b""

            req = {
                "query": dict(urllib.parse.parse_qsl(parsed.query)),
                # ★ 폼 파싱은 parse_form 이 한다 (STEP 147).
                #   GET Route 면 빈 dict — GET 으로 상태를 바꾸지 않는다
                "form": parse_form(route, body),
                "cookie": self.headers.get("Cookie"),
                "method": method,
            }
            try:
                status, headers, out = app["resolve"](route, path_vars, req)
            except Exception as exc:                  # noqa: BLE001
                page = getattr(exc, "page", None)
                return self._error(page if page is not None
                                   else error_page(exc,
                                                   app.get("run_id", "")))
            ctype = headers.pop("Content-Type", "text/html; charset=utf-8")
            self._send(status, out, ctype, headers)

        def _drain(self, n: int) -> None:
            left = n
            while left > 0:
                chunk = self.rfile.read(min(left, _drain_chunk(app)))
                if not chunk:
                    break
                left -= len(chunk)

        def _error(self, err: ErrorPage):
            html = render("_error.html",
                          {"page": app["blank_page"](err.title), "err": err})
            self._send(err.status, html.encode("utf-8"),
                       "text/html; charset=utf-8")

        def do_GET(self):                             # noqa: N802
            self._handle(GET)

        def do_POST(self):                            # noqa: N802
            self._handle(POST)

    return Handler


def serve(app, host: str | None = None, port: int | None = None,
          root: str = ROOT) -> int:
    cfg = load_web_config(root)
    host = host or cfg["host"]
    port = int(port or cfg["port"])
    if host not in ("127.0.0.1", "localhost", "::1"):
        print(EXTERNAL_WARN)
    print(f"http://{host}:{port}    (Ctrl+C 로 중지)")
    httpd = HTTPServer((host, port), make_handler(app))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n중지했습니다.")
    finally:
        httpd.server_close()
    return 0


__all__ = ["guard", "load_web_config", "make_handler", "serve",
           "content_type", "csrf_ok", "new_csrf", "read_cookie",
           "set_cookie", "static_path", "ANONYMOUS", "HTTP_OK",
           "HTTP_NOT_FOUND"]
