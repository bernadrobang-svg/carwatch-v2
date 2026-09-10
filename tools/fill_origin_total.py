# -*- coding: utf-8 -*-
"""★ M-1 — **신차출고가(옵션 포함)** 를 저장한다 (지시 r1213).

★★★ 마스터 — 「★ 감가율의 **분모**다.  ★ 신차**정가**가 아니라 ★ 신차**출고가**(옵션 포함)다」
★ `price_origin_won` 은 ★ **등급기준가**다 (엔카 `category.originPrice`) — ★ 옵션이 빠졌다.
★ 옵션값은 ★ `dict_model_option.price_manwon` 이 안다 (차종·트림 열쇠별로).
★★ 옵션 목록이 ★ **두 꼴**이다 (지시 H) —
  ★ 코드 글자(`["1050",…]`) · ★ 값이 함께 오는 dict(`[{"name":…,"price":…}]`).
★★★ 못 셈하면 ★ **비운다** — ★ 「신차가 미조회」다.  ★ 0 으로 두지 않는다 (금지 12).
  ★ 옵션을 하나도 모르면 ★ 등급기준가만으로 ★ **출고가라 하지 않는다** —
  ★ ★ 옵션이 빠진 값을 분모로 쓰면 ★ 감가율이 실제보다 **나빠 보인다**

돌리는 법
    python3.11 tools/fill_origin_total.py            ★ 잰다
    python3.11 tools/fill_origin_total.py --write    ★ 넣는다
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import glob
import re
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from store.rawfile import read           # noqa: E402

# ★ KB 상세가 ★ **스스로** 신차가를 준다 — ★ 우리가 셈하지 않아도 된다.
#   ★ 원문   var newcarPrice = "4863";   ★ 만원 · ★ **부가세 뺀 값**이다
#   ★ 화면이 ★ `newcarPrice * 1.1` 로 그리고,
#   ★ ★ 그 값을 KB 스스로 「선택옵션 · 프로모션 · 부가세가 포함된 실 구매가격」이라 적는다
#   ★ 그러니 ★ **×1.1 한 것**이 우리가 찾는 **출고가**다
KB_NEWCAR = re.compile(r'var\s+newcarPrice\s*=\s*"(\d+)"')
KB_VAT = 1.1


def kb_newcar_book(root: str = ROOT) -> dict:
    """KB 상세 원문 → {source_id: 신차출고가(원)}.  ★ 0 은 ★ **미조회**다."""
    got: dict = {}
    for path in glob.glob(os.path.join(root, "raw/kbchachacha/detail/*/*.json")):
        env = read(path)
        body = (env or {}).get("body") or b""
        if isinstance(body, str):
            body = body.encode("utf-8", "replace")
        hit = KB_NEWCAR.search(body.decode("utf-8", "replace"))
        if not hit or hit.group(1) == "0":
            continue
        key = os.path.basename(path)[:-5]
        got[key] = round(int(hit.group(1)) * KB_VAT) * 10000
    return got


def _price_table(conn: sqlite3.Connection) -> dict:
    """(사이트, 차종열쇠, 코드) → 값(원).  ★ 없는 것은 안 넣는다."""
    got: dict = {}
    for site, key, code, won in conn.execute(
            "SELECT site, model_catalog_key, option_code, price_manwon"
            "  FROM dict_model_option WHERE price_manwon IS NOT NULL"):
        got[(str(site), str(key), str(code))] = int(won) * 10000
    return got


def option_won(codes, site: str, key: str, table: dict) -> tuple:
    """옵션값 합 · 값을 못 찾은 코드 수.

    ★ 값이 함께 온 것은 ★ 그대로 쓴다.  ★ 코드 글자는 ★ 표를 본다.
    ★ 목록이 비어 있으면 ★ 「선택 옵션 없음」이라 ★ 0 이 맞다 (확인된 사실이다)
    """
    if codes is None:
        return None, 0
    if not codes:
        return 0, 0
    total, miss = 0, 0
    for one in codes:
        if isinstance(one, dict):
            won = one.get("price")
            if won:
                total += int(won)
            else:
                miss += 1
            continue
        won = table.get((site, key, str(one)))
        if won:
            total += won
        else:
            miss += 1
    return total, miss


def run(write: bool = False, db: str = "carwatch.db") -> Counter:
    conn = sqlite3.connect(os.path.join(ROOT, db))
    table = _price_table(conn)
    kb = kb_newcar_book()
    tally: Counter = Counter()
    rows = conn.execute(
        "SELECT listing_id, site, model_catalog_key, price_origin_won,"
        "       options_choice_json, source_id, price_current_won"
        "  FROM core_listing"
        " WHERE status IN ('active','new','relisted')").fetchall()
    for lid, site, key, origin, optj, sid, now in rows:
        said = kb.get(str(sid)) if site == "kbchachacha" else None
        if said:
            # ★ 판매가가 신차가보다 높으면 ★ 그 신차가를 믿지 않는다 —
            #   ★ ★ 값을 억지로 넣어 ★ 감가율을 음수로 만들지 않는다
            if now and now > said:
                tally["신차가가 판매가보다 낮다"] += 1
                continue
            tally["채움 — KB 신차가"] += 1
            if write:
                conn.execute(
                    "UPDATE core_listing SET price_origin_total_won = ?,"
                    "       price_origin_total_src = 'kb_신차가'"
                    " WHERE listing_id = ?", (said, lid))
            continue
        if not origin:
            tally["등급기준가가 없다"] += 1
            continue
        try:
            codes = json.loads(optj) if optj else None
        except (ValueError, TypeError):
            codes = None
        won, miss = option_won(codes, str(site), str(key or ""), table)
        if won is None:
            # ★ 옵션을 아예 모른다 — ★ 출고가라 부를 수 없다
            tally["옵션을 모른다"] += 1
            continue
        if miss:
            # ★ 값을 못 찾은 코드가 있다 — ★ 모자란 합을 출고가라 하지 않는다
            tally["옵션값이 모자라다"] += 1
            continue
        tally["채움 — 엔카 셈"] += 1
        if write:
            conn.execute(
                "UPDATE core_listing SET price_origin_total_won = ?,"
                "       price_origin_total_src = 'encar_계산'"
                " WHERE listing_id = ?", (int(origin) + won, lid))
    if write:
        conn.commit()
    conn.close()
    return tally


if __name__ == "__main__":
    for k, v in sorted(run("--write" in sys.argv).items()):
        print(f"  {k:20} {v:,}")
