# -*- coding: utf-8 -*-
"""안전 40점 — 진단 20 + 보증상품 20.

지시서   7장 STEP 79
근거     전기 4종은 extendWarranty · deemedExtendWarranty 가 매물 전건 0 이다.
         상품 구조상 부재이므로 -1 (분모 제외)이다.  0 점이 아니다
금지     facet Trust 를 근거로 쓰는 것 — BANNED_SOURCES 다.
         v1 초판이 그것을 근거로 삼았고, 0 인 것은 Warranty 가 아니라 ExtendWarranty 였다
압류·저당 여기서 점수화하지 않는다.  E등급 절대조건이다 (STEP 82)
"""
from __future__ import annotations

from analyze.axes import AxisContext
from analyze.verdict import PRIO_MANUFACTURER, PRIO_OBSERVED, Verdict, put

DIAGNOSIS = "safety.diagnosis"
PRODUCT = "safety.warranty_product"

NA_VALUE = -1


def analyze_safety(ctx: AxisContext, v: Verdict) -> None:
    s, r = ctx.snapshot, ctx.policy.rule("safety")

    diag = ctx.snapshot.diagnosis_car
    if diag is None:
        put(v, DIAGNOSIS, None, PRIO_OBSERVED, "missing", excluded=True)
    else:
        put(v, DIAGNOSIS, r["diagnosis_yes"] if diag else r["diagnosis_no"],
            PRIO_OBSERVED, "advertisement_diagnosisCar")

    # 차종 상품 구조가 1순위다 (STEP 79 근거 우선순위)
    if s.target_key in r["warranty_product_na_targets"]:
        put(v, PRODUCT, NA_VALUE, PRIO_MANUFACTURER, "product_absent",
            excluded=True)
        return
    ext = ctx.snapshot.warranty_extend
    deemed = ctx.snapshot.warranty_deemed
    if ext is None and deemed is None:
        put(v, PRODUCT, None, PRIO_OBSERVED, "missing", excluded=True)
        return
    has = bool(ext) or bool(deemed)
    put(v, PRODUCT, r["warranty_product_yes"] if has else r["warranty_product_no"],
        PRIO_OBSERVED, "advertisement_warranty")
