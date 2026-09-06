# -*- coding: utf-8 -*-
"""이미 받아 둔 엔카 상세 원문에서 ★ **새 칸만** 다시 읽는다 (r1190 K-2 · A-19).

★ 다시 받지 않는다 — ★ 파일이 원본이다 (`S46-185`).
★ 채우는 칸 — `delivery_nationwide`(전국 배달) · `site_inspection`(사이트 진단).
★ 이미 값이 있는 칸은 안 덮는다.  ★ 못 읽으면 ★ NULL 로 둔다 — ★ N 이 아니다 (K-4).

돌리는 법
    python3.11 tools/refill_encar_detail.py           ★ 잰다
    python3.11 tools/refill_encar_detail.py --write   ★ 넣는다
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from parse.encar.mapping import parse_detail  # noqa: E402
from store.rawfile import walk, read          # noqa: E402

COLS = ("delivery_nationwide", "site_inspection")


def run(write: bool = False, db: str = "carwatch.db") -> Counter:
    conn = sqlite3.connect(os.path.join(ROOT, db))
    ids = {str(r[1]): r[0] for r in conn.execute(
        "SELECT listing_id, source_id FROM core_listing WHERE site='encar'")}
    tally: Counter = Counter()
    for path in walk(site="encar", endpoint="detail", root=ROOT):
        env = read(path) or {}
        body = env.get("body")
        if not body:
            tally["몸통 없음"] += 1
            continue
        try:
            got = parse_detail(json.loads(body), "encar", env.get("source_id"))
        except (ValueError, TypeError, AttributeError, KeyError):
            tally["못 읽음"] += 1
            continue
        lid = ids.get(str(env.get("source_id") or ""))
        if lid is None:
            tally["매물 없음"] += 1
            continue
        vals = {c: got.get(c) for c in COLS if got.get(c) is not None}
        if not vals:
            tally["값 없음"] += 1
            continue
        for c, v in vals.items():
            tally[f"{c}={v}"] += 1
        if write:
            sets = ", ".join(f"{c}=?" for c in vals)
            conn.execute(f"UPDATE core_listing SET {sets} WHERE listing_id=?",
                         [*vals.values(), lid])
        tally["채움"] += 1
    if write:
        conn.commit()
    conn.close()
    return tally


if __name__ == "__main__":
    got = run("--write" in sys.argv)
    for k, v in sorted(got.items()):
        print(f"  {k:34} {v:,}")
