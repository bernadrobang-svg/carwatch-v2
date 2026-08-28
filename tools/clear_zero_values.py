# -*- coding: utf-8 -*-
"""★★ 「값이 아닌 0」을 ★ 모름(NULL)으로 되돌린다.

★★★ 08-28 실측 — ★ `displacement_cc = 0` 이 ★ 256건 있었다
  (엔카 179 · 리본카 55 · KB 22).  ★ 0cc 짜리 차는 없다 — ★ 「모름」이다.
★ 그것 때문에 ★ KB 상세 받기가 멈췄다 —
  ★ 「불변 필드 변경: displacement_cc 0 → 3470 — 원인 분류 못 함」 (STEP 29).
★ 앞으로 들어오는 것은 ★ `store/core.upsert_core` 가 막는다 (`NOT_A_VALUE`).
★ 이 도구는 ★ **이미 들어간 것**만 되돌린다 — ★ 한 번 돌리면 끝이다.
★ 원문은 안 건드린다.  ★ 다른 칸도 안 건드린다.

사용   python3.11 tools/clear_zero_values.py           재기만 한다
      python3.11 tools/clear_zero_values.py --write   되돌린다
"""
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "carwatch.db")
# ★ 정본은 store/core.NOT_A_VALUE 다 — ★ 두 벌을 만들지 않는다
sys.path.insert(0, ROOT)


def main(write: bool) -> int:
    from store.core import NOT_A_VALUE

    if not os.path.isfile(DB):
        print("carwatch.db 가 없다")
        return 1
    conn = sqlite3.connect(DB)
    try:
        total = 0
        for col, bad in NOT_A_VALUE.items():
            marks = ",".join("?" * len(bad))
            rows = conn.execute(
                f"SELECT site, COUNT(*) n FROM core_listing"
                f" WHERE {col} IN ({marks}) GROUP BY site ORDER BY n DESC",
                tuple(bad)).fetchall()
            n = sum(x[1] for x in rows)
            total += n
            print(f"★ {col} 이 값이 아닌 것 {n}건")
            for site, cnt in rows:
                print(f"   {site:<16}{cnt:>7}")
            if write and n:
                conn.execute(
                    f"UPDATE core_listing SET {col} = NULL"
                    f" WHERE {col} IN ({marks})", tuple(bad))
        if not write:
            print("  ★ --write 없이는 재기만 한다")
            return 0
        conn.commit()
        print(f"★ 되돌렸다 {total}건 (모름으로 둔다)")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main("--write" in sys.argv))
