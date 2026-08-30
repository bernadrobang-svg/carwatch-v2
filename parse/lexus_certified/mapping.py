# -*- coding: utf-8 -*-
"""렉서스 인증중고 목록·상세 → `core_listing` 칸 (규격 `LEXUS_CERTIFIED_API.md` 2장).

★★★★★ 08-30 (명령서 r974 · 0j 1) — ★ `parse/` 열 곳 가운데 ★ **여기만 없었다.**
  ★ ★ 그래서 ★ 목록이 주는 칸조차 축에 안 들어갔다 — ★ 연식 80점이 통째로 비었다
  ★ ★ 실측 08-30 — ★ `year_month` 가 ★ **35건 전건 NULL** (다른 아홉 곳은 다 찬다)

★★★ ★ 연식은 ★ `year` 가 **아니다** — ★ `year` 는 ★ 모델연도다 (규격 3장 ③).
  ★ 연식은 ★ `car_info.registration_date` 다 — ★ 「2025년 8월」 → `202508`.
  ★ ★ 그러므로 ★ **상세를 열어야** ★ 연식이 채워진다.  ★ 목록만으로는 못 한다

★★ ★ 안 뽑는 것 (규격 3장 ① 이 못 박았다)
  ✘ 골격 · 외판 · 누유 · 수리비 · 압류저당 · 소유자변경 · 용도
     → ★ **NULL 이다.  0 이 아니다** (개정 325 · 금지 12)
  ✘ `accident_history` 는 ★ 22/22 전건 「무사고」다 — ★ 갈리지 않는다.
     → ★ `site_condition_json` 에만 담고 ★ **축에 안 쓴다** (규격 부록)

★ 검산 `S46-178`
"""
from __future__ import annotations

import json
import re

SITE_CODE = "lexus_certified"
WON_PER_MANWON = 10_000

# ★ 「2025년 8월」 · 「2030년 8월까지 (120,000km)」
RE_YM = re.compile(r"(\d{4})\s*년\s*(\d{1,2})\s*월")
RE_KM = re.compile(r"([\d,]+)\s*km", re.I)


def _title(v):
    """★ 사이트가 `{"code":…, "title":…}` 로 주는 칸 — ★ 사람 말만 남긴다."""
    if isinstance(v, dict):
        return v.get("title") or v.get("code")
    return v or None


def _int(v):
    if v is None:
        return None
    got = re.sub(r"[^0-9]", "", str(v))
    return int(got) if got else None


def year_month(text: str | None) -> str | None:
    """「2025년 8월」 → `'202508'`.  ★ 못 읽으면 ★ None 이다 — ★ 지어내지 않는다."""
    m = RE_YM.search(text or "")
    return f"{m.group(1)}{int(m.group(2)):02d}" if m else None


def _months_between(start: str | None, end: str | None) -> int | None:
    """`'202508'` → `'203008'` 사이의 달 수.  ★ 보증 축은 ★ 「등록부터 몇 달」을 받는다."""
    if not start or not end:
        return None
    return ((int(end[:4]) - int(start[:4])) * 12
            + (int(end[4:6]) - int(start[4:6])))


def parse_list_item(one: dict) -> dict | None:
    """목록 한 줄 → `core_listing` 한 줄.

    ★ 목록이 주는 것은 ★ 값·신차가·주행·모델연도·트림·색·지점이다.
    ★ ★ 연식(`year_month`)은 ★ 여기 없다 — ★ 상세가 준다 (규격 3장 ③)
    """
    if not one or not one.get("idx"):
        return None
    out: dict = {
        "site": SITE_CODE, "source_id": str(one["idx"]), "price_unit": "won",
        "site_model": one.get("model_name") or None,
        "trim_badge": one.get("class_name") or None,
        "color_ext_raw": _title(one.get("color")),
        "dealer_shop": _title(one.get("branch")),
    }
    col = one.get("color")
    if isinstance(col, dict) and col.get("value"):
        out["color_ext_hex"] = col["value"]
    for src, key, mul in (("price", "price_current_won", WON_PER_MANWON),
                          ("release_price", "price_origin_won", WON_PER_MANWON),
                          ("mileage", "mileage_km", 1)):
        got = _int(one.get(src))
        if got is not None:
            out[key] = got * mul
    # ★ `year` 는 ★ 모델연도다 — ★ `form_year` 에 넣는다.  ★ 연식이 아니다
    fy = _int(str(one.get("year") or "")[:4])
    if fy:
        out["form_year"] = fy
    return out


