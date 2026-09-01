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
from store.raw import commit, raw_body

# 변하는 것만 추적한다 (STEP 29).  좁게 잡는다.
TRACKED_FIELDS: tuple[str, ...] = ("price_current_won", "sales_status", "status")

# 이것이 바뀌면 변경 이력이 아니라 검증 실패다 (STEP 29 · 6장 V2).
# 단위 환산 (2장 상수표 · V4-13)
MONTHS_PER_YEAR = 12

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
    run_id: str | None = None,
) -> None:
    """변경 1건을 적재한다.  삭제하지 않는다.

    ★★★★★ 09-03 (`S46-230`) — ★ `run_id` 를 함께 남긴다.
      ★ 「동시 발생」을 ★ **한 판 안**으로 세려면 ★ 그 행이 어느 판인지 알아야 한다
    """
    conn.execute(
        "INSERT OR REPLACE INTO core_listing_change"
        "(listing_id,changed_at,field,old_value,new_value,change_kind,cause,"
        " run_id)"
        " VALUES (?,?,?,?,?,?,?,?)",
        (listing_id, changed_at, field,
         None if old is None else str(old),
         None if new is None else str(new),
         change_kind, cause, run_id),
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
        vin_hash,
    )

    out = {k: v for k, v in parsed.items() if not k.startswith("_pii_")}
    lid = parsed.get("listing_id")
    # ★★★★★ 09-02 마스터 확정 — ★ 차대번호도 ★ **감춘다** (`S46-216`).
    #   ★ 짝의 열쇠를 ★ VIN 으로 올린다 — ★ 번호판은 바뀌고 ★ VIN 은 안 바뀐다
    if parsed.get("vin"):
        out["vin_hash"] = vin_hash(parsed.get("vin"), key)
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
    # ★★★ 08-28 — ★ 규격은 「★ **동시** 발생 건수를 본다」다 (STEP 29 판별 ②).
    #   ★★ ★ `_today(parsed)` 는 ★ `parsed` 에 `last_seen`·`first_seen` 이 없으면
    #     ★ ★ **빈 글자**를 돌려준다.  ★ `S4` 가 넘기는 `parsed` 가 그렇다 —
    #     ★ ★ 그러면 ★ `changed_at >= ''` 이라 ★ **역사 전체를 센다.**
    #   ★★ ★ 실측 08-28 — ★ 엔카 봉투 전 기간에 ★ 색이 바뀐 매물은 ★ **2건뿐**인데
    #     ★ ★ 누적 4건에 ★ 이번 둘이 더해져 ★ 문턱 5를 넘어 ★ `site_schema_change`
    #       ★ ★ 로 잘못 갈렸고 ★ `S4` 가 통째로 멈췄다.
    #     ★ ★ 시간이 갈수록 ★ **반드시** 넘는다 — ★ 누적은 「동시」가 아니다
    #   ★ 관측 시각이 있으면 그것을 쓴다 — ★ 이 함수가 이미 받고 있다
    # ★★★★★ 09-03 (`S46-230`) — ★ 「동시」를 ★ **한 판 안**으로 센다.
    #   ★ 날로 세면 ★ 같은 날 다시 돌릴 때 ★ 앞 판이 남긴 행을 **또 센다** —
    #   ★ ★ **실패가 다음 실패를 만든다**.  ★ `run_id` 가 있으면 그것으로 좁힌다.
    #   ★ ★ ★ `run_id` 를 모르면 ★ 옛 길(날)로 내린다 — ★ 그때만이다
    run_id = parsed.get("_run_id") or parsed.get("run_id")
    if run_id:
        n = conn.execute(
            "SELECT COUNT(DISTINCT listing_id) FROM core_listing_change"
            " WHERE field = ? AND change_kind = 'invariant_violation'"
            " AND run_id = ?", (field, str(run_id))).fetchone()[0]
    else:
        since = _today(parsed) or str(observed_at)[:10]
        n = conn.execute(
            "SELECT COUNT(DISTINCT listing_id) FROM core_listing_change"
            " WHERE field = ? AND change_kind = 'invariant_violation'"
            " AND changed_at >= ?", (field, since)).fetchone()[0]
    if n >= _schema_change_min():
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
        # ★★ 08-28 — ★ `site` 를 가린다.  ★ `raw_response` 에 ★ 엔카 말고도
        #   ★ 목록 봉투가 들어온다 (명령서 3-2) — ★ 남의 봉투를 읽으면
        #   ★ ★ 「이전 원문」이 ★ 엉뚱한 것이 된다 (`S46-78` 과 같은 자리다)
        "SELECT fetched_at, body FROM raw_response"
        " WHERE endpoint='list' AND status='ok' AND site='encar'"
        " ORDER BY id DESC LIMIT ?", (_lookback(),)
    ):
        try:
            doc = _json.loads(raw_body(body))
        except (ValueError, TypeError):
            continue
        for item in doc.get("SearchResults") or []:
            if str(item.get("Id")) == str(source_id):
                out.setdefault(at[:10], (at, item.get(key)))
    return [v for _k, v in sorted(out.items())]


def _schema_change_min() -> int:
    """같은 필드가 몇 건 동시에 바뀌면 사이트 스키마 변경인가 (STEP 29 ④).

    ★ 임계값은 config 다 (V4-13)
    """
    import json as _json
    import os as _os

    root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    with open(_os.path.join(root, "config", "web.json"),
              encoding="utf-8") as f:
        return int(_json.load(f)["invariant_schema_change_min"])


def _current(conn, lid: str, key: str):
    row = conn.execute(f"SELECT {key} FROM core_listing WHERE listing_id = ?",
                       (lid,)).fetchone()
    return row[0] if row else None


def _today(parsed: dict) -> str:
    return (parsed.get("last_seen") or parsed.get("first_seen") or "")[:10]


# ★★★ 08-28 — ★ 「값이 아닌 0」을 ★ 안 넣는다 (금지 12 · 개정 325).
#   ★ 실측 08-28 — ★ `displacement_cc = 0` 이 ★ **256건** 있었다
#     (엔카 179 · 리본카 55 · KB 22).  ★ 0cc 짜리 차는 없다 — ★ 「모름」이다.
#   ★ ★ 그것 때문에 ★ KB 상세 받기가 ★ 멈췄다 —
#     ★ ★ 「불변 필드 변경: displacement_cc 0 → 3470 — 원인 분류 못 함」 (STEP 29).
#   ★ ★ 0 을 값으로 두면 ★ 진짜 값이 왔을 때 ★ 「값이 바뀌었다」로 잡힌다.
#   ★ 「모르는 것을 모른다고 낸다」 — ★ NULL 이 맞다
NOT_A_VALUE = {"displacement_cc": (0,)}


def _drop_non_values(parsed: dict) -> dict:
    """★ 값이 아닌 것을 ★ 넣기 전에 뺀다.  ★ 위 `NOT_A_VALUE` 참고."""
    for key, bad in NOT_A_VALUE.items():
        if key in parsed and parsed[key] in bad:
            parsed = {k: v for k, v in parsed.items() if k != key}
    return parsed


# ★ 이 회차에 버린 신차가 — ★ 수집기가 끝에 세어 낸다 (조용히 안 버린다)
_ORIGIN_DROPPED: list = []


def origin_dropped() -> list:
    """★ 이 회차에 ★ 「신차가 < 현재값」이라 버린 것.  ★ 부르는 쪽이 센다."""
    return list(_ORIGIN_DROPPED)


def _drop_impossible_origin(parsed: dict) -> dict:
    """★★★★ 신차가가 ★ **현재값보다 작으면** ★ 신차가가 아니다 (마스터 지시 08-30).

    ★★★ 08-30 실측 — ★ 「신차가 < 현재값」이 ★ **477건**이었다
      (엔카 418 · 리본카 36 · KB 13 · 헤이딜러 9 · 렉서스 1).
      ★ ★ 리본카는 ★ 신차가가 ★ **10,000원**인 것이 있었다 — ★ 값은 9,420만이다.
    ★★ 까닭은 사이트마다 다르다 —
      ★ 현대인증은 ★ 「신차 가격 대비 9,100,000원 **절약**」의 절약액을 잡았고 (08-30 정정),
      ★ 리본카·헤이딜러·KB·엔카는 ★ 각자 다른 자리에서 뽑는다.
    ★ 그래서 ★ **파서마다 고치지 않고** ★ 넣는 문 하나에서 막는다 —
      ★ ★ 낱말이 무엇이든 ★ 「신차가 < 현재값」은 ★ 신차가일 수 없다.
    ★ 지어내지 않는다 — ★ **버린다** (`None` 이 되어 「모름」이다).
      ★ ★ 0 으로 채우면 ★ 감가율이 거짓이 된다 (개정 289·434)
    ★ 둘 중 하나가 없으면 ★ 못 견주므로 ★ 안 건드린다
    """
    own = parsed.get("price_origin_won")
    now = parsed.get("price_current_won")
    try:
        if own is not None and now is not None and int(own) < int(now):
            parsed = dict(parsed)
            parsed.pop("price_origin_won", None)
            # ★ 조용히 버리지 않는다 — ★ 세어서 남긴다.
            #   ★ `_` 로 시작하는 키는 ★ 칸이 아니라 ★ 「센 것」이다 —
            #   ★ ★ `_pii_plate_no` 와 같은 꼴이다 (A-2 가 무는 것은 ★ 칸인 척하는 키다)
            _ORIGIN_DROPPED.append((parsed.get("site"), parsed.get("source_id"), int(own)))
    except (TypeError, ValueError):
        pass
    return parsed

