# -*- coding: utf-8 -*-
"""이력 55점 — 사고 20 · 보험 15 · 렌트 20.

지시서   7장 STEP 76 (사고) · 77 (보험) · 78 (렌트)
근거     골격/외판은 attributes(RANK_*) 로 직접 판정한다.  부위명 문자열이 아니다
         v1 은 사전이 「프론트펜더」, 원문이 「프론트 휀더(우)」여서 344건이 미분류였고
         사고 20점이 한 번도 작동하지 않았다
금지     부위명 문자열 매칭.  type 3 을 감점에 넣는 것.  insuranceBenefit 사용
         SellType 을 렌트 1순위로 쓰는 것 — 현재 판매 형태지 과거 이력이 아니다
"""
from __future__ import annotations

import json

from analyze.axes import AxisContext
from analyze.verdict import PRIO_CLASSIFIER, PRIO_OBSERVED, Verdict, put

DAMAGE = "history.damage"
INSURANCE = "history.insurance"
RENTAL = "history.rental"

RENT_TITLE = "렌트"


SWAP = "swap"


def outer_swap_count(panels: list[dict], outer_ranks,
                     by_status: dict) -> int:
    """외판(RANK_ONE·TWO) 중 감점 대상 상태인 판수 (STEP 76).

    ★ 한 판에 여러 상태가 붙으면 가장 무거운 것으로 센다.
      교환 · 용접,절단  >  판금/용접  >  손상
    ★ 같은 판을 두 번 세지 않는다
    금지   상태로 골격을 판정하는 것.  골격은 랭크가 정한다
          RANK_TWO 는 「용접,절단」이 있어도 외판이다
    """
    n = 0
    for el in panels:
        ranks = el.get("attributes") or []
        if not any(a in outer_ranks for a in ranks):
            continue
        titles = [s.get("title") for s in (el.get("statusTypes") or [])]
        if any(by_status.get(t) == SWAP for t in titles):
            n += 1          # 판 단위로 한 번만 센다
    return n


def cost_points(ratio: float, curve: list) -> int:
    """금액 비율 → 점수.  마지막 항(ratio=null)이 초과 구간이다.

    경계를 실매물 분위수에 맞춘다.  한쪽에 몰리면 이 축이 순위를 못 가른다.
    """
    for row in curve:
        r = row["ratio"]
        if r is not None and ratio <= r:
            return row["points"]
    return curve[-1]["points"]


def _insurance(ctx: AxisContext, v: Verdict, r: dict) -> None:
    """금액 곡선 × 건수 상한 (STEP 77).

    ★ 금액 0 인데 사고 건수가 있는 경우 = type 3 만 있는 매물이다.
      내 차 피해가 아니므로 만점이고 건수 상한도 적용하지 않는다.
    필수   건수는 myAccidentCnt 다.  accidentCnt 가 아니다
    금지   type 3 을 감점에 넣는 것.  insuranceBenefit 사용
    """
    s = ctx.snapshot
    cost, cnt = s.accident_my_cost, s.accident_my_cnt
    if cost is None or cnt is None:
        put(v, INSURANCE, None, PRIO_OBSERVED, "missing", excluded=True)
        return
    full = ctx.policy.comp(INSURANCE)
    if not cost:
        # type 3 만 있는 매물 · 무사고 둘 다 여기다.  내 차 피해 금액이 0 이다
        put(v, INSURANCE, full, PRIO_OBSERVED, "no_own_damage")
        return
    if not s.price_origin_won:
        put(v, INSURANCE, None, PRIO_OBSERVED, "origin_price_missing",
            excluded=True)
        return
    pts = cost_points(cost / s.price_origin_won, r["insurance_cost_curve"])
    cap = r["insurance_cap_by_count"].get(str(cnt), r["insurance_cap_min"])
    put(v, INSURANCE, min(pts, cap), PRIO_OBSERVED, "record_cost_and_count")


def analyze_history(ctx: AxisContext, v: Verdict) -> None:
    s = ctx.snapshot
    r = ctx.policy.rule("history")
    af = ctx.policy.rule("absolute_fail")

    # ── 사고 20점 (STEP 76) ──────────────────────────────────────────
    if s.inspection_panels is None:
        put(v, DAMAGE, None, PRIO_OBSERVED, "missing", excluded=True)
    else:
        n = outer_swap_count(s.inspection_panels, af["outer_ranks"],
                             r["damage_by_status"])
        table = r["damage_by_swap"]
        pts = table.get(str(n), r["damage_min"])
        put(v, DAMAGE, pts, PRIO_OBSERVED, "inspection_outers")

    # ── 보험 15점 (STEP 77) ──────────────────────────────────────────
    _insurance(ctx, v, r)

    # ── 렌트 20점 (STEP 78) ──────────────────────────────────────────
    rr = r["rental"]
    usage = ctx.snapshot.usage_change_types_json
    if usage is not None:
        types = json.loads(usage)
        is_rent = any(t.get("title") == RENT_TITLE for t in types)
        put(v, RENTAL, rr["rental"] if is_rent else rr["non_rental"],
            PRIO_OBSERVED, "usage_change_types")
        return
    # ★ 허·하·호 = 렌터카.  원본이 아니라 파생 한 글자로 판정한다 (STEP 35)
    if s.plate_use_char is not None:
        put(v, RENTAL, rr["rental"], PRIO_CLASSIFIER, "plate_use_char")
        return
    if s.plate_history_hash_json is not None:
        put(v, RENTAL, rr["non_rental"], PRIO_CLASSIFIER, "record_plate")
        return
    # 불명 — 수집 실패를 렌트로 단정하지 않는다.  0 으로 두면 실패가 감점이 된다
    put(v, RENTAL, rr["unknown"], PRIO_CLASSIFIER, "unknown")
