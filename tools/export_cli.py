# -*- coding: utf-8 -*-
"""데이터 내보내기 (9장 STEP 91a · B-6).

사용     python3 run.py export --format csv
         python3 run.py export --format json --target KOLEOS_HEV

★ 개인정보는 나가지 않는다.  core_pii 를 읽지 않는다 (STEP 35)
★ 덮어쓰지 않는다.  같은 이름이면 실패한다 — 어제 것과 비교해야 한다
금지     임의 위치에 쓰는 것.  outputs/ 고정이다
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from report.exports.export import (  # noqa: E402
    CSV, JSON, MD, export, write_export,
)
from report.render import render_listing  # noqa: E402
from report.views import ReportMeta  # noqa: E402

FORMATS = (CSV, JSON, MD)


def _cfg(name: str) -> dict:
    with open(os.path.join(ROOT, "config", name), encoding="utf-8") as f:
        return json.load(f)


def _opt(args: list, name: str) -> str | None:
    return (args[args.index(name) + 1]
            if name in args and args.index(name) + 1 < len(args) else None)


def main() -> int:
    args = sys.argv[1:]
    fmt = _opt(args, "--format") or CSV
    if fmt not in FORMATS:
        print(f"[X] --format 은 {' · '.join(FORMATS)} 중 하나다: {fmt}")
        return 2
    target = _opt(args, "--target")

    db = os.path.join(ROOT, "carwatch.db")
    if not os.path.isfile(db):
        print(f"[X] DB 가 없다: {db}")
        return 2
    conn = sqlite3.connect(db)
    ver = conn.execute(
        "SELECT MAX(calc_version) FROM result_score").fetchone()[0]
    if not ver:
        print("[X] 판정 결과가 없다.  먼저 수집·채점을 돌린다")
        return 2

    sql = ("SELECT s.listing_id FROM result_score s "
           "JOIN core_listing l ON l.listing_id = s.listing_id "
           "WHERE s.calc_version = ?")
    params: list = [ver]
    if target:
        sql += " AND l.target_key = ?"
        params.append(target)
    lids = [r[0] for r in conn.execute(sql + " ORDER BY s.listing_id", params)]
    if not lids:
        print("[X] 내보낼 판정 결과가 없다")
        return 2

    fin, lab, pol = (_cfg("finance.json"), _cfg("labels.json"),
                     _cfg("scoring.json"))
    views = [render_listing(conn, lid, ver, fin, pol, ROOT) for lid in lids]

    run_id = (conn.execute("SELECT run_id FROM audit_request "
                           "ORDER BY id DESC LIMIT 1").fetchone()
              or ("manual",))[0]
    # ★ 전 요소를 ReportMeta 에서 가져온다.  손으로 조립하지 않는다 (STEP 91a)
    meta = ReportMeta(run_id=run_id, layer="L2", site="encar",
                      target_key=target or "all", calc_version=ver,
                      generated_at=None)
    res = export(views if fmt != MD else views[0], fmt, lab, meta=meta)
    try:
        path = write_export(res, ROOT)
    except FileExistsError as e:
        print(f"[X] {e}")
        return 2
    print(f"{fmt.upper()} {len(views):,}건 → {os.path.relpath(path, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
