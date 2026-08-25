# -*- coding: utf-8 -*-
"""헤이딜러 수집 — 토큰 → 차종별 목록 → 상세 (명령서 37).

쓰기   python3.11 tools/collect_heydealer.py            차종 15종 전부
      python3.11 tools/collect_heydealer.py --dry      받기만 하고 저장 안 함
      python3.11 tools/collect_heydealer.py --target XC60_IMPORT
★ 토큰은 바퀴마다 새로 받는다 (JWT).  ★ 저장소에 안 적는다 (명령서 37-3)
★ 한 쪽에 10건이 상한이다 — 10 이면 다음 쪽으로 간다
★ 연료는 목록에 없다 — ★ 상세를 받아야 fuel_match 가 걸린다
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

from adapters.heydealer import PAGE_SIZE, SITE_CODE, HeydealerAdapter  # noqa: E402
from parse.heydealer.mapping import (parse_detail, parse_list_item,   # noqa: E402
                                     options_of)
from store.raw import open_db                                          # noqa: E402

MAX_PAGES = 40          # ★ 안전장치.  ★ 10건 미만이 오면 그 전에 멈춘다


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get(req) -> tuple[int, object]:
    r = urllib.request.Request(req.url, headers=req.headers)
    try:
        with urllib.request.urlopen(r, timeout=req.timeout_sec) as res:
            raw = res.read()
            return res.status, json.loads(raw)
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception:
        return 0, None


def _targets(args: list) -> list:
    with open(os.path.join(ROOT, "config", "targets.json"), encoding="utf-8") as f:
        rows = json.load(f)
    want = None
    if "--target" in args:
        i = args.index("--target")
        want = {a for a in args[i + 1:] if not a.startswith("--")}
    out = []
    for key, one in rows.items():
        if key.startswith("_") or not isinstance(one, dict):
            continue
        q = (one.get("site_query") or {}).get(SITE_CODE)
        if not q or (want and key not in want):
            continue
        out.append((key, q if isinstance(q, list) else [q]))
    return out


def walk(adapter, key: str, queries: list, interval: float) -> list:
    """한 차종의 매물 전부.  ★ 해시가 둘이면 둘 다 돈다 (G80·그랜저)."""
    seen, rows = set(), []
    for q in queries:
        pick = {k: q[k] for k in ("brand", "model-group", "model") if q.get(k)}
        for page in range(1, MAX_PAGES + 1):
            code, body = _get(adapter.list_url(None, page, pick))
            if code != 200 or not isinstance(body, list):
                print(f"    {key} {q.get('_차명', '')} {page}쪽 — ★ {code} · 멈춘다")
                break
            for one in body:
                got = parse_list_item(one, SITE_CODE)
                if got and got["source_id"] not in seen:
                    seen.add(got["source_id"])
                    rows.append(got)
            if len(body) < PAGE_SIZE:
                break
            time.sleep(interval)
    return rows


def main() -> int:
    args = sys.argv[1:]
    with open(os.path.join(ROOT, "config", "endpoints.json"), encoding="utf-8") as f:
        cfg = json.load(f)[SITE_CODE]
    adapter = HeydealerAdapter(cfg)
    adapter.token()                       # ★ 바퀴마다 새로 받는다
    interval = float(cfg.get("interval_sec") or 0.5)

    targets = _targets(args)
    print(f"★ 헤이딜러 — 차종 {len(targets)}종")
    got_all: dict = {}
    for key, queries in targets:
        rows = walk(adapter, key, queries, interval)
        for r in rows:
            got_all[r["source_id"]] = r
        print(f"  {key:<16} 매물 {len(rows):>4}")
    print(f"★ 목록 합 {len(got_all):,}건 (겹친 것을 뺀 수)")
    if "--dry" in args:
        print("★ --dry 라 저장하지 않았다")
        return 0

    from store.core import resolve_listing_id, split_pii, upsert_core
    from store.pii import load_key
    from store.raw import commit, save_site_raw

    conn = open_db(os.path.join(ROOT, "carwatch.db"))
    at, pii_key = _now(), load_key()
    for one in got_all.values():
        one["listing_id"] = resolve_listing_id(conn, SITE_CODE,
                                               one["source_id"], at)
        upsert_core(conn, split_pii(conn, one, SITE_CODE, pii_key, at), at)
    commit(conn)
    print(f"★ 목록 저장 {len(got_all):,}건 · site='{SITE_CODE}'")

    # ★ 상세 — ★ 연료·차량번호가 여기에만 있다.  ★ 전건 받는다
    done = {r[0] for r in conn.execute(
        "SELECT source_id FROM core_listing WHERE site=? AND detail_status='ok'",
        (SITE_CODE,))}
    todo = [o for o in got_all.values() if o["source_id"] not in done]
    print(f"★ 상세 — 받을 것 {len(todo)}건 (이미 받은 것 {len(done)}건은 건너뛴다)")
    seen = {"정상": 0, "못 받음": 0}
    for one in todo:
        code, body = _get(adapter.detail_urls(one["source_id"])[0])
        if code != 200 or not isinstance(body, dict):
            seen["못 받음"] += 1
            time.sleep(interval)
            continue
        # ★★ 원문을 ★ 먼저 남긴다 (명령서 3-2 필수) — ★ 「갈래를 넓히시면 다시 판다」
        save_site_raw(conn, SITE_CODE, "detail", one["source_id"],
                      adapter.detail_urls(one["source_id"])[0].url,
                      json.dumps(body, ensure_ascii=False), at)
        deep = parse_detail(body, SITE_CODE, one["source_id"])
        if deep:
            # ★★ 옵션을 ★ **한글 이름으로** 저장한다 (명령서 B · 08-25).
            #   ★ 엔카는 ★ 숫자 코드만 준다 — ★ 헤이딜러가 ★ 이름을 준다.
            #   ★ ★ 이것이 ★ `option_names.json` 의 밑감이다
            got = options_of(body)
            if got:
                deep["options_standard_json"] = json.dumps(
                    [x["name"] for x in got if x["loaded"]], ensure_ascii=False)
                deep["options_etc_json"] = json.dumps(
                    [x["name"] for x in got if not x["loaded"]],
                    ensure_ascii=False)
            deep["listing_id"] = one["listing_id"]
            deep["detail_status"] = "ok"
            upsert_core(conn, split_pii(conn, deep, SITE_CODE, pii_key, at), at)
            seen["정상"] += 1
        time.sleep(interval)
    commit(conn)
    print("★ 상세 — " + " · ".join(f"{k} {v}" for k, v in seen.items()))
    n = conn.execute("SELECT COUNT(*) FROM core_listing WHERE site=?",
                     (SITE_CODE,)).fetchone()[0]
    print(f"★ 저장된 헤이딜러 매물 — {n:,}건")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
