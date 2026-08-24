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
import re
import os
import sqlite3
from urllib.parse import quote, urlencode

from dataclasses import replace

from report.finance import build_finance, purchase_cost

# sites.json 은 한 요청 안에서 안 바뀐다.  root 별로 한 번만 읽는다
_SITES_CACHE: dict = {}

# 리포트 계층 이름 (STEP 91).  ★ 코드가 아니라 사람 말로 낸다
REPORT_LAYERS = {"L1": "매물 리포트", "L2": "차종 리포트", "L3": "실행 리포트"}
from report.render import render_listing, render_run
from analyze.trust import SOURCE_WORDS, inspection_source, platform_trust
from report.why_cheap import verdict as why_verdict
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
    RelaxRow, ReportFile, ReportsView,
    WatchRow,
    TargetStat, ViewerState,
)
from report.views import AxisView, ReportMeta, VersionStamp
from contracts import ROLE_ADMIN, ROLE_USER, Account, require_role
# ★ 어긋남 조건은 store 에 하나만 둔다 (V3-50).  화면이 SQL 을 짓지 않는다
from store.core import record_mismatch_sql, relist_counts

NOT_RATED = "NOT_RATED"
# 분위수는 표시 파라미터다.  config 가 정본이며 여기 값은 호출측 미지정 시 대체다
MARKET_QUANTILES = (0.25, 0.50, 0.75)
GONE = "gone"

# 목록에 띄우는 축 요약 (STEP 97).  Component 이름을 쓴다
# 목록에 좁은 칸으로 세우는 축.  ★ v1 원본이 정본이다 (STEP 149o · 개정 277)
# v1 22열 — 사고 · 골격 · 수리비 · 용도 · 보증 · 트림 · 옵션 · HUD · 선루프.
# ★ 개정 292 로 축이 다시 짜였다.  상태(180)가 사양(75)보다 크다 —
#   마스터 지적 「깡통에 HUD 만 있어도 만점」이 이 순서로 뒤집힌다
# ★ 한 칸에 몰아넣으면 「이 차만 사고가 있다」가 세로로 안 보인다
# ★ 부록 G 의 목록 열 14~17 이다 (개정 332).
#   35열을 늘어놓으면 「고를 것을 좁힌다」가 안 된다 — 상세로 보낸다
# ★★ 목록 카드의 ★ **판정 다섯** (v3_listings_시안 · 마스터 확정 열셋 · 명령서 1b).
#   ★ 사고 · 골격 · 용도 · 제조사 보증 · **사이트 보증**
#   ★★ 실측 08-24 — ★ 넷뿐이라 ★ 「사이트 보증」이 빠져 있었다.
#     ★ ★ 그래서 ★ 마스터가 ★ 목록에서 ★ 무엇이 좋은 매물인지 못 보셨다 (오판 100)
CHIP_AXES = ("state.accident", "state.frame", "history.use",
             "warranty.power", "warranty.site")


def site_badge(site: str | None, sell_type: str | None,
               root: str = ".") -> str:
    """사이트 배지 — 「엔카」 · 「K카 직영」 · 「K카 직거래」 (50-multisite).

    ★ 사이트 이름을 코드에 박지 않는다.  config/sites.json 이 정본이다
    ★ 판매 유형을 함께 내는 사이트만 낸다.  엔카의 sell_type 은
      「일반·렌트·리스」로 용도지 판매 유형이 아니다 —
      그것을 붙이면 「엔카 렌트」가 배지가 된다
    """
    with open(f"{root}/config/sites.json", encoding="utf-8") as f:
        sites = json.load(f)
    one = sites.get(site or "")
    if not isinstance(one, dict):
        return str(site or "")
    label = one.get("label") or str(site)
    kinds = one.get("sell_type_labels") or {}
    tail = kinds.get(str(sell_type or "").strip())
    return f"{label} {tail}" if tail else label


def axis_heads(root: str = ".") -> list[dict]:
    """목록 축 열의 머리말.  ★ 문구를 화면에 박지 않는다 (STEP 91 · V6-02)."""
    al = _labels(root)["AXIS_LABELS"]
    return [{"axis": a, "label": al.get(a, a)} for a in CHIP_AXES]

import os as _os_lbl
_ROOT_LBL = _os_lbl.path.dirname(_os_lbl.path.dirname(
    _os_lbl.path.dirname(_os_lbl.path.abspath(__file__))))


def _grade_order() -> tuple:
    """등급 차례.  ★ 정본은 config/labels.json GRADE_ORDER 다 (개정 433).

    ★ 여기에 ("S","A","B","C","D","E") 를 박지 않는다 — 개정 433 이 8단계로
      내렸을 때 이 튜플이 세 모듈에 흩어져 있어 전수로 찾아야 했다 (S14)
    """
    import json as _j
    import os as _o
    _p = _o.path.join(_ROOT_LBL, "config", "labels.json")
    with open(_p, encoding="utf-8") as _f:
        return tuple(_j.load(_f)["GRADE_ORDER"])


def _not_ranked() -> tuple:
    """순위를 안 매기는 것 — 제외 · 등급 없음 · 평가 불가 (개정 433)."""
    import json as _j
    import os as _o
    _p = _o.path.join(_ROOT_LBL, "config", "labels.json")
    with open(_p, encoding="utf-8") as _f:
        return tuple(_j.load(_f)["GRADE_NOT_RANKED"])


RANK_ORDER = _grade_order()
NOT_RANKED = _not_ranked()



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


def _unknown_cfg() -> dict:
    """「모름」의 정본 — config/unknown_split.json (개정 435).

    ★ 코드에 source 이름을 박지 않는다 (S14)
    """
    import json as _j
    with open(_os_lbl.path.join(_ROOT_LBL, "config", "unknown_split.json"),
              encoding="utf-8") as _f:
        return _j.load(_f)


def is_unknown(source: str | None) -> bool:
    """그 source 가 「확인 안 됨」인가 (개정 435).

    ★★ 「없다고 확인한 것」이 먼저다 — no_warranty 는 「보증이 없음을
      확인한 것」이지 「모르는 것」이 아니다
    """
    cfg = _unknown_cfg()
    src = str(source or "")
    if src in cfg["confirmed_absent_sources"]:
        return False
    if src in cfg["unknown_sources"]:
        return True
    # ★ 축이 사유를 이어 붙인 것 — 「integrity_계기판 확인 못 함」
    return any(w in src for w in cfg["unknown_source_marks"])


def chip(axis: str, value: int | None, excluded: bool, labels: dict,
         base: str = "/listings", source: str | None = None) -> AxisChip:
    """전 화면이 같은 문구를 쓴다.  화면마다 다르게 쓰지 않는다 (V6-02)."""
    vl = labels["VALUE_LABELS"]
    al = labels["AXIS_LABELS"]
    if value is None and excluded:
        label, tone, bucket = vl["unknown"], TONE_UNKNOWN, "unknown"
    elif value == -1 and excluded:
        label, tone, bucket = vl["na"], TONE_MUTED, "na"
    elif value is None:
        label, tone, bucket = vl["unknown"], TONE_UNKNOWN, "unknown"
    # ★★ 개정 435 — 「확인 안 됨」은 value 가 아니라 source 에 있다.
    #   ★ 전에는 여기가 없어서 source='missing' 15,709건이 「· 없음」으로
    #     나갔다.  바로 아래 :159 에 「v1 사고가 되풀이된다」고 적어 두고서다
    elif is_unknown(source):
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
    return AxisChip(axis, text, tone, url, head=al.get(axis, axis), mark=mark,
                    # ★ 관문에 걸린 것은 붉게 (개정 427 상세 ④절)
                    blocked=(tone == TONE_BAD))


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
    # ★ source · max_points 도 같은 쿼리로 싣는다.  쿼리를 늘리지 않는다 (V11-34)
    #   source  렌트를 어디서 찾았는가 (개정 302)
    #   max_points  확인율 「555 중 350점 확인」 (개정 298 I)
    for lid, axis, value, excluded, source, mx in conn.execute(
        f"SELECT listing_id, axis, value, excluded, source, max_points "
        f"FROM result_axis WHERE calc_version = ? AND listing_id IN ({marks})",
        (calc_version, *lids)
    ):
        out.setdefault(lid, {})[axis] = (value, bool(excluded), source, mx)
    return out


def confirm_ratio(got: dict, total: float) -> tuple:
    """확인율 — 「555 중 350점을 확인했습니다 (63%)」 (개정 298 I).

    ★ 분모로 등급을 막지 않는다.  대신 얼마나 확인했는지를 화면에 낸다
    """
    seen = sum(float(v[3] or 0) for v in got.values() if not v[1])
    # ★ 배점은 정수다.  「550.0점」이 아니라 「550점」으로 낸다
    return (int(seen) if seen == int(seen) else seen,
            seen / total if total else 0.0)


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



def photo_urls(photos_json: str | None, base: str) -> list:
    """사진 전부 (개정 375).  ★ 순서대로.  ★ 우리가 내려받지 않는다.

    ★ 상세는 「최대한 모든 정보」다.  대표 하나만 내면 실물을 못 본다 —
      마스터 지적 「목록은 간략하게 상세는 최대한 모든 정보가 들어가야 한다」
    ★ 엔카는 33장까지 준다.  상한을 두지 않는다 — 원문이 주는 만큼 낸다
    """
    if not photos_json:
        return []
    try:
        photos = json.loads(photos_json)
    except (ValueError, TypeError):
        return []
    if not isinstance(photos, list):
        return []
    got = []
    for p in photos:
        if not isinstance(p, dict):
            continue
        loc = p.get("location")
        if not loc or not str(loc).startswith("/"):
            continue
        try:
            o = float(p.get("ordering"))
        except (TypeError, ValueError):
            o = float("inf")       # 순서를 모르면 맨 뒤 — 있는 것을 버리지 않는다
        got.append((o, f"{base}{loc}"))
    got.sort(key=lambda x: x[0])
    # 같은 주소가 두 번 오면 한 번만 — 화면에 같은 사진이 겹친다
    return list(dict.fromkeys(u for _o, u in got))


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


# 개월을 해로 끊는 자리.  ★ 「남은 26개월」보다 「2년 2개월」이 읽힌다
MONTHS_PER_YEAR = 12
# 단위 환산.  ★ 화면 표기를 한 자리에 모은다 (2장 상수표 · V4-13)
WON_PER_MANWON = 10_000

M_PER_KM = 1_000


