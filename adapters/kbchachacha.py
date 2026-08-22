# -*- coding: utf-8 -*-
"""KB차차차 어댑터 — URL · 헤더 (1장 STEP 11).

지시서   `docs/KBCHACHACHA_API.md` · 명령서 `ORDER_20260822_r515.md` 3-2
근거     ★ 인증·토큰·암호화가 없다.  robots 는 로그인·내차팔기·리뷰상세만 막는다
실측     2026-08-23 · 운영 서버에서 직접
        목록 `GET /public/search/list.empty?page=N` → 200 · 302KB · ★ 쪽당 40건
        상세 `GET /public/car/detail.kbc?carSeq=N`  → 200 · 246~275KB
값규칙   ★★ 봇 차단을 ★ 반드시 가른다 — 200 인데 본문이 2,759B 「로봇 여부 확인 중」
        ★ 「없음」으로 저장하면 ★ 28% 가 「사고 없음·압류 없음」이 된다
금지     robots 가 막은 경로를 두드리는 것 — 로그인 · 내차팔기 · 리뷰상세
"""
from __future__ import annotations

import json
import os

from contracts import EndpointSpec, Request, TargetSpec
from errors import PolicyError

SITE_CODE = "kbchachacha"

# ★★ 봇 차단을 가르는 기준 (KBCHACHACHA_API 1-1).  ★ 코드에 박지 않고 config 가 정본이다
BOT_MARK = "로봇 여부 확인"
BOT_MIN_BYTES = 10_000

_SCHEMA: dict[str, EndpointSpec] = {
    "list": EndpointSpec(
        kind="list",
        scope="target",
        required_keys=[],          # ★ HTML 이다.  JSON 키가 없다
        root_type="html",
        per_call="매물 40",
    ),
    "detail": EndpointSpec(
        kind="detail",
        scope="listing",
        required_keys=[],
        root_type="html",
        per_call="매물 1",
    ),
}


def load_config(root: str = ".") -> dict:
    with open(os.path.join(root, "config", "endpoints.json"),
              encoding="utf-8") as f:
        got = json.load(f).get(SITE_CODE)
    if not got:
        raise PolicyError(
            "config/endpoints.json 에 kbchachacha 가 없다",
            endpoint="*", step="STEP 17")
    return got


def is_bot_wall(body: str | None, cfg: dict | None = None) -> bool:
    """★★ 봇 차단인가 (KBCHACHACHA_API 1-1).

    ★ 200 인데 ★ 본문이 2,759B 「로봇 여부 확인 중」 한 줄로 올 때가 있다
    ★ 이것은 ★ 「없음」이 아니라 ★ 「우리가 못 받았다」다 (개정 289·434 셋째)
    ★ 판정을 ★ 여기 하나에 둔다 — 부르는 쪽마다 다르게 세면 28% 가 샌다
    """
    if body is None:
        return True
    least = int((cfg or {}).get("bot_min_bytes") or BOT_MIN_BYTES)
    mark = (cfg or {}).get("bot_mark") or BOT_MARK
    return len(body) < least or mark in body


class KbChaChaChaAdapter:
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
                "config/endpoints.json kbchachacha.headers 가 비어 있다",
                endpoint="*", step="STEP 25a")
        return h

    def list_url(self, target: TargetSpec, page: int = 1) -> Request:
        """목록.  ★ 쪽넘김이다 — 무한스크롤이 아니다 (실측)."""
        del target
        url = self._base + self._paths["list"].format(page=int(page))
        return Request("GET", url, self.headers(), self._timeout)

    def detail_urls(self, source_id: str) -> list[Request]:
        """매물당 1종.  ★ 한 쪽이 245~275KB 로 전부를 준다."""
        return [Request("GET",
                        self._base + self._paths["detail"].format(
                            source_id=source_id),
                        self.headers(), self._timeout)]

    def facet_urls(self, target: TargetSpec) -> list[Request]:
        """제조사 · 옵션 facet.  ★ 둘 다 열려 있다."""
        del target
        return [Request("GET", self._base + self._paths[k],
                        self.headers(), self._timeout)
                for k in ("facet_maker", "facet_option")]

    def endpoint_schema(self) -> dict[str, EndpointSpec]:
        return dict(_SCHEMA)
