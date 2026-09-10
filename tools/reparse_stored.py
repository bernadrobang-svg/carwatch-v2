# -*- coding: utf-8 -*-
"""이미 가진 원문을 ★ 다시 읽어 ★ `core_listing` 칸에 넣는다 (N-2 · G).

★★ `tools/parse_stored_encar.py` 는 ★ 엔카 전용이고 ★ **JSON 만** 읽는다.
  ★ 그런데 열두 곳 중 여럿은 ★ 원문이 **HTML** 이다 (리본카 · 볼보 · BMW · 보배 …).
  ★ ★ 그 사이트의 `parse_detail` 은 ★ 글자를 그대로 받는다 — ★ 이 자는 둘 다 한다.
★ 다시 받지 않는다.  ★ 파일이 정본이다 (`S46-185`).
★ 파서가 안 준 칸은 ★ **안 건드린다** — ★ 있던 값을 「없음」으로 덮지 않는다 (금지 12).

돌리는 법
    python3.11 tools/reparse_stored.py heydealer kia_cpo           ★ 잰다
    python3.11 tools/reparse_stored.py heydealer kia_cpo --write   ★ 넣는다
"""
from __future__ import annotations

import importlib
import json
import os
import sqlite3
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from store.rawfile import read, walk          # noqa: E402


def _body(env: dict):
    """원문 → ★ 파서가 받는 꼴.  ★ JSON 이면 풀고 ★ 아니면 글자 그대로."""
    body = env.get("body")
    if body is None:
        return None
    if isinstance(body, bytes):
        body = body.decode("utf-8", "replace")
    said = body.lstrip()[:1]
    if said in ("{", "["):
        try:
            return json.loads(body)
        except ValueError:
            return body
    return body


def _call(fn, raw, site: str, sid: str):
    """파서를 ★ 그 파서가 받는 꼴로 부른다."""
    import inspect

    names = list(inspect.signature(fn).parameters)
    if len(names) >= 2 and names[1] in ("site", "site_code"):
        return fn(raw, site, sid)
    if len(names) >= 2:
        return fn(raw, sid)
    return fn(raw)


def run(sites: list, write: bool = False, db: str = "carwatch.db") -> Counter:
    conn = sqlite3.connect(os.path.join(ROOT, db))
    cols = {r[1] for r in conn.execute("PRAGMA table_info(core_listing)")}
    tally: Counter = Counter()
    for site in sites:
        try:
            mod = importlib.import_module(f"parse.{site}.mapping")
        except ImportError:
            tally[f"{site} 파서가 없다"] += 1
            continue
        fn = getattr(mod, "parse_detail", None)
        if fn is None:
            tally[f"{site} parse_detail 이 없다"] += 1
            continue
        have = {str(r[0]) for r in conn.execute(
            "SELECT source_id FROM core_listing WHERE site = ?", (site,))}
        seen: set = set()
        # ★ 새 파일이 먼저다 — ★ 같은 매물을 여러 날 받았으면 ★ 마지막 것을 쓴다
        for path in sorted(walk(site=site, endpoint="detail", root=ROOT),
                           reverse=True):
            env = read(path) or {}
            sid = str(env.get("source_id")
                      or os.path.basename(path)[:-5] or "")
            if not sid or sid in seen or sid not in have:
                continue
            seen.add(sid)
            raw = _body(env)
            if raw is None:
                continue
            # ★ 파서마다 ★ 받는 것이 다르다 — ★ BMW 는 `(html, source_id)` 둘이다.
            #   ★ 규격을 하나로 맞추는 것은 ★ 이 자의 몫이 아니다 —
            #     ★ ★ 여기서는 ★ **있는 대로 부른다** (규칙 2)
            try:
                got = _call(fn, raw, site, sid)
            except (ValueError, TypeError, AttributeError, KeyError):
                tally[f"{site} 못 읽음"] += 1
                continue
            if not isinstance(got, dict) or not got:
                tally[f"{site} 못 읽음"] += 1
                continue
            use = {k: v for k, v in got.items()
                   if k in cols and v is not None and k != "listing_id"}
            if not use:
                tally[f"{site} 넣을 칸이 없다"] += 1
                continue
            tally[f"{site} 채움"] += 1
            if write:
                sets = ", ".join(f"{k} = ?" for k in use)
                conn.execute(
                    f"UPDATE core_listing SET {sets}"
                    "  WHERE site = ? AND source_id = ?",
                    [*use.values(), site, sid])
        if write:
            conn.commit()
    conn.close()
    return tally


if __name__ == "__main__":
    want = [a for a in sys.argv[1:] if not a.startswith("-")]
    for k, v in sorted(run(want, "--write" in sys.argv).items()):
        print(f"  {k:28} {v:,}")
