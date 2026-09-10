# -*- coding: utf-8 -*-
"""★ M-5 — **하체 낱말 13개**를 잡아 경고한다 (지시 r1212).

★★★ 마스터 — 「정비이력에서 하체 낱말 13개를 잡아 경고한다 — 너클 · 로워암」.

★★★★★ 실측 09-10 — ★ **정비이력을 주는 창구가 어디에도 없다.**
  ★ 엔카 열세 창구 (`catalog` `detail` `diagnosis` `ev_battery` `extend_warrant`
    `facet` `inspection` `inspection_summary` `list` `platform_check` `record`
    `record_summary` `sellingpoint`) · ★ KB · ★ K카 — ★ 전부 훑었다.
  ★ 성능점검부에도 안 나온다 — ★ 383장에 ★ 스티어링기어 2건뿐이다.
  ★ 보험이력에도 안 나온다 — ★ `accidents_json` 은 ★ **금액만** 준다.
★★ 그래서 ★ 지금 잡을 수 있는 것은 ★ `ad_body_text` — ★ **판매자가 쓴 글**이다.
  ★ 실측 — ★ 엔카 상세 1,200장 중 ★ **103대**에 하체 낱말이 있었다.
  ★★★ 이것은 ★ **정비이력이 아니다.**  ★ 그래서 ★ `undercarriage_src` 에
    ★ ★ 「판매자 글」이라 적는다 — ★ 화면이 그것을 그대로 낸다 (금지 6).

돌리는 법
    python3.11 tools/fill_undercarriage.py            ★ 잰다
    python3.11 tools/fill_undercarriage.py --write    ★ 넣는다
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

BOOK = os.path.join(ROOT, "config", "dictionaries", "undercarriage.json")
SRC_AD = "판매자 글"


def rule(path: str = BOOK) -> dict:
    """판매자 글에서만 쓰는 잣대.  ★ 값을 코드에 안 박는다 (S14)."""
    with open(path, encoding="utf-8") as fh:
        return json.load(fh).get("판매자_글_규칙") or {}


def words(path: str = BOOK) -> list:
    """사전 → [(대표말, [찾을 말들], [안 잡을 말들])].  ★ 값을 코드에 안 박는다 (S14)."""
    with open(path, encoding="utf-8") as fh:
        book = json.load(fh)
    out = []
    for one in book.get("낱말") or ():
        said = str(one.get("말") or "").strip()
        if not said:
            continue
        find = [said, *(one.get("같은말") or ())]
        skip = list(one.get("안_잡을_말") or ())
        out.append((said, find, skip))
    return out


def found_in(text: str, book: list, seller: dict | None = None) -> list:
    """그 글에서 잡힌 하체 낱말.  ★ 「휠하우스」를 「휠」로 세지 않는다.

    ★ `seller` 를 주면 ★ **판매자 글** 잣대를 쓴다 —
      ★ 고침 낱말 옆에 있을 때만 잡고 ★ 「휠」은 안 잡는다 (사전이 그렇게 적었다)
    """
    said = str(text or "")
    if not said:
        return []
    seller = seller or {}
    skip_all = set(seller.get("판매자_글에서_안_잡을_말") or ())
    fixes = list(seller.get("고침_낱말") or ())
    near = int(seller.get("옆_글자수") or 0)
    deny = list(seller.get("아니라고_말하는_꼴") or ())
    got = []
    for name, find, skip in book:
        if name in skip_all:
            continue
        # ★ 안 잡을 말을 ★ 먼저 지운다 — ★ 그래야 짧은 말이 안 걸린다
        room = said
        for bad in skip:
            room = room.replace(bad, " ")
        where = [i for w in find
                 for i in _every(room, w)]
        if not where:
            continue
        if not fixes:
            got.append(name)
            continue
        # ★ 고침 낱말이 ★ **옆에** 있어야 한다 — ★ 자랑과 고침을 가른다
        for i in where:
            room2 = room[max(0, i - near):i + near + len(name)]
            if not any(f in room2 for f in fixes):
                continue
            # ★ 「교체도 **없는**」은 ★ 안 했다는 말이다 — ★ 경고가 아니다
            if any(no in room2 for no in deny):
                continue
            got.append(name)
            break
    return got


def _every(text: str, want: str) -> list:
    """그 말이 나온 자리들."""
    out, at = [], text.find(want)
    while at >= 0:
        out.append(at)
        at = text.find(want, at + 1)
    return out


def run(write: bool = False, db: str = "carwatch.db") -> Counter:
    book = words()
    seller = rule()
    conn = sqlite3.connect(os.path.join(ROOT, db))
    tally: Counter = Counter()
    for lid, text in conn.execute(
            "SELECT listing_id, ad_body_text FROM core_listing"
            " WHERE ad_body_text IS NOT NULL AND ad_body_text <> ''"):
        tally["글을 본 매물"] += 1
        got = found_in(text, book, seller)
        if not got:
            continue
        tally["하체 낱말이 나온 매물"] += 1
        for w in got:
            tally[f"  {w}"] += 1
        if write:
            conn.execute(
                "UPDATE core_listing SET undercarriage_json = ?,"
                "       undercarriage_src = ? WHERE listing_id = ?",
                (json.dumps(got, ensure_ascii=False), SRC_AD, lid))
    if write:
        conn.commit()
    conn.close()
    return tally


if __name__ == "__main__":
    for k, v in sorted(run("--write" in sys.argv).items(),
                       key=lambda x: (-x[1], x[0])):
        print(f"  {k:22} {v:,}")
