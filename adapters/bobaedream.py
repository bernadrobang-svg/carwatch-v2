# -*- coding: utf-8 -*-
"""보배드림 어댑터 — URL · 헤더 (1장 STEP 11).

지시서   `docs/BOBAEDREAM_API.md`
근거     ★★ 호스트가 ★ `m.bobaedream.co.kr` 다 — ★ 모바일이다.  `www.` 는 다른 화면이다
        ★ 가이드가 PC 주소로 두드려 81B 를 받고 「상세를 못 봤다」로 적었다 (개정 526)
값규칙   ★ PC 는 EUC-KR · ★ 모바일은 ★ UTF-8 이다 — ★ 섞지 마라
        ★ 인증·토큰·쿠키가 ★ 없다.  ★ 모바일 UA 만 있으면 된다
금지     ★ `www.` 로 상세를 부르는 것
"""
from __future__ import annotations

import json
import os

from contracts import EndpointSpec, Request, TargetSpec
from errors import PolicyError

SITE_CODE = "bobaedream"

_SCHEMA: dict[str, EndpointSpec] = {
    "list": EndpointSpec(kind="list", scope="target", required_keys=[],
                         root_type="html", per_call="매물 50"),
    "detail": EndpointSpec(kind="detail", scope="listing", required_keys=[],
                           root_type="html", per_call="매물 1"),
}


def load_config(root: str = ".") -> dict:
    with open(os.path.join(root, "config", "endpoints.json"),
              encoding="utf-8") as f:
        got = json.load(f).get(SITE_CODE)
    if not got:
        raise PolicyError("config/endpoints.json 에 bobaedream 이 없다",
                          endpoint="*", step="STEP 17")
    return got


class BobaedreamAdapter:
    """SiteAdapter 구현 (1장 STEP 11)."""

    site_code = SITE_CODE

    def __init__(self, cfg: dict) -> None:
        self._cfg = cfg
        self._base = cfg["base_url"]
        self._paths = cfg["paths"]
        self._timeout = float(cfg["timeout_sec"])

    def headers(self) -> dict[str, str]:
        h = {k: v for k, v in (self._cfg.get("headers") or {}).items() if v}
        if not h:
            raise PolicyError(
                "config/endpoints.json bobaedream.headers 가 비어 있다",
                endpoint="*", step="STEP 25a")
        return h

    def list_url(self, target: TargetSpec, page: int = 1,
                 maker: str | None = None) -> Request:
        """목록.  ★ 쪽당 50건 (실측).  ★ `maker_no` 로 좁힐 수 있다."""
        del target
        path = self._paths["list"].format(page=int(page))
        if maker:
            path += f"?maker_no={maker}"
        return Request("GET", self._base + path, self.headers(), self._timeout)

    def detail_urls(self, source_id: str) -> list[Request]:
        """매물당 1종.  ★ 한 쪽이 77~90KB 로 전부를 준다."""
        return [Request("GET",
                        self._base + self._paths["detail"].format(
                            source_id=source_id),
                        self.headers(), self._timeout)]

    def endpoint_schema(self) -> dict[str, EndpointSpec]:
        return dict(_SCHEMA)
