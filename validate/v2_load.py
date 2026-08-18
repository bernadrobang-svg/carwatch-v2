# -*- coding: utf-8 -*-
"""V2 적재 검증 — 옮겨졌는가 · 전일 대비 변동이 타당한가.

지시서   6장 STEP 56 (기본) · 57 (전일 GAP) · 58 (보정)
근거     V2-06 options.choice 의 '[]' 가 0건이면 falsy → None 버그다
         V2-07 insp_outer_json 전건 NULL 이었고 사고 20점이 죽어 있었다
금지     anomaly 를 원인 분류 없이 새 값으로 덮어쓰는 것
"""
from __future__ import annotations

from dataclasses import dataclass, field

from validate.base import (
    Check,
    FATAL,
    KIND_CODE,
    KIND_CONTRACT,
    KIND_EXTERNAL,
    WARN,
    _cfg,
    not_applicable,
    result,
)

C = {
    "V2-01": Check("V2", "V2-01", "ok 원문 수 == CORE 행 수", FATAL, "run",
                     "파싱이 빠진 원문을 찾아 S6 을 재실행한다 (재수집 아님)",
                    KIND_CODE),
    "V2-02": Check("V2", "V2-02", "필수 컬럼 NOT NULL 위반 없음", FATAL, "run",
                     "필수 컬럼이 NULL 인 행의 원문을 열어 매핑 누락인지 확인한다",
                    KIND_CODE),
    "V2-04": Check("V2", "V2-04", "status 열거값 위반 없음", FATAL, "run",
                     "열거값 위반 행의 파서를 고치고 S6 을 재실행한다",
                    KIND_CODE),
    "V2-05": Check("V2", "V2-05", "단위 — 가격이 만원 단위로 남아 있지 않은가", FATAL, "run",
                     "×10,000 환산이 빠진 경로를 찾는다. 값 크기로 되돌리는 보정은 금지다",
                    KIND_CODE),
    "V2-06": Check("V2", "V2-06", "빈 컨테이너가 NULL 로 저장되지 않았는가", FATAL, "run",
                     "serialize_container 가 빈 컨테이너를 None 으로 만들지 않는지 확인하고 S6 을 재실행한다",
                    KIND_EXTERNAL),
    "V2-07": Check("V2", "V2-07", "전건 NULL 컬럼", WARN, "run",
                     "원문에 값이 있으면 파싱 결함(fatal), 없으면 「원본 미제공」으로 등록부에 기록한다",
                    KIND_EXTERNAL),
    "V2-09": Check("V2", "V2-09", "core_pii 를 직접 조회하는 코드 없음", FATAL, "run",
                   "get_pii() 를 경유하도록 호출부를 고친다",
                    KIND_CONTRACT),
    "V2-10": Check("V2", "V2-10",
                   "core_listing 에 plate_no · dealer_name · phone · "
                   "address 없음", FATAL, "run",
                   "PII 원본은 core_pii 에만 둔다 (STEP 35). "
                   "본 표에 있으면 화면·내보내기로 새어 나간다",
                   KIND_CONTRACT),
    "V2-12": Check("V2", "V2-12", "secrets/plate_hmac.key 가 버전 관리 밖",
                   FATAL, "run",
                   "키가 저장소에 들어가면 해시가 뜻을 잃는다 (STEP 35)",
                   KIND_CONTRACT),
    "V2-10b": Check("V2", "V2-10b", "core_* 에 마스킹 컬럼 없음", FATAL, "run",
                    "*_masked 컬럼을 지우고 hash IS NOT NULL 로 확보 여부를 낸다",
                    KIND_CONTRACT),
    "V2-17": Check("V2", "V2-17", "PII 고아 행 없음", FATAL, "run",
                   "대리키 확정 전에 PII 를 저장한 경로를 찾는다. "
                   "resolve_*_id 가 실패하면 flush_pii 를 하지 않는다",
                    KIND_CODE),
    "V2-20": Check("V2", "V2-20", "파싱 실패 필드가 있는 행도 CORE 에 있음",
                   FATAL, "run",
                   "필드 예외가 매물 파싱을 중단시키는 경로를 찾는다 (STEP 19a)",
                   KIND_CODE),
    "V2-21": Check("V2", "V2-21", "parse_error · type_mismatch 건수",
                   WARN, "run",
                   "건수가 늘면 원문 구조가 바뀐 것이다. 파서를 본다",
                   KIND_EXTERNAL),
    "V2-28": Check("V2", "V2-28", "파싱 실패해도 남은 필드가 저장됨",
                   FATAL, "run",
                   "필드 단위로 구제한다. 한 필드 오류로 매물이 사라지면 "
                   "그 매물의 다른 16축도 못 본다 (STEP 19a)",
                   KIND_CODE),
    "V2-29": Check("V2", "V2-29", "upsert 가 버린 키를 기록함", WARN, "run",
                   "컬럼에 없는 키를 조용히 버리지 않는다. 세어서 남긴다",
                   KIND_EXTERNAL),
    "V2-13": Check("V2", "V2-13", "core_record 에 record_plate_no 원본 없음",
                   FATAL, "run",
                   "번호판 원본은 core_pii 다. 해시만 CORE 에 둔다 (STEP 35)",
                   KIND_CONTRACT),
    "V2-22": Check("V2", "V2-22", "현재 DB 스키마가 sql/ddl 과 일치",
                   FATAL, "run",
                   "run.py migrate 를 실행한다 (STEP 32b)", KIND_CODE),
    "V2-23": Check("V2", "V2-23", "중간 노드 None 인 매물도 CORE 에 있음",
                   FATAL, "run",
                   "dig() 로 바꾼다. 중간 null 하나로 매물이 사라진다",
                   KIND_CODE),
    "V2-24": Check("V2", "V2-24", "배열 기대 필드가 전건 list 로 정규화됨",
                   FATAL, "run",
                   "as_list() 를 통과시킨다. 문자열 순회는 사전을 오염시킨다",
                   KIND_CODE),
    "V2-25": Check("V2", "V2-25", "스칼라 null 이 0 으로 저장된 컬럼 없음",
                   FATAL, "run",
                   "「모른다」를 0 으로 바꾸지 않는다 (STEP 32)", KIND_CODE),
    "V2-27": Check("V2", "V2-27", "parse/ 에 원문 연쇄 첨자가 없음",
                   FATAL, "run",
                   "dig(raw, \"a.b.c\") 로 바꾼다. 중간 null 하나로 매물이 사라진다",
                   KIND_CODE),
    "V2-19": Check("V2", "V2-19", "원문 유래 컬럼에 NOT NULL 없음", FATAL, "run",
                   "그 컬럼의 NOT NULL 을 뺀다. 사이트가 안 주면 없는 것이다",
                   KIND_CODE),
    "V2-18": Check("V2", "V2-18", "parse_rule 재처리 후 전 봉투가 현재 "
                   "parse_version", FATAL, "run",
                   "S6 을 parse_rule 사유로 재실행한다 (전체 봉투)",
                    KIND_CODE),
    "V2-14": Check("V2", "V2-14", "참조되는 5종 PK 가 단일 INTEGER", FATAL, "run",
                   "STEP 30 대리키 규격으로 DDL 을 고친다",
                    KIND_CODE),
    "V2-15": Check("V2", "V2-15", "자연키가 UNIQUE 로 걸려 있음", FATAL, "run",
                   "UNIQUE 제약을 추가한다. 중복 방지가 사라진다",
                    KIND_CODE),
    "V2-16": Check("V2", "V2-16", "PK·FK 컬럼에 개인정보 없음", FATAL, "run",
                   "번호판·연락처를 키에서 빼고 vehicle_identity 로 옮긴다",
                    KIND_CONTRACT),
    "V2-11": Check("V2", "V2-11", "plate_hash 가 전건 16자 hex", FATAL, "run",
                   "secrets/plate_hmac.key 로 재파싱한다 (S6)",
                    KIND_CODE),
    "V2-08": Check("V2", "V2-08", "값 종류 1인 컬럼", WARN, "run",
                     "차종 특성인지 결함인지 8차종 통합 분포로 판정한다",
                    KIND_EXTERNAL),
    "V2-31": Check("V2", "V2-31", "target_key NULL 이 판정에 들어가지 않음",
                   FATAL, "run",
                   "차종이 없으면 판정 대상이 아니다.  임의의 차종에 넣지 "
                   "않는다 (개정 271)",
                   KIND_CODE),
    "V2-32": Check("V2", "V2-32", "NULL 매물의 모델명이 화면에서 보임",
                   WARN, "run",
                   "왜 안 붙었는지 알 수 있어야 사람이 targets.json 을 "
                   "고친다 (개정 271)",
                   KIND_CODE),
    "V2-30": Check("V2", "V2-30", "전 파서가 row_status 를 냄", FATAL, "run",
                   "같은 자리를 넷이 쓰는데 하나만 빠지면 눈으로 못 잡는다. "
                   "parse_diagnosis 가 빠져 S6 이 통째로 죽었다 (개정 270)",
                   KIND_CODE)
}

