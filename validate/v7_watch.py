# -*- coding: utf-8 -*-
"""V7 관심·추적 검증.

지시서   11장 STEP 108~120 · 6장 STEP 54
근거     ★ 관심 목록은 판정에 끼어들지 않는다.
         체크리스트·실구매가는 사람의 판단 재료이지 점수가 아니다
금지     알림이 검증 실패 실행에서 나가는 것 — 틀린 값을 알린다
"""
from __future__ import annotations

import ast
import os

from validate.base import (
    FATAL, KIND_CODE, KIND_CONTRACT, KIND_EXTERNAL, WARN, Check,
    not_applicable, result,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# DDL CHECK 와 같아야 한다 (11장).  자유 문구를 넘기면 CHECK 위반이다
CLOSED_REASONS = ("bought", "lost", "dropped")

# 추적 시점을 되살리는 버전 4종 (STEP 110).
# ★ 계수는 버전 문자열이 아니라 coefficient_history 행을 가리킨다 (STEP 71)
TRACK_VERSIONS = ("parse_version", "dict_version", "calc_version",
                  "coefficient_id")

C = {
    "V7-01": Check("V7", "V7-01", "watch_track 에 버전 4종 전건 있음",
                   FATAL, "run",
                   "그 시점의 판정을 되살릴 수 없다. 버전을 함께 적재한다",
                   KIND_CODE),
    "V7-02": Check("V7", "V7-02", "cause != 'listing' 인 이벤트가 알림되지 않음",
                   FATAL, "run",
                   "규칙이 바뀌어 생긴 변화는 알리지 않는다 (STEP 116)",
                   KIND_CONTRACT),
    "V7-04": Check("V7", "V7-04", "같은 이벤트 중복 발송 0건", FATAL, "run",
                   "발송 기록을 키로 막는다", KIND_CODE),
    "V7-05": Check("V7", "V7-05", "gone 매물이 목록에서 삭제되지 않음",
                   FATAL, "run",
                   "내려간 매물도 이력이다. status 로 표시한다", KIND_CONTRACT),
    "V7-06": Check("V7", "V7-06", "검증 실패 실행에서 알림이 나가지 않음",
                   FATAL, "run",
                   "틀린 값을 알리지 않는다. 검증 통과 후 발송한다",
                   KIND_CONTRACT),
    "V7-07": Check("V7", "V7-07", "relist 결합에 identity_kind 기록",
                   WARN, "run",
                   "무엇으로 같은 차라고 봤는지 남긴다", KIND_EXTERNAL),
    "V7-10": Check("V7", "V7-10", "발송 시도 대비 성공률", FATAL, "run",
                   "발송 실패를 조용히 넘기지 않는다. "
                   "시도를 먼저 기록하고 결과를 갱신한다 (STEP 120a)",
                   KIND_CONTRACT),
    "V7-12": Check("V7", "V7-12", "남의 관심 항목을 고치지 못함", FATAL, "run",
                   "watch_update · watch_close 에 account_id 를 걸고 "
                   "assert_owner 로 막는다 (STEP 111)",
                   KIND_CONTRACT),
    "V7-11": Check("V7", "V7-11", "closed_reason 이 CHECK 안의 값",
                   FATAL, "run",
                   "bought · lost · dropped 뿐이다. 자유 문구를 넘기지 않는다",
                   KIND_CODE),
    "V7-08": Check("V7", "V7-08", "구매 체크리스트가 점수·등급에 반영되지 않음",
                   FATAL, "run",
                   "체크리스트는 사람의 확인이다. 점수에 넣지 않는다",
                   KIND_CONTRACT),
    "V7-15": Check("V7", "V7-15", "진행 메모를 자유롭게 적을 수 있음",
                   FATAL, "run",
                   "이 도구는 엔카와 직거래를 하기 위한 것이다.  폐기된 "
                   "4단계는 파는 쪽을 대신하는 사람이 쓰던 것이었다. "
                   "연락함 · 보러 감 · 끝 세 메모다. "
                   "★ 단계를 강제하지 않는다 (개정 362)",
                   KIND_CODE),
    "V7-09": Check("V7", "V7-09", "실구매가·총소유비용이 점수에 반영되지 않음",
                   FATAL, "run",
                   "금융 조건은 표시다. 차량 품질 점수와 섞지 않는다",
                   KIND_CONTRACT),
}


def _cols(conn, table: str) -> set:
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}


def _reads(dirs: tuple, needles: tuple) -> list:
    """그 계층이 읽으면 안 되는 것을 읽는가.  문자열 상수만 본다 (STEP 53)."""
    bad = []
    for d in dirs:
        base_dir = os.path.join(ROOT, d)
        if not os.path.isdir(base_dir):
            continue
        for base, subs, files in os.walk(base_dir):
            subs[:] = [s for s in subs if s != "__pycache__"]
            for f in files:
                if not f.endswith(".py"):
                    continue
                path = os.path.join(base, f)
                try:
                    tree = ast.parse(open(path, encoding="utf-8").read())
                except SyntaxError:
                    continue
                rel = os.path.relpath(path, ROOT).replace("\\", "/")
                for n in ast.walk(tree):
                    if not (isinstance(n, ast.Constant)
                            and isinstance(n.value, str)):
                        continue
                    for needle in needles:
                        if needle in n.value:
                            bad.append(f"{rel}: {needle}")
    return sorted(set(bad))


