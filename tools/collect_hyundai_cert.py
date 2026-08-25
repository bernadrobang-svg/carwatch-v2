#!/usr/bin/env python3.11
"""현대·제네시스 인증중고차 목록 수집 (명령서 `ORDER_20260822_r515.md` 3장 · 단계 11).

    python3.11 tools/collect_hyundai_cert.py --count       건수만 (조건 없이)
    python3.11 tools/collect_hyundai_cert.py [--dry]       목록을 끝까지 받아 저장
    python3.11 tools/collect_hyundai_cert.py --detail [N]  ★ 상세까지 받는다 (N건만)

지시서   `docs/HYUNDAI_CERTIFIED_API.md`
근거     ★ robots 가 ★ 금지 경로를 하나도 두지 않았다 (Allow: /)
        ★ 인증·토큰·암호화 ★ 없다.  `tmnlId` 는 ★ 빈 문자열이어도 된다 (실측)
값규칙   ★ 목록 응답은 ★ HTML 조각이다.  매물번호는 `data-favContsNo` 에 있다
        ★ `data-id` 가 ★ 아니다 — 개정 480 이 잘못 적었고 485 가 고쳤다
        ★ 차종이 안 걸리면 ★ 「차종 미정」으로 두고 ★ 버리지 않는다
금지     ★ 못 받은 것을 「없음」으로 저장하는 것
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from parse.hyundai_cert.mapping import (  # noqa: E402
    cards,
    parse_card,
    parse_detail_all,
)
from parse.target_rules import target_by_rules  # noqa: E402
from store.raw import open_db  # noqa: E402

SITE_CODE = "hyundai_cert"
BASE = "https://certified.hyundai.com"
LIST_PATH = "/m/search/results/selling"
COUNT_PATH = "/api/search/vehicle/count/selling?srchType=srchFilter"
DETAIL_PATH = "/m/goods/goodsDetail.do?goodsNo={goods_no}"
ROWS = 100
MAX_PAGES = 60
INTERVAL = 1.0

# ★ 매물번호 — 영문 3 + 숫자 12 (개정 485 정정)
RE_GOODS = re.compile(r'data-favContsNo="([A-Z]{3}\d{12})"')

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Linux; Android 14; SM-S928N) "
                   "AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36"),
    "Content-Type": "application/json",
    "Referer": f"{BASE}/m/search/vehicle?srchType=srchFilter",
    "X-Requested-With": "XMLHttpRequest",
}

# ★ 브라우저가 보내는 본문 그대로 (HYUNDAI_CERTIFIED_API 5장)
BODY = {
    "type": None, "sortType": "popularity", "srchType": "srchFilter",
    "recentYn": "N", "tmnlId": "", "mbrNo": None, "siteNo": None,
    "saleCorpCd": None, "rowsPerPage": ROWS, "pageIdx": 1,
    "startNo": None, "listCnt": None, "searchWord": None,
    "lowPrice": None, "highPrice": None, "lowMileage": None,
    "highMileage": None, "lowModelYear": 2017, "highModelYear": None,
    "sdStatCd": None,
}


def target_of(parsed: dict) -> str | None:
    """사이트 차종 → 우리 차종 키.

    ★★ 개정 540 — ★ 쓰는 자리는 `config/dictionaries/target_map.json` 하나다.
      ★ 전에는 sites.json 에도 같은 표가 있었다 — ★ 두 곳이면 어긋난다
    ★ 표에 없으면 ★ None 이다 — 「차종 미정」이고 ★ 버리지 않는다
    ★★ 갈래(2.5T·LPG…)는 ★ `targets.json` 이 고른다 — ★ 새 규칙을 만들지 않는다
       (HYUNDAI_CERTIFIED_API 2d).  ★ 제목에 차종·연료·배기량이 다 있어
       ★ 상세가 없어도 갈린다 — ★ 전수 1,113건에 걸어 ★ 170건이 붙는다
    """
    got = target_by_rules(
        SITE_CODE, parsed.get("site_model_group"), parsed.get("fuel_raw"),
        parsed.get("site_model"), parsed.get("displacement_cc"))
    return got.target_key if got else None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _post(url: str, payload: dict) -> str | None:
    data = json.dumps(payload).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=data, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as f:    # noqa: S310
            return f.read().decode("utf-8", "replace")
    except OSError:
        return None


def _get(url: str) -> str | None:
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": HEADERS["User-Agent"],
                          "Referer": BASE + "/"})
        with urllib.request.urlopen(req, timeout=30) as f:    # noqa: S310
            return f.read().decode("utf-8", "replace")
    except OSError:
        return None


def fetch_detail(goods_no: str) -> tuple | None:
    """상세 하나 → (core_listing 몫, core_record 몫, 원문).

    ★ 짧으면 ★ 「못 받음」이다 — ★ 「없음」으로 내려가지 않는다
    돌려줌  (core_listing 몫, core_record 몫, ★ 원문 글자) 또는 None
    """
    body = _get(BASE + DETAIL_PATH.format(goods_no=goods_no))
    got = parse_detail_all(body or "", SITE_CODE, goods_no)
    # ★★ 원문도 함께 돌려준다 — ★ 부르는 쪽이 `raw_response` 에 남긴다
    #   (명령서 3-2 필수 「갈래를 넓히시면 다시 판다」)
    return None if got is None else (got[0], got[1], body)


def load_filters(root: str = ROOT) -> list:
    """★ 좁히는 조건 — ★ config 가 정본이다 (HYUNDAI_CERTIFIED_API 2e).

    ★ 차종군 코드를 ★ 코드에 박지 않는다 (S14 · 금지 6)
    """
    # ★★ 08-25 — ★ 좁히는 코드는 ★ `targets.json` 의 `site_query` **하나**가 정본이다
    #   (명령서 3-1 · 「코드는 각 사이트 규격에 있다.  targets.json 으로 옮겨라」).
    #   ★ ★ 전에는 ★ `sites.json` 의 `collect_filters` 에 따로 있어 ★ 두 곳이 갈렸다
    with open(os.path.join(root, "config", "targets.json"), encoding="utf-8") as f:
        rows = json.load(f)
    got, seen = [], set()
    for key, one in rows.items():
        if key.startswith("_") or not isinstance(one, dict):
            continue
        q = (one.get("site_query") or {}).get(SITE_CODE)
        if not isinstance(q, dict):
            continue
        # ★ 같은 부름을 두 번 하지 않는다 (G70_20T · G70_25T 가 같다)
        pick = {k: q[k] for k in ("mdlGrpList", "fuelList") if q.get(k)}
        mark = tuple(sorted(pick.items()))
        if not pick or mark in seen:
            continue
        seen.add(mark)
        got.append({**{k: [v] for k, v in pick.items()}, "for": key})
    if got:
        return got
    # ★ 옛 자리 — ★ targets.json 이 비면 그때만 본다
    with open(os.path.join(root, "config", "sites.json"), encoding="utf-8") as f:
        old = (json.load(f).get(SITE_CODE) or {}).get("collect_filters") or {}
    return old.get("groups") or []


def total_count(params: str = "") -> int | None:
    """★ 조건을 주면 그 조건의 건수다.  ★ 안 주면 전체다."""
    try:
        url = BASE + COUNT_PATH + (("&" + params) if params else "")
        req = urllib.request.Request(url,
                                     headers={"User-Agent": HEADERS["User-Agent"]})
        with urllib.request.urlopen(req, timeout=20) as f:    # noqa: S310
            got = json.loads(f.read().decode("utf-8"))
        return int(got.get("body") or 0)
    except (OSError, ValueError):
        return None


def walk(extra: dict | None = None, seen: set | None = None) -> tuple[list, int]:
    """목록을 끝까지 받는다.  ★ pageIdx 로 쪽을 넘긴다.

    ★ 카드까지 파싱해서 돌려준다 — ★ 매물번호만 넣으면 껍데기가 된다
    ★ `extra` 가 ★ 차종군 조건이다 (2e).  ★ 없으면 전량이다
    """
    seen, rows, pages = (set() if seen is None else seen), [], 0
    base = dict(BODY, **(extra or {}))
    for page in range(1, MAX_PAGES + 1):
        body = _post(BASE + LIST_PATH, dict(base, pageIdx=page))
        pages = page
        if body is None:
            print(f"  {page}쪽 — ★ 못 받았다.  ★ 저장하지 않는다")
            break
        fresh = 0
        for chunk in cards(body):
            got = parse_card(chunk, SITE_CODE)
            if got and got["source_id"] not in seen:
                seen.add(got["source_id"])
                rows.append(got)
                fresh += 1
        if not fresh:
            break
        time.sleep(INTERVAL)
    return rows, pages


def main() -> int:
    args = sys.argv[1:]
    said = total_count()
    print(f"사이트가 말한 건수 — {said if said is not None else '못 받았다'}")
    if "--count" in args:
        return 0

    groups = load_filters()
    if "--all" in args or not groups:
        if not groups:
            print("★ config 에 collect_filters 가 없다 — ★ 전량을 받는다")
        ids, pages = walk()
        print(f"목록 {pages}쪽 · 매물 {len(ids):,}건")
        if said and len(ids) != said:
            print(f"  ★ 어긋난다 — 사이트 {said} vs 받은 {len(ids)}")
    else:
        # ★★ 차종군마다 ★ 따로 부른다 — ★ 여섯 번이다 (2e).
        #   ★ 한 번에 부르면 ★ fuelList 가 ★ 전체에 걸려 389건이 온다 (규격 실측)
        ids, pages, seen = [], 0, set()
        print(f"★ 좁혀 받는다 — 차종군 {len(groups)}개 (전량 {said} 중)")
        for g in groups:
            cond = {k: g[k] for k in ("mdlGrpList", "fuelList") if g.get(k)}
            q = "&".join(f"{k}={v}" for k in cond for v in cond[k])
            said_n = total_count(q)
            got, pg = walk(cond, seen)
            for one in got:
                # ★ 제목에 연료 낱말이 없는 것은 ★ 전동화 전용 차종군이다.
                #   ★ 우리가 그 부름에서 달라고 한 연료를 쓴다 — ★ 짐작이 아니다
                if not one.get("fuel_raw") and g.get("fuel"):
                    one["fuel_raw"] = g["fuel"]
            pages += pg
            ids.extend(got)
            mark = "" if said_n == g.get("expect") else "  ★ 규격과 다르다"
            print(f"  {g['for']:22} {q:32} 사이트 {said_n:>4} · 받은 {len(got):>4}"
                  f" (규격 {g.get('expect')}){mark}")
            time.sleep(INTERVAL)
        print(f"목록 {pages}쪽 · 매물 {len(ids):,}건  ← ★ 전량 {said} 을 받지 않았다")

    hit: dict = {}
    for one in ids:
        one["target_key"] = target_of(one)
        k = one["target_key"] or "차종 미정"
        hit[k] = hit.get(k, 0) + 1
    for k, n in sorted(hit.items(), key=lambda kv: -kv[1]):
        print(f"  {k:16} {n:>5}건")

    want_detail = "--detail" in args
    limit = 0
    if want_detail:
        i = args.index("--detail")
        if i + 1 < len(args) and args[i + 1].isdigit():
            limit = int(args[i + 1])

    if "--dry" in args:
        print("★ --dry 라 저장하지 않았다")
        return 0

    from store.core import resolve_listing_id, split_pii, upsert_core
    from store.pii import load_key
    from store.raw import commit, save_site_raw

    conn = open_db(os.path.join(ROOT, "carwatch.db"))
    at = _now()
    key = load_key()
    for one in ids:
        one["listing_id"] = resolve_listing_id(conn, SITE_CODE,
                                               one["source_id"], at)
        upsert_core(conn, split_pii(conn, one, SITE_CODE, key, at), at)
    commit(conn)
    print(f"★ 저장 {len(ids):,}건 · site='{SITE_CODE}'")

    if not want_detail:
        print("★ 상세는 --detail 로 받는다")
        return 0

    todo = ids[:limit] if limit else ids
    got = {"정상": 0, "못 받음": 0}
    from store.core import upsert_child

    for one in todo:
        pair = fetch_detail(one["source_id"])
        if pair is None:
            # ★ 못 받은 것을 ★ 「없음」으로 저장하지 않는다 (금지 12)
            got["못 받음"] += 1
            time.sleep(INTERVAL)
            continue
        deep, record, body = pair
        # ★★ 원문을 ★ 먼저 남긴다 (명령서 3-2 필수)
        save_site_raw(conn, SITE_CODE, "detail", one["source_id"],
                      BASE + DETAIL_PATH.format(goods_no=one["source_id"]),
                      body, at)
        deep["listing_id"] = one["listing_id"]
        upsert_core(conn, split_pii(conn, deep, SITE_CODE, key, at), at)
        # ★ 사고·소유자 이력은 ★ core_record 의 칸이다 (A-2)
        record["listing_id"] = one["listing_id"]
        record["collected_at"] = at
        upsert_child(conn, "core_record", record, "p1", at)
        got["정상"] += 1
        time.sleep(INTERVAL)
    commit(conn)
    print("★ 상세 — " + " · ".join(f"{k} {v}" for k, v in got.items()))
    from tools.daily_enqueue import enqueue_after_store
    enqueue_after_store(os.path.join(ROOT, "carwatch.db"), SITE_CODE,
                        got.get("정상", 0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
