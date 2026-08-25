# -*- coding: utf-8 -*-
"""원문에 ★ 빠진 `run_id` 를 채운다 (`V1-19` · A-10 · 개발측 자진 수정).

쓰기   python3.11 tools/fill_raw_run_id.py --dry     세기만
      python3.11 tools/fill_raw_run_id.py           채운다

★★ 왜 비었나 — ★ 08-26 에 ★ 사이트 원문 보관(`save_site_raw`)을 켜면서
   ★ ★ `run_id` 를 ★ **안 넘겼다.**  ★ 내 결함이다.
   ★ ★ `V1-19` 가 ★ 「run_id 없는 원문 159건」으로 잡았다 —
     「★ run_id 가 없으면 ★ 어느 실행이 넣은 원문인지 ★ 못 되짚는다」
★★ 무엇으로 채우나 — ★ **지어내지 않는다.**
   ★ 같은 (사이트 · 엔드포인트) 묶음의 ★ **가장 이른 `fetched_at`** 을
   ★ ★ `run.py` 와 같은 꼴(`%Y%m%dT%H%M%S`)로 적는다.
   ★ ★ 그것은 ★ 「이 묶음은 그때 시작한 실행이 넣었다」는 ★ 참인 말이다
★ 앞으로는 ★ `store/raw.py` 의 `proc_run_id()` 가 ★ 프로세스마다 채운다
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from store.raw import commit, open_db          # noqa: E402


def main() -> int:
    dry = "--dry" in sys.argv
    conn = open_db(os.path.join(ROOT, "carwatch.db"))
    rows = conn.execute(
        "SELECT site, endpoint, COUNT(*), MIN(fetched_at)"
        "  FROM raw_response WHERE run_id IS NULL GROUP BY 1, 2"
        " ORDER BY 3 DESC").fetchall()
    if not rows:
        print("★ run_id 가 빈 원문이 없다")
        return 0
    total = sum(r[2] for r in rows)
    print(f"★ run_id 가 빈 원문 {total:,}건")
    plan = []
    for site, endpoint, n, first in rows:
        # ★ '2026-08-25T02:04:28.135989+00:00' → '20260825T020428'
        rid = (str(first)[:19].replace("-", "").replace(":", "")
               .replace("T", "T"))
        plan.append((site, endpoint, rid))
        print(f"   {site:<16} {endpoint:<8} {n:>6}건 · 첫 원문 {first}"
              f"  → run_id {rid}")
    if dry:
        print("★ --dry 라 바꾸지 않았다")
        return 0
    for site, endpoint, rid in plan:
        conn.execute(
            "UPDATE raw_response SET run_id=?"
            " WHERE run_id IS NULL AND site=? AND endpoint=?",
            (rid, site, endpoint))
    commit(conn)
    left = conn.execute(
        "SELECT COUNT(*) FROM raw_response WHERE run_id IS NULL").fetchone()[0]
    print(f"\n★ 채웠다 — 남은 것 {left:,}건")
    print("★ 원문은 한 글자도 안 건드렸다 — ★ run_id 칸만 채웠다")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
