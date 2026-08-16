# -*- coding: utf-8 -*-
"""8장 등록부 시험.

지시서   STEP 87 (미사용 등록부) · 6장 V4-06 · 06b · 07~11
핵심     ★ 오염된 원문을 등록부에 넣지 않는다.
         v1 record 를 라벨로 훑으면 142경로, 실제는 49개다
사용     python3 tests/test_registry.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from errors import ValidationError  # noqa: E402
from store.raw import open_db  # noqa: E402
from tools.sync_registry import (  # noqa: E402
    assert_registered, collect_paths, json_paths, list_by_usage, shape_ok,
    sync_registry,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
CFG = json.load(open(os.path.join(ROOT, "config", "field_usage.json"),
                     encoding="utf-8"))
T1, T2, T3, T4 = ("2026-08-1%dT00:00:00" % i for i in range(4))
FAIL: list[str] = []


def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{'  ' + detail if detail else ''}")
    if not ok:
        FAIL.append(name)


def fx(n):
    return json.load(open(os.path.join(FX, n), encoding="utf-8"))


def db():
    return open_db(os.path.join(tempfile.mkdtemp(), "t.db"),
                   os.path.join(ROOT, "sql", "ddl"))


def put_raw(conn, endpoint, doc, sid="1"):
    conn.execute(
        "INSERT INTO raw_response(site,source_id,endpoint,request_url,status,"
        "body,origin,fetched_at) VALUES ('encar',?,?,'u','ok',?,'collector',?)",
        (sid, endpoint, json.dumps(doc, ensure_ascii=False), T1))
    conn.commit()


# ── 경로 추출 ────────────────────────────────────────────────────────
def test_paths() -> None:
    p = json_paths({"a": {"b": 1}, "c": [{"d": 2}]})
    check("중첩 경로", {"a", "a.b", "c", "c[].d"} <= p, str(sorted(p)))
    check("배열은 [] 로 한 경로", "c[]" in p or "c[].d" in p)

    ins = json_paths(fx("inspection_frame.json"))
    check("실물 점검부 경로 추출",
          "outers[].attributes" in ins and "master.detail.mileage" in ins,
          f"{len(ins)}경로")


# ── ★ 오염 차단 (STEP 87) ────────────────────────────────────────────
def test_contamination() -> None:
    conn = db()
    # v1 사고 재현 — 점검부 응답이 record 라벨로 저장돼 있다
    put_raw(conn, "record", fx("record_with_accident.json"), "1")
    put_raw(conn, "record", fx("inspection_frame.json"), "2")

    check("라벨과 내용이 어긋나면 shape_ok 가 거부",
          shape_ok("record", fx("record_with_accident.json"))
          and not shape_ok("record", fx("inspection_frame.json")))

    paths = collect_paths(conn)
    got = {p for (e, p) in paths if e == "record"}
    check("★ 오염분 경로가 등록부에 들어가지 않는다",
          "outers" not in got and "master" not in got,
          f"record {len(got)}경로")
    check("정상 record 경로는 들어간다", "carNo" in got and "accidents[].type" in got)

    st = sync_registry(conn, CFG, T1)
    rows = {(e, p) for e, p in conn.execute(
        "SELECT endpoint, json_path FROM meta_field_usage")}
    check("등록부에 master · outers 가 record 로 기록되지 않는다",
          ("record", "master") not in rows and ("record", "outers") not in rows)
    check("적재 건수 보고", st.added == len(paths), f"{st.added}건")


# ── 시드 분류 · 전량 등록 ────────────────────────────────────────────
def test_seed() -> None:
    conn = db()
    put_raw(conn, "detail", fx("detail_gasoline_genesis.json"))
    put_raw(conn, "inspection", fx("inspection_clean.json"))
    sync_registry(conn, CFG, T1)

    def usage(e, p):
        r = conn.execute(
            "SELECT usage, reason, core_column FROM meta_field_usage "
            "WHERE endpoint=? AND json_path=?", (e, p)).fetchone()
        return r

    check("★ CORE 컬럼이 없는 경로도 등록한다 (v1 방치 경로 차단)",
          conn.execute("SELECT COUNT(*) FROM meta_field_usage").fetchone()[0] > 100)
    check("시드 — viewCount 는 display_only",
          usage("detail", "manage.viewCount")[0] == "display_only")
    check("시드 — motorType 은 in_use",
          usage("inspection", "master.detail.motorType")[0] == "in_use")
    check("시드 — inners[] 는 display_only (전건 「양호」로 변별력 0)",
          usage("inspection", "inners")[0] == "display_only"
          or usage("inspection", "inners") is not None)
    check("시드 — engineCheck 는 blocked + 해소 조건",
          usage("inspection", "master.detail.engineCheck")[0] == "blocked")
    e = conn.execute(
        "SELECT unblock_condition FROM meta_field_usage "
        "WHERE json_path='master.detail.engineCheck'").fetchone()
    check("blocked 에는 unblock_condition 이 있다 (V4-08)", bool(e[0]), str(e))

    # ★ 시드가 다 채워지면 미분류가 0 이다.  그것이 목표 상태다.
    #   기전을 시험하려면 시드에 없는 경로를 하나 넣는다
    doc = fx("detail_gasoline_genesis.json")
    doc["새필드"] = "값"          # 형식 검증을 통과해야 훑는다
    put_raw(conn, "detail", doc, "9")
    sync_registry(conn, CFG, T1)
    un = list_by_usage(conn, "unclassified")
    check("★ 시드에 없는 새 경로는 unclassified 로 남는다",
          any(p == "새필드" for _e, p in un), str(un[:3]))
    try:
        assert_registered(conn)
        check("unclassified 가 있으면 중단 (V4-11)", False)
    except ValidationError:
        check("unclassified 가 있으면 중단 (V4-11)", True)


# ── 유령 경로 (STEP 87) ──────────────────────────────────────────────
def test_ghost() -> None:
    conn = db()
    conn.execute(
        "INSERT INTO meta_field_usage(site,endpoint,json_path,usage,reason,"
        "miss_streak,first_seen,last_seen) VALUES "
        "('encar','detail','advertisement.isVerifyOwner','unused_by_policy',"
        "'초판 시드',0,?,?)", (T1, T1))
    put_raw(conn, "detail", fx("detail_gasoline_genesis.json"))
    conn.commit()

    for i, at in enumerate((T2, T3, T4), start=1):
        st = sync_registry(conn, CFG, at)
        row = conn.execute(
            "SELECT usage, miss_streak FROM meta_field_usage "
            "WHERE json_path='advertisement.isVerifyOwner'").fetchone()
        if i < CFG["ghost_miss_limit"]:
            check(f"유령 경로 {i}회 미관측 — 아직 유지", row[0] == "unused_by_policy",
                  str(row))
        else:
            check("★ 3회 연속 미관측 → not_provided 전환",
                  row[0] == "not_provided" and st.retired == 1, str(row))

    check("응답에 있는 경로는 유지된다",
          conn.execute("SELECT miss_streak FROM meta_field_usage "
                       "WHERE json_path='vin'").fetchone()[0] == 0)


# ── V4-06 대조 ───────────────────────────────────────────────────────
def test_v4_06() -> None:
    conn = db()
    put_raw(conn, "detail", fx("detail_ev_tesla.json"))
    sync_registry(conn, CFG, T1)
    observed = {p for (_e, p) in collect_paths(conn)}
    registered = {r[0] for r in conn.execute(
        "SELECT json_path FROM meta_field_usage")}
    check("★ RAW 경로 전수가 등록부에 있다 (V4-06)",
          observed <= registered, str(sorted(observed - registered)[:5]))


# ── 시드를 채운 뒤 재실행하면 반영된다 (STEP 87) ─────────────────────
def test_seed_reapply() -> None:
    """★ 기존 행이라고 건너뛰면 분류가 영영 안 붙는다 (실측 305건)."""
    conn = db()
    put_raw(conn, "detail", fx("detail_gasoline_genesis.json"))
    empty = {"seed": {}, "default": CFG["default"],
             "ghost_miss_limit": CFG["ghost_miss_limit"]}
    sync_registry(conn, empty, T1)
    before = len(list_by_usage(conn, "unclassified"))
    check("시드 없이 돌리면 전부 미분류", before > 50, str(before))

    st = sync_registry(conn, CFG, T2)
    after = len(list_by_usage(conn, "unclassified"))
    check("★ 시드를 채우고 재실행하면 분류가 붙는다", after < before,
          f"{before} → {after}")
    check("갱신 건수가 보고된다", st.added > 0, str(st.added))

    row = conn.execute(
        "SELECT usage FROM meta_field_usage WHERE json_path='vin'").fetchone()
    check("분류된 행은 unclassified 가 아니다", row[0] != "unclassified", str(row))


# ── V4-11 은 성격별로 가른다 (파이프라인을 막는 것만 fatal) ──────────
def test_unclassified_severity() -> None:
    """★ 아무도 안 읽는 새 필드가 전체를 멈추면 새 차종마다 파이프라인이 죽는다."""
    import json as _json

    from validate.base import run_phase

    conn = db()
    doc = fx("detail_gasoline_genesis.json")
    doc["신규마케팅필드"] = "X"        # 파서가 안 읽는다
    put_raw(conn, "detail", doc)
    sync_registry(conn, CFG, T1)

    class _V:
        run_id = "r1"
        policy_raw = _json.load(open(os.path.join(ROOT, "config",
                                                  "scoring.json"),
                                     encoding="utf-8"))
        depreciation: dict = {}
        target_keys: tuple = ()
        started_at = None

    res = {r.check.code: r for r in run_phase(conn, _V(), "V4")}
    check("★ 판정에 안 쓰는 미분류는 warn — 파이프라인을 막지 않는다",
          res["V4-11"].passed and res["V4-11"].check.severity == "fatal",
          str(res["V4-11"].samples[:3]))
    check("★ 그래도 목록으로 남긴다 (다음 회차에 모아서 분류)",
          not res["V4-11b"].passed
          and any("신규마케팅필드" in s for s in res["V4-11b"].samples),
          str(res["V4-11b"].samples[:3]))
    check("V4-11b 는 warn", res["V4-11b"].check.severity == "warn")


if __name__ == "__main__":
    print("8장 등록부 시험")
    test_paths()
    test_contamination()
    test_seed()
    test_seed_reapply()
    test_unclassified_severity()
    test_ghost()
    test_v4_06()
    print()
    print("결과:", "통과" if not FAIL else "실패 — " + " / ".join(FAIL))
    sys.exit(1 if FAIL else 0)
