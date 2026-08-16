# -*- coding: utf-8 -*-
"""11장 후보 추적 시험.

지시서   STEP 111 · 112 (중복 3종) · 113 · 114 · 115 · 116
핵심     ★ 같은 차량번호가 재등록이 아니다.  v1 실측 1,113그룹 중 1,111이 동시 중복
사용     python3 tests/test_watch.py
"""
from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from store.raw import open_db  # noqa: E402
from store.watch import (  # noqa: E402
    CAUSE_CALC, CAUSE_COEFFICIENT, CAUSE_DICT, CAUSE_LISTING,
    DUP_CROSS_DEALER, DUP_RELIST, DUP_SAME_DEALER, EV_GONE, EV_PRICE_DROP,
    EV_TARGET_HIT, TrackPoint, WatchEvent, classify_cause, classify_duplicates,
    deduped_count, detect_events, message, notify, snapshot, sync_duplicates,
    track_points,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T1, T2 = "2026-08-10", "2026-08-11"
FAIL: list[str] = []


def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{'  ' + detail if detail else ''}")
    if not ok:
        FAIL.append(name)


def db():
    return open_db(os.path.join(tempfile.mkdtemp(), "t.db"),
                   os.path.join(ROOT, "sql", "ddl"))


def add(conn, lid, dealer, status, price, first_seen, vk=1, gone_at=None):
    """lid 는 source_id 로 쓴다.  listing_id 는 DB 가 만든다 (STEP 30)."""
    conn.execute(
        "INSERT OR IGNORE INTO core_vehicle(vehicle_id,site_count,"
        "listing_count,first_seen,last_seen,updated_at) VALUES (?,0,0,?,?,?)",
        (vk, first_seen, first_seen, first_seen))
    conn.execute(
        "INSERT OR IGNORE INTO core_dealer(dealer_id,site,site_dealer_id,"
        "listing_count,sample_sufficient,calculated_at) VALUES (?,?,?,0,0,?)",
        (abs(hash(dealer)) % 1000 + 1, "encar", dealer, first_seen))
    did = conn.execute(
        "SELECT dealer_id FROM core_dealer WHERE site_dealer_id=?",
        (dealer,)).fetchone()[0]
    conn.execute(
        "INSERT INTO core_listing(listing_id,site,source_id,target_key,"
        "vehicle_id,dealer_id,status,price_current_won,first_seen,last_seen,"
        "gone_at,row_status,parse_version) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,'ok','p1')",
        (int(lid.split("_")[-1]), "encar", lid.split("_")[-1], "G80_25T", vk,
         did, status, price, first_seen, first_seen, gone_at))
    conn.commit()


def watch(conn, vk=1, target=None):
    conn.execute(
        # ★ login_name 은 로그인·식별용이다.  display_name 과 나뉜다 (STEP 34)
        "INSERT OR IGNORE INTO account(account_id,role,login_name,"
        "display_name,secret_hash,created_at) "
        "VALUES (1,'admin','마스터','마스터','x',?)", (T1,))
    conn.execute(
        "INSERT INTO watch_item(watch_id,account_id,vehicle_id,"
        "primary_listing_id,added_at,target_price_won) "
        "VALUES (1,1,?,1,?,?)", (vk, T1, target))
    conn.commit()


# ── STEP 112 중복 3종 ────────────────────────────────────────────────
def test_same_dealer() -> None:
    conn = db()
    add(conn, "encar_1", "D1", "active", 35000000, T1)
    add(conn, "encar_2", "D1", "active", 35000000, T1)
    d = classify_duplicates(conn, 1)
    check("★ 같은 딜러 · 둘 다 active → 동시 중복 (재등록 아님)",
          len(d) == 2 and all(x["kind"] == DUP_SAME_DEALER for x in d),
          str([x["kind"] for x in d]))
    check("재등록으로 잡히지 않는다",
          not any(x["kind"] == DUP_RELIST for x in d))
    check("대표는 1건뿐 (가장 싼 것)",
          sum(x["representative"] for x in d) == 1)

    sync_duplicates(conn, T1)
    check("★ 집계에서 1건으로 센다 (물량 부풀림 차단)",
          deduped_count(conn, "G80_25T") == 1,
          str(deduped_count(conn, "G80_25T")))


def test_cross_dealer() -> None:
    conn = db()
    add(conn, "encar_1", "D1", "active", 35000000, T1)
    add(conn, "encar_2", "D2", "active", 34000000, T1)
    d = classify_duplicates(conn, 1)
    check("★ 다른 딜러 · 둘 다 active → 딜러 간 중복",
          all(x["kind"] == DUP_CROSS_DEALER for x in d),
          str([x["kind"] for x in d]))
    check("양쪽 다 보여준다 (가격 비교 대상)",
          all(x["representative"] for x in d))
    sync_duplicates(conn, T1)
    check("딜러 간 중복은 집계에서 접지 않는다",
          deduped_count(conn, "G80_25T") == 2)


def test_relist() -> None:
    conn = db()
    add(conn, "encar_1", "D1", "gone", 35000000, T1, gone_at=T1)
    add(conn, "encar_2", "D1", "active", 34500000, T2)
    d = classify_duplicates(conn, 1)
    check("★ gone 이후 새 listing_id → 재등록",
          any(x["kind"] == DUP_RELIST for x in d), str([x["kind"] for x in d]))
    check("동시 중복으로 잡히지 않는다",
          not any(x["kind"] == DUP_SAME_DEALER for x in d))


# ── STEP 115 원인 분류 ───────────────────────────────────────────────
def tp(**kw):
    base = dict(listing_id="encar_1", run_id="r", observed_at=T1,
                price_won=35000000, listing_status="active",
                calc_version="c1", dict_version="d1", parse_version="p1",
                coefficient_id=1)
    base.update(kw)
    return TrackPoint(**base)


def test_cause() -> None:
    check("사전 변경 → dict",
          classify_cause(tp(), tp(dict_version="d2")) == CAUSE_DICT)
    check("배점 변경 → calc",
          classify_cause(tp(), tp(calc_version="c2")) == CAUSE_CALC)
    check("계수 변경 → coefficient",
          classify_cause(tp(), tp(coefficient_id=2)) == CAUSE_COEFFICIENT)
    check("가격만 바뀌면 → listing",
          classify_cause(tp(), tp(price_won=34000000)) == CAUSE_LISTING)


# ── STEP 113·114·116 ─────────────────────────────────────────────────
def _two_runs(target=None, price2=34500000, status2="active"):
    conn = db()
    add(conn, "encar_1", "D1", "active", 35000000, T1)
    watch(conn, target=target)
    conn.execute(
        "INSERT INTO result_score(listing_id,calc_version,dict_version,"
        "score_total,denominator,grade,calculated_at) "
        "VALUES (1,'c1','d1',400,475,'B',?)", (T1,))
    conn.commit()
    snapshot(conn, "run1", T1, coefficient_id=1)
    conn.execute("UPDATE core_listing SET price_current_won=?, status=? "
                 "WHERE listing_id=1", (price2, status2))
    conn.commit()
    snapshot(conn, "run2", T2, coefficient_id=1)
    return conn


def test_snapshot() -> None:
    conn = _two_runs()
    pts = track_points(conn, 1)
    check("관심 매물만 스냅샷", len(pts) == 2, f"{len(pts)}행")
    cols = [d[1] for d in conn.execute("PRAGMA table_info(watch_track)")]
    check("★ 점수를 복제하지 않는다 (버전 키만 갖는다)",
          "score_total" not in cols and "grade" not in cols
          and "calc_version" in cols)
    joined = conn.execute(
        "SELECT s.grade FROM watch_track t JOIN result_score s "
        "ON s.listing_id=t.listing_id AND s.calc_version=t.calc_version "
        "WHERE t.run_id='run2'").fetchone()
    check("버전 키로 조인해 그 시점 점수를 얻는다", joined == ("B",), str(joined))


def test_events() -> None:
    conn = _two_runs()
    ev = detect_events(conn, "run2", T2)
    check("가격 하락 감지", EV_PRICE_DROP in {e.kind for e in ev},
          str({e.kind for e in ev}))
    check("원인이 listing", all(e.cause == CAUSE_LISTING for e in ev))
    n = notify(conn, ev)
    check("가격 하락은 기본 알림", n["sent"] >= 1, str(n))
    n2 = notify(conn, ev)
    check("★ 같은 실행에서 반복 발송하지 않는다",
          n2["sent"] == 0 and n2["skipped_duplicate"] >= 1, str(n2))

    conn = _two_runs(status2="gone")
    check("gone 감지",
          EV_GONE in {e.kind for e in detect_events(conn, "run2", T2)})

    conn = _two_runs(target=34600000)
    check("목표가 도달 감지",
          EV_TARGET_HIT in {e.kind for e in detect_events(conn, "run2", T2)})


def test_cause_gate() -> None:
    """★ 규칙 변경은 알리지 않는다 (STEP 115)."""
    conn = _two_runs()
    conn.execute("UPDATE watch_track SET calc_version='c2' WHERE run_id='run2'")
    conn.commit()
    ev = detect_events(conn, "run2", T2)
    check("배점 변경이면 cause=calc",
          all(e.cause == CAUSE_CALC for e in ev), str([e.cause for e in ev]))
    n = notify(conn, ev)
    check("★ cause != listing 이면 발송하지 않는다",
          n["sent"] == 0 and n["skipped_cause"] >= 1, str(n))


# ── STEP 111·116 문구 ────────────────────────────────────────────────
def test_message() -> None:
    e = WatchEvent(1, 1, "r", EV_PRICE_DROP, "34700000",
                   "34200000", CAUSE_LISTING, T1)
    check("가격 하락 문구", message(e) == "3,470만 → 3,420만 (−50만)", message(e))

    e = WatchEvent(1, 1, "r", EV_GONE, "active", "gone",
                   CAUSE_LISTING, T1)
    m = message(e, last_price=34200000, gone_at="2026-08-09")
    check("★ 「목록에서 사라짐」 — 「판매되었습니다」가 아니다",
          "목록에서 사라짐" in m and "판매" not in m, m)
    check("마지막 가격과 시각을 함께 낸다",
          "3,420만" in m and "2026-08-09" in m, m)

    e = WatchEvent(1, 1, "r", "relist", None, None, CAUSE_LISTING, T1)
    check("재등록 문구에 결합 근거",
          "차량번호" in message(e, key_source="차량번호"))

    import ast

    src = open(os.path.join(ROOT, "store", "watch.py"), encoding="utf-8").read()
    ddl = open(os.path.join(ROOT, "sql", "ddl", "07_watch.sql"),
               encoding="utf-8").read()
    # 주석·독스트링의 「금지」 서술은 위반이 아니다.  SQL 문자열만 본다
    sql = [n.value for n in ast.walk(ast.parse(src))
           if isinstance(n, ast.Constant) and isinstance(n.value, str)
           and ("SELECT " in n.value or "INSERT " in n.value
                or "UPDATE " in n.value)]
    check("★ sold_price · sold_at 을 만들지 않는다",
          not any("sold_" in s for s in sql)
          and "sold_price" not in ddl and "sold_at" not in ddl,
          str([s[:30] for s in sql if "sold_" in s]))
    check("alert_on_sold → on_gone · on_relist",
          "on_gone" in ddl and "on_relist" in ddl and "alert_on_sold" not in ddl)


if __name__ == "__main__":
    print("11장 후보 추적 시험")
    test_same_dealer()
    test_cross_dealer()
    test_relist()
    test_cause()
    test_snapshot()
    test_events()
    test_cause_gate()
    test_message()
    print()
    print("결과:", "통과" if not FAIL else "실패 — " + " / ".join(FAIL))
    sys.exit(1 if FAIL else 0)
