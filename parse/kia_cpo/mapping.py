# -*- coding: utf-8 -*-
"""기아 인증중고차(CPO) 원문 → CORE 필드 (L3).

지시서   `docs/KIA_CPO_API.md` 2장(목록) · 명령서 `ORDER_20260822_r515.md` 3-1
근거     수집은 저장만 한다.  해석은 여기가 한다 (1장 STEP 9)
값규칙   ★ 값은 ★ 원 단위로 온다 (`price: 26830000`).  엔카는 만원이다 — 다르다
        ★ `firstRegisteredOn` 이 ★ 날짜로 온다 (2024-10-11).  엔카는 연·월이다
금지     ★ 없는 값을 지어내는 것.  ★ 안 오는 필드는 ★ None 이다 (금지 12)
금지     falsy 를 None 으로 만드는 것 — 「없음」이 「실패」로 저장된다
"""
from __future__ import annotations

import json

from errors import ParseError

PRICE_UNIT = "won"

# ★ 사이트가 요약해 주는 판정 (`customKeywords`).  ★ 우리가 뜻을 정하지 않는다 —
#   원문 그대로 남기고 축은 파서 밖(분석)에서 읽는다
KEYWORD_NO_INSURANCE = "보험이력없음"


def _json(value) -> str | None:
    """배열·객체는 ★ 직렬화만 한다.  가공하지 않는다 (STEP 19 금지)."""
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def _int(value) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _ym(value) -> str | None:
    """'2024-10-11' → '2024-10'.  ★ 날짜를 통째로 버리지 않는다 —
    원본은 first_registration 칸에 그대로 남는다
    """
    if not value or not isinstance(value, str) or len(value) < 7:
        return None
    return value[:7]


def _date10(value) -> str | None:
    if not value or not isinstance(value, str) or len(value) < 10:
        return None
    return value[:10]


def unpack_envelope(body: dict) -> tuple[int, list[dict]]:
    """봉투를 펼친다 (STEP 18a).  ★ 펼치는 것은 파싱이다."""
    if not isinstance(body, dict) or "content" not in body:
        raise ParseError("목록 봉투가 아니다", endpoint="list", step="STEP 18a")
    return int(body.get("totalElements") or 0), list(body.get("content") or [])


def next_cursors(rows: list) -> list | None:
    """다음 쪽 커서.  ★ 마지막 줄의 `cursors` 를 그대로 넘긴다.

    ★ 실측 — `&cursors=A&cursors=B` 로 ★ 같은 이름을 두 번 넘겨야 넘어간다.
      ★ `cursors=A,B` 로 한 번에 주면 ★ 첫 쪽이 그대로 온다
    """
    if not rows:
        return None
    got = rows[-1].get("cursors")
    return list(got) if got else None


