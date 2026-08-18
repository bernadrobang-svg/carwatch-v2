# -*- coding: utf-8 -*-
"""리포트 생성 (L9).

지시서   9장 STEP 90 (4층) · 91 (표시 규칙)
근거     Reporter 는 DTO 를 받아 형식만 바꾼다.  판정을 계산하지 않는다
금지     제외 축을 「0점」으로 쓰는 것.  「평가 불가」를 낮은 등급으로 쓰는 것
         「판매됨」이라 쓰는 것 — gone 은 목록에서 사라진 것이다
"""
from __future__ import annotations

import json
import sqlite3

from report.finance import build_finance
from report.views import (
    RunStep,
    CostRow,
    FetchView,
    DiagnosisView,
    AxisStat, AxisView, ClassifySummary, CoefficientChange, CollectSummary,
    DictChangeSummary, HaltReport, PriceSummary, ReportMeta, RunReport,
    ScoreView, TargetReport, VersionStamp,
)

LISTING_ENDPOINTS = ("detail", "inspection", "record", "diagnosis")
STATUS_KINDS = ("ok", "empty", "not_found", "error", "not_requested")


def _labels(root: str = ".") -> dict:
    with open(f"{root}/config/labels.json", encoding="utf-8") as f:
        return json.load(f)


def _stamp(conn, lid: str, calc_version: str) -> VersionStamp:
    row = conn.execute(
        "SELECT l.parse_version, s.dict_version, s.calc_version, s.calculated_at "
        "FROM core_listing l LEFT JOIN result_score s "
        "ON s.listing_id = l.listing_id AND s.calc_version = ? "
        "WHERE l.listing_id = ?", (calc_version, lid)).fetchone()
    coef = conn.execute(
        "SELECT id, after_value FROM coefficient_history "
        "WHERE target_key = (SELECT target_key FROM core_listing WHERE listing_id=?) "
        "ORDER BY changed_at DESC LIMIT 1", (lid,)).fetchone()
    return VersionStamp(row[0] if row else None, row[1] if row else None,
                        calc_version, coef[1] if coef else None,
                        coef[0] if coef else None, row[3] if row else None)


def _curve_points(year_month: str | None, as_of: str | None,
                  root: str = ".") -> tuple:
    """감가 곡선 + 이 차의 자리 (시안 v2_why .curve).

    ★ 기대가가 어떻게 나왔는지를 보여 준다.  시세차 숫자만 내면 근거가 없다
    """
    import json as _j
    import os as _o

    path = _o.path.join(root, "config", "depreciation.json")
    if not _o.path.isfile(path):
        return ()
    with open(path, encoding="utf-8") as f:
        dep = _j.load(f)
    # 막대의 최대 높이(px).  ★ % 로 주면 안 그려진다 —
    #   .curve .c .bar 는 높이가 정해진 상자의 손자라 백분율이 0 이 된다.
    #   표시 정책이라 config 에 둔다 (S14)
    with open(_o.path.join(root, "config", "web.json"), encoding="utf-8") as f:
        max_px = int(_j.load(f)["curve_max_px"])
    curve = dep.get("curve") or {}
    if not curve:
        return ()
    years = sorted(int(k) for k in curve)
    # ★ 지금 시각을 읽지 않는다.  판정한 시각(calculated_at)을 쓴다 —
    #   그래야 화면의 곡선과 판정이 같은 기준이 된다
    from analyze.axis._util import months_between

    months = months_between(year_month, as_of)
    mine = None
    if months is not None:
        age = months // MONTHS_PER_YEAR
        mine = age if age in years else (years[-1] if age > years[-1] else None)
    top = max(float(curve[str(y)]) for y in years) or 1.0
    return tuple({"year": y, "rate": float(curve[str(y)]),
                  "pct": round(float(curve[str(y)]) / top * 100),
                  "px": round(float(curve[str(y)]) / top * max_px),
                  "now": y == mine}
                 for y in years)


MONTHS_PER_YEAR = 12


def _encar_url(source_id: str, root: str = ".") -> str:
    """엔카 원문 주소 (STEP 149q).  ★ 주소를 코드에 박지 않는다 (config/web.json)."""
    import json as _j
    import os as _o

    with open(_o.path.join(root, "config", "web.json"), encoding="utf-8") as f:
        return str(_j.load(f)["encar_detail_url"]).format(source_id=source_id)


