# -*- coding: utf-8 -*-
"""저장된 매물을 ★ 갈래에 넣는다 — ★ 사이트 도구가 쓴 줄용 (명령서 37·39).

쓰기   python3.11 tools/classify_stored.py            전 사이트
      python3.11 tools/classify_stored.py --site heydealer
      python3.11 tools/classify_stored.py --dry      세기만

★★ 왜 이것이 따로 있나 —
   ★ `S4` 는 ★ **수집 봉투(raw_response)** 를 읽어 갈래를 정한다.
   ★ 그런데 ★ 사이트 도구(K카·KB·헤이딜러·리본카)는 ★ `core_listing` 에 ★ 바로 쓴다.
   ★ ★ 그래서 ★ 그 줄들은 ★ `S4` 가 ★ 한 번도 못 본다 — ★ `target_key` 가 안 붙는다
   ★ ★ 실측 08-24 — ★ 헤이딜러 151 · 리본카 1,036 이 ★ 전건 `target_key` 없음이었다
★ 갈래를 고르는 규칙은 ★ `parse/classify.py` 하나다.  ★ 여기서 다시 정하지 않는다
금지  ★ 차종을 코드에 박는 것 (S14 · 금지 6)
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from parse.classify import classify                                # noqa: E402
from store.dictionary import (collect_group_of, fuel_normalize,    # noqa: E402
                              match_target_name, target_map)
from store.raw import commit, open_db                              # noqa: E402


def _targets() -> dict:
    import json
    with open(os.path.join(ROOT, "config", "targets.json"), encoding="utf-8") as f:
        rows = json.load(f)
    return {k: v for k, v in rows.items()
            if not k.startswith("_") and isinstance(v, dict)
            and v.get("collect_group")}


def main() -> int:
    args = sys.argv[1:]
    site = None
    if "--site" in args:
        i = args.index("--site")
        if i + 1 < len(args):
            site = args[i + 1]
    targets = _targets()
    conn = open_db(os.path.join(ROOT, "carwatch.db"))
    at = datetime.now(timezone.utc).isoformat()

    where = "target_key IS NULL AND site_model_group IS NOT NULL"
    argv: list = []
    if site:
        where += " AND site=?"
        argv = [site]
    rows = conn.execute(
        "SELECT listing_id, site, site_model_group, fuel_raw, trim_badge, "
        "       trim_grade_name, displacement_cc "
        f"FROM core_listing WHERE {where}", argv).fetchall()
    print(f"★ 갈래가 안 붙은 줄 {len(rows):,}건")

    got = {"붙음": 0, "갈래 밖": 0, "이름 모름": 0, "후보 여럿": 0}
    per: dict = {}
    for lid, st, name, fuel, badge, grade, cc in rows:
        # ★ 사이트가 꾸밈말·세대를 붙여 준다 — ★ 아는 이름이 들어 있으면 그것이다
        named = match_target_name(st, name) or name
        cg = collect_group_of(st, named)
        if not cg:
            got["이름 모름"] += 1
            continue
        # ★★ 사전이 ★ `target_key` 를 못 박아 둔 사이트가 있다 (KB · 볼보 · 렉서스 · BMW).
        #   ★ ★ 그 사이트는 ★ **차종을 골라서 부른다** — ★ 슬러그·해시가 곧 차종이다.
        #     ★ ★ 그때는 ★ 연료를 몰라도 ★ 차종이 정해진다.
        #     ★ ★ 실측 08-24 — ★ 목록만 받은 159건이 ★ 연료가 없어 ★ 전건 떨어졌다
        fixed = (target_map(st).get(named) or {}).get("target_key")
        if fixed and fixed in targets:
            got["붙음"] += 1
            per[st] = per.get(st, 0) + 1
            if "--dry" not in args:
                conn.execute(
                    "UPDATE core_listing SET target_key=?, classify_stage=?, "
                    "classify_source=?, status='active', last_seen=? "
                    "WHERE listing_id=?",
                    (fixed, "provisional", "list", at, lid))
            continue
        res = classify(targets, cg, fuel_normalize(st, fuel), badge, grade, cc)
        if not res.target_key:
            got["후보 여럿" if res.conflict else "갈래 밖"] += 1
            continue
        got["붙음"] += 1
        per[st] = per.get(st, 0) + 1
        if "--dry" not in args:
            conn.execute(
                "UPDATE core_listing SET target_key=?, classify_stage=?, "
                "classify_source=?, classify_conflict=?, status='active', "
                "last_seen=? WHERE listing_id=?",
                (res.target_key, res.stage, res.source,
                 1 if res.conflict else 0, at, lid))
    if "--dry" not in args:
        commit(conn)
    print("★ " + " · ".join(f"{k} {v:,}" for k, v in got.items()))
    for st, n in sorted(per.items(), key=lambda x: -x[1]):
        print(f"   {st:<14} {n:>5}건")
    if "--dry" in args:
        print("★ --dry 라 저장하지 않았다")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
