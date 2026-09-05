# -*- coding: utf-8 -*-
"""D5 ② — ★ **파서가 매핑표를 읽는다** (지시 r1168 · `S46-282`).

★★★ 마스터 — 「★ 내가 ★ **사이트별로 매핑표를 만들고 ★ 그걸 파서가 보게 하라**고 했는데
   ★ 왜 안 되어 있지?  ★ ★ 지금 파서에 ★ **`if` 구문으로 하드코딩**되어 있거나
   ★ ★ ★ **정규식으로 흩어져** 있지?」
★★ 실측 09-05 — ★ 파서가 표를 ★ **한 곳도 안 읽었다** (KB `if` 24·정규식 38 ·
  ★ 리볼트 `if` 41 · 볼보 `if` 25·정규식 27).

★ 정본은 ★ `config/dictionaries/field_map.json` 이다 —
  ★ ★ `tools/load_field_map.py` 가 ★ **등록부(`meta_field_usage`)에서** 낸다.
  ★ ★ ★ 손으로 안 적는다 · ★ 파서는 ★ **DB 를 안 연다** (`V11-01` 과 같은 뜻).

★★ **덮지 않는다** — ★ 파서가 이미 채운 칸은 ★ 그대로 둔다.
  ★ ★ 표는 ★ **빈 칸만** 메운다 — ★ 코드가 더 잘 아는 자리가 있다 (단위·꼴 바꾸기).
★ 길이 없는 줄(「코드에 박혀 있다」)은 ★ 표에 안 들어온다 — ★ 읽을 길이 없다
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MAP: dict | None = None

# ★ 값으로 안 보는 것 — ★ 「없음」을 값으로 삼지 않는다 (금지 12)
EMPTY = (None, "", [], {}, "None", "null")


def table(site: str, root: str = ROOT) -> dict:
    """★ 그 사이트의 ★ `{길: 칸}`.  ★ 없으면 빈 표다 (지어내지 않는다)."""
    global _MAP

    if _MAP is None:
        path = os.path.join(root, "config", "dictionaries", "field_map.json")
        try:
            with open(path, encoding="utf-8") as f:
                _MAP = json.load(f).get("by_site") or {}
        except (OSError, ValueError):
            _MAP = {}
    return dict(_MAP.get(site) or {})


def _dig(item, path: str):
    """★ 점으로 이은 길을 따라간다 — ★ `a.b.c`.  ★ 없으면 `None`."""
    got = item
    for step in str(path).split("."):
        if isinstance(got, dict):
            got = got.get(step)
        else:
            return None
        if got is None:
            return None
    return got


def apply_map(site: str, item, out: dict, root: str = ROOT) -> dict:
    """★ 원문 한 건에서 ★ **표가 아는 칸**을 메운다.

    ★ `item` 은 ★ 푼 묶음(dict)이다 — ★ HTML 은 못 읽는다 (길이 없다).
    ★ `out` 에 ★ **이미 있는 칸은 안 건드린다** — ★ 파서가 더 잘 아는 자리다.
    ★ 돌려줌  ★ 메운 칸 이름들
    """
    if not isinstance(item, dict) or not isinstance(out, dict):
        return {}
    got = table(site, root)
    if not got:
        return {}
    filled: dict = {}
    for path, col in got.items():
        if col in out and out[col] not in EMPTY:
            continue                      # ★ 파서가 이미 채웠다
        val = _dig(item, path)
        if val in EMPTY:
            continue                      # ★ 「없음」은 안 넣는다
        if isinstance(val, (dict, list)):
            continue                      # ★ 묶음은 ★ 파서가 풀 몫이다
        out[col] = val
        filled[col] = path
    return filled
