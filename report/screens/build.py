# -*- coding: utf-8 -*-
"""화면 데이터 생성.

지시서   10장 STEP 93~107
근거     모든 화면은 result_* 와 core_* 만 읽는다 (STEP 105)
필수     모든 화면 함수는 Account 를 첫 인자로 받는다 (STEP 105 · 13장 STEP 126)
         개인화는 watch_* 조회에 account_id 를 거는 것으로 끝난다
금지     화면이 raw_response 를 직접 파싱 (V6-03)
         판정 결과가 계정별로 달라지는 것 — 같은 차는 누가 봐도 같은 등급이다
         NOT_RATED 에 순위를 매기는 것 (V6-04)
         gone 을 팔린 것으로 표기하는 것 — 목록에서 사라진 것이다 (V6-06)
         버전이 다른 결과를 한 목록에 섞어 정렬하는 것 (9장 STEP 91)
"""
from __future__ import annotations

import json
import os
import sqlite3
from urllib.parse import urlencode

from dataclasses import replace

from report.finance import build_finance
from report.render import render_listing, render_run
from report.screens.views import (
    MIN_SAMPLE,
    Bucket,
    ExcludedGroup,
    PendingValue,
    StepRow,
    TodayChange,
    TONE_BAD, TONE_GOOD, TONE_MUTED, TONE_UNKNOWN,
    AttentionItem, AxisChip, ChangeRow, CompareView, DashboardView, DealerRow,
    ListingFilter, ListingRow, MarketRow, MarketView, NotReadyView,
    WatchRow,
    TargetStat, ViewerState,
)
from report.views import AxisView, ReportMeta, VersionStamp
from contracts import ROLE_ADMIN, ROLE_USER, Account, require_role

NOT_RATED = "NOT_RATED"
# 분위수는 표시 파라미터다.  config 가 정본이며 여기 값은 호출측 미지정 시 대체다
MARKET_QUANTILES = (0.25, 0.50, 0.75)
GONE = "gone"

# 목록에 띄우는 축 요약 (STEP 97).  Component 이름을 쓴다
# 목록에 좁은 칸으로 세우는 축.  ★ v1 원본이 정본이다 (STEP 149o · 개정 277)
# v1 22열 — HUD · 보증 · 사고 · 보험 · 렌트 (외장·내장은 원값 열로 따로 낸다).
# HDA · 선루프는 시안이 더한 것이라 함께 둔다 — 넓으면 더 보여 준다 (개정 278).
# ★ 한 칸에 몰아넣으면 「이 차만 HUD 가 없다」가 세로로 안 보인다
CHIP_AXES = ("spec.hud", "spec.hda", "spec.sunroof", "warranty.general",
             "history.damage", "history.insurance", "history.rental")


def axis_heads(root: str = ".") -> list[dict]:
    """목록 축 열의 머리말.  ★ 문구를 화면에 박지 않는다 (STEP 91 · V6-02)."""
    al = _labels(root)["AXIS_LABELS"]
    return [{"axis": a, "label": al.get(a, a)} for a in CHIP_AXES]

RANK_ORDER = ("S", "A", "B", "C", "D", "E")


def _labels(root: str = ".") -> dict:
    with open(f"{root}/config/labels.json", encoding="utf-8") as f:
        return json.load(f)


def viewer_state(account: Account) -> ViewerState:
    """역할별 표시 분기.  ★ 화면 숨김은 권한이 아니다 — 서버가 막는다 (STEP 126)."""
    return ViewerState(
        role=account.role,
        display_name=account.display_name,
        can_watch=account.role in (ROLE_USER, ROLE_ADMIN),
        can_admin=account.role == ROLE_ADMIN,
        must_change_secret=account.must_change_secret)


def chip(axis: str, value: int | None, excluded: bool, labels: dict,
         base: str = "/listings") -> AxisChip:
    """전 화면이 같은 문구를 쓴다.  화면마다 다르게 쓰지 않는다 (V6-02)."""
    vl = labels["VALUE_LABELS"]
    al = labels["AXIS_LABELS"]
    if value is None and excluded:
        label, tone, bucket = vl["unknown"], TONE_UNKNOWN, "unknown"
    elif value == -1 and excluded:
        label, tone, bucket = vl["na"], TONE_MUTED, "na"
    elif value is None:
        label, tone, bucket = vl["unknown"], TONE_UNKNOWN, "unknown"
    elif value > 0:
        label, tone, bucket = vl["1"], TONE_GOOD, "1"
    else:
        label, tone, bucket = vl["0"], TONE_BAD, "0"
    url = f"{base}?{urlencode({'axis': axis, 'bucket': bucket})}"
    # ★ 「없음」과 「모름」을 같은 기호로 내면 v1 사고가 되풀이된다.
    #   O(있음) · ·(없음) · ?(확인 못 함) 셋으로 가른다 (STEP 149f · A-4)
    mark = labels.get("VALUE_MARKS", {}).get(bucket, "?")
    # ★ 9장 대조표는 value=1/0 을 전제하는데 result_axis.value 는 점수(0~20)다.
    #   위험 축(사고·렌트·보험)은 「점수를 받았다 = 그 일이 없다」라
    #   대조표를 그대로 쓰면 뜻이 뒤집힌다 —
    #   실측 08-16: S등급 매물에 「사고 있음」이 떴다.
    #   축별 문구가 있으면 그것을 쓴다 (config/labels.json)
    over = labels.get("AXIS_VALUE_LABELS", {}).get(axis, {}).get(bucket)
    text = over or f"{al.get(axis, axis)} {label}"
    return AxisChip(axis, text, tone, url, head=al.get(axis, axis), mark=mark)


def _stamp(calc_version: str, dict_version: str | None) -> VersionStamp:
    return VersionStamp(None, dict_version, calc_version, None, None, None)


def _bulk_axes(conn, lids: list, calc_version: str) -> dict:
    """축 값을 한 번에 읽는다 (F-3 · V11-34).

    ★ 행마다 5쿼리를 돌면 200행에 1,000쿼리다.  IN 절로 한 번에 받는다
    """
    if not lids:
        return {}
    marks = ",".join("?" * len(lids))
    out: dict = {}
    for lid, axis, value, excluded in conn.execute(
        f"SELECT listing_id, axis, value, excluded FROM result_axis "
        f"WHERE calc_version = ? AND listing_id IN ({marks})",
        (calc_version, *lids)
    ):
        out.setdefault(lid, {})[axis] = (value, bool(excluded))
    return out


