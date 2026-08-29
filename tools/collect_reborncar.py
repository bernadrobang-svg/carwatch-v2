# -*- coding: utf-8 -*-
"""리본카 수집 — 사이트맵 전량 → 우리 쪽에서 거른다 (명령서 39).

쓰기   python3.11 tools/collect_reborncar.py --count     몇 건인지만
      python3.11 tools/collect_reborncar.py             전량 (1,036건)
      python3.11 tools/collect_reborncar.py --limit 50  앞에서 N건만
      python3.11 tools/collect_reborncar.py --missing-raw  ★ 원문이 없는 우리 차종만 (P3)
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
from parse.target_rules import fill_target_key  # noqa: E402
from store.dictionary import known_model_of                    # noqa: E402
from store.raw import link_raws as raw_link_raws  # noqa: E402
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
    # ★★★ 08-29 (개정 838) — ★ 「끝까지 받았나」.
    #   ★ 리본카는 ★ **사이트맵 한 번**으로 전부를 준다 — ★ 쪽넘김이 없다.
    #   ★ 그러나 ★ `--limit` 으로 자르면 ★ 전부가 아니다 — ★ 그때는 안 매긴다
    _done = bool(got)
    _all_ids = set(got)
    if "--limit" in args:
        i = args.index("--limit")
        if i + 1 < len(args) and args[i + 1].isdigit():
            got = got[:int(args[i + 1])]
            _done = False

    from store.core import resolve_listing_id, split_pii, upsert_core
    from store.pii import load_key
    from store.raw import commit, save_site_raw

    conn = open_db(os.path.join(ROOT, "carwatch.db"))
    at, pii_key = _now(), load_key()
    done = {r[0] for r in conn.execute(
        "SELECT source_id FROM core_listing WHERE site=? AND detail_status='ok'",
        (SITE_CODE,))}
    # ★★★ 08-26 — ★ `--missing-raw` : ★ **원문이 없는 것만** 다시 받는다 (P3).
    #   ★ 실측 08-26 — ★ `detail_status='ok'` 가 ★ 1,045건인데
    #     ★ ★ `raw_response` 는 ★ **23건**뿐이었다.  ★ 우리 21종 72건은 ★ **0건**이다.
    #   ★ ★ 원문이 없으면 ★ **다시 캘 수가 없다** — ★ 사진도 축도 못 뽑는다.
    #     ★ ★ 「원문은 남긴다.  갈래를 넓히시면 다시 판다」(명령서 3-2)가 안 지켜졌다.
    #   ★ 전량을 다시 받지 않는다 — ★ **원문이 빈 것만**이다
    if "--missing-raw" in args:
        have = {r[0] for r in conn.execute(
            "SELECT source_id FROM raw_response WHERE site=? AND endpoint='detail'",
            (SITE_CODE,))}
        ours_keys = {r[0] for r in conn.execute(
            "SELECT source_id FROM core_listing"
            " WHERE site=? AND target_key IS NOT NULL", (SITE_CODE,))}
        todo = [c for c in got if c in ours_keys and c not in have]
        print(f"★ 원문이 없는 우리 차종 {len(todo):,}건만 다시 받는다"
              f" (원문 있는 것 {len(have):,}건 · 우리 차종 {len(ours_keys):,}건)")
    else:
        # ★★★★★ 08-29 (ORDER r879 1d) — ★ 「이미 받았나」를 ★ **원문으로** 가른다.
        #   ★ 앞서는 `detail_status='ok'` 로 갈랐다.  ★ 그런데 실측 08-29 —
        #   ★ ★ `detail_status='ok'` **1,106건** vs ★ 상세 원문 **301건**.
        #   ★ ★ **805건이 「받았다」고 서 있는데 원문이 없다** — ★ 다시 캘 수가 없고
        #   ★ ★ 그래서 ★ `target_key` 가 ★ 1,107 중 **72건**뿐이다 (차종 미정 1,035).
        #   ★ 원문이 정본이다 (명령서 3-2 「원문은 남긴다.  갈래를 넓히시면 다시 판다」).
        #   ★ ★ KB 도 08-29 에 같은 까닭으로 고쳤다 (개정 857)
        have = {r[0] for r in conn.execute(
            "SELECT source_id FROM raw_response WHERE site=? AND endpoint='detail'",
            (SITE_CODE,))}
        todo = [c for c in got if c not in have]
        print(f"★ 상세 — 받을 것 {len(todo):,}건"
              f" (원문이 있는 것 {len(have):,}건은 건너뛴다)")
        if len(done) > len(have):
            print(f"  ★ `detail_status='ok'` 는 {len(done):,}건인데 "
                  f"원문은 {len(have):,}건이다 — {len(done) - len(have):,}건이 "
                  "「받았다」고 서 있으나 원문이 없다 (그래서 다시 받는다)")
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
        # ★★ 원문을 ★ 먼저 남긴다 (명령서 3-2 필수) — ★ 「갈래를 넓히시면 다시 판다」.
        #   ★ 파싱보다 앞에 둔다 — ★ 파싱이 실패해도 ★ 원문은 남아야 한다
        save_site_raw(conn, SITE_CODE, "detail", one,
                      cfg["base_url"] + cfg["paths"]["detail"].format(
                          source_id=one), html, at)
        # ★★ 08-29 (개정 857) — ★ 곧바로 커밋한다.
        #   ★ 통신·`sleep` 이 ★ 트랜잭션 안에 들면 ★ 잠금 창이 분 단위가 된다
        #   (KB 실측 — 100건 × 1.2초 = 120초 · 잠금 38.4초 · locked 로 죽었다)
        commit(conn)
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
            # ★ 넣기 직전에 ★ 차종을 붙인다 (마스터 지시 08-30) — ★ 안 붙이면 판정에 안 들어간다
            fill_target_key(SITE_CODE, deep)
            upsert_core(conn, split_pii(conn, deep, SITE_CODE, pii_key, at), at)
        # ★ 자기 전에 커밋한다 — ★ 넣기가 sleep 을 넘지 않게 (개정 857)
        commit(conn)
        time.sleep(interval)
    commit(conn)
    # ★★★★★ 08-29 (개정 838 · 오판 161) — ★ 팔린 차를 거른다 (`S46-117`)
    from store.core import sweep_gone_groups

    # ★ 넣기가 끝났다 — ★ 원문을 매물에 잇는다 (S46-97 · 08-29)
    raw_link_raws(conn, SITE_CODE)
    _got = sweep_gone_groups(conn, SITE_CODE, [(_done, _all_ids)], at)
    print(f"★ 목록에 없어 gone 으로 매긴 것 {sum(_got.values())}건 "
          f"({len(_got)}차종) · 끝까지 받았나 {'예' if _done else '아니오'}")
    print("★ 상세 — " + " · ".join(f"{k} {v}" for k, v in seen.items()))
    print(f"★ 우리 대상 — {ours}건 / {len(todo)}건 "
          f"· ★ 안 넣은 것 {skipped}건 (원문은 남는다)")
    n = conn.execute("SELECT COUNT(*) FROM core_listing WHERE site=?",
                     (SITE_CODE,)).fetchone()[0]
    print(f"★ 저장된 리본카 매물 — {n:,}건")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
