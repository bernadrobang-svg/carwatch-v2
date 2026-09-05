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

UNKNOWN = "모름"
NOT_ASKED = "미조회"

# ★ 규격 ⑥ — ★ 평가 한 마디.  ★ 우리가 짓지 않는다 — ★ 가이드가 쓴 값을 읽는다
VERDICT_LABEL = {"buy": "구매 적절", "hold": "보류",
                 "wait": "대기", "risk": "위험"}


def tabs_config(root: str = ".") -> list:
    """★ A-1 — 탭 목록.  ★ 자료가 정본이다."""
    got = (load_config(f"{root}/config/web.json") or {}).get("recommend_tabs")
    return list(got or [])


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

    group("지역", "rg", [(r["key"], r["label"])
                         for r in cfg.get("recommend_regions") or ()])
    live = [r[0] for r in conn.execute(
        "SELECT target_key, COUNT(*) FROM core_listing"
        " WHERE target_key IS NOT NULL AND status IN"
        " ('active','new','relisted') GROUP BY 1 ORDER BY 2 DESC")]
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
            f" {taste_sql} AS _taste, {safe_sql} AS _safe,"
            f" {grade_rank} AS _grade_rank")
    got = conn.execute(
        "SELECT " + cols + body + " ORDER BY "
        + ORDER_SQL.get(order, ORDER_SQL["value"])
        + ", l.listing_id LIMIT ? OFFSET ?",
        [*SAFE_AXES, *args, size, (page["page"] - 1) * size]).fetchall()

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
            "region": rlabel, "region_kind": rkind,
            "over_budget": False,
            "depreciation": _dep(r[3], r[18]),
            "dep_ok": _dep_ok(r[3], r[18]),
            "soh": f"{r[17]}%" if r[17] is not None else None,
            "accident": None,
            "km_vs_avg": _km(r[5]),
            "trim": r[9] or r[8] or UNKNOWN,
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


def view_tab3(conn: sqlite3.Connection, account_id: int,
              root: str = ".") -> dict:
    """★ A-3 — 분석.  ★ **내가 맡긴 차만** 있다 (관심과 따로다).

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
    keys = tab_targets("4", root)
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
            "region": rlabel, "region_kind": rkind,
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
