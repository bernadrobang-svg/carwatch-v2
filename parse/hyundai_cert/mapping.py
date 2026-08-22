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

import json
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


# ── 상세 (HYUNDAI_CERTIFIED_API 2a) ──────────────────────────────────
# ★ 상세는 ★ HTML 이다.  ★ 표를 지우면 「이름 값 이름 값」이 한 줄로 남는다
#   ★ 그래서 ★ 이름을 닻으로 삼아 그 뒤 한 칸을 읽는다
RE_REG = re.compile(r"최초등록일\s*(\d{4})\.(\d{2})\.(\d{2})")
RE_CC = re.compile(r"배기량\s*([\d,]+)\s*cc")
RE_FUEL = re.compile(r"연료\s*([가-힣A-Za-z]+)")
RE_COLOR_EXT = re.compile(r"외관컬러\s*([^\s]+)")
RE_COLOR_INT = re.compile(r"내장컬러\s*([^\s]+)")
RE_TRANS = re.compile(r"변속기\s*([가-힣]+)")
RE_OFFER = re.compile(r"제시번호\s*(\d+)")
RE_ACCIDENT = re.compile(r"내차피해(?:이력)?\s*(\d+)\s*건")
RE_OWNER = re.compile(r"소유자\s*변경\s*(있음|없음|\d+\s*회)")
RE_SEIZE = re.compile(r"압류\s*(있음|없음)")
RE_PLEDGE = re.compile(r"저당\s*(있음|없음)")
# ★★ 잔여 보증 — ★ 꼴이 ★ 둘이다 (실측 08-23)
#   남은 것  「차체 · 일반 · 냉난방 부품 ★ 2 년 10 개월 남음 … ★ 79,435 km 남음」
#   끝난 것  「차체 · 일반 · 냉난방 부품 ★ 만료 2025 년 1 월 까지 ★ 만료 100,000 km 까지」
#   ★ 남은 것은 ★ 사이트가 ★ 그대로 준다 — ★ 우리가 안 잰다 (네 사이트 중 현대뿐이다)
RE_W_HEAD = {
    "warranty_body": re.compile(r"차체\s*·?\s*일반[^가-힣0-9]{0,12}냉난방[^0-9만]{0,12}"),
    "warranty_power": re.compile(r"엔진\s*및\s*동력전달[^0-9만]{0,12}"),
}
RE_W_LEFT = re.compile(r"(?:(\d+)\s*년\s*)?(\d+)\s*개월\s*남음")
RE_W_KM_LEFT = re.compile(r"([\d,]+)\s*km\s*남음")
RE_W_DONE = re.compile(r"만료")
# ★ 사이트 검증의 근거 — 「정밀점검 287개 항목」 · 「성능점검기록부 발행완료」
MARK_CERTIFIED = "정밀점검"


def _json(value) -> str | None:
    """배열은 ★ 직렬화만 한다.  가공하지 않는다 (STEP 19 금지)."""
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def detail_text(html: str) -> str:
    """상세 HTML → 한 줄 글.  ★ 표시를 지우고 공백을 하나로 만든다."""
    body = re.sub(r"<script.*?</script>", " ", html or "", flags=re.S)
    body = re.sub(r"<style.*?</style>", " ", body, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body))


def _one(pat, text, group: int = 1):
    got = pat.search(text)
    return got.group(group) if got else None


def parse_detail(html: str, site: str, source_id: str) -> dict | None:
    """상세 → (core_listing 필드, core_record 필드) 를 함께 낸다."""
    got = parse_detail_all(html, site, source_id)
    return got[0] if got else None


