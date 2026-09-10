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
        # ★ 09-10 — ★ 사이트가 ★ 「이 차엔 **없다**」고 밝힌 옵션.
        #   ★ 그것을 안 보면 ★ 「모른다」와 「없다」를 못 가른다 (`S46-227`)
        "       l.options_absent_json,"
        "       l.undercarriage_json, l.dealer_region, l.paired_source_id,"
        "       r.accident_my_cost, r.accident_other_cost, r.accident_total_cnt,"
        "       s.grade, s.score_total, r.record_plate_hash, l.plate_hash"
        "  FROM core_listing l"
        "  LEFT JOIN core_record  r ON r.listing_id = l.listing_id"
        "  LEFT JOIN result_score s ON s.listing_id = l.listing_id"
        " WHERE l.target_key = 'GV70_25T'"
        "   AND l.status IN ('active','new','relisted')"
        "   AND l.price_current_won IS NOT NULL"
        "   AND l.price_current_won <= ?"
        "   AND l.price_current_won >= ?"
        "   AND l.year_month >= ? AND l.mileage_km <= ?"
        f"   AND COALESCE(l.advertisement_type,'') NOT IN ({m})"
        f"   AND COALESCE(l.sell_type,'') NOT IN ({m2})"
        " ORDER BY l.price_current_won",
        [c["차값_최대_원"], c.get("차값_최소_원") or 0,
         c["연식_이후"], c["주행_최대km"], *ads, *sells]
    ).fetchall()
    return got


_GONE: dict = {}


def _gone() -> dict:
    """사이트에서 내려간 매물 — ★ `tools/week_fetch.py` 가 적는다."""
    if not _GONE:
        try:
            with open(os.path.join(ROOT, "outputs", "week_gone.json"),
                      encoding="utf-8") as fh:
                _GONE.update(json.load(fh) or {"_": []})
        except (OSError, ValueError):
            _GONE["_"] = []
    return _GONE


_PLATE: dict = {}


def _plate(site: str, sid: str) -> str | None:
    """그 매물의 차번호 — ★ 보험이력 원문이 준다 (`carNo`).

    ★ 우리 표에는 ★ 해시만 남는다 (개인정보 · STEP 35) — ★ 견줄 수가 없다.
    ★ 그래서 ★ **원문 파일**을 본다.  ★ 없으면 ★ None (모른다)
    """
    import glob as _g

    key = f"{site}/{sid}"
    if key in _PLATE:
        return _PLATE[key]
    _PLATE[key] = None
    for path in _g.glob(os.path.join(ROOT, "raw", site, "record",
                                     "*", f"{sid}.json")):
        from store.rawfile import read as _read

        body = (_read(path) or {}).get("body") or b""
        if isinstance(body, bytes):
            body = body.decode("utf-8", "replace")
        try:
            said = json.loads(body).get("carNo")
        except (ValueError, TypeError, AttributeError):
            continue
        if said:
            _PLATE[key] = str(said).strip()
            break
    return _PLATE[key]


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


def swap_won(won, cfg: dict) -> int:
    """★ 갈아타는 값 — ★ 차값 ＋ **위약 80만** (마스터 09-10).

    ★ 계약을 포기하면 위약금이 든다 — ★ 그것을 안 더하면 ★ **덜 비싸 보인다**
    """
    return int(won or 0) + int(cfg.get("위약금_원") or 0)


def wear_won(km, cfg: dict) -> int:
    """소모품 — ★ 4.5만km 를 넘는 차만 더한다 (지시 3장)."""
    w = cfg["소모품"]
    if km is None or km <= w["넘는km"]:
        return 0
    return int(w["타이어_원"][0] + w["브레이크_원"][0])