def _note_skipped(conn, lid, field: str, cause: str, at: str) -> None:
    """★★★★★ 09-03 (`S46-230` 3번) — ★ 「원인을 못 가른 불변 변경」을 ★ **센다**.

    ★ 규격 `STEP 50` 8번 — 「★ **경고 — 기록하고 계속**」.
      ★ ★ 판을 죽이지 않는다.  ★ 그 매물만 건너뛴다.
    ★★ 다만 ★ **조용히 넘기지 않는다** — ★ 이력에 남기고 ★ 리포트가 수로 낸다.
      ★ ★ 「고쳤습니다」만 적는 것이 ★ 이 프로젝트의 가장 큰 실패 모드다
    """
    try:
        conn.execute(
            "INSERT OR REPLACE INTO core_listing_change"
            "(listing_id,changed_at,field,old_value,new_value,change_kind,"
            " cause,run_id) VALUES (?,?,?,?,?,?,?,?)",
            (lid, at, f"{field}:skipped", None, None, "anomaly",
             cause or "분류 못 함", None))
        commit(conn)
    except sqlite3.Error:
        # ★ 기록을 못 남겨도 ★ 판은 이어 간다 — ★ 그것이 규격이 시킨 것이다
        pass


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
    parsed = _drop_non_values(parsed)
    parsed = _drop_impossible_origin(parsed)
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
            # ★★★★★ 09-03 (`S46-230` 2번) — ★ ①③ 으로 갈려 ★ **건너뛴 것**도
            #   ★ 행을 남기면 ★ 그 행이 ★ 다음 판의 「동시」 셈에 ★ **다시 든다**.
            #   ★ ★ 곧 ★ **실패가 다음 실패를 만든다**.
            #   ★★ 그래서 ★ 갈래를 ★ **먼저 본다** — ★ ①③ 이면
            #     ★ ★ `invariant_violation` 이 아니라 ★ `anomaly` 로 남긴다.
            #     ★ ★ ★ **이력은 그대로 남는다** — ★ 사람이 다 볼 수 있다 (P3)
            skipped = cause in (CAUSE_PARSE, CAUSE_REPLACED)
            record_change(conn, lid, field, old[field], parsed[field],
                          observed_at,
                          "anomaly" if skipped else "invariant_violation",
                          cause=cause or None,
                          run_id=parsed.get("_run_id") or parsed.get("run_id"))
            commit(conn)
            if cause == CAUSE_SOURCE_EDIT:
                # ★ 원문이 실제로 바뀌었다 (딜러 오기입 정정).
                #   조치는 「변경 수용 · 이력 기록」이다 (STEP 29 ②)
                continue
            if cause in (CAUSE_PARSE, CAUSE_REPLACED):
                # ★★★ 08-28 — ★ 규격 STEP 29 의 ★ **조치 표**를 따른다.
                #   ★ ① 파싱 오류  → 「파서 수정 · 재파싱」
                #   ★ ③ 매물 교체  → 「별도 매물로 분리」
                #   ★ ④ 스키마 변경 → 「★ **수집 중단**」
                #   ★★ ★ 「수집 중단」은 ★ **④ 하나뿐**이다.
                #     ★ ★ 그런데 코드는 ★ ①③ 에도 ★ 통째로 멈추고 있었다 —
                #     ★ ★ 실측 08-28 — ★ 매물 하나(5980)의 색 하나 때문에
                #       ★ ★ `S4` 가 멈춰 ★ **08-24T07:40 뒤로 아무것도 안 실렸다.**
                #       ★ ★ 마스터께서 브라우저로 넣어 주신 봉투 931건이
                #         ★ ★ 그대로 쌓여만 있었다 (수입 3,013건이 0건이었다)
                #   ★★ ★ 그 매물만 ★ **건너뛴다** — ★ 값을 덮어쓰지 않는다
                #     (금지 「원인 분류 없이 새 값으로 덮어쓰는 것」).
                #     ★ ★ 이력은 위에서 이미 남겼다 — ★ 사람이 볼 수 있다
                return 0
            # ★★★★★ 09-03 (`S46-230` 3번) — ★ **판을 통째로 죽이지 않는다.**
            #   ★ 규격 `STEP 50` 8번은 ★ 「**경고 — 기록하고 계속**」이다.
            #   ★ ★ 여기서 `raise` 하면 ★ 매물 하나 때문에 ★ 전 판이 멈춘다 —
            #   ★ ★ ★ 08-28 에 그 일이 실제로 났다 (봉투 931건이 안 실렸다).
            #   ★★ 그 매물만 ★ **건너뛴다.**  ★ 이력은 위에 남겼다 —
            #     ★ ★ 리포트가 ★ **수로** 낸다 (`_note_skipped`)
            _note_skipped(conn, lid, field, cause, observed_at)
            return 0

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


def sweep_gone(conn: sqlite3.Connection, site: str, target_key: str,
               seen_source_ids: set, at: str) -> int:
    """★★★★★ 차종 하나를 ★ **끝까지 받았을 때** ★ 이번 목록에 없는 것을 gone.

    지시서   11장 STEP 「언제 gone 으로 매기나」 (개정 838 · 마스터 08-29)
    사고     ★ `mark_gone` 을 ★ `tools/collect_kcar.py` ★ 하나만 불렀다.
             ★ 엔카·KB·볼보·현대·헤이딜러·리본카·보배 ★ 일곱이 안 불러
             ★ ★ 마스터께서 ★ **두 달째 팔린 차를 보셨다** (오판 161).
             ★ 실측 08-29 — ★ gone 을 매긴 사이트가 ★ `kcar` 하나였다
    ★★      ★ **그 차종만 건드린다.**  ★ 안 받은 차종은 그대로 둔다 —
             ★ 마스터께서 ★ 차종별로 나눠 받아 주시기 때문이다.
    ★★      ★ 부르는 쪽이 ★ **끝까지 받았을 때만** 부른다.
             ★ 반만 받고 부르면 ★ **산 차를 죽인다** — ★ 그 판단은 부르는 쪽에 있다
    금지     ★ 지우는 것 (마스터 확정 08-24).  ★ `gone_at` 과 그때 값을 남긴다
    반환     ★ 이번에 gone 으로 매긴 건수
    """
    if not seen_source_ids:
        # ★ 빈 목록으로는 ★ 아무것도 안 매긴다 — ★ 전멸시키지 않는다
        return 0
    # ★★★★★ 08-30 (마스터 지시 4) — ★ `target_key` 가 **없는** 행도 훑는다.
    #   ★ 실측 08-30 — ★ 볼보에 ★ 값·주행·연식이 다 빈 행 **15건**이 있었다.
    #   ★ ★ 차종이 안 붙어 ★ 이 함수가 ★ **한 번도 안 본 행**이다 —
    #   ★ ★ 목록에서 사라져도 ★ **영영 `gone` 이 안 된다.**  ★ 결함이다.
    #   ★ `target_key=None` 으로 부르면 ★ 그 사이트의 ★ 차종 없는 행을 훑는다.
    #   ★★ 안전 — ★ 부르는 쪽이 ★ **끝까지 받았을 때만** 부른다.  ★ 그 조건은 그대로다
    if target_key is None:
        rows = conn.execute(
            "SELECT listing_id, source_id FROM core_listing"
            " WHERE site = ? AND target_key IS NULL AND status = 'active'",
            (site,)).fetchall()
    else:
        rows = conn.execute(
            "SELECT listing_id, source_id FROM core_listing"
            " WHERE site = ? AND target_key = ? AND status = 'active'",
            (site, target_key)).fetchall()
    n = 0
    for lid, sid in rows:
        if str(sid) in seen_source_ids:
            continue
        mark_gone(conn, lid, at)
        n += 1
    return n


