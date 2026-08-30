#!/usr/bin/env python3.11
"""★★★★★ 회차마다 낼 세 수 — ★ **화면 기준**으로 센다 (마스터 지시 08-30).

★★★ 마스터 — 「★ **잣대는 마스터가 보시는 화면 기준이어야 한다**」

★★ 08-30 실측 — ★ 내가 손으로 짠 SQL 이 ★ 화면과 달랐다 —
   ★ ③ 전기차 A 이상 — ★ 내 수 **195** · ★ 화면 **13**
     ★ 까닭 — ★ `fuel_raw LIKE '%전기%'` 가 ★ **「가솔린+전기」 122건**을 잡았다.
       ★ ★ 그것은 하이브리드다.  ★ 화면은 `fuel_raw IN (…)` 로 정확한 낱말만 본다.
       ★ ★ 거기에 `target_key LIKE '%_EV%'` 를 또 더해 부풀렸다.
   ★ ② 같은 차 짝 — ★ 내 수 **275** · ★ 화면 **245**
     ★ 까닭 — ★ `plate_hash` 묶음을 셌다.  ★ 화면은 거르개를 거친 뒤를 센다

★★ 그래서 ★ **`_listings_where()` 를 그대로 부른다.**
   ★ 손으로 조건을 짜지 않는다 — ★ 화면이 바뀌면 이 수도 함께 바뀐다

사용   python3.11 tools/three_numbers.py
"""
from __future__ import annotations

import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from report.screens.build import _listings_where, view_track  # noqa: E402
from report.screens.views import ListingFilter  # noqa: E402

JOIN = ("FROM core_listing l"
        " LEFT JOIN result_score s ON s.listing_id = l.listing_id WHERE ")
NINE = ("bobaedream", "heydealer", "hyundai_cert", "kbchachacha", "kcar",
        "reborncar", "volvo_selekt", "bmw_bps", "lexus_certified", "kia_cpo")


def screen(conn, **kw) -> int:
    """★ 화면이 거르는 조건 그대로 센다."""
    parts, args = _listings_where(ListingFilter(**kw))
    return conn.execute(
        f"SELECT COUNT(*) {JOIN}{' AND '.join(parts)}", args).fetchone()[0]


def main() -> int:
    conn = sqlite3.connect(
        f"file:{os.path.join(ROOT, 'carwatch.db')}?mode=ro", uri=True)
    conn.execute("PRAGMA busy_timeout = 60000")

    one = sum(screen(conn, site=s, min_grade="A") for s in NINE)
    three = screen(conn, fuel="electric", min_grade="A")

    # ★★ ② 같은 차 짝 — ★ 08-30 (마스터 r956) — ★ `/track` 의
    #   ★ 「짝지어진 차 N대」 ★ **그 수**다.  ★ **대**이지 매물이 아니다.
    #   ★ 전에 나는 ★ 「짝에 든 매물」을 세어 ★ 두 배 가까이 냈다.
    #   ★ 손으로 SQL 을 짜지 않는다 — ★ 화면을 그대로 부른다
    cv = conn.execute("SELECT MAX(calc_version) FROM result_score").fetchone()[0]
    two = view_track(None, conn, cv).total_pairs

    print("★ 회차마다 낼 세 수 (화면 기준)")
    print(f"  ① 아홉 사이트 A 이상   {one:6,d}건")
    print(f"  ② 같은 차 짝          {two:6,d}건")
    print(f"  ③ 전기차 A 이상       {three:6,d}건")
    print(f"     (참고 — 화면 전체 {screen(conn):,}건 · "
          f"전기만 {screen(conn, fuel='electric'):,}건)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
