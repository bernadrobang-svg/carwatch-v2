# -*- coding: utf-8 -*-
"""채점 · 분모 (L7).

지시서   7장 STEP 83 · 0장 STEP 7.1 (분모 시험 6종)
근거     분모의 절반이 빠진 매물과 전부 있는 매물을 같은 등급표로 비교할 수 없다
값규칙   분모 = 555 − Σ(excluded Component 배점).  NULL 이 아니라 excluded 가 결정한다
금지     if value is None: denominator -= weight    모든 NULL 이 자동 제외된다
         if value is None: score = 0               모든 NULL 이 0점이 된다
         보증 잔여 가치를 실구매가에서 차감하는 것 — 가격·보증 이중 계산
"""
from __future__ import annotations

from dataclasses import dataclass

from analyze.axes import COMPONENTS, ScoringPolicy, axis_of
from errors import PolicyError
from analyze.verdict import Verdict


@dataclass(frozen=True)
class ScoreResult:
    score_total: float
    denominator: float
    applicable: float
    earned: float
    grade: str | None
    absolute_fail: str | None
    by_axis: dict[str, float]
    not_rated_reason: str | None


REASON_ALL_MISSING = "전 축 수집 실패"
REASON_BANNED_ONLY = "금지 근거만 존재"
REASON_MIN_DENOM = "분모 최소 기준 미만"


def score(v: Verdict, policy: ScoringPolicy,
          absolute: list[str] | None = None) -> ScoreResult:
    total = float(policy.raw["total_points"])
    if policy.points_sum() != policy.raw["total_points"]:
        raise PolicyError(
            f"배점 합 {policy.points_sum()} != total_points "
            f"{policy.raw['total_points']} (STEP 128)", step="STEP 128")
    excluded_points = 0.0
    earned = 0.0
    by_axis: dict[str, float] = {}

    for comp in COMPONENTS:
        if policy.skipped(comp):
            # ★ 스킵은 전 매물이다.  총점에서 빠졌으므로 분모에서도 뺄 것이 없다
            continue
        weight = float(policy.comp(comp))
        if comp in v.excluded or comp not in v.values:
            excluded_points += weight
            continue
        value = v.values[comp]
        if value is None:
            # excluded 없이 NULL 이 오면 판정기가 계약을 어긴 것이다
            excluded_points += weight
            continue
        earned += float(value)
        by_axis[axis_of(comp)] = by_axis.get(axis_of(comp), 0.0) + float(value)

    applicable = total - excluded_points
    fail = "; ".join(absolute) if absolute else None

    if applicable <= 0:
        return ScoreResult(0.0, 0.0, 0.0, earned, "NOT_RATED", fail, by_axis,
                           REASON_ALL_MISSING)
    ratio = applicable / total
    if ratio < float(policy.raw["min_denominator_ratio"]):
        return ScoreResult(0.0, applicable, applicable, earned, "NOT_RATED",
                           fail, by_axis, REASON_MIN_DENOM)

    final = earned / applicable * total
    return ScoreResult(round(final, 2), applicable, applicable, earned,
                       None, fail, by_axis, None)
