# -*- coding: utf-8 -*-
"""축 판정 계약.

지시서   7장 정의서 · STEP 67 (축 설계 원칙) · STEP 68 (배점) · STEP 83 (분모)
근거     Axis 는 집계·표시 단위 7개.  Component 는 판정 단위 17개.
         분모 제외는 Component 단위로 일어난다.
금지     ctx 밖의 것을 읽는 것 — DB · 네트워크 · 시각 · 난수.
         v 에 직접 대입하는 것.  기록은 put() 으로만 한다.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from contracts import ListingSnapshot, TargetSpec


@dataclass(frozen=True)
class AxisSpec:
    axis: str
    max_points: int
    value_domain: tuple
    excludable: bool
    sources: list[tuple[int, str]]
    banned: list[str]
    rationale_ref: str


@dataclass(frozen=True)
class DictionarySet:
    """Analyzer 가 읽는 사전.  DB 접근을 대신한다 (순수 함수 유지)."""

    option_names: dict[str, str] = field(default_factory=dict)
    # 선택 옵션가 (원).  ★ 사양 축의 「옵션 합」 백분위에 쓴다 (개정 292 ③)
    option_prices: dict[str, int] = field(default_factory=dict)
    option_descriptions: dict[str, str] = field(default_factory=dict)
    tint_keywords: tuple[str, ...] = ()
    color_grade: dict[str, str] = field(default_factory=dict)
    # ★ 열거된 선호·중립 밖은 전부 기피다.  추정이 아니라 여집합 규칙이다 (STEP 80)
    color_default: str | None = None


@dataclass(frozen=True)
class ScoringPolicy:
    """config/scoring.json.  코드에 임계값을 박지 않는다 (V4-13).

    components 는 두 형태다 (13장 STEP 128).
        "spec.hud": 20                                  일반
        "spec.tinting": {"points": 5, "skipped": true}  스킵
    ★ 스킵은 전 매물이다.  excluded 는 그 매물만이다
    필수   Σ(skipped 아닌 points) == total_points
    """

    raw: dict

    def comp(self, name: str) -> int:
        """스킵된 성분은 0 이다.  총점에도 분모에도 들어가지 않는다."""
        v = self.raw["components"][name]
        if isinstance(v, dict):
            return 0 if v.get("skipped") else int(v["points"])
        return int(v)

    def skipped(self, name: str) -> bool:
        v = self.raw["components"].get(name)
        return isinstance(v, dict) and bool(v.get("skipped"))

    def active_components(self) -> list[str]:
        return [c for c in self.raw["components"] if not self.skipped(c)]

    def points_sum(self) -> int:
        return sum(self.comp(c) for c in self.raw["components"])

    def rule(self, name: str):
        return self.raw["axis_rules"][name]


@dataclass(frozen=True)
class AxisContext:
    snapshot: ListingSnapshot
    dicts: DictionarySet
    policy: ScoringPolicy
    target: TargetSpec
    target_config: dict = field(default_factory=dict)


# Component 목록 — result_axis 는 이 단위로 저장한다 (STEP 68 · 개정 292)
# ★ 갈래별 합   값 250 · 상태 180 · 사양 75 · 사이트 보증 50 · 취향 50 = 605
#   등급은 ①②③⑤ = 555 로 매긴다.  ④ 취향은 순위에만 쓴다 (개정 306)
COMPONENTS: tuple[str, ...] = (
    "value.market", "value.depreciation", "value.mileage",
    "state.accident", "state.frame", "state.repair",
    "state.usage", "state.warranty",
    "spec.trim", "spec.options",
    "site.certified", "site.inspection", "site.warranty",
    "taste.hud", "taste.sunroof", "taste.color", "taste.picked",
)

# 등급에 들어가지 않는 갈래 (개정 292 ④).  ★ 취향으로 등급이 오르내리면 안 된다
GRADE_EXCLUDED_AXES: tuple[str, ...] = ("taste",)


def axis_of(component: str) -> str:
    """'spec.hud' → 'spec'.  집계는 Component → Axis → 총점 순이다."""
    return component.split(".")[0]
