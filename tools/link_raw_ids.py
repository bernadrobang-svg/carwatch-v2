# -*- coding: utf-8 -*-
"""★★ 이미 쌓인 원문의 `listing_id` 를 ★ `source_id` 로 이어 채운다.

★★★ 마스터 지시 08-26 — 「★ 정본은 사이트 매물번호(`source_id`)다.
  ★ `request_url` 에서 되뽑는 건 ★ 임시다.  규격이 아니다.
  ★ `listing_id` 도 ★ 지우지 말고 ★ **둘 다 둬라**」

★ 앞으로 들어오는 것은 ★ `store/raw.py` 의 `save_site_raw` 가 채운다.
  ★ 이 도구는 ★ **이미 쌓인 것**만 메운다 — ★ 한 번 돌리면 끝이다.
★ 원문을 ★ 다시 받지 않는다.  ★ 몸통도 주소도 ★ 건드리지 않는다.
★ 검산 — `S46-97`

사용   python3.11 tools/link_raw_ids.py           재기만 한다
      python3.11 tools/link_raw_ids.py --write   채운다
"""
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "carwatch.db")

SQL_FIND = (
    "SELECT r.site, COUNT(*) n FROM raw_response r"
    "  JOIN core_listing l ON l.site=r.site AND l.source_id=r.source_id"
    " WHERE r.listing_id IS NULL GROUP BY r.site ORDER BY n DESC"
)
SQL_FILL = (
    "UPDATE raw_response SET listing_id = ("
    "  SELECT l.listing_id FROM core_listing l"
    "   WHERE l.site=raw_response.site AND l.source_id=raw_response.source_id)"
    " WHERE listing_id IS NULL AND source_id IS NOT NULL AND source_id <> ''"
    "   AND EXISTS (SELECT 1 FROM core_listing l"
    "                WHERE l.site=raw_response.site"
    "                  AND l.source_id=raw_response.source_id)"
)


def main(write: bool) -> int:
    if not os.path.isfile(DB):
        print("carwatch.db 가 없다")
        return 1
    conn = sqlite3.connect(DB)
    try:
        rows = conn.execute(SQL_FIND).fetchall()
        total = sum(n for _, n in rows)
        print("★ source_id 로 이어지는데 listing_id 가 빈 원문")
        for site, n in rows:
            print(f"  {site:<16}{n:>8}")
        print(f"  {'합':<16}{total:>8}")
        if not write:
            print("  ★ --write 없이는 재기만 한다")
            return 0
        conn.execute(SQL_FILL)
        conn.commit()
        left = sum(n for _, n in conn.execute(SQL_FIND).fetchall())
        print(f"★ 채웠다 {total - left}건 · 남은 것 {left}건")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main("--write" in sys.argv))
