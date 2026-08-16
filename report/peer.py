# -*- coding: utf-8 -*-
"""유사군 조회 (7장 STEP 82e).

지시서   STEP 82e · STEP 15a (의존 방향)
근거     ★ 조회는 store 가 아니라 호출자가 한다.
         store 가 analyze 를 부르면 층이 거꾸로 간다.
         report 는 store · analyze 를 둘 다 볼 수 있는 유일한 층이다
금지     analyze 안에서 DB 를 여는 것 (S11)
"""
from __future__ import annotations

import sqlite3

from analyze.peer import build_peer_group, empty_peer_group, stage_conditions


def peer_group(conn: sqlite3.Connection, snap, policy_raw: dict):
    """표본이 최소치 미만이면 조건을 넓힌다.  그래도 미달이면 NULL."""
    need = int(policy_raw["peer_min_sample"])
    for stage, cond in stage_conditions(snap, policy_raw):
        where = ["target_key = :target_key", "status = 'active'",
                 "price_current_won IS NOT NULL"]
        if "trim_badge" in cond:
            where.append("trim_badge = :trim_badge")
        if "year_from" in cond:
            where.append("CAST(SUBSTR(year_month,1,4) AS INTEGER) "
                         "BETWEEN :year_from AND :year_to")
        if "mileage" in cond:
            where.append("ABS(mileage_km - :mileage) <= :mileage_window")
        rows = [r[0] for r in conn.execute(
            "SELECT price_current_won FROM core_listing WHERE "
            + " AND ".join(where), cond)]
        if len(rows) >= need:
            return build_peer_group(rows, stage, policy_raw)
    return empty_peer_group()
