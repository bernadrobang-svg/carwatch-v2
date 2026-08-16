# -*- coding: utf-8 -*-
"""facet 원문에 실제로 어떤 축이 왔는지 본다.

지시서   2장 STEP 23 (facet 2요청 · 필수 축) · STEP 25a (실측 절차)
근거     ★ 추측으로 URL 을 바꿔가며 던지지 않는다.  원문을 열어 확인한다
사용     python tools/inspect_facet.py [carwatch.db]
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

SAMPLE_VALUES = 3
NAME_WIDTH = 26
RULE_WIDTH = 70   # 화면 구분선 폭 (형식)


def walk(node, out):
    """(Name, Type) 을 전부 뽑는다.  Name 만으로 훑지 않는다 (STEP 23)."""
    stack = [node]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            name, typ = cur.get("Name"), cur.get("Type")
            if isinstance(name, str):
                out.setdefault((name, typ), []).append(cur)
            stack.extend(v for v in cur.values() if isinstance(v, (dict, list)))
        elif isinstance(cur, list):
            stack.extend(v for v in cur if isinstance(v, (dict, list)))


def main() -> int:
    db = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "carwatch.db")
    if not os.path.isfile(db):
        print(f"[X] {db} 가 없다")
        return 1
    conn = sqlite3.connect(db)
    rows = conn.execute(
        "SELECT target_key, request_kind, request_url, body FROM raw_facet "
        "ORDER BY target_key, request_kind").fetchall()
    if not rows:
        print("[X] raw_facet 이 비어 있다")
        return 1

    for target, kind, url, body in rows:
        doc = json.loads(body)
        found: dict = {}
        walk(doc, found)
        print(f"\n{'=' * RULE_WIDTH}")
        print(f"{target}  ·  {kind}")
        print(f"URL  {url}")
        print(f"루트 키  {sorted(doc)[:12] if isinstance(doc, dict) else type(doc).__name__}")
        print(f"축 {len(found)}개")
        for (name, typ), nodes in sorted(found.items(),
                                         key=lambda kv: (kv[0][0], str(kv[0][1]))):
            facets = nodes[0].get("Facets") or []
            vals = [str(f.get("Value")) for f in facets[:SAMPLE_VALUES]
                    if isinstance(f, dict)]
            mark = " ★" if "badge" in name.lower() or "trim" in name.lower() else ""
            print(f"   {name:{NAME_WIDTH}} {str(typ):14} "
                  f"{len(facets):4}값  {', '.join(vals)}{mark}")

    print(f"\n{'=' * RULE_WIDTH}")
    print("★ 표시된 것이 트림 축 후보다.  이름이 Badge 가 아닐 수 있다")
    return 0


if __name__ == "__main__":
    sys.exit(main())
