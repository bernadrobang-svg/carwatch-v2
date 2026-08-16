# -*- coding: utf-8 -*-
"""① 값 250점 — 시세 대비 120 · 신차가 대비 감가 70 · 주행 대비 60.

지시서   7장 STEP 70 · 71 · 81 · 5장 「배점 재설계 — 시장 기준」 (개정 292)
근거     ★ 이 도구는 「값이 싼가」를 보는 것이다.  ①이 가장 크다
        감가율 1년 12% · 2년 22% · 3년 33% · 이후 연 7%
        주행 연 15,000~20,000km 가 평균
값규칙   시세는 실매물 중앙값이다.  이론가가 아니다 (개정 292)
        표본이 모자라면 시세 축만 excluded 다 — 감가·주행은 그대로 본다
금지     중앙값을 못 냈을 때 이론가로 대신하는 것.  그것이 v1 의 「전부 싸다」다
"""
from __future__ import annotations

from analyze.axes import AxisContext
from analyze.axis._util import months_between
from analyze.axis.price import coefficient_sane, expected_price
from analyze.verdict import PRIO_OBSERVED, Verdict, put

MARKET = "value.market"
DEPRECIATION = "value.depreciation"
MILEAGE = "value.mileage"

MONTHS_PER_YEAR = 12


def points_from_curve(x: float, curve: list, key: str) -> int:
    """구간 곡선 → 점수.  마지막 항(값 null)이 초과 구간이다.

    ★ price.py 의 score_from_curve 와 같은 모양이다.  키 이름만 다르다
    """
    for row in curve:
        edge = row[key]
        if edge is not None and x <= edge:
            return int(row["points"])
    return int(curve[-1]["points"])


def _market(ctx: AxisContext, v: Verdict) -> None:
    """시세 대비 120 — 같은 차종·트림·연식 실매물 중앙값 대비 (개정 292 ①)."""
    s = ctx.snapshot
    if s.price_current_won is None:
        put(v, MARKET, None, PRIO_OBSERVED, "price_missing", excluded=True)
        return
    median, n = s.market_median_won, s.market_sample_n
    if not median:
        # ★ 표본이 모자라면 그렇게 적는다.  이론가로 메우지 않는다
        put(v, MARKET, None, PRIO_OBSERVED, "market_sample_short", excluded=True)
        return
    deviation = (s.price_current_won - median) / median
    pts = points_from_curve(deviation, ctx.policy.rule("value")["market_curve"],
                            "deviation")
    put(v, MARKET, pts, PRIO_OBSERVED, f"market_median_{n}")


def _depreciation(ctx: AxisContext, v: Verdict) -> None:
    """신차가 대비 감가 70 — 시장 평균보다 더 떨어졌으면 그만큼 싸게 사는 것."""
    s = ctx.snapshot
    dep = ctx.target_config.get("depreciation") or {}
    coef = (dep.get("coefficient") or {}).get(s.target_key)
    if not coefficient_sane(coef, dep.get("coefficient_sane_range")):
        put(v, DEPRECIATION, None, PRIO_OBSERVED, "coefficient_out_of_range",
            excluded=True)
        return
    age = months_between(s.first_registration_date or s.year_month,
                         ctx.target_config.get("as_of"))
    exp = expected_price(s.price_origin_won, age, dep.get("curve"), coef,
                         dep.get("curve_beyond"))
    if not exp or s.price_current_won is None:
        put(v, DEPRECIATION, None, PRIO_OBSERVED, "expected_unavailable",
            excluded=True)
        return
    deviation = (s.price_current_won - exp) / exp
    pts = points_from_curve(deviation,
                            ctx.policy.rule("value")["depreciation_curve"],
                            "deviation")
    put(v, DEPRECIATION, pts, PRIO_OBSERVED, "expected_price")


def _mileage(ctx: AxisContext, v: Verdict) -> None:
    """주행 대비 60 — 연 주행거리로 본다.  총 주행거리가 아니다 (개정 292).

    ★ 「3년에 6만」과 「1년에 6만」은 다른 차다.  총 km 만 보면 같아진다
    """
    s = ctx.snapshot
    r = ctx.policy.rule("value")
    if s.mileage_km is None:
        # 전 매물에 있어야 하는 값이다.  없으면 그것이 결함 신호다 (STEP 81)
        put(v, MILEAGE, r["mileage_unknown_points"], PRIO_OBSERVED, "missing")
        return
    age = months_between(s.first_registration_date or s.year_month,
                         ctx.target_config.get("as_of"))
    if not age:
        put(v, MILEAGE, None, PRIO_OBSERVED, "age_unknown", excluded=True)
        return
    per_year = s.mileage_km / (age / MONTHS_PER_YEAR)
    pts = points_from_curve(per_year, r["mileage_curve"], "km_per_year")
    put(v, MILEAGE, pts, PRIO_OBSERVED, "mileage_per_year")


def analyze_value(ctx: AxisContext, v: Verdict) -> None:
    _market(ctx, v)
    _depreciation(ctx, v)
    _mileage(ctx, v)
