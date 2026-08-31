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
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from contracts import ANONYMOUS, ROLE_ANONYMOUS, ROLE_PENDING, ROLE_RANK, ROLE_USER
from web.context import (
    FORBIDDEN, NEED_LOGIN, PENDING_WAIT, HTTP_NOT_FOUND, HTTP_OK, HTTP_SEE_OTHER, NOT_FOUND, ErrorPage,
    error_page,
)
from web.routes import GET, POST, match
from web.session import (
    content_type, csrf_ok, new_csrf, parse_form, read_cookie, set_cookie,
    static_path,
)
from web.template import render

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# ★ 상대가 먼저 끊은 연결에 쓰면 나는 예외다 (docs/SERVER_SURVIVAL.md 1장).
#   실측 08-23 — `_error` 가 오류 화면을 보내려는데 브라우저가 이미 닫혀
#   BrokenPipeError 가 났고, 그 뒤 서버가 3시간 16분 아무것도 못 냈다.
#   ★ 그 연결 하나만 버린다.  서버는 살아 있어야 한다
DISCONNECTED = (BrokenPipeError, ConnectionResetError)
# ★ 붙어 놓고 아무것도 안 보내는 연결을 버리는 시간(초).
#   실측 08-23 — 이런 연결 ★ 하나로 서버 전체가 3시간 16분 멎었다.
#   `BaseRequestHandler.timeout` 기본값이 None 이라 ★ 영원히 기다렸다
IDLE_TIMEOUT = 30
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
        # ★ 「관리자만」은 route.role 이 admin 일 때만 참이다.
        #   ROLE_USER 화면에 그 말을 내면 거짓말이다 — 마스터가 로그인해도
        #   안 될 것처럼 읽힌다 (실측 08-22 · /watch)
        if ROLE_RANK[route.role] <= ROLE_RANK[ROLE_USER]:
            return NEED_LOGIN
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
        # ★ 이것이 없으면 rfile.readline() 이 영원히 기다린다 (SERVER_SURVIVAL 1장)
        timeout = IDLE_TIMEOUT

        def log_message(self, fmt, *args):           # noqa: N802
            pass                                      # 접속 로그는 안 남긴다

        def _send(self, status, body: bytes, ctype: str, extra=None):
            # ★ end_headers() 도 소켓에 쓴다 — 머리글에서도 끊길 수 있다.
            #   그래서 write 한 줄이 아니라 보내는 동안 전부를 감싼다
            try:
                self.send_response(int(status))
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("X-Content-Type-Options", "nosniff")
                for k, v in (extra or {}).items():
                    self.send_header(k, v)
                self.end_headers()
                # ★ HEAD 는 ★ 머리글만 낸다 — ★ 몸통을 쓰지 않는다 (RFC 9110 9.3.2)
                if not getattr(self, "head_only", False):
                    self.wfile.write(body)
            except DISCONNECTED:
                # ★ 보낼 곳이 없다.  조용히 이 연결만 버린다 (SERVER_SURVIVAL 1장)
                self.close_connection = True

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
                # ★★★★★ 09-02 명령서 ② — ★ 「★ 차종 단추는 ★ **켜고 끄는 스위치**
                #   ★ ★ · ★ **여럿 켜면 OR** · ★ 주소에 남긴다 —
                #   ★ ★ ★ `?tab=1&model=MODEL_Y&model=KOLEOS_HEV`」
                #   ★★ `dict(parse_qsl(...))` 는 ★ **마지막 하나만** 남긴다 —
                #     ★ ★ 그러면 ★ 여럿 켠 것을 잃는다.  ★ 나란히 둔다.
                #   ★ ★ ★ `query` 는 안 건드린다 — ★ 쓰던 화면이 다 그대로 돈다
                "query_all": urllib.parse.parse_qs(parsed.query),
                # ★ 폼 파싱은 parse_form 이 한다 (STEP 147).
                #   GET Route 면 빈 dict — GET 으로 상태를 바꾸지 않는다
                "form": parse_form(route, body),
                "cookie": self.headers.get("Cookie"),
                # ★ 앞단(리버스 프록시)이 TLS 를 맡는다 — 앱은 평문으로 듣는다.
                #   그래서 「지금 HTTPS 인가」는 이 머리글로만 알 수 있다.
                #   이것이 없으면 쿠키에 Secure 를 붙일 수 없다 (14장 · ORDER_https)
                "proto": (self.headers.get("X-Forwarded-Proto")
                          or "http").split(",")[0].strip().lower(),
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
            # ★ 쿠키를 넘긴다.  안 넘기면 오류 화면마다 「비로그인」이 된다
            req = {"cookie": self.headers.get("Cookie")}
            # ★ 오류 화면을 만드는 도중에도 끊길 수 있다.  _send 밖까지 감싼다 —
            #   08-23 에 죽은 자리가 정확히 여기다 (SERVER_SURVIVAL 1장)
            try:
                html = render("_error.html",
                              {"page": app["blank_page"](err.title, req),
                               "err": err})
                self._send(err.status, html.encode("utf-8"),
                           "text/html; charset=utf-8")
            except DISCONNECTED:
                self.close_connection = True

        def handle_one_request(self):                 # noqa: N802
            """★ 한 겹 더 — 요청 줄을 읽는 중에 끊겨도 서버는 산다.

            `_send` · `_error` 밖(머리글 읽기 · finish 의 flush)에서 나는
            것까지 여기서 받는다 (SERVER_SURVIVAL 1장 ②).
            """
            try:
                super().handle_one_request()
            except TimeoutError:
                # ★ IDLE_TIMEOUT 동안 아무것도 안 왔다.  이 연결만 버린다
                self.close_connection = True
            except DISCONNECTED:
                self.close_connection = True

        def do_GET(self):                             # noqa: N802
            self._handle(GET)

        def do_POST(self):                            # noqa: N802
            self._handle(POST)

        def do_HEAD(self):                            # noqa: N802
            """HEAD — ★ GET 과 같은 머리글 · ★ 몸통은 안 보낸다.

            ★★ 실측 08-24 — ★ 이것이 없어 ★ `curl -I` 가 ★ 501 을 받았다.
              ★ `CLAUDE.md` 가 ★ 건강 확인으로 ★ 바로 그 명령을 적어 두어
              ★ 사이트가 멀쩡한데 ★ 「501」로 보였다 (GET 은 200 이었다)
            """
            self.head_only = True
            try:
                self._handle(GET)
            finally:
                self.head_only = False

    return Handler


def serve(app, host: str | None = None, port: int | None = None,
          root: str = ROOT) -> int:
    cfg = load_web_config(root)
    host = host or cfg["host"]
    port = int(port or cfg["port"])
    if host not in ("127.0.0.1", "localhost", "::1"):
        print(EXTERNAL_WARN)
    print(f"http://{host}:{port}    (Ctrl+C 로 중지)")
    # ★ ThreadingHTTPServer 다.  HTTPServer 는 ★ 한 연결이 막히면 전체가 막힌다 —
    #   08-23 에 그것으로 3시간 16분 멎었다 (docs/SERVER_SURVIVAL.md 1장 · 실측)
    httpd = ThreadingHTTPServer((host, port), make_handler(app))
    # ★ 남은 실이 종료를 붙잡지 않게 한다
    httpd.daemon_threads = True
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
