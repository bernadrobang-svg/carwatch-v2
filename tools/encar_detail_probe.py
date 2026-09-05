# -*- coding: utf-8 -*-
"""엔카 상세를 서버에서 얼마나 받을 수 있는가 — ★ 두드려 재는 자 (지시 r1184 E).

★ 「막혔다」는 ★ 증거가 있어야 적는다 (`S46-256` · 내가 두 번 틀렸다).
★ 간격을 바꿔 가며 ★ 몇 번째에 407 이 나는지 센다.  ★ 회선은 안 바꾼다
"""
from __future__ import annotations

import sqlite3
import sys
import time
import urllib.error
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
      " (KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def one(source_id: str) -> tuple:
    url = f"https://api.encar.com/v1/readside/vehicle/{source_id}"
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept": "application/json",
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Referer": "https://fem.encar.com/"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, len(r.read())
    except urllib.error.HTTPError as e:
        return e.code, 0
    except OSError as e:
        return type(e).__name__, 0


def probe(gap: float, n: int, db: str = "carwatch.db") -> list:
    conn = sqlite3.connect(db)
    ids = [r[0] for r in conn.execute(
        "SELECT source_id FROM core_listing WHERE site='encar'"
        " AND detail_status IS NULL AND target_key IS NOT NULL LIMIT ?", (n,))]
    got = []
    for i, sid in enumerate(ids):
        code, size = one(sid)
        got.append((i + 1, sid, code, size))
        print(f"  #{i + 1:<3} {sid}  {code}  {size}B", flush=True)
        if i < len(ids) - 1:
            time.sleep(gap)
    ok = sum(1 for g in got if g[2] == 200)
    print(f"간격 {gap}s · {len(got)}번 시도 → 200 {ok}건 · "
          f"407 {sum(1 for g in got if g[2] == 407)}건")
    return got


if __name__ == "__main__":
    probe(float(sys.argv[1]) if len(sys.argv) > 1 else 5.0,
          int(sys.argv[2]) if len(sys.argv) > 2 else 10)
