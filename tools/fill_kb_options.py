# -*- coding: utf-8 -*-
"""★ KB 상세 원문에서 ★ **주요옵션**을 집는다 (지시 r1232 1단계).

★★★ 마스터 09-12 — 「★ **옵션 정보도 하나도 없고** ★ 신차 가격도 없고
  ★ 성능 정보도 없는 것들을 ★ 상위에 집어넣는다」.
★ 실측 09-13 — GV70 2.5T 중 ★ KB 상세를 받은 것이 **482대**인데
  ★ ★ 그중 옵션을 읽은 것이 ★ **0대**였다.  ★ 원문에는 있었는데 ★ 안 읽고 있었다.

★ 원문 꼴
    <ul class="car-option-list ...">
      <li class="option1"><span class="text">내비게이션 <br /> (순정)</span></li>
      <li class="option2"><span class="text">선루프 <br /> (파노라마)</span></li>

★★ 엔카와 ★ **같은 것이 아니다** — ★ 엔카는 ★ 선택옵션 **코드＋정가**를 주고
  ★ KB 는 ★ **주요옵션 이름**만 준다 (정가가 없다).
  ★ 그래서 ★ 값 안에 ★ `"출처": "kb 주요옵션"` 을 ★ 함께 적는다 —
  ★ ★ 뒤에 보는 사람이 ★ 둘을 섞지 않도록.
★★★ 옵션**값**은 ★ 이것으로 재지 않는다 — ★ 옵션값은 ★ 신차출고가 − 신차정가다
  ★ (가이드 답 09-12).  ★ 여기서 하는 일은 ★ 「옵션을 봤다」를 남기는 것뿐이다

돌리는 법
    python3.11 tools/fill_kb_options.py            ★ 잰다
    python3.11 tools/fill_kb_options.py --write    ★ 넣는다
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

LIST = re.compile(r'<ul class="car-option-list[^"]*">(.*?)</ul>', re.S)
ITEM = re.compile(r'<li class="option\d+[^"]*">\s*<span class="text">(.*?)</span>',
                  re.S)


def _clean(chunk: str) -> str:
    """<br/> 와 빈칸을 걷어 ★ 「선루프 (파노라마)」 한 줄로."""
    got = re.sub(r"<[^>]+>", " ", chunk)
    return " ".join(got.split())


def book(root: str = ROOT) -> dict:
    got: dict = {}
    for path in glob.glob(os.path.join(root, "raw/kbchachacha/detail/*/*.json")):
        env = read(path)
        body = (env or {}).get("body") or b""
        if isinstance(body, bytes):
            body = body.decode("utf-8", "replace")
        block = LIST.search(body)
        if not block:
            continue
        names = [_clean(x) for x in ITEM.findall(block.group(1))]
        names = [x for x in names if x]
        if names:
            got[os.path.basename(path)[:-len(".json")]] = names
    return got


def run(write: bool = False, db: str = "carwatch.db") -> Counter:
    got = Counter()
    said = book()
    conn = sqlite3.connect(os.path.join(ROOT, db))
    rows = conn.execute(
        "SELECT listing_id, source_id, options_choice_json FROM core_listing"
        " WHERE site = 'kbchachacha'").fetchall()
    for lid, sid, had in rows:
        names = said.get(str(sid))
        if not names:
            got["원문에 옵션 칸이 없다 — 비워 둔다"] += 1
            continue
        if had:
            got["이미 있다"] += 1
            continue
        if write:
            conn.execute(
                "UPDATE core_listing SET options_choice_json = ?"
                " WHERE listing_id = ?",
                (json.dumps({"출처": "kb 주요옵션", "이름": names},
                            ensure_ascii=False), lid))
        got[f"채움 — 옵션 {len(names)}가지"] += 1
    if write:
        conn.commit()
    conn.close()
    return got


if __name__ == "__main__":
    out = run("--write" in sys.argv)
    keep = Counter()
    for k, v in out.items():
        keep["채움" if k.startswith("채움") else k] += v
    for k, v in sorted(keep.items()):
        print(f"  {k:28} {v:>8,}")
