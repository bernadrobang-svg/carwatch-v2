# -*- coding: utf-8 -*-
"""★★★★★ 08-30 (명령서 r974 · 0j 4) — ★ Ⓐ 「이미 오는 것을 읽는다」.

★★★ ★ 사이트를 ★ **한 번도 안 두드린다.**  ★ 저장해 둔 원문을 ★ 다시 읽을 뿐이다.
  ★ ★ 파서가 늘어났으므로 ★ 옛 원문에서 ★ 이제야 나오는 칸이 있다 —
  ★ ★ 그것이 ★ 헤이딜러 183점이다 (사고·자차·소유자·용도·특수·보증)

돌리는 법
    python3.11 tools/backfill_from_raw.py heydealer          ★ 잰다 (안 고친다)
    python3.11 tools/backfill_from_raw.py heydealer --write  ★ 넣는다
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from errors import ValidationError  # noqa: E402
from store.raw import raw_body  # noqa: E402


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def latest_details(conn, site: str) -> list:
    """매물마다 ★ 마지막 상세 원문 한 통.  ★ 없는 것은 안 낸다."""
    return list(conn.execute(
        "SELECT listing_id, source_id, body FROM ("
        " SELECT listing_id, source_id, body,"
        "        ROW_NUMBER() OVER (PARTITION BY listing_id"
        "                           ORDER BY fetched_at DESC, id DESC) n"
        "   FROM raw_response"
        "  WHERE site=? AND endpoint='detail' AND listing_id IS NOT NULL"
        ") WHERE n=1", (site,)))


def heydealer(conn, write: bool) -> Counter:
    from parse.heydealer.mapping import part_enums, record_of, warranty_of
    from store.core import upsert_child
    from store.dictionary import upsert_enum

    at = _now()
    got: Counter = Counter()
    for lid, _sid, blob in latest_details(conn, "heydealer"):
        try:
            body = json.loads(raw_body(blob))
        except (ValueError, TypeError):
            got["못 읽음"] += 1
            continue
        if not isinstance(body, dict) or not body.get("detail_info"):
            got["알맹이 없음"] += 1
            continue
        rec = record_of(body, "heydealer")
        war = warranty_of(body)
        parts = part_enums(body)
        if rec:
            got["이력"] += 1
            for k in ("accident_my_cnt", "accident_my_cost", "owner_change_cnt",
                      "use_gov", "use_business", "total_loss_cnt"):
                if rec.get(k) is not None:
                    got[f"  {k}"] += 1
            if rec.get("use_cd"):
                got["  ★ 렌트 (용도 축 안 엶)"] += 1
        if war:
            got["보증"] += 1
        got["부위"] += len(parts)
        if not write:
            continue
        if rec:
            rec["listing_id"] = lid
            rec["collected_at"] = at
            upsert_child(conn, "core_record", rec, "p1", at)
        if war:
            keys = list(war)
            conn.execute(
                "UPDATE core_listing SET "
                + ", ".join(f"{k}=?" for k in keys)
                + " WHERE listing_id=?", [war[k] for k in keys] + [lid])
        for one in parts:
            # ★★★ 08-30 — ★ `part` 축은 ★ **정책 표(STEP 41)에 행이 없다.**
            #   ★ 실측 — `ValidationError: 축 정책 미정의: part`.
            #   ★★ 규격 `HEYDEALER_API.md` 3a ② 는 ★ 「`dict_enum(axis='part')` 에
            #     ★ 넣으라」 하는데 ★ STEP 41 표에 ★ `part` 가 없다 — ★ 규격끼리 어긋난다.
            #   ★★ 내가 표에 행을 더하지 않는다 (규칙 2) — ★ 마스터께 올린다.
            #   ★ ★ 그때까지 ★ 값은 ★ 원문에 그대로 남아 있다 (P3) — ★ 잃지 않는다
            try:
                upsert_enum(conn, "heydealer", "part", one["part"],
                            one["part"], 1, "detail", "d1", at,
                            force_pending=True)
            except ValidationError:
                got["  ★ part 축 정책이 없다 (STEP 41)"] += 1
                break
    if write:
        conn.commit()
    return got


SITES = {"heydealer": heydealer}


def main() -> int:
    args = sys.argv[1:]
    site = next((a for a in args if not a.startswith("-")), None)
    if site not in SITES:
        print("쓰는 법 — python3.11 tools/backfill_from_raw.py "
              f"<{' | '.join(SITES)}> [--write]")
        return 2
    write = "--write" in args
    conn = sqlite3.connect(os.path.join(ROOT, "carwatch.db"), timeout=60)
    conn.execute("PRAGMA busy_timeout = 60000")
    print(f"★ {site} — 저장된 상세 원문을 다시 읽는다 "
          f"({'넣는다' if write else '★ 재기만 한다'})")
    got = SITES[site](conn, write)
    for k, v in got.items():
        print(f"   {k:<28} {v:>6,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
