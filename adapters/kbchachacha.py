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
# ★★ 끝 판정 — ★ 크기로 완전히 갈린다 (KBCHACHACHA_API 1a · 개정 572)
#   봇 차단  2,759B 「로봇 확인 중」      → ★ 재시도한다
#   진짜 끝  3,585B 「차량이 없습니다」   → ★ 거기서 멈춘다
#   ★ 「carSeq 가 0이면 끝」으로 적지 마라 — ★ X3 14·15쪽은 71KB·25KB 인데 0건이다
END_MARK = "차량이 없습니다"

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


def is_real_end(body: str | None, cfg: dict | None = None) -> bool:
    """★ 진짜 끝인가 — ★ 봇 차단과 ★ 갈라야 한다 (KBCHACHACHA_API 1a).

    ★ 봇 차단이면 ★ 여기서 False 다 — ★ `is_bot_wall` 이 먼저 잡는다
    ★ 크기가 커도 ★ 0건인 꼬리 쪽이 있다 (X3 14·15쪽) — ★ 그것도 끝이다
    """
    if body is None:
        return False
    mark = (cfg or {}).get("end_mark") or END_MARK
    return mark in body


def is_bot_wall(body: str | None, cfg: dict | None = None) -> bool:
    """★★ 봇 차단인가 (KBCHACHACHA_API 1-1).

    ★ 200 인데 ★ 본문이 2,759B 「로봇 여부 확인 중」 한 줄로 올 때가 있다
    ★ 이것은 ★ 「없음」이 아니라 ★ 「우리가 못 받았다」다 (개정 289·434 셋째)
    ★ 판정을 ★ 여기 하나에 둔다 — 부르는 쪽마다 다르게 세면 28% 가 샌다
    """
    if body is None:
        return True
    # ★★ 진짜 끝 쪽은 ★ 3,585B 라 ★ 크기만 보면 ★ 봇 차단으로 읽힌다 —
    #   ★ 그러면 ★ 끝에서 3회씩 다시 부르고 ★ 멈추지도 못한다.
    #   ★ 실측 08-23 — X3 16쪽이 정확히 그 꼴이다 (3,585B · 「차량이 없습니다」)
    if is_real_end(body, cfg):
        return False
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

    def list_url(self, target: TargetSpec, page: int = 1,
                 maker: str | None = None, klass: str | None = None) -> Request:
        """목록.  ★ 쪽넘김이다 — 무한스크롤이 아니다 (실측).

        ★ `maker`·`klass` 를 주면 ★ 좁혀 부른다 (KBCHACHACHA_API 1a) —
          ★ 전체 164,490건이 아니라 ★ 우리 대상 2,084건만 받는다 (명령서 3-0)
        """
        del target
        if maker and klass:
            path = self._paths["list_narrow"].format(
                page=int(page), maker=maker, klass=klass)
        else:
            path = self._paths["list"].format(page=int(page))
        return Request("GET", self._base + path, self.headers(), self._timeout)

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
