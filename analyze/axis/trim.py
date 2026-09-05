# -*- coding: utf-8 -*-
"""④ 사양 45 — 트림 25 · 옵션 20 (docs/ref/F-scoring.md ④).

지시서   7장 STEP 73 · 74 · `docs/ref/F-scoring.md` ④ (개정 329)
근거     ★ 마스터 지적 — 「깡통에 HUD 만 있어도 만점」.
        ★★ 개정 382 — 트림은 「몇째 자리인가」가 아니라 「얼마짜리 급인가」다.
        마스터 — 「트림의 신차 가격이 중요해.  그게 차량의 가격 차이야」
값규칙   트림이 1종뿐이면 만점 — 그 차종 안에서 못 가르는 것이지 나쁜 것이 아니다
        옵션가는 그 차종·트림 P90 을 만점 기준으로 삼는다
금지     셋을 같은 값으로 두는 것 —
        「선택 옵션 없음(확인됨)」 · 「가격 미상(확인 안 됨)」 · 「표본 부족(확인 안 됨)」
"""
from __future__ import annotations

from analyze.axes import AxisContext
from analyze.verdict import PRIO_MANUFACTURER, Verdict, put

TRIM = "taste.trim"
OPTIONS = "taste.option"


def price_ratio(value: float, ladder: list) -> float:
    """내 트림 신차가 ÷ 그 차종 최고 트림 신차가 (0.0~1.0) — 개정 382.

    ★★ 마스터 지적 — 「그건 너다.  트림별 가격 차이를 고려 안 해서야.
      트림의 신차 가격이 중요해.  그게 차량의 가격 차이야」
    ★ 순위(k/n)로 재면 가격 차이가 사라진다.
      스탠다드 6,500 · 스포츠 7,200 · 플러스 7,800 이면
      순위로는 8.3/16.7/25 다 — 700만·600만 차이가 안 보인다.
      신차가로 재면 20.8/23.1/25 다
    ★ 트림이 10종인 차종이면 한 칸이 2.5점이라 값과 무관해졌다
    """
    top = max(ladder)
    if not top:
        return 0.0
    return min(float(value) / float(top), 1.0)


def _trim(ctx: AxisContext, v: Verdict) -> None:
    s = ctx.snapshot
    full = ctx.policy.comp(TRIM)
    ladder = (ctx.target_config.get("trim_ladder") or {}).get(s.target_key)
    if s.price_origin_won is None:
        put(v, TRIM, 0, PRIO_MANUFACTURER, "origin_price_missing")
        return
    if not ladder:
        put(v, TRIM, 0, PRIO_MANUFACTURER, "ladder_missing")
        return
    if len(set(ladder)) == 1:
        # ★ 트림이 1종뿐이다.  못 가르는 것이지 나쁜 것이 아니다
        put(v, TRIM, full, PRIO_MANUFACTURER, "trim_single")
        return
    # ★ 신차가로 잰다.  순위로 재지 않는다 (개정 382).
    #   최고 트림이 25 · 나머지는 그에 대한 비율
    put(v, TRIM, round(price_ratio(s.price_origin_won, ladder) * full, 1),
        PRIO_MANUFACTURER, "trim_origin_price")


def _options(ctx: AxisContext, v: Verdict) -> None:
    """4-2 옵션 20 — 내 옵션가 합 ÷ 그 차종·트림 P90."""
    s = ctx.snapshot
    full = ctx.policy.comp(OPTIONS)
    base = (ctx.target_config.get("option_base") or {}).get(s.target_key)
    if s.options_choice is None:
        put(v, OPTIONS, 0, PRIO_MANUFACTURER, "missing")
        return
    if not s.options_choice:
        # ★ 「선택 옵션이 없다」는 확인한 사실이다.  0점이되 확인됨이다
        put(v, OPTIONS, 0, PRIO_MANUFACTURER, "no_choice_option")
        return
    if s.option_total_won is None:
        put(v, OPTIONS, 0, PRIO_MANUFACTURER, "option_price_unknown")
        return
    if not base:
        put(v, OPTIONS, 0, PRIO_MANUFACTURER, "option_base_short")
        return
    put(v, OPTIONS, round(min(s.option_total_won / base, 1.0) * full),
        PRIO_MANUFACTURER, "options_choice_price")


def analyze_trim(ctx: AxisContext, v: Verdict) -> None:
    # ★ 개정 r1174 — 트림 축은 물러났다 (「내장」이 그 배점 20 을 받는다).
    #   이 갈래는 이제 옵션 30 만 낸다.  `_trim` 은 옛 셈을 남겨 둔 것이다
    _options(ctx, v)
