# -*- coding: utf-8 -*-
"""CORE 저장소 (L4).  사이트 무관 공통 스키마.

지시서   3장 STEP 29 (이력 보존) · STEP 30 (키 체계) · STEP 31 (공통 컬럼)
         STEP 32 (NULL 3종) · STEP 34 (설계 원칙)
근거     전량 스냅샷을 쌓지 않는다.  변하는 것은 가격과 게시 상태뿐이다.
금지     불변 필드가 바뀌었을 때 원인 분류 없이 새 값으로 덮어쓰는 것.
         빈 컨테이너를 NULL 로 저장하는 것 — v1 은 `_js()` 가 falsy 를 전부
         None 으로 만들어 「없음」이 「실패」로 저장됐고 분모가 부풀려졌다.
"""
from __future__ import annotations

import json
import sqlite3

from contracts import ListingSnapshot
from errors import ValidationError
from store.raw import commit

# 변하는 것만 추적한다 (STEP 29).  좁게 잡는다.
TRACKED_FIELDS: tuple[str, ...] = ("price_current_won", "sales_status", "status")

# 이것이 바뀌면 변경 이력이 아니라 검증 실패다 (STEP 29 · 6장 V2).
INVARIANT_FIELDS: tuple[str, ...] = (
    "displacement_cc",
    "year_month",
    "form_year",
    "trim_badge",
    "color_ext_raw",
    "vin",
    "plate_hash",
)


def resolve_listing_id(conn: sqlite3.Connection, site: str, source_id: str,
                       at: str) -> int:
    """자연키 (site, source_id) → 대리키 listing_id (STEP 30).

    ★ PK 를 문자열로 조립하지 않는다.  사이트가 ID 체계를 바꿔도 흔들리지 않는다
    """
    row = conn.execute(
        "SELECT listing_id FROM core_listing WHERE site=? AND source_id=?",
        (site, source_id)).fetchone()
    if row:
        return row[0]
    cur = conn.execute(
        "INSERT INTO core_listing(site,source_id,status,first_seen,last_seen,"
        "row_status) VALUES (?,?,'new',?,?,'ok')", (site, source_id, at, at))
    commit(conn)
    return cur.lastrowid


def resolve_dealer_id(conn: sqlite3.Connection, site: str,
                      site_dealer_id: str, at: str) -> int:
    """자연키 (site, site_dealer_id) → 대리키 dealer_id."""
    row = conn.execute(
        "SELECT dealer_id FROM core_dealer WHERE site=? AND site_dealer_id=?",
        (site, site_dealer_id)).fetchone()
    if row:
        return row[0]
    cur = conn.execute(
        "INSERT INTO core_dealer(site,site_dealer_id,listing_count,"
        "sample_sufficient,calculated_at) VALUES (?,?,0,0,?)",
        (site, site_dealer_id, at))
    commit(conn)
    return cur.lastrowid


def serialize_container(value) -> str | None:
    """빈 컨테이너는 그대로 직렬화한다.  None 은 「없었다」일 때만이다 (STEP 32).

    금지   if not v: return None
    검증   '[]' 건수 + NULL 건수 = 전체.  '[]' 가 0건이면 이 버그를 의심한다 (V2-06)
    """
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def record_change(
    conn: sqlite3.Connection,
    listing_id: str,
    field: str,
    old,
    new,
    changed_at: str,
    change_kind: str,
    cause: str | None = None,
) -> None:
    """변경 1건을 적재한다.  삭제하지 않는다."""
    conn.execute(
        "INSERT OR REPLACE INTO core_listing_change"
        "(listing_id,changed_at,field,old_value,new_value,change_kind,cause)"
        " VALUES (?,?,?,?,?,?,?)",
        (listing_id, changed_at, field,
         None if old is None else str(old),
         None if new is None else str(new),
         change_kind, cause),
    )


