# -*- coding: utf-8 -*-
"""큐를 소비한다 — 목록이 저장되면 나머지가 이어서 돈다 (STEP 136g · 개정 314).

지시서   13장 STEP 132a · 136g · V10-26 · V10-27
근거     마스터 지시 — 「셋팅해줘」.
        지금까지는 사람이 「이어서 해라」를 말해야 했다.
        ★ 큐에 넣는 쪽은 있었는데 꺼내 도는 쪽이 없었다 (실측 08-17)
필수     ⑤ 판정은 ②③ 이 끝난 뒤에.  중간 상태로 판정하지 않는다
        ★ 상세가 반만 왔는데 판정하면 등급이 틀린다
필수     실패하면 멈추고 사유를 남긴다.  다음 단계로 가지 않는다
금지     겹쳐 도는 것 — 원문이 꼬인다
금지     서비스를 재시작하는 것 (개정 308 — 마스터의 CSRF 가 끊긴다)
사용     python3.11 -m collect.worker          한 번 돌고 끝
        python3.11 -m collect.worker --watch   큐를 지켜본다
"""
from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

DB = os.path.join(ROOT, "carwatch.db")
# 큐를 얼마나 자주 보나 (초).  ★ 자주 볼 이유가 없다 — 하루 몇 번이다
POLL_SEC = 20


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def take_one(conn) -> tuple | None:
    """가장 오래 기다린 하나를 집어 running 으로 바꾼다.

    ★ 집는 것과 표시하는 것이 한 트랜잭션이어야 한다 —
      둘로 나누면 두 일꾼이 같은 것을 집는다
    """
    conn.isolation_level = None
    conn.execute("BEGIN IMMEDIATE")
    row = conn.execute(
        "SELECT job_id, reason, from_step, scope FROM recalc_job"
        " WHERE status='queued' ORDER BY queued_at LIMIT 1").fetchone()
    if row is None:
        conn.execute("COMMIT")
        return None
    if conn.execute("SELECT COUNT(*) FROM recalc_job"
                    " WHERE status='running'").fetchone()[0]:
        conn.execute("COMMIT")
        return None                    # 이미 도는 것이 있다.  겹쳐 돌지 않는다
    conn.execute(
        "UPDATE recalc_job SET status='running', updated_at=?,"
        " current_step=? WHERE job_id=?", (_now(), row[2], row[0]))
    conn.execute("COMMIT")
    return row


def run_job(job: tuple) -> tuple:
    """파이프라인을 그 단계부터 돌린다.  (성공, 마지막 줄)."""
    job_id, _reason, from_step, _scope = job
    log = os.path.join(ROOT, "outputs", "worker", f"{job_id}.log")
    os.makedirs(os.path.dirname(log), exist_ok=True)
    # ★ 서비스를 건드리지 않는다.  자기 프로세스로 돈다 (개정 308)
    cmd = [sys.executable, os.path.join(ROOT, "run.py"), "collect",
           "--from", from_step, "--resume"]
    with open(log, "w", encoding="utf-8") as f:
        got = subprocess.run(cmd, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT,
                             check=False)
    tail = ""
    with open(log, encoding="utf-8") as f:
        lines = [x.rstrip() for x in f if x.strip()]
        tail = " / ".join(lines[-3:])[:400]
    return got.returncode == 0, tail


def finish(conn, job_id: str, ok: bool, detail: str) -> None:
    conn.execute(
        "UPDATE recalc_job SET status=?, detail=?, ended_at=?, updated_at=?"
        " WHERE job_id=?",
        ("done" if ok else "failed", detail, _now(), _now(), job_id))
    conn.commit()


def tick(db: str = DB) -> str | None:
    """큐에서 하나를 집어 끝까지 돌린다.  집을 것이 없으면 None."""
    conn = sqlite3.connect(db, timeout=30)
    try:
        job = take_one(conn)
    finally:
        conn.close()
    if job is None:
        return None
    ok, tail = run_job(job)
    conn = sqlite3.connect(db, timeout=30)
    try:
        # ★ 실패하면 멈추고 사유를 남긴다.  다음 것으로 넘어가지 않는다
        finish(conn, job[0], ok, tail)
    finally:
        conn.close()
    return job[0]


def main() -> int:
    watch = "--watch" in sys.argv
    while True:
        got = tick()
        if got:
            print(f"작업 {got[:8]} 끝")
        if not watch:
            return 0
        time.sleep(POLL_SEC)


if __name__ == "__main__":
    sys.exit(main())
