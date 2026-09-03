# -*- coding: utf-8 -*-
"""원문 획득 · 형식 검증.

지시서   2장 STEP 16 (수집 계층 원칙) · STEP 18 (라벨↔내용) · STEP 24 (요청 정책)
         1장 STEP 12 (원문 획득 계약) · 0장 STEP 8-④⑤
근거     수집은 받아서 저장만 한다.  해석하지 않는다.
금지     전역 변수로 원문을 전달하는 것.  v1 은 last_raw 하나로 원문 2,183건을
         잘못된 라벨로 저장했고 이력 축이 통째로 죽었다.
         404 재시도 — 404 는 실패가 아니라 not_found 결과다.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timezone

from contracts import Clock, EndpointSpec, FetchResult, Fetcher, Request, Response

HTTP_OK_FLOOR = 200
HTTP_REDIRECT_FLOOR = 300
HTTP_NOT_FOUND = 404


class SystemClock:
    """시각 주입의 기본 구현 (STEP 8-⑤).  분석 계층은 이것을 모른다."""

    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class UrlFetcher:
    """표준 라이브러리만 쓴다 (STEP 2 · 표준 라이브러리 우선)."""

    def get(self, url: str, headers: dict[str, str]) -> Response:
        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req) as res:
                raw = res.read()
                enc = res.headers.get_content_charset() or "utf-8"
                return Response(
                    http_code=res.status,
                    body_text=raw.decode(enc, errors="replace"),
                    content_type=res.headers.get("Content-Type"),
                    encoding=enc,
                )
        except urllib.error.HTTPError as e:
            raw = e.read()
            enc = e.headers.get_content_charset() or "utf-8"
            return Response(
                http_code=e.code,
                body_text=raw.decode(enc, errors="replace"),
                content_type=e.headers.get("Content-Type"),
                encoding=enc,
            )


def fetch(req: Request, fetcher: Fetcher, kind: str, clock: Clock,
          source_id: str | None = None, spec=None) -> FetchResult:
    """획득만 한다.  파싱하지 않는다.

    반환값에 raw 를 담는다.  공유 변수를 쓰지 않는다 (STEP 12).

    status   ok        200대 · 본문이 JSON 으로 읽힘 · 비어 있지 않음
             empty     200대인데 내용이 없음.  요청은 했다
             not_found 404.  없는 자원이다.  재시도하지 않는다
             error     그 외 (네트워크 · 4xx · 5xx · JSON 파싱 실패)
    """
    at = clock.now()
    try:
        res = fetcher.get(req.url, req.headers)
    except Exception as e:  # 하위 예외는 감싸서 결과로 만든다 (STEP 3)
        return FetchResult(kind, source_id, "error", None, None, repr(e), at)

    if res.http_code == HTTP_NOT_FOUND:
        return FetchResult(kind, source_id, "not_found", None, res.http_code, None, at)
    if not (HTTP_OK_FLOOR <= res.http_code < HTTP_REDIRECT_FLOOR):
        return FetchResult(
            kind, source_id, "error", None, res.http_code, res.body_text[:HTTP_OK_FLOOR], at
        )
    try:
        body = json.loads(res.body_text)
    except ValueError as e:
        # ★★★★★ 09-03 (가이드 지시 ①②) — ★ **원문이 다 JSON 은 아니다.**
        #   ★ BMW BPS·현대인증·K카·보배드림 상세는 ★ **HTML 쪽**이다 —
        #   ★ ★ 그것이 그 사이트의 ★ **바른 원문**이다 (파서가 그렇게 받는다).
        #   ★★ 실측 09-03 — ★ BMW 상세 194건이 ★ **HTTP 200 인데 전부 `error`**
        #     ★ ★ 였다.  ★ 「200 이 왔다」와 「제대로 왔다」가 다른 자리이지만,
        #     ★ ★ ★ 여기서는 ★ **우리가 JSON 만 알아서** 난 것이다.
        #   ★★★ 어댑터가 ★ 「이 창구는 HTML 이다」라고 말하면 ★ 그대로 받는다 —
        #     ★ ★ `endpoint_schema()[kind].root_type == "html"`.
        #     ★ ★ ★ 말이 없으면 ★ 옛날처럼 ★ **`error`** 다 (조용히 안 삼킨다)
        if str(getattr(spec, "root_type", "") or "") == "html":
            body = res.body_text
            status = "empty" if not (body or "").strip() else "ok"
            return FetchResult(kind, source_id, status, body,
                               res.http_code, None, at)
        return FetchResult(kind, source_id, "error", None, res.http_code, repr(e), at)

    status = "empty" if body in (None, {}, []) else "ok"
    return FetchResult(kind, source_id, status, body, res.http_code, None, at)


def verify_shape(res: FetchResult, spec: EndpointSpec) -> bool:
    """라벨↔내용 형식 검증.  저장 직전에 건다 (STEP 18).

    all() 이다.  any() 가 아니다.
    점검부 응답에도 master 가 있으므로, any() 로 쓰면 record 라벨로 저장돼도 통과한다.
    키 하나로는 라벨을 구분하지 못한다 — v1 최대 사고가 그것이다.
    """
    if res.status != "ok":
        return True  # empty · not_found · error 는 검증 대상이 아니다
    # ★★★★★ 09-03 — ★ **HTML 창구는 ★ 키로 못 잰다.**
    #   ★ `required_keys` 는 ★ JSON 의 열쇠다 — ★ HTML 에는 그런 것이 없다.
    #   ★ 실측 09-03 — ★ BMW 상세 194건이 ★ `ok` 인데 ★ **형식 검증 거부 194건**이었다.
    #   ★★ 「비어 있지 않은가」만 본다 — ★ 내용은 ★ **파서가 본다** (층을 지킨다)
    if str(getattr(spec, "root_type", "") or "") == "html":
        return bool(str(res.raw or "").strip())
    body = res.raw
    if spec.root_type == "array":
        if not isinstance(body, list):
            return False
        if not body:
            return True  # 빈 배열은 정상 (3장 STEP 32)
        return all(k in body[0] for k in spec.required_keys)
    return isinstance(body, dict) and all(k in body for k in spec.required_keys)


def reject_reason(res: FetchResult, spec: EndpointSpec) -> str:
    """어느 required_key 가 없었는가.  「몇 건 거부」만으로는 못 고친다."""
    body = res.raw
    if spec.root_type == "array":
        if not isinstance(body, list):
            return f"root_type=array 인데 {type(body).__name__} 이 왔다"
        head = body[0] if body else {}
    else:
        if not isinstance(body, dict):
            return f"root_type=object 인데 {type(body).__name__} 이 왔다"
        head = body
    missing = [k for k in spec.required_keys if k not in head]
    return f"required_keys 누락: {','.join(missing)}"