def split_pii(conn: sqlite3.Connection, parsed: dict, site: str,
              key: bytes, at: str) -> dict:
    """PII 를 떼어내고 해시만 남긴다 (STEP 35).

    순서   1 split_pii     PII 를 떼어 보관.  CORE 딕셔너리에서 제거
          2 resolve_*_id  대리키 확정
          3 flush_pii     확정된 대리키로 저장
    필수   1 에서 뗀 값이 CORE 로 새지 않는다.  같은 딕셔너리를 재사용하지 않는다
    필수   2 가 실패하면 3 을 하지 않는다.  PII 만 남는 고아를 만들지 않는다 (V2-17)
    반환   CORE 에 넣을 새 dict.  입력을 변경하지 않는다
    """
    import json as _json

    from store.pii import (
        hash_list, plate_hash, plate_use_char, save_dealer_pii, save_listing_pii,
    )

    out = {k: v for k, v in parsed.items() if not k.startswith("_pii_")}
    lid = parsed.get("listing_id")
    plate = parsed.get("_pii_plate_no")
    if plate is not None:
        out["plate_hash"] = plate_hash(plate, key)
        if lid:
            save_listing_pii(conn, lid, plate, None, at)

    # ★ 번호판이 세 가지에 쓰인다 (STEP 35).  하나만 빼면 나머지가 죽는다
    rec = parsed.get("_pii_record_plate_no")
    if rec is not None:
        out["record_plate_hash"] = plate_hash(rec, key)
        out["plate_use_char"] = plate_use_char(rec)
        if lid:
            save_listing_pii(conn, lid, None, None, at, record_plate_no=rec)
    hist = parsed.get("_pii_plate_history_json")
    if hist is not None:
        out["plate_history_hash_json"] = _json.dumps(
            hash_list(_json.loads(hist), key), ensure_ascii=False)
        if lid:
            save_listing_pii(conn, lid, None, hist, at)
    # ★ 딜러 PII 는 대리키가 정해진 뒤 저장한다.  키 단위가 다르다 (STEP 35)
    out["_pii_dealer"] = (parsed.get("_pii_dealer_name"),
                          parsed.get("_pii_dealer_phone"),
                          parsed.get("_pii_dealer_address"))
    out["_site_dealer_id"] = parsed.get("_site_dealer_id")
    _ = save_dealer_pii
    return out


def flush_dealer_pii(conn: sqlite3.Connection, dealer_id: int,
                     payload: tuple, at: str) -> None:
    from store.pii import save_dealer_pii

    if any(payload):
        save_dealer_pii(conn, dealer_id, payload[0], payload[1], payload[2], at)


# 컬럼이 아닌 것이 정상인 키.  ★ 접두로 판별한다 — 늘어나도 안 깨진다
DROP_ALLOW_PREFIX = ("_pii_", "_site_")


def _record_dropped(conn: sqlite3.Connection, parsed: dict, cols,
                    at: str) -> None:
    """★ 버려지는 키를 센다 (A-2 · V2-29).

    파서가 새 필드를 내도 컬럼이 없으면 조용히 사라진다.
    등록부가 그것을 못 보면 「원문에 새 필드가 왔다」를 영영 모른다
    """
    known = set(cols)
    dropped = [k for k in parsed
               if k not in known and not k.startswith(DROP_ALLOW_PREFIX)]
    for key in dropped:
        conn.execute(
            "INSERT OR IGNORE INTO meta_field_usage"
            "(site,endpoint,json_path,usage,reason,miss_streak,"
            " first_seen,last_seen) VALUES (?,?,?,?,?,0,?,?)",
            (parsed.get("site", "encar"), "core", key, "unclassified",
             "upsert 가 버린 키 — 컬럼이 없다", at, at))


# 같은 필드가 이만큼 동시에 바뀌면 사이트 스키마 변경이다 (STEP 29 ④)
SCHEMA_CHANGE_MIN = 5


# 불변 필드 → 목록 원문의 키.  ★ 여기 없는 필드는 기계가 분류하지 못한다
INVARIANT_SOURCE_KEY = {
    "trim_badge": "Badge",
    "year_month": "Year",
    "form_year": "FormYear",
    "color_ext_raw": "Color",
}

