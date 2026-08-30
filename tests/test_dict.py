# -*- coding: utf-8 -*-
"""4장 키·코드·사전 시험.

지시서   STEP 40 (scope_key) · 41 (축별 특성) · 42 (생성) · 43 (완전 일치 · Count=0)
         STEP 44 (코드값 우선) · 45 (미분류 0건 · 충돌) · 46 (분류 2단)
사용     python3 tests/test_dict.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from errors import ValidationError  # noqa: E402
from parse.classify import STAGE_CONFIRMED, STAGE_PROVISIONAL, classify  # noqa: E402
from store.dictionary import (  # noqa: E402
    AXIS_POLICY,
    assert_no_unknown,
    bump_dict_version,
    installed_option_names,
    normalize_enum,
    resolve_code,
    retire_unseen,
    scope_key,
    upsert_enum,
    upsert_option3,
)
from store.raw import open_db  # noqa: E402
from tools.build_dict import build_catalog_dict, build_dict, extract_distinct  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T1, T2 = "2026-08-10T00:00:00", "2026-08-11T00:00:00"
FAIL: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{'  ' + detail if detail else ''}")
    if not ok:
        FAIL.append(name)


def db():
    return open_db(os.path.join(tempfile.mkdtemp(), "t.db"),
                   os.path.join(ROOT, "sql", "ddl"))


# ── STEP 40 scope_key ────────────────────────────────────────────────
def test_scope_key() -> None:
    check("global → site", scope_key("global", "encar") == "encar")
    check("target → site/target", scope_key("target", "encar", "KOLEOS_HEV")
          == "encar/KOLEOS_HEV")
    check("model → site/model", scope_key("model", "encar",
                                          model_catalog_key="843925") == "encar/843925")
    try:
        scope_key("model", "encar")
        check("model 인데 키 없음 → 중단", False)
    except ValidationError:
        check("model 인데 키 없음 → 중단", True)


# ── STEP 43 Count=0 ──────────────────────────────────────────────────
FUEL_12 = [
    ("가솔린", 730), ("가솔린+전기", 613), ("전기", 489), ("디젤", 264),
    ("LPG(일반인 구입)", 250), ("가솔린+LPG", 1),
    ("LPG+가솔린", 0), ("LPG+전기", 0), ("가솔린+CNG", 0),
    ("디젤+전기", 0), ("수소", 0), ("기타", 0),
]


def test_count_zero() -> None:
    conn = db()
    body = {"iNav": {"Nodes": [{
        "Name": "FuelType", "Type": "Aspect",
        "Facets": [{"Value": v, "Count": c} for v, c in FUEL_12]}]}}
    conn.execute("INSERT INTO raw_facet VALUES "
                 "('encar','encar:G80','unspecified','u',1,?,?)",
                 (json.dumps(body, ensure_ascii=False), T1))
    conn.commit()

    vals = extract_distinct(conn, "facet", "FuelType")
    check("facet 12종 전량 추출 (Count=0 포함)", len(vals) == 12, f"{len(vals)}종")

    rep = build_dict(conn, "encar", "d1", T1)
    n = conn.execute("SELECT COUNT(*) FROM dict_enum WHERE axis='fuel'").fetchone()[0]
    check("사전에 12종 등록", n == 12, f"{n}종")
    z = conn.execute("SELECT status FROM dict_enum WHERE value='수소'").fetchone()
    check("Count=0 도 confirmed (pending·retired 아님)", z == ("confirmed",), str(z))
    assert_no_unknown(conn, "encar", "fuel")
    check("facet 축은 바로 판정에 쓸 수 있다", True)
    check("신규 12건 보고", len(rep.new_values.get("fuel", [])) == 12)


# ── STEP 41 축별 정책 ────────────────────────────────────────────────
def test_axis_policy() -> None:
    # ★ 개정 540 — `target` 축이 늘어 13 → 14 다 (docs/TARGET_KEY_MAP.md 6장).
    #   ★ 이 수는 ★ 몰래 늘지 않았는가를 보는 빗장이다 — ★ 늘리면 까닭을 적는다
    # ★★★★★ 08-31 — ★ 14 → **16**.  ★ `part`·`repair` 를 더했다.
    #   ★ 까닭 — ★ 가이드가 ★ 08-30 에 ★ **STEP 41 표에 두 행을 넣었다**
    #     (`docs/chapters/12-dict.md:137` — ★ `part` site · `repair` site).
    #   ★ ★ 그 전에는 ★ 표에 없어서 ★ `ValidationError: 축 정책 미정의: part` 로
    #     ★ ★ 헤이딜러 부위 코드가 ★ 사흘 막혀 있었다
    check("축 16종 정책 정의", len(AXIS_POLICY) == 16, f"{len(AXIS_POLICY)}종")

    conn = db()
    # panel_rank — 5값 고정.  새 값은 pending 이 아니라 중단
    for v in ("RANK_ONE", "RANK_A"):
        conn.execute("INSERT INTO dict_enum"
                 "(site,axis,value,display,count_seen,status,"
                 "source_endpoint,dict_version,first_seen,last_seen)"
                 " VALUES "
                     "('encar','panel_rank',?,?,1,'confirmed','inspection','d1',?,?)",
                     (v, v, T1, T1))
    conn.commit()
    try:
        upsert_enum(conn, "encar", "panel_rank", "RANK_D", "RANK_D", 1,
                    "inspection", "d1", T1)
        check("panel_rank 새 값 → 중단", False)
    except ValidationError:
        check("panel_rank 새 값 → 중단", True)

    # trim — 차종·연식마다 늘어난다.  중단시키면 수집이 멈춘다
    r = upsert_enum(conn, "encar", "trim", "2.5 터보 AWD", "2.5 터보 AWD", 5,
                    "facet", "d1", T1)
    check("trim 새 값 → 등록 (중단 아님)", r == "new")

    # panel_status · accident_type — 감점 방향이 그 값에 걸려 있다.  새 값은 중단
    for axis, val in (("panel_status", "신규상태"), ("accident_type", "9")):
        try:
            upsert_enum(conn, "encar", axis, val, val, 1, "inspection", "d1", T1)
            check(f"{axis} 새 값 → 중단", False)
        except ValidationError:
            check(f"{axis} 새 값 → 중단", True)

    # panel — 부위명은 표시 전용.  판정은 panel_rank 가 한다.  halt 면 자주 멈춘다
    upsert_enum(conn, "encar", "panel", "프론트 휀더(우)", "프론트 휀더(우)", 3,
                "inspection", "d1", T1)
    st = conn.execute(
        "SELECT status FROM dict_enum WHERE axis='panel'").fetchone()
    check("panel 새 값 → pending", st == ("pending",), str(st))
    try:
        assert_no_unknown(conn, "encar", "panel")
        check("pending 있으면 그 축 판정 중단", False)
    except ValidationError:
        check("pending 있으면 그 축 판정 중단", True)


def test_conflict() -> None:
    conn = db()
    upsert_enum(conn, "encar", "fuel", "가솔린", "가솔린", 10, "facet", "d1", T1)
    r = upsert_enum(conn, "encar", "fuel", "가솔린", "휘발유", 10, "facet", "d1", T2)
    check("fuel 충돌 → pending (중단 아님)", r == "conflict")
    st = conn.execute(
        "SELECT status FROM dict_enum WHERE axis='fuel'").fetchone()
    check("충돌 값은 판정에서 빠진다", st == ("pending",), str(st))

    conn2 = db()
    conn2.execute("INSERT INTO dict_enum"
                 "(site,axis,value,display,count_seen,status,"
                 "source_endpoint,dict_version,first_seen,last_seen)"
                 " VALUES "
                  "('encar','accident_type','1','1',5,'confirmed','record','d1',?,?)",
                  (T1, T1))
    conn2.commit()
    try:
        upsert_enum(conn2, "encar", "accident_type", "1", "다른뜻", 5,
                    "record", "d1", T2)
        check("accident_type 충돌 → 중단", False)
    except ValidationError:
        check("accident_type 충돌 → 중단", True)

    conn3 = db()
    upsert_option3(conn3, "encar", "G80_25T", "095", "헤드업 디스플레이(HUD)", 9,
                   "d1", T1)
    try:
        upsert_option3(conn3, "encar", "MODEL_Y", "095", "다른 이름", 1, "d1", T1)
        check("3자리 코드 충돌 → 중단", False)
    except ValidationError:
        check("3자리 코드 충돌 → 중단", True)


# ── STEP 22 · 14.1 카탈로그 ──────────────────────────────────────────
def test_catalog() -> None:
    conn = db()
    for mck, items in (
        ("843925", [{"optionCd": "1026", "optionName": "20인치 휠", "price": 129}]),
        ("999111", [{"optionCd": "1026", "optionName": "AR-HUD", "price": 200}]),
    ):
        conn.execute(
            "INSERT INTO raw_response(site,source_id,endpoint,request_url,status,"
            "body,origin,fetched_at) VALUES ('encar',?,'catalog','u','ok',?,"
            "'collector',?)",
            (mck, json.dumps(items, ensure_ascii=False), T1))
    conn.commit()
    n = build_catalog_dict(conn, "encar", "d1", T1)
    check("카탈로그 2건 적재", n == 2)
    check("같은 코드가 모델마다 다른 옵션 — 충돌 아님",
          resolve_code(conn, "option_model", "1026", "encar/843925").display == "20인치 휠"
          and resolve_code(conn, "option_model", "1026", "encar/999111").display == "AR-HUD")
    check("빈 codes → 빈 목록 (금지 위반 판별법)",
          installed_option_names(conn, "encar", "843925", []) == [])
    check("그 매물의 코드만 이름으로",
          installed_option_names(conn, "encar", "843925", ["1026"]) == ["20인치 휠"])


# ── STEP 42 · 45 상태 · 버전 ─────────────────────────────────────────
def test_status_version() -> None:
    conn = db()
    upsert_enum(conn, "encar", "fuel", "디젤", "디젤", 3, "facet", "d1", T1)
    n = retire_unseen(conn, "encar", "fuel", T2)
    check("이번에 안 보인 값 → retired", n == 1)
    left = conn.execute("SELECT COUNT(*) FROM dict_enum").fetchone()[0]
    check("retired 는 삭제하지 않는다", left == 1)
    upsert_enum(conn, "encar", "fuel", "디젤", "디젤", 4, "facet", "d2", T2)
    st = conn.execute("SELECT status FROM dict_enum").fetchone()
    check("다시 나타나면 confirmed 로 복귀", st == ("confirmed",), str(st))
    check("dict_version 증가", bump_dict_version("d1") == "d2")
    check("normalize_enum 은 완전 일치만",
          normalize_enum(conn, "encar", "fuel", "디젤") == "디젤"
          and normalize_enum(conn, "encar", "fuel", "디") is None)


# ── STEP 46 분류 2단 ─────────────────────────────────────────────────
def test_classify() -> None:
    from collect.runner import load_targets
    tg = load_targets(os.path.join(ROOT, "config", "targets.json"))

    r = classify(tg, "encar:KOLEOS", "가솔린+전기", "1.5 E-TECH", None, None)
    check("상세 A 미확보 → provisional 유지 (버리지 않는다)",
          r.stage == STAGE_PROVISIONAL and r.target_key == "KOLEOS_HEV", r.reason)

    r = classify(tg, "encar:KOLEOS", "가솔린+전기", "1.5 E-TECH", None, 1499)
    check("1499 · 가솔린+전기 → confirmed",
          r.stage == STAGE_CONFIRMED and r.target_key == "KOLEOS_HEV" and not r.conflict)

    r = classify(tg, "encar:KOLEOS", "가솔린", "2.0", None, 1969)
    check("1969 · 가솔린 → 대상 외", r.target_key is None and not r.conflict, r.reason)

    r = classify(tg, "encar:KOLEOS", "가솔린+LPG", None, None, 1499)
    check("배기량은 대상 · 연료는 제외 → conflict (배제 아님)",
          r.conflict and r.target_key == "KOLEOS_HEV", r.reason)

    r = classify(tg, "encar:G80", "전기", None, None, None)
    check("G80 그룹에서 연료로 EV 분리", r.target_key == "G80_EV")
    r = classify(tg, "encar:G80", "가솔린", "2.5 터보", None, 2497)
    check("G80 그룹에서 배기량으로 2.5T 확정",
          r.target_key == "G80_25T" and r.stage == STAGE_CONFIRMED)
    r = classify(tg, "encar:G70", "가솔린", None, None, 1998)
    check("G70 2.0 / 2.5 를 배기량이 가른다", r.target_key == "G70_20T", r.reason)


# ── STEP 45 검토 절차 ────────────────────────────────────────────────
def test_review() -> None:
    from store.dictionary import confirm_enum, list_pending

    conn = db()
    upsert_enum(conn, "encar", "panel", "본넷", "본넷", 5, "inspection",
                "d1", T1)
    upsert_enum(conn, "encar", "panel", "프론트 휀더(우)", "프론트 휀더(우)", 3,
                "inspection", "d1", T1)
    rows = list_pending(conn, "encar")
    check("★ 검토 대기 목록에 관측 수와 원천이 나온다",
          len(rows) == 2 and rows[0][3] == 5 and rows[0][4] == "inspection",
          str(rows[0]))

    check("확정하면 confirmed",
          confirm_enum(conn, "encar", "panel", "본넷", T1) == "confirmed")
    check("★ 재확정은 멱등",
          confirm_enum(conn, "encar", "panel", "본넷", T1) == "confirmed")
    check("확정한 것은 목록에서 빠진다",
          len(list_pending(conn, "encar")) == 1)
    try:
        confirm_enum(conn, "encar", "panel", "없는값", T1)
        check("없는 값은 거부", False)
    except ValidationError:
        check("없는 값은 거부", True)


if __name__ == "__main__":
    print("4장 키·코드·사전 시험")
    test_scope_key()
    test_count_zero()
    test_axis_policy()
    test_conflict()
    test_catalog()
    test_status_version()
    test_classify()
    test_review()
    print()
    print("결과:", "통과" if not FAIL else "실패 — " + " / ".join(FAIL))
    sys.exit(1 if FAIL else 0)
