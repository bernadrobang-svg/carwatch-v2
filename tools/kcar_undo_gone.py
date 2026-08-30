#!/usr/bin/env python3.11
"""★★★★★ 잘못 매긴 K카 `gone` 을 되돌린다 (마스터 0a · 08-30).

★★★ 마스터 — 「★ K카 152 → 6 — ★ **살아 있는 차를 죽였을 수 있다**」
★ 실측 08-30 — ★ 08-29 에 gone 으로 매긴 19건을 ★ **하나씩 눌러 봤다** —
  ★ ★ **12건이 아직 살아 있었다** · 7건만 정말 팔렸다.
★ 까닭 — ★ `stock_list` 가 ★ **전량이 아니다** (487건뿐 · 총계도 487).
  ★ ★ 살아 있는 12건은 ★ 그 창구에 아예 안 온다.

★★ 되돌리는 잣대 — ★ **짐작으로 안 되돌린다.  ★ 눌러서 살아 있는 것만** 되돌린다.
   ★ 상세가 `data.rvo.carCd` 를 주면 ★ 살아 있는 것이다 (규격 3-3 ①).
★ `gone_at` · `last_price_won` 을 지우고 ★ `status` 를 되돌린다.
★ 자취(`core_listing_change`)에 ★ 되돌린 것도 남긴다 — ★ 조용히 고치지 않는다

사용   python3.11 tools/kcar_undo_gone.py            재기만 한다
      python3.11 tools/kcar_undo_gone.py --write   되돌린다
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from adapters.kcar import SITE_CODE, KcarAdapter, load_config  # noqa: E402
from store.core import record_change  # noqa: E402
from store.raw import commit, connect_db  # noqa: E402

# ★ 이 날 매긴 것만 본다 — ★ 그 회차가 결함이었다.  ★ 앞의 것은 안 건드린다
BAD_DAY = "2026-08-29"
SLEEP_SEC = 0.8


def _now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def alive(adapter: KcarAdapter, source_id: str) -> bool | None:
    """★ 사이트에 아직 있나.  ★ 못 받으면 None — ★ 모르는 것은 안 건드린다."""
    req = adapter.detail_urls(source_id)[0]
    try:
        body = urllib.request.urlopen(
            urllib.request.Request(req.url, headers=req.headers),
            timeout=req.timeout_sec).read()
    except OSError:
        return None
    try:
        rvo = ((json.loads(body).get("data") or {}).get("rvo") or {})
    except ValueError:
        return None
    return bool(rvo.get("carCd"))


def main() -> int:
    write = "--write" in sys.argv
    adapter = KcarAdapter(load_config(ROOT))
    conn = connect_db(os.path.join(ROOT, "carwatch.db"))
    rows = conn.execute(
        "SELECT listing_id, source_id, status FROM core_listing"
        " WHERE site = ? AND substr(gone_at, 1, 10) = ?",
        (SITE_CODE, BAD_DAY)).fetchall()
    print(f"★ {BAD_DAY} 에 gone 으로 매긴 K카 {len(rows)}건을 눌러 본다")
    got = {"살아 있다": 0, "정말 팔렸다": 0, "못 받음": 0}
    at = _now()
    for lid, sid, _st in rows:
        ok = alive(adapter, sid)
        if ok is None:
            got["못 받음"] += 1
        elif ok:
            got["살아 있다"] += 1
            if write:
                # ★ 되돌린다 — ★ `status` 는 `active` 로.  ★ 차종이 없으면
                #   ★ 다음 재판정이 `out_of_scope` 로 다시 옮긴다 (그것이 맞다)
                conn.execute(
                    "UPDATE core_listing SET status='active', gone_at=NULL,"
                    " last_price_won=NULL WHERE listing_id=?", (lid,))
                # ★ `change_kind` 는 정해진 값만 받는다 (DDL CHECK) —
                #   ★ 죽었다가 되살아난 것이 ★ `relisted` 다.  ★ 새 갈래를 안 만든다
                record_change(conn, lid, "status", "gone", "active", at,
                              "relisted")
                commit(conn)
        else:
            got["정말 팔렸다"] += 1
        time.sleep(SLEEP_SEC)
    print("★ " + " · ".join(f"{k} {v}" for k, v in got.items()))
    print("★ 되돌렸다" if write else "★ --write 를 줘야 되돌린다 (지금은 재기만 했다)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
