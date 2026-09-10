# -*- coding: utf-8 -*-
"""★ 이번 주 과제 — ★ 후보의 **상세 · 성능점검 · 보험**을 받는다 (P-3).

★★★ 마스터 기준을 걸려면 ★ 넷이 있어야 한다 (지시 6-2) —
  ★ ① 진단 코멘트 ② 성능점검 골격랭크 ③ 보험이력 ④ 정비이력.
★★ 실측 09-10 — ★ 조건에 든 141대 중 ★ **골격을 아는 것은 2대**뿐이다.
  ★ 엔카 성능점검·보험은 ★ 서버에서 **407** 이 잦다 — ★ 다만 ★ **늘** 막히지는 않는다.
  ★ ★ 실측 — ★ 같은 자리를 네 번 두드리면 ★ 한두 번은 200 이 온다.
★ 그러니 ★ **값싼 것부터 · 천천히 · 막히면 쉬었다** 이어받는다.
★ 이미 받은 것은 ★ 파일이 있으므로 ★ 건너뛴다 (S46-185 · S46-266).

돌리는 법
    python3.11 tools/week_fetch.py            ★ 값싼 것부터 다 받는다
    python3.11 tools/week_fetch.py --max 40   ★ 마흔 대만
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from store.rawfile import read as raw_read      # noqa: E402
from store.rawfile import save as raw_save      # noqa: E402
from store.rawfile import walk as raw_walk      # noqa: E402

WANT = ("detail", "inspection", "record")
GAP = 2.5                    # ★ 한 번 받고 이만큼 쉰다
TRIES = 2                    # ★ 한 자리를 이만큼 두드린다
# ★★★★★ 09-10 실측 — ★ 조리개가 **완전히 닫히는 때**가 있다.
#   ★ 그때는 ★ 계약하신 차(`42598705`)까지 407 이 난다 — ★ 매물 탓이 아니다.
#   ★ ★ 25분을 두드려 ★ **한 건도 못 받았다.**  ★ 자주 두드리면 더 길어질 뿐이다.
#   ★ 그러니 ★ **물러섰다 받는다** — ★ 이어서 막히면 ★ 쉬는 시간을 늘린다
REST_MIN, REST_MAX = 30.0, 900.0
WALL_ROW = 6                 # ★ 이어서 이만큼 막히면 ★ 크게 쉰다


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def have(site: str = "encar") -> dict:
    """이미 가진 원문 — {창구: {매물번호}}.  ★ 다시 받지 않는다."""
    got: dict = {k: set() for k in WANT}
    for ep in WANT:
        for path in raw_walk(site=site, endpoint=ep, root=ROOT):
            env = raw_read(path) or {}
            if str(env.get("status") or "ok") != "ok":
                continue
            got[ep].add(os.path.basename(path)[:-5])
    return got


def targets(db: str = "carwatch.db", cap: int = 0) -> list:
    """후보 — ★ **값싼 것부터**.  ★ 이기는 차부터 확인해야 뜻이 있다."""
    from report.screens.build import _lease_kinds

    with open(os.path.join(ROOT, "config", "week_task.json"),
              encoding="utf-8") as fh:
        cfg = json.load(fh)["조건"]
    ads, sells = _lease_kinds(ROOT)
    m, m2 = ",".join("?" * len(ads)), ",".join("?" * len(sells))
    conn = sqlite3.connect(os.path.join(ROOT, db))
    got = [r[0] for r in conn.execute(
        "SELECT source_id FROM core_listing"
        " WHERE target_key = 'GV70_25T' AND site = 'encar'"
        "   AND status IN ('active','new','relisted')"
        "   AND price_current_won IS NOT NULL AND price_current_won <= ?"
        "   AND year_month >= ? AND mileage_km <= ?"
        f"   AND COALESCE(advertisement_type,'') NOT IN ({m})"
        f"   AND COALESCE(sell_type,'') NOT IN ({m2})"
        " ORDER BY price_current_won",
        [cfg["차값_최대_원"], cfg["연식_이후"], cfg["주행_최대km"],
         *ads, *sells])]
    conn.close()
    return got[:cap] if cap else got


GONE = os.path.join(ROOT, "outputs", "week_gone.json")


def _mark_gone(sid: str, ep: str) -> None:
    """★ 사이트에서 내려간 매물을 적어 둔다.  ★ 파일이 정본이다."""
    got = gone_book()
    got.setdefault(str(sid), [])
    if ep not in got[str(sid)]:
        got[str(sid)].append(ep)
    tmp = GONE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(got, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, GONE)


def gone_book() -> dict:
    try:
        with open(GONE, encoding="utf-8") as fh:
            return json.load(fh) or {}
    except (OSError, ValueError):
        return {}


def run(cap: int = 0) -> dict:
    with open(os.path.join(ROOT, "config", "endpoints.json"),
              encoding="utf-8") as fh:
        e = json.load(fh)["encar"]
    mine = have()
    ids = targets(cap=cap)
    tally = {"받음": 0, "이미 있다": 0, "사이트에 없다": 0, "막혔다": 0}
    rest, row = REST_MIN, 0
    print(f"★ 후보 {len(ids):,}대 · 창구 {len(WANT)}종", flush=True)
    for n, sid in enumerate(ids, 1):
        for ep in WANT:
            if sid in mine[ep]:
                tally["이미 있다"] += 1
                continue
            url = e["base_url"] + e["paths"][ep].format(source_id=sid)
            for _try in range(TRIES):
                try:
                    req = urllib.request.Request(url, headers=e["headers"])
                    with urllib.request.urlopen(req, timeout=20) as r:
                        body = r.read()
                    raw_save("encar", ep, sid, url,
                             body.decode("utf-8", "replace"), _now(),
                             root=ROOT)
                    tally["받음"] += 1
                    break
                except urllib.error.HTTPError as ex:
                    if ex.code == 404:
                        # ★ 사이트에 없다 — ★ 「못 찾았다」가 아니라 ★ **없다**.
                        #   ★★ 404 와 407 은 다르다 — ★ 407 은 「지금 막혔다」다.
                        #   ★ 이 사실을 ★ **남긴다** — ★ 안 남기면 ★ 내려간 차가
                        #     ★ ★ 다음에도 ★ 「이기는 차」로 올라온다 (실측 09-10)
                        tally["사이트에 없다"] += 1
                        _mark_gone(sid, ep)
                        break
                    time.sleep(rest)
                except OSError:
                    time.sleep(rest)
            else:
                tally["막혔다"] += 1
                row += 1
                if row >= WALL_ROW:
                    rest = min(rest * 2, REST_MAX)
                    row = 0
                    print(f"    ★ 이어서 막힌다 — 쉬는 시간을 {rest:.0f}초로"
                          " 늘린다", flush=True)
                time.sleep(GAP)
                continue
            # ★ 받았으면 ★ 쉬는 시간을 도로 줄인다 — ★ 조리개가 열린 것이다
            row = 0
            rest = max(REST_MIN, rest / 2)
            time.sleep(GAP)
        if n % 10 == 0:
            print(f"    {n}/{len(ids)} … "
                  + " · ".join(f"{k} {v}" for k, v in tally.items()),
                  flush=True)
    print("★ 끝 — " + " · ".join(f"{k} {v:,}" for k, v in tally.items()),
          flush=True)
    return tally


if __name__ == "__main__":
    n = 0
    if "--max" in sys.argv:
        i = sys.argv.index("--max")
        if i + 1 < len(sys.argv) and sys.argv[i + 1].isdigit():
            n = int(sys.argv[i + 1])
    run(n)
