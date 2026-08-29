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
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from store.dictionary import known_model_of        # noqa: E402
from store.raw import commit, open_db              # noqa: E402

SITE_CODE = "lexus_certified"
WON_PER_MANWON = 10_000


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
    req = urllib.request.Request(cfg["base_url"] + cfg["paths"]["list"],
                                 headers=cfg.get("headers") or {})
    d = json.loads(urllib.request.urlopen(
        req, timeout=float(cfg.get("timeout_sec") or 40)).read())
    sl = d.get("search_list") or {}
    cars = sl.get("car_list") or []
    print(f"★ car_list {len(cars)}건 · total_list_num {sl.get('total_list_num')} "
          f"(★ 서로 다르다 — car_list 가 매물이다)")

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

    # ★ 렉서스는 ★ 한 번에 ★ `car_list` 전부를 준다 — ★ 쪽넘김이 없다.
    #   ★ 그것이 비지 않았으면 ★ 끝까지 받은 것이다
    _done = bool(cars)
    _got = sweep_gone_groups(conn, SITE_CODE, [(_done, {r["source_id"] for r in rows})], at)
    print(f"★ 목록에 없어 gone 으로 매긴 것 {sum(_got.values())}건 "
          f"({len(_got)}차종) · 끝까지 받았나 {'예' if _done else '아니오'}")
    n = conn.execute("SELECT COUNT(*) FROM core_listing WHERE site=?",
                     (SITE_CODE,)).fetchone()[0]
    print(f"★ 저장 {len(keep)}건 · 저장된 렉서스 매물 {n:,}건")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