def _bulk_market(conn, lids: list, root: str = ".") -> dict:
    """같은 차종·트림·연식의 실제 매물 중앙값 (STEP 149n-3 · 개정 283).

    ★ 감가 곡선의 이론가가 아니다.  우리가 가진 매물의 중앙값이다
    ★ 렌트·리스 승계를 뺀다 — 표시가가 인수금이라 중앙값을 끌어내린다
      (실측 08-17: 2023 G80 2.5T AWD 에서 3,990만 → 4,115만)
    ★ 표본이 모자라면 내지 않는다.  「표본 N건」을 함께 낸다
    """
    if not lids:
        return {}
    need = _view_cfg("market_min_sample", root)
    marks = ",".join("?" * len(lids))
    keys = {r[0]: (r[1], r[2], r[3]) for r in conn.execute(
        f"SELECT listing_id, target_key, trim_badge, substr(year_month,1,4)"
        f" FROM core_listing WHERE listing_id IN ({marks})", tuple(lids))}
    want = {k for k in keys.values() if all(k)}
    if not want:
        return {lid: (None, 0) for lid in keys}
    # ★ 조합마다 한 번씩 돌면 한 쪽에 50쿼리다 — 한 번에 받는다 (V11-34).
    #   실측 08-17: 그렇게 했다가 화면 쿼리가 20 → 35 로 늘었다
    groups: dict = {}
    for tk, trim, year, price in conn.execute(
        "SELECT target_key, trim_badge, substr(year_month,1,4),"
        " price_current_won FROM core_listing"
        " WHERE status='active' AND price_current_won IS NOT NULL"
        " AND target_key IS NOT NULL AND trim_badge IS NOT NULL"
        " AND (advertisement_type IS NULL"
        "      OR advertisement_type NOT LIKE '%SUCCESSION%')"
        " ORDER BY target_key, trim_badge, 3, price_current_won"
    ):
        groups.setdefault((tk, trim, year), []).append(price)
    out: dict = {}
    for k in want:
        prices = groups.get(k, [])
        out[k] = ((prices[len(prices) // 2], len(prices))
                  if len(prices) >= need else (None, len(prices)))
    return {lid: out.get(k, (None, 0)) for lid, k in keys.items()}


def _bulk_state(conn, lids: list) -> dict:
    """축 칸에 낼 「상태」의 재료 (STEP 149n · 개정 280).

    ★ 점수를 상태인 것처럼 내지 않는다.  원문에 있는 사실을 그대로 낸다.
      「일반보증은 얼마가 남았는지」 「사고 없으면 무사고라고」 —
      마스터가 물은 것이 그대로 답이다
    ★ 행마다 돌지 않는다.  IN 절 한 번이다 (V11-34)
    """
    if not lids:
        return {}
    marks = ",".join("?" * len(lids))
    out: dict = {}
    for (lid, bm, bkm, pm, pkm, km, ym, soh, sohg) in conn.execute(
        f"SELECT listing_id, warranty_body_month, warranty_body_km,"
        f" warranty_power_month, warranty_power_km, mileage_km, year_month,"
        # ★ 전기차는 SOH 가 주행거리에 해당한다 (개정 296)
        f" ev_battery_soh, ev_battery_grade"
        f" FROM core_listing WHERE listing_id IN ({marks})", tuple(lids)
    ):
        out[lid] = {"warranty": (bm, bkm, pm, pkm, km, ym),
                    "battery": (soh, sohg)}
    for (lid, mycnt, mycost, othcnt, tot, not_join) in conn.execute(
        f"SELECT listing_id, accident_my_cnt, accident_my_cost,"
        f" accident_other_cnt, accident_total_cnt, not_join_json"
        f" FROM core_record WHERE listing_id IN ({marks})", tuple(lids)
    ):
        out.setdefault(lid, {})["record"] = (mycnt, mycost, othcnt, tot)
        # ★ 자차 미가입 기간 — 받아 두고 안 쓰고 있었다 (개정 294 · 299 ⑦).
        #   실측 08-17: 2,243건 중 1,308건(58%)에 기간이 있다
        out[lid]["not_join"] = not_join_months(not_join)
    return out


def not_join_months(raw: str | None) -> int:
    """자차 미가입 개월 수 합 (개정 294).

    원문   ["202412~202502", null, null, null, null]
    ★ 「기간이 있다」가 아니라 「몇 달인가」다 — 1달과 5년은 다른 사실이다
    """
    if not raw:
        return 0
    try:
        spans = [x for x in json.loads(raw) if x]
    except (ValueError, TypeError):
        return 0
    total = 0
    for span in spans:
        got = re.match(r"(\d{4})(\d{2})~(\d{4})(\d{2})", str(span))
        if not got:
            continue
        a = int(got.group(1)) * MONTHS_PER_YEAR + int(got.group(2))
        b = int(got.group(3)) * MONTHS_PER_YEAR + int(got.group(4))
        total += max(0, b - a)
    return total


def _left(total_month, total_km, used_month, used_km):
    """보증 잔여.  ★ 둘 중 하나라도 지나면 만료다 (실제 보증 약관)."""
    if total_month is None:
        return None
    mo = total_month - (used_month or 0)
    km = (total_km or 0) - (used_km or 0)
    return (mo, km)


def _warranty_state(got, as_of) -> tuple:
    """(일반보증, 엔진보증) 상태 문구."""
    from analyze.axis._util import months_between

    bm, bkm, pm, pkm, km, ym = got
    used = months_between(ym, as_of)
    if used is None:
        return ("?", "?")
    out = []
    for tot_m, tot_km in ((bm, bkm), (pm, pkm)):
        got_left = _left(tot_m, tot_km, used, km)
        if got_left is None:
            out.append("?")
            continue
        mo, left_km = got_left
        if mo <= 0 or left_km <= 0:
            out.append("만료")
            continue
        years, rest = divmod(mo, MONTHS_PER_YEAR)
        span = (f"{years}년 {rest}개월" if years and rest
                else f"{years}년" if years else f"{rest}개월")
        out.append(f"{span} · {left_km // M_PER_KM:,}천km")
    return tuple(out)


# 축 → 상태를 어디서 가져오는가 (STEP 149n).
# ★ 여기 없는 축은 기호(O · - · ?)를 그대로 쓴다.  지어내지 않는다
STATE_AXES = ("warranty.general", "warranty.power", "state.accident",
              "state.frame", "state.outer", "state.my_cost", "history.use",
              "history.not_join", "taste.trim", "taste.option",
              "warranty.site")


# 렌트를 어디서 찾았는가 → 화면 문구 (개정 302).  ★ 「렌트 이력」만 내지 않는다
RENT_SOURCE_WORDS = {"advertisement_type": "광고", "usage_change_types": "점검부",
                     "record_use": "보험", "plate_use_char": "번호판"}


def _axis_state(axis: str, chip, state: dict, as_of: str,
                source: str = "") -> str:
    """축 칸에 낼 상태 문구 (STEP 149n · 개정 280).

    ★ 「0」 하나로 일곱 축을 다 말할 수 없다.  축마다 말이 다르다
    ★ 원문에 없으면 빈 문자다 — 화면이 기호로 되돌아간다
    """
    # ★★ 기호를 코드에 박지 않는다 — ★ `config/labels.json` 이 정본이다.
    #   ★ ★ 실측 08-24 — ★ 「?」로 박아 두어서 ★ 기호를 「—」로 바꾸자 ★ 조용히 어긋났다.
    #     ★ ★ 톤은 기호가 바뀌어도 안 변한다 (V6-02)
    if chip.tone == TONE_UNKNOWN:
        return ""            # 확인 못 한 것은 기호가 정확하다
    w = state.get("warranty")
    rec = state.get("record")
    # ★ 개정 365 — 일반과 동력계를 따로 낸다.  긴 쪽 하나로 뭉치지 않는다
    if axis in ("warranty.general", "warranty.power") and w:
        gen, power = _warranty_state(w, as_of)
        return power if axis == "warranty.power" else gen
    if axis == "state.accident" and rec:
        mycnt, _cost, othcnt, tot = rec
        n = tot if tot is not None else (mycnt or 0) + (othcnt or 0)
        return "무사고" if not n else f"{n}회"
    if axis in ("state.frame", "state.outer"):
        return "골격 이상" if chip.tone != TONE_GOOD else "골격 이상 없음"
    if axis == "state.my_cost" and rec:
        _mycnt, cost, _o, _t = rec
        if cost is None:
            return ""
        return "0원" if not cost else f"{int(cost) // WON_PER_MANWON:,}만"
    if axis == "history.use":
        # ★ 점수를 받았으면 렌트가 아니다 (excluded 가 아니라 값이 있을 때만)
        if chip.tone == TONE_GOOD:
            return "렌트 아님"
        # ★ 어디서 찾았는지를 함께 낸다.  「렌트 이력」만으로는 확인할 수 없다
        got = [RENT_SOURCE_WORDS[k] for k in source.split("+")
               if k in RENT_SOURCE_WORDS]
        return f"렌트 이력 ({'·'.join(got)})" if got else "렌트 이력"
    if axis == "taste.trim":
        # ★ 트림은 그 차종 신차가 사다리의 백분위다.  「있음/없음」이 아니다
        pts, mx = state.get("points", {}).get(axis, (None, None))
        if pts is None or not mx:
            return ""
        return f"상위 {max(1, 100 - round(pts / mx * 100))}%"
    if axis == "warranty.site":
        # ★ 개정 365 — 무엇으로 받았는지 낸다.
        #   「엔카검증 10 + 엔카보증 10 = 20 / 50」
        # ★★ 출처는 ★ 인자로 온다 — ★ `AxisChip` 에는 그 칸이 없다.
        #   ★ ★ 실측 08-24 — ★ `warranty.site` 가 ★ 목록 칩에 처음 들어오자
        #     ★ `AttributeError` 로 ★ /listings 가 500 이 됐다 (명령서 1b)
        got = (source or "").replace("+", " + ")
        return got if got and got not in ("missing", "no_warranty") else (
            "보증 없음" if got == "no_warranty" else "확인 못 함")
    if axis == "taste.option":
        # ★ 옵션은 금액이다.  얼마짜리를 달았는지가 사실이다 (개정 301)
        won = state.get("option_won")
        if won is None:
            return ""
        return "없음" if not won else f"{won // WON_PER_MANWON:,}만"
    if axis.startswith(("spec.", "taste.")):
        # 사양·취향 축은 있고 없고가 전부다 (STEP 149n 표)
        return "있음" if chip.tone == TONE_GOOD else "없음"
    return ""


def _sites_cfg(root: str) -> dict:
    """sites.json.  ★ 행마다 파일을 열지 않는다 — 목록이 200행이다."""
    import os as _o

    from store.crosssite import load_sites

    got = _SITES_CACHE.get(root)
    if got is None:
        got = load_sites(_o.path.join(root, "config", "sites.json"))
        _SITES_CACHE[root] = got
    return got


def _row(conn, rec, labels, fin_cfg, rank, calc_version: str,
         opt_prices: dict | None = None,   # noqa: ARG001 — 아래에서 쓴다
         axes: dict | None = None, changes_by: dict | None = None,
         photo_base: str = "", encar_tpl: str = "",
         km_unit: int = 0, monthly_unit: int = 0,
         dep_cfg: dict | None = None, state_by: dict | None = None,
         market_by: dict | None = None, high_km: int = 0,
         root: str = ".") -> ListingRow:
    """★ calc_version 을 인자로 받는다.  함수 속성은 전역 상태다 (F-2).

    워커를 늘리면 즉시 섞인다 — 증상이 재현되지 않는 부류다
    """
    (lid, tk, trim, ym, km, ce, ci, price, grade, earned, denom,
     dealer, dstatus, first_seen, last_seen, dv, photos, sid,
     origin_won, calc_at, absolute_fail, trust, quadrant, enough,
     insp_fmt, diag_car, w_ext, w_deemed, opt_json, g_earned, g_base,
     g_value, g_car, g_warranty, g_site, g_taste, pen_json, conf_pts,
     _site, _sell_type, _mismatch, _kmpl, _seats) = rec
    got = (axes or {}).get(lid, {})
    st = (state_by or {}).get(lid, {})
    # ★ 원문이 배열이 아닐 수 있다.  그때는 0 이 아니라 「모른다」다
    _codes = json.loads(opt_json) if opt_json else []
    _opt_won = (sum((opt_prices or {}).get(c, 0) for c in _codes)
                if isinstance(_codes, list) else 0)
    _fmt = json.loads(insp_fmt) if insp_fmt else None
    _insp_word = SOURCE_WORDS.get(inspection_source(_fmt), "")
    # 신차가 = 등급기준 + 선택옵션 (개정 301)
    _origin_total = (origin_won + _opt_won) if origin_won else None
    chips = []
    for axis in CHIP_AXES:
        if axis in got:
            # ★ source 를 넘긴다 (개정 435).  안 넘기면 「모름」이 「없음」이 된다
            one = chip(axis, got[axis][0], got[axis][1], labels,
                       source=got[axis][2])
        else:
            one = chip(axis, None, True, labels)
        # ★★ ⓓ (개정 491) — ★ 관문 칩을 감점과 맞춘다.
        #   ★ 「골격 O」인데 골격 판금 감점이 붙은 매물이 있었다 (실측 08-22).
        #   ★ 그 축에 감점이 붙었으면 ★ 「있음」이라 하지 않는다
        if axis in _pen_axes(pen_json, root) and one.tone != TONE_BAD:
            one = replace(one, tone=TONE_BAD,
                          mark=labels.get("VALUE_MARKS", {}).get("0", "·"),
                          label=f"{one.head or one.axis} 감점 있음")
        # ★ 축 칸에는 상태를 낸다.  점수를 내지 않는다 (STEP 149n)
        chips.append(replace(one, state=_axis_state(
            axis, one, dict(st, option_won=_opt_won,
                            inspection_word=_insp_word, points={
                a: (v[0], v[3]) for a, v in got.items()}),
            calc_at, (got.get(axis) or (0, 0, ""))[2])))
    # ★★ ⓕ — 채점이 저장한 confirmed_points 를 쓴다.  ★ 화면이 다시 세지 않는다.
    #   ★ 없으면(옛 판) 그때만 다시 센다
    _den = float(denom or _total_points())
    _confirm = ((float(conf_pts), float(conf_pts) / _den if _den else 0.0)
                if conf_pts is not None
                else confirm_ratio(got, _den))
    _fmt = json.loads(insp_fmt) if insp_fmt else None
    _has_w = bool(w_ext and w_ext != "0") or bool(w_deemed and w_deemed != "0")
    _trust, _why = platform_trust(_fmt, diag_car, _has_w)
    fin = build_finance(price, fin_cfg, tk)
    # ⑨ 비용 — 그 사이트 기준 총액 (개정 353 · V11-120)
    _buy = purchase_cost(_site, price, fin_cfg, _sites_cfg(root), tk)
    changes, first_won = (changes_by or {}).get(lid, (0, None))
    # ★ 시세차 — 가격 축이 excluded 면 내지 않는다.  기대가를 못 구한 것이다
    exp = None
    if dep_cfg is not None and not (got.get("value.origin")
                                    or (None, True))[1]:
        exp = market_price(origin_won, ym, calc_at, tk, dep_cfg)
    gap = (price - exp) if (exp and price is not None) else None
    mkt, mkt_n = (market_by or {}).get(lid, (None, 0))
    _gap_won = (price - mkt) if (mkt and price is not None) else None
    _rec = (state_by or {}).get(lid, {}).get("record")
    _rental = next((c for c in chips if c.axis == "state.usage"), None)
    _why_cheap = why_verdict(_gap_won, {
        "inspection_formats": _fmt, "diagnosis_car": diag_car,
        "has_warranty": _has_w, "inspection_source": inspection_source(_fmt),
        "rental_note": (_rental.state if _rental and _rental.state
                        and "렌트 이력" in _rental.state else None),
        "accident_cnt": (_rec[3] if _rec else None),
        "repair_won": (_rec[1] if _rec else None),
        "mileage_note": (f"주행 {km:,}km"
                         if km and high_km and km >= high_km else None),
        "color_note": None,
        "not_join": (st or {}).get("not_join") or 0,
        "battery_soh": (st.get("battery") or (None, None))[0],
        "battery_soh_low": _soh_low(root),
    })
    # 경과 — 처음 본 날부터 며칠.  ★ 게시일이 아니라 우리가 처음 본 날이다
    dom = _days_between(first_seen, calc_at)
    tags = []
    if absolute_fail:
        tags.append(absolute_fail)
    return ListingRow(
        # ★ 성능부와 보험이력이 어긋난다 (V3-50)
        record_mismatch=bool(_mismatch),
        # ★ 비교 화면에만 쓴다 (S46-45).  ★ 없으면 None — ★ 0 이 아니다
        spec_fuel_economy_kmpl=_kmpl, spec_seats=_seats,
        listing_id=lid, grade=grade or NOT_RATED,
        # ★★ 감점 (개정 491) — 상한을 먹인 뒤의 합과 문구
        penalty_won=_pen_sum(pen_json),
        penalty_labels=_pen_words(pen_json),
        # ★★ 네 묶음 막대 (개정 427).  ★ 갈래 이름은 scoring.json groups 가 정본
        # ★ 등급 문구 — 「제외」는 문자가 아니다 (개정 433).  config 가 정본
        grade_label=labels.get("GRADE_LABELS", {}).get(
            grade or NOT_RATED, grade or NOT_RATED),
        color_ext_hex=_view_dict("color_swatch", root).get(ce),
        bars=_score_bars({"값": g_value, "차량": g_car,
                          "제조사 보증": g_warranty, "사이트 검증": g_site,
                          "취향": g_taste}, root),
        # ★ 상세 조회가 안 끝났으면 「잠정」이다 (STEP 97).
        #   ★ 판정을 감추지 않는다 — 등급은 내되 잠정이라 적는다
        provisional=(g_base is None or not insp_fmt),
        # ★ NOT_RATED 에 순위를 매기지 않는다.  비교 대상이 아니다
        rank=None if (grade or NOT_RATED) == NOT_RATED else rank,
        # ★ 비율이 크게 · 원점수/분모가 작게 (STEP 149f · A-1).
        #   분모가 다른 매물을 눈으로 갈라야 한다
        # ★ 비율은 등급과 같은 자로 낸다 — 505 기준 (개정 292)
        earned=g_earned if g_earned is not None else earned,
        denominator=g_base if g_base else denom,
        ratio_pct=(round(g_earned / g_base * 100, 1)
                   if g_earned is not None and g_base
                   else round(earned / denom * 100, 1)
                   if earned is not None and denom else None),
        # 순위는 취향까지 넣은 555 로 매긴다 (개정 292 ④)
        rank_earned=earned, rank_total=denom,
        # 분모가 만점보다 짧으면 색으로 가른다 (A-2).
        # ★ 개정 298 로 분모는 늘 만점이다 — 짧으면 그것 자체가 사고다
        denom_short=bool(denom and denom < _total_points()),
        confirmed_points=_confirm[0], confirm_pct=round(_confirm[1] * 100, 1),
        # ★ 값을 누르면 그 조건으로 걸러진다 (부록 G).  없으면 링크를 안 만든다
        price_bucket_won=_bucket(price, _view_int("price_bucket_won", root)),
        mileage_bucket_km=_bucket(km, _view_int("mileage_bucket_km", root)),
        status_key=dstatus or None,
        target_label=tk or "",
        # ★ 세부등급을 못 받았으면 그렇게 적는다.  빈 값으로 두지 않는다 (개정 285)
        trim=(trim if trim and " · " in trim
              else f"{trim} · 세부등급 없음" if trim else ""),
        trim_detail_known=bool(trim and " · " in trim),
        # 옵션 — 「5종 890만」.  ★ 「옵션 있음」 같은 말을 쓰지 않는다 (개정 313)
        option_count=len(_codes) if isinstance(_codes, list) else 0,
        year_month=ym, mileage_km=km,
        color_ext=ce, color_int=ci, axis_chips=chips, price_won=price,
        # ★ 어느 사이트에서 왔는지 매물마다 낸다 (V9-06).
        #   화면이 「엔카」를 글자로 박고 있었다 — 사이트가 둘이 되면 거짓말이다
        site_badge=site_badge(_site, _sell_type, root),
        # ★ 「그 사이트에서 사면 얼마를 내는가」다 (개정 353).
        #   사이트마다 정책이 다르다 — K카는 보증 가입비·기타가 붙는다.
        #   ★ 표시가가 싼 쪽이 실제로 싼 쪽이 아닐 수 있다
        total_cost_won=(_buy.total_won if _buy else
                        ((price + fin.acquisition_cost_won) if fin else None)),
        buy_estimated=bool(_buy and _buy.estimated),
        loan_principal_won=fin.loan_principal_won if fin else None,
        monthly_won=fin.monthly_payment_won if fin else None,
        # ★ 현금은 초기 부담이다.  표시가와 무관하게 고정이다 (STEP 83)
        down_payment_won=fin.down_payment_won if fin else None,
        cash_only=bool(fin and fin.cash_only),
        price_gap_pct=(round(gap / exp * 100, 1) if (gap is not None and exp)
                       else None),
        price_change_cnt=changes, days_on_market=dom,
        dealer_shop=dealer, dealer_honesty=None, note=None,
        versions=_stamp(calc_version, dv),
        expected_price_won=int(exp) if exp else None,
        origin_price_won=origin_won,
        # ★ 신차가 = 등급기준 + 선택옵션 (개정 301).  셋을 다 낸다 —
        #   엔카는 6,547만(5,787 + 760)인데 우리는 5,787만만 냈다
        option_price_won=_opt_won,
        origin_total_won=_origin_total,
        # 플랫폼 신뢰도 (개정 300) — 같은 값이라도 누가 보증하느냐가 다르다
        platform_trust=_trust, platform_trust_why=_why,
        # ★ 전기차 배터리 (개정 296).  「있다」만 남기면 그 값을 버리는 것이다
        battery_soh=(st.get("battery") or (None, None))[0],
        battery_grade=(st.get("battery") or (None, None))[1],
        market_price_won=mkt,
        market_sample=mkt_n,
        market_gap_won=_gap_won,
        # ★ 부록 G 10·11 — 마스터가 「없다」고 지적한 그것이다.
        #   금액이 아니라 %다.  「−13.0%」가 사람에게 읽힌다
        market_gap_pct=(round(_gap_won / mkt * 100, 1)
                        if (_gap_won is not None and mkt) else None),
        origin_gap_pct=(round((price - _origin_total) / _origin_total * 100, 1)
                        if (_origin_total and price is not None) else None),
        # ★ 「싸다」를 말할 때 「왜 싼가」를 함께 낸다 (개정 299 · V3-52).
        #   금지 — 「시세차 −1,100만」만 내고 끝내는 것
        why_cheap=_why_cheap[0] if _gap_won and _gap_won < 0 else None,
        why_cheap_reasons=_why_cheap[1] if _gap_won and _gap_won < 0 else [],
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



def _pen_rows(raw) -> list:
    """감점 원문 → [(키, 점수, 문구)].  ★ 못 읽으면 빈 것이다."""
    if not raw:
        return []
    try:
        got = json.loads(raw)
    except (ValueError, TypeError):
        return []
    return [tuple(x) for x in got if isinstance(x, list) and len(x) == 3]


def _pen_axes(raw, root: str = ".") -> set:
    """감점이 붙은 축 (개정 491 ⓓ).

    ★ 어느 감점이 어느 축인지는 ★ config/scoring.json penalty_axis 가 정본이다.
      ★ 코드에 박지 않는다 (S14 · V4-13)
    ★ 「cap:축」 줄은 되돌린 몫이라 ★ 세지 않는다 — 그 축은 이미 들어 있다
    """
    rows = _pen_rows(raw)
    if not rows:
        return set()
    with open(os.path.join(root, "config", "scoring.json"),
              encoding="utf-8") as f:
        where = json.load(f).get("penalty_axis") or {}
    out = set()
    for key, _p, _w in rows:
        axis = where.get(key)
        if axis:
            out.add(axis)
    return out


def _pen_sum(raw) -> int:
    """★ 상한을 먹인 뒤의 합 (개정 491).

    ★ 「cap:축」 줄이 되돌려 준 몫까지 더한 값이다 — 그것이 실제로 깎인 값이다
    """
    return int(sum(p for _k, p, _w in _pen_rows(raw)))


def _pen_words(raw) -> list:
    """화면 문구.  ★ 「깎인 합 → 상한」 줄을 ★ 감추지 않는다 (개정 491)."""
    # ★ 「cap:축」 줄은 되돌린 몫이라 ★ 점수를 따로 적지 않는다 —
    #   문구 자체가 「… → 상한 …」이라 숫자를 또 붙이면 두 번 읽힌다
    return [{"key": k, "points": p, "label": w,
             "is_cap": str(k).startswith("cap:")}
            for k, p, w in _pen_rows(raw)]


def _view_cfg(key: str, root: str = ".") -> int:
    """화면 표시 정책.  ★ 코드에 박지 않는다 (config/web.json)."""
    with open(os.path.join(root, "config", "web.json"), encoding="utf-8") as f:
        return int(json.load(f)[key])


# ★ 개정 433 — 8단계 + 순위를 안 매기는 것 셋 (제외·등급 없음·평가 불가)
GRADE_ORDER = RANK_ORDER + NOT_RANKED
# 가격 분포 칸 수 · 오늘 변동 줄 수.  ★ 표시 정책이라 코드에 박지 않는다
PRICE_BINS = _view_cfg("price_bins")
TRIM_ROWS = _view_cfg("trim_rows")
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

# ★ 순위를 안 매기는 것은 뒤로.  비교 대상이 아니다
# ★★ 개정 433 — 전에는 ('E','NOT_RATED') 였다.  E 는 이제 30~40% 자리라
#   그대로 두면 **멀쩡한 E 매물이 목록 맨 뒤로 밀린다**
ORDER_HEAD = ("(CASE WHEN s.grade IN ("
              + ",".join("'%s'" % g for g in NOT_RANKED)
              + ") THEN 1 ELSE 0 END)")
# ★★ 같은 점수면 사이트 보증이 높은 쪽이 앞이다 (개정 306 · V9-09).
#   마스터 — 「최고급 우선이야」.  그 우선이 정렬에도 들어간다.
#   ★ 사이트 이름으로 올리지 않는다 — ⑤ 사이트 보증 축의 점수로 올린다.
#     K카 직거래까지 올리면 안 된다 (규격 금지)
SITE_WARRANTY_ORDER = (
    "(SELECT a.score FROM result_axis a WHERE a.listing_id = l.listing_id"
    "   AND a.calc_version = s.calc_version AND a.axis = 'warranty.site')"
    " DESC")
# ★ 타이브레이커가 없으면 같은 점수가 페이지마다 다르게 나온다 (V6-07)
ORDER_TAIL = ("(s.earned * 1.0 / NULLIF(s.denominator, 0)) DESC,"
              f" {SITE_WARRANTY_ORDER},"
              " l.price_current_won ASC, l.listing_id ASC")


def order_clause(order: str) -> str:
    """4단 정렬.  ★ 축을 바꿔도 뒤 3단은 남는다."""
    first = ORDER_SQL.get(order, ORDER_SQL["rank"])
    return f"{ORDER_HEAD}, {first}, {ORDER_TAIL}"


def _view_str(key: str, root: str = ".") -> str:
    """화면 표시 정책 중 문자열.  ★ 코드에 박지 않는다 (config/web.json)."""
    with open(os.path.join(root, "config", "web.json"), encoding="utf-8") as f:
        return str(json.load(f)[key])


def _lease_kinds(root: str = ".") -> tuple:
    """목록에서 뺄 리스·렌트 (개정 420).  ★ 값은 config 가 갖는다 (S14)."""
    with open(f"{root}/config/web.json", encoding="utf-8") as f:
        cfg = json.load(f)
    return (list(cfg["lease_advertisement_types"]),
            list(cfg["lease_sell_types"]))


def excluded_hidden(conn, flt: ListingFilter, root: str = ".") -> int:
    """★ 뺀 건수를 밝힌다 (개정 433).  「몇 건을 안 보여 줬는지」를 안 적으면
    사람이 목록을 전부로 착각한다 — 리스에서 겪은 것과 같다 (개정 420).
    """
    if getattr(flt, "excluded", False):
        return 0
    from dataclasses import replace as _rep

    on, args_on = _listings_where(_rep(flt, excluded=True))
    return conn.execute(
        "SELECT COUNT(*) FROM core_listing l LEFT JOIN result_score s"
        " ON s.listing_id = l.listing_id AND s.calc_version = ?"
        " LEFT JOIN core_dealer d ON d.dealer_id = l.dealer_id WHERE "
        + " AND ".join(on), [flt.calc_version, *args_on]).fetchone()[0]


def lease_hidden(conn, flt: ListingFilter, root: str = ".") -> int:
    """지금 조건에서 리스·렌트를 몇 건 뺐나 (개정 420).

    ★ 조용히 빼지 않는다.  건수를 안 내면 매물이 사라진 것으로 보인다
    ★ 「뺀 것만」 센다 — 같은 조건에 리스를 켠 것과 끈 것의 차다
    """
    if getattr(flt, "lease", False):
        return 0
    from dataclasses import replace as _rep

    on, args_on = _listings_where(_rep(flt, lease=True))
    off, args_off = _listings_where(flt)
    sql = ("SELECT COUNT(*) FROM core_listing l LEFT JOIN result_score s"
           " ON s.listing_id = l.listing_id AND s.calc_version = ?"
           " LEFT JOIN core_dealer d ON d.dealer_id = l.dealer_id WHERE ")
    a = conn.execute(sql + " AND ".join(on),
                     [flt.calc_version, *args_on]).fetchone()[0]
    b = conn.execute(sql + " AND ".join(off),
                     [flt.calc_version, *args_off]).fetchone()[0]
    return max(0, a - b)


def _listings_where(flt: ListingFilter) -> tuple[list, list]:
    """목록 조건.  ★ 세는 것과 뽑는 것이 같은 조건을 쓴다 —
    갈라 두면 「3,471건 중 200건」의 3,471 이 거짓말이 된다 (V11-55)."""
    # ★ 사이트별로 거를 수 있게 한다 — 「엔카만」 「K카 직영만」 「전부」 (개정 306).
    #   ★ site 가 비면 「전부」다.  전에는 늘 encar 로 고정돼 전부를 볼 수 없었다
    where: list = []
    args: list = []
    if flt.site:
        where.append("l.site = ?")
        args.append(flt.site)
    if getattr(flt, "sell_type", None):
        where.append("l.sell_type = ?")
        args.append(flt.sell_type)
    if not where:
        where.append("1=1")
    if flt.target_key:
        where.append("l.target_key = ?")
        args.append(flt.target_key)
    if getattr(flt, "mismatch", False):
        where.append(record_mismatch_sql())
    # ★ 리스·렌트는 기본으로 뺀다 (개정 420).  ?lease=1 이면 함께 낸다
    if not getattr(flt, "lease", False):
        ads, sells = _lease_kinds()
        where.append(
            "(l.advertisement_type IS NULL OR l.advertisement_type NOT IN"
            f" ({','.join('?' * len(ads))}))")
        args.extend(ads)
        where.append("(l.sell_type IS NULL OR l.sell_type NOT IN"
                     f" ({','.join('?' * len(sells))}))")
        args.extend(sells)
    # ★★ 관문 배제는 기본으로 뺀다 (개정 433).  ?excluded=1 이면 그것만 낸다
    #   ★ 「기본 목록에 안 나온다」 — 리스와 같은 방식이다.  지우지 않는다
    if getattr(flt, "excluded", False):
        where.append("s.grade = 'EXCLUDED'")
    elif getattr(flt, "lease", False):
        # ★★ 리스는 관문 배제 사유이기도 하다 (FAIL_LEASE).  그래서 개정 433
        #   뒤에는 ?lease=1 만으로는 리스가 안 나온다 — 제외로도 숨겨진다.
        #   ★ 개정 420 「지우는 것이 아니다.  ?lease=1 로 볼 수 있다」를 지킨다
        from analyze.absolute import FAIL_LEASE

        where.append("(s.grade IS NULL OR s.grade <> 'EXCLUDED'"
                     " OR s.absolute_fail LIKE ?)")
        args.append(f"%{FAIL_LEASE}%")
    else:
        where.append("(s.grade IS NULL OR s.grade <> 'EXCLUDED')")
    # ★ 매물 하나만 (개정 427 상세).  ★ 맨 앞에 둔다 — 가장 좁은 조건이다
    if getattr(flt, "listing_id", None) is not None:
        where.append("l.listing_id = ?")
        args.append(flt.listing_id)
    if getattr(flt, "listing_ids", ()):
        marks = ",".join("?" * len(flt.listing_ids))
        where.append(f"l.listing_id IN ({marks})")
        args.extend(flt.listing_ids)
    # ══ 칩 7 · ＋12 (개정 427 · STEP 97) ══
    # ★ 필터가 두꺼워야 목록이 얇아진다.  ★ 전부 SQL 로 건다 (V11-164) —
    #   밖에서 거르면 「7건」과 실제 건수가 어긋난다
    for field, col in (("color_ext", "l.color_ext_raw"),
                       ("color_int", "l.color_int_raw"),
                       ("fuel", "l.fuel_raw"),
                       ("region", "d.dealer_region")):
        got = getattr(flt, field, None)
        if got:
            where.append(f"{col} = ?")
            args.append(got)
    if getattr(flt, "trim", None):
        where.append("l.trim_badge LIKE ?")
        args.append(f"%{flt.trim}%")
    if getattr(flt, "days_max", None) is not None:
        where.append("julianday('now') - julianday(l.first_seen) <= ?")
        args.append(flt.days_max)
    if getattr(flt, "price_dropped", False):
        # ★ 첫 게시가는 core_listing_change 가 갖고 있다 — l 에는 없다
        where.append(
            "EXISTS (SELECT 1 FROM core_listing_change ch"
            "  WHERE ch.listing_id = l.listing_id AND ch.field = 'price_current_won'"
            "    AND CAST(ch.new_value AS INTEGER)"
            "        < CAST(ch.old_value AS INTEGER))")
    if getattr(flt, "warranty_month_min", None) is not None:
        where.append("COALESCE(l.warranty_body_month, 0) >= ?")
        args.append(flt.warranty_month_min)
    if getattr(flt, "honesty_min", None) is not None:
        where.append("d.trust_score >= ?")
        args.append(flt.honesty_min)
    # ★★ 점수 필터 — 갈래 합이 result_score 에 앉아 있다 (개정 428).
    #   ★ JOIN 없이 걸린다.  「값 220 이상」 「취향 60 이상」
    #   ★ COALESCE 를 쓴다.  ★ NULL >= 0 은 참이 아니다 —
    #     그냥 걸면 판정이 없는 매물이 **조용히 사라진다** (실측 08-21)
    for field, col in (("score_value_min", "s.group_value"),
                       ("score_car_min", "s.group_car"),
                       ("score_taste_min", "s.group_taste")):
        got = getattr(flt, field, None)
        if got is not None:
            where.append(f"COALESCE({col}, 0) >= ?")
            args.append(got)
    # ★ 보증 막대는 제조사 보증 + 사이트 검증 둘을 합친 것이다 (config score_bars)
    if getattr(flt, "score_warranty_min", None) is not None:
        where.append("COALESCE(s.group_warranty, 0)"
                     " + COALESCE(s.group_site, 0) >= ?")
        args.append(flt.score_warranty_min)
    # 차종 (개정 420).  ★ target_key 가 차종이다
    if getattr(flt, "model", None):
        where.append("l.target_key LIKE ?")
        args.append(f"{flt.model}%")
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
    # ★ 「A 이상만」 (STEP 149s).  순위 밖(제외·등급 없음·평가 불가)은 뺀다
    #   ★ 개정 433 — RANK_ORDER 가 8단계다.  「E 이상」이 이제 뜻이 있다
    if flt.min_grade and flt.min_grade in RANK_ORDER:
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
                  page_size: int | None = None,
                  extras: bool = True,
                  with_state: bool = True,
                  opt_money: bool | None = None) -> list[ListingRow]:
    """축·버킷 필터는 Component 이름을 쓴다 — /listings?axis=spec.hud&bucket=1.

    ★ opt_money — 신차가(등급기준 + 선택옵션가)를 낼지.  ★ 쿼리 하나가 든다.
      안 주면 with_state 를 따른다 (옛 동작).  ★ 상세는 켜야 한다 —
      끄면 「신차가 6,170만 · 선택 옵션가 없음」이 나온다 (실측 08-22)
    """
    where, args = _listings_where(flt)

    sql = (
        "SELECT l.listing_id, l.target_key,"
        # ★ 트림은 Badge + BadgeDetail 이다 (개정 313).
        #   「가솔린 2.5 터보 AWD」만으로는 깡통과 시그니처가 같아진다
        " l.trim_badge || CASE WHEN l.trim_badge_detail IS NULL THEN ''"
        "   ELSE ' · ' || l.trim_badge_detail END, l.year_month,"
        " l.mileage_km, l.color_ext_raw, l.color_int_raw, l.price_current_won,"
        # ★ earned 를 가져온다.  비율은 earned/denominator 다 —
        #   score_total(555 환산)로 나누면 분모가 짧을수록 부풀려진다 (E-1)
        " s.grade, s.earned, s.denominator, l.dealer_shop, l.status,"
        # ★ 사진은 이미 원문에서 뽑아 앉아 있다 — 다시 받지 않는다 (개정 274)
        " l.first_seen, l.last_seen, s.dict_version, l.photo_list_json,"
        # ★ 시세차 · 경과 · 정직도 · 비고 (개정 277 · 278).
        #   행마다 따로 조회하면 200행에 1,000쿼리다 — 조인으로 한 번에 (V11-34)
        " l.source_id, l.price_origin_won, s.calculated_at, s.absolute_fail,"
        " d.trust_score, d.quadrant, d.sample_sufficient,"
        # 개정 300·301 — 점검 출처 · 엔카진단 · 엔카보증 · 선택 옵션가
        " l.inspection_formats_json, l.diagnosis_car,"
        " l.warranty_extend, l.warranty_deemed, l.options_choice_json,"
        # ★ 등급은 취향을 뺀 505 로 매긴다 (개정 292).  555 로 잰 비율을 내면
        #   화면과 등급이 어긋난다 — 실측 08-17: 84.9%(555) 인데 S(505 기준)
        " s.grade_earned, s.grade_base,"
        # ★★ 네 묶음 막대 (개정 427 · V11-163).  ★ 목록의 시그니처다.
        #   행마다 따로 조회하면 200행에 1,000쿼리다 — 같은 조인으로 받는다
        " s.group_value, s.group_car, s.group_warranty,"
        " s.group_site, s.group_taste,"
        # ★★ 감점 (개정 491 · 명령서 1-2 ⓒ).  ★ 목록 한 행에 딱지를 낸다.
        #   ★ 같은 조인으로 받는다 — 행마다 따로 조회하지 않는다 (V11-34)
        " s.penalties_json,"
        # ★★ 확인율은 ★ 채점이 낸 값 하나다 (개정 491 · 명령서 1-2 ⓕ).
        #   ★ 화면이 다시 세면 /why 와 어긋난다 — 실측 「상세 100% vs /why 99.6%」
        " s.confirmed_points,"
        # 사이트 배지 (50-multisite · V9-06) — 「K카 직영」까지 낸다
        " l.site, l.sell_type,"
        # ★ 성능부 ↔ 보험 어긋남 (V3-50).  조건은 store 에 하나만 둔다 —
        #   화면과 검사가 다른 것을 세면 「857건」이 거짓말이 된다
        f" {record_mismatch_sql()},"
        # ★★ 제원 둘 (마스터 확정 08-24 · UI_REVIEW 10) — ★ **비교 화면용**이다.
        #   ★ 목록 카드에는 안 낸다 (S46-45) — ★ 비교는 견주는 자리라 갈리는 값이다
        #   ★★ 축이 아니다 — ★ 판정에 안 들어간다
        " l.spec_fuel_economy_kmpl, l.spec_seats"
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
    # ★ 화면이 안 쓰는 값은 안 받는다 (V11-34).  현황판은 등급·가격만 쓴다 —
    #   상태·시세까지 받으면 한 화면이 3쿼리씩 무거워진다
    state_by = _bulk_state(conn, lids) if (extras and with_state) else {}
    market_by = _bulk_market(conn, lids, root) if extras else {}
    base = _view_str("photo_base_url", root)
    encar_tpl = _view_str("encar_detail_url", root)
    km_unit = _view_cfg("km_bucket", root)
    monthly_unit = _view_cfg("monthly_bucket_won", root)
    with open(os.path.join(root, "config", "depreciation.json"),
              encoding="utf-8") as f:
        dep_cfg = json.load(f)
    # ★ 순위는 쪽을 넘어가도 이어진다 — 2쪽 첫 줄이 다시 1위가 되면 거짓말이다
    first = 0 if flt.show_all else (flt.page - 1) * page_size
    # ★ 옵션가 사전은 한 번만 읽는다 (개정 301).  행마다 읽으면 쿼리가 는다
    # ★★ with_state 에 매달지 않는다 (실측 08-22) — 상세는 with_state=False 라
    #   옵션가 사전이 비어 「신차가 6,170만 · 선택 옵션가 없음」이 나왔다.
    #   ★ 목록은 7,779만, 채점은 7,730만(트림+옵션)인데 상세만 트림가였다.
    #   ★ 신차가 = 등급기준 + 선택옵션가 합이다 (f-table 518 · 개정 301)
    #   ★ 그렇다고 늘 켜면 현황이 21쿼리가 되어 상한 20 을 넘는다 (V11-34).
    #     ★ 신차가를 내는 화면만 켠다
    want_opt = with_state if opt_money is None else opt_money
    opt_prices = _option_prices(conn) if (extras and want_opt) else {}
    high_km = _high_km(root)
    return [_row(conn, r, labels, fin_cfg, first + i + 1, flt.calc_version,
                 opt_prices, axes, changes, base, encar_tpl, km_unit,
                 monthly_unit, dep_cfg, state_by, market_by, high_km, root)
            for i, r in enumerate(recs)]



def _score_bars(sums: dict, root: str = ".") -> list:
    """★ 네 묶음 막대 (개정 427 · V11-163) — 목록의 시그니처.

    ★ 늘 넷이다.  값이 없어도 자리를 지운다 — 행마다 개수가 달라지면
      스캔이 깨진다 (규격 「금지 — 배지를 행마다 다른 개수로 붙이는 것」)
    ★ 어느 갈래를 어느 막대에 넣는지는 config/web.json score_bars 가 정본이다
    """
    from report.screens.views import ScoreBar

    caps = _group_caps(root)
    out = []
    for one in _view_list("score_bars", root):
        cap = sum(caps.get(g, 0.0) for g in one["groups"])
        got = sum(sums.get(g) or 0.0 for g in one["groups"])
        pct = int(round(got / cap * 100)) if cap else 0
        out.append(ScoreBar(one["key"], one["label"], one["css"],
                            max(0, min(100, pct)), round(got, 1), cap))
    return out


def _group_caps(root: str = ".") -> dict:
    """갈래별 만점.  ★ config/scoring.json groups 가 정본이다 (S14)."""
    with open(os.path.join(root, "config", "scoring.json"),
              encoding="utf-8") as f:
        cfg = json.load(f)
    comp = cfg["components"]
    out = {}
    # ★ 갈래(f-table 넷) ＋ ★ 화면이 나눠 내는 이름(`group_parts`).
    #   ★ 없으면 ★ 만점이 0 이 되어 ★ 막대가 ★ 늘 0% 로 보인다 (UI_REVIEW 1장)
    table = dict(cfg.get("groups") or {}, **(cfg.get("group_parts") or {}))
    for name, prefixes in table.items():
        out[name] = float(sum(
            (v if isinstance(v, (int, float)) else (v or {}).get("points") or 0)
            for k, v in comp.items()
            if any(k == p or k.startswith(p) for p in prefixes)))
    return out


def _view_list(key: str, root: str = ".") -> list:
    with open(os.path.join(root, "config", "web.json"), encoding="utf-8") as f:
        return json.load(f)[key]


def _view_dict(key: str, root: str = ".") -> dict:
    with open(os.path.join(root, "config", "web.json"), encoding="utf-8") as f:
        return json.load(f)[key]


def _soh_low(root: str) -> float:
    """이보다 낮으면 「배터리가 닳았다」를 싼 이유로 낸다 (개정 296).

    ★ 실측 08-17 — 30건의 SOH 가 91.1~96.8, 중앙 94.4 다
    """
    with open(f"{root}/config/scoring.json", encoding="utf-8") as f:
        return float(json.load(f)["axis_rules"]["value"]["battery_soh_low"])


def _view_int(key: str, root: str) -> int:
    """화면 임계값은 config 다 (V4-13 · V4-17)."""
    with open(f"{root}/config/web.json", encoding="utf-8") as f:
        return int(json.load(f)[key])


def _bucket(value, step: int):
    """값을 그 단위로 올려 잡는다.  ★ 없으면 None — 빈 주소를 만들지 않는다."""
    if value is None:
        return None
    return ((int(value) + step - 1) // step) * step


def _high_km(root: str) -> int:
    """이만큼 넘으면 「많이 달렸다」를 싼 이유로 낸다 (개정 299 ⑤).

    ★ 정책값이라 config 에 둔다 — 코드에 박지 않는다 (V4-13)
    """
    with open(f"{root}/config/scoring.json", encoding="utf-8") as f:
        return int(json.load(f)["axis_rules"]["value"]["high_mileage_km"])


def _option_prices(conn) -> dict:
    """선택 옵션 코드 → 값 (원).  ★ 같은 코드가 카탈로그마다 있어 중앙값을 쓴다."""
    by_code: dict = {}
    for code, mw in conn.execute(
        "SELECT option_code, price_manwon FROM dict_model_option"
        " WHERE price_manwon IS NOT NULL"
    ):
        by_code.setdefault(code, []).append(int(mw))
    return {c: sorted(v)[len(v) // 2] * WON_PER_MANWON
            for c, v in by_code.items()}


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
        " AND grade IN (" + ",".join("'%s'" % g for g in NOT_RANKED)
        + ")", (calc_version,)).fetchone()[0]
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
                   fin_cfg: dict, root: str = ".",
                   extras: bool = True,
                   with_state: bool = True) -> list[ListingRow]:
    """추천 대상만.  ★ 제외·등급 없음·평가 불가는 순위를 안 매긴다 (STEP 84).

    ★ 개정 433 — 전에는 「E 와 NOT_RATED」였다.  E 가 관문 배제였기 때문이다.
      이제 배제는 EXCLUDED 다 — E 를 빼면 30~40% 매물이 추천에서 사라진다
    """
    rows = [r for r in view_listings(account, conn, flt, fin_cfg, root,
                                     extras=extras, with_state=with_state)
            if r.grade not in NOT_RANKED]
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
            # ★ 이유를 못 대면 추천하지 않는다 (개정 304)
            recommend_reason=recommend_reason(r),
            got_pct=round((r.earned or 0) / total * 100, 1) if total else 0.0,
            may_pct=round(gain / total * 100, 1) if total else 0.0))
    # ★ 이유를 못 댄 것은 뺀다.  「그냥 점수가 높아서」는 추천이 아니다 (개정 304).
    #   ★ extras 를 끄면 시세·상태를 안 읽어 이유를 만들 재료가 없다 —
    #     그때는 버리지 않는다.  「못 봤다」와 「이유가 없다」는 다르다
    return [r for r in out if r.recommend_reason] if extras else out


_EMPTY = AxisChip("", "", TONE_UNKNOWN, "")


def recommend_reason(row) -> str:
    """왜 이 순위인가 — 한 문장 (개정 304).

    ★ 강점 태그 나열이 아니라 문장 하나다.
      마스터 지적 — 「추천하는 이유가 내 눈에 보여야지」
    금지   이유를 못 대는데 추천 목록에 두는 것
    """
    parts = []
    if row.market_gap_won and row.market_gap_won < 0:
        parts.append(f"시세보다 {abs(row.market_gap_won) // WON_PER_MANWON:,}만 싸고")
    # ★ 축 점수로 만든다.  상태 문구에 기대면 그 조회를 켠 화면에서만 이유가 난다
    full = {c.axis: c for c in row.axis_chips}
    if (full.get("state.accident") or _EMPTY).tone == TONE_GOOD:
        parts.append("무사고이며")
    if (full.get("history.use") or _EMPTY).tone == TONE_GOOD:
        parts.append("렌트 이력이 없고")
    if (full.get("warranty.site") or _EMPTY).tone == TONE_GOOD:
        parts.append("사이트가 우수등급을 준")
    if not parts:
        return ""
    # ★ 조사를 이어 한 문장으로 만든다.  「무사고 엔카가 보증합니다」는 말이 아니다
    last = parts[-1]
    tail = {"싸고": "쌉니다", "무사고이며": "무사고입니다",
            "렌트 이력이 없고": "렌트 이력이 없습니다",
            "사이트가 우수등급을 준": "사이트가 우수등급을 줬습니다"}
    for k, v in tail.items():
        if last.endswith(k):
            parts[-1] = last[:len(last) - len(k)] + v
            break
    return " ".join(parts)


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
        # ★ 개정 433 — 배제는 EXCLUDED 다.  grade='E' 로 세면 0건이 나온다
        "SELECT absolute_fail FROM result_score "
        "WHERE calc_version=? AND grade='EXCLUDED'", (calc_version,)
    ):
        for part in (reason or "사유 없음").split(";"):
            key = part.strip() or "사유 없음"
            counts[key] = counts.get(key, 0) + 1
    # ★★ 개정 433 — 링크가 ?grade=E 였다.  E 는 이제 30~40% 자리라
    #   그대로 두면 「골격 사고」를 눌렀는데 멀쩡한 E 매물이 나온다
    return [ExcludedGroup(k, v, EXCLUDED_NOTES.get(k, ""),
                          f"/listings?excluded=1&reason={k}")
            for k, v in sorted(counts.items(), key=lambda kv: -kv[1])]


