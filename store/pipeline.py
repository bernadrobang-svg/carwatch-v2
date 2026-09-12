# -*- coding: utf-8 -*-
"""★ 수집 기록 — ★ 「그날 그 사이트가 뭘 했나」를 남긴다 (09-12 지시 1번).

★★★ 왜 새 표인가 —
  ★ `audit_request` 는 ★ **건별 요청**이다.  ★ 「그 사이트가 오늘 뭘 했나」를 못 낸다.
  ★ `recalc_job` 은 ★ **판정 작업**이지 ★ 수집 기록이 아니다.
★★ 그래서 ★ 엔카가 ★ **일주일째 멈춘 것**을 ★ 아무도 못 봤다 (실측 09-12 — 09-04 가 마지막).

★★★ 「자동으로 저장하면 무엇이 들어갔는지 모른다」 —
  ★ 그 걱정을 ★ **이 표가 푼다.**  ★ 사람이 누르는 것으로 풀 일이 아니다.
  ★ 두드린 수 · 받은 수 · 넣은 수 · 막힌 수를 ★ 낱개 까닭과 함께 남긴다
"""
from __future__ import annotations

import secrets
import sqlite3
from datetime import datetime, timezone

RUN_ID_BYTES = 8


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def start(conn: sqlite3.Connection, site: str, step: str,
          trigger: str = "schedule") -> str:
    """한 판을 연다 → ★ `run_id`."""
    rid = secrets.token_hex(RUN_ID_BYTES)
    conn.execute(
        "INSERT INTO pipeline_run(run_id, site, step, trigger, status,"
        " asked, got, stored, blocked, started_at)"
        " VALUES (?,?,?,?,'running',0,0,0,0,?)",
        (rid, site, step, trigger, _now()))
    conn.commit()
    return rid


def say(conn: sqlite3.Connection, rid: str, kind: str, said: str,
        source_id: str | None = None) -> None:
    """왜 그렇게 됐는지 ★ 한 줄 남긴다.  ★ 셈도 함께 올린다."""
    conn.execute(
        "INSERT INTO pipeline_reason(run_id, at, kind, source_id, said)"
        " VALUES (?,?,?,?,?)", (rid, _now(), kind, source_id, said[:400]))
    if kind in ("asked", "got", "stored", "blocked"):
        conn.execute(
            f"UPDATE pipeline_run SET {kind} = COALESCE({kind}, 0) + 1"
            "  WHERE run_id = ?", (rid,))
    conn.commit()


def done(conn: sqlite3.Connection, rid: str, status: str = "done",
         detail: str = "") -> None:
    """판을 닫는다.  ★ 「막혔다」도 ★ **끝난 것**이다 — ★ 열어 둔 채 두지 않는다."""
    conn.execute(
        "UPDATE pipeline_run SET status = ?, ended_at = ?, detail = ?"
        "  WHERE run_id = ?", (status, _now(), detail[:400], rid))
    conn.commit()


def latest(conn: sqlite3.Connection, limit: int = 40) -> list:
    """사이트마다 ★ **마지막 판**.  ★ 현황 화면이 이것을 낸다."""
    return conn.execute(
        "SELECT r.site, r.step, r.status, r.asked, r.got, r.stored,"
        "       r.blocked, r.started_at, r.ended_at, r.detail"
        "  FROM pipeline_run r"
        "  JOIN (SELECT site, MAX(started_at) AS at FROM pipeline_run"
        "         GROUP BY site) m"
        "    ON m.site = r.site AND m.at = r.started_at"
        " ORDER BY r.started_at DESC LIMIT ?", (limit,)).fetchall()
