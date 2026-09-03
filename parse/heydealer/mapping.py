# -*- coding: utf-8 -*-
"""헤이딜러 원문 → `core_listing` (명령서 37-3 ② · `docs/HEYDEALER_API.md`).

실측     2026-08-24 · 표본 — 볼보 XC60 2세대 `andYAaQb`
★ 목록(compact)은 칸 14개다 — ★ **연료가 없다.**  ★ 값은 상세에 있다
★ 상세는 칸 33개 · `detail_info` 51개다
금지     ★ 없는 값을 지어내는 것.  ★ 안 오면 None 이다 (모름)
"""
from __future__ import annotations

import json
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


# ★★★★★ 08-30 (명령서 r974 · 0j 4) — ★ Ⓐ 「이미 오는 것을 읽는다」 183점.
#   ★ 상세 원문에 ★ 다 와 있는데 ★ 읽는 코드가 없어 ★ 축이 비어 있었다
#   ★ 규격 `HEYDEALER_API.md` 3-2 · 3-4 가 칸을 하나하나 못 박아 두었다

RE_LEFT_KM = re.compile(r"([\d,]+)\s*km", re.I)
RE_LEFT_Y = re.compile(r"(\d+)\s*년")
RE_LEFT_M = re.compile(r"(\d+)\s*개월")
W_KEY = {"차체/일반 부품": "warranty_body", "엔진/주요 부품": "warranty_power"}


def record_of(body: dict, site: str) -> dict | None:
    """`carhistory` → `core_record` 한 줄 (규격 3-2).

    ★★ 없는 칸은 ★ **안 담는다** — ★ `None` 은 「모른다」다.  ★ 0 이 아니다
    ★★★ ★ 렌트 이력(`has_rent_use_record`)이 ★ 참이면 ★ 용도 축을 ★ **안 연다**.
      ★ 까닭 — ★ `history.use` 축이 렌트를 가리는 길은 넷이고
        (`advertisement_type`·`usage_change_types`·`record_use`·`plate_use_char`)
        ★ ★ 헤이딜러의 불리언은 ★ 그 넷 어디에도 안 맞는다.
      ★ ★ 열어 두면 ★ 렌트 차가 ★ 「자가용 30점」을 ★ 받는다 — ★ 지어 주는 꼴이다.
      ★ ★ 그래서 ★ 렌트면 ★ 「모른다」로 둔다 (0점＋미확인).  ★ 마스터께 올린다
    """
    if not isinstance(body, dict):
        return None
    ch = (body.get("detail_info") or {}).get("carhistory") or {}
    if not ch:
        return None
    out: dict = {"site": site, "row_status": "ok", "record_open": 1}
    for src, col in (("my_car_accident_count", "accident_my_cnt"),
                     ("my_car_accident_cost", "accident_my_cost"),
                     ("other_car_accident_count", "accident_other_cnt"),
                     ("owner_changed_count", "owner_change_cnt"),
                     ("car_number_changed_count", "plate_change_cnt"),
                     ("flooded_count", "flood_total_cnt"),
                     ("total_loss_count", "total_loss_cnt"),
                     ("stolen_count", "robber_cnt")):
        if ch.get(src) is not None:
            out[col] = int(ch[src])
    my, other = out.get("accident_my_cnt"), out.get("accident_other_cnt")
    if my is not None or other is not None:
        out["accident_total_cnt"] = (my or 0) + (other or 0)
    for src, col in (("my_car_accident_list", "accidents_json"),
                     ("owner_changed_list", "owner_change_dates_json")):
        if isinstance(ch.get(src), list):
            out[col] = json.dumps(ch[src], ensure_ascii=False)

    rent = ch.get("has_rent_use_record")
    gov = ch.get("has_public_use_record")
    biz = ch.get("has_business_use_record")
    if gov is not None:
        out["use_gov"] = 1 if gov else 0
    if biz is not None:
        out["use_business"] = 1 if biz else 0
    if rent:
        # ★ 렌트다.  ★ 그 사실만 남기고 ★ 용도 축은 안 연다 (위 까닭)
        out["use_cd"] = "heydealer:has_rent_use_record"
    elif rent is False and gov is not None and biz is not None:
        # ★ 셋을 다 봤다 — ★ 그때만 ★ 「봤다」고 말할 수 있다 (`history.use` 관문).
        #   ★ 번호판 변경 이력이 ★ 관문의 셋째다 — ★ 원문 그대로 담는다
        out["plate_history_hash_json"] = json.dumps(
            ch.get("car_information_changed_list") or [], ensure_ascii=False)
    return out


