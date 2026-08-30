# -*- coding: utf-8 -*-
"""K카 상세 → `core_listing` (`docs/KCAR_API.md` 3장 · `MULTISITE_MAPPING.md` 1장).

지시서   `docs/KCAR_API.md` 3-1·3-2·3-3 · `docs/MULTISITE_MAPPING.md`
근거     ★ 상세 하나(74~87KB)가 ★ 전부를 준다.  ★ 목록은 `enc` 라 못 부른다
값규칙   ★★ 응답이 ★ `{"data":{…}}` 로 싸여 있다.  ★ `data` 를 안 벗기면 ★ 전건 NULL 이다
        ★★ `Yn` 필드가 ★ 전부 문자열이다 — ★ `bool('N')` 은 ★ 참이다 (개정 537).
           ★ `bool()` 로 가르지 않는다.  ★ 값을 대 놓고 견준다
        ★ `npriceFullType` 은 ★ 신차가가 아니라 ★ 판매가다 (규격 3-1).  ★ 안 쓴다
금지     ★ `smplReprYn`·`acdtHistYn` 으로 사고를 가르는 것 (규격 3-2)
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone

WON_PER_MANWON = 10_000

# ★ 「예」로 읽을 값.  ★ 문자열이다 — ★ `bool()` 이 아니라 ★ 이 표로 가른다
YES = ("Y", "y", "1", 1, True)
NO = ("N", "n", "0", 0, False)


def _int(value) -> int | None:
    """숫자만 남긴다.  ★ 못 읽으면 None (모름) — ★ 0 이 아니다."""
    if value is None:
        return None
    got = "".join(ch for ch in str(value) if ch.isdigit())
    return int(got) if got else None


def yn(value) -> int | None:
    """`Yn` 문자열 → 1 · 0 · None.

    ★★ `bool('N')` 은 ★ 참이다 — ★ 엔카에서 이것으로 522건이 새어 나갔다 (개정 536·537)
    ★ 표에 없는 값은 ★ None 이다.  ★ 지어내지 않는다
    """
    if value in YES:
        return 1
    if value in NO:
        return 0
    return None


def _months_until(yyyymmdd, at: datetime) -> int | None:
    """종료일 → ★ 남은 개월.  ★ 지난 것은 0 이다 (「없다고 확인한 것」).

    ★ K카는 ★ 잔여가 아니라 ★ 끝나는 날을 준다 (MULTISITE_MAPPING 5a⑥)
    """
    got = _int(yyyymmdd)
    if got is None or got < 19000101:
        return None
    y, m = divmod(got // 100, 100)
    if not (1 <= m <= 12):
        return None
    return max(0, (y - at.year) * 12 + (m - at.month))


def _model_group(name: str | None) -> str | None:
    """`modelNm` → 차종.  ★ 괄호 안(세대)만 뗀다.

    「G80 (RG3 F/L)」 → 「G80」 · 「그랑 콜레오스」 → 「그랑 콜레오스」
    ★ 첫 낱말만 쓰면 ★ 두 낱말 차종이 잘린다 — ★ 실측에서 잡았다
    """
    got = (name or "").split("(")[0].strip()
    return got or None


def parse_detail(body: dict, site: str, source_id: str,
                 at: datetime | None = None) -> dict | None:
    """상세 한 건 → `core_listing` 한 줄.

    ★ 「없는 매물」·「못 받음」은 ★ 부르는 쪽이 이미 갈랐다 (`collect_kcar.classify`)
    ★ 못 읽은 칸은 ★ 넣지 않는다 — ★ None 은 「모름」이다 (개정 289·434)
    """
    if not isinstance(body, dict):
        return None
    # ★★ 여기가 함정이다 — ★ `data` 를 안 벗기면 ★ 전건 NULL 이다
    data = body.get("data") or {}
    rvo = data.get("rvo") or {}
    if not rvo.get("carCd"):
        return None
    hist = data.get("carhistory") or {}
    mast = data.get("master") or {}
    now = at or datetime.now(timezone.utc)

    out: dict = {
        "site": site,
        "source_id": str(source_id),
        "price_unit": "won",
        "site_manufacturer": rvo.get("mnuftrNm"),
        "site_model": rvo.get("modelNm"),
        # ★ 「G80 (RG3 F/L)」 → 「G80」.  ★ 괄호 안은 세대라 뗀다
        # ★★ 첫 낱말만 쓰면 안 된다 — ★ 「그랑 콜레오스」가 ★ 「그랑」이 된다 (실측 08-24)
        "site_model_group": _model_group(rvo.get("modelNm")),
        "trim_badge": rvo.get("grdNm"),
        "trim_badge_detail": rvo.get("grdDtlNm"),
        "fuel_raw": rvo.get("fuelTypecdNm"),
        "color_ext_raw": rvo.get("extrColorNm"),
        "dealer_shop": rvo.get("cntrNm"),
        "vin": rvo.get("vin"),
        # ★★ 번호판은 ★ PII 다 — ★ `split_pii` 가 해시한다 (STEP 35)
        "_pii_plate_no": rvo.get("cno"),
        "year_month": (str(rvo.get("mfgDt")) or None) if rvo.get("mfgDt") else None,
        "form_year": _int(rvo.get("regModelyr")),
        "mileage_km": _int(rvo.get("milg")),
        "displacement_cc": _int(rvo.get("engdispmnt")),
    }
    # ★ 값 — ★ `salprc` 는 만원이다.  ★ `npriceFullType` 은 ★ 신차가가 아니다 (규격 3-1)
    won = _int(rvo.get("salprc"))
    if won is not None:
        out["price_current_won"] = won * WON_PER_MANWON

    # ★ 제조사 보증 — ★ 끝나는 날과 상한 km 를 준다.  ★ 두 축을 따로 읽는다
    for axis, day, milg in (
        ("general", rvo.get("nwcaGurnteGnrlSurvDt"),
         rvo.get("nwcaGurnteGnrlCmpntMilg")),
        ("power", rvo.get("nwcaGurnteEngeSurvDt"),
         rvo.get("nwcaGurnteEngeMssnMilg")),
    ):
        left = _months_until(day, now)
        if left is not None:
            out[f"warranty_{'body' if axis == 'general' else 'power'}_month"] = left
        km = _int(milg)
        if km is not None:
            out[f"warranty_{'body' if axis == 'general' else 'power'}_km"] = km

    # ★★ `Yn` 은 ★ 문자열이다.  ★ `yn()` 이 가른다 — ★ `bool()` 이 아니다
    out["seizing_cnt"] = yn(mast.get("szrMogeYn"))
    out["owner_change_cnt_summary"] = _int(hist.get("ownrChngCnt"))
    out["total_loss_cnt_summary"] = _int(hist.get("gnrlTtlsAcdtCnt"))
    out["flood_total_cnt_summary"] = _int(hist.get("fldgAcdtCnt"))
    out["robber_cnt_summary"] = _int(hist.get("rbrTtlsAcdtCnt"))
    # ★ 렌트 이력 — ★ 「직영은 렌트를 안 판다」는 틀렸다 (오판 #45).  ★ 값을 그대로 본다
    if yn(hist.get("rentHistYn")) == 1:
        out["sell_type"] = "렌트"
    elif yn(hist.get("bizuseHistYn")) == 1:
        out["business_flag"] = 1
    out["business_flag"] = yn(hist.get("bizuseHistYn"))
    out["government_flag"] = yn(hist.get("instnHistYn"))

    # ★★★ 사진 (명령서 73장 · 실측 08-26).  ★ K카는 ★ **상세**에만 사진이 있다.
    #   ★ `photoList` 가 겉·속·옵션을 다 담는다 — ★ 그것을 그대로 쓴다
    photos = _photos(data)
    if photos:
        out["photo_main"] = photos[0]
        out["photo_list_json"] = json.dumps(photos, ensure_ascii=False)
    return out


# ★ 사진이 담긴 자리 넷 (실측 08-26).  ★ `photoList` 가 전부를 담고
#   나머지 셋은 갈래별로 겹친다 — ★ 겹치는 것은 한 번만 넣는다
PHOTO_KEYS = ("photoList", "outerPhotoList", "innerPhotoList",
              "optionPhotoList")


def _photos(data: dict) -> list:
    """그 매물의 사진 (명령서 73장).  ★ 없으면 빈 목록 — ★ 지어내지 않는다."""
    seen, out = set(), []
    for key in PHOTO_KEYS:
        for one in (data.get(key) or []):
            url = (one or {}).get("elanPath") if isinstance(one, dict) else None
            if not url or url in seen:
                continue
            seen.add(url)
            out.append(url)
    return out


def parse_list_item(item: dict, site: str) -> dict | None:
    """목록 한 건 → `core_listing` 한 줄 (KCAR_API 0a · 명령서 18-2).

    ★★ 실측 08-24 — ★ 94칸 중 ★ 값이 있는 것은 ★ 37칸이다.
       ★ 규격 18-2 가 온다고 적은 ★ `cno`·`acdtHistCnts`·`engdispmnt`·`trnsmsnNm` 은
       ★ 527건 ★ 전건이 None 이다 — ★ 그것들은 ★ 상세에서 온다
    ★ 목록으로 채울 수 있는 것만 채운다.  ★ 없는 칸은 ★ 안 넣는다 (None = 모름)
    """
    if not isinstance(item, dict) or not item.get("carCd"):
        return None
    out: dict = {
        "site": site,
        "source_id": str(item["carCd"]),
        "price_unit": "won",
        "site_manufacturer": item.get("mnuftrNm"),
        "site_model": item.get("modelNm"),
        "site_model_group": _model_group(item.get("modelNm")),
        "trim_badge": item.get("grdNm"),
        "trim_badge_detail": item.get("grdDtlNm"),
        "fuel_raw": item.get("fuelNm"),
        "color_ext_raw": item.get("extrColorNm"),
        "dealer_shop": item.get("cntrNm"),
        "form_year": _int(item.get("prdcnYr")),
        "mileage_km": _int(item.get("milg")),
    }
    if item.get("mfgDt"):
        out["year_month"] = str(item["mfgDt"])
    # ★ `prc` 는 만원이다.  ★ `dcPrc` 는 할인 뒤 표시가다 (실측 — 1130 → 1080)
    won = _int(item.get("prc"))
    if won is not None:
        out["price_current_won"] = won * WON_PER_MANWON
    cut = _int(item.get("dcPrc"))
    if cut is not None:
        out["price_detail_won"] = cut * WON_PER_MANWON
    # ★★★★★ 08-30 (`11-store/a-key.md` 08-29 절 · 미확정 20) —
    #   ★ K카가 ★ **`resvYn`** 을 준다 — ★ `Y` 118 / `N` 369 (487건 중 · 가이드 실측).
    #   ★ ★ 지금까지 ★ **이 칸을 안 읽어** ★ 계약 중인 차 118대가
    #   ★ ★ 「판매 중」으로 화면에 서 있었다.
    #   ★★ 사이트가 준 값을 ★ **그대로** 적는다 — ★ 「reserved」로 옮기지 않는다.
    #   ★ ★ 우리 말로 옮기는 것은 ★ `dict_enum(site,'sales_status',…)` 이 한다.
    #   ★ ★ `status`(우리 판정)와 ★ 섞지 않는다
    if item.get("resvYn") is not None:
        out["sales_status"] = f"resvYn={item['resvYn']}"
    # ★ 위탁이면 직영이 아니다 — ★ 사이트 검증 단계가 다르다 (f-table)
    out["copy_car"] = None
    if item.get("csgmtYn") is not None:
        out["business_flag"] = yn(item.get("csgmtYn"))
    return out


def accident_of(body: dict) -> str | None:
    """사고 판정 — ★ `acdtHistComnt` 하나로 가른다 (규격 3-2).

    ★ `smplReprYn` 으로 가르지 않는다 — ★ 단순수리와 사고가 ★ 둘 다 2 다
    ★ `acdtHistYn` 으로 가르지 않는다 — ★ 표본 12건 ★ 전부 1 이다
    """
    return ((body.get("data") or {}).get("rvo") or {}).get("acdtHistComnt")

def record_of(body: dict, site: str) -> dict | None:
    """상세 → ★ `core_record` 한 줄 (규격 3-2 · 3-3).

    ★★★ 08-28 — ★ K카는 ★ `core_listing` 만 쓰고 ★ **`core_record` 를 안 썼다.**
      ★ ★ 실측 — ★ 엔카는 5,603행인데 ★ K카는 ★ **0행**이었다.
      ★ ★ 그래서 ★ 상세를 받아도 ★ `state.accident` 51점이 ★ 0/34 로 비어 있었다 —
        ★ ★ 사고 축은 ★ `core_record` 에서 온다.  ★ 「상세가 전부다」인데 ★ 그 자리가 비었다
    ★ 칸은 ★ 표본으로 ★ 눈으로 확인한 것만 담는다 (`EC61306360` · 08-28)
      carhistory.rsltCd '000' · owncarDmgeAcdtCnt 1 · owncarDmgeInsrAmtSum 3,222,770
      othrcarWrdgAcdtCnt 1 · gnrlTtlsAcdtCnt 0 · fldgAcdtCnt 0 · rbrTtlsAcdtCnt 0
      carOwnrChngHistList[].title '신규등록(수입차)' · '명의이전등록'
    ★ 없는 것은 안 담는다 — ★ 「없음 0」으로 지어내지 않는다 (개정 325)
    """
    data = body.get("data") or {}
    hist = data.get("carhistory") or {}
    if not hist:
        return None

    def _i(key):
        got = hist.get(key)
        return int(got) if isinstance(got, (int, float)) or (
            isinstance(got, str) and got.strip().isdigit()) else None

    # ★ 소유자 변경 — ★ 「명의이전등록」 줄만 센다.  ★ 신규등록은 소유자 변경이 아니다
    owners = data.get("carOwnrChngHistList") or []
    chng = sum(1 for o in owners
               if "명의이전" in str((o or {}).get("title") or ""))
    biz = str(hist.get("bizuseHistYn") or "").upper()

    out = {
        "listing_id": None,           # ★ 부르는 쪽이 대리키를 넣는다
        "site": site,
        "row_status": "ok",
        "collected_at": None,         # ★ 부르는 쪽이 넣는다
        # ★ 이력 조회가 됐나 — ★ `000` 이 성공이다 (규격 3-3)
        "record_open": 1 if str(hist.get("rsltCd") or "") == "000" else 0,
        "accident_my_cnt": _i("owncarDmgeAcdtCnt"),
        "accident_my_cost": _i("owncarDmgeInsrAmtSum"),
        "accident_other_cnt": _i("othrcarWrdgAcdtCnt"),
        "accident_other_cost": _i("othrcarWrdgInsrAmtSum"),
        "accident_total_cnt": _i("acdtCnt"),
        "total_loss_cnt": _i("gnrlTtlsAcdtCnt"),
        "flood_total_cnt": _i("fldgAcdtCnt"),
        "robber_cnt": _i("rbrTtlsAcdtCnt"),
    }
    if owners:
        out["owner_change_cnt"] = chng
    if biz in ("Y", "N"):
        out["use_business"] = 1 if biz == "Y" else 0

    # ★★★★★ 08-31 (명령서 r1007 · 1-9) — ★ 남은 칸을 채운다.
    #   ★ 코드 표는 ★ `f-table` **3c** 다 — ★ 내가 뜻을 지어내지 않는다
    gov = str(hist.get("instnHistYn") or "").upper()
    if gov in ("Y", "N"):
        # ★ 3c — ★ 관용 이력.  ★ `"N"` 은 ★ 「아니다」이지 「모른다」가 아니다
        out["use_gov"] = 1 if gov == "Y" else 0
    rent = str(hist.get("rentHistYn") or "").upper()
    if rent == "Y":
        # ★★ 3c — ★ 렌트다.  ★ 그런데 ★ `history.use` 축이 렌트를 가리는 길은 넷이고
        #   ★ ★ K카의 Y/N 은 ★ 그 넷 어디에도 안 맞는다 (헤이딜러 불리언과 같은 자리).
        #   ★ ★ 그래서 ★ 사실만 남기고 ★ **용도 축을 안 연다** — ★ 열면 렌트 차가
        #   ★ ★ ★ 「자가용 22점」을 받는다.  ★ 마스터께 올려 둔 물음이다
        out["use_cd"] = "kcar:rentHistYn=Y"
    elif rent == "N" and gov in ("Y", "N") and biz in ("Y", "N"):
        # ★ 셋을 다 봤다 — ★ 그때만 ★ 「봤다」고 말할 수 있다 (`history.use` 관문).
        #   ★ 번호판 변경 이력이 ★ 관문의 셋째다 — ★ 원문 그대로 담는다
        out["plate_history_hash_json"] = json.dumps(
            [hist.get("fstCarInfo")] if hist.get("fstCarInfo") else [],
            ensure_ascii=False)
    if _i("carInfoChngCnt") is not None:
        out["plate_change_cnt"] = _i("carInfoChngCnt")
    # ★ 소유자 변경 — ★ 이력 목록이 없으면 ★ `ownrChngCnt` 를 쓴다 (3-2)
    if "owner_change_cnt" not in out and _i("ownrChngCnt") is not None:
        out["owner_change_cnt"] = _i("ownrChngCnt")
    # ★★ 자차 미가입 — ★ 「2026년03월~2026년05월」로 온다.
    #   ★ 축은 ★ `["202603~202605"]` 꼴을 읽는다 (`store/core.py:_not_join_months`)
    spans = _not_join_spans(hist.get("unnsPerd"))
    if spans is not None:
        out["not_join_json"] = json.dumps(spans, ensure_ascii=False)
    if hist.get("useCd"):
        # ★ 3c — ★ `useCd` 는 ★ **숫자다.  2·3 이 무엇인지 아직 모른다.**
        #   ★ ★ 모르는 채로 `private` 로 매기지 않는다 — ★ 원문만 남긴다
        out["use1_json"] = json.dumps(
            {"useCd": hist.get("useCd"), "fstUseCd": hist.get("fstUseCd"),
             "useChngCnt": hist.get("useChngCnt")}, ensure_ascii=False)
    return {k: v for k, v in out.items() if v is not None or k in
            ("listing_id", "collected_at")}


RE_UNNS = re.compile(r"(\d{4})\s*년\s*(\d{1,2})\s*월\s*~\s*"
                     r"(\d{4})\s*년\s*(\d{1,2})\s*월")


def _not_join_spans(text) -> list | None:
    """「2026년03월~2026년05월」 → `["202603~202605"]`.

    ★ 칸이 아예 없으면 ★ `None` (모른다) · ★ 빈 값이면 ★ `[]` (미가입 기간이 없다).
      ★ ★ 둘은 다르다 (개정 435 — 「기간이 0」과 「모른다」)
    """
    if text is None:
        return None
    got = RE_UNNS.findall(str(text))
    if not got:
        return [] if not str(text).strip() else None
    return [f"{a}{int(b):02d}~{c}{int(d):02d}" for a, b, c, d in got]
