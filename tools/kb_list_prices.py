# -*- coding: utf-8 -*-
"""★ KB 목록으로 ★ **값·트림**을 채운다 (이번 주 과제 P-2 를 돌아가는 길).

★★★ 실측 09-10 — ★ KB 상세는 ★ **열 건마다 막고** 지금은 통째로 잠겼다.
  ★ 그런데 ★ **목록 쪽은 열린다** (301KB · 200 · 한 장에 40대).
  ★ 675번 두드릴 것을 ★ **열일곱 장**으로 끝낸다.
★★ 목록이 주는 것 — ★ `data-ga4` 라는 딱지 안에 JSON 이 들어 있다:
    {"params": {"vehicle_price": "3890만원",
                "vehicle_info": "제네시스 GV70 디젤 2.2 AWD "}}
  ★ ★ 값과 트림 이름이다.  ★ 이것만으로도 ★ **값으로 거를 수 있다**.
★ 연식·주행·색은 ★ 목록이 안 준다 — ★ 그것은 상세가 열릴 때 채운다 (금지 12).

돌리는 법
    python3.11 tools/kb_list_prices.py            ★ 받아 재기만
    python3.11 tools/kb_list_prices.py --write    ★ core_listing 에 넣는다
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
import time
import urllib.request
from collections import Counter
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from store.rawfile import save as raw_save          # noqa: E402

# ★ 매물번호와 ★ 그 딱지를 함께 잡는다 — ★ 둘이 같은 `<a>` 안에 있다
RE_GA4 = re.compile(r'carSeq=(\d+)"[^>]*?data-ga4=\'(\{.*?\})\'', re.S)
RE_WON = re.compile(r"([\d,]+)\s*만원")
# ★★★★★ 09-10 — ★ 목록이 ★ **연식·주행·지역**까지 준다.
#   ★ 실측 — 「21/04식(21년형) ¦ 89,082km ¦ 경기」.
#   ★ 상세가 막혀도 ★ 마스터 조건 ②③ 을 ★ **여기서** 걸 수 있다
RE_YM = re.compile(r"(\d{2})/(\d{2})식")
RE_KM = re.compile(r"([\d,]+)\s*km")
GAP = 5.0


def cards(html: str) -> dict:
    """{매물번호: {값(원), 이름}}.  ★ 못 읽으면 ★ 안 담는다."""
    got: dict = {}
    for sid, blob in RE_GA4.findall(html or ""):
        if sid in got:
            continue
        try:
            said = (json.loads(blob).get("params") or {})
        except (ValueError, TypeError):
            continue
        won = RE_WON.search(str(said.get("vehicle_price") or ""))
        if not won:
            continue
        got[sid] = {"won": int(won.group(1).replace(",", "")) * 10000,
                    "name": str(said.get("vehicle_info") or "").strip()}
    # ★★ 연식·주행은 ★ 딱지가 아니라 ★ **카드 글자**에 있다.
    #   ★ 한 카드에 ★ `carSeq` 가 ★ **다섯 번** 나온다 (숨은 것 · 사진 · 글자…).
    #     ★ ★ 글자는 ★ **마지막 것 뒤**에 있다 (실측 09-10 — 앞 둘에는 없다).
    #   ★ 그래서 ★ 마지막 자리에서 ★ 짧게 읽는다 — ★ 옆 카드까지 넘보지 않게
    where: dict = {}
    for m in re.finditer(r"carSeq=(\d+)", html):
        where[m.group(1)] = m.start()
    for sid in got:
        at = where.get(sid)
        if at is None:
            continue
        card = html[at:at + 900]
        ym = RE_YM.search(card)
        if ym:
            year = 2000 + int(ym.group(1))
            got[sid]["ym"] = f"{year}-{ym.group(2)}"
        km = RE_KM.search(card)
        if km:
            got[sid]["km"] = int(km.group(1).replace(",", ""))
    return got


def from_files() -> dict:
    """★ 이미 받아 둔 목록 원문에서 읽는다 — ★ 다시 안 받는다 (S46-266)."""
    import glob as _g

    got: dict = {}
    for path in sorted(_g.glob(os.path.join(
            ROOT, "raw", "kbchachacha", "list", "*", "gv70-*.json"))):
        from store.rawfile import read as _read

        body = (_read(path) or {}).get("body") or b""
        if isinstance(body, bytes):
            body = body.decode("utf-8", "replace")
        got.update(cards(body))
    return got


def fetch(pages: int = 20) -> dict:
    """GV70 목록을 받는다.  ★ 빈 쪽이 나오면 끝이다."""
    with open(os.path.join(ROOT, "config", "endpoints.json"),
              encoding="utf-8") as fh:
        e = json.load(fh)["kbchachacha"]
    with open(os.path.join(ROOT, "config", "targets.json"),
              encoding="utf-8") as fh:
        q = ((json.load(fh)["GV70_25T"].get("site_query") or {})
             .get("kbchachacha") or {})
    car = (q.get("carCode") or [None])[0]
    got: dict = {}
    for page in range(1, pages + 1):
        url = e["base_url"] + e["paths"]["list_gen"].format(
            page=page, maker=q["makerCode"], klass=q["classCode"], car=car)
        try:
            req = urllib.request.Request(url, headers=e["headers"])
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read().decode("utf-8", "replace")
        except OSError as ex:
            print(f"  {page}쪽 — 못 받았다 ({type(ex).__name__})", flush=True)
            break
        if len(body) < 10000:
            # ★ 「로봇여부 확인」 쪽이다 — ★ 값으로 삼지 않는다
            print(f"  {page}쪽 — 막혔다 ({len(body):,}자)", flush=True)
            break
        raw_save("kbchachacha", "list", f"gv70-{page:04d}", url, body,
                 datetime.now(timezone.utc).isoformat(), root=ROOT)
        one = cards(body)
        print(f"  {page}쪽 — {len(body):,}자 · 값을 읽은 것 {len(one)}",
              flush=True)
        if not one:
            break
        got.update(one)
        time.sleep(GAP)
    return got


def run(write: bool = False, db: str = "carwatch.db",
        again: bool = False) -> Counter:
    got = fetch() if again else (from_files() or fetch())
    conn = sqlite3.connect(os.path.join(ROOT, db))
    mine = {r[0] for r in conn.execute(
        "SELECT source_id FROM core_listing WHERE site = 'kbchachacha'")}
    tally: Counter = Counter()
    tally["목록에서 읽은 것"] = len(got)
    for sid, one in got.items():
        if sid not in mine:
            tally["우리 표에 없는 매물"] += 1
            continue
        tally["값을 넣는다"] += 1
        if write:
            conn.execute(
                "UPDATE core_listing SET price_current_won = ?,"
                "       price_unit = 'won',"
                "       trim_grade_name = COALESCE(?, trim_grade_name),"
                "       year_month = COALESCE(?, year_month),"
                "       mileage_km = COALESCE(?, mileage_km)"
                " WHERE site = 'kbchachacha' AND source_id = ?",
                (one["won"], one["name"] or None, one.get("ym"),
                 one.get("km"), sid))
    if write:
        conn.commit()
    conn.close()
    return tally


if __name__ == "__main__":
    for k, v in sorted(run("--write" in sys.argv,
                            again="--again" in sys.argv).items()):
        print(f"  {k:22} {v:,}")
