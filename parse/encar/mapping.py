# -*- coding: utf-8 -*-
"""엔카 원문 → CORE 필드 (L3).

지시서   2장 STEP 19 (list) · 20 (detail) · 21 (inspection) · 21a (record)
         3장 STEP 32 (NULL 3종) · 0장 STEP 4 (명명)
근거     수집은 저장만 한다.  해석은 여기가 한다 (1장 STEP 9).
         파싱 규칙이 바뀌면 재파싱만으로 복구된다.  재수집이 필요 없다.
금지     배열을 가공해서 저장하는 것.  직렬화만 한다.
         v1 은 outers 를 가공하려다 존재하지 않는 경로(outers[].children[])를
         읽어 전건 NULL 이 됐고, 사고 20점이 한 번도 작동하지 않았다.
         falsy 를 None 으로 만드는 것 — 「없음」이 「실패」로 저장된다.
"""
from __future__ import annotations

from contracts import clean_vin  # noqa: F401

import json

from errors import ParseError

# 단위 환산.  가격은 만원 단위로 온다 (STEP 20)
WON_PER_MANWON = 10000

PRICE_UNIT = "manwon"

# 원문 구조 — notJoinDate1 ~ notJoinDate5 (STEP 21a)
NOT_JOIN_INDEXES = (1, 2, 3, 4, 5)


def _get(node, path: str):
    """`a.b.c` 를 따라간다.  없으면 None — 「그 경로가 없었다」다."""
    cur = node
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
        if cur is None:
            return None
    return cur


def _json(value) -> str | None:
    """배열·객체는 원문 그대로 직렬화한다.

    금지   if not v: return None
           빈 컨테이너는 '[]' 로 남는다.  None 은 「없었다」일 때만이다 (STEP 32)
    """
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def _won(manwon) -> int | None:
    """만원 → 원.  값 크기로 단위를 추정해 되돌리지 않는다 (STEP 20)."""
    if manwon is None:
        return None
    return int(round(float(manwon) * WON_PER_MANWON))


# ── VIN 형식 (3장 STEP 30) ───────────────────────────────────────────
# ★ 17자리 · 영숫자 · I·O·Q 미포함.  표준 형식이라 검증이 가능한 유일한 결합 키다.
# 실측   상세 A 17자리 411 · 없음 89          정상
#        점검부 17자리 418 · 6자리 50 · 11자리 7 · 16자리 1   ★ 원문에 오염이 있다
# 금지   길이 검증 없이 결합 검증자로 쓰는 것
#        → 6자리 값이 우연히 겹쳐 다른 차를 같은 차로 묶는다
from contracts import VIN_LENGTH  # noqa: F401  (STEP 15a)
from contracts import VIN_FORBIDDEN  # noqa: F401  (STEP 15a)


# clean_vin 은 contracts.py 다 — store 도 쓴다 (STEP 15a)


def _ym(value) -> str | None:
    """`202603.0` → `2026-03`."""
    if value is None:
        return None
    s = str(int(float(value)))
    if len(s) != len("202603"):
        raise ParseError(f"Year 형식 이상: {value!r}", step="STEP 19")
    return f"{s[:4]}-{s[4:]}"


def _date10(value) -> str | None:
    """날짜를 `YYYY-MM-DD` 로 통일한다.

    실측   detail    `2026-03-05T11:22:33`   ISO
           점검부    `20210615`              구분자 없음
    근거   같은 개념에 두 형식이 섞이면 경과월 계산이 어긋난다 (STEP 4 `_date`)
    금지   형식이 다르다는 이유로 한쪽을 버리는 것
    """
    if value is None:
        return None
    s = str(value).strip()
    if s.isdigit() and len(s) == len("20210615"):
        return f"{s[:4]}-{s[4:6]}-{s[6:]}"
    return s[:len("2026-03-05")]


def _int(value) -> int | None:
    if value is None:
        return None
    return int(float(value))


def _bool(value) -> int | None:
    if value is None:
        return None
    return 1 if value else 0


