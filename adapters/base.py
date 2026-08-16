# -*- coding: utf-8 -*-
"""사이트 어댑터 인터페이스.

지시서   1장 STEP 11
근거     사이트 종속 코드를 Adapter 와 Parser 매핑으로 격리한다.
         CORE · Analyzer · Scorer 는 변경하지 않는 것이 목표다.
금지     「어댑터 하나만 바꾸면 된다」는 식의 과도한 추상화.
         이 파일의 목적은 바뀌지 않아야 하는 곳을 명시하는 것이다.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from contracts import EndpointSpec, Request, TargetSpec


@runtime_checkable
class SiteAdapter(Protocol):
    site_code: str  # 'encar' · 'kbchachacha'

    def list_url(self, target: TargetSpec, page: int) -> Request: ...

    def detail_urls(self, source_id: str) -> list[Request]: ...

    def facet_urls(self, target: TargetSpec) -> list[Request]: ...

    def endpoint_schema(self) -> dict[str, EndpointSpec]: ...


# 사이트 추가 시 필요한 것 (STEP 11) — 어댑터 하나가 아니다.
#   Adapter          URL · 헤더 · 쿼리 조립          ← 이 파일
#   Parser 매핑       응답 경로 → CORE 필드           ← parse/{site}/
#   EndpointSpec     kind · required_keys · root_type ← endpoint_schema()
#   Dictionary 매핑   사이트 코드 → CORE 열거값        ← 4장
#   Target 매핑      사이트 차종 표현 → target_key    ← config/targets.json
#   사이트 전용 검증   그 사이트에만 있는 제약           ← validate/
