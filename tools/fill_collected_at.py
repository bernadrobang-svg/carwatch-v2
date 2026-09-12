# -*- coding: utf-8 -*-
"""★ R-1 — ★ `collected_at` 을 ★ **원문 파일**에서 채운다 (09-12 지시).

★★★ 실측 09-12 — ★ 엔카 말고 ★ **열한 곳이 전부 빈칸**이었다.
  ★ 그래서 ★ 「그 사이트를 언제 마지막으로 받았나」를 ★ 아무도 못 봤고,
  ★ ★ 엔카가 ★ **일주일 멈춘 것**도 못 봤다.

★★ 왜 원문에서 채우나 — ★ `collected_at` 은 `collect/runner.py` 의 ★ **S3 경로**에만
  있다.  ★ 사이트별 수집기(`collect_kbchachacha` 따위)는 ★ 그 길을 안 지난다.
  ★ ★ **원문 파일이 정본이다** (S46-185) — ★ 그 파일이 ★ 「언제 받았나」를 안다.
★ 지어내지 않는다 — ★ 원문이 없는 매물은 ★ **그대로 빈칸**이다 (금지 12)

돌리는 법
    python3.11 tools/fill_collected_at.py            ★ 잰다
    python3.11 tools/fill_collected_at.py --write    ★ 넣는다
"""
from __future__ import annotations

import os
import sqlite3
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from store.rawfile import read, walk          # noqa: E402


def newest(site: str) -> dict:
    """{매물번호: 가장 새 원문의 때}.  ★ 창구를 안 가린다 — ★ 아무거나 받았으면 받은 것이다."""
    got: dict = {}
    for ep in ("detail", "list", "inspection", "record"):
        for path in walk(site=site, endpoint=ep, root=ROOT):
            env = read(path) or {}
            at = env.get("fetched_at") or env.get("at") or env.get("asked_at")
            if not at:
                continue
            sid = str(env.get("source_id") or os.path.basename(path)[:-5])
            if sid and (sid not in got or str(at) > got[sid]):
                got[sid] = str(at)
    return got


def run(write: bool = False, db: str = "carwatch.db") -> Counter:
    conn = sqlite3.connect(os.path.join(ROOT, db))
    sites = [r[0] for r in conn.execute(
        "SELECT DISTINCT site FROM core_listing ORDER BY site")]
    tally: Counter = Counter()
    for site in sites:
        book = newest(site)
        if not book:
            tally[f"{site} 원문이 없다"] += 1
            continue
        mine = {str(r[0]): r[1] for r in conn.execute(
            "SELECT source_id, collected_at FROM core_listing WHERE site = ?",
            (site,))}
        n = 0
        for sid, at in book.items():
            if sid not in mine or mine[sid]:
                continue
            n += 1
            if write:
                conn.execute(
                    "UPDATE core_listing SET collected_at = ?"
                    " WHERE site = ? AND source_id = ? AND collected_at IS NULL",
                    (at, site, sid))
        tally[f"{site}"] = n
    if write:
        conn.commit()
    conn.close()
    return tally


if __name__ == "__main__":
    for k, v in sorted(run("--write" in sys.argv).items(), key=lambda x: -x[1]):
        print(f"  {k:22} {v:,}")