def sweep_gone_groups(conn: sqlite3.Connection, site: str, groups: list,
                      at: str) -> dict:
    """★★★★★ 여러 묶음을 받은 뒤 ★ **끝까지 받은 것만** 골라 gone 을 매긴다.

    지시서   11장 STEP 「언제 gone 으로 매기나」 (개정 838 · 마스터 08-29)
    ★★      ★ 아홉 수집기가 ★ **다 이것을 부른다** — ★ 같은 잣대를 쓰기 위해서다.
             ★ 수집기마다 따로 적으면 ★ 한 군데만 고치는 일이 생긴다 (검사 `S46-117`)
    groups   ★ `[(끝까지_받았나: bool, 본_source_id 집합), …]`
             ★ 「끝까지」의 판단은 ★ 수집기가 한다 — ★ 사이트마다 끝이 다르다
    ★★      ★ 안 끝난 묶음이 건드린 차종은 ★ **통째로 뺀다** —
             ★ 한 차종을 두 묶음이 나눠 받았는데 하나만 끝났으면 ★ 반만 본 것이다.
             ★ ★ 반만 보고 매기면 ★ **산 차를 죽인다**
    ★        ★ 본 것이 하나도 없으면 ★ 아무것도 안 매긴다 (전멸 방지)
    반환     ★ `{target_key: 매긴 건수}`
    """
    seen_by_t: dict = {}
    blocked: set = set()
    for done, ids in groups:
        ids = {str(x) for x in (ids or ()) if x is not None}
        if not ids:
            continue
        marks = ",".join("?" * len(ids))
        # ★★★★ 08-30 (마스터 지시 4) — ★ `target_key IS NOT NULL` 을 뺐다.
        #   ★ 차종이 안 붙은 행도 ★ 한 갈래(None)로 훑는다 —
        #   ★ ★ 안 그러면 ★ 값이 빈 행이 ★ **영영 안 죽는다** (볼보 15건)
        rows = conn.execute(
            f"SELECT DISTINCT target_key FROM core_listing"
            f" WHERE site = ? AND source_id IN ({marks})", (site, *ids)).fetchall()
        for (tk,) in rows:
            if done:
                seen_by_t.setdefault(tk, set()).update(ids)
            else:
                blocked.add(tk)
    out: dict = {}
    # ★ `None`(차종 미정)이 섞이므로 ★ 정렬 열쇠를 글자로 만든다
    for tk in sorted(set(seen_by_t) - blocked, key=lambda x: (x is None, x or "")):
        n = sweep_gone(conn, site, tk, seen_by_t[tk], at)
        if n:
            out[tk if tk is not None else "차종 미정"] = n
    return out


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
        " r.not_join_json,"
        # ★ F-scoring ② 가 쓰는 것 (개정 329)
        " i.inspection_inner_json, i.inspection_tuning, i.inspection_car_state,"
        " i.inspection_board_state,"
        " r.use_gov, r.use_business"
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
        # ★★★★★ 09-02 — ★ 사이트가 ★ 「이 차엔 없다」고 밝힌 옵션 (`S46-227`)
        options_absent=jload("options_absent_json"),
        inspection_panels=jload("inspection_panel_json"),
        # ★ 점검 출처 — TABLE 플랫폼 직영 · IMAGE 판매자 등록 (개정 300 · 306)
        inspection_formats=jload("inspection_formats_json"),
        not_join_months=_not_join_months(d.get("not_join_json")),
        # ★ F-scoring ② 가 쓰는 것 (개정 329)
        inspection_inner_json=d.get("inspection_inner_json"),
        inspection_tuning=_flag(d.get("inspection_tuning")),
        car_state_ok=(None if d.get("inspection_car_state") is None
                      else d.get("inspection_car_state") == CAR_STATE_OK),
        # ★ 개정 435 — 계기판 상태.  car_state_ok 와 같은 규칙이다
        board_state_ok=(None if d.get("inspection_board_state") is None
                        else d.get("inspection_board_state") == CAR_STATE_OK),
        ev_battery_soh=d.get("ev_battery_soh"),
        use_gov=_flag(d.get("use_gov")), use_business=_flag(d.get("use_business")),
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
        # ★★★★★ 09-03 개정 1085 — ★ 내장색 (`taste.color_int`)
        color_int_raw=d.get("color_int_raw"),
        color_ext_hex=d["color_ext_hex"],
        sell_type=d["sell_type"],
        plate_hash=d["plate_hash"],
        ad_body_text=d["ad_body_text"],
        site_flags={
            # ★ site_* 만이 아니다.  ⑤ 사이트 보증의 근거는 이름이
            #   site_ 로 시작하지 않는다 (개정 365) — 전건 0점이 됐다
            k: d[k] for k in cols
            if (k.startswith("site_") or k in SITE_WARRANTY_FIELDS)
            and d.get(k) is not None
        },
    )


# ⑤ 사이트 보증의 근거가 되는 칸 (개정 365).
# ★ config/sites.json 의 warranty_items 가 이 이름들을 가리킨다
SITE_WARRANTY_FIELDS = ("platform_verified", "warranty_deemed",
                        "warranty_extend", "sell_type", "diagnosis_car",
                        # ★★ 개정 491 — ★ 진단을 정말 받았는가.
                        #   ★ 미조회인데 만점을 주면 「누가 확인했는가」가 거짓이 된다
                        #   실측 08-23: warranty_extend=1 인 43건이 ★ 전부 미조회였다
                        "diagnosis_status")


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


