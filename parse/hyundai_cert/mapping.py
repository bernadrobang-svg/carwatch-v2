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
# ★★★★★ 08-30 (`HYUNDAI_CERTIFIED_API.md` 08-29 절 · 마스터 지시 3) —
#   ★ **신차가를 준다.**  ★ 앞서 여러 규격이 「안 준다」고 적었는데 ★ 틀렸다.
#   ★ 실측 08-29 — ★ 상세에 ★ 「신차 가격 대비 {값}」이 ★ **8/8** 있고
#   ★ ★ 값이 **매물마다 다르다** (19,200,000 · 31,000,000 · 16,800,000 …).
#   ★ ★ 안내문이 아니다 — ★ 오판 192 의 잣대(값이 다 같으면 안내문)를 통과했다.
#   ★ 낱말은 규격이 준 것을 그대로 쓴다 — ★ 개발측이 새로 짓지 않는다
# ★★★★★ 08-30 정정 — ★ 앞 판이 ★ **절약액을 신차가로 잡았다.**
#   ★ 원문에 이런 줄이 있다 —
#     「304루9851은 ★ **신차 가격 대비 9,100,000 원 절약** 할 수 있어요」
#     「2023 더 뉴 그랜저 (IG) LPG 3.0 프리미엄 ★ **신차가 35,000,000 원**」
#   ★ ★ 앞 정규식은 ★ 「신차 가격」 뒤 12자 안의 첫 수를 잡아 ★ **9,100,000** 을 넣었다.
#   ★ ★ 그 매물의 값이 25,900,000 이라 ★ 값/신차가 = **284.6%** 가 되어
#   ★ ★ `value.origin` 75점이 ★ 0점이 됐다 (실측 · 매물 10217).
#   ★ 그래서 ★ **「대비」가 붙은 것을 빼고** ★ 「신차가 {값} 원」만 잡는다.
#   ★ ★ 원문이 스스로 적어 둔다 — 「신차가는 실제출고가격과 다르게 표현될 수 있습니다」
RE_ORIGIN = re.compile(
    r"신차\s*가(?!\s*격\s*대비)(?:격)?(?!\s*대비)[^0-9]{0,8}([\d,]{7,})\s*원")


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


# ★ 차명 앞에 붙는 꾸밈말이다.  ★ 이것을 안 걷어내면 차종이 「더」가 된다 —
#   ★ 실측 08-23 — 「2021 더 뉴 G70 …」 221건이 ★ `site_model_group='더'` 로 들어갔고
#   ★ 그 안에 ★ 「더 뉴 그랜저」(`IG02`) ★ 152건이 있었다.  ★ 규격이 「IG02·GN01 둘 다」라 한 그것이다
#   ★ 지어낸 목록이 아니다 — ★ DB 에 실제로 들어온 제목에서 세어 뽑았다
# ★ 제목에 연료가 들어 있다 (HYUNDAI_CERTIFIED_API 2d).
#   ★ 실측 08-23 — 제목의 낱말과 상세의 `fuel_raw` 가 ★ 1,006건 전건 같았다 (어긋남 0)
#   ★ 낱말이 없는 108건은 ★ 전동화 전용 차종이다 (Electrified GV70 · GV60 · 아이오닉)
FUEL_WORDS = ("가솔린", "디젤", "LPG", "하이브리드", "전기")


def _fuel_of(name: str) -> str | None:
    """제목 → 연료.  ★ 없으면 None 이다 — ★ 지어내지 않는다."""
    for w in FUEL_WORDS:
        if w in (name or ""):
            return w
    return None


NAME_PREFIX = ("디 올 뉴", "올 뉴", "더 뉴", "더 올 뉴", "신형", "The new", "Electrified")


