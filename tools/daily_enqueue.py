# -*- coding: utf-8 -*-
"""하루 한 번 스스로 돈다 (STEP 136h · 개정 315).

지시서   13장 STEP 136h · V10-28
근거     마스터 지시 — 「셋팅해줘」
필수     서버에서 부를 수 있는 것만 — 상세 4종 · 새 5종 · 재판정 · 검사
필수     ★ 엔카 목록은 자동이 아니다 (407).  마스터를 기다린다
필수     이미 도는 것이 있으면 건너뛴다 — 겹쳐 돌면 원문이 꼬인다
금지     서비스를 재시작하는 것 — 마스터의 CSRF 가 끊긴다 (개정 308)
금지     cron — systemd 가 이미 서비스를 돌린다.  둘을 섞지 않는다
★        큐를 꺼내 도는 것은 collect/worker.py 다 (STEP 132a · 개정 261).
         웹 서버 안 스레드로 이미 돈다 — 여기서는 넣기만 한다
사용     systemd timer 가 부른다.  손으로는 python3.11 tools/daily_enqueue.py
★        tools/ 에 둔다 — collect/ 는 라이브러리라 __main__ 블록을 두지 않는다
         (V4-23 모듈 최상위 부작용)
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

DB = os.path.join(ROOT, "carwatch.db")
# 매일 어디부터 도는가.  ★ 목록(S1)은 빼고 상세(S5)부터다 — 407 이라 못 부른다
DAILY_FROM_STEP = "S5"
DAILY_REASON = "raw_missing"
# 단위 환산 (2장 상수표 · V4-13)
SECONDS_PER_DAY = 86_400
JOB_ID_BYTES = 8
DB_TIMEOUT_SEC = 30


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _cfg() -> dict:
    with open(os.path.join(ROOT, "config", "web.json"), encoding="utf-8") as f:
        return json.load(f)


def enqueue_daily(conn, at: str) -> str | None:
    """큐에 하루치를 넣는다.  ★ 넣기만 한다 — 도는 것은 일꾼이다."""
    import secrets

    if conn.execute("SELECT COUNT(*) FROM recalc_job"
                    " WHERE status IN ('queued','running')").fetchone()[0]:
        return None                    # 이미 있다.  겹쳐 넣지 않는다
    jid = secrets.token_hex(JOB_ID_BYTES)
    conn.execute(
        "INSERT INTO recalc_job(job_id,account_id,trigger,reason,from_step,"
        "scope,status,queued_at) VALUES (?,NULL,'schedule',?,?,'all',"
        "'queued',?)", (jid, DAILY_REASON, DAILY_FROM_STEP, at))
    conn.commit()
    return jid


def list_age_days(conn, at: str) -> float | None:
    """엔카 목록이 며칠째 안 들어왔나 (STEP 136i).

    ★ 가격 변동은 목록에서 온다.  목록이 멈추면 변동이 멈춘다
    """
    row = conn.execute(
        "SELECT MAX(fetched_at) FROM raw_response"
        " WHERE endpoint='list' AND status='ok'").fetchone()
    if not row or not row[0]:
        return None
    then = datetime.fromisoformat(row[0])
    now = datetime.fromisoformat(at)
    return (now - then).total_seconds() / SECONDS_PER_DAY


def main() -> int:
    at = _now()
    conn = sqlite3.connect(DB, timeout=DB_TIMEOUT_SEC)
    try:
        age = list_age_days(conn, at)
        stale = float(_cfg()["list_stale_days"])
        if age is not None and age > stale:
            # ★ 조용히 옛 목록으로 판정하지 않는다.  화면이 이것을 낸다
            print(f"★ 엔카 목록이 {age:.1f}일째 갱신되지 않았습니다 — "
                  "브라우저 수집을 눌러 주십시오 (/admin/collect)")
        got = enqueue_daily(conn, at)
    finally:
        conn.close()
    print(f"하루치를 큐에 넣었습니다 — {got[:8]}" if got
          else "이미 도는 작업이 있어 건너뜁니다")
    return 0


if __name__ == "__main__":
    sys.exit(main())
