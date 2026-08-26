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


def purchase_cost(site: str, price_won: int | None, fin: dict, sites: dict,
                  target_key: str | None = None,
                  site_total_won: int | None = None):
    """그 사이트에서 사면 실제로 얼마를 내는가 (8장 · 개정 353).

    마스터 확정 — 「사이트별로 정책이 다를 건데.  케이카로 구매 시 가격이고
    엔카 구매 시 가격이잖아.  사이트별 총합을 내라」

    ★ 사이트가 총액을 주면 그것을 쓴다 — 우리가 계산하지 않는다 (개정 353 [원문])
    ★ 안 주면 계산하고 「추정」이라 적는다.  단정하지 않는다
    금지   차량가만 내는 것
    금지   점수에 넣는 것 — 가격 축과 이중 계산이 된다
    ★ 사이트 이름을 코드에 박지 않는다 (V3-55).  sites.json 이 정본이다
    """
    from report.views import PurchaseCostItem, PurchaseCostView

    one = sites.get(site) if isinstance(sites.get(site), dict) else None
    rule = (one or {}).get("purchase_cost")
    if price_won is None or not rule:
        return None
    label = (one or {}).get("label") or site
    # ★★ 08-26 — ★ 시안은 「차값」이고 ★ 규격은 「차량가」다 (41-view.md:74).
    #   ★ ★ 어긋난다.  ★ 규칙 1 대로 ★ **규격을 따른다** — ★ 가이드께 여쭈었다
    items = [PurchaseCostItem("차량가", int(price_won), False)]

    # 사이트가 총액을 줬으면 내역을 우리가 지어내지 않는다
    if site_total_won is not None:
        rest = int(site_total_won) - int(price_won)
        if rest:
            items.append(PurchaseCostItem("사이트가 낸 부대비용", rest, False))
        return PurchaseCostView(
            site, label, tuple(items), int(site_total_won), True,
            tuple(rule.get("extra_benefit") or ()))

    # ★ 이전등록비는 법정 요율이라 계산할 수 있다.  다만 공채·증지는
    #   finance.json 의 bond_table 이 비어 있어 못 넣는다 — 그래서 「추정」이다
    if rule.get("transfer_fee_rule") == "acquisition":
        got, est = acquisition_cost(int(price_won), fin, target_key)
        # ★ 시안은 「이전비」 · 규격은 「이전등록비」다 (40-report.md:668).  ★ 규격을 따른다
        items.append(PurchaseCostItem("이전등록비", got, bool(est)))
    for key, name in (("warranty_fee", "보증 가입비"),
                      ("etc_fee", "기타"),
                      ("delivery_fee", "배송비")):
        won = int(rule.get(key) or 0)
        if won:
            items.append(PurchaseCostItem(name, won, False))
    total = sum(x.won for x in items)
    return PurchaseCostView(site, label, tuple(items), total, False,
                            tuple(rule.get("extra_benefit") or ()))


def monthly_payment(principal: int, annual_rate: float, months: int) -> int:
    """원리금 균등.  월 납입 = 원금 × r × (1+r)^n ÷ ((1+r)^n − 1)."""
    if principal <= 0 or months <= 0:
        return 0
    r = annual_rate / MONTHS_PER_YEAR
    if r == 0:
        return int(round(principal / months))
    f = (1 + r) ** months
    return int(round(principal * r * f / (f - 1)))


def cash_limit(fin: dict) -> int:
    """현금 상한 (개정 400).  ★ config 를 읽는 자리는 여기 하나다.

    마스터 확정 — 「1500 은 사정을 봐서 일괄로 바꾸는 기준값으로」
    ★ 여기저기서 읽으면 「일괄로 바꾼다」가 성립하지 않는다 (V11-152)
    """
    return int(fin["cash_limit"])


def build_finance(price_listed_won: int | None, fin: dict,
                  target_key: str | None,
                  tinting_needed: bool = False) -> FinanceView | None:
    """배분이 먼저다.  초기 현금 부담은 선납금 고정이다.

    전액 현금   표시가 + 부대비용 <= 현금 상한
    검산       차값 선납 + 할부 원금 == 표시가

    ★ 개정 400 — 부족액을 내지 않는다.  화면은 「전액 현금」인가 아닌가
      둘뿐이다.  1,500만은 총액 상한이지 「모자란 만큼 더 내는 돈」이 아니다
    """
    if price_listed_won is None:
        return None
    cost, est = acquisition_cost(price_listed_won, fin, target_key,
                                 tinting_needed)
    down = cash_limit(fin)
    months = int(fin["loan_months"])

    if price_listed_won + cost <= down:
        return FinanceView(price_listed_won, cost, down, price_listed_won,
                           0, 0, 0, True, est)

    vehicle_down = max(0, down - cost)
    principal = price_listed_won - vehicle_down
    pay = monthly_payment(principal, float(fin["loan_rate_annual"]), months)
    return FinanceView(price_listed_won, cost, down, vehicle_down, principal,
                       pay, pay * months - principal, False, est)


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
    hi = monthly_cap_won * int(fin["loan_months"]) + cash_limit(fin)
    while hi - lo > 1:                      # 1원까지 좁힌다.  횟수도 안 박는다
        mid = (lo + hi) // 2
        got = build_finance(mid, fin, target_key)
        if got and got.monthly_payment_won <= monthly_cap_won:
            lo = mid
        else:
            hi = mid
    return lo
