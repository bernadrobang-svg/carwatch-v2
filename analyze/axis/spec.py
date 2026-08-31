# -*- coding: utf-8 -*-
"""사양 90점 — HUD 20 · 선루프 20 · SVM 10 · SCC 10 · 후측방 5 · 틴팅 5.

지시서   7장 STEP 73 · 74 (근거 우선순위) · 75 (틴팅)
근거     사양표 > 실측 > 판정기 > 문자열.  뒤로 갈수록 틀릴 여지가 크다
         v1 은 판매글 키워드가 실장착을 이겨 선루프 84건이 부당하게 1이었다
금지     카탈로그 전체 목록 · facet Count 를 장착 근거로 쓰는 것
         put() 을 거치지 않고 값을 직접 대입하는 것
         -1 을 facet Count 0 으로 붙이는 것 — 제조사 사양표 근거로만 붙인다
"""
from __future__ import annotations

from analyze.axes import AxisContext
from analyze.verdict import (
    PRIO_KEYWORD, PRIO_MANUFACTURER, PRIO_OBSERVED, Verdict, put,
)

HUD, SUNROOF = "spec.hud", "spec.sunroof"
SVM, SCC, BSD, TINTING = "spec.svm", "spec.scc", "spec.bsd", "spec.tinting"

NA_VALUE = -1

# 3자리 코드는 전 차종 공통이다 (4장 STEP 40 실측)
OPTION3 = {HUD: "095", SUNROOF: "010", SVM: "087", SCC: "079", BSD: "086"}

SIMPLE = (HUD, SUNROOF, SVM, SCC, BSD)

# ★★★★★ 09-02 — ★ `OPTION3` 는 ★ **엔카 코드**다.  ★ K카는 HUD 가 `094` 다.
#   ★ 나머지 아홉 사이트는 ★ **한글 이름**을 준다 —
#   ★ ★ `"095" in {"파노라마 썬루프", …}` 은 ★ **언제나 거짓**이라 0점이었다.
#   ★ ★ ★ 표는 ★ 규격이 줬다 (`docs/OPTION_CATALOG.md` 「이름 맞대기 표」) —
#     ★ ★ `config/dictionaries/option_names.json` 의 `axis_match` 가 그 사본이다
AXIS_KEY = {HUD: "taste.hud", SUNROOF: "taste.sunroof",
            SVM: "spec.svm", SCC: "spec.scc", BSD: "spec.bsd"}


def _norm(name: str) -> str:
    """맞대기 꼴 — ★ **띄어쓰기·괄호·「썬/선」을 지운다** (규격 「맞대는 법」).

    ★ 「헤드업 디스플레이(HUD)」·「헤드업디스플레이」·「HUD」 → ★ 다 같은 것
    ★ 「파노라마 썬루프」·「파노라마선루프」·「와이드 선루프」 → ★ 다 선루프
    """
    import re as _re

    got = _re.sub(r"[\s()\[\]\u00b7,/-]+", "", str(name or ""))
    return got.replace("\uc37c", "\uc120").upper()


def _match_table(ctx: AxisContext) -> dict:
    """규격의 ★ **이름 맞대기 표**.  ★ 표에 없는 이름은 ★ 미확인 0점이다."""
    got = getattr(ctx.dicts, "option_axis_match", None)
    return got if isinstance(got, dict) else {}


def _has_option(ctx: AxisContext, comp: str):
    """이 차에 그 옵션이 있나.  ★ 모르면 ★ `None` — ★ 0 이 아니다.

    ★★ 규격 「맞대는 법」 — ★ **코드가 있으면 코드가 먼저**다 (엔카·K카) ·
      ★ ★ 없으면 ★ 이름이다.  ★ 사이트끼리 코드를 견주지 않는다 (오판 218)
    """
    # ★★★★★ 09-02 — ★ **「안 읽었다」와 「읽었는데 없다」는 다르다.**
    #   ★ `None` — ★ 원문에 옵션 칸이 아예 없었다 → ★ 미확인 (분모에서 뺀다)
    #   ★ `[]`  — ★ 읽었는데 ★ 하나도 없었다 → ★ **0점이 맞다** (확인한 0 이다)
    #   ★ 실측 09-02 — ★ 내가 이 둘을 뭉개서 ★ `test_score` 가 깨졌다
    s = ctx.snapshot
    if s.options_standard is None and s.options_choice is None:
        return None
    got = _installed(ctx)
    table = _match_table(ctx).get(AXIS_KEY.get(comp) or comp)
    if not got:
        return False
    if table:
        code = (table.get("codes") or {}).get(
            str(getattr(ctx.snapshot, "site", "") or ""))
        if code:
            return code in got
        want = [_norm(x) for x in (table.get("names") or ()) if _norm(x)]
        if want:
            # ★★★★★ 09-02 — ★ **품은 것도 맞다** (규격 「맞대는 법」).
            #   ★ 규격이 ★ 「파노라마 썬루프」·「와이드 선루프」를 ★ 선루프로 든다 —
            #   ★ ★ 곧 ★ **똑같은 글자만 찾는 것이 아니다.**
            #   ★ ★ ★ 실측 09-02 — ★ KB 는 ★ 「선루프 (일반)」로 준다.
            #     ★ ★ 똑같이만 찾으니 ★ 86건이 ★ 있는데도 0점이었다
            for one in got:
                k = _norm(one)
                if not k:
                    continue
                if any(w in k or k in w for w in want):
                    return True
            return False
    return OPTION3[comp] in got


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
    # ★ 개정 505 가 HDA 를 지우면서 rule("spec") 을 쓰는 곳이 없어졌다 —
    #   ★ 안 쓰는 이름을 남기면 ruff(F841)가 잡는다 (개발측 정리 08-23)
    s = ctx.snapshot
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
        hit = _has_option(ctx, comp)
        if hit is None:
            put(v, comp, None, PRIO_OBSERVED, "missing", excluded=True)
            continue
        put(v, comp, ctx.policy.comp(comp) if hit else 0,
            PRIO_OBSERVED, "installed")

    _tinting(ctx, v)


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
