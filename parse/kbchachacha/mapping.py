# -*- coding: utf-8 -*-
"""KB차차차 상세 → `core_listing` (`docs/KBCHACHACHA_API.md` 3장).

지시서   `docs/KBCHACHACHA_API.md` · `docs/MULTISITE_MAPPING.md` 1장
근거     ★ 상세 한 쪽(246~275KB)이 ★ 전부를 준다.  ★ 목록만으로는 껍데기다
        ★ 머리에 ★ `ld+json` 이 있다 — ★ 차명·값이 ★ 파싱 없이 온다.  ★ 그것을 먼저 쓴다
값규칙   ★ 「없음」과 「모름」과 「못 받았다」를 ★ 가른다 (개정 289·434) —
        ★ 「없음」은 0 · ★ 「정보없음」은 None · ★ 봇 차단은 부르는 쪽이 막는다
금지     ★ 참/거짓을 `bool()` 로 가르는 것 (개정 537).  ★ 문자열을 그대로 보지 않는다
        ★ 못 받은 것을 「없음」으로 저장하는 것 (금지 12)
"""
from __future__ import annotations

import json
import re

WON_PER_MANWON = 10_000

RE_LD = re.compile(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
                   re.S)
RE_TAG = re.compile(r"<[^>]+>")
RE_WS = re.compile(r"\s+")

# ★ 「26년01월(26년형)」 → 연식 202601 · 년형 2026
RE_YM = re.compile(r"연식\s*(\d{2})년\s*(\d{2})월\s*\(\s*(\d{2})년형\s*\)")
RE_KM = re.compile(r"주행거리\s*([\d,]+)\s*km", re.I)
RE_CC = re.compile(r"배기량\s*([\d,]+)\s*cc")
RE_FUEL = re.compile(r"연료\s*([^\s]+(?:\([^)]*\))?)\s*변속기")
RE_TRANS = re.compile(r"변속기\s*(\S+)\s*연비")
RE_BODY = re.compile(r"차종\s*(\S+)\s*배기량")
RE_COLOR_EXT = re.compile(r"차량색상\s*(\S+)")
RE_COLOR_INT = re.compile(r"시트색상\s*(\S+)")
RE_PLATE = re.compile(r"차량정보\s*(\d{2,3}[가-힣]\d{4})")
RE_NEWCAR_PCT = re.compile(r"신차 출고 가격 대비\s*([\d.]+)\s*%")
RE_YEARLY_KM = re.compile(r"연평균\s*([\d,]+)\s*Km", re.I)
RE_REGION = re.compile(r"^(\S+)\s*지역 거래")

# ★ 「있음 / 없음」을 주는 자리.  ★ 그 밖의 글자는 ★ 모름(None) 이다
YES_NO = ("압류", "저당", "세금미납")
HISTORY = ("전손이력", "침수이력", "용도이력")


def _text(html: str) -> str:
    """태그를 지우고 한 줄로 만든다.  ★ 원문을 고치지 않는다 (STEP 19)."""
    return RE_WS.sub(" ", RE_TAG.sub(" ", html or "")).strip()


def _int(value) -> int | None:
    if value is None:
        return None
    got = re.sub(r"[^\d]", "", str(value))
    return int(got) if got else None


def ld_json(html: str) -> dict:
    """머리의 `ld+json`.  ★ 없으면 빈 dict — ★ 지어내지 않는다."""
    got = RE_LD.search(html or "")
    if not got:
        return {}
    try:
        out = json.loads(got.group(1))
    except (TypeError, ValueError):
        return {}
    return out if isinstance(out, dict) else {}


def _yes_no(text: str, word: str) -> int | None:
    """「없음」 → 0 · 「있음」 → 1 · 「N 회」·「N 건」 → 그 수.  ★ 못 읽으면 None.

    ★ `bool()` 로 가르지 않는다 — ★ 「없음」도 참인 문자열이다 (개정 537)
    ★★ 실측 08-23 — ★ 압류·저당은 ★ 「저당 1 건」처럼 ★ 「건」으로 온다.
       ★ 「회」만 찾으면 ★ 저당이 있는 매물이 ★ 「모름」이 되어 ★ 감점을 못 준다
    ★★ 「정보없음」은 ★ 0 이 아니라 ★ None 이다 — ★ 사이트가 모른다는 뜻이다
       ★ 0 으로 넣으면 ★ 「없다고 확인한 것」이 된다 (개정 289·434)
    """
    got = re.search(rf"{word}\s*(없음|있음|정보없음|\d+\s*[회건])", text)
    if not got:
        return None
    said = got.group(1)
    if said == "정보없음":
        return None
    if said == "없음":
        return 0
    if said == "있음":
        return 1
    return _int(said)