def warranty_of(body: dict) -> dict:
    """`warranty_info.manufacturer_warranties[]` → 보증 칸 (규격 3-4).

    ★★★ 헤이딜러는 ★ **남은 양**을 준다 (「49,991km / 10개월 남음」).
      ★ 그런데 ★ `warranty.general`·`.power` 축은 ★ 「등록부터 몇 달」을 받아
        ★ ★ 스스로 ★ 경과분을 뺀다 (`analyze/axis/warranty.py:_remaining_months`).
      ★ ★ 그래서 ★ 남은 값을 그대로 넣으면 ★ **두 번 빠진다.**
      ★ ★ 여기서 ★ 경과분을 ★ 도로 더해 ★ **총량**으로 바꿔 넣는다 — ★ 셈이지 짐작이 아니다
    ★ 「보증기간 종료」는 ★ 0 이다 — ★ 「확인한 값」이지 「모름」이 아니다
    """
    out: dict = {}
    d = body.get("detail_info") or {}
    elapsed = _months_since(d.get("initial_registration_date"))
    mileage = _int(d.get("mileage"))
    for one in (body.get("warranty_info") or {}).get(
            "manufacturer_warranties") or []:
        key = W_KEY.get(one.get("name"))
        if not key:
            continue                    # ★ 고전압 배터리·전기차 전용은 ★ 다른 축이다
        text = str(one.get("description") or "")
        if not one.get("is_active"):
            out[f"{key}_month"] = 0
            out[f"{key}_km"] = 0
            continue
        y, m = RE_LEFT_Y.search(text), RE_LEFT_M.search(text)
        left = (int(y.group(1)) * 12 if y else 0) + (int(m.group(1)) if m else 0)
        if (y or m) and elapsed is not None:
            out[f"{key}_month"] = left + elapsed
        km = RE_LEFT_KM.search(text)
        if km and mileage is not None:
            out[f"{key}_km"] = _int(km.group(1)) + mileage
    return out


def _months_since(text: str | None) -> int | None:
    """최초등록부터 오늘까지 몇 달.  ★ 못 읽으면 ★ None 이다."""
    from datetime import datetime, timezone

    got = re.match(r"(\d{4})-(\d{2})", str(text or ""))
    if not got:
        return None
    now = datetime.now(timezone.utc)
    return max(0, (now.year - int(got.group(1))) * 12
               + (now.month - int(got.group(2))))


def part_enums(body: dict) -> list:
    """★ `accident_repairs[]` 의 `part` — ★ **원문 그대로** 낸다.

    ★★ 규격 3a ② — 「`dict_enum(site='heydealer', axis='part')` 에 넣는다.
      ★ ★ **우리말로 옮기지 마라 — 원문이 정본**」
    ★★★ ★ 골격(`state.frame` 43) · 외판(`state.outer` 28) 은 ★ **아직 못 매긴다** —
      ★ 축은 ★ 판마다 ★ `attributes` 의 ★ 등급(`RANK_A`·`RANK_ONE`…)을 보는데
        ★ ★ 규격이 ★ 헤이딜러 `part` → 등급 표를 ★ 아직 안 줬다.
      ★ ★ 내가 지어 옮기면 ★ 골격을 외판으로 (또는 거꾸로) 매긴다 — ★ 안 한다 (규칙 2)
    """
    out = []
    for one in (body.get("detail_info") or {}).get("accident_repairs") or []:
        if isinstance(one, dict) and one.get("part"):
            out.append({"part": one["part"], "repair": one.get("repair")})
    return out


# ★★★★★ 08-30 (명령서 r990 · 1-3) — ★ 골격 43 · 외판 28 을 연다.
#   ★ 지난 회차에 ★ 「`part` → 등급 표가 규격에 없다」고 올렸더니
#   ★ ★ 마스터께서 ★ `f-table` **3a · 3b** 에 ★ 표를 내려 주셨다.
#   ★★ 아래는 ★ **그 표를 그대로 옮긴 것이다** — ★ 내가 지어낸 것이 없다.
#     ★ ★ 표에 없는 코드는 ★ **미확인 0점**이다 (3a·3b 의 마지막 줄)

