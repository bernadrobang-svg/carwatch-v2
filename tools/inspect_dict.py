# -*- coding: utf-8 -*-
"""사전 검토 — pending 값과 원문 표본을 본다.

지시서   4장 STEP 45 (검토 절차) · STEP 41 (축 정책)
근거     ★ 사람이 확인하기 전에는 그 축을 쓰는 판정이 돌지 않는다.
         확인하려면 「무슨 값이 왜 떴는가」가 보여야 한다
사용     python tools/inspect_dict.py [carwatch.db]
         python tools/inspect_dict.py --confirm <axis> <value>
         python tools/inspect_dict.py --confirm-axis <axis>
"""
from __future__ import annotations

import os
import sqlite3
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from store.dictionary import confirm_enum, list_pending  # noqa: E402

DB = os.path.join(ROOT, "carwatch.db")
SITE = "encar"
VALUE_WIDTH = 34


def show(conn) -> int:
    rows = list_pending(conn, SITE)
    if not rows:
        print("검토 대기 없음 — S9 가 진행된다")
        return 0
    print(f"■ 검토 대기 {len(rows)}건\n")
    axis = None
    for a, value, _disp, cnt, src, first in rows:
        if a != axis:
            axis = a
            print(f"\n[{a}]  원천 {src}")
        print(f"   {value:{VALUE_WIDTH}} 관측 {cnt:5}  최초 {first[:10]}")
    print("\n■ 조치\n")
    print("   원문을 보고 값이 타당하면 확정한다")
    print("   run.bat dict --confirm <axis> <value>")
    print("   run.bat dict --confirm-axis <axis>      그 축을 전부")
    print("\n   ★ 값이 이상하면 확정하지 않는다 — 파싱을 먼저 본다")
    return 0


def main() -> int:
    args = sys.argv[1:]
    db = next((a for a in args if a.endswith(".db")), DB)
    if not os.path.isfile(db):
        print(f"[X] {db} 가 없다")
        return 1
    conn = sqlite3.connect(db)
    at = datetime.now(timezone.utc).isoformat()

    if "--confirm" in args:
        i = args.index("--confirm")
        axis, value = args[i + 1], args[i + 2]
        print(f"{axis}.{value} → {confirm_enum(conn, SITE, axis, value, at)}")
        return 0
    if "--confirm-axis" in args:
        axis = args[args.index("--confirm-axis") + 1]
        n = 0
        for a, value, *_rest in list_pending(conn, SITE):
            if a == axis:
                confirm_enum(conn, SITE, axis, value, at)
                n += 1
        print(f"{axis} {n}건 확정")
        return 0
    return show(conn)


if __name__ == "__main__":
    sys.exit(main())