# ── STEP 18a 봉투 ────────────────────────────────────────────────────
# 라벨 ↔ 내용 형식은 contracts 에 있다 (0장 불변식 ④).
# ★ store 가 parse 를 부르면 층이 거꾸로 돈다 — 형식 규칙은 계약이지 파싱이 아니다
from contracts import FIELD_SHAPES, shape_ok, shape_violations  # noqa: E402,F401

def unpack_envelope(body: dict) -> tuple[int, list[dict]]:
    """봉투를 펼친다.  펼치는 것은 파싱이다.  저장이 아니다 (STEP 18a)."""
    if not isinstance(body, dict) or "SearchResults" not in body:
        raise ParseError("목록 봉투가 아니다", endpoint="list", step="STEP 18a")
    return int(body.get("Count") or 0), list(body.get("SearchResults") or [])


# ── STEP 19 list ─────────────────────────────────────────────────────
def parse_list_item(item: dict, site: str) -> dict:
    """SearchResults[] 요소 → core_listing 필드."""
    sid = item.get("Id")
    if sid is None:
        raise ParseError("Id 없음", endpoint="list", step="STEP 19")
    return {
        # ★ listing_id 는 DB 가 만든다.  문자열로 조립하지 않는다 (STEP 30)
        "site": site,
        "source_id": str(sid),
        "site_model_group": item.get("ModelGroup"),
        "site_model": item.get("Model"),
        "site_manufacturer": item.get("Manufacturer"),
        "trim_badge": item.get("Badge"),
        # ★ 세부등급 (개정 313).  Badge 만으로는 트림이 안 갈린다 —
        #   「가솔린 2.5 터보 AWD」가 깡통과 시그니처를 같게 만든다
        "trim_badge_detail": item.get("BadgeDetail"),
        "fuel_raw": item.get("FuelType"),
        "year_month": _ym(item.get("Year")),
        "form_year": _int(item.get("FormYear")),
        "mileage_km": _int(item.get("Mileage")),
        "price_current_won": _won(item.get("Price")),
        "price_unit": PRICE_UNIT,
        "color_ext_raw": item.get("Color"),
        "color_ext_hex": item.get("ColorExpression"),
        "color_int_raw": item.get("SeatColor"),
        "color_int_hex": item.get("SeatColorExpression"),
        "transmission": item.get("Transmission"),
        "sell_type": item.get("SellType"),
        "sales_status": item.get("SalesStatus"),
        "copy_car": item.get("ServiceCopyCar"),
        # ★ 지역이다.  v1 은 딜러 상사명 컬럼에 넣어 전건이 오염됐다
        "dealer_region": item.get("OfficeCityState"),
        "dealer_photo": item.get("DealerPhoto"),
        "photo_main": item.get("Photo"),
        "photo_list_json": _json(item.get("Photos")),
        "site_service_marks_json": _json(item.get("ServiceMark")),
        "site_trust_json": _json(item.get("Trust")),
        "site_condition_json": _json(item.get("Condition")),
        "site_separation_json": _json(item.get("Separation")),
        "site_ad_type_json": _json(item.get("AdType")),
        "site_buy_type_json": _json(item.get("BuyType")),
        "site_home_verify": item.get("HomeServiceVerification"),
        "row_status": "ok",
    }