# ★ 3a. 부위 코드 — ★ 헤이딜러
#   ★★ 헤이딜러는 ★ 「골격이냐 외판이냐」까지만 준다 — ★ A·B·C 나 1·2 를 안 준다.
#   ★ ★ 축은 ★ 등급을 ★ **어느 무리에 드는가**로만 본다
#     (`analyze/axis/state.py:_rank_worst` — ★ `attributes` 가 그 목록에 드는지).
#   ★ ★ 그러므로 ★ 무리의 첫 값을 쓰는 것이 ★ 점수에 아무 영향이 없다.
#   ★ ★ 곧 ★ `RANK_A` 는 ★ 「A랭크다」가 아니라 ★ 「골격 무리다」라는 뜻이다
HD_BONE, HD_OUTER = "RANK_A", "RANK_ONE"
HD_PART = {
    # ★★★★★ 09-03 (개정 1105 · `S46-258`) — ★ **후드가 빠져 있었다.**
    #   ★ 정부 서식 외판 여덟 중 ★ 열 칸을 적어 두고 ★ **후드 하나만** 없었다.
    #   ★ ★ 사전(`fixed_enums.json`)에도 없고 ★ 코드에도 없어 ★ **두 번 샜다**.
    #   ★★ 이것은 ★ 판정 축이다 — ★ `state.outer` **28점** ·
    #     ★ ★ 헤이딜러 **275건**이 ★ 외판 판정을 못 받고 있었다.
    #   ★ 후드는 ★ **외판**이다 (골격이 아니다) — ★ 정부 서식 외판 8부위에 든다
    "hood": HD_OUTER,
    "radiator_support": HD_BONE,          # ★ 라디에이터서포트는 뼈대다 (3a)
    "door_front_driver": HD_OUTER,
    "door_front_passenger": HD_OUTER,
    "door_rear_driver": HD_OUTER,
    "door_rear_passenger": HD_OUTER,
    "fender_front_driver": HD_OUTER,
    "fender_front_passenger": HD_OUTER,
    "fender_rear_driver": HD_OUTER,
    "fender_rear_passenger": HD_OUTER,
    "trunk_lid": HD_OUTER,                # ★ 트렁크리드 — 트렁크플로어(골격)와 다르다
}
# ★ 3b. 수리 코드 — ★ 축이 보는 낱말로 옮긴다
#   `analyze/axis/state.py` — SWAP_TITLES=("교환(교체)","용접,절단") · SHEET_TITLES=("판금/용접",)
HD_REPAIR = {
    "weld": ("W", "용접,절단"),            # ★ 3b — swap · 골격 0 · 외판 0
    "exchange": ("X", "교환(교체)"),        # ★ 3b — swap · 골격 0 · 외판 0
    "sheet_metal": ("S", "판금/용접"),      # ★ 3b — sheet1 26 · paint12 17
}


def panels_of(body: dict) -> list | None:
    """`accident_repairs[]` → 엔카 `inspection_panel_json` 과 같은 꼴 (3a·3b).

    돌려줌  판 목록.  ★ 빈 배열이면 ★ **「무사고로 확인했다」**다 (3a 실측 — 완전무사고
           11건이 빈 배열이었다).  ★ 칸 자체가 없으면 ★ `None` (「못 봤다」)
    ★★ 표에 없는 부위·수리 코드는 ★ **안 낸다** — ★ 미확인 0점이 맞다 (금지 6)
    """
    if not isinstance(body, dict):
        return None
    d = body.get("detail_info") or {}
    if "accident_repairs" not in d and "accident_repairs" not in body:
        return None                     # ★ 칸이 없다 — ★ 「이상 없음」으로 치지 않는다
    got = d.get("accident_repairs")
    if got is None:
        got = body.get("accident_repairs")
    if not isinstance(got, list):
        return None
    out, unknown = [], []
    for one in got:
        if not isinstance(one, dict):
            continue
        rank = HD_PART.get(str(one.get("part") or ""))
        pair = HD_REPAIR.get(str(one.get("repair") or ""))
        if not rank or not pair:
            unknown.append((one.get("part"), one.get("repair")))
            continue                    # ★ 표에 없다 — ★ 미확인.  ★ 짐작으로 안 옮긴다
        code, title = pair
        out.append({"type": {"code": str(one.get("part")),
                             "title": str(one.get("part"))},
                    "statusTypes": [{"code": code, "title": title}],
                    "attributes": [rank]})
    if unknown:
        # ★ 새 코드가 나오면 ★ **미확인으로 두고 마스터께 올린다** (3a 의 「필수」)
        UNKNOWN_CODES.extend(unknown)
    return out


# ★ 이번 바퀴에 본 ★ 「표에 없는 코드」.  ★ 부르는 쪽이 읽어 보고한다
UNKNOWN_CODES: list = []