def judge(one, cfg: dict) -> tuple:
    """(이기는 칸, 떨어진 까닭들).  ★ 못 본 것은 ★ 「미조회」로 남긴다."""
    c = cfg["조건"]
    (site, sid, won, ym, km, color, dx, trim, swap, weld, frame, parts,
     origin, opt_c, opt_s, opt_n, opt_absent, under, region, paired,
     my_cost, ot_cost, acc_cnt, grade, score, rec_hash, plate_hash) = one

    why = []
    if str(sid) in cfg["이미_거른_것"]:
        return None, ["이미 걸렀다 (WEEK_TASK 4·5장)"]
    if str(paired or "") in cfg["이미_거른_것"]:
        return None, ["이미 걸렀다 (같은 차)"]
    # ★★★★★ 09-10 — ★ **차번호로도 거른다.**
    #   ★ 실측 — ★ `42305326` 이 「이기는 차」로 올라왔는데 ★ 차번호가
    #     ★ ★ `342러8929` 였다 — ★ WEEK_TASK 4장의 「문 2짝 교환」 그 차다.
    #   ★ 매물번호는 ★ 사이트가 다시 등록하면 바뀐다.  ★ 차번호는 안 바뀐다
    said = _plate(site, sid)
    if said and said in cfg.get("이미_거른_차번호", ()):
        return None, [f"이미 걸렀다 (차번호 {said})"]
    # ★★★★★ 09-10 — ★ **사이트에서 내려간 차는 올리지 않는다.**
    #   ★ 실측 — ★ 값싼 열 대 중 ★ **일곱**이 404 였다.
    #   ★ 우리 표는 `active` 인데 사이트에는 없다 — ★ 두드려 본 것만 안다 (S46-267).
    #   ★ 404 와 407 은 다르다 — ★ **404 만** 여기 적힌다
    # ★★★★★ 09-10 (곧바로 고침) — ★ **상세가 404 일 때만** 「없다」다.
    #   ★ 실측 — ★ `42136860` 은 ★ 보험·점검이 404 인데 ★ 상세는 열린다.
    #     ★ ★ 그것은 ★ **그 창구를 안 연 것**이지 ★ 차가 없어진 것이 아니다.
    #   ★ 창구를 안 가리고 빼면 ★ 멀쩡한 차를 지운다 — ★ 자를 먼저 의심한다
    if "detail" in (_gone().get(str(sid)) or ()):
        return None, ["사이트에 없다 (상세가 404)"]
    if won > cfg["조건"]["차값_최대_원"]:
        return None, [f"차값 {_won(won)} — 상한 초과"]
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

    # ★★★★★ 09-10 — ★ **「모른다」를 「없다」로 읽지 않는다** (금지 12).
    #   ★ 실측 09-10 — ★ 조건에 든 735대 중 ★ 진단을 **아는 것은 73대**뿐이다.
    #     ★ ★ 그런데 칸 C·D 가 ★ 「진단 있음」을 요구해 ★ 나머지가 다 떨어졌다.
    #   ★ ★ ★ 그것은 ★ 「진단이 없다」가 아니라 ★ **「아직 안 봤다」**다.
    #   ★ 그러니 ★ 미조회는 ★ **떨어뜨리지 않고** ★ 「확인하면 이긴다」로 가른다
    hud = _has_hud(opt_c, opt_s, opt_n)
    # ★★ 사이트가 ★ 「HUD 없다」고 밝혔으면 ★ **없는 것**이다 — ★ 미조회가 아니다
    if opt_absent and ("헤드업" in str(opt_absent) or "HUD" in str(opt_absent)):
        hud = False
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
                and "흰색" in str(color or "") and hud is not False \
                and dx is not None and clean:
            band = key
            break
        # ★★ 09-10 (r1216) — ★ 칸 D 를 마스터가 더하셨다.
        #   ★ 3,900~3,999만 · 2023년 이후 · 흰색 · 진단 · 사고 0.  ★ **HUD 는 안 본다**
        if key == "D" and won <= one_band["차값_최대_원"] \
                and won > cfg["이기는_칸"][2]["차값_최대_원"] \
                and str(ym or "") >= one_band["등록_이후"] \
                and "흰색" in str(color or "") and dx is not None and clean:
            band = key
            break
    if band is None:
        # ★ 값·연식·색은 맞는데 ★ **진단이나 사고를 아직 안 본** 것인가
        maybe = (str(ym or "") >= "2023-01" and "흰색" in str(color or "")
                 and won <= cfg["조건"]["차값_최대_원"]
                 and (dx is None or acc_cnt is None))
        why.append("확인하면 이길 수 있다 (진단·사고 미조회)" if maybe
                   else "이기는 칸에 못 든다")
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
        absent = one[16]
        hud = ("없다 (사이트가 밝혔다)"
               if absent and ("헤드업" in str(absent) or "HUD" in str(absent))
               else ("있다" if _has_hud(one[13], one[14], one[15]) else UNKNOWN))
        real = swap_won(won, cfg) + wear
        print(f"[{band}] {_won(won)} → 갈아타면 {_won(real)}"
              f"{f' (위약 80만＋소모품 {_won(wear)})' if wear else ' (위약 80만)'}"
              f" · {ym} · {km:,}km · {color or UNKNOWN}"
              f" · {dx or '진단 없음'}"
              f" · 골격 {frame if frame is not None else UNKNOWN}"
              f" · ★ HUD {hud}")
        print(f"      {_url(site, sid, one[18])}")
    # ★★ 「확인하면 이긴다」 — ★ 값·연식·색은 맞는데 ★ 진단·사고를 아직 안 본 것.
    #   ★ **이것이 다음에 받을 목록**이다 — ★ 아무거나 받지 않는다 (가이드 r1215)
    maybe = [(w, o) for _b, w, o in out["lost"]
             if any("확인하면" in x for x in w)]
    if maybe:
        print(f"\n★ 확인하면 이길 수 있는 것 {len(maybe)}대 "
              "— 진단·사고만 안 봤다 (값·연식·색은 맞는다)")
        for _w, one in sorted(maybe, key=lambda x: x[1][2])[:20]:
            site, sid, won, ym, km, color = one[0], one[1], one[2], one[3], one[4], one[5]
            print(f"  {_won(won):>8} → {_won(swap_won(won, cfg) + wear_won(km, cfg))}"
                  f" · {ym} · {km:,}km · {color}"
                  f"\n        {_url(site, sid, one[19])}")
    if "--all" in sys.argv:
        print("\n★ 떨어진 까닭")
        for _b, why, one in out["lost"][:60]:
            print(f"  {_won(one[2])} {one[1]:<12}{' · '.join(why)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


def kb_only(db: str = "carwatch.db") -> list:
    """★ KB 후보 — ★ **값만 아는 것**.  ★ 연식·주행은 ★ 상세가 막혀 못 받았다.

    ★★ 그래도 낸다 — ★ 그것이 ★ **아직 아무도 안 본 곳**이기 때문이다 (지시 6-1).
      ★ ★ 다만 ★ 화면에 ★ 「연식·주행 미조회」라 적는다 — ★ 지어내지 않는다.
    ★ 값은 ★ 목록의 `data-ga4` 가 준다 (`tools/kb_list_prices.py`)
    """
    cfg = book()
    c = cfg["조건"]
    conn = sqlite3.connect(os.path.join(ROOT, db))
    got = conn.execute(
        "SELECT source_id, price_current_won, trim_grade_name,"
        "       year_month, mileage_km"
        "  FROM core_listing"
        " WHERE site = 'kbchachacha' AND target_key = 'GV70_25T'"
        "   AND price_current_won IS NOT NULL"
        "   AND price_current_won >= ? AND price_current_won <= ?"
        # ★ 마스터 차는 ★ 2.5T 다 — ★ 디젤 2.2 는 다른 차다
        "   AND trim_grade_name LIKE '%2.5T%'"
        " ORDER BY price_current_won",
        (c.get("차값_최소_원") or 0, cfg["기준차"]["차값_원"])).fetchall()
    conn.close()
    return got