def view_why(account: Account, conn, listing_id: int, calc_version: str,
             fin_cfg: dict, policy: dict, root: str = "."):
    """L1 — 9장 STEP 90 L1 항목 전건."""
    return render_listing(conn, listing_id, calc_version, fin_cfg, policy, root)


def _compare_conclusion(rows: list) -> str:
    """★ 한 줄 결론 (개정 427) — 「A는 취향이 낫고 B는 값이 낫습니다」.

    ★ 표를 눈으로 훑게 두지 않는다.  ★ 막대 넷 중 **누가 어디서 앞서는가**다
    ★ 지어내지 않는다 — 막대가 없으면 빈 말을 안 한다
    """
    if len(rows) < 2:
        return ""
    said = []
    for i, one in enumerate(rows):
        best = [b.label for b in one.bars
                if all(b.pct >= (other.bars[j].pct if j < len(other.bars)
                                 else 0)
                       for other in rows if other is not one
                       for j, x in enumerate(one.bars) if x is b)]
        if best:
            said.append(f"{i + 1}번({one.target_label})은 "
                        f"{' · '.join(best[:2])}이 낫습니다")
    if not said:
        return "네 갈래 모두 한쪽이 앞서지 않습니다 — 값과 취향으로 고르십시오."
    return " · ".join(said) + "."


