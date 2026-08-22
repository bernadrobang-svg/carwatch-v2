#!/usr/bin/env python3.11
"""KB차차차 목록 수집 · 총 매물 수 세기 (명령서 `ORDER_20260822_r515.md` 3-2 · 단계 9).

    python3.11 tools/collect_kbchachacha.py --count          총 매물 수·마지막 쪽만 센다
    python3.11 tools/collect_kbchachacha.py --pages N        N쪽까지 받아 저장
    python3.11 tools/collect_kbchachacha.py --probe N        상세 N건을 재 봇차단 비율을 낸다

지시서   `docs/KBCHACHACHA_API.md` · `docs/TARGET_KEY_MAP.md`
근거     ★★ 봇 차단 가르기가 ★ 핵심이다 (명령서 3-2)
값규칙   ★ 10KB 미만이거나 「로봇 여부 확인」이 있으면 ★ 수집 실패다.
        ★ 최대 3회 재시도.  ★ 절대 「없음」으로 저장하지 않는다
        ★ 3회 다 실패하면 ★ 그대로 두고 ★ 세어서 보고한다
금지     ★ 못 받은 것을 「없음」으로 저장하는 것 — ★ 28% 가 「사고 없음」이 된다
"""
from __future__ import annotations

import os
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from adapters.kbchachacha import (  # noqa: E402
    SITE_CODE,
    KbChaChaChaAdapter,
    is_bot_wall,
    load_config,
)
from store.raw import open_db  # noqa: E402

RETRY = 3               # ★ 봇 차단 재시도 (KBCHACHACHA_API 1-1)
RETRY_WAIT = 3.0
MAX_PAGES = 400         # ★ 빈 쪽이 나오면 그 전에 멈춘다.  이것은 안전장치다
RE_CARSEQ = re.compile(r"carSeq=(\d+)")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get(url: str, headers: dict, timeout: float) -> str | None:
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as f:   # noqa: S310
            return f.read().decode("utf-8", "replace")
    except OSError:
        return None


def fetch_ok(url: str, headers: dict, timeout: float, cfg: dict) -> tuple:
    """★ 봇 차단이면 다시 부른다.  ★ 「없음」으로 내려가지 않는다.

    반환   (본문 또는 None, 시도 횟수, 봇차단이었나)
    ★ 3회 다 막히면 ★ None 이다 — ★ 부르는 쪽이 「못 받았다」로 적는다
    """
    walled = False
    for n in range(1, RETRY + 1):
        body = _get(url, headers, timeout)
        if body is not None and not is_bot_wall(body, cfg):
            return body, n, walled
        walled = True
        if n < RETRY:
            time.sleep(RETRY_WAIT * n)
    return None, RETRY, True


def page_ids(body: str) -> list:
    """쪽에서 매물번호를 뽑는다.  ★ 고유하게 · 나온 차례대로."""
    out, seen = [], set()
    for one in RE_CARSEQ.findall(body or ""):
        if one not in seen:
            seen.add(one)
            out.append(one)
    return out


def count_all(adapter: KbChaChaChaAdapter, cfg: dict, limit: int = MAX_PAGES):
    """★ 빈 쪽까지 늘려 가며 센다 (명령서 3-2 「확인해 알려 줄 것」 ③)."""
    seen, pages, empty_at = set(), 0, None
    for page in range(1, limit + 1):
        req = adapter.list_url(None, page=page)
        body, _tries, walled = fetch_ok(req.url, req.headers,
                                        req.timeout_sec, cfg)
        pages = page
        if body is None:
            print(f"  {page}쪽 — ★ 못 받았다 (봇 차단 {walled})")
            break
        got = page_ids(body)
        if not got:
            empty_at = page
            break
        before = len(seen)
        seen.update(got)
        if len(seen) == before:
            empty_at = page          # ★ 새 것이 없으면 끝이다
            break
        if page % 20 == 0:
            print(f"  {page}쪽 … 누적 {len(seen):,}건")
        time.sleep(float(cfg.get("interval_sec") or 1.2))
    return seen, pages, empty_at


def probe_detail(adapter: KbChaChaChaAdapter, cfg: dict, ids: list) -> dict:
    """★ 봇 차단 비율을 잰다.  ★ 세어서 보고한다 — 판정하지 않는다."""
    got = {"본": 0, "정상": 0, "재시도로 살림": 0, "3회 다 막힘": 0}
    for one in ids:
        req = adapter.detail_urls(one)[0]
        body, tries, walled = fetch_ok(req.url, req.headers,
                                       req.timeout_sec, cfg)
        got["본"] += 1
        if body is None:
            got["3회 다 막힘"] += 1
        elif walled:
            got["재시도로 살림"] += 1
        else:
            got["정상"] += 1
        del tries
        time.sleep(float(cfg.get("interval_sec") or 1.2))
    return got


def main() -> int:
    cfg = load_config(ROOT)
    adapter = KbChaChaChaAdapter(cfg)
    args = sys.argv[1:]

    def opt(name: str, default: int) -> int:
        if name in args:
            i = args.index(name)
            if i + 1 < len(args) and args[i + 1].isdigit():
                return int(args[i + 1])
        return default

    if "--count" in args:
        seen, pages, empty_at = count_all(adapter, cfg, opt("--count", MAX_PAGES))
        print(f"★ 총 매물 {len(seen):,}건 · 받은 쪽 {pages} · "
              f"빈 쪽 {empty_at if empty_at else '안 나왔다'}")
        return 0

    if "--probe" in args:
        req = adapter.list_url(None, page=1)
        body, _t, _w = fetch_ok(req.url, req.headers, req.timeout_sec, cfg)
        ids = page_ids(body or "")[:opt("--probe", 10)]
        got = probe_detail(adapter, cfg, ids)
        print("★ 봇 차단 실측 —", " · ".join(f"{k} {v}" for k, v in got.items()))
        return 0

    pages = opt("--pages", 1)
    seen: set = set()
    for page in range(1, pages + 1):
        req = adapter.list_url(None, page=page)
        body, _t, walled = fetch_ok(req.url, req.headers, req.timeout_sec, cfg)
        if body is None:
            print(f"  {page}쪽 — ★ 못 받았다 (봇 차단 {walled}).  ★ 저장하지 않는다")
            continue
        seen.update(page_ids(body))
        time.sleep(float(cfg.get("interval_sec") or 1.2))
    print(f"목록 {pages}쪽 · 매물번호 {len(seen):,}건")

    from store.core import resolve_listing_id
    from store.raw import commit

    conn = open_db(os.path.join(ROOT, "carwatch.db"))
    at = _now()
    for one in sorted(seen):
        resolve_listing_id(conn, SITE_CODE, one, at)
    commit(conn)
    print(f"★ 매물번호만 넣었다 {len(seen):,}건 · site='{SITE_CODE}'")
    print("★ 상세는 아직이다 — ★ 봇 차단을 가르는 자리를 먼저 세웠다")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