# ── STEP 20 detail ───────────────────────────────────────────────────
def parse_detail(body: dict, site: str, source_id: str) -> dict:
    """상세 A → core_listing 필드.

    ★ options.choice 는 '[]' 와 NULL 을 구분한다.
      '[]' = 선택 옵션 없음(값 0).  NULL = 수집 실패
    """
    firm = _get(body, "partnership.dealer.firm") or {}
    return {
        "site": site,
        "source_id": str(source_id),
        "price_origin_won": _won(_get(body, "category.originPrice")),
        "warranty_body_month": _int(_get(body, "category.warranty.bodyMonth")),
        "warranty_body_km": _int(_get(body, "category.warranty.bodyMileage")),
        "warranty_power_month": _int(
            _get(body, "category.warranty.transmissionMonth")),
        "warranty_power_km": _int(
            _get(body, "category.warranty.transmissionMileage")),
        "model_catalog_key": (
            None if _get(body, "category.jatoVehicleId") is None
            else str(_get(body, "category.jatoVehicleId"))),
        "trim_grade_name": _get(body, "category.gradeName"),
        "displacement_cc": _int(_get(body, "spec.displacement")),
        "mileage_detail_km": _int(_get(body, "spec.mileage")),
        "color_ext_detail": _get(body, "spec.colorName"),
        "fuel_detail": _get(body, "spec.fuelName"),
        "trade_type": _get(body, "spec.tradeType"),
        "options_standard_json": _json(_get(body, "options.standard")),
        "options_choice_json": _json(_get(body, "options.choice")),
        "options_etc_json": _json(_get(body, "options.etc")),
        "options_tuning_json": _json(_get(body, "options.tuning")),
        "seizing_cnt": _int(_get(body, "condition.seizing.seizingCount")),
        "pledge_cnt": _int(_get(body, "condition.seizing.pledgeCount")),
        "has_record": _bool(_get(body, "condition.accident.recordView")),
        "has_resume": _bool(_get(body, "condition.accident.resumeView")),
        "inspection_formats_json": _json(
            _get(body, "condition.inspection.formats")),
        "price_detail_won": _won(_get(body, "advertisement.price")),
        "diagnosis_car": _bool(_get(body, "advertisement.diagnosisCar")),
        "site_pass_type": _get(body, "advertisement.encarPassType"),
        "site_pass_grade": _get(body, "advertisement.encarPassCategoryType"),
        "warranty_extend": _get(body, "advertisement.extendWarranty"),
        "warranty_deemed": _get(body, "advertisement.deemedExtendWarranty"),
        "photo_underbody_json": _json(_get(body, "advertisement.underBodyPhotos")),
        "site_diagnosis_grade": _get(body, "view.encarDiagnosis"),
        # E등급 절대조건 근거 (STEP 82).  키 이름은 leaseRentInfo 다 — lease 가 아니다
        "advertisement_type": _get(body, "advertisement.advertisementType"),
        "lease_rent_info_json": _json(_get(body, "advertisement.leaseRentInfo")),
        "reg_at": _get(body, "manage.registDateTime"),
        "first_ad_at": _get(body, "manage.firstAdvertisedDateTime"),
        "modify_at": _get(body, "manage.modifyDateTime"),
        "is_dummy": _bool(_get(body, "manage.dummy")),
        "paired_source_id": (
            None if _get(body, "manage.dummyVehicleId") is None
            else str(_get(body, "manage.dummyVehicleId"))),
        "view_cnt": _int(_get(body, "manage.viewCount")),
        "subscribe_cnt": _int(_get(body, "manage.subscribeCount")),
        # ★ 상호(firm.name)와 실명(dealer.name)은 다른 값이다.
        #   원문에서 나뉘어 온다 — v1 이 한 컬럼에 섞었을 뿐이다 (STEP 35).
        #   실명은 CORE 가 아니라 core_dealer_pii 로 간다
        "_pii_dealer_name": _get(body, "partnership.dealer.name"),
        "dealer_shop": firm.get("name"),
        "dealer_shop_code": (
            None if firm.get("code") is None else str(firm.get("code"))),
        # 사이트 원문 ID.  대리키는 resolve_dealer_id 가 만든다 (STEP 30)
        "_site_dealer_id": (
            None if firm.get("code") is None else str(firm.get("code"))),
        "_pii_dealer_phone": _get(body, "contact.no"),
        "_pii_dealer_address": _get(body, "contact.address"),
        "ad_body_text": _get(body, "contents.text"),
        "vin": clean_vin(body.get("vin")),
        "_pii_plate_no": body.get("vehicleNo"),
        "row_status": "ok",
    }


