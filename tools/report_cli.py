# -*- coding: utf-8 -*-
"""리포트 재생성 (9장 STEP 90 · 91a · B-6).

사용     python3 run.py report
         python3 run.py report --target KOLEOS_HEV
         python3 run.py report --listing 242

★ 덮어쓰지 않고 새 파일로 낸다.  재생성이 필요하면 calc_version 이 올라간 뒤다
★ L1 은 매물별이라 수가 많다.  --target 없이 부르면 L2 · L3 만 낸다
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from report.exports.export import MD, export, write_export  # noqa: E402
from report.render import (  # noqa: E402
    render_listing, render_run, render_target,
)

L1_LIMIT = 50   # ★ 한 번에 내는 L1 상한.  전량은 export 가 낸다


def _cfg(name: str) -> dict:
    with open(os.path.join(ROOT, "config", name), encoding="utf-8") as f:
        return json.load(f)


def _opt(args: list, name: str) -> str | None:
    return (args[args.index(name) + 1]
            if name in args and args.index(name) + 1 < len(args) else None)


def _write(report, labels, made: list) -> None:
    """★ 이미 있으면 건너뛴다.  덮어쓰지 않는다 (V8-01)."""
    res = export(report, MD, labels)
    try:
        made.append(os.path.relpath(write_export(res, ROOT), ROOT))
    except FileExistsError:
        made.append(f"(이미 있음) {res.filename}")
    except ValueError as e:
        made.append(f"(건너뜀) {e}")


def main() -> int:
    args = sys.argv[1:]
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
    run_id = (conn.execute("SELECT run_id FROM audit_request "
                           "ORDER BY id DESC LIMIT 1").fetchone()
              or ("manual",))[0]

    fin, lab, pol = (_cfg("finance.json"), _cfg("labels.json"),
                     _cfg("scoring.json"))
    made: list = []

    listing = _opt(args, "--listing")
    target = _opt(args, "--target")

    if listing:
        if not listing.isdigit():
            print(f"[X] --listing 은 숫자다: {listing}")
            return 2
        _write(render_listing(conn, int(listing), ver, fin, pol, root=ROOT),
               lab, made)
    else:
        # L2 — 차종별
        keys = ([target] if target else
                [r[0] for r in conn.execute(
                    "SELECT DISTINCT target_key FROM core_listing "
                    "WHERE target_key IS NOT NULL ORDER BY 1")])
        for key in keys:
            # ★ root 는 키워드로 넘긴다.  자리로 넘기면 top_n 에 들어간다
            _write(render_target(conn, key, run_id, ver, fin, pol,
                                 root=ROOT), lab, made)
        # L3 — 실행 전체
        _write(render_run(conn, run_id, ver), lab, made)
        # L1 — --target 을 준 경우만
        if target:
            lids = [r[0] for r in conn.execute(
                "SELECT s.listing_id FROM result_score s "
                "JOIN core_listing l ON l.listing_id = s.listing_id "
                "WHERE s.calc_version = ? AND l.target_key = ? "
                "ORDER BY s.listing_id LIMIT ?", (ver, target, L1_LIMIT))]
            for lid in lids:
                _write(render_listing(conn, lid, ver, fin, pol, root=ROOT),
                       lab, made)

    for m in made:
        print(f"  {m}")
    print(f"리포트 {len(made)}건")
    return 0


if __name__ == "__main__":
    sys.exit(main())
