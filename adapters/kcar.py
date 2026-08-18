# -*- coding: utf-8 -*-
"""K카 어댑터 — URL · 헤더 (12장 · STEP 11).

지시서   `docs/KCAR_API.md` · 12장 다중 사이트
근거     마스터 지시 — 「케이카는 최고급 우선이야」.  K카 직영은 무조건 보증 50 (개정 365)
실측     2026-08-18 · 서버(43.201.16.78)에서 직접 · 표본 `EC61393706`
        ★ 문서에 없던 호스트를 번들에서 뽑았다 — `mapi.kcar.com`
          api.kcar.com · marketm-api.kcar.com 은 전부 404 였다
        ★ /bc/detail/popup/* 은 API 가 아니라 SPA 껍데기다 (2.1MB HTML)
값규칙   ★ 한 경로가 전부를 준다.  엔카처럼 4종으로 나뉘지 않는다
        상세 · 옵션 42 · 보증 5 · 타이어 5 · 소유이력 · 보험 · 진단
        ★ 타이어 트레드가 여기 있다 (tirResQty) — 엔카는 401 이라 못 받는다
금지     사이트 이름을 판정 코드에 박는 것 (V3-55)
"""
from __future__ import annotations

import json
import os

from contracts import EndpointSpec, Request, TargetSpec
from errors import PolicyError

SITE_CODE = "kcar"

# ── 형식 검증 근거 (STEP 18) ─────────────────────────────────────────
# ★ 실측한 키만 적는다.  「그 응답이 맞는지」를 보는 최소 집합이다
_SCHEMA: dict[str, EndpointSpec] = {
    # 한 번에 전부 준다 — 상세 · 옵션 · 보증 · 타이어 · 소유이력 · 보험 · 진단
    "detail": EndpointSpec(
        kind="detail",
        scope="listing",
        required_keys=["data"],
        root_type="object",
        per_call="매물 1",
    ),
    # 점검 사진 · 점검 요약.  ★ 462B 로 작다
    "inspection": EndpointSpec(
        kind="inspection",
        scope="listing",
        required_keys=["data"],
        root_type="object",
        per_call="매물 1",
    ),
}

LISTING_ENDPOINT_KINDS: tuple[str, ...] = ("detail", "inspection")


def load_config(root: str = ".") -> dict:
    with open(os.path.join(root, "config", "endpoints.json"),
              encoding="utf-8") as f:
        got = json.load(f).get(SITE_CODE)
    if not got:
        raise PolicyError(
            "config/endpoints.json 에 kcar 가 없다",
            endpoint="*", step="STEP 17")
    return got


class KcarAdapter:
    """SiteAdapter 구현 (1장 STEP 11).

    ★ 목록은 아직 없다.  경로를 못 찾았다 (2026-08-18) —
      list_url 이 PolicyError 를 던진다.  조용히 빈 목록을 내지 않는다
    """

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
                "config/endpoints.json kcar.headers 가 비어 있다",
                endpoint="*", step="STEP 25a")
        return h

    def list_url(self, target: TargetSpec, page: int) -> Request:
        """★ 아직 못 찾았다.  지어내지 않는다 (STEP 17a).

        실측 2026-08-18 — mapi.kcar.com 에서 여섯 경로를 눌러 전부 404.
        m.kcar.com/bc/search/CarList 는 200 이나 SPA 껍데기(2.1MB HTML)다
        """
        del target, page
        raise PolicyError(
            "K카 목록 경로를 아직 못 찾았다 (docs/KCAR_API.md). "
            "상세는 source_id 를 알면 받을 수 있다",
            endpoint="list", step="STEP 17a")

    def detail_urls(self, source_id: str) -> list[Request]:
        """매물당 2종.  ★ 한 경로가 상세·옵션·보증·타이어를 함께 준다."""
        out = []
        for kind in LISTING_ENDPOINT_KINDS:
            url = self._base + self._paths[kind].format(source_id=source_id)
            out.append(Request("GET", url, self.headers(), self._timeout))
        return out

    def endpoint_schema(self) -> dict[str, EndpointSpec]:
        return dict(_SCHEMA)