CAUSE_PARSE = "parse_error"        # ① 같은 원문을 다시 읽으면 이전 값이 나온다
CAUSE_SOURCE_EDIT = "source_edit"  # ② 원문이 실제로 바뀌었다 (딜러 오기입 정정)
CAUSE_REPLACED = "listing_replaced"  # ③ source_id 재사용 · vin/plate 불일치
CAUSE_SCHEMA = "site_schema_change"  # ④ 여러 매물에서 동시 발생


def classify_invariant_change(conn, lid: str, field: str, old, new,
                              parsed: dict, observed_at: str) -> str:
    """불변 필드가 바뀐 원인을 규격의 판별 순서대로 가른다 (STEP 29).

    판별 순서   ① 이전 원문과 현재 원문을 비교한다  → 같으면 ① 다르면 ②③④
               ② 동시 발생 건수를 본다            → 다수면 ④
               ③ vin · plate 를 대조한다          → 불일치면 ③
    ★ 사람이 아니라 이 순서가 분류한다.  다만 수용은 ②만이다
    금지   원인 분류 없이 새 값으로 덮어쓰는 것
    """
    # ③ 먼저 걸러 낸다 — 다른 차면 원문 비교가 뜻이 없다
    for key in ("vin", "plate_hash"):
        a, b = parsed.get(key), _current(conn, lid, key)
        if a and b and a != b:
            return CAUSE_REPLACED
    # ④ 같은 필드가 이번 실행에 여럿 바뀌었는가
    n = conn.execute(
        "SELECT COUNT(DISTINCT listing_id) FROM core_listing_change"
        " WHERE field = ? AND change_kind = 'invariant_violation'"
        " AND changed_at >= ?", (field, _today(parsed))).fetchone()[0]
    if n >= SCHEMA_CHANGE_MIN:
        return CAUSE_SCHEMA
    # ① 이전 원문을 실제로 읽어 본다.  ★ 못 읽으면 분류하지 않는다 —
    #   「모르는 것을 ②로 두면」 이 가드가 있으나 마나 해진다
    key = INVARIANT_SOURCE_KEY.get(field)
    if key is None:
        return ""
    got = _source_history(conn, parsed.get("source_id"), key)
    if len(got) < 2:
        return ""                      # 견줄 원문이 하나뿐이다.  사람이 봐야 한다
    before, now = got[-2][1], got[-1][1]
    if str(before) == str(now):
        # 원문은 안 바뀌었는데 값이 달라졌다 — 우리가 잘못 읽고 있었다
        return CAUSE_PARSE
    if str(before) == str(old) and str(now) == str(new):
        # 원문이 실제로 바뀌었다 (딜러 오기입 정정) — 규격 ②
        return CAUSE_SOURCE_EDIT
    return ""                          # 어느 쪽도 아니다.  사람이 봐야 한다


def _lookback() -> int:
    """이전 원문을 몇 봉투까지 거슬러 찾는가 (STEP 29 ①).

    ★ 임계값은 config 다 (V4-13).  하루 395쪽이라 이틀치를 덮어야 한다
    """
    import json as _json
    import os as _os

    root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    with open(_os.path.join(root, "config", "web.json"),
              encoding="utf-8") as f:
        return int(_json.load(f)["invariant_source_lookback"])


def _source_history(conn, source_id, key: str) -> list:
    """그 매물이 나온 목록 원문을 시각순으로 (봉투 시각, 값) (STEP 29 ①).

    ★ 원문을 다시 읽는다.  「우리가 저장한 값」과 견주면 순환이다
    ★ 같은 봉투 묶음에서 여러 번 나오면 한 번만 센다 — 쪽이 여럿이다
    """
    import json as _json

    if not source_id:
        return []
    out: dict = {}
    for at, body in conn.execute(
        "SELECT fetched_at, body FROM raw_response"
        " WHERE endpoint='list' AND status='ok'"
        " ORDER BY id DESC LIMIT ?", (_lookback(),)
    ):
        try:
            doc = _json.loads(body)
        except (ValueError, TypeError):
            continue
        for item in doc.get("SearchResults") or []:
            if str(item.get("Id")) == str(source_id):
                out.setdefault(at[:10], (at, item.get(key)))
    return [v for _k, v in sorted(out.items())]


