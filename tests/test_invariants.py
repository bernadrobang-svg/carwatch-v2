# -*- coding: utf-8 -*-
"""불변식 시험.

지시서   0장 STEP 7 (불변식 6개) · 6장 V3-11 · V5-01
범위     0~1장 착수분으로 검증 가능한 것만 둔다.
         ③ source 전건 NULL · ④ 라벨↔내용 · ⑥ 사전 미분류 는 2~4장 착수 후 추가한다.
사용     python3 tests/test_invariants.py
"""
from __future__ import annotations

import io
import itertools
import json
import os
import random
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyze.verdict import (  # noqa: E402
    BANNED_SOURCES,
    PRIO_KEYWORD,
    PRIO_MANUFACTURER,
    PRIO_OBSERVED,
    Verdict,
    put,
)
from errors import ValidationError  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAIL: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{'  ' + detail if detail else ''}")
    if not ok:
        FAIL.append(name)


# ── 불변식 ① put() 호출 순서를 뒤섞어도 결과가 같다 ──────────────────
def inv1_order_independent() -> None:
    calls = [
        ("spec.hud", 1, PRIO_MANUFACTURER, "spec_table"),
        ("spec.hud", 0, PRIO_KEYWORD, "keyword"),
        ("spec.hud", 1, PRIO_OBSERVED, "installed"),
        ("spec.sunroof", 1, PRIO_OBSERVED, "installed"),
        ("spec.sunroof", 0, PRIO_KEYWORD, "keyword"),
        ("history.damage", 0, PRIO_OBSERVED, "inspection"),
    ]
    base = None
    n = 0
    for order in itertools.permutations(range(len(calls))):
        v = Verdict()
        for i in order:
            axis, val, prio, src = calls[i]
            put(v, axis, val, prio, src)
        got = (
            tuple(sorted(v.values.items())),
            tuple(sorted(v.sources.items())),
            tuple(sorted(v.prios.items())),
        )
        if base is None:
            base = got
        elif got != base:
            check("불변식① 순서 무관", False, f"{order} 에서 어긋남")
            return
        n += 1
    check("불변식① 순서 무관", True, f"{n}순열 전건 동일")


def inv1_shuffle_100() -> None:
    """V3-11 — 표본 셔플 시험 (6장 STEP 60)."""
    rnd = random.Random(20260810)
    calls = [
        (f"axis{i}", i % 3, (i % 4) + 1, f"src{i % 5}") for i in range(12)
    ]
    base = None
    for _ in range(100):
        order = calls[:]
        rnd.shuffle(order)
        v = Verdict()
        for axis, val, prio, src in order:
            put(v, axis, val, prio, src)
        got = tuple(sorted(v.values.items()))
        if base is None:
            base = got
        elif got != base:
            check("V3-11 셔플 100회", False)
            return
    check("V3-11 셔플 100회", True)


# ── 불변식 ② 금지 근거가 판정에 들어가면 실패 ────────────────────────
def inv2_banned() -> None:
    bad = []
    for src in sorted(BANNED_SOURCES):
        v = Verdict()
        try:
            put(v, "spec.hud", 1, PRIO_OBSERVED, src)
            bad.append(src)
        except ValidationError:
            pass
    check("불변식② 금지 근거 차단", not bad, f"미차단 {bad}" if bad else "4종 전건")

    # 정상 근거는 통과해야 한다 — 과차단 확인
    v = Verdict()
    put(v, "spec.hud", 1, PRIO_OBSERVED, "installed")
    check("불변식② 과차단 없음", v.values.get("spec.hud") == 1)


# ── 불변식 ⑤ 배점 합계가 config 의 총점과 일치 ───────────────────────
def inv5_points() -> None:
    sc = json.load(io.open(os.path.join(ROOT, "config", "scoring.json"), encoding="utf-8"))
    comp = sc["components"]
    check(
        "불변식⑤ 배점 합 == total_points",
        sum(comp.values()) == sc["total_points"],
        f"{sum(comp.values())} / {sc['total_points']}",
    )
    check("V5-02 등급컷 내림차순", list(sc["grade_cuts"].values()) == sorted(
        sc["grade_cuts"].values(), reverse=True))


# ── put() 세부 계약 (STEP 13) ────────────────────────────────────────
def put_contract() -> None:
    v = Verdict()
    put(v, "a", None, PRIO_MANUFACTURER, "spec_table")
    check("None 은 값이 아니다", "a" not in v.values)

    v = Verdict()
    put(v, "b", 1, PRIO_OBSERVED, "installed")
    put(v, "b", 0, PRIO_OBSERVED, "inspection")
    check("동일 prio 충돌 → 첫 값 유지", v.values["b"] == 1 and len(v.conflicts) == 1)

    v = Verdict()
    put(v, "c", 0, PRIO_KEYWORD, "keyword")
    put(v, "c", 1, PRIO_MANUFACTURER, "spec_table")
    check("낮은 prio 가 이긴다", v.values["c"] == 1 and v.prios["c"] == PRIO_MANUFACTURER)


