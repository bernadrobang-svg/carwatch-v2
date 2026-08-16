# -*- coding: utf-8 -*-
"""세션 · CSRF · 정적 파일 (14장 STEP 145~147).

지시서   STEP 145 (정적) · 146 (세션) · 147 (폼)
근거     ★ 쿠키를 고쳐 권한을 올릴 수 있으면 안 된다.  session_id 만 담는다
금지     쿠키에 role 을 담는 것 · 클라이언트 값을 신뢰하는 것
         GET 으로 상태를 바꾸는 것
         web/static/ 밖의 경로를 여는 것
"""
from __future__ import annotations

import hmac
import os
import posixpath
import secrets

from store.admin import SECRET_BYTES

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
TOKEN_BYTES = SECRET_BYTES   # 구현 상수 (2장 상수표)

# 쿠키 속성.  ★ HttpOnly 로 스크립트가 못 읽는다 (STEP 146)
COOKIE_FLAGS = ("HttpOnly", "SameSite=Lax", "Path=/")

STATIC_TYPES = {
    ".css": "text/css; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
    ".svg": "image/svg+xml",
}


def set_cookie(name: str, value: str, max_age: int,
               secure: bool = False) -> str:
    """★ session_id 만 담는다.  역할·이름을 담지 않는다 (STEP 146)."""
    flags = list(COOKIE_FLAGS) + ([f"Max-Age={max_age}"])
    if secure:
        flags.append("Secure")
    return f"{name}={value}; " + "; ".join(flags)


def read_cookie(header: str | None, name: str) -> str | None:
    for part in (header or "").split(";"):
        k, _, v = part.strip().partition("=")
        if k == name:
            return v or None
    return None


# ── CSRF (STEP 147) ─────────────────────────────────────────────────
def new_csrf() -> str:
    """세션당 토큰 1개.  폼에 hidden 으로 넣는다."""
    return secrets.token_urlsafe(TOKEN_BYTES)


def csrf_ok(expected: str | None, got: str | None) -> bool:
    """★ 불일치면 403.  이력에 남긴다 (호출자가 기록한다).

    ★ 바이트로 견준다.  compare_digest 는 ASCII 아닌 문자열에 TypeError 를
      던진다 — 한글 토큰 하나로 500 이 났다 (실측 08-15).
      500 은 「우리 결함」이라는 뜻이고, 남이 보낸 값으로 나면 안 된다
    """
    if not expected or not got:
        return False
    return hmac.compare_digest(expected.encode("utf-8", "replace"),
                               got.encode("utf-8", "replace"))


# ── 정적 파일 (STEP 145) ────────────────────────────────────────────
def static_path(rel: str, root: str | None = None) -> str | None:
    """★ web/static/ 밖으로 못 나간다.  경로 탈출로 secrets/ 가 읽히면 안 된다.

    금지   ../ 를 포함한 경로 · 심볼릭 링크 추적 · 절대 경로
    반환   실제 파일 경로.  벗어나거나 없으면 None
    """
    base = os.path.realpath(root or STATIC_DIR)
    clean = posixpath.normpath("/" + rel.replace("\\", "/")).lstrip("/")
    if not clean or clean.startswith(".."):
        return None
    target = os.path.realpath(os.path.join(base, clean))
    if target != base and not target.startswith(base + os.sep):
        return None
    if os.path.islink(os.path.join(base, clean)):
        return None
    return target if os.path.isfile(target) else None


def content_type(path: str) -> str:
    return STATIC_TYPES.get(os.path.splitext(path)[1].lower(),
                            "application/octet-stream")


# ── 폼 파싱 · 검증 (STEP 147) ───────────────────────────────────────
def parse_form(route, raw: str | bytes) -> dict:
    """폼 본문 → dict.  ★ 값을 해석하지 않는다 — 화면이 판정하지 않는다.

    금지   여기서 형변환·기본값 채우기.  핸들러가 규격을 안다
    필수   POST 가 아닌 Route 면 빈 dict.  GET 으로 상태를 바꾸지 않는다
    """
    import urllib.parse

    if "POST" not in getattr(route, "methods", ()):
        return {}
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "replace")
    if _is_multipart(raw):
        return _parse_multipart(raw)
    return dict(urllib.parse.parse_qsl(raw or ""))


# 파일 올리기 (13장 STEP 136a).  ★ urlencoded 본문에는 날 CRLF 가 없다 —
# 값이 퍼센트 인코딩되기 때문이다.  그래서 본문만 보고 갈라도 안전하다
MULTIPART_MARK = "Content-Disposition: form-data"


def _is_multipart(raw: str) -> bool:
    return raw.startswith("--") and MULTIPART_MARK in raw


def _parse_multipart(raw: str) -> dict:
    """multipart/form-data → dict.  ★ 파일도 값 하나로 받는다.

    근거   붙여넣기 상한을 넘는 목록은 파일로 올린다 (STEP 136a)
    금지   조용히 자르는 것.  자르면 「넣었는데 일부만 들어간」 것이 된다
    """
    boundary = raw.split("\r\n", 1)[0].strip()
    if not boundary:
        return {}
    out: dict = {}
    for part in raw.split(boundary):
        head, sep, body = part.partition("\r\n\r\n")
        if not sep or MULTIPART_MARK not in head:
            continue
        name = ""
        for chunk in head.split(";"):
            if chunk.strip().startswith("name="):
                name = chunk.split("=", 1)[1].strip().strip('"')
                break
        if not name:
            continue
        # 마지막 CRLF 는 경계 앞 구분자다.  값의 일부가 아니다
        out[name] = body[:-2] if body.endswith("\r\n") else body
    return out
