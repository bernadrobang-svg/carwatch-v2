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
    FATAL, KIND_CODE, KIND_CONTRACT, KIND_EXTERNAL, WARN, Check, result,
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

    # V7-08 · V7-09 — 판정 계층이 사람의 확인·금융을 읽는가
    for code, needles in (
        ("V7-08", ("watch_checklist", "checklist")),
        ("V7-09", ("finance", "total_cost", "real_price")),
    ):
        bad = _reads(("score", "analyze"), needles)
        out.append(result(C[code], rid, 0, bad or 0, not bad, bad))
    return out
