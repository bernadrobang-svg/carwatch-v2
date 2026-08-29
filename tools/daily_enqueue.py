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


def _admin_cfg() -> dict:
    """★ 상한은 config 에 있다 (S14).  코드에 시간을 안 적는다."""
    with open(os.path.join(ROOT, "config", "admin.json"),
              encoding="utf-8") as f:
        return json.load(f)


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


def enqueue_after_store(db_path: str, site: str, stored: int) -> str | None:
    """★ 새 사이트를 저장했으면 ★ 재판정을 함께 큐에 넣는다 (명령서 14-3 ④).

    ★ 지금은 ★ 저장하고 ★ 하루를 기다려야 화면에 나온다 —
      ★ 116건을 넣고도 ★ 등급 분포가 안 바뀌면 ★ 마스터가 「안 들어왔다」로 보신다
    ★ 넣기만 한다.  ★ 꺼내 도는 것은 ★ 웹 서버 안의 소비기다 (STEP 132a)
    ★ 저장한 것이 없으면 ★ 아무것도 안 한다
    """
    if not stored:
        return None
    # ★★★★★ 08-29 실측 — ★ 하루치를 이어 돌릴 때 ★ **여기가 뒤를 죽인다**.
    #   ★ 보배가 221건을 저장하고 재판정을 큐에 넣었다 (09:16:20).
    #   ★ ★ 소비기가 그것을 9분 5초 동안 돌았고 (09:16:20 → 09:25:25)
    #   ★ ★ 그 창 안에서 돈 ★ **네 수집기가 다 `database is locked` 로 죽었다** —
    #   ★ ★ heydealer · bmw · kia_cpo · reborncar.  ★ 그 앞의 셋은 다 성공했다.
    #   ★★ 묶어 돌 때는 ★ 각자 큐에 넣지 않는다 — ★ 다 받은 뒤에
    #   ★ ★ `daily_enqueue.py` 가 ★ **한 번만** 넣는다 (유닛의 ExecStart 가 그것이다)
    if os.environ.get("CARWATCH_DEFER_RECALC") == "1":
        print(f"★ 재판정은 다 받은 뒤에 한 번만 넣습니다 ({site} {stored:,}건 저장)")
        return None
    conn = sqlite3.connect(db_path, timeout=DB_TIMEOUT_SEC)
    try:
        got = enqueue_daily(conn, _now())
    finally:
        conn.close()
    if got:
        print(f"★ 재판정을 큐에 넣었습니다 — {got[:8]} ({site} {stored:,}건 저장)")
    else:
        print("★ 이미 도는 작업이 있어 재판정을 건너뜁니다")
    return got


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
        # ★ 끊긴 작업을 먼저 닫는다 (개정 413).  하나가 running 으로 남으면
        #   「이미 도는 것이 있으면 건너뛴다」에 걸려 자동화가 통째로 멈춘다
        from store.adminops import reap_stale_jobs

        dead = reap_stale_jobs(conn, _admin_cfg()["job_stale_hours"], at)
        if dead:
            print(f"끊긴 작업 {len(dead)}건을 닫았습니다 — "
                  f"{' · '.join(d[:8] for d in dead)}")
        got = enqueue_daily(conn, at)
    finally:
        conn.close()
    if got:
        print(f"하루치를 큐에 넣었습니다 — {got[:8]}")
        return 0
    # ★★ 건너뛰었으면 ★ **실패로 끝낸다** (명령서 56장 · 마스터 확정 08-25).
    #   ★ ★ 전에는 ★ exit 0 으로 끝나 ★ 아무도 몰랐다 —
    #     ★ ★ 실측 08-24 — ★ 07:40 에 죽은 작업 하나가 ★ 13:00 을 막았는데
    #       ★ ★ `job_stale_hours=6` 에 ★ 5.33시간이라 ★ 안 걸렸고 ★ exit 0 이었다.
    #       ★ ★ 그래서 ★ 판본이 ★ 하루 넘게 멈췄다
    #   ★ ★ 이제 ★ systemd 가 ★ 네 시간 뒤 ★ 한 번 더 부른다 (Restart=on-failure).
    #     ★ ★ 그때는 ★ 9시간이 넘어 ★ 되찾기에 걸린다.  ★ 성공하면 ★ 그날은 더 안 돈다
    print("★ 이미 도는 작업이 있어 건너뜁니다 — ★ 네 시간 뒤 다시 부릅니다")
    return 1


if __name__ == "__main__":
    sys.exit(main())