# ── STEP 21 inspection ───────────────────────────────────────────────
def parse_inspection(body: dict, site: str, source_id: str) -> dict:
    """점검부 → core_inspection.

    ★ outers 는 요소 원문 그대로 배열로 저장한다.  가공하지 않는다.
      골격/외판 해석은 7장 Analyzer 가 attributes(RANK_*) 로 한다 (STEP 44).
      v1 은 outers[].children[].statusType 이라는 존재하지 않는 경로를 읽었다.
    """
    d = _get(body, "master.detail") or {}
    return {
        "site": site,
        "source_id": str(source_id),
        "inspection_vin": clean_vin(d.get("vin")),
        "inspection_mileage_km": _int(d.get("mileage")),
        "first_registration_date": _date10(d.get("firstRegistrationDate")),
        "inspection_valid_from": _date10(d.get("validityStartDate")),
        "inspection_valid_to": _date10(d.get("validityEndDate")),
        "inspection_issued_at": _date10(d.get("issueDate")),
        "check_engine": d.get("engineCheck"),
        "check_transmission": d.get("trnsCheck"),
        "motor_type_code": d.get("motorType"),
        "inspection_comment": d.get("comments"),
        # 원문 철자가 accdient 다.  고치지 않는다
        "inspection_accident_flag": _get(body, "master.accdient"),
        "inspection_simple_repair": _get(body, "master.simpleRepair"),
        "inspection_flood": d.get("waterlog"),
        "inspection_tuning": d.get("tuning"),
        "inspection_recall": d.get("recall"),
        # ★ usageChangeTypes 는 record 가 아니라 점검부 master.detail 에 있다.
        #   v1 은 record 에서 찾다가 「존재하지 않는 필드」로 금지했다 (STEP 21a)
        #   렌트 판정 근거다 (7장 STEP 78)
        "usage_change_types_json": _json(d.get("usageChangeTypes")),
        "inspection_panel_json": _json(body.get("outers")),
        "inspection_inner_json": _json(body.get("inners")),
        "inspection_etc_json": _json(body.get("etcs")),
        "inspection_image_json": _json(body.get("images")),
        "row_status": "ok",
    }


# ── STEP 21a record ──────────────────────────────────────────────────
def parse_record(body: dict, site: str, source_id: str) -> dict:
    """이력 → core_record.

    ★ accidents[] 는 원문 그대로 저장한다.
      type 해석·금액 합산은 7장 Analyzer 가 한다 (STEP 77).
    금지   파싱 단계에서 type 을 합산하거나 필터링하는 것
    ★ fuel · maker 는 저장하되 분류에 쓰지 않는다 (STEP 43 · BANNED_SOURCES)
    """
    # notJoinDate 는 1~5 로 고정된 필드명이다.  임계값이 아니라 원문 구조다
    not_join = [body.get(f"notJoinDate{i}") for i in NOT_JOIN_INDEXES]
    return {
        "site": site,
        "source_id": str(source_id),
        "_pii_record_plate_no": body.get("carNo"),
        "record_first_date": _date10(body.get("firstDate")),
        "record_reg_date": _date10(body.get("regDate")),
        "record_open": body.get("openData"),
        "accident_my_cnt": _int(body.get("myAccidentCnt")),
        "accident_my_cost": _int(body.get("myAccidentCost")),
        "accident_other_cnt": _int(body.get("otherAccidentCnt")),
        "accident_other_cost": _int(body.get("otherAccidentCost")),
        "accident_total_cnt": _int(body.get("accidentCnt")),
        "accidents_json": _json(body.get("accidents")),
        "owner_change_cnt": _int(body.get("ownerChangeCnt")),
        "owner_change_dates_json": _json(body.get("ownerChanges")),
        "plate_change_cnt": _int(body.get("carNoChangeCnt")),
        "_pii_plate_history_json": _json(body.get("carInfoChanges")),
        "total_loss_cnt": _int(body.get("totalLossCnt")),
        "total_loss_date": _date10(body.get("totalLossDate")),
        "flood_total_cnt": _int(body.get("floodTotalLossCnt")),
        "flood_part_cnt": _int(body.get("floodPartLossCnt")),
        "flood_date": _date10(body.get("floodDate")),
        "robber_cnt": _int(body.get("robberCnt")),
        "robber_date": _date10(body.get("robberDate")),
        "use_gov": body.get("government"),
        "use_business": body.get("business"),
        "loan_cnt": _int(body.get("loan")),
        "use_cd": body.get("use"),
        "use1_json": _json(body.get("carInfoUse1s")),
        "use2_json": _json(body.get("carInfoUse2s")),
        "not_join_json": _json(not_join),
        "record_fuel": body.get("fuel"),
        "record_maker": body.get("maker"),
        "row_status": "ok",
    }


