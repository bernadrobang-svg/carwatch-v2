# -*- coding: utf-8 -*-
"""③ 사양 75점 — 트림 등급 45 · 옵션 합 30.

지시서   7장 STEP 73 · 74 · 5장 「배점 재설계 — 시장 기준」 (개정 292 ③)
근거     ★ ③은 ①과 겹친다 — 트림·옵션이 좋으면 신차가가 높고 시세도 높다.
        그래서 「같은 값이면 사양이 좋은 쪽」을 가르는 정도다
★ 마스터 지적 — 「깡통에 HUD 만 있어도 만점」.
  이 배점이면 깡통은 45점 중 낮은 점수를 받고 HUD 는 ④ 15점이라 등급에 안 들어간다
값규칙   백분위다.  절대 금액이 아니다 — 차종마다 신차가 폭이 다르다
금지     그 차종 표본이 하나면 백분위를 매기는 것.  분모가 없다
"""
from __future__ import annotations

from analyze.axes import AxisContext
from analyze.verdict import PRIO_MANUFACTURER, Verdict, put

TRIM = "spec.trim"
OPTIONS = "spec.options"


def percentile(value: float, ladder: list) -> float:
    """오름차순 사다리에서 value 의 백분위 (0.0~1.0).

    ★ 같은 값이 여럿이면 그 무리의 가운데를 준다 — 순서에 따라 안 흔들린다
    """
    below = sum(1 for x in ladder if x < value)
    same = sum(1 for x in ladder if x == value)
    return (below + same / 2) / len(ladder)


def _trim(ctx: AxisContext, v: Verdict) -> None:
    """트림 등급 45 — 그 차종의 트림을 신차가 순으로 줄 세운 백분위."""
    s = ctx.snapshot
    ladder = (ctx.target_config.get("trim_ladder") or {}).get(s.target_key)
    if s.price_origin_won is None:
        put(v, TRIM, None, PRIO_MANUFACTURER, "origin_price_missing",
            excluded=True)
        return
    if not ladder or len(ladder) < ctx.policy.rule("spec")["ladder_min"]:
        put(v, TRIM, None, PRIO_MANUFACTURER, "ladder_short", excluded=True)
        return
    pts = round(percentile(s.price_origin_won, ladder) * ctx.policy.comp(TRIM))
    put(v, TRIM, pts, PRIO_MANUFACTURER, "trim_origin_price")


def _options(ctx: AxisContext, v: Verdict) -> None:
    """옵션 합 30 — 선택 옵션가 합을 만점 기준 대비 비율로."""
    s = ctx.snapshot
    prices = ctx.dicts.option_prices
    top = ctx.policy.rule("spec")["option_full_won"]
    if s.options_choice is None:
        put(v, OPTIONS, None, PRIO_MANUFACTURER, "missing", excluded=True)
        return
    got = sum(prices.get(c, 0) for c in s.options_choice)
    # ★ 그 차종 최대 대비로 하면 최대가 한 매물에 좌우된다.
    #   「옵션 이만큼이면 만점」을 config 에 두고 그것으로 본다
    ratio = min(got / top, 1.0)
    put(v, OPTIONS, round(ratio * ctx.policy.comp(OPTIONS)),
        PRIO_MANUFACTURER, "options_choice_price")


def analyze_trim(ctx: AxisContext, v: Verdict) -> None:
    _trim(ctx, v)
    _options(ctx, v)
