# -*- coding: utf-8 -*-
"""4-4 — ★ **407 이 `not_found` 로 굳은 자리를 푼다** (지시문 r1141 · `S46-267`).

★★★ 지시 4-4 — 「★ 엔카 **407** 이 `not_found` 로 굳는 자리 — ★ `error` 로」

★ **왜 이것이 큰일인가** — ★ 철학 ②의 「다」가 ★ `detail_status='not_found'` 를
  ★ ★ 「상세로 대조했더니 없더라」로 읽는다.  ★ 그런데 ★ **407 은 대조가 아니다** —
  ★ ★ ★ 「우리가 못 받았다」다.  ★ 그것으로 죽이면 ★ **산 차를 죽인다**.

★ 실측 09-04 —

| 무엇 | 수 |
|---|--:|
| 엔카 `detail_status='not_found'` | **9,377** |
| ★ 그중 ★ **407 봉투가 있다** | ★ **9,348** |
| 참 404 봉투가 있다 | 429 |
| 봉투가 아예 없다 | 0 |

★ 잣대 — ★ `not_found` 인데 ★ **407 봉투가 있고 ★ 404 봉투가 없는** 것만 ★ `error` 로 돌린다.
  ★ ★ 참 404 가 하나라도 있으면 ★ **안 건드린다** — ★ 사이트가 「없다」고 답한 것이다.

★ 그리고 ★ 그 거짓 증거로 ★ `gone` 이 된 것을 ★ **되살린다** —
  ★ `core_listing_change.cause` 가 ★ 「다-상세가없다함」 **하나뿐**인 것만.
  ★ ★ 「나-사이트가팔렸다함」이 함께 적힌 것은 ★ **그대로 둔다** (사이트가 말한 것이다)

돌리는 법
    python3.11 tools/fix_407_not_found.py            ★ 센다
    python3.11 tools/fix_407_not_found.py --write    ★ 고친다
"""
from __future__ import annotations

import os
import sqlite3
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from store.core import record_change  # noqa: E402

CAUSE = "407 은 「없다」가 아니라 「못 받았다」다 (지시 4-4 · 09-04)"

# ★ `not_found` 인데 ★ 407 봉투가 있고 ★ 404 봉투가 없는 것
FROZEN = """
  SELECT l.listing_id, l.site, l.status FROM core_listing l
   WHERE l.detail_status = 'not_found'
     AND EXISTS (SELECT 1 FROM raw_response r
                  WHERE r.site = l.site AND r.endpoint = 'detail'
                    AND r.source_id = l.source_id AND r.http_code = 407)
     AND NOT EXISTS (SELECT 1 FROM raw_response r
                  WHERE r.site = l.site AND r.endpoint = 'detail'
                    AND r.source_id = l.source_id AND r.http_code = 404)
"""

# ★ 그 거짓 증거 하나로만 죽은 것 — ★ 「나」가 함께 적힌 것은 뺀다
ONLY_DETAIL = """
  SELECT 1 FROM core_listing_change c
   WHERE c.listing_id = ? AND c.new_value = 'gone'
     AND c.cause LIKE '%다-상세가없다함%'
     AND c.cause NOT LIKE '%나-사이트가팔렸다함%'
"""


def main() -> int:
    write = "--write" in sys.argv
    conn = sqlite3.connect(os.path.join(ROOT, "carwatch.db"), timeout=60)
    conn.execute("PRAGMA busy_timeout = 60000")
    at = datetime.now(timezone.utc).isoformat()

    rows = conn.execute(FROZEN).fetchall()
    per: dict = {}
    for _lid, site, st in rows:
        per.setdefault(site, {"합": 0, "gone": 0})
        per[site]["합"] += 1
        if st == "gone":
            per[site]["gone"] += 1
    print(f"★ 407 이 `not_found` 로 굳은 행 {len(rows):,}개")
    for site, n in sorted(per.items(), key=lambda x: -x[1]["합"]):
        print(f"   {site:<16}{n['합']:>7,}  (그중 gone {n['gone']:,})")
    if not write:
        print("★ `--write` 가 없다.  ★ 안 고친다")
        return 0

    fixed = revived = 0
    for lid, _site, st in rows:
        conn.execute("UPDATE core_listing SET detail_status='error'"
                     " WHERE listing_id=?", (lid,))
        record_change(conn, lid, "detail_status", "not_found", "error", at,
                      "status", cause=CAUSE)
        fixed += 1
        # ★ 그 거짓 증거 하나로만 죽었으면 ★ 되살린다
        if st == "gone" and conn.execute(ONLY_DETAIL, (lid,)).fetchone():
            conn.execute("UPDATE core_listing SET status='active',"
                         " gone_at=NULL WHERE listing_id=?", (lid,))
            record_change(conn, lid, "status", "gone", "active", at,
                          "relisted", cause=CAUSE)
            revived += 1
        if fixed % 500 == 0:
            conn.commit()
    conn.commit()
    print(f"★ `error` 로 돌린 행 {fixed:,}개 · ★ 되살린 매물 {revived:,}건")
    left = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE detail_status='not_found'"
    ).fetchone()[0]
    print(f"★ 남은 `not_found` {left:,}건 — ★ 참 404 가 있는 것만 남았다")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
