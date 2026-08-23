# -*- coding: utf-8 -*-
"""차종군 + `targets.json` 규칙으로 ★ 갈래를 고른다.

지시서   `docs/HYUNDAI_CERTIFIED_API.md` 2d · 명령서 `ORDER_20260822_r515.md` 2a장
근거     ★ 「★ 이미 있는 `targets.json` 의 `fuel_match`·`trim_include`·
         `displacement_range` 를 쓴다.  ★ 새 규칙을 만들지 않는다 —
         ★ 엔카가 쓰는 그 칸이다」 (규격 2d)
계층     ★ `parse` 다.  ★ `store` 에 두면 ★ V4-22(역방향 import)에 걸린다 —
         ★ `store` 는 `contracts`·`errors` 밖을 못 부른다 (실측 08-23)
금지     ★ 차종 문자열·엔드포인트를 지어내는 것 (금지 6)
"""
from __future__ import annotations

import json
import os

from parse.classify import classify
from store.dictionary import collect_group_of, fuel_normalize

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TARGETS: dict | None = None


def load_targets(path: str | None = None) -> dict[str, dict]:
    """`targets.json` — ★ 최상위가 `target_key` 다 (0장 STEP 6).

    ★ `collect/runner.py` 의 같은 이름 함수와 ★ 뜻이 같다.  ★ 그것을 부르지 않는 것은
      ★ `collect` 가 ★ 이 층보다 위라 ★ 부르면 역방향이 되기 때문이다 (V4-22)
    """
    global _TARGETS

    if _TARGETS is None or path:
        at = path or os.path.join(ROOT, "config", "targets.json")
        with open(at, encoding="utf-8") as f:
            raw = json.load(f)
        got = {k: v for k, v in raw.items()
               if isinstance(v, dict) and "collect_group" in v}
        if path:
            return got
        _TARGETS = got
    return _TARGETS


def target_by_rules(site: str, name: str | None, fuel_raw: str | None,
                    title: str | None, displacement_cc: int | None = None):
    """사이트 차종 이름 → ★ 우리 갈래.

    ★ 제목에 차종·연료·배기량이 다 있어 ★ 상세가 없어도 갈린다 (규격 2d) —
      ★ 전수 1,113건에 걸어 ★ 170건이 붙는다
    돌려줌   `ClassifyResult` · ★ 차종군을 모르면 None (「차종 미정」)
    """
    grp = collect_group_of(site, name)
    if not grp:
        return None
    return classify(load_targets(), grp, fuel_normalize(site, fuel_raw),
                    title, None, displacement_cc)