def parse_list_item(item: dict, site: str) -> dict:
    """`content[]` 요소 → core_listing 필드 (KIA_CPO_API 2장).

    ★ 목록만으로 채워지는 것 — 트림 · 연식 · 주행 · 값 · 색상 · 사이트검증
    ★ 목록에 ★ 안 오는 것은 ★ 넣지 않는다.  상세가 채운다
    """
    sid = item.get("id")
    if sid is None:
        raise ParseError("id 없음", endpoint="list", step="STEP 19")
    keywords = item.get("customKeywords") or []
    return {
        # ★ listing_id 는 DB 가 만든다.  문자열로 조립하지 않는다 (STEP 30)
        "site": site,
        "source_id": str(sid),
        # ★ 기아 CPO 는 제조사가 기아뿐이다 (KIA_CPO_API 4장)
        "site_manufacturer": "기아",
        "site_model_group": item.get("modelCodeName"),
        "site_model": item.get("modelName"),
        "trim_badge": item.get("modelTrim"),
        "fuel_raw": item.get("modelEngine"),
        # ★ 값이 ★ 원 단위다.  엔카(만원)와 다르다
        "price_current_won": _int(item.get("price")),
        "price_unit": PRICE_UNIT,
        "mileage_km": _int(item.get("drivingDistance")),
        # ★ 날짜로 온다 — 연·월과 원본을 ★ 둘 다 남긴다
        "year_month": _ym(item.get("firstRegisteredOn")),
        "form_year": _int(item.get("modelYear")),
        "reg_at": _date10(item.get("firstRegisteredOn")),
        "color_ext_raw": item.get("exteriorColorCodeName"),
        "color_int_raw": item.get("interiorColorCodeName"),
        "transmission": item.get("modelMission"),
        "photo_main": item.get("exteriorImageUrl"),
        # ★ 사이트가 매기는 등급 — LITE · EXCLUSIVE · PREMIUM (실측 셋)
        "site_pass_grade": item.get("classification"),
        # ★ 사이트가 요약해 주는 판정.  ★ 원문 그대로 남긴다
        "site_condition_json": _json(keywords),
        # ★★ 번호판은 ★ PII 다 (STEP 35).  ★ 원본을 core 에 넣지 않는다 —
        #   ★ split_pii 가 해시로 바꾼다.  파서는 ★ 원문 이름으로 넘긴다
        "_pii_plate_no": item.get("plateNumber"),
        "first_ad_at": _date10(item.get("displayedAt")),
        # ★ 예약됨은 「팔렸다」가 아니다 (V6-06).  원문 그대로다
        "sales_status": "RESERVED" if item.get("reserved") else None,
        "view_cnt": _int(item.get("consultationCount")),
        "subscribe_cnt": _int(item.get("wishCount")),
    }

def parse_detail(doc: dict, site: str = "kia_cpo",
                 source_id: str | None = None) -> dict | None:
    """★★★★★ 09-04 (가이드 배포 실측) — ★ **상세 파서가 아예 없었다.**

    ★★★ 실측 09-04 — ★ 기아 CPO 상세 원문이 ★ **1,584건** 있는데
      ★ ★ `parse_detail` 이 없어 ★ 한 건도 못 풀었다 —
      ★ ★ ★ 그래서 ★ 상세율 **100%** 인데 ★ 파싱률은 **7%** 였다.
    ★★ 상세의 `car` 는 ★ 목록과 ★ **거의 같은 열쇠**를 쓴다 —
      ★ ★ 다른 것만 옮긴다 (`color` 가 묶음 · `trim` 이 낱말 · `engine`).
    ★ 원문에 없는 것은 ★ **안 만든다** (금지 12) — ★ 없으면 그 칸을 안 넣는다
    """
    if not isinstance(doc, dict):
        return None
    car = doc.get("car")
    if not isinstance(car, dict):
        return None
    sid = source_id or doc.get("id")
    if not sid:
        return None
    color = car.get("color") if isinstance(car.get("color"), dict) else {}
    got = {
        "site": site,
        "source_id": str(sid),
        "site_manufacturer": "기아",
        "site_model_group": car.get("modelCodeName"),
        "site_model": car.get("modelName"),
        "trim_badge": car.get("trim"),
        "fuel_raw": car.get("engine"),
        "price_current_won": _int(car.get("price")),
        "price_unit": PRICE_UNIT,
        "mileage_km": _int(car.get("drivingDistance")),
        "year_month": _ym(car.get("firstRegisteredOn")),
        "form_year": _int(car.get("modelYear")),
        "reg_at": _date10(car.get("firstRegisteredOn")),
        "color_ext_raw": color.get("exteriorCodeName"),
        "color_int_raw": color.get("interiorCodeName"),
        "transmission": car.get("mission"),
        "_pii_plate_no": car.get("plateNumber"),
    }
    # ★ 배기량은 ★ 「1,598」처럼 ★ 쉼표가 든 글월이다
    cc = str(car.get("displacement") or "").replace(",", "").strip()
    if cc.isdigit():
        got["displacement_cc"] = int(cc)
    # ★ 값이 없는 칸은 ★ **넣지 않는다** — ★ 「없음」으로 덮지 않는다 (금지 12)
    return {k: v for k, v in got.items() if v is not None}
