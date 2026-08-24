#!/usr/bin/env python3.11
"""KB차차차 목록 수집 · 총 매물 수 세기 (명령서 `ORDER_20260822_r515.md` 3-2 · 단계 9).

    python3.11 tools/collect_kbchachacha.py --count          총 매물 수·마지막 쪽만 센다
    python3.11 tools/collect_kbchachacha.py --pages N        N쪽까지 받아 저장
    python3.11 tools/collect_kbchachacha.py --probe N        상세 N건을 재 봇차단 비율을 낸다
    python3.11 tools/collect_kbchachacha.py --narrow [--detail N] [--interval S]
                                                            좁혀 받아 상세까지 넣는다

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
    is_real_end,
    load_config,
)
from parse.kbchachacha.mapping import parse_detail  # noqa: E402
from store.raw import open_db  # noqa: E402

RETRY = 3               # ★ 봇 차단 재시도 (KBCHACHACHA_API 1-1)
RETRY_WAIT = 3.0
MAX_PAGES = 400         # ★ 빈 쪽이 나오면 그 전에 멈춘다.  이것은 안전장치다
# ★★ 한 회차에 부를 상세 수 (명령서 14-1).  ★ 막히는 자리는 ★ 목록이 아니라 ★ 상세다 —
#   ★ 목록 53쪽은 ★ 봇 차단 0건이다 (실측 08-24 · C 확인).
#   ★ 목록은 ★ 한 번에 다 받고 · ★ 상세만 ★ 회차를 나눈다
DETAIL_BATCH = 50
# ★ 이만큼 이어서 막히면 ★ 그 회차를 끝낸다 (명령서 14-1)
# ★★ 가이드 지시 08-24 — 「★ 회차 50건 · ★ 2,759B 세 번이면 끝」.
#   ★ 200/8 로는 ★ 막힌 뒤에도 ★ 오래 두드려 ★ 다음 회차까지 막혔다 (실측 08-24)
WALL_GIVE_UP = 3
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


def load_filters(root: str = ROOT) -> list:
    """★ 좁히는 조건 — ★ `targets.json` 의 `site_query` 가 정본이다 (명령서 3-1).

    ★★ 08-25 — ★ 코드를 ★ **한 곳으로** 모았다.
      ★ ★ 전에는 ★ `sites.json` 의 `collect_filters` 에 따로 있어 ★ 두 곳이 갈렸다
    ★ 같은 부름을 두 번 하지 않는다 — ★ 차종 둘이 같은 코드를 쓸 수 있다
    """
    import json as _j

    with open(os.path.join(root, "config", "targets.json"), encoding="utf-8") as f:
        rows = _j.load(f)
    got, seen = [], set()
    for key, one in rows.items():
        if key.startswith("_") or not isinstance(one, dict):
            continue
        q = (one.get("site_query") or {}).get(SITE_CODE)
        if not isinstance(q, dict) or not q.get("makerCode"):
            continue
        mark = (q["makerCode"], q.get("classCode"))
        if mark in seen:
            continue
        seen.add(mark)
        got.append({"for": key, "makerCode": q["makerCode"],
                    "classCode": q.get("classCode", ""),
                    # ★ 규격이 적어 둔 예상 건수 — ★ 없으면 「—」다.  ★ 지어내지 않는다
                    "expect": q.get("_expect", "—")})
    if got:
        return got
    # ★ 옛 자리 — ★ targets.json 이 비면 그때만 본다
    with open(os.path.join(root, "config", "sites.json"), encoding="utf-8") as f:
        old = (_j.load(f).get(SITE_CODE) or {}).get("collect_filters") or {}
    return old.get("groups") or []


# ★ 꼬리 쪽 — ★ 크기는 큰데 매물이 0인 쪽이 이어진다 (X3 14·15쪽 71KB·25KB).
#   ★ 「0건이면 끝」으로 멈추면 ★ 까닭이 다르다 (규격 1a 금지).
#   ★ 그러나 ★ 끝없이 돌 수도 없다 — ★ 0건이 이만큼 이어지면 그만 본다
TAIL_LIMIT = 4


def walk_group(adapter: KbChaChaChaAdapter, cfg: dict, g: dict,
               seen: set) -> dict:
    """차종 하나를 ★ 끝까지 받는다.  ★ 끝은 ★ 크기로 가른다 (규격 1a).

    ★ 봇 차단(2,759B)  → ★ 재시도한다.  ★ 「없음」으로 저장하지 않는다
    ★ 진짜 끝(3,585B + 「차량이 없습니다」) → ★ 거기서 멈춘다
    """
    got, pages, walls, tail = [], 0, 0, 0
    for page in range(1, MAX_PAGES + 1):
        req = adapter.list_url(None, page=page,
                               maker=g["makerCode"], klass=g["classCode"])
        body, _tries, walled = fetch_ok(req.url, req.headers,
                                        req.timeout_sec, cfg)
        pages = page
        if walled:
            walls += 1
        if body is None:
            # ★ 3회 다 막혔다.  ★ 여기서 끝이라고 하지 않는다 — ★ 못 받은 것이다
            print(f"    {page}쪽 — ★ 3회 다 막혔다.  ★ 저장하지 않는다")
            break
        if is_real_end(body, cfg):
            break                       # ★ 진짜 끝이다
        ids = [x for x in page_ids(body) if x not in seen]
        if not page_ids(body):
            tail += 1
            if tail >= TAIL_LIMIT:
                break
        else:
            tail = 0
        seen.update(ids)
        got.extend(ids)
        time.sleep(float(cfg.get("interval_sec") or 1.2))
    return {"ids": got, "pages": pages, "walls": walls}


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


def store_details(adapter: KbChaChaChaAdapter, cfg: dict, ids: list,
                  limit: int = 0) -> int:
    """★ 상세를 받아 ★ 함께 넣는다.  ★ 껍데기를 안 넣는다 (명령서 5단계).

    ★ 봇 차단(30%)은 ★ 「없음」으로 저장하지 않는다 — ★ 다음 회차에 다시 부른다
    ★ 이미 받은 것은 ★ 건너뛴다 — ★ 여러 회차에 나눠 채운다 (규격 1-1)
    """
    from store.core import resolve_listing_id, split_pii, upsert_core
    from store.pii import load_key
    from store.raw import commit

    conn = open_db(os.path.join(ROOT, "carwatch.db"))
    at, key = _now(), load_key()
    done = {r[0] for r in conn.execute(
        "SELECT source_id FROM core_listing WHERE site=? "
        "AND detail_status='ok'", (SITE_CODE,))}
    todo = [x for x in ids if x not in done]
    if limit:
        todo = todo[:limit]
    print(f"★ 상세 — 받을 것 {len(todo):,}건 "
          f"(이미 받은 것 {len(done):,}건은 건너뛴다)")
    got = {"정상": 0, "봇차단 3회": 0, "파싱 실패": 0}
    walls_in_row = 0
    for n, one in enumerate(todo, 1):
        req = adapter.detail_urls(one)[0]
        body, _tries, _w = fetch_ok(req.url, req.headers, req.timeout_sec, cfg)
        if body is None:
            # ★ 못 받았다.  ★ 「없음」으로 저장하지 않는다 (금지 12 · 개정 289)
            got["봇차단 3회"] += 1
            walls_in_row += 1
            # ★★ 이만큼 이어서 막히면 ★ 사이트가 회차를 닫은 것이다 —
            #   ★ 그 회차를 끝내고 ★ 다음 회차로 넘긴다 (명령서 14-1).
            #   ★ 계속 두드리는 것은 ★ 사이트에 부담이고 ★ 소용도 없다
            if walls_in_row >= WALL_GIVE_UP:
                print(f"    ★ {walls_in_row}건 이어서 막혔다 — "
                      "★ 이 회차를 여기서 끝낸다.  ★ 다음 회차에 이어 받는다")
                break
            continue
        walls_in_row = 0
        deep = parse_detail(body, SITE_CODE, one)
        if not deep:
            got["파싱 실패"] += 1
            continue
        deep["listing_id"] = resolve_listing_id(conn, SITE_CODE, one, at)
        deep["detail_status"] = "ok"
        upsert_core(conn, split_pii(conn, deep, SITE_CODE, key, at), at)
        got["정상"] += 1
        if n % 100 == 0:
            commit(conn)
            print(f"    {n:,}/{len(todo):,} … 정상 {got['정상']:,}")
        time.sleep(float(cfg.get("interval_sec") or 1.2))
    commit(conn)
    print("★ 상세 — " + " · ".join(f"{k} {v:,}" for k, v in got.items()))
    left = conn.execute("SELECT COUNT(*) FROM core_listing WHERE site=?",
                        (SITE_CODE,)).fetchone()[0]
    print(f"★ 저장된 KB 매물 — {left:,}건")
    conn.close()
    from tools.daily_enqueue import enqueue_after_store
    enqueue_after_store(os.path.join(ROOT, "carwatch.db"), SITE_CODE,
                        got.get("정상", 0))
    return 0


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

    if "--narrow" in args:
        groups = load_filters()
        seen: set = set()
        print(f"★ 좁혀 받는다 — 차종 {len(groups)}종 (전체 164,490 중)")
        by_group = []
        for g in groups:
            r = walk_group(adapter, cfg, g, seen)
            mark = "" if r["ids"] else "  ★ 0건이다"
            print(f"  {g['for']:12} maker={g['makerCode']} class={g['classCode']}"
                  f"  {r['pages']:>3}쪽 · 매물 {len(r['ids']):>4}"
                  f" (규격 {g.get('expect', '—')})  봇차단 {r['walls']}{mark}")
            by_group.append((g, r["ids"]))
        print(f"★ 합 {len(seen):,}건  (규격 2,084 — ★ 그것은 쪽마다의 합이다.  "
              f"★ 겹친 것을 뺀 수가 이것이다)")
        if "--dry" in args:
            print("★ --dry 라 저장하지 않았다")
            return 0
        # ★ 간격 — ★ 오래 이어 부르면 ★ 사이트가 막는다 (실측 08-23 — 100건 뒤 전건 차단).
        #   ★ 규격 1-1 「한 번에 다 받으려 하지 마라.  여러 회차에 나눠 채운다」
        gap = opt("--interval", 0)
        if gap:
            cfg = dict(cfg, interval_sec=gap)
        # ★ 회차 상한 — ★ 안 주면 200 이다 (명령서 14-1).  ★ 0 을 주면 전량이다
        want = opt("--detail", DETAIL_BATCH)
        return store_details(adapter, cfg, [i for _g, ids in by_group
                                            for i in ids], want)

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
