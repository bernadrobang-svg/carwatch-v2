# -*- coding: utf-8 -*-
"""★ 잘못 내린 `out_of_scope` 를 되돌린다 (09-04 · `tools/undo_wrong_gone.py` 와 같은 꼴).

★★★ 무엇이 잘못됐나 — ★ `tools/sync_target_map.py --apply` 의 else 줄이
  ★ ★ `target_key` 가 **있는** 행까지 ★ `out_of_scope` 로 내렸다.
  ★ ★ ★ `out_of_scope` 는 ★ 「**우리 차종이 아니다**」라는 뜻이다 —
    ★ ★ ★ ★ 우리 열쇠가 붙은 행이 ★ 그것일 수 없다.  ★ **모순**이다.
★ 실측 09-04 — ★ 그런 행이 ★ **4,122건** (스포티지 682 · GLC 573 · 그랜저 512 ·
  ★ G80 407 · X3 354 · 모델Y 268 · Q5 218 · G70 175 · XC60 145 · XC40 112 …).
★★ 잣대 — ★ `status='out_of_scope'` 이고 ★ `target_key` 가 있고
  ★ ★ **`result_score` 가 있는 것**만 되돌린다.
  ★ ★ ★ 점수가 있다는 것은 ★ 전에 ★ `active` 였다는 뜻이다 (S10 은 `active` 만 매긴다).
  ★ 점수가 없는 것은 ★ **안 건드린다** — ★ 짐작으로 살리지 않는다
★ `core_listing_change` 에 ★ 자취를 남긴다 — ★ 조용히 안 고친다

돌리는 법
    python3.11 tools/undo_wrong_out_of_scope.py            ★ 센다
    python3.11 tools/undo_wrong_out_of_scope.py --write    ★ 되돌린다
"""
from __future__ import annotations

import os
import sqlite3
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from store.core import record_change  # noqa: E402

CAUSE = "sync_target_map --apply 가 차종 붙은 행을 out_of_scope 로 내렸다 (09-04)"
PICK = """
  SELECT l.listing_id, l.target_key FROM core_listing l
    JOIN result_score s ON s.listing_id = l.listing_id
   WHERE l.status = 'out_of_scope' AND l.target_key IS NOT NULL
"""


def main() -> int:
    write = "--write" in sys.argv
    conn = sqlite3.connect(os.path.join(ROOT, "carwatch.db"), timeout=60)
    conn.execute("PRAGMA busy_timeout = 60000")
    at = datetime.now(timezone.utc).isoformat()
    rows = conn.execute(PICK).fetchall()
    print(f"★ 되돌릴 것 {len(rows):,}건 — ★ 차종이 붙었는데 out_of_scope 이고"
          " ★ 점수가 있는 행")
    per: dict = {}
    for _lid, tk in rows:
        per[tk] = per.get(tk, 0) + 1
    for tk, n in sorted(per.items(), key=lambda x: -x[1])[:10]:
        print(f"   {tk:<18}{n:>6,}")
    if not write:
        print("★ `--write` 가 없다.  ★ 안 고친다")
        return 0
    for lid, _tk in rows:
        conn.execute("UPDATE core_listing SET status='active'"
                     " WHERE listing_id=?", (lid,))
        record_change(conn, lid, "status", "out_of_scope", "active", at,
                      "status", cause=CAUSE)
    conn.commit()
    left = conn.execute(
        "SELECT COUNT(*) FROM core_listing"
        " WHERE status='out_of_scope' AND target_key IS NOT NULL").fetchone()[0]
    print(f"★ 되돌렸다 {len(rows):,}건 (active) ·"
          f" ★ 아직 남은 「차종 붙은 out_of_scope」 {left:,}건 (점수가 없어 안 건드렸다)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
