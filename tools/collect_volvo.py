# -*- coding: utf-8 -*-
"""볼보 셀렉트 수집 — xhr-results 쪽넘김 (명령서 1a).

★ 한 쪽에 링크 12개가 상한이다 — ★ 12 면 다음 쪽이 있다
★ 총건수는 ★ 화면 글자 「총 N」에서 읽는다 — ★ 링크를 세면 늘 12 다
★ 슬러그로 거른다 — ★ 우리 차종만 (xc60 · s60 · xc40 · v60-cross-country)
★ 503 이 잦다 — ★ 재시도 (규격 _note)
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from store.raw import commit, open_db                       # noqa: E402

SITE_CODE = "volvo_selekt"
PAGE_LINKS = 12                # ★ 한 쪽 상한
MAX_PAGES = 40
RETRY, RETRY_WAIT = 3, 3.0
RE_LINK = re.compile(r'href="(/kr/vehicles/volvo/([a-z0-9-]+)/([^"/]+))"')
# ★★ 총건수 — ★ `data-found` 가 정본이다 (가이드 실측 · 명령서 1a).
#   ★ 없으면 ★ 받은 매물번호를 센다 — ★ 「총 N」 글자는 ★ **다른 수**다
#   ★ ★ 실측 08-24 — ★ 「총 180」이라 적혀 있으나 ★ 매물번호는 ★ 221개였다.
#     ★ ★ 180 을 믿었으면 ★ 41건을 조용히 버릴 뻔했다
RE_TOTAL = re.compile(r'data-found="(\d+)"')
# ★ 우리 차종의 슬러그 — ★ `targets.json` 이 정본이 아니라 ★ 사이트 말이다
OURS = {"xc60": "XC60", "s60": "S60", "xc40": "XC40",
        "v60-cross-country": "V60 크로스 컨트리", "v60cc": "V60 크로스 컨트리"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get(url: str, headers: dict, timeout: float) -> str | None:
    for _ in range(RETRY):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as res:
                return res.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503):
                return None
            time.sleep(RETRY_WAIT)
        except Exception:
            return None
    return None


def main() -> int:
    args = sys.argv[1:]
    with open(os.path.join(ROOT, "config", "endpoints.json"), encoding="utf-8") as f:
        cfg = json.load(f)[SITE_CODE]
    head = cfg.get("headers") or {}
    timeout = float(cfg.get("timeout_sec") or 40)
    interval = float(cfg.get("interval_sec") or 1.0)
    base = cfg["base_url"]

    said, seen = None, {}
    for page in range(1, MAX_PAGES + 1):
        raw = _get(f"{base}/kr/vehicles/xhr-results/{page}", head, timeout)
        if not raw:
            print(f"  {page}쪽 — ★ 못 받았다.  멈춘다")
            break
        if said is None:
            got = RE_TOTAL.search(raw)
            said = int(got.group(1)) if got else None
        links = RE_LINK.findall(raw)
        for path, slug, sid in links:
            seen[sid] = (slug, base + path)
        if len(links) < PAGE_LINKS:
            break
        time.sleep(interval)
    ours = {k: v for k, v in seen.items() if v[0] in OURS}
    print(f"★ data-found {said if said is not None else '없다'} · "
          f"받은 매물번호 {len(seen)}건 · 쪽 {page}")
    if said is not None and said != len(seen):
        print(f"  ★ 어긋난다 — {said - len(seen):+d}건")
    print(f"★ 우리 대상 — {len(ours)}건 (슬러그 {sorted({v[0] for v in ours.values()})})")
    if "--dry" in args or not ours:
        print("★ --dry 라 저장하지 않았다" if "--dry" in args else "★ 우리 대상이 없다")
        return 0

    from store.core import resolve_listing_id, upsert_core

    conn = open_db(os.path.join(ROOT, "carwatch.db"))
    at = _now()
    for sid, (slug, url) in ours.items():
        row = {"site": SITE_CODE, "source_id": sid, "price_unit": "won",
               "site_model_group": OURS[slug], "site_model": slug,
               "detail_status": "not_requested"}
        row["listing_id"] = resolve_listing_id(conn, SITE_CODE, sid, at)
        upsert_core(conn, row, at)
    commit(conn)
    n = conn.execute("SELECT COUNT(*) FROM core_listing WHERE site=?",
                     (SITE_CODE,)).fetchone()[0]
    print(f"★ 저장 {len(ours)}건 · 저장된 볼보 매물 {n:,}건")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
