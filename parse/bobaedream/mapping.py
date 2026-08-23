# -*- coding: utf-8 -*-
"""보배드림 상세 → `core_listing` (`docs/BOBAEDREAM_API.md` 2·3·1a장).

지시서   `docs/BOBAEDREAM_API.md` · `docs/MULTISITE_MAPPING.md`
근거     ★ 상세가 ★ `<span class="title1">라벨</span><span class="text">값</span>` 꼴이다
값규칙   ★★ 「무사고」 문구는 ★ 판매자가 쓴 글이다 (20건 중 4건) — ★ 축에 쓰지 않는다
        ★★ 「실차확인」은 ★ 값을 읽는다 — ★ 쪽 안의 안내 문구를 찾으면 ★ 전건이 걸린다
           ★ 「확인사항」 팝업에 ★ 「실차확인은 … 직원이 직접 촬영 한 차량입니다」가
             ★ 매물마다 늘 있다 (실측 08-24).  ★ 그것은 ★ 그 매물 이야기가 아니다
        ★ 보험이력 「미공개」는 ★ NULL 이다 — ★ 「사고 없음(0)」이 ★ 아니다
        ★ 성능점검이 ★ 이미지다 — ★ 골격·외판·누유는 ★ NULL 이다.  ★ 0 이 아니다
금지     ★ 제목·본문의 「무사고」를 ★ `state.accident` 에 쓰는 것 (규격 3장 ①)
"""
from __future__ import annotations

import re

WON_PER_MANWON = 10_000

# ★★ 라벨은 ★ `[^<]` 로 잡는다 — ★ `.*?` 로 두면 ★ 「확인사항」 팝업의 ★ 겹친 <span> 을
#   ★ 가로질러 매치돼 ★ 라벨이 통째로 길어지고 ★ 차대번호가 버려졌다 (실측 08-24)
RE_PAIR = re.compile(
    r'<span class="title1">\s*([^<]{1,12}?)\s*</span>\s*'
    r'<span class="text">\s*(.*?)\s*</span>', re.S)
RE_PAIR2 = re.compile(
    r'<span class="title">\s*([^<]{1,12}?)\s*</span>\s*'
    r'<span class="text">\s*(.*?)\s*</span>', re.S)
RE_PRICE = re.compile(
    r'<strong class="price">\s*([\d,]+)\s*</strong>\s*'
    r'<span class="unit">\s*만원')
# ★ 보험이력 건수 — ★ 「미공개」면 이 꼴이 아예 없다
RE_INSURANCE = re.compile(
    r'<span class="title">\s*보험이력\s*</span>\s*'
    r'<span class="count">\s*(\d+)\s*</span>')
RE_REPAIR = re.compile(
    r'<span class="title">\s*수리이력\s*</span>\s*'
    r'<span class="count">\s*(\d+)\s*</span>')
RE_TAG = re.compile(r"<[^>]+>")
# ★ 번호판 — ★ 라벨로 안 온다.  ★ 보험이력 링크의 `car_number=` 에 있다 (실측 08-24).
#   ★ 이것이 ★ 사이트 간 짝짓기 열쇠다 (DEDUP_CROSS_SITE 1장)
RE_PLATE = re.compile(r"car_number=([0-9]{2,3}[가-힣][0-9]{4})")
# ★ 목록 한 줄 — 매물번호와 차명
RE_ITEM = re.compile(
    r'href="/mycar/mview/(\d+)".*?<span class="title">\s*(.*?)\s*</span>', re.S)
# 「24/02/13(23년형)」 · 「25/01/20」
RE_YMD = re.compile(r"(\d{2})/(\d{2})/(\d{2})(?:\s*\((\d{2})년형\))?")
RE_WARRANTY = re.compile(r"(\d+)\s*개월\s*/\s*([\d.]+)\s*만\s*km")

MARK_VERIFIED = "보배드림 직접촬영"   # ★ 이것만 사이트 검증이다 (9/25 = 36%)
LEASE_MARK = "월리스료"


def _txt(value: str) -> str:
    return RE_TAG.sub("", value or "").strip()


def _int(value) -> int | None:
    if value is None:
        return None
    got = "".join(ch for ch in str(value) if ch.isdigit())
    return int(got) if got else None


