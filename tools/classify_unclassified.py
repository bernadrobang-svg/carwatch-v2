# -*- coding: utf-8 -*-
"""미분류 경로를 원인별로 가른다 (개정 341 · V4-26 · V4-27).

지시서   `docs/chapters/61-web/g-chart.md` 「미분류」 · 2장 STEP 87
근거     가이드 지적 — 「349개를 사람이 하나씩 보라는 뜻입니다.  아무도 안 봅니다」
값규칙   ★ 자동 분류를 정본에 바로 넣지 않는다.  「제안」까지만 한다 (STEP 87)
갈래     ② 같은 뜻인데 이름이 다른 것   ← 이미 분류된 잎 이름과 같다
        ③ 값이 늘 비어 있는 것        ← 전건 null
        ④ 정말 새로운 것              ← 사람이 봐야 한다
금지     「349건 미분류」라고만 내는 것
사용     python3.11 tools/classify_unclassified.py
        python3.11 tools/classify_unclassified.py --suggest
        ★ --suggest 는 config/field_usage.suggested.json 을 새로 만든다.
          ★ 정본(field_usage.json)에 넣지 않는다 — 사람이 옮긴다 (STEP 87)
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

DB = os.path.join(ROOT, "carwatch.db")
# 엔드포인트마다 원문 몇 개를 열어 볼 것인가.
# ★ 전건을 열면 오래 걸린다.  값이 「늘 비어 있는가」는 표본으로 충분하다
# 화면·보고에 몇 줄까지 낼 것인가
TOP_ROWS = 20


# 조회는 store 에 있다.  ★ web · report 도 같은 것을 쓴다 —
# 그 계층은 tools 를 부르지 못한다 (V4-22 · S15)
from store.core import classify_unclassified   # noqa: E402


def write_suggestion(rows: list) -> str:
    """제안을 파일로 낸다 (STEP 87).

    ★ 정본에 자동으로 넣지 않는다.  「이렇게 보입니다」까지만이다
    ★ ④ 정말 새로운 것은 넣지 않는다 — 사람이 봐야 한다
    """
    out = {"_note": "tools/classify_unclassified.py --suggest 가 만든다. "
                    "★ 사람이 확인한 뒤 config/field_usage.json 으로 "
                    "옮긴다 (STEP 87).  자동으로 정본이 되지 않는다",
           "_kinds": {}, "candidates": {}}
    for one in rows:
        kind = one["kind"]
        out["_kinds"][kind] = out["_kinds"].get(kind, 0) + 1
        if kind.startswith("④"):
            continue
        usage = ("not_provided" if kind.startswith("③") else "")
        out["candidates"][f"{one['endpoint']}:{one['path']}"] = {
            "kind": kind, "suggested_usage": usage,
            "reason": one["hint"],
            "observed": one["hits"], "of": one["total"]}
    path = os.path.join(ROOT, "config", "field_usage.suggested.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return path


def write_blocking_list(conn) -> str:
    """판정을 막는 32건을 목록으로 (개정 390 · V4-30).

    ★ 값 분포는 2단계다.  목록을 먼저 낸다 —
      「목록이 없으니 가이드도 마스터도 아무것도 못 정한다」
    ★ 저장소에 남긴다.  DB 와 화면에만 있으면 아무도 못 본다
    """
    from datetime import datetime, timezone

    from store.core import blocking_rows
    from tools.classify_fields import (
        WHOLE_CONTAINERS, parser_lines, parser_paths,
    )

    rows = blocking_rows(conn, parser_paths(), WHOLE_CONTAINERS,
                         parser_lines())
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    path = os.path.join(ROOT, "outputs", f"{day}_registry32_목록.md")
    out = [
        "# 판정을 막는 미분류 — 목록",
        "",
        "**`python3.11 tools/classify_unclassified.py --blocking --list` "
        "가 만든다. 손으로 고치지 않는다.**",
        "",
        f"**{len(rows)}건** · 많이 관측된 순",
        "",
        "```",
        "★ 이 목록은 「파서가 실제로 그 경로를 읽는 것」이다.",
        "  그래서 분류 전에는 판정을 막는다 (V4-11).",
        "★ 정말 읽는지 「파서가 읽는 곳」의 파일·줄로 보실 수 있다.",
        "★ 값 분포는 2단계다 — /admin/registry 에서 항목마다 봅니다",
        "```",
        "",
        "| # | 엔드포인트 | 경로 | 관측 | 파서가 읽는 곳 |",
        "|--:|---|---|--:|---|",
    ]
    for i, r in enumerate(rows, 1):
        out.append(f"| {i} | {r['endpoint']} | `{r['endpoint']}:{r['path']}` "
                   f"| {r['hits']}/{r['total']} "
                   f"| `{r['where'] or '★ 못 찾음'}` |")
    got: dict = {}
    for r in rows:
        got[r["endpoint"]] = got.get(r["endpoint"], 0) + 1
    out += ["", "## 엔드포인트별", "", "| 엔드포인트 | 몇 개 |", "|---|--:|"]
    for name, n in sorted(got.items(), key=lambda kv: -kv[1]):
        out.append(f"| {name} | {n} |")
    out.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    return os.path.relpath(path, ROOT)


def main() -> int:
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        if "--blocking" in sys.argv and "--list" in sys.argv:
            where = write_blocking_list(conn)
            print(f"판정을 막는 것 목록 → {where}")
            print("★ 「파서가 읽는 곳」을 파일·줄로 적었습니다 — "
                  "정말 읽는지 보실 수 있습니다\n")
            return 0
        rows = classify_unclassified(conn)
    finally:
        conn.close()
    if not rows:
        print("미분류가 없습니다")
        return 0

    by_kind: dict = {}
    by_ep: dict = {}
    for one in rows:
        by_kind[one["kind"]] = by_kind.get(one["kind"], 0) + 1
        by_ep[one["endpoint"]] = by_ep.get(one["endpoint"], 0) + 1

    print(f"미분류 {len(rows)}건 — 원인별로 갈랐습니다 (개정 341)\n")
    print("엔드포인트별")
    for ep, n in sorted(by_ep.items(), key=lambda kv: -kv[1]):
        print(f"  {ep:<22} {n:>4}건")
    print("\n갈래별")
    for kind, n in sorted(by_kind.items()):
        print(f"  {kind:<16} {n:>4}건")
    need = by_kind.get("④ 새로운 것", 0)
    print(f"\n★ 사람이 봐야 할 것 {need}건 · "
          f"나머지 {len(rows) - need}건은 제안이 있습니다\n")

    if "--suggest" in sys.argv:
        where = write_suggestion(rows)
        print(f"제안 → {where}")
        print("★ 정본에 자동으로 넣지 않았습니다.  "
              "사람이 확인한 뒤 config/field_usage.json 으로 옮깁니다 "
              "(STEP 87)\n")

    print(f"자주 나온 순 {TOP_ROWS}건 — ★ 급한 정도가 다릅니다")
    for one in rows[:TOP_ROWS]:
        print(f"  {one['hits']:>4}/{one['total']:<4} {one['endpoint']:<20}"
              f" {one['path'][:44]:<46} {one['kind']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