def view_compare(account: Account, conn, listing_ids: list[int],
                 calc_version: str, fin_cfg: dict, policy: dict,
                 root: str = ".") -> CompareView:
    """분모가 다르면 경고 · 버전이 다르면 비교 불가 (V6-05).

    ★★ 고른 것이 없으면 ★ **아무것도 안 그린다** (UI_REVIEW 11-3 · 마스터 결정 08-24).
      ★ ★ 실측 08-24 — ★ `ids` 없이 열면 ★ 전건을 그려 ★ **9,008,767B · 35.2초**였다.
        ★ 고른 둘을 주면 ★ 7,438B · 0.34초다 — ★ 1,211배다
      ★ ★ 비교는 ★ 「관심에서 고른 것」만 받는다.  ★ 목록 전체를 견주는 화면이 아니다
    """
    if not listing_ids:
        return CompareView([], [], {}, False, False,
                           conclusion="관심 화면에서 견줄 매물을 고르십시오 — "
                                      "카드의 네모를 누른 뒤 「고른 N대 비교하기」")
    views = [render_listing(conn, i, calc_version, fin_cfg, policy, root)
             for i in listing_ids]
    axes = [a.axis for a in views[0].axes] if views else []
    cells: dict[tuple[str, str], AxisView] = {}
    for v in views:
        for a in v.axes:
            cells[(v.listing_id, a.axis)] = a
    denoms = {v.denominator for v in views}
    vers = {(v.versions.calc_version, v.versions.dict_version) for v in views}
    # ★ 비교도 사람이 고른 것이다 — 리스라고 빼면 고른 차가 사라진다 (개정 420)
    #   ★ 제외된 것도 뺀 뒤 고른 것이라면 낸다 (개정 433)
    # ★★ 전건을 읽고 파이썬에서 고르지 않는다 —
    #   전에는 첫 쪽 50건 안에서만 찾아 **고른 매물이 조용히 빠졌다** (실측 08-21)
    flt = ListingFilter(calc_version=calc_version, lease=True,
                        excluded=False, show_all=True,
                        listing_ids=tuple(listing_ids))
    rows = view_listings(account, conn, flt, fin_cfg, root,
                         page_size=max(1, len(listing_ids)))
    if len(rows) < len(listing_ids):
        got = {r.listing_id for r in rows}
        rows += [r for r in view_listings(
            account, conn, _rep_flt(flt, excluded=True), fin_cfg, root,
            page_size=max(1, len(listing_ids)))
            if r.listing_id not in got]
    # ★ 사람이 고른 차례를 지킨다 — 표의 열 차례가 뒤바뀌면 못 읽는다
    order = {int(x): i for i, x in enumerate(listing_ids)}
    rows.sort(key=lambda r: order.get(int(r.listing_id), 99))
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
    # ★ 옵션 차이만 낸다.  같은 것은 접는다 (61-web 「비교」)
    from store.core import option_diff

    diff = option_diff(conn, list(listing_ids))
    by_id = {r.listing_id: r for r in rows}
    only = tuple({"listing_id": lid,
                  "label": (by_id[lid].trim if lid in by_id else str(lid)),
                  "items": got}
                 for lid, got in sorted(diff["only"].items()) if got)
    return CompareView(rows, axes, cells, len(denoms) > 1, len(vers) > 1,
                       axis_winner=winner,
                       option_same=tuple(diff["same"]), option_only=only,
                       conclusion=_compare_conclusion(rows))


