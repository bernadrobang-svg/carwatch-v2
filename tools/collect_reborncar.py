# -*- coding: utf-8 -*-
"""리본카 수집 — 사이트맵 전량 → 우리 쪽에서 거른다 (명령서 39).

쓰기   python3.11 tools/collect_reborncar.py --count     몇 건인지만
      python3.11 tools/collect_reborncar.py             전량 (1,036건)
      python3.11 tools/collect_reborncar.py --limit 50  앞에서 N건만
★ 목록 API 는 robots 가 막았다 — ★ 사이트맵이 목록이다 (1b장)
★ 차종 좁히기가 없다 — ★ K카와 같이 ★ **전량을 받아 우리가 거른다**
★ 모바일 UA 로 받는다 — ★ 데스크톱은 값이 거짓이다 (2a장)
★ 503 이 나면 다시 두드린다 — ★ 한 번 났다가 살아났다 (명령서 39)
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

from parse.reborncar.mapping import parse_detail, title_name   # noqa: E402
from store.dictionary import known_model_of                    # noqa: E402
from store.raw import open_db                                  # noqa: E402

SITE_CODE = "reborncar"
RE_LOC = re.compile(r"<loc>([^<]+)</loc>")
RETRY = 3                 # ★ 503 은 한 번 났다가 살아났다 (명령서 39)
RETRY_WAIT = 3.0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get(url: str, headers: dict, timeout: float) -> str | None:
    for _ in range(RETRY):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as res:
                return res.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code != 503:
                return None
            time.sleep(RETRY_WAIT)
        except Exception:
            return None
    return None


def codes(cfg: dict) -> list:
    """사이트맵에서 매물번호를 뽑는다 (1b장)."""
    raw = _get(cfg["base_url"] + cfg["paths"]["sitemap"],
               cfg["headers"], float(cfg["timeout_sec"]))
    if not raw:
        print("★ 사이트맵을 못 받았다")
        return []
    locs = RE_LOC.findall(raw)
    det = [u for u in locs if "/smartbuy/SB1002/" in u]
    got = sorted({u.rstrip("/").rsplit("/", 1)[-1] for u in det})
    print(f"사이트맵 {len(raw):,}B · <loc> {len(locs):,}개 · "
          f"★ 매물 {len(got):,}건 (중복 {len(det) - len(got)})")
    return got


def main() -> int:
    args = sys.argv[1:]
    with open(os.path.join(ROOT, "config", "endpoints.json"), encoding="utf-8") as f:
        cfg = json.load(f)[SITE_CODE]
    got = codes(cfg)
    if not got:
        return 1
    if "--count" in args:
        return 0
    if "--limit" in args:
        i = args.index("--limit")
        if i + 1 < len(args) and args[i + 1].isdigit():
            got = got[:int(args[i + 1])]

    from store.core import resolve_listing_id, split_pii, upsert_core
    from store.pii import load_key
    from store.raw import commit

    conn = open_db(os.path.join(ROOT, "carwatch.db"))
    at, pii_key = _now(), load_key()
    done = {r[0] for r in conn.execute(
        "SELECT source_id FROM core_listing WHERE site=? AND detail_status='ok'",
        (SITE_CODE,))}
    todo = [c for c in got if c not in done]
    print(f"★ 상세 — 받을 것 {len(todo):,}건 (이미 받은 것 {len(done):,}건은 건너뛴다)")
    interval = float(cfg.get("interval_sec") or 1.0)
    seen = {"정상": 0, "못 받음": 0}
    ours = skipped = 0
    for one in todo:
        html = _get(cfg["base_url"] + cfg["paths"]["detail"].format(source_id=one),
                    cfg["headers"], float(cfg["timeout_sec"]))
        if not html:
            seen["못 받음"] += 1
            time.sleep(interval)
            continue
        deep = parse_detail(html, SITE_CODE, one)
        if deep:
            # ★ 차종은 ★ 우리가 아는 이름이 들어 있는지로 고른다 (K카와 같다)
            known = known_model_of(title_name(html))
            seen["정상"] += 1
            if not known:
                # ★★ 3-2 걸러 저장 (마스터 확정 08-25) — ★ 차종이 안 맞으면
                #   ★ **`core_listing` 에 안 넣는다.**  ★ 좁힐 길이 없는 사이트다
                #   ★ ★ `raw_response` 에는 남는다 — ★ 갈래를 넓히면 다시 판다
                skipped += 1
                time.sleep(interval)
                continue
            deep["site_model_group"] = known
            ours += 1
            deep["detail_status"] = "ok"
            deep["listing_id"] = resolve_listing_id(conn, SITE_CODE, one, at)
            upsert_core(conn, split_pii(conn, deep, SITE_CODE, pii_key, at), at)
        time.sleep(interval)
    commit(conn)
    print("★ 상세 — " + " · ".join(f"{k} {v}" for k, v in seen.items()))
    print(f"★ 우리 대상 — {ours}건 / {len(todo)}건 "
          f"· ★ 안 넣은 것 {skipped}건 (원문은 남는다)")
    n = conn.execute("SELECT COUNT(*) FROM core_listing WHERE site=?",
                     (SITE_CODE,)).fetchone()[0]
    print(f"★ 저장된 리본카 매물 — {n:,}건")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
