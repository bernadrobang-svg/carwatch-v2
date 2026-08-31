# -*- coding: utf-8 -*-
"""리볼트 (revolt.kr) — 전기차 전용 인증중고차 (규격 `docs/REVOLT_API.md` · `S46-200`).

★★★★★ 09-01 마스터 확정 — 「★ **보배를 빼고 여기 것 쓰자 ★ 지금 우선 작업으로**」

★★ 만든 곳이 ★ **PRND** 다 — ★ **헤이딜러와 같은 회사**라 ★ 칸 이름이 거의 같다.
  ★ 규격 — 「★ `parse/revolt/` 를 ★ `parse/heydealer/` 에서 **베껴** 만든다」
  ★ ★ 다만 ★ **같지 않은 자리가 있다** [실측 09-01 · 표본 `dnKx0DQo`] —
      헤이딜러                          리볼트
      `detail_info.…`                  ★ 껍데기가 없다 (바로 `car_info`·`carhistory`)
      `carhistory.owner_changed_count`  ★ **`driving_history.owner_changed_count`**
      `carhistory.has_rent_use_record`  ★ **`driving_history.…`**
      `carhistory.my_car_accident_cost` ★ **`my_car_accident_total_amount`**
      `carhistory.flooded_count`        ★ **없다** — ★ `special_accident_count` 하나로 온다
  ★ ★ ★ 그래서 ★ **그대로 베끼지 않았다** — ★ 칸을 하나씩 눈으로 맞췄다 (금지 6)

★ 전건 전기·수소 (전기 212 · 수소 8) · ★ 전건 무사고 (규격 「전체를 쟀다」)
★ 금지 — ★ `App-Os`·`App-Type`·`App-Version` 헤더 (500) · ★ 몰아쳐 부르기 (500)
"""
from __future__ import annotations

import json
import re

SITE_CODE = "revolt"
WON_PER_MANWON = 10_000
RE_YM = re.compile(r"(\d{4})-(\d{2})")
# ★ 「2년 6개월 / 60,390km 남음」 (규격 3장)
RE_W_Y = re.compile(r"(\d+)\s*년")
RE_W_M = re.compile(r"(\d+)\s*개월")
RE_W_KM = re.compile(r"([\d,]+)\s*km", re.I)
RE_SEIZE = re.compile(r"압류\s*및\s*저당\s*[:：]\s*([^<]{1,12})")
# ★ 보증 이름 — ★ 헤이딜러와 같은 낱말이다 (규격 3장)
W_KEY = {"차체/일반 부품": "warranty_body", "엔진/주요 부품": "warranty_power"}


def _int(v):
    if v is None:
        return None
    got = re.sub(r"[^0-9]", "", str(v))
    return int(got) if got else None


def _won(manwon):
    got = _int(manwon)
    return got * WON_PER_MANWON if got is not None else None


def _ym(text):
    m = RE_YM.match(str(text or ""))
    return f"{m.group(1)}-{m.group(2)}" if m else None


def parse_list_item(one: dict) -> dict | None:
    """목록 한 줄 → `core_listing` 한 줄.  ★ 목록이 이미 많이 준다."""
    if not isinstance(one, dict) or not one.get("hash_id"):
        return None
    out = {
        "site": SITE_CODE, "source_id": str(one["hash_id"]),
        "price_unit": "won",
        "site_model": one.get("model_name") or None,
        "trim_badge": one.get("grade_part_name") or one.get("grade_name"),
        "fuel_raw": one.get("fuel") or None,
        "sales_status": one.get("sale_status") or None,
    }
    for src, key in (("price", "price_current_won"),
                     ("new_car_price", "price_origin_won")):
        got = _won(one.get(src))
        if got is not None:
            out[key] = got
    if _int(one.get("mileage")) is not None:
        out["mileage_km"] = _int(one["mileage"])
    if _int(one.get("year")):
        out["form_year"] = _int(one["year"])
    ym = _ym(one.get("initial_registration_date"))
    if ym:
        out["year_month"] = ym
        out["reg_at"] = str(one["initial_registration_date"])[:10]
    # ★ 인증중고차다 — ★ 사이트의 사실이다 (`merchandise_type: 'certified'`)
    if one.get("merchandise_type") == "certified":
        out["site_home_verify"] = 1
    return out


