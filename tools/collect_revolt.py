# -*- coding: utf-8 -*-
"""리볼트 수집 (규격 `docs/REVOLT_API.md` · 마스터 확정 09-01 · `S46-200`).

★★★ 마스터 — 「★ **보배를 빼고 여기 것 쓰자 ★ 지금 우선 작업으로.
  ★ 하고 빨리 수집하고 ★ 화면도 만들고 빨리**」

★ 전체 220건 (한 쪽 20건 × 11쪽) · ★ 전건 전기·수소 · ★ 전건 무사고
★★ 금지 — ★ `App-Os`·`App-Type`·`App-Version` 헤더 (**500**)
★★ 금지 — ★ 몰아쳐 부르기 (**500**).  ★ 사이를 둔다

★★★★★ 09-01 마스터 지시 — ★ **받기 걸음은 파일만 쓴다.  ★ DB 를 안 연다.**
  ★ 자리 — `raw/{site}/{endpoint}/{YYYY-MM-DD}/{source_id}.json`
  ★       `raw/{site}/{endpoint}/{YYYY-MM-DD}/page-{NNNN}.json`  ← 목록
  ★★ 넣기는 ★ **`tools/load_raw.py`** 가 한다 — ★ 그것이 DB 를 여는 유일한 자리다
  ★ ★ 까닭 — ★ 실측 09-01.  ★ 내가 한 건마다 DB 에 쓰다가
    ★ ★ `check_all` 이 ★ **`database is locked`** 로 통째로 죽었다

돌리는 법
    python3.11 tools/collect_revolt.py --dry
    python3.11 tools/collect_revolt.py            ★ 목록만 → 파일
    python3.11 tools/collect_revolt.py --detail   ★ 상세까지 → 파일
    python3.11 tools/load_raw.py revolt --write   ★ ★ 그다음 넣는다
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from parse.revolt.mapping import SITE_CODE, parse_list_item  # noqa: E402
# ★ 차종 짚기는 ★ 사전을 읽을 뿐이다 — ★ 본 DB 를 안 연다
from store.dictionary import known_model_of  # noqa: E402
# ★★ 여기서 ★ **DB 를 들이지 않는다** — ★ 잠금이 아예 안 생긴다 (`S46-202`)
from store.rawfile import save as save_file  # noqa: E402

BASE = "https://api.revolt.kr/customers/web"
UA = ("Mozilla/5.0 (Linux; Android 13; SM-G991N) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36")
# ★★ 규격 2장 — ★ 「User-Agent · Referer · Accept 만」.  ★ App-* 를 넣으면 500 이다
HEADERS = {"User-Agent": UA, "Referer": "https://www.revolt.kr/",
           "Accept": "application/json"}
MAX_PAGES = 30
SLEEP = 1.2                # ★ 몰아치면 500 이다 (규격 「금지」)

# ★★★★★ 09-01 — ★ 목록에 없다고 죽이지 않는다 (0c 와 같은 자리).
#   ★ 상세로 확인한 뒤 죽이는 꼴로 바꾼 뒤 다시 켠다
SWEEP_OFF = ("08-29 — 목록에 없다고 죽이면 살아 있는 차를 죽인다 "
             "(11-store/a-key 08-29 절).  상세로 확인한 뒤 죽이는 꼴로 "
             "바꾼 뒤 다시 켠다")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get(url: str, timeout: float = 30.0):
    """★ 못 받으면 ★ `None` — ★ 「없음」으로 저장하지 않는다 (금지 12)."""
    try:
        with urllib.request.urlopen(
                urllib.request.Request(url, headers=HEADERS),
                timeout=timeout) as res:
            return res.read()
    except urllib.error.HTTPError as e:
        print(f"  ★ HTTP {e.code} — {url}")
        return None
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        print(f"  ★ 못 받음 {type(e).__name__} — {url}")
        return None


def main() -> int:
    args = sys.argv[1:]
    cars: list = []
    pages: list = []          # ★ 쪽마다 파일 하나로 남긴다
    seen: set = set()
    done = False
    for page in range(1, MAX_PAGES + 1):
        body = _get(f"{BASE}/cars/?page={page}")
        if body is None:
            break
        try:
            got = json.loads(body)
        except ValueError:
            break
        if isinstance(got, dict):
            got = got.get("results") or got.get("cars") or []
        if not got:
            done = True            # ★ 빈 쪽을 봤다 = 끝을 봤다
            break
        pages.append(got)
        fresh = [x for x in got if x.get("hash_id") not in seen]
        seen.update(x.get("hash_id") for x in fresh)
        cars.extend(fresh)
        print(f"  page={page} → {len(got)}건 (새로 {len(fresh)} · 누계 {len(cars)})")
        if not fresh:
            done = True            # ★ 같은 쪽이 되풀이된다 — ★ 끝이다
            break
        time.sleep(SLEEP)
    print(f"★ 목록 합계 {len(cars)}건 · 끝까지 받았나 {'예' if done else '아니오'}")

    rows = []
    raw_of: dict = {}
    for one in cars:
        row = parse_list_item(one)
        if row is None:
            continue
        row["detail_status"] = "not_requested"
        known = known_model_of((row.get("site_model") or "").split()[0]
                               if row.get("site_model") else None)
        if known:
            row["site_model_group"] = known
        raw_of[row["source_id"]] = one
        rows.append(row)
    ours = [r for r in rows if r.get("site_model_group")]
    print(f"★ 우리 대상 — {len(ours)}건 / {len(rows)}건 "
          f"({sorted({r['site_model_group'] for r in ours})})")
    if "--dry" in args:
        print("★ --dry 라 저장하지 않았다")
        return 0

    at = _now()
    run_id = f"revolt-{at[:19]}"
    # ★★ 목록은 ★ 쪽마다 한 파일이다 — ★ `page-{NNNN}.json` (마스터 지시)
    for n, page in enumerate(pages, 1):
        save_file(SITE_CODE, "list", None, f"{BASE}/cars/?page={n}",
                  json.dumps(page, ensure_ascii=False), at,
                  run_id=run_id, page=n, root=ROOT)
    print(f"★ 목록 {len(pages)}쪽을 파일로 남겼다 — "
          f"raw/{SITE_CODE}/list/{at[:10]}/")

    if "--detail" not in args:
        print("★ 상세는 --detail 로 받는다 · 넣기는 "
              "python3.11 tools/load_raw.py revolt --write")
        return 0

    got = {"정상": 0, "못 받음": 0}
    for r in ours:
        sid = r["source_id"]
        url = f"{BASE}/cars/{sid}/"
        body = _get(url)
        if body is None:
            got["못 받음"] += 1
            time.sleep(SLEEP * 2)
            continue
        save_file(SITE_CODE, "detail", sid, url, body, at,
                  run_id=run_id, root=ROOT)
        got["정상"] += 1
        time.sleep(SLEEP)
    print("★ 상세 — " + " · ".join(f"{k} {v}" for k, v in got.items()))
    print("★ 넣기 — python3.11 tools/load_raw.py revolt --write")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