# ★ 차명 앞에 붙는 꾸밈말.  ★ 이것을 안 걷어내면 차종이 「The」·「뉴」가 된다 —
#   ★ 실측 08-23 — 「아우디 ★The New★ Q5(FY) …」 · 「렉서스 ★뉴★ RX 450h …」
#   ★ KB 상세 `ld+json` 의 이름에서 ★ 세어 뽑았다.  ★ 지어낸 목록이 아니다
#   ★ 「볼보 XC60 ★2세대★ …」처럼 ★ 뒤에 붙는 것은 ★ 걷어낼 것이 없다
NAME_PREFIX = ("디 올 뉴", "The New", "The new", "All New", "올 뉴", "더 뉴",
               "신형", "뉴")


def _model_of(name: str) -> tuple:
    """`ld+json` 의 이름 → (제조사, 차종).

    「BMW X3 (G45) xDrive 20 M Sport (2026년형)」   → 「X3」
    「아우디 The New Q5(FY) 40 TDI quattro …」      → 「Q5」
    ★ 괄호 안 세대 코드는 뗀다 — ★ 이름이 아니다
    """
    words = (name or "").split()
    if len(words) < 2:
        return None, None
    rest = " ".join(words[1:])
    low = rest.lower()
    for pre in sorted(NAME_PREFIX, key=len, reverse=True):
        if low.startswith(pre.lower()):
            rest = rest[len(pre):].strip()
            break
    got = rest.split()[0] if rest.split() else ""
    return words[0], (got.split("(")[0].strip() or None)


# ★★★★★ 09-02 (로드맵 차례 1-5 · KB **169점**) — ★ **주요옵션 표**.
#   ★ 실측 09-02 — ★ `<li class="optionN">` · ★ **`disable` 이면 「없음」**이다.
#   ★ ★ 「선루프 (일반)」·「헤드업디스플레이」가 ★ 원문에 그대로 있다.
#   ★ ★ ★ 그런데 ★ `options_standard_json` 이 ★ **전건 NULL** 이었다 —
#     ★ ★ 그래서 ★ `taste.option` 43 · `taste.sunroof` 12 · `taste.hud` 18 이
#     ★ ★ ★ 332건 **전건 0점**이었다.  ★ 사이트가 안 준 것이 아니라 ★ 안 읽었다
RE_OPT_LI = re.compile(
    r'<li[^>]*class="option\d+([^"]*)"[^>]*>\s*<span[^>]*class="text"[^>]*>'
    r'(.*?)</span>', re.S)


def _options(html: str) -> tuple:
    """주요옵션 → (있는 것, 없는 것).  ★ 못 읽으면 ★ 빈 짝이다 (지어내지 않는다).

    ★ `disable` 이 붙은 칸은 ★ **그 차에 없는 옵션**이다 [실측 09-02].
      ★ ★ 「없다」도 사실이다 — ★ 버리지 않고 따로 담는다
    """
    have, miss = [], []
    for cls, inner in RE_OPT_LI.findall(html or ""):
        name = RE_WS.sub(" ", RE_TAG.sub(" ", inner)).strip()
        name = re.sub(r"\s*\(\s*", " (", name)
        name = re.sub(r"\s*\)", ")", name).strip()
        if not name:
            continue
        (miss if "disable" in cls else have).append(name)
    return have, miss


# ★★★★★ 09-02 (로드맵 차례 1-5) — ★ **제조사 보증 표**.
#   ★ 실측 09-02 — ★ 「차체/일반 (100,000km / 5년) 45,007km / 2개월 남음」
#   ★ ★ 표본 60건 중 ★ **39건**에 있다.  ★ `warranty.general` 22 ＋ `warranty.power` 32
#   ★ ★ ★ KB 332건이 ★ 이 둘을 ★ 거의 다 0점으로 두고 있었다
RE_WARRANTY = re.compile(
    r"(차체\s*/\s*일반|엔진\s*/\s*주요|동력\s*전달|파워\s*트레인)"
    r"\s*\(\s*([\d,]+)\s*km"
    r"\s*/\s*(\d+)\s*년\s*\)", re.I)
