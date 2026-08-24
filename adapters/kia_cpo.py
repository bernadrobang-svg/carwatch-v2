# -*- coding: utf-8 -*-
"""기아 인증중고차(CPO) 어댑터 — URL · 헤더 (1장 STEP 11).

지시서   `docs/KIA_CPO_API.md` · 명령서 `ORDER_20260822_r515.md` 3-1
근거     ★ 인증·토큰·암호화가 없다.  robots.txt 자체가 404 다 (규칙이 없다)
실측     2026-08-23 · 운영 서버(43.201.16.78)에서 직접
        목록 `GET /api/search/?size=100` → 200 · totalElements 1,020
        ★ 쪽넘김은 ★ 커서다 — 줄마다 `cursors: [wishCount, id]` 가 온다.
          ★ 다음 쪽은 ★ `&cursors=A&cursors=B` 로 ★ 같은 이름을 두 번 넘긴다
          ★ `cursors=A,B` 로 한 번에 넘기면 ★ 첫 쪽이 그대로 온다 (실측)
        ★ 12쪽에 1,020건 전부를 받았다
값규칙   ★ 차종 질의가 없다.  ★ 전부 받아 ★ 우리 차종에 맞춘다 (TARGET_KEY_MAP)
금지     사이트 이름을 판정 코드에 박는 것 (V3-55)
금지     robots 가 막은 경로를 두드리는 것 — ★ 여기는 robots 가 없다
"""
from __future__ import annotations

import json
import os

from urllib.parse import quote

from contracts import EndpointSpec, Request, TargetSpec
from errors import PolicyError

SITE_CODE = "kia_cpo"

# ── 형식 검증 근거 (STEP 18) ─────────────────────────────────────────
# ★ 실측한 키만 적는다.  「그 응답이 맞는지」를 보는 최소 집합이다
_SCHEMA: dict[str, EndpointSpec] = {
    "list": EndpointSpec(
        kind="list",
        scope="target",
        required_keys=["content", "totalElements"],
        root_type="object",
        per_call="매물 100",
    ),
    # ★ 한 경로가 상세·성능·보험·보증·정비를 함께 준다 (KIA_CPO_API 3장)
    "detail": EndpointSpec(
        kind="detail",
        scope="listing",
        required_keys=["id", "car"],
        root_type="object",
        per_call="매물 1",
    ),
}

LISTING_ENDPOINT_KINDS: tuple[str, ...] = ("detail",)


def load_config(root: str = ".") -> dict:
    with open(os.path.join(root, "config", "endpoints.json"),
              encoding="utf-8") as f:
        got = json.load(f).get(SITE_CODE)
    if not got:
        raise PolicyError(
            "config/endpoints.json 에 kia_cpo 가 없다",
            endpoint="*", step="STEP 17")
    return got


class KiaCpoAdapter:
    """SiteAdapter 구현 (1장 STEP 11).

    ★ 목록에 차종 질의가 없다 — ★ 전부 받는다.  거르는 것은 우리 쪽 일이다
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
                "config/endpoints.json kia_cpo.headers 가 비어 있다",
                endpoint="*", step="STEP 25a")
        return h

    def list_url(self, target: TargetSpec, page: int = 1,
                 cursors: list | None = None,
                 names: list | None = None) -> Request:
        """목록.  ★ 커서 방식이다 — page 는 안 쓴다.

        ★★ 08-25 — ★ **좁혀 받는다** (명령서 3-1).  ★ `modelCodeNames`(복수형 · 한글).
          ★ ★ 규격 실측 ★ 1,020 → **76** (`KIA_CPO_API` · 개정 543)
          ★ ★ 이름은 ★ `targets.json` 의 `site_query.kia_cpo` 가 정본이다 (S14) —
            ★ 코드에 차종을 박지 않는다 (금지 6)
        ★ cursors 는 앞 쪽 ★ 마지막 줄의 `cursors` 를 그대로 넘긴다
        """
        del target, page
        url = self._base + self._paths["list"]
        for one in names or ():
            url += f"&modelCodeNames={quote(str(one))}"
        if cursors:
            url += "".join(f"&cursors={c}" for c in cursors)
        return Request("GET", url, self.headers(), self._timeout)

    def detail_urls(self, source_id: str) -> list[Request]:
        """매물당 1종.  ★ 한 경로가 전부를 준다 (KIA_CPO_API 3장)."""
        return [Request("GET",
                        self._base + self._paths[k].format(source_id=source_id),
                        self.headers(), self._timeout)
                for k in LISTING_ENDPOINT_KINDS]

    def facet_urls(self, target: TargetSpec) -> list[Request]:
        """차종 목록 · 조건.  ★ 둘 다 열려 있다 (실측)."""
        del target
        return [Request("GET", self._base + self._paths[k],
                        self.headers(), self._timeout)
                for k in ("facet_models", "facet_conditions")]

    def endpoint_schema(self) -> dict[str, EndpointSpec]:
        return dict(_SCHEMA)
