# -*- coding: utf-8 -*-
"""★★★★★ 08-31 (로드맵 차례 5 · `V1-23`) — ★ **안 부른 카탈로그를 받는다.**

★ 잰 것 [실측 08-31] — ★ 필요한 조합 **747** 중 ★ 받은 것 **127 (17.0%)**.
  ★ ★ 못 받은 까닭이 셋인데 ★ **598조합이 `not_called`** 다 — ★ 우리 잘못이다.
    ★ ★ 그 조합을 가진 매물이 ★ **4,540건** 이고 ★ **전건 `active` · 전건 차종이 있다.**
  ★ 나머지 — ★ `empty` 21조합 (사이트가 빈 배열을 준다) · `not_found` 1조합

★★ 왜 안 불렀나 — ★ `S7` 은 ★ 회차의 **차종 범위 안에서만** 부른다 (`_scope`).
  ★ ★ 회차마다 차종을 갈라 돌므로 ★ 다른 차종의 조합은 ★ 그 회차에 안 불린다.
  ★ ★ 그것이 쌓여 ★ 598 이 됐다 — ★ **한 번 몰아서 받으면 닫힌다**

★★★ ★ `S7` 과 **같은 꼴**로 남긴다 —
  ★ 부르는 열쇠는 ★ **매물 ID** · ★ 저장하는 열쇠는 ★ **모델 카탈로그 키**다 (STEP 22).
  ★ 대표를 여럿 든다 — ★ 하나가 404 여도 ★ 조합이 없는 것이 아니다 (개정 327)

돌리는 법
    python3.11 tools/fetch_missing_catalog.py            ★ 잰다
    python3.11 tools/fetch_missing_catalog.py --write    ★ 받는다
    python3.11 tools/fetch_missing_catalog.py --write --limit 50
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from store.core import catalog_coverage  # noqa: E402

REPS = 3            # ★ 대표 셋까지 물어본다 (개정 327)
SLEEP = 0.8


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _status(code: int, body: bytes) -> str:
    """★ 봉투의 뜻.  ★ `S7` 이 쓰는 낱말과 같게 둔다."""
    if code == 404:
        return "not_found"
    if code != 200:
        return "error"
    text = (body or b"").decode("utf-8", "replace").strip()
    if text in ("", "[]", "{}"):
        return "empty"          # ★ 사이트가 「없다」고 답했다 — ★ 우리 잘못이 아니다
    return "ok"


def main() -> int:
    args = sys.argv[1:]
    write = "--write" in args
    limit = 0
    if "--limit" in args:
        i = args.index("--limit")
        if i + 1 < len(args) and args[i + 1].isdigit():
            limit = int(args[i + 1])

    from adapters.encar import EncarAdapter

    conn = sqlite3.connect(os.path.join(ROOT, "carwatch.db"), timeout=60)
    conn.execute("PRAGMA busy_timeout = 60000")
    cov = catalog_coverage(conn)
    miss = sorted(cov["why"].get("not_called") or ())
    need, ok = cov["need"], cov["ok"]
    print(f"★ 필요한 조합 {len(need):,} · 받은 것 {len(ok & need):,}"
          f" = {len(ok & need) / max(len(need), 1) * 100:.1f}%")
    print(f"★ 안 부른 조합 {len(miss):,}"
          f" · 매물 {sum(cov['weight'].get(k, 0) for k in miss):,}건")
    if not miss:
        return 0

    # ★ 조합마다 ★ 대표 매물을 든다 — ★ 부르는 열쇠는 매물 ID 다
    reps: dict = {}
    marks = ",".join("?" * len(miss))
    # ★★★★★ 08-31 — ★ **엔카 매물만 대표로 쓴다.**
    #   ★ 창구가 ★ 엔카 것이다 (`api.encar.com/v1/readside/vehicles/car/{id}`).
    #   ★★ 08-31 (차례 2) 에 ★ 아홉 사이트에도 `model_catalog_key` 를 이었더니
    #     ★ ★ 헤이딜러 매물번호(`2yM25bnW`)가 ★ 대표로 뽑혀 ★ 엔카에 들어갔다 →
    #     ★ ★ ★ **HTTP 400**.  ★ `V1-23` 의 `error` 3조합이 그것이었다 [실측 08-31]
    #   ★ 운영 `S7` 은 ★ `_scope` 가 ★ `site = ?` 를 붙여 안 걸린다 —
    #     ★ ★ 이 도구만 ★ 안 걸러 두고 있었다
    for k, sid in conn.execute(
        f"SELECT model_catalog_key, source_id FROM core_listing"
        f" WHERE model_catalog_key IN ({marks}) AND status='active'"
        f"   AND site='encar'"
        f" ORDER BY source_id", tuple(miss)
    ):
        reps.setdefault(k, []).append(sid)
    keys = [k for k in miss if reps.get(k)]
    if limit:
        keys = keys[:limit]
    print(f"★ 받을 조합 {len(keys):,}" + ("" if write else "  ★ 재기만 한다"))
    if not write:
        return 0

    with open(os.path.join(ROOT, "config", "endpoints.json"),
              encoding="utf-8") as f:
        cfg = json.load(f)["encar"]
    adapter = EncarAdapter(cfg)
    got: Counter = Counter()
    at = _now()
    for n, key in enumerate(keys, 1):
        code = st = None
        body = b""
        url = ""
        for sid in reps[key][:REPS]:
            req = adapter.catalog_url(str(sid))
            url = req.url
            try:
                with urllib.request.urlopen(
                        urllib.request.Request(url, headers=req.headers),
                        timeout=float(cfg.get("timeout_sec") or 30)) as res:
                    code, body = res.status, res.read()
            except urllib.error.HTTPError as e:
                code, body = e.code, e.read()
            except (urllib.error.URLError, OSError, TimeoutError) as e:
                got[f"못 받음 ({type(e).__name__})"] += 1
                time.sleep(SLEEP * 2)
                continue
            st = _status(code, body)
            if st != "not_found":
                break
            # ★ 이 매물만 사라진 것일 수 있다 — ★ 다음 대표로 다시 묻는다
            time.sleep(SLEEP)
        if st is None:
            time.sleep(SLEEP)
            continue
        got[st] += 1
        conn.execute(
            "INSERT INTO raw_response(run_id,site,listing_id,source_id,endpoint,"
            " request_url,request_meta,http_code,response_meta,status,body,"
            " origin,fetched_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (f"catalog-{at[:19]}", "encar", None, key, "catalog", url, None,
             code, None, st, body.decode("utf-8", "replace"),
             "collector", _now()))
        conn.commit()
        if n % 50 == 0:
            print(f"   {n}/{len(keys)} · " + " · ".join(
                f"{k} {v}" for k, v in got.most_common()))
        time.sleep(SLEEP)
    print("★ " + " · ".join(f"{k} {v}" for k, v in got.most_common()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