MONTHS_PER_YEAR = 12


def _warranty(text: str) -> dict:
    """제조사 보증 → 개월·km.  ★ 못 읽으면 ★ 빈 표다 (지어내지 않는다).

    ★ 「(100,000km / 5년)」은 ★ **그 차의 보증 한도**다 — ★ 잔여가 아니다.
      ★ ★ 잔여는 ★ 축이 ★ 연식·주행으로 스스로 낸다 (`analyze/axis/warranty.py`)
    """
    out: dict = {}
    for kind, km, year in RE_WARRANTY.findall(text or ""):
        k = re.sub(r"\s+", "", kind)
        # ★ KB 는 ★ 「엔진/주요」라 적는다 [실측 09-02] — ★ 그것이 동력계다
        pre = "body" if k.startswith("차체") else "power"
        out[f"warranty_{pre}_km"] = int(km.replace(",", ""))
        out[f"warranty_{pre}_month"] = int(year) * MONTHS_PER_YEAR
    return out


def parse_detail(html: str, site: str, source_id: str) -> dict | None:
    """상세 한 쪽 → `core_listing` 한 줄.

    ★ 봇 차단인지는 ★ 부르는 쪽이 이미 갈랐다 (`adapters.kbchachacha.is_bot_wall`)
    ★ 여기서는 ★ 읽히는 것만 담는다.  ★ 못 읽은 칸은 ★ 넣지 않는다 (None = 모름)
    """
    if not html:
        return None
    ld = ld_json(html)
    text = _text(html)
    out: dict = {"site": site, "source_id": str(source_id),
                 "price_unit": "won"}

    name = ld.get("name")
    if name:
        out["site_model"] = name
        maker, group = _model_of(name)
        out["site_manufacturer"] = (ld.get("brand") or {}).get("name") or maker
        out["site_model_group"] = group

    # ★ 값 — `ld+json` 이 ★ 원 단위로 준다.  ★ 만원을 곱하지 않는다
    price = ((ld.get("offers") or {}).get("price"))
    if price is not None:
        out["price_current_won"] = _int(price)

    got = RE_YM.search(text)
    if got:
        out["year_month"] = f"20{got.group(1)}{got.group(2)}"
        out["form_year"] = 2000 + int(got.group(3))
    for key, rx in (("mileage_km", RE_KM), ("displacement_cc", RE_CC)):
        m = rx.search(text)
        if m:
            out[key] = _int(m.group(1))
    for key, rx in (("fuel_raw", RE_FUEL), ("transmission", RE_TRANS),
                    ("color_ext_raw", RE_COLOR_EXT),
                    ("color_int_raw", RE_COLOR_INT)):
        m = rx.search(text)
        if m and m.group(1) != "정보없음":
            out[key] = m.group(1)

    # ★★ 번호판은 ★ PII 다 — ★ `split_pii` 가 해시한다.  ★ 원문 이름으로 넘긴다
    m = RE_PLATE.search(text)
    if m:
        out["_pii_plate_no"] = m.group(1)

    m = re.search(r"(\S+)\s*지역 거래", (ld.get("description") or ""))
    if m:
        out["dealer_region"] = m.group(1)

    out["seizing_cnt"] = _yes_no(text, "압류")
    out["pledge_cnt"] = _yes_no(text, "저당")
    out["owner_change_cnt_summary"] = _yes_no(text, "소유자변경")
    out["total_loss_cnt_summary"] = _yes_no(text, "전손이력")
    out["flood_total_cnt_summary"] = _yes_no(text, "침수이력")
    out["record_use_code"] = _yes_no(text, "용도이력")

    # ★ 신차가 — ★ KB 는 ★ 비율을 준다 (규격 3-1).  ★ 값에서 되돌려 신차가를 낸다
    #   ★ 130% 가 나온다 — ★ 신차가보다 비싼 매물이다.  ★ 자르지 않는다
    m = RE_NEWCAR_PCT.search(text)
    if m and out.get("price_current_won"):
        pct = float(m.group(1))
        if pct > 0:
            out["price_origin_won"] = round(out["price_current_won"] * 100 / pct)

    out["diagnosis_car"] = 1 if "KB진단" in text else 0

    # ★★★ 사진 (명령서 73장 · 실측 08-26).  ★ KB 는 ★ **상세**에만 사진이 있다 —
    #   ★ 목록 봉투에는 없다.  ★ 그래서 상세를 돌 때 함께 채운다
    # ★ 파일 이름이 ★ `{carSeq}_…` 로 시작하는 것만 담는다 —
    #   ★ 같은 쪽에 ★ 매거진(`/IMG/board/`) · 딜러(`/IMG/memberimg/`) 사진이 섞여 있다
    photos = _photos(html, str(source_id))
    if photos:
        out["photo_main"] = photos[0]
        out["photo_list_json"] = json.dumps(photos, ensure_ascii=False)

    # ★★★★★ 09-02 — ★ 제조사 보증 (로드맵 차례 1-5).  ★ 없으면 ★ 안 담는다
    out.update(_warranty(text))

    # ★★★★★ 09-02 — ★ 주요옵션 (로드맵 차례 1-5).  ★ 없으면 ★ 안 담는다
    have, miss = _options(html)
    if have:
        out["options_standard_json"] = json.dumps(have, ensure_ascii=False)
        # ★★★★★ 09-06 (r1184 H) — ★ 「옵션은 두 갈래로 저장한다.
        #   ★ 가격이 있으면 `options_choice_json` · ★ **이름만 있으면
        #   ★ ★ `options_name_json`**.  ★ 가격이 없다고 옵션 축을 0 으로 두지 않는다」
        #   ★ KB 는 ★ **가격을 안 준다** — ★ 이름만 온다.  ★ 값을 지어내지 않는다
        out["options_name_json"] = json.dumps(have, ensure_ascii=False)
    if miss:
        # ★ 「이 차에 없는 옵션」도 사실이다 — ★ 버리지 않는다.
        #   ★ 값 자리를 지어내지 않고 ★ 곁말로 남긴다
        out["options_absent_json"] = json.dumps(miss, ensure_ascii=False)
    return out