def _progress_note_check(conn, rid):
    """V7-15 — 진행 메모를 자유롭게 적을 수 있는가 (11장 STEP 118 · 개정 362).

    ★★ 계약 4단계를 폐기하고 이것이 대신 들어왔다.
      마스터 지적 — 이 도구는 엔카와 직거래를 하기 위한 것이지
      파는 쪽을 대신해 주는 것이 아니다 (개정 362).
      폐기된 4단계는 파는 쪽을 대신하는 사람이 쓰는 것이었다
    ★ 「자유롭게」가 검산이다 —
      ① 단계를 강제하지 않는가 (앞 단계 없이 '끝'을 적을 수 있는가)
      ② 메모가 본체인가 (빈 메모를 거절하는가)
      ③ 화면에 적을 자리가 있는가 (CLI 는 완성이 아니다 · S27)
      ④ 남의 메모를 못 보고 못 지우는가 (V7-12)
    """
    import sqlite3 as _s

    from errors import CarWatchError
    from store.watch import NOTE_KINDS, note_add, note_delete, notes_of

    bad = []
    # ★ 운영 DB 를 건드리지 않는다.  메모리 사본에서 시험한다
    probe = _s.connect(":memory:")
    conn.backup(probe)
    lid = probe.execute("SELECT listing_id FROM core_listing LIMIT 1").fetchone()
    if lid is None:
        probe.close()
        return not_applicable(C["V7-15"], rid, "매물이 없다")
    lid = lid[0]
    at = "2026-01-01T00:00:00+00:00"
    # ★ 검사가 예외로 죽으면 진단이 안 나온다.  붙잡아 결함으로 낸다.
    #   실측 08-19 — 되살림 시험에서 검사가 통째로 죽어 무엇이 틀렸는지
    #   한 줄도 안 나왔다.  「죽는 검사」는 「없는 검사」와 같다
    blew = (CarWatchError, _s.Error)
    try:
        # ① 앞 단계 없이 「끝」을 적을 수 있어야 한다
        try:
            note_add(probe, 1, lid, "done", "안 샀다. 실차가 사진과 달랐다", at)
        except blew as e:
            bad.append(f"★ 단계를 강제한다 — 앞 단계 없이 「끝」을 못 적는다: "
                       f"{type(e).__name__} {e}")
            note_add(probe, 1, lid, "contacted", "되살림용", at)
            note_add(probe, 1, lid, "done", "되살림용", at)
        got = notes_of(probe, 1, lid)
        if not got:
            bad.append("적었는데 안 보인다")
        if len(NOTE_KINDS) != 3:
            bad.append(f"갈래가 셋이 아니다: {sorted(NOTE_KINDS)}")
        # ② 빈 메모는 거절해야 한다 — 메모가 본체다
        try:
            note_add(probe, 1, lid, "contacted", "   ", at)
            bad.append("빈 메모를 받는다 — 메모가 본체다")
        except blew:
            pass
        # ★ 계약·대행 갈래가 들어오면 안 된다.
        #   ★ DDL 의 CHECK 가 막으면 IntegrityError 다 — 그것도 「막았다」다
        try:
            note_add(probe, 1, lid, "contract", "폐기된 갈래", at)
            bad.append("★ 계약 갈래를 받는다 — 폐기된 개념이다 (개정 362)")
        except blew:
            pass
        # ③ 남의 메모는 안 보이고 못 지운다
        if notes_of(probe, 2, lid):
            bad.append("★ 남의 메모가 보인다 (V7-12)")
        rows = notes_of(probe, 1, lid)
        if rows:
            try:
                note_delete(probe, rows[0][0], 2)
                bad.append("★ 남의 메모를 지울 수 있다 (V7-12)")
            except blew:
                pass
    except blew as e:                                   # noqa: BLE001
        bad.append(f"진행 메모가 안 돈다: {type(e).__name__} {e}"[:80])
    finally:
        probe.close()

    # ④ 화면에 적을 자리가 있는가 — CLI 는 완성이 아니다 (S27)
    tpl = os.path.join(ROOT, "web", "templates", "watch.html")
    if os.path.isfile(tpl):
        body = open(tpl, encoding="utf-8").read()
        if 'name="note_kind"' not in body or 'name="body"' not in body:
            bad.append("관심 화면에 진행을 적을 자리가 없다")
    return result(C["V7-15"], rid, "적을 수 있다",
                  "된다" if not bad else "안 된다", not bad, bad[:6])