def list_items(html: str) -> list:
    """목록 → [(매물번호, 차명)].  ★ 나온 차례대로 · 고유하게."""
    out, seen = [], set()
    for no, name in RE_ITEM.findall(html or ""):
        if no in seen:
            continue
        seen.add(no)
        out.append((no, _txt(name)))
    return out


def fields(html: str) -> dict:
    """`title1`/`text` 짝 → dict.  ★ 라벨이 긴 것은 버린다 (팝업 본문이다)."""
    out = {}
    for k, v in RE_PAIR.findall(html or ""):
        key = _txt(k)
        if key and len(key) <= 12:
            out[key] = _txt(v)
    for k, v in RE_PAIR2.findall(html or ""):
        key = _txt(k)
        if key and len(key) <= 12 and key not in out:
            out[key] = _txt(v)
    return out


def _warranty(said: str | None, elapsed: int | None) -> tuple:
    """보증기간 → (남은 개월, 상한 km).  ★ 꼴이 셋이다 (규격 3a ③).

    「36개월/10만km」 ★ 전체 기간이다 — ★ 연식과 빼서 잔여를 낸다
    「만료」  → ★ 0 (확인한 값)
    「불가」  → ★ None — ★ 보증을 못 받는 차다.  ★ 0 과 다르다
    """
    if not said:
        return None, None
    if "만료" in said:
        return 0, None
    if "불가" in said:
        return None, None
    got = RE_WARRANTY.search(said)
    if not got:
        return None, None
    total = int(got.group(1))
    km = int(float(got.group(2)) * 10_000)
    if elapsed is None:
        return None, km
    return max(0, total - elapsed), km


def parse_detail(html: str, site: str, source_id: str,
                 elapsed_months=None) -> dict | None:
    """상세 한 쪽 → `core_listing` 한 줄."""
    if not html:
        return None
    f = fields(html)
    if not f:
        return None
    out: dict = {"site": site, "source_id": str(source_id),
                 "price_unit": "won"}

    got = RE_PRICE.search(html)
    if got:
        out["price_current_won"] = _int(got.group(1)) * WON_PER_MANWON

    ymd = RE_YMD.search(f.get("연식") or "")
    if ymd:
        out["year_month"] = f"20{ymd.group(1)}{ymd.group(2)}"
        out["form_year"] = 2000 + int(ymd.group(4) or ymd.group(1))

    for key, col in (("주행거리", "mileage_km"), ("배기량", "displacement_cc"),
                     ("승차정원", None)):
        if col and f.get(key):
            out[col] = _int(f[key])
    for key, col in (("연료", "fuel_raw"), ("변속기", "transmission"),
                     ("색상", "color_ext_raw")):
        if f.get(key):
            # ★ 「자동 Array단」은 ★ 사이트가 낸 깨진 값이다 —
            #   ★ 그대로 저장하고 ★ 정규화에서 거른다 (MULTISITE_MAPPING 1a)
            out[col] = f[key]
    if f.get("차대번호"):
        out["vin"] = f["차대번호"]
    # ★★ 번호판은 ★ PII 다 — ★ `split_pii` 가 해시한다.  ★ 원문 이름으로 넘긴다
    plate = RE_PLATE.search(html)
    if plate:
        out["_pii_plate_no"] = plate.group(1)

    # ★ 보증 — ★ 전체 기간을 준다.  ★ 잔여가 아니다
    month, km = _warranty(f.get("보증기간"), elapsed_months)
    if month is not None:
        out["warranty_body_month"] = month
    if km is not None:
        out["warranty_body_km"] = km

    # ★★ 사이트 검증 — ★ 「보배드림 직접촬영」인 매물에만 준다 (9/25).
    #   ★ 「직원이 직접 촬영 한 차량입니다」는 ★ 팝업 안내다.  ★ 값에서 읽는다
    out["site_home_verify"] = 1 if f.get("실차확인") == MARK_VERIFIED else 0

    # ★ 보험이력 — ★ 「미공개」면 ★ NULL 이다.  ★ 0 이 아니다 (개정 289·434)
    ins = RE_INSURANCE.search(html)
    if ins:
        out["_insurance_cnt"] = int(ins.group(1))
    rep = RE_REPAIR.search(html)
    if rep:
        out["_repair_cnt"] = int(rep.group(1))

    # ★ 리스는 ★ 「제외」다 (명령서 0).  ★ 월리스료를 값으로 쓰지 않는다
    if LEASE_MARK in html:
        out["sell_type"] = "리스"
        out.pop("price_current_won", None)
    return out
