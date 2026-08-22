# -*- coding: utf-8 -*-
"""현대·제네시스 인증중고차 목록 카드 → CORE 필드 (L3).

지시서   `docs/HYUNDAI_CERTIFIED_API.md` 5장 · 명령서 `ORDER_20260822_r515.md` 3장
값규칙   ★ 목록 응답은 ★ HTML 조각이다.  ★ 카드 하나가 한 매물이다
        ★ 표시가는 ★ 할인 뒤 값을 쓴다 (HYUNDAI_CERTIFIED_API 2a)
        ★ 값이 ★ 만원 단위로 온다
금지     ★ 번호판 원본을 core 에 넣는 것 — ★ PII 다 (STEP 35 · V2-11)
금지     ★ 못 읽은 칸을 0 으로 채우는 것.  ★ 없으면 None 이다
"""
from __future__ import annotations

import re

WON_PER_MANWON = 10_000
PRICE_UNIT = "manwon"

RE_GOODS = re.compile(r'data-favContsNo=["\']([A-Z]{3}\d{12})["\']')
# ★★ 카드의 머리는 ★ 상품 이미지다 — ★ alt 에 제목이 통째로 있다 (실측 08-23)
#   「alt="2023 투싼(NX4) 하이브리드 2WD 모던"」
#   ★ 표시(data-favContsNo)는 그 ★ 뒤에 두 번 나온다 (찜하기 · 비교하기)
RE_CARD_HEAD = re.compile(r'alt="(\d{4}\s[^"]{3,60})"')
# 「23년 11월」 — ★ 최초등록 연·월
RE_YM = re.compile(r"(\d{2})년\s*(\d{1,2})월")
RE_KM = re.compile(r"([\d,]+)\s*km")
RE_PLATE = re.compile(r"(\d{2,3}[가-힣]\d{4})")
RE_MANWON = re.compile(r"([\d,]+)\s*만원")


def _int(text: str | None) -> int | None:
    if not text:
        return None
    try:
        return int(text.replace(",", ""))
    except ValueError:
        return None


def cards(html: str) -> list:
    """카드 단위로 자른다.  ★ 상품 이미지가 카드의 머리다.

    ★★ 실측 08-23 — ★ 표시(data-favContsNo)를 경계로 삼으면 어긋난다.
      ★ 표시가 카드 ★ 가운데에 두 번 나오기 때문이다 (찜하기 · 비교하기).
      ★ 제목은 이미지 alt 에 있고 ★ 표시보다 앞이다
    """
    marks = [m.start() for m in RE_CARD_HEAD.finditer(html or "")]
    out = []
    for i, at in enumerate(marks):
        end = marks[i + 1] if i + 1 < len(marks) else len(html)
        out.append(html[at:end])
    return out


def parse_card(chunk: str, site: str) -> dict | None:
    """카드 하나 → core_listing 필드.  ★ 매물번호가 없으면 None 이다."""
    got = RE_GOODS.search(chunk)
    head = RE_CARD_HEAD.search(chunk)
    if not got or not head:
        return None
    name = head.group(1)                 # 「2023 투싼(NX4) 하이브리드 2WD 모던」
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", chunk))
    ym = RE_YM.search(text)
    km = RE_KM.search(text)
    plate = RE_PLATE.search(text)
    # ★ 값이 여럿 나온다 — 「2,570 만원 · 2,710 만원 · 140 만원 할인」.
    #   ★ 첫째가 ★ 할인 뒤 표시가다 (실측)
    prices = RE_MANWON.findall(text)
    return {
        "site": site,
        "source_id": got.group(1),
        "site_manufacturer": "현대",
        "site_model": name,
        # ★ 「2023 투싼(NX4) 하이브리드 …」 → 차종은 연식 다음 낱말이다
        # ★ 「2023 투싼(NX4) 하이브리드」 → 투싼 · 「2023 GV70 가솔린 …」 → GV70
        "site_model_group": (name.split(maxsplit=2)[1].split("(")[0].strip()
                             if len(name.split()) > 1 else None),
        "form_year": _int(name.split(maxsplit=1)[0]),
        "year_month": (f"20{ym.group(1)}-{int(ym.group(2)):02d}"
                       if ym else None),
        "mileage_km": _int(km.group(1)) if km else None,
        "price_current_won": (_int(prices[0]) * WON_PER_MANWON
                              if prices else None),
        "price_unit": "won",
        # ★★ 번호판은 ★ PII 다.  ★ split_pii 가 해시한다 (V2-11 에서 배웠다)
        "_pii_plate_no": plate.group(1) if plate else None,
    }
