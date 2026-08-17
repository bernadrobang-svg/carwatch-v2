# -*- coding: utf-8 -*-
"""등록부 미분류 정리 — 근거가 있는 것만 (8장 STEP 87 · V4-11).

지시서   8장 STEP 87 · 11장 `meta_field_usage`
근거     규격은 「사람이 분류해야 한다」이다.  그래서 ★ 추정하지 않는다 —
        원문과 코드에서 답이 나오는 것만 기계가 정하고 나머지는 남긴다
값규칙   in_use            core 컬럼에 실제로 저장하고 있다 (파서가 읽는다)
        not_provided      원문에 늘 null 이다 — 사이트가 안 준다
        display_only      저장은 하는데 판정에 안 쓴다
        unclassified      ★ 남긴다.  사람이 봐야 한다
금지     「비슷하니까」로 정하는 것.  추정으로 등록부를 채우는 것
사용     python3.11 tools/classify_registry.py [--apply]
★        tools/classify_fields.py 와 다른 것이다 —
         그쪽은 suggested.json 초안을 만들고, 이쪽은 DB 등록부를 정리한다
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

DB = os.path.join(ROOT, "carwatch.db")
# 이만큼 표본을 봐야 「늘 null 이다」를 말할 수 있다
NULL_MIN_SAMPLE = 30


def parser_source() -> str:
    """파서가 읽는 경로.  ★ 코드가 근거다 — 이름이 비슷한 것을 세지 않는다."""
    out = []
    for base in ("parse", "store", "analyze"):
        for dirpath, dirs, files in os.walk(os.path.join(ROOT, base)):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            out += [open(os.path.join(dirpath, f), encoding="utf-8").read()
                    for f in files if f.endswith(".py")]
    return "\n".join(out)


def sample_values(conn, endpoint: str, path: str) -> tuple:
    """그 경로가 원문에서 실제로 값을 갖는가.  (본 수, 값이 있던 수)."""
    seen = have = 0
    for (body,) in conn.execute(
        "SELECT body FROM raw_response WHERE endpoint=? AND status='ok'"
        " ORDER BY id DESC LIMIT ?", (endpoint, NULL_MIN_SAMPLE)
    ):
        try:
            node = json.loads(body)
        except (ValueError, TypeError):
            continue
        seen += 1
        for part in path.split("."):
            if isinstance(node, dict):
                node = node.get(part)
            elif isinstance(node, list) and node:
                node = node[0].get(part) if isinstance(node[0], dict) else None
            else:
                node = None
            if node is None:
                break
        if node not in (None, "", [], {}):
            have += 1
    return seen, have


def core_column(leaf: str, columns: dict) -> str | None:
    """그 필드가 들어가는 CORE 컬럼.  ★ 없으면 in_use 라 부르지 않는다 (V4-07).

    ★ 파서가 「읽는다」와 「저장한다」는 다르다.  저장하는 곳이 있어야 in_use 다
    """
    import re as _re

    snake = _re.sub(r"(?<!^)(?=[A-Z])", "_", leaf).lower()
    for table, cols in columns.items():
        for col in cols:
            if col in (snake, leaf.lower(), snake + "_json",
                       snake.replace("_cnt", "_count")):
                return f"{table}.{col}"
    return None


def decide(path: str, src: str, seen: int, have: int,
           columns: dict) -> tuple:
    """(usage, 사유, core_column).  ★ 답이 안 나오면 unclassified 로 남긴다."""
    leaf = path.split(".")[-1]
    # ① 파서가 그 이름을 읽고 + 들어가는 컬럼이 있는가 — 둘 다여야 in_use 다
    if f'"{leaf}"' in src or f"'{leaf}'" in src or f'get("{leaf}")' in src:
        col = core_column(leaf, columns)
        if col:
            return "in_use", f"파서가 {leaf} 를 읽어 {col} 에 넣는다", col
        # ★ 읽기는 하는데 저장하는 컬럼이 없다 — 사람이 봐야 한다 (V4-07)
        return "", "", None
    # ② 원문이 늘 비어 있는가 — 사이트가 안 준다
    if seen >= NULL_MIN_SAMPLE and have == 0:
        return "not_provided", f"원문 {seen}건에 전부 없다", None
    # ③ 그 밖은 사람이 봐야 한다.  ★ 추정하지 않는다
    return "", "", None


def main() -> int:
    apply = "--apply" in sys.argv
    conn = sqlite3.connect(DB)
    src = parser_source()
    columns = {t: [r[1] for r in conn.execute(f"PRAGMA table_info({t})")]
               for (t,) in conn.execute(
                   "SELECT name FROM sqlite_master WHERE type='table'"
                   " AND name LIKE 'core_%'")}
    rows = conn.execute(
        "SELECT site, endpoint, json_path FROM meta_field_usage"
        " WHERE usage='unclassified' ORDER BY endpoint, json_path").fetchall()
    got: dict = {"in_use": 0, "not_provided": 0, "": 0}
    left = []
    for site, endpoint, path in rows:
        seen, have = sample_values(conn, endpoint, path)
        usage, why, col = decide(path, src, seen, have, columns)
        got[usage] = got.get(usage, 0) + 1
        if not usage:
            left.append(f"{endpoint}:{path}")
            continue
        if apply:
            conn.execute(
                "UPDATE meta_field_usage SET usage=?, reason=?, core_column=?"
                " WHERE site=? AND endpoint=? AND json_path=?",
                (usage, why, col, site, endpoint, path))
    if apply:
        conn.commit()
    print(f"미분류 {len(rows)}건")
    print(f"  in_use        {got.get('in_use', 0)}  파서가 읽는다")
    print(f"  not_provided  {got.get('not_provided', 0)}  원문에 전부 없다")
    print(f"  ★ 남긴 것     {len(left)}  사람이 봐야 한다")
    for name in left[:12]:
        print(f"      {name}")
    if not apply:
        print("\n★ --apply 를 붙여야 실제로 넣는다")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
