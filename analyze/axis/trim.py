# -*- coding: utf-8 -*-
"""④ 사양 45 — 트림 25 · 옵션 20 (docs/ref/F-scoring.md ④).

지시서   7장 STEP 73 · 74 · `docs/ref/F-scoring.md` ④ (개정 329)
근거     ★ 마스터 지적 — 「깡통에 HUD 만 있어도 만점」.
        트림은 신차가 순으로 줄 세운 자리다.  「있다/없다」가 아니다
값규칙   트림이 1종뿐이면 만점 — 그 차종 안에서 못 가르는 것이지 나쁜 것이 아니다
        옵션가는 그 차종·트림 P90 을 만점 기준으로 삼는다
금지     셋을 같은 값으로 두는 것 —
        「선택 옵션 없음(확인됨)」 · 「가격 미상(확인 안 됨)」 · 「표본 부족(확인 안 됨)」
"""
from __future__ import annotations

from analyze.axes import AxisContext
from analyze.verdict import PRIO_MANUFACTURER, Verdict, put

TRIM = "spec.trim"
OPTIONS = "spec.options"


def rank_ratio(value: float, ladder: list) -> float:
    """오름차순 사다리에서 value 의 자리 (0.0~1.0) — k / n (F ④-1).

    ★ 같은 값이 여럿이면 그 무리의 가운데를 준다 — 순서에 안 흔들린다
    """
    below = sum(1 for x in ladder if x < value)
    same = sum(1 for x in ladder if x == value)
    return (below + same / 2) / len(ladder)


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
    put(v, TRIM, round(rank_ratio(s.price_origin_won, ladder) * full),
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
    _trim(ctx, v)
    _options(ctx, v)