RE_CARIMG = re.compile(
    r'https?://img\.kbchachacha\.com/IMG/carimg/[^"\'\s<>]+?\.(?:jpg|jpeg|png|webp)',
    re.I)


def _photos(html: str, source_id: str) -> list:
    """그 매물의 사진만 (명령서 73장).  ★ 없으면 빈 목록 — ★ 지어내지 않는다."""
    seen, out = set(), []
    for url in RE_CARIMG.findall(html or ""):
        name = url.rsplit("/", 1)[-1]
        if not name.startswith(f"{source_id}_"):
            continue          # ★ 이 매물의 사진이 아니다
        if url in seen:
            continue
        seen.add(url)
        out.append(url)
    return out


# ★★★★★★ 09-05 (D4 · `S46-279`) — ★ **목록 파서.**
#   ★★★ 마스터 — 「★ **가격이랑 세부 항목이랑 이미지랑**」.
#   ★★ 실측 09-05 — ★ 이 파일에 ★ `parse_detail` 뿐이고 ★ **목록 파서가 없었다** —
#     ★ ★ 그래서 ★ 매물 5,704건 중 ★ 값 **12%** · 사진 **9%** · ★ 트림 **0** 이었다.
#   ★ 그런데 ★ 목록 카드가 ★ **다 준다** [실측 09-05 · page-0001 291KB] —
#     ★ `data-car-seq` · `<strong class="tit">` 차명 ·
#     ★ `<div class="data-line">` 「24/08식(24년형)」 「13,748km」 「경기」 ·
#     ★ `<span class="price">3,970<span class="unit">만원` · `img.kbchachacha.com` 사진
#   ★★ **색·옵션은 카드에 없다** — ★ 상세가 준다.  ★ 지어내지 않는다 (금지 6)
RE_CARD = re.compile(r'<div class="area[^"]*"\s+data-car-seq="(\d+)"(.*?)'
                     r'(?=<div class="area[^"]*"\s+data-car-seq=|\Z)', re.S)
