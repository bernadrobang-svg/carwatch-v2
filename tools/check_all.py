# -*- coding: utf-8 -*-
"""실측 DB 회귀 — V1~V5 · V10 전건을 한 번에 돌린다.

지시서   개선요청 4-1 (실측 DB 회귀)
근거     ★ 실패 1건 고치고 「다시 돌려보십시오」 금지.
         전 검사를 돌려 남은 것을 한 번에 낸다.
         모의 응답 시험만으로는 마스터 실행이 개발측 시험을 대신하게 된다
사용     python tools/check_all.py [carwatch.db] [--target KOLEOS_HEV]
"""
from __future__ import annotations

import io
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from validate.base import PHASE_ORDER, run_phase  # noqa: E402

# ★ 환경에 따라 갈리는 검사.  결함이 아니라 차이다 (개선요청 4-2)
ENV_DEPENDENT = {
    "V4-01": "HMAC 키가 다르면 plate_hash 가 전건 불일치한다",
    "V1-05": "실행 시작 시각 기준이라 DB 만으로는 재현되지 않는다",
}
WIDTH = 52


def _first_fetch(conn) -> datetime:
    row = conn.execute(
        "SELECT MIN(fetched_at) FROM raw_response").fetchone()
    if row and row[0]:
        try:
            return datetime.fromisoformat(row[0])
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def main() -> int:
    args = sys.argv[1:]
    db = next((a for a in args if a.endswith(".db")),
              os.path.join(ROOT, "carwatch.db"))
    targets = tuple(args[i + 1] for i, a in enumerate(args)
                    if a == "--target" and i + 1 < len(args))
    if not os.path.isfile(db):
        print(f"[X] {db} 가 없다")
        return 2
    conn = sqlite3.connect(db)

    class Ctx:
        run_id = (conn.execute("SELECT run_id FROM audit_request "
                               "ORDER BY rowid DESC LIMIT 1").fetchone()
                  or ("-",))[0]
        policy_raw = json.load(io.open(os.path.join(ROOT, "config",
                                                    "scoring.json"),
                                       encoding="utf-8"))
        depreciation = json.load(io.open(os.path.join(ROOT, "config",
                                                      "depreciation.json"),
                                         encoding="utf-8"))
        target_keys = targets
        # ★ 빈 DB 에서도 돈다 (B-5 · V1-18).
        #   수집 전에 검사를 못 돌리면 첫 실행을 시험할 수 없다
        started_at = _first_fetch(conn)

    fatal, warn, env, skip, ok = [], [], [], [], 0
    for phase in PHASE_ORDER:
        try:
            results = run_phase(conn, Ctx(), phase)
        except Exception as e:                      # noqa: BLE001
            fatal.append((phase, f"검사가 예외로 죽었다: {type(e).__name__}: {e}"))
            continue
        for r in results:
            if not r.applicable:
                # ★ 이번 실행에서 안 돈 단계.  통과로 세지 않는다 (V1-16)
                skip.append((r.check.code, r.actual))
            elif r.passed:
                ok += 1
            elif r.check.code in ENV_DEPENDENT:
                env.append((r.check.code, ENV_DEPENDENT[r.check.code]))
            elif r.check.severity == "fatal":
                fatal.append((r.check.code, f"{r.check.title} — {r.actual}"))
            else:
                warn.append((r.check.code, f"{r.check.title} — {r.actual}"))

    print(f"DB {os.path.basename(db)} · run {Ctx.run_id}"
          + (f" · 범위 {', '.join(targets)}" if targets else ""))
    print(f"통과 {ok} · fatal {len(fatal)} · warn {len(warn)}"
          f" · 환경 차이 {len(env)} · 미실행 {len(skip)}\n")
    for title, rows in (("■ FATAL — 고쳐야 한다", fatal),
                        ("■ warn — 진행은 된다", warn),
                        ("■ 환경 차이 — 결함이 아니다", env),
                        ("■ 미실행 — 이번 실행에서 그 단계를 안 돌았다", skip)):
        if not rows:
            continue
        print(title)
        for code, detail in rows:
            print(f"  {code:9} {detail[:WIDTH * 2]}")
        print()
    return 1 if fatal else 0


if __name__ == "__main__":
    sys.exit(main())