def parse_detail(body, site: str = SITE_CODE,
                 source_id: str | None = None) -> dict | None:
    """상세 → `core_listing` 한 줄.  ★ 껍데기가 없다 — ★ 바로 `car_info` 다."""
    if isinstance(body, (bytes, str)):
        try:
            body = json.loads(body)
        except ValueError:
            return None
    if not isinstance(body, dict) or not body.get("hash_id"):
        return None
    ci = body.get("car_info") or {}
    out = parse_list_item(dict(body, **{
        k: ci.get(k) for k in ("model_name", "grade_part_name", "grade_name",
                               "year", "initial_registration_date", "mileage")
        if ci.get(k) is not None})) or {}
    out["site"] = site
    out["source_id"] = str(source_id or body.get("hash_id"))
    out["detail_status"] = "ok"
    if ci.get("brand_name"):
        out["site_manufacturer"] = ci["brand_name"]
    # ★★ 차량번호 — ★ 원문을 CORE 에 안 넣는다.  ★ `split_pii` 가 해시한다 (STEP 35)
    if body.get("car_number"):
        out["_pii_plate_no"] = str(body["car_number"]).strip()
    col = ci.get("color_and_trim") or {}
    if col.get("exterior_description"):
        out["color_ext_raw"] = col["exterior_description"]
    if col.get("interior_description"):
        out["color_int_raw"] = col["interior_description"]
    ev = body.get("ev_info") or {}
    if ev.get("wheel_drive"):
        out["drive_type"] = ev["wheel_drive"]
    # ★ 압류·저당 — ★ `etc_info_html` 에 ★ 「압류 및 저당 : 없음」으로 온다
    m = RE_SEIZE.search(str(body.get("etc_info_html") or ""))
    if m:
        none = "없음" in m.group(1)
        out["seizing_cnt"] = 0 if none else 1
        out["pledge_cnt"] = 0 if none else 1
    out.update(warranty_of(body))
    got = options_of(body)
    if got:
        out["options_standard_json"] = json.dumps(
            [x for x in got if x], ensure_ascii=False)
    return out


def options_of(body: dict) -> list:
    """옵션 — ★ 한글 이름으로 온다 (헤이딜러와 같다)."""
    out = []
    for one in ((body.get("car_info") or {}).get("options") or []):
        if isinstance(one, dict) and one.get("name"):
            out.append(one["name"])
        elif isinstance(one, str):
            out.append(one)
    return out


def warranty_of(body: dict) -> dict:
    """`manufacturer_warranty.items` → 보증 칸.

    ★★ 리볼트도 ★ **남은 양**을 준다 (「2년 6개월 / 60,390km 남음」) —
      ★ 축은 ★ 「등록부터 몇 달」을 받아 ★ 스스로 경과분을 뺀다.
      ★ ★ 그래서 ★ 경과분을 ★ **도로 더해** 총량으로 넣는다 (헤이딜러와 같은 자리)
    """
    out: dict = {}
    ci = body.get("car_info") or {}
    elapsed = _months_since(ci.get("initial_registration_date")
                            or body.get("initial_registration_date"))
    mileage = _int(ci.get("mileage") or body.get("mileage"))
    for one in ((body.get("manufacturer_warranty") or {}).get("items") or []):
        if not isinstance(one, dict):
            continue
        key = W_KEY.get(one.get("name"))
        if not key:
            continue                # ★ 고전압 배터리 등은 ★ 다른 축이다
        text = str(one.get("description") or "")
        if "종료" in text or one.get("is_active") is False:
            out[f"{key}_month"] = 0
            out[f"{key}_km"] = 0
            continue
        y, m = RE_W_Y.search(text), RE_W_M.search(text)
        left = (int(y.group(1)) * 12 if y else 0) + (int(m.group(1)) if m else 0)
        if (y or m) and elapsed is not None:
            out[f"{key}_month"] = left + elapsed
        km = RE_W_KM.search(text)
        if km and mileage is not None:
            out[f"{key}_km"] = _int(km.group(1)) + mileage
    return out