def dealer_trust(conn: sqlite3.Connection, at: str) -> dict:
    """★★★ 딜러 정직도를 잰다 (7장 STEP 82c · 개정 822 · 08-29).

    ★ 규격이 08-29 에 왔다 — `docs/chapters/11-store/b-core.md`.
      ★ 그 전에는 셈 규칙이 한 줄도 없어 ★ 1,182곳이 다 NULL 이었고
        ★ 「정직도」 거르개가 ★ 늘 0건이었다 (시험자 #9).
    ★ 넷을 25점씩 더한다.  ★ 값이 없는 것은 ★ 분모에서 뺀다 (규격 그대로).
    ★ 매물 10건 미만이면 ★ 재지 않는다 — ★ `trust_score` 는 NULL 그대로다.
      ★ 세 건 파는 딜러의 「팔림 비율」은 뜻이 없다 (규격).
    ★ 추정으로 채우지 않는다.
    """
    rows = conn.execute(
        "SELECT l.dealer_id,"
        "       COUNT(*),"
        # ★ 올렸다 내린 것 — status 가 gone 이 된 매물
        "       SUM(CASE WHEN l.status = 'gone' THEN 1 ELSE 0 END),"
        # ★ 얼마나 적어 주나 — 사진 · 사고 · 보증 · 옵션 넷 중 채운 칸
        "       SUM(CASE WHEN COALESCE(l.photo_list_json,'') NOT IN ('','[]')"
        "                THEN 1 ELSE 0 END),"
        "       SUM(CASE WHEN r.listing_id IS NOT NULL THEN 1 ELSE 0 END),"
        "       SUM(CASE WHEN l.warranty_body_month IS NOT NULL"
        "                THEN 1 ELSE 0 END),"
        "       SUM(CASE WHEN COALESCE(l.options_choice_json,'')"
        "                NOT IN ('','[]') THEN 1 ELSE 0 END)"
        "  FROM core_listing l"
        "  LEFT JOIN core_record r ON r.listing_id = l.listing_id"
        " WHERE l.dealer_id IS NOT NULL"
        " GROUP BY l.dealer_id").fetchall()
    # ★ 값 바뀜 수 — `core_listing_change` 의 값(price) 변경 (규격의 「값을 얼마나 자주 바꾸나」)
    vol = {r[0]: r[1] for r in conn.execute(
        "SELECT l.dealer_id, COUNT(*) FROM core_listing_change c"
        "  JOIN core_listing l ON l.listing_id = c.listing_id"
        " WHERE c.field = 'price_current_won' AND l.dealer_id IS NOT NULL"
        " GROUP BY l.dealer_id")}
    # ★ 며칠 만에 팔리나 — first_seen ~ gone_at.  ★ 가운데값이다
    doms: dict = {}
    for did, days in conn.execute(
        "SELECT dealer_id, julianday(gone_at) - julianday(first_seen)"
        "  FROM core_listing"
        " WHERE dealer_id IS NOT NULL AND status = 'gone'"
        "   AND gone_at IS NOT NULL AND first_seen IS NOT NULL"):
        if days is not None and days >= 0:
            doms.setdefault(did, []).append(float(days))

    cfg = _trust_cfg()
    least = int(cfg["min_listings"])
    lo_d = float(cfg["dom_full_days"])
    hi_d = float(cfg["dom_zero_days"])
    w = cfg["weights"]
    # ★ 가름의 중앙값은 ★ **재는 딜러들**의 매물 수로 낸다 (규격의 표).
    #   ★ 못 재는 딜러(매물 10건 미만 968곳)까지 넣으면 ★ 중앙값이 1~2 로 내려가
    #     ★ 재는 딜러가 ★ 전부 「매물이 많다」가 된다 — ★ 실측 Q1 213 · Q3 1
    counts = sorted(r[1] for r in rows if r[1] >= least)
    mid_n = counts[len(counts) // 2] if counts else 0
    done = skipped = 0
    for (did, n, gone, ph, rec, war, opt) in rows:
        if n < least:
            # ★ 표본이 모자라면 ★ 재지 않는다.  ★ 0 으로 채우지 않는다
            conn.execute(
                "UPDATE core_dealer SET sample_sufficient = 0,"
                " trust_score = NULL, quadrant = NULL, listing_count = ?,"
                " calculated_at = ? WHERE dealer_id = ?", (n, at, did))
            skipped += 1
            continue
        # ★ (무게, 값) 넷.  ★ 무게도 config 가 정본이다 (dealer_trust.weights)
        parts = [
            (float(w["drop_event"]), 1.0 - (gone / n)),
            (float(w["price_volatility"]),
             1.0 - min(vol.get(did, 0) / n, 1.0)),
        ]
        got = doms.get(did)
        if got:                                              # ★ 없으면 분모에서 뺀다
            got = sorted(got)
            med = got[len(got) // 2]
            parts.append((float(w["dom"]),
                          max(0.0, min(1.0, (hi_d - med) / (hi_d - lo_d)))))
        parts.append((float(w["info"]), (ph + rec + war + opt) / (4.0 * n)))
        tot_w = sum(x for x, _v in parts)
        score = round(100.0 * sum(x * v for x, v in parts) / tot_w, 1)
        # ★ 넷으로 나눈다 — 매물 수 중앙값 · 점수 가름 (규격의 표)
        big, high = n >= mid_n, score >= float(cfg["quadrant_score_cut"])
        quad = "Q1" if (big and high) else ("Q2" if high else
                                            ("Q3" if big else "Q4"))
        conn.execute(
            "UPDATE core_dealer SET trust_score = ?, quadrant = ?,"
            " sample_sufficient = 1, listing_count = ?, calculated_at = ?"
            " WHERE dealer_id = ?", (score, quad, n, at, did))
        done += 1
    commit(conn)
    return {"scored": done, "too_few": skipped, "dealers": len(rows),
            "min_listings": least}


def _trust_cfg() -> dict:
    """정직도 셈의 상수.  ★ 정본은 `config/scoring.json` 의 `dealer_trust` 다.

    ★★ 08-29 마스터 — 「★ 거기서 읽어라.  ★ 코드 기본값을 지워라」.
      ★ 그래서 ★ 기본값을 두지 않는다 — ★ 없으면 ★ 조용히 딴 값으로 재지 않고
        ★ **곧바로 터진다.**  ★ 「선언과 실제의 괴리」를 막는 것이 이 프로젝트다
    """
    import json as _tj
    import os as _to

    here = _to.path.dirname(_to.path.dirname(_to.path.abspath(__file__)))
    with open(_to.path.join(here, "config", "scoring.json"),
              encoding="utf-8") as f:
        got = _tj.load(f)["dealer_trust"]
    return got


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
# 점검부의 「차량 상태」가 정상인 문구.  ★ 코드가 아니라 문구다 (실측)
CAR_STATE_OK = "양호"


def _flag(raw) -> int | None:
    """'0' · '1' · True · False → 0 · 1.  ★ 「모른다」는 None 으로 남긴다."""
    if raw is None:
        return None
    if isinstance(raw, bool):
        return int(raw)
    got = str(raw).strip().lower()
    if got in ("1", "true", "y"):
        return 1
    if got in ("0", "false", "n", ""):
        return 0
    return None


def _not_join_months(raw) -> int | None:
    """자차 미가입 개월 합 (개정 294).

    원문   ["202412~202502", null, null, null, null]
    ★ 「있다」가 아니라 몇 달인지다 — 1달과 5년은 다른 사실이다
    """
    import re as _re

    if not raw:
        return None
    try:
        spans = [x for x in json.loads(raw) if x]
    except (ValueError, TypeError):
        return None
    total = 0
    for span in spans:
        got = _re.match(r"(\d{4})(\d{2})~(\d{4})(\d{2})", str(span))
        if not got:
            continue
        a = int(got.group(1)) * MONTHS_PER_YEAR + int(got.group(2))
        b = int(got.group(3)) * MONTHS_PER_YEAR + int(got.group(4))
        total += max(0, b - a)
    return total


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
        # ★★★ 08-27 — ★ **사이트를 가린다.**  ★ 배너 글이 「엔카 목록」이다.
        #   ★★ 실측 — ★ 원문 보관을 켠 뒤 ★ 렉서스 목록(04:28)이 들어와
        #     ★ ★ 엔카 목록(전날 07:54)이 ★ **신선한 것처럼 보였다** —
        #     ★ ★ 그래서 ★ 「갱신되지 않았습니다」 배너가 ★ 안 떴다
        "list_at": "SELECT COALESCE(MAX(fetched_at),'') FROM raw_response "
                   "WHERE endpoint='list' AND status='ok' AND site='encar'",
        # ★★★ 엔카가 ★ 우리 회선을 막은 마지막 때 (마스터 지시 08-27 ⓑ).
        #   ★ `407` 은 ★ 고장이 아니다 — ★ 규격이다 (`ENCAR_API.md:48`
        #     「서울 IP 407 · 브라우저 수집」).  ★ 그러나 ★ 화면이 ★ 까닭을 말해야 한다
        "encar_407_at": "SELECT COALESCE(MAX(requested_at),'') "
                        "FROM audit_request WHERE site='encar' "
                        "AND kind='list' AND http_code=407",
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


# 카탈로그를 못 받은 사유 (개정 327).  ★ not_called 는 우리 잘못이다
CATALOG_ENDPOINT = "catalog"
# 못 받은 사유 중 우리 잘못인 것 (개정 327).
# ★ empty · not_found 는 사이트가 안 주는 것이다 — 세되 벌하지 않는다
OUR_FAULT = ("not_called", "http_error", "parse_failed", "error")


def our_fault(why: str) -> bool:
    """그 사유가 우리 잘못인가.

    ★ 함수로 낸다.  표현 계층(report/)은 store 의 대문자 이름을
      import 하지 않는다 — 그것은 DTO 자리다 (S15 · STEP 15)
    """
    return why in OUR_FAULT


def catalog_coverage(conn) -> dict:
    """필요한 조합 · 받은 것 · 못 받은 사유 (개정 327).

    ★ 카탈로그는 「모델·연식·트림」 조합 단위다.  매물 단위가 아니다.
      호출 키가 곧 조합 키다 — raw_response.source_id 가 model_catalog_key 다
    ★ 「몇 건 받았다」가 아니라 「몇 개 중 몇 개」를 낸다
    """
    # ★ 판정하는 매물의 조합만 「필요」다.  out_of_scope 는 안 판정하므로
    #   그 카탈로그를 안 부른 것은 잘못이 아니다 — 그대로 세면
    #   「not_called 3조합 · 우리 잘못」이 영영 뜬다 (실측 08-18)
    need = {r[0] for r in conn.execute(
        "SELECT DISTINCT model_catalog_key FROM core_listing"
        " WHERE model_catalog_key IS NOT NULL AND status='active'")}
    tried: dict = {}
    for key, status in conn.execute(
        "SELECT source_id, status FROM raw_response WHERE endpoint=?",
        (CATALOG_ENDPOINT,)
    ):
        tried.setdefault(key, set()).add(status)
    ok = {k for k, v in tried.items() if "ok" in v}
    why: dict = {"not_called": sorted(need - set(tried))}
    for key in set(tried) - ok:
        for status in sorted(tried[key]):
            why.setdefault(status, []).append(key)
    # 조합마다 매물이 몇 건 걸려 있는가 — 급한 정도가 다르다
    weight = dict(conn.execute(
        "SELECT model_catalog_key, COUNT(*) FROM core_listing"
        " WHERE model_catalog_key IS NOT NULL AND status='active'"
        " GROUP BY model_catalog_key"))
    # ★ 마스터가 읽는 것은 15자리 키가 아니라 「G80_25T · 2024-11」이다
    label = {}
    for key, target, ym in conn.execute(
        "SELECT model_catalog_key, MIN(target_key), MIN(year_month)"
        " FROM core_listing WHERE model_catalog_key IS NOT NULL"
        " AND status='active' GROUP BY model_catalog_key"
    ):
        label[key] = " · ".join(x for x in (target, ym) if x) or key
    return {"need": need, "ok": ok, "why": why, "weight": weight,
            "label": label,
            "linked": {r[0] for r in conn.execute(
                "SELECT DISTINCT model_catalog_key FROM dict_model_option"
                " WHERE model_catalog_key IS NOT NULL")}}


def _walk(node, prefix: str, out: dict) -> None:
    """원문을 훑어 경로마다 「값이 있었는가」를 센다.

    ★ 배열은 `[]` 로 접는다 — 등록부가 그렇게 적는다
    """
    if isinstance(node, dict):
        for key, val in node.items():
            path = f"{prefix}.{key}" if prefix else key
            out[path] = out.get(path, 0) + (0 if val in (None, "", [], {})
                                            else 1)
            _walk(val, path, out)
    elif isinstance(node, list):
        for one in node[:3]:
            _walk(one, f"{prefix}[]", out)


def _sample_bodies() -> int:
    """엔드포인트마다 원문 몇 개를 열어 볼 것인가 (개정 341).

    ★ 전건을 열면 오래 걸린다.  「늘 비어 있는가」는 표본으로 충분하다
    """
    import os as _o

    root = _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__)))
    with open(_o.path.join(root, "config", "checks.json"),
              encoding="utf-8") as f:
        return int(json.load(f)["unclassified_sample_bodies"])


