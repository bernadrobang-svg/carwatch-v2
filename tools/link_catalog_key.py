# -*- coding: utf-8 -*-
"""★★★★★ 08-31 (로드맵 차례 2) — ★ `model_catalog_key` 를 아홉 사이트에 잇는다.

★★★ 먼저 잰 것 — ★ `model_catalog_key` 는 ★ **엔카의 카탈로그 ID** 다
  (`8174400202106211031` — ★ 모델코드＋날짜＋트림코드).
  ★ ★ 곧 ★ 「`target_key`＋`year`＋`trim`」은 ★ **값이 아니라 ★ 맞대기 열쇠**다.
  ★ ★ 우리 손으로 문자열을 지어 넣으면 ★ 표를 하나도 못 짚는다 (127가지와 안 맞는다)

★★ 그래서 ★ 엔카 매물이 이미 붙여 둔 것에서 ★ 표를 만든다 —
      (target_key, form_year, trim_badge) → model_catalog_key
  ★ ★ 트림 글자가 사이트마다 달라 ★ 셋으로는 ★ **60건**만 맞는다 [실측 08-31].
  ★ ★ 둘(차종·연식)로 넓히면 ★ 766건이 맞지만 ★ 트림이 섞인다 —
    ★ ★ ★ 그래서 ★ **그 짝에 카탈로그 열쇠가 하나뿐일 때만** 넓힌다.
    ★ ★ ★ 여럿이면 ★ **안 잇는다** — ★ 0점＋미확인이 맞다 (`f-table` 「매칭 안 되면 0점」)

돌리는 법
    python3.11 tools/link_catalog_key.py          ★ 잰다
    python3.11 tools/link_catalog_key.py --write  ★ 넣는다
"""
from __future__ import annotations

import os
import sqlite3
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def tables(conn):
    """엔카가 붙인 것에서 ★ 열쇠 표 둘을 만든다."""
    three: dict = {}
    two: dict = defaultdict(set)
    for tk, yr, tr, key in conn.execute(
        "SELECT target_key, form_year, trim_badge, model_catalog_key"
        "  FROM core_listing WHERE site='encar'"
        "   AND model_catalog_key IS NOT NULL AND target_key IS NOT NULL"
        "   AND form_year IS NOT NULL GROUP BY 1,2,3,4"
    ):
        if tr is not None:
            three.setdefault((tk, yr, tr), key)
        two[(tk, yr)].add(key)
    return three, two


def main() -> int:
    write = "--write" in sys.argv[1:]
    conn = sqlite3.connect(os.path.join(ROOT, "carwatch.db"), timeout=60)
    conn.execute("PRAGMA busy_timeout = 60000")
    three, two = tables(conn)
    have = {r[0] for r in conn.execute(
        "SELECT DISTINCT model_catalog_key FROM dict_model_option")}
    print(f"★ 엔카 열쇠 — 셋 {len(three):,}가지 · 둘 {len(two):,}가지"
          f" · 옵션표가 아는 것 {len(have)}가지")
    got: Counter = defaultdict(Counter)
    rows = list(conn.execute(
        "SELECT listing_id, site, target_key, form_year, trim_badge"
        "  FROM core_listing WHERE site <> 'encar'"
        "   AND status IN ('active','new') AND model_catalog_key IS NULL"))
    for lid, site, tk, yr, tr in rows:
        key = three.get((tk, yr, tr))
        why = "셋이 다 같다"
        if key is None:
            cand = two.get((tk, yr)) or set()
            if len(cand) == 1:
                key = next(iter(cand))
                why = "차종·연식이 같고 카탈로그가 하나뿐이다"
            elif len(cand) > 1:
                got[site]["★ 카탈로그가 여럿이라 안 이었다"] += 1
                continue
            else:
                got[site]["★ 엔카에 같은 차종·연식이 없다"] += 1
                continue
        got[site][f"이었다 ({why})"] += 1
        if key in have:
            got[site]["  옵션표까지 닿는다"] += 1
        if write:
            conn.execute("UPDATE core_listing SET model_catalog_key=?"
                         " WHERE listing_id=?", (key, lid))
    if write:
        conn.commit()
    print(f"\n{'사이트':<16}{'대상':>6}   갈래")
    for site in sorted(got, key=lambda s: -sum(got[s].values())):
        print(f"{site:<16}{sum(got[site].values()):>6,}")
        for k, v in got[site].most_common():
            print(f"     {k:<38}{v:>6,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