def parse_detail_all(html: str, site: str, source_id: str) -> tuple | None:
    """상세 → core_listing 필드 (HYUNDAI_CERTIFIED_API 2a 표).

    ★ 못 읽은 칸은 ★ None 이다.  ★ 0 으로 채우지 않는다 —
      ★ 「없음」과 「모름」은 다르다 (개정 289·434)
    ★ 짧으면 ★ 못 받은 것이다.  ★ None 을 돌려준다 (KB 봇페이지와 같은 함정)
    """
    if not html or len(html) < 50_000:
        return None
    text = detail_text(html)
    if "최초등록일" not in text:
        return None
    reg = RE_REG.search(text)
    seize = _one(RE_SEIZE, text)
    pledge = _one(RE_PLEDGE, text)
    acc = _one(RE_ACCIDENT, text)
    owner = _one(RE_OWNER, text)
    out = {
        "site": site,
        "source_id": source_id,
        "reg_at": (f"{reg.group(1)}-{reg.group(2)}-{reg.group(3)}"
                   if reg else None),
        "year_month": f"{reg.group(1)}-{reg.group(2)}" if reg else None,
        "displacement_cc": _num(_one(RE_CC, text)),
        "fuel_raw": _one(RE_FUEL, text),
        "color_ext_raw": _one(RE_COLOR_EXT, text),
        "color_int_raw": _one(RE_COLOR_INT, text),
        "transmission": _one(RE_TRANS, text),
        # ★ 진정성 — 제시번호가 있으면 「신고된 차」다
        "site_pass_type": _one(RE_OFFER, text),
        # ★ 소유자 변경 — 「있음 / 없음」으로 온다.  ★ 횟수가 아니다
        "owner_change_cnt_summary": (None if owner is None
                                     else (1 if "있음" in owner
                                           else _num(owner) or 0)),
        # ★ 압류·저당 — 「없음」이면 0 이다.  ★ 못 읽으면 None 이다
        "seizing_cnt": (None if seize is None else (0 if seize == "없음" else 1)),
        "pledge_cnt": (None if pledge is None else (0 if pledge == "없음" else 1)),
        # ★ 사이트 검증 — 정밀점검 287개 항목 (2a)
        "site_pass_grade": ("CERTIFIED" if MARK_CERTIFIED in text else None),
        "diagnosis_status": "ok" if MARK_CERTIFIED in text else None,
    }
    out.update(_warranty(text))
    out["options_standard_json"] = _json(_options(text))
    # ★★ 사고 건수는 ★ core_listing 이 아니라 ★ core_record 의 칸이다.
    #   ★ 남의 표 칸을 core 에 넣으면 upsert 가 조용히 버린다 (A-2)
    record = {
        "listing_id": None,          # ★ 부르는 쪽이 대리키를 넣는다
        "site": site,
        "row_status": "ok",
        "record_open": 1,            # ★ 화면에 이력이 열려 있다 (2a)
        "collected_at": None,        # ★ 부르는 쪽이 넣는다
        "accident_my_cnt": _num(acc),
        "owner_change_cnt": (None if owner is None
                             else (1 if "있음" in owner else _num(owner) or 0)),
    }
    return out, record


def _num(text) -> int | None:
    if text is None:
        return None
    got = re.sub(r"\D", "", str(text))
    return int(got) if got else None


def _warranty(text: str) -> dict:
    """★ 잔여 보증 — ★ 현대만 년·월·km 로 남은 양을 그대로 준다 (2a).

    ★ 「N 년 M 개월 남음」이면 ★ 그 값을 쓴다.  ★ 우리가 날짜에서 재지 않는다
    ★ 「만료」면 ★ 0 이다 — ★ 「없다고 확인한 것」이지 「모름」이 아니다
    ★ 둘 다 못 읽으면 ★ 넣지 않는다 (None).  ★ 0 으로 지어내지 않는다
    """
    out: dict = {}
    for key, head in RE_W_HEAD.items():
        got = head.search(text)
        if not got:
            continue
        near = text[got.end():got.end() + 90]
        left = RE_W_LEFT.search(near)
        km = RE_W_KM_LEFT.search(near)
        if left:
            out[f"{key}_month"] = int(left.group(1) or 0) * 12 + int(left.group(2))
        elif RE_W_DONE.match(near.strip()):
            out[f"{key}_month"] = 0
        if km:
            out[f"{key}_km"] = _num(km.group(1))
        elif RE_W_DONE.match(near.strip()):
            out[f"{key}_km"] = 0
    return out


def _months_left(year: int, month: int) -> int:
    """★ 오늘 기준 남은 개월.  ★ 음수는 0 이다."""
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    return max(0, (year - now.year) * 12 + (month - now.month))


# ★ 옵션은 ★ 이름으로 온다 (2a) — ★ 숫자 코드가 아니다.  ★ 그대로 남긴다
OPTION_WORDS = (
    "내비게이션", "하이패스", "열선 스티어링 휠", "열선시트", "통풍시트",
    "전동시트", "가죽 시트", "전동식 트렁크", "선루프", "헤드업 디스플레이",
    "서라운드 뷰 모니터", "후방 모니터", "후측방 경보 시스템",
    "차선 이탈 경보", "스마트 크루즈 컨트롤", "전방 주차거리 경고",
)


def _options(text: str) -> list:
    """붙어 있는 옵션 이름.  ★ 화면 글에 있는 것만 센다 — 지어내지 않는다."""
    head = text.find("옵션 정보")
    if head < 0:
        return []
    near = text[head:head + 1200]
    return [w for w in OPTION_WORDS if w in near]
