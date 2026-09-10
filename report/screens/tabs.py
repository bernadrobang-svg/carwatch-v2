# -*- coding: utf-8 -*-
"""추천 탭 2·3·4 — ★ 값을 붙인다 (지시 `r1184` A · 규격 `docs/RECOMMEND_SCREEN.md`).

★ 화면(틀·CSS)은 ★ 가이드가 짓는다.  ★ 여기는 ★ **틀이 부르는 이름에 값을 맞춘다**.
★★ 없는 값은 ★ 빈칸으로 두지 않는다 — ★ 「모름」·「미조회」를 넣는다 (지시 [화면]).
★★★ 탭 목록은 ★ `config/web.json` `recommend_tabs` 가 정본이다 —
  ★ 코드에 탭을 박지 않는다 (A-1 · 마스터 「탭들이 자꾸 늘어나고 빠진다」).
"""
from __future__ import annotations

import json as _j
import sqlite3
from urllib.parse import quote, urlencode

from report.screens.build import (
    _first_photo,
    _listings_where,
    _photo_note,
    _view_str,
    load_config,
    region_of,
)
from store.dictionary import vehicle_keys, vehicle_says, vehicle_table

UNKNOWN = "모름"
NOT_ASKED = "미조회"

# ★ 규격 ⑥ — ★ 평가 한 마디.  ★ 우리가 짓지 않는다 — ★ 가이드가 쓴 값을 읽는다
VERDICT_LABEL = {"buy": "구매 적절", "hold": "보류",
                 "wait": "대기", "risk": "위험"}


def tabs_config(root: str = ".") -> list:
    """★ A-1 — 탭 목록.  ★ 자료가 정본이다.

    ★★★★★ 09-06 (r1190 A-1) — ★ 「탭 목록을 ★ `vehicle_table.json` 에서 읽는다」.
      ★ 탭이 ★ **몇 개인가**는 ★ `web.json` `recommend_tabs` 가 말하고 ·
      ★ ★ 그 탭에 ★ **어느 차종을 내는가**는 ★ 차종 표의 `tabN` 이 말한다.
      ★ ★ ★ 그러므로 ★ **표에 한 차종도 없는 탭은 안 낸다** — ★ 빈 탭을 안 낸다.
      ★ 표를 못 읽으면 ★ 다 낸다 (`S46-289` 몫)
    """
    got = list((load_config(f"{root}/config/web.json") or {})
               .get("recommend_tabs") or [])
    if not vehicle_table(root):
        return got
    return [t for t in got
            if vehicle_keys(f"tab{t.get('n')}", root)
            or not str(t.get("n") or "").isdigit()]


def tab_list(on: str, root: str = ".", counts: dict | None = None) -> list:
    """틀이 받는 `tabs` — ★ `n`·`label`·`on`.

    ★ 시안은 ★ 「분석 · 3」처럼 ★ 수를 뒤에 붙인다 —
      ★ `config` 의 `count` 가 가리키는 수를 ★ 있을 때만 붙인다.
      ★ 0 이면 ★ 안 붙인다 (「분석 · 0」은 없는 것을 있는 것처럼 보인다)
    """
    out = []
    for t in tabs_config(root):
        label = str(t.get("label") or f"탭 {t.get('n')}")
        key = t.get("count")
        if key and (counts or {}).get(key):
            label = f"{label} · {counts[key]:,}"
        out.append({"n": str(t.get("n")), "label": label,
                    "on": str(t.get("n")) == str(on)})
    return out


def tab_template(n: str, root: str = ".") -> str | None:
    for t in tabs_config(root):
        if str(t.get("n")) == str(n):
            return t.get("template")
    return None


def tab_targets(n: str, root: str = ".") -> tuple:
    for t in tabs_config(root):
        if str(t.get("n")) == str(n):
            return tuple(t.get("targets") or ())
    return ()


# ── 값 다듬기 ────────────────────────────────────────────────────────────
def _won(v) -> str:
    """★ 만 단위.  ★ 없으면 ★ 「미조회」 — ★ 0 으로 두지 않는다 (금지 12)."""
    if v is None:
        return NOT_ASKED
    return f"{round(float(v) / 10000):,}만"


def _km(v) -> str:
    if v is None:
        return UNKNOWN
    return f"{float(v) / 10000:.1f}만km"


def _ym(v) -> str:
    s = str(v or "").strip()
    if len(s) >= 6 and s[:6].isdigit():
        return f"{s[:4]}-{s[4:6]}"
    if len(s) >= 7 and s[4] in "-.":
        return s[:7].replace(".", "-")
    return UNKNOWN


def _year_dot(v) -> str:
    s = _ym(v)
    return s.replace("-", ".") if s != UNKNOWN else UNKNOWN


def _q(base: str, **kw) -> str:
    """주소를 만든다 — ★ 값은 반드시 인코딩한다 (`S46-66`)."""
    got = [(k, v) for k, v in kw.items() if v not in (None, "", ())]
    flat: list = []
    for k, v in got:
        flat.extend((k, x) for x in v) if isinstance(v, (list, tuple)) \
            else flat.append((k, v))
    return f"{base}?{urlencode(flat, quote_via=quote)}" if flat else base


def _median(xs: list):
    if not xs:
        return None
    xs = sorted(xs)
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else (xs[m - 1] + xs[m]) / 2


def _quantile(xs: list, p: float):
    if not xs:
        return None
    xs = sorted(xs)
    i = max(0, min(len(xs) - 1, round(p * (len(xs) - 1))))
    return xs[i]


# ── 탭 2 — 값 → 등급 → 취향 (A-2 · A-6 · A-7 · A-8 · A-9) ────────────────
GRADE_ORDER = ("S", "A", "B", "C", "D", "E", "F", "G")
# ★ 규격 ⑤-2 — ★ 목록 펼침에 낼 넷 ＋ 옵션·보증·트림·색.  ★ 26축은 `/detail` 몫
SAFE_AXES = ("state.accident", "state.frame", "state.outer")


def _band_where(band: dict, col: str, lo: str, hi: str) -> tuple:
    """값·주행 칸 하나를 SQL 로. ★ 칸은 `config` 가 준다 — 코드에 안 박는다."""
    where, args = [], []
    if band.get(lo) is not None:
        where.append(f"{col} > ?")
        args.append(band[lo])
    if band.get(hi) is not None:
        where.append(f"{col} <= ?")
        args.append(band[hi])
    return where, args


def _picks(conn, root, flt, sel: dict, base: str) -> list:
    """★ A-7 — 고르개.  ★ 고른 것은 ★ 모두 함께(AND) 걸린다.

    ★ 켜고 끄는 주소를 ★ 여기서 만든다 — ★ 누르면 그 하나만 뒤집힌다.
    ★ 「배달」 묶음은 ★ 안 낸다 — ★ 어느 사이트도 배달 여부를 주지 않는다
      (09-06 실측 0건).  ★ 없는 것을 있는 척 내지 않는다 (금지 6)
    """
    cfg = load_config(f"{root}/config/web.json") or {}
    names = load_config(f"{root}/config/targets.json") or {}
    out = []

    def group(label, key, items):
        got = []
        for k, txt in items:
            on = k in sel.get(key, ())
            now = [x for x in sel.get(key, ()) if x != k] if on \
                else [*sel.get(key, ()), k]
            q = dict(sel)
            q[key] = now
            got.append({"label": txt, "on": on,
                        "q": _q(base, **{kk: vv for kk, vv in q.items() if vv})})
        if got:
            out.append({"label": label, "items": got})

    # ★★★★★ 09-06 (r1190 K) — ★ **배달 묶음을 낸다.**  ★ 전에는 못 냈다 —
    #   ★ 어느 사이트도 배달 여부를 안 줬기 때문이다 (09-05 실측 0건).
    #   ★ 이제 ★ `delivery_nationwide` 가 있다 (엔카 실측 Y 5,913 · N 3,382)
    group("배달", "dv", [("Y", "전국 배달"), ("N", "배달 없음"),
                         ("q", "배달 미조회")])
    group("지역", "rg", [(r["key"], r["label"])
                         for r in cfg.get("recommend_regions") or ()])
    live = [r[0] for r in conn.execute(
        "SELECT target_key, COUNT(*) FROM core_listing"
        " WHERE target_key IS NOT NULL AND status IN"
        " ('active','new','relisted') GROUP BY 1 ORDER BY 2 DESC")
        # ★ J-4 — ★ 그 탭에 내는 차종만 고르개에 낸다 (차종 표가 정본)
        if vehicle_says(r[0], "tab2", root) or not vehicle_table(root)]
    group("차종", "m", [(k, str((names.get(k) or {}).get("label") or k))
                        for k in live])
    group("등급", "g", [(g, g) for g in GRADE_ORDER])
    group("값", "pb", [(b["key"], b["label"])
                       for b in cfg.get("recommend_price_bands") or ()])
    del flt
    return out


def _sorts(root, sel: dict, base: str) -> tuple:
    """★ A-8 — 줄 세우기 여섯.  ★ 눌린 것이 보인다."""
    cfg = load_config(f"{root}/config/web.json") or {}
    now = sel.get("sort") or "value"
    got = []
    for s in cfg.get("recommend_sorts") or ():
        q = dict(sel)
        q["sort"] = s["key"]
        got.append({"label": s["label"], "on": s["key"] == now,
                    "q": _q(base, **{k: v for k, v in q.items() if v})})
    return tuple(got), now


ORDER_SQL = {
    "value":  "l.price_current_won IS NULL, l.price_current_won ASC",
    "grade":  "s.grade IS NULL, _grade_rank ASC",
    "taste":  "_taste IS NULL, _taste DESC",
    "safe":   "_safe IS NULL, _safe DESC",
    "km":     "l.mileage_km IS NULL, l.mileage_km ASC",
    "year":   "l.year_month IS NULL, l.year_month DESC",
}


