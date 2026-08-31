# -*- coding: utf-8 -*-
"""렉서스 인증중고 수집 (명령서 1a).

★ 모바일 UA ＋ Referer 가 있어야 준다
★ `search_list.car_list` 가 매물이다 — ★ `total_list_num` 은 믿지 않는다
   ★ 실측 08-24 — car_list 36 · total_list_num 84 (서로 다르다)
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

from parse.lexus_certified.mapping import (  # noqa: E402
    parse_list_item,
)
from store.dictionary import known_model_of        # noqa: E402
# ★★★★★ 09-01 마스터 지시 — ★ 받기는 ★ **파일만** 쓴다 (`S46-204`)
from store.rawfile import save as save_file  # noqa: E402

SITE_CODE = "lexus_certified"
WON_PER_MANWON = 10_000
# ★ 쪽넘김 상한.  ★ 실측 3쪽이다 — ★ 사이트가 끝을 안 알려도 여기서 멈춘다
MAX_PAGES = 20
SLEEP_SEC = 1.0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _title(v) -> str | None:
    """★ 사이트가 `{"code":…, "title":…}` 로 주는 칸 — ★ 사람 말만 남긴다."""
    if isinstance(v, dict):
        return v.get("title") or v.get("code")
    return v if v else None


def main() -> int:
    args = sys.argv[1:]
    with open(os.path.join(ROOT, "config", "endpoints.json"), encoding="utf-8") as f:
        cfg = json.load(f)[SITE_CODE]
    # ★★★★★ 08-29 (`LEXUS_CERTIFIED_API.md` 1c) — ★ **쪽넘김이 있다**.
    #   ★ 열쇠는 ★ `cur_page` 다 — ★ `page` · `pageNo` 는 ★ **조용히 1쪽을 준다**.
    #   ★ 개정 587 이 그것에 속아 ★ 「전수 36」으로 적었다.
    #   ★ 실측 08-29 — ★ cur_page 1→36 · 2→36 · 3→2 · 4→0 · 전수 74.
    #   ★★ 1쪽만 받고 `sweep_gone` 을 부르면 ★ 2·3쪽 38건이
    #     ★ ★ **안 팔렸는데 gone 이 된다** — ★ 그것이 이 고침의 까닭이다
    base = cfg["base_url"] + cfg["paths"]["list"]
    sep = "&" if "?" in base else "?"
    timeout = float(cfg.get("timeout_sec") or 40)
    cars: list = []
    pages, done = 0, False
    for page in range(1, MAX_PAGES + 1):
        req = urllib.request.Request(f"{base}{sep}cur_page={page}",
                                     headers=cfg.get("headers") or {})
        d = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
        sl = d.get("search_list") or {}
        got = sl.get("car_list") or []
        # ★ 돌려준 `cur_page` 가 ★ 부른 쪽과 다르면 ★ 쪽넘김이 안 먹은 것이다.
        #   ★ 그 응답은 1쪽의 되풀이다 — ★ 넣으면 안 되고 ★ 「끝까지」도 아니다
        if got and str(sl.get("cur_page") or page) != str(page):
            print(f"★ cur_page={page} 인데 응답이 {sl.get('cur_page')} 다 — "
                  "쪽넘김이 안 먹었다.  ★ 끝까지 받은 것으로 치지 않는다")
            break
        pages += 1
        cars.extend(got)
        print(f"  cur_page={page} → {len(got)}건 (누계 {len(cars)})")
        if not got:
            done = True                # ★ 빈 쪽을 봤다 = 끝을 봤다
            break
        total_page = sl.get("total_page")
        if total_page and page >= int(total_page):
            done = True                # ★ 사이트가 말한 마지막 쪽까지 왔다
            break
        time.sleep(SLEEP_SEC)
    print(f"★ car_list 합계 {len(cars)}건 · {pages}쪽 · "
          f"total_list_num {sl.get('total_list_num')} "
          f"· 끝까지 받았나 {'예' if done else '아니오'}")

    rows = []
    # ★★ 원문 항목을 ★ 파싱 결과와 ★ 짝지어 둔다 (명령서 3-2 필수) —
    #   ★ 렉서스는 ★ 상세가 없다.  ★ 목록 항목이 ★ 원문의 전부다
    raw_of: dict = {}
    for one in cars:
        if not one.get("idx"):
            continue
        # ★★★★★ 08-30 (r974 · 0j 1) — ★ 칸 짓기를 ★ `parse/lexus_certified` 로 옮겼다.
        #   ★ 열 곳 중 ★ 여기만 파서가 없어 ★ 검사가 못 보는 자리였다 (`S46-178`)
        row = parse_list_item(one)
        if row is None:
            continue
        row["detail_status"] = "not_requested"
        name = row.get("site_model") or ""
        # ★ 「NX 350h」 → NX · 「RX 450h+」 → RX.  ★ 등록부가 아는 이름만
        known = known_model_of(name.split()[0] if name else None)
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

    # ★★★★★ 09-01 마스터 지시 — ★ **받기 걸음은 파일만 쓴다.  ★ DB 를 안 연다.**
    #   ★ 「★ 넣기 걸음은 그 폴더를 읽어 `raw_response` ＋ `core_listing` 에 넣는다」
    #   ★★ 그래서 ★ 여기서 ★ `open_db`·`upsert_core`·`sweep_gone_groups` 를 ★ **뺐다**.
    #     ★ ★ 넣기는 ★ `python3.11 tools/load_raw.py lexus_certified --write` 가 한다
    at = _now()
    # ★★ 원문은 ★ **다 남긴다** — ★ 안 넣는 것도 남긴다 (「갈래를 넓히면 다시 판다」)
    #   ★ 걸러 넣기(3-2)는 ★ 넣기 걸음이 한다 — ★ 받기는 다 남길 뿐이다
    for r in rows:
        save_file(SITE_CODE, "list", r["source_id"], cfg["base_url"],
                  json.dumps(raw_of.get(r["source_id"]), ensure_ascii=False),
                  at, root=ROOT)
    print(f"★ 목록 {len(rows)}건을 파일로 남겼다 — "
          f"raw/{SITE_CODE}/list/{at[:10]}/")
    print(f"★ 우리 대상으로 보이는 것 {len(ours)}건 — ★ 넣기는 "
          f"python3.11 tools/load_raw.py {SITE_CODE} --write")

    if "--detail" not in args:
        print("★ 상세는 --detail 로 받는다 — ★ 연식(`year_month`)은 상세에만 있다")
        return 0
    return _detail(cfg, ours, at)


DETAIL_PATH = "/api/json/getData_car_detail.json.php?idx={idx}"


def _detail(cfg, rows, at) -> int:
    """상세를 받아 ★ **파일로만** 남긴다 (마스터 지시 09-01).

    ★ 목록의 `year` 는 ★ 모델연도다.  ★ 연식은 ★ `car_info.registration_date` 다
      (규격 `LEXUS_CERTIFIED_API.md` 3장 ③).  ★ 그래서 ★ 상세를 열어야 한다
    ★★ ★ **DB 를 안 연다** — ★ 넣기는 `tools/load_raw.py` 가 한다
    """
    base = cfg["base_url"]
    timeout = float(cfg.get("timeout_sec") or 40)
    got = {"정상": 0, "못 받음": 0}
    for r in rows:
        sid = r["source_id"]
        url = base + DETAIL_PATH.format(idx=sid)
        try:
            req = urllib.request.Request(url, headers=cfg.get("headers") or {})
            body = urllib.request.urlopen(req, timeout=timeout).read()
        except (urllib.error.URLError, OSError, TimeoutError) as e:
            # ★ 못 받은 것을 ★ 「없음」으로 저장하지 않는다 (금지 12)
            print(f"  idx={sid} ★ 못 받음 — {e}")
            got["못 받음"] += 1
            time.sleep(SLEEP_SEC)
            continue
        save_file(SITE_CODE, "detail", sid, url, body, at, root=ROOT)
        got["정상"] += 1
        time.sleep(SLEEP_SEC)
    print("★ 상세 — " + " · ".join(f"{k} {v}" for k, v in got.items()))
    print(f"★ 넣기 — python3.11 tools/load_raw.py {SITE_CODE} --write")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