def hits_of(seen: dict, path: str) -> int:
    """등록부가 적은 경로를 관측 결과에서 찾는다.

    ★★ 실측 08-19 — 등록부는 `list:BadgeDetail` 이라 적는데
      원문을 훑으면 `SearchResults[].BadgeDetail` 로 나온다.  이름이 달라
      **값이 20,204건 있는데도 「0/200」이 됐다** (개정 413 갈래 ②).
      ★ 「관측 0」이 「값이 없다」로 읽히므로 이 어긋남은 조용히 틀린다
    ★ 꼬리가 같은 것이 여럿이면 안 고른다 — 단정하지 않는다
    """
    if path in seen:
        return seen[path]
    bare = path.replace("[]", "")
    if bare in seen:
        return seen[bare]
    tails = [k for k in seen
             if k.endswith(f"[].{path}") or k.endswith(f".{path}")]
    return seen[tails[0]] if len(tails) == 1 else 0


def key_seen(seen: dict, path: str) -> bool:
    """그 키가 원문에 **있기라도** 했는가 (값은 없어도).

    ★ 「키가 아예 없다」와 「키는 있는데 값이 전건 null」은 다르다.
      앞은 사이트가 그 필드를 안 준다는 뜻이고,
      뒤는 그 엔드포인트가 비워서 준다는 뜻이다 (개정 413 갈래 ①)
    """
    if path in seen:
        return True
    if path.replace("[]", "") in seen:
        return True
    return any(k.endswith(f"[].{path}") or k.endswith(f".{path}")
               for k in seen)


def stored_hits(conn) -> dict:
    """등록부에 적힌 관측 수 (개정 413).  ★ 전건을 센 값이다.

    ★ 화면이 원문을 다시 열지 않는다 — /admin/registry 한 쪽이 26쿼리였다.
      `sync_registry` 가 전 원문을 한 번 도는 김에 세어 적어 둔다 (V11-34)
    ★ 표본 200 이 아니라 전건이라 「0/200」 같은 착시가 없다
    """
    out: dict = {}
    for endpoint, path, hits, total in conn.execute(
        "SELECT endpoint, json_path, observed_hits, observed_total"
        " FROM meta_field_usage"
    ):
        out[(endpoint, path)] = (hits, total)
    return out


def sample_bodies(conn, endpoint: str) -> list:
    """그 엔드포인트 원문 표본.  ★ 한 요청에 한 번만 읽는다.

    실측 08-19 — `observed()` 와 `_peek()` 가 같은 원문을 따로 읽어
    /admin/registry 한 쪽이 26쿼리였다 (상한 20).  둘이 나눠 쓴다
    """
    cache = getattr(conn, "_cw_bodies", None)
    if cache is None:
        cache = {}
        try:
            conn._cw_bodies = cache
        except AttributeError:
            pass
    if endpoint not in cache:
        cache[endpoint] = [raw_body(b) for (b,) in conn.execute(
            "SELECT body FROM raw_response WHERE endpoint=? AND status='ok'"
            " AND body IS NOT NULL"
            " ORDER BY (id * 2654435761) % 1000003 LIMIT ?",
            (endpoint, _sample_bodies()))]
    return cache[endpoint]


def observed(conn, endpoint: str) -> tuple:
    """그 엔드포인트에서 경로마다 값이 있었던 횟수 · 본 원문 수.

    ★★ 표본을 id 순으로 자르지 않는다 (실측 08-19).  `ev_battery` 는
      최신 200건이 전부 비전기차라 `ensolRawInfo` 가 「0/200」으로 나왔다 —
      값은 전기차 1,838건 중 55건에 있다.  ★ 「없다」가 아니라 「안 봤다」였다
    ★ 흩어 뽑되 무작위가 아니다.  같은 DB 면 같은 표본이 나온다 —
      돌릴 때마다 숫자가 달라지면 그것도 못 믿는다
    """
    # ★ 한 요청에 여러 번 부른다 — 카드·갈래·목록이 각각 부른다.
    #   그때마다 원문 200개를 열면 화면 하나가 무거워진다 (V11-34)
    cache = getattr(conn, "_cw_observed", None)
    if cache is None:
        cache = {}
        try:
            conn._cw_observed = cache
        except AttributeError:
            pass
    if endpoint in cache:
        return cache[endpoint]
    seen: dict = {}
    rows = sample_bodies(conn, endpoint)
    for body in rows:
        try:
            got = json.loads(body)
        except (ValueError, TypeError):
            continue
        # ★ 원문 하나를 「한 번」으로 센다.  배열 안을 도는 경로는
        #   본문 하나에서 여러 번 나온다 — 그대로 더하면 「459/200」이 된다
        one: dict = {}
        _walk(got, "", one)
        for key, hit in one.items():
            base = seen.setdefault(key, 0)
            seen[key] = base + (1 if hit else 0)
    cache[endpoint] = (seen, len(rows))
    return cache[endpoint]


def known_leaves(conn) -> dict:
    """이미 분류된 경로의 잎 이름 → (분류, 경로).

    ★ 이름이 같으면 같은 것일 「가능성」이다.  단정하지 않는다
    """
    out: dict = {}
    for endpoint, usage, path in conn.execute(
        "SELECT endpoint, usage, json_path FROM meta_field_usage"
        " WHERE usage NOT IN ('unclassified')"
    ):
        leaf = path.replace("[]", "").split(".")[-1]
        out.setdefault(leaf.lower(), (usage, path, endpoint))
    return out


def has_unclassified(conn) -> bool:
    """미분류가 하나라도 있는가.  ★ SQL 은 store 가 갖는다 (V11-01)."""
    return bool(conn.execute(
        "SELECT 1 FROM meta_field_usage WHERE usage='unclassified' LIMIT 1"
    ).fetchone())


