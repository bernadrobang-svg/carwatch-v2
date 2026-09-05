# -*- coding: utf-8 -*-
"""D5 ① — ★ **가이드 매핑표를 ★ `meta_field_usage` 에 넣는다** (지시 r1168 · `S46-282`).

★★★ 마스터 — 「★ 내가 ★ **사이트별로 매핑표를 만들고 ★ 그걸 파서가 보게 하라**고 했는데
   ★ 왜 안 되어 있지?」 · 「★ **표는 너가 만들어야지**」
★ 가이드가 ★ `tools/make_field_map.py` 로 ★ **표를 냈다** —
  ★ `outputs/field_map_{site}.json` 열둘 ＋ ★ 한 벌(`field_map_ALL.json` · **126줄**).
★★ **넣는 것은 개발측 몫**이다 (지시 D5 ①).

★ 실측 09-05 — ★ `meta_field_usage` 가 ★ **858줄인데 ★ 엔카가 850줄**이다.
  ★ ★ 나머지 넷이 ★ 8줄 · ★ **일곱 곳은 한 줄도 없다** —
  ★ ★ ★ `sync_registry()` 가 ★ **엔카 원문만** 훑기 때문이다.

★ 안 덮는다 — ★ 이미 있는 줄은 ★ **그대로 둔다** (마스터가 정하신 분류를 안 밀어낸다).
  ★ ★ `core_column` 만 비어 있으면 ★ 그 칸만 채운다

돌리는 법
    python3.11 tools/load_field_map.py            ★ 센다
    python3.11 tools/load_field_map.py --write    ★ 넣는다
"""
from __future__ import annotations

import glob
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# ★ 파서가 코드로 뽑는 칸은 ★ 「길」이 없다 — ★ 그 사실을 그대로 적는다
IN_CODE = "(코드에 박혀 있다)"
REASON = "가이드 매핑표 09-05 (field_map) — 파서 {code} · 식 {expr}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rows() -> list:
    """★ `outputs/field_map_{site}.json` 을 다 읽어 ★ 한 줄씩 낸다."""
    out = []
    for path in sorted(glob.glob(os.path.join(ROOT, "outputs",
                                              "field_map_*.json"))):
        if path.endswith("field_map_ALL.json"):
            continue          # ★ 한 벌은 사이트별의 합이다 — ★ 두 번 안 넣는다
        try:
            with open(path, encoding="utf-8") as f:
                got = json.load(f)
        except (OSError, ValueError):
            continue
        for one in (got.get("표") or []):
            if isinstance(one, dict) and one.get("site") and one.get(
                    "core_column"):
                out.append(one)
    return out


def main() -> int:
    write = "--write" in sys.argv
    got = rows()
    per: dict = {}
    for r in got:
        per[r["site"]] = per.get(r["site"], 0) + 1
    print(f"★ 매핑표 {len(got):,}줄 · 사이트 {len(per)}곳")
    for site, n in sorted(per.items(), key=lambda x: -x[1]):
        print(f"   {site:<18}{n:>4}")

    conn = sqlite3.connect(os.path.join(ROOT, "carwatch.db"), timeout=60)
    conn.execute("PRAGMA busy_timeout = 60000")
    before = dict(conn.execute(
        "SELECT site, COUNT(*) FROM meta_field_usage GROUP BY 1"))
    print(f"\n★ 지금 등록부 — {sum(before.values()):,}줄 "
          f"({', '.join(f'{k} {v:,}' for k, v in sorted(before.items(), key=lambda x: -x[1])[:4])})")
    if not write:
        print("★ `--write` 가 없다.  ★ 안 넣는다")
        return 0

    at = _now()
    added = filled = kept = 0
    for r in got:
        site = str(r["site"])
        col = str(r["core_column"])
        # ★ 길이 없으면 ★ 「코드에 박혀 있다」를 ★ 그대로 적는다 —
        #   ★ ★ 지어낸 길을 넣으면 ★ 뒤에 아무도 못 믿는다
        path = str(r.get("json_path") or IN_CODE)
        # ★★★★★ 09-05 — ★ **길이 없는 줄이 서로 겹친다.**
        #   ★ 열쇠가 ★ `(site, endpoint, json_path)` 인데
        #   ★ ★ 코드에 박힌 칸은 ★ 길이 다 ★ 「(코드에 박혀 있다)」로 같다 —
        #   ★ ★ ★ 그래서 ★ 한 사이트에 ★ **한 줄만** 남았다 [실측 09-05 — 126 → 68].
        #   ★ 칸 이름을 붙여 가른다 — ★ 지어낸 길이 아니라 ★ **「어느 칸의 코드인가」**다
        if path == IN_CODE:
            path = f"{IN_CODE} {col}"
        # ★ 창구를 모른다 — ★ 표가 안 준다.  ★ `-` 로 둔다 (「모른다」다)
        ep = str(r.get("endpoint") or "-")
        why = REASON.format(code=r.get("코드") or "?", expr=r.get("식") or "?")
        cur = conn.execute(
            "SELECT usage, core_column FROM meta_field_usage"
            " WHERE site=? AND endpoint=? AND json_path=?",
            (site, ep, path)).fetchone()
        if cur is None:
            conn.execute(
                "INSERT INTO meta_field_usage"
                "(site,endpoint,json_path,core_column,usage,reason,"
                " observed_hits,observed_total,miss_streak,first_seen,"
                " last_seen) VALUES (?,?,?,?,?,?,0,0,0,?,?)",
                (site, ep, path, col, "in_use", why, at, at))
            added += 1
        elif not (cur[1] or "").strip():
            # ★ 분류는 안 건드린다 — ★ 빈 `core_column` 만 채운다
            conn.execute(
                "UPDATE meta_field_usage SET core_column=?, last_seen=?"
                " WHERE site=? AND endpoint=? AND json_path=?",
                (col, at, site, ep, path))
            filled += 1
        else:
            kept += 1
        if (added + filled) % 50 == 0:
            conn.commit()
    conn.commit()
    print(f"\n★ 새로 넣은 줄 {added:,} · 빈 칸을 채운 것 {filled:,} · 그대로 둔 것 {kept:,}")
    after = dict(conn.execute(
        "SELECT site, COUNT(*) FROM meta_field_usage GROUP BY 1"))
    print(f"★ 등록부 {sum(before.values()):,} → {sum(after.values()):,}줄 ·"
          f" 사이트 {len(before)} → {len(after)}곳")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