def market_trims(conn, target_key: str, root: str = ".",
                 picked: str | None = None) -> list:
    """그 차종의 트림 목록 — 고를 수 있게 (V11-83 · 개정 282).

    ★ 「G80_25T 1,713건을 한 시세로 묶으면 뜻이 없다」 (개정 285).
      트림을 고르면 분포도 그 트림만 본다
    """
    need = _view_cfg("market_min_sample", root)
    out = []
    for trim, n in conn.execute(
        "SELECT trim_badge, COUNT(*) FROM core_listing"
        " WHERE target_key=? AND status='active' AND trim_badge IS NOT NULL"
        " GROUP BY 1 ORDER BY 2 DESC", (target_key,)
    ):
        out.append({"trim": trim, "count": n, "enough": n >= need,
                    # ★ 템플릿은 비교를 모른다.  켜짐을 여기서 정한다 (V11-104)
                    "on": trim == picked,
                    "url": f"/market?target={target_key}"
                           f"&trim={quote(trim, safe='')}"})
    return out


def view_market(account: Account, conn, target_key: str,
                depreciation: dict, quantiles=None, trim: str | None = None,
                root: str = ".") -> MarketView:
    from report.render import CoefficientChange  # noqa: F401

    # ★ 트림을 고르면 그 트림만 본다 (V11-83)
    trim_sql = " AND trim_badge=?" if trim else ""
    trim_arg = (trim,) if trim else ()
    prices = [r[0] for r in conn.execute(
        "SELECT price_current_won FROM core_listing WHERE target_key=? "
        + trim_sql +
        " AND price_current_won IS NOT NULL ORDER BY price_current_won",
        (target_key, *trim_arg))]

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
                      price_bins=_price_bins(prices, target_key, root=root),
                      by_year=_by_year(conn, target_key),
                      # 연식별 중앙값을 선으로 (개정 340 · V11-119).
                      # ★ 표로만 내면 기울기가 안 보인다
                      year_line=_year_line(_by_year(conn, target_key), root),
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


