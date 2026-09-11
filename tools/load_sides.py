# -*- coding: utf-8 -*-
"""★ 받아 둔 **성능점검 · 보험이력** 원문을 제 표에 넣는다.

★★ `tools/reparse_stored.py` 는 ★ **상세만** 넣는다 — ★ 그 둘은 ★ 표가 따로다
  (`core_inspection` · `core_record`).  ★ 안 넣으면 ★ 원문만 쌓이고 ★ 화면은 빈다.
★ 이미 있는 줄은 ★ 덮는다 — ★ 새로 받은 것이 더 새 것이다
★ 못 읽으면 ★ 0 이다 — ★ 원문은 남아 있다 (S46-185)

돌리는 법
    python3.11 tools/load_sides.py encar kbchachacha
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

from report.screens.fetch import _into_side        # noqa: E402
from store.rawfile import read, walk               # noqa: E402

KINDS = ("inspection", "record")


def run(sites: list, write: bool = True, db: str = "carwatch.db") -> Counter:
    conn = sqlite3.connect(os.path.join(ROOT, db))
    tally: Counter = Counter()
    for site in sites:
        try:
            mod = importlib.import_module(f"parse.{site}.mapping")
        except ImportError:
            tally[f"{site} 파서가 없다"] += 1
            continue
        for kind in KINDS:
            for path in sorted(walk(site=site, endpoint=kind, root=ROOT),
                               reverse=True):
                env = read(path) or {}
                if str(env.get("status") or "ok") != "ok":
                    continue
                body = env.get("body")
                if isinstance(body, bytes):
                    body = body.decode("utf-8", "replace")
                said = str(body or "").lstrip()[:1]
                raw = body
                if said in ("{", "["):
                    try:
                        raw = json.loads(body)
                    except ValueError:
                        pass
                sid = os.path.basename(path)[:-5]
                got = _into_side(conn, mod, kind, site, sid, raw) if write else 0
                tally[f"{site}.{kind} " + ("넣음" if got else "안 들어감")] += 1
    conn.commit()
    conn.close()
    return tally


if __name__ == "__main__":
    want = [a for a in sys.argv[1:] if not a.startswith("-")]
    for k, v in sorted(run(want or ["encar"]).items()):
        print(f"  {k:28} {v:,}")
