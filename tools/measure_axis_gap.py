"""★ 3 — ★ 짝이 245 인데 ★ 아홉 사이트 A 가 0 인 까닭을 ★ **잰다**.

★ 고치지 않는다.  ★ 「어느 축이 비는가」를 ★ 수로 낸다 (명령서 r956 · 3).
"""
from __future__ import annotations

import sqlite3
import sys
from collections import Counter, defaultdict

DB = sys.argv[1] if len(sys.argv) > 1 else "carwatch.db"


def main() -> int:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cv = conn.execute("SELECT MAX(calc_version) FROM result_axis").fetchone()[0]
    print(f"★ calc_version = {cv}\n")

    # ── ① 짝 — plate_hash 가 같고 ★ 엔카와 아홉 사이트가 ★ 함께 있는 것
    rows = list(conn.execute(
        "SELECT l.plate_hash, l.listing_id, l.site, l.price_current_won,"
        "       s.grade, s.earned, s.not_rated_reason, l.target_key"
        " FROM core_listing l"
        " LEFT JOIN result_score s"
        "   ON s.listing_id = l.listing_id AND s.calc_version = ?"
        " WHERE l.plate_hash IS NOT NULL AND l.status IN ('active','new')", (cv,)))
    by_plate = defaultdict(list)
    for r in rows:
        by_plate[r["plate_hash"]].append(r)
    pairs = {p: g for p, g in by_plate.items() if len({x["site"] for x in g}) > 1}
    cross = {p: g for p, g in pairs.items()
             if any(x["site"] == "encar" for x in g)
             and any(x["site"] != "encar" for x in g)}
    print(f"① 짝 {len(pairs):,}쌍 · 그중 ★ 엔카 ↔ 아홉 사이트 {len(cross):,}쌍\n")

    # ── ② 아홉 사이트 쪽 ★ 등급 갈래
    nine = [x for g in pairs.values() for x in g if x["site"] != "encar"]
    print("② 짝에 든 아홉 사이트 매물의 등급 —")
    for k, v in sorted(Counter(x["grade"] for x in nine).items(),
                       key=lambda t: -t[1]):
        print(f"     {str(k):<12} {v:>5,}")

    # ── ③ ★ 축마다 ★ 몇 건이 비는가 (아홉 사이트 · 짝에 든 것)
    ids = [x["listing_id"] for x in nine]
    if not ids:
        print("\n③ 짝에 아홉 사이트가 없다")
        return 0
    q = ",".join("?" * len(ids))
    axes = list(conn.execute(
        f"SELECT axis, excluded, value, max_points, source, listing_id"
        f" FROM result_axis WHERE calc_version=? AND listing_id IN ({q})",
        [cv, *ids]))
    tot = defaultdict(int)
    empty = defaultdict(int)
    zero = defaultdict(int)
    pts = defaultdict(float)
    mx = defaultdict(float)
    for a in axes:
        k = a["axis"]
        tot[k] += 1
        mx[k] += float(a["max_points"] or 0)
        if a["excluded"] or a["value"] is None:
            empty[k] += 1
        else:
            pts[k] += float(a["value"])
            if not float(a["value"]):
                zero[k] += 1
    print(f"\n③ 축마다 — 아홉 사이트 {len(set(ids)):,}건 (짝에 든 것)")
    print(f"   {'축':<22}{'행':>6}{'★ 비었다':>10}{'0점':>7}"
          f"{'받은 점':>10}{'만점':>10}{'비율':>8}")
    for k in sorted(tot, key=lambda k: -(mx[k] - pts[k])):
        r = pts[k] / mx[k] * 100 if mx[k] else 0.0
        print(f"   {k:<22}{tot[k]:>6,}{empty[k]:>10,}{zero[k]:>7,}"
              f"{pts[k]:>10,.0f}{mx[k]:>10,.0f}{r:>7.1f}%")

    # ── ④ ★ 한 짝을 열어 ★ 나란히 본다
    pick = None
    for p, g in cross.items():
        e = [x for x in g if x["site"] == "encar"]
        n = [x for x in g if x["site"] != "encar"]
        if e and n and e[0]["grade"] and e[0]["grade"] <= "B":
            pick = (e[0], n[0])
            break
    if pick is None and cross:
        g = next(iter(cross.values()))
        pick = ([x for x in g if x["site"] == "encar"][0],
                [x for x in g if x["site"] != "encar"][0])
    if pick is None:
        print("\n④ 엔카 ↔ 아홉 사이트 짝이 없다 — 열 것이 없다")
        return 0
    a, b = pick
    print(f"\n④ ★ 한 짝을 연다 — {a['target_key']}")
    for x in (a, b):
        print(f"     {x['site']:<16} {x['listing_id']:<28}"
              f" {(x['price_current_won'] or 0)//10000:>6,}만"
              f" · 등급 {x['grade']} · {x['earned']} · {x['not_rated_reason'] or ''}")
    left = {r["axis"]: r for r in conn.execute(
        "SELECT * FROM result_axis WHERE calc_version=? AND listing_id=?",
        (cv, a["listing_id"]))}
    right = {r["axis"]: r for r in conn.execute(
        "SELECT * FROM result_axis WHERE calc_version=? AND listing_id=?",
        (cv, b["listing_id"]))}
    print(f"\n   {'축':<22}{a['site']:>22}{b['site']:>22}   ★")
    for k in sorted(set(left) | set(right)):
        def cell(d):
            r = d.get(k)
            if r is None:
                return "행이 없다"
            if r["excluded"] or r["value"] is None:
                return f"★ 비었다 ({r['source']})"
            return f"{float(r['value']):.0f}/{float(r['max_points'] or 0):.0f} ({r['source']})"
        lc, rc = cell(left), cell(right)
        mark = "  ←★" if ("비었다" in rc or "행이 없다" in rc) and "비었다" not in lc else ""
        print(f"   {k:<22}{lc:>22}{rc:>22}{mark}")
    return 0