def _current(conn, lid: str, key: str):
    row = conn.execute(f"SELECT {key} FROM core_listing WHERE listing_id = ?",
                       (lid,)).fetchone()
    return row[0] if row else None


def _today(parsed: dict) -> str:
    return (parsed.get("last_seen") or parsed.get("first_seen") or "")[:10]


def upsert_core(conn: sqlite3.Connection, parsed: dict, observed_at: str) -> int:
    """파싱 결과를 core_listing 에 적재한다.

    반환   기록된 변경 건수
    금지   불변 필드 변경을 조용히 덮어쓰는 것.  원인을 분류한 뒤 판정한다 (STEP 29)
           원인 분류는 6장 STEP 58 이 한다.  여기서는 감지하고 남긴다
    금지   컬럼에 없는 키를 조용히 버리는 것 (A-2).
           파서가 새 필드를 내도 아무도 모른다 — 세어서 남긴다
    금지   라벨과 내용 형식이 어긋난 값을 저장하는 것 (0장 불변식 ④).
           「주행거리」 자리에 날짜가 오면 그것은 파싱이 아니라 우연이다
    """
    from contracts import shape_violations

    bad = shape_violations(parsed)
    if bad:
        raise ValidationError(
            f"라벨과 내용 형식이 어긋난다: {', '.join(bad[:3])}",
            step="0장 불변식 ④")
    lid = parsed["listing_id"]
    cols = [r[1] for r in conn.execute("PRAGMA table_info(core_listing)")]
    cur = conn.execute(
        "SELECT * FROM core_listing WHERE listing_id = ?", (lid,)
    ).fetchone()
    changes = 0
    if cur is None:
        raise ValidationError("listing_id 미해결. resolve_listing_id 를 먼저 부른다",
                              step="STEP 30")
    old = dict(zip(cols, cur, strict=True))
    _record_dropped(conn, parsed, cols, observed_at)
    if old.get("status") == "new" and old.get("price_current_won") is None:
        # resolve_listing_id 가 만든 빈 행이다.  첫 적재로 채운다
        payload = {k: parsed.get(k) for k in cols
                   if k in parsed and k != "listing_id"}
        payload["last_seen"] = observed_at
        payload.setdefault("status", "new")
        sets = ",".join(f"{k}=?" for k in payload)
        conn.execute(f"UPDATE core_listing SET {sets} WHERE listing_id = ?",
                     [*payload.values(), lid])
        record_change(conn, lid, "status", None, payload["status"],
                      observed_at, "new")
        commit(conn)
        return 1

    for field in INVARIANT_FIELDS:
        if field not in parsed:
            continue
        if old.get(field) is not None and parsed[field] is not None \
                and old[field] != parsed[field]:
            cause = classify_invariant_change(conn, lid, field, old[field],
                                              parsed[field], parsed,
                                              observed_at)
            record_change(conn, lid, field, old[field], parsed[field],
                          observed_at, "invariant_violation",
                          cause=cause or None)
            commit(conn)
            if cause == CAUSE_SOURCE_EDIT:
                # ★ 원문이 실제로 바뀌었다 (딜러 오기입 정정).
                #   조치는 「변경 수용 · 이력 기록」이다 (STEP 29 ②)
                continue
            raise ValidationError(
                f"불변 필드 변경: {field} {old[field]!r} → {parsed[field]!r} "
                f"— 원인 {cause or '분류 못 함'}. 이 원인은 사람이 봐야 한다",
                listing_id=lid,
                step="STEP 29",
            )

    for field in TRACKED_FIELDS:
        if field in parsed and old.get(field) != parsed[field]:
            kind = "price" if field == "price_current_won" else "status"
            record_change(conn, lid, field, old.get(field), parsed[field],
                          observed_at, kind)
            changes += 1

    payload = {k: parsed.get(k) for k in cols
               if k in parsed and k != "listing_id"}
    payload["last_seen"] = observed_at
    sets = ",".join(f"{k}=?" for k in payload)
    conn.execute(
        f"UPDATE core_listing SET {sets} WHERE listing_id = ?",
        [*payload.values(), lid],
    )
    commit(conn)
    return changes