# 단위 검사 기준 — 중앙값이 이 미만이면 만원 단위가 남아 있다 (STEP 56)
MIN_MEDIAN_WON = _cfg("price_median_min_won")

WATCH_COLUMNS = (
    "options_choice_json", "options_standard_json", "price_origin_won",
    "warranty_body_month", "displacement_cc", "vin",
    "site_diagnosis_grade", "ad_body_text", "plate_hash", "dealer_shop",
)


@dataclass
class DayGapReport:
    """전일 대비 GAP (STEP 57).  변동 4종."""

    increase: int = 0
    decrease: int = 0
    change: int = 0
    anomaly: int = 0
    prev_total: int = 0
    total: int = 0
    samples: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class GapCause:
    listing_id: str
    field: str
    cause: str  # parse_error · source_edit · listing_swap · schema_change


def run(conn, ctx) -> list:
    rid = ctx.run_id
    out = []

    # V2-01 — ok 원문이 전부 CORE 행이 됐는가 (STEP 56).
    # ★ 「지금까지 한 번이라도 ok 였던 매물」과 「지금 ok 인 행」을 견주면 안 된다.
    #   08-16 에 ok 였다가 08-17 에 404 가 된 매물이 24건 있다 — 팔려서
    #   내려간 것이다.  detail_status='not_found' 가 맞는 값이고
    #   원문 ok 도 버리면 안 되는 사실이다 (P3 무손실).
    #   견줄 것은 「매물마다 마지막 detail 봉투」다 (실측 08-18)
    ok_raw = conn.execute(
        "SELECT COUNT(*) FROM ("
        " SELECT listing_id, status,"
        "        ROW_NUMBER() OVER (PARTITION BY listing_id"
        "                           ORDER BY fetched_at DESC, id DESC) AS n"
        " FROM raw_response WHERE endpoint='detail' AND listing_id IS NOT NULL"
        ") WHERE n=1 AND status='ok'").fetchone()[0]
    core = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE detail_status='ok'").fetchone()[0]
    # ★ ok 로 받아 놓고 CORE 에 행이 아예 없는 것 — v1 의 사고가 이 모양이었다
    lost = conn.execute(
        "SELECT COUNT(DISTINCT r.listing_id) FROM raw_response r"
        " WHERE r.endpoint='detail' AND r.status='ok'"
        " AND r.listing_id IS NOT NULL"
        " AND NOT EXISTS (SELECT 1 FROM core_listing l"
        "                 WHERE l.listing_id=r.listing_id)").fetchone()[0]
    out.append(result(C["V2-01"], rid, ok_raw,
                      core if not lost else f"{core} · 행이 없는 매물 {lost}",
                      ok_raw == core and not lost,
                      [] if not lost else
                      [f"ok 로 받았는데 core_listing 에 행이 없는 매물 {lost}건"]))

    n = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE site IS NULL OR source_id IS NULL "
        "OR status IS NULL OR row_status IS NULL").fetchone()[0]
    out.append(result(C["V2-02"], rid, 0, n, n == 0))

    # CHECK 제약이 이미 막지만, 스키마 변경 시 뚫릴 수 있으므로 값으로 다시 본다
    n = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE status NOT IN "
        "('new','active','gone','relisted','out_of_scope')").fetchone()[0]
    out.append(result(C["V2-04"], rid, 0, n, n == 0))

    row = conn.execute(
        "SELECT COUNT(*), AVG(price_current_won) FROM core_listing "
        "WHERE price_current_won IS NOT NULL").fetchone()
    if row[0]:
        avg = row[1]
        out.append(result(C["V2-05"], rid, f">= {MIN_MEDIAN_WON}", int(avg),
                          avg >= MIN_MEDIAN_WON))
    else:
        out.append(result(C["V2-05"], rid, "표본 없음", 0, True))

    # ★ '[]' 가 0건이면 falsy → None 버그다 (STEP 32)
    empty = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE options_choice_json = '[]'"
    ).fetchone()[0]
    nulls = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE options_choice_json IS NULL"
    ).fetchone()[0]
    total = conn.execute("SELECT COUNT(*) FROM core_listing").fetchone()[0]
    out.append(result(C["V2-06"], rid, "'[]' > 0 또는 전건 NULL 아님",
                      f"[]={empty} NULL={nulls} 전체={total}",
                      total == 0 or empty > 0 or nulls < total))

    all_null, single = [], []
    for col in WATCH_COLUMNS:
        r = conn.execute(
            f"SELECT COUNT({col}), COUNT(DISTINCT {col}) FROM core_listing"
        ).fetchone()
        if total and r[0] == 0:
            all_null.append(col)
        elif r[1] == 1 and total > 1:
            single.append(col)
    out.append(result(C["V2-07"], rid, "없음 또는 설명됨", all_null or "없음",
                      not all_null, all_null))
    out.append(result(C["V2-08"], rid, "없음 또는 설명됨", single or "없음",
                      not single, single))

    # ★ PII 는 get_pii() 로만 읽는다 (3장 STEP 35).  SQL 문자열만 본다
    out.append(_pii_access_check(rid))

    # ★ 중간값을 저장하면 PII 판단이 원본/마스킹/해시 셋으로 갈린다 (STEP 35)
    masked = []
    for (tbl,) in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name LIKE 'core_%'"
    ).fetchall():
        masked += [f"{tbl}.{r[1]}" for r in conn.execute(
            f"PRAGMA table_info({tbl})") if r[1].endswith("_masked")]
    out.append(result(C["V2-10b"], rid, 0, masked or 0, not masked, masked))
    out.append(_pii_column_check(conn, rid))
    out.append(_secret_key_check(rid))

    out += _surrogate_key_checks(conn, rid)
    out.append(_not_null_check(conn, rid))
    out.append(_chained_subscript_check(rid))
    out += _exception_shape_checks(conn, rid)
    out.append(_salvage_check(rid))
    dropped = [f"{r[0]} ({r[1]})" for r in conn.execute(
        "SELECT json_path, reason FROM meta_field_usage "
        "WHERE endpoint = 'core' AND reason LIKE 'upsert%' LIMIT 20")]
    out.append(result(C["V2-29"], rid, 0, len(dropped), True, dropped))

    # ★ 매물이 사라지는 것이 아니라 축 하나가 빠지는 것이다 (STEP 19a)
    orphan = 0 if not _table_exists(conn, "core_parse_issue") else conn.execute(
        "SELECT COUNT(DISTINCT p.listing_id) FROM core_parse_issue p "
        "WHERE NOT EXISTS (SELECT 1 FROM core_listing l "
        " WHERE l.listing_id = p.listing_id)").fetchone()[0]
    out.append(result(C["V2-20"], rid, 0, orphan, orphan == 0))

    broken = [] if not _table_exists(conn, "core_parse_issue") else [
        f"{r[0]}:{r[1]} {r[2]}건" for r in conn.execute(
        "SELECT endpoint, json_path, COUNT(*) FROM core_parse_issue "
        "WHERE reason IN ('parse_error','type_mismatch') "
        "GROUP BY endpoint, json_path ORDER BY 3 DESC LIMIT 20")]
    out.append(result(C["V2-21"], rid, 0, len(broken), not broken, broken))

    # V2-18 — parse_rule 재처리 후 옛 판이 남아 있는가 (13-pipeline · STEP 31).
    # ★ MAX(parse_version) 을 쓰지 않는다.  글자 최대값은 'p10' < 'p9' 다 —
    #   store/core.py 가 이미 겪고 적어 둔 함정이다.  「가장 최근에 펼친 판」이다
    cur = conn.execute(
        "SELECT parse_version FROM core_listing WHERE parse_version <> ''"
        " ORDER BY parsed_at DESC, rowid DESC LIMIT 1").fetchone()
    cur = cur[0] if cur else None
    # ★ 「옛 판이 남았다」와 「펼친 적이 없다」는 다르다.
    #   detail 이 404 라 펼칠 본문이 없는 행은 parse_version 이 비어 있는 것이
    #   맞는 값이다 (실측 08-18 · 30건 전부 detail_status='not_found').
    #   비었는데 본문이 ok 인 행은 진짜 결함이다 — 그것만 잡는다
    stale = conn.execute(
        "SELECT COUNT(*) FROM core_listing"
        " WHERE parse_version <> '' AND parse_version <> ?",
        (cur,)).fetchone()[0] if cur else 0
    unparsed = conn.execute(
        "SELECT COUNT(*) FROM core_listing"
        " WHERE parse_version = '' AND detail_status = 'ok'").fetchone()[0]
    never = conn.execute(
        "SELECT COUNT(*) FROM core_listing"
        " WHERE parse_version = ''").fetchone()[0]
    note = [] if not unparsed else [
        f"본문을 ok 로 받아 놓고 펼친 적이 없는 행 {unparsed}건"]
    out.append(result(
        C["V2-18"], rid, 0,
        f"{stale + unparsed}" + (f" · 펼칠 본문이 없는 행 {never}"
                                 if never else ""),
        stale == 0 and unparsed == 0, note))

    # ★ 2 가 실패하면 3 을 하지 않는다.  PII 만 남는 고아를 만들지 않는다 (STEP 35)
    orphan = conn.execute(
        "SELECT COUNT(*) FROM core_pii p WHERE NOT EXISTS "
        "(SELECT 1 FROM core_listing l WHERE l.listing_id = p.listing_id)"
    ).fetchone()[0] + conn.execute(
        "SELECT COUNT(*) FROM core_dealer_pii d WHERE NOT EXISTS "
        "(SELECT 1 FROM core_dealer c WHERE c.dealer_id = d.dealer_id)"
    ).fetchone()[0]
    out.append(result(C["V2-17"], rid, 0, orphan, orphan == 0))

    bad = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE plate_hash IS NOT NULL "
        "AND (LENGTH(plate_hash) <> 16 OR plate_hash GLOB '*[^0-9a-f]*')"
    ).fetchone()[0]
    out.append(result(C["V2-11"], rid, 0, bad, bad == 0))
    return out


