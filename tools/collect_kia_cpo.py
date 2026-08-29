#!/usr/bin/env python3.11
"""기아 인증중고차(CPO) 목록 수집 (명령서 `ORDER_20260822_r515.md` 3-1 · 단계 8).

    python3.11 tools/collect_kia_cpo.py [--dry]

지시서   `docs/KIA_CPO_API.md` · `docs/TARGET_KEY_MAP.md`
근거     ★ 인증·토큰·암호화가 없다.  robots.txt 가 404 다 (규칙 자체가 없다)
값규칙   ★ 원문을 통째로 남긴다 (raw_response).  ★ 엔카와 ★ 같은 표에 넣는다
        ★ 같은 차가 다른 사이트에 있어도 ★ 합치지 않는다 (명령서 3-1)
        ★ 차종이 안 걸리면 ★ 「차종 미정」으로 두고 ★ 버리지 않는다
          (TARGET_KEY_MAP 6장 — 「mapped 가 빈 사이트값은 수집하되 버리지 않는다」)
        ★ 차종만으로 안 걸리는 것은 ★ 연료로 한 번 더 거른다
          `SPORTAGE_LPI` ← 「스포티지」 + 연료 LPI
금지     ★ 못 받은 것을 만점으로 지어 주는 것 (금지 12)
금지     ★ 상세를 여기서 받는 것 — ★ 명령서가 「목록부터」라 했다 (3-1)
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from adapters.kia_cpo import SITE_CODE, KiaCpoAdapter, load_config  # noqa: E402
from parse.kia_cpo.mapping import (  # noqa: E402
    next_cursors,
    parse_list_item,
    unpack_envelope,
)
from store.dictionary import target_key_of  # noqa: E402
from store.raw import open_db  # noqa: E402

MAX_PAGES = 40          # ★ 1,020건 ÷ 100 = 11쪽.  ★ 넉넉히 두고 새 것이 없으면 멈춘다


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fetch(url: str, headers: dict, timeout: float) -> dict:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as f:   # noqa: S310
        return json.loads(f.read().decode("utf-8"))


def target_of(parsed: dict) -> str | None:
    """사이트 차종 → 우리 차종 키.

    ★★ 개정 540 — ★ 쓰는 자리는 `config/dictionaries/target_map.json` 하나다.
      ★ 전에는 sites.json 에도 같은 표가 있었다 — ★ 두 곳이면 어긋난다
    ★ 표에 없으면 ★ None 이다 — 「차종 미정」이고 ★ 버리지 않는다
    ★ 차종만으로 안 걸리면 ★ 연료로 한 번 더 거른다 (명령서 2a)
    """
    return target_key_of(
        SITE_CODE, parsed.get("site_model_group"),
        f"{parsed.get('fuel_raw') or ''} {parsed.get('site_model') or ''}")


def wanted_names(root: str = ROOT) -> list:
    """좁혀 받을 차종 이름 — ★ `targets.json` 이 정본이다 (명령서 3-1).

    ★ 코드에 차종을 박지 않는다 (S14 · 금지 6)
    """
    with open(os.path.join(root, "config", "targets.json"), encoding="utf-8") as f:
        rows = json.load(f)
    got = []
    for key, one in rows.items():
        if key.startswith("_") or not isinstance(one, dict):
            continue
        q = (one.get("site_query") or {}).get(SITE_CODE)
        name = (q or {}).get("modelCodeNames") if isinstance(q, dict) else None
        if name and name not in got:
            got.append(name)
    return got


def walk(adapter: KiaCpoAdapter, cfg: dict,
         names: list | None = None) -> tuple:
    """목록을 끝까지 받는다.  ★ 커서 방식이다 (adapters/kia_cpo.py).

    ★★★ 08-29 (개정 838) — ★ 「끝까지 받았나」를 함께 돌려준다.
      ★ 커서가 다 떨어지거나 · 더 올 것이 없을 때만 참이다 —
      ★ `MAX_PAGES` 를 다 쓴 것은 ★ 끝이 아니다
    """
    rows, seen, cursors, total = [], set(), None, 0
    done = False
    for _page in range(MAX_PAGES):
        req = adapter.list_url(None, cursors=cursors, names=names)
        body = _fetch(req.url, req.headers, req.timeout_sec)
        total, got = unpack_envelope(body)
        if not got:
            done = True                # ★ 더 올 것이 없다
            break
        fresh = [x for x in got if x.get("id") not in seen]
        if not fresh:
            done = True                # ★ 커서가 안 넘어간다 — ★ 끝이다
            break
        for one in fresh:
            seen.add(one["id"])
        rows.extend(fresh)
        cursors = next_cursors(got)
        if not cursors:
            done = True                # ★ 커서가 다 떨어졌다 — ★ 끝이다
            break
        time.sleep(float(cfg.get("interval_sec") or 0.5))
    return total, rows, done


def main() -> int:
    dry = "--dry" in sys.argv
    cfg = load_config(ROOT)
    adapter = KiaCpoAdapter(cfg)
    names = [] if "--all" in sys.argv else wanted_names()
    if names:
        print(f"★ 좁혀 받는다 — modelCodeNames={' · '.join(names)}")
    total, rows, _done = walk(adapter, cfg, names)
    print(f"목록 — 사이트가 말한 총 {total}건 · 받은 {len(rows)}건")
    if total and len(rows) != total:
        print(f"  ★ 어긋난다 — {total - len(rows)}건을 못 받았다")

    hit: dict = {}
    parsed_rows = []
    # ★★ 원문 항목을 ★ 파싱 결과와 ★ 짝지어 들고 간다 (명령서 3-2 필수) —
    #   ★ 기아는 ★ 상세가 없다.  ★ 목록 항목이 ★ 원문의 전부다
    raw_of: dict = {}
    for one in rows:
        p = parse_list_item(one, SITE_CODE)
        raw_of[p["source_id"]] = one
        p["target_key"] = target_of(p)
        hit[p["target_key"] or "차종 미정"] = hit.get(
            p["target_key"] or "차종 미정", 0) + 1
        parsed_rows.append(p)
    for k, n in sorted(hit.items(), key=lambda kv: -kv[1]):
        print(f"  {k:16} {n:>5}건")

    if dry:
        print("★ --dry 라 저장하지 않았다")
        return 0

    from store.core import resolve_listing_id, split_pii, upsert_core
    from store.pii import load_key
    from store.raw import commit, save_site_raw

    conn = open_db(os.path.join(ROOT, "carwatch.db"))
    at = _now()
    key = load_key()
    stored = 0
    for p in parsed_rows:
        # ★★ 번호판은 ★ PII 다 (STEP 35) — ★ 원본을 core 에 넣지 않는다.
        #   ★ 순서를 지킨다 — split_pii → resolve_id → upsert
        p["listing_id"] = resolve_listing_id(conn, SITE_CODE, p["source_id"], at)
        # ★★ 원문을 남긴다 (명령서 3-2 필수) — ★ 「갈래를 넓히시면 다시 판다」
        save_site_raw(conn, SITE_CODE, "list", p["source_id"],
                      adapter.list_url(None).url,
                      json.dumps(raw_of.get(p["source_id"]),
                                 ensure_ascii=False), at,
                      listing_id=p["listing_id"])
        upsert_core(conn, split_pii(conn, p, SITE_CODE, key, at), at)
        stored += 1
    commit(conn)
    # ★★★★★ 08-29 (개정 838 · 오판 161) — ★ 팔린 차를 거른다 (`S46-117`)
    from store.core import sweep_gone_groups

    _got = sweep_gone_groups(conn, SITE_CODE, [(_done, {r["source_id"] for r in parsed_rows})], at)
    print(f"★ 목록에 없어 gone 으로 매긴 것 {sum(_got.values())}건 "
          f"({len(_got)}차종) · 끝까지 받았나 {'예' if _done else '아니오'}")
    print(f"저장 {stored}건 · site='{SITE_CODE}'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