def mark_gone(conn: sqlite3.Connection, listing_id: str, at: str) -> None:
    """목록에서 사라져도 삭제하지 않는다.  gone_at 이 「얼마에 팔렸나」의 근거다."""
    cur = conn.execute(
        "SELECT status, price_current_won FROM core_listing WHERE listing_id = ?",
        (listing_id,),
    ).fetchone()
    if cur is None or cur[0] == "gone":
        return
    conn.execute(
        "UPDATE core_listing SET status='gone', gone_at=?, last_price_won=? "
        "WHERE listing_id = ?",
        (at, cur[1], listing_id),
    )
    record_change(conn, listing_id, "status", cur[0], "gone", at, "gone")
    commit(conn)


def load_snapshot(conn: sqlite3.Connection, listing_id: str) -> ListingSnapshot:
    """core_* 조인 → DTO.  Row 를 상위 계층으로 넘기지 않는다 (0장 STEP 1).

    core_diagnosis 는 아직 없다 (STEP 35).  진단은 core_listing.diagnosis_car 로만 온다.
    """
    row = conn.execute(
        "SELECT l.*, i.first_registration_date, i.inspection_panel_json,"
        " i.inspection_flood,"
        " r.flood_total_cnt, r.flood_part_cnt, r.total_loss_cnt,"
        " r.accident_my_cost, r.accident_my_cnt, r.accident_other_cnt,"
        " r.owner_change_cnt, r.plate_use_char, r.plate_history_hash_json,"
        " r.not_join_json"
        " FROM core_listing l"
        " LEFT JOIN core_inspection i ON i.listing_id = l.listing_id"
        " LEFT JOIN core_record r ON r.listing_id = l.listing_id"
        " WHERE l.listing_id = ?",
        (listing_id,),
    )
    cols = [d[0] for d in row.description]
    rec = row.fetchone()
    if rec is None:
        raise ValidationError("매물이 없다", listing_id=listing_id, step="STEP 31")
    d = dict(zip(cols, rec, strict=True))

    def jload(key):
        v = d.get(key)
        return None if v is None else json.loads(v)

    return ListingSnapshot(
        listing_id=d["listing_id"],
        site=d["site"],
        target_key=d["target_key"],
        price_current_won=d["price_current_won"],
        price_origin_won=d["price_origin_won"],
        year_month=d["year_month"],
        mileage_km=d["mileage_km"],
        displacement_cc=d["displacement_cc"],
        warranty_body_month=d["warranty_body_month"],
        warranty_body_km=d["warranty_body_km"],
        warranty_power_month=d["warranty_power_month"],
        warranty_power_km=d["warranty_power_km"],
        first_registration_date=d.get("first_registration_date"),
        options_standard=jload("options_standard_json"),
        options_choice=jload("options_choice_json"),
        inspection_panels=jload("inspection_panel_json"),
        # ★ 점검 출처 — TABLE 플랫폼 직영 · IMAGE 판매자 등록 (개정 300 · 306)
        inspection_formats=jload("inspection_formats_json"),
        flood_total_cnt=d.get("flood_total_cnt"),
        flood_part_cnt=d.get("flood_part_cnt"),
        total_loss_cnt=d.get("total_loss_cnt"),
        airbag_deployed=None,  # 원천 미확정 (8장 등록부)
        seizing_cnt=d["seizing_cnt"],
        pledge_cnt=d["pledge_cnt"],
        accident_my_cost=d.get("accident_my_cost"),
        accident_my_cnt=d.get("accident_my_cnt"),
        accident_other_cnt=d.get("accident_other_cnt"),
        inspection_waterlog=d.get("inspection_flood"),
        sales_status=d["sales_status"],
        lease_present=None,  # 7장 STEP 78 이 sell_type · site_* 에서 판정한다
        lease_type=None,
        not_join_json=d.get("not_join_json"),
        owner_change_cnt=d.get("owner_change_cnt"),
        plate_use_char=d.get("plate_use_char"),
        plate_history_hash_json=d.get("plate_history_hash_json"),
        color_ext_raw=d["color_ext_raw"],
        color_ext_hex=d["color_ext_hex"],
        sell_type=d["sell_type"],
        plate_hash=d["plate_hash"],
        ad_body_text=d["ad_body_text"],
        site_flags={
            k: d[k] for k in cols if k.startswith("site_") and d.get(k) is not None
        },
    )