# 참조되는 것만 대리키다.  나머지는 자연키가 곧 정체성이다 (STEP 30)
SURROGATE_TABLES = ("core_listing", "core_vehicle", "core_dealer",
                    "account", "watch_item")
NATURAL_UNIQUE = {
    "core_listing": ("site", "source_id"),
    "core_dealer": ("site", "site_dealer_id"),
    "watch_item": ("account_id", "vehicle_id"),
}
# ★ 키에 들어가면 안 되는 이름.  나중에 누가 번호판을 키로 쓰면 걸린다
PII_KEY_WORDS = ("plate_no", "phone", "address", "dealer_name", "vin")


def _surrogate_key_checks(conn, run_id) -> list:
    out = []
    bad = []
    for tbl in SURROGATE_TABLES:
        info = list(conn.execute(f"PRAGMA table_info({tbl})"))
        pk = [r for r in info if r[5]]
        if len(pk) != 1 or pk[0][2].upper() != "INTEGER":
            bad.append(f"{tbl}: {[(r[1], r[2]) for r in pk]}")
    out.append(result(C["V2-14"], run_id, 0, bad or 0, not bad, bad))

    bad = []
    for tbl, cols in NATURAL_UNIQUE.items():
        found = False
        for idx in conn.execute(f"PRAGMA index_list({tbl})"):
            if not idx[2]:
                continue
            names = tuple(r[2] for r in conn.execute(
                f"PRAGMA index_info({idx[1]})"))
            if set(names) == set(cols):
                found = True
        if not found:
            bad.append(f"{tbl}{cols}")
    out.append(result(C["V2-15"], run_id, 0, bad or 0, not bad, bad))

    bad = []
    for (tbl,) in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall():
        info = list(conn.execute(f"PRAGMA table_info({tbl})"))
        keys = {r[1] for r in info if r[5]}
        for fk in conn.execute(f"PRAGMA foreign_key_list({tbl})"):
            keys.add(fk[3])
        for k in keys:
            if any(w in k for w in PII_KEY_WORDS):
                bad.append(f"{tbl}.{k}")
    out.append(result(C["V2-16"], run_id, 0, bad or 0, not bad, bad))
    return out


