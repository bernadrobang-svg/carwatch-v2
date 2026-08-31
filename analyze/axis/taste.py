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
from analyze.axis.spec import _has_option, _installed, _spec_table
from analyze.verdict import PRIO_MANUFACTURER, PRIO_OBSERVED, Verdict, put

HUD = "taste.hud"
SUNROOF = "taste.sunroof"
COLOR = "taste.color"
PICKED = "taste.fitting"

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
    # ★★★★★ 09-02 — ★ **이름으로도 맞댄다** (규격 `OPTION_CATALOG` 09-01).
    #   ★ 전에는 ★ 엔카 3자리 코드만 봤다 — ★ 아홉 사이트는 한글 이름을 준다.
    #   ★ ★ 그래서 ★ KB 332건이 ★ `taste.hud`·`taste.sunroof` **전건 0점**이었다
    has = _has_option(ctx, spec_name)
    if has is None:
        put(v, comp, None, PRIO_OBSERVED, "missing", excluded=True)
        return
    put(v, comp, full if has else 0, PRIO_OBSERVED, "option_codes")


def color_grade_of(name: str, groups: dict) -> str:
    """색 이름 → 갈래.  ★ 표에 없으면 ★ `default` 다 (마스터 확정 08-29).

    ★★★★★ 08-31 (r1000 ②) — ★ 마스터 —
      「★ 붉은색하고 갈색류는 빵점이고 ★ 흰색하고 검정색 쪽은 디폴트로 7점이고
       ★ 진주색이랑 푸른색 계열은 모두 15점」
    ★★ 사이트마다 색 이름이 다르다 (「크리스탈 화이트펄」·「스노우화이트」…) —
      ★ 그래서 ★ **표의 이름이 들어 있으면 그 갈래**로 본다.
      ★ ★ 긴 이름부터 본다 — ★ 「화이트펄」이 ★ 「화이트」보다 먼저다.
      ★ ★ 안 그러면 ★ 「크리스탈 화이트펄」이 ★ 보통(7)으로 떨어진다
    ★★ 표에 없으면 ★ **`default`(7점)** 다 — ★ 「모른다」가 아니다 (마스터 확정).
      ★ ★ 새 이름은 ★ 가이드에게 올린다.  ★ 짐작으로 갈래를 지어 넣지 않는다
    """
    got = str(name or "")
    hit = None
    for grade, names in groups.items():
        for one in names or ():
            if one and one in got and (hit is None or len(one) > len(hit[1])):
                hit = (grade, one)
    return hit[0] if hit else "default"


def _color(ctx: AxisContext, v: Verdict) -> None:
    """색상 15/7/0 — ★ 좋아함 15 · 보통 7 · 싫어함 0 (마스터 확정 08-29 · r1000 ②)."""
    r = ctx.policy.rule("taste")
    if _off(ctx, COLOR):
        put(v, COLOR, ctx.policy.comp(COLOR), PRIO_OBSERVED, "taste_off")
        return
    name = ctx.snapshot.color_ext_raw
    if not name:
        put(v, COLOR, None, PRIO_OBSERVED, "missing", excluded=True)
        return
    groups = r.get("color_groups")
    if groups:
        # ★ 08-31 — ★ 갈래 표가 ★ `scoring.json` 으로 옮겨졌다 (가이드가 정본을 쥔다).
        #   ★ 옛 `color_grade.json` 은 ★ 「흔한가」로 재던 표라 ★ 뜻이 다르다
        grade = color_grade_of(name, groups)
    else:
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