def _months_since(text) -> int | None:
    from datetime import datetime, timezone

    m = RE_YM.match(str(text or ""))
    if not m:
        return None
    now = datetime.now(timezone.utc)
    return max(0, (now.year - int(m.group(1))) * 12
               + (now.month - int(m.group(2))))


def record_of(body: dict, site: str = SITE_CODE) -> dict | None:
    """`carhistory` ＋ `driving_history` → `core_record`.

    ★★ 헤이딜러와 ★ **자리가 다르다** — ★ 소유자·용도가 `driving_history` 에 있다.
      ★ ★ 베껴 쓰면 ★ 전건 NULL 이 된다.  ★ 눈으로 맞췄다 (실측 09-01)
    """
    if not isinstance(body, dict):
        return None
    ch = body.get("carhistory") or {}
    dh = body.get("driving_history") or {}
    if not ch and not dh:
        return None
    out = {"listing_id": None, "site": site, "row_status": "ok",
           "collected_at": None, "record_open": 1}
    for src, col in (("my_car_accident_count", "accident_my_cnt"),
                     ("my_car_accident_total_amount", "accident_my_cost"),
                     ("other_car_accident_count", "accident_other_cnt"),
                     ("other_car_accident_total_amount", "accident_other_cost"),
                     ("special_accident_count", "total_loss_cnt")):
        if ch.get(src) is not None:
            out[col] = int(ch[src])
    my, other = out.get("accident_my_cnt"), out.get("accident_other_cnt")
    if my is not None or other is not None:
        out["accident_total_cnt"] = (my or 0) + (other or 0)
    if dh.get("owner_changed_count") is not None:
        out["owner_change_cnt"] = int(dh["owner_changed_count"])
    if dh.get("dashboard_change_count") is not None:
        out["plate_change_cnt"] = int(dh["dashboard_change_count"])
    gov, biz = dh.get("has_public_use_record"), dh.get("has_business_use_record")
    rent = dh.get("has_rent_use_record")
    if gov is not None:
        out["use_gov"] = 1 if gov else 0
    if biz is not None:
        out["use_business"] = 1 if biz else 0
    if rent:
        # ★ 헤이딜러와 같은 자리 — ★ 축을 안 연다 (렌트가 「자가용 22점」을 받지 않게)
        out["use_cd"] = "revolt:has_rent_use_record"
    elif rent is False and gov is not None and biz is not None:
        out["plate_history_hash_json"] = json.dumps(
            dh.get("owner_records") or [], ensure_ascii=False)
    return out


def panels_of(body: dict) -> list | None:
    """`inspection_records.accident_repairs` → 판.

    ★ `f-table` 3a·3b 표를 ★ **헤이딜러 것을 그대로 쓴다** — ★ 같은 회사다 (규격 「필수」).
    ★★ 표에 없는 코드는 ★ **미확인**이다 — ★ 짐작으로 안 옮긴다
    """
    from parse.heydealer.mapping import HD_PART, HD_REPAIR, UNKNOWN_CODES

    if not isinstance(body, dict):
        return None
    rec = body.get("inspection_records")
    if rec is None:
        return None                 # ★ 칸이 없다 — ★ 「이상 없음」으로 안 친다
    got = (rec or {}).get("accident_repairs") if isinstance(rec, dict) else rec
    if got is None:
        return None
    if not isinstance(got, list):
        return None
    out = []
    for one in got:
        if not isinstance(one, dict):
            continue
        rank = HD_PART.get(str(one.get("part") or ""))
        pair = HD_REPAIR.get(str(one.get("repair") or ""))
        if not rank or not pair:
            UNKNOWN_CODES.append((one.get("part"), one.get("repair")))
            continue
        code, title = pair
        out.append({"type": {"code": str(one.get("part")),
                             "title": str(one.get("part"))},
                    "statusTypes": [{"code": code, "title": title}],
                    "attributes": [rank]})
    return out
