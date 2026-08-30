# -*- coding: utf-8 -*-
"""★ 0k (명령서 r974 뒤) — ★ **잰다.  안 고친다.**

  ① ★ −67 감점이 ★ 몇 매물에 · 무슨 값으로 붙나
  ② ★ 「근거 글은 있는데 0점」인 축이 ★ 어느 값에서 막히나
  ③ ★ Ⓐ(파서가 읽기만 하면 되는 것) 가 ★ 사이트마다 몇 축 남았나
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB = os.path.join(ROOT, "carwatch.db")

# ★ 「우리가 못 받았다」를 뜻하는 근거 글.  ★ 「그 차에 없다」와 가른다 (개정 323)
NOT_RECEIVED = frozenset({
    "missing", "rule_or_source_missing", "origin_price_missing",
    "ladder_missing", "option_base_short", "market_sample_short",
    "option_price_unknown", "site_unavailable",
})
NINE_ONLY = "l.site <> 'encar' AND l.status IN ('active','new')"


def main() -> int:
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 60000")
    cv = conn.execute("SELECT MAX(calc_version) FROM result_score").fetchone()[0]

    # ── ① 감점
    print("★ ① 감점 — 몇 매물에 · 무슨 값으로")
    pen = defaultdict(Counter)
    for r in conn.execute(
        "SELECT l.site, s.penalties_json FROM result_score s"
        " JOIN core_listing l USING(listing_id)"
        " WHERE s.calc_version=? AND l.status IN ('active','new')", (cv,)
    ):
        try:
            got = json.loads(r["penalties_json"] or "[]")
        except ValueError:
            continue
        for one in got:
            key = one[0] if isinstance(one, list) else one.get("key")
            if not str(key).startswith("cap:"):
                pen[key][r["site"]] += 1
    # ★★ 「못 받아서 벌을 받는가」는 ★ 감점마다 ★ **조건이 다르다** —
    #   ★ 값이 0 이라서 붙는 것 둘만 ★ 「못 받았다」와 섞일 수 있다.
    #   ★ 골격·자차·압류는 ★ **근거 글이 있을 때만** 붙는다 (`score/penalty.py`) —
    #     ★ ★ 그러므로 ★ 「못 받아서」가 ★ 구조적으로 0 이다.  ★ 0 이라고 적는다
    table = json.load(open(os.path.join(ROOT, "config", "scoring.json"),
                          encoding="utf-8"))["penalties"]
    VALUE_ZERO = {"rental_history": "history.use",
                  "no_site_grade": "warranty.site"}
    marks = ",".join("?" * len(NOT_RECEIVED))
    print(f"   {'감점':<18}{'점':>6}{'붙은 매물':>10}"
          f"{'★ 못 받아 안 붙인 것':>20}   ★ 붙는 조건")
    for key, sites in sorted(pen.items(), key=lambda t: -sum(t[1].values())):
        n = sum(sites.values())
        ax = VALUE_ZERO.get(key)
        if ax:
            miss = conn.execute(
                "SELECT COUNT(*) FROM result_axis a JOIN core_listing l"
                " USING(listing_id) WHERE a.calc_version=? AND a.axis=?"
                "   AND l.status IN ('active','new')"
                "   AND a.excluded=0 AND a.value=0"
                f"   AND a.source IN ({marks})",
                (cv, ax, *sorted(NOT_RECEIVED))).fetchone()[0]
            why = f"{ax} 가 0 점 (근거 글을 안 본다)"
        else:
            miss = 0
            why = "근거 글이 있을 때만 붙는다"
        # ★★ 08-30 (r990 1-1 뒤) — ★ `miss` 는 ★ **안 붙인 것**이다.
        #   ★ 고치기 전에는 ★ 이것들이 ★ 다 붙어 있었다
        print(f"   {str(key):<18}{table.get(key, 0):>6}{n:>10,}{miss:>20,}"
              f"   {why}")

    # ── ② 근거는 있는데 점수가 안 나오는 축
    print("\n★ ② 근거 글은 있는데 점수가 거의 안 나오는 축 (아홉 사이트)")
    agg = defaultdict(lambda: [0, 0.0, 0.0, Counter()])
    for r in conn.execute(
        "SELECT a.axis, a.source, a.value, a.max_points FROM result_axis a"
        f" JOIN core_listing l USING(listing_id) WHERE a.calc_version=? AND {NINE_ONLY}"
        "   AND a.excluded=0 AND a.value IS NOT NULL", (cv,)
    ):
        if r["source"] in NOT_RECEIVED:
            continue
        k = agg[r["axis"]]
        k[0] += 1
        k[1] += float(r["value"])
        k[2] += float(r["max_points"] or 0)
        k[3][r["source"]] += 1
    print(f"   {'축':<20}{'행':>6}{'받은':>9}{'만점':>9}{'비율':>7}   근거 글")
    for ax, (n, got, mx, src) in sorted(
            agg.items(), key=lambda t: t[1][1] / (t[1][2] or 1)):
        ratio = got / mx * 100 if mx else 0.0
        if ratio > 40:
            continue
        print(f"   {ax:<20}{n:>6,}{got:>9,.0f}{mx:>9,.0f}{ratio:>6.1f}%   "
              + " · ".join(f"{k}×{v}" for k, v in src.most_common(2)))

    # ── ③ Ⓐ — 사이트마다 몇 축이 「못 받았다」로 남았나
    print("\n★ ③ Ⓐ — 사이트마다 ★ 「우리가 못 받아서」 비어 있는 축")
    per = defaultdict(lambda: [Counter(), 0.0, set()])
    for r in conn.execute(
        "SELECT l.site, a.axis, a.source, a.value, a.max_points, a.listing_id"
        f" FROM result_axis a JOIN core_listing l USING(listing_id)"
        f" WHERE a.calc_version=? AND {NINE_ONLY}", (cv,)
    ):
        cell = per[r["site"]]
        cell[2].add(r["listing_id"])
        if r["excluded"] if "excluded" in r.keys() else False:
            pass
        if r["source"] in NOT_RECEIVED or r["value"] is None:
            cell[0][r["axis"]] += 1
            cell[1] += float(r["max_points"] or 0)
    print(f"   {'사이트':<17}{'매물':>6}{'★ 못 받은 축':>13}{'한 대당 점':>11}   큰 것부터")
    for site, (axes, pts, ids) in sorted(per.items(), key=lambda t: -t[1][1]):
        n = max(len(ids), 1)
        big = sorted(axes, key=lambda a: -axes[a])[:4]
        print(f"   {site:<17}{len(ids):>6,}{len(axes):>13}{pts / n:>11,.0f}   "
              + " · ".join(big))
    per_site(conn, cv)
    return 0


def per_site(conn, cv) -> None:
    """★★ 08-30 (r990 「회차마다 낼 것」) — ★ 사이트마다 한 표로.

        「원문 못 받음 N점 · 근거 있는데 0점 M점 · 감점 K점」
    """
    import json as _j
    from collections import defaultdict as _dd

    got = _dd(lambda: {"ids": set(), "miss": 0.0, "zero": 0.0, "pen": 0.0})
    for r in conn.execute(
        "SELECT l.site, a.axis, a.source, a.value, a.max_points, a.excluded,"
        "       a.listing_id FROM result_axis a JOIN core_listing l"
        " USING(listing_id) WHERE a.calc_version=?"
        "   AND l.status IN ('active','new')", (cv,)
    ):
        cell = got[r["site"]]
        cell["ids"].add(r["listing_id"])
        mx = float(r["max_points"] or 0)
        if r["excluded"] or r["value"] is None or r["source"] in NOT_RECEIVED:
            cell["miss"] += mx
        elif not float(r["value"]):
            cell["zero"] += mx
    for r in conn.execute(
        "SELECT l.site, s.penalties_json FROM result_score s"
        " JOIN core_listing l USING(listing_id)"
        " WHERE s.calc_version=? AND l.status IN ('active','new')", (cv,)
    ):
        try:
            pen = _j.loads(r["penalties_json"] or "[]")
        except ValueError:
            continue
        got[r["site"]]["pen"] += sum(
            float(one[1] if isinstance(one, list) else one.get("points", 0))
            for one in pen)
    print("\n★ 사이트마다 — 한 대당 점 (음수가 감점이다)")
    print(f"   {'사이트':<17}{'매물':>6}{'원문 못 받음':>12}"
          f"{'근거 있는데 0':>13}{'감점':>9}")
    for site in sorted(got, key=lambda s: -len(got[s]["ids"])):
        c = got[site]
        n = max(len(c["ids"]), 1)
        print(f"   {site:<17}{len(c['ids']):>6,}{c['miss'] / n:>12,.0f}"
              f"{c['zero'] / n:>13,.0f}{c['pen'] / n:>9,.0f}")


if __name__ == "__main__":
    raise SystemExit(main())
