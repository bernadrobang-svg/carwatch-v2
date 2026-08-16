# -*- coding: utf-8 -*-
"""④ 취향 50점 — HUD 15 · 선루프 10 · 색상 10 · 지정 옵션 15.

지시서   7장 STEP 73 · 80 · 5장 「배점 재설계 — 시장 기준」 (개정 292 ④)
근거     ★ 취향은 사람마다 다르다.  ④가 가장 작고, 등급에 들어가지 않는다
        등급은 ①+②+③ = 505 로 매기고 ④는 순위에만 쓴다
        ★ 취향으로 등급이 오르내리면 남에게 못 보여 준다
필수     사용자가 켜고 끈다.  끄면 그 점수는 만점 처리한다 —
        「나는 선루프 필요 없다」를 반영한다
금지     취향 축을 끄지 않은 채로 전체 등급을 논하는 것
"""
from __future__ import annotations

from analyze.axes import AxisContext
from analyze.axis.spec import OPTION3, _installed, _spec_table
from analyze.verdict import PRIO_MANUFACTURER, PRIO_OBSERVED, Verdict, put

HUD = "taste.hud"
SUNROOF = "taste.sunroof"
COLOR = "taste.color"
PICKED = "taste.picked"

NA_VALUE = -1

# 취향 축 → 사양 코드를 찾을 때 쓰는 옛 성분 이름 (OPTION3 는 그 이름을 쓴다)
AS_SPEC = {HUD: "spec.hud", SUNROOF: "spec.sunroof"}


def _off(ctx: AxisContext, comp: str) -> bool:
    """사용자가 이 취향을 껐는가.  ★ 끄면 만점이다 — 감점이 아니다."""
    return comp in (ctx.target_config.get("taste_off") or ())


def _fitting(ctx: AxisContext, v: Verdict, comp: str) -> None:
    s = ctx.snapshot
    full = ctx.policy.comp(comp)
    if _off(ctx, comp):
        put(v, comp, full, PRIO_OBSERVED, "taste_off")
        return
    spec_name = AS_SPEC[comp]
    table = _spec_table(ctx, spec_name)
    if table == NA_VALUE:
        put(v, comp, NA_VALUE, PRIO_MANUFACTURER, "spec_table", excluded=True)
        return
    if table == 1:
        put(v, comp, full, PRIO_MANUFACTURER, "spec_table")
        return
    if s.options_standard is None and s.options_choice is None:
        put(v, comp, None, PRIO_OBSERVED, "missing", excluded=True)
        return
    has = OPTION3[spec_name] in _installed(ctx)
    put(v, comp, full if has else 0, PRIO_OBSERVED, "option_codes")


def _color(ctx: AxisContext, v: Verdict) -> None:
    """색상 10 — 흰·검정 10 · 회색·은색 7 · 유색 3 (시장 선호 순서)."""
    r = ctx.policy.rule("taste")
    if _off(ctx, COLOR):
        put(v, COLOR, ctx.policy.comp(COLOR), PRIO_OBSERVED, "taste_off")
        return
    name = ctx.snapshot.color_ext_raw
    if not name:
        put(v, COLOR, None, PRIO_OBSERVED, "missing", excluded=True)
        return
    grade = ctx.dicts.color_grade.get(name, ctx.dicts.color_default)
    if grade is None:
        put(v, COLOR, None, PRIO_OBSERVED, "unclassified", excluded=True)
        return
    put(v, COLOR, r["color_points"][grade], PRIO_OBSERVED, "detail_color")


def _picked(ctx: AxisContext, v: Verdict) -> None:
    """지정 옵션 15 — 사용자가 고른 것.  아무것도 안 골랐으면 만점이다."""
    s = ctx.snapshot
    full = ctx.policy.comp(PICKED)
    want = tuple(ctx.target_config.get("picked_options") or ())
    if not want:
        # ★ 고른 것이 없으면 「원하는 것을 다 얻었다」다.  감점이 아니다
        put(v, PICKED, full, PRIO_OBSERVED, "nothing_picked")
        return
    if s.options_standard is None and s.options_choice is None:
        put(v, PICKED, None, PRIO_OBSERVED, "missing", excluded=True)
        return
    codes = _installed(ctx)
    hit = sum(1 for c in want if c in codes)
    put(v, PICKED, round(hit / len(want) * full), PRIO_OBSERVED,
        f"picked_{hit}_of_{len(want)}")


def analyze_taste(ctx: AxisContext, v: Verdict) -> None:
    _fitting(ctx, v, HUD)
    _fitting(ctx, v, SUNROOF)
    _color(ctx, v)
    _picked(ctx, v)
