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

from parse.target_rules import fill_target_key  # noqa: E402
from store.dictionary import known_model_of        # noqa: E402
from store.raw import link_raws as raw_link_raws  # noqa: E402
# ★★★★★ 09-01 마스터 지시 — ★ 받기는 ★ **파일만** 쓴다 (`S46-204`)
from store.rawfile import save as save_file  # noqa: E402
from store.raw import commit, open_db              # noqa: E402

SITE_CODE = "bmw_bps"
RETRY, RETRY_WAIT = 3, 3.0
# ★★★★★ 08-29 실측 — ★ 20 은 ★ **상한에 걸리는 값**이었다.
#   ★ BMW 전수는 ★ 364건 · 37쪽이다 (쪽당 10건).  ★ 20쪽에서 끊어
#   ★ ★ **164건이 통째로 빠져 있었다**.  ★ 그러면서 「끝까지 받았나」가
#   ★ ★ 거짓이라 ★ gone 도 영영 못 매겼다.
#   ★ 눌러 봤다 — page 21·22·25·30 이 다 새 매물 10건씩을 준다.
#   ★ ★ page 38 이 0건이다 — ★ 거기가 끝이다.
#   ★ 넉넉히 둔다 — ★ 끝은 「빈 쪽」과 「안 늘어남」으로 안다.  상한은 안전판이다
MAX_PAGES = 120
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



def _have_detail(conn) -> set:
    """★ 이미 상세 원문이 있는 매물번호.  ★ `detail_status` 가 아니라 **원문**으로 가른다.

    ★ 08-29 리본카에서 ★ `detail_status='ok'` 1,106건인데 ★ 원문이 301건이었다 —
      ★ ★ 「받았다」고 서 있는데 ★ 다시 캘 수가 없었다.  ★ 같은 실수를 안 한다
    """
    if not hasattr(_have_detail, "_cache"):
        _have_detail._cache = {r[0] for r in conn.execute(
            "SELECT source_id FROM raw_response"
            " WHERE site=? AND endpoint='detail'", (SITE_CODE,))}
    return _have_detail._cache


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
        # ★★ 빈 쪽도 ★ 끝이다 (08-29) — ★ 앞서는 이것을 안 봐서
        #   ★ ★ 상한에 걸려도 ★ 「안 늘어남」이 안 오면 ★ done 이 거짓이었다
        if not RE_ITEM.search(raw):
            done = True
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
    from store.raw import raw_body

    conn = open_db(os.path.join(ROOT, "carwatch.db"))
    at = _now()
    # ★★ 원문을 남긴다 (명령서 3-2 필수) — ★ 「갈래를 넓히시면 다시 판다」.
    #   ★ 쪽마다 한 줄이다 — ★ 매물번호가 없으니 ★ 겹침을 안 접는다
    for _u, _b in pages:
        save_file(SITE_CODE, "list", None, _u, _b, at)
    for r in rows:
        r["listing_id"] = resolve_listing_id(conn, SITE_CODE, r["source_id"], at)
        # ★ 넣기 직전에 ★ 차종을 붙인다 (마스터 지시 08-30) — ★ 안 붙이면 판정에 안 들어간다
        fill_target_key(SITE_CODE, r)
        upsert_core(conn, r, at)
    commit(conn)
    # ★★★★★ 08-29 (개정 838 · 오판 161) — ★ 팔린 차를 거른다 (`S46-117`).
    #   ★ 저장한 **뒤에** 부른다 — ★ 새 매물이 차종을 갖고 있어야 한다.
    #   ★ 「끝까지 받았나」가 거짓이면 ★ 안 매긴다 — 반만 보고 매기면 산 차를 죽인다
    from store.core import sweep_gone_groups

    # ★ 넣기가 끝났다 — ★ 원문을 매물에 잇는다 (S46-97 · 08-29)
    raw_link_raws(conn, SITE_CODE)
    _got = sweep_gone_groups(conn, SITE_CODE, [(done, set(seen))], at)
    print(f"★ 목록에 없어 gone 으로 매긴 것 {sum(_got.values())}건 "
          f"({len(_got)}차종) · 끝까지 받았나 {'예' if done else '아니오'}")

    # ★★★★★ 08-30 (마스터 지시 4 · `BMW_BPS_API.md` 08-29 절) —
    #   ★ **값·주행·연식이 다 상세에 있다.**  ★ 목록 카드에는 없다.
    #   ★ ★ 그래서 화면 BMW 가 ★ 376건 전부 ★ 값·주행·연식이 비어 있었다.
    #   ★ 우리 대상만 받는다 — ★ 전량 364건을 다 받지 않는다 (마스터 확정 3-0)
    from parse.bmw_bps.mapping import inspect_of, parse_detail

    have = _have_detail(conn)
    todo = [r for r in ours if r["source_id"] not in have]
    print(f"★ 상세 — 받을 것 {len(todo)}건 "
          f"(우리 대상 {len(ours)}건 중 · 원문이 있는 것 {len(ours) - len(todo)}건은 안 받는다)")
    got = {"받음": 0, "못 받음": 0, "원문에서 다시 넣음": 0}
    for one in ours:
        sid = one["source_id"]
        if sid in have:
            # ★★ 안 받는다.  ★ 그러나 ★ **넣기는 한다** — ★ 파서가 늘면
            #   ★ ★ 이미 받은 원문에서 ★ 새 칸이 나온다 (리본카 08-29 에서 배운 것)
            row = conn.execute(
                "SELECT body FROM raw_response WHERE site=? AND endpoint='detail'"
                "   AND source_id=? LIMIT 1", (SITE_CODE, sid)).fetchone()
            html = raw_body(row[0]) if row else None
            if html is None:
                continue
            got["원문에서 다시 넣음"] += 1
        else:
            html = _get(f"{base}/shop/item.php?it_id={sid}", head, timeout)
            if not html:
                # ★ 못 받은 것을 ★ 「없음」으로 저장하지 않는다 (금지 12)
                got["못 받음"] += 1
                time.sleep(interval)
                continue
            save_file(SITE_CODE, "detail", sid,
                          f"{base}/shop/item.php?it_id={sid}", html, at,
                          listing_id=one.get("listing_id"))
            # ★ 통신·sleep 이 트랜잭션 안에 들지 않게 곧바로 커밋한다 (개정 857)
            commit(conn)
            got["받음"] += 1
        one = dict(one)
        deep = parse_detail(html, sid)
        deep["listing_id"] = one.get("listing_id")
        deep["detail_status"] = "ok"
        # ★★ 차종 이름은 ★ **목록**이 준다 (상세에는 없다) — ★ 이어 준다.
        #   ★ 안 이으면 ★ `fill_target_key` 가 ★ 이름이 없어 못 붙인다
        for k in ("site_model_group", "site_model"):
            if one.get(k) and not deep.get(k):
                deep[k] = one[k]
        n_chk, chk = inspect_of(html)
        if n_chk:
            deep["inspection_status"] = "ok"
        fill_target_key(SITE_CODE, deep)
        upsert_core(conn, deep, at)
        commit(conn)
        if sid not in have:
            time.sleep(interval)
    print("★ 상세 — " + " · ".join(f"{k} {v}" for k, v in got.items()))
    raw_link_raws(conn, SITE_CODE)
    n = conn.execute("SELECT COUNT(*) FROM core_listing WHERE site=?",
                     (SITE_CODE,)).fetchone()[0]
    print(f"★ 저장 {len(rows)}건 · 저장된 BMW 매물 {n:,}건")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
