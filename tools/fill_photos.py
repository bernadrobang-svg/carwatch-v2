# -*- coding: utf-8 -*-
"""★★★ 이미 받아 둔 원문에서 ★ 사진을 채운다 (명령서 73장).

지시서   명령서 73장 「사진이 60건 중 48건 없다」 · `docs/MULTISITE_MAPPING.md`
근거     ★★ 실측 08-26 — ★ 사진이 있는 사이트는 ★ **엔카 하나**였다.
         ★ ★ 엔카는 ★ **목록 봉투**가 사진을 준다 (`Photo`·`Photos`) —
           ★ 그래서 상세를 안 받아도 사진이 있다 (7,379/7,413).
         ★ ★ KB·K카·리본카는 ★ **상세**에만 있다.  ★ 원문은 이미 받아 두었는데
           ★ 파서가 그 칸을 안 읽었다 — ★ 다시 받지 않고 ★ 여기서 채운다
금지     ★ 사진을 지어내는 것.  ★ 남의 매물 사진을 붙이는 것
         ★ 원문을 다시 받는 것 — ★ `raw_response` 에 이미 있다 (P3 무손실)
사용     python3.11 tools/fill_photos.py            재기만 한다
         python3.11 tools/fill_photos.py --write    채운다
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from parse.kbchachacha.mapping import parse_detail as kb_detail    # noqa: E402
from parse.kcar.mapping import parse_detail as kcar_detail         # noqa: E402
from parse.reborncar.mapping import parse_detail as reborn_detail  # noqa: E402

DB = os.path.join(ROOT, "carwatch.db")


def _photos_of(site: str, sid: str, body: str) -> list:
    """그 사이트 파서가 읽어 낸 사진.  ★ 파서를 두 벌 만들지 않는다."""
    if site == "kbchachacha":
        got = kb_detail(body, site, sid)
    elif site == "kcar":
        try:
            got = kcar_detail(json.loads(body), site, sid)
        except (ValueError, TypeError):
            return []
    elif site == "reborncar":
        got = reborn_detail(body, site, sid)
    else:
        return []
    return json.loads((got or {}).get("photo_list_json") or "[]")


SITES = ("kbchachacha", "kcar", "reborncar")


def main() -> int:
    write = "--write" in sys.argv
    if not os.path.isfile(DB):
        print("[X] carwatch.db 가 없다")
        return 2
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")
    # ★ 매물번호 → 우리 번호.  ★ 사이트마다 따로 잡는다 — 번호가 겹칠 수 있다
    by_sid: dict = {}
    for lid, site, sid, main_photo in conn.execute(
        "SELECT listing_id, site, source_id, photo_main FROM core_listing"
    ):
        by_sid[(site, str(sid))] = (lid, main_photo)

    total = {s: [0, 0, 0] for s in SITES}      # 원문 · 사진찾음 · 채움
    # ★★ 정본은 `source_id` 다 (마스터 지시 08-26 · S46-97).
    #   ★ 주소에서 되뽑지 않는다 — 그것은 임시였고 규격이 아니었다
    for site, sid, body in conn.execute(
        "SELECT site, source_id, body FROM raw_response"
        " WHERE endpoint='detail' AND status='ok' AND body IS NOT NULL"
        " AND source_id IS NOT NULL AND source_id <> ''"
        f" AND site IN ({','.join('?' * len(SITES))})", SITES
    ):
        sid = str(sid)
        total[site][0] += 1
        photos = _photos_of(site, sid, body)
        if not photos:
            continue
        total[site][1] += 1
        hit = by_sid.get((site, sid))
        if not hit:
            continue                 # ★ 원문은 있는데 매물이 없다 — 접혔거나 팔렸다
        lid, had = hit
        if (had or "").strip():
            continue                 # ★ 이미 있다.  ★ 덮어쓰지 않는다
        total[site][2] += 1
        if write:
            conn.execute(
                "UPDATE core_listing SET photo_main=?, photo_list_json=?"
                " WHERE listing_id=?",
                (photos[0], json.dumps(photos, ensure_ascii=False), lid))
    if write:
        conn.commit()

    print("★ 이미 받아 둔 상세에서 사진을 채운다 (명령서 73장)")
    print("  %-14s %8s %10s %8s" % ("site", "상세원문", "사진 찾음", "채울 것"))
    for site in SITES:
        got = total[site]
        print("  %-14s %8d %10d %8d" % (site, got[0], got[1], got[2]))
    print("  ★ --write 없이는 재기만 한다" if not write else "  ★ 채웠다")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
