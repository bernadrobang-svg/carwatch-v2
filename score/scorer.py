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



def _certified_credit(policy: ScoringPolicy, snapshot) -> tuple:
    """★★ 인증중고차 몫 — ★ 근거 없는 축에 ★ 배점의 일부를 준다.

    ★★★ 마스터 08-28 — 「★ 볼보는 그 점수들을 안 받아도 돼.  ★ 80% 수준에 맞춰
      ★ 일괄로」 · 「★ K카는 줘도 돼」 · 「★ C 로 하자」(헤이딜러·리본카도).
    ★ 까닭 — ★ 인증중고차는 ★ 제조사(또는 직영)가 ★ 검사를 마친 차다.
      ★ ★ **종이를 안 줄 뿐이지 ★ 안 본 것이 아니다.**
    ★ 정본은 ★ `config/scoring.json` 의 `certified_credit` 이다 (S14) —
      ★ ★ 사이트 목록도 ★ 축 목록도 ★ 비율도 ★ 거기 있다.  ★ 코드에 안 박는다
    ★ 분모(910)는 ★ 그대로 둔다 — ★ 다른 차와 견줄 수 있어야 한다
    ★ 돌려줌 (그 축 집합, 비율) — ★ 해당 없으면 (빈 집합, 0.0)
    """
    rule = policy.raw.get("certified_credit") or {}
    site = getattr(snapshot, "site", None) if snapshot is not None else None
    if not rule or not site or site not in (rule.get("sites") or ()):
        return frozenset(), 0.0
    return frozenset(rule.get("axes") or ()), float(rule.get("ratio") or 0.0)


def axis_points(v: Verdict, policy: ScoringPolicy,
                snapshot=None) -> dict:
    """★★★★★ 축마다 ★ **`earned` 에 실제로 더해지는 점수** (마스터 지시 09-05 ①).

    ★★★ 지시 — 「★ `runner.py:1855` 에 ★ `score` 를 넣어라.
      ★ 값은 ★ `v.values[comp]` × 규칙 → 점수.  ★ `max_points` 는 이미 넣고 있다」
    ★★ 규칙을 ★ **여기 한 자리**에 둔다 — ★ `score()` 도 이것을 쓴다.
      ★ ★ 두 벌로 적으면 ★ 갈린다 (이 저장소가 거듭 겪은 것이다 · `S14`).
    ★ 규칙 —
      ① `policy.skipped(comp)`        → ★ 표에 아예 안 넣는다 (전 매물 스킵)
      ② `excluded` · 값이 없음 · `None` → ★ **`None`** (「0점」과 「안 봤다」는 다르다)
      ③ 인증중고차 몫 — ★ 근거 없는 축이 ★ 0 이면 ★ `배점 × 비율` (마스터 08-28)
      ④ 그 밖                          → ★ `v.values[comp]` 그대로
    ★ 돌려줌  `{comp: 점수 또는 None}`
    """
    credit_axes, credit_ratio = _certified_credit(policy, snapshot)
    out: dict = {}
    for comp in COMPONENTS:
        if policy.skipped(comp):
            continue
        if comp in v.excluded or comp not in v.values:
            out[comp] = None
            continue
        got = v.values[comp]
        if got is None:
            out[comp] = None
            continue
        got = float(got)
        if (comp in credit_axes and credit_ratio and got == 0.0
                and v.sources.get(comp) in UNCONFIRMED_SOURCES):
            got = float(policy.comp(comp)) * credit_ratio
        out[comp] = got
    return out


