# -*- coding: utf-8 -*-
"""리본카 상세 → `core_listing` (명령서 39 · `docs/REBORNCAR_API.md` 1b).

실측     2026-08-24 · 표본 `C26011900046` (320KB)
★ 값이 `<dt>이름</dt><dd>값</dd>` 로 온다 — ★ 이름이 41가지다
★ ★ 모바일 UA 로 받아야 참값이 온다 — ★ 데스크톱은 「용도변경 없음」이 거짓이다 (2a장)
금지     ★ 없는 값을 지어내는 것.  ★ 안 오면 None 이다 (모름)
"""
from __future__ import annotations

import re

WON_PER_MANWON = 10_000
RE_PAIR = re.compile(r"<dt[^>]*>(.{1,20}?)</dt>\s*<dd[^>]*>(.{1,200}?)</dd>", re.S)
RE_TAG = re.compile(r"<[^>]+>")
# ★ 「2018년 10월」 → 201810 (MULTISITE_MAPPING 5a② — YYYYMM)
RE_YM = re.compile(r"(20\d{2})\s*년\s*(\d{1,2})\s*월")
RE_NUM = re.compile(r"([\d,]+)")
# ★ 차명은 <title> 에 있다 — 「지프 지프 랭글러(JL) 2.0 루비콘 4DR | 직영중고차 리본카」
#   ★ 상세에 차종 칸이 따로 없다 (BOBAEDREAM 과 같다)
RE_TITLE = re.compile(r"<title>([^<|]{4,90})", re.I)


def _txt(s: str) -> str:
    return re.sub(r"\s+", " ", RE_TAG.sub(" ", s)).replace("&gt;", "").strip()


def _int(s: str | None) -> int | None:
    got = RE_NUM.search(s or "")
    try:
        return int(got.group(1).replace(",", "")) if got else None
    except ValueError:
        return None


def fields(html: str) -> dict:
    """`<dt>·<dd>` 짝을 이름→값 으로.  ★ 먼저 나온 것이 이긴다."""
    out: dict = {}
    for got in RE_PAIR.finditer(html):
        k, v = got.group(1), got.group(2)
        key, val = _txt(k), _txt(v)
        # ★ `${...}` 는 화면 틀이다 — ★ 값이 아니다
        if not key or not val or "${" in key or "${" in val:
            continue
        out.setdefault(key, val)
    return out


def title_name(html: str) -> str | None:
    """차명.  ★ 사이트가 제조사를 두 번 적기도 한다 — ★ 그대로 둔다."""
    got = RE_TITLE.search(html)
    return _txt(got.group(1)) if got else None


def parse_detail(html: str, site: str, source_id: str) -> dict | None:
    f = fields(html)
    if not f:
        return None
    out: dict = {"site": site, "source_id": str(source_id), "price_unit": "won"}
    name = title_name(html)
    if name:
        out["site_model"] = name

    ym = RE_YM.search(f.get("연식") or "")
    if ym:
        out["year_month"] = f"{ym.group(1)}{int(ym.group(2)):02d}"
        out["form_year"] = int(ym.group(1))

    for key, col in (("주행거리", "mileage_km"), ("배기량", "displacement_cc")):
        got = _int(f.get(key))
        if got is not None:
            out[col] = got
    for key, col in (("차량가격", "price_current_won"),
                     ("신차출고가", "price_origin_won")):
        got = _int(f.get(key))
        if got is not None:
            out[col] = got * WON_PER_MANWON
    for key, col in (("연료", "fuel_raw"), ("색상", "color_ext_raw"),
                     ("변속기", "transmission")):
        if f.get(key):
            out[col] = f[key]
    # ★ 차량번호 — ★ `split_pii` 가 해시로 바꾼다.  ★ 원문을 안 남긴다
    if f.get("차량번호"):
        out["_pii_plate_no"] = f["차량번호"]
    return out


def seats(html: str) -> int | None:
    """승차인원 — ★ 「5인승」.  ★ 낼 곳은 규격이 아직 안 정했다 (UI_REVIEW 10)."""
    return _int(fields(html).get("승차인원"))


def marks(html: str) -> dict:
    """사이트가 사실로 주는 것 — ★ 사고·침수·용도변경·패널·프레임."""
    f = fields(html)
    return {k: f[k] for k in ("사고여부", "침수여부", "용도변경",
                              "외부 패널", "프레임") if f.get(k)}