def _group_prices(conn, target_key: str, expr: str) -> dict:
    """묶음별 가격 목록을 한 번에 받는다.

    ★ 항목마다 한 번씩 돌면 연식 6종 + 트림 20종 = 26쿼리다 (V11-34).
      실측 08-17: 시세 화면이 13쿼리였다
    """
    out: dict = {}
    for key, price in conn.execute(
        f"SELECT {expr}, price_current_won FROM core_listing"
        f" WHERE target_key=? AND {expr} IS NOT NULL"
        f" ORDER BY 1, price_current_won", (target_key,)
    ):
        got = out.setdefault(key, [])
        if price is not None:
            got.append(price)
    return out


def _by_year(conn, target_key: str) -> list:
    """연식별 중앙값.  ★ 표본 5건 미만은 내지 않는다 — 시세로 믿게 된다."""
    groups = _group_prices(conn, target_key, "substr(year_month,1,4)")
    counts = dict(conn.execute(
        "SELECT substr(year_month,1,4), COUNT(*) FROM core_listing "
        "WHERE target_key=? AND year_month IS NOT NULL GROUP BY 1",
        (target_key,)))
    out = []
    for ym in sorted(counts, reverse=True):
        prices = groups.get(ym, [])
        enough = len(prices) >= MIN_SAMPLE
        out.append(Bucket(f"{ym}년", None, None, counts[ym],
                          _median(prices) if enough else None,
                          f"/listings?target={target_key}&year={ym}", enough))
    return out


def _year_line(rows: list, root: str = ".") -> list:
    """연식별 중앙값을 선으로 그릴 좌표 (개정 340).

    ★ 화면이 좌표를 계산하지 않는다 (STEP 152).  여기서 낸다
    ★ 표본이 모자란 해는 점을 찍지 않는다 — 이으면 없는 값을 만든다
    """
    got = [(r.label, r.median_won) for r in rows if r.median_won]
    if len(got) < 2:
        return []
    got.sort()                       # 연식 오름차순 — 왼쪽이 옛 차다
    pad = _view_cfg("chart_line_pad_pct", root)
    lo = min(v for _y, v in got)
    hi = max(v for _y, v in got)
    span = (hi - lo) or 1
    room = 100 - pad * 2
    out = []
    for i, (year, won) in enumerate(got):
        out.append({
            "year": year, "won": won,
            "x": round(i * 100 / (len(got) - 1), 1),
            # ★ 위가 비싼 쪽이다.  SVG 는 아래가 y 가 크다 — 뒤집는다
            "y": round(pad + room - (won - lo) * room / span, 1),
        })
    return out


def _by_trim(conn, target_key: str, top: int = TRIM_ROWS) -> list:
    """트림별 중앙값.  ★ 항목마다 돌지 않는다 — 한 번에 받는다 (V11-34)."""
    groups = _group_prices(conn, target_key, "trim_badge")
    out = []
    for trim, cnt in conn.execute(
        "SELECT trim_badge, COUNT(*) FROM core_listing WHERE target_key=? "
        "AND trim_badge IS NOT NULL GROUP BY 1 ORDER BY 2 DESC LIMIT ?",
        (target_key, top)
    ):
        prices = groups.get(trim, [])
        enough = len(prices) >= MIN_SAMPLE
        out.append(Bucket(trim, None, None, cnt,
                          _median(prices) if enough else None,
                          f"/listings?target={target_key}"
                          f"&trim={quote(trim, safe='')}", enough))
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
    # ★★ 개정 427 — 이 한 쿼리로 둘을 만든다.
    #   ① A등급 중앙가 (차종별 표)  ② ★ 차종별 시세 사분위 (시세 흡수)
    #   ★ 따로 부르면 현황이 21쿼리가 되어 상한 20 을 넘는다 (실측 08-21)
    price_rows = conn.execute(
        "SELECT l.target_key, l.price_current_won, s.grade FROM result_score s "
        "JOIN core_listing l ON l.listing_id = s.listing_id "
        "WHERE s.calc_version = ? "
        "AND l.price_current_won IS NOT NULL ORDER BY 1, 2",
        (calc_version,)).fetchall()
    prices: dict = {}
    all_prices: dict = {}
    for tk, p, g in price_rows:
        all_prices.setdefault(tk, []).append(p)
        if g == "A":
            prices.setdefault(tk, []).append(p)
    market_rows = _quartiles_by_target(all_prices)

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

    # ★ 조치가 필요한 것 — 네 물음을 한 번에 센다 (V11-34 · STEP 95)
    counts = conn.execute(
        "SELECT (SELECT COUNT(*) FROM meta_field_usage "
        "        WHERE usage='unclassified'), "
        "       (SELECT COUNT(*) FROM dict_enum WHERE status='pending'), "
        "       (SELECT COUNT(DISTINCT axis) FROM result_axis "
        "        WHERE excluded=1 AND source IN "
        "        ('gate_closed','coefficient_out_of_range')), "
        # ★ STEP 95 — 「확인 필요」는 넷이다.  검증 warn 이 빠져 있었다.
        #   ★ 같은 쿼리에 붙인다 — 따로 부르면 상한 20 을 넘는다 (V11-34)
        # ★ 이 화면이 보여 주는 그 실행의 warn 이다.  다른 실행 것을 섞지
        #   않는다 — 「어제 통과, 오늘도 통과」로 잘못 읽힌다 (A-7 · V1-16)
        "       (SELECT COUNT(*) FROM audit_validation "
        "        WHERE severity='warn' AND passed=0 AND applicable=1 "
        "          AND run_id=?)", (run_id,)
        ).fetchone()
    attention = []
    for n, kind, detail, action in (
        (counts[0], "unclassified", "등록부 미분류 경로",
         "config/field_usage.suggested.json 을 확인·수정해 "
         "config/field_usage.json 으로 옮긴 뒤 재실행한다"),
        (counts[1], "pending", "사전 미검토 값",
         "원문 표본 3건을 확인해 confirmed 로 올린 뒤 S9 를 재실행한다"),
        (counts[2], "undecided", "미확정으로 분모에서 빠진 축",
         "감가 곡선·색상 목록을 확정한다"),
        # ★ v1 은 이런 것이 조용히 지나갔다.  첫 화면에 띄운다 (STEP 95)
        (counts[3], "warn", "검증 warn — 진행은 되지만 확인이 필요하다",
         "python3.11 tools/check_all.py 로 warn 목록을 본다"),
    ):
        if n:
            attention.append(AttentionItem(kind, detail, n, action))

    # ★ 같은 집계를 두 번 돌면 화면 한 쪽이 그만큼 늘어난다 (V11-34 · B-2)
    # ★ 개정 427 — 등급 분포는 위 by_target 을 접으면 나온다.  다시 묻지 않는다.
    #   ★ 쿼리 둘(등급 집계 · 전체 건수)을 여기서 없앤다 — 그 자리에
    #     STEP 95 의 「사라짐 목록」·「축별 미달」을 넣는다
    grade_counts = _grade_counts(conn, calc_version, by_target)
    grade_total = sum(grade_counts.values())

    steps = _step_rows(conn, run_id)

    # ★ STEP 95 — 축별 미달.  「어느 축에서 떨어지는가」가 판단 재료다
    axis_shortfall = _axis_shortfall(conn, calc_version)
    # ★ 개정 427 — 사라짐 목록 · 관심매물 요약.  ★ 한 쿼리로 둘을 받는다
    gone_rows, watch_summary = _gone_and_watch(conn, account, root)

    return DashboardView(
        meta=ReportMeta(run_id, "L3", "encar", None, calc_version, None),
        viewer=viewer_state(account),
        target_stats=stats, recent_changes=changes,
        # ★ 차종별 시세 사분위 (개정 427) — 같은 쿼리로 만들었다
        market_rows=market_rows,
        # ★ 상위 후보 — 점수순이 아니다.  view_recommend 와 같은 순서다
        # ★ 현황판은 등급·가격만 낸다.  상태·시세는 안 받는다 (V11-34)
        # ★ 현황판에서도 「왜 이 순위인가」와 시세차를 봐야 한다 (개정 304).
        #   다만 상태·옵션 조회는 끈다 — 이유는 축 점수로 만든다 (V11-34 쿼리 상한)
        finalists=view_recommend(
            account, conn, ListingFilter(calc_version=calc_version),
            fin_cfg, root, with_state=False)[:5],
        grade_counts=grade_counts,
        # ★ 막대 높이를 화면이 계산하지 않는다 (STEP 152).
        #   첫 화면에 그림이 하나도 없으면 무엇이 있는지 모른다 (개정 340)
        grade_rows=_bars([{"grade": k, "count": v}
                          for k, v in grade_counts.items()], "count", root),
        grade_total=grade_total,
        e_reasons=_e_reasons(conn, calc_version),
        today_changes=_today_changes(conn),
        steps=steps,
        # ★★ STEP 95 — v1 블록 넷이 선언만 되고 비어 있었다 (실측 08-22).
        #   DashboardView 에 자리는 있는데 view_dashboard 가 안 채웠다 —
        #   ★ 「선언과 실제의 괴리」다.  채운다
        relax_sim=_relax_sim(grade_counts, root),
        axis_shortfall=axis_shortfall,
        watch_summary=watch_summary,
        # ★ 개정 427 — 사라짐 목록 · 진행률
        gone_rows=gone_rows,
        progress=_progress(steps),
        # 주의 항목은 관리자만 본다 — 조치가 관리자 행동이다
        attention=attention if account.role == ROLE_ADMIN else [])


# 등급 표시 차례.  ★ 색을 쓰지 않으므로 순서가 유일한 단서다 (STEP 145a)
# 수집 단계 이름.  ★ 「없음(not_found)」과 「실패」는 뜻이 다르다
STEP_LABELS = {"list": "S1 목록", "detail": "S5 상세",
               "inspection": "S5 성능점검", "record": "S5 이력",
               "diagnosis": "S6a 진단", "catalog": "S7 카탈로그",
               "facet": "S2 분류"}


def _bars(rows: list, key: str, root: str = ".") -> list:
    """막대 높이(%)를 붙인다 (개정 340).

    ★ 화면이 나눗셈을 하지 않는다 (STEP 152).  여기서 낸다
    ★ 0 이 아닌데 안 보이면 「없다」로 읽힌다 — 최소 높이를 준다
    """
    least = _view_cfg("chart_bar_min_pct", root)
    top = max((r.get(key) or 0) for r in rows) if rows else 0
    for one in rows:
        got = one.get(key) or 0
        one["pct"] = (max(least, round(got * 100 / top))
                      if top and got else 0)
    return rows


def _grade_counts(conn, calc_version: str, by_target: dict | None = None) -> dict:
    """등급 분포.

    ★ by_target 을 주면 묻지 않는다 (V11-34).  현황은 이미 차종×등급을
      받아 왔다 — 접으면 같은 수가 나온다.  두 번 세면 화면이 그만큼 늘어난다
    """
    if by_target is not None:
        got: dict = {}
        for grades in by_target.values():
            for g, n in grades.items():
                got[g] = got.get(g, 0) + n
    else:
        got = {r[0]: r[1] for r in conn.execute(
            "SELECT grade, COUNT(*) FROM result_score WHERE calc_version=? "
            "GROUP BY grade", (calc_version,))}
    return {g: got.get(g, 0) for g in GRADE_ORDER}


def _relax_sim(grade_counts: dict, root: str = ".") -> list:
    """조건 완화 시뮬레이션 (STEP 95).

    ★ 「A 이상 0건」만 내면 사람이 다음에 무엇을 할지 모른다.
      ★ 한 단계 낮추면 몇 건이 되는지를 함께 낸다 — 그것이 다음 행동이다
    ★ 순위를 안 매기는 셋(제외·등급 없음·평가 불가)은 세지 않는다 (STEP 84)
    """
    out = []
    upto = 0
    for i, grade in enumerate(RANK_ORDER):
        upto += grade_counts.get(grade, 0)
        if i + 1 >= len(RANK_ORDER):
            break
        nxt = RANK_ORDER[i + 1]
        out.append(RelaxRow(
            condition=f"{grade} 이상",
            current=upto,
            relaxed=upto + grade_counts.get(nxt, 0)))
    return out


def _axis_shortfall(conn, calc_version: str) -> list:
    """축별 미달 건수 (STEP 95) — ★ 어느 축에서 떨어지는가.

    ★ 「확인 안 됨」을 미달로 센다.  value 가 아니라 source 로 가른다
      (개정 435 · V3-96) — value NULL 로 세면 15,709건이 조용히 빠진다
    ★ 잃은 점수까지 낸다.  건수만으로는 어느 축이 아픈지 모른다
    """
    out = []
    for axis, n, lost in conn.execute(
        "SELECT axis, COUNT(*), SUM(max_points) FROM result_axis "
        "WHERE calc_version=? AND source IN "
        "      ('missing','site_unavailable','nothing_picked') "
        "GROUP BY axis ORDER BY SUM(max_points) DESC", (calc_version,)
    ):
        out.append({"axis": axis, "count": n,
                    "lost_points": round(lost or 0.0, 1)})
    return out