# ── vehicle_id 결합 (STEP 30) ────────────────────────────────────────
# 「1순위니까 바로 확정」이 아니다.  후보를 모으고 증거를 대조한 뒤 확정한다.
KEY_PLATE, KEY_VIN, KEY_SITE = "plate", "vin", "site_id"


def build_identities(plate_hash_value: str | None,
                     plate_history_hashes: list[str] | None,
                     vin: str | None, site_id_hash: str) -> list[tuple]:
    """결합 후보를 우선순위대로 만든다 (STEP 30).

    1순위   차량번호 (변경 이력 포함 — 소유자가 바뀌면 번호가 바뀐다)
    2순위   차대번호   불변.  결합 검증자
    3순위   사이트 ID  위 둘이 없을 때만
    금지    차종·연식·주행거리가 비슷하다는 이유로 같은 차로 묶는 것
    반환    [(kind, value_hash, confidence)]
    """
    from contracts import clean_vin

    out: list[tuple] = []
    if plate_hash_value:
        out.append((KEY_PLATE, plate_hash_value, "confirmed"))
    for h in plate_history_hashes or []:
        out.append((KEY_PLATE, h, "probable"))
    v = clean_vin(vin)  # ★ 형식 위반이면 결합에 쓰지 않는다
    if v:
        out.append((KEY_VIN, v, "confirmed"))
    if not out:
        out.append((KEY_SITE, site_id_hash, "probable"))
    return out


def resolve_vehicle_id(conn: sqlite3.Connection, identities: list[tuple],
                       at: str) -> tuple[int, str, str]:
    """식별자로 vehicle_id 를 찾거나 만든다.

    ★ 식별자는 행이다, 키가 아니다.  번호판이 바뀌면 행이 하나 늘 뿐이다
    반환   (vehicle_id, kind, confidence)
    """
    for kind, value_hash, conf in identities:
        row = conn.execute(
            "SELECT vehicle_id FROM vehicle_identity WHERE kind=? "
            "AND value_hash=?", (kind, value_hash)).fetchone()
        if row:
            vid = row[0]
            break
    else:
        cur = conn.execute(
            "INSERT INTO core_vehicle(site_count,listing_count,first_seen,"
            "last_seen,updated_at) VALUES (0,0,?,?,?)", (at, at, at))
        vid = cur.lastrowid

    for kind, value_hash, conf in identities:
        conn.execute(
            "INSERT INTO vehicle_identity"
            "(vehicle_id,kind,value_hash,confidence,first_seen,last_seen)"
            " VALUES (?,?,?,?,?,?) ON CONFLICT(kind,value_hash) DO UPDATE SET"
            " last_seen=excluded.last_seen",
            (vid, kind, value_hash, conf, at, at))
    commit(conn)
    head = identities[0]
    return vid, head[0], head[2]


def merge_conflict(a_vin: str | None, b_vin: str | None) -> bool:
    """vin 이 양쪽에 있고 불일치하면 결합 취소 (STEP 30 결합 규칙 3).

    형식 위반 값은 없는 것으로 본다 — 6자리끼리 달라도 conflict 가 아니다.
    """
    from contracts import clean_vin

    a, b = clean_vin(a_vin), clean_vin(b_vin)
    return bool(a and b and a != b)