def _pager(total: int, page: int, size: int, sel: dict, base: str) -> dict:
    """★ A-6 — 「N건 중 1–20」 ＋ 쪽 번호 ＋ 맨 앞·맨 뒤."""
    last = max(1, (total + size - 1) // size)
    page = max(1, min(page, last))
    lo = (page - 1) * size + 1 if total else 0
    hi = min(page * size, total)

    def q(n):
        got = dict(sel)
        got["pg"] = n
        return _q(base, **{k: v for k, v in got.items() if v})

    lo_n, hi_n = max(1, page - 4), min(last, max(1, page - 4) + 8)
    # ★ 틀은 ★ `page.first` · `page.last` 를 ★ **주소**로 쓴다 (`href`) —
    #   ★ 쪽 수는 ★ `pages` 로 따로 준다
    return {"total": total, "from": lo, "to": hi, "page": page, "pages": last,
            "links": [{"n": n, "on": n == page, "q": q(n)}
                      for n in range(lo_n, hi_n + 1)],
            "first": q(1), "last": q(last)}


def _sel(query: dict, query_all: dict) -> dict:
    """주소에서 고른 것을 읽는다. ★ 여럿은 `query_all` 이 다 준다."""
    def many(k):
        got = tuple((query_all or {}).get(k) or ())
        if not got and (query or {}).get(k):
            got = (str(query[k]),)
        return tuple(x for x in got if x)
    return {"rg": many("rg"), "m": many("m"), "g": many("g"), "pb": many("pb"),
            "dv": many("dv"),
            "sort": str((query or {}).get("sort") or "") or None}


def _region_kind(label: str | None, root: str = ".") -> tuple:
    """지역 글자 → (보일 말, 갈래).  ★ 모르면 ★ 「미조회」 — 지어내지 않는다."""
    if not label:
        return NOT_ASKED, "far"
    cfg = load_config(f"{root}/config/web.json") or {}
    for r in cfg.get("recommend_regions") or ():
        for m in r.get("match") or ():
            if m and m in label:
                return label, str(r.get("kind") or "far")
    return label, "far"


def _region_key(label: str | None, root: str = ".") -> str:
    if not label:
        return "etc"
    cfg = load_config(f"{root}/config/web.json") or {}
    for r in cfg.get("recommend_regions") or ():
        for m in r.get("match") or ():
            if m and m in label:
                return str(r["key"])
    return "etc"


def view_tab2(conn: sqlite3.Connection, calc_version: str, flt,
              query: dict, query_all: dict, root: str = ".") -> dict:
    """★ A-2 — 탭 2 에 넘길 값 전부.

    ★ 값 → 등급 → 취향 차례가 기본이다 (규격 「값이 먼저」).
    ★ 목록 조건은 ★ `/listings` 와 ★ **같은 부품**(`_listings_where`)을 쓴다 —
      ★ 갈라 두면 ★ 「N건 중」이 거짓말이 된다 (`V11-55`).
    """
    base = "/recommend"
    sel = _sel(query, query_all)
    sel_q = {"tab": "2", **{k: v for k, v in sel.items() if v}}
    cfg = load_config(f"{root}/config/web.json") or {}
    size = int(cfg.get("rows_per_page") or 30)

    where, args = _listings_where(flt)
    where = list(where)
    # ★★★★★ 09-06 (r1188 J-4) — ★ **탭마다 낼 차종이 다르다.**
    #   ★ 정본은 ★ `config/vehicle_table.json` 의 ★ `tab2` 칸이다.
    #   ★ 표가 없으면 ★ 안 거른다 — ★ 표가 없다고 화면이 비면 안 된다 (`S46-289` 몫)
    _on2 = vehicle_keys("tab2", root)
    if vehicle_table(root) and _on2:
        marks = ",".join("?" * len(_on2))
        where.append(f"l.target_key IN ({marks})")
        args.extend(_on2)
    if sel["m"]:
        marks = ",".join("?" * len(sel["m"]))
        where.append(f"l.target_key IN ({marks})")
        args.extend(sel["m"])
    if sel["g"]:
        marks = ",".join("?" * len(sel["g"]))
        where.append(f"s.grade IN ({marks})")
        args.extend(sel["g"])
    # ★ 지역 — ★ 세는 것과 뽑는 것이 ★ **같은 조건**이어야 한다 (`V11-55`).
    #   ★ 그러므로 ★ SQL 에 건다 — ★ 뽑은 뒤에 걸러 내면 ★ 「N건 중」이 거짓말이 된다.
    #   ★ `region_of` 는 ★ ① `dealer_region` ② 지점 이름 표 차례로 보므로
    #     ★ ★ 두 칸을 다 훑는다.  ★ 「그 외」는 ★ **다른 어느 갈래도 아닌 것**이다
    if sel["rg"]:
        cfgr = cfg.get("recommend_regions") or []
        named = [m for r in cfgr for m in (r.get("match") or ())]
        ors, oargs = [], []
        for key in sel["rg"]:
            one = next((r for r in cfgr if r["key"] == key), None)
            if not one:
                continue
            got = [m for m in (one.get("match") or ()) if m]
            if got:
                ors.append("(" + " OR ".join(
                    "l.dealer_region LIKE ? OR l.dealer_shop LIKE ?"
                    for _ in got) + ")")
                for m in got:
                    oargs.extend([f"%{m}%", f"%{m}%"])
            else:
                # ★ 「그 외」 — ★ 이름 붙은 어느 곳에도 안 드는 것
                ors.append("NOT (" + " OR ".join(
                    "COALESCE(l.dealer_region,'') LIKE ?"
                    " OR COALESCE(l.dealer_shop,'') LIKE ?"
                    for _ in named) + ")" if named else "1=1")
                for m in named:
                    oargs.extend([f"%{m}%", f"%{m}%"])
        if ors:
            where.append("(" + " OR ".join(ors) + ")")
            args.extend(oargs)
    # ★ A-7 — ★ 배달.  ★ `q` 는 ★ **미조회**다 — ★ N 과 다르다 (K-4)
    if sel["dv"]:
        part, dargs = [], []
        for key in sel["dv"]:
            if key == "q":
                part.append("l.delivery_nationwide IS NULL")
            else:
                part.append("l.delivery_nationwide = ?")
                dargs.append(key)
        where.append("(" + " OR ".join(part) + ")")
        args.extend(dargs)
    for key in sel["pb"]:
        band = next((b for b in cfg.get("recommend_price_bands") or ()
                     if b["key"] == key), None)
        if band:
            w, a = _band_where(band, "l.price_current_won",
                               "min_won", "max_won")
            if w:
                where.append("(" + " AND ".join(w) + ")")
                args.extend(a)

    sorts, order = _sorts(root, sel_q, base)
    taste_sql = ("(SELECT SUM(value) FROM result_axis x WHERE"
                 " x.listing_id = l.listing_id AND x.excluded = 0"
                 " AND x.axis LIKE 'taste.%')")
    safe_sql = ("(SELECT SUM(value) FROM result_axis x WHERE"
                " x.listing_id = l.listing_id AND x.excluded = 0"
                f" AND x.axis IN ({','.join('?' * len(SAFE_AXES))}))")
    grade_rank = "CASE s.grade " + " ".join(
        f"WHEN '{g}' THEN {i}" for i, g in enumerate(GRADE_ORDER)) + " ELSE 99 END"

    body = (" FROM core_listing l"
            " LEFT JOIN result_score s ON s.listing_id = l.listing_id"
            " WHERE " + " AND ".join(where))
    total = conn.execute("SELECT COUNT(*)" + body, list(args)).fetchone()[0]
    page = _pager(total, int(str((query or {}).get("pg") or 1) or 1),
                  size, sel_q, base)

    cols = ("l.listing_id, l.site, l.target_key, l.price_current_won,"
            " l.year_month, l.mileage_km, l.color_ext_raw, l.color_int_raw,"
            " l.trim_badge, l.trim_grade_name, l.photo_list_json,"
            " l.dealer_region, l.dealer_shop, l.sell_type,"
            " l.warranty_body_month, l.warranty_body_km,"
            " l.site_pass_grade, l.ev_battery_soh, l.price_origin_won,"
            " l.options_choice_json, l.advertisement_type, s.grade,"
            " l.paired_source_id, s.confirmed_points, l.source_id,"
            " l.delivery_nationwide, l.site_inspection,"
            " (SELECT accident_my_cost FROM core_record x"
            "   WHERE x.listing_id = l.listing_id) AS _ins,"
            f" {taste_sql} AS _taste, {safe_sql} AS _safe,"
            f" {grade_rank} AS _grade_rank")
    got = conn.execute(
        "SELECT " + cols + body + " ORDER BY "
        + ORDER_SQL.get(order, ORDER_SQL["value"])
        + ", l.listing_id LIMIT ? OFFSET ?",
        [*SAFE_AXES, *args, size, (page["page"] - 1) * size]).fetchall()

    from report.screens.build import site_badge

    names = load_config(f"{root}/config/targets.json") or {}
    sites = (load_config(f"{root}/config/sites.json") or {}).get("labels") or {}
    rows = []
    for r in got:
        region = region_of(r[1], r[11], r[12], root)
        rlabel, rkind = _region_kind(region, root)
        photos = r[10]
        rows.append({
            "listing_id": r[0],
            "photo_url": _first_photo(photos, root),
            "photo_note": _photo_note(r[1], photos,
                                      _view_str("photo_base_url", root), None)
            or NOT_ASKED,
            "price": _won(r[3]),
            "grade": r[21] or "판정 중",
            "taste_rank": None,
            "title": str((names.get(r[2]) or {}).get("label") or r[2] or UNKNOWN),
            "meta": " · ".join(x for x in (
                _ym(r[4]), _km(r[5]),
                " / ".join(y for y in (r[6], r[7]) if y) or None,
                sites.get(r[1], r[1])) if x),
            # ★ 09-06 K — ★ 전국 배달이면 ★ 지역을 안 봐도 된다 (규격 ⑤ ①).
            #   ★ 틀의 `.rc2-region.deliver` 가 그 자리다
            "region": ("전국 배달" if str(r[25] or "") == "Y" else rlabel),
            "region_kind": ("deliver" if str(r[25] or "") == "Y" else rkind),
            "over_budget": False,
            "depreciation": _dep(r[3], r[18]),
            "dep_ok": _dep_ok(r[3], r[18]),
            "soh": f"{r[17]}%" if r[17] is not None else None,
            "accident": None,
            "km_vs_avg": _km(r[5]),
            "trim": r[9] or r[8] or UNKNOWN,
            # ★★★★★ 09-06 (r1190 A-6 · A-8 · A-10 · A-11 · A-12) —
            #   ★ 마스터 지시 — 「★ **목록과 추천 1 의 정보는 ★ 추천 2·3 에
            #     ★ ★ 다 들어가야 한다**」.  ★ 탭 1 이 내던 것을 여기도 낸다
            "site_badge": site_badge(r[1], None, root),
            "encar_url": _source_url_of(r[1], r[24], r[22], root),
            "accident_tone": _accident_tone(r[27], None, _tab3_cfg(root))[0],
            "clean_car": _accident_tone(r[27], None, _tab3_cfg(root))[1],
            "insurance_cost": (_won(r[27]) if r[27] is not None
                               else NOT_ASKED),
            "thin_data": (r[23] is not None
                          and r[23] < (_tab3_cfg(root).get("thin_points")
                                       or 700)),
            "thin_why": _thin_why(r[18], r[27], r[26]),
            "colors": " / ".join(y for y in (r[6], r[7]) if y) or UNKNOWN,
            "options": _opt_label(r[19]),
            "warranty": _warranty(r[14], r[15]),
            "site_warranty": r[16] or NOT_ASKED,
            "tire": NOT_ASKED,
        })
    for i, one in enumerate(rows, 1):
        one["taste_rank"] = i if order == "taste" else None
    del calc_version
    return {"picks": _picks(conn, root, flt, sel_q, base), "sorts": sorts,
            "page": page, "rows": rows}


def _dep(now, origin):
    """감가율.  ★ 신차가를 모르면 ★ None — ★ 0% 라 적지 않는다."""
    if not now or not origin:
        return None
    return f"{(1 - float(now) / float(origin)) * 100:.0f}%"


def _dep_ok(now, origin):
    if not now or not origin:
        return False
    return (1 - float(now) / float(origin)) >= 0.5


def _opt_label(raw) -> str:
    try:
        got = _j.loads(raw) if raw else []
    except (ValueError, TypeError):
        return NOT_ASKED
    if not isinstance(got, list) or not got:
        return NOT_ASKED
    return f"{len(got)}가지"


def _warranty(month, km) -> str:
    part = []
    if month:
        part.append(f"{month}개월")
    if km:
        part.append(f"{int(km):,}km")
    return " · ".join(part) if part else NOT_ASKED


# ── 탭 3 — 분석 (A-3 · A-5) ─────────────────────────────────────────────
def analyze_count(conn, account_id: int) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM analyze_request"
        " WHERE account_id = ? AND dropped_at IS NULL",
        (account_id,)).fetchone()[0]


