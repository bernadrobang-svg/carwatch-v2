#!/usr/bin/env python3.11
"""차종 대응표 → `dict_enum` (명령서 `ORDER_20260822_r515.md` 2a장 · 개정 540).

    python3.11 tools/sync_target_map.py [--dry]     대응표를 dict_enum 에
    python3.11 tools/sync_target_map.py --reparse   ★ 이미 받은 제목에서 차종을 다시 뽑는다
    python3.11 tools/sync_target_map.py --apply     ★ 이미 받은 매물에 차종을 붙인다

지시서   `docs/TARGET_KEY_MAP.md`
값규칙   ★ 쓰는 자리는 `config/dictionaries/target_map.json` 하나다
        ★ 그것을 `dict_enum(site, axis='target', value, mapped)` 에 넣는다
        ★ 사이트가 실제로 부르는 이름도 ★ 함께 넣는다 —
          ★ mapped 가 빈 것은 ★ 「차종 미정」이다.  ★ 지우지 않는다
금지     ★ facet 을 안 받고 차종 문자열을 지어내는 것 (금지 6)
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from parse.hyundai_cert.mapping import _model_group  # noqa: E402
from parse.target_rules import target_by_rules  # noqa: E402
from store.dictionary import (  # noqa: E402
    collect_group_of, target_key_of, target_map)
from store.raw import open_db  # noqa: E402

AXIS = "target"
DICT_VERSION = "d1"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def observed(conn) -> dict:
    """사이트가 실제로 부르는 차종 이름 · 건수.  ★ DB 가 정본이다."""
    out: dict = {}
    for site, name, n in conn.execute(
        "SELECT site, site_model_group, COUNT(*) FROM core_listing"
        " WHERE site_model_group IS NOT NULL GROUP BY 1, 2"
    ):
        out.setdefault(site, {})[name] = n
    return out


def reparse_model_group(conn) -> int:
    """★ 이미 받은 제목에서 ★ 차종을 다시 뽑는다 (개정 540 · 실측 08-23).

    ★ 왜 — ★ 옛 파서가 ★ 「연식 다음 낱말」을 차종으로 삼았다.
      ★ 「2021 더 뉴 그랜저 (IG) …」 가 ★ 「더」가 되어 ★ 152건이 숨었다.
      ★ `repnCarCd` `IG02` 가 ★ 규격이 「둘 다 받으라」 한 그 세대다 (TARGET_KEY_MAP 4장)
    ★ 다시 받지 않는다 — ★ 제목(`site_model`)이 DB 에 있다.  ★ 그것에서 다시 뽑는다
    """
    rows = conn.execute(
        "SELECT listing_id, site_model, site_model_group FROM core_listing"
        " WHERE site='hyundai_cert' AND site_model IS NOT NULL").fetchall()
    fixed = 0
    for lid, name, was in rows:
        now = _model_group(name)
        if now and now != was:
            conn.execute("UPDATE core_listing SET site_model_group=?"
                         " WHERE listing_id=?", (now, lid))
            fixed += 1
    conn.commit()
    print(f"★ 제목에서 차종을 다시 뽑았다 — {len(rows)}건 중 ★ {fixed}건이 달라졌다")
    return fixed


def main() -> int:
    dry = "--dry" in sys.argv
    conn = open_db(os.path.join(ROOT, "carwatch.db"))
    at = _now()
    if "--reparse" in sys.argv:
        reparse_model_group(conn)
    seen = observed(conn)
    rows, mapped_n = 0, 0
    for site, names in sorted(seen.items()):
        table = target_map(site)
        for name, count in sorted(names.items(), key=lambda kv: -kv[1]):
            spec = table.get(name) or {}
            # ★ 우리 값이 ★ 하나면 그 키 · ★ 갈래가 여럿이면 ★ 차종군을 적는다.
            #   ★ 「그랜저」 하나에 우리 갈래가 여럿 걸리므로 ★ 1:1 이 아니다
            got = spec.get("target_key") or spec.get("collect_group")
            rows += 1
            if got:
                mapped_n += 1
            if dry:
                continue
            # ★ upsert_enum 은 mapped 를 mapped_values.json 에서 찾는다 —
            #   ★ 차종은 target_map.json 이 정본이라 ★ 여기서 직접 넣는다
            conn.execute(
                "INSERT INTO dict_enum(site,axis,value,display,mapped,"
                " count_seen,status,source_endpoint,dict_version,"
                " first_seen,last_seen)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?)"
                " ON CONFLICT(site,axis,value) DO UPDATE SET"
                "  mapped=excluded.mapped, count_seen=excluded.count_seen,"
                "  status=excluded.status, last_seen=excluded.last_seen",
                (site, AXIS, name, name, got, count,
                 "confirmed" if got else "pending",
                 "list", DICT_VERSION, at, at))
    if not dry:
        conn.commit()
    print(f"차종 이름 {rows}종 · ★ 대응표에 있는 것 {mapped_n}종"
          + (" (--dry 라 안 넣었다)" if dry else ""))
    for site, names in sorted(seen.items()):
        table = target_map(site)
        hit = sum(n for k, n in names.items()
                  if (table.get(k) or {}).get("target_key")
                  or (table.get(k) or {}).get("collect_group"))
        print(f"  {site:14} 이름 {len(names):>3}종 · 매물 {sum(names.values()):>6} "
              f"· ★ 이름이 맞는 것 {hit:>5}건")
    print("★ 위는 ★ 이름만 본 수다 — ★ 연료까지 맞아야 붙는다 (--apply 가 낸다)")

    if "--apply" not in sys.argv:
        return 0
    # ★★★★★ 09-04 — ★ `--dry` 는 ★ **아무것도 안 고쳐야 한다.**
    #   ★ 실측 09-04 — ★ `--apply --dry` 로 돌렸는데 ★ 「(--dry 라 안 넣었다)」라 찍고
    #   ★ ★ 그 아래에서 ★ **4,151건에 차종을 붙였다**.  ★ 말과 한 일이 달랐다
    if "--dry" in sys.argv:
        print("★ `--dry` 다 — ★ 차종을 안 붙였다 (`--apply` 만으로 돌려라)")
        return 0
    return apply_targets(conn, at)


def apply_targets(conn, at: str) -> int:
    """★ 이미 받은 매물에 차종을 붙인다 (명령서 2a 검산).

    ★ 차종 이름 ★ 과 ★ 연료 ★ 둘 다 맞아야 붙는다
    ★ 안 맞는 것은 ★ 「차종 미정」 그대로 둔다.  ★ 버리지 않는다
    """
    del at
    sites = [s for s in target_map()]
    put, keep = 0, 0
    for site in sites:
        for lid, name, fuel, model, cc in conn.execute(
            "SELECT listing_id, site_model_group, fuel_raw, site_model,"
            " displacement_cc FROM core_listing WHERE site=?", (site,)
        ):
            # ★ 차종군이 있으면 ★ targets.json 규칙이 갈래를 고른다 (2d).
            #   ★ 없으면 ★ 이름+연료로 거른다 (TARGET_KEY_MAP 6장)
            if collect_group_of(site, name):
                r = target_by_rules(site, name, fuel, model, cc)
                got = r.target_key if r else None
            else:
                got = target_key_of(site, name, f"{fuel or ''} {model or ''}")
            # ★★ `status` 를 함께 정한다 (개정 633 실측) —
            #   ★ `collect/runner.py:568` 이 ★ 엔카에서 쓰는 그 규칙 그대로다:
            #     ★ 차종이 붙으면 `active` · 아니면 `out_of_scope`
            #   ★ 안 정하면 ★ `status='new'` 로 남고 ★ S10 이
            #     `WHERE status='active'` 라 ★ 통째로 건너뛴다 —
            #     ★ 저장은 됐는데 ★ 채점이 안 되는 것이 ★ 그 까닭이다
            #   ★ `out_of_scope` 도 ★ 행은 남는다.  ★ 버리는 것이 아니다
            said = "active" if got else "out_of_scope"
            if got:
                # ★ 차종은 ★ 늘 붙인다 — ★ 팔린 차도 ★ 「무슨 차였나」는 남아야 한다
                conn.execute(
                    "UPDATE core_listing SET target_key=? WHERE listing_id=?",
                    (got, lid))
                # ★★★★★ 09-04 — ★ **`gone` 을 되살리지 않는다.**
                #   ★ 실측 09-04 — ★ 전에는 ★ `status` 를 함께 `active` 로 덮어
                #   ★ ★ 팔려서 내린 ★ **2,036건**이 ★ 도로 살아났다 —
                #   ★ ★ ★ 철학 ②(`S46-267`)가 한 일을 ★ 이 줄이 물렸다.
                #   ★★ 되살리는 자리는 ★ **하나**다 — ★ `collect/sweep.py` 의 「마」
                #     ★ ★ (`mark_relisted` · 상세가 「아직 판다」고 할 때만)
                conn.execute(
                    "UPDATE core_listing SET status=? WHERE listing_id=?"
                    "   AND status <> 'gone'", (said, lid))
                put += 1
            else:
                # ★★★★★ 09-04 — ★ **차종이 이미 붙어 있으면 ★ 안 내린다.**
                #   ★ 실측 09-04 — ★ 이 줄이 ★ `target_key` 가 **있는** 행까지
                #   ★ ★ `out_of_scope` 로 내렸다 — ★ **4,122건**이
                #   ★ ★ ★ 「우리 차종 열쇠가 붙었는데 ★ 남의 차」라는 ★ **모순**이 됐다
                #     ★ ★ ★ ★ (스포티지 682 · GLC 573 · 그랜저 512 · X3 354 · 모델Y 268 …).
                #   ★★ 규칙이 ★ **이번 판에 못 짚었을 뿐**이다 —
                #     ★ ★ 못 짚은 것을 ★ 「남의 차」라고 말하지 않는다 (금지 6)
                conn.execute(
                    "UPDATE core_listing SET status=? WHERE listing_id=?"
                    " AND status='new' AND target_key IS NULL", (said, lid))
                keep += 1
    conn.commit()
    print(f"★ 차종을 붙였다 {put}건 · ★ 「차종 미정」으로 둔 것 {keep}건")
    left = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE target_key IS NULL"
    ).fetchone()[0]
    print(f"★ 전체 차종 미정 — {left:,}건")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