# ── STEP 19a 필드 단위 실패 ──────────────────────────────────────────
# ★ 필드 하나를 못 읽어도 나머지가 저장되게 한다.
#   한 필드 오류로 매물 전체가 사라지면 그 매물의 다른 16축도 못 본다
REASON_NOT_PROVIDED = "not_provided"
REASON_PARSE_ERROR = "parse_error"
REASON_TYPE_MISMATCH = "type_mismatch"

def _sample_chars(root: str = ".") -> int:
    """표본 길이.  정책이라 config 다 (V4-13)."""
    import os

    here = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    with open(os.path.join(here, "config", "scoring.json"),
              encoding="utf-8") as f:
        return int(json.load(f)["validation"]["parse_sample_chars"])


SAMPLE_CHARS = _sample_chars()


def safe_field(fn, body, path: str, issues: list, endpoint: str):
    """필드 하나를 읽는다.  실패하면 그 필드만 NULL 이고 사유를 남긴다.

    금지   필드 하나의 예외가 매물 파싱을 중단시키는 것
    반환   값 (실패면 None).  issues 에 (endpoint, path, reason, 표본) 추가
    """
    try:
        value = fn(body)
    except (TypeError, ValueError) as e:
        issues.append((endpoint, path, REASON_TYPE_MISMATCH,
                       f"{type(e).__name__}: {e}"[:SAMPLE_CHARS]))
        return None
    except Exception as e:                                    # noqa: BLE001
        issues.append((endpoint, path, REASON_PARSE_ERROR,
                       f"{type(e).__name__}: {e}"[:SAMPLE_CHARS]))
        return None
    if value is None:
        # 사이트가 안 준 것이다.  결함이 아니다
        issues.append((endpoint, path, REASON_NOT_PROVIDED, None))
    return value


def parse_with_issues(parser, body, site: str, source_id,
                      endpoint: str) -> tuple[dict, list]:
    """파서를 돌리되, 죽지 않게 감싼다 (STEP 19a).

    파서 전체가 죽으면 그 매물이 사라진다 — 그때도 CORE 행은 남긴다.
    """
    issues: list = []
    try:
        return parser(body, site, source_id), issues
    except Exception as e:                                    # noqa: BLE001
        issues.append((endpoint, "(전체)", REASON_PARSE_ERROR,
                       f"{type(e).__name__}: {e}"[:SAMPLE_CHARS]))
    # ★ 전체가 죽어도 살아남은 필드는 건진다 (STEP 19a · A-1).
    #   한 필드 오류로 매물이 통째로 사라지면 그 매물의 다른 16축도 못 본다.
    #   실측: originPrice 를 "사천만원" 으로 바꾸자 남은 필드가 2개였다
    return _salvage(parser, body, site, source_id, endpoint, issues), issues


def _salvage(parser, body, site: str, source_id, endpoint: str,
             issues: list) -> dict:
    """필드를 하나씩 빼며 다시 돌려, 죽이는 필드만 골라낸다.

    ★ 원문 최상위 키 단위로 본다.  깊은 경로까지 파고들지 않는다 —
      비용이 지수로 늘고, 어차피 사람이 볼 것은 「어느 블록이 깨졌나」다
    금지   추정으로 기본값을 넣는 것.  못 읽은 것은 없는 것이다
    """
    out = {"site": site, "source_id": str(source_id)}
    if not isinstance(body, dict):
        return out

    # ★ 「죽이는 키 하나」를 고르려 하지 않는다.  두 블록이 같은 자리에서
    #   같은 예외를 내면 문구로도 위치로도 구분이 안 된다 (실측 08-15 · A-6).
    #   살아날 때까지 빼고, 그 뒤에 무고한 키를 되돌려 넣는다
    trimmed = dict(body)
    dropped: list = []
    for key in list(body):
        if _parses(parser, trimmed, site, source_id):
            break
        trimmed.pop(key, None)
        dropped.append(key)
    if not _parses(parser, trimmed, site, source_id):
        return out                    # 다 빼도 안 산다 — 더는 못 한다

    # 되돌려 넣기 — 안 죽이는 키는 살린다.  ★ 무고한 블록을 버리지 않는다
    guilty = []
    for key in dropped:
        probe = dict(trimmed)
        probe[key] = body[key]
        if _parses(parser, probe, site, source_id):
            trimmed = probe
        else:
            guilty.append(key)

    got = parser(trimmed, site, source_id)
    for key in guilty:
        issues.append((endpoint, key, REASON_PARSE_ERROR, None))
    for k, v in got.items():
        out.setdefault(k, v)
    return out