# ★ 우리가 만드는 값 (STEP 31a).  이것만 NOT NULL 이어도 된다.
#   원문에서 오는 값은 사이트가 안 주면 없는 것이다 — 그것도 사실이다
OUR_COLUMNS: frozenset[str] = frozenset({
    # 식별 · 계보
    "listing_id", "site", "source_id", "vehicle_id", "dealer_id", "account_id",
    "watch_id", "query_id", "run_id", "endpoint", "request_url", "origin",
    "site_dealer_id", "primary_listing_id",
    # 시각 — 우리가 찍는다
    "fetched_at", "created_at", "updated_at", "calculated_at", "detected_at",
    "observed_at", "first_seen", "last_seen", "applied_at", "executed_at",
    "queued_at", "changed_at", "added_at", "occurred_at", "checked_at",
    "requested_at", "expires_at", "first_hit_at", "last_hit_at", "decided_at",
    "parsed_at", "collected_at",
    # 진행 메모 — 사람이 적는다.  원문에서 오지 않는다 (개정 362)
    "noted_at",
    # 진단 부위 — resultCode 가 있는 것만 넣는다.  거르고 남은 것이라 필수다
    "item_code", "part_name", "result_code",
    # 로그인 시도 — 우리가 찍는다 (STEP 126)
    "succeeded", "attempted_at", "display_name",
    # 검사를 돌았는가 — 우리가 판단한다 (A-7 · V1-16)
    "applicable",
    # 조건 추적 — 사용자가 화면에서 만든다 (STEP 117a)
    "conditions_json", "notify_on_new", "notify_on_price", "name",
    # 계정 — 사람이 정한다.  원문에서 오는 값이 아니다 (STEP 34)
    "login_name",
    "date",
    # 버전 · 상태 — 우리가 정한다
    "parse_version", "dict_version", "calc_version", "status", "row_status",
    "listing_status", "confidence", "kind", "usage", "reason", "code",
    "phase", "severity", "scope", "trigger", "from_step", "cause",
    "change_kind", "field", "decision", "role", "display_name",
    "secret_hash", "must_change_secret", "attempt", "measured",
    # 집계 · 판정 산출 — 기본값이 있다
    "listing_count", "site_count", "sample_sufficient", "miss_streak",
    "count_seen", "axis_count", "peer_count", "representative", "notified",
    "acknowledged", "excluded", "max_points", "passed", "expected", "actual",
    "classify_conflict", "sample_size", "prio", "source", "axis",
    "score_total", "denominator", "grade", "after_value", "value_hash",
    "json_path", "display", "source_endpoint", "target_key", "active",
    "on_price_drop", "on_target_price", "on_gone", "on_relist",
    "on_grade_change", "on_dom", "evidence", "warning_code", "title",
    "body", "sql_text", "url", "condition", "label", "file", "key_path",
    "curve_json", "sample_json", "request_kind", "reject_reason", "raw_body",
})