RE_TIT = re.compile(r'<strong class="tit">\s*(.*?)\s*</strong>', re.S)
RE_DATALINE = re.compile(r'<div class="data-line">(.*?)</div>', re.S)
RE_SPAN = re.compile(r'<span[^>]*>\s*(.*?)\s*</span>', re.S)
RE_PRICE = re.compile(r'<span class="price">\s*([\d,]+)\s*<span class="unit">')
RE_CARD_IMG = re.compile(r'src="(https://img\.kbchachacha\.com/[^"?]+)')
# ★ 이름을 가른다 — ★ 위 `RE_YM`·`RE_KM`(상세용)을 ★ 덮으면 안 된다.
#   ★ 실측 09-05 — ★ 덮었더니 ★ `parse_detail` 이 `group(3)` 에서 죽었다
RE_CARD_YM = re.compile(r"(\d{2})/(\d{2})식")
RE_CARD_KM = re.compile(r"([\d,]+)\s*km", re.I)


def parse_list(html: str, site: str = "kbchachacha") -> list:
    """★ 목록 한 쪽 → ★ `core_listing` 줄들 (D4).

    ★ 카드가 주는 것만 넣는다 — ★ 값 · 주행 · 연식 · 차명(트림) · 지역 · 사진.
    ★ ★ **색 · 옵션은 안 넣는다** — ★ 카드에 없다.  ★ 상세가 준다
    ★ 못 읽은 칸은 ★ 아예 안 넣는다 — ★ 「없음」으로 덮지 않는다 (금지 12)
    """
    out = []
    for sid, block in RE_CARD.findall(html or ""):
        row = {"site": site, "source_id": str(sid), "price_unit": "won"}
        tit = RE_TIT.search(block)
        if tit:
            name = " ".join(_text(tit.group(1)).split())
            if name:
                row["site_model"] = name[:120]
                maker, model = _model_of(name)
                if maker:
                    row["site_manufacturer"] = maker
                if model:
                    row["site_model_group"] = model
                # ★ 트림 — ★ 차명에서 ★ 차종 뒤를 쓴다.  ★ 없으면 안 넣는다
                if model and model in name:
                    trim = name.split(model, 1)[1].strip()
                    trim = trim.split(")", 1)[-1].strip() if trim.startswith(
                        "(") else trim
                    if trim:
                        row["trim_badge"] = trim[:80]
                        # ★★★★★ 09-06 (r1184 F-3) — ★ 「트림 0건」의 자리.
                        #   ★ 검사 `S46-279` 와 화면은 ★ `trim_grade_name` 을
                        #   ★ ★ 센다 — ★ `trim_badge` 만 채우면 ★ 0 으로 남는다.
                        #   ★ KB 카드가 주는 것은 ★ 등급명 그대로다 —
                        #     ★ ★ 우리가 고치지 않고 ★ 그대로 넣는다
                        row["trim_grade_name"] = trim[:80]
        line = RE_DATALINE.search(block)
        if line:
            parts = [" ".join(_text(x).split())
                     for x in RE_SPAN.findall(line.group(1))]
            for one in parts:
                ym = RE_CARD_YM.search(one)
                if ym and "year_month" not in row:
                    # ★ 「24/08식」 → 2024-08.  ★ 두 자리 해는 2000년대다
                    row["year_month"] = f"20{ym.group(1)}-{ym.group(2)}"
                    row["form_year"] = 2000 + int(ym.group(1))
                    continue
                km = RE_CARD_KM.search(one)
                if km and "mileage_km" not in row:
                    row["mileage_km"] = _int(km.group(1))
                    continue
                if one and "dealer_region" not in row and not any(
                        ch.isdigit() for ch in one):
                    row["dealer_region"] = one[:20]
        won = RE_PRICE.search(block)
        if won:
            got = _int(won.group(1))
            if got is not None:
                row["price_current_won"] = got * 10000      # 만원 → 원
        shots = []
        for u in RE_CARD_IMG.findall(block):
            if u not in shots:
                shots.append(u)
        if shots:
            row["photo_list_json"] = json.dumps(shots, ensure_ascii=False)
        if len(row) > 3:            # ★ 번호만 있는 것은 줄이 아니다
            out.append(row)
    return out


def parse_list_item(one, site: str = "kbchachacha") -> dict | None:
    """★ 이미 푼 줄 하나 (`load_raw` 가 부른다).  ★ 표 꼴을 안 바꾼다."""
    if isinstance(one, dict) and one.get("source_id"):
        return {**one, "site": site}
    return None