def upsert_vehicle(conn: sqlite3.Connection, vehicle_id: int, at: str) -> None:
    """실물 차량 집계 갱신.  식별자는 vehicle_identity 가 갖는다 (STEP 30).

    ★ 1차에는 site_count 가 전부 1 이다.  그래도 만든다 (STEP 35).
    """
    agg = conn.execute(
        "SELECT COUNT(DISTINCT site), COUNT(*), MIN(price_current_won), "
        "       MAX(price_current_won) FROM core_listing WHERE vehicle_id = ?",
        (vehicle_id,),
    ).fetchone()
    site_count, listing_count, lo, hi = agg
    spread = None if lo is None or hi is None else hi - lo
    conn.execute(
        "UPDATE core_vehicle SET site_count=?, listing_count=?, min_price_won=?,"
        " max_price_won=?, price_spread_won=?, last_seen=?, updated_at=? "
        "WHERE vehicle_id=?",
        (site_count or 0, listing_count or 0, lo, hi, spread, at, at,
         vehicle_id))
    commit(conn)


def upsert_dealer(conn: sqlite3.Connection, site: str, dealer_id: int,
                  fields: dict, run_id: str, at: str) -> None:
    """딜러는 매물의 속성이 아니라 독립 개체다 (STEP 35).

    core_dealer 는 덮어쓰므로 history 에 스냅샷을 남긴다.
    남기지 않으면 「어제 Q1 이던 딜러가 오늘 Q4」를 설명할 수 없다.
    행태 지표(trust_score · quadrant)는 7장 STEP 82c 가 채운다.
    """
    n = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE dealer_id=?",
        (dealer_id,),
    ).fetchone()[0]
    # ★ 실명·연락처·주소는 core_dealer_pii 다.  여기는 상호·지역만 (STEP 35)
    conn.execute(
        "UPDATE core_dealer SET dealer_shop=?, shop_code=?, region=?,"
        " listing_count=?, calculated_at=? WHERE dealer_id=?",
        (fields.get("dealer_shop"), fields.get("dealer_shop_code"),
         fields.get("dealer_region"), n, at, dealer_id),
    )
    conn.execute(
        "INSERT OR REPLACE INTO core_dealer_history"
        "(dealer_id,run_id,observed_at,listing_count,sample_sufficient)"
        " VALUES (?,?,?,?,0)", (dealer_id, run_id, at, n),
    )
    commit(conn)


def upsert_child(conn: sqlite3.Connection, table: str, parsed: dict,
                 parse_version: str, at: str) -> None:
    """core_inspection · core_record 적재.  매물당 1행."""
    cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]
    payload = {k: v for k, v in parsed.items() if k in cols}
    payload["parsed_at"] = at
    payload["parse_version"] = parse_version
    keys = list(payload)
    conn.execute(
        f"INSERT OR REPLACE INTO {table} ({','.join(keys)}) "
        f"VALUES ({','.join('?' * len(keys))})",
        [payload[k] for k in keys],
    )
    commit(conn)


# ── 화면 안내용 집계 (14장 STEP 149) ─────────────────────────────────
def state_counts(conn: sqlite3.Connection) -> dict:
    """★ 조회는 여기서 한다.  화면에 SQL 을 두지 않는다 (V11-01)."""
    def one(sql: str) -> int:
        try:
            return conn.execute(sql).fetchone()[0]
        except sqlite3.Error:
            return 0

    sqls = {
        "listings": "SELECT COUNT(*) FROM core_listing",
        "unclassified": "SELECT COUNT(*) FROM meta_field_usage "
                        "WHERE usage='unclassified'",
        "scores": "SELECT COUNT(*) FROM result_score",
        "not_rated": "SELECT COUNT(*) FROM result_score "
                     "WHERE grade='NOT_RATED'",
        # ★ 목록이 언제 들어왔나 (STEP 136i · 개정 316).
        #   가격 변동은 목록에서 온다 — 목록이 멈추면 변동이 멈춘다
        "list_at": "SELECT COALESCE(MAX(fetched_at),'') FROM raw_response "
                   "WHERE endpoint='list' AND status='ok'",
    }
    # ★ 넷을 한 번에 센다 — 화면 한 쪽의 쿼리 수를 줄인다 (V11-34 · B-2)
    try:
        row = conn.execute(
            "SELECT " + ", ".join(f"({s})" for s in sqls.values())).fetchone()
        return dict(zip(sqls, row, strict=True))
    except sqlite3.Error:
        # 표가 아직 없을 수 있다 — 그때는 하나씩 세고 없는 것만 0 으로 둔다
        return {k: one(s) for k, s in sqls.items()}


