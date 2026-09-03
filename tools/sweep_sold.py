# -*- coding: utf-8 -*-
"""철학 ② — ★ **팔린 것을 치운다** (마스터 확정 09-03 · `S46-267`).

돌리는 법
    python3.11 tools/sweep_sold.py                     ★ 센다 (안 고친다)
    python3.11 tools/sweep_sold.py --write             ★ 내린다
    python3.11 tools/sweep_sold.py --write --site encar
    python3.11 tools/sweep_sold.py --write --target KOLEOS_HEV
    python3.11 tools/sweep_sold.py --revive --write    ★ 「마」 되살리기

★ 정본은 `collect/sweep.py` 다.  ★ 여기 옮겨 적지 않는다
"""
from __future__ import annotations

import os
import sqlite3
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from collect.sweep import candidates, revive, sold_words, sweep_sold  # noqa: E402


def main() -> int:
    args = sys.argv[1:]
    write = "--write" in args

    def opt(name):
        return next((args[i + 1] for i, a in enumerate(args)
                     if a == name and i + 1 < len(args)), None)

    site = opt("--site")
    target = opt("--target")
    targets = (target,) if target else ()
    at = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(os.path.join(ROOT, "carwatch.db"), timeout=60)
    conn.execute("PRAGMA busy_timeout = 60000")

    print(f"★ 「팔렸다」로 보는 말 — {' · '.join(sold_words())}"
          "  (config/scoring.json 이 정본)")

    if "--revive" in args:
        if not write:
            print("★ `--write` 가 없다.  ★ 안 고친다")
            return 0
        n = revive(conn, at, site=site)
        print(f"★ 「마」 되살린 것 {n:,}건 (relisted)")
        return 0

    got = candidates(conn, site=site, target_keys=targets)
    tally: dict = {}
    for _lid, _sid, why in got:
        tally[why] = tally.get(why, 0) + 1
    live = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE status IN ('active','new')"
        + (" AND site=?" if site else "")
        + (" AND target_key=?" if target else ""),
        tuple(x for x in (site, target) if x)).fetchone()[0]
    print(f"★ 마스터 화면에 살아 있는 것 {live:,}건")
    print(f"★ 그중 내릴 것 {len(got):,}건"
          f" ({len(got) / live * 100:.1f}%)" if live else "")
    for why, n in sorted(tally.items(), key=lambda x: -x[1]):
        print(f"   {why:<28}{n:>8,}")
    if not write:
        print("★ `--write` 가 없다.  ★ 안 내린다")
        return 0
    done = sweep_sold(conn, at, site=site, target_keys=targets)
    total = sum(done.values())
    print(f"★ 내렸다 {total:,}건 — ★ 지운 것이 아니다 (`gone` · gone_at 을 남긴다)")
    for why, n in sorted(done.items(), key=lambda x: -x[1]):
        print(f"   {why:<28}{n:>8,}")
    left = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE status IN ('active','new')"
        + (" AND site=?" if site else "")
        + (" AND target_key=?" if target else ""),
        tuple(x for x in (site, target) if x)).fetchone()[0]
    print(f"★ 남은 것 {left:,}건 ({live:,} → {left:,})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
