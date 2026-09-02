"""사이트에 몇 대인데 ★ 우리가 몇 대 받았나 — ★ 이걸 아무도 안 셌다.

★★★ 09-02 마스터 지적 —
  「★ 내가 선정한 차종이 안 들어오는 것을 ★ 너나 개발놈들이 ★ 제대로 수집 검증을 안 한 거야.
   ★ 목록이 제대로 뽑히는지부터 ★ 차종들의 호출 쿼리가 정상인 건지」
  「★ 다른 모든 사이트도 그럴 거야 ★ 전수 검사해」

★ 실측 09-02 — ★ KB차차차 ★ **6,261대 중 589대(9.4%)** 만 들고 있었다.
  ★ ★ 대상 **29종 중 26종이 0건**이었다 — ★ GV70 전동화 23 · iX3 22 · C40 2 가 ★ 다 0 이다.
  ★ ★ ★ 그런데 ★ **호출 쿼리는 정상**이었다 (`carCode=9999` → 0건 · `3077` → 1,801건).
    ★ 쪽넘김도 45쪽까지 다 나온다.  ★ **사이트는 다 준다.  ★ 우리가 안 받았다.**

★ `S5` 는 ★ 「두드린 수 vs 응답 수」만 본다 — ★ 「저기 몇 대인가」를 ★ 안 센다.
  ★ ★ 그래서 ★ **90%를 놓치고도 판이 「성공」으로 끝난다**.

돌리기   python3 tools/site_coverage.py            (다 센다)
         python3 tools/site_coverage.py kbchachacha
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs", "site_coverage.json")
PAGE_CAP = 200          # ★ 안전장치.  ★ 여기 걸리면 「못 쟀다」로 적는다
SLEEP = 0.6


def _cfg(name: str) -> dict:
    with open(os.path.join(ROOT, "config", name), encoding="utf-8") as f:
        return json.load(f)


def _get(url: str, headers: dict, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return res.read().decode("utf-8", "replace")


# ── 사이트마다 ★ 「한 쪽에 몇 건인가」를 세는 법이 다르다 ────────────────
def _count_kb(ep: dict, q: dict, page: int) -> int:
    url = (ep["base_url"] + "/public/search/list.empty?page=%d&makerCode=%s"
           % (page, q["makerCode"]))
    if q.get("classCode"):
        url += "&classCode=%s" % q["classCode"]
    if q.get("_car"):
        url += "&carCode=%s" % q["_car"]
    return len(set(re.findall(r"carSeq=(\d+)", _get(url, ep.get("headers") or {}))))


def _count_revolt(ep: dict, _q: dict, page: int) -> int:
    body = _get(ep["base_url"] + "/cars/?page=%d" % page, ep.get("headers") or {})
    data = json.loads(body)
    return len(data) if isinstance(data, list) else len(data.get("results") or [])


COUNTERS = {"kbchachacha": _count_kb, "revolt": _count_revolt}

# ★ 한 번에 수를 주는 곳 — ★ 쪽을 안 넘겨도 된다
TOTAL_FIELD = {
    "kia_cpo": ("/api/search/?size=1", r'"totalElements"\s*:\s*(\d+)'),
    "lexus_certified": ("/api/json/getList_search.json.php"
                        "?price_area_min=0&price_area_max=9999",
                        r'"total_list_num"\s*:\s*"?(\d+)'),
}


def total_by_paging(site: str, ep: dict, q: dict) -> int | str:
    """★ 빈 쪽이 나올 때까지 센다.  ★ 두 배씩 뛰고 반씩 좁힌다."""
    fn = COUNTERS[site]
    if fn(ep, q, 1) == 0:
        return 0
    lo, hi = 1, 1
    while fn(ep, q, hi) > 0:
        lo, hi = hi, hi * 2
        if hi > PAGE_CAP:
            return "못 쟀다 — 쪽 상한"
        time.sleep(SLEEP)
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if fn(ep, q, mid) > 0:
            lo = mid
        else:
            hi = mid
        time.sleep(SLEEP)
    per = fn(ep, q, 1)
    return (lo - 1) * per + fn(ep, q, lo)


def total_by_field(site: str, ep: dict) -> int | str:
    path, pat = TOTAL_FIELD[site]
    try:
        m = re.search(pat, _get(ep["base_url"] + path, ep.get("headers") or {}))
        return int(m.group(1)) if m else "못 쟀다 — 수 필드 없음"
    except Exception as exc:  # noqa: BLE001
        return f"못 쟀다 — {type(exc).__name__}"


def run(only: str | None = None) -> dict:
    eps = _cfg("endpoints.json")
    eps = eps.get("sites", eps)
    targets = _cfg("targets.json")
    res: dict = {}
    for site in sorted(set(list(COUNTERS) + list(TOTAL_FIELD))):
        if only and site != only:
            continue
        ep = eps.get(site) or {}
        if not ep.get("base_url"):
            res[site] = {"_": "못 쟀다 — endpoints 에 없다"}
            continue
        if site in TOTAL_FIELD:
            res[site] = {"_전체": total_by_field(site, ep)}
            print(f"{site:<16} 전체 {res[site]['_전체']}", flush=True)
            continue
        per: dict = {}
        for key, val in targets.items():
            if not isinstance(val, dict):
                continue
            q = (val.get("site_query") or {}).get(site)
            if not isinstance(q, dict) or not q.get("makerCode"):
                if site == "revolt" and q:
                    q = {}
                else:
                    continue
            cars = q.get("carCode")
            cars = [cars] if isinstance(cars, str) else (cars or [None])
            got = 0
            for car in cars:
                qq = dict(q)
                qq["_car"] = car
                try:
                    n = total_by_paging(site, ep, qq)
                except Exception as exc:  # noqa: BLE001
                    n = f"못 쟀다 — {type(exc).__name__}"
                if isinstance(n, int):
                    got += n
                else:
                    got = n
                    break
                time.sleep(SLEEP)
            per[key] = got
            print(f"{site:<16}{key:<16}{got}", flush=True)
            if site == "revolt":
                break          # ★ 리볼트는 차종별로 안 걸린다 — 전체만 센다
        res[site] = per
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print("\n적었다:", OUT)
    return res


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else None)