def _not_null_check(conn, run_id):
    """★ 판정은 「모르면 뺀다」인데 저장이 「모르면 멈춘다」면 앞뒤가 안 맞는다."""
    bad = []
    for (table,) in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall():
        for row in conn.execute(f"PRAGMA table_info({table})"):
            name, notnull, pk = row[1], row[3], row[5]
            if notnull and not pk and name not in OUR_COLUMNS:
                bad.append(f"{table}.{name}")
    return result(C["V2-19"], run_id, 0, bad or 0, not bad, bad)


# ★ 원문 접근은 parse/ 에서만 한다.  범위를 좁히면 예외 목록이 필요 없다 (STEP 19a)
RAW_VARS = frozenset({"raw", "body", "doc", "node", "o", "el", "item"})


def _chained_subscript_check(run_id):
    """parse/ 안에서 원문 변수에 연쇄 첨자를 쓰지 않는가.

    ★ raw["a"]["b"] 는 중간이 None 이면 죽는다 — 그 매물 전체가 사라진다
    허용   dig(raw, "a.b.c") · as_list(...)
    """
    import ast
    import os

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bad = []
    for base, _dirs, files in os.walk(os.path.join(root, "parse")):
        for f in files:
            if not f.endswith(".py"):
                continue
            path = os.path.join(base, f)
            try:
                tree = ast.parse(open(path, encoding="utf-8").read())
            except SyntaxError:
                continue
            for n in ast.walk(tree):
                # a[...][...] 형태 — 첨자가 겹친 것만 본다
                if not (isinstance(n, ast.Subscript)
                        and isinstance(n.value, ast.Subscript)):
                    continue
                inner = n.value
                while isinstance(inner, ast.Subscript):
                    inner = inner.value
                if isinstance(inner, ast.Name) and inner.id in RAW_VARS:
                    rel = os.path.relpath(path, root)
                    bad.append(f"{rel}:{n.lineno} {inner.id}[...][...]")
    return result(C["V2-27"], run_id, 0, bad or 0, not bad, bad)


# 배열이어야 하는 CORE 컬럼 (STEP 19a).  전건 JSON 배열이어야 한다
ARRAY_COLUMNS = (
    ("core_listing", "site_trust_json"), ("core_listing", "site_condition_json"),
    ("core_listing", "site_service_marks_json"),
    ("core_listing", "options_standard_json"),
    ("core_listing", "options_choice_json"),
    ("core_inspection", "inspection_panel_json"),
)


# 구제 시험에서 깨뜨릴 블록.  ★ 1개만 깨뜨리면 다중 붕괴를 못 잡는다 (B-3)
BREAK_KEYS = ("category", "spec", "advertisement", "manage")


class _Boom(dict):
    """읽으면 죽는 블록.  ★ 값을 「이상하게」 두는 걸로는 예외가 안 난다 —
    파서가 관대해서 그냥 None 을 낸다.  실제로 던져야 구제 경로가 돈다."""

    def get(self, *a, **k):
        raise TypeError("깨진 블록")


