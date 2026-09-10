# -*- coding: utf-8 -*-
"""★ 이번 주 과제 — ★ **계약한 차를 이기는 GV70 만** 낸다 (기한 09-11).

★★★ 마스터가 ★ 270오1279 (엔카 42598705 · 차값 3,490만) 을 계약하셨다.
  ★ 7일 안에 ★ **그 값을 이기는 차**를 찾는 것이 이번 주 과제다.
★ 정본은 ★ `docs/WEEK_TASK.md` (마스터가 쓰신 것) — ★ 잣대는 `config/week_task.json`.
★★ 차값으로 견준다 — ★ 부대비용은 ★ **어디서 사도 같다** (지시 3장).
  ★ 주행 4.5만km 를 넘는 차만 ★ 소모품(타이어·브레이크)을 더한다.
★★★ **이기지 못하면 올리지 않는다** — ★ 마스터 시간을 쓰는 일이다 (지시 P-5).

돌리는 법
    python3.11 tools/week_task.py                 ★ 낸다
    python3.11 tools/week_task.py --all           ★ 떨어진 것도 까닭과 함께 낸다
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

BOOK = os.path.join(ROOT, "config", "week_task.json")
UNKNOWN = "미조회"


def book(path: str = BOOK) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _won(n) -> str:
    if n is None:
        return UNKNOWN
    return f"{round(n / 10000):,}만"


def rows(conn: sqlite3.Connection, cfg: dict) -> list:
    """조건에 드는 매물.  ★ 리스·렌트는 뺀다 — ★ 내 차가 되지 않는다."""
    from report.screens.build import _lease_kinds

    ads, sells = _lease_kinds(ROOT)
    m, m2 = ",".join("?" * len(ads)), ",".join("?" * len(sells))
    c = cfg["조건"]
    got = conn.execute(
        "SELECT l.site, l.source_id, l.price_current_won, l.year_month,"
        "       l.mileage_km, l.color_ext_raw, l.site_inspection,"
        "       l.trim_grade_name, l.accident_swap_cnt, l.accident_weld_cnt,"
        "       l.accident_frame_cnt, l.accident_parts_json,"
        "       l.price_origin_total_won, l.options_choice_json,"
        "       l.options_standard_json, l.options_name_json,"
        "       l.undercarriage_json, l.dealer_region, l.paired_source_id,"
        "       r.accident_my_cost, r.accident_other_cost, r.accident_total_cnt,"
        "       s.grade, s.score_total"
        "  FROM core_listing l"
        "  LEFT JOIN core_record  r ON r.listing_id = l.listing_id"
        "  LEFT JOIN result_score s ON s.listing_id = l.listing_id"
        " WHERE l.target_key = 'GV70_25T'"
        "   AND l.status IN ('active','new','relisted')"
        "   AND l.price_current_won IS NOT NULL"
        "   AND l.price_current_won <= ?"
        "   AND l.year_month >= ? AND l.mileage_km <= ?"
        f"   AND COALESCE(l.advertisement_type,'') NOT IN ({m})"
        f"   AND COALESCE(l.sell_type,'') NOT IN ({m2})"
        " ORDER BY l.price_current_won",
        [c["차값_최대_원"], c["연식_이후"], c["주행_최대km"], *ads, *sells]
    ).fetchall()
    return got


def _has_hud(*jsons) -> bool | None:
    """HUD 가 있나.  ★ 옵션을 하나도 모르면 ★ None(미조회)."""
    seen = False
    for one in jsons:
        if not one:
            continue
        seen = True
        said = str(one)
        if "HUD" in said or "헤드업" in said or "1046" in said:
            return True
    return False if seen else None


def wear_won(km, cfg: dict) -> int:
    """소모품 — ★ 4.5만km 를 넘는 차만 더한다 (지시 3장)."""
    w = cfg["소모품"]
    if km is None or km <= w["넘는km"]:
        return 0
    return int(w["타이어_원"][0] + w["브레이크_원"][0])


def judge(one, cfg: dict) -> tuple:
    """(이기는 칸, 떨어진 까닭들).  ★ 못 본 것은 ★ 「미조회」로 남긴다."""
    base = cfg["기준차"]
    c = cfg["조건"]
    (site, sid, won, ym, km, color, dx, trim, swap, weld, frame, parts,
     origin, opt_c, opt_s, opt_n, under, region, paired,
     my_cost, ot_cost, acc_cnt, grade, score) = one

    why = []
    if str(sid) in cfg["이미_거른_것"]:
        return None, ["이미 걸렀다 (WEEK_TASK 4·5장)"]
    if str(paired or "") in cfg["이미_거른_것"]:
        return None, ["이미 걸렀다 (같은 차)"]
    if won > base["차값_원"] + 0 and won > cfg["이기는_칸"][2]["차값_최대_원"]:
        return None, [f"차값 {_won(won)} — 3,900만 초과"]
    # ★ 색 — ★ 빨간색·자주색은 제외 (마스터 확정)
    said = str(color or "")
    if any(x in said for x in c["색_제외"]):
        why.append(f"색 {said}")
    # ★ 골격 — ★ 상했으면 탈락.  ★ 미조회는 ★ 탈락이 아니다 (못 찾았다 ≠ 없다)
    if frame is not None and frame > 0:
        why.append(f"골격 {frame}곳")
    # ★ 하체 낱말 (P-4) — ★ 나오면 탈락
    if under:
        try:
            got = json.loads(under)
        except (ValueError, TypeError):
            got = []
        if got:
            why.append("하체 " + "·".join(str(x) for x in got))
    if why:
        return None, why

    hud = _has_hud(opt_c, opt_s, opt_n)
    clean = (acc_cnt == 0) or (my_cost == 0 and ot_cost == 0)
    band = None
    for one_band in cfg["이기는_칸"]:
        key = one_band["칸"]
        if key == "A" and won <= one_band["차값_최대_원"] \
                and km is not None and km <= one_band["주행_최대km"]:
            band = key
            break
        if key == "B" and won <= one_band["차값_최대_원"] \
                and ((km is not None and km <= one_band["주행_최대km"]) or clean):
            band = key
            break
        if key == "C" and won <= one_band["차값_최대_원"] \
                and str(ym or "") >= one_band["등록_이후"] \
                and "흰색" in str(color or "") and hud and dx and clean:
            band = key
            break
    if band is None:
        why.append("이기는 칸에 못 든다")
    return band, why


def report(db: str = "carwatch.db") -> dict:
    cfg = book()
    conn = sqlite3.connect(os.path.join(ROOT, db))
    got = rows(conn, cfg)
    win, lost = [], []
    for one in got:
        band, why = judge(one, cfg)
        # ★★★★★ 09-10 — ★ `(band and win or lost)` 로 썼다가 ★ **첫 승자를 잃었다.**
        #   ★ `win` 이 ★ 빈 목록이면 ★ 거짓이라 ★ `and` 가 그것을 내놓고
        #     ★ ★ `or` 가 ★ `lost` 로 넘긴다.  ★ 실측 — 3,230만 · 36,859km 짜리가
        #       ★ ★ ★ 「이기는 차 0대」 속에 묻혀 있었다.  ★ 짧게 쓰려다 값을 잃었다
        if band:
            win.append((band, why, one))
        else:
            lost.append((band, why, one))
    conn.close()
    return {"cfg": cfg, "win": win, "lost": lost, "seen": len(got)}


def _url(site, sid, paired) -> str:
    if site == "encar":
        return f"https://fem.encar.com/cars/detail/{sid}"
    if site == "kbchachacha":
        return f"https://www.kbchachacha.com/public/car/detail.kbc?carSeq={sid}"
    if site == "kcar":
        return f"https://www.kcar.com/bc/detail/carInfoDtl?i_sCarCd={sid}"
    return str(paired or sid)


def main() -> int:
    out = report()
    cfg, base = out["cfg"], out["cfg"]["기준차"]
    print(f"★ 조건에 든 매물 {out['seen']:,}대 · "
          f"이기는 것 {len(out['win'])}대\n")
    print(f"기준 — {base['번호']} 차값 {_won(base['차값_원'])} · "
          f"{base['등록']} · {base['주행km']:,}km · {base['색']} · "
          f"{base['점수']}점({base['등급']})\n")
    if not out["win"]:
        print("★ 이기는 차가 없다 — 올리지 않는다 (지시 P-5)")
    for band, _why, one in sorted(out["win"], key=lambda x: x[2][2]):
        (site, sid, won, ym, km, color, dx, trim, swap, weld, frame, parts,
         origin, *_rest) = one
        wear = wear_won(km, cfg)
        print(f"[{band}] {_won(won)}"
              f"{f' (＋소모품 {_won(wear)})' if wear else ''}"
              f" · {ym} · {km:,}km · {color or UNKNOWN}"
              f" · {dx or '진단 없음'}"
              f" · 골격 {frame if frame is not None else UNKNOWN}")
        print(f"      {_url(site, sid, one[18])}")
    if "--all" in sys.argv:
        print("\n★ 떨어진 까닭")
        for _b, why, one in out["lost"][:60]:
            print(f"  {_won(one[2])} {one[1]:<12}{' · '.join(why)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