def view_analyze_list(conn: sqlite3.Connection, account_id: int,
                      root: str = ".") -> dict:
    """★ 분석을 맡긴 차 (`/analyze`).  ★ **내가 맡긴 차만** 있다 (관심과 따로다).

    ★★★★★ 09-06 (r1190 A-14) — ★ 마스터께서 ★ **탭 3 을 다시 정하셨다** —
      ★ ★ 「가이드가 쓴 글」이 아니라 ★ **GV70 후보 목록**이다 (`view_tab3`).
      ★ ★ ★ 그래서 이 갈래는 ★ 탭에서 내려와 ★ `/analyze` 길만 쓴다.
      ★ ★ ★ ★ 「분석 맡기기」 단추는 ★ 그대로다 — ★ 담은 것이 여기 쌓인다

    ★ 평가와 글은 ★ **가이드가 쓴다** — ★ 없으면 ★ 「대기」 · 「아직 분석 전」이다.
      ★ 우리가 지어내지 않는다 (규격 ⑥ 「모르는 것은 「모른다」」)
    ★ 항목 수를 못 박지 않는다 — ★ `parts` 가 주는 만큼 낸다
    """
    names = load_config(f"{root}/config/targets.json") or {}
    sites = (load_config(f"{root}/config/sites.json") or {}).get("labels") or {}
    got = conn.execute(
        "SELECT a.listing_id, a.asked_at, a.verdict, a.body,"
        "       l.target_key, l.year_month, l.mileage_km,"
        "       l.price_current_won, l.site"
        "  FROM analyze_request a"
        "  JOIN core_listing l ON l.listing_id = a.listing_id"
        " WHERE a.account_id = ? AND a.dropped_at IS NULL"
        " ORDER BY a.asked_at DESC", (account_id,)).fetchall()
    rows = []
    for r in got:
        verdict = r[2] or "wait"
        rows.append({
            "listing_id": r[0],
            "title": str((names.get(r[4]) or {}).get("label") or r[4] or UNKNOWN),
            "meta": " · ".join(x for x in (
                _ym(r[5]), _km(r[6]), _won(r[7]),
                sites.get(r[8], r[8])) if x),
            "verdict": verdict,
            "verdict_label": VERDICT_LABEL.get(verdict, "대기"),
            "asked_at": str(r[1] or "")[:16].replace("T", " ") or UNKNOWN,
            "parts": _parts(r[3]),
        })
    return {"rows": rows, "count": len(rows),
            "total_url": "/recommend?tab=3&total=1"}


def _parts(body) -> list:
    """가이드가 쓴 글을 ★ 제목/본문 마디로 나눈다. ★ 없으면 빈 목록이다."""
    if not body:
        return []
    try:
        got = _j.loads(body)
    except (ValueError, TypeError):
        return [{"h": "분석", "p": str(body)}]
    if isinstance(got, list):
        return [{"h": str(x.get("h") or ""), "p": str(x.get("p") or "")}
                for x in got if isinstance(x, dict)]
    return [{"h": "분석", "p": str(body)}]


# ── 타 AI 요청 — ★ 원문을 그대로 하나의 글월로 (규격 ⑦) ──────────────────
COPY_FIELDS = (
    ("사이트", "site"), ("매물번호", "source_id"), ("차종", "target_key"),
    ("트림", "trim_grade_name"), ("등급명", "trim_badge"),
    ("연식", "year_month"), ("주행", "mileage_km"),
    ("표시가", "price_current_won"), ("신차가", "price_origin_won"),
    ("외장색", "color_ext_raw"), ("내장색", "color_int_raw"),
    ("연료", "fuel_raw"), ("변속기", "transmission"),
    ("판매형태", "sell_type"), ("광고형태", "advertisement_type"),
    ("압류", "seizing_cnt"), ("저당", "pledge_cnt"),
    ("소유자변경", "owner_change_cnt_summary"),
    ("전손", "total_loss_cnt_summary"), ("침수(전손)", "flood_total_cnt_summary"),
    ("침수(분손)", "flood_part_cnt_summary"), ("도난", "robber_cnt_summary"),
    ("보험이력", "has_record"), ("성능점검", "has_resume"),
    ("배터리 SOH", "ev_battery_soh"),
    ("기본옵션", "options_standard_json"), ("선택옵션", "options_choice_json"),
    ("판매지역", "dealer_region"), ("판매점", "dealer_shop"),
)


def copy_text(conn: sqlite3.Connection, listing_id: int,
              root: str = ".") -> str:
    """★ 규격 ⑦ — ★ **사이트가 준 원문 그대로** 하나의 글월로.

    ★ 우리가 고친 값이 아니다 — ★ `core_listing` 에 담긴 ★ 원문 칸을 그대로 낸다.
    ★ 없는 것은 ★ 「미조회」라 적는다 — ★ 빈칸으로 두지 않는다
    """
    cols = ", ".join(c for _, c in COPY_FIELDS)
    row = conn.execute(
        f"SELECT {cols} FROM core_listing WHERE listing_id = ?",
        (listing_id,)).fetchone()
    if not row:
        return f"매물 {listing_id} 이 없습니다."
    out = [f"# 매물 {listing_id} — 사이트가 준 원문 그대로",
           "# (우리가 고친 값이 아닙니다.  없는 것은 「미조회」입니다)", ""]
    for (label, _c), v in zip(COPY_FIELDS, row, strict=True):
        out.append(f"{label}: {NOT_ASKED if v is None or v == '' else v}")
    url = _source_link(conn, listing_id, root)
    out.append(f"사이트 주소: {url or NOT_ASKED}")
    return "\n".join(out)


def _source_link(conn, listing_id: int, root: str = ".") -> str | None:
    from report.screens.build import _site_detail_urls, _source_url

    row = conn.execute(
        "SELECT site, source_id, paired_source_id FROM core_listing"
        " WHERE listing_id = ?", (listing_id,)).fetchone()
    if not row:
        return None
    try:
        return _source_url(row[0], row[1], _site_detail_urls(root), row[2])
    except (TypeError, ValueError, KeyError):
        return None


# ── 탭 4 — 두 차종 격자 (A-4 · B-11 · B-12) ─────────────────────────────
# ★★★★★ 09-06 — ★ 마스터께서 ★ **직접 재신 표**를 화면에 낸다 (지시 0-1c).
#   ★ **리스·렌트를 뺀 수**로 낸다 — ★ 879 가 아니라 755 다.
#   ★ 정본은 ★ `config/scoring.json` 의 관문이다 — ★ 코드에 말을 안 박는다
def _lease_where() -> tuple:
    """리스·렌트를 뺀다 (B-8 · 0-1c).

    ★ 갈래 이름을 ★ **코드에 박지 않는다** (`S14`) — ★ `config/scoring.json` 이
      ★ 정본이고 ★ `_lease_kinds()` 가 목록과 ★ **같은 부품**이다.
    ★ 실측 09-06 — GV70 2,042건 중 ★ 160건이 리스·렌트다
    """
    from report.screens.build import _lease_kinds

    ads, sells = _lease_kinds()
    part, args = [], []
    if ads:
        marks = ",".join("?" * len(ads))
        part.append(f"COALESCE(l.advertisement_type,'') NOT IN ({marks})")
        args.extend(ads)
    if sells:
        marks = ",".join("?" * len(sells))
        part.append(f"COALESCE(l.sell_type,'') NOT IN ({marks})")
        args.extend(sells)
    return (" AND ".join(part) or "1=1"), args


def _band_case(bands: list, col: str, lo: str, hi: str) -> tuple:
    """칸을 ★ 한 줄의 `CASE` 로 바꾼다 — ★ 칸마다 질의하지 않으려고."""
    part, args = [], []
    for b in bands:
        w, a = _band_where(b, col, lo, hi)
        part.append(f"WHEN {' AND '.join(w) or '1=1'} THEN ?")
        args.extend([*a, b["key"]])
    return "CASE " + " ".join(part) + " ELSE NULL END", args