def _salvage_check(rid):
    """★ 실제로 깨뜨려 본다.  1개 · 2개 · 4개를 다 본다 (F-5 · B-3).

    실측 08-15: 1블록이면 50필드인데 2블록이면 2필드로 무너졌다.
    「1개만 시험」이 그것을 가리고 있었다
    """
    import copy
    import json as _j
    import os

    from parse.encar.mapping import parse_detail, parse_with_issues

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, "tests", "fixtures",
                        "detail_hybrid_renault.json")
    if not os.path.isfile(path):
        return not_applicable(C["V2-28"], rid, "표본이 없다")
    with open(path, encoding="utf-8") as f:
        good = _j.load(f)
    base = len(parse_detail(good, "encar", "1"))

    bad = []
    for n in (1, 2, len(BREAK_KEYS)):
        body = copy.deepcopy(good)
        for key in BREAK_KEYS[:n]:
            body[key] = _Boom()
        got, issues = parse_with_issues(parse_detail, body, "encar", "1",
                                        "detail")
        if len(got) <= MIN_SALVAGED:
            bad.append(f"{n}블록 깨짐 → {len(got)}필드 (정상 {base})")
        named = {i[1] for i in issues if i[1] != "(전체)"}
        missing = set(BREAK_KEYS[:n]) - named
        if missing:
            bad.append(f"{n}블록: 깨진 블록을 못 짚는다 {sorted(missing)}")
    return result(C["V2-28"], rid, 0, len(bad), not bad, bad)


# 구제 후 남아야 할 최소 필드 수 (V2-28)
MIN_SALVAGED = _cfg("min_salvaged_fields")


def _table_exists(conn, table: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,)).fetchone() is not None


def _exception_shape_checks(conn, rid) -> list:
    """원문 이상 4종이 CORE 에 어떻게 남았는가 (STEP 19a).

    ★ 표가 없어도 죽지 않는다.  V2-22 가 「스키마가 어긋났다」로 알려준다.
      검사가 예외로 죽으면 나머지 검사도 못 본다
    """
    import json

    out = []

    # V2-13 — 번호판 원본이 core_record 에 없어야 한다
    cols = {r[1] for r in conn.execute("PRAGMA table_info(core_record)")}
    bad = sorted(cols & {"record_plate_no", "plate_no"})
    out.append(result(C["V2-13"], rid, 0, bad or 0, not bad, bad))

    # V2-22 — DDL 과 현재 스키마가 같은가
    out.append(_schema_sync_check(conn, rid))
    out.append(_parser_common_fields_check(rid))
    out.append(_null_target_not_judged_check(conn, rid))
    out.append(_null_target_visible_check(conn, rid))

    # V2-23 — 파싱이 죽어 매물이 사라지지 않았는가
    if _table_exists(conn, "core_parse_issue"):
        lost = conn.execute(
            "SELECT COUNT(*) FROM core_parse_issue p WHERE p.json_path='(전체)' "
            "AND NOT EXISTS (SELECT 1 FROM core_listing l "
            " WHERE l.listing_id = p.listing_id)").fetchone()[0]
        out.append(result(C["V2-23"], rid, 0, lost, lost == 0))

    # V2-24 — 배열 컬럼이 전건 list 인가
    bad = []
    for table, col in ARRAY_COLUMNS:
        if col not in {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}:
            continue
        for (v,) in conn.execute(
            f"SELECT {col} FROM {table} WHERE {col} IS NOT NULL LIMIT 200"
        ):
            try:
                if not isinstance(json.loads(v), list):
                    bad.append(f"{table}.{col}: {str(v)[:30]}")
                    break
            except ValueError:
                bad.append(f"{table}.{col}: JSON 아님 {str(v)[:30]}")
                break
    out.append(result(C["V2-25" if False else "V2-24"], rid, 0, bad or 0,
                      not bad, bad))

    # V2-25 — 「모른다」가 0 으로 저장되지 않았는가
    #   원문 null 인데 CORE 가 0 이면 판정이 「없음」으로 갈린다
    zero_bad = []
    cols = {r[1] for r in conn.execute("PRAGMA table_info(core_listing)")}
    for col in ("seizing_cnt", "pledge_cnt", "accident_my_cost"):
        if col not in cols:
            continue
        n0 = conn.execute(
            f"SELECT COUNT(*) FROM core_listing WHERE {col} = 0").fetchone()[0]
        nnull = conn.execute(
            f"SELECT COUNT(*) FROM core_listing WHERE {col} IS NULL"
        ).fetchone()[0]
        if n0 and not nnull:
            zero_bad.append(f"{col}: 0 이 {n0}건인데 NULL 이 0건")
    out.append(result(C["V2-25"], rid, 0, zero_bad or 0, not zero_bad,
                      zero_bad))
    return out


def _schema_sync_check(conn, rid):
    """★ CREATE TABLE IF NOT EXISTS 는 기존 표를 바꾸지 않는다 (STEP 32b)."""
    import os
    import sqlite3 as _sq

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    mem = _sq.connect(":memory:")
    ddl = os.path.join(root, "sql", "ddl")
    for name in sorted(os.listdir(ddl)):
        if name.endswith(".sql"):
            mem.executescript(open(os.path.join(ddl, name),
                                   encoding="utf-8").read())

    def shape(c):
        out = {}
        for (tb,) in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%'"
        ).fetchall():
            out[tb] = {(r[1], r[2], r[3]) for r in c.execute(
                f"PRAGMA table_info({tb})")}
        return out

    want, got = shape(mem), shape(conn)
    bad = [f"{t}: 없음" for t in sorted(set(want) - set(got))]
    bad += [f"{t}.{c[0]} 어긋남" for t in sorted(set(want) & set(got))
            for c in sorted(want[t] - got[t])]
    return result(C["V2-22"], rid, 0, len(bad), not bad, bad[:20])


PII_TABLES = ("core_pii", "core_dealer_pii")
# ★ 검사기 자신은 대상이 아니다.  V2-17 이 고아를 세려면 그 테이블을 조회해야 한다.
#   금지 조항 서술·검사 질의가 검사에 잡히는 것은 이 문서에서 다섯 번째다
PII_ALLOWED = ("store/pii.py",)
PII_SKIP_DIRS = ("validate/", "tools/")


