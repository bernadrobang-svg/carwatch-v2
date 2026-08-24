# -*- coding: utf-8 -*-
"""헤이딜러 원문 → `core_listing` (명령서 37-3 ② · `docs/HEYDEALER_API.md`).

실측     2026-08-24 · 표본 — 볼보 XC60 2세대 `andYAaQb`
★ 목록(compact)은 칸 14개다 — ★ **연료가 없다.**  ★ 값은 상세에 있다
★ 상세는 칸 33개 · `detail_info` 51개다
금지     ★ 없는 값을 지어내는 것.  ★ 안 오면 None 이다 (모름)
"""
from __future__ import annotations

import re

# ★ 값이 만원 단위로 온다 (price 2860 = 2,860만원).  ★ 원으로 바꾼다
WON_PER_MANWON = 10_000
# ★ 「9.1km/ℓ」 에서 수만 뽑는다.  ★ 단위 글자는 사이트마다 다르다
RE_KMPL = re.compile(r"([\d.]+)\s*km")
# ★ 「무사고」·「1인 소유」 처럼 ★ tags 가 사실을 준다
MARK_NO_ACCIDENT = "무사고"


def _int(x) -> int | None:
    try:
        return int(str(x).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _won(manwon) -> int | None:
    n = _int(manwon)
    return n * WON_PER_MANWON if n is not None else None


def _ym(text: str | None) -> str | None:
    """`2023-10-30 00:00:00` → `202310` (MULTISITE_MAPPING 5a② — YYYYMM)."""
    if not text:
        return None
    got = re.match(r"(\d{4})-(\d{2})", str(text))
    return f"{got.group(1)}{got.group(2)}" if got else None


def _model_group(detail: dict) -> str | None:
    """차종 이름.  ★ `model_group_name` 이 있으면 그것이 정본이다.

    ★★ 실측 08-24 — ★ **상세에는 `model_group_name` · `model_name` 이 둘 다 None** 이다.
      ★ ★ `model_part_name`(「볼보 XC60 2세대」) 만 온다 — ★ 앞의 제조사와 ★ 세대를 뗀다
    ★ 목록에는 `model_name`(「XC60 2세대」)이 온다 — ★ 그쪽이 먼저다
    """
    got = (detail.get("model_group_name") or detail.get("model_name")
           or detail.get("model_part_name"))
    if not got:
        return None
    got = str(got)
    brand = detail.get("brand_name")
    if brand and got.startswith(str(brand)):
        got = got[len(str(brand)):]
    return re.sub(r"\s*\d+세대.*$", "", got).strip() or None


def parse_list_item(item: dict, site: str) -> dict | None:
    """목록 한 건 → 최소 줄.  ★ 연료는 여기 없다 — 상세에서 채운다."""
    if not isinstance(item, dict) or not item.get("hash_id"):
        return None
    d = item.get("detail_info") or {}
    out: dict = {
        "site": site,
        "source_id": str(item["hash_id"]),
        "price_unit": "won",
        "price_current_won": _won(item.get("price")),
        "site_model": d.get("model_part_name") or d.get("model_name"),
        "site_model_group": _model_group(d),
        "trim_badge": d.get("grade_part_name") or d.get("grade_name"),
        "trim_grade_name": d.get("grade_name"),
        "mileage_km": _int(d.get("mileage")),
        "form_year": _int(d.get("year")),
        "year_month": _ym(d.get("initial_registration_date")),
        "color_ext_raw": d.get("exterior_description"),
        "color_int_raw": d.get("interior_description"),
        # ★ 신차가 — ★ 판매자가 적은 것이 아니라 ★ 사이트가 준다
        "price_origin_won": _won(d.get("factory_price")),
        "sales_status": item.get("sale_status"),
    }
    # ★ 전 가격이 있으면 ★ 값이 내린 것이다 — ★ 원문이 그대로 준다 (명령서 37-2)
    if item.get("previous_price") is not None:
        out["last_price_won"] = _won(item.get("previous_price"))
    return {k: v for k, v in out.items() if v is not None}


def parse_detail(body: dict, site: str, source_id: str) -> dict | None:
    """상세 한 건 → `core_listing` 줄.

    ★★ 여기서만 오는 것 — ★ `car_number`(차량번호) · `fuel_display`(연료)
      ★ `fuel_efficiency`(복합연비) · `displacement`(배기량) · `warranty_info`
    """
    if not isinstance(body, dict) or not body.get("hash_id"):
        return None
    d = body.get("detail_info") or {}
    out = parse_list_item(dict(body, detail_info=d), site) or {}
    out.update({
        "site": site,
        "source_id": str(source_id),
        # ★ 차량번호 — ★ `split_pii` 가 해시로 바꾼다.  ★ 원문을 안 남긴다
        "_pii_plate_no": body.get("car_number"),
        "fuel_raw": d.get("fuel_display"),
        "displacement_cc": _int(d.get("displacement")),
        "transmission": d.get("transmission_display") or d.get("transmission"),
        "sales_status": body.get("sale_status"),
    })
    # ★★ 제원 (마스터 확정 08-24) — ★ 헤이딜러는 ★ 복합연비를 준다.
    #   ★ 승차정원은 ★ 안 준다 — ★ NULL 로 둔다 (0 이 아니다)
    kmpl = fuel_efficiency_kmpl(body)
    if kmpl is not None:
        out["spec_fuel_economy_kmpl"] = kmpl
    return {k: v for k, v in out.items() if v is not None}


def fuel_efficiency_kmpl(body: dict) -> float | None:
    """복합연비 — ★ 「9.1km/ℓ」 에서 수만 (UI_REVIEW 10 · `spec_fuel_economy_kmpl`)."""
    got = RE_KMPL.search(str((body.get("detail_info") or {})
                             .get("fuel_efficiency") or ""))
    return float(got.group(1)) if got else None


def options_of(body: dict) -> list:
    """옵션 — ★ 한글 이름 ＋ 장착 여부 (명령서 37-2).

    ★★ `choice='absent'`(없다) 와 ★ `availability='unavailable'`(그 트림에
      아예 없는 옵션) 을 ★ **섞지 않는다** (명령서 37-3 필수)
    """
    out = []
    for one in (body.get("detail_info") or {}).get("options") or []:
        if not isinstance(one, dict) or not one.get("name"):
            continue
        avail = one.get("availability")
        if avail == "unavailable":
            continue                    # ★ 그 트림에 없는 것 — 「미장착」이 아니다
        # ★ default 는 기본 장착이다.  ★ choice 가 있으면 그것이 답이다
        loaded = (one.get("choice") == "loaded") or (avail == "default")
        out.append({"name": one["name"], "loaded": bool(loaded)})
    return out
