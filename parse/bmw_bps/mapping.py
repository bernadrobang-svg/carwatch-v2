# -*- coding: utf-8 -*-
"""BMW BPS 상세 파서 (`docs/BMW_BPS_API.md` 08-29 절).

★★★ 마스터 — 「★ **BMW 값 주행이란 것들은 무슨 의미인지 잘 모르겠어.
   ★ 현재 BMW 값을 못 갖고 와서 문제 아니냐**」 → ★ 그렇다.

★ 규격이 08-29 에 정정했다 — ★ 「가격은 목록 카드에 있다」가 **틀렸다.**
  ★ ★ 목록 카드 글자는 「`XM_BL 미네랄화이트 자동 휘발유`」 넉 줄뿐이고
  ★ ★ **값도 주행도 연식도 없다.**  ★ 다 상세에 있다.
★ 그래서 화면 BMW 가 **18/910** 이었다 (주행·예산·연식이 빈다)

값규칙  ★ 값은 ★ **딜러가 손으로 쓴 글**이라 꼴이 셋이다 —
        `판매가: 71,000,000원` · `차량가격 : 45,000,000 원` · `판매 가격 : 12,500만원`
금지    ★ 「신차가: 약 11300만원」을 ★ 판매가로 넣는 것
금지    ★ 쪽 아래 거르개의 ★ 「최저 가격 1500 만원 2000 만원 …」을 값으로 넣는 것 —
        ★ 「만원」만 찾으면 ★ 거르개 숫자가 들어온다.  ★ 반드시 라벨을 함께 본다
금지    ★ 못 잡은 것을 ★ 지어내는 것 — ★ 「값 없음」으로 남긴다
"""
from __future__ import annotations

import re

SITE_CODE = "bmw_bps"
WON_PER_MANWON = 10_000

RE_TAG = re.compile(r"<[^>]+>")

# ★ 라벨을 반드시 함께 본다 (금지 둘째)
RE_PRICE = re.compile(
    r"(?:판매\s*가격|판매가|차량가격)\s*:?\s*([\d,]+)\s*(원|만원)")
# ★ 신차가는 ★ **판매가가 아니다** — ★ 따로 뽑아 `price_origin_won` 으로 간다
RE_NEW = re.compile(r"신차가\s*:?\s*약?\s*([\d,]+)\s*만원")
RE_MILEAGE = re.compile(r"주행거리\s*([\d,]+)\s*km")
RE_YEAR = re.compile(r"연식\s*(\d{4})")
RE_REG = re.compile(r"차량\s*등록일\s*(\d{4})\s*/\s*(\d{1,2})")
RE_ACCIDENT = re.compile(r"사고유무\s*(\S+)")
RE_INSPECT = re.compile(r"(\d+)\s*가지\s*점검\s*(\S+)")
RE_SEIZE = re.compile(r"압류\s*(\d+)\s*건\s*,?\s*저당\s*(\d+)\s*건")
# ★★ 08-30 — ★ 연료가 없으면 ★ 차종이 안 갈린다 (X3 는 휘발유·경유가 갈린다).
#   ★ 목록 카드에는 낱말로만 있고 ★ 우리가 안 읽었다 — ★ 상세가 「연료 휘발유」로 준다
RE_FUEL = re.compile(r"연료\s*(\S+)")
RE_CC = re.compile(r"배기량\s*([\d,]+)")
RE_TRANS = re.compile(r"변속기\s*(\S+)")


def _text(html: str) -> str:
    """★ 태그를 걷고 ★ 사이 빈칸을 하나로 만든다 — ★ 낱말이 줄에 걸려도 잡히게."""
    return " ".join(RE_TAG.sub(" ", html or "").split())


def _int(v) -> int | None:
    try:
        return int(str(v).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def parse_detail(html: str, source_id: str) -> dict:
    """상세 한 장 → `core_listing` 몫.

    ★ 못 잡은 칸은 ★ **안 넣는다** — ★ `None` 을 넣어 덮어쓰지 않는다.
      ★ ★ 목록이 넣어 둔 값을 ★ 상세가 지우면 안 된다
    """
    t = _text(html)
    out: dict = {"site": SITE_CODE, "source_id": str(source_id),
                 "price_unit": "won"}

    m = RE_PRICE.search(t)
    if m:
        won = _int(m.group(1))
        if won is not None:
            out["price_current_won"] = (won * WON_PER_MANWON
                                        if m.group(2) == "만원" else won)
    m = RE_NEW.search(t)
    if m:
        won = _int(m.group(1))
        if won is not None:
            # ★ 신차가는 ★ 늘 「만원」으로 적힌다 (실측 08-29)
            out["price_origin_won"] = won * WON_PER_MANWON
    m = RE_MILEAGE.search(t)
    if m and _int(m.group(1)) is not None:
        out["mileage_km"] = _int(m.group(1))
    m = RE_YEAR.search(t)
    if m:
        out["form_year"] = _int(m.group(1))
    m = RE_REG.search(t)
    if m:
        # ★ 「연식」과 ★ 「차량 등록일」이 ★ 다를 수 있다 (2024 연식 · 2023/11 등록).
        #   ★ `year_month` 는 ★ **등록**이다 — ★ 감가는 등록으로 센다
        out["year_month"] = f"{m.group(1)}-{int(m.group(2)):02d}"
    m = RE_FUEL.search(t)
    if m:
        out["fuel_raw"] = m.group(1)
    m = RE_CC.search(t)
    if m and _int(m.group(1)):
        out["displacement_cc"] = _int(m.group(1))
    m = RE_TRANS.search(t)
    if m:
        out["transmission_raw"] = m.group(1)
    m = RE_ACCIDENT.search(t)
    if m:
        out["accident_raw"] = m.group(1)
    m = RE_SEIZE.search(t)
    if m:
        out["seizure_count"] = _int(m.group(1))
        out["mortgage_count"] = _int(m.group(2))
    return out


def inspect_of(html: str) -> tuple:
    """★ 「72가지 점검 없음」 — ★ (몇 가지, 결과).  ★ 못 찾으면 (None, None)."""
    m = RE_INSPECT.search(_text(html))
    return (_int(m.group(1)), m.group(2)) if m else (None, None)
