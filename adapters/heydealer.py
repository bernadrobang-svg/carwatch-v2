# -*- coding: utf-8 -*-
"""헤이딜러 어댑터 — 토큰 두 걸음 (명령서 37 · `docs/HEYDEALER_API.md` 0장).

지시서   `docs/HEYDEALER_API.md` 0장 · 명령서 37-1
근거     ★★ 500 은 「고장」이 아니라 「토큰 없이 불렀다」였다 (개정 694 · 오판 97)
실측     2026-08-24 · 서버(43.201.16.78)에서 직접
        ① POST api.heydealer.com/v2/customers/web/initialize_app/
             본문 {"referrer_url": "https://www.heydealer.com/"}   ★ 없으면 400
             → {"token": "eyJ…"}                                   ★ JWT
        ② GET  market-api.heydealer.com/v2/customers/web/market/cars/
             헤더 App-Os: web · Authorization: Bearer {token}       ★ 없으면 500
             → 200 · ★ 리스트로 온다 (감싸는 객체가 없다)
값규칙   ★ 목록은 쪽당 10건이다.  10 이면 다음 쪽이 있다
        ★ 연료는 ★ 목록에 없다 — ★ 상세의 `detail_info.fuel_display` 다 (실측 08-24)
        ★ 상세에 ★ `car_number`(차량번호) 가 있다 — ★ 5a 짝짓기가 된다
금지     ★ 토큰을 저장소에 적는 것 (명령서 37-3)
        ★ 응답의 리스트를 `results` 로 감싸 벗기는 것 — 원래 리스트다
"""
from __future__ import annotations

import json
import urllib.request

from contracts import EndpointSpec, Request, TargetSpec
from errors import PolicyError

SITE_CODE = "heydealer"

# ★ 한 쪽에 오는 최대 건수.  이만큼 오면 다음 쪽이 있다 (명령서 37-3 ③)
PAGE_SIZE = 10

_SCHEMA: dict[str, EndpointSpec] = {
    "list": EndpointSpec(
        kind="list", scope="target", required_keys=[],
        root_type="array", per_call=f"매물 {PAGE_SIZE}",
    ),
    "detail": EndpointSpec(
        kind="detail", scope="listing",
        required_keys=["hash_id", "detail_info"],
        root_type="object", per_call="매물 1",
    ),
}


def schema(kind: str) -> EndpointSpec:
    if kind not in _SCHEMA:
        raise PolicyError(f"없는 갈래: {kind}", endpoint=kind, step="STEP 18")
    return _SCHEMA[kind]


class HeydealerAdapter:
    """SiteAdapter 구현 (1장 STEP 11).

    ★ 토큰은 ★ 바퀴마다 새로 받는다 — ★ JWT 라 만료가 있다 (명령서 37-3)
    """

    site_code = SITE_CODE

    def __init__(self, cfg: dict) -> None:
        self._cfg = cfg
        self._base = cfg["base_url"]
        self._paths = cfg["paths"]
        self._timeout = float(cfg["timeout_sec"])
        self._token: str | None = None

    def headers(self) -> dict[str, str]:
        h = {k: v for k, v in (self._cfg.get("headers") or {}).items() if v}
        if not h:
            raise PolicyError(
                "config/endpoints.json heydealer.headers 가 비어 있다",
                endpoint="*", step="STEP 25a")
        if self._token:
            h = dict(h, Authorization=f"Bearer {self._token}")
        return h

    def token(self, force: bool = False) -> str:
        """① 손님 토큰을 받는다.  ★ 저장소에 안 적는다 (명령서 37-3)."""
        if self._token and not force:
            return self._token
        url = self._cfg.get("token_api_url")
        if not url:
            raise PolicyError(
                "config/endpoints.json heydealer.token_api_url 이 없다",
                endpoint="token", step="STEP 17a")
        body = json.dumps(
            {"referrer_url": self._cfg.get("token_referrer")
             or "https://www.heydealer.com/"}).encode()
        head = {k: v for k, v in (self._cfg.get("headers") or {}).items() if v}
        head["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=body, method="POST",
                                     headers=head)
        with urllib.request.urlopen(req, timeout=self._timeout) as res:
            got = json.loads(res.read())
        tok = got.get("token")
        if not tok:
            raise PolicyError("헤이딜러가 토큰을 안 줬다", endpoint="token",
                              step="STEP 17a")
        self._token = tok
        return tok

    def list_url(self, target: TargetSpec | None, page: int,
                 query: dict | None = None) -> Request:
        """② 목록.  ★ 해시 셋(brand · model-group · model)과 ★ `fuel` 로 좁힌다.

        ★ 해시는 `targets.json` 의 `site_query.heydealer` 가 정본이다 (S14)
        ★★★★ 08-29 (`HEYDEALER_API.md`) — ★ `fuel` 을 더했다.
          ★ 사이트가 `filters/` 로 ★ 연료를 준다 —
            휘발유 gasoline · 경유 diesel · LPG lpg · 바이퓨얼 bifuel ·
            전기 electric · 수소 hydrogen · 하이브리드 hybrid
          ★ ★ `&fuel=electric` → ★ **200건** (빈 쪽까지 · 실측 08-29).
          ★ ★ 앞서는 이 셋뿐이라 ★ 연료로만 좁힌 질의가 ★ 주소에 아무것도 못 실어
          ★ ★ **조건 없는 전량 1,330건**을 끌어왔다 (평소 207)
        """
        del target
        path = self._paths["list"].format(page=page)
        for key in ("brand", "model-group", "model", "fuel"):
            val = (query or {}).get(key)
            if val:
                path += f"&{key}={val}"
        return Request(method="GET", url=self._base + path,
                       headers=self.headers(), timeout_sec=self._timeout)

    def detail_urls(self, source_id: str) -> list[Request]:
        return [Request(
            method="GET",
            url=self._base + self._paths["detail"].format(source_id=source_id),
            headers=self.headers(), timeout_sec=self._timeout)]
