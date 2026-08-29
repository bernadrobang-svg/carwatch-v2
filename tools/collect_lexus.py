# -*- coding: utf-8 -*-
"""렉서스 인증중고 수집 (명령서 1a).

★ 모바일 UA ＋ Referer 가 있어야 준다
★ `search_list.car_list` 가 매물이다 — ★ `total_list_num` 은 믿지 않는다
   ★ 실측 08-24 — car_list 36 · total_list_num 84 (서로 다르다)
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

from store.dictionary import known_model_of        # noqa: E402
from store.raw import link_raws as raw_link_raws  # noqa: E402
from store.raw import commit, open_db              # noqa: E402

SITE_CODE = "lexus_certified"
WON_PER_MANWON = 10_000
# ★ 쪽넘김 상한.  ★ 실측 3쪽이다 — ★ 사이트가 끝을 안 알려도 여기서 멈춘다
MAX_PAGES = 20
SLEEP_SEC = 1.0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _title(v) -> str | None:
    """★ 사이트가 `{"code":…, "title":…}` 로 주는 칸 — ★ 사람 말만 남긴다."""
    if isinstance(v, dict):
        return v.get("title") or v.get("code")
    return v if v else None


def main() -> int:
    args = sys.argv[1:]
    with open(os.path.join(ROOT, "config", "endpoints.json"), encoding="utf-8") as f:
        cfg = json.load(f)[SITE_CODE]
    # ★★★★★ 08-29 (`LEXUS_CERTIFIED_API.md` 1c) — ★ **쪽넘김이 있다**.
    #   ★ 열쇠는 ★ `cur_page` 다 — ★ `page` · `pageNo` 는 ★ **조용히 1쪽을 준다**.
    #   ★ 개정 587 이 그것에 속아 ★ 「전수 36」으로 적었다.
    #   ★ 실측 08-29 — ★ cur_page 1→36 · 2→36 · 3→2 · 4→0 · 전수 74.
    #   ★★ 1쪽만 받고 `sweep_gone` 을 부르면 ★ 2·3쪽 38건이
    #     ★ ★ **안 팔렸는데 gone 이 된다** — ★ 그것이 이 고침의 까닭이다
    base = cfg["base_url"] + cfg["paths"]["list"]
    sep = "&" if "?" in base else "?"
    timeout = float(cfg.get("timeout_sec") or 40)
    cars: list = []
    pages, done = 0, False
    for page in range(1, MAX_PAGES + 1):
        req = urllib.request.Request(f"{base}{sep}cur_page={page}",
                                     headers=cfg.get("headers") or {})
        d = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
        sl = d.get("search_list") or {}
        got = sl.get("car_list") or []
        # ★ 돌려준 `cur_page` 가 ★ 부른 쪽과 다르면 ★ 쪽넘김이 안 먹은 것이다.
        #   ★ 그 응답은 1쪽의 되풀이다 — ★ 넣으면 안 되고 ★ 「끝까지」도 아니다
        if got and str(sl.get("cur_page") or page) != str(page):
            print(f"★ cur_page={page} 인데 응답이 {sl.get('cur_page')} 다 — "
                  "쪽넘김이 안 먹었다.  ★ 끝까지 받은 것으로 치지 않는다")
            break
        pages += 1
        cars.extend(got)
        print(f"  cur_page={page} → {len(got)}건 (누계 {len(cars)})")
        if not got:
            done = True                # ★ 빈 쪽을 봤다 = 끝을 봤다
            break
        total_page = sl.get("total_page")
        if total_page and page >= int(total_page):
            done = True                # ★ 사이트가 말한 마지막 쪽까지 왔다
            break
        time.sleep(SLEEP_SEC)
    print(f"★ car_list 합계 {len(cars)}건 · {pages}쪽 · "
          f"total_list_num {sl.get('total_list_num')} "
          f"· 끝까지 받았나 {'예' if done else '아니오'}")

    rows = []
    # ★★ 원문 항목을 ★ 파싱 결과와 ★ 짝지어 둔다 (명령서 3-2 필수) —
    #   ★ 렉서스는 ★ 상세가 없다.  ★ 목록 항목이 ★ 원문의 전부다
    raw_of: dict = {}
    for one in cars:
        if not one.get("idx"):
            continue
        name = one.get("model_name") or ""
        # ★ 「NX 350h」 → NX · 「RX 450h+」 → RX.  ★ 등록부가 아는 이름만
        known = known_model_of(name.split()[0] if name else None)
        row = {"site": SITE_CODE, "source_id": str(one["idx"]),
               "price_unit": "won", "site_model": name,
               "trim_badge": one.get("class_name"),
               # ★★ `color` · `branch` 는 ★ **dict 로 온다** (실측 08-24) —
               #   ★ 그대로 넣으면 sqlite 가 거부한다.  ★ `title` 이 사람 말이다
               "color_ext_raw": _title(one.get("color")),
               "dealer_shop": _title(one.get("branch")),
               "detail_status": "not_requested"}
        if known:
            row["site_model_group"] = known
        for src, col, mul in (("price", "price_current_won", WON_PER_MANWON),
                              ("release_price", "price_origin_won", WON_PER_MANWON),
                              ("mileage", "mileage_km", 1)):
            try:
                row[col] = int(str(one.get(src)).replace(",", "")) * mul
            except (TypeError, ValueError):
                pass
        try:
            row["form_year"] = int(str(one.get("year"))[:4])
        except (TypeError, ValueError):
            pass
        raw_of[row["source_id"]] = one
        rows.append(row)
    ours = [r for r in rows if r.get("site_model_group")]
    print(f"★ 우리 대상 — {len(ours)}건 / {len(rows)}건 "
          f"({sorted({r['site_model_group'] for r in ours})})")
    if "--dry" in args:
        print("★ --dry 라 저장하지 않았다")
        return 0

    from store.core import resolve_listing_id, upsert_core
    from store.raw import save_site_raw

    conn = open_db(os.path.join(ROOT, "carwatch.db"))
    at = _now()
    # ★★ 3-2 걸러 저장 (마스터 확정 08-25) — ★ 우리 대상만 넣는다.
    #   ★ 렉서스는 ★ 전수 36건이라 ★ 좁힐 길이 없다 — ★ 다 받되 ★ 걸러 넣는다
    #   ★ ★ 원문은 남는다 — ★ 갈래를 넓히면 다시 판다
    keep = ours if "--all" not in args else rows
    print(f"★ 저장할 것 {len(keep)}건 · ★ 안 넣는 것 {len(rows) - len(keep)}건 "
          f"(원문은 남는다)")
    # ★★ 원문은 ★ **다 남긴다** — ★ 안 넣는 것도 남긴다 (「갈래를 넓히면 다시 판다」)
    for r in rows:
        save_site_raw(conn, SITE_CODE, "list", r["source_id"], cfg["base_url"],
                      json.dumps(raw_of.get(r["source_id"]),
                                 ensure_ascii=False), at)
    for r in keep:
        r["listing_id"] = resolve_listing_id(conn, SITE_CODE, r["source_id"], at)
        upsert_core(conn, r, at)
    commit(conn)
    # ★★★★★ 08-29 (개정 838 · 오판 161) — ★ 팔린 차를 거른다 (`S46-117`).
    #   ★ 저장한 **뒤에** 부른다 — ★ 새 매물이 차종을 갖고 있어야 한다.
    #   ★ 「끝까지 받았나」가 거짓이면 ★ 안 매긴다 — 반만 보고 매기면 산 차를 죽인다
    from store.core import sweep_gone_groups

    # ★★ 「끝까지 받았나」는 ★ **마지막 쪽을 봤는가**다 (08-29).
    #   ★ 앞서는 `bool(cars)` 였다 — ★ 1쪽만 받고도 참이었다.
    #   ★ ★ 그래서 ★ 2·3쪽 38건이 ★ 안 팔렸는데 gone 이 됐다
    _done = done and bool(cars)
    # ★ 넣기가 끝났다 — ★ 원문을 매물에 잇는다 (S46-97 · 08-29)
    raw_link_raws(conn, SITE_CODE)
    _got = sweep_gone_groups(conn, SITE_CODE, [(_done, {r["source_id"] for r in rows})], at)
    print(f"★ 목록에 없어 gone 으로 매긴 것 {sum(_got.values())}건 "
          f"({len(_got)}차종) · 끝까지 받았나 {'예' if _done else '아니오'}")
    n = conn.execute("SELECT COUNT(*) FROM core_listing WHERE site=?",
                     (SITE_CODE,)).fetchone()[0]
    print(f"★ 저장 {len(keep)}건 · 저장된 렉서스 매물 {n:,}건")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
