# -*- coding: utf-8 -*-
"""★ M-3 — ★ KB 상세 원문에서 ★ **골격(프레임)·외판** 을 집는다 (지시 r1232).

★★★ 마스터 09-12 — 「★ 성능 정보도 없는 것들을 상위에 집어넣는다」.
★ 1단계(「있어야 보인다」)를 막는 ★ **가장 큰 구멍**이 골격이다 —
  ★ 실측 09-13 — GV70 2.5T 1,639대 중 ★ 골격을 아는 것이 ★ **70대**뿐이다.
★★ 엔카 성능점검은 서버에서 부르면 ★ **407** 이다 (규격 08-23).
  ★ 그런데 ★ KB 상세는 ★ 제 쪽에서 ★ **차마다** 이렇게 적는다 —

      <div id="diagResultFrame">프레임 <strong class="blue">정상</strong></div>
      <div id="diagResultPanel">외부패널 <strong class="blue">정상</strong></div>
      <p class="txt ...">345가1625 차량의 진단 결과 <span>무사고 차량</span>입니다</p>

  ★ 번호판이 함께 나오므로 ★ **차마다 다른 값**이다.

★★★ 안 쓰는 것 — ★ 「해당 차량은 프레임 정상과 외부패널 정상을 진단받은…」 문장.
  ★ 실측 — ★ 원문 1,330개 중 ★ **704개에 글자 그대로 같이** 들어 있다.
  ★ 그것은 ★ **안내 문구**지 ★ 그 차의 값이 아니다.
  ★ ★ 안내 문구를 값으로 삼으면 ★ 「없다」와 「안 봤다」를 섞는 것이다 (금지 12)

★★ 못 집으면 ★ **비운다.**  ★ 0 으로 두지 않는다 —
  ★ KB 는 ★ 프레임이 정상이 아니면 ★ 진단차로 안 올린다고 ★ 제 쪽에서 밝힌다.
  ★ ★ 그러니 ★ 「진단표가 없다」는 ★ 「무사고다」가 **아니다**

돌리는 법
    python3.11 tools/fill_kb_frame.py            ★ 잰다
    python3.11 tools/fill_kb_frame.py --write    ★ 넣는다
"""
from __future__ import annotations

import glob
import json
import os
import re
import sqlite3
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from store.rawfile import read           # noqa: E402

# ★ `id` 로 집는다 — ★ 안내 문구에는 이 `id` 가 없다
FRAME = re.compile(r'id="diagResultFrame"[^>]*>\s*프레임\s*<[^>]+>([가-힣]{2,8})<')
PANEL = re.compile(r'id="diagResultPanel"[^>]*>\s*외부패널\s*<[^>]+>([가-힣]{2,8})<')
OK = "정상"


def book(root: str = ROOT) -> dict:
    """{source_id: (프레임말, 외판말)}.  ★ 진단표가 없으면 안 담는다."""
    got: dict = {}
    for path in glob.glob(os.path.join(root, "raw/kbchachacha/detail/*/*.json")):
        env = read(path)
        body = (env or {}).get("body") or b""
        if isinstance(body, bytes):
            body = body.decode("utf-8", "replace")
        f, p = FRAME.search(body), PANEL.search(body)
        if not f:
            continue
        got[os.path.basename(path)[:-len(".json")]] = (
            f.group(1), p.group(1) if p else None)
    return got


def run(write: bool = False, db: str = "carwatch.db") -> Counter:
    got = Counter()
    said = book()
    conn = sqlite3.connect(os.path.join(ROOT, db))
    rows = conn.execute(
        "SELECT listing_id, source_id, accident_frame_cnt FROM core_listing"
        " WHERE site = 'kbchachacha'").fetchall()
    for lid, sid, had in rows:
        pair = said.get(str(sid))
        if not pair:
            got["진단표가 없다 — 비워 둔다"] += 1
            continue
        frame, panel = pair
        # ★ 「정상」이면 0.  ★ 아니면 ★ **몇 곳인지는 모른다** — ★ 1 로 적고
        #   ★ 부위명에 ★ 원문 낱말을 그대로 남긴다 (지어내지 않는다 · 금지 6)
        cnt = 0 if frame == OK else 1
        parts = json.dumps(
            {"골격": frame, "외판": panel, "출처": "kb 진단표"},
            ensure_ascii=False)
        if had is not None and had == cnt:
            got["이미 같다"] += 1
            continue
        if write:
            conn.execute(
                "UPDATE core_listing SET accident_frame_cnt = ?,"
                " accident_parts_json = COALESCE(accident_parts_json, ?)"
                " WHERE listing_id = ?", (cnt, parts, lid))
        got["채움 — 골격 무사고" if not cnt else "채움 — 골격 상함"] += 1
    if write:
        conn.commit()
    conn.close()
    return got


if __name__ == "__main__":
    for k, v in sorted(run("--write" in sys.argv).items()):
        print(f"  {k:24} {v:>8,}")