def _parses(parser, body: dict, site: str, source_id) -> bool:
    try:
        parser(body, site, source_id)
    except Exception:                                         # noqa: BLE001
        return False
    return True
# ── STEP 19b 안전 조회 · 타입 정규화 ─────────────────────────────────
def dig(node, path: str, default=None):
    """중간 노드가 null 이어도 죽지 않는다.

    ★ raw["partnership"]["dealer"]["firm"]["name"] 은 중간이 None 이면 죽는다.
      그 매물 전체가 사라져 다른 16축도 못 본다 (STEP 19a).
    금지   중간 노드 존재를 전제한 연쇄 접근
    """
    cur = node
    for part in path.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        elif isinstance(cur, list):
            try:
                cur = cur[int(part)]
            except (ValueError, IndexError):
                return default
        else:
            return default
        if cur is None:
            return default
    return cur


def as_list(value) -> list:
    """배열 필드를 배열로 만든다.

    ★ 사이트가 같은 필드를 str 로 줄 때가 있다.
      문자열을 그대로 순회하면 글자 하나하나가 값이 되어 사전이 오염된다.
    None → []   ·   str → [str]   ·   list → list   ·   그 외 → [값]
    """
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, (str, int, float, bool)):
        return [value]
    return list(value)


# ── 진단 리포트 (2장 STEP 21b) ───────────────────────────────────────
# ★ 판정 근거가 아니라 표시용이다.
#   진단 items 의 교환 부위가 성능점검부 outers 와 전건 일치한다 (582건 확인).
#   같은 사실을 두 축으로 세면 중복 감점이 된다 — history.damage 는 outers 로만 한다
DIAG_CHECKER_CODE = "006039"      # 판정 문장.  「외부패널 단순교환 차량」 등
DIAG_PANEL_CODE = "006040"        # 외판 상세
DIAG_NORMAL, DIAG_REPLACEMENT = "NORMAL", "REPLACEMENT"

# 진단이 없는 것이 정답인 값.  404 를 결과로 처리해도 된다 (STEP 21b)
DIAG_GRADE_NONE = -1


def _diag_comment(items: list, code: str) -> str | None:
    for it in items:
        if isinstance(it, dict) and it.get("code") == code:
            return it.get("result")
    return None


def parse_diagnosis(body: dict, site: str, source_id: str) -> dict:
    """진단 → core_diagnosis.

    ★ items 는 원문 그대로 저장한다.  부위별 결과를 컬럼으로 펴지 않는다.
      전건 10개 고정이지만, 고정을 전제하면 늘었을 때 조용히 잘린다 (STEP 32)
    금지   items[].resultCode 로 사고 판정을 하는 것.  outers 와 겹친다
    """
    items = as_list(body.get("items"))
    # ★ 소견(resultCode null)은 부위 판정이 아니다.  집계에서 뺀다
    judged = [i for i in items
              if isinstance(i, dict) and i.get("resultCode")]
    return {
        "site": site,
        "source_id": str(source_id),
        "diagnosis_no": dig(body, "diagnosisNo"),
        "diagnosed_at": dig(body, "realDiagnosisDate"),
        "center_code": dig(body, "centerCode"),
        "center_name": dig(body, "reservationCenterName"),
        "item_count": len(judged),
        "replacement_count": sum(1 for i in judged
                                 if i["resultCode"] == DIAG_REPLACEMENT),
        "normal_count": sum(1 for i in judged
                            if i["resultCode"] == DIAG_NORMAL),
        "checker_comment": _diag_comment(items, DIAG_CHECKER_CODE),
        "outer_panel_comment": _diag_comment(items, DIAG_PANEL_CODE),
        # ★ core_diagnosis.row_status 는 NOT NULL 이다 (3장 STEP 35).
        #   다른 파서 셋은 내는데 여기만 빠져 있었다 — 실물 진단이 처음
        #   들어온 08-16 에 S6 이 통째로 죽었다 (IntegrityError)
        "row_status": "ok",
    }