def _grid_stats(conn, target: str, pbs: list, kbs: list) -> dict:
    """★★★★★ 09-06 (r1184 · `V11-34` 가 잡았다) — ★ 격자를 ★ **한 번에** 뽑는다.

    ★ 전에는 ★ 칸마다 한 질의였다 — ★ 4×4 = **16 질의**.
      ★ 실측 09-06 — ★ `/recommend?tab=4` 한 쪽이 ★ **28 질의**(상한 20)였다.
    ★ 칸 나누기를 ★ `CASE` 로 옮겨 ★ **한 질의**로 줄인다
    """
    lw, la = _lease_where()
    pcase, pargs = _band_case(pbs, "l.price_current_won", "min_won", "max_won")
    kcase, kargs = _band_case(kbs, "l.mileage_km", "min_km", "max_km")
    got = conn.execute(
        f"SELECT {pcase} AS pb, {kcase} AS kb, COUNT(*),"
        "       AVG(l.price_current_won), AVG(l.mileage_km),"
        "       AVG(CAST(SUBSTR(l.year_month,1,4) AS INTEGER)),"
        "       AVG(CAST(SUBSTR(l.year_month,6,2) AS INTEGER))"
        f" FROM core_listing l WHERE l.target_key = ? AND {lw}"
        " GROUP BY 1, 2",
        [*pargs, *kargs, target, *la]).fetchall()
    out = {}
    for r in got:
        if r[0] is None or r[1] is None:
            continue
        out[(r[0], r[1])] = {"n": r[2] or 0, "price": r[3], "km": r[4],
                             "year": (r[5], r[6]) if r[5] else None}
    return out


def _year_label(pair) -> str:
    if not pair or pair[0] is None:
        return UNKNOWN
    y, m = pair
    return f"{round(y)}.{max(1, min(12, round(m or 1)))}"


def view_tab4(conn: sqlite3.Connection, query: dict,
              root: str = ".") -> dict:
    """★ A-4 · B-11 · B-12 — 두 차종 · 격자 둘 · 칸을 누르면 등급순 목록."""
    cfg = load_config(f"{root}/config/web.json") or {}
    names = load_config(f"{root}/config/targets.json") or {}
    # ★ J-4 — ★ 탭 4 의 두 차종도 ★ **표**가 정한다 (`tab4` 칸).
    #   ★ `config/web.json` 의 `targets` 는 ★ 표가 없을 때만 쓴다
    keys = vehicle_keys("tab4", root) or tab_targets("4", root)
    if not keys:
        return {"two": [], "rows": [], "pick": None}
    cur = str((query or {}).get("m") or keys[0])
    if cur not in keys:
        cur = keys[0]
    label = str((names.get(cur) or {}).get("label") or cur)

    two = []
    for k in keys:
        n = conn.execute(
            "SELECT COUNT(*) FROM core_listing l WHERE l.target_key = ?",
            (k,)).fetchone()[0]
        d = conn.execute(
            "SELECT COUNT(*) FROM core_listing l WHERE l.target_key = ?"
            " AND l.detail_status = 'ok'", (k,)).fetchone()[0]
        two.append({"key": k, "on": k == cur,
                    "label": str((names.get(k) or {}).get("label") or k),
                    "cnt": f"{n:,}건 · 상세 {d:,}건",
                    "q": _q("/recommend", tab="4", m=k)})

    pbs = list(cfg.get("recommend_price_bands") or ())
    kbs = list(cfg.get("recommend_km_bands") or ())
    _lw, _la = _lease_where()
    live = conn.execute(
        "SELECT COUNT(*) FROM core_listing l WHERE l.target_key = ? AND "
        + _lw, (cur, *_la)).fetchone()[0]
    allc = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE target_key = ?",
        (cur,)).fetchone()[0]

    sel_p = str((query or {}).get("p") or "")
    sel_k = str((query or {}).get("km") or "")
    grid = _grid_stats(conn, cur, pbs, kbs)
    rows_g = []
    for pb in pbs:
        cells = []
        for kb in kbs:
            st = grid.get((pb["key"], kb["key"]),
                          {"n": 0, "price": None, "km": None, "year": None})
            on = (pb["key"] == sel_p and kb["key"] == sel_k)
            cells.append({
                "n": st["n"] if st["n"] else "—",
                "price": _won(st["price"]), "km": _km(st["km"]),
                "year": _year_label(st["year"]),
                "q": _q("/recommend", tab="4", m=cur,
                        p=pb["key"], km=kb["key"]) if st["n"] else None,
                "cls": ("none" if not st["n"]
                        else ("sel" if on else ("hot" if st["n"] >= 30 else "")))})
        rows_g.append({"label": pb["label"], "cells": cells})

    grid_km = {"title": f"{label} · 가격대 × 주행",
               "note": f"리스·렌트를 뺀 {live:,}건. {allc:,}건이 아닙니다",
               "cols": [k["label"] for k in kbs], "rows": rows_g,
               "split": _split_km(rows_g, kbs)}

    trim_rows = []
    for pb in pbs:
        w = ["l.target_key = ?", _lw]
        a: list = [cur, *_la]
        ww, aa = _band_where(pb, "l.price_current_won", "min_won", "max_won")
        w.extend(ww)
        a.extend(aa)
        got = conn.execute(
            "SELECT COALESCE(NULLIF(l.trim_grade_name,''),"
            "       NULLIF(l.trim_badge,''), '모름'),"
            "       COUNT(*), AVG(l.mileage_km),"
            "       AVG(CAST(SUBSTR(l.year_month,1,4) AS INTEGER)),"
            "       AVG(CAST(SUBSTR(l.year_month,6,2) AS INTEGER))"
            " FROM core_listing l WHERE " + " AND ".join(w)
            + " GROUP BY 1 ORDER BY 2 DESC LIMIT 4", a).fetchall()
        for i, r in enumerate(got):
            trim_rows.append({"price_label": pb["label"] if not i else "",
                              "trim": r[0], "n": r[1], "km": _km(r[2]),
                              "year": _year_label((r[3], r[4])), "cls": ""})
    grid_trim = {"title": f"{label} · 가격대별 트림", "rows": trim_rows,
                 "split": _split_trim(trim_rows)}

    pick, rows = None, []
    if sel_p and sel_k:
        pb = next((b for b in pbs if b["key"] == sel_p), None)
        kb = next((b for b in kbs if b["key"] == sel_k), None)
        if pb and kb:
            rows = _cell_rows(conn, cur, pb, kb, root)
            pick = {"label": f"{pb['label']} · {kb['label']}",
                    "cnt": len(rows),
                    "clear": _q("/recommend", tab="4", m=cur)}
    return {"two": two, "market": _market(conn, cur, label),
            "grid_km": grid_km, "grid_trim": grid_trim,
            "pick": pick, "rows": rows,
            "head": " · ".join(o["label"] for o in two),
            "sub": "두 차종만 봅니다. 리스·렌트를 뺀 수로 냅니다"}


def _split_km(rows_g: list, kbs: list) -> str:
    """★ 값이 갈리는 자리 — ★ **잰 수로만** 적는다.  ★ 문장을 지어내지 않는다."""
    said = []
    for i in range(len(rows_g) - 1):
        a = [c for c in rows_g[i]["cells"] if isinstance(c["n"], int)]
        b = [c for c in rows_g[i + 1]["cells"] if isinstance(c["n"], int)]
        if not a or not b:
            continue
        ka = _avg_km_of(rows_g[i]), _avg_km_of(rows_g[i + 1])
        if ka[0] is None or ka[1] is None:
            continue
        said.append(f"{rows_g[i]['label']} → {rows_g[i + 1]['label']} 이면 "
                    f"주행이 {ka[0]:.1f}만 → {ka[1]:.1f}만")
    del kbs
    return " · ".join(said) if said else UNKNOWN


def _avg_km_of(row) -> float | None:
    got = [c for c in row["cells"]
           if isinstance(c["n"], int) and c["km"] != UNKNOWN]
    if not got:
        return None
    tot = sum(c["n"] * float(c["km"].replace("만km", "")) for c in got)
    return tot / sum(c["n"] for c in got)


def _split_trim(rows: list) -> str:
    """같은 값대에서 트림끼리 주행을 견준다. ★ 잰 것만 적는다."""
    said = []
    seen: dict = {}
    for r in rows:
        key = r["price_label"] or (list(seen)[-1] if seen else "")
        seen.setdefault(key, []).append(r)
    for band, got in seen.items():
        got = [g for g in got if g["km"] != UNKNOWN]
        if len(got) < 2:
            continue
        got.sort(key=lambda g: float(g["km"].replace("만km", "")))
        said.append(f"{band} — {got[0]['trim']} {got[0]['km']} < "
                    f"{got[-1]['trim']} {got[-1]['km']}")
    return " · ".join(said) if said else UNKNOWN


def _market(conn, target: str, label: str) -> dict:
    _mlw, _mla = _lease_where()
    got = conn.execute(
        "SELECT price_current_won, mileage_km, price_origin_won, year_month"
        " FROM core_listing l WHERE l.target_key = ? AND " + _mlw,
        (target, *_mla)).fetchall()
    price = [float(r[0]) for r in got if r[0]]
    km = [float(r[1]) for r in got if r[1]]
    origin = [float(r[2]) for r in got if r[2]]
    by_year: dict = {}
    for r in got:
        y = str(r[3] or "")[:4]
        if y.isdigit() and r[0]:
            by_year.setdefault(y, []).append(float(r[0]))
    said = " · ".join(f"{y} {_won(_median(v))}"
                      for y, v in sorted(by_year.items()) if len(v) >= 3)
    return {"title": f"{label} · 중고 시장",
            "sample": f"{len(got):,}",
            "median": _won(_median(price)), "q1": _won(_quantile(price, .25)),
            "q3": _won(_quantile(price, .75)),
            "origin": _won(_median(origin)) if origin else NOT_ASKED,
            "origin_cls": "" if origin else "v3-unknown",
            "avg_km": _km(sum(km) / len(km)) if km else UNKNOWN,
            "by_year": said or UNKNOWN}


