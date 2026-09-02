#!/usr/bin/env python3.11
"""★★★★★ 09-03 (2부 S6) — ★ **차량 키가 빈 매물을 채운다.**

★★★ 명령서 S6 — 「★ `vehicle_id` 가 ★ 11,917건(56.3%) 없다.
  ★ ★ `build_identities` 는 ★ 번호판·차대가 없어도 ★ `site_id` 로 키를 만든다 —
  ★ ★ ★ **돌기만 하면 NULL 이 안 남는다**」

★★ 왜 따로 도는가 — ★ 엔카는 ★ 판(`S6`)이 상세를 풀며 키를 붙인다.
  ★ ★ 그런데 ★ 열한 사이트는 ★ 저마다의 수집기가 ★ **목록만** 넣는다 (상세는 뒤에).
  ★ ★ ★ 그 사이 ★ 키가 비어 ★ 같은 차를 못 묶는다.
★ 키는 ★ **번호판 → 차대 → 사이트 ID** 차례다 (STEP 30) —
  ★ ★ 앞의 둘이 있으면 ★ 그것을 쓴다.  ★ 없을 때만 ★ 사이트 ID 다.
★★ `parsed_at` 은 ★ **안 건드린다** — ★ 그것은 「원문을 풀었다」는 뜻이다.
  ★ ★ 안 풀고 적으면 ★ 그것이 ★ 이 판이 막으려는 ★ 「선언과 실제의 괴리」다

쓰기   python3.11 tools/backfill_vehicle_id.py [--dry]
"""
from __future__ import annotations

import os
import sqlite3
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from store.core import build_identities, resolve_vehicle_id


def run(db: str, dry: bool = False) -> int:
    conn = sqlite3.connect(db)
    at = datetime.now(timezone.utc).isoformat()
    rows = conn.execute(
        "SELECT listing_id, site, source_id, plate_hash, vin_hash"
        "  FROM core_listing WHERE vehicle_id IS NULL").fetchall()
    print(f"★ 키가 빈 매물 {len(rows):,}건")
    by_kind: dict = {}
    done = 0
    for lid, site, sid, plate, vin in rows:
        # ★ `vin_hash` 는 ★ 이미 해시다 — ★ `build_identities` 는 ★ 날 것 `vin` 을
        #   ★ ★ 받아 스스로 해시한다.  ★ 그래서 ★ 여기서는 ★ **번호판과 사이트 ID** 만 준다.
        #   ★ ★ ★ 차대는 ★ 상세를 풀 때 ★ 판이 붙인다 — ★ 두 번 해시하지 않는다
        ident = build_identities(plate, None, None, f"{site}/{sid}")
        if not ident:
            continue
        if dry:
            by_kind[ident[0][0]] = by_kind.get(ident[0][0], 0) + 1
            done += 1
            continue
        vid, kind, _conf = resolve_vehicle_id(conn, ident, at)
        conn.execute("UPDATE core_listing SET vehicle_id=? WHERE listing_id=?",
                     (vid, lid))
        by_kind[kind] = by_kind.get(kind, 0) + 1
        done += 1
        if done % 2000 == 0:
            conn.commit()
            print(f"  {done:,}건", flush=True)
    if not dry:
        conn.commit()
    left = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE vehicle_id IS NULL").fetchone()[0]
    print(f"★ 붙인 것 {done:,}건 — " +
          " · ".join(f"{k} {v:,}" for k, v in sorted(by_kind.items())))
    print(f"★ 아직 빈 것 {left:,}건" + ("  (--dry 라 안 썼다)" if dry else ""))
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(run(os.path.join(ROOT, "carwatch.db"), "--dry" in sys.argv))
