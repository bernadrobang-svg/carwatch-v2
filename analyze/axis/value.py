# -*- coding: utf-8 -*-
"""① 값 250 — 시세 대비 100 · 신차가 대비 80 · 주행 대비 70.

지시서   7장 STEP 70 · 71 · 81 · `docs/ref/F-scoring.md` ① (개정 329)
근거     ★ 이 도구는 「얼마짜리를 얼마에 사나」를 보는 것이다.  ①이 가장 크다
        마스터 지적 — 「신차가 대비 얼마나 싼지 없음 · 시세보다 낮은지 높은지 없음」
값규칙   시세는 실매물 중앙값이다.  이론가가 아니다
        신차가 = 등급기준 + 선택옵션가 합 (개정 301) —
        ★ 그래서 옵션 많은 차가 자동으로 반영된다
        전기차는 주행 40 + 배터리 SOH 30 (개정 318)
        ★★ 개정 419 — 계단표를 없앴다.  퍼센트에 비례해 준다
          1-1 시세 대비  싼 쪽 ×5 · 비싼 쪽 ×8   범위 −100 ~ +100
          1-2 신차가 대비 싼 쪽 ×1 · 비싼 쪽 ×3   범위 −30 ~ +80
        ★ 왜 비대칭인가 — 싼 데는 이유가 있고(사고·침수·급매) 그 이유는
          ②상태·③이력이 이미 잡는다.  비싼 데는 이유가 없다.  그냥 손해다
금지     중앙값을 못 냈을 때 이론가로 대신하는 것.  그것이 v1 의 「전부 싸다」다
        본문 배점표를 읽는 것 — 전부 폐기됐다.  부록 F 만 본다 (개정 330)
        0 에서 멈추는 바닥.  ★ 비싸면 계속 깎인다 —
        그래야 다른 축이 번 점수를 실제로 깎는다 (개정 419)
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


def by_percent(pct: float, r: dict, key: str) -> float:
    """퍼센트에 비례해 준다 (개정 419).  ★ 계단이 아니다.

    pct   싼 쪽이 양수다 (시세보다 5% 싸면 +5.0)
    key   "market" 또는 "origin"
    ★ 싼 쪽과 비싼 쪽의 기울기가 다르다.  범위도 config 가 정한다 —
      계수를 코드에 박지 않는다 (S14 · V4-13)
    """
    per = float(r[f"{key}_per_percent_cheap" if pct >= 0
                  else f"{key}_per_percent_over"])
    got = pct * per
    return max(float(r[f"{key}_min"]), min(float(r[f"{key}_max"]), got))


def adjusted_median(s, r: dict) -> tuple:
    """옵션·트림을 반영한 견줄 값 (개정 421).

    마스터 — 「그랜저도 깡통이 4000이면 최고트림의 풀옵션이 7000이니」

    돌려줌   (견줄 값, 어떻게 냈나)
    ★ 표본이 모자라면 차종으로 넓히고 **그렇게 냈다고 밝힌다** —
      화면이 「같은 트림 3건뿐 · 차종 전체로 견줬습니다」를 낸다 (V3-85)
    """
    median = s.market_median_won
    if not median or not r.get("option_adjust"):
        return median, "market_median"
    need = int(r["option_min_sample"])
    mine = s.option_total_won
    trim_med = s.option_median_by_trim_won
    n = s.option_trim_sample_n or 0
    if n >= need and mine is not None and trim_med is not None:
        # ★ 내 옵션이 그 트림 중앙보다 비싸면 견줄 값도 그만큼 올라간다
        return median + (mine - trim_med), f"option_adjusted_{n}"
    # 넓힘 — 차종 중앙값 × (내 신차가 ÷ 차종 신차가 중앙값)
    model_med = s.origin_median_by_model_won
    mine_origin = s.origin_total_won or s.price_origin_won
    if model_med and mine_origin:
        return round(median * (mine_origin / model_med)), f"model_scaled_{n}"
    return median, f"market_median_{n}"


def _market(ctx: AxisContext, v: Verdict) -> None:
    """1-1 시세 대비 100 — 같은 차종·트림·연식 실매물 중앙값 대비."""
    s, r = ctx.snapshot, ctx.policy.rule("value")
    if s.price_current_won is None:
        put(v, MARKET, 0, PRIO_OBSERVED, "missing")
        return
    if not s.market_median_won:
        # ★ 표본이 모자라면 그렇게 적는다.  이론가로 메우지 않는다
        put(v, MARKET, 0, PRIO_OBSERVED, "market_sample_short")
        return
    median, how = adjusted_median(s, r)
    if not median:
        put(v, MARKET, 0, PRIO_OBSERVED, "market_sample_short")
        return
    # ★ 싼 쪽이 양수다.  5% 싸면 +5.0 → ×5 = 25점
    pct = (median - s.price_current_won) / median * 100
    put(v, MARKET, round(by_percent(pct, r, "market")), PRIO_OBSERVED, how)


def _depreciation(ctx: AxisContext, v: Verdict) -> None:
    """1-2 신차가 대비 80 — 기준 잔가율보다 더 떨어졌으면 그만큼 싸게 산다."""
    s, r = ctx.snapshot, ctx.policy.rule("value")
    origin = s.origin_total_won or s.price_origin_won
    if not origin or s.price_current_won is None:
        put(v, DEPRECIATION, 0, PRIO_OBSERVED, "origin_price_missing")
        return
    # ★ 잔가율 표를 안 쓴다 (개정 419).  「신차가 대비 몇 % 싼가」 그대로다 —
    #   마스터 「신차 대비 30% 싸면 30점」
    #   ★ origin_price 에 옵션·트림이 이미 들어 있어 여기는 보정하지 않는다
    pct = (origin - s.price_current_won) / origin * 100
    put(v, DEPRECIATION, round(by_percent(pct, r, "origin")),
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