def _cell_rows(conn, target: str, pb: dict, kb: dict, root: str) -> list:
    """★ B-12 — 고른 칸의 차를 ★ **등급순**으로 (A → E · PENDING 은 맨 뒤)."""
    lw, la = _lease_where()
    w = ["l.target_key = ?", lw]
    a: list = [target, *la]
    for band, col, lo, hi in ((pb, "l.price_current_won", "min_won", "max_won"),
                              (kb, "l.mileage_km", "min_km", "max_km")):
        ww, aa = _band_where(band, col, lo, hi)
        w.extend(ww)
        a.extend(aa)
    rank = "CASE s.grade " + " ".join(
        f"WHEN '{g}' THEN {i}" for i, g in enumerate(GRADE_ORDER)) + " ELSE 99 END"
    got = conn.execute(
        "SELECT l.listing_id, l.price_current_won, s.grade, l.trim_badge,"
        "       l.trim_grade_name, l.year_month, l.mileage_km,"
        "       l.color_ext_raw, l.color_int_raw, l.site, l.photo_list_json,"
        "       l.dealer_region, l.dealer_shop, l.price_origin_won,"
        "       l.advertisement_type, l.options_choice_json"
        "  FROM core_listing l"
        "  LEFT JOIN result_score s ON s.listing_id = l.listing_id"
        " WHERE " + " AND ".join(w)
        + f" ORDER BY {rank}, l.price_current_won LIMIT 40", a).fetchall()
    sites = (load_config(f"{root}/config/sites.json") or {}).get("labels") or {}
    out = []
    for r in got:
        region = region_of(r[9], r[11], r[12], root)
        rlabel, rkind = _region_kind(region, root)
        out.append({
            "listing_id": r[0], "price": _won(r[1]),
            "grade": r[2] or "PENDING",
            "verdict": None, "verdict_cls": "",
            "title": " ".join(x for x in (r[4] or r[3],) if x) or UNKNOWN,
            "lease": bool(r[14]),
            # ★ 09-06 K — ★ 전국 배달이면 ★ 지역을 안 봐도 된다 (규격 ⑤ ①).
            #   ★ 틀의 `.rc2-region.deliver` 가 그 자리다
            "region": ("전국 배달" if str(r[25] or "") == "Y" else rlabel),
            "region_kind": ("deliver" if str(r[25] or "") == "Y" else rkind),
            "photo_url": _first_photo(r[10], root),
            "photo_note": f"사진<br>{NOT_ASKED}",
            "meta": " · ".join(x for x in (
                _ym(r[5]), _km(r[6]),
                " / ".join(y for y in (r[7], r[8]) if y) or None,
                sites.get(r[9], r[9])) if x),
            "pkgs": (), "calc": _calc(r[1], r[13], r[15])})
    return out


def _calc(now, origin, opt_json) -> list:
    """값 셈 — ★ 모르는 자리는 ★ 「미조회」다.  ★ 0 으로 채우지 않는다."""
    got = [{"label": "표시가", "value": _won(now), "mark": "", "cls": ""}]
    try:
        opts = _j.loads(opt_json) if opt_json else []
    except (ValueError, TypeError):
        opts = []
    won = sum(int(o.get("price") or 0) for o in opts
              if isinstance(o, dict)) if isinstance(opts, list) else 0
    got.append({"label": "든 옵션값",
                "value": _won(won) if won else NOT_ASKED,
                "mark": "" if won else "v3-unknown", "cls": ""})
    got.append({"label": "신차가 (옵션 포함)", "value": _won(origin),
                "mark": "" if origin else "v3-unknown", "cls": ""})
    if now and origin:
        gap = float(origin) - float(now)
        got.append({"label": "신차 대비", "value": f"{_won(gap)} 낮다",
                    "mark": "v3-good", "cls": "sum"})
    else:
        got.append({"label": "신차 대비", "value": NOT_ASKED,
                    "mark": "v3-unknown", "cls": "sum"})
    return got


# ── 탭 3 — GV70 후보 (A-14 ~ A-25 · 마스터 확정 09-06) ────────────────────
# ★★★ 마스터 — ★ 탭 3 은 ★ 「가이드가 쓴 글」이 ★ **아니다.**
#   ★ ★ **지금 고르고 계신 차**를 조건으로 추려 내는 자리다.
# ★★ 조건은 ★ `config/web.json` `tab3_candidate` 가 정본이다 — ★ 코드에 안 박는다.
# ★★★ 조건에 안 맞는다고 ★ **화면에서 없애지 않는다** — ★ 뒤로 보낼 뿐이다.
#   ★ 모르는 조건은 ★ 「미조회」다 — ★ O 로도 X 로도 치지 않는다
MARK_OK, MARK_NO, MARK_Q = "O", "X", "미조회"


def _mark(state) -> tuple:
    """참/거짓/모름 → (표시, 글자 갈래)."""
    if state is None:
        return MARK_Q, "q"
    return (MARK_OK, "y") if state else (MARK_NO, "n")


def _tab3_cfg(root: str = ".") -> dict:
    return (load_config(f"{root}/config/web.json") or {}).get(
        "tab3_candidate") or {}


def _warranty_left(month, km) -> bool | None:
    """제조사 보증이 남아 있는가.  ★ 안 받았으면 ★ None(미조회)."""
    if month is None and km is None:
        return None
    return bool(month) or bool(km)


def _insurance_won(row_cost) -> int | None:
    return int(row_cost) if row_cost is not None else None


def view_tab3(conn: sqlite3.Connection, root: str = ".",
              query: dict | None = None) -> dict:
    """★ A-14 ~ A-25 — ★ GV70 후보를 ★ 두 묶음으로 낸다.

    ★ 위  — 조건에 ★ **다 맞는 차** (값 낮은 순)
    ★ 아래 — ★ **하나가 아쉬운 차** (값 낮은 순).  ★ 지우지 않는다
    ★ 등급으로 자르지 않는다 — ★ 자료가 없어 낮은 것이지 ★ 차가 나쁜 것이 아니다.
      ★ ★ 대신 ★ `thin_data`·`thin_why` 로 ★ 까닭을 화면에 낸다
    """
    del query
    cfg = _tab3_cfg(root)
    if not cfg:
        return {"cond": [], "count": {"all": 0, "matched": 0, "near": 0,
                                      "by_site": UNKNOWN},
                "matched": [], "near": [], "head": "후보", "sub": UNKNOWN}
    sites = list(cfg.get("sites") or ())
    marks = ",".join("?" * len(sites)) if sites else "''"
    # ★★★★★ 09-06 — ★ **리스·렌트를 뺀다.**  ★ 표시가가 ★ **차값이 아니다.**
    #   ★ 실측 09-06 — ★ 값 낮은 순 맨 앞 여섯이 ★ 전부 리스·렌트였다
    #     (`38만` · `649만` · `660만` … ★ GV70 이 그 값일 수 없다).
    #   ★ 잣대는 ★ 목록과 ★ **같은 부품**을 쓴다 (`_lease_kinds` · B-8)
    lw, la = _lease_where()
    got = conn.execute(
        "SELECT l.listing_id, l.site, l.source_id, l.price_current_won,"
        "       l.year_month, l.mileage_km, l.color_ext_raw, l.color_int_raw,"
        "       l.trim_grade_name, l.trim_badge, l.photo_list_json,"
        "       l.warranty_body_month, l.warranty_body_km,"
        "       l.delivery_nationwide, l.site_inspection,"
        "       l.dealer_shop, l.dealer_region, l.paired_source_id,"
        "       l.sell_type, l.price_origin_won, s.confirmed_points,"
        "       s.grade, r.accident_my_cost, r.accident_total_cnt,"
        # ★ 09-10 M-3 — ★ 마스터 기준 「★ 골격에 안 갔으면 통과」를 ★ **조건으로 건다**
        "       l.accident_swap_cnt, l.accident_frame_cnt"
        "  FROM core_listing l"
        "  LEFT JOIN result_score s ON s.listing_id = l.listing_id"
        "  LEFT JOIN core_record  r ON r.listing_id = l.listing_id"
        f" WHERE l.target_key = ? AND l.site IN ({marks})"
        "   AND l.status IN ('active','new','relisted')"
        f"   AND {lw}",
        [cfg.get("target"), *sites, *la]).fetchall()

    matched, near = [], []
    by_site: dict = {}
    for row in got:
        card, ok = _tab3_card(row, cfg, root)
        by_site[card["site_label"]] = by_site.get(card["site_label"], 0) + 1
        (matched if ok else near).append(card)
    matched.sort(key=lambda c: c["_won"] or 10 ** 12)
    # ★ 「**하나가** 아쉬운 차」 — ★ 말 그대로 ★ **아쉬운 수가 적은 것부터** 낸다.
    #   ★ 같으면 ★ 값 낮은 순이다 (지시 「아래도 값 낮은 순」)
    near.sort(key=lambda c: (len(c["miss"]), c["_won"] or 10 ** 12))
    near_all = len(near)
    cap = int(cfg.get("near_max") or 30)
    near = near[:cap]
    said = " · ".join(f"{k} {v}" for k, v in
                      sorted(by_site.items(), key=lambda x: -x[1]))
    return {
        "cond": _tab3_cond(cfg),
        "count": {"all": len(got), "matched": len(matched),
                  "near": near_all, "shown": len(near),
                  "by_site": said or UNKNOWN},
        "matched": matched, "near": near,
        "head": _tab3_head(cfg, root),
        "sub": _tab3_sub(cfg),
    }


def _tab3_head(cfg, root) -> str:
    names = load_config(f"{root}/config/targets.json") or {}
    label = (names.get(cfg.get("target")) or {}).get("label") or cfg.get("target")
    return f"{label} 후보"


def _tab3_sub(cfg) -> str:
    return " · ".join(x for x in (
        f"{_won(cfg.get('price_grace_won'))} 이하",
        f"{str(cfg.get('year_from') or '')[:4]}년식 이상",
        f"{int((cfg.get('mileage_max_km') or 0) / 10000)}만km 미만",
        "보증 남음", "멀쩡한 차") if x)


def _tab3_cond(cfg) -> list:
    got = [{"label": str(cfg.get("target") or UNKNOWN), "cls": ""},
           {"label": f"{_won(cfg.get('price_grace_won'))} 이하", "cls": ""},
           {"label": f"{str(cfg.get('year_from') or '')[:4]}년식 ↑", "cls": ""},
           {"label": f"{int((cfg.get('mileage_max_km') or 0) / 10000)}만km 미만",
            "cls": ""}]
    if cfg.get("need_warranty"):
        got.append({"label": "보증 남음", "cls": ""})
    if cfg.get("need_delivery"):
        got.append({"label": "전국 배달", "cls": ""})
    got.append({"label": f"멀쩡 (보험 {_won(cfg.get('insurance_max_won'))} 미만)",
                "cls": "ok"})
    # ★ 마스터 기준을 ★ 조건 줄에도 적는다 — ★ 「단순교환까지」
    got.append({"label": "골격 무사고 (단순교환까지)", "cls": "ok"})
    for c in cfg.get("color_ext") or ():
        got.append({"label": str(c), "cls": ""})
    if cfg.get("need_inspection"):
        got.append({"label": "사이트 진단 필수", "cls": "ok"})
    return got