# ── excluded (STEP 83 · 승인 5번) ────────────────────────────────────
def excluded_contract() -> None:
    v = Verdict()
    put(v, "spec.hud", -1, PRIO_MANUFACTURER, "spec_table", excluded=True)
    check("구조적 부재 → excluded", v.values["spec.hud"] == -1 and "spec.hud" in v.excluded)

    v = Verdict()
    put(v, "spec.tinting", None, PRIO_KEYWORD, "unknown", excluded=True)
    check("값 None + excluded → 기록된다",
          "spec.tinting" in v.values and "spec.tinting" in v.excluded)

    v = Verdict()
    put(v, "spec.sunroof", 0, PRIO_OBSERVED, "installed")
    check("미장착은 제외가 아니다", v.values["spec.sunroof"] == 0 and not v.excluded)

    # 강한 근거가 뒤집으면 excluded 도 함께 풀린다
    v = Verdict()
    put(v, "spec.hud", None, PRIO_KEYWORD, "unknown", excluded=True)
    put(v, "spec.hud", 1, PRIO_MANUFACTURER, "spec_table")
    check("강한 근거가 excluded 를 해제", v.values["spec.hud"] == 1 and not v.excluded)


# ── ③④⑥ (0장 STEP 7) ────────────────────────────────────────────────
# ★ 장을 착수하면 그 장이 여는 불변식을 그 자리에서 넣는다.
#   「나중에」로 두었더니 시험이 「전부 통과」로 나오는데 절반만 보고 있었다


def inv3_source_not_null() -> None:
    """③ 전 축의 source 가 전건 NULL 이면 실패.

    ★ 근거 없이 나온 점수는 되짚을 수 없다.  판정이 아니라 숫자다
    """
    # ★ 운영 DB 를 읽지 않는다 (0장 · S24).  씨앗으로 본다.
    #   실물 데이터에 대한 같은 불변식은 check_all 의 V3-01·02 가 본다 (개정 247)
    from seed import seed_db_path

    conn = sqlite3.connect(seed_db_path())
    rows = conn.execute(
        "SELECT calc_version, COUNT(*), SUM(source IS NULL) "
        "FROM result_axis GROUP BY calc_version").fetchall()
    bad = [f"{ver}: {null}/{n} 이 NULL"
           for ver, n, null in rows if n and null == n]
    check("불변식③ source 가 전건 NULL 이 아니다", not bad, str(bad[:3]))
    conn.close()


def inv4_label_shape() -> None:
    """④ 원문 라벨과 내용 형식이 어긋나면 저장 거부.

    ★ 「주행거리」 자리에 날짜가 오면 그것은 파싱이 아니라 우연이다
    """
    from parse.encar.mapping import shape_ok

    cases = (("mileage_km", 6318, True), ("mileage_km", "2025-07", False),
             ("year_month", "2025-07", True), ("year_month", 6318, False),
             ("price_current_won", 32540000, True),
             ("price_current_won", "사천만원", False))
    bad = [f"{field}={value!r}" for field, value, want in cases
           if shape_ok(field, value) is not want]
    check("불변식④ 라벨 ↔ 내용 형식", not bad, str(bad))


def inv6_no_unclassified() -> None:
    """⑥ 사전 미분류 0건.

    ★ 미분류가 남아 있으면 그 축은 판정이 멈춘 것이다 — 0점이 아니다
    """
    # ★ 운영 DB 를 읽지 않는다 (0장 · S24).  실물 쪽은 check_all V4-25 가 본다
    from seed import seed_db_path

    conn = sqlite3.connect(seed_db_path())
    n = conn.execute("SELECT COUNT(*) FROM dict_enum "
                     "WHERE status='pending'").fetchone()[0]
    check("불변식⑥ 사전 미분류 0", n == 0, f"{n}건")
    conn.close()


if __name__ == "__main__":
    print("불변식 시험 (0장 STEP 7)")
    inv1_order_independent()
    inv1_shuffle_100()
    inv2_banned()
    inv3_source_not_null()
    inv4_label_shape()
    inv5_points()
    inv6_no_unclassified()
    put_contract()
    excluded_contract()
    print()
    print("결과:", "통과" if not FAIL else "실패 — " + " / ".join(FAIL))
    sys.exit(1 if FAIL else 0)