def score(v: Verdict, policy: ScoringPolicy,
          absolute: list[str] | None = None,
          snapshot=None) -> ScoreResult:
    total = float(policy.raw["total_points"])
    # ★★★★★ 08-30 (마스터 확정 08-29 밤 · r992 ①②) —
    #   ★ `value.market` 30 → **0** · `state.consumable` 15 → **0**.
    #   ★ ★ 마스터 — 「★ **분모는 910 그대로** (모수를 안 바꾼다)」
    #   ★ ★ 그래서 ★ 배점 합이 ★ **865** 다 — ★ 45점은 ★ **닿을 수 없는 자리**로 남는다.
    #   ★★ 관문이 「같아야 한다」였다 — ★ 「넘으면 안 된다」로 바꾼다.
    #     ★ ★ 이 관문이 막던 것은 ★ **분모를 줄여 비율을 높이는 등급 인플레**다
    #       (개정 128 · 실측 08-17 — 사고를 모르는데 등급이 난 것 1,131건).
    #     ★ ★ 합이 ★ **작은** 것은 ★ 그 반대다 — ★ 후하게 매겨질 길이 없다.
    #     ★ ★ 합이 ★ **큰** 것은 ★ 여전히 막는다 (100%를 넘는 축 합은 앞뒤가 안 맞는다)
    if policy.points_sum() > policy.raw["total_points"]:
        raise PolicyError(
            f"배점 합 {policy.points_sum()} > total_points "
            f"{policy.raw['total_points']} (STEP 128)", step="STEP 128")
    # ★ 핵심 축이 빠지면 등급을 매기지 않는다 (개정 287).
    #   분모를 줄여 비율을 높이는 것이 등급 인플레다 —
    #   실측 08-17: 사고를 모르는데 등급이 난 것 1,131건
    core = tuple(policy.raw.get("score_core_axes") or ())
    # ★★ 인증중고차 몫 (마스터 08-28) — ★ 위 `_certified_credit` 참고
    credit_axes, credit_ratio = _certified_credit(policy, snapshot)
    credit_given = 0.0
    excluded_points = 0.0
    earned = 0.0
    grade_earned = 0.0
    # ★ 등급 분모는 ★ 만점에서 시작해 ★ 「등급에서 뺀 축」만 덜어낸다 (아래 참고)
    grade_base = total
    confirmed = 0.0
    by_axis: dict[str, float] = {}
    # ★ 축별 점수 — ★ 규칙은 `axis_points()` 하나다 (09-05 지시 ①)
    per_comp = axis_points(v, policy, snapshot)

    for comp in COMPONENTS:
        if policy.skipped(comp):
            # ★ 스킵은 전 매물이다.  총점에서 빠졌으므로 분모에서도 뺄 것이 없다
            continue
        weight = float(policy.comp(comp))
        # ★ 등급은 취향을 뺀 505 로 매긴다.  분모는 못 봐도 505 그대로다
        for_grade = axis_of(comp) not in GRADE_EXCLUDED_AXES
        if not for_grade:
            # ★★★★★ 08-30 (마스터 확정 r992 ①②) — ★ 등급 분모는 ★ **모수 그대로**다.
            #   ★ 마스터 — 「★ 분모는 910 그대로 (모수를 안 바꾼다)」
            #   ★ ★ 전에는 ★ 「본 축의 배점을 더해」 만들었다 — ★ 그러면
            #     ★ ★ `value.market`·`state.consumable` 을 끄자 ★ 865 로 내려가
            #     ★ ★ 등급이 저절로 후해진다 (65%가 591.5 → 562).
            #   ★ ★ 그래서 ★ 만점에서 ★ **등급에서 뺀 축만** 덜어낸다.
            #     ★ 지금 `GRADE_EXCLUDED_AXES` 는 비어 있으므로 ★ 곧 910 이다
            grade_base -= weight
        # ★★★★★ 09-05 — ★ 점수는 ★ `axis_points()` 하나가 낸다 (지시 ①).
        #   ★ `runner.py` 가 ★ `result_axis.score` 에 넣는 것과 ★ **같은 값**이어야 한다 —
        #   ★ ★ 두 벌로 적으면 ★ 화면과 표가 갈린다.  ★ `S46-272` 가 그것을 본다
        got = per_comp.get(comp)
        if got is None:
            excluded_points += weight
            continue
        raw_value = v.values.get(comp)
        value = float(got)
        confirmed_here = v.sources.get(comp) not in UNCONFIRMED_SOURCES
        # ★★ 인증중고차 몫을 받았나 — ★ 값이 늘었으면 그것이다 (규칙은 위 한 자리)
        if (comp in credit_axes and not confirmed_here and credit_ratio
                and raw_value is not None and float(raw_value) == 0.0
                and value > 0.0):
            credit_given += value
            # ★ 받은 몫은 ★ 「근거 있는 축의 합」에도 넣는다 (규격 `_pending_note`) —
            #   ★ ★ 그래야 ★ 「판정 중」에서 풀린다
            confirmed_here = True
        earned += value
        # ★ 확인율은 「근거가 있는 축」만 센다 (개정 325).
        #   「카탈로그를 안 받아 0점」을 확인했다고 하면 화면이 거짓말을 한다
        if confirmed_here:
            confirmed += weight
        if for_grade:
            grade_earned += value
        by_axis[axis_of(comp)] = by_axis.get(axis_of(comp), 0.0) + value

    # ★ applicable 은 「확인한 축의 배점 합」이다.  분모가 아니다.
    #   화면이 「555점 중 330점 · 205점은 확인하지 못했습니다」를 내는 데 쓴다
    # ★★★★★ 08-30 (마스터 확정 r992 ①②) — ★ **닿을 수 있는 합**에서 뺀다.
    #   ★ 전에는 ★ `total`(910) 에서 뺐다.  ★ 그런데 ★ `value.market`·
    #     `state.consumable` 이 ★ 0 이 되어 ★ 배점 합이 ★ 865 다.
    #   ★ ★ 그러면 ★ **전 축을 다 못 봐도** ★ `applicable` 이 ★ 45 로 남아
    #     ★ ★ 「전 축 수집 실패」 갈래가 ★ **닿지 않는 길**이 된다 (실측 08-30 · 시험 D).
    #   ★ ★ 「확인할 수 있었던 점」이 ★ 애초에 865 이므로 ★ 그것이 옳다.
    #     ★ ★ 분모(`denominator`)는 ★ 910 그대로다 — ★ 이것과 다른 값이다
    applicable = float(policy.points_sum()) - excluded_points
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
