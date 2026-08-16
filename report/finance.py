# -*- coding: utf-8 -*-
"""금융 — 점수가 아니라 비용이다.

지시서   9장 STEP 91 · 7장 STEP 83
근거     ★ 선납금은 취득 부대비용을 포함한 초기 현금 부담이다.  표시가와 무관하게 고정이다
         순서   ① 취득 부대비용 산출  ② 차값 선납 = 선납금 − 부대비용
                ③ 할부 원금 = 표시가 − 차값 선납
금지     표시가에 취득세를 더한 뒤 거기서 선납금을 빼는 것
         → 선납금에 이미 취득세가 들어 있으므로 두 번 반영된다
         보증 잔여 가치를 실구매가에서 차감하는 것 (가격·보증 이중 계산)
         1500 · 48 · 5.5 를 코드에 상수로 두는 것 (V4-13)
"""
from __future__ import annotations

from report.views import FinanceView

MONTHS_PER_YEAR = 12


def acquisition_cost(price_won: int, fin: dict, target_key: str | None,
                     tinting_needed: bool = False) -> tuple[int, tuple[str, ...]]:
    """취득 부대비용.  실구매가에 가산한다 (STEP 83).

    반환   (금액, 추정 항목 목록)
    """
    exempt = target_key in (fin.get("ev_tax_exempt") or [])
    tax = 0 if exempt else int(round(price_won * fin["tax_acquisition_rate"]))
    fees = sum(int(fin.get(k) or 0) for k in
               ("fee_stamp", "fee_transfer", "fee_delivery"))
    if tinting_needed:
        fees += int(fin.get("fee_tinting") or 0)
    return tax + fees, tuple(fin.get("_estimated") or ())


def monthly_payment(principal: int, annual_rate: float, months: int) -> int:
    """원리금 균등.  월 납입 = 원금 × r × (1+r)^n ÷ ((1+r)^n − 1)."""
    if principal <= 0 or months <= 0:
        return 0
    r = annual_rate / MONTHS_PER_YEAR
    if r == 0:
        return int(round(principal / months))
    f = (1 + r) ** months
    return int(round(principal * r * f / (f - 1)))


def build_finance(price_listed_won: int | None, fin: dict,
                  target_key: str | None,
                  tinting_needed: bool = False) -> FinanceView | None:
    """배분이 먼저다.  초기 현금 부담은 선납금 고정이다.

    전액 현금   표시가 + 부대비용 <= 선납금
    선납 부족   부대비용 > 선납금  →  차값 선납 0 · 부족액 표시
    검산       차값 선납 + 할부 원금 == 표시가
    """
    if price_listed_won is None:
        return None
    cost, est = acquisition_cost(price_listed_won, fin, target_key,
                                 tinting_needed)
    down = int(fin["down_payment_won"])
    months = int(fin["loan_months"])

    if price_listed_won + cost <= down:
        return FinanceView(price_listed_won, cost, down, price_listed_won,
                           0, 0, 0, True, 0, est)

    shortfall = max(0, cost - down)
    vehicle_down = max(0, down - cost)
    principal = price_listed_won - vehicle_down
    pay = monthly_payment(principal, float(fin["loan_rate_annual"]), months)
    return FinanceView(price_listed_won, cost, down, vehicle_down, principal,
                       pay, pay * months - principal, False, shortfall, est)


def price_for_monthly(monthly_cap_won: int, fin: dict,
                      target_key: str | None) -> int:
    """월납입이 상한 이하가 되는 가장 비싼 표시가.

    ★ 「월 80만 이하」를 SQL 로 걸려면 가격 상한이 필요하다.
      build_finance 를 그대로 불러 되짚는다 — 식을 두 벌 두지 않는다
    """
    if monthly_cap_won <= 0:
        return 0
    # ★ 상한을 상수로 박지 않는다.  월 납입 × 개월수는 원금보다 크고,
    #   원금은 표시가보다 크지 않다 — 그러니 이것이 확실한 상한이다.
    #   선납금만큼 더 얹어 경계를 넘긴다 (V4-13)
    lo = 0
    hi = monthly_cap_won * int(fin["loan_months"]) + int(fin["down_payment_won"])
    while hi - lo > 1:                      # 1원까지 좁힌다.  횟수도 안 박는다
        mid = (lo + hi) // 2
        got = build_finance(mid, fin, target_key)
        if got and got.monthly_payment_won <= monthly_cap_won:
            lo = mid
        else:
            hi = mid
    return lo
