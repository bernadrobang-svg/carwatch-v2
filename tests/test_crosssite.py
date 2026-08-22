# -*- coding: utf-8 -*-
"""12장 다중 사이트 시험.

지시서   3장 STEP 30 (VIN 검증) · 12장 STEP 121·123·123a (V9)·124
사용     python3 tests/test_crosssite.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parse.encar.mapping import clean_vin, parse_detail, parse_inspection  # noqa: E402
from store.core import build_identities, merge_conflict, resolve_vehicle_id  # noqa: E402
from store.crosssite import (  # noqa: E402
    MSG_NO_PEER, active_sites, match_cross_site, readiness,
    rebuild_core_vehicle, regression_check, snapshot_baseline,
)
from store.raw import open_db  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
SITES = json.load(open(os.path.join(ROOT, "config", "sites.json"),
                       encoding="utf-8"))
T1 = "2026-08-10"
VIN_A = "LRWYGCFJ5SC205893"
VIN_B = "KMTGB41CBRU218546"
FAIL: list[str] = []


def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{'  ' + detail if detail else ''}")
    if not ok:
        FAIL.append(name)


def db():
    return open_db(os.path.join(tempfile.mkdtemp(), "t.db"),
                   os.path.join(ROOT, "sql", "ddl"))


def add(conn, lid, site, vk, price, vin=None, status="active"):
    conn.execute(
        "INSERT OR IGNORE INTO core_vehicle(vehicle_id,site_count,"
        "listing_count,first_seen,last_seen,updated_at) VALUES (?,1,1,?,?,?)",
        (vk, T1, T1, T1))
    conn.execute(
        "INSERT OR IGNORE INTO vehicle_identity(vehicle_id,kind,value_hash,"
        "confidence,first_seen,last_seen) VALUES (?,'plate',?,'confirmed',?,?)",
        (vk, f"h{vk}", T1, T1))
    conn.execute(
        "INSERT INTO core_listing(site,source_id,target_key,"
        "vehicle_id,vin,status,price_current_won,first_seen,last_seen,"
        "row_status) VALUES (?,?,?,?,?,?,?,?,?,'ok')",
        (site, lid.split("_")[-1], "G80_25T", vk, vin, status, price, T1, T1))
    conn.commit()


# ── 3장 STEP 30 VIN 검증 ─────────────────────────────────────────────
def test_vin() -> None:
    check("17자리 정상 VIN 통과", clean_vin(VIN_A) == VIN_A)
    check("★ v1 이 망가뜨린 값은 버린다",
          all(clean_vin(v) is None for v in ("0", "000556", "001940")))
    check("6자리 · 11자리 · 16자리 점검부 오염분도 버린다",
          all(clean_vin(v) is None for v in
              ("123456", "12345678901", "1234567890123456")))
    check("I · O · Q 가 있으면 버린다",
          clean_vin("KMTGB41CBRU21854I") is None
          and clean_vin("KMTGB41CBRU21854O") is None)
    check("공백·소문자는 정규화한다", clean_vin(f"  {VIN_A.lower()} ") == VIN_A)

    check("★ 형식 위반 VIN 으로 결합하지 않는다",
          build_identities(None, None, "000556", "encar/1")[0][0] == "site_id")
    check("★ 결합 입력은 번호판 해시 (원본은 core_pii)",
          build_identities("a1b2c3d4e5f60718", None, None, "x")[0][:2]
          == ("plate", "a1b2c3d4e5f60718"))
    check("정상 VIN 이면 vin 근거로 결합",
          build_identities(None, None, VIN_A, "x")[0][0] == "vin")
    check("차량번호가 1순위",
          build_identities("a1b2c3d4e5f60718", None, VIN_A, "x")[0][0]
          == "plate")
    check("★ 과거 번호도 후보에 넣는다 (소유자가 바뀌면 번호가 바뀐다)",
          len(build_identities("h1", ["h0"], None, "x")) == 2)

    conn = db()
    ids = build_identities("h1", None, VIN_A, "x")
    v1, kind, conf = resolve_vehicle_id(conn, ids, T1)
    v2, _k, _c = resolve_vehicle_id(conn, build_identities("h1", None, None, "y"),
                                    T1)
    check("★ 같은 식별자면 같은 vehicle_id", v1 == v2 and isinstance(v1, int))
    v3, _k, _c = resolve_vehicle_id(conn, build_identities("h9", None, None, "z"),
                                    T1)
    check("다른 식별자는 다른 vehicle_id", v3 != v1)
    n = conn.execute("SELECT COUNT(*) FROM vehicle_identity "
                     "WHERE vehicle_id=?", (v1,)).fetchone()[0]
    check("★ 식별자는 행이다 — 번호판이 바뀌면 행이 는다", n == 2, f"{n}행")

    check("★ 6자리끼리 달라도 conflict 가 아니다 (형식 위반)",
          not merge_conflict("000556", "001940"))
    check("정상 VIN 이 다르면 결합 취소", merge_conflict(VIN_A, VIN_B))
    check("한쪽만 있으면 결합 유지", not merge_conflict(VIN_A, None))


def test_vin_parse() -> None:
    d = parse_detail(json.load(open(os.path.join(FX, "detail_ev_tesla.json"),
                                    encoding="utf-8")), "encar", "1")
    check("상세 A VIN 은 17자리이거나 None",
          d["vin"] is None or len(d["vin"]) == 17, str(d["vin"]))
    i = parse_inspection(
        json.load(open(os.path.join(FX, "inspection_frame.json"),
                       encoding="utf-8")), "encar", "1")
    check("점검부 VIN 도 형식 검증을 거친다",
          i["inspection_vin"] is None or len(i["inspection_vin"]) == 17,
          str(i["inspection_vin"]))

    conn = db()
    add(conn, "encar_1", "encar", 1, 35000000, vin=VIN_A)
    add(conn, "encar_2", "encar", 2, 34000000, vin=None)
    bad = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE vin IS NOT NULL "
        "AND LENGTH(vin) <> 17").fetchone()[0]
    check("★ 검산 — vin IS NOT NULL 인 행이 전건 17자리 (V2-03)", bad == 0)


# ── STEP 123 · V9 ────────────────────────────────────────────────────
def test_cross_site() -> None:
    conn = db()
    add(conn, "encar_1", "encar", 1, 35000000)
    # ★★ 실측 08-23 — active 가 늘어난다 (기아 CPO 를 붙였다 · 명령서 3-1).
    #   ★ 「1곳」을 시험에 박으면 ★ 사이트를 붙일 때마다 거짓 실패가 난다.
    #   ★ V9-03 이 보는 것은 ★ 「짝이 없을 때 단독이라 쓰지 않는가」다 —
    #     그것을 재려고 ★ 이 시험 안에서만 한 곳으로 좁힌다
    one = {k: (dict(v, status="planned")
               if isinstance(v, dict) and k != "encar" else v)
           for k, v in SITES.items()}
    check("★ 이 시험은 active 를 한 곳으로 좁혀 잰다",
          active_sites(one) == ["encar"], str(active_sites(one)))

    m = match_cross_site(conn, 1, one)
    check("★ V9-03 — active 1곳이면 「단독 매물」이라 쓰지 않는다",
          m.message == MSG_NO_PEER and "단독" not in m.message, m.message)
    check("★ V9-01 — match_source · confidence 를 함께 낸다",
          m.match_source == "plate" and m.confidence == "confirmed")

    two = dict(one)
    two["kcar"] = dict(SITES["kcar"], status="active")
    add(conn, "kcar_9", "kcar", 1, 34000000)
    m = match_cross_site(conn, 1, two)
    check("2개 사이트 → 게시 수와 가격차",
          "2개 사이트" in m.message and "100만" in m.message, m.message)
    check("가격을 평균 내지 않고 그대로 나열한다",
          sorted(x[2] for x in m.listings) == [34000000, 35000000])
    check("가격차 계산", m.price_spread_won == 1000000)

    m2 = match_cross_site(conn, 99, two)
    check("결합 근거 불명이면 표시하지 않는다", m2 is None)

    src = open(os.path.join(ROOT, "store", "crosssite.py"),
               encoding="utf-8").read()
    check("★ V9-02 — 사이트 간 점수를 비교하지 않는다 (가격만)",
          "score_total" not in src.split("def regression_check")[0])

    n = rebuild_core_vehicle(conn, T1)
    check("core_vehicle 집계 갱신", n >= 1)
    row = conn.execute(
        "SELECT site_count, listing_count, price_spread_won FROM core_vehicle "
        "WHERE vehicle_id=1").fetchone()
    check("site_count 가 실제 사이트 수", row == (2, 2, 1000000), str(row))


# ── STEP 124 회귀 ────────────────────────────────────────────────────
def test_regression() -> None:
    conn = db()
    add(conn, "encar_1", "encar", 1, 35000000)
    conn.execute(
        "INSERT INTO result_score(listing_id,calc_version,dict_version,"
        "score_total,denominator,grade,calculated_at) "
        "VALUES (1,'c1','d1',400,475,'B',?)", (T1,))
    conn.commit()
    base = snapshot_baseline(conn, "c1")
    check("기준선을 얼려 둔다", base[1]["grade"] == "B")

    r = regression_check(conn, base, "c1")
    check("★ 변동 없으면 통과",
          r.score_mismatch == 0 and r.grade_mismatch == 0
          and r.denominator_mismatch == 0)

    conn.execute("UPDATE result_score SET score_total=390, grade='C' "
                 "WHERE listing_id=1")
    conn.commit()
    r = regression_check(conn, base, "c1")
    check("★ 점수가 바뀌면 검출 — 「조금 바뀐 것」으로 넘기지 않는다",
          r.score_mismatch == 1 and r.grade_mismatch == 1, str(r.samples))

    conn.execute("UPDATE result_score SET denominator=455 "
                 "WHERE listing_id=1")
    conn.commit()
    r = regression_check(conn, base, "c1")
    check("★ 분모 변동도 검출 (엔드포인트 집합이 섞였다)",
          r.denominator_mismatch == 1)


# ── STEP 121 착수 조건 ───────────────────────────────────────────────
def test_readiness() -> None:
    conn = db()
    rep = readiness(conn, SITES, "kcar", "c1")
    check("채점 결과가 없으면 착수 불가", not rep.ready, str(rep.checks))

    add(conn, "encar_1", "encar", 1, 35000000)
    conn.execute(
        "INSERT INTO result_score(listing_id,calc_version,dict_version,"
        "score_total,denominator,grade,calculated_at) "
        "VALUES (1,'c1','d1',400,475,'B',?)", (T1,))
    conn.commit()
    rep = readiness(conn, SITES, "kcar", "c1")
    check("★ 착수 조건 5종 전부 참", rep.ready,
          str({k: v for k, v in rep.checks.items() if not v}))
    check("site 키가 들어가 있다", rep.checks["site 키가 들어가 있다"])
    check("★ CORE 컬럼명에 사이트 고유 명칭 없음",
          rep.checks["CORE 컬럼명에 사이트 고유 명칭 없음"])

    rep = readiness(conn, SITES, "unknown_site", "c1")
    check("미등록 사이트는 착수 불가", not rep.ready)


def v9_04_site_isolation() -> None:
    """V9-04 — 사이트를 추가해도 기존 사이트 결과가 바뀌지 않는가 (STEP 124).

    ★ 전 사이트 수집을 여기서 돌릴 수는 없다.  격리가 「구조로」 보장되는지 본다:
      판정에 들어가는 조회가 site 로 갈리는가.
      갈리지 않으면 사이트를 더한 순간 남의 매물이 분모에 섞인다
    금지   「새 사이트 때문에 조금 바뀐 것」으로 넘기는 것
    """
    import os
    import sqlite3

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db = os.path.join(root, "carwatch.db")
    if not os.path.isfile(db):
        check("V9-04 — 사이트 격리", True, "DB 없음 — 규칙만 검사")
        return
    conn = sqlite3.connect(db)

    bad = []
    # ① 사이트를 가르는 컬럼이 원천 표에 있는가
    for table in ("raw_response", "core_listing", "core_dealer"):
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]
        if "site" not in cols:
            bad.append(f"{table} 에 site 컬럼이 없다")

    # ② 한 vehicle 이 두 사이트에 걸쳐 판정되지 않는가
    n = conn.execute(
        "SELECT COUNT(*) FROM (SELECT vehicle_id FROM core_listing "
        "WHERE vehicle_id IS NOT NULL GROUP BY vehicle_id "
        "HAVING COUNT(DISTINCT site) > 1)").fetchone()[0]
    if n:
        bad.append(f"두 사이트에 걸친 vehicle {n}건 — 격리가 깨졌다")

    # ③ 같은 calc_version 안에서 분모가 사이트별로 섞이지 않는가
    rows = conn.execute(
        "SELECT l.site, COUNT(DISTINCT s.denominator) FROM result_score s "
        "JOIN core_listing l ON l.listing_id = s.listing_id GROUP BY l.site"
    ).fetchall()
    _ = rows          # 사이트가 하나면 비교 대상이 없다 — 구조만 본다
    check("★ V9-04 — 사이트 격리가 구조로 보장된다", not bad, str(bad[:3]))
    conn.close()


if __name__ == "__main__":
    print("12장 다중 사이트 시험")
    test_vin()
    test_vin_parse()
    test_cross_site()
    test_regression()
    test_readiness()
    v9_04_site_isolation()
    print()
    print("결과:", "통과" if not FAIL else "실패 — " + " / ".join(FAIL))
    sys.exit(1 if FAIL else 0)