def _progress(steps: list) -> dict:
    """수집 진행률 (개정 427).

    ★ 「없음(not_found)」은 실패가 아니다 — 그 매물에 없는 것이다 (V6-06).
      ★ 분모에서 뺀다.  넣으면 진행률이 까닭 없이 낮게 보인다
    """
    req = ok = failed = 0
    for one in steps:
        req += (one.requested or 0) - (one.missing or 0)
        ok += one.ok or 0
        failed += one.failed or 0
    return {"requested": req, "ok": ok, "failed": failed,
            "pct": round(ok * 100 / req, 1) if req else 0.0}


def _gone_and_watch(conn, account, root: str = ".") -> tuple:
    """사라짐 목록 · 관심매물 요약 (STEP 95 · 개정 427).

    ★ 한 쿼리로 둘을 받는다 — 따로 부르면 현황이 상한 20 을 넘는다 (V11-34)
    ★ gone 을 「팔렸다」로 적지 않는다.  목록에서 사라진 것이다 (V6-06)
    ★ 사라짐은 두 갈래다 — 우리 status 가 내려간 것과
      사이트 sales_status 가 CONTRACT(계약) 로 바뀐 것.  둘 다 낸다
    """
    labels = _labels(root)["STATUS_LABELS"]
    gone, watch = [], []
    for kind, lid, tk, trim, price, old, new, at in conn.execute(
        "SELECT 'gone', c.listing_id, l.target_key, l.trim_badge, "
        "       l.price_current_won, c.old_value, c.new_value, c.changed_at "
        "  FROM core_listing_change c "
        "  JOIN core_listing l ON l.listing_id = c.listing_id "
        " WHERE c.change_kind='status' "
        "   AND ((c.field='status' AND c.new_value IN ('gone','out_of_scope')) "
        "     OR (c.field='sales_status' AND c.new_value='CONTRACT')) "
        "UNION ALL "
        "SELECT 'watch', w.primary_listing_id, l.target_key, l.trim_badge, "
        "       l.price_current_won, w.status, w.memo, w.added_at "
        "  FROM watch_item w "
        "  JOIN core_listing l ON l.listing_id = w.primary_listing_id "
        " WHERE w.account_id = ? "
        " ORDER BY 8 DESC", (getattr(account, "account_id", 0) or 0,)
    ):
        row = {"listing_id": lid, "target_key": tk or "차종 미정",
               "trim": trim, "price_won": price, "at": (at or "")[:10]}
        if kind == "gone":
            # ★ 원문 값을 그대로 두지 않는다.  뜻을 적는다
            # ★ 처음 본 값은 「앞」이 없다.  ★ 지어내지 않는다 —
            #   화면이 화살표를 안 그린다 (앞이 없으면 「지금 무엇인가」만 낸다)
            row["from_label"] = labels.get(old, old) if old else ""
            row["to_label"] = labels.get(new, "계약 중" if new == "CONTRACT"
                                         else new)
            gone.append(row)
        else:
            row["status_label"] = labels.get(old, old)
            row["memo"] = new
            watch.append(row)
    return gone[:TODAY_ROWS], watch[:TODAY_ROWS]


def _e_reasons(conn, calc_version: str) -> dict:
    """E 사유별 건수.

    ★ 「제외 33건」만 내면 사람이 아무것도 못 한다.  왜인지가 판단 재료다.
      absolute_fail 은 여러 사유가 「; 」로 붙는다 — 쪼개서 센다
    """
    out: dict = {}
    for (reason,) in conn.execute(
        # ★ 개정 433 — 배제는 EXCLUDED 다
        "SELECT absolute_fail FROM result_score "
        "WHERE calc_version=? AND grade='EXCLUDED'", (calc_version,)
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
    # ★★ 리스 제외는 /listings · /recommend 에만이다 (개정 420).
    #   관심은 사람이 이미 고른 것이다 — 빼면 담아 둔 차가 사라진다.
    #   실측 08-21 — 안 켰더니 관심 목록이 통째로 비었다 (V11-119 가 잡았다)
    flt = ListingFilter(calc_version=calc_version, lease=True)
    by_id = {r.listing_id: r
             for r in view_listings(account, conn, flt, fin_cfg, root)}
    spark = _bulk_spark(conn, [r[1] for r in rows])
    # ★ 묶되 「N번 재등록」을 낸다 (V7-14 · 개정 355).
    #   내렸다 다시 올린 것은 그 자체가 정보다 — 묶어서 지우지 않는다
    times = relist_counts(conn)
    vids = dict(conn.execute(
        "SELECT listing_id, vehicle_id FROM core_listing"
        " WHERE listing_id IN (%s)" % ",".join(
            "?" * len(rows)), [r[1] for r in rows])) if rows else {}
    out = []
    for wid, lid, target, added, closed, memo in rows:
        listing = by_id.get(lid)
        if listing is None:
            continue          # 아직 채점 전이다 — 조용히 빼지 않고 다음 회차에
        got = times.get(vids.get(lid)) or {}
        out.append(WatchRow(watch_id=wid, listing=listing,
                            target_price_won=target, added_at=added,
                            closed_at=closed, memo=memo,
                            spark=spark.get(lid, ()),
                            relist_times=got.get("times", 0),
                            # ★ 값이 안 바뀌었으면 안 낸다 — 같은 값을
                            #   「3,200만 → 3,200만」이라 내면 읽는 사람이 헷갈린다
                            relist_low_won=(got.get("low_won")
                                            if got.get("low_won")
                                            != got.get("high_won") else None),
                            relist_high_won=got.get("high_won")))
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
    n_field = conn.execute(
        "SELECT COUNT(*) FROM meta_field_usage WHERE usage='unclassified'"
    ).fetchone()[0]
    n = n_field
    if n:
        reasons.append(f"등록부 미분류 {n}건 — V4-11 이 판정을 막는다")
        actions.append("config/field_usage.suggested.json 을 확인·수정해 "
                       "config/field_usage.json 으로 옮긴 뒤 재실행한다")
    rows, oos, n_null, n_oos = _unmatched_rows(conn)
    n_ok = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE target_key IS NOT NULL"
    ).fetchone()[0]
    if n_null:
        reasons.append(f"모르는 차 {n_null:,}건 — 판정 대상이 아니다")
        actions.append("아래 모델명·배지를 보고 targets.json 의 "
                       "fuel_match · trim_include 를 고치거나 그대로 둔다")
    if n_oos:
        # ★ 묻는 자리가 아니다 — ★ 마스터가 「제외해」로 정하셨다 (`UI_REVIEW` 9a)
        reasons.append(f"범위 밖 {n_oos:,}건 — 아는 차인데 갈래가 다르다 "
                       f"(마스터 결정 「제외해」)")
    return NotReadyView(
        ReportMeta(run_id, "L3", "encar", None, calc_version, None),
        reasons, actions,
        pending_values=_pending_values(conn),
        done=_done_items(conn, calc_version),
        unmatched=rows, unmatched_total=n_null, matched_total=n_ok,
        out_of_scope=oos, out_of_scope_total=n_oos,
        field_unclassified=n_field)


def _unmatched_rows(conn, limit: int | None = None) -> tuple[list, list]:
    """차종이 안 붙은 매물을 ★ **두 갈래로** 묶어 낸다 (개정 271 · V2-32 · `UI_REVIEW` 9a).

    ★ 「4,188건」만 내면 사람이 아무것도 못 한다.
      「그랜저 가솔린 706건」이라야 targets.json 을 고칠지 정한다
    ★★ 08-24 마스터 결정 「제외해」 — ★ 둘은 ★ 뜻이 다르다
       ★ 미분류   ★ 모르는 차다.  ★ **묻는 자리**다
       ★ 범위 밖  ★ 아는 차인데 ★ 갈래(연료·트림)가 다르다.  ★ **건수만** 낸다
       ★ ★ GV70 가솔린 1,161건은 ★ 「모르는 차」가 아니다 — ★ 우리가 전기만 등록했다
    돌려줌  (미분류 줄, 범위 밖 줄, 미분류 합, 범위 밖 합)
    ★ 줄은 화면 몫만 자르되 ★ **합은 전건을 센다** — ★ 자른 것을 합으로 내면
      ★ 「이게 전부」로 읽힌다 (검토 17)
    """
    limit = _view_cfg("rows_per_page") if limit is None else limit
    from store.dictionary import known_model_of

    mine, oos, n_mine, n_oos = [], [], 0, 0
    for site, mf, mg, fuel, trim, n in conn.execute(
            # ★★ 모델명이 없으면 ★ 마스터가 정하실 수가 없다 (가이드 지시 08-24).
            #   ★ 새 사이트는 ★ 아는 차만 `site_model_group` 을 채운다 —
            #   ★ ★ 모르는 차는 ★ 차명이 `site_model` 에 있다.  ★ 그것을 낸다
            "SELECT site, site_manufacturer, "
            "       COALESCE(site_model_group, site_model), fuel_raw, "
            "       trim_badge, COUNT(*) "
            "FROM core_listing WHERE target_key IS NULL "
            "GROUP BY 1, 2, 3, 4 ORDER BY 6 DESC"):
        # ★ 시안이 ★ 사이트를 낸다 — ★ 「어느 사이트가 준 말인가」가 있어야 정한다
        row = {"site": site, "manufacturer": mf, "model_group": mg,
               "fuel": fuel, "trim": trim, "count": n}
        known = known_model_of(mg)
        if known:
            oos.append(dict(row, known=known)); n_oos += n
        else:
            mine.append(row); n_mine += n
    return mine[:limit], oos[:limit], n_mine, n_oos


# 리포트 파일 이름 — {run_id}_{layer}_{target|ALL}_{calc_version}.{ext}
# ★ 이름 규칙은 report/exports/export.py:filename 이 정본이다.
#   여기서 다시 정하지 않는다 — 갈리면 목록에 안 뜨는 파일이 생긴다
REPORT_NAME = re.compile(
    r"^(?P<run>[^_]+)_(?P<layer>L\d)_(?P<target>.+)_(?P<calc>[^_.]+)"
    r"\.(?P<ext>md|csv|json)$")


def _report_files(root: str = ".") -> list:
    """낼 수 있는 리포트 목록 (개정 357).

    ★ outputs/ 에는 작업 기록도 있다.  이름 규칙에 맞는 것만 낸다 —
      아무 파일이나 열어 주면 그것이 파일 새는 구멍이다
    """
    from datetime import datetime, timezone

    from report.exports.export import OUTPUT_DIR

    base = os.path.join(root, OUTPUT_DIR)
    if not os.path.isdir(base):
        return []
    out = []
    for name in sorted(os.listdir(base), reverse=True):
        got = REPORT_NAME.match(name)
        if not got:
            continue
        full = os.path.join(base, name)
        if not os.path.isfile(full):
            continue
        st = os.stat(full)
        layer = got.group("layer")
        out.append(ReportFile(
            name=name, layer=layer, ext=got.group("ext"), bytes=st.st_size,
            made_at=datetime.fromtimestamp(st.st_mtime,
                                           tz=timezone.utc).isoformat(),
            label=f"{REPORT_LAYERS.get(layer, layer)} · "
                  f"{got.group('target')} · {got.group('calc')}"))
    return out


def view_reports(account: Account, open_name: str | None = None,
                 root: str = ".") -> ReportsView:
    """리포트를 화면에서 읽는다 (8장 · 개정 357 · V11-122).

    마스터 확정 — 「목록을 보고 클릭하면 내용을 볼 수 있게 팝업 박스로.
    다운로드 누를 때 다운로드」
    ★ 열자마자 내려받지 않는다.  다운로드는 따로 누른다
    ★ 큰 파일은 앞부분만 낸다 — 상한은 config 다 (V4-13)
    """
    import csv as _csv
    import io as _io
    import json as _cfgjson

    from errors import ValidationError

    require_role(account, ROLE_USER)
    files = _report_files(root)
    if not open_name:
        return ReportsView(files=tuple(files))
    # ★ 목록에 있는 것만 연다.  임의 경로를 받으면 파일이 새 나간다
    known = {f.name: f for f in files}
    one = known.get(open_name)
    if one is None:
        raise ValidationError(f"열 수 없는 리포트입니다: {open_name[:60]}",
                              step="STEP 91b")
    with open(os.path.join(root, "config", "web.json"), encoding="utf-8") as f:
        cap = int(_cfgjson.load(f)["report_preview_bytes"])
    from report.exports.export import ENCODING, OUTPUT_DIR

    with open(os.path.join(root, OUTPUT_DIR, one.name),
              encoding=ENCODING) as f:
        body = f.read(cap + 1)
    cut = len(body) > cap
    body = body[:cap]
    rows: tuple = ()
    head: tuple = ()
    if one.ext == "csv":
        got = list(_csv.reader(_io.StringIO(body)))
        # ★ 잘렸으면 마지막 줄은 반쪽일 수 있다.  버린다
        if cut and got:
            got = got[:-1]
        head = tuple(got[0]) if got else ()
        rows = tuple(tuple(r) for r in got[1:])
        body = ""
    return ReportsView(files=tuple(files), open_name=one.name,
                       open_ext=one.ext, open_text=body, open_rows=rows,
                       open_head=head, truncated=cut, open_bytes=one.bytes)


# ══════════════════════════════════════════════════════════════════════
# ★★ /detail/<id> — 11절 (개정 427 · STEP 97a)
#   정본은 ref/screens/v2_시안_목록상세.html
#   ★ 마스터 확정 — 「목록은 간략하게 상세는 최대한 모든 정보」
#   ★ 다만 최종 확인과 실물 사진은 엔카에서 본다 — 상세는 「갈지 말지」까지다
# ══════════════════════════════════════════════════════════════════════

