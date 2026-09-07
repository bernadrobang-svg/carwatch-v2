# -*- coding: utf-8 -*-
"""원문 파일이 ★ `ok` 인데 ★ DB 가 ★ 「못 받았다」로 적힌 자리를 고친다 (09-08).

★★★ 실측 09-08 — ★ 마스터 회선으로 받아 ★ `ok` 였던 상세 둘이
  ★ 하룻밤 사이 ★ **`error` 로 덮여** 있었다.  ★ 원문 파일은 ★ 그대로였다.
  ★ ★ 곧 ★ **자료는 있는데 없다고 적힌 것**이다 — ★ 화면이 「미조회」라 거짓말한다.
★ 되덮는 자리는 막았다 (`collect/runner.py` · `report/screens/fetch.py`).
  ★ 이 자는 ★ **이미 어긋난 것**을 원문 기준으로 되돌린다.
★ 파일이 정본이다 (`S46-185`).  ★ 다시 받지 않는다

돌리는 법
    python3.11 tools/heal_status_from_raw.py            ★ 잰다
    python3.11 tools/heal_status_from_raw.py --write    ★ 고친다
"""
from __future__ import annotations

import os
import sqlite3
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from store.rawfile import read, walk  # noqa: E402

# ★ 「잘 받았다」로 볼 상태.  ★ 이보다 낮은 것으로 덮여 있으면 되돌린다
GOOD = ("ok", "not_found")
LOW = ("error", "empty")


def run(write: bool = False, db: str = "carwatch.db") -> Counter:
    conn = sqlite3.connect(os.path.join(ROOT, db))
    cols = {r[1] for r in conn.execute("PRAGMA table_info(core_listing)")}
    tally: Counter = Counter()
    base = os.path.join(ROOT, "raw")
    for site in sorted(os.listdir(base)) if os.path.isdir(base) else []:
        sdir = os.path.join(base, site)
        if not os.path.isdir(sdir):
            continue
        for kind in sorted(os.listdir(sdir)):
            col = f"{kind}_status"
            if col not in cols:
                continue
            # ★ 매물마다 ★ **가장 좋은** 파일 상태를 본다 —
            #   ★ 같은 매물을 여러 날 받았으면 ★ 하나라도 `ok` 면 받은 것이다
            best: dict = {}
            for path in walk(site=site, endpoint=kind, root=ROOT):
                env = read(path) or {}
                sid = str(env.get("source_id") or "")
                if not sid:
                    continue
                st = str(env.get("status") or "")
                if st in GOOD and (env.get("body") or st == "not_found"):
                    best[sid] = "ok" if st == "ok" else best.get(sid, st)
            if not best:
                continue
            marks = ",".join("?" * len(LOW))
            rows = conn.execute(
                f"SELECT source_id, {col} FROM core_listing"
                f" WHERE site = ? AND {col} IN ({marks})",
                (site, *LOW)).fetchall()
            for sid, was in rows:
                good = best.get(str(sid))
                if not good:
                    continue
                tally[f"{site}.{kind}  {was} → {good}"] += 1
                if write:
                    conn.execute(
                        f"UPDATE core_listing SET {col} = ?"
                        " WHERE site = ? AND source_id = ?",
                        (good, site, str(sid)))
    if write:
        conn.commit()
    conn.close()
    return tally


if __name__ == "__main__":
    got = run("--write" in sys.argv)
    if not got:
        print("  어긋난 자리가 없다")
    for k, v in sorted(got.items()):
        print(f"  {k:36} {v:,}건")
    print(f"  합 {sum(got.values()):,}건")