def _tab3_card(row, cfg: dict, root: str) -> tuple:
    """카드 한 장 ＋ ★ 「다 맞는가」.

    ★ 모르는 조건은 ★ 「미조회」다 — ★ 그것도 ★ **다 맞는 것은 아니다** (뒤로 간다).
      ★ ★ 다만 ★ X 와 달리 ★ 딱지에 ★ 「미조회」로 적는다 (지시 A-24)
    """
    from report.screens.build import site_badge

    (lid, site, sid, won, ym, km, cext, cint, tgrade, tbadge, photos,
     wmon, wkm, deliver, inspect, shop, region, paired, _sell, origin,
     confirmed, _grade, ins_cost, acc_cnt, swap, frame) = row
    sites = (load_config(f"{root}/config/sites.json") or {}).get("labels") or {}
    label = sites.get(site, site)

    grace = cfg.get("price_grace_won")
    want_year = str(cfg.get("year_from") or "")[:7]
    kmax = cfg.get("mileage_max_km")
    colors = tuple(cfg.get("color_ext") or ())
    ins_max = cfg.get("insurance_max_won")

    st_price = None if won is None else (won <= grace)
    st_year = None if not ym else (str(ym)[:7] >= want_year)
    st_km = None if km is None else (km < kmax)
    st_war = _warranty_left(wmon, wkm) if cfg.get("need_warranty") else True
    st_col = None if not cext else any(c in str(cext) for c in colors)
    st_del = ({"Y": True, "N": False}.get(str(deliver or ""))
              if cfg.get("need_delivery") else True)
    st_dx = (bool(inspect) or None) if cfg.get("need_inspection") else True
    # ★ 보험 — ★ 「멀쩡하다」는 ★ 판금·범퍼·휀더를 사고로 안 친다.
    #   ★ 우리가 가진 것은 ★ **금액**이다 — ★ 금액으로 잰다 (지시 「300만 미만이면 본다」)
    st_ins = None if ins_cost is None else (int(ins_cost) < ins_max)
    # ★★ 마스터 기준 — 「★ 단순교환까지.  ★ **골격에 안 갔으면 통과**」.
    #   ★ 성능점검부의 ★ **자리별 등급**이 그것을 안다 (RANK_A·B·C 가 골격이다).
    #   ★ 못 받았으면 ★ 「미조회」다 — ★ 「무사고」로 읽지 않는다
    st_frame = None if frame is None else (frame == 0)

    checks = []
    for name, state, said in (
            ("값", st_price, _won(won)),
            ("연식", st_year, _ym(ym)),
            ("주행", st_km, _km(km)),
            ("제조사 보증", st_war, _warranty(wmon, wkm)),
            ("보험", st_ins,
             _won(ins_cost) if ins_cost is not None else NOT_ASKED),
            ("외장", st_col, cext or NOT_ASKED),
            ("배달", st_del, {"Y": "전국 배달", "N": "없음"}.get(
                str(deliver or ""), NOT_ASKED)),
            ("사이트 진단", st_dx, inspect or NOT_ASKED),
            ("골격", st_frame, _frame_said(swap, frame))):
        mark, cls = _mark(state)
        checks.append({"label": name, "mark": mark, "cls": cls,
                       "said": "" if mark == MARK_Q else said})

    miss = []
    if st_price is False and won is not None:
        miss.append(f"＋{_won(won - grace)}")
    if st_km is False and km is not None:
        miss.append(f"＋{_km(km - kmax)}")
    if st_year is False:
        miss.append(f"{_ym(ym)}")
    if st_col is False:
        miss.append(str(cext))
    if st_dx is None:
        miss.append("진단 미조회")
    if st_del is None:
        miss.append("배달 미조회")
    if st_war is None:
        miss.append("보증 미조회")
    if st_ins is None:
        miss.append("보험 미조회")
    if st_ins is False:
        miss.append(f"보험 {_won(ins_cost)}")
    if st_frame is None:
        miss.append("골격 미조회")
    if st_frame is False:
        miss.append(f"골격 {frame}곳")

    tone, clean = _accident_tone(ins_cost, acc_cnt, cfg)
    ok = (all(x is True for x in (st_price, st_year, st_km, st_war,
                                  st_col, st_del, st_dx))
          and st_ins is not False and st_frame is not False)
    thin = confirmed is not None and confirmed < (cfg.get("thin_points") or 700)
    return ({
        "listing_id": lid, "_won": won, "price": _won(won),
        "verdict": _verdict(ok, tone, miss)[0],
        "verdict_label": _verdict(ok, tone, miss)[1],
        "site_label": label, "site_badge": site_badge(site, None, root),
        "inspection": inspect or NOT_ASKED, "inspection_ok": bool(inspect),
        "miss": miss[:2],
        "meta": " · ".join(x for x in (
            _ym(ym), _km(km),
            " / ".join(y for y in (cext, cint) if y) or None,
            tgrade or tbadge) if x),
        "shop": f"판매 {shop or NOT_ASKED} · {region or NOT_ASKED} · "
                + {"Y": "전국 배달", "N": "배달 없음"}.get(
                    str(deliver or ""), f"배달 {NOT_ASKED}"),
        "photo_url": _first_photo(photos, root),
        "photo_note": _photo_note(site, photos,
                                  _view_str("photo_base_url", root), None)
        or NOT_ASKED,
        "accident_tone": tone, "clean_car": clean,
        "insurance_cost": _won(ins_cost) if ins_cost is not None else NOT_ASKED,
        "thin_data": thin, "thin_why": _thin_why(origin, ins_cost, inspect),
        "encar_url": _source_url_of(site, sid, paired, root),
        "checks": checks, "good": _good_line(won, km, ym, tone),
    }, ok)


def _accident_tone(ins_cost, acc_cnt, cfg) -> tuple:
    """★ A-10 · A-11 — 카드 색 띠.  ★ **미조회는 안 칠한다.**

    ★ 마스터 — 「★ 모르는 것을 ★ 좋게도 나쁘게도 칠하지 않는다」
    """
    if ins_cost is None and acc_cnt is None:
        return "none", False
    cost = int(ins_cost or 0)
    if cost > int(cfg.get("insurance_max_won") or 3000000):
        return "bad", False
    if cost > int(cfg.get("clean_max_won") or 1000000):
        return "mid", False
    return "clean", True


def _verdict(ok: bool, tone: str, miss: list) -> tuple:
    if ok:
        return ("buy", "멀쩡 · 조건 다 맞음") if tone == "clean" \
            else ("hold", "조건 다 맞음")
    if any("미조회" in m for m in miss):
        return "wait", "보류"
    return "hold", (miss[0] if miss else "아쉬움")


def _thin_why(origin, ins_cost, inspect) -> str:
    got = []
    if not origin:
        got.append("신차가 미조회")
    if ins_cost is None:
        got.append("보험 이력 미조회")
    if not inspect:
        got.append("사이트 진단 미조회")
    return " · ".join(got) or UNKNOWN


def _good_line(won, km, ym, tone) -> str:
    """★ A-25 — 아래 묶음에도 ★ **좋은 점**을 한 줄.  ★ 잰 것만 적는다."""
    got = []
    if km is not None and km < 50000:
        got.append(f"주행이 {_km(km)}로 적습니다")
    if ym and str(ym)[:4] >= "2023":
        got.append(f"연식이 {_ym(ym)}로 새것입니다")
    if tone == "clean":
        got.append("사고가 깨끗합니다")
    if won is not None and won < 33000000:
        got.append(f"값이 {_won(won)}로 낮습니다")
    return " · ".join(got[:2]) or "좋은 점을 아직 못 쟀습니다"


def _source_url_of(site, sid, paired, root):
    from report.screens.build import _site_detail_urls, _source_url

    try:
        return _source_url(site, sid, _site_detail_urls(root), paired)
    except (TypeError, ValueError, KeyError):
        return None


# ── 탭 4 — GV70 전용 (지시 r1206 M · 규격 `docs/GV70_TAB4.md`) ────────────
# ★★★ 마스터께서 ★ **이틀에 걸쳐 예순 대 넘게** 걸러 얻은 기준이다.
#   ★ 값은 ★ `config/web.json` `tab4_gv70` · 뜻은 ★ `targets.json` `_탭4_규격` 이 정본.
# ★★ 모르는 것은 ★ 「미조회」다 — ★ 지어내지 않는다 (규격 13장).
#   ★ 특히 ★ **감가율의 분모는 신차출고가**다 — ★ 없으면 비운다 (M-2)
GROUPS = (("값", "value."), ("상태", "state."), ("이력", "history."),
          ("보증", "warranty."), ("취향", "taste."))


def _t4(root: str = ".") -> dict:
    return (load_config(f"{root}/config/web.json") or {}).get("tab4_gv70") or {}


def _dep_pct(now, origin):
    """★ **잔가율** = 판매가 ÷ 신차출고가.  ★ 분모가 없으면 ★ None(미조회).

    ★★★ 09-10 (r1213 M-1) — ★ 규격이 ★ **두 말을 함께** 쓴다:
      ★ 기준 — 「신차출고가 대비 ★ **78% 이하**」 · 「★ 25% 아래는 값이 센 편」
      ★ 셈  — 「감가율 = ★ **(1 − 판매가 ÷ 신차출고가) × 100**」
    ★★ 둘은 ★ 서로 뒤집힌 값이다 — ★ 78% 는 ★ 판매가÷신차가(잔가율)이고
      ★ ★ 셈이 말하는 것은 ★ 100 − 잔가율(감가율)이다.
      ★ ★ ★ 시안이 ★ 3,850만 / 5,210만 = ★ **73.9%** 로 적었으니 ★ 잔가율이다.
    ★ 그래서 ★ **둘 다 낸다** — ★ 거르기는 잔가율로 · 화면에 감가율도 적는다.
      ★ ★ 회차에 여쭀다 (말이 어긋난다)
    """
    if not now or not origin:
        return None
    return round(float(now) * 100 / float(origin), 1)


def _fee(won, pct) -> int:
    return round(float(won or 0) * float(pct) / 100)