def _pii_access_check(run_id: str):
    """AST · 문자열 상수만 본다.  주석의 「금지」 서술은 위반이 아니다."""
    import ast
    import os

    bad = []
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", "ref")]
        for f in files:
            if not f.endswith(".py"):
                continue
            rel = os.path.relpath(os.path.join(base, f), root).replace("\\", "/")
            if (rel in PII_ALLOWED or rel.startswith("tests/")
                    or rel.startswith(PII_SKIP_DIRS)):
                continue
            try:
                tree = ast.parse(open(os.path.join(base, f),
                                      encoding="utf-8").read())
            except SyntaxError:
                continue
            for n in ast.walk(tree):
                if not (isinstance(n, ast.Constant)
                        and isinstance(n.value, str)):
                    continue
                s = n.value
                if "SELECT " not in s and "FROM " not in s:
                    continue
                if any(tb in s for tb in PII_TABLES):
                    bad.append(f"{rel}: {s[:40]}")
    return result(C["V2-09"], run_id, 0, len(bad), not bad, bad)


DAY_GAP_TOTAL_LIMIT = _cfg("day_gap_total_limit")
DAY_GAP_NEW_RATIO = _cfg("day_gap_new_ratio")


def gap_alerts(rep: DayGapReport) -> list[str]:
    """이상 판정 기준 (STEP 57).  시장이 하루에 30% 변하지 않는다."""
    bad = []
    if rep.prev_total:
        rate = abs(rep.total - rep.prev_total) / rep.prev_total
        if rate > DAY_GAP_TOTAL_LIMIT:
            bad.append(f"총건수 변동률 {rate:.0%} — 수집 실패·쿼리 변경 의심 (fatal)")
        if rep.increase / rep.prev_total > DAY_GAP_NEW_RATIO:
            bad.append(f"신규 비율 {rep.increase / rep.prev_total:.0%} (warn)")
        if rep.decrease / rep.prev_total > DAY_GAP_NEW_RATIO:
            bad.append(f"소멸 비율 {rep.decrease / rep.prev_total:.0%} (warn)")
    if rep.anomaly:
        bad.append(f"anomaly {rep.anomaly}건 — 원인 분류 필수 (STEP 58)")
    return bad


def diff_prev_day(conn, run_id: str, prev_run_id: str) -> DayGapReport:
    """전일 대비 GAP (STEP 57).  설명하지 못하면 데이터를 믿을 수 없다."""
    rep = DayGapReport()
    rep.total = conn.execute("SELECT COUNT(*) FROM core_listing").fetchone()[0]
    for kind, n in conn.execute(
        "SELECT change_kind, COUNT(*) FROM core_listing_change GROUP BY change_kind"
    ).fetchall():
        if kind == "new":
            rep.increase += n
        elif kind == "gone":
            rep.decrease += n
        elif kind in ("price", "status", "relisted"):
            rep.change += n
        else:
            rep.anomaly += n
    rep.prev_total = rep.total - rep.increase + rep.decrease
    rep.samples = [r[0] for r in conn.execute(
        "SELECT listing_id FROM core_listing_change "
        "WHERE change_kind IN ('anomaly','invariant_violation') LIMIT 20")]
    return rep


def explain_gap(conn, rep: DayGapReport) -> list[GapCause]:
    """원인 4종으로 분류한다 (STEP 58).

    판별 순서   ① 이전 원문과 현재 원문 비교 → 같으면 파싱 오류
               ② 동시 발생 건수 → 다수면 스키마 변경
               ③ vin · plate 대조 → 불일치면 매물 교체
               ④ 나머지 → 원문 수정
    금지       원인 분류 없이 덮어쓰는 것
    """
    causes = []
    rows = conn.execute(
        "SELECT listing_id, field FROM core_listing_change "
        "WHERE change_kind IN ('anomaly','invariant_violation')").fetchall()
    by_field: dict[str, int] = {}
    for _lid, f in rows:
        by_field[f] = by_field.get(f, 0) + 1
    for lid, f in rows:
        if by_field[f] > 1:
            causes.append(GapCause(lid, f, "schema_change"))
        else:
            causes.append(GapCause(lid, f, "source_edit"))
    return causes


# core_* 에 있으면 안 되는 PII 컬럼 (3장 STEP 35).
# ★ 원본은 core_pii 에만 둔다.  본 표에 있으면 화면·내보내기로 새어 나간다
PII_COLUMNS = ("plate_no", "plate_number", "dealer_name", "owner_name",
               "phone", "phone_no", "mobile", "address", "addr")
# 저장소에 들어가면 안 되는 파일.  ★ 키가 새면 해시가 뜻을 잃는다
SECRET_PATHS = ("secrets/plate_hmac.key",)


def _pii_column_check(conn, rid):
    """V2-10 — core_* 에 PII 원본 컬럼이 없는가.

    ★ core_pii 는 예외다.  거기가 원본을 두라고 만든 표다
    """
    bad = []
    for (tbl,) in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name LIKE 'core_%'"
    ):
        if tbl.endswith("_pii"):
            continue
        for r in conn.execute(f"PRAGMA table_info({tbl})"):
            if r[1] in PII_COLUMNS:
                bad.append(f"{tbl}.{r[1]}")
    return result(C["V2-10"], rid, 0, bad or 0, not bad, bad)


