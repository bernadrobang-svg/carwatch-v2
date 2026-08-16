# -*- coding: utf-8 -*-
"""② 상태 180점 — 사고 70 · 골격 40 · 수리비 30 · 용도 25 · 보증 15.

지시서   7장 STEP 76 · 77 · 78 · 72 · 5장 「배점 재설계 — 시장 기준」 (개정 292) · 개정 302 (렌트 세 곳 대조)
근거     「사고는 가격 결정에 가장 큰 영향을 미치는 감가 요인」
        A등급 사고차(프론트휀더·도어패널·트렁크리드) 평균 감가 12.02±5.43%
        「렌트·리스는 정상 시세보다 큰 감가 요인」
★ 마스터 지적 — 「깡통에 HUD 만 있어도 만점」.  옛 배점은 상태 55 < 사양 90 이었다
금지     부위명 문자열로 골격을 판정하는 것.  RANK_A/B/C 를 쓴다
"""
from __future__ import annotations

from analyze.axes import AxisContext
from analyze.axis._util import months_between
from analyze.axis.history import rental_findings
from analyze.axis.warranty import _remaining_months
from analyze.verdict import PRIO_MANUFACTURER, PRIO_OBSERVED, Verdict, put

ACCIDENT = "state.accident"
FRAME = "state.frame"
REPAIR = "state.repair"
USAGE = "state.usage"
WARRANTY = "state.warranty"

# 골격 상태 — 무거운 쪽이 이긴다.  한 판에 여러 상태가 붙는다
FRAME_SWAP = ("교환(교체)", "용접,절단")
FRAME_SHEET = ("판금/용접",)


def _accident(ctx: AxisContext, v: Verdict) -> None:
    """사고 회수 70 — 무사고 70 · 1회 40 · 2회 20 · 3회 이상 0."""
    s, r = ctx.snapshot, ctx.policy.rule("state")
    my, other = s.accident_my_cnt, s.accident_other_cnt
    if my is None and other is None:
        put(v, ACCIDENT, None, PRIO_OBSERVED, "missing", excluded=True)
        return
    n = (my or 0) + (other or 0)
    table = r["accident_by_count"]
    put(v, ACCIDENT, table.get(str(n), r["accident_min"]),
        PRIO_OBSERVED, "record_accident_count")


def frame_state(panels: list, frame_ranks) -> str:
    """골격 판의 가장 무거운 상태 (개정 292 ②).

    ★ 랭크가 골격을 정한다.  부위명 문자열이 아니다 —
      v1 은 사전이 「프론트펜더」, 원문이 「프론트 휀더(우)」여서 344건이 미분류였다
    """
    worst = "none"
    for el in panels:
        if not any(a in frame_ranks for a in (el.get("attributes") or [])):
            continue
        titles = [t.get("title") for t in (el.get("statusTypes") or [])]
        if any(t in FRAME_SWAP for t in titles):
            return "swap"
        if any(t in FRAME_SHEET for t in titles):
            worst = "sheet"
    return worst


def _frame(ctx: AxisContext, v: Verdict) -> None:
    """골격 손상 40 — 없음 40 · 판금 20 · 용접·교환 0."""
    s, r = ctx.snapshot, ctx.policy.rule("state")
    if s.inspection_panels is None:
        put(v, FRAME, None, PRIO_OBSERVED, "missing", excluded=True)
        return
    got = frame_state(s.inspection_panels,
                      ctx.policy.rule("absolute_fail")["frame_ranks"])
    put(v, FRAME, r["frame_points"][got], PRIO_OBSERVED, f"frame_{got}")


def _repair(ctx: AxisContext, v: Verdict) -> None:
    """자차 수리비 30 — 0원 30 · 100만 미만 20 · 300만 미만 10 · 그 이상 0.

    금지   insuranceBenefit 사용.  type 3(내 차 피해가 아닌 것)을 감점에 넣는 것
    """
    s, r = ctx.snapshot, ctx.policy.rule("state")
    cost = s.accident_my_cost
    if cost is None:
        put(v, REPAIR, None, PRIO_OBSERVED, "missing", excluded=True)
        return
    for row in r["repair_curve"]:
        edge = row["won"]
        if edge is None or cost < edge:
            put(v, REPAIR, int(row["points"]), PRIO_OBSERVED, "record_my_cost")
            return
    put(v, REPAIR, int(r["repair_curve"][-1]["points"]), PRIO_OBSERVED,
        "record_my_cost")


def _usage(ctx: AxisContext, v: Verdict) -> None:
    """용도 25 — 자가용 25 · 리스 10 · 렌트 0 (개정 292 · 302).

    ★ 렌트를 세 곳에서 대조한다 — 광고형태 · 점검부 용도변경 · 보험이력
    """
    s, r = ctx.snapshot, ctx.policy.rule("state")
    hist = ctx.policy.rule("history")
    found = rental_findings(s, hist["commercial_use_codes"])
    if found:
        keys = [k for k, _why in found]
        # 리스만 있고 렌트 근거가 없으면 리스다.  둘을 같은 점수로 두지 않는다
        lease_only = (keys == ["advertisement_type"]
                      and s.advertisement_type in r["lease_ad_types"])
        put(v, USAGE, r["usage_lease"] if lease_only else r["usage_rental"],
            PRIO_OBSERVED, "+".join(keys))
        return
    if (s.usage_change_types_json is not None or s.record_use_json is not None
            or s.plate_history_hash_json is not None):
        put(v, USAGE, r["usage_private"], PRIO_OBSERVED, "checked_three")
        return
    put(v, USAGE, r["usage_unknown"], PRIO_OBSERVED, "unknown")


def _warranty(ctx: AxisContext, v: Verdict) -> None:
    """보증 잔여 15 — 일반·엔진 잔여에 비례 (개정 292 ②).

    ★ 옛 배점은 보증만 100점이었다.  시장은 그만큼 안 쳐 준다
    """
    s = ctx.snapshot
    r = ctx.policy.rule("warranty")
    base = s.first_registration_date or s.year_month
    elapsed = months_between(base, ctx.target_config.get("as_of"))
    kpm = r["km_per_month"]
    remains = [
        _remaining_months(m, km, elapsed, s.mileage_km, kpm)
        for m, km in ((s.warranty_body_month, s.warranty_body_km),
                      (s.warranty_power_month, s.warranty_power_km))
    ]
    got = [x for x in remains if x is not None]
    if not got:
        put(v, WARRANTY, None, PRIO_MANUFACTURER, "missing", excluded=True)
        return
    full, cap = float(r["full_months"]), ctx.policy.comp(WARRANTY)
    # 둘 중 긴 쪽으로 본다.  ★ 엔진 보증이 남았으면 그것이 값이다
    best = max(got)
    pts = 0 if best <= 0 else round(min(best, full) / full * cap)
    put(v, WARRANTY, pts, PRIO_MANUFACTURER, "encar")


def analyze_state(ctx: AxisContext, v: Verdict) -> None:
    _accident(ctx, v)
    _frame(ctx, v)
    _repair(ctx, v)
    _usage(ctx, v)
    _warranty(ctx, v)