def _bulk_changes(conn, lids: list) -> dict:
    """가격 변동 건수와 첫 게시가 (v1 「변동」 열 · 개정 277).

    ★ 「몇 번 바뀌었나」만으로는 오른 건지 내린 건지 모른다.
      가장 오래된 변경의 old_value 가 첫 게시가다
    """
    if not lids:
        return {}
    marks = ",".join("?" * len(lids))
    out: dict = {}
    for lid, n, first_won in conn.execute(
        f"SELECT listing_id, COUNT(*),"
        f" (SELECT old_value FROM core_listing_change c2"
        f"  WHERE c2.listing_id = c1.listing_id AND c2.change_kind='price'"
        f"  ORDER BY c2.changed_at ASC LIMIT 1)"
        f" FROM core_listing_change c1 "
        f"WHERE change_kind='price' AND listing_id IN ({marks}) "
        f"GROUP BY listing_id", tuple(lids)
    ):
        try:
            first = int(float(first_won)) if first_won is not None else None
        except (TypeError, ValueError):
            first = None            # 숫자가 아니면 없는 것으로 둔다 — 지어내지 않는다
        out[lid] = (n, first)
    return out


def _total_points() -> float:
    """만점.  ★ 분모가 이보다 짧으면 색으로 가른다 (STEP 149f · A-2)."""
    import json as _j
    import os as _o

    here = _o.path.dirname(_o.path.dirname(_o.path.dirname(
        _o.path.abspath(__file__))))
    with open(_o.path.join(here, "config", "scoring.json"),
              encoding="utf-8") as f:
        return float(_j.load(f)["total_points"])


def photo_url(photos_json: str | None, base: str) -> str | None:
    """대표 사진 주소 (개정 274).

    원문 Photos 중 ordering 이 가장 앞인 것 하나다.
    ★ 우리가 내려받지 않는다 — 저작권은 엔카에 있고, 링크는 참조다.
    ★ 원문이 깨져 있어도 화면을 무너뜨리지 않는다.  못 고르면 None 이다 (V11-57)
    """
    if not photos_json:
        return None
    try:
        photos = json.loads(photos_json)
    except (ValueError, TypeError):
        return None
    if not isinstance(photos, list):
        return None
    best, best_ord = None, None
    for p in photos:
        if not isinstance(p, dict):
            continue
        loc = p.get("location")
        if not loc:
            continue
        try:
            o = float(p.get("ordering"))
        except (TypeError, ValueError):
            o = float("inf")       # 순서를 모르면 맨 뒤로 — 있는 것을 버리진 않는다
        if best_ord is None or o < best_ord:
            best, best_ord = loc, o
    return f"{base}{best}" if best else None


def market_price(origin_won, year_month, as_of, target_key, dep: dict):
    """기대가 = 신차가 × 감가계수(경과년) × 차종 보정계수 (7장 STEP 70).

    ★ 판정과 같은 함수를 쓴다 — 화면이 식을 새로 쓰면 숫자가 갈린다.
      계수가 범위 밖인 차종은 판정에서도 안 쓰므로 여기서도 안 쓴다
    """
    from analyze.axis._util import months_between
    from analyze.axis.price import coefficient_sane, expected_price

    coef = (dep.get("coefficient") or {}).get(target_key)
    if not coefficient_sane(coef, dep.get("coefficient_sane_range")):
        return None
    age = months_between(year_month, as_of)
    return expected_price(origin_won, age, dep.get("curve"), coef,
                          dep.get("curve_beyond"))


def _days_between(a: str | None, b: str | None) -> int | None:
    """며칠.  ★ 시각을 직접 읽지 않는다 — 둘 다 저장된 값이다."""
    from datetime import date

    if not a or not b:
        return None
    try:
        # ★ 판정값이 아니라 ISO 문자열의 자릿수다 — 'YYYY-MM-DD' 는 10자
        x = date.fromisoformat(str(a)[:10])
        y = date.fromisoformat(str(b)[:10])
    except ValueError:
        return None
    return (y - x).days


