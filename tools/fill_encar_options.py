# -*- coding: utf-8 -*-
"""★ 엔카 옵션 **이름**을 사전에 채운다 (`catalog` 창구가 준다).

★★★ 09-11 실측 — ★ 엔카 옵션은 ★ 상세에 **숫자 코드**로만 온다 (`["1051","1055"]`).
  ★ `dict_option_code` 에 이름이 ★ **153개 중 3개**뿐이라 ★ 코드를 못 풀었다.
  ★ ★ 그래서 ★ 「파퓰러 패키지Ⅰ 이상인가」·「HUD 가 있나」를 ★ **못 읽었다**.
★★ 그런데 ★ `raw/encar/catalog/` 가 ★ **코드 ↔ 이름 ↔ 정가**를 준다:
    {"optionCd": "1040", "optionName": "파노라마 선루프", "price": 140}
  ★ 731장이 쌓여 있는데 ★ **아무도 안 읽고 있었다.**
★ 정가(만원)도 함께 담는다 — ★ M-1 의 옵션값에도 쓰인다

돌리는 법
    python3.11 tools/fill_encar_options.py            ★ 잰다
    python3.11 tools/fill_encar_options.py --write    ★ 넣는다
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

from store.rawfile import read                       # noqa: E402

SITE = "encar"


def _now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def book(root: str = ROOT) -> dict:
    """{코드: (이름, 정가만원)}.  ★ 여러 장에 같은 코드가 있으면 ★ 같은 값이다."""
    got: dict = {}
    for path in glob.glob(os.path.join(root, "raw", SITE, "catalog",
                                       "*", "*.json")):
        body = (read(path) or {}).get("body") or b""
        if isinstance(body, bytes):
            body = body.decode("utf-8", "replace")
        try:
            rows = json.loads(body)
        except ValueError:
            continue
        if not isinstance(rows, list):
            continue
        for one in rows:
            if not isinstance(one, dict):
                continue
            code = str(one.get("optionCd") or "").strip()
            name = str(one.get("optionName") or "").strip()
            if not code or not name:
                continue
            got.setdefault(code, (name, one.get("price")))
    return got


def run(write: bool = False, db: str = "carwatch.db") -> Counter:
    got = book()
    conn = sqlite3.connect(os.path.join(ROOT, db))
    # ★ 열쇠가 ★ (site, target_key, code) 다 — ★ 차종을 안 가리는 것은 `*` 다
    #   ★ 카탈로그는 ★ 차종별로 오지만 ★ 코드는 ★ 엔카 안에서 하나다 (실측 09-11)
    tally: Counter = Counter({"카탈로그가 준 코드": len(got)})
    have = {r[0] for r in conn.execute(
        "SELECT code FROM dict_option_code WHERE site = ?", (SITE,))}
    for code, (name, price) in sorted(got.items()):
        if code in have:
            tally["이미 있다 — 이름·정가를 고친다"] += 1
            if write:
                # ★ 09-11 (M-7) — ★ **정가도 넣는다.**
                #   ★ 앞서는 이름만 고쳐 ★ 「옵션값 400만 이상」을 못 쟀다
                conn.execute(
                    "UPDATE dict_option_code SET display = ?,"
                    "       price_manwon = COALESCE(?, price_manwon)"
                    " WHERE site = ? AND code = ?",
                    (name, int(price) if price else None, SITE, code))
            continue
        tally["새로 넣는다"] += 1
        if write:
            # ★ 이 표는 ★ 칸 넷이 ★ NOT NULL 이다 — ★ 있는 줄과 같은 꼴로 넣는다.
            #   ★ `status='confirmed'` — ★ 사이트가 제 카탈로그로 준 이름이다.
            #     ★ ★ 짐작이 아니다 (S46-161 「안 준다에 증거가 있는가」)
            use = {"site": SITE, "target_key": "*", "code": code,
                   "display": name, "price_manwon": int(price) if price
                   else None, "status": "confirmed",
                   "dict_version": "d1", "count_seen": 1,
                   "first_seen": _now(), "last_seen": _now()}
            keys = ",".join(use)
            marks = ",".join("?" * len(use))
            conn.execute(
                f"INSERT OR REPLACE INTO dict_option_code ({keys})"
                f" VALUES ({marks})", list(use.values()))
    if write:
        conn.commit()
    conn.close()
    return tally


if __name__ == "__main__":
    for k, v in sorted(run("--write" in sys.argv).items()):
        print(f"  {k:26} {v:,}")
