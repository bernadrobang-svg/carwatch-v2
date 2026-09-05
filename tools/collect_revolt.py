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


def _get(url: str, timeout: float = 30.0, endpoint: str | None = None,
         source_id=None, page: int | None = None):
    """★ 못 받으면 ★ `None` — ★ 「없음」을 **값으로 삼지** 않는다 (금지 12).

    ★★★★★ 09-05 (지시 1번 · `S46-278` · `STEP 53-⑤`) — ★ **막힌 응답도 원문이다.**
      ★ 전에는 ★ 실패하면 ★ **몸통을 버렸다** — ★ 「어떻게 막혔나」를 뒤에 못 봤다
    """
    from collect.rawfetch import keep_blocked

    try:
        with urllib.request.urlopen(
                urllib.request.Request(url, headers=HEADERS),
                timeout=timeout) as res:
            return res.read()
    except urllib.error.HTTPError as e:
        print(f"  ★ HTTP {e.code} — {url}")
        if endpoint:
            try:
                keep_blocked(SITE_CODE, endpoint, source_id, url, e.read(),
                             page=page, http_code=e.code, root=ROOT)
            except OSError:
                pass
        return None
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        print(f"  ★ 못 받음 {type(e).__name__} — {url}")
        return None


def _targets() -> dict:
    """★★★★★ 09-01 — ★ 가이드가 ★ **리볼트 질의 열쇠**를 줬다 (`targets.json`).

    ★ 앞서는 ★ 차종 이름(「Model Y」)으로 짚으려다 ★ **264/270건을 못 넣었다**.
      ★ ★ 이제 ★ `model_hash_id` 로 ★ **사이트가 직접 갈라 준다** — ★ 이름을 안 옮긴다
    돌려줌  {model_hash_id: target_key}
    """
    with open(os.path.join(ROOT, "config", "targets.json"),
              encoding="utf-8") as f:
        got = json.load(f)
    out: dict = {}
    for key, spec in got.items():
        if key.startswith("_") or not isinstance(spec, dict):
            continue
        if not spec.get("active"):
            continue
        q = (spec.get("site_query") or {}).get(SITE_CODE)
        if not isinstance(q, dict):
            continue
        # ★★ 열쇠 둘을 ★ **함께** 쓴다 — ★ 규격이 준 것을 ★ 하나도 안 버린다.
        #   ★ 실측 09-01 — ★ `?brand_hash_id=` 도 ★ 걸린다
        #     (폴스타 `RWlnAZ` → 7건 · 볼보 `Jo6rOo` → 0건 = 재고 없음)
        bid = q.get("brand_hash_id")
        mid = q.get("model_hash_id")
        for one in (mid if isinstance(mid, list) else [mid]):
            if one:
                out[(str(bid) if bid else "", str(one))] = key
    return out


def main() -> int:
    args = sys.argv[1:]
    want = _targets()
    print(f"★ 우리 차종의 리볼트 열쇠 {len(want)}가지 — "
          f"{sorted(set(want.values()))}")
    cars: list = []
    pages: list = []          # ★ (열쇠, 쪽번호, 항목들) — ★ 쪽마다 파일 하나
    seen: set = set()
    key_of: dict = {}         # ★ hash_id → 우리 차종 키.  ★ **질의가 알려 준다**
    done = True
    # ★★★★★ 09-01 규격 (`docs/REVOLT_API.md` 「거르개는 `?model_hash_id=` 다」) —
    #   ★ ★ **차종마다 따로 받는다.**  ★ 전량 220건을 훑고 이름으로 거르지 않는다.
    #   ★ ★ ★ 까닭 — ★ 목록 항목에 ★ `model_hash_id` 가 ★ **없다** [실측 09-01].
    #     ★ ★ 있는 것은 ★ `model_name`(영문 "Model Y")뿐이라 ★ 이름을 옮겨야 했고,
    #     ★ ★ ★ 그래서 ★ **264/270건을 못 넣었다**.  ★ 질의로 가르면 ★ 옮길 것이 없다
    #   ★ ★ ★ `?model=` 은 안 걸린다 (규격) — ★ `?model_hash_id=` 여야 한다
    for (bid, mid), tkey in sorted(want.items()):
        for page in range(1, MAX_PAGES + 1):
            url = (f"{BASE}/cars/?brand_hash_id={bid}&model_hash_id={mid}"
                   f"&page={page}")
            body = _get(url, endpoint="list", page=page)
            if body is None:
                done = False       # ★ 못 받았다 — ★ 「끝까지 받았다」고 하지 않는다
                break
            try:
                got = json.loads(body)
            except ValueError:
                done = False
                break
            if isinstance(got, dict):
                got = got.get("results") or got.get("cars") or []
            if not got:
                break              # ★ 빈 쪽 = ★ 이 차종은 끝이다
            pages.append((bid, mid, page, got))
            fresh = [x for x in got if x.get("hash_id") not in seen]
            seen.update(x.get("hash_id") for x in fresh)
            for x in fresh:
                key_of[x.get("hash_id")] = tkey
            cars.extend(fresh)
            print(f"  {tkey:<14} {mid} page={page} → {len(got)}건 "
                  f"(새로 {len(fresh)} · 누계 {len(cars)})")
            if not fresh:
                break              # ★ 같은 쪽이 되풀이된다
            time.sleep(SLEEP)
    print(f"★ 목록 합계 {len(cars)}건 · 끝까지 받았나 {'예' if done else '아니오'}")

    rows = []
    raw_of: dict = {}
    for one in cars:
        row = parse_list_item(one)
        if row is None:
            continue
        row["detail_status"] = "not_requested"
        # ★★★★★ 09-01 — ★ **질의가 짚어 줬다** (이름으로 안 짚는다).
        #   ★ `?model_hash_id=` 로 받았으니 ★ 이 쪽에 온 것은 ★ 그 차종이다
        tkey = key_of.get(one.get("hash_id"))
        if tkey:
            row["target_key"] = tkey
        known = known_model_of((row.get("site_model") or "").split()[0]
                               if row.get("site_model") else None)
        if known:
            row["site_model_group"] = known
        raw_of[row["source_id"]] = one
        rows.append(row)
    ours = [r for r in rows if r.get("target_key") or r.get("site_model_group")]
    print(f"★ 우리 대상 — {len(ours)}건 / {len(rows)}건 "
          f"({sorted({r.get('target_key') or r.get('site_model_group')  for r in ours})})")
    if "--dry" in args:
        print("★ --dry 라 저장하지 않았다")
        return 0

    at = _now()
    run_id = f"revolt-{at[:19]}"
    # ★★ 목록은 ★ 쪽마다 한 파일이다 — ★ `page-{NNNN}.json` (마스터 지시)
    for n, (bid, mid, pno, page) in enumerate(pages, 1):
        save_file(SITE_CODE, "list", None,
                  f"{BASE}/cars/?brand_hash_id={bid}"
                  f"&model_hash_id={mid}&page={pno}",
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
        body = _get(url, endpoint="detail", source_id=sid)
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
