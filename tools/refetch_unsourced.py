#!/usr/bin/env python3.11
"""★★★★★ 찌꺼기를 끊고 ★ 근거 없는 행의 상세를 다시 받는다 (마스터 0e · 08-30).

★★★ 마스터 확정 08-30 —
  ① `raw_response.listing_id` → NULL (2,406건).  ★ **원문 줄은 지우지 마라** (P3)
  ② 969건의 `detail_status` 를 비운다.  ★ `status` 는 `active` 그대로 — 목록에서 빼지 마라
  ③ 다시 받는다 — 사이트마다 끊어서
  ★ **`core_listing` 행을 지우지 마라.** ★ 969건에 살아 있는 차가 섞여 있다

★★ 뿌리 (0d 실측) — ★ 엔카 원문 2,406건이 ★ **남의 매물에 붙어 있었다.**
  ★ 08-24~25 에만 생겼고 ★ `_scope` 가 08-27 에 고쳐져 ★ 그 뒤로는 0건이다.
  ★ 그 원문의 `source_id` 는 ★ 엔카에 매물이 없다 (0/2,406) —
  ★ ★ 어디에도 옳게 못 붙인다.  ★ 그래서 ★ **끊는다** (원문은 남는다)

★★ 「살아 있음」의 잣대 — ★ **200 으로 안 가른다** (마스터 지시).
  ★ K카는 ★ 71,282B ↔ 3,186B 다.  ★ 그 사이트 파서가 값을 뽑는가로 가른다 —
  ★ ★ `tools/undo_wrong_gone.probe()` 가 이미 사이트마다 그것을 안다.  ★ 같이 쓴다

★ 받은 뒤 셋으로 —
  살아 있다 / `detail_gone` / ★ 잇달아 사흘이면 `unreachable`

사용   python3.11 tools/refetch_unsourced.py [사이트…]           재기만 한다
      python3.11 tools/refetch_unsourced.py [사이트…] --write   끊고 · 비우고 · 다시 받는다
      python3.11 tools/refetch_unsourced.py --cut-only --write   ①②만 (받지 않는다)
"""
from __future__ import annotations

import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from store.core import record_change  # noqa: E402
from store.raw import commit, connect_db  # noqa: E402
from tools.undo_wrong_gone import probe  # noqa: E402

SLEEP_SEC = 0.85
# ★ 잇달아 이만큼 못 받으면 ★ `unreachable` 이다 (마스터 확정)
UNREACHABLE_DAYS = 3


def _now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def cut_wrong_links(conn, write: bool) -> int:
    """① 남의 매물을 가리키는 `listing_id` 를 끊는다.  ★ 원문 줄은 안 지운다."""
    rows = conn.execute(
        "SELECT r.id FROM raw_response r"
        "  JOIN core_listing l ON l.listing_id = r.listing_id"
        " WHERE r.site <> l.site").fetchall()
    if write and rows:
        conn.executemany("UPDATE raw_response SET listing_id=NULL WHERE id=?",
                         [(r[0],) for r in rows])
        commit(conn)
    return len(rows)


def unsourced(conn) -> list:
    """② 상세 원문이 없는데 `detail_status='ok'` 인 행.

    ★ 열쇠는 ★ `(site, source_id)` 다 — ★ `listing_id` 로 재면 틀린다 (0d 에서 배웠다)
    """
    have = {(r[0], r[1]) for r in conn.execute(
        "SELECT DISTINCT site, source_id FROM raw_response"
        " WHERE endpoint='detail' AND source_id IS NOT NULL")}
    # ★★★★ 08-30 — ★ `detail_status='ok'` 만 보면 ★ **한 번 비운 뒤 못 찾는다.**
    #   ★ ①②를 돌리면 ★ 그 969건은 ★ `detail_status` 가 NULL 이 된다 —
    #   ★ ★ 그러면 이 함수가 ★ 0건을 내고 ★ ③이 아무것도 안 받는다.
    #   ★ 그래서 ★ **「상세 원문이 없는데 목록에는 사는 것」**으로 본다 —
    #   ★ ★ `out_of_scope`(대상 아님)와 ★ `not_requested`(아직 안 부름)는 뺀다
    return [r for r in conn.execute(
        "SELECT listing_id, site, source_id, status FROM core_listing"
        " WHERE site <> 'encar'"
        "   AND status IN ('active','new','gone')"
        "   AND (detail_status IS NULL OR detail_status='ok')")
        if (r[1], r[2]) not in have]


def main() -> int:
    write = "--write" in sys.argv
    cut_only = "--cut-only" in sys.argv
    want = [a for a in sys.argv[1:] if not a.startswith("-")]
    conn = connect_db(os.path.join(ROOT, "carwatch.db"))
    at = _now()

    n_cut = cut_wrong_links(conn, write)
    print(f"① 남의 매물을 가리키던 원문 {n_cut:,}건"
          + (" — ★ 끊었다 (원문 줄은 그대로)" if write else " (재기만 했다)"))

    rows = unsourced(conn)
    if want:
        rows = [r for r in rows if r[1] in want]
    print(f"② 근거 없는 행 {len(rows):,}건")
    if write:
        for lid, _s, _sid, _st in rows:
            # ★ `status` 는 안 건드린다 — ★ 목록에서 빼지 않는다 (마스터 지시)
            conn.execute("UPDATE core_listing SET detail_status=NULL"
                         " WHERE listing_id=?", (lid,))
        commit(conn)
        print("   ★ detail_status 를 비웠다 (status 는 그대로)")
    if cut_only or not write:
        print("★ --write 없이 · 또는 --cut-only 라 안 받았다")
        return 0

    print(f"③ 다시 받는다 — {len(rows):,}건 · 사이트마다 끊어서")
    got = {"살아 있다": 0, "detail_gone(not_found)": 0, "unreachable": 0}
    per: dict = {}
    for lid, site, sid, _st in rows:
        ok = probe(site, sid)
        per.setdefault(site,
                       {"살아 있다": 0, "detail_gone(not_found)": 0,
                        "unreachable": 0})
        if ok is True:
            key = "살아 있다"
            conn.execute("UPDATE core_listing SET detail_status='ok'"
                         " WHERE listing_id=?", (lid,))
        elif ok is False:
            # ★★★★ 08-30 — ★ `detail_status` 는 ★ 정해진 다섯만 받는다 (DDL CHECK) —
            #   ★ `ok` · `empty` · `not_found` · `error` · `not_requested`.
            #   ★ 마스터께서 말씀하신 「detail_gone」이 ★ 그 다섯에 없다.
            #   ★★ **새 이름을 만들지 않는다** (규칙 2) — ★ 뜻이 같은 `not_found` 를 쓴다.
            #   ★ ★ 사이트가 「없다」고 답한 것이 ★ 곧 `not_found` 다
            key = "detail_gone(not_found)"
            conn.execute("UPDATE core_listing SET detail_status='not_found'"
                         " WHERE listing_id=?", (lid,))
            record_change(conn, lid, "detail_status", "ok", "not_found", at,
                          "status")
        else:
            # ★ 못 받았다 — ★ 「없다」로 안 적는다.  ★ 다음 바퀴가 다시 본다.
            #   ★ 잇달아 사흘이면 ★ `unreachable` 이다 (마스터 확정)
            key = "unreachable"
        got[key] += 1
        per[site][key] += 1
        commit(conn)
        time.sleep(SLEEP_SEC)
    for site, k in sorted(per.items()):
        print(f"   {site:16s} " + " · ".join(f"{a} {b}" for a, b in k.items()))
    print("★ 합계 — " + " · ".join(f"{k} {v}" for k, v in got.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
