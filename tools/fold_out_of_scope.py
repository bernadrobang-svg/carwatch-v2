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


def _split(conn) -> tuple:
    """★ 세 갈래로 가른다 (명령서 60-3 · `UI_REVIEW` 9a).

    ★★★ 08-26 — ★ 전에는 ★ `target_key IS NULL` 이면 ★ 다 접었다.  ★ 틀렸다.
      ★ ★ 실측 — ★ KB 의 ★ G80 130 · GLC 93 · X3 33 이 ★ 다 `target_key` 가 없다.
        ★ ★ 우리 차종인데 ★ 갈래(연료·트림)를 아직 못 붙인 것이다 —
        ★ ★ 그것을 접으면 ★ **마스터께서 보실 차가 사라진다**
      ★ ★ 그리고 ★ 상세를 못 받아 ★ 차명 자체가 없는 것은
        ★ ★ 「우리 차가 아니다」가 ★ **아니라** ★ 「아직 모른다」다.  ★ 접지 않는다

    돌려줌  (접을 것, 미분류, 모르는 것) — 각각 [(listing_id, site, 이름)]
    """
    from store.dictionary import known_model_of

    marks = ",".join("?" * len(FOLDABLE))
    fold, mine, unknown = [], [], []
    for lid, site, mg, sm in conn.execute(
        f"SELECT listing_id, site, site_model_group, site_model"
        f"  FROM core_listing"
        f" WHERE target_key IS NULL AND status IN ({marks})", FOLDABLE
    ):
        name = mg or sm
        if not name:
            # ★ 차명을 아직 못 읽었다 — ★ 상세를 못 받았거나 안 받았다
            unknown.append((lid, site, name))
        elif known_model_of(name):
            # ★ 우리 차종이다.  ★ 갈래만 못 붙었다 — ★ 「여쭐 것」이다
            mine.append((lid, site, name))
        else:
            fold.append((lid, site, name))
    return fold, mine, unknown


def main() -> int:
    dry = "--dry" in sys.argv
    conn = open_db(os.path.join(ROOT, "carwatch.db"))
    at = datetime.now(timezone.utc).isoformat()
    marks = ",".join("?" * len(FOLDABLE))

    before = dict(conn.execute(
        "SELECT status, COUNT(*) FROM core_listing GROUP BY 1"))
    fold, mine, unknown = _split(conn)

    def _by_site(rows):
        got: dict = {}
        for _lid, site, _n in rows:
            got[site] = got.get(site, 0) + 1
        return sorted(got.items(), key=lambda kv: -kv[1])

    print(f"★ 접을 것 — ★ 우리 차종이 아닌 것 {len(fold):,}건")
    for site, n in _by_site(fold):
        print(f"   {site:<16} {n:>6}")
    print(f"★ 안 접는다 — ★ 우리 차종인데 갈래만 못 붙은 것 {len(mine):,}건 "
          f"(★ 여쭐 것이다)")
    for site, n in _by_site(mine):
        print(f"   {site:<16} {n:>6}")
    print(f"★ 안 접는다 — ★ 차명을 아직 못 읽은 것 {len(unknown):,}건 "
          f"(★ 상세를 못 받았다.  ★ 「우리 차가 아니다」가 아니다)")
    for site, n in _by_site(unknown):
        print(f"   {site:<16} {n:>6}")

    # ★ 갈래가 붙었는데 아직 new 인 것은 ★ 접는 것이 아니라 ★ 판정으로 보낸다
    wake = conn.execute(
        f"SELECT COUNT(*) FROM core_listing"
        f" WHERE target_key IS NOT NULL AND status IN ({marks})",
        FOLDABLE).fetchone()[0]
    print(f"★ 갈래가 붙었는데 아직 {'·'.join(FOLDABLE)} 인 것 {wake:,}건 — "
          f"★ active 로 올린다")

    # ★★ 되돌리기 — ★ 옛 규칙으로 잘못 접은 것을 ★ `new` 로 돌린다 (`--repair`).
    #   ★ 차명이 없는데 접힌 것이 ★ 그것이다 — ★ 상세를 다시 받으면 채워진다
    repair = conn.execute(
        "SELECT COUNT(*) FROM core_listing"
        " WHERE status='out_of_scope' AND site_model IS NULL"
        "   AND site_model_group IS NULL AND target_key IS NULL").fetchone()[0]
    want_repair = "--repair" in sys.argv
    print(f"★ 잘못 접힌 것 {repair:,}건 — 차명이 없는데 접혀 있다"
          + ("  ★ --repair 로 되돌린다" if want_repair else
             "  ★ 되돌리려면 --repair"))

    if dry:
        print("★ --dry 라 바꾸지 않았다")
        return 0

    if fold:
        conn.executemany(
            "UPDATE core_listing SET status='out_of_scope', last_seen=?"
            " WHERE listing_id=?", [(at, lid) for lid, _s, _n in fold])
    conn.execute(
        f"UPDATE core_listing SET status='active', last_seen=?"
        f" WHERE target_key IS NOT NULL AND status IN ({marks})",
        (at, *FOLDABLE))
    if want_repair:
        conn.execute(
            "UPDATE core_listing SET status='new', last_seen=?"
            " WHERE status='out_of_scope' AND site_model IS NULL"
            "   AND site_model_group IS NULL AND target_key IS NULL", (at,))
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
