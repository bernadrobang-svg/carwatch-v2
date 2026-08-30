# -*- coding: utf-8 -*-
"""볼보 셀렉트 상세 → `core_listing` 칸 (규격 `VOLVO_SELEKT_API.md` 2장).

★★ 마스터 지시 08-26 ② — 「상세는 현대인증부터 · ★ 그다음 볼보」.
★★★ ★ HTML 자리는 ★ **규격에 없었다.**  ★ 그래서 ★ 표본을 받아 ★ 눈으로 보고 적었다
  (실측 08-26 · `xc60/b5-awd-ultra-bright-ejbbg46` · 200 · 70,924B).
  ★ 지어내지 않았다 (금지 6).

★ 칸 표는 ★ 라벨/값 두 칸짜리 표다 — ★ 여덟 칸이 나온다
    <td><div class="small"> 모델 년도 </div></td>
    <td><div class="small">2026</div></td>
★ 가격만 표 밖이다 — `<div class="… h3">64,000,000원</div>`

★★★ ★ 안 뽑는 것 (규격 0b·3장이 못 박았다)
  ✘ `state.accident` 사고 · `warranty.*` 보증 —
     ★ 딜러가 ★ 소개글에 ★ 손으로 적은 자유 문장이다.  ★ 12건 중 2건에만 있다.
     ★ ★ 「볼보 셀렉트는 인증이니 무사고」로 ★ 만점을 지어 주지 않는다 (금지 12).
     ★ ★ 「없음」이 아니라 ★ 「모름(NULL)」이다 (개정 325).  ★ 검산 `S46-7`
"""
from __future__ import annotations

import json
import re

# ★ 라벨/값 두 칸 표.  ★ 표본에서 재서 적었다 (08-26)
RE_ROW = re.compile(
    r'<div class="small">\s*([^<]{1,20}?)\s*</div>\s*</td>\s*'
    r'<td[^>]*>\s*<div class="small">(.*?)</div>',
    re.S)
# ★ 가격 — 표 밖이다.  ★ 원 단위다 (규격 2장 「×10000 하지 마라」)
RE_PRICE = re.compile(r'>\s*([\d,]{7,})\s*원\s*<')
RE_TAG = re.compile(r"<[^>]+>")


def _txt(value: str) -> str:
    return RE_TAG.sub("", value or "").replace("&nbsp;", " ").strip()


def _int(value: str | None) -> int | None:
    if not value:
        return None
    got = re.sub(r"[^0-9]", "", value)
    return int(got) if got else None


def fields(html: str) -> dict:
    """라벨 → 값.  ★ 화면에 있는 것만 담는다 — ★ 없는 칸을 만들지 않는다."""
    return {k: _txt(v) for k, v in RE_ROW.findall(html or "")}


def parse_detail(html: str, site: str, source_id: str) -> dict | None:
    """상세 한 쪽 → `core_listing` 한 줄.  ★ 못 읽은 칸은 ★ 안 담는다 (NULL 이 맞다)."""
    if not html:
        return None
    f = fields(html)
    if not f:
        return None
    out: dict = {"site": site, "source_id": source_id, "price_unit": "won",
                 "detail_status": "ok"}

    price = RE_PRICE.search(html)
    if price:
        # ★ 원 단위 그대로다 (규격 2장) — ★ 만원으로 바꾸지 않는다
        out["price_current_won"] = _int(price.group(1))

    if f.get("모델 년도"):
        out["form_year"] = _int(f["모델 년도"])
    reg = f.get("등록일") or ""
    got = re.match(r"(\d{4})-(\d{2})", reg)
    if got:
        # ★ 연식은 ★ 등록일로 잰다 — ★ 「모델 년도」와 다르다 (규격 2장 · 개정 534③)
        out["year_month"] = got.group(1) + got.group(2)
    if f.get("마일리지"):
        out["mileage_km"] = _int(f["마일리지"])
    if f.get("색상"):
        out["color_ext_raw"] = f["색상"]
    if f.get("내부 색상"):
        out["color_int_raw"] = f["내부 색상"]
    if f.get("엔진 크기"):
        # ★ 원문이 `1,969 cm<sup>3</sup>` 이라 ★ 태그를 떼면 `1,969 cm3` 가 된다.
        #   ★ 그대로 읽으면 ★ 19,693 이 된다 (실측 08-26).  ★ cm 앞까지만 읽는다
        out["displacement_cc"] = _int(f["엔진 크기"].split("cm")[0])
    if f.get("연료 유형"):
        out["fuel_raw"] = f["연료 유형"]
    if f.get("트랜스미션"):
        out["transmission"] = f["트랜스미션"]

    # ★ 사이트 검증 — ★ 볼보 공식딜러 인증중고차라는 ★ 사이트의 사실이다.
    #   ★ 배점은 `f-table` 5장이 정한다 — ★ 여기서 점수를 매기지 않는다
    out["site_home_verify"] = 1
    return out


