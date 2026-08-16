# -*- coding: utf-8 -*-
"""요청 기록을 본다 — 무엇을 던졌고 무엇이 돌아왔는가.

지시서   2장 STEP 25a (실측 절차) · 5장 STEP 51 (audit_request)
근거     ★ 추측으로 URL 을 바꿔가며 던지지 않는다.  보낸 것을 먼저 본다
사용     python tools/inspect_requests.py [kind] [carwatch.db]
"""
from __future__ import annotations

import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE = 3
URL_WIDTH = 150


def main() -> int:
    kind = sys.argv[1] if len(sys.argv) > 1 else None
    db = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "carwatch.db")
    if not os.path.isfile(db):
        print(f"[X] {db} 가 없다")
        return 1
    conn = sqlite3.connect(db)

    print("■ 종류별 상태\n")
    sql = ("SELECT kind, status, http_code, COUNT(*) FROM audit_request "
           "GROUP BY kind, status, http_code ORDER BY kind, COUNT(*) DESC")
    for k, status, code, n in conn.execute(sql):
        print(f"  {k:12} {status:12} {str(code):5} {n:6}")

    where, args = "", ()
    if kind:
        where, args = " WHERE kind = ?", (kind,)
    print(f"\n■ 요청 URL 표본{' — ' + kind if kind else ''}\n")
    seen: dict[str, int] = {}
    for k, status, code, url in conn.execute(
        "SELECT kind, status, http_code, url FROM audit_request"
        + where + " ORDER BY kind, status", args
    ):
        key = f"{k}/{status}"
        seen[key] = seen.get(key, 0) + 1
        if seen[key] > SAMPLE:
            continue
        print(f"  [{k} · {status} · {code}]")
        print(f"  {url[:URL_WIDTH]}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