def current_versions(conn: sqlite3.Connection) -> dict:
    """화면이 읽은 버전 (STEP 144).  ★ 조회는 저장 계층이 한다."""
    def one(sql: str) -> str:
        try:
            row = conn.execute(sql).fetchone()
            return (row[0] if row and row[0] else "") or ""
        except sqlite3.Error:
            return ""

    # ★ MAX(version) 은 글자 크기다 — 판이 아니다.  실측 08-16:
    #   08-15 시험 행 하나가 남긴 'c3' 가 'c1' 보다 커서 전 화면이 c3 을 현재로
    #   읽었다.  c3 에는 채점이 1건뿐이라 /recommend 후보가 1건이 되고
    #   /listings 3,470행의 등급이 전부 비었다.  'c10' < 'c9' 도 같은 함정이다.
    #   현재 판은 「가장 최근에 쓰인 것」이다 — 시각으로 고른다
    return {
        "calc_version": one("SELECT calc_version FROM result_score"
                            " ORDER BY calculated_at DESC, rowid DESC LIMIT 1"),
        # ★ 화면의 사전판은 「지금 보이는 판정이 쓴 사전」이다.
        #   사전만 고치고 재채점을 안 했으면 옛 사전이 맞다 (선언과 실제의 일치)
        "dict_version": one("SELECT dict_version FROM result_score"
                            " ORDER BY calculated_at DESC, rowid DESC LIMIT 1")
        or one("SELECT MAX(dict_version) FROM dict_enum"),
        "parse_version": one("SELECT parse_version FROM core_listing"
                             " WHERE parse_version <> ''"
                             " ORDER BY parsed_at DESC, rowid DESC LIMIT 1"),
        "run_id": one("SELECT run_id FROM audit_request "
                      "ORDER BY rowid DESC LIMIT 1"),
    }


def diagnosis_of(conn: sqlite3.Connection, listing_id: int) -> dict | None:
    """진단 리포트 1건 (STEP 21b).  없으면 None — 「진단 안 받은 차」다."""
    row = conn.execute(
        "SELECT diagnosed_at, center_name, checker_comment, "
        "outer_panel_comment, item_count, replacement_count "
        "FROM core_diagnosis WHERE listing_id = ?", (listing_id,)).fetchone()
    if row is None:
        return None
    return {"diagnosed_at": row[0], "center_name": row[1],
            "checker_comment": row[2], "outer_panel_comment": row[3],
            "item_count": row[4], "replacement_count": row[5]}


def target_counts(conn: sqlite3.Connection) -> list:
    """차종별 매물 수.  ★ 조회는 여기서 한다 (V11-01)."""
    return [{"target_key": r[0], "count": r[1]} for r in conn.execute(
        "SELECT target_key, COUNT(*) FROM core_listing "
        "WHERE target_key IS NOT NULL GROUP BY 1 ORDER BY 2 DESC")]


def top_target(conn: sqlite3.Connection) -> str | None:
    rows = target_counts(conn)
    return rows[0]["target_key"] if rows else None


def vehicle_of(conn: sqlite3.Connection, listing_id: int) -> int | None:
    row = conn.execute(
        "SELECT vehicle_id FROM core_listing WHERE listing_id = ?",
        (listing_id,)).fetchone()
    return int(row[0]) if row and row[0] is not None else None


def collect_scale(conn: sqlite3.Connection) -> tuple[int, int]:
    """수집 규모 — (매물 수, 차종 수).

    ★ 조회는 store 가 한다.  화면에 SQL 을 두지 않는다 (V11-01)
    """
    seen = conn.execute(
        "SELECT COUNT(*) FROM core_listing").fetchone()[0] or 0
    known = conn.execute(
        "SELECT COUNT(DISTINCT target_key) FROM core_listing "
        "WHERE target_key IS NOT NULL").fetchone()[0] or 1
    return int(seen), int(known)
