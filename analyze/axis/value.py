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
from analyze.curve import ascending
from analyze.verdict import PRIO_OBSERVED, Verdict, put

DEPRECIATION = "value.origin"   # f-table 은 value.origin 이라 적었다 — id 는 안 바꾼다
MILEAGE = "value.mileage"
MARKET = "value.market"          # ★ 개정 469 — 시세 30 (마스터 확정)
YEAR = "state.year"              # ★ 개정 469 신설 — 연식 80 (차량 갈래)
BUDGET = "value.budget"          # ★ 개정 452 신설 — 예산 95
PCT = 100.0

MONTHS_PER_YEAR = 12
WON_PER_MANWON = 10_000


def elapsed_years(ctx: AxisContext) -> float | None:
    """최초등록부터 경과 연수.  ★ 최소 0.5 — 갓 나온 차의 연평균이 폭발한다."""
    s = ctx.snapshot
    months = months_between(s.first_registration_date or s.year_month,
                            ctx.target_config.get("as_of"))
    if months is None:
        return None
    return max(float(ctx.policy.rule("value")["min_years"]),
               months / MONTHS_PER_YEAR)


def _depreciation(ctx: AxisContext, v: Verdict) -> None:
    """② 값 — 신차가 대비 75 (개정 452).

    ★ 신차가 = 트림가 + 선택 옵션가 (개정 301).  origin_total_won 이 그것이다
    ★ 마스터 — 「80% 까지는 점수가 거의 없다가 낮아지면서 로그 곡선처럼 오르는 것」
      80% 이상 0 · 65% 만점 · 그 아래는 만점 유지 (f-table 5장-2a ①)
    ★ 자르지 않는다.  비싸면 점수가 낮을 뿐이다 (개정 452)
    """
    s, r = ctx.snapshot, ctx.policy.rule("value")
    origin = s.origin_total_won or s.price_origin_won
    if not origin or s.price_current_won is None:
        put(v, DEPRECIATION, 0, PRIO_OBSERVED, "origin_price_missing")
        return
    ratio = s.price_current_won / origin * PCT
    # ★★★★ 08-30 (마스터 지시 3 · `f-table` 5장 갈래 ③) —
    #   ★ 끌어온 신차가는 ★ **원문과 같아 보이게 하지 않는다** (규격 필수).
    #   ★ 근거 코드를 갈라 두면 ★ `/why`·축 칩·확인율이 ★ 저절로 따라온다
    put(v, DEPRECIATION, round(ascending(ratio, r["origin_curve"])),
        PRIO_OBSERVED,
        getattr(s, "origin_lent_from", None) or "origin_price")


def _budget(ctx: AxisContext, v: Verdict) -> None:
    """② 값 — 예산 95 (개정 452 신설).

    ★ 차종별 마지노선 대비.  ★ 예산 초과는 점수가 낮아질 뿐이다 —
      마스터 「예산 초과는 점수가 낮아야겠지.  이것도 로그화해」
    ★ 등급 상한도 예외추천도 없다 (개정 452 로 폐기)
    """
    s, r = ctx.snapshot, ctx.policy.rule("value")
    cfg = ctx.policy.raw.get("budget_manwon") or {}
    won = _budget_won(cfg, s.target_key)
    if not won or s.price_current_won is None:
        put(v, BUDGET, 0, PRIO_OBSERVED, "missing")
        return
    ratio = s.price_current_won / won * PCT
    put(v, BUDGET, round(ascending(ratio, r["budget_curve"])),
        PRIO_OBSERVED, "budget_line")


def _budget_won(cfg: dict, target_key: str | None) -> int | None:
    """예산 마지노선(원).  ★ 차종별이 먼저다 (f-table 5장-2a ②).

    ★ 연료별은 차종별이 없을 때다.  지금 스냅숏에 연료가 없어 쓰지 못한다 —
      차종을 늘릴 때 붙인다 (명령서 §4-②).  ★ 그때까지는 전역 기본이다
    """
    man = (cfg.get("by_target") or {}).get(target_key)
    if man is None:
        man = cfg.get("default")
    return int(man) * WON_PER_MANWON if man else None


