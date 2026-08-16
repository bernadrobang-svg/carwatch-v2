# -*- coding: utf-8 -*-
"""주행거리 30점.

지시서   7장 STEP 81
근거     4만 이하 만점 — 전체의 38%.  10만 초과 0점 — 12% 만 해당
값규칙   주행 불명은 0 점이다.  excluded 가 아니다
         전 매물에 있어야 하는 값이라, 없으면 그것이 결함 신호다
금지     차종 내부 변별력이 0 이라는 이유로 배점을 낮추는 것
"""
from __future__ import annotations

from analyze.axes import AxisContext
from analyze.verdict import PRIO_OBSERVED, Verdict, put

AXIS = "mileage"


def analyze_mileage(ctx: AxisContext, v: Verdict) -> None:
    r = ctx.policy.rule("mileage")
    km = ctx.snapshot.mileage_km
    if km is None:
        put(v, AXIS, r["unknown_points"], PRIO_OBSERVED, "missing")
        return
    full, zero = r["full_km"], r["zero_km"]
    if km <= full:
        pts = ctx.policy.comp(AXIS)
    elif km >= zero:
        pts = 0
    else:
        pts = ctx.policy.comp(AXIS) * (zero - km) / (zero - full)
    put(v, AXIS, round(pts), PRIO_OBSERVED, "list_mileage")