def classify_unclassified(conn) -> list:
    """미분류 경로마다 (엔드포인트, 경로, 관측, 표본, 갈래, 제안)."""
    leaves = known_leaves(conn)
    by_ep: dict = {}
    for endpoint, path in conn.execute(
        "SELECT endpoint, json_path FROM meta_field_usage"
        " WHERE usage='unclassified' ORDER BY endpoint, json_path"
    ):
        by_ep.setdefault(endpoint, []).append(path)

    out = []
    counted = stored_hits(conn)
    for endpoint, paths in sorted(by_ep.items()):
        seen, total = ({}, 0)
        if not all(counted.get((endpoint, p), (None, 0))[1] for p in paths):
            seen, total = observed(conn, endpoint)   # 아직 안 세어진 것만
        for path in paths:
            bare = path.replace("[]", "")
            got = counted.get((endpoint, path))
            if got and got[1]:
                hits, total = got[0], got[1]
            else:
                hits = hits_of(seen, path)
            leaf = bare.split(".")[-1].lower()
            twin = leaves.get(leaf)
            if total and not hits:
                kind, hint = "③ 늘 비어 있음", "not_provided — 안 쓰기로 정하면 됩니다"
            elif twin and (twin[2], twin[1]) != (endpoint, path):
                # ★ 같은 잎 이름이 다른 엔드포인트에 이미 분류돼 있다.
                #   경로 글자만 견주면 record 와 record_summary 처럼
                #   이름이 똑같은 짝을 놓친다 (실측 08-18)
                kind = "② 이름만 다름"
                hint = (f"{twin[0]} — 「{twin[2]}:{twin[1]}」과 "
                        "같은 것으로 보입니다")
            else:
                kind, hint = "④ 새로운 것", "사람이 봐야 합니다"
            out.append({"endpoint": endpoint, "path": path, "hits": hits,
                        "total": total, "kind": kind, "hint": hint})
    out.sort(key=lambda r: (-r["hits"], r["endpoint"], r["path"]))
    return out



def _card_limit() -> int:
    """미분류 화면에 한 번에 낼 카드 수.  ★ config 가 정본이다 (V4-13)."""
    return int(_admin_cfg()["decide_cards"])


def _value_chars() -> int:
    """화면에 낼 값 한 조각의 길이.  ★ config 가 정본이다 (V4-13)."""
    return int(_admin_cfg()["decide_value_chars"])


def _admin_cfg() -> dict:
    """config/admin.json.  ★ 한 번만 읽는다."""
    import json as _j
    import os as _o

    global _ADMIN
    if _ADMIN is None:
        root = _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__)))
        with open(_o.path.join(root, "config", "admin.json"),
                  encoding="utf-8") as f:
            _ADMIN = _j.load(f)
    return _ADMIN


_ADMIN: dict | None = None


def unclassified_cards(conn, limit: int | None = None,
                       rows: list | None = None,
                       blocking: set | None = None) -> list:
    """미분류 항목마다 판단할 재료 다섯 (개정 367 · V4-28).

    마스터 지적 — 「이걸 보고 내가 무엇을 하라는 말이지?  뭔지도 모르겠는데」
    ★ 원문 경로만 내고 「사람이 봐야 합니다」라 하면 아무도 못 정한다

    한 항목에 이 다섯
      ① 실제 값과 분포 ② 판정에 쓰이는가 ③ 원문에서 어디에 있었나
      ④ 고를 것을 단추로 ⑤ 안 정하면 무엇이 막히나

    ★ 원문은 엔드포인트마다 한 번만 읽는다.  항목마다 읽으면
      한 쪽에 378쿼리 · 11.8초가 된다 (실측 08-19 · V11-34 가 잡았다)
    """
    limit = _card_limit() if limit is None else limit
    # ★★ 화면과 검사가 같은 것을 세야 한다 (개정 390).
    #   전에는 화면이 _blocking_paths(103건)를, V4-11 과 목록이
    #   parser_paths(32건)를 봤다 — 겹치는 것이 22건뿐이었다.
    #   「32건」과 화면의 수가 어긋나면 마스터가 무엇을 정할지 모른다
    # ★ 부르는 쪽이 「막는 것」을 준다 — store 는 parse·tools 를 못 부른다 (V4-22).
    #   안 주면 옛 셈(_blocking_paths)을 쓴다 — 그것은 화면과 검사가 갈린다
    stops = blocking if blocking is not None else _blocking_paths(conn)
    # ★ 이미 센 것이 있으면 다시 세지 않는다.  같은 쪽에서 두 번 세면
    #   한 쪽 쿼리가 상한(20)을 넘는다 — V11-34 가 30으로 잡았다
    rows = list(rows if rows is not None else classify_unclassified(conn))
    # ★ 막는 것 먼저 · 그다음 많이 관측된 순.  자를 것을 먼저 자른다
    rows.sort(key=lambda r: ((r["endpoint"], r["path"]) not in stops,
                             -r["hits"]))
    rows = rows[:limit]

    want: dict = {}
    for one in rows:
        want.setdefault(one["endpoint"], []).append(
            one["path"].replace("[]", ""))
    facts = {ep: _peek(conn, ep, paths) for ep, paths in want.items()}

    out = []
    for one in rows:
        ep, path = one["endpoint"], one["path"]
        bare = path.replace("[]", "")
        blocks = (ep, path) in stops
        got = facts.get(ep, {}).get(bare, ({}, []))
        out.append({
            "endpoint": ep, "path": path, "leaf": bare.split(".")[-1],
            "hits": one["hits"], "total": one["total"], "kind": one["kind"],
            "hint": one["hint"],
            "values": got[0], "siblings": got[1],
            "used": "판정을 막습니다" if blocks else "지금 안 쓰입니다",
            "if_left": ("판정이 막힙니다 — 이 매물들이 등급을 못 받습니다"
                        if blocks else "막지 않습니다 — 그냥 안 씁니다"),
            "blocks": blocks,
        })
    return out


def _peek(conn, endpoint: str, paths: list) -> dict:
    """그 엔드포인트 원문을 한 번 읽어 경로마다 값·형제를 뽑는다.

    ★ 표본으로 본다.  전건을 펼치면 화면이 안 뜬다
    ★ 값이 길면 자른다 — 화면이 129KB 가 됐다 (V11-76)
    """
    import json as _j

    seen: dict = {p: {} for p in paths}
    sibs: dict = {p: {} for p in paths}
    for body in sample_bodies(conn, endpoint):
        try:
            doc = _j.loads(body)
        except (ValueError, TypeError):
            continue
        for p in paths:
            parts = p.split(".")
            node = doc
            for key in parts[:-1]:
                if isinstance(node, list):
                    node = node[0] if node else None
                if not isinstance(node, dict):
                    node = None
                    break
                node = node.get(key)
            if isinstance(node, list):
                node = node[0] if node else None
            if not isinstance(node, dict):
                continue
            leaf = parts[-1]
            for k in node:
                if k != leaf:
                    sibs[p][k] = sibs[p].get(k, 0) + 1
            got = node.get(leaf)
            key = "없음" if got is None else _short(got)
            seen[p][key] = seen[p].get(key, 0) + 1
    out = {}
    for p in paths:
        values = [{"value": k, "n": v}
                  for k, v in sorted(seen[p].items(),
                                     key=lambda kv: -kv[1])[:5]]
        top = [k for k, _v in sorted(sibs[p].items(),
                                     key=lambda kv: -kv[1])[:3]]
        out[p] = (values, top)
    return out


def _short(value) -> str:
    """화면에 낼 값 한 조각.  ★ 통째로 내면 한 쪽이 129KB 가 된다."""
    if isinstance(value, dict):
        return "{" + " · ".join(sorted(value)[:3]) + " …}"
    if isinstance(value, list):
        return f"[{len(value)}개]"
    got = str(value)
    cap = _value_chars()
    return got if len(got) <= cap else got[:cap] + "…"


def _blocking_paths(conn) -> set:
    """판정을 막는 미분류 경로 (V4-11 이 세는 것과 같은 것을 본다).

    ★ 검사와 화면이 다른 것을 세면 「32건」과 화면의 수가 어긋난다
    """
    return {(r[0], r[1]) for r in conn.execute(
        "SELECT u.endpoint, u.json_path FROM meta_field_usage u"
        " WHERE u.usage='unclassified'"
        "   AND EXISTS (SELECT 1 FROM meta_field_usage k"
        "               WHERE k.endpoint = u.endpoint"
        "                 AND k.usage NOT IN ('unclassified','not_provided')"
        "                 AND k.json_path LIKE"
        "                     substr(u.json_path, 1,"
        "                            length(u.json_path)"
        "                            - length(replace(u.json_path, '.', ''))) "
        "                     || '%')")}


# 이미 판정에 쓰는 엔드포인트 — 「받은 원문」 절에 또 내지 않는다 (개정 378).
# ★ 판정에 쓰이기 시작하면 위쪽 축별 판정으로 올라가고 여기서 사라진다
def _raw_rows_max() -> int:
    """「받은 원문」 절에 낼 줄 수.  ★ config 가 정본이다 (V4-13)."""
    import json as _j
    import os as _o

    root = _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__)))
    with open(_o.path.join(root, "config", "web.json"), encoding="utf-8") as f:
        return int(_j.load(f)["raw_rows_max"])