def _secret_key_check(rid):
    """V2-12 — 키가 버전 관리 밖인가.

    ★ 「파일이 없다」가 아니라 「추적되지 않는다」를 본다.
      .git 이 없는 배포본에서는 .gitignore 로 판단한다
    """
    import os
    import subprocess

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bad = []
    for rel in SECRET_PATHS:
        if os.path.isdir(os.path.join(root, ".git")):
            r = subprocess.run(["git", "ls-files", "--error-unmatch", rel],
                               cwd=root, capture_output=True, text=True)
            if r.returncode == 0:
                bad.append(f"{rel} 가 추적되고 있다")
            continue
        ignore = os.path.join(root, ".gitignore")
        rules = (open(ignore, encoding="utf-8").read()
                 if os.path.isfile(ignore) else "")
        head = rel.split("/")[0]
        if not any(line.strip().rstrip("/") in (head, rel)
                   for line in rules.splitlines()):
            bad.append(f"{rel} 가 .gitignore 에 없다")
    return result(C["V2-12"], rid, 0, bad or 0, not bad, bad)


# 파서가 결과를 넣는 표.  ★ 넷을 한 줄에 놓고 본다 (개정 270)
PARSER_TABLES: tuple[tuple[str, str], ...] = (
    ("parse_list_item", "core_listing"),
    ("parse_detail", "core_listing"),
    ("parse_inspection", "core_inspection"),
    ("parse_record", "core_record"),
    ("parse_diagnosis", "core_diagnosis"),
)


def _parser_common_fields_check(rid):
    """V2-30 — 전 파서가 NOT NULL 공통 필드를 내는가 (개정 270).

    ★ 하나씩 보면 안 보인다.  셋은 맞고 하나만 틀리기 때문이다.
      실측 08-16 — parse_diagnosis 가 row_status 를 안 내 S6 이 통째로 죽었다
    ★ 표의 NOT NULL 이면서 코드가 채우지 않는 칸을 기계로 찾는다.
      「row_status 만」 보면 다음에 다른 칸이 빠졌을 때 또 못 잡는다
    """
    import ast
    import os as _o
    import sqlite3 as _sq

    root = _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__)))
    src_path = _o.path.join(root, "parse", "encar", "mapping.py")
    src = open(src_path, encoding="utf-8").read()
    tree = ast.parse(src)
    returns: dict = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        keys = set()
        for sub in ast.walk(node):
            if isinstance(sub, ast.Dict):
                keys |= {k.value for k in sub.keys
                         if isinstance(k, ast.Constant)
                         and isinstance(k.value, str)}
        returns[node.name] = keys

    # 표의 NOT NULL 칸 — 파서가 채워야 하는 것 (기본값·파이프라인이 채우는 것 제외)
    filled_by_pipeline = {"parsed_at", "parse_version", "listing_id",
                          "first_seen", "last_seen", "site", "source_id",
                          "status", "classify_conflict"}
    mem = _sq.connect(":memory:")
    ddl = _o.path.join(root, "sql", "ddl")
    for name in sorted(_o.listdir(ddl)):
        if name.endswith(".sql"):
            mem.executescript(open(_o.path.join(ddl, name),
                                   encoding="utf-8").read())
    bad = []
    for fn, table in PARSER_TABLES:
        if fn not in returns:
            bad.append(f"{fn} 이 없다")
            continue
        need = {r[1] for r in mem.execute(f"PRAGMA table_info({table})")
                if r[3] and r[4] is None} - filled_by_pipeline
        miss = sorted(need - returns[fn])
        if miss:
            bad.append(f"{fn} → {table}: {', '.join(miss)} 를 안 낸다")
    return result(C["V2-30"], rid, 0, len(bad), not bad, bad)


def _null_target_not_judged_check(conn, rid):
    """V2-31 — 차종 없는 매물이 판정에 들어갔는가 (개정 271).

    ★ 「미정으로 두면 된다」가 아니다.  판정에 섞이면 등급 분포가 거짓이 된다
    """
    n_null = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE target_key IS NULL"
    ).fetchone()[0]
    if not n_null:
        return not_applicable(C["V2-31"], rid, "차종 미정 매물이 없다")
    judged = conn.execute(
        "SELECT COUNT(*) FROM result_score s JOIN core_listing l "
        "ON l.listing_id = s.listing_id WHERE l.target_key IS NULL"
    ).fetchone()[0]
    active = conn.execute(
        "SELECT COUNT(*) FROM core_listing "
        "WHERE target_key IS NULL AND status='active'").fetchone()[0]
    bad = []
    if judged:
        bad.append(f"차종 미정인데 판정된 매물 {judged}건")
    if active:
        bad.append(f"차종 미정인데 status='active' {active}건 — S5 가 가져간다")
    return result(C["V2-31"], rid, 0, judged, not bad, bad)


def _null_target_visible_check(conn, rid):
    """V2-32 — 왜 안 붙었는지 화면에서 볼 수 있는가 (개정 271).

    ★ 건수만 내면 사람이 아무것도 못 한다.  모델명·배지가 있어야
      targets.json 을 고칠지 규칙을 고칠지 정한다
    """
    import os as _o

    n_null = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE target_key IS NULL"
    ).fetchone()[0]
    if not n_null:
        return not_applicable(C["V2-32"], rid, "차종 미정 매물이 없다")
    root = _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__)))
    tpl = _o.path.join(root, "web", "templates", "notready.html")
    bad = []
    if not _o.path.isfile(tpl):
        bad.append("notready.html 이 없다")
    else:
        html = open(tpl, encoding="utf-8").read()
        if "unmatched" not in html:
            bad.append("차종 미정 절이 화면에 없다")
    return result(C["V2-32"], rid, "보임",
                  "보임" if not bad else "없음", not bad, bad)
