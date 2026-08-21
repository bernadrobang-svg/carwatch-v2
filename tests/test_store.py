# -*- coding: utf-8 -*-
"""3장 테이블 시험.

지시서   STEP 29 (이력 · 불변 필드) · STEP 30 (키) · STEP 32 (NULL 3종)
         STEP 36 (사전) · STEP 39 (제약) · 4장 STEP 45 (충돌 · 미분류)
사용     python3 tests/test_store.py
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import re
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from errors import ValidationError  # noqa: E402
from store.core import (  # noqa: E402
    load_snapshot,
    resolve_listing_id,
    mark_gone,
    serialize_container,
    upsert_core,
)
from store.dictionary import (  # noqa: E402
    assert_no_unknown,
    normalize_enum,
    upsert_enum,
    upsert_option3,
)
from store.raw import open_db  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T1, T2 = "2026-08-10T00:00:00", "2026-08-11T00:00:00"
FAIL: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{'  ' + detail if detail else ''}")
    if not ok:
        FAIL.append(name)


def seed(conn, **kw) -> dict:
    d = base(**kw)
    d["listing_id"] = resolve_listing_id(conn, d["site"], d["source_id"], T1)
    return d


def base(**kw) -> dict:
    d = {
        "site": "encar", "source_id": "1",
        "target_key": "G80_25T", "price_current_won": 50000000,
        "displacement_cc": 2497, "sales_status": "ADVERTISE",
        "status": "active", "row_status": "ok",
        "seizing_cnt": 0, "pledge_cnt": 0,
        "color_ext_raw": "블랙", "color_ext_hex": "#000",
        "sell_type": "일반", "plate_hash": "a1b2c3d4e5f60718",
        "ad_body_text": "",
        "price_origin_won": 70000000, "year_month": "2023-05",
        "mileage_km": 30000, "warranty_body_month": 60, "warranty_body_km": 100000,
        "warranty_power_month": 60, "warranty_power_km": 100000,
    }
    d.update(kw)
    return d


def db():
    d = tempfile.mkdtemp()
    return open_db(os.path.join(d, "t.db"), os.path.join(ROOT, "sql", "ddl"))


# ── DDL (STEP 28 · 39) ───────────────────────────────────────────────
def test_schema() -> None:
    conn = db()
    # ★ sqlite_sequence 는 AUTOINCREMENT 가 있으면 SQLite 가 스스로 만든다.
    #   우리 표가 아니다 — DDL 과 견줄 때 빼야 수가 맞는다
    names = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%'")}
    # ★ 수를 소스에 박지 않는다.  DDL 이 정본이다 —
    #   박아 두면 표가 하나 늘 때마다 시험이 규격 변경을 막는다.
    #   실측 08-19 — watch_note 를 더하자 「44개 생성」이 틀렸다고 했다
    want = len(re.findall(r"CREATE TABLE(?: IF NOT EXISTS)? (\w+)",
                          "\n".join(
                              open(os.path.join(ROOT, "sql", "ddl", f),
                                   encoding="utf-8").read()
                              for f in sorted(os.listdir(
                                  os.path.join(ROOT, "sql", "ddl")))
                              if f.endswith(".sql"))))
    check(f"DDL 의 표 {want}개가 다 생긴다", len(names) == want,
          f"{len(names)}개")
    # ★ 2026-08-14 실측으로 원문 582건 확보 — 스키마가 확정됐다 (STEP 21b)
    check("core_diagnosis · _item 이 있다",
          {"core_diagnosis", "core_diagnosis_item"} <= names)

    conn.execute("INSERT INTO core_listing(site,source_id,status,first_seen,"
                 "last_seen,row_status) VALUES ('encar','9','active','a','a','ok')")
    try:
        conn.execute("UPDATE core_listing SET status='zzz'")
        check("status CHECK 제약", False)
    except sqlite3.IntegrityError:
        check("status CHECK 제약", True)
    try:
        conn.execute("INSERT INTO core_listing(site,source_id,status,"
                     "first_seen,last_seen,row_status) "
                     "VALUES ('encar','9','active','a','a','ok')")
        check("(site, source_id) UNIQUE", False)
    except sqlite3.IntegrityError:
        check("(site, source_id) UNIQUE", True)
    try:
        conn.execute("INSERT INTO result_score"
                     "(listing_id,calc_version,dict_version,score_total,denominator,"
                     # ★ 개정 433 — F·G 는 이제 진짜 등급이다.  'Z' 로 잰다
                     "grade,calculated_at) VALUES (1,'v1','d1',400,555,'Z','a')")
        check("grade CHECK — 8단계 + 제외·등급없음·평가불가 11값", False)
    except sqlite3.IntegrityError:
        check("grade CHECK — 8단계 + 제외·등급없음·평가불가 11값", True)


# ── STEP 30 키 ───────────────────────────────────────────────────────
def test_key() -> None:
    conn = db()
    a = resolve_listing_id(conn, "encar", "42473896", T1)
    b = resolve_listing_id(conn, "encar", "42473896", T1)
    check("★ 자연키 → 대리키.  같은 자연키는 같은 번호", a == b and isinstance(a, int))
    c = resolve_listing_id(conn, "encar", "999", T1)
    check("다른 자연키는 다른 번호", c != a)
    check("PK 를 문자열로 조립하지 않는다", isinstance(a, int))


# ── STEP 32 NULL 3종 ─────────────────────────────────────────────────
def test_null_three() -> None:
    check("빈 배열은 '[]' 로 저장", serialize_container([]) == "[]")
    check("None 은 None", serialize_container(None) is None)
    check("빈 dict 는 '{}'", serialize_container({}) == "{}")


# ── STEP 29 이력 ─────────────────────────────────────────────────────
def test_change_history() -> None:
    conn = db()
    upsert_core(conn, seed(conn), T1)
    n = upsert_core(conn, seed(conn, price_current_won=48000000), T2)
    check("가격 변경 1건 기록", n == 1)
    row = conn.execute(
        "SELECT field, old_value, new_value, change_kind FROM core_listing_change"
        " WHERE change_kind='price'").fetchone()
    check("변경 내용이 남는다",
          row == ("price_current_won", "50000000", "48000000", "price"), str(row))

    n2 = upsert_core(conn, seed(conn, price_current_won=48000000), T2)
    check("값이 같으면 이력이 늘지 않는다", n2 == 0)

    mark_gone(conn, 1, T2)
    g = conn.execute(
        "SELECT status, gone_at, last_price_won FROM core_listing").fetchone()
    check("gone 은 삭제가 아니다.  gone_at · last_price_won 이 남는다",
          g == ("gone", T2, 48000000), str(g))


def test_invariant_violation() -> None:
    conn = db()
    upsert_core(conn, seed(conn), T1)
    try:
        upsert_core(conn, seed(conn, displacement_cc=1999), T2)
        check("불변 필드 변경 → ValidationError", False)
    except ValidationError:
        check("불변 필드 변경 → ValidationError", True)
    kind = conn.execute(
        "SELECT change_kind FROM core_listing_change"
        " WHERE field='displacement_cc'").fetchone()
    check("invariant_violation 으로 기록", kind == ("invariant_violation",), str(kind))
    keep = conn.execute(
        "SELECT displacement_cc FROM core_listing").fetchone()
    check("조용히 덮어쓰지 않는다", keep == (2497,), str(keep))


# ── DTO (STEP 34 · 0장 STEP 1) ───────────────────────────────────────
def test_snapshot() -> None:
    conn = db()
    upsert_core(conn, seed(conn, options_choice_json="[]",
                           options_standard_json=json.dumps(["010", "095"])), T1)
    conn.execute(
        "INSERT INTO core_inspection(listing_id,site,inspection_panel_json,row_status)"
        " VALUES (1,'encar',?,'ok')",
        (json.dumps([{"type": {"code": "P022"}, "attributes": ["RANK_ONE"]}]),))
    conn.commit()
    s = load_snapshot(conn, 1)
    check("DTO 로 넘어온다", s.listing_id == 1 and s.target_key == "G80_25T")
    check("빈 배열이 [] 로 살아온다 (NULL 아님)", s.options_choice == [])
    check("점검 원문 배열 그대로", s.inspection_panels[0]["attributes"] == ["RANK_ONE"])
    check("이력 미확보 → None (수집 실패와 구분은 status 컬럼)",
          s.accident_my_cnt is None)
    # ★ 개정 365 — ⑤ 사이트 보증의 근거는 이름이 site_ 로 시작하지 않는다
    #   (platform_verified · warranty_deemed …).  그것만 더 담는다
    from store.core import SITE_WARRANTY_FIELDS

    check("site_flags 는 site_* 와 보증 근거만",
          all(k.startswith("site_") or k in SITE_WARRANTY_FIELDS
              for k in s.site_flags))


# ── 사전 (STEP 36 · 4장 STEP 45) ─────────────────────────────────────
def test_dictionary() -> None:
    conn = db()
    # 원문 관측값 축(panel)은 pending 으로 들어간다.
    # facet 이 선언한 열거값(fuel 등)은 confirmed 다 — 축별 정책은 4장 시험이 본다
    r = upsert_enum(conn, "encar", "panel", "프론트 휀더(우)", "프론트 휀더(우)", 344,
                    "inspection", "d1", T1)
    check("신규 값 → pending 적재", r == "new")
    st = conn.execute("SELECT status FROM dict_enum").fetchone()
    check("unknown 이 아니라 pending", st == ("pending",), str(st))

    try:
        assert_no_unknown(conn, "encar", "panel")
        check("pending 있으면 판정 중단", False)
    except ValidationError:
        check("pending 있으면 판정 중단", True)

    check("normalize_enum — pending 은 반환하지 않는다",
          normalize_enum(conn, "encar", "panel", "프론트 휀더(우)") is None)
    check("사전에 없는 값 → None (추정 금지)",
          normalize_enum(conn, "encar", "panel", "프론트펜더") is None)

    conn.execute("UPDATE dict_enum SET status='confirmed'")
    conn.commit()
    assert_no_unknown(conn, "encar", "panel")
    check("confirmed 만 남으면 통과", True)
    check("confirmed 는 정규화된다",
          normalize_enum(conn, "encar", "panel", "프론트 휀더(우)") == "프론트 휀더(우)")

    upsert_option3(conn, "encar", "G80_25T", "095", "헤드업 디스플레이(HUD)", 10, "d1", T1)
    upsert_option3(conn, "encar", "MODEL_Y", "095", "헤드업 디스플레이(HUD)", 3, "d1", T1)
    check("3자리 코드는 차종 간 공통 — 같은 이름이면 통과", True)
    try:
        upsert_option3(conn, "encar", "KOLEOS_HEV", "095", "다른 이름", 1, "d1", T1)
        check("3자리 코드 충돌 → 중단 (STEP 45)", False)
    except ValidationError:
        check("3자리 코드 충돌 → 중단 (STEP 45)", True)


if __name__ == "__main__":
    print("3장 테이블 시험")
    test_schema()
    test_key()
    test_null_three()
    test_change_history()
    test_invariant_violation()
    test_snapshot()
    test_dictionary()
    print()
    print("결과:", "통과" if not FAIL else "실패 — " + " / ".join(FAIL))
    sys.exit(1 if FAIL else 0)
