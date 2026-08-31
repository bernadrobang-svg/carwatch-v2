# -*- coding: utf-8 -*-
"""넣기 걸음 — ★ **파일 폴더를 읽어 `raw_response` ＋ `core_listing` 에 넣는다.**

지시서   `docs/ARCHITECTURE_20260830.md` 2장 · 마스터 지시 09-01
★★★ 마스터 — 「★ 받기 걸음은 ★ **파일만 쓴다.  ★ DB 를 안 연다** — 잠금이 아예 안 생긴다.
   ★ ★ **넣기 걸음은 그 폴더를 읽어 ★ `raw_response` ＋ `core_listing` 에 넣는다**」

★★ 곧 ★ **DB 를 여는 곳은 여기 하나다.**  ★ 통신은 하나도 안 한다 —
  ★ 그래서 ★ 한 번에 몰아 넣고 ★ 곧바로 끝난다.  ★ 잠금 창이 짧다

돌리는 법
    python3.11 tools/load_raw.py revolt            ★ 잰다
    python3.11 tools/load_raw.py revolt --write    ★ 넣는다
    python3.11 tools/load_raw.py revolt --write --day 2026-08-31
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from store.rawfile import read, walk  # noqa: E402

# ★ 사이트마다 ★ 「봉투 → 줄」을 내는 자리.  ★ 코드에 사이트 이름을 박지 않는다 —
#   ★ `parse/{site}/mapping.py` 가 정본이다
LOADERS = {
    "revolt": "parse.revolt.mapping",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _rows_from(site: str, env: dict, mod) -> tuple:
    """봉투 하나 → (core 줄들, 이력, 판).  ★ 목록이면 여러 줄이 나온다."""
    body = env.get("body")
    if not body:
        return [], None, None
    try:
        got = json.loads(body)
    except ValueError:
        return [], None, None
    if env.get("endpoint") == "list":
        items = got.get("results") if isinstance(got, dict) else got
        rows = [mod.parse_list_item(x) for x in (items or [])
                if isinstance(x, dict)]
        return [r for r in rows if r], None, None
    deep = mod.parse_detail(got, site, env.get("source_id"))
    rec = mod.record_of(got, site) if hasattr(mod, "record_of") else None
    pan = mod.panels_of(got) if hasattr(mod, "panels_of") else None
    return ([deep] if deep else []), rec, pan


def main() -> int:
    args = sys.argv[1:]
    site = next((a for a in args if not a.startswith("-")), None)
    if site not in LOADERS:
        print("쓰는 법 — python3.11 tools/load_raw.py "
              f"<{' | '.join(LOADERS)}> [--write] [--day YYYY-MM-DD]")
        return 2
    write = "--write" in args
    day = None
    if "--day" in args:
        i = args.index("--day")
        if i + 1 < len(args):
            day = args[i + 1]

    import importlib

    mod = importlib.import_module(LOADERS[site])
    files = walk(site=site, day=day, root=ROOT)
    print(f"★ {site} — 파일 {len(files):,}개"
          + ("" if write else "  ★ 재기만 한다"))
    got: Counter = Counter()
    if not write:
        for path in files:
            env = read(path)
            if env is None:
                got["못 읽음"] += 1
                continue
            rows, rec, pan = _rows_from(site, env, mod)
            got[env.get("endpoint") or "?"] += 1
            got["  줄"] += len(rows)
            if rec:
                got["  이력"] += 1
            if pan is not None:
                got["  판"] += 1
        for k, v in got.most_common():
            print(f"   {k:<20}{v:>7,}")
        return 0

    from parse.target_rules import fill_target_key
    from store.core import resolve_listing_id, split_pii, upsert_child, upsert_core
    from store.dictionary import known_model_of
    from store.pii import load_key
    from store.raw import commit, open_db, save_site_raw
    from store.raw import link_raws as raw_link_raws

    conn = open_db(os.path.join(ROOT, "carwatch.db"))
    at = _now()
    key = load_key()
    for path in files:
        env = read(path)
        if env is None:
            got["못 읽음"] += 1
            continue
        got[env.get("endpoint") or "?"] += 1
        # ★★ 원문을 ★ 먼저 남긴다 — ★ 파일이 원본이고 ★ 이것은 사본이다 (P3)
        save_site_raw(conn, site, env["endpoint"],
                      env.get("source_id"), env.get("url") or "",
                      env.get("body"), env.get("fetched_at") or at,
                      http_code=int(env.get("http_code") or 200))
        rows, rec, pan = _rows_from(site, env, mod)
        for row in rows:
            known = known_model_of((row.get("site_model") or "").split()[0]
                                   if row.get("site_model") else None)
            if known:
                row["site_model_group"] = known
            elif env.get("endpoint") == "list":
                # ★ 우리 차종이 아니다 — ★ **원문은 남고** ★ core 에만 안 넣는다
                got["  차종을 못 짚음"] += 1
                continue
            row["listing_id"] = resolve_listing_id(
                conn, site, row["source_id"], at)
            fill_target_key(site, row)
            upsert_core(conn, split_pii(conn, row, site, key, at), at)
            got["  넣음"] += 1
            if rec:
                rec["listing_id"] = row["listing_id"]
                rec["collected_at"] = at
                upsert_child(conn, "core_record", rec, "p1", at)
                got["  이력"] += 1
            if pan is not None:
                upsert_child(conn, "core_inspection", {
                    "listing_id": row["listing_id"], "site": site,
                    "row_status": "ok",
                    "inspection_panel_json": json.dumps(pan,
                                                        ensure_ascii=False),
                    "collected_at": at}, "p1", at)
                got["  판"] += 1
    commit(conn)
    raw_link_raws(conn, site)
    commit(conn)
    for k, v in got.most_common():
        print(f"   {k:<20}{v:>7,}")
    n = conn.execute("SELECT COUNT(*) FROM core_listing WHERE site=?",
                     (site,)).fetchone()[0]
    print(f"★ 저장된 {site} 매물 {n:,}건")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