def photos(html: str, source_id: str) -> list:
    """매물 사진.  ★ 이 매물 것만 담는다 — ★ 배너·모델 홍보 그림은 뺀다."""
    if not html:
        return []
    # ★ 상대경로다 — `/picserver1/userdata/…/xxl_kfz88348_1.jpg` (실측 08-26 · 88개)
    got = re.findall(r'(?:src|data-src)="(/picserver\d*/[^"]+?\.(?:jpg|jpeg|png|webp))"',
                     html, re.I)
    seen, out = set(), []
    for one in got:
        if one in seen:
            continue
        seen.add(one)
        out.append(one)
    return out


def photos_json(html: str, source_id: str) -> str | None:
    got = photos(html, source_id)
    return json.dumps(got, ensure_ascii=False) if got else None


# ★★★★★ 08-31 (명령서 r1007 · 1-6 · 로드맵 차례 1) — ★ 딜러 글에서 ★ **사고만** 읽는다.
#   ★ 실측 08-31 — ★ 딜러 소개글에 ★ **라벨 꼴**로 온다 —
#       「- 사고이력: 무사고 / 침수 및 용도이력 없는 신차 컨디션」
#   ★★ **라벨이 있을 때만 읽는다.**  ★ 낱말을 글 속에서 주워 담지 않는다 —
#     ★ ★ 보배 「판매완료 573」이 ★ 딜러 실적이었던 것과 ★ 같은 함정이다 (0c)
#   ★★★ ★ **부위·판금·교환은 안 읽는다** — ★ `f-table` **3d** 가
#     ★ ★ 「볼보는 아직 안 쟀다 · ★ 내가 재서 3e·3f 로 붙인다 ·
#        ★ 개발측은 표가 있는 것만 연다」라 한다 (규칙 2)
#   ★ 규격 0b·3장이 못 박은 ★ 「딜러 자유 문장으로 만점을 지어 주지 마라」는
#     ★ ★ 여전히 지킨다 — ★ **라벨이 없으면 NULL** 이다 (「무사고」가 아니다)
RE_ACC_LABEL = re.compile(r"사고\s*이력\s*[:：]\s*([^/·\n<]{1,20})")
RE_FLOOD_LABEL = re.compile(r"침수\s*(?:및\s*용도이력\s*)?(없는|없음|있음)")
ACC_NONE = ("무사고",)


def record_of(html: str, site: str) -> dict | None:
    """딜러 글 → `core_record`.  ★ 라벨이 없으면 ★ `None` 이다."""
    t = re.sub(r"\s+", " ", RE_TAG.sub(" ", html or ""))
    acc = RE_ACC_LABEL.search(t)
    if not acc:
        return None
    word = acc.group(1).strip()
    out = {"listing_id": None, "site": site, "row_status": "ok",
           "collected_at": None, "record_open": 1}
    if word in ACC_NONE:
        # ★ 「무사고」라 적혀 있다 — ★ 사이트가 그렇게 말한 사실이다
        out["accident_my_cnt"] = 0
        out["accident_other_cnt"] = 0
        out["accident_total_cnt"] = 0
    else:
        # ★ 「무사고」가 아닌 낱말 — ★ 몇 건인지는 ★ 모른다.  ★ 수를 지어내지 않는다
        out["use_cd"] = f"volvo:사고이력={word}"
        return out
    flood = RE_FLOOD_LABEL.search(t)
    if flood and flood.group(1).startswith("없"):
        # ★ 「침수 및 용도이력 없는」 — ★ 둘을 함께 말한 문장이다
        out["flood_total_cnt"] = 0
        out["use_gov"] = 0
        out["use_business"] = 0
        out["plate_history_hash_json"] = "[]"
    return out
