# -*- coding: utf-8 -*-
"""이미 들어온 것을 ★ 되돌린다 — ★ 우리 대상이 아닌 것은 ★ 접는다 (명령서 3-3).

쓰기   python3.11 tools/fold_out_of_scope.py --dry     세기만
      python3.11 tools/fold_out_of_scope.py           접는다

★★ **지우지 않는다.**  ★ 「접는다」는 ★ 지우는 것이 아니다 (마스터 확정).
   ★ `status='out_of_scope'` 로 표시만 한다 — ★ 갈래를 넓히면 ★ 되살아난다
★ `raw_response` 는 ★ 손대지 않는다 — ★ 원문은 무손실이다 (P3)
★★ 갈래를 정하는 규칙은 ★ `parse/classify.py` 하나다 — ★ 여기서 다시 정하지 않는다
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from store.raw import commit, open_db          # noqa: E402

# ★ 접을 수 있는 상태 — ★ `active` 는 ★ `S9` 가 정한 것이라 안 건드린다.
#   ★ `gone` 은 ★ 팔린 것이다 — ★ 덮으면 「얼마에 팔렸나」가 사라진다
FOLDABLE = ("new",)


def main() -> int:
    dry = "--dry" in sys.argv
    conn = open_db(os.path.join(ROOT, "carwatch.db"))
    at = datetime.now(timezone.utc).isoformat()
    marks = ",".join("?" * len(FOLDABLE))

    before = dict(conn.execute(
        "SELECT status, COUNT(*) FROM core_listing GROUP BY 1"))
    rows = conn.execute(
        f"SELECT site, COUNT(*) FROM core_listing"
        f" WHERE target_key IS NULL AND status IN ({marks})"
        f" GROUP BY 1 ORDER BY 2 DESC", FOLDABLE).fetchall()
    total = sum(n for _s, n in rows)
    print(f"★ 접을 것 — 갈래가 안 붙고 상태가 {'·'.join(FOLDABLE)} 인 것 {total:,}건")
    for site, n in rows:
        print(f"   {site:<16} {n:>6}")

    # ★ 갈래가 붙었는데 아직 new 인 것은 ★ 접는 것이 아니라 ★ 판정으로 보낸다
    wake = conn.execute(
        f"SELECT COUNT(*) FROM core_listing"
        f" WHERE target_key IS NOT NULL AND status IN ({marks})",
        FOLDABLE).fetchone()[0]
    print(f"★ 갈래가 붙었는데 아직 {'·'.join(FOLDABLE)} 인 것 {wake:,}건 — ★ active 로 올린다")

    if dry:
        print("★ --dry 라 바꾸지 않았다")
        return 0

    conn.execute(
        f"UPDATE core_listing SET status='out_of_scope', last_seen=?"
        f" WHERE target_key IS NULL AND status IN ({marks})", (at, *FOLDABLE))
    conn.execute(
        f"UPDATE core_listing SET status='active', last_seen=?"
        f" WHERE target_key IS NOT NULL AND status IN ({marks})",
        (at, *FOLDABLE))
    commit(conn)

    after = dict(conn.execute(
        "SELECT status, COUNT(*) FROM core_listing GROUP BY 1"))
    print("\n★ 상태 — 전 → 후")
    for key in sorted(set(before) | set(after)):
        print(f"   {key:<14} {before.get(key, 0):>6} → {after.get(key, 0):>6}")
    print("\n★ 지우지 않았다 — ★ 접었을 뿐이다.  ★ 갈래를 넓히면 되살아난다")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
