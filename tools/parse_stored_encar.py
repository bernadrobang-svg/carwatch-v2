# -*- coding: utf-8 -*-
"""이미 가진 엔카 상세 원문을 ★ `core_listing` 칸에 넣는다 (09-08).

★★★ 실측 09-08 — ★ 원문 파일은 ★ `ok` 인데 ★ DB 는 ★ `error` 로 적혀 있었다
  (`tools/heal_status_from_raw.py` 가 ★ **8,450건**을 찾았다).
  ★ 상태만 되돌려서는 ★ 칸이 안 찬다 — ★ **원문을 읽어 넣어야** 한다.
★ 다시 받지 않는다.  ★ 파일이 정본이다 (`S46-185`).
★ `refill_encar_detail` 은 ★ 칸 둘만 썼다 — ★ 이 자는 ★ **파서가 주는 칸을 다** 넣는다

돌리는 법
    python3.11 tools/parse_stored_encar.py            ★ 잰다
    python3.11 tools/parse_stored_encar.py --write    ★ 넣는다
"""
from __future__ import annotations

import os
import sqlite3
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from report.screens.fetch import _parse_into  # noqa: E402
from store.rawfile import read, walk          # noqa: E402


def run(write: bool = False, db: str = "carwatch.db") -> Counter:
    conn = sqlite3.connect(os.path.join(ROOT, db))
    have = {str(r[0]) for r in conn.execute(
        "SELECT source_id FROM core_listing WHERE site='encar'")}
    tally: Counter = Counter()
    seen: set = set()
    # ★ 새 파일이 먼저다 — ★ 같은 매물을 여러 날 받았으면 ★ 마지막 것을 쓴다
    for path in sorted(walk(site="encar", endpoint="detail", root=ROOT),
                       reverse=True):
        env = read(path) or {}
        sid = str(env.get("source_id") or "")
        if not sid or sid in seen or sid not in have:
            tally["건너뜀"] += 1
            continue
        if str(env.get("status") or "") != "ok" or not env.get("body"):
            continue
        seen.add(sid)
        if not write:
            tally["넣을 것"] += 1
            continue
        got = _parse_into(conn, "encar", "detail", sid, env["body"], ROOT)
        tally["채움" if got else "못 읽음"] += 1
    conn.close()
    return tally


if __name__ == "__main__":
    for k, v in sorted(run("--write" in sys.argv).items()):
        print(f"  {k:12} {v:,}")
