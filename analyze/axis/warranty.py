# -*- coding: utf-8 -*-
"""보증 100점 — 일반 50 + 파워트레인 50.

지시서   7장 STEP 72
근거     잔여 24개월 이상이면 그 사이 주요 고장이 무상 처리된다
         월 1,250km = 연 15,000km.  ★ 환산이 아니라 정책이다 → config
값규칙   음수 허용.  하한 0 으로 자르면 만료 페널티가 걸리지 않는다
금지     보증 잔여 가치를 실구매가에서 차감하는 것 (가격 축과 이중 계산)
         extendWarranty · deemedExtendWarranty 를 점수에 넣는 것 — 표시 전용
전기차   transmissionMonth 는 필드명이 '변속기'일 뿐 값은 배터리 보증이다.  그대로 쓴다
"""
from __future__ import annotations

from analyze.axes import AxisContext
from analyze.axis._util import months_between
from analyze.verdict import PRIO_MANUFACTURER, Verdict, put

GENERAL = "warranty.general"
POWER = "warranty.power"


def _remaining_months(months, km_limit, elapsed, mileage, km_per_month):
    """잔여 = min(보증월 − 경과월, (보증km − 주행km) ÷ 월주행)."""
    if months is None or elapsed is None:
        return None
    by_time = months - elapsed
    if km_limit is None or mileage is None:
        return by_time
    return min(by_time, (km_limit - mileage) / km_per_month)


def _score(remain, full_months, max_points, expire_penalty):
    if remain is None:
        return None
    if remain <= 0:
        return expire_penalty
    return round(min(remain, full_months) / full_months * max_points)


def analyze_warranty(ctx: AxisContext, v: Verdict) -> None:
    s, r = ctx.snapshot, ctx.policy.rule("warranty")
    base = s.first_registration_date or s.year_month
    elapsed = months_between(base, ctx.target_config.get("as_of"))
    kpm = r["km_per_month"]

    for comp, months, km in (
        (GENERAL, s.warranty_body_month, s.warranty_body_km),
        (POWER, s.warranty_power_month, s.warranty_power_km),
    ):
        remain = _remaining_months(months, km, elapsed, s.mileage_km, kpm)
        pts = _score(remain, r["full_months"], ctx.policy.comp(comp),
                     r["expire_penalty"])
        if pts is None:
            put(v, comp, None, PRIO_MANUFACTURER, "missing", excluded=True)
        else:
            put(v, comp, pts, PRIO_MANUFACTURER, "encar")
