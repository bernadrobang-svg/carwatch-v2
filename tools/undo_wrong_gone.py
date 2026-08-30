#!/usr/bin/env python3.11
"""★★★★★ 잘못 매긴 `gone` 을 되돌린다 (마스터 0a·0c · 08-30).

★★★ 마스터 — 「★ 같은 함정이 아홉 곳이다.  ★ 살아 있는 것이 하나라도 나오면
  ★ 그 사이트 sweep 을 끄고 ★ **되돌려라**.  ★ 원문이 남아 있으니 되돌릴 수 있다」

★★ 실측 08-30 — ★ 08-29 에 매긴 gone 을 ★ 표본으로 눌러 봤다 —
   K카 19건 중 12 · 현대인증 10/10 · KB 9/9 · 헤이딜러 8/10 ·
   리본카 3/10 · 보배 2/10 이 ★ **살아 있었다**.  ★ 볼보 0/8 · 렉서스는 상세가 없다.

★★ 되돌리는 잣대 — ★ **짐작으로 안 되돌린다.  ★ 눌러서 살아 있는 것만** 되돌린다.
   ★ 「살아 있음」은 ★ **그 사이트 파서가 값을 뽑는가**로 가른다 —
     ★ 낱말은 사이트마다 달라 ★ 낱말로 가르면 틀린다 (보배는 「판매완료」가 딜러 실적이다).
★ 못 받은 것은 ★ **안 건드린다** — ★ 모르는 것을 고치지 않는다.
★ 자취(`core_listing_change`)에 ★ `relisted` 로 남긴다 — ★ 조용히 고치지 않는다

사용   python3.11 tools/undo_wrong_gone.py [사이트…]           재기만 한다
      python3.11 tools/undo_wrong_gone.py [사이트…] --write   되돌린다
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from store.core import record_change  # noqa: E402
from store.raw import commit, connect_db  # noqa: E402

CFG = json.load(open(os.path.join(ROOT, "config", "endpoints.json"), encoding="utf-8"))
# ★ 이 날 매긴 것만 본다 — ★ 그 회차가 결함이었다.  ★ 앞의 것은 안 건드린다
DAY = "2026-08-29"
SLEEP_SEC = 0.6


def _now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def _get(url, head, timeout=35):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=head or {}),
                                   timeout=timeout)
        return r.getcode(), r.read()
    except urllib.error.HTTPError as e:
        # ★★ 08-30 — ★ 몸통을 **읽는다.**  ★ 앞서는 버려서 ★ 헤이딜러의
        #   ★ 403 「판매중인 차량이 아닙니다」를 ★ 「못 받음」으로 셌다
        try:
            return e.code, e.read()
        except OSError:
            return e.code, b""
    except Exception:                                          # noqa: BLE001
        return None, b""


def probe(site, sid):
    """★ 살아 있나.  True/False/None(못 받음)."""
    sc = CFG.get(site) or {}
    paths = sc.get("paths") or {}
    if site == "kcar":
        # ★ K카는 ★ 상세가 `data.rvo.carCd` 를 주면 살아 있다 (규격 3-3 ① · 실측 08-30).
        #   ★ 없는 매물도 ★ 200 을 준다 (3,256B) — ★ 크기가 아니라 ★ 이 칸으로 가른다
        from adapters.kcar import KcarAdapter, load_config

        r = KcarAdapter(load_config(ROOT)).detail_urls(sid)[0]
        code, b = _get(r.url, r.headers)
        if not b:
            return None
        try:
            return bool(((json.loads(b).get("data") or {}).get("rvo") or {}).get("carCd"))
        except ValueError:
            return None
    if site == "bobaedream":
        from parse.bobaedream.mapping import parse_detail
        code, b = _get(sc["base_url"] + paths["detail"].format(source_id=sid), sc.get("headers"))
        if not b: return None
        d = parse_detail(b.decode("utf-8", "replace"), site, sid)
        return bool(d and d.get("price_current_won"))
    if site == "reborncar":
        from parse.reborncar.mapping import parse_detail
        code, b = _get(sc["base_url"] + paths["detail"].format(source_id=sid), sc.get("headers"))
        if not b: return None
        d = parse_detail(b.decode("utf-8", "replace"), site, sid)
        return bool(d and d.get("price_current_won"))
    if site == "hyundai_cert":
        from parse.hyundai_cert.mapping import parse_detail_all
        base, p = sc["base_url"], paths.get("detail")
        code, b = _get(base + p.format(goods_no=sid) if "{goods_no}" in p
                       else base + p.format(source_id=sid), sc.get("headers"))
        if not b: return None
        return parse_detail_all(b.decode("utf-8", "replace"), site, sid) is not None
    if site == "kbchachacha":
        from parse.kbchachacha.mapping import parse_detail
        code, b = _get(sc["base_url"] + paths["detail"].format(source_id=sid), sc.get("headers"))
        if not b: return None
        d = parse_detail(b.decode("utf-8", "replace"), site, sid)
        return bool(d and d.get("price_current_won"))
    if site == "heydealer":
        from adapters.heydealer import HeydealerAdapter
        a = HeydealerAdapter(sc); a.token()
        r = a.detail_urls(sid)[0]
        code, b = _get(r.url, r.headers)
        if code == 200 and b:
            try:
                return bool(json.loads(b).get("hash_id"))
            except ValueError:
                return None
        # ★★★★ 08-30 (마스터 지시 3) — ★ 토큰이 만료된 것이 **아니었다.**
        #   ★ 토큰을 새로 받고 다시 눌러도 ★ **403** 이 오고, ★ 그 몸통에
        #   ★ ★ 「**판매중인 차량이 아닙니다**」가 들어 있다 (실측 08-30 · 4건 전부 · 120B).
        #   ★ 곧 ★ 403 은 ★ 「못 받음」이 아니라 ★ **사이트가 「없다」고 답한 것**이다.
        #   ★ 낱말을 그 자리에서 본다 — ★ 코드만으로 안 정한다
        if code == 403 and b and "판매중인 차량이 아닙" in b.decode("utf-8", "replace"):
            return False
        return False if code in (404, 410) else None
    if site == "volvo_selekt":
        from parse.volvo_selekt.mapping import parse_detail
        c = sqlite3.connect("file:carwatch.db?mode=ro", uri=True)
        row = c.execute("select site_model from core_listing where site=? and source_id=?",
                        (site, sid)).fetchone()
        slug = row[0] if row else None
        if not slug: return None
        code, b = _get(f"{sc['base_url']}/kr/vehicles/volvo/{slug}/{sid}", sc.get("headers"))
        if not b: return None
        d = parse_detail(b.decode("utf-8", "replace"), site, sid)
        return bool(d and d.get("price_current_won"))
    if site == "lexus_certified":
        # ★★★★★ 08-30 — ★ **상세가 있다.  ★ 마스터께서 찾아 주셨다** (지시 1).
        #   ★ 규격 1c 「목록이 매물의 전부다」는 ★ **물린다** (마스터 지시).
        #   ★★ `GET /api/json/getData_car_detail.json.php?idx={idx}`
        #     ★ 살아 있다 → `car_detail` 이 있다 (실측 6394 · 12,772B)
        #     ★ 없다     → `car_detail` 이 없다 (실측 6385·6386 · 117B)
        #   ★★★ **200 으로 가르지 않는다** — ★ 없는 것도 200 을 준다 (마스터 지시)
        code, b = _get(f"{sc['base_url']}/api/json/getData_car_detail.json.php?idx={sid}",
                       sc.get("headers"))
        if not b:
            return None
        try:
            return bool((json.loads(b) or {}).get("car_detail"))
        except ValueError:
            return None
    return None




def main() -> int:
    write = "--write" in sys.argv
    want = [a for a in sys.argv[1:] if not a.startswith("-")]
    conn = connect_db(os.path.join(ROOT, "carwatch.db"))
    sites = want or [r[0] for r in conn.execute(
        "SELECT DISTINCT site FROM core_listing"
        " WHERE substr(gone_at, 1, 10) = ? ORDER BY 1", (DAY,))]
    at = _now()
    total = {"살아있다": 0, "정말 없다": 0, "못 받음": 0}
    for site in sites:
        rows = conn.execute(
            "SELECT listing_id, source_id FROM core_listing"
            " WHERE site = ? AND substr(gone_at, 1, 10) = ?", (site, DAY)).fetchall()
        if not rows:
            continue
        got = {"살아있다": 0, "정말 없다": 0, "못 받음": 0}
        for lid, sid in rows:
            ok = probe(site, sid)
            if ok is None:
                got["못 받음"] += 1
            elif ok:
                got["살아있다"] += 1
                if write:
                    conn.execute(
                        "UPDATE core_listing SET status='active', gone_at=NULL,"
                        " last_price_won=NULL WHERE listing_id=?", (lid,))
                    # ★ `change_kind` 는 정해진 값만 받는다 (DDL CHECK) —
                    #   ★ 죽었다가 되살아난 것이 ★ `relisted` 다
                    record_change(conn, lid, "status", "gone", "active", at,
                                  "relisted")
                    commit(conn)
            else:
                got["정말 없다"] += 1
            time.sleep(SLEEP_SEC)
        for k in total:
            total[k] += got[k]
        mark = "  ★ 되살렸다" if (write and got["살아있다"]) else ""
        print(f"  {site:16s} {len(rows):3d}건 — "
              + " · ".join(f"{k} {v}" for k, v in got.items()) + mark)
    print("★ 합계 — " + " · ".join(f"{k} {v}" for k, v in total.items()))
    print("★ 되돌렸다" if write else "★ --write 를 줘야 되돌린다 (지금은 재기만 했다)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