def _wear(km, cfg) -> tuple:
    """소모품 예상비 (M-10).  ★ 주행을 모르면 ★ 「미조회」다."""
    if km is None:
        return None, "미조회"
    got, say = 0, []
    if km >= int(cfg.get("tire_from_km") or 45000):
        got += int(cfg.get("tire_won") or 0)
        say.append("타이어")
    if km >= int(cfg.get("brake_from_km") or 50000):
        got += int(cfg.get("brake_won") or 0)
        say.append("브레이크")
    return got, (" · ".join(say) if say else "아직 아닙니다")


def view_gv70(conn: sqlite3.Connection, root: str = ".",
              query: dict | None = None) -> dict:
    """★ M — 추천 탭 4.  ★ 마스터 기준 일곱으로 거른다.

    ★ 리스·렌트 승계는 뺀다 (M-13) — ★ **내 차가 되지 않는다.**
    ★ 렌터카 이력은 ★ **결격이 아니다** — ★ 리본카·K카는 그것을 정리해 판다.
    """
    del query
    cfg = _t4(root)
    if not cfg:
        return {"rule": [], "rows": [], "count": {}, "head": "GV70",
                "sub": UNKNOWN, "note": ""}
    names = load_config(f"{root}/config/targets.json") or {}
    label = str((names.get(cfg["target"]) or {}).get("label") or cfg["target"])
    sites = (load_config(f"{root}/config/sites.json") or {}).get("labels") or {}
    lw, la = _lease_where()

    allc = conn.execute(
        "SELECT COUNT(*) FROM core_listing l WHERE l.target_key = ?",
        (cfg["target"],)).fetchone()[0]
    got = conn.execute(
        "SELECT l.listing_id, l.site, l.source_id, l.price_current_won,"
        # ★ 09-10 M-1 — ★ 분모는 ★ **출고가**(옵션 포함)다.
        #   ★ 없으면 ★ 등급기준가로 **대신하지 않는다** — ★ 「미조회」로 비운다
        "       l.price_origin_total_won, l.year_month, l.mileage_km,"
        # ★★★★★ 09-10 (r1212 급한것 1) — ★ 「상세를 받았나」는 ★ **따로** 읽는다.
        #   ★★ 내가 낸 잘못 — ★ 위 칸을 `price_origin_won` → `price_origin_total_won`
        #     ★ ★ 으로 바꾸면서 ★ **그 칸으로 「상세」를 세던 줄을 안 고쳤다**.
        #   ★ ★ 그래서 ★ 「상세 62대」가 ★ 하루 만에 ★ 「5대」로 보였다 —
        #     ★ ★ ★ **상태가 되돌아간 것이 아니라** ★ 자가 딴것을 세고 있었다.
        #   ★ 실측 09-10 — ★ GV70_25T 1,554대 중
        #     ★ 등급기준가 79 · 신차출고가 5 · ★ **`detail_status='ok'` 219**.
        #   ★ 화면이 「상세를 받은 것」이라 적으므로 ★ **그것을 센다**
        "       l.trim_grade_name, l.trim_badge, l.site_inspection,"
        "       l.options_choice_json, l.warranty_body_month,"
        "       l.warranty_body_km, l.paired_source_id, s.grade,"
        "       r.accident_my_cnt, r.accident_my_cost,"
        "       r.accident_other_cnt, r.accident_other_cost,"
        # ★ 09-10 M-3 — ★ 교환 · 판금 · 골격을 ★ 갈라 읽는다 ＋ 부위명
        "       l.accident_swap_cnt, l.accident_weld_cnt,"
        "       l.accident_frame_cnt, l.accident_parts_json,"
        "       s.group_value, s.group_car, s.group_warranty, s.group_taste,"
        "       s.grade_earned, s.grade_base,"
        # ★ 09-10 M-5 — ★ 하체 낱말 (정비이력이 없어 ★ 판매자 글에서 잡은 것)
        "       l.undercarriage_json, l.undercarriage_src,"
        # ★ 맨 뒤다 — ★ `r[-1]` 로 읽는다 (자리를 세지 않게)
        "       l.detail_status"
        "  FROM core_listing l"
        "  LEFT JOIN result_score s ON s.listing_id = l.listing_id"
        "  LEFT JOIN core_record  r ON r.listing_id = l.listing_id"
        " WHERE l.target_key = ? AND l.status IN ('active','new','relisted')"
        f"   AND {lw}"
        "   AND l.year_month >= ? AND l.mileage_km <= ?",
        (cfg["target"], *la, cfg["year_from"],
         cfg["mileage_max_km"])).fetchall()
    passed = len(got)
    # ★ 「상세를 받았다」 = ★ `detail_status` 가 ok 인 것 (화면 글자 그대로)
    detailed = sum(1 for r in got if str(r[-1] or "") == "ok")
    rows = [_gv70_card(r, cfg, sites, root, conn)
            for r in got if str(r[-1] or "") == "ok"]
    # ★★★★★ 09-10 (r1212) — ★ 감가율을 못 재는 차를 ★ **지우지 않는다**.
    #   ★ 지시 r1213 — 「분모가 없으면 ★ 「신차가 미조회 — 감가율을 계산하지 않음」
    #     ★ ★ 으로 **비운다**」.  ★ 「비운다」는 ★ **차를 지운다**가 아니다.
    #   ★ 잣대를 넘은 것 · 못 잰 것도 ★ 뒤에 세운다 — ★ 마스터가 보고 고르신다
    keep = [c for c in rows if c["_ok"]]
    rest = [c for c in rows if not c["_ok"]]
    keep.sort(key=lambda c: c["_total"] or 10 ** 12)
    rest.sort(key=lambda c: c["_total"] or 10 ** 12)
    picked = len(keep)
    keep = (keep + rest)[:int(cfg.get("shown") or 20)]
    _mark_best(keep)
    return {
        "head": label,
        "sub": "마스터 기준으로 걸렀습니다 — "
               f"감가 {cfg['depreciation_max_pct']}% 이하 · "
               f"{cfg['year_from'][:4]}년 {int(cfg['year_from'][5:7])}월↑ · "
               f"{int(cfg['mileage_max_km'] / 10000)}만km 이하 · 골격 무사고",
        "rule": [
            {"label": f"감가 {cfg['depreciation_max_pct']}% 이하", "key": "key"},
            {"label": f"{cfg['year_from'][:4]}년 "
                      f"{int(cfg['year_from'][5:7])}월 ↑", "key": "key"},
            {"label": f"{int(cfg['mileage_max_km'] / 10000)}만km 이하",
             "key": "key"},
            {"label": "골격 무사고", "key": "key"},
            {"label": "단순교환까지 봄", "key": ""},
            {"label": "깡통도 후보", "key": ""},
            {"label": f"진단 없어도 감가 {cfg['depreciation_no_dx_pct']}%↓면 후보",
             "key": ""},
            {"label": "리스·렌트 승계 제외", "key": ""},
        ],
        "note": "렌터카 이력은 결격이 아닙니다. "
                "리본카·K카는 렌터카를 정리해 팔아 값이 쌉니다.",
        "count": {"all": allc, "passed": passed, "detailed": detailed,
                  "missing": passed - detailed, "shown": len(keep),
                  # ★ 「다 맞는 차」가 몇인지 ★ 따로 센다 — ★ shown 과 다르다
                  "picked": picked},
        "rows": keep,
    }


def _gv70_card(r, cfg: dict, sites: dict, root: str, conn=None) -> dict:
    (lid, site, sid, won, origin, ym, km, tgrade, tbadge, dx, optj,
     wmon, wkm, paired, grade, my_cnt, my_cost, ot_cnt, ot_cost,
     swap, weld, frame, parts_json,
     g_value, g_car, g_warranty, g_taste, earned, base,
     under_json, under_src, _detail) = r
    pct = _dep_pct(won, origin)
    cap = float(cfg["depreciation_max_pct"])
    nodx = float(cfg["depreciation_no_dx_pct"])
    # ★ 진단이 없으면 ★ 확인 비용이 따로 든다 — ★ 감가가 더 낮아야 후보다
    ok = pct is not None and pct <= (cap if dx else nodx)
    # ★ 마스터 기준 — 「★ 단순교환까지.  ★ **골격에 안 갔으면 통과**」.
    #   ★ 골격이 ★ **상한 것**은 후보가 아니다.
    #   ★★ 미조회는 ★ 자르지 않는다 — ★ 「★ 못 찾았다」와 「★ 없다」는 다르다.
    #     ★ ★ 대신 ★ 화면에 ★ 「골격 미조회」로 적고 ★ 「다 맞는 차」로 안 친다
    if frame is not None and frame > 0:
        ok = False
    # ★ 교환이 ★ **4곳 이상**이면 ★ 사고 1,000만 이상으로 본다
    many = int(_panel_book(root).get("교환_많으면", {}).get("갯수", 4))
    big = swap is not None and swap >= many
    lo, hi = float(cfg["accident_signal_lo_pct"]), float(
        cfg["accident_signal_hi_pct"])

    fee = _fee(won, cfg["fee_pct"])
    wear, wear_say = _wear(km, cfg)
    total = (won or 0) + fee + (wear or 0)

    def cell(v, cls=""):
        return {"v": v, "cls": cls}

    dep_cls = "ok" if (pct is not None and pct <= cap) else "no"
    if pct is not None and lo <= pct <= hi:
        dep_cls = "warn"          # ★ 65~68% 는 ★ **사고 신호**다
    four = [
        {"label": "값 / 신차출고가 / 잔가율 (감가율)",
         "cells": [cell(_won(won)),
                   cell(_won(origin) if origin
                        else "신차가 미조회 — 감가율을 계산하지 않음",
                        "" if origin else "no"),
                   cell(f"{pct}% (감가 {round(100 - pct, 1)}%)"
                        if pct is not None else NOT_ASKED, dep_cls)]},
        {"label": "주행 / 최초등록",
         "cells": [cell(_km(km), "ok" if km is not None else "no"),
                   cell(_ym(ym), "ok" if ym else "no")]},
        # ★ M-3 — ★ **교환 · 판금 · 골격**을 갈라 낸다.  ★ 부위명도 낸다
        {"label": "사고",
         "cells": _accident_cells(swap, weld, frame, parts_json,
                                  my_cnt, my_cost, ot_cnt, ot_cost, big)},
        {"label": "진단 / 보증",
         "cells": [cell(dx or NOT_ASKED, "ok" if dx else "no"),
                   cell(_warranty(wmon, wkm))]},
    ]
    return {
        "listing_id": lid, "price": _won(won),
        "grade": grade or "판정 중",
        "name": tgrade or tbadge or UNKNOWN,
        "site": sites.get(site, site),
        "dx": dx or NOT_ASKED, "dx_ok": bool(dx),
        "pick": bool(ok and dx),
        "url": _source_url_of(site, sid, paired, root),
        "four": four,
        "pkgs": _pkgs(optj, conn, site),
        "pkg_note": _opt_label(optj),
        "total": [
            {"label": "차값", "v": _won(won), "cls": ""},
            {"label": f"이전등록비 · 매도비 ({cfg['fee_pct']}%)",
             "v": _won(fee), "cls": ""},
            {"label": f"소모품 — {wear_say}",
             "v": _won(wear) if wear else ("0" if wear == 0 else NOT_ASKED),
             "cls": ""},
            {"label": "총비용", "v": _won(total), "cls": "sum"},
        ],
        "bars": _bars(g_value, g_car, g_warranty, g_taste, earned, base),
        "say": _gv70_say(pct, lo, hi, dx, wmon, wkm, swap, frame, big, many,
                         under_json, under_src),
        "_ok": ok, "_total": total,
    }