def ceiling(db: str = DB) -> int:
    """⑤ ★ 아홉 사이트가 ★ **닿을 수 있는 천장**을 잰다.

    ★ 「축이 비면 0점이고 ★ 분모는 만점 그대로」이므로 (개정 289)
      ★ 못 채우는 축의 배점 합이 ★ 그대로 천장을 깎는다.
    """
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    cv = conn.execute("SELECT MAX(calc_version) FROM result_axis").fetchone()[0]
    cut = float(__import__("json").loads(
        open("config/scoring.json", encoding="utf-8").read())["grade_cuts"]["A"])
    print(f"\n\n⑤ ★ 천장 — A 는 {cut:.0%} 다")
    rows = list(conn.execute(
        "SELECT l.site, a.axis, a.max_points, a.value, a.source, a.excluded,"
        "       a.listing_id"
        " FROM result_axis a JOIN core_listing l USING(listing_id)"
        " WHERE a.calc_version=? AND l.status IN ('active','new')", (cv,)))
    per = defaultdict(lambda: defaultdict(lambda: [0, 0.0, 0.0]))
    ids = defaultdict(set)
    for r in rows:
        ids[r["site"]].add(r["listing_id"])
        c = per[r["site"]][r["axis"]]
        c[0] += 1
        c[1] += float(r["max_points"] or 0)
        if not (r["excluded"] or r["value"] is None):
            c[2] += float(r["value"])
    print(f"   {'사이트':<17}{'매물':>7}{'★ 늘 0인 축':>13}"
          f"{'그 배점':>10}{'천장':>9}{'A 가능':>8}")
    for site in sorted(per, key=lambda s: -len(ids[s])):
        dead = [a for a, c in per[site].items() if c[2] == 0.0]
        deadpts = sum(per[site][a][1] for a in dead) / max(len(ids[site]), 1)
        base = sum(c[1] for c in per[site].values()) / max(len(ids[site]), 1)
        top = (base - deadpts) / base if base else 0.0
        print(f"   {site:<17}{len(ids[site]):>7,}{len(dead):>13}"
              f"{deadpts:>10,.0f}{top:>8.1%}{('예' if top >= cut else '★ 못 한다'):>8}")
    return 0


if __name__ == "__main__":
    main()
    raise SystemExit(ceiling())
