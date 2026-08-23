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
    return out


def accident_of(body: dict) -> str | None:
    """사고 판정 — ★ `acdtHistComnt` 하나로 가른다 (규격 3-2).

    ★ `smplReprYn` 으로 가르지 않는다 — ★ 단순수리와 사고가 ★ 둘 다 2 다
    ★ `acdtHistYn` 으로 가르지 않는다 — ★ 표본 12건 ★ 전부 1 이다
    """
    return ((body.get("data") or {}).get("rvo") or {}).get("acdtHistComnt")
