# -*- coding: utf-8 -*-
"""★ M-3 — **교환 · 판금 · 골격**을 갈라 저장하고 ★ 부위명을 낸다 (지시 r1213).

★★★ 마스터 기준 — 「★ **단순교환까지**.  ★ 골격에 안 갔으면 통과」.
  ★ 지금 화면이 ★ 「사고 미조회」라 ★ 그 기준을 걸 수 없다.
★ 자료는 ★ 이미 있다 — ★ `core_inspection.inspection_panel_json` 에
  ★ 부위명·상태(`X` 교환 · `W` 판금)·랭크(외판 1·2 · 주요골격 A·B·C)가 다 온다.
★ 부호는 ★ `config/dictionaries/panel_rank.json` 이 정본이다 — ★ 코드에 안 박는다.
★★ 점검부를 못 받았으면 ★ **비운다** — ★ 0 은 「없다」이지 「모른다」가 아니다 (금지 12)

돌리는 법
    python3.11 tools/fill_accident_parts.py            ★ 잰다
    python3.11 tools/fill_accident_parts.py --write    ★ 넣는다
"""
from __future__ import annotations

import glob
import json
import os
import sqlite3
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from store.rawfile import read as rawread          # noqa: E402

DICT = os.path.join(ROOT, "config", "dictionaries", "panel_rank.json")


def _book() -> tuple:
    with open(DICT, encoding="utf-8") as f:
        d = json.load(f)
    return d.get("상태") or {}, d.get("랭크") or {}


def split_panels(panels, state_book: dict, rank_book: dict) -> dict | None:
    """부위 목록 → 교환 · 판금 · 골격 · 부위명.

    ★ 목록이 ★ **빈 것**은 ★ 「상한 자리가 없다」다 — ★ 0 이 맞다 (확인된 사실).
    ★ 목록 자체가 ★ 없으면 ★ `None` 이다 — ★ 「모른다」다
    """
    if panels is None:
        return None
    swap = weld = frame = 0
    parts = []
    for one in panels:
        if not isinstance(one, dict):
            continue
        name = str(((one.get("type") or {}).get("title") or "")).strip()
        kinds = {str((s or {}).get("code") or "")
                 for s in (one.get("statusTypes") or [])}
        is_frame = any((rank_book.get(str(a)) or {}).get("골격")
                       for a in (one.get("attributes") or []))
        said = None
        for code in kinds:
            got = state_book.get(code)
            if not got:
                continue
            if got.get("갈래") == "swap":
                swap += 1
            else:
                weld += 1
            said = got.get("말")
        if said is None:
            continue
        if is_frame:
            frame += 1
        parts.append({"part": name or "이름 미조회", "kind": said,
                      "frame": bool(is_frame)})
    return {"swap": swap, "weld": weld, "frame": frame, "parts": parts}


def raw_panels(root: str = ROOT) -> dict:
    """★ 원문이 ★ **정본**이다 (S46-185) — {(사이트, 사이트열쇠): outers}.

    ★★ 실측 09-10 — ★ 점검 원문 9,969건에 `outers` 칸이 있는데
      ★ ★ DB 점검부에 자리 목록이 안 들어간 것이 ★ **17건** 있었다.
    ★ 그 17건을 ★ 원문에서 되찾는다.  ★ `outers` 가 ★ **빈 목록**이면
      ★ ★ 그것은 ★ 「모른다」가 아니라 ★ **「무사고」**다 (금지 12 의 반대쪽)
    """
    got: dict = {}
    for path in glob.glob(os.path.join(root, "raw/encar/inspection/*/*.json")):
        env = rawread(path)
        body = (env or {}).get("body") or b""
        if isinstance(body, str):
            body = body.encode("utf-8", "replace")
        if len(body) < 2000:
            continue
        try:
            said = json.loads(body)
        except ValueError:
            continue
        if "outers" not in said:
            continue
        got[os.path.basename(path)[:-5]] = said.get("outers") or []
    return got


def run(write: bool = False, db: str = "carwatch.db") -> Counter:
    state_book, rank_book = _book()
    conn = sqlite3.connect(os.path.join(ROOT, db))
    back = raw_panels()
    where = {r[0]: r[1] for r in conn.execute(
        "SELECT listing_id, source_id FROM core_listing WHERE site = 'encar'")}
    tally: Counter = Counter()
    for lid, raw in conn.execute(
            "SELECT listing_id, inspection_panel_json FROM core_inspection"):
        if raw is None:
            # ★ 점검부가 비었어도 ★ **원문**에 있으면 그것을 쓴다
            said = back.get(where.get(lid))
            if said is None:
                tally["점검부에도 원문에도 자리 목록이 없다"] += 1
                continue
            raw = json.dumps(said, ensure_ascii=False)
            tally["원문에서 되찾음"] += 1
        try:
            panels = json.loads(raw)
        except (ValueError, TypeError):
            tally["못 읽음"] += 1
            continue
        got = split_panels(panels, state_book, rank_book)
        if got is None:
            tally["모른다"] += 1
            continue
        tally["무사고" if not got["parts"] else
              ("골격 상함" if got["frame"] else "단순교환·판금")] += 1
        if write:
            conn.execute(
                "UPDATE core_listing SET accident_swap_cnt = ?,"
                " accident_weld_cnt = ?, accident_frame_cnt = ?,"
                " accident_parts_json = ? WHERE listing_id = ?",
                (got["swap"], got["weld"], got["frame"],
                 json.dumps(got["parts"], ensure_ascii=False), lid))
    # ★★ 점검부 **줄 자체가 없는** 매물 — ★ 원문에는 있다.
    #   ★ 위 되돌이는 `core_inspection` 을 훑으므로 ★ 이것들을 못 본다
    seen = {r[0] for r in conn.execute(
        "SELECT listing_id FROM core_inspection")}
    for lid, sid in where.items():
        if lid in seen or sid not in back:
            continue
        got = split_panels(back[sid], state_book, rank_book)
        if got is None:
            continue
        tally["점검부 줄이 없어 원문에서 되찾음"] += 1
        tally["무사고" if not got["parts"] else
              ("골격 상함" if got["frame"] else "단순교환·판금")] += 1
        if write:
            conn.execute(
                "UPDATE core_listing SET accident_swap_cnt = ?,"
                " accident_weld_cnt = ?, accident_frame_cnt = ?,"
                " accident_parts_json = ? WHERE listing_id = ?",
                (got["swap"], got["weld"], got["frame"],
                 json.dumps(got["parts"], ensure_ascii=False), lid))
    if write:
        conn.commit()
    conn.close()
    return tally


if __name__ == "__main__":
    for k, v in sorted(run("--write" in sys.argv).items()):
        print(f"  {k:22} {v:,}")