def used_endpoints(conn: sqlite3.Connection) -> set:
    """판정에 쓰는 엔드포인트 (meta_field_usage).

    ★ 등록부가 정본이다.  코드에 이름을 박지 않는다
    """
    return {r[0] for r in conn.execute(
        "SELECT DISTINCT endpoint FROM meta_field_usage WHERE usage='in_use'")}


def raw_sections(conn: sqlite3.Connection, listing_id: int,
                 used: set | None = None,
                 cap: int | None = None) -> list:
    """받아 놓고 아직 판정에 안 쓰는 원문 (개정 378 · V11-134).

    마스터 지적 — 「내가 보는 게 우선이지 않니?  그런데 네가 판정을 못 내려서
    받아 놓고 안 보이는데 말이 되니?」
    ★ 파서가 없으면 원문 JSON 을 그대로 편다.
      「파서를 만들 때까지 안 보여준다」는 안 된다
    돌려줌   [{endpoint, at, rows:[{key, value}], deep}]
    """
    import json as _j

    # ★ 이미 판정에 쓰는 엔드포인트는 여기 또 내지 않는다.
    #   판정에 쓰이기 시작하면 위쪽 축별 판정으로 올라가고 여기서 사라진다
    used = used if used is not None else used_endpoints(conn)
    cap = _raw_rows_max() if cap is None else cap
    out = []
    for endpoint, at, body in conn.execute(
        "SELECT endpoint, fetched_at, body FROM raw_response"
        " WHERE listing_id = ? AND status = 'ok'"
        " GROUP BY endpoint HAVING MAX(fetched_at) = fetched_at"
        " ORDER BY endpoint", (listing_id,)
    ):
        if endpoint in used:
            continue
        try:
            doc = _j.loads(raw_body(body))
        except (ValueError, TypeError):
            continue
        rows = _flatten(doc, cap)
        # ★ 비어 있어도 낸다.  「받았는데 사이트가 값을 안 줬다」는
        #   마스터가 알아야 할 사실이다 — 전기차 7,374건이 그렇다 (실측 08-19).
        #   안 내면 「안 받았다」와 구별이 안 된다
        out.append({"endpoint": endpoint, "at": at, "rows": rows,
                    "deep": len(rows) >= cap, "empty": not rows})
    return out


def _flatten(node, cap: int, prefix: str = "") -> list:
    """원문을 「키 = 값」 줄로 편다.

    ★ 값이 없는 가지는 안 낸다 — 빈 줄만 수십 개가 되면 못 읽는다
    ★ 너무 깊으면 그 자리에서 멈춘다.  한 쪽이 수백 KB 가 된다
    """
    out: list = []
    if isinstance(node, dict):
        for k, v in node.items():
            if len(out) >= cap:
                break
            out += _flatten(v, cap - len(out), f"{prefix}.{k}" if prefix else k)
    elif isinstance(node, list):
        if not node:
            return out
        # ★ 목록은 첫 것만 편다.  나머지는 「그 밖 N개」로 센다
        out += _flatten(node[0], cap, f"{prefix}[0]")
        if len(node) > 1:
            out.append({"key": prefix, "value": f"그 밖 {len(node) - 1}개"})
    elif node not in (None, "", {}, []):
        out.append({"key": prefix, "value": str(node)[:80]})
    return out[:cap]


def option_diff(conn: sqlite3.Connection, listing_ids: list,
                dicts=None) -> dict:
    """비교 — 옵션 차이만 (61-web 「비교 (/compare)」).

    ★ 「옵션 차이만 낸다.  같은 것은 접는다」
      「A 에만 있음: 파노라마 선루프 140만 · 드라이빙 어시스트 150만」
    ★ 이것이 비교 화면의 핵심이다.  같은 트림이면 옵션이 값을 가른다
    돌려줌   {"same": [이름…], "only": {매물: [{code,name,won}…]}}
    """
    import json as _j

    del dicts
    picked: dict = {}
    for lid in listing_ids:
        row = conn.execute(
            "SELECT options_choice_json FROM core_listing WHERE listing_id=?",
            (lid,)).fetchone()
        try:
            codes = _j.loads(row[0]) if row and row[0] else []
        except (ValueError, TypeError):
            codes = []
        picked[lid] = [str(c) for c in codes] if isinstance(codes, list) else []
    names, prices = _option_names(conn)
    every = [set(v) for v in picked.values()]
    same = sorted(set.intersection(*every)) if every else []
    only = {}
    for lid, codes in picked.items():
        rest = set()
        for other, o_codes in picked.items():
            if other != lid:
                rest |= set(o_codes)
        mine = sorted(set(codes) - rest)
        only[lid] = [{"code": c, "name": names.get(c, c),
                      "won": prices.get(c)} for c in mine]
    return {"same": [{"code": c, "name": names.get(c, c)} for c in same],
            "only": only}


def _option_names(conn: sqlite3.Connection) -> tuple:
    """옵션 코드 → 이름 · 값.  ★ 없으면 코드를 그대로 쓴다 (추정하지 않는다)."""
    names, prices = {}, {}
    for code, display in conn.execute(
            "SELECT value, display FROM dict_enum WHERE axis='option3'"):
        if display:
            names[str(code)] = display
    try:
        for code, won in conn.execute(
                "SELECT option_code, price_won FROM dict_option_price"):
            prices[str(code)] = won
    except sqlite3.OperationalError:
        pass
    return names, prices


def blocking_keys(conn, used: set, containers: tuple) -> set:
    """판정을 막는 경로의 (엔드포인트, 경로)만 — 관측 수는 안 센다.

    ★ blocking_rows 는 엔드포인트마다 원문을 훑어 관측을 센다.
      화면이 「막는가」만 알면 될 때 그것을 부르면 한 쪽이 52쿼리가 된다
      (실측 08-19 · V11-34 상한 20)
    """
    out = set()
    for endpoint, path in conn.execute(
        "SELECT endpoint, json_path FROM meta_field_usage"
        " WHERE usage='unclassified'"
    ):
        bare = path.replace("[]", "")
        if bare in used or path.split("[]")[0] in containers:
            out.add((endpoint, path))
    return out


def full_hits(conn, endpoint: str, path: str) -> tuple:
    """그 엔드포인트 원문을 **전건** 열어 그 경로에 값이 몇 번 있었나.

    ★ 표본이 0 일 때만 부른다.  「0/200」이 「없다」인지 「드물다」인지는
      전건을 봐야 갈린다 — ev_battery 는 12,589건 중 55건에만 값이 있다.
      표본 200 으로는 못 본다 (실측 08-19)
    ★ 전건을 늘 여는 것이 아니다.  0 인 것만 한 번 더 본다
    """
    hits = total = 0
    for (body,) in conn.execute(
        "SELECT body FROM raw_response WHERE endpoint=? AND status='ok'"
        " AND body IS NOT NULL", (endpoint,)
    ):
        try:
            got = json.loads(raw_body(body))
        except (ValueError, TypeError):
            continue
        total += 1
        one: dict = {}
        _walk(got, "", one)
        if hits_of(one, path):
            hits += 1
    return hits, total


def axis_paths_empty(conn, used: set) -> list:
    """판정 축이 쓰는 경로 중 **어디서도** 값이 안 오는 것 (개정 413).

    ★ 엔드포인트 하나가 0 이라고 축이 빈 것이 아니다.
      `record_summary:myAccidentCost` 는 전건 null 이지만
      같은 값을 `record` 가 준다 — 축은 안 빈다 (실측 08-19)
    ★ 그래서 **잎 이름**으로 묶어 모든 엔드포인트를 함께 본다.
      전부 0 이어야 「축 하나가 통째로 빈 것」이다
    돌려줌   [{leaf, paths, endpoints, hits, total}] — 값이 0 인 것만
    """
    by_leaf: dict = {}
    for endpoint, path in conn.execute(
        "SELECT endpoint, json_path FROM meta_field_usage"
    ):
        bare = path.replace("[]", "")
        if bare not in used:
            continue
        by_leaf.setdefault(bare.split(".")[-1], []).append((endpoint, path))
    cache: dict = {}
    out = []
    for leaf, pairs in sorted(by_leaf.items()):
        best, where, tot = 0, [], 0
        for endpoint, path in pairs:
            if endpoint not in cache:
                cache[endpoint] = observed(conn, endpoint)
            seen, total = cache[endpoint]
            got = hits_of(seen, path)
            if not got:
                # ★ 표본이 0 이면 전건을 한 번 더 본다.  드문 것을 「없다」 하지 않는다
                got, total = full_hits(conn, endpoint, path)
            where.append(f"{endpoint}:{path}")
            best, tot = max(best, got), max(tot, total)
        if not best:
            out.append({"leaf": leaf, "paths": where, "hits": 0, "total": tot})
    return out