def parse_diagnosis_items(body: dict) -> list[dict]:
    """부위별 판정 → core_diagnosis_item.  ★ 소견은 뺀다 (STEP 35)."""
    return [{"item_code": i["code"], "part_name": i["name"],
             "result_code": i["resultCode"], "result_text": i.get("result")}
            for i in as_list(body.get("items"))
            if isinstance(i, dict) and i.get("resultCode")]


def _text(value) -> str | None:
    """문자열로 남긴다.  ★ 빈 문자는 None 이 아니다 — 「없음」과 「못 받음」은 다르다"""
    if value is None:
        return None
    got = str(value).strip()
    return got or None


# ── 개정 296·297 로 늘어난 원문 (docs/ENCAR_API.md) ──────────────────
# ★ 원문에 있는 것만 넣는다.  추정하지 않는다 (OVERNIGHT ③)
def parse_record_summary(body: dict, site: str, source_id: str) -> dict:
    """보험이력 요약 → core_listing 보강.

    ★ 용도(use) · 특수 사고이력(전손 · 침수 · 도난) · 소유자 변경 · 저당.
      우리가 advertisementType 으로만 보던 렌트가 여기 명시돼 있다 (개정 296 §4)
    """
    def num(v):
        try:
            return int(v)
        except (TypeError, ValueError):
            return None

    return {
        "record_use_code": _text(body.get("use")),
        "owner_change_cnt_summary": num(body.get("ownerChangeCnt")),
        "total_loss_cnt_summary": num(body.get("totalLossCnt")),
        "flood_total_cnt_summary": num(body.get("floodTotalLossCnt")),
        "flood_part_cnt_summary": num(body.get("floodPartLossCnt")),
        "robber_cnt_summary": num(body.get("robberCnt")),
        "loan_flag": num(body.get("loan")),
        "business_flag": num(body.get("business")),
        "government_flag": num(body.get("government")),
        "row_status": "ok",
    }


def parse_platform_check(body: dict, site: str, source_id: str) -> dict:
    """엔카 클린 판정.  ★ 플랫폼이 책임지는 판정이다 (개정 297 §2)."""
    got = body.get("cleaned")
    return {"platform_verified": 1 if got is True else 0 if got is False else None,
            "row_status": "ok"}


def parse_inspection_summary(body: dict, site: str, source_id: str) -> dict:
    """성능점검 요약 — 점검자 이름.  ★ 누가 점검했는지가 신뢰의 근거다."""
    return {"inspector_name": _text(body.get("inspName")), "row_status": "ok"}


def parse_ev_battery(body: dict, site: str, source_id: str) -> dict:
    """전기차 배터리 진단 (개정 296).

    ★ 08-16 에는 전건 null 이라 「있다/없다」만 남겼다.
      08-17 재수집에 실제 진단이 들어왔다 — SOH 93.9 · 등급 SS.
      「있다」만 남기면 그 값을 버리는 것이다
    """
    summary = ((body.get("ensolRawInfo") or {}).get("summaryInfo") or {})
    soh = summary.get("soh")
    got = any(body.get(k) for k in
              ("ensolRawInfo", "jatoBatteryInfo", "encarComputedInfo"))
    return {"ev_battery_known": 1 if got else 0,
            # ★ SOH 는 「배터리가 얼마나 남았나」다.  전기차의 주행거리에 해당한다
            "ev_battery_soh": float(soh) if soh is not None else None,
            "ev_battery_grade": _text(summary.get("sohGrade")),
            "ev_battery_checked_at": _text(
                summary.get("diagnosisCompletedDate")),
            "row_status": "ok"}


def parse_sellingpoint(body: dict, site: str, source_id: str) -> dict:
    """판매 포인트.  ★ 표시용이다.  판정에 쓰지 않는다."""
    sp = body.get("sellingPoint")
    name = None
    if isinstance(sp, dict):
        name = sp.get("smallCategoryName") or sp.get("mediumCategoryName")
    return {"selling_point": _text(name), "row_status": "ok"}
