# -*- coding: utf-8 -*-
"""재판정이 밀렸으면 채운다 (명령서 14-3 · 마스터 지시 08-24).

지시서   명령서 `ORDER_20260822_r515.md` 14-3
근거     ★ 마스터 — 「안 돌면 네 시간 단위로 체크해서 진행하게 해」
        ★ 실측 08-24 — 08-23 13시 타이머는 ★ 트리거 기록만 있고 ★ 서비스 로그가 없다.
          ★ 그날 서버가 11:59~15:15 멎어 있었다.  ★ 그래서 하루치가 통째로 밀렸다
필수     ★ 밀린 것만 채운다.  ★ 무조건 돌리지 않는다 (14-3 ②)
필수     ★ 시각·기준은 `config/admin.json` 이 정본이다 (V10-31) — ★ 두 벌로 적지 않는다
금지     ★ 서비스를 재시작하는 것 — ★ 마스터의 CSRF 가 끊긴다 (개정 308)
사용     systemd timer 가 부른다.  손으로는 python3.11 tools/recalc_catchup.py [--dry]
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
DB_TIMEOUT_SEC = 30
SECONDS_PER_HOUR = 3600.0
REASON = "재판정 채우기 (네 시간 확인)"


def _admin_cfg() -> dict:
    with open(os.path.join(ROOT, "config", "admin.json"),
              encoding="utf-8") as f:
        return json.load(f)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def last_recalc_hours(conn, at: str) -> float | None:
    """마지막 재판정이 ★ 몇 시간 전인가.  ★ 한 번도 없으면 None.

    ★ 판정이 끝난 시각을 본다 — ★ 큐에 넣은 시각이 아니다.
      ★ 넣기만 하고 안 돌면 ★ 「돌았다」가 되어 ★ 영영 안 채운다
    """
    row = conn.execute(
        "SELECT MAX(calculated_at) FROM result_score").fetchone()
    if not row or not row[0]:
        return None
    then = datetime.fromisoformat(row[0])
    now = datetime.fromisoformat(at)
    if then.tzinfo is None:
        then = then.replace(tzinfo=timezone.utc)
    return (now - then).total_seconds() / SECONDS_PER_HOUR



def collector_running(conn, at: str) -> tuple[bool, str]:
    """★★★★ 수집기가 지금 도는가 (마스터 0b ② · 08-30).

    ★★★ 마스터 — 「★ `CARWATCH_DEFER_RECALC` 를 타이머에도 준다.
      ★ `recalc_catchup.py` 가 ★ **수집기가 도는지 보고 돌면 미룬다**.
      ★ 「도는지」는 ★ **시각 짐작 말고** ★ 표로 본다」

    ★★ `collect_run` 표는 ★ **없다** (표 44개를 다 셌다 · 실측 08-30).
      ★ 그래서 ★ **`raw_response.fetched_at`** 으로 본다 —
      ★ ★ 수집기가 원문을 넣는 그 순간이 ★ 「도는 중」의 정본이다.
      ★ ★ 짐작이 아니라 ★ **그 사이트가 방금 무엇을 받았다는 사실**이다.
    ★ 창은 `config/admin.json` 이 정본이다 (V10-31) — ★ 코드에 안 박는다
    """
    win = float(_admin_cfg().get("collect_busy_minutes") or 10)
    row = conn.execute(
        "SELECT site, COUNT(*), MAX(fetched_at) FROM raw_response"
        " WHERE fetched_at > datetime(?, ?) GROUP BY site"
        " ORDER BY 3 DESC LIMIT 1", (at, f"-{win:g} minutes")).fetchone()
    if not row:
        return False, ""
    return True, f"{row[0]} 가 {win:g}분 안에 원문 {row[1]}건을 넣었다 (마지막 {row[2][11:19]})"


def main() -> int:
    at = _now()
    dry = "--dry" in sys.argv
    cfg = _admin_cfg()
    stale = float(cfg.get("recalc_stale_hours") or 4)
    conn = sqlite3.connect(DB, timeout=DB_TIMEOUT_SEC)
    try:
        # ★★★★★ 08-30 (마스터 0b ②) — ★ 수집기가 돌면 ★ **미룬다.**
        #   ★ 까닭 — ★ 재판정 한 판이 12~13분이고 ★ KB 한 회차가 297초다.
        #   ★ ★ 겹치면 ★ 수집기가 `database is locked` 로 죽는다 (08-29 실측).
        #   ★ 다음 타이머(네 시간 뒤)가 다시 본다 — ★ 밀린 것은 안 잃는다
        busy, why = collector_running(conn, at)
        if busy:
            print(f"★ 수집기가 도는 중이라 미룬다 — {why}")
            return 0
        age = last_recalc_hours(conn, at)
        if age is None:
            print("★ 재판정 기록이 없다 — 채운다")
        elif age <= stale:
            # ★ 돌았다.  ★ 아무것도 안 한다 (14-3 ②)
            print(f"마지막 재판정 {age:.1f}시간 전 · 기준 {stale:g}시간 — "
                  "★ 안 밀렸다.  아무것도 안 한다")
            return 0
        else:
            print(f"★ 마지막 재판정 {age:.1f}시간 전 · 기준 {stale:g}시간 — "
                  "★ 밀렸다.  채운다")
        if dry:
            print("★ --dry 라 큐에 안 넣었다")
            return 0
        # ★ 끊긴 작업을 먼저 닫는다 — ★ 하나가 running 으로 남으면 자동화가 통째로 멈춘다
        from store.adminops import reap_stale_jobs
        from tools.daily_enqueue import enqueue_daily

        dead = reap_stale_jobs(conn, cfg["job_stale_hours"], at)
        if dead:
            print(f"끊긴 작업 {len(dead)}건을 닫았습니다")
        got = enqueue_daily(conn, at)
    finally:
        conn.close()
    print(f"★ 재판정을 큐에 넣었습니다 — {got[:8]}" if got
          else "이미 도는 작업이 있어 건너뜁니다")
    return 0


if __name__ == "__main__":
    sys.exit(main())
