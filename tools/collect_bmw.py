# -*- coding: utf-8 -*-
"""BMW 바바리안(BPS) 수집 (명령서 1a).

★★ 503 은 고장이 아니다 — ★ 「503·200·200」이다.  ★ 재시도 세 번이면 산다
   ★ 가이드 정정 08-24 — 「마스터 손」이라 적은 것은 ★ 틀렸다
★ 딜러 한 곳이다.  ★ 가격은 목록 카드에 있다 — ★ 상세에는 없다 (규격 _note)
★ 쪽넘김이 있다 — ★ 매물번호가 안 늘면 멈춘다
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

from store.dictionary import known_model_of        # noqa: E402
from store.raw import commit, open_db              # noqa: E402

SITE_CODE = "bmw_bps"
RETRY, RETRY_WAIT = 3, 3.0
MAX_PAGES = 20
RE_ITEM = re.compile(r'it_id=([A-Za-z0-9_-]+)[^>]*>(.{0,400}?)</a>', re.S)
RE_TAG = re.compile(r"<[^>]+>")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get(url: str, headers: dict, timeout: float) -> str | None:
    """★ 503 이 나면 다시 두드린다 — ★ 503·200·200 이다 (실측 08-24)."""
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
            time.sleep(RETRY_WAIT)
    return None


def main() -> int:
    args = sys.argv[1:]
    with open(os.path.join(ROOT, "config", "endpoints.json"), encoding="utf-8") as f:
        cfg = json.load(f)[SITE_CODE]
    head = cfg.get("headers") or {}
    timeout = float(cfg.get("timeout_sec") or 40)
    interval = float(cfg.get("interval_sec") or 1.0)
    base = cfg["base_url"]

    seen: dict = {}
    # ★★ 목록 쪽 원문을 들고 간다 (명령서 3-2 필수) —
    #   ★ BMW·볼보는 ★ 상세가 없다.  ★ 목록 쪽이 ★ 원문의 전부다
    pages: list = []
    walls = 0
    # ★★★ 08-29 (개정 838) — ★ 「끝까지 받았나」.  ★ 안 늘어 멈췄을 때만 참이다
    done = False
    for page in range(1, MAX_PAGES + 1):
        raw = _get(f"{base}/shop/list.php?ca_id=10&page={page}", head, timeout)
        pages.append((f"{base}/shop/list.php?ca_id=10&page={page}", raw))
        if raw is None:
            walls += 1
            print(f"  {page}쪽 — ★ 못 받았다 (재시도 {RETRY}회)")
            break
        before = len(seen)
        for sid, block in RE_ITEM.findall(raw):
            text = " ".join(RE_TAG.sub(" ", block).split())
            if text and sid not in seen:
                seen[sid] = text
        if len(seen) == before:
            done = True                 # ★ 안 늘면 끝이다 — ★ 끝까지 받았다
            break
        time.sleep(interval)
    print(f"★ 매물번호 {len(seen)}건 · 쪽 {page} · 못 받은 쪽 {walls}")

    rows = []
    for sid, text in seen.items():
        known = known_model_of(text)
        row = {"site": SITE_CODE, "source_id": sid, "price_unit": "won",
               "site_model": text[:80], "detail_status": "not_requested"}
        if known:
            row["site_model_group"] = known
        rows.append(row)
    ours = [r for r in rows if r.get("site_model_group")]
    print(f"★ 우리 대상 — {len(ours)}건 / {len(rows)}건 "
          f"({sorted({r['site_model_group'] for r in ours}) or '없다'})")
    if "--dry" in args:
        print("★ --dry 라 저장하지 않았다")
        return 0

    from store.core import resolve_listing_id, upsert_core
    from store.raw import save_site_raw

    conn = open_db(os.path.join(ROOT, "carwatch.db"))
    at = _now()
    # ★★ 원문을 남긴다 (명령서 3-2 필수) — ★ 「갈래를 넓히시면 다시 판다」.
    #   ★ 쪽마다 한 줄이다 — ★ 매물번호가 없으니 ★ 겹침을 안 접는다
    for _u, _b in pages:
        save_site_raw(conn, SITE_CODE, "list", None, _u, _b, at)
    for r in rows:
        r["listing_id"] = resolve_listing_id(conn, SITE_CODE, r["source_id"], at)
        upsert_core(conn, r, at)
    commit(conn)
    # ★★★★★ 08-29 (개정 838 · 오판 161) — ★ 팔린 차를 거른다 (`S46-117`).
    #   ★ 저장한 **뒤에** 부른다 — ★ 새 매물이 차종을 갖고 있어야 한다.
    #   ★ 「끝까지 받았나」가 거짓이면 ★ 안 매긴다 — 반만 보고 매기면 산 차를 죽인다
    from store.core import sweep_gone_groups

    _got = sweep_gone_groups(conn, SITE_CODE, [(done, set(seen))], at)
    print(f"★ 목록에 없어 gone 으로 매긴 것 {sum(_got.values())}건 "
          f"({len(_got)}차종) · 끝까지 받았나 {'예' if done else '아니오'}")
    n = conn.execute("SELECT COUNT(*) FROM core_listing WHERE site=?",
                     (SITE_CODE,)).fetchone()[0]
    print(f"★ 저장 {len(rows)}건 · 저장된 BMW 매물 {n:,}건")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
