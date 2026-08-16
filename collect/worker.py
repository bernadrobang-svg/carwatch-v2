# -*- coding: utf-8 -*-
"""큐 소비기 (13장 STEP 132a · 개정 261).

지시서   STEP 132a — 「큐에 넣은 것은 누군가 가져간다」
근거     실측 08-16.  run.py 가 recalc_job 을 한 번도 읽지 않아
         queued 가 쌓였고, 아무 일도 안 일어난 채 화면만 잠겼다.
         두 번 갇혔다 — 큐를 푸는 화면조차 못 여는 상태였다
금지     화면이 「자동으로 돕니다」라고 하면서 실제로는 아무도 안 가져가는 것
★        웹 서버 안의 스레드로 돈다.  systemd 를 쓰지 않는다 —
         개정 250 이 「CLI 없이 돌아간다」고 했고, 타이머는 터미널 관리가 필요하다
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
import traceback

STATUS_QUEUED = "queued"
STATUS_RUNNING = "running"
STATUS_DONE = "done"
STATUS_FAILED = "failed"


def poll_seconds(root: str = ".") -> float:
    """큐를 얼마나 자주 보나.  ★ 코드에 박지 않는다 (config.web)."""
    with open(os.path.join(root, "config", "web.json"),
              encoding="utf-8") as f:
        return float(json.load(f)["worker_poll_sec"])


def take_next(conn: sqlite3.Connection, at: str) -> dict | None:
    """가장 오래된 queued 하나를 running 으로 바꿔 가져온다.

    ★ 한 번에 하나만 돈다.  둘이 같은 매물을 동시에 쓰면 결과가 섞인다
    ★ UPDATE 로 집는다 — SELECT 뒤 UPDATE 사이에 다른 소비기가 끼어들 수 있다
    """
    row = conn.execute(
        "SELECT job_id, reason, scope, from_step FROM recalc_job "
        "WHERE status = ? ORDER BY queued_at LIMIT 1",
        (STATUS_QUEUED,)).fetchone()
    if row is None:
        return None
    job_id, reason, scope, from_step = row
    got = conn.execute(
        "UPDATE recalc_job SET status = ?, updated_at = ? "
        "WHERE job_id = ? AND status = ?",
        (STATUS_RUNNING, at, job_id, STATUS_QUEUED))
    conn.commit()
    if not got.rowcount:
        return None                      # 다른 소비기가 먼저 집었다
    return {"job_id": job_id, "reason": reason, "scope": scope,
            "from_step": from_step}


def finish(conn: sqlite3.Connection, job_id: str, status: str, at: str,
           detail: str | None = None, run_id: str | None = None) -> None:
    conn.execute(
        "UPDATE recalc_job SET status = ?, ended_at = ?, updated_at = ?, "
        "detail = ?, run_id = COALESCE(?, run_id) WHERE job_id = ?",
        (status, at, at, detail, run_id, job_id))
    conn.commit()


def run_once(db_path: str, make_ctx, make_executors_fn, root: str = ".",
             clock=None) -> dict | None:
    """큐에 있으면 하나 돌린다.  없으면 None.

    make_ctx            () -> RunContext        ★ 주입받는다
    make_executors_fn   () -> dict              ★ 주입받는다
    """
    from collect.pipeline import run_recalc

    now = (clock or _utc_now)()
    conn = sqlite3.connect(db_path)
    try:
        job = take_next(conn, now())
        if job is None:
            return None
        ctx = make_ctx()
        try:
            reports = run_recalc(conn, ctx, make_executors_fn(),
                                 job["reason"], job["scope"], origin="web")
            halted = [f"{r.step}: {r.halt_reason}" for r in reports if r.halted]
            # ★ 「돌았다」가 아니라 「무엇이 나왔나」를 남긴다
            detail = (" / ".join(halted) if halted
                      else " · ".join(f"{r.step} ok {r.ok}" for r in reports))
            finish(conn, job["job_id"],
                   STATUS_FAILED if halted else STATUS_DONE,
                   now(), detail[:500], ctx.run_id)
            return {"job_id": job["job_id"], "halted": bool(halted),
                    "detail": detail}
        except Exception as exc:                            # noqa: BLE001
            # ★ 삼키지 않는다.  무엇이 왜 실패했는지 화면에 남긴다 (STEP 132a)
            finish(conn, job["job_id"], STATUS_FAILED, now(),
                   f"{type(exc).__name__}: {exc}"[:500])
            traceback.print_exc()
            return {"job_id": job["job_id"], "halted": True, "detail": str(exc)}
    finally:
        conn.close()


def _utc_now():
    from datetime import datetime, timezone

    return lambda: datetime.now(timezone.utc).isoformat()


def start(db_path: str, make_ctx, make_executors_fn, root: str = ".",
          stop: threading.Event | None = None) -> threading.Thread:
    """소비기를 띄운다.  ★ 웹 서버와 같은 프로세스에서 돈다.

    데몬 스레드다 — 서버가 죽으면 함께 죽는다.  중간에 끊겨도
    STEP 52 의 재개점과 raw_response 가 남아 처음부터 다시 하지 않는다
    """
    gap = poll_seconds(root)
    flag = stop or threading.Event()

    def loop():
        while not flag.is_set():
            try:
                if run_once(db_path, make_ctx, make_executors_fn, root) is None:
                    flag.wait(gap)
            except Exception:                               # noqa: BLE001
                traceback.print_exc()
                flag.wait(gap)

    th = threading.Thread(target=loop, name="carwatch-queue", daemon=True)
    th.start()
    return th
