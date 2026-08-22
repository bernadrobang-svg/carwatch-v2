# -*- coding: utf-8 -*-
"""③ 이력 80 — 어떻게 쓰였나 (docs/ref/F-scoring.md ③).

지시서   7장 STEP 78 · `docs/ref/F-scoring.md` ③ (개정 329)
축      용도 30 · 자차 미가입 25 · 소유자 변경 15 · 압류·저당 10
근거     ★ 렌트를 세 곳에서 대조한다 (개정 302) —
        advertisementType 은 「지금 리스 상품인가」다.  과거 용도가 아니다
        ★ 소유자 변경은 연식 대비로 본다 — 3년차 3회는 1년차 3회보다 낫다
금지     SellType 을 렌트 1순위로 쓰는 것.  원문 없이 「자가용」으로 두는 것
"""
from __future__ import annotations

import json

from analyze.axes import AxisContext
from analyze.curve import ascending, step_down
from analyze.verdict import PRIO_OBSERVED, Verdict, put

USAGE = "history.use"
NOT_JOIN = "history.not_join"
OWNER = "history.owner"
LIEN = "history.seizing"

RENT_TITLE = "렌트"
# 광고형태가 이미 렌트·리스라고 말하는 것 (개정 302 ①)
RENT_AD_TYPES = {"RENT_SUCCESSION": "렌트 승계 매물",
                 "RENT_CAR": "렌터카",
                 "OPERATING_LEASE": "운용리스 매물",
                 "FINANCING_LEASE": "금융리스 매물"}
LEASE_AD_TYPES = ("OPERATING_LEASE", "FINANCING_LEASE")


def rental_findings(s, commercial_codes) -> list:
    """렌트 이력을 세 곳에서 찾는다 (개정 302).

    ★ 실측 08-17 — 「렌트 아님」이라 한 144건이 광고형태로는 렌트·리스였다
    ★ 보험이력 용도 코드의 뜻이 규격에 없어 실측으로 짚었다 —
      점검부가 「렌트」라 한 646건 중 627건에 용도 3(영업용)이 있었다
    """
    out = []
    if s.advertisement_type in RENT_AD_TYPES:
        out.append(("advertisement_type", RENT_AD_TYPES[s.advertisement_type]))
    if s.usage_change_types_json is not None:
        titles = [t.get("title") for t in json.loads(s.usage_change_types_json)]
        if RENT_TITLE in titles:
            out.append(("usage_change_types", "점검부 용도변경 렌트"))
    if s.record_use_json is not None:
        codes = json.loads(s.record_use_json)
        if any(str(c) in commercial_codes for c in codes):
            out.append(("record_use", "보험이력 영업용 이력"))
    if s.plate_use_char is not None:
        out.append(("plate_use_char", "번호판이 렌터카"))
    return out


def _usage(ctx: AxisContext, v: Verdict) -> None:
    """3-1 용도 30 — 자가용 30 · 관용 20 · 영업용 8 · 렌트 0 · 리스 10."""
    s, r = ctx.snapshot, ctx.policy.rule("history")
    pts = r["usage_points"]
    found = rental_findings(s, r["commercial_use_codes"])
    if found:
        keys = [k for k, _w in found]
        lease_only = (keys == ["advertisement_type"]
                      and s.advertisement_type in LEASE_AD_TYPES)
        put(v, USAGE, pts["lease"] if lease_only else pts["rental"],
            PRIO_OBSERVED, "+".join(keys))
        return
    # ★ 「자가용이다」는 셋 중 하나라도 실제로 봤을 때만 말할 수 있다
    if (s.usage_change_types_json is None and s.record_use_json is None
            and s.plate_history_hash_json is None):
        put(v, USAGE, 0, PRIO_OBSERVED, "missing")
        return
    if s.use_gov:
        put(v, USAGE, pts["government"], PRIO_OBSERVED, "record_gov")
        return
    if s.use_business:
        put(v, USAGE, pts["business"], PRIO_OBSERVED, "record_business")
        return
    put(v, USAGE, pts["private"], PRIO_OBSERVED, "checked_three")


def _not_join(ctx: AxisContext, v: Verdict) -> None:
    """3-2 자차 미가입 25 — 미가입 기간 ÷ 보유 기간 (개정 294).

    ★ 그 기간의 사고는 알 수 없다.  「기간이 있다」가 아니라 비율이다
    """
    s, r = ctx.snapshot, ctx.policy.rule("history")
    if s.not_join_months is None:
        put(v, NOT_JOIN, 0, PRIO_OBSERVED, "missing")
        return
    # ★★ 개정 435 — 미가입 기간이 0 이면 보유 기간과 무관하게 흠이 없다.
    #   ★ 전에는 `not s.owned_months` 로 함께 걸러 「확인 안 됨」을 냈다.
    #     실측 08-21 — 갓 등록된 차 7건이 보유 0개월이라 여기 걸렸다.
    #     보험이력은 열려 있고(openData=true) 미가입 날짜가 하나도 없다 —
    #     ★ 「모른다」가 아니라 「미가입 기간이 없다」다
    if not s.not_join_months:
        ratio = 0.0
    elif not s.owned_months:
        put(v, NOT_JOIN, 0, PRIO_OBSERVED, "missing")
        return
    else:
        ratio = min(1.0, s.not_join_months / s.owned_months)
    put(v, NOT_JOIN, round(ascending(ratio, r["not_join_curve"])),
        PRIO_OBSERVED, f"not_join_{ratio:.0%}")


def _owner(ctx: AxisContext, v: Verdict) -> None:
    """3-3 소유자 변경 15 — 연식 대비로 본다.

    ★ 3년차에 3회면 1년차에 3회보다 낫다.
      횟수 ÷ 경과연수가 1.0 을 넘으면 한 단계 더 내린다
    """
    from analyze.axis.value import elapsed_years

    s, r = ctx.snapshot, ctx.policy.rule("history")
    if s.owner_change_cnt is None:
        put(v, OWNER, 0, PRIO_OBSERVED, "missing")
        return
    n = int(s.owner_change_cnt)
    years = elapsed_years(ctx)
    if years and n / years > float(r["owner_per_year_limit"]):
        n += 1                      # 한 단계 더 내린다
    put(v, OWNER, round(step_down(n, r["owner_curve"])),
        PRIO_OBSERVED, f"owner_{s.owner_change_cnt}")


def _lien(ctx: AxisContext, v: Verdict) -> None:
    """3-4 압류·저당 10 — 있으면 소유권 이전이 막힌다.  값보다 먼저 볼 것이다."""
    s, r = ctx.snapshot, ctx.policy.rule("history")
    got = (s.seizing_cnt, s.pledge_cnt)
    if all(x is None for x in got):
        put(v, LIEN, 0, PRIO_OBSERVED, "missing")
        return
    bad = any(x for x in got if x)
    put(v, LIEN, r["lien_bad"] if bad else r["lien_ok"],
        PRIO_OBSERVED, "detail_seizing")


def analyze_history(ctx: AxisContext, v: Verdict) -> None:
    _usage(ctx, v)
    _not_join(ctx, v)
    _owner(ctx, v)
    _lien(ctx, v)
