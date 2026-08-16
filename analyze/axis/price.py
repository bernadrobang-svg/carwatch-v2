# -*- coding: utf-8 -*-
"""가격 200점.

지시서   7장 STEP 70 (기대가 · 감가 곡선) · STEP 71 (배점 곡선)
근거     기대가는 「평균적인 매물 값」이다.  딱 맞으면 중간 점수가 맞다.
         v1 초판은 ±0% 에 60점을 줘서 매물 74% 가 하위 구간에 몰렸다
값규칙   기대가가 NULL 이면 (originPrice 부재) NULL + excluded.  0 점이 아니다
금지     보증 잔여 가치를 가격에서 차감하는 것 — 보증 100점과 이중 계산 (STEP 83)
         감가 곡선 값을 코드에 상수로 두는 것.  v1 의 87/69/55% 는 출처가 없었다
★ 미확정 감가 곡선은 첫 수집 후 실매물 분포에서 산출한다 (STEP 26-5).
         config.depreciation.curve 가 null 인 동안 NULL + excluded 로 둔다
"""
from __future__ import annotations

from analyze.axes import AxisContext
from analyze.axis._util import months_between
from analyze.verdict import PRIO_OBSERVED, Verdict, put

AXIS = "price"
MONTHS_PER_YEAR = 12


def coefficient_sane(coefficient, sane_range) -> bool:
    """★ 계수가 범위 밖이면 그 차종의 가격 축을 쓰지 않는다 (STEP 70).

    사례   스포티지 LPi 1.517.  originPrice 가 기본 트림가라 실매물보다 낮다
    금지   계수를 그대로 쓰는 것 — 그 차종만 기대가가 1.5배가 된다
           범위 안으로 자르는 것 — 근거 없이 값을 만드는 것이다
    """
    if coefficient is None or not sane_range:
        return True
    return sane_range[0] <= float(coefficient) <= sane_range[1]


def expected_price(origin_won, age_months, curve, coefficient,
                   curve_beyond=None):
    """기대가 = 신차가 × 감가계수(경과년) × 차종 보정계수."""
    if origin_won is None or age_months is None or not curve:
        return None
    year = str(age_months // MONTHS_PER_YEAR)
    rate = curve.get(year, curve_beyond)
    if rate is None:
        return None
    return origin_won * float(rate) * float(coefficient or 1.0)


def score_from_curve(deviation: float, price_curve: list) -> int:
    """구간별 점수.  마지막 항(deviation=null)이 초과 구간이다."""
    for row in price_curve:
        d = row["deviation"]
        if d is not None and deviation <= d:
            return row["points"]
    return price_curve[-1]["points"]


def _curve_ready(dep: dict, age_months: int) -> bool:
    """그 연차의 표본이 curve_min_sample 이상인가 (STEP 70).

    표본 수가 없으면 검사하지 않는다 — 첫 실행에는 sample 이 없다.
    """
    need = dep.get("curve_min_sample")
    samples = dep.get("curve_sample")
    if not need or not samples:
        return True
    return int(samples.get(str(age_months // MONTHS_PER_YEAR), 0)) >= int(need)


def analyze_price(ctx: AxisContext, v: Verdict) -> None:
    s = ctx.snapshot
    dep = ctx.target_config.get("depreciation") or {}
    coef = (dep.get("coefficient") or {}).get(s.target_key)
    if not coefficient_sane(coef, dep.get("coefficient_sane_range")):
        # 신차가 정보가 부정확하다.  다른 축은 정상 판정하고 분모만 200 줄인다
        put(v, AXIS, None, PRIO_OBSERVED, "coefficient_out_of_range",
            excluded=True)
        return
    age = months_between(s.first_registration_date or s.year_month,
                         ctx.target_config.get("as_of"))
    # ★ 표본 미달 연차는 곡선을 만들지 않는다.  보간은 추정이라 금지 (STEP 70)
    if age is not None and not _curve_ready(dep, age):
        put(v, AXIS, None, PRIO_OBSERVED, "curve_sample_short", excluded=True)
        return
    exp = expected_price(s.price_origin_won, age, dep.get("curve"), coef,
                         dep.get("curve_beyond"))
    if exp is None or not exp or s.price_current_won is None:
        put(v, AXIS, None, PRIO_OBSERVED, "expected_unavailable", excluded=True)
        return
    deviation = (s.price_current_won - exp) / exp
    pts = score_from_curve(deviation, ctx.policy.raw["price_curve"])
    put(v, AXIS, pts, PRIO_OBSERVED, "expected_price")
