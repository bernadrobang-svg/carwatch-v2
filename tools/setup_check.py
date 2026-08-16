# -*- coding: utf-8 -*-
"""착수 점검 — 실행 전에 무엇이 준비됐는지 한 번에 본다.

지시서   0장 STEP 5.2b (착수 Gate) · 3장 STEP 35 (키) · 13장 STEP 126 (계정)
근거     빠진 것을 실행 중에 알면 중간에 멈춘다.  먼저 본다
사용     python3 tools/setup_check.py
종료     0 준비됨 · 1 빠진 것 있음
"""
from __future__ import annotations

import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# 형식 — 이 코드가 요구하는 최소 파이썬 (2장 상수표 성격 「형식」)
MIN_PYTHON = (3, 10)

DB = os.path.join(ROOT, "carwatch.db")
KEY = os.path.join(ROOT, "secrets", "plate_hmac.key")


def main() -> int:
    rows: list[tuple[str, bool, str]] = []

    rows.append((f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} 이상",
                 sys.version_info >= MIN_PYTHON, sys.version.split()[0]))
    rows.append(("HMAC 키 (secrets/plate_hmac.key)", os.path.isfile(KEY),
                 "있음" if os.path.isfile(KEY) else "[1] 초기 설정 을 먼저"))

    has_db = os.path.isfile(DB)
    rows.append(("데이터베이스 (carwatch.db)", has_db,
                 "있음" if has_db else "첫 수집 때 생성된다"))

    accounts = listings = scores = 0
    unclassified = pending = 0
    if has_db:
        conn = sqlite3.connect(DB)
        def one(sql):
            try:
                return conn.execute(sql).fetchone()[0]
            except sqlite3.Error:
                return 0
        accounts = one("SELECT COUNT(*) FROM account")
        listings = one("SELECT COUNT(*) FROM core_listing")
        scores = one("SELECT COUNT(*) FROM result_score")
        unclassified = one(
            "SELECT COUNT(*) FROM meta_field_usage WHERE usage='unclassified'")
        pending = one("SELECT COUNT(*) FROM dict_enum WHERE status='pending'")
    rows.append(("관리자 계정", accounts > 0,
                 f"{accounts}개" if accounts else "[1] 초기 설정 을 먼저"))

    ua = "?"
    try:
        import json

        with open(os.path.join(ROOT, "config", "endpoints.json"),
                  encoding="utf-8") as f:
            ua = (json.load(f)["encar"]["headers"] or {}).get("User-Agent")
    except (OSError, ValueError, KeyError):
        ua = None
    rows.append(("User-Agent 설정", bool(ua), "있음" if ua else "endpoints.json"))

    print("■ 준비 상태\n")
    ok = True
    for name, good, note in rows:
        mark = "O" if good else "X"
        print(f"  [{mark}] {name:34} {note}")
        ok = ok and good

    if has_db:
        print("\n■ 현재 데이터\n")
        print(f"      매물 {listings}건 · 채점 {scores}건")
        print(f"      등록부 미분류 {unclassified}건 · 사전 미검토 {pending}건")
        if unclassified:
            # ★ 미분류는 더 이상 파이프라인을 막지 않는다 (V4-11 / V4-11b 분리)
            print("\n      → 판정에 쓰는 경로가 미분류면 V4-11 (fatal)")
            print("        그 외는 V4-11b (warn) — 진행은 된다")
            print("        모아서 config/field_usage.json 에 옮기면 된다")

    print("\n결과:", "준비됨" if ok else "빠진 것이 있다")
    if not ok:
        print("\n■ 다음\n")
        print("   run.bat migrate     DDL 변경을 기존 DB 에 반영")
        print("   run.bat             메뉴")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
