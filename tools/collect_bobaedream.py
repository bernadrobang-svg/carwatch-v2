#!/usr/bin/env python3.11
"""보배드림 수집 (명령서 7단계 · `docs/BOBAEDREAM_API.md`).

    python3.11 tools/collect_bobaedream.py --pages N [--dry] [--interval S]

지시서   `docs/BOBAEDREAM_API.md` · 명령서 3-0 「전량을 받지 않는다」
근거     ★ 목록이 ★ 차명을 준다 — ★ 우리 차종만 골라 ★ 상세를 받는다.
        ★ `maker_no` 코드표는 ★ facet 을 못 받았다 (규격 5장) — ★ 지어내지 않는다.
        ★ 대신 ★ 목록의 차명으로 ★ 미리 거른다.  ★ 상세를 3,307번 부르지 않는다
값규칙   ★ 「무사고」 문구를 ★ 쓰지 않는다 — ★ 판매자 글이다 (규격 3장 ①)
        ★ 보험이력 「미공개」는 ★ NULL 이다.  ★ 0 이 아니다
금지     ★ `www.` 로 부르는 것 (EUC-KR · 다른 화면이다)
"""
from __future__ import annotations

import os
import sys
import time
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from adapters.bobaedream import (  # noqa: E402
    SITE_CODE,
    BobaedreamAdapter,
    load_config,
)
from parse.bobaedream.mapping import list_items, parse_detail  # noqa: E402
from store.dictionary import target_map  # noqa: E402
from store.raw import open_db  # noqa: E402

MAX_PAGES = 80


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get(url: str, headers: dict, timeout: float) -> str | None:
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as f:   # noqa: S310
            # ★ 모바일은 UTF-8 이다 (규격 1장).  ★ PC(EUC-KR)와 섞지 않는다
            return f.read().decode("utf-8", "replace")
    except OSError:
        return None


def target_names(root: str = ROOT) -> list:
    """우리가 보는 차종 이름.  ★ `target_map.json` 이 정본이다 — ★ 코드에 안 박는다."""
    out = set()
    for site in target_map():
        for name in target_map(site):
            out.add(name)
    return sorted(out, key=len, reverse=True)


def wanted(title: str, names: list) -> str | None:
    """목록의 차명에 ★ 우리 차종 이름이 들어 있는가.  ★ 없으면 None."""
    for n in names:
        if n and n in (title or ""):
            return n
    return None


def _elapsed(year_month: str | None, at: datetime) -> int | None:
    if not year_month or len(str(year_month)) < 6:
        return None
    y, m = int(str(year_month)[:4]), int(str(year_month)[4:6])
    return max(0, (at.year - y) * 12 + (at.month - m))


def load_filters(root: str = ROOT) -> list:
    """좁히는 코드 — ★ `targets.json` 의 `site_query` 가 정본이다 (명령서 3-1).

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
        if not isinstance(q, dict) or not q.get("maker_no"):
            continue
        mark = (q["maker_no"], q.get("model_no"))
        if mark in seen:
            continue
        seen.add(mark)
        got.append({"for": key, "maker_no": q["maker_no"],
                    "model_no": q.get("model_no")})
    return got


def _walk_plan(groups: list, pages: int):
    """★ 어느 조건으로 ★ 몇 쪽까지 도는가.  ★ 조건이 없으면 ★ 전량이다."""
    if not groups:
        for page in range(1, pages + 1):
            yield None, page
        return
    for g in groups:
        for page in range(1, pages + 1):
            yield g, page


def main() -> int:
    args = sys.argv[1:]

    def opt(name: str, default):
        if name in args:
            i = args.index(name)
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                return type(default)(args[i + 1])
        return default

    cfg = load_config(ROOT)
    gap = opt("--interval", 0.0) or float(cfg.get("interval_sec") or 1.2)
    adapter = BobaedreamAdapter(cfg)
    names = target_names()
    pages = opt("--pages", 5)
    groups = load_filters()
    if groups:
        print(f"★ 좁혀 받는다 — 차종 {len(groups)}종 "
              f"(maker_no ＋ model_no · 가이드 확인 08-25)")
    else:
        print(f"★ 우리 차종 이름 {len(names)}가지로 목록에서 미리 거른다")

    hits, seen, scanned = [], set(), 0
    for g, page in _walk_plan(groups, min(pages, MAX_PAGES)):
        req = adapter.list_url(None, page=page,
                              maker=g.get("maker_no") if g else None,
                              model=g.get("model_no") if g else None)
        body = _get(req.url, req.headers, req.timeout_sec)
        if body is None:
            print(f"  {page}쪽 — ★ 못 받았다.  ★ 저장하지 않는다")
            break
        got = list_items(body)
        if not got:
            break
        for no, title in got:
            if no in seen:
                continue
            seen.add(no)
            scanned += 1
            name = wanted(title, names)
            if name:
                hits.append((no, title, name))
        time.sleep(gap)
    print(f"목록 {page}쪽 · 훑은 매물 {scanned}건 · ★ 우리 차종 {len(hits)}건")
    for no, title, name in hits[:10]:
        print(f"    {no}  [{name}] {title[:44]}")
    if not hits:
        print("★ 이 쪽들에 우리 차종이 없다")
        return 0
    if "--dry" in args:
        print("★ --dry 라 상세를 안 받았다")
        return 0

    from store.core import resolve_listing_id, split_pii, upsert_core
    from store.pii import load_key
    from store.raw import commit

    conn = open_db(os.path.join(ROOT, "carwatch.db"))
    at, key = _now(), load_key()
    now = datetime.now(timezone.utc)
    kept = {"저장": 0, "못 받음": 0, "리스·렌트": 0}
    for no, _title, _name in hits:
        d = adapter.detail_urls(no)[0]
        html = _get(d.url, d.headers, d.timeout_sec)
        if not html:
            kept["못 받음"] += 1
            continue
        deep = parse_detail(html, SITE_CODE, no)
        if not deep:
            kept["못 받음"] += 1
            continue
        # ★ 보증은 ★ 전체 기간이라 ★ 연식과 빼야 잔여가 된다 (규격 3a ③)
        deep = parse_detail(html, SITE_CODE, no,
                            _elapsed(deep.get("year_month"), now))
        # ★ 상세에 ★ 차종 칸이 없다 — ★ 목록에서 고른 이름을 넣는다.
        #   ★ 지어낸 것이 아니라 ★ 목록이 준 차명에서 ★ 짚은 것이다
        deep["site_model"] = _title
        deep["site_model_group"] = _name
        if deep.get("sell_type") == "리스":
            kept["리스·렌트"] += 1
        deep.pop("_insurance_cnt", None)
        deep.pop("_repair_cnt", None)
        deep["listing_id"] = resolve_listing_id(conn, SITE_CODE, no, at)
        deep["detail_status"] = "ok"
        upsert_core(conn, split_pii(conn, deep, SITE_CODE, key, at), at)
        kept["저장"] += 1
        time.sleep(gap)
    commit(conn)
    print("★ " + " · ".join(f"{k} {v}" for k, v in kept.items()))
    conn.close()
    from tools.daily_enqueue import enqueue_after_store
    enqueue_after_store(os.path.join(ROOT, "carwatch.db"), SITE_CODE,
                        kept.get("저장", 0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