def _why_cheap_of(conn, listing_id: int, root: str) -> tuple:
    """③ 왜 싼가 (개정 299).  ★ 목록은 요약이고 이유는 상세에 둔다 (부록 G).

    ★ 이유를 못 찾으면 그것도 낸다 — 그것이 오히려 위험 신호다
    ★ 화면을 다시 그리지 않는다.  판정 결과와 원문에서 바로 만든다
    """
    from analyze.trust import inspection_source
    from report.why_cheap import verdict as why_verdict
    from store.core import _not_join_months

    row = conn.execute(
        "SELECT l.inspection_formats_json, l.diagnosis_car,"
        " l.warranty_extend, l.warranty_deemed, l.mileage_km,"
        " l.ev_battery_soh, r.accident_my_cnt, r.accident_my_cost,"
        " r.not_join_json, s.grade"
        " FROM core_listing l"
        " LEFT JOIN core_record r ON r.listing_id = l.listing_id"
        " LEFT JOIN result_score s ON s.listing_id = l.listing_id"
        " WHERE l.listing_id = ? LIMIT 1", (listing_id,)).fetchone()
    if row is None:
        return None, []
    fmt = json.loads(row[0]) if row[0] else None
    has_w = bool(row[2] and str(row[2]) != "0") or \
        bool(row[3] and str(row[3]) != "0")
    cfg = _scoring(root)["axis_rules"]["value"]
    got = why_verdict(-1, {
        "inspection_formats": fmt, "diagnosis_car": row[1],
        "has_warranty": has_w, "inspection_source": inspection_source(fmt),
        "rental_note": None,
        "accident_cnt": row[6], "repair_won": row[7],
        "mileage_note": (f"주행 {row[4]:,}km"
                         if row[4] and row[4] >= int(cfg["high_mileage_km"])
                         else None),
        "color_note": None,
        "not_join": _not_join_months(row[8]) or 0,
        "battery_soh": row[5],
        "battery_soh_low": float(cfg["battery_soh_low"]),
    })
    return got[0], list(got[1])


def _scoring(root: str) -> dict:
    import os

    with open(os.path.join(root, "config", "scoring.json"),
              encoding="utf-8") as f:
        return json.load(f)


def _penalty_rows(raw) -> tuple:
    """뺀 것 → 화면 행 (개정 322).  ★ 무엇을 왜 뺐는지가 보여야 한다."""
    if not raw:
        return ()
    try:
        got = json.loads(raw)
    except (ValueError, TypeError):
        return ()
    return tuple({"key": k, "points": p, "label": w} for k, p, w in got)


