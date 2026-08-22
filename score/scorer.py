# -*- coding: utf-8 -*-
"""채점 · 분모 (L7).

지시서   7장 STEP 83 · 0장 STEP 7.1 (분모 시험 6종)
근거     분모의 절반이 빠진 매물과 전부 있는 매물을 같은 등급표로 비교할 수 없다
값규칙   ★ 분모는 만점 그대로다.  555 다.  예외 없다 (개정 289 · 298)
         ★ 등급은 취향을 뺀 505 로 매긴다 (개정 292).  순위는 555 로 매긴다
         못 본 축은 0점이다 — 「우리가 못 받았다」는 그 차의 사정이 아니다
         excluded 는 「왜 0점인가」의 사유로만 남긴다.  분모 조정에 쓰지 않는다
금지     분모를 줄이는 것.  어떤 사유로도
         ★ 08-16 실측 — 330/350 = 94.3% S · 330/555 = 59.5% D.
           같은 차가 분모에 따라 등급이 갈렸다.  못 찾을수록 좋은 등급이 됐다
         보증 잔여 가치를 실구매가에서 차감하는 것 — 가격·보증 이중 계산
"""
from __future__ import annotations

from dataclasses import dataclass

from analyze.axes import (
    COMPONENTS, GRADE_EXCLUDED_AXES, ScoringPolicy, axis_of,
)
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
    # 뺀 것 (키, 점수, 문구).  ★ 화면에 그대로 낸다 (개정 322)
    penalties: tuple = ()
    # ★ 등급용 — ①+②+③ = 505.  취향(④)을 뺀 것이다 (개정 292 · V3-46)
    grade_earned: float = 0.0
    grade_base: float = 0.0
    # ★ 근거가 있는 축의 배점 합 (개정 325).  applicable 과 다르다 —
    #   「원문을 안 받아 0점」은 확인한 것이 아니다
    confirmed: float = 0.0
    # 더한 것 (키, 점수, 문구) — 개정 380.  ★ 축이 아니다.  분모를 안 늘린다
    bonuses: tuple = ()


REASON_ALL_MISSING = "전 축 수집 실패"
REASON_CORE_MISSING = "핵심 축을 확인하지 못했다"
REASON_BANNED_ONLY = "금지 근거만 존재"
# ★ REASON_MIN_DENOM 은 폐기됐다 (개정 298).  분모로 등급을 막지 않는다


# 근거가 아닌 사유 (개정 325).  ★ 이 사유로 0점이면 「확인했다」가 아니다
UNCONFIRMED_SOURCES: frozenset[str] = frozenset({
    "missing", "na", "rule_or_source_missing", "market_sample_short",
    "expected_unavailable", "coefficient_out_of_range", "age_unknown",
    "ladder_short", "option_top_unknown", "gate_closed", "unclassified",
    "origin_price_missing", "curve_sample_short", "unknown",
})


def score(v: Verdict, policy: ScoringPolicy,
          absolute: list[str] | None = None,
          snapshot=None) -> ScoreResult:
    total = float(policy.raw["total_points"])
    if policy.points_sum() != policy.raw["total_points"]:
        raise PolicyError(
            f"배점 합 {policy.points_sum()} != total_points "
            f"{policy.raw['total_points']} (STEP 128)", step="STEP 128")
    # ★ 핵심 축이 빠지면 등급을 매기지 않는다 (개정 287).
    #   분모를 줄여 비율을 높이는 것이 등급 인플레다 —
    #   실측 08-17: 사고를 모르는데 등급이 난 것 1,131건
    core = tuple(policy.raw.get("score_core_axes") or ())
    excluded_points = 0.0
    earned = 0.0
    grade_earned = 0.0
    grade_base = 0.0
    confirmed = 0.0
    by_axis: dict[str, float] = {}

    for comp in COMPONENTS:
        if policy.skipped(comp):
            # ★ 스킵은 전 매물이다.  총점에서 빠졌으므로 분모에서도 뺄 것이 없다
            continue
        weight = float(policy.comp(comp))
        # ★ 등급은 취향을 뺀 505 로 매긴다.  분모는 못 봐도 505 그대로다
        for_grade = axis_of(comp) not in GRADE_EXCLUDED_AXES
        if for_grade:
            grade_base += weight
        if comp in v.excluded or comp not in v.values:
            excluded_points += weight
            continue
        value = v.values[comp]
        if value is None:
            # excluded 없이 NULL 이 오면 판정기가 계약을 어긴 것이다
            excluded_points += weight
            continue
        earned += float(value)
        # ★ 확인율은 「근거가 있는 축」만 센다 (개정 325).
        #   「카탈로그를 안 받아 0점」을 확인했다고 하면 화면이 거짓말을 한다
        if v.sources.get(comp) not in UNCONFIRMED_SOURCES:
            confirmed += weight
        if for_grade:
            grade_earned += float(value)
        by_axis[axis_of(comp)] = by_axis.get(axis_of(comp), 0.0) + float(value)

    # ★ applicable 은 「확인한 축의 배점 합」이다.  분모가 아니다.
    #   화면이 「555점 중 330점 · 205점은 확인하지 못했습니다」를 내는 데 쓴다
    applicable = total - excluded_points
    fail = "; ".join(absolute) if absolute else None

    if applicable <= 0:
        # 한 축도 못 봤다.  점수를 매길 근거가 하나도 없다 (분모 시험 D)
        # ★ 핵심 축보다 먼저 본다 — 「전 축 실패」가 더 정확한 사유다
        return ScoreResult(0.0, total, 0.0, earned, "NOT_RATED", fail, by_axis,
                           REASON_ALL_MISSING, (), grade_earned, grade_base,
                           confirmed)

    missing_core = [c for c in core
                    if c in v.excluded or v.values.get(c) is None]
    if missing_core:
        return ScoreResult(0.0, total, applicable, earned, "NOT_RATED", fail,
                           by_axis,
                           f"{REASON_CORE_MISSING} — {' · '.join(missing_core)}",
                           (), grade_earned, grade_base, confirmed)

    # ★ 마이너스는 총점에서 뺀다.  0 아래로도 내려간다 (개정 322)
    cut = _penalties(v, policy, snapshot)
    minus = sum(p for _k, p, _w in cut)
    # ★ 가점은 더한다 (개정 380).  축이 아니다 —
    #   분모를 안 늘린다.  가점이 크면 100%를 넘고 그대로 낸다
    plus_rows = _bonuses(policy, snapshot)
    plus = sum(p for _k, p, _w in plus_rows)

    # ★ 분모는 언제나 만점이다.  못 본 축은 0점으로 남는다 (개정 289)
    return ScoreResult(round(earned + minus + plus, 2), total, applicable,
                       earned + minus + plus, None, fail, by_axis, None,
                       tuple(cut), round(grade_earned + minus + plus, 2),
                       grade_base, confirmed, bonuses=tuple(plus_rows))


def _bonuses(policy: ScoringPolicy, snapshot) -> list:
    """더할 것들 (개정 380).  ★ 없으면 아무 일도 없다."""
    if snapshot is None:
        return []
    from score.penalty import bonuses_of

    return bonuses_of(policy, snapshot)


def _penalties(v: Verdict, policy: ScoringPolicy, snapshot) -> list:
    if snapshot is None:
        return []
    # ★ 개정 491 — 축별로 묶어 합산한 뒤 그 축 배점에서 자른다.
    #   ★ 자른 것을 감추지 않는다 — 되돌린 몫이 「cap:축」 줄로 함께 온다
    from score.penalty import cap_penalties, penalties_of

    return cap_penalties(penalties_of(v, policy, snapshot), policy)