def _ceil_to(value, unit: int):
    """구간 상한.  ★ 「이 값 이하」로 걸 때 자기 자신은 반드시 들어와야 한다."""
    if value is None or unit <= 0:
        return None
    return -(-int(value) // unit) * unit


def _row(conn, rec, labels, fin_cfg, rank, calc_version: str,
         axes: dict | None = None, changes_by: dict | None = None,
         photo_base: str = "", encar_tpl: str = "",
         km_unit: int = 0, monthly_unit: int = 0,
         dep_cfg: dict | None = None) -> ListingRow:
    """★ calc_version 을 인자로 받는다.  함수 속성은 전역 상태다 (F-2).

    워커를 늘리면 즉시 섞인다 — 증상이 재현되지 않는 부류다
    """
    (lid, tk, trim, ym, km, ce, ci, price, grade, earned, denom,
     dealer, dstatus, first_seen, last_seen, dv, photos, sid,
     origin_won, calc_at, absolute_fail, trust, quadrant, enough) = rec
    got = (axes or {}).get(lid, {})
    chips = []
    for axis in CHIP_AXES:
        if axis in got:
            chips.append(chip(axis, got[axis][0], got[axis][1], labels))
        else:
            chips.append(chip(axis, None, True, labels))
    fin = build_finance(price, fin_cfg, tk)
    changes, first_won = (changes_by or {}).get(lid, (0, None))
    # ★ 시세차 — 가격 축이 excluded 면 내지 않는다.  기대가를 못 구한 것이다
    exp = None
    if dep_cfg is not None and not (got.get("price") or (None, True))[1]:
        exp = market_price(origin_won, ym, calc_at, tk, dep_cfg)
    gap = (price - exp) if (exp and price is not None) else None
    # 경과 — 처음 본 날부터 며칠.  ★ 게시일이 아니라 우리가 처음 본 날이다
    dom = _days_between(first_seen, calc_at)
    tags = []
    if absolute_fail:
        tags.append(absolute_fail)
    return ListingRow(
        listing_id=lid, grade=grade or NOT_RATED,
        # ★ NOT_RATED 에 순위를 매기지 않는다.  비교 대상이 아니다
        rank=None if (grade or NOT_RATED) == NOT_RATED else rank,
        # ★ 비율이 크게 · 원점수/분모가 작게 (STEP 149f · A-1).
        #   분모가 다른 매물을 눈으로 갈라야 한다
        earned=earned, denominator=denom,
        ratio_pct=(round(earned / denom * 100, 1)
                   if earned is not None and denom else None),
        # 분모가 만점보다 짧으면 색으로 가른다 (A-2)
        denom_short=bool(denom and denom < _total_points()),
        target_label=tk or "", trim=trim, year_month=ym, mileage_km=km,
        color_ext=ce, color_int=ci, axis_chips=chips, price_won=price,
        total_cost_won=(price + fin.acquisition_cost_won) if fin else None,
        loan_principal_won=fin.loan_principal_won if fin else None,
        monthly_won=fin.monthly_payment_won if fin else None,
        price_gap_pct=(round(gap / exp * 100, 1) if (gap is not None and exp)
                       else None),
        price_change_cnt=changes, days_on_market=dom,
        dealer_shop=dealer, dealer_honesty=None, note=None,
        versions=_stamp(calc_version, dv),
        expected_price_won=int(exp) if exp else None,
        price_gap_won=int(gap) if gap is not None else None,
        price_change_won=((price - first_won)
                          if (first_won is not None and price is not None)
                          else None),
        # ★ 표본이 모자란 딜러는 점수를 내지 않는다.  0 으로 내면 나쁜 딜러가 된다
        dealer_trust=trust if enough else None,
        dealer_quadrant=quadrant if enough else None,
        note_tags=tuple(tags),
        photo_url=photo_url(photos, photo_base),
        source_id=sid,
        # ★ source_id 가 없으면 링크를 만들지 않는다.  깨진 주소를 내지 않는다
        encar_url=(encar_tpl.format(source_id=sid)
                   if sid and encar_tpl else None),
        # ★ 'YYYY-MM' 의 앞 4자가 연식이다 — 판정값이 아니다
        year=(ym or "")[:4] or None,
        km_bucket=_ceil_to(km, km_unit),
        monthly_bucket_won=_ceil_to(
            fin.monthly_payment_won if fin else None, monthly_unit),
        # ★ gone 은 목록에서 사라진 것이다.  팔렸다고 단정하지 않는다
        status_label=labels["STATUS_LABELS"].get(dstatus) if dstatus else None)



def _view_cfg(key: str, root: str = ".") -> int:
    """화면 표시 정책.  ★ 코드에 박지 않는다 (config/web.json)."""
    with open(os.path.join(root, "config", "web.json"), encoding="utf-8") as f:
        return int(json.load(f)[key])


GRADE_ORDER = ("S", "A", "B", "C", "D", "E", "NOT_RATED")
# 가격 분포 칸 수 · 오늘 변동 줄 수.  ★ 표시 정책이라 코드에 박지 않는다
PRICE_BINS = _view_cfg("price_bins")
TODAY_ROWS = _view_cfg("today_rows")
MS_PER_SEC = 1000.0


# 정렬 1단.  ★ 뒤 3단은 어느 축을 골라도 그대로 붙는다 (STEP 106a · E-3)
ORDER_SQL = {
    # ★ earned/denominator 다.  score_total 은 555 환산이라 분모가 다른
    #   매물이 잘못 섞인다 (E-1 · E-3)
    "rank": "(s.earned * 1.0 / NULLIF(s.denominator, 0)) DESC",
    "grade": "s.grade ASC",
    "price": "l.price_current_won ASC",
    "price_desc": "l.price_current_won DESC",
    "mileage": "l.mileage_km ASC",
    "year": "l.year_month DESC",
    "new": "l.first_seen DESC",
    "dom": "l.first_seen ASC",
}

# ★ E 와 NOT_RATED 는 뒤로.  비교 대상이 아니다
ORDER_HEAD = ("(CASE WHEN s.grade IN ('E','NOT_RATED') THEN 1 ELSE 0 END)")
# ★ 타이브레이커가 없으면 같은 점수가 페이지마다 다르게 나온다 (V6-07)
ORDER_TAIL = ("(s.earned * 1.0 / NULLIF(s.denominator, 0)) DESC,"
              " l.price_current_won ASC, l.listing_id ASC")


def order_clause(order: str) -> str:
    """4단 정렬.  ★ 축을 바꿔도 뒤 3단은 남는다."""
    first = ORDER_SQL.get(order, ORDER_SQL["rank"])
    return f"{ORDER_HEAD}, {first}, {ORDER_TAIL}"


def _view_str(key: str, root: str = ".") -> str:
    """화면 표시 정책 중 문자열.  ★ 코드에 박지 않는다 (config/web.json)."""
    with open(os.path.join(root, "config", "web.json"), encoding="utf-8") as f:
        return str(json.load(f)[key])


def _listings_where(flt: ListingFilter) -> tuple[list, list]:
    """목록 조건.  ★ 세는 것과 뽑는 것이 같은 조건을 쓴다 —
    갈라 두면 「3,471건 중 200건」의 3,471 이 거짓말이 된다 (V11-55)."""
    where = ["l.site = ?"]
    args: list = [flt.site]
    if flt.target_key:
        where.append("l.target_key = ?")
        args.append(flt.target_key)
    if flt.grade:
        where.append("s.grade = ?")
        args.append(flt.grade)
    # ★ 시세 막대를 누르면 그 구간 매물로 간다 (STEP 97).
    #   링크가 200 을 내는 것과 필터가 걸리는 것은 다르다 (실측 08-15)
    if flt.price_min is not None:
        where.append("l.price_current_won >= ?")
        args.append(flt.price_min)
    if flt.price_max is not None:
        where.append("l.price_current_won <= ?")
        args.append(flt.price_max)
    # ★ 값을 누르면 그 조건으로 (STEP 149p · 개정 276).
    #   링크만 걸고 조건이 안 걸리면 200 은 나오지만 전건이 나온다 (실측 08-15)
    if flt.dealer:
        where.append("l.dealer_shop = ?")
        args.append(flt.dealer)
    if flt.year:
        where.append("l.year_month LIKE ?")
        args.append(f"{flt.year}%")
    if flt.km_max is not None:
        where.append("l.mileage_km <= ?")
        args.append(flt.km_max)
    if flt.listing_status:
        where.append("l.status = ?")
        args.append(flt.listing_status)
    # ★ 「A 이상만」 (STEP 149s).  NOT_RATED 는 등급이 아니라 뺀다
    if flt.min_grade:
        ok = [g for g in RANK_ORDER
              if RANK_ORDER.index(g) <= RANK_ORDER.index(flt.min_grade)]
        where.append(f"s.grade IN ({','.join('?' * len(ok))})")
        args += ok
    if not flt.show_all:
        where.append("l.status <> 'out_of_scope'")
    if flt.axis and flt.bucket:
        cond = {
            "1": "a.value > 0 AND a.excluded = 0",
            "0": "a.value = 0 AND a.excluded = 0",
            "na": "a.value = -1 AND a.excluded = 1",
            "unknown": "a.value IS NULL AND a.excluded = 1",
        }[flt.bucket]
        where.append(
            "EXISTS (SELECT 1 FROM result_axis a WHERE a.listing_id=l.listing_id"
            f" AND a.axis=? AND a.calc_version=? AND {cond})")
        args += [flt.axis, flt.calc_version]
    return where, args


def count_listings(conn: sqlite3.Connection, flt: ListingFilter) -> int:
    """조건에 맞는 전체 건수 (V11-55).  ★ 쪽을 나누려면 전체를 알아야 한다.

    쿼리 1개를 더 쓴다 — 「몇 건 중 몇 건」을 못 내는 것보다 낫다 (V11-34 여유 안)
    """
    where, args = _listings_where(flt)
    return conn.execute(
        "SELECT COUNT(*) FROM core_listing l LEFT JOIN result_score s"
        " ON s.listing_id = l.listing_id AND s.calc_version = ?"
        f" WHERE {' AND '.join(where)}", [flt.calc_version, *args]).fetchone()[0]


def view_listings(account: Account, conn: sqlite3.Connection,
                  flt: ListingFilter, fin_cfg: dict, root: str = ".",
                  page_size: int | None = None) -> list[ListingRow]:
    """축·버킷 필터는 Component 이름을 쓴다 — /listings?axis=spec.hud&bucket=1."""
    where, args = _listings_where(flt)

    sql = (
        "SELECT l.listing_id, l.target_key, l.trim_badge, l.year_month,"
        " l.mileage_km, l.color_ext_raw, l.color_int_raw, l.price_current_won,"
        # ★ earned 를 가져온다.  비율은 earned/denominator 다 —
        #   score_total(555 환산)로 나누면 분모가 짧을수록 부풀려진다 (E-1)
        " s.grade, s.earned, s.denominator, l.dealer_shop, l.status,"
        # ★ 사진은 이미 원문에서 뽑아 앉아 있다 — 다시 받지 않는다 (개정 274)
        " l.first_seen, l.last_seen, s.dict_version, l.photo_list_json,"
        # ★ 시세차 · 경과 · 정직도 · 비고 (개정 277 · 278).
        #   행마다 따로 조회하면 200행에 1,000쿼리다 — 조인으로 한 번에 (V11-34)
        " l.source_id, l.price_origin_won, s.calculated_at, s.absolute_fail,"
        " d.trust_score, d.quadrant, d.sample_sufficient"
        " FROM core_listing l LEFT JOIN result_score s"
        " ON s.listing_id = l.listing_id AND s.calc_version = ?"
        " LEFT JOIN core_dealer d ON d.dealer_id = l.dealer_id"
        f" WHERE {' AND '.join(where)}"
        f" ORDER BY {order_clause(flt.order)}"
        " LIMIT ? OFFSET ?")
    labels = _labels(root)
    # all=1 은 전체다.  페이지 크기는 정책값이라 config 에 둔다 (STEP 106)
    if page_size is None:
        # ★ 출처는 web.rows_per_page 하나다 (E-5).
        #   옛 판은 scoring 쪽에도 같은 값이 있어 화면마다 갈렸다
        with open(f"{root}/config/web.json", encoding="utf-8") as f:
            page_size = int(json.load(f)["rows_per_page"])
    limit = -1 if flt.show_all else page_size
    recs = conn.execute(
        sql, [flt.calc_version, *args, limit, (flt.page - 1) * limit]).fetchall()
    lids = [r[0] for r in recs]
    axes = _bulk_axes(conn, lids, flt.calc_version)
    changes = _bulk_changes(conn, lids)
    base = _view_str("photo_base_url", root)
    encar_tpl = _view_str("encar_detail_url", root)
    km_unit = _view_cfg("km_bucket", root)
    monthly_unit = _view_cfg("monthly_bucket_won", root)
    with open(os.path.join(root, "config", "depreciation.json"),
              encoding="utf-8") as f:
        dep_cfg = json.load(f)
    # ★ 순위는 쪽을 넘어가도 이어진다 — 2쪽 첫 줄이 다시 1위가 되면 거짓말이다
    first = 0 if flt.show_all else (flt.page - 1) * page_size
    return [_row(conn, r, labels, fin_cfg, first + i + 1, flt.calc_version,
                 axes, changes, base, encar_tpl, km_unit, monthly_unit,
                 dep_cfg) for i, r in enumerate(recs)]


def recommend_funnel(conn, calc_version: str, shown: int) -> dict:
    """후보가 몇 건인지만 내면 「왜 이것뿐인가」를 못 본다 (마스터 지시 08-16 · 7번).

    ★ 단계마다 숫자를 낸다 — 어디서 줄었는지 눈으로 본다.
      실측 08-16: 후보가 1건이었던 원인은 현재 판(calc_version)이 잘못
      뽑힌 것이었다.  이 줄이 있었으면 바로 보였다
    """
    judged = conn.execute(
        "SELECT COUNT(*) FROM result_score WHERE calc_version=?",
        (calc_version,)).fetchone()[0]
    dropped = conn.execute(
        "SELECT COUNT(*) FROM result_score WHERE calc_version=?"
        " AND grade IN ('E','NOT_RATED')", (calc_version,)).fetchone()[0]
    return {"judged": judged, "dropped": dropped,
            "eligible": judged - dropped, "shown": shown}


def _bulk_upside(conn, lids: list, calc_version: str) -> dict:
    """확인 못 한 축의 배점 합 (시안 v2_recommend .pbar).

    ★ 행마다 돌지 않는다.  IN 절로 한 번에 받는다 (V11-34)
    """
    if not lids:
        return {}
    marks = ",".join("?" * len(lids))
    return {r[0]: float(r[1] or 0) for r in conn.execute(
        f"SELECT listing_id, SUM(max_points) FROM result_axis "
        f"WHERE calc_version = ? AND excluded = 1 AND value IS NULL "
        f"AND listing_id IN ({marks}) GROUP BY listing_id",
        (calc_version, *lids))}


def view_recommend(account: Account, conn, flt: ListingFilter,
                   fin_cfg: dict, root: str = ".") -> list[ListingRow]:
    """추천 대상만.  E 와 NOT_RATED 는 순위를 매기지 않는다 (7장 STEP 84)."""
    rows = [r for r in view_listings(account, conn, flt, fin_cfg, root)
            if r.grade not in ("E", NOT_RATED)]
    # ★ 「지금 얼마」와 「채우면 얼마까지」를 함께 낸다 (STEP 105 · 149h).
    #   지금 비율만 보면 이 차가 끝인지 아닌지 알 수 없다
    up = _bulk_upside(conn, [r.listing_id for r in rows], flt.calc_version)
    total = _total_points()
    out = []
    for r in rows:
        gain = up.get(r.listing_id, 0.0)
        out.append(replace(
            r,
            upside_points=gain,
            got_pct=round((r.earned or 0) / total * 100, 1) if total else 0.0,
            may_pct=round(gain / total * 100, 1) if total else 0.0))
    return out


# 절대조건 탈락 사유별 안내.  ★ 「왜 뺐는지」가 판단 재료다 (시안 v2_recommend)
EXCLUDED_NOTES = {
    "리스·렌트 상품": "표시가가 승계 인수금입니다. 월 사용료가 따로 듭니다",
    "계약중·판매완료": "이미 계약된 매물입니다",
    "골격 손상": "골격 수리 이력이 있습니다",
    "수리비 10% 초과": "수리비가 차값의 10% 를 넘었습니다",
    "전손": "전손 처리 이력이 있습니다",
    "저당": "저당 · 압류가 걸려 있습니다",
}


def excluded_groups(conn, calc_version: str) -> list:
    """후보에서 뺀 것.  ★ 몇 건인지보다 왜인지가 먼저다."""
    counts: dict = {}
    for (reason,) in conn.execute(
        "SELECT absolute_fail FROM result_score "
        "WHERE calc_version=? AND grade='E'", (calc_version,)
    ):
        for part in (reason or "사유 없음").split(";"):
            key = part.strip() or "사유 없음"
            counts[key] = counts.get(key, 0) + 1
    return [ExcludedGroup(k, v, EXCLUDED_NOTES.get(k, ""),
                          f"/listings?grade=E&reason={k}")
            for k, v in sorted(counts.items(), key=lambda kv: -kv[1])]


def view_why(account: Account, conn, listing_id: int, calc_version: str,
             fin_cfg: dict, policy: dict, root: str = "."):
    """L1 — 9장 STEP 90 L1 항목 전건."""
    return render_listing(conn, listing_id, calc_version, fin_cfg, policy, root)


def view_compare(account: Account, conn, listing_ids: list[int],
                 calc_version: str, fin_cfg: dict, policy: dict,
                 root: str = ".") -> CompareView:
    """분모가 다르면 경고 · 버전이 다르면 비교 불가 (V6-05)."""
    views = [render_listing(conn, i, calc_version, fin_cfg, policy, root)
             for i in listing_ids]
    axes = [a.axis for a in views[0].axes] if views else []
    cells: dict[tuple[str, str], AxisView] = {}
    for v in views:
        for a in v.axes:
            cells[(v.listing_id, a.axis)] = a
    denoms = {v.denominator for v in views}
    vers = {(v.versions.calc_version, v.versions.dict_version) for v in views}
    flt = ListingFilter(calc_version=calc_version)
    rows = [r for r in view_listings(account, conn, flt, fin_cfg, root)
            if r.listing_id in set(listing_ids)]
    # ★ 「이 셋 중에서」 — 축마다 누가 앞서는가.  표를 눈으로 훑게 두지 않는다
    winner = {}
    for axis in axes:
        best, top = None, None
        for v in views:
            cell = cells.get((v.listing_id, axis))
            if cell is None or cell.excluded:
                continue
            if top is None or cell.points > top:
                best, top = v.listing_id, cell.points
        winner[axis] = best
    return CompareView(rows, axes, cells, len(denoms) > 1, len(vers) > 1,
                       axis_winner=winner)


def view_market(account: Account, conn, target_key: str,
                depreciation: dict, quantiles=None) -> MarketView:
    from report.render import CoefficientChange  # noqa: F401

    prices = [r[0] for r in conn.execute(
        "SELECT price_current_won FROM core_listing WHERE target_key=? "
        "AND price_current_won IS NOT NULL ORDER BY price_current_won",
        (target_key,))]

    def q(p):
        return prices[int(len(prices) * p)] if prices else None

    qs = quantiles or MARKET_QUANTILES
    row = MarketRow("", len(prices), len(prices),
                    prices[0] if prices else None, q(qs[0]), q(qs[1]), q(qs[2]),
                    prices[-1] if prices else None)
    hist = [r for r in conn.execute(
        "SELECT target_key, before_value, after_value, sample_size, reason,"
        " changed_at FROM coefficient_history WHERE target_key=?", (target_key,))]
    curve = sorted((int(k), float(v))
                   for k, v in (depreciation.get("curve") or {}).items())
    return MarketView(target_key, [row], list(hist), curve,
                      price_bins=_price_bins(prices, target_key),
                      by_year=_by_year(conn, target_key),
                      by_trim=_by_trim(conn, target_key),
                      other_targets=_other_targets(conn, target_key))


def _web_cfg(key, root: str = "."):
    """화면 설정.  ★ 수를 코드에 박지 않는다 (V4-17)."""
    import json as _j
    import os as _o

    here = _o.path.dirname(_o.path.dirname(_o.path.dirname(
        _o.path.abspath(__file__))))
    with open(_o.path.join(here, "config", "web.json"), encoding="utf-8") as f:
        return _j.load(f)[key]





def _median(xs: list):
    xs = sorted(x for x in xs if x is not None)
    return xs[len(xs) // 2] if xs else None


def _with_height(buckets: list, root: str = ".") -> list:
    """막대 높이를 채운다.  ★ 가장 많은 구간이 100% 다 (시안 v2_market .hist).

    ★ 최소 높이는 표시 정책이라 config 에 둔다 —
      0건이 아닌데 안 보이면 「없다」로 읽힌다
    """
    top = max((b.count for b in buckets), default=0)
    if not top:
        return buckets
    floor = _view_cfg("hist_min_bar_pct", root)
    return [replace(b, height_pct=max(floor, round(b.count / top * 100))
                    if b.count else 0)
            for b in buckets]


def _price_bins(prices: list, target_key: str,
                bins: int = PRICE_BINS, root: str = ".") -> list:
    """가격 분포.  ★ 막대를 누르면 그 구간 매물로 간다 (시안 v2_market)."""
    if not prices:
        return []
    lo, hi = prices[0], prices[-1]
    if hi <= lo:
        return [Bucket("", lo, hi, len(prices), lo,
                       f"/listings?target={target_key}")]
    width = (hi - lo) / bins
    out = []
    for i in range(bins):
        a = int(lo + width * i)
        b = int(lo + width * (i + 1)) if i < bins - 1 else hi
        got = [p for p in prices if a <= p <= b]
        out.append(Bucket("", a, b, len(got), _median(got),
                          f"/listings?target={target_key}"
                          f"&price_min={a}&price_max={b}"))
    return _with_height(out, root)


def _by_year(conn, target_key: str) -> list:
    """연식별 중앙값.  ★ 표본 5건 미만은 내지 않는다 — 시세로 믿게 된다."""
    out = []
    for ym, cnt in conn.execute(
        "SELECT substr(year_month,1,4), COUNT(*) FROM core_listing "
        "WHERE target_key=? AND year_month IS NOT NULL "
        "GROUP BY 1 ORDER BY 1 DESC", (target_key,)
    ):
        prices = [r[0] for r in conn.execute(
            "SELECT price_current_won FROM core_listing WHERE target_key=? "
            "AND substr(year_month,1,4)=? AND price_current_won IS NOT NULL",
            (target_key, ym))]
        enough = len(prices) >= MIN_SAMPLE
        out.append(Bucket(f"{ym}년", None, None, cnt,
                          _median(prices) if enough else None,
                          f"/listings?target={target_key}&year={ym}", enough))
    return out


def _by_trim(conn, target_key: str) -> list:
    out = []
    for trim, cnt in conn.execute(
        "SELECT trim_badge, COUNT(*) FROM core_listing WHERE target_key=? "
        "AND trim_badge IS NOT NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 20",
        (target_key,)
    ):
        prices = [r[0] for r in conn.execute(
            "SELECT price_current_won FROM core_listing WHERE target_key=? "
            "AND trim_badge=? AND price_current_won IS NOT NULL",
            (target_key, trim))]
        enough = len(prices) >= MIN_SAMPLE
        out.append(Bucket(trim, None, None, cnt,
                          _median(prices) if enough else None,
                          f"/listings?target={target_key}&trim={trim}",
                          enough))
    return out


def _other_targets(conn, target_key: str) -> list:
    return [Bucket(tk, None, None, cnt, None, f"/market?target={tk}")
            for tk, cnt in conn.execute(
                "SELECT target_key, COUNT(*) FROM core_listing "
                "WHERE target_key IS NOT NULL AND target_key<>? "
                "GROUP BY 1 ORDER BY 2 DESC", (target_key,))]


def count_dealers(conn, site: str = "encar") -> int:
    """딜러 전체 곳수.  ★ SQL 은 web/ 에 두지 않는다 (V11-01)."""
    return conn.execute("SELECT COUNT(*) FROM core_dealer WHERE site=?",
                        (site,)).fetchone()[0]


def _dealer_targets(conn, dealer_ids: list, top: int) -> dict:
    """딜러별 차종 분포 (마스터 지적 ⑤).

    ★ 행마다 돌지 않는다 — IN 절로 한 번에 받는다 (V11-34)
    """
    if not dealer_ids:
        return {}
    marks = ",".join("?" * len(dealer_ids))
    out: dict = {}
    for did, tk, n in conn.execute(
        f"SELECT dealer_id, target_key, COUNT(*) FROM core_listing "
        f"WHERE dealer_id IN ({marks}) AND target_key IS NOT NULL "
        f"GROUP BY 1, 2 ORDER BY 1, 3 DESC", tuple(dealer_ids)
    ):
        got = out.setdefault(did, [])
        if len(got) < top:
            got.append({"target_key": tk, "count": n})
    return {k: tuple(v) for k, v in out.items()}


def _dealer_region(conn, dealer_ids: list) -> dict:
    """지역.  ★ core_dealer.region 이 전건 비어 있다 (실측 08-16 · 719/719).

    원문에는 있다 — core_listing.dealer_region 이 7,629건 채워져 있다.
    S11 딜러 집계가 그것을 안 옮긴다.  고쳐지기 전까지 매물에서 읽는다
    """
    if not dealer_ids:
        return {}
    marks = ",".join("?" * len(dealer_ids))
    return {r[0]: r[1] for r in conn.execute(
        f"SELECT dealer_id, MAX(dealer_region) FROM core_listing "
        f"WHERE dealer_id IN ({marks}) AND dealer_region IS NOT NULL "
        f"GROUP BY 1", tuple(dealer_ids))}


def view_dealers(account: Account, conn, site: str = "encar",
                 root: str = ".", page: int = 1) -> list[DealerRow]:
    """sample_sufficient=0 이면 trust_score 를 확정 표시하지 않는다 (V3-26).

    ★ 719곳을 한 번에 보내지 않는다 — 139KB 였다 (검토 15).  쪽으로 나눈다
    """
    size = _view_cfg("rows_per_page", root)
    out = []
    for r in conn.execute(
        # ★ 실명을 조회하지 않는다.  상호만 쓴다 (STEP 35)
        "SELECT dealer_id, dealer_shop, region, career_years,"
        " quadrant, trust_score, sample_sufficient, listing_count,"
        " total_sales, recent_year_sales FROM core_dealer WHERE site=?"
        " ORDER BY listing_count DESC, dealer_id LIMIT ? OFFSET ?",
        (site, size, (max(1, page) - 1) * size)
    ):
        out.append(DealerRow(r[0], r[1], r[2], r[3], r[4],
                             r[5] if r[6] else None, bool(r[6]), r[7],
                             r[8], r[9]))
    # ★ 4분면 좌표 (시안 v2_dealers .quad).  가로는 매물 수, 세로는 정직도다.
    #   표본이 모자란 딜러는 좌표를 주지 않는다 — 0 으로 찍으면
    #   「정직도 0인 딜러」가 되어 없는 사실을 만든다 (V3-26)
    top = max((d.volume or 0 for d in out), default=0)
    ids = [d.dealer_id for d in out]
    by_target = _dealer_targets(conn, ids, _view_cfg("dealer_target_top", root))
    by_region = _dealer_region(conn, ids)
    return [replace(d,
                    dealer_region=d.dealer_region or by_region.get(d.dealer_id),
                    targets=by_target.get(d.dealer_id, ()),
                    quad_x=round((d.volume or 0) / top * 100, 1) if top else None,
                    quad_y=(round(float(d.honesty_score), 1)
                            if d.sample_sufficient and d.honesty_score is not None
                            else None))
            for d in out]


def view_run(account: Account, conn, run_id: str, calc_version: str):
    """수집·판정 실행 상태는 관리자만 본다 (STEP 126 권한 표)."""
    require_role(account, ROLE_ADMIN)
    return render_run(conn, run_id, calc_version)


def _rank1_of(grades: dict) -> str | None:
    """가장 높은 등급.  ★ 없으면 None 이다 — 0 이 아니다."""
    for g in GRADE_ORDER:
        if grades.get(g):
            return g
    return None


def view_dashboard(account: Account, conn, run_id: str, calc_version: str,
                   fin_cfg: dict, root: str = ".") -> DashboardView:
    # ★ 차종마다 조회하면 12차종에 24쿼리다.  한 번에 묶는다 (V11-34 · B-2)
    grade_rows = conn.execute(
        "SELECT l.target_key, s.grade, COUNT(*) FROM result_score s "
        "JOIN core_listing l ON l.listing_id = s.listing_id "
        "WHERE s.calc_version = ? GROUP BY 1, 2", (calc_version,)).fetchall()
    by_target: dict = {}
    for tk, grade, n in grade_rows:
        by_target.setdefault(tk, {})[grade] = n
    price_rows = conn.execute(
        "SELECT l.target_key, l.price_current_won FROM result_score s "
        "JOIN core_listing l ON l.listing_id = s.listing_id "
        "WHERE s.calc_version = ? AND s.grade = 'A' "
        "AND l.price_current_won IS NOT NULL ORDER BY 1, 2",
        (calc_version,)).fetchall()
    prices: dict = {}
    for tk, p in price_rows:
        prices.setdefault(tk, []).append(p)

    stats = []
    # ★ 차종이 없는 매물이 있다.  목록 쿼리가 ModelGroup 단위라
    #   우리가 안 보는 트림·연료가 함께 온다 (실측 08-16 · 4,188건).
    #   None 을 그냥 정렬하면 화면이 통째로 500 이 된다 — 이름을 주어 함께 낸다
    for tk in sorted(by_target, key=lambda k: (k is None, k or "")):
        grades = by_target[tk]
        got = prices.get(tk, [])
        stats.append(TargetStat(
            target_key=tk or "차종 미정", total=sum(grades.values()),
            grades=grades,
            rank1=_rank1_of(grades),
            median_price_a_won=got[len(got) // 2] if got else None))

    changes = [ChangeRow(*r) for r in conn.execute(
        "SELECT listing_id, field, old_value, new_value, change_kind,"
        " changed_at FROM core_listing_change "
        "ORDER BY changed_at DESC LIMIT 20")]

    # ★ 조치가 필요한 것 — 세 물음을 한 번에 센다 (V11-34)
    counts = conn.execute(
        "SELECT (SELECT COUNT(*) FROM meta_field_usage "
        "        WHERE usage='unclassified'), "
        "       (SELECT COUNT(*) FROM dict_enum WHERE status='pending'), "
        "       (SELECT COUNT(DISTINCT axis) FROM result_axis "
        "        WHERE excluded=1 AND source IN "
        "        ('gate_closed','coefficient_out_of_range'))").fetchone()
    attention = []
    for n, kind, detail, action in (
        (counts[0], "unclassified", "등록부 미분류 경로",
         "config/field_usage.suggested.json 을 확인·수정해 "
         "config/field_usage.json 으로 옮긴 뒤 재실행한다"),
        (counts[1], "pending", "사전 미검토 값",
         "원문 표본 3건을 확인해 confirmed 로 올린 뒤 S9 를 재실행한다"),
        (counts[2], "undecided", "미확정으로 분모에서 빠진 축",
         "감가 곡선·HDA Gate·색상 목록을 확정한다"),
    ):
        if n:
            attention.append(AttentionItem(kind, detail, n, action))

    # ★ 같은 집계를 두 번 돌면 화면 한 쪽이 그만큼 늘어난다 (V11-34 · B-2)
    grade_counts = _grade_counts(conn, calc_version)

    return DashboardView(
        meta=ReportMeta(run_id, "L3", "encar", None, calc_version, None),
        viewer=viewer_state(account),
        target_stats=stats, recent_changes=changes,
        # ★ 상위 후보 — 점수순이 아니다.  view_recommend 와 같은 순서다
        finalists=view_recommend(
            account, conn, ListingFilter(calc_version=calc_version),
            fin_cfg, root)[:5],
        grade_counts=grade_counts,
        grade_rows=[{"grade": k, "count": v}
                    for k, v in grade_counts.items()],
        grade_total=conn.execute(
            "SELECT COUNT(*) FROM result_score WHERE calc_version=?",
            (calc_version,)).fetchone()[0],
        e_reasons=_e_reasons(conn, calc_version),
        today_changes=_today_changes(conn),
        steps=_step_rows(conn, run_id),
        # 주의 항목은 관리자만 본다 — 조치가 관리자 행동이다
        attention=attention if account.role == ROLE_ADMIN else [])


# 등급 표시 차례.  ★ 색을 쓰지 않으므로 순서가 유일한 단서다 (STEP 145a)
# 수집 단계 이름.  ★ 「없음(not_found)」과 「실패」는 뜻이 다르다
STEP_LABELS = {"list": "S1 목록", "detail": "S5 상세",
               "inspection": "S5 성능점검", "record": "S5 이력",
               "diagnosis": "S6a 진단", "catalog": "S7 카탈로그",
               "facet": "S2 분류"}


def _grade_counts(conn, calc_version: str) -> dict:
    got = {r[0]: r[1] for r in conn.execute(
        "SELECT grade, COUNT(*) FROM result_score WHERE calc_version=? "
        "GROUP BY grade", (calc_version,))}
    return {g: got.get(g, 0) for g in GRADE_ORDER}


def _e_reasons(conn, calc_version: str) -> dict:
    """E 사유별 건수.

    ★ 「E 33건」만 내면 사람이 아무것도 못 한다.  왜 E 인지가 판단 재료다.
      absolute_fail 은 여러 사유가 「; 」로 붙는다 — 쪼개서 센다
    """
    out: dict = {}
    for (reason,) in conn.execute(
        "SELECT absolute_fail FROM result_score "
        "WHERE calc_version=? AND grade='E'", (calc_version,)
    ):
        for part in (reason or "사유 없음").split(";"):
            key = part.strip() or "사유 없음"
            out[key] = out.get(key, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def _today_changes(conn, limit: int = TODAY_ROWS) -> list:
    """오늘 변동.  ★ 인하는 좋음, 인상은 나쁨 — 색이 뜻을 갖는 유일한 자리다."""
    rows = []
    for lid, field_, old, new, kind, _at, tk in conn.execute(
        "SELECT c.listing_id, c.field, c.old_value, c.new_value, "
        "c.change_kind, c.changed_at, l.target_key "
        "FROM core_listing_change c "
        "JOIN core_listing l ON l.listing_id = c.listing_id "
        "ORDER BY c.changed_at DESC LIMIT ?", (limit,)
    ):
        delta = None
        if kind == "price" and old and new:
            try:
                delta = int(float(new)) - int(float(old))
                kind = "인상" if delta > 0 else "인하"
            except ValueError:
                delta = None
        try:
            price = int(float(new)) if new else None
        except ValueError:
            price = None
        rows.append(TodayChange(kind, tk or "-", field_, delta, price, lid))
    return rows


def _step_rows(conn, run_id: str) -> list:
    """수집 단계.  ★ 「없음」을 실패로 세지 않는다 — 그 매물에 없는 것이다."""
    out = []
    for kind, req, ok, missing, failed, ms in conn.execute(
        "SELECT kind, COUNT(*), "
        " SUM(CASE WHEN status='ok' THEN 1 ELSE 0 END), "
        " SUM(CASE WHEN status='not_found' THEN 1 ELSE 0 END), "
        " SUM(CASE WHEN status NOT IN ('ok','not_found') THEN 1 ELSE 0 END), "
        " SUM(elapsed_ms) FROM audit_request WHERE run_id=? "
        "GROUP BY kind ORDER BY MIN(id)", (run_id,)
    ):
        out.append(StepRow(kind, STEP_LABELS.get(kind, kind), req, ok or 0,
                           missing or 0, failed or 0, (ms or 0) / MS_PER_SEC,
                           "정상" if not failed else f"실패 {failed}"))
    return out


def _bulk_spark(conn, lids: list) -> dict:
    """관심 매물의 가격 추이 (시안 v2_watch .spark).

    ★ 「지금 얼마」만으로는 내려가는 중인지 올라가는 중인지 모른다.
    ★ 행마다 돌지 않는다 — IN 절로 한 번에 (V11-34)
    """
    lids = [x for x in lids if x is not None]
    if not lids:
        return {}
    marks = ",".join("?" * len(lids))
    series: dict = {}
    for lid, old, new in conn.execute(
        f"SELECT listing_id, old_value, new_value FROM core_listing_change "
        f"WHERE change_kind='price' AND listing_id IN ({marks}) "
        f"ORDER BY changed_at ASC", tuple(lids)
    ):
        try:
            a, b = int(float(old)), int(float(new))
        except (TypeError, ValueError):
            continue          # 숫자가 아니면 없는 것으로 둔다 — 지어내지 않는다
        got = series.setdefault(lid, [])
        if not got:
            got.append(a)
        got.append(b)
    out: dict = {}
    for lid, prices in series.items():
        top = max(prices) or 1
        out[lid] = tuple(
            {"pct": round(p / top * 100), "won": p,
             # ★ 인하가 좋음 · 인상이 나쁨 (STEP 145a)
             "dn": i > 0 and p < prices[i - 1],
             "now": i == len(prices) - 1}
            for i, p in enumerate(prices))
    return out


def view_watch(account: Account, conn, fin_cfg: dict,
               calc_version: str, root: str = ".") -> list:
    """★ 개인화는 watch_* 조회에 account_id 를 거는 것으로 끝난다.

    판정은 계정과 무관하다.  같은 차는 누가 봐도 같은 등급이다 (STEP 105).
    비로그인은 관심 등록을 못 한다 (STEP 126 권한 표).
    """
    require_role(account, ROLE_USER)
    # ★ watch_id 를 함께 낸다.  없으면 목표가 저장 · 추적 종료를 못 누른다
    rows = conn.execute(
        # ★ 관심 하나에 한 행이다.  vehicle_id 로 조인하면 같은 차의
        #   매물이 여럿일 때 한 관심이 여러 행으로 늘어나고,
        #   목표가가 어느 행 것인지 알 수 없다 (실측 08-15)
        "SELECT w.watch_id, "
        "       COALESCE(w.primary_listing_id, MIN(l.listing_id)), "
        "       w.target_price_won, w.added_at, w.closed_at, w.memo "
        "FROM watch_item w LEFT JOIN core_listing l "
        "ON l.vehicle_id = w.vehicle_id "
        "WHERE w.account_id = ? AND w.closed_at IS NULL "
        "GROUP BY w.watch_id "
        "ORDER BY w.added_at DESC", (account.account_id,)).fetchall()
    if not rows:
        return []
    flt = ListingFilter(calc_version=calc_version)
    by_id = {r.listing_id: r
             for r in view_listings(account, conn, flt, fin_cfg, root)}
    spark = _bulk_spark(conn, [r[1] for r in rows])
    out = []
    for wid, lid, target, added, closed, memo in rows:
        listing = by_id.get(lid)
        if listing is None:
            continue          # 아직 채점 전이다 — 조용히 빼지 않고 다음 회차에
        out.append(WatchRow(watch_id=wid, listing=listing,
                            target_price_won=target, added_at=added,
                            closed_at=closed, memo=memo,
                            spark=spark.get(lid, ())))
    return out


# 사전 미검토 값이 막는 축.  ★ 「무엇을 막고 있나」가 판단 재료다
DICT_AXIS_BLOCKS = {
    "panel_status": "사고 축 판정에 씀 — 이 값이 감점 대상인지 정해야 합니다",
    "panel_rank": "사고 축 — 골격인지 외판인지가 갈립니다",
    "color_ext": "색상 축 — 선호 3색인지 정해야 합니다",
    "color_int": "색상 축 — 내장색 선호를 정해야 합니다",
    "fuel": "사양 축 — 연료 구분에 씁니다",
    "accident_type": "이력 축 — 사고 유형 감점에 씁니다",
}


def _pending_values(conn) -> list:
    """★ 「17건」이 아니라 축·값·건수·막는 것을 낸다 (G-1)."""
    return [PendingValue(axis, value, cnt,
                         DICT_AXIS_BLOCKS.get(axis, "판정에 쓰지 않습니다"))
            for axis, value, cnt in conn.execute(
                "SELECT axis, value, count_seen FROM dict_enum "
                "WHERE status='pending' ORDER BY count_seen DESC LIMIT 40")]


def _done_items(conn, calc_version: str) -> list:
    """이미 된 것.

    ★ 「아무것도 안 됐다」와 「등급만 없다」는 다르다.
      가격·연식·주행·사양은 이미 파싱됐다 — 지금도 볼 수 있다
    """
    out = []
    n = conn.execute("SELECT COUNT(*) FROM core_listing").fetchone()[0]
    # ★ raw_* 를 화면이 직접 조회하지 않는다 (V6-03).
    #   원문 건수는 요청 기록(audit_request)으로 센다 — 같은 사실의 표시용 면이다
    raw = conn.execute(
        "SELECT COUNT(*) FROM audit_request WHERE status='ok'").fetchone()[0]
    if n:
        out.append(f"수집 — 매물 {n:,}건 · 응답 {raw:,}건 저장")
    n = conn.execute(
        "SELECT COUNT(*) FROM core_listing "
        "WHERE price_current_won IS NOT NULL").fetchone()[0]
    if n:
        out.append(f"파싱 — 가격 · 연식 · 주행 · 사양 {n:,}건 완료")
    n = conn.execute("SELECT COUNT(*) FROM result_score "
                     "WHERE calc_version=?", (calc_version,)).fetchone()[0]
    if n:
        out.append(f"채점 — {n:,}건 (등급은 아래 사유로 일부가 멈춰 있습니다)")
    return out


def view_notready(account: Account, conn, calc_version: str,
                  run_id: str) -> NotReadyView:
    """판정 결과를 빈 값으로 보여주지 않는다 (STEP 104)."""
    reasons, actions = [], []
    n = conn.execute("SELECT COUNT(*) FROM result_score "
                     "WHERE calc_version=?", (calc_version,)).fetchone()[0]
    if not n:
        reasons.append("채점 결과가 없다 (S10 미실행 또는 중단)")
        actions.append("python3 run.py collect 를 실행한다")
    n = conn.execute(
        "SELECT COUNT(*) FROM meta_field_usage WHERE usage='unclassified'"
    ).fetchone()[0]
    if n:
        reasons.append(f"등록부 미분류 {n}건 — V4-11 이 판정을 막는다")
        actions.append("config/field_usage.suggested.json 을 확인·수정해 "
                       "config/field_usage.json 으로 옮긴 뒤 재실행한다")
    rows = _unmatched_rows(conn)
    n_null = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE target_key IS NULL"
    ).fetchone()[0]
    n_ok = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE target_key IS NOT NULL"
    ).fetchone()[0]
    if n_null:
        reasons.append(f"차종이 안 붙은 매물 {n_null:,}건 — 판정 대상이 아니다")
        actions.append("아래 모델명·배지를 보고 targets.json 의 "
                       "fuel_match · trim_include 를 고치거나 그대로 둔다")
    return NotReadyView(
        ReportMeta(run_id, "L3", "encar", None, calc_version, None),
        reasons, actions,
        pending_values=_pending_values(conn),
        done=_done_items(conn, calc_version),
        unmatched=rows, unmatched_total=n_null, matched_total=n_ok)


def _unmatched_rows(conn, limit: int | None = None) -> list:
    """차종이 안 붙은 매물을 모델·연료·배지로 묶어 낸다 (개정 271 · V2-32).

    ★ 「4,188건」만 내면 사람이 아무것도 못 한다.
      「그랜저 가솔린 706건」이라야 targets.json 을 고칠지 정한다
    """
    limit = _view_cfg("rows_per_page") if limit is None else limit
    return [{"manufacturer": mf, "model_group": mg, "fuel": fuel,
             "trim": trim, "count": n}
            for mf, mg, fuel, trim, n in conn.execute(
                "SELECT site_manufacturer, site_model_group, fuel_raw, "
                "       trim_badge, COUNT(*) "
                "FROM core_listing WHERE target_key IS NULL "
                "GROUP BY 1, 2, 3 ORDER BY 5 DESC LIMIT ?", (limit,))]