def parse_detail(body, site: str = SITE_CODE,
                 source_id: str | None = None) -> dict | None:
    """상세 한 쪽 → `core_listing` 한 줄.  ★ 못 읽은 칸은 ★ 안 담는다 (NULL 이 맞다).

    ★★ 「없는 차」도 ★ 200 을 준다 (규격 08-29 절) — ★ `car_detail` 이 없으면 ★ None.
      ★ ★ 200 으로 가르지 않는다
    """
    if not body:
        return None
    if isinstance(body, bytes):
        body = body.decode("utf-8", "replace")
    try:
        d = json.loads(body) if isinstance(body, str) else body
    except ValueError:
        return None
    cd = (d or {}).get("car_detail") if isinstance(d, dict) else None
    if not isinstance(cd, dict):
        return None                       # ★ 없는 차다.  꼴은 200 이어도 알맹이가 없다

    out = parse_list_item(cd) or {}
    out["site"] = site
    out["source_id"] = str(source_id or cd.get("idx") or "")
    out["detail_status"] = "ok"
    ci = cd.get("car_info") or {}

    # ★★★ 연식 — ★ 이것이 ★ 0j 1 의 80점이다
    ym = year_month(ci.get("registration_date"))
    if ym:
        out["year_month"] = ym
        out["reg_at"] = f"{ym[:4]}-{ym[4:6]}-01"

    for src, key in (("fuel", "fuel_raw"), ("transmission", "transmission"),
                     ("innerColor", "color_int_raw")):
        if ci.get(src):
            out[key] = ci[src]
    # ★ `car_info.color` 는 ★ 사람 말이다 (「소닉 크롬」) — ★ 목록의 「Gray」보다 낫다
    if ci.get("color"):
        out["color_ext_detail"] = ci["color"]
    cc = _int(ci.get("displacement"))
    if cc:
        out["displacement_cc"] = cc

    # ★★ 번호판 — ★ 원문을 CORE 에 넣지 않는다.  ★ `split_pii` 가 해시한다 (STEP 35)
    if ci.get("number_plate"):
        out["_pii_plate_no"] = str(ci["number_plate"]).strip()

    # ★★ 보증 — ★ 「2030년 8월까지 (120,000km)」.  ★ 축은 ★ 「등록부터 몇 달」을 받는다
    war = ci.get("warranty") or ""
    until = year_month(war)
    months = _months_between(ym, until)
    if months is not None and months > 0:
        out["warranty_body_month"] = months
        km = RE_KM.search(war)
        if km:
            out["warranty_body_km"] = _int(km.group(1))

    # ★ 사이트 검증 — ★ 불리언이 ★ 사이트의 사실이다.  ★ 점수는 `f-table` 이 정한다
    if cd.get("isCertified"):
        out["site_home_verify"] = 1
    cond = {k: ci.get(k) for k in ("accident_history", "check_date")
            if ci.get(k)}
    if cd.get("isCheckComplete") is not None:
        cond["isCheckComplete"] = bool(cd["isCheckComplete"])
    if cd.get("isCertified") is not None:
        cond["isCertified"] = bool(cd["isCertified"])
    if cond:
        # ★ 「무사고」는 ★ 여기까지다 — ★ 22/22 전건 같아 ★ 축에 안 쓴다 (규격 부록)
        out["site_condition_json"] = json.dumps(cond, ensure_ascii=False)

    # ★ 옵션 — ★ `spec[]` 은 ★ **이름**이다.  ★ 코드가 아니라 값이 없다.
    #   ★ 그래서 `options_choice_json`(선택 옵션·값 있음) 이 아니라
    #   ★ `options_standard_json`(기본 사양) 에 담는다.  ★ 값을 지어내지 않는다
    names = [x.get("txt") for g in (cd.get("spec") or [])
             for x in (g.get("list") or []) if x.get("txt")]
    if names:
        out["options_standard_json"] = json.dumps(names, ensure_ascii=False)

    got = photos(cd)
    if got:
        out["photo_main"] = got[0]
        out["photo_list_json"] = json.dumps(got, ensure_ascii=False)

    # ★★★ `payment.isLease` 를 ★ `sell_type` 에 ★ **안 넣었다** — ★ 마스터께 여쭙는다.
    #   ★ 규격 부록은 ★ 「`payment.isLease` → `sell_type` · 리스 제외에 태운다」라 한다.
    #   ★ 그런데 ★ 이 칸의 다른 값은 ★ 「일반 13,491 · 렌트 849 · 리스 587」로
    #     ★ ★ **그 차가 렌트·리스 차였나**를 뜻한다 (내력).
    #   ★ ★ 렉서스 `payment` 는 ★ 「현금·할부·리스로 살 수 있나」다 (결제 수단).
    #     ★ 실측 08-30 — idx 6047 은 셋이 다 true 다.  ★ 리스 차라는 뜻이 아니다
    #   ★★ 넣으면 ★ 멀쩡한 차가 ★ 「리스」로 보이고 ★ 거르개에서 빠진다.
    #     ★ ★ 그래서 ★ **안 넣는다** (금지 12 · 규칙 2 — ★ 규격을 내가 안 고친다)
    return out


def photos(cd: dict) -> list:
    """매물 사진.  ★ 이 매물 것만 담는다."""
    got = [cd.get("img_url")] + [x.get("img_url")
                                 for x in (cd.get("add_images") or [])]
    seen, out = set(), []
    for one in got:
        if not one or one in seen:
            continue
        seen.add(one)
        out.append(one)
    return out
