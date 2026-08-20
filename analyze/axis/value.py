# -*- coding: utf-8 -*-
"""① 값 250 — 시세 대비 100 · 신차가 대비 80 · 주행 대비 70.

지시서   7장 STEP 70 · 71 · 81 · `docs/ref/F-scoring.md` ① (개정 329)
근거     ★ 이 도구는 「얼마짜리를 얼마에 사나」를 보는 것이다.  ①이 가장 크다
        마스터 지적 — 「신차가 대비 얼마나 싼지 없음 · 시세보다 낮은지 높은지 없음」
값규칙   시세는 실매물 중앙값이다.  이론가가 아니다
        신차가 = 등급기준 + 선택옵션가 합 (개정 301) —
        ★ 그래서 옵션 많은 차가 자동으로 반영된다
        전기차는 주행 40 + 배터리 SOH 30 (개정 318)
금지     중앙값을 못 냈을 때 이론가로 대신하는 것.  그것이 v1 의 「전부 싸다」다
        본문 배점표를 읽는 것 — 전부 폐기됐다.  부록 F 만 본다 (개정 330)
"""
from __future__ import annotations

from analyze.axes import AxisContext
from analyze.axis._util import months_between
from analyze.curve import ascending, descending
from analyze.verdict import PRIO_OBSERVED, Verdict, put

MARKET = "value.market"
DEPRECIATION = "value.depreciation"
MILEAGE = "value.mileage"

MONTHS_PER_YEAR = 12


def elapsed_years(ctx: AxisContext) -> float | None:
    """최초등록부터 경과 연수.  ★ 최소 0.5 — 갓 나온 차의 연평균이 폭발한다."""
    s = ctx.snapshot
    months = months_between(s.first_registration_date or s.year_month,
                            ctx.target_config.get("as_of"))
    if months is None:
        return None
    return max(float(ctx.policy.rule("value")["min_years"]),
               months / MONTHS_PER_YEAR)


def residual_expected(years: float, r: dict) -> float:
    """기준 잔가율 — 1년 0.88 · 2년 0.78 · 3년 0.67 · 이후 연 −0.07 (F ①-2)."""
    table = r["residual_by_year"]
    key = str(int(years)) if years >= 1 else "1"
    if key in table:
        return float(table[key])
    got = float(table["3"]) - (int(years) - 3) * float(r["residual_step"])
    return max(float(r["residual_floor"]), got)


def _market(ctx: AxisContext, v: Verdict) -> None:
    """1-1 시세 대비 100 — 같은 차종·트림·연식 실매물 중앙값 대비."""
    s, r = ctx.snapshot, ctx.policy.rule("value")
    if s.price_current_won is None:
        put(v, MARKET, 0, PRIO_OBSERVED, "missing")
        return
    median, n = s.market_median_won, s.market_sample_n
    if not median:
        # ★ 표본이 모자라면 그렇게 적는다.  이론가로 메우지 않는다
        put(v, MARKET, 0, PRIO_OBSERVED, "market_sample_short")
        return
    cheaper = (median - s.price_current_won) / median
    put(v, MARKET, round(descending(cheaper, r["market_curve"])),
        PRIO_OBSERVED, f"market_median_{n}")


def _depreciation(ctx: AxisContext, v: Verdict) -> None:
    """1-2 신차가 대비 80 — 기준 잔가율보다 더 떨어졌으면 그만큼 싸게 산다."""
    s, r = ctx.snapshot, ctx.policy.rule("value")
    origin = s.origin_total_won or s.price_origin_won
    years = elapsed_years(ctx)
    if not origin or s.price_current_won is None or years is None:
        put(v, DEPRECIATION, 0, PRIO_OBSERVED, "origin_price_missing")
        return
    actual = s.price_current_won / origin
    gap = residual_expected(years, r) - actual
    put(v, DEPRECIATION, round(descending(gap, r["depreciation_curve"])),
        PRIO_OBSERVED, "origin_price")


def _mileage(ctx: AxisContext, v: Verdict) -> None:
    """1-3 주행 대비 70 — 연평균으로 본다.  총 주행거리가 아니다.

    ★ 「3년에 6만」과 「1년에 6만」은 다른 차다
    ★ 전기차는 주행 40 + SOH 30 (개정 318)
    """
    s, r = ctx.snapshot, ctx.policy.rule("value")
    full = float(ctx.policy.comp(MILEAGE))
    is_ev = s.ev_battery_soh is not None
    cap = float(r["ev_mileage_points"]) if is_ev else full
    years = elapsed_years(ctx)
    if s.mileage_km is None or years is None:
        put(v, MILEAGE, 0, PRIO_OBSERVED, "missing")
        return
    per_year = s.mileage_km / years
    got = ascending(per_year, r["mileage_curve"]) * cap / full
    if not is_ev:
        put(v, MILEAGE, round(got), PRIO_OBSERVED, "mileage_per_year")
        return
    # ★ 전기차는 배터리가 남은 값을 가른다 (개정 318)
    got += descending(float(s.ev_battery_soh), r["soh_curve"])
    put(v, MILEAGE, round(got), PRIO_OBSERVED, "mileage_and_soh")


def analyze_value(ctx: AxisContext, v: Verdict) -> None:
    _market(ctx, v)
    _depreciation(ctx, v)
    _mileage(ctx, v)