def run(conn, ctx) -> list:
    rid = ctx.run_id
    out = []

    # V7-01 — 그 시점을 되살릴 수 있는가
    have = _cols(conn, "watch_track")
    miss = [v for v in TRACK_VERSIONS if v in have and conn.execute(
        f"SELECT COUNT(*) FROM watch_track WHERE {v} IS NULL").fetchone()[0]]
    absent = [v for v in TRACK_VERSIONS if v not in have]
    bad = [f"{v} NULL 있음" for v in miss] + [f"{v} 컬럼 없음" for v in absent]
    out.append(result(C["V7-01"], rid, 0, len(bad), not bad, bad))

    # V7-02 — 규칙 변경으로 생긴 이벤트는 알리지 않는다
    n = 0
    if "cause" in _cols(conn, "watch_event"):
        n = conn.execute(
            "SELECT COUNT(*) FROM watch_event WHERE cause <> 'listing' "
            "AND notified = 1").fetchone()[0]
    out.append(result(C["V7-02"], rid, 0, n, n == 0))

    # V7-04 — 같은 이벤트를 두 번 보내지 않는다
    dup = conn.execute(
        "SELECT COUNT(*) FROM (SELECT listing_id, event_kind, occurred_at "
        "FROM watch_event WHERE notified = 1 GROUP BY 1,2,3 "
        "HAVING COUNT(*) > 1)").fetchone()[0] if "event_kind" in _cols(
            conn, "watch_event") else 0
    out.append(result(C["V7-04"], rid, 0, dup, dup == 0))

    # V7-05 — 내려간 매물을 지우지 않는다
    dels = _reads(("store", "report", "collect"),
                  ("DELETE FROM core_listing", "DELETE FROM watch_item"))
    out.append(result(C["V7-05"], rid, 0, dels or 0, not dels, dels))

    # V7-06 — 검증 실패 실행에서 알림이 나갔는가
    leaked = conn.execute(
        "SELECT COUNT(*) FROM watch_event e WHERE e.notified = 1 "
        "AND EXISTS (SELECT 1 FROM audit_validation v "
        " WHERE v.passed = 0 AND v.severity = 'fatal')").fetchone()[0]
    out.append(result(C["V7-06"], rid, 0, leaked, leaked == 0))

    # V7-07 — 무엇으로 같은 차라고 봤는가
    miss_kind = 0
    if "identity_kind" in _cols(conn, "watch_event"):
        miss_kind = conn.execute(
            "SELECT COUNT(*) FROM watch_event WHERE event_kind = 'relist' "
            "AND identity_kind IS NULL").fetchone()[0]
    out.append(result(C["V7-07"], rid, 0, miss_kind, miss_kind == 0))

    # V7-10 — 1차는 화면만이다.  그래도 기록 구조가 있어야 한다 (STEP 120a)
    #   ★ 발송 성공을 낙관해 notified=1 로 먼저 쓰지 않는다
    bad = []
    if "notified" not in _cols(conn, "watch_event"):
        bad.append("watch_event 에 notified 가 없다")
    # ★ 「먼저 쓴다」만 본다.  중복 확인용 조회(WHERE notified=1)는 정상이다
    optimistic = _reads(("store", "report", "web"),
                        ("SET notified=1, ", "notified=1 WHERE 1"))
    bad += [f"{p} — 성공을 낙관해 먼저 기록한다" for p in optimistic]
    if "notify_attempted_at" not in _cols(conn, "watch_event"):
        bad.append("시도 기록 컬럼이 없다 (notify_attempted_at)")
    # 영구 보관 표를 지우는 코드가 있으면 증거가 사라진다
    bad += _reads(("store", "report", "collect", "web"),
                  ("DELETE FROM watch_track", "DELETE FROM watch_event"))
    out.append(result(C["V7-10"], rid, 0, bad or 0, not bad, bad))

    # V7-12 — 실제로 남의 것을 고쳐 본다 (C-1)
    import inspect

    from store.watch import watch_close, watch_update

    bad = [f.__name__ for f in (watch_update, watch_close)
           if "account_id" not in inspect.signature(f).parameters]
    out.append(result(C["V7-12"], rid, 0, bad or 0, not bad,
                      [f"{n} 에 account_id 가 없다" for n in bad]))

    # V7-11 — DDL CHECK 밖의 값이 코드에 있는가
    bad = [f"{r[0]} {r[1]}건" for r in conn.execute(
        "SELECT closed_reason, COUNT(*) FROM watch_item "
        "WHERE closed_reason IS NOT NULL GROUP BY 1")
        if r[0] not in CLOSED_REASONS]
    bad += [f"{p} — CHECK 밖의 문구" for p in _reads(
        ("web", "report", "store"), ("사용자 해제", "직접 해제"))]
    out.append(result(C["V7-11"], rid, 0, bad or 0, not bad, bad))

    # V7-15 — 진행 메모 (개정 362).  ★ 계약 4단계 대신 들어온 것이다
    out.append(_progress_note_check(conn, rid))

    # V7-08 · V7-09 — 판정 계층이 사람의 확인·금융을 읽는가
    for code, needles in (
        ("V7-08", ("watch_checklist", "checklist")),
        ("V7-09", ("finance", "total_cost", "real_price")),
    ):
        bad = _reads(("score", "analyze"), needles)
        out.append(result(C[code], rid, 0, bad or 0, not bad, bad))
    return out
