#!/usr/bin/env python3.11
"""현대·제네시스 인증중고차 목록 수집 (명령서 `ORDER_20260822_r515.md` 3장 · 단계 11).

    python3.11 tools/collect_hyundai_cert.py --count      건수만 (조건 없이)
    python3.11 tools/collect_hyundai_cert.py [--dry]      목록을 끝까지 받아 저장

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

from parse.hyundai_cert.mapping import cards, parse_card  # noqa: E402
from store.raw import open_db  # noqa: E402

SITE_CODE = "hyundai_cert"
BASE = "https://certified.hyundai.com"
LIST_PATH = "/m/search/results/selling"
COUNT_PATH = "/api/search/vehicle/count/selling?srchType=srchFilter"
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


def load_target_table(root: str = ROOT) -> dict:
    """차종 대응표.  ★ config 가 정본이다 — 코드에 차종을 박지 않는다."""
    with open(os.path.join(root, "config", "sites.json"), encoding="utf-8") as f:
        got = (json.load(f).get(SITE_CODE) or {}).get("target_map") or {}
    return {k: v for k, v in got.items() if not k.startswith("_")}


def target_of(parsed: dict, table: dict) -> str | None:
    """사이트 차종 → 우리 차종 키.  ★ 없으면 「차종 미정」이다 — 버리지 않는다."""
    got = table.get(parsed.get("site_model_group") or "")
    if not got:
        return None
    need = got.get("fuel_contains")
    if need and need.lower() not in (parsed.get("site_model") or "").lower():
        return None
    return got["target_key"]


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


def total_count() -> int | None:
    """★ 조건 없이 부르면 전체 건수다 — 끝 쪽까지 받는 기준으로 쓴다."""
    try:
        req = urllib.request.Request(BASE + COUNT_PATH,
                                     headers={"User-Agent": HEADERS["User-Agent"]})
        with urllib.request.urlopen(req, timeout=20) as f:    # noqa: S310
            got = json.loads(f.read().decode("utf-8"))
        return int(got.get("body") or 0)
    except (OSError, ValueError):
        return None


def walk() -> tuple[list, int]:
    """목록을 끝까지 받는다.  ★ pageIdx 로 쪽을 넘긴다.

    ★ 카드까지 파싱해서 돌려준다 — ★ 매물번호만 넣으면 껍데기가 된다
    """
    seen, rows, pages = set(), [], 0
    for page in range(1, MAX_PAGES + 1):
        body = _post(BASE + LIST_PATH, dict(BODY, pageIdx=page))
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

    ids, pages = walk()
    print(f"목록 {pages}쪽 · 매물 {len(ids):,}건")
    if said and len(ids) != said:
        print(f"  ★ 어긋난다 — 사이트 {said} vs 받은 {len(ids)}")

    table = load_target_table()
    hit: dict = {}
    for one in ids:
        one["target_key"] = target_of(one, table)
        k = one["target_key"] or "차종 미정"
        hit[k] = hit.get(k, 0) + 1
    for k, n in sorted(hit.items(), key=lambda kv: -kv[1])[:6]:
        print(f"  {k:16} {n:>5}건")

    if "--dry" in args:
        print("★ --dry 라 저장하지 않았다")
        return 0

    from store.core import resolve_listing_id, split_pii, upsert_core
    from store.pii import load_key
    from store.raw import commit

    conn = open_db(os.path.join(ROOT, "carwatch.db"))
    at = _now()
    key = load_key()
    for one in ids:
        one["listing_id"] = resolve_listing_id(conn, SITE_CODE,
                                               one["source_id"], at)
        upsert_core(conn, split_pii(conn, one, SITE_CODE, key, at), at)
    commit(conn)
    print(f"★ 저장 {len(ids):,}건 · site='{SITE_CODE}'")
    print("★ 상세(27축)는 아직이다 — ★ 목록만으로 차종·연식·주행·값이 찬다")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
