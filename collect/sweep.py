# -*- coding: utf-8 -*-
"""철학 ② — ★ **팔린 것은 대조하고 치운다** (마스터 확정 09-03 · `S46-267`).

★★★ 마스터 — 「★ 제발 좀 ★ **이미 팔린 상태**, 즉 ★ 목록에 없는 상품에 대해서
   ★ **상태 체크한 다음에 치우는 걸** 만들어줘.  ★ 특히 **엔카** 쪽
   ★ 목록에 없는데 · 또는 ★ 상태가 판매 중으로 받았는데 **판매 완료가 된 것**은
   ★ ★ **상세로 대조한 다음에 목록에서 삭제**해 줘」

★★★★★ 마스터 확정 09-03 (두 번째) — ★ **세게 내린다.**
  「★ 100개 중 90개를 버려야 하는데 ★ 91개를 버린다고 ★ 살아있는 1개 때문에
   ★ 90개를 안 버리는 ★ **너의 철학을 인정 못해**」
  ★ 곧 ★ **덜 버리는 잘못이 ★ 더 버리는 잘못보다 나쁘다.**
  ★ ★ 마스터는 ★ **팔린 차를 찾지 않으신다** — ★ 팔린 것이 섞이면 화면이 못 쓴다.
  ★ ★ ★ `gone` 은 ★ **지우는 것이 아니다** — ★ 「마」가 ★ `relisted` 로 되살린다

★ 무엇을 근거로 내리나 [실측 09-03 · 그랑 콜레오스 `KOLEOS_HEV`]

| 근거 | 무엇 | 콜레오스 467대 중 |
|---|---|--:|
| **가** | 목록에서 사라졌다 (`sweep_done_ratio` 를 넘게 받았을 때만) | S4 가 매긴다 |
| **나** | ★ `sales_status` 가 ★ 「판매완료·계약중」 | **11** |
| **다** | ★ 상세가 ★ 「없다」고 했다 (`detail_status='not_found'`) | **346** |
| — | 둘 중 하나라도 | ★ **346 (74%)** |

★ 「나」의 말은 ★ 코드에 안 박는다 — ★ `config/scoring.json` 의
  ★ `axis_rules.absolute_fail.sales_status_fail` 이 ★ **정본**이다 (`CONTRACT`·`SOLD`).
★ ★ `RESERVED`(예약중)는 ★ 그 목록에 없다 — ★ 예약은 판매완료가 아니다

★★ 「다」의 잣대에 대해 ★ **여쭐 것이 있다** (회차 9절) —
  ★ 실측 09-03 — ★ `detail_status='not_found'` 9,377건 가운데
  ★ ★ `raw_response` 에 ★ 참 404 봉투가 남은 것은 ★ **401건**뿐이다.
  ★ ★ ★ 엔카 상세는 ★ 서버에 **407** 이 뜨는데(137,573건) ★ 그것이
    ★ ★ ★ ★ `not_found` 로 굳은 자리가 있는지 ★ 못 짚었다.
  ★★ ★ 그래도 ★ **지시에 따라 내린다** — ★ 마스터 확정이 그것이다.
    ★ ★ 되돌릴 문은 ★ 「마」(`relisted`)로 남긴다

금지     ★ 지우는 것 — ★ `gone_at` 과 ★ 「왜 죽였나」를 남긴다 (마스터 확정 08-24)
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ★ 왜 죽였나 — ★ 규격의 가·나·다 그대로 적는다 (`core_listing_change.cause`)
WHY_LIST_GONE = "가-목록에없다"
WHY_SITE_SOLD = "나-사이트가팔렸다함"
WHY_DETAIL_ABSENT = "다-상세가없다함"
WHY_REVIVED = "마-상세가아직판다함"

# ★ 상세가 ★ 「없다」고 한 것.  ★ `error` 는 ★ **안 넣는다** —
#   ★ 그것은 ★ 「못 받았다」이지 ★ 「없다」가 아니다 (엔카 407 이 여기 든다)
DETAIL_ABSENT = ("not_found",)


def sold_words(root: str = ROOT) -> tuple:
    """「팔렸다」로 볼 사이트 말.  ★ 코드에 안 박는다 — ★ config 가 정본이다."""
    try:
        with open(os.path.join(root, "config", "scoring.json"),
                  encoding="utf-8") as f:
            got = (json.load(f).get("axis_rules", {})
                   .get("absolute_fail", {}).get("sales_status_fail"))
    except (OSError, ValueError):
        got = None
    return tuple(got or ("CONTRACT", "SOLD"))


def candidates(conn, *, site: str | None = None,
               target_keys: tuple = ()) -> list:
    """★ 「나」·「다」에 걸린 것.  ★ 돌려줌 `[(listing_id, source_id, 까닭), …]`.

    ★ 「가」는 ★ S4 의 `sweep_gone` 이 매긴다 — ★ 목록을 그 자리에서만 안다
    """
    words = sold_words()
    sql = ["SELECT listing_id, source_id, sales_status, detail_status",
           "  FROM core_listing",
           " WHERE status IN ('active','new')"]
    args: list = []
    if site:
        sql.append("   AND site = ?")
        args.append(site)
    if target_keys:
        marks = ",".join("?" * len(target_keys))
        sql.append(f"   AND target_key IN ({marks})")
        args.extend(target_keys)
    wmarks = ",".join("?" * len(words))
    dmarks = ",".join("?" * len(DETAIL_ABSENT))
    sql.append(f"   AND (sales_status IN ({wmarks})"
               f"        OR detail_status IN ({dmarks}))")
    args.extend(words)
    args.extend(DETAIL_ABSENT)
    out = []
    for lid, sid, sales, detail in conn.execute("\n".join(sql), tuple(args)):
        # ★ 까닭을 ★ 둘 다 적는다 — ★ 「왜 죽였나」가 남아야 되살릴 수 있다
        why = []
        if sales in words:
            why.append(WHY_SITE_SOLD)
        if detail in DETAIL_ABSENT:
            why.append(WHY_DETAIL_ABSENT)
        out.append((lid, sid, "·".join(why)))
    return out


def sweep_sold(conn, at: str, *, site: str | None = None,
               target_keys: tuple = (), run_id: str | None = None,
               limit: int | None = None) -> dict:
    """★ 「나」·「다」에 걸린 것을 ★ `gone` 으로 매긴다.  ★ 돌려줌 까닭별 건수.

    ★ 한 건씩 돈다 — ★ 전건을 RAM 에 올리지 않는다 (`S46-265`)
    """
    from store.core import mark_gone

    got = candidates(conn, site=site, target_keys=target_keys)
    if limit is not None:
        got = got[:limit]
    tally: dict = {}
    for lid, _sid, why in got:
        mark_gone(conn, lid, at, cause=why, run_id=run_id)
        tally[why] = tally.get(why, 0) + 1
    return tally


def revive(conn, at: str, *, site: str | None = None,
           run_id: str | None = None) -> int:
    """★ 「마」 — ★ 상세가 ★ 「아직 판다」면 ★ **되살린다** (`relisted`).

    ★ 잘못 죽이지 않는다 — ★ 세게 내리는 대신 ★ 이 문을 둔다.
      ★ 잣대 — ★ `gone` 인데 ★ `detail_status='ok'` 이고
      ★ ★ `sales_status` 가 ★ 「팔렸다」 말이 **아닌** 것
    """
    from store.core import mark_relisted

    words = sold_words()
    wmarks = ",".join("?" * len(words))
    sql = ["SELECT listing_id FROM core_listing",
           " WHERE status = 'gone' AND detail_status = 'ok'",
           f"   AND (sales_status IS NULL OR sales_status NOT IN ({wmarks}))"]
    args: list = list(words)
    if site:
        sql.append("   AND site = ?")
        args.append(site)
    n = 0
    for (lid,) in conn.execute("\n".join(sql), tuple(args)).fetchall():
        mark_relisted(conn, lid, at, cause=WHY_REVIVED, run_id=run_id)
        n += 1
    return n