def _pkgs(optj, conn=None, site: str = "encar") -> list:
    """★ M-7 — 옵션을 ★ **패키지 이름 ＋ 정가**로.

    ★★ 실측 09-08 — ★ 엔카는 ★ **숫자 코드**만 준다 (`["1050","1046",…]`).
      ★ 그것을 그대로 내면 ★ 화면에 ★ 「1050 미조회」가 뜬다 —
      ★ ★ **사람이 못 읽는 말**이다.
    ★ 이름은 ★ `dict_option_code` 가 안다 — ★ 있으면 붙인다.
    ★★ 정가는 ★ **우리에게 없다** — ★ `catalog` 창구가 그것을 준다 (지금 0.8%).
      ★ ★ 그러니 ★ 「정가 미조회」라 적는다.  ★ 지어내지 않는다 (금지 12)
    """
    try:
        got = _j.loads(optj) if optj else []
    except (ValueError, TypeError):
        return []
    if not isinstance(got, list) or not got:
        return []
    name: dict = {}
    if conn is not None:
        try:
            name = {str(r[0]): str(r[1]) for r in conn.execute(
                "SELECT code, display FROM dict_option_code WHERE site = ?",
                (site,))}
        except sqlite3.Error:
            name = {}
    out = []
    for one in got:
        if isinstance(one, dict):
            out.append({"label": str(one.get("name") or one.get("label")
                                     or UNKNOWN),
                        "won": _won(one.get("price"))})
        else:
            code = str(one)
            said = name.get(code, "")
            # ★ 사전에 든 것이 ★ **코드 그 자체**이면 ★ 이름을 모르는 것이다 —
            #   ★ 「1057」을 이름인 척 내지 않는다 (금지 12)
            out.append({"label": (said if said and said != code
                                  else f"코드 {code} · 이름 미조회"),
                        "won": "정가 미조회"})
    return out[:6]


def _bars(g_value, g_car, g_warranty, g_taste, earned, base) -> list:
    """★ M-12 — 갈래별 막대 다섯 ＋ 총점.  ★ 배점은 `result_score` 가 준다."""
    got = []
    for label, v in (("값", g_value), ("상태", g_car),
                     ("보증", g_warranty), ("취향", g_taste)):
        if v is None:
            got.append({"label": label, "pct": 0, "said": NOT_ASKED,
                        "best": False, "hi": ""})
        else:
            got.append({"label": label, "pct": 0, "said": f"{v:g}",
                        "best": False, "hi": "", "_v": float(v)})
    if earned and base:
        got.append({"label": "총점", "pct": round(earned * 100 / base),
                    "said": f"{earned:g}/{base:g}", "best": False, "hi": "hi"})
    else:
        got.append({"label": "총점", "pct": 0, "said": NOT_ASKED,
                    "best": False, "hi": ""})
    return got


def _mark_best(rows: list) -> None:
    """★ 갈래별 1등에 ★ 별을 붙인다 (M-12).  ★ 잰 것이 없으면 안 붙인다."""
    if not rows:
        return
    for i in range(len(rows[0]["bars"]) - 1):
        vals = [(c["bars"][i].get("_v"), c) for c in rows
                if c["bars"][i].get("_v") is not None]
        if not vals:
            continue
        top = max(v for v, _c in vals)
        for v, c in vals:
            c["bars"][i]["pct"] = round(v * 100 / top) if top else 0
            if v == top:
                c["bars"][i]["best"] = True
                c["bars"][i]["hi"] = "hi"
                c["bars"][i]["said"] += " ★"


def _gv70_say(pct, lo, hi, dx, wmon, wkm,
              swap=None, frame=None, big=False, many=4,
              under_json=None, under_src=None) -> str:
    """★ 한 줄 — ★ **잰 것만** 적는다.  ★ 지어내지 않는다."""
    got = []
    # ★★ M-5 — ★ 하체 낱말.  ★ **어디서 잡았는지**를 함께 적는다 —
    #   ★ 정비이력이 아니라 ★ 판매자 글이면 ★ 그렇게 말한다 (금지 6)
    said = _under_say(under_json, under_src)
    if said:
        got.append(said)
    # ★ M-3 — ★ 마스터 기준을 ★ **그 줄에서** 말한다
    if frame is None:
        got.append("골격 미조회 — 「골격에 안 갔으면 통과」를 아직 못 걸었습니다")
    elif frame > 0:
        got.append(f"골격이 {frame}곳 상했습니다 — 마스터 기준에서 벗어납니다")
    if big:
        got.append(f"교환이 {swap}곳입니다 — {many}곳 이상이면 사고 1,000만 이상으로 봅니다")
    if pct is not None and lo <= pct <= hi:
        got.append(f"감가가 {pct}% 입니다 — 이 자리는 사고 신호일 수 있습니다")
    if not dx:
        got.append("사이트 진단이 없습니다 — 확인 비용이 따로 듭니다")
    if wmon or wkm:
        got.append(f"제조사 보증 {_warranty(wmon, wkm)}")
    return " · ".join(got) or "더 볼 것을 아직 못 쟀습니다"


def _accident_cells(swap, weld, frame, parts_json,
                    my_cnt, my_cost, ot_cnt, ot_cost, big=False) -> list:
    """★ M-3 — 교환 · 판금 · 골격 ＋ 부위명 ＋ 보험 금액.

    ★ 점검부를 못 받았으면 ★ 「미조회」다 — ★ 0 으로 두지 않는다 (금지 12).
    ★ 「골격 무사고」는 ★ **확인해서 0 일 때**만 적는다
    """
    def cell(v, cls=""):
        return {"v": v, "cls": cls}

    try:
        parts = _j.loads(parts_json) if parts_json else []
    except (ValueError, TypeError):
        parts = []
    if not isinstance(parts, list):
        parts = []
    parts = [p for p in parts if isinstance(p, dict)]
    got = []
    if swap is None:
        got.append(cell(f"교환·판금·골격 {NOT_ASKED}", "no"))
    else:
        # ★ 부위명을 낸다 — ★ 「판금 1곳」이 아니라 ★ 「판금 1곳 (뒷휀더)」
        def where(kind):
            said = [str(p.get("part") or UNKNOWN)
                    for p in parts if p.get("kind") == kind]
            return f" ({' · '.join(said[:3])})" if said else ""

        # ★ 교환이 4곳 이상이면 ★ **사고 1,000만 이상**으로 본다 — ★ 노랗게
        got.append(cell(f"교환 {swap}곳{where('교환')}",
                        "warn" if big else ("ok" if not swap else "")))
        got.append(cell(f"판금 {weld}곳{where('판금')}",
                        "ok" if not weld else ""))
        if frame:
            said = [str(p.get("part") or UNKNOWN)
                    for p in parts if p.get("frame")]
            got.append(cell(f"★ 골격 {frame}곳 ({' · '.join(said[:3])})", "no"))
        else:
            got.append(cell("골격 무사고", "ok"))
    # ★ 미조회를 ★ **초록(무사고)으로 칠하지 않는다** — ★ 「없음」을 값으로
    #   삼지 않는다 (금지 12).  ★ 0 은 ★ **확인해서 0** 일 때만이다
    got.append(cell(f"내차 {my_cnt}회 / {_won(my_cost)}"
                    if my_cnt is not None else f"내차 {NOT_ASKED}",
                    "ok" if my_cnt == 0 else ("no" if my_cnt is None else "")))
    got.append(cell(f"상대차 {ot_cnt}회 / {_won(ot_cost)}"
                    if ot_cnt is not None else f"상대차 {NOT_ASKED}",
                    "ok" if ot_cnt == 0 else ("no" if ot_cnt is None else "")))
    return got


_PANEL_BOOK: dict = {}


def _panel_book(root: str = ".") -> dict:
    """★ 자리·상태 사전 — ★ 값을 코드에 안 박는다 (S14)."""
    if not _PANEL_BOOK:
        got = load_config(f"{root}/config/dictionaries/panel_rank.json") or {}
        _PANEL_BOOK.update(got or {"교환_많으면": {"갯수": 4}})
    return _PANEL_BOOK


def _frame_said(swap, frame) -> str:
    """★ 골격 딱지에 적을 말 — ★ 잰 것만."""
    if frame is None:
        return NOT_ASKED
    if frame:
        return f"골격 {frame}곳"
    return f"교환 {swap}곳 · 골격 없음" if swap else "무사고"


def _under_say(under_json, under_src) -> str:
    """하체 낱말 한 마디.  ★ 없으면 ★ 빈 글 — ★ 「없다」고 말하지 않는다.

    ★★ 「미조회」라 안 적는다 — ★ **거의 모든 차가 미조회**라
      ★ ★ 그 말을 다 붙이면 ★ 줄이 그 말로만 찬다.  ★ 잡힌 것만 말한다
    """
    try:
        got = _j.loads(under_json) if under_json else []
    except (ValueError, TypeError):
        return ""
    if not isinstance(got, list) or not got:
        return ""
    where = str(under_src or UNKNOWN)
    return (f"하체를 건드린 자국이 있습니다 — {' · '.join(str(x) for x in got)}"
            f" ({where}에서 봤습니다)")