def _market_pos(conn, listing_id: int, root: str = ".") -> dict:
    """이 차가 시세 분포의 어디인가 (개정 340 · V11-119).

    ★ 「−13.0%」만 내면 그것이 싼 것인지 감이 안 온다.
      분포 위의 자리를 보면 눈으로 안다
    ★ 표본이 모자라면 내지 않는다.  왜 없는지를 적는다 (개정 325)
    """
    import json as _j

    with open(f"{root}/config/web.json", encoding="utf-8") as f:
        need = int(_j.load(f)["market_min_sample"])
    key = conn.execute(
        "SELECT target_key, trim_badge, substr(year_month,1,4),"
        " price_current_won FROM core_listing WHERE listing_id=?",
        (listing_id,)).fetchone()
    if not key or not all(key[:3]) or key[3] is None:
        return {"why": "차종·트림·연식이나 가격이 없어 분포를 못 냅니다"}
    prices = [r[0] for r in conn.execute(
        "SELECT price_current_won FROM core_listing"
        " WHERE status='active' AND price_current_won IS NOT NULL"
        " AND target_key=? AND trim_badge=? AND substr(year_month,1,4)=?"
        " AND (advertisement_type IS NULL OR advertisement_type='NORMAL')"
        " ORDER BY price_current_won", key[:3])]
    if len(prices) < need:
        return {"why": f"같은 조건 매물이 {len(prices)}건뿐입니다 "
                       f"— {need}건 미만이라 분포를 내지 않습니다"}
    low, high, mine = prices[0], prices[-1], key[3]
    mid = prices[len(prices) // 2]
    span = high - low
    if not span:
        # ★ 전부 같은 값이면 분포가 없다.  가운데에 점을 찍으면
        #   「가운데쯤이다」로 읽혀 없는 뜻이 생긴다
        return {"why": f"같은 조건 {len(prices)}건이 모두 "
                       f"{low:,}원이라 분포가 없습니다"}

    def at(v):
        return round((v - low) * 100 / span)

    return {"low": low, "high": high, "mid": mid, "mine": mine,
            "count": len(prices),
            "mine_pct": max(0, min(at(high), at(mine))), "mid_pct": at(mid),
            "cheaper": sum(1 for p in prices if p < mine)}


def _site_badge(site, sell_type, root: str = ".") -> str:
    """사이트 배지.  ★ report/screens/build 와 같은 하나를 쓴다 (V4-21)."""
    from report.screens.build import site_badge

    return site_badge(site, sell_type, root)


def _axis_why(source: str, site: str, axis: str, root: str) -> str:
    """축이 0점인 사유를 사람 말로 (개정 306).

    ★ 「우리가 못 받았다」와 「그 사이트가 아예 안 준다」는 다르다.
      뒤는 우리 잘못이 아니고, 사람이 「그럼 다른 사이트에서 찾아볼까」를 한다
    """
    import json as _j
    import os as _o

    from contracts import SITE_UNAVAILABLE
    from store.crosssite import active_sites

    if source != SITE_UNAVAILABLE:
        return ""
    with open(_o.path.join(root, "config", "sites.json"),
              encoding="utf-8") as f:
        cfg = _j.load(f)
    mine = (cfg.get(site) or {}).get("label") or site
    # ★ 쓰는 사이트만 안내한다.  아직 안 쓰는 사이트를 대안이라 하면
    #   「거기 가서 보십시오」가 거짓말이 된다
    others = sorted(
        (cfg[name].get("label") or name)
        for name in active_sites(cfg)
        if name != site
        and axis not in (cfg[name].get("axes_not_provided") or []))
    tail = (f"  {' · '.join(others)} 매물은 확인할 수 있습니다."
            if others else "  다른 사이트를 붙이면 확인할 수 있습니다.")
    return f"{mine}는 이 값을 제공하지 않습니다.{tail}"


def _photo_urls(photos_json, root: str) -> tuple:
    """상세에 낼 사진 전부 (개정 375).

    ★ 우리가 내려받지 않는다 — ci.encar.com 을 직접 참조한다 (개정 274)
    """
    import json as _j
    import os as _o

    from report.screens.build import photo_urls

    with open(_o.path.join(root, "config", "web.json"), encoding="utf-8") as f:
        base = _j.load(f)["photo_base_url"]
    # ★ 번호를 여기서 붙인다.  템플릿 엔진에 loop.index 가 없다 —
    #   없는 것을 쓰면 앵커가 전부 id="p" 가 되어 :target 이 안 듣는다
    return tuple({"n": i, "url": u}
                 for i, u in enumerate(photo_urls(photos_json, base), 1))


def _purchase_costs(conn, listing_id: int, site, price_won, target_key,
                    fin_cfg: dict, root: str) -> tuple:
    """⑨ 비용 — 사이트별 총액 (부록 G 상세 ⑨ · 개정 353 · V11-120 · V11-121).

    ★ 여러 사이트에 같은 차가 있으면 나란히 낸다.
      표시가가 싼 쪽이 실제로 싼 쪽이 아닐 수 있다
    ★ 사이트가 총액을 주면 그것을 쓴다.  지금은 K카 파서가 없어 못 받는다 —
      못 받으면 계산하고 「추정」이라 적는다 (개정 353 [판단])
    """
    import os as _o

    from report.finance import purchase_cost
    from store.crosssite import load_sites, site_prices_of

    if not site:
        return ()
    sites = load_sites(_o.path.join(root, "config", "sites.json"))
    out = []
    mine = purchase_cost(site, price_won, fin_cfg, sites, target_key)
    if mine:
        out.append(mine)
    for other, other_price in site_prices_of(conn, listing_id):
        got = purchase_cost(other, other_price, fin_cfg, sites, target_key)
        if got:
            out.append(got)
    return tuple(out)


def render_listing(conn: sqlite3.Connection, listing_id: int,
                   calc_version: str, fin_cfg: dict, policy: dict,
                   root: str = ".") -> ScoreView:
    """L1 — 왜 이 점수인가.  축별 source · prio 를 반드시 낸다."""
    lab = _labels(root)["AXIS_LABELS"]
    _why = _why_cheap_of(conn, listing_id, root)
    head = conn.execute(
        "SELECT l.target_key, l.price_current_won, s.score_total, s.denominator,"
        " s.earned, s.not_rated_reason,"
        " s.grade, s.absolute_fail, l.source_id, l.year_month,"
        " s.calculated_at,"
        # 개정 322 · 325 — 뺀 것 · 근거가 있는 축의 배점 합
        " s.grade_earned, s.grade_base, s.confirmed_points, s.penalties_json,"
        # 사이트 배지 (50-multisite · V9-06) — 상세에도 출처를 낸다
        " l.site, l.sell_type,"
        # 상세 사진 (개정 375).  ★ 대표 하나가 아니라 전부다
        " l.photo_list_json,"
        # 가점 (개정 380) · 전기차인가 — 「배터리 진단 없음」을 낼지 정한다
        " s.bonuses_json, l.ev_battery_known"
        " FROM core_listing l "
        "LEFT JOIN result_score s ON s.listing_id=l.listing_id "
        "AND s.calc_version=? WHERE l.listing_id=?",
        (calc_version, listing_id)).fetchone()
    if head is None:
        raise KeyError(listing_id)

    axes, pending = [], []
    for axis, value, source, prio, excluded, mx, score in conn.execute(
        "SELECT axis, value, source, prio, excluded, max_points, score "
        "FROM result_axis WHERE listing_id=? AND calc_version=? ORDER BY axis",
        (listing_id, calc_version)
    ):
        axes.append(AxisView(axis, lab.get(axis, axis), value,
                             float(score or (value or 0)), int(mx or 0),
                             bool(excluded), source, prio,
                             why=_axis_why(source, head[15], axis, root)))
        if excluded and source in ("gate_closed", "coefficient_out_of_range",
                                   "rule_undefined", "catalog_missing",
                                   "not_provided"):
            # ★ 「무엇이 · 몇 점 · 왜」를 함께 낸다.  축 이름만 내면
            #   채우면 얼마나 오르는지 알 수 없다 (STEP 149h · D-1)
            pending.append({
                "axis": axis, "label": lab.get(axis, axis),
                "points": int(mx or 0),
                "reason": EXCLUDE_REASONS.get(source, source),
                "source": source,
            })

    return ScoreView(
        listing_id=listing_id, target_key=head[0], grade=head[6] or "NOT_RATED",
        score_total=float(head[2] or 0), earned=float(head[4] or 0),
        denominator=float(head[3] or 0),
        absolute_fail=head[7], not_rated_reason=head[5], axes=axes,
        versions=_stamp(conn, listing_id, calc_version),
        # ★ 값이 어느 사이트 원문에서 왔는지 사람이 알아야 한다
        site_badge=_site_badge(head[15], head[16], root),
        # 시세 위치 — 「3,100만 ─── ● 4,550만 ─── 6,000만」 (개정 340)
        market_pos=_market_pos(conn, listing_id, root),
        finance=build_finance(head[1], fin_cfg, head[0]),
        pending_items=tuple(pending), component_count=len(axes),
        grade_earned=float(head[11] or 0), grade_base=float(head[12] or 0),
        # ★ 「안 받아서 0점」은 확인한 것이 아니다 (개정 325)
        confirmed_points=float(head[13] or 0),
        confirm_pct=(round(float(head[13] or 0) / float(head[3]) * 100, 1)
                     if head[3] else 0.0),
        penalties=_penalty_rows(head[14]),
        penalty_total=sum(p["points"] for p in _penalty_rows(head[14])),
        # ★ 가점 (개정 380).  없으면 「배터리 진단 없음」을 낸다
        bonuses=_penalty_rows(head[18]),
        bonus_total=sum(b["points"] for b in _penalty_rows(head[18])),
        ev=bool(head[19]),
        # ★ 「싸다」를 말할 때 「왜 싼가」를 함께 낸다 (개정 299 · 부록 G ③)
        why_cheap=_why[0], why_cheap_reasons=tuple(_why[1]),
        # ★ 채웠을 때 어디까지 오르는지 낸다 (STEP 149h · D-2).
        #   「점수는 낮은데 확실한 것」과 「높은데 불확실한 것」을 가른다
        pending_best=_pending_best(pending, float(head[4] or 0),
                                   float(head[3] or 0), policy),
        diagnosis=_diagnosis_view(conn, listing_id),
        fetches=_fetch_views(conn, listing_id, axes),
        strengths=_strengths(axes), weaknesses=_weaknesses(axes),
        costs=_cost_rows(head[1], build_finance(head[1], fin_cfg, head[0])),
        # ⑨ 비용 — 사이트별 총액 (개정 353).  ★ 점수에 넣지 않는다
        purchase_costs=_purchase_costs(conn, listing_id, head[15],
                                       head[1], head[0], fin_cfg, root),
        # ★ 5절 주요 옵션 — 옵션별 탑재 여부 (STEP 149c)
        options=_option_rows(conn, listing_id),
        known_issues=_known_issues(head[0], root),
        source_id=head[8],
        # ★ 상세는 사진을 전부 낸다 (개정 375).  주소는 config 가 갖는다
        photos=_photo_urls(head[17], root),
        curve=_curve_points(head[9], head[10], root),
        # ★ source_id 가 없으면 링크를 만들지 않는다.  깨진 주소를 내지 않는다
        encar_url=(_encar_url(head[8], root) if head[8] else None))


# 왜 분모에서 빠졌는가.  ★ 코드가 아니라 사람 말로 낸다 (STEP 149h)
EXCLUDE_REASONS = {
    "gate_closed": "판정 조건이 아직 정해지지 않았습니다",
    "coefficient_out_of_range": "감가 계수가 범위를 벗어났습니다",
    "rule_undefined": "이 차종의 판정 규칙이 없습니다",
    "catalog_missing": "카탈로그를 받지 못했습니다",
    "not_provided": "사이트가 이 값을 주지 않았습니다",
}


# 화면에 낼 옵션 묶음.  ★ 「기본」과 「선택」을 가른다 —
# 선택 옵션은 돈을 더 낸 것이라 값이 다르다 (STEP 149c)
OPTION_GROUPS = (("options_choice_json", "선택 옵션"),
                 ("options_standard_json", "기본 옵션"),
                 ("options_etc_json", "기타"),
                 ("options_tuning_json", "튜닝"))


def _option_rows(conn: sqlite3.Connection, listing_id: int) -> tuple:
    """주요 옵션 — 옵션별 탑재 여부 (STEP 149c 5절).

    ★ 코드만 내면 사람이 못 읽는다.  사전에 이름이 있으면 붙인다 —
      없으면 코드를 그대로 낸다.  추정으로 이름을 만들지 않는다
    """
    cols = ", ".join(c for c, _lb in OPTION_GROUPS)
    row = conn.execute(
        f"SELECT {cols} FROM core_listing WHERE listing_id = ?",
        (listing_id,)).fetchone()
    if row is None:
        return ()
    names = {code: display for code, display in conn.execute(
        "SELECT code, display FROM dict_option_code")}
    out = []
    for (col, label), blob in zip(OPTION_GROUPS, row, strict=True):
        try:
            codes = json.loads(blob or "[]")
        except (TypeError, ValueError):
            codes = []
        if not codes:
            continue
        out.append({
            "group": label, "count": len(codes),
            "items": [{"code": c, "name": names.get(c) or c,
                       "known": c in names} for c in codes],
        })
    return tuple(out)


# 무엇을 조회했는가 (STEP 149 · 시안 v2_why).
# ★ 「안 부른 것」과 「불렀는데 못 받은 것」은 다르다 —
#   전자는 우리 잘못이고 후자는 그 매물에 없는 것이다
FETCH_LABELS: dict[str, tuple[str, str]] = {
    "detail": ("상세", "가격 · 보증 · 사양 · 색상"),
    "inspection": ("성능점검기록부", "사고 부위 · 상태 · 렌트 이력"),
    "record": ("자동차이력정보", "보험처리액 · 번호판 이력"),
    "catalog": ("카탈로그", "HDA 등급"),
    "diagnosis": ("엔카 자체진단", "외판 부위별 판정"),
}
STATUS_LABEL = {"ok": "받음", "not_found": "없음"}
NOT_REQUESTED = "미조회"
# 그 응답이 없으면 막히는 축.  ★ 사람이 「무엇을 채우면 오르나」를 안다
FETCH_IMPACT = {
    "catalog": "사양 축 판정 불가",
    "diagnosis": "이 매물은 미진단",
    "inspection": "사고 · 렌트 판정 불가",
    "record": "보험 판정 불가",
}


def _fetch_views(conn: sqlite3.Connection, listing_id: int,
                 axes: list) -> tuple:
    """★ 조회 상태를 낸다.  판정의 근거가 어디서 왔는지가 먼저다 (G-1)."""
    got = {ep: st for ep, st in conn.execute(
        "SELECT endpoint, status FROM raw_response WHERE listing_id = ?",
        (listing_id,))}
    out = []
    for ep, (label, gives) in FETCH_LABELS.items():
        st = got.get(ep)
        status = STATUS_LABEL.get(st, NOT_REQUESTED) if st else NOT_REQUESTED
        impact = FETCH_IMPACT.get(ep) if status != "받음" else None
        out.append(FetchView(ep, label, status, gives, impact))
    return tuple(out)


def _strengths(axes: list) -> tuple:
    """만점을 받은 축.  ★ 「왜 이 순위인가」의 앞쪽이다."""
    return tuple(a.label for a in axes
                 if not a.excluded and a.max_points
                 and a.points >= a.max_points)


def _weaknesses(axes: list) -> tuple:
    """절반 미만인 축.  ★ 0 점만 보면 「아깝게 깎인 것」이 안 보인다."""
    return tuple(f"{a.label} {a.points:g}/{a.max_points:g}" for a in axes
                 if not a.excluded and a.max_points
                 and a.points * 2 < a.max_points)


def _pending_best(pending: list, earned: float, denom: float,
                  policy_raw: dict) -> dict | None:
    """확인 못 한 축을 다 채웠을 때의 비율·등급 (STEP 149h · D-2).

    ★ 낙관값이다 — 「최대 이만큼」이라고 밝혀 쓴다.  단정하지 않는다
    """
    if not pending or not denom:
        return None
    from analyze.axes import ScoringPolicy
    from score.grade import cutoffs

    # ★ 호출자가 dict · ScoringPolicy · 경로 문자열을 다 준다.
    #   여기서 죽으면 /why 가 통째로 안 열린다 — 못 읽으면 조용히 접는다
    if hasattr(policy_raw, "raw"):
        policy = policy_raw
    elif isinstance(policy_raw, dict) and "grade_cuts" in policy_raw:
        policy = ScoringPolicy(policy_raw)
    else:
        return None
    add = sum(p["points"] for p in pending)
    best_denom = denom + add
    best_ratio = (earned + add) / best_denom if best_denom else 0
    grade = "E"
    for g, cut in cutoffs(policy):
        if best_ratio >= cut:
            grade = g
            break
    return {"points": add, "ratio_pct": round(best_ratio * 100, 1),
            "grade": grade,
            "now_pct": round(earned / denom * 100, 1) if denom else 0}


def _cost_rows(price_won, fin) -> tuple:
    """중고 ↔ 신차 동일 트림.  ★ 점수에 반영하지 않는다 (시안 v2_why)."""
    if fin is None or price_won is None:
        return ()
    rows = [CostRow("차량가", int(price_won), getattr(fin, "new_price_won",
                                                   None))]
    for label, used, new in (
        ("취득세·등록비", getattr(fin, "registration_won", None),
         getattr(fin, "new_registration_won", None)),
        ("할부 원금", getattr(fin, "loan_principal_won", None),
         getattr(fin, "new_loan_principal_won", None)),
        ("월 할부", getattr(fin, "monthly_won", None),
         getattr(fin, "new_monthly_won", None)),
        ("총 이자", getattr(fin, "total_interest_won", None),
         getattr(fin, "new_total_interest_won", None)),
    ):
        if used is not None or new is not None:
            rows.append(CostRow(label, used, new))
    return tuple(rows)


def _known_issues(target_key: str, root: str) -> tuple:
    """차종 공통 알려진 문제.

    ★ 사람이 넣는다.  수집으로 채우지 않는다 — 출처가 커뮤니티·리콜 공고다.
      점수에 반영하지 않는다 (참고 자료다)
    """
    import json as _j
    import os as _o

    path = _o.path.join(root, "config", "known_issues.json")
    if not _o.path.isfile(path):
        return ()
    with open(path, encoding="utf-8") as f:
        data = _j.load(f)
    items = data.get(target_key) or []
    return tuple(items if isinstance(items, list) else [])


def _diagnosis_view(conn: sqlite3.Connection, listing_id: int):
    """★ 표시용이다.  점수에 반영하지 않는다 (STEP 21b).

    없으면 None — 「진단 안 받은 차」다.  화면이 그렇게 표시한다
    """
    from store.core import diagnosis_of

    row = diagnosis_of(conn, listing_id)
    return DiagnosisView(**row) if row else None


def render_target(conn: sqlite3.Connection, target_key: str, run_id: str,
                  calc_version: str, fin_cfg: dict, policy: dict,
                  top_n: int | None = None, root: str = ".") -> TargetReport:
    """L2 — 어느 축이 갈리는가.  「값 종류 수」를 반드시 낸다.

    top_n 은 표본 수라 config 다.  코드에 박지 않는다 (V4-13).
    """
    if top_n is None:
        top_n = int(policy["report"]["top_n"])
    n = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE target_key=?",
        (target_key,)).fetchone()[0]
    rates, counts = {}, {}
    for ep in LISTING_ENDPOINTS:
        c = {k: 0 for k in STATUS_KINDS}
        for st, m in conn.execute(
            f"SELECT {ep}_status, COUNT(*) FROM core_listing WHERE target_key=? "
            f"GROUP BY {ep}_status", (target_key,)):
            if st:
                c[st] = m
        counts[ep] = c
        rates[ep] = (c["ok"] / n) if n else 0.0

    cls = {r[0]: r[1] for r in conn.execute(
        "SELECT classify_stage, COUNT(*) FROM core_listing WHERE target_key=? "
        "GROUP BY classify_stage", (target_key,))}
    conf = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE target_key=? AND "
        "classify_conflict=1", (target_key,)).fetchone()[0]

    prices = [r[0] for r in conn.execute(
        "SELECT price_current_won FROM core_listing WHERE target_key=? "
        "AND price_current_won IS NOT NULL ORDER BY price_current_won",
        (target_key,))]
    med = prices[len(prices) // 2] if prices else 0
    coef = conn.execute(
        "SELECT id, after_value FROM coefficient_history WHERE target_key=? "
        "ORDER BY changed_at DESC LIMIT 1", (target_key,)).fetchone()

    stats, warns = [], []
    for axis, avg, dv, ex, tot, mx in conn.execute(
        "SELECT a.axis, AVG(a.value), COUNT(DISTINCT a.value), SUM(a.excluded),"
        " COUNT(*), MAX(a.max_points) FROM result_axis a "
        "JOIN core_listing l ON l.listing_id=a.listing_id "
        "WHERE l.target_key=? AND a.calc_version=? GROUP BY a.axis",
        (target_key, calc_version)
    ):
        src = {r[0]: r[1] for r in conn.execute(
            "SELECT a.source, COUNT(*) FROM result_axis a "
            "JOIN core_listing l ON l.listing_id=a.listing_id "
            "WHERE l.target_key=? AND a.axis=? AND a.calc_version=? "
            "GROUP BY a.source", (target_key, axis, calc_version))}
        stats.append(AxisStat(axis, float(avg or 0), int(mx or 0), dv,
                              (ex or 0) / tot if tot else 0.0, src))
        if dv <= 1:
            warns.append(f"{axis}: 값 종류 {dv} — 순위에 기여하지 않는다 (V3-04)")

    grades = {r[0]: r[1] for r in conn.execute(
        "SELECT s.grade, COUNT(*) FROM result_score s "
        "JOIN core_listing l ON l.listing_id=s.listing_id "
        "WHERE l.target_key=? AND s.calc_version=? GROUP BY s.grade",
        (target_key, calc_version))}
    top_ids = [r[0] for r in conn.execute(
        "SELECT s.listing_id FROM result_score s "
        "JOIN core_listing l ON l.listing_id=s.listing_id "
        "WHERE l.target_key=? AND s.calc_version=? AND s.grade<>'NOT_RATED' "
        "ORDER BY s.score_total DESC LIMIT ?", (target_key, calc_version, top_n))]

    return TargetReport(
        meta=ReportMeta(run_id, "L2", "encar", target_key, calc_version, None),
        collect=CollectSummary(n, rates, counts),
        classify=ClassifySummary(cls.get("provisional", 0),
                                 cls.get("confirmed", 0), conf),
        price=PriceSummary(med, 0, coef[1] if coef else None,
                           coef[0] if coef else None, {}),
        axes=stats, grades=grades,
        top=[render_listing(conn, i, calc_version, fin_cfg, policy, root)
             for i in top_ids],
        warnings=warns)


def render_run(conn: sqlite3.Connection, run_id: str,
               calc_version: str) -> RunReport:
    """L3 — 수집·검증이 정상인가.

    ★ steps 는 화면이 필드로 읽는다.  튜플로 두면 조용히 빈다 (C-3)
    """
    checks = conn.execute(
        "SELECT phase, code, expected, actual, passed, severity, samples "
        "FROM audit_validation WHERE run_id=? AND phase LIKE 'V%' "
        "ORDER BY phase, code", (run_id,)).fetchall()
    steps = conn.execute(
        "SELECT code, expected, actual, passed FROM audit_validation "
        "WHERE run_id=? AND code LIKE 'STEP53-%' ORDER BY rowid",
        (run_id,)).fetchall()
    coefs = [CoefficientChange(r[0], r[1], r[2], r[3], r[4], r[5])
             for r in conn.execute(
                 "SELECT target_key, before_value, after_value, sample_size,"
                 " reason, changed_at FROM coefficient_history")]
    dc = {r[0]: r[1] for r in conn.execute(
        "SELECT status, COUNT(*) FROM dict_enum GROUP BY status")}
    by_axis = {r[0]: r[1] for r in conn.execute(
        "SELECT axis, COUNT(*) FROM dict_enum GROUP BY axis")}
    un = conn.execute(
        "SELECT COUNT(*) FROM meta_field_usage WHERE usage='unclassified'"
    ).fetchone()[0]
    steps = [RunStep(step=s[0], expected=s[1],
                     requested=_j(s[2], "requested"), ok=_j(s[2], "ok"),
                     not_found=_j(s[2], "not_found"),
                     error=_j(s[2], "error"),
                     halted=not bool(s[3]))
             for s in steps] if steps and isinstance(steps[0], tuple) \
        else steps
    return RunReport(
        meta=ReportMeta(run_id, "L3", "encar", None, calc_version, None),
        steps=steps, checks=checks, day_gap=None,
        coefficient_changes=coefs,
        dict_changes=DictChangeSummary(dc.get("pending", 0),
                                       dc.get("confirmed", 0),
                                       dc.get("retired", 0), by_axis),
        unclassified_count=un)


def render_halt(conn: sqlite3.Connection, run_id: str, calc_version: str,
                blocked: list, reports: list, artifacts=None) -> HaltReport:
    """L0 — 실패가 아니라 「다음 행동」을 내는 리포트다 (STEP 90).

    completed_steps 를 반드시 낸다.  처음부터 다시 도는 것이 아님을 알 수 있어야 한다.
    """
    halted = [r for r in reports if r.halted]
    return HaltReport(
        meta=ReportMeta(run_id, "L0", "encar", None, calc_version, None),
        halted_step=halted[0].step if halted else "",
        halted_at=None,
        failures=list(blocked),
        actions={r.check.code: r.check.action for r in blocked},
        completed_steps=[r for r in reports if not r.halted],
        artifacts=list(artifacts or []),
        versions=VersionStamp(None, None, calc_version, None, None, None))


def _j(blob, key: str) -> int:
    """단계 집계 JSON 에서 한 값.  ★ 없으면 0 이다 — 추정하지 않는다."""
    import json as _json

    try:
        return int(_json.loads(blob or "{}").get(key) or 0)
    except (TypeError, ValueError):
        return 0
