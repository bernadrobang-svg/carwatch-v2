# -*- coding: utf-8 -*-
"""E등급 절대조건 10종.

지시서   7장 STEP 82
근거     되돌리기 어려운 판정이라 「모른다」를 「위험하다」로 바꾸지 않는다
값규칙   근거 필드가 NULL 이면 그 조건은 판정하지 않는다.  E 로 만들지 않는다
금지     부위명 문자열로 골격을 판정하는 것.  RANK_A/B/C 를 쓴다
         열거값을 손으로 적는 것 — 「OPERATING_LEASE 만」처럼 일부만 적으면 나머지가 통과한다
"""
from __future__ import annotations

from analyze.axes import AxisContext

FAIL_FRAME = "골격 손상"
FAIL_FLOOD = "침수"
FAIL_AIRBAG = "에어백 전개"
FAIL_TOTAL_LOSS = "전손"
FAIL_LEASE = "리스·렌트 상품"
FAIL_REPAIR = "수리비 10% 초과"
FAIL_RENT_NO_RECORD = "렌트인데 이력 없음"
FAIL_SEIZING = "압류"
FAIL_PLEDGE = "저당"
FAIL_SOLD = "계약중·판매완료"


# ★ 「모른다」와 「안전하다」는 다르다.
#   모르는 것을 안전으로 바꾸면 사면 안 되는 차가 통과한다 (영향분석 4)
UNKNOWN_SEIZING = "압류 확인 불가"
UNKNOWN_PLEDGE = "저당 확인 불가"


def absolute_fail(ctx: AxisContext) -> list[str]:
    """E등급 사유.  판정 못 한 항목은 absolute_check 로 따로 받는다."""
    return absolute_check(ctx)[0]


def absolute_check(ctx: AxisContext) -> tuple[list[str], list[str]]:
    """반환   (확정된 E 사유, 판정 못 한 항목)

    빈 사유 목록이면 절대조건에 걸리지 않았다.
    unknown 이 있으면 「그 항목은 확인하지 못했다」는 뜻이다 — 안전이 아니다.
    """
    s = ctx.snapshot
    r = ctx.policy.rule("absolute_fail")
    out: list[str] = []
    unknown: list[str] = []

    if s.inspection_panels is not None:
        if any(a in r["frame_ranks"]
               for el in s.inspection_panels
               for a in (el.get("attributes") or [])):
            out.append(FAIL_FRAME)

    if s.inspection_waterlog not in (None, "N", 0, "0"):
        out.append(FAIL_FLOOD)
    elif s.flood_total_cnt:
        out.append(FAIL_FLOOD)

    if s.airbag_deployed:
        out.append(FAIL_AIRBAG)
    if s.total_loss_cnt:
        out.append(FAIL_TOTAL_LOSS)

    # ★ 「현재 판매 형태」다.  과거 리스·렌트 이력은 E 가 아니다 (history_rental)
    ad_type = ctx.snapshot.advertisement_type
    if ad_type is not None and ad_type != r["advertisement_type_normal"]:
        out.append(FAIL_LEASE)
    elif ctx.snapshot.lease_rent_info is not None:
        out.append(FAIL_LEASE)

    if s.accident_my_cost is not None and s.price_origin_won:
        if s.accident_my_cost / s.price_origin_won > r["repair_cost_ratio"]:
            out.append(FAIL_REPAIR)

    # ★ None 은 「없음」이 아니라 「모름」이다.
    #   0 으로 보면 저당 있는 차를 놓친다 — 실측 79건이 None 이었다
    #   하나가 없다고 둘 다 못 보지는 않는다 — 필드마다 따로 본다
    if s.seizing_cnt is None:
        unknown.append(UNKNOWN_SEIZING)
    elif s.seizing_cnt:
        out.append(FAIL_SEIZING)
    if s.pledge_cnt is None:
        unknown.append(UNKNOWN_PLEDGE)
    elif s.pledge_cnt:
        out.append(FAIL_PLEDGE)
    if s.sales_status in r["sales_status_fail"]:
        out.append(FAIL_SOLD)
    return out, unknown
