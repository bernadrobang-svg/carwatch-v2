# -*- coding: utf-8 -*-
"""★ 「없다」인가 ★ **안내문**인가 — ★ 사이트마다 상세 응답 크기를 잰다 (r1190 ③).

★★★ 가이드 실측 09-06 — ★ K카 상세가 ★ 「데이터가 하나도 없다」가 아니라
  ★ ★ **팔린 차의 3.6KB 안내문**이었다.  ★ `success` 가 `true` 로 와서
  ★ ★ ★ 성공한 줄 알고 ★ 「없다」로 본 것이다.
★ 그러므로 ★ **크기로 가른다** — ★ 200 이라고 다 받은 것이 아니다.
★★ 「못 찾았다」와 「없다」는 다르다 (`S46-184` · `S46-256`).

돌리는 법   python3.11 tools/thin_detail_report.py
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from report.screens.build import load_config   # noqa: E402
from store.rawfile import read, walk           # noqa: E402

REPORT = "outputs/thin_detail.json"
# ★ 「안내문」으로 볼 크기.  ★ 사이트마다 다르다 — ★ `config/endpoints.json` 이 정본이다.
#   ★ 없으면 이 값을 쓴다 (K카 실측 — 안내문 3.6KB · 참 상세 80~114KB)
FALLBACK_MIN = 6000
# ★ 팔린 차 안내문에 나오는 말.  ★ 크기와 ★ **함께** 봐야 한다 — 하나만으로 굳히지 않는다
SOLD_WORDS = ("판매완료", "판매 완료", "삭제된", "존재하지 않")


def _min_bytes(site: str, root: str = ".") -> int:
    got = (load_config(f"{root}/config/endpoints.json") or {}).get(site) or {}
    return int(got.get("min_detail_bytes") or FALLBACK_MIN)


def run(root: str = ROOT) -> dict:
    out: dict = {}
    base = os.path.join(root, "raw")
    for site in sorted(os.listdir(base)) if os.path.isdir(base) else []:
        if not os.path.isdir(os.path.join(base, site, "detail")):
            continue
        cut = _min_bytes(site, root)
        tally: Counter = Counter()
        for path in walk(site=site, endpoint="detail", root=root):
            body = (read(path) or {}).get("body") or ""
            n = len(body)
            tally["전체"] += 1
            if n < cut:
                tally["안내문(작다)"] += 1
                if any(w in body for w in SOLD_WORDS):
                    tally["  그중 팔린 차"] += 1
            else:
                tally["참 상세"] += 1
            tally["글자 합"] += n
        if tally["전체"]:
            tally["평균 글자"] = tally["글자 합"] // tally["전체"]
            del tally["글자 합"]
            out[site] = {"기준": cut, **dict(tally)}
    with open(os.path.join(root, REPORT), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    return out


if __name__ == "__main__":
    for site, got in run().items():
        thin = got.get("안내문(작다)", 0)
        print(f"  {site:16} 전체 {got['전체']:>6,} · 참 상세 {got.get('참 상세', 0):>6,}"
              f" · 안내문 {thin:>5,} (그중 팔린 차 {got.get('  그중 팔린 차', 0):,})"
              f" · 평균 {got['평균 글자']:,}B")
