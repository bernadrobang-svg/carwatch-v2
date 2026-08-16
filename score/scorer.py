# -*- coding: utf-8 -*-
"""채점 · 분모 (L7).

지시서   7장 STEP 83 · 0장 STEP 7.1 (분모 시험 6종)
근거     분모의 절반이 빠진 매물과 전부 있는 매물을 같은 등급표로 비교할 수 없다
값규칙   ★ 분모는 만점 그대로다.  555 다.  예외 없다 (개정 289)
         못 본 축은 0점이다 — 「우리가 못 받았다」는 그 차의 사정이 아니다
         excluded 는 「왜 0점인가」의 사유로만 남긴다.  분모 조정에 쓰지 않는다
금지     분모를 줄이는 것.  어떤 사유로도
         ★ 08-16 실측 — 330/350 = 94.3% S · 330/555 = 59.5% D.
           같은 차가 분모에 따라 등급이 갈렸다.  못 찾을수록 좋은 등급이 됐다
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
# ★ REASON_MIN_DENOM 은 폐기됐다 (개정 298).  분모로 등급을 막지 않는다


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

    # ★ applicable 은 「확인한 축의 배점 합」이다.  분모가 아니다.
    #   화면이 「555점 중 330점 · 205점은 확인하지 못했습니다」를 내는 데 쓴다
    applicable = total - excluded_points
    fail = "; ".join(absolute) if absolute else None

    if applicable <= 0:
        # 한 축도 못 봤다.  점수를 매길 근거가 하나도 없다
        return ScoreResult(0.0, total, 0.0, earned, "NOT_RATED", fail, by_axis,
                           REASON_ALL_MISSING)

    # ★ 분모는 언제나 만점이다.  못 본 축은 0점으로 남는다 (개정 289)
    return ScoreResult(round(earned, 2), total, applicable, earned,
                       None, fail, by_axis, None)
