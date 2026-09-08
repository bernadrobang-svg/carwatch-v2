# -*- coding: utf-8 -*-
"""탭 3 후보의 상세를 ★ **서버가** 받는다 (지시 r1206 L-1 ~ L-2).

★★★ 마스터 — 「★ **내가 안 받을 거야**」.  ★ `/fetch`(마스터 회선)는 쓰지 않는다.
★ 실측 09-07 — ★ 상세 `vehicle/{id}` 는 ★ 데이터센터 IP 에서도 ★ **5번 중 3번** 열린다.
★★ L-2 — ★ 407 이 나면 ★ **그 건만 건너뛰고 다음으로.**  ★ 한 바퀴 돈 뒤 다시.
  ★ ★ 한 자리에서 기다리지 않는다 — ★ 60초 쉬면 한 바퀴가 몇 시간이 된다.
★ 조건은 ★ `config/web.json` `tab3_candidate` 가 정본이다 (`S14`).
★ 이미 있는 것은 ★ 파일을 보고 건너뛴다 (`have_ok` · `V2-20` 과 같은 잣대).

돌리는 법
    python3.11 tools/fetch_candidate_details.py            ★ 잰다
    python3.11 tools/fetch_candidate_details.py --write [초]  ★ 받는다
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from report.screens.fetch import _parse_into  # noqa: E402
from store.rawfile import have_ok, save       # noqa: E402

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
      " (KHTML, like Gecko) Chrome/126.0 Safari/537.36")
DONE = ("ok", "not_found")


def _cfg(name: str) -> dict:
    with open(os.path.join(ROOT, "config", name), encoding="utf-8") as f:
        return json.load(f)


def candidates(conn: sqlite3.Connection) -> list:
    """★ 색은 안 건다 — ★ 마스터께서 흰색만 보시는 것이 아니다 (M 기준 일곱).

    ★ 값·연식·주행 셋으로 좁힌다.  ★ 리스·렌트는 뺀다 (M-13)
    """
    cfg = (_cfg("web.json") or {}).get("tab3_candidate") or {}
    sites = list(cfg.get("sites") or ())
    marks = ",".join("?" * len(sites))
    return [(r[0], str(r[1])) for r in conn.execute(
        "SELECT listing_id, source_id FROM core_listing"
        f" WHERE target_key = ? AND site IN ({marks})"
        "   AND status IN ('active','new','relisted')"
        "   AND price_current_won <= ? AND year_month >= ?"
        "   AND mileage_km < ?"
        "   AND COALESCE(advertisement_type,'') NOT IN"
        "       ('OPERATING_LEASE','FINANCING_LEASE','RENT_CAR','RENT_SUCCESSION')"
        "   AND COALESCE(sell_type,'') NOT IN ('렌트','리스')"
        "   AND (detail_status IS NULL OR detail_status NOT IN ('ok','not_found'))"
        " ORDER BY price_current_won",
        (cfg.get("target"), *sites, cfg.get("price_grace_won"),
         cfg.get("year_from"), cfg.get("mileage_max_km")))]


def _one(url: str) -> tuple:
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept": "application/json",
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Referer": "https://fem.encar.com/"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except OSError:
        return 0, ""


def run(write: bool = False, limit_sec: int = 1800) -> Counter:
    conn = sqlite3.connect(os.path.join(ROOT, "carwatch.db"))
    enc = (_cfg("endpoints.json") or {}).get("encar") or {}
    base = str(enc.get("base_url") or "").rstrip("/")
    path = (enc.get("paths") or {}).get("detail") or ""
    gap = float(enc.get("interval_sec", [0.3, 0.3])[0])
    files = have_ok("encar", "detail", ROOT)
    todo = [(lid, sid) for lid, sid in candidates(conn) if sid not in files]
    tally: Counter = Counter({"대상": len(todo)})
    print(f"★ 후보 중 상세 없는 것 {len(todo):,}대", flush=True)
    if not write or not base or not path:
        return tally
    t0 = time.time()
    lap = 0
    while todo and time.time() - t0 < limit_sec:
        lap += 1
        again = []
        for lid, sid in todo:
            if time.time() - t0 >= limit_sec:
                again.append((lid, sid))
                continue
            code, body = _one(base + path.format(source_id=sid))
            if code == 200 and len(body) > 100:
                save("encar", "detail", sid, base + path.format(source_id=sid),
                     body, http_code=200, status="ok", origin="collector",
                     root=ROOT)
                conn.execute(
                    "UPDATE core_listing SET detail_status='ok'"
                    " WHERE listing_id=?", (lid,))
                conn.commit()
                _parse_into(conn, "encar", "detail", sid, body, ROOT)
                tally["받음"] += 1
            elif code == 404:
                conn.execute(
                    "UPDATE core_listing SET detail_status='not_found'"
                    " WHERE listing_id=?", (lid,))
                conn.commit()
                tally["팔린 차"] += 1
            else:
                # ★ L-2 — ★ **그 건만 건너뛰고 다음으로.**  ★ 한 바퀴 뒤 다시
                again.append((lid, sid))
                tally[f"막힘 {code}"] += 1
            time.sleep(gap)
        print(f"  {lap}바퀴 — 받음 {tally['받음']} · 남은 {len(again)}"
              f" · {round(time.time() - t0)}초", flush=True)
        if len(again) == len(todo):
            time.sleep(30)      # ★ 한 바퀴에 하나도 못 받았다 — 잠깐 쉰다
        todo = again
    tally["남은"] = len(todo)
    conn.close()
    return tally


if __name__ == "__main__":
    secs = next((int(a) for a in sys.argv[1:] if a.isdigit()), 1800)
    for k, v in run("--write" in sys.argv, secs).items():
        print(f"  {k:12} {v:,}")