def _model_group(name: str) -> str | None:
    """제목 → 차종 이름.  ★ 「2023 더 뉴 그랜저 (IG) LPG …」 → 「그랜저」.

    ★ 연식을 떼고 · ★ 꾸밈말을 떼고 · ★ 그 다음 낱말이 차종이다
    ★ 괄호 안 코드(`(IG)` · `(NX4)`)는 ★ 뗀다 — ★ 세대라서 이름이 아니다
    """
    rest = name.split(maxsplit=1)[1] if len(name.split()) > 1 else ""
    if not rest:
        return None
    low = rest.lower()
    for pre in sorted(NAME_PREFIX, key=len, reverse=True):
        if low.startswith(pre.lower()):
            rest = rest[len(pre):].strip()
            break
    got = rest.split(maxsplit=1)[0] if rest.split() else ""
    return got.split("(")[0].strip() or None


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
        "site_model_group": _model_group(name),
        "fuel_raw": _fuel_of(name),
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
# ★ 남은 기간의 꼴이 ★ 셋이다 (실측 08-23 · 배포에서 상세를 받아 봤다) —
#   「1 년 7 개월 남음」 · ★ 「1 년 남음」(개월이 없다) · 「7 개월 남음」
#   ★ 옛 정규식은 ★ `개월` 을 반드시 찾아 ★ 「1 년 남음」을 ★ 못 읽었다
RE_W_YM = re.compile(r"(\d+)\s*년\s*(\d+)\s*개월\s*남음")
RE_W_Y = re.compile(r"(\d+)\s*년\s*남음")
RE_W_M = re.compile(r"(\d+)\s*개월\s*남음")
RE_W_KM_LEFT = re.compile(r"([\d,]+)\s*km\s*남음")
RE_W_DONE = re.compile(r"만료")
# ★ 블록이 여기서 끝난다.  ★ 이 뒤는 ★ 「워런티 플러스」 광고다 —
#   ★ 「최대 12개월 / 20,000 km 구매 가능」이 있어 ★ 창이 넓으면 그것을 읽는다
W_STOP = ("기간 혹은 주행거리", "워런티 플러스")
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
        # ★ 신차가 (08-30).  ★ 원 단위 그대로 온다 — ★ 만원 환산을 안 한다
        "price_origin_won": _num(_one(RE_ORIGIN, text)),
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
    # ★★★★★ 08-30 (r990 1-2) — ★ **두 번 빼던 것을 고쳤다.**
    #   ★ 현대인증은 ★ 「1년 4개월 남음」처럼 ★ **남은 양**을 준다.
    #   ★ 그런데 ★ `warranty.general`·`.power` 축은 ★ 그 칸을
    #     ★ ★ 「등록부터 몇 달」(총량)로 읽고 ★ 스스로 경과분을 뺀다
    #     (`analyze/axis/warranty.py:_remaining_months` — `months - elapsed`).
    #   ★ ★ 그래서 ★ 남은 값을 그대로 넣으면 ★ **경과분이 두 번 빠졌다.**
    #   ★★ 실측 08-30 — ★ 167건이 ★ `1.1/22` 였다 (엔카는 평균 48.9개월인데
    #     ★ ★ 현대인증만 16.5개월이었다 — ★ 그것이 「남은 양」이라는 자국이다).
    #   ★ 고침 — ★ 최초등록일부터 오늘까지를 ★ **도로 더해** 총량으로 넣는다.
    #     ★ ★ 셈이지 짐작이 아니다.  ★ 등록일을 못 읽으면 ★ 넣지 않는다 (None)
    out.update(_warranty(text, out.get("reg_at")))
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


def _warranty(text: str, reg_at: str | None = None) -> dict:
    """★ 잔여 보증 — ★ 현대만 년·월·km 로 남은 양을 그대로 준다 (2a).

    ★ 「N 년 M 개월 남음」이면 ★ 그 값을 쓴다.  ★ 우리가 날짜에서 재지 않는다
    ★ 「만료」면 ★ 0 이다 — ★ 「없다고 확인한 것」이지 「모름」이 아니다
    ★ 둘 다 못 읽으면 ★ 넣지 않는다 (None).  ★ 0 으로 지어내지 않는다
    """
    out: dict = {}
    # ★ 블록의 ★ 시작과 끝을 먼저 잡는다.  ★ 창을 90자로 잘라 쓰면
    #   ★ 일반 블록이 ★ 동력 블록의 값을 읽는다 —
    #   ★ 실측 HGN260618029076 : 일반은 「1 년 남음」인데 ★ 16개월로 들어갔다.
    #     ★ 다음 블록의 「1 년 4 개월 남음」을 ★ 집은 것이다
    elapsed = _months_since(reg_at)
    marks = sorted(
        ((got.end(), got.start(), key)
         for key, head in RE_W_HEAD.items()
         for got in [head.search(text)] if got),
        key=lambda t: t[0])
    for i, (start, _, key) in enumerate(marks):
        stop = marks[i + 1][1] if i + 1 < len(marks) else len(text)
        for word in W_STOP:                       # ★ 광고 앞에서 멈춘다
            at = text.find(word, start, stop)
            if at > 0:
                stop = at
        near = text[start:stop]
        ym, yy, mm = (RE_W_YM.search(near), RE_W_Y.search(near),
                      RE_W_M.search(near))
        km = RE_W_KM_LEFT.search(near)
        done = RE_W_DONE.match(near.strip())
        left = None
        if ym:
            left = int(ym.group(1)) * 12 + int(ym.group(2))
        elif yy:
            left = int(yy.group(1)) * 12
        elif mm:
            left = int(mm.group(1))
        if left is not None:
            # ★★ 남은 달 → ★ **총량**.  ★ 축이 경과분을 다시 뺀다 (r990 1-2)
            if elapsed is None:
                continue                          # ★ 등록일을 모른다 — 안 넣는다
            out[f"{key}_month"] = left + elapsed
        elif done:
            out[f"{key}_month"] = 0               # ★ 「만료」는 0 — 확인한 것이다
        if km:
            # ★ 「남은 km」이므로 ★ 총 한도 = 남은 것 ＋ 이미 달린 것.
            #   ★ 주행거리를 여기서 못 본다 — ★ 남은 값만으로는 총량을 못 낸다.
            #   ★ ★ 그래서 ★ **km 은 안 넣는다** (None).  ★ 축은 달로만 잰다.
            #   ★ 0 이나 남은 값을 넣으면 ★ 「보증 끝났다」로 잘못 읽힌다 (금지 12)
            pass
        elif done:
            out[f"{key}_km"] = 0
    return out


def _months_since(reg_at: str | None) -> int | None:
    """최초등록부터 오늘까지 몇 달.  ★ 못 읽으면 ★ None 이다 (0 이 아니다)."""
    from datetime import datetime, timezone

    got = re.match(r"(\d{4})-(\d{2})", str(reg_at or ""))
    if not got:
        return None
    now = datetime.now(timezone.utc)
    return max(0, (now.year - int(got.group(1))) * 12
               + (now.month - int(got.group(2))))


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
