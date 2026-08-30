#!/usr/bin/env python3.11
"""★★★★ 「신차가 < 현재값」인 신차가를 지운다 (마스터 지시 2 · 08-30).

★★★ 마스터 — 「★ 값이 현재값보다 작으면 ★ **신차가가 아니다**」
★ 실측 08-30 — ★ 477건이었다 (엔카 418 · 리본카 36 · KB 13 · 헤이딜러 9 · 렉서스 1).
  ★ ★ 리본카는 ★ 신차가가 ★ **10,000원**인 것이 있었다 — ★ 값은 9,420만이다.
★ 앞으로 들어오는 것은 ★ `store/core._drop_impossible_origin` 이 문에서 막는다.
  ★ ★ 이 도구는 ★ **이미 든 것**만 치운다 — ★ 한 번 돌리면 끝이다.
★ 지어내지 않는다 — ★ `NULL` 로 둔다 (「모름」이다).  ★ 0 으로 채우면 감가율이 거짓이 된다
★ 자취(`core_listing_change`)에 남긴다 — ★ 조용히 고치지 않는다

사용   python3.11 tools/clear_bad_origin.py           재기만 한다
      python3.11 tools/clear_bad_origin.py --write   지운다
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from store.core import record_change  # noqa: E402
from store.raw import commit, connect_db  # noqa: E402


def main() -> int:
    write = "--write" in sys.argv
    conn = connect_db(os.path.join(ROOT, "carwatch.db"))
    rows = conn.execute(
        "SELECT listing_id, site, source_id, price_origin_won, price_current_won"
        "  FROM core_listing"
        " WHERE price_origin_won IS NOT NULL AND price_current_won IS NOT NULL"
        "   AND price_origin_won < price_current_won"
        " ORDER BY site, listing_id").fetchall()
    per: dict = {}
    for _lid, site, _sid, _own, _now in rows:
        per[site] = per.get(site, 0) + 1
    print(f"★ 「신차가 < 현재값」인 것 {len(rows):,}건")
    for site, n in sorted(per.items(), key=lambda x: -x[1]):
        print(f"   {site:16s} {n:5d}")
    if not write:
        print("★ --write 를 줘야 지운다 (지금은 재기만 했다)")
        return 0
    at = datetime.now(timezone.utc).isoformat()
    for lid, _site, _sid, own, _now in rows:
        conn.execute("UPDATE core_listing SET price_origin_won=NULL"
                     " WHERE listing_id=?", (lid,))
        # ★ `change_kind` 는 정해진 값만 받는다 (DDL CHECK) — ★ `anomaly` 가 그것이다
        record_change(conn, lid, "price_origin_won", str(own), None, at, "anomaly")
    commit(conn)
    print(f"★ {len(rows):,}건의 신차가를 지웠다 (NULL · 「모름」)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