def _warranty_until(conn, listing_id: int, root: str = ".") -> dict:
    """보증 잔여 → ★ 「언제까지 · 몇 km 까지」 (명령서 13-2 ⑦).

    ★ 우리가 가진 것은 ★ 남은 개월이다.  ★ 오늘에 더해 ★ 끝나는 달을 낸다
    ★ 0 개월은 ★ 「만료」다 — ★ 확인한 값이라 그렇게 적는다
    ★ 없으면 ★ 빈 것이다.  ★ 「없다」로 적지 않는다 (개정 325)
    """
    from datetime import datetime, timezone

    row = conn.execute(
        "SELECT warranty_body_month, warranty_body_km,"
        " warranty_power_month, warranty_power_km, target_key"
        " FROM core_listing WHERE listing_id=?", (listing_id,)).fetchone()
    if row is None:
        return {}
    # ★ 제조사 보증 기간표에 ★ 글로 남긴 것이 있으면 함께 낸다 (명령서 16-2 ⓐ) —
    #   ★ BMW 는 ★ 「주행거리 무제한」이라 ★ km 칸에 넣을 수가 없다.
    #   ★ 큰 수를 넣으면 ★ 「무제한」과 「모름」이 섞인다
    note = ""
    try:
        with open(os.path.join(root, "config", "scoring.json"),
                  encoding="utf-8") as f:
            said = ((json.load(f).get("axis_rules") or {}).get("warranty") or {})
        table = ((said.get("maker_default") or {}).get("by_target") or {})
        got = table.get(row[4] or "")
        rows = got if isinstance(got, list) else [got or {}]
        for one in rows:
            if isinstance(one, dict) and one.get("warranty_note"):
                note = str(one["warranty_note"])
                break
    except (OSError, ValueError, AttributeError):
        note = ""
    now = datetime.now(timezone.utc)
    out: dict = {}
    for key, month, km in (("general", row[0], row[1]),
                           ("power", row[2], row[3])):
        if month is None:
            continue
        if int(month) <= 0:
            out[key] = "만료" + (f" ({int(km):,}km 까지)" if km else "")
            continue
        total = (now.year * 12 + now.month - 1) + int(month)
        y, m = divmod(total, 12)
        said = f"{y}년 {m + 1}월까지"
        out[key] = said + (f" ({int(km):,}km 까지)" if km
                           else (f" ({note})" if note else ""))
    return out


def _verdict_lines(v, row, root: str = ".") -> list:
    """1절 — ★ 「왜 그 등급인가」를 **문장으로** 쓴다 (V11-160).

    ★ 점수 나열이 아니다.  「같은 트림·옵션 기준 시세보다 410만원 쌉니다」
    ★ 지어내지 않는다 — 값이 없으면 그 줄을 안 쓴다
    """
    # ★ 문장에 HTML 을 담지 않는다.  머리 · 굵게 · 꼬리 셋으로 나눠 준다 —
    #   화면이 이스케이프를 못 하면 원문 글자가 태그가 될 수 있다 (STEP 152)
    out = []

    def say(tone, head, strong="", tail=""):
        out.append({"tone": tone, "head": head, "strong": strong,
                    "tail": tail})

    # 값 — 시세보다 싼가
    if row is not None and row.market_gap_won is not None:
        gap = row.market_gap_won
        opt = (f" 옵션값 {_manwon_str(row.option_price_won)}을 더해 견줬습니다."
               if row.option_price_won else "")
        say("g" if gap < 0 else "r", "같은 트림·옵션 기준 시세보다 ",
            _manwon_str(abs(gap)),
            (" 쌉니다." if gap < 0 else " 비쌉니다.") + opt)
    # 차량 — 사고·골격
    if row is not None:
        for chip in row.axis_chips:
            if chip.axis == "state.accident" and chip.state:
                say("g" if "무사고" in chip.state else "r", "", chip.state, ".")
                break
    # 보증 · 검증 — ★ 얼마나 원문으로 확인했는가
    if v.site_badge or v.confirm_pct:
        say("g", "확인율 ", f"{v.confirm_pct:.0f}%",
            f" — {v.denominator:.0f}점 중 {v.confirmed_points:.0f}점을 "
            f"원문으로 확인했습니다.")
    # 취향
    if v.strengths:
        say("o", "원하시는 ", " · ".join(v.strengths[:3]), " 가 맞습니다.")
    # 약점 — ★ 좋은 말만 하지 않는다
    for w in v.weaknesses[:2]:
        say("r", "", str(w), ".")
    return out


def _manwon_str(won) -> str:
    """원 → 「N,NNN만」.  ★ 표기를 한 자리에 모은다 (V4-13)."""
    if won is None:
        return ""
    return f"{int(won) // 10_000:,}만"


def _unknown_lines(conn, listing_id: int, calc_version: str,
                   root: str = ".") -> list:
    """5절 ★ 아직 모르는 것 — 갈래 ②③④ 가 여기 들어간다 (개정 434 · 435).

    ★ 「확인 안 됨」은 source 에 있다.  value 로 가르지 않는다 (개정 435)
    ★ 누구 잘못인지 함께 낸다 — ① 딜러 · ②③④ 우리
    """
    import json as _j

    with open(os.path.join(root, "config", "unknown_split.json"),
              encoding="utf-8") as f:
        cfg = _j.load(f)
    labels = _labels(root).get("AXIS_LABELS", {})
    out = []
    for axis, value, source, cap in conn.execute(
            "SELECT axis, value, source, max_points FROM result_axis"
            " WHERE listing_id = ? AND calc_version = ?"
            " ORDER BY max_points DESC", (listing_id, calc_version)):
        if not is_unknown(source):
            continue
        one = cfg["axes"].get(axis) or {}
        kind = one.get("kind_override") or ("3" if source == "site_unavailable"
                                            else "1")
        out.append({
            "axis": axis, "label": labels.get(axis, axis),
            "points": cap or 0, "kind": kind,
            "whose": "우리" if kind in ("2", "3", "4") else "딜러",
            "why": cfg["_kinds"].get(kind, ""),
            "got": value or 0})
    return out


def _price_history(conn, listing_id: int) -> list:
    """8절 ★ 가격 추이 — 등록가 → 현재가 · 변동 N회 · 최저가."""
    rows = conn.execute(
        "SELECT changed_at, old_value, new_value FROM core_listing_change"
        " WHERE listing_id = ? AND field = 'price_current_won'"
        " ORDER BY changed_at", (listing_id,)).fetchall()
    out = []
    for at, old, new in rows:
        try:
            o, n = int(old), int(new)
        except (TypeError, ValueError):
            continue
        out.append({"at": (at or "")[:10], "old": o, "new": n,
                    "down": n < o, "diff": n - o})
    return out


def _alternatives(account, conn, row, flt, fin_cfg, root: str = ".") -> list:
    """11절 ★ 이 차 대신 볼 것 — **왜 나은지 한 줄** (V11-161 자매).

    ★ 「비슷한 차」 나열이 아니다.  ★ 사이트는 이것을 못 한다 — 파는 쪽이라서다
    """
    if row is None or not row.target_label:
        return []
    # ★ 같은 차종만 · 40건만.  ★ 이 화면은 「대신 볼 것 넷」이면 된다
    # ★ 이 절이 쓰는 것은 등급·가격·주행뿐이다 (본 질의에 이미 들어 있다).
    #   ★ extras 를 켜면 시세·옵션·상태를 또 받아 한 쪽 쿼리가 곱절이 된다 (V11-34)
    near = view_listings(account, conn,
                         _rep_flt(flt, target_key=row.target_label,
                                  listing_id=None, page=1, model=None),
                         fin_cfg, root, extras=False, with_state=False,
                         page_size=40)
    out = []
    for other in near:
        if other.listing_id == row.listing_id:
            continue
        why = []
        if (other.grade or "") < (row.grade or "") and other.grade:
            why.append(f"등급이 {other.grade} 로 높습니다")
        if (other.price_won or 0) and (row.price_won or 0) \
                and other.price_won < row.price_won:
            why.append(f"{_manwon_str(row.price_won - other.price_won)} 쌉니다")
        if (other.mileage_km or 0) and (row.mileage_km or 0) \
                and other.mileage_km < row.mileage_km:
            why.append("주행이 적습니다")
        if not why:
            continue                     # ★ 왜 나은지 못 쓰면 안 낸다
        out.append({"row": other, "why": " · ".join(why[:2])})
        if len(out) >= 4:
            break
    return out


def _rep_flt(flt, **kw):
    from dataclasses import replace as _r

    return _r(flt, **kw)


def view_detail(account: Account, conn, listing_id: int, calc_version: str,
                fin_cfg: dict, policy: dict, root: str = ".") -> dict:
    """/detail/<id> — 11절 (STEP 97a).  ★ /why 를 흡수한다.  주소는 살린다."""
    v = render_listing(conn, listing_id, calc_version, fin_cfg, policy, root)
    # ★ 그 매물만 집는다.  ★ 전건을 읽고 파이썬에서 고르지 않는다 (V11-34)
    flt = ListingFilter(calc_version=calc_version, lease=True,
                        excluded=False, listing_id=listing_id, show_all=True)
    # ★ with_state 를 끄면 3쿼리가 준다 (실측 08-21 — 8 → 5).
    #   ★ 옵션가·상태는 render_listing 이 이미 받아 온 v 에 있다 — 두 번 안 받는다
    # ★ opt_money=True — 상세 ②절이 신차가·선택 옵션가를 낸다 (개정 301)
    rows = view_listings(account, conn, flt, fin_cfg, root, page_size=2,
                         with_state=False, opt_money=True)
    if not rows:
        # ★ 제외된 매물도 상세는 열려야 한다 — 왜 제외됐는지가 판단 재료다
        rows = view_listings(account, conn, _rep_flt(flt, excluded=True),
                             fin_cfg, root, page_size=2, with_state=False,
                             opt_money=True)
    row = rows[0] if rows else None
    # ★ 템플릿은 == 비교를 못 한다 (V11-104).  ★ 고르는 일은 여기서 한다
    by_axis = {a.axis: a for a in v.axes}
    # ★ 보증을 ★ 날짜로 낸다 (명령서 13-2 ⑦ · UI_REVIEW 7장).
    #   ★ 렉서스는 「2030년 10월까지 (120,000km)」를 준다 — ★ 점수만 내면 언제까진지 모른다
    w_until = _warranty_until(conn, listing_id, root)
    return {
        "v": v, "row": row,
        "warranty_general": by_axis.get("warranty.general"),
        "warranty_power": by_axis.get("warranty.power"),
        "warranty_general_until": w_until.get("general"),
        "warranty_power_until": w_until.get("power"),
        "verdict": _verdict_lines(v, row, root),
        "unknowns": _unknown_lines(conn, listing_id, calc_version, root),
        "history": _price_history(conn, listing_id),
        "alts": _alternatives(account, conn, row, flt, fin_cfg, root),
        "rep_raw": v.raw_sections,
    }


def _quartiles_by_target(by: dict) -> list:
    """차종별 사분위 (개정 427).  ★ 조회는 부르는 쪽이 한다 —
    현황이 이미 받아 온 값을 다시 받지 않기 위해서다 (V11-34)."""
    qs = MARKET_QUANTILES
    out = []
    for key, prices in sorted(by.items()):
        if not prices:
            continue
        ps = sorted(prices)

        def at(p, _ps=ps):
            return _ps[min(len(_ps) - 1, int(len(_ps) * p))]

        mid = at(qs[1])
        out.append({"target_key": key or "차종 미정", "count": len(ps),
                    "min_won": ps[0], "p25_won": at(qs[0]),
                    "median_won": mid, "p75_won": at(qs[2]),
                    "max_won": ps[-1],
                    # ★ 넓은지 좁은지 — 사분위 폭을 중앙값으로 나눈다
                    "spread_pct": round((at(qs[2]) - at(qs[0])) / mid * 100, 1)
                    if mid else 0.0})
    return out


def market_by_target(conn, root: str = ".") -> list:
    """★ 차종별 시세표 (개정 427) — /market 이 하던 것이 현황으로 온다.

    ★ 「사분위」다.  중앙값 하나만 내면 넓은지 좁은지를 모른다
    ★ 한 쿼리로 전 차종을 센다 — 차종마다 부르면 열 쿼리가 된다 (V11-34)
    """
    rows = conn.execute(
        "SELECT target_key, price_current_won FROM core_listing"
        " WHERE price_current_won IS NOT NULL AND status <> 'out_of_scope'"
        " ORDER BY target_key, price_current_won").fetchall()
    by: dict = {}
    for key, won in rows:
        by.setdefault(key, []).append(won)
    qs = MARKET_QUANTILES
    out = []
    for key, prices in sorted(by.items()):
        def at(p, _ps=prices):
            return _ps[min(len(_ps) - 1, int(len(_ps) * p))]

        out.append({"target_key": key, "count": len(prices),
                    "min_won": prices[0], "p25_won": at(qs[0]),
                    "median_won": at(qs[1]), "p75_won": at(qs[2]),
                    "max_won": prices[-1],
                    # ★ 넓은지 좁은지 — 사분위 폭을 중앙값으로 나눈다
                    "spread_pct": round(
                        (at(qs[2]) - at(qs[0])) / at(qs[1]) * 100, 1)
                    if at(qs[1]) else 0.0})
    return out
