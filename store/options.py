# -*- coding: utf-8 -*-
"""옵션 목록 — ★ **두 꼴**을 한 자리에서 푼다 (지시 H · 09-10).

★★★ 왜 이 파일이 생겼나 — ★ `options_choice_json` 이 ★ **두 꼴**로 담긴다.
  ★ 코드 글자   `["1050", "1046"]`                     — 엔카
  ★ 값이 든 dict `[{"name": "파퓰러 패키지", "price": 5100000}]` — K카 · 헤이딜러
★ 지시 H — 「가격이 있으면 `options_choice_json` · 이름만 있으면 `options_name_json`.
  ★ 가격이 없다고 옵션 축을 0 으로 두지 않는다」.  ★ 두 꼴은 ★ **일부러 둘**이다.

★★ 그런데 ★ 읽는 자리가 ★ **여덟 곳**인데 ★ 저마다 따로 풀고 있었다 —
  ★ ★ dict 를 ★ 표의 열쇠나 집합에 넣어 ★ `unhashable type: 'dict'` 로 죽었다.
  ★ ★ ★ 실측 — ★ 09-08 에 세 곳을 고쳤는데 ★ 09-10 에 ★ **또 두 곳**이 죽었다.
★ 그러니 ★ **푸는 곳을 하나로 모은다.**  ★ 새 꼴이 생기면 ★ 여기만 고친다
"""
from __future__ import annotations

import json


def option_list(raw) -> list:
    """원문 글자 · 목록 → ★ 목록.  ★ 못 읽으면 ★ 빈 목록."""
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return list(raw)
    try:
        got = json.loads(raw)
    except (ValueError, TypeError):
        return []
    return got if isinstance(got, list) else []


def option_codes(raw) -> list:
    """★ **열쇠로 쓸 수 있는 글자**만 낸다.

    ★ dict 는 ★ `code` → `name` 차례로 본다.  ★ 둘 다 없으면 ★ 뺀다 —
      ★ ★ dict 를 ★ 집합·표에 그대로 넣으면 ★ 죽는다
    """
    out = []
    for one in option_list(raw):
        if isinstance(one, dict):
            said = one.get("code") or one.get("name")
            if said is None:
                continue
            out.append(str(said))
            continue
        if one is None:
            continue
        out.append(str(one))
    return out


def option_total(raw, prices: dict | None = None) -> int:
    """옵션값 합(원).  ★ 값이 든 dict 는 ★ 그 값을 쓰고
    ★ 코드 글자는 ★ 표(`prices`)를 본다.  ★ 모르면 ★ 0 으로 센다 —
    ★★ 「모른다」와 「없다」를 갈라야 하는 자리에서는 ★ `option_total_strict` 를 쓴다
    """
    prices = prices or {}
    got = 0
    for one in option_list(raw):
        if isinstance(one, dict):
            won = one.get("price")
            if isinstance(won, (int, float)):
                got += int(won)
            continue
        try:
            got += int(prices.get(one, 0) or 0)
        except (TypeError, ValueError):
            continue
    return got


def option_total_strict(raw, prices: dict | None = None) -> tuple:
    """(합, 값을 모르는 것의 수).  ★ 모르는 것이 있으면 ★ 부르는 쪽이 ★ 비운다."""
    prices = prices or {}
    got, miss = 0, 0
    for one in option_list(raw):
        if isinstance(one, dict):
            won = one.get("price")
            if isinstance(won, (int, float)):
                got += int(won)
            else:
                miss += 1
            continue
        won = prices.get(one)
        if won:
            got += int(won)
        else:
            miss += 1
    return got, miss
