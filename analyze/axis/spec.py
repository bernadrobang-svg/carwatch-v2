# -*- coding: utf-8 -*-
"""사양 90점 — HUD 20 · HDA 20 · 선루프 20 · SVM 10 · SCC 10 · 후측방 5 · 틴팅 5.

지시서   7장 STEP 73 · 74 (근거 우선순위) · 75 (HDA 3단계 · 틴팅)
근거     사양표 > 실측 > 판정기 > 문자열.  뒤로 갈수록 틀릴 여지가 크다
         v1 은 판매글 키워드가 실장착을 이겨 선루프 84건이 부당하게 1이었다
금지     카탈로그 전체 목록 · facet Count 를 장착 근거로 쓰는 것
         put() 을 거치지 않고 값을 직접 대입하는 것
         -1 을 facet Count 0 으로 붙이는 것 — 제조사 사양표 근거로만 붙인다
★ Gate   HDA 는 실측 확정 전 NULL + excluded 다 (STEP 75).  추정으로 1·2 를 매기지 않는다
"""
from __future__ import annotations

from analyze.axes import AxisContext
from analyze.verdict import (
    PRIO_KEYWORD, PRIO_MANUFACTURER, PRIO_OBSERVED, Verdict, put,
)

HUD, HDA, SUNROOF = "spec.hud", "spec.hda", "spec.sunroof"
SVM, SCC, BSD, TINTING = "spec.svm", "spec.scc", "spec.bsd", "spec.tinting"

NA_VALUE = -1

# 3자리 코드는 전 차종 공통이다 (4장 STEP 40 실측)
OPTION3 = {HUD: "095", SUNROOF: "010", SVM: "087", SCC: "079", BSD: "086"}

SIMPLE = (HUD, SUNROOF, SVM, SCC, BSD)


def _installed(ctx: AxisContext) -> set[str]:
    s = ctx.snapshot
    return set(s.options_standard or []) | set(s.options_choice or [])


def _spec_table(ctx: AxisContext, comp: str):
    """1순위 — 제조사 사양표.  -1 은 여기서만 나온다."""
    on = (ctx.target_config.get("SPEC_DEFAULT_ON") or {}).get(comp)
    off = (ctx.target_config.get("SPEC_DEFAULT_OFF") or {}).get(comp)
    if on:
        return 1
    if off:
        return NA_VALUE
    return None


def analyze_spec(ctx: AxisContext, v: Verdict) -> None:
    s, r = ctx.snapshot, ctx.policy.rule("spec")
    codes = _installed(ctx)
    has_codes = s.options_standard is not None or s.options_choice is not None

    for comp in SIMPLE:
        table = _spec_table(ctx, comp)
        if table == NA_VALUE:
            put(v, comp, NA_VALUE, PRIO_MANUFACTURER, "spec_table", excluded=True)
            continue
        if table == 1:
            put(v, comp, ctx.policy.comp(comp), PRIO_MANUFACTURER, "spec_table")
            continue
        if not has_codes:
            put(v, comp, None, PRIO_OBSERVED, "missing", excluded=True)
            continue
        hit = OPTION3[comp] in codes
        put(v, comp, ctx.policy.comp(comp) if hit else 0,
            PRIO_OBSERVED, "installed")

    _hda(ctx, v, r, codes, has_codes)
    _tinting(ctx, v)


def _hda(ctx, v, r, codes, has_codes) -> None:
    """HDA 3단계.  옵션명이 아니라 description 을 본다 (STEP 75).

    v1 문서의 「1044 = 고속도로 주행 보조 2」는 근거가 없었다.
    실제 옵션명은 「드라이빙 어시스턴스 패키지 II」이고, Ⅰ 에는 HDA 가 없다.
    """
    table = _spec_table(ctx, HDA)
    if table == NA_VALUE:
        put(v, HDA, NA_VALUE, PRIO_MANUFACTURER, "spec_table", excluded=True)
        return
    if not r.get("hda_gate_open"):
        # ★ 2026-08-11 실측으로 열렸다.  닫힌 상태는 근거가 없을 때만이다
        put(v, HDA, None, PRIO_MANUFACTURER, "gate_closed", excluded=True)
        return
    if table == 1:
        put(v, HDA, r["hda_points"]["2"], PRIO_MANUFACTURER, "spec_table")
        return
    if not has_codes:
        put(v, HDA, None, PRIO_OBSERVED, "missing", excluded=True)
        return
    descs = " ".join(
        ctx.dicts.option_descriptions.get(c, "") for c in sorted(codes))
    if not descs.strip():
        # ★ 카탈로그를 못 받은 매물이다.  Gate 미통과가 아니다 (STEP 75)
        put(v, HDA, None, PRIO_OBSERVED, "catalog_missing", excluded=True)
        return
    # ★ 2 문구를 먼저 본다.  1 문구가 2 문구에 포함된다
    level = "0"
    if any(p in descs for p in r["hda_level2_phrases"]):
        level = "2"
    elif any(p in descs for p in r["hda_level1_phrases"]):
        level = "1"
    put(v, HDA, r["hda_points"][level], PRIO_CLASSIFIER_OR_OBSERVED,
        "catalog_description")


PRIO_CLASSIFIER_OR_OBSERVED = PRIO_OBSERVED


def _tinting(ctx: AxisContext, v: Verdict) -> None:
    """언급 없음은 NULL + excluded 다.  0 이 아니다 (STEP 75).

    미언급을 0 으로 떨어뜨리면 광고를 성실히 쓴 딜러가 불리해진다.
    키워드는 사전이다.  코드에 배열로 박지 않는다
    """
    text = ctx.snapshot.ad_body_text
    if not text:
        put(v, TINTING, None, PRIO_KEYWORD, "no_mention", excluded=True)
        return
    hit = any(k in text for k in ctx.dicts.tint_keywords)
    if hit:
        put(v, TINTING, ctx.policy.comp(TINTING), PRIO_KEYWORD, "ad_text")
    else:
        put(v, TINTING, None, PRIO_KEYWORD, "no_mention", excluded=True)