def _year(ctx: AxisContext, v: Verdict) -> None:
    """① 차량 — 연식 75 (개정 452 신설).

    ★ 차령으로 본다.  절대 연도로 박으면 해마다 규격을 고쳐야 한다
    ★ 최신 만점 · 차령 6(2026 기준 2020년) 이 마스터 기준선 · 차령 8 에서 0
    """
    s, r = ctx.snapshot, ctx.policy.rule("value")
    age = elapsed_years(ctx)
    if age is None:
        put(v, YEAR, 0, PRIO_OBSERVED, "missing")
        return
    del s
    put(v, YEAR, round(ascending(age, r["year_curve"])),
        PRIO_OBSERVED, "age_years")


def _mileage(ctx: AxisContext, v: Verdict) -> None:
    """① 차량 — 주행 100 (개정 452).  ★ 총 주행거리다.  연평균이 아니다.

    ★ 전에는 연평균이었다.  「3년에 6만」과 「1년에 6만」의 차이는
      ★ 이제 연식 축이 따로 본다 (f-table 5장-2a ③·④)
    ★★ 전기차 SOH 를 여기서 더하지 않는다 — SOH 는 가점이다 (개정 380).
      전에는 축 안에서도 더하고 bonuses_json 에도 넣어 ★ 두 번 셌다 (실측 08-22)
    ★ 8만 km 가 기준선 · 20만에서 0.  ★ 10만을 넘겨도 자르지 않는다
    """
    s, r = ctx.snapshot, ctx.policy.rule("value")
    if s.mileage_km is None:
        put(v, MILEAGE, 0, PRIO_OBSERVED, "missing")
        return
    put(v, MILEAGE, round(ascending(float(s.mileage_km), r["mileage_curve"])),
        PRIO_OBSERVED, "mileage_total")


def _market(ctx: AxisContext, v: Verdict) -> None:
    """② 값 — 시세 대비 30 (개정 469).

    ★ 마스터 확정 08-22 — 「시세를 반영하되 점수를 30점 정도 주라」
    ★ 싼 쪽이 양수다.  ★ 비싸면 음수로 계속 깎인다 — 0 에서 멈추지 않는다
    ★ 표본이 모자라면 0점 + 「확인 안 됨」.  ★ 이론가로 메우지 않는다 (개정 325)
    """
    s, r = ctx.snapshot, ctx.policy.rule("value")
    # ★★★★★ 08-30 (마스터 확정 08-29 밤 · r992 ①) — ★ **이 축이 꺼졌다.**
    #   ★ 마스터 — 「★ 시세 음수를 뺀다.  ★ 분모는 910 그대로 (모수를 안 바꾼다).
    #     ★ ★ 음수를 다시 넣는 것은 다음에 정한다」
    #   ★★ 배점이 0 이면 ★ **값도 0 이어야 한다.**
    #     ★ ★ 채점은 배점을 곱하므로 ★ 점수에는 영향이 없었다 —
    #     ★ ★ 그러나 ★ `result_axis.value` 에 ★ 30·−30 이 그대로 남아
    #     ★ ★ ★ 화면과 `/why` 가 ★ **꺼진 축의 점수를 보인다.**
    #     ★ ★ 실측 08-31 — ★ `V3-86` 이 잡았다 (배점 0 인데 값 30 인 행 3,893건)
    #   ★ 셈은 그대로 둔다 — ★ 되살릴 때 이 줄만 뺀다
    if not ctx.policy.comp(MARKET):
        put(v, MARKET, 0, PRIO_OBSERVED, "site_unavailable")
        return
    median = s.market_median_won
    if not median or (s.market_sample_n or 0) < int(r["market_min_sample"]) \
            or s.price_current_won is None:
        put(v, MARKET, 0, PRIO_OBSERVED, "market_sample_short")
        return
    pct = (median - s.price_current_won) / median * PCT
    per = float(r["market_per_percent_cheap" if pct >= 0
                  else "market_per_percent_over"])
    got = max(float(r["market_min"]), min(float(r["market_max"]), pct * per))
    put(v, MARKET, round(got), PRIO_OBSERVED, "market_median")


def analyze_value(ctx: AxisContext, v: Verdict) -> None:
    _market(ctx, v)
    _depreciation(ctx, v)
    _budget(ctx, v)
    _mileage(ctx, v)
    _year(ctx, v)