def blocking_rows(conn, used: set, containers: tuple,
                  where: dict | None = None) -> list:
    """판정을 막는 미분류 경로 — 목록 (개정 390 · V4-30).

    마스터 지시 — 「실제값으로 너랑 나랑 판단해야지」
    ★ V4-11 이 세는 것과 **같은 자리**를 본다 — parser_paths() 가 정본이다.
      다른 것을 세면 「32건」과 목록의 수가 어긋난다
    ★ 「파서가 읽는 곳」을 파일·줄로 적는다 —
      이 32건은 「파서가 실제로 그 경로를 읽는 것」이라 막는 것이다.
      정말 읽는지 줄로 보여야 한다
    돌려줌   [{endpoint, path, hits, total, where}] — 많이 관측된 순
    """
    # ★ 파서 지식은 부르는 쪽이 준다 — store 는 contracts·errors 만 부른다 (V4-22).
    #   실측 08-19 — tools 를 부르다 역방향 import 로 걸렸다
    where = where or {}
    out = []
    counted = stored_hits(conn)
    for endpoint, path in conn.execute(
        "SELECT endpoint, json_path FROM meta_field_usage"
        " WHERE usage='unclassified' ORDER BY endpoint, json_path"
    ):
        bare = path.replace("[]", "")
        head = path.split("[]")[0]
        if not (bare in used or head in containers):
            continue
        got = counted.get((endpoint, path))
        seen, total = ({path: got[0]}, got[1]) if got and got[1] else (
            observed(conn, endpoint))
        # ★ 통째로 읽는 컨테이너는 잎 이름으로 안 잡힌다 —
        #   파서가 outers 를 통째로 받아 그 안을 도는 것이다.
        #   그 자리를 짚어야 「정말 읽는지」를 볼 수 있다 (실측 08-19)
        spot = (where.get(bare) or where.get(bare.split(".")[-1])
                or (f"{where[head]} (컨테이너 통째)" if head in where
                    and head in containers else ""))
        hits = hits_of(seen, path)
        out.append({
            "endpoint": endpoint, "path": path,
            "hits": hits, "total": total,
            "where": spot,
            # ★ 관측 0 을 「없다」로 읽지 않게 한다 (개정 413)
            "why": ("" if hits else
                    "키는 있는데 값이 전건 비었다" if key_seen(seen, path)
                    else "키 자체가 원문에 없다"),
        })
    out.sort(key=lambda r: (-r["hits"], r["endpoint"], r["path"]))
    return out

# 성능부와 보험이력이 어긋난 것을 가르는 조건 (30-score/d-history · V3-50).
# ★ SQL 을 화면·검사에 두지 않는다.  세는 곳과 뽑는 곳이 같은 것을 본다 —
#   갈라 두면 「836건」과 화면의 수가 어긋난다 (V11-55 와 같은 사고)
RECORD_MISMATCH = (
    "EXISTS (SELECT 1 FROM core_inspection ci"
    " JOIN core_record cr ON cr.listing_id = ci.listing_id"
    " WHERE ci.listing_id = l.listing_id"
    "   AND ((ci.inspection_accident_flag = 0"
    "         AND COALESCE(cr.accident_my_cost, 0) > 0)"
    "     OR (ci.inspection_accident_flag = 1"
    "         AND COALESCE(cr.accident_my_cost, 0) = 0"
    "         AND COALESCE(cr.accident_my_cnt, 0) = 0)))"
)


def record_mismatch_sql() -> str:
    """목록 질의에 붙일 조건.  ★ 함수로 낸다 —
    대문자 상수를 계층 밖으로 넘기지 않는다 (S15 · our_fault 와 같은 자리)."""
    return RECORD_MISMATCH


def record_mismatch_count(conn) -> dict:
    """성능부와 보험이력이 어긋난 건수 (V3-50).

    조사한 것   「성능 기록부에는 흔적이 없는데 보험 이력에는 수리 비용이 있었다」
    ★ 양쪽을 다 센다 — 성능부가 무사고인데 보험에 있는 것,
      성능부가 사고인데 보험에 없는 것.  어느 쪽이든 「다르다」다
    ★ 「둘 다 받은 것」을 분모로 낸다.  못 받은 것을 「맞다」로 세지 않는다
    """
    both = conn.execute(
        "SELECT COUNT(*) FROM core_inspection i"
        " JOIN core_record r ON r.listing_id = i.listing_id").fetchone()[0]
    no_acc = conn.execute(
        "SELECT COUNT(*) FROM core_inspection i"
        " JOIN core_record r ON r.listing_id = i.listing_id"
        " WHERE i.inspection_accident_flag = 0"
        "   AND COALESCE(r.accident_my_cost, 0) > 0").fetchone()[0]
    no_ins = conn.execute(
        "SELECT COUNT(*) FROM core_inspection i"
        " JOIN core_record r ON r.listing_id = i.listing_id"
        " WHERE i.inspection_accident_flag = 1"
        "   AND COALESCE(r.accident_my_cost, 0) = 0"
        "   AND COALESCE(r.accident_my_cnt, 0) = 0").fetchone()[0]
    return {"both": both, "no_inspection_trace": no_acc,
            "no_insurance_trace": no_ins, "mismatch": no_acc + no_ins}


def relist_counts(conn) -> dict:
    """같은 `vehicle_id` 가 몇 번 올라왔나 (V7-14 · 개정 355).

    ★ 내렸다 다시 올린 것은 그 자체가 정보다.  묶되 횟수를 낸다
    돌려줌   {vehicle_id: {"times": n, "first_won": …, "last_won": …}}
    """
    out: dict = {}
    for vid, n, lo, hi in conn.execute(
        "SELECT vehicle_id, COUNT(*), MIN(price_current_won),"
        " MAX(price_current_won) FROM core_listing"
        " WHERE vehicle_id IS NOT NULL AND vehicle_id <> ''"
        " GROUP BY vehicle_id HAVING COUNT(*) > 1"
    ):
        out[vid] = {"times": n, "low_won": lo, "high_won": hi}
    return out


def listing_models(conn) -> list:
    """매물이 있는 차종 · 건수 (개정 420).

    ★ config 의 목록이 아니라 실제로 있는 것이다.  없는 차종을 고르게 하면
      「0건」만 나온다 — 그것은 조작이 아니다
    """
    return [(k, n) for k, n in conn.execute(
        "SELECT target_key, COUNT(*) FROM core_listing"
        " WHERE status='active' AND target_key IS NOT NULL"
        " GROUP BY target_key ORDER BY COUNT(*) DESC")]


# ★ 목록 필터 선택지 — 그 칸에 실제로 있는 값 (개정 427 · STEP 97).
#   ★ web/ 은 SQL 을 못 쓴다 (V11-01).  조회는 여기 있다
#   ★ 목록을 코드에 박지 않는다 — DB 에 없는 선택지를 내면 0건이 나온다
FILTER_OPTION_COLUMNS: tuple[str, ...] = (
    "color_ext_raw", "color_int_raw", "fuel_raw", "dealer_region",
)


def filter_options(conn, column: str, limit: int = 14) -> list:
    """그 칸의 값과 건수를 많은 순으로.

    ★ 칸 이름을 밖에서 그대로 받지 않는다 — 허용 목록으로 가둔다
    """
    if column not in FILTER_OPTION_COLUMNS:
        raise ValidationError(f"목록 필터가 못 쓰는 칸이다 — {column}",
                              step="STEP 97",
                              action="config/web.json 의 필터 목록을 보십시오")
    rows = conn.execute(
        f"SELECT {column}, COUNT(*) FROM core_listing"
        f" WHERE {column} IS NOT NULL AND {column} <> ''"
        f" GROUP BY 1 ORDER BY 2 DESC LIMIT ?", (limit,)).fetchall()
    return [{"value": v, "count": n} for v, n in rows]



def site_counts(conn) -> dict:
    """사이트별 ★ active · out_of_scope 건수 (개정 306 · 08-24).

    ★★ `web/` 은 ★ SQL 문자열을 못 쓴다 (V11-01) — ★ 질의는 여기 있다
    ★ 「0」과 「안 받았다」를 가르려면 ★ 둘을 함께 내야 한다
    """
    return {r[0]: (r[1] or 0, r[2] or 0) for r in conn.execute(
        "SELECT site,"
        "       SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END),"
        "       SUM(CASE WHEN status = 'out_of_scope' THEN 1 ELSE 0 END)"
        "  FROM core_listing GROUP BY site")}
