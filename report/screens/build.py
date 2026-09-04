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

# ★★★ 설정 캐시 — ★ 실측 08-28.  `/detail` 한 장이 ★ config 를 27,336번 열었다
#   (scoring 11,795 · unknown_split 7,761 · web 6,206 · sites 1,552).
#   ★ 31KB 짜리를 만 번 파싱해 ★ 한 장에 8.6초를 썼다 — ★ 규격 상한은 2.0초다
#   (`config/web.json` screen_max_sec).  ★ DB 쿼리는 1ms 대였다 —
#   ★ 느린 것은 ★ 쿼리가 아니라 ★ 이쪽이었다
# ★ 파일이 바뀌면 다시 읽는다 (mtime · 크기).  ★ 관리 화면이 config 를 고쳐도
#   ★ 다음 요청이 새 값을 받는다 — ★ 서버를 껐다 켜지 않아도 된다
# ★ 돌려준 것을 ★ 고치지 않는다.  ★ 같은 객체를 나눠 쓴다
#   (전 사용처가 읽기만 하는 것을 확인했다 · 08-28).  ★ 안쪽을 내주는
#   `_view_list` · `_view_dict` 는 ★ 베껴서 낸다 — ★ 캐시가 더럽혀지지 않게
_JSON_CACHE: dict = {}


# ★★★ 08-29 — ★ 「되묻는 창」(1초)을 ★ 넣었다가 ★ **되돌렸다.**
#   ★ `os.stat` 27,393회를 없애 ★ 0.077초를 벌었지만,
#   ★ ★ 관리 화면에서 ★ 저장하고 되돌아온 화면이 ★ **옛 값을 낼 수 있었다** —
#     ★ 되돌림(redirect)이 ★ 그 창 안에 들어간다.
#   ★ ★ 그것이 ★ 이 프로젝트가 막으려는 ★ 「선언과 실제의 괴리」다.
#     ★ 7.7% 를 벌자고 ★ 감수할 것이 아니다.  ★ mtime 을 늘 본다
def load_config(path: str) -> dict:
    """설정을 읽는다.  ★ 파일이 그대로면 지난번 것을 그대로 준다."""
    st = os.stat(path)
    stamp = (st.st_mtime_ns, st.st_size)
    key = os.path.abspath(path)
    hit = _JSON_CACHE.get(key)
    if hit is not None and hit[0] == stamp:
        return hit[1]
    with open(path, encoding="utf-8") as fp:
        data = json.load(fp)
    _JSON_CACHE[key] = (stamp, data)
    return data

# 리포트 계층 이름 (STEP 91).  ★ 코드가 아니라 사람 말로 낸다
REPORT_LAYERS = {"L1": "매물 리포트", "L2": "차종 리포트", "L3": "실행 리포트"}
from report.render import render_listing, render_run
from analyze.trust import SOURCE_WORDS, inspection_source, platform_trust
from report.why_cheap import verdict as why_verdict
from report.screens.views import (
    MIN_SAMPLE,
    RecommendAxis,
    RecommendRow,
    RecommendView,
    Bucket,
    ExcludedGroup,
    PendingValue,
    StepRow,
    TodayChange,
    TONE_BAD, TONE_GOOD, TONE_MUTED, TONE_UNKNOWN,
    AttentionItem, AxisChip, AxisPoint, ChangeRow, CompareView, DashboardView,
    DealerRow,
    TrackPair, TrackView,
    ListingFilter, ListingRow, MarketRow, MarketView, NotReadyView,
    RelaxRow, ReportFile, ReportsView,
    SoldBin, SoldRow, SoldView,
    WatchRow,
    TargetStat, ViewerState,
)
from report.views import AxisView, ReportMeta, VersionStamp
from contracts import ROLE_ADMIN, ROLE_USER, Account, require_role
from store.core import photo_ready_sites
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

# ★★★★★ 09-02 시안 `lst-axes`·`rc-axes` (`S46-98`·`S46-242`) —
#   ★ 「색상 (외장) 25/25 · 색상 (내장) 10/10 · 크기 (전장) 9/31 · 트림 17/20」
#   ★★ **취향 넷**이다.  ★ 마스터 09-01 — 「★ 크기·내장색 축이 화면에 안 보인다」.
#     ★ ★ 이름은 ★ `config/labels.json` 이 원천이다 — ★ 코드에 안 박는다 (`S14`)
POINT_AXES = ("taste.color", "taste.color_int", "taste.size", "taste.trim")


def site_badge(site: str | None, sell_type: str | None,
               root: str = ".") -> str:
    """사이트 배지 — 「엔카」 · 「K카 직영」 · 「K카 직거래」 (50-multisite).

    ★ 사이트 이름을 코드에 박지 않는다.  config/sites.json 이 정본이다
    ★ 판매 유형을 함께 내는 사이트만 낸다.  엔카의 sell_type 은
      「일반·렌트·리스」로 용도지 판매 유형이 아니다 —
      그것을 붙이면 「엔카 렌트」가 배지가 된다
    """
    sites = load_config(f"{root}/config/sites.json")
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
# ★★ 명령서 67장 — 상세를 못 받아 근거가 절반도 없는 매물.  등급이 아니다
PENDING = "PENDING"



def _labels(root: str = ".") -> dict:
    return load_config(f"{root}/config/labels.json")


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
    return load_config(
        _os_lbl.path.join(_ROOT_LBL, "config", "unknown_split.json"))


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
    import os as _o

    here = _o.path.dirname(_o.path.dirname(_o.path.dirname(
        _o.path.abspath(__file__))))
    return float(
        load_config(_o.path.join(here, "config", "scoring.json"))
        ["total_points"])



def _photo_note(site, photos, base: str, ready) -> str | None:
    """★★★★★ 09-02 (1부 1-4 · `RULES.md` 2) — ★ 사진이 없으면 ★ **까닭**을 낸다.

    ★ 마스터께서 09-01 에 ★ 「왜 안 보이지」를 ★ 네 번 물으셨다.
      ★ ★ 화면이 ★ 까닭을 말했으면 ★ 안 물으셨을 것이다.
    ★★ 가른다 —
      ★ ㉮ 그 사이트에서 ★ **한 장도 못 받았다** → ★ 「우리가 아직 못 받았다」
      ★ ㉯ 같은 사이트의 다른 매물엔 있다 → ★ 「그 매물에 사진이 없다」
    ★ 사진이 있으면 ★ `None` 이다 — ★ 쓸데없는 말을 안 낸다
    """
    if photo_url(photos, base):
        return None
    name = (_site_labels().get(str(site)) or str(site or "이 사이트"))
    if site and ready is not None and str(site) not in ready:
        # ★ 「보배드림**는**」은 틀린 말이다.  ★ 받침이 있으면 「은」이다.
        #   ★ 한글 낱자 셈 — ★ (코드 − 0xAC00) % 28 이 0 이 아니면 받침이 있다
        last = name[-1]
        has_jong = ("가" <= last <= "힣") and (ord(last) - 0xAC00) % 28
        return f"{name}{'은' if has_jong else '는'} 사진을 아직 못 받았습니다"
    return "이 매물에는 사진이 없습니다"


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
    for i, p in enumerate(photos):
        # ★★★★★ 09-02 명령서 12 (`S46-243`) — ★ **꼴이 사이트마다 다르다.**
        #   ★ 마스터 09-01 — 「★ 사진이 하나도 안 보이고」.
        #   ★★ 까닭을 쟀다 [실측 09-02] — ★ 밑주소가 아니었다.
        #     ★ 엔카만  `{"location": "/carpicture…", "ordering": …}` 꼴이고
        #     ★ ★ K카·차차차·리본카·볼보·렉서스는 ★ **온전한 주소 글월**이다
        #       ★ ★ (`["https://img.kcar.com/…", …]`).
        #     ★ ★ ★ `isinstance(p, dict)` 에서 ★ **다섯 사이트가 통째로 버려졌다**
        #   ★ 온전한 주소는 ★ 밑주소를 **안 붙인다** — ★ 붙이면 두 번 들어간다
        if isinstance(p, str):
            u = p.strip()
            if u.startswith(("http://", "https://")):
                got.append((float(i), u))     # ★ 차례는 적힌 차례다
            continue
        if not isinstance(p, dict):
            continue
        loc = p.get("location")
        if not loc:
            continue
        loc = str(loc)
        if loc.startswith(("http://", "https://")):
            url = loc                          # ★ 이미 온전하다
        elif loc.startswith("/"):
            url = f"{base}{loc}"
        else:
            continue
        try:
            o = float(p.get("ordering"))
        except (TypeError, ValueError):
            o = float("inf")       # 순서를 모르면 맨 뒤 — 있는 것을 버리지 않는다
        got.append((o, url))
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
    # ★★★★★ 09-02 명령서 12 — ★ **`photo_urls` 하나로 모은다.**
    #   ★ 전에는 ★ 여기서 ★ 꼴을 **따로 풀었다** — ★ 그래서 `photo_urls` 만
    #   ★ ★ 고치면 ★ 목록 대표 사진은 ★ 그대로 안 나온다.
    #   ★ ★ ★ 같은 일을 두 군데 적으면 ★ 한 군데만 고치는 일이 생긴다 (`S14`)
    got = photo_urls(photos_json, base)
    return got[0] if got else None


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
        # ★★★★★ 09-02 마스터 물음 ① — ★ **보험과 성능점검은 다른 것이다**.
        #   ★ 보험 = ★ 보험금이 나갔는가 · ★ 성능점검 = ★ 골격이 상했는가
        #   ★★ 「★ 보험 건수가 있으면 ★ **「무사고」라 쓰지 마라**」 (`S46-218`)
        #     ★ ★ 이 축은 ★ **보험 이력**을 센다 — ★ 그러니 ★ 그렇게 적는다
        mycnt, _cost, othcnt, tot = rec
        n = tot if tot is not None else (mycnt or 0) + (othcnt or 0)
        return "보험 이력 없음" if not n else f"보험 {n}건"
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
         photo_base: str = "", site_tpl: dict | None = None,
         photo_sites: set | None = None,
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
     _site, _sell_type, _mismatch, _kmpl, _seats,
     _sites_n, _dupe_low, _dupe_high, _sales_status,
     _region, _shop, _site_model) = rec
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
    # ★★★★★ 09-02 — ★ 시안 `lst-axes` 줄.  ★ **몇 점인지**를 낸다.
    #   ★ 미확인(`excluded`)은 ★ `got=None` — ★ 0점과 가른다 (금지 12)
    _pts = []
    for _a in POINT_AXES:
        _v = got.get(_a)
        if _v is None:
            continue
        _full = float(_v[3] or 0)
        if not _full:
            continue        # ★ 배점이 0 인 축은 ★ 안 낸다
        _pts.append(AxisPoint(
            label=(labels.get("AXIS_LABELS", {}) or {}).get(_a, _a),
            got=(None if _v[1] else float(_v[0] or 0)), full=_full))

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
        # ★ 「N곳」 배지 — ★ 1 이면 안 낸다 (겹친 것이 없다)
        site_count=int(_sites_n or 1), multi_site=int(_sites_n or 1) > 1,
        # ★ 값 폭 — ★ 배지에 「2,890~3,260만」으로 낸다
        dupe_low_won=_dupe_low, dupe_high_won=_dupe_high,
        listing_id=lid, grade=grade or NOT_RATED,
        # ★★ 감점 (개정 491) — 상한을 먹인 뒤의 합과 문구
        penalty_won=_pen_sum(pen_json),
        penalty_labels=_pen_words(pen_json),
        # ★★★★★ 09-02 — ★ 가장 큰 감점 하나 (접힌 채로 보인다)
        penalty_top=_pen_top(pen_json),
        # ★★★★★ 09-02 마스터 확정 — ★ 연식·거리에 ★ 셈을 함께 낸다
        age_label=_age_label(ym),
        km_per_year_label=_km_per_year(ym, km),
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
        # ★★ 「판정 중」도 마찬가지다 (명령서 67장).  근거가 절반도 없다
        rank=None if (grade or NOT_RATED) in (NOT_RATED, PENDING) else rank,
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
        # ★ 막대 둘째 칸 — ★ 음수가 되지 않게 0 에서 자른다 (부록 G A-3)
        confirm_extra_pct=max(0.0, round(
            _confirm[1] * 100
            - (g_earned / g_base * 100 if g_base else 0), 1)),
        # ★ 값을 누르면 그 조건으로 걸러진다 (부록 G).  없으면 링크를 안 만든다
        price_bucket_won=_bucket(price, _view_int("price_bucket_won", root)),
        mileage_bucket_km=_bucket(km, _view_int("mileage_bucket_km", root)),
        status_key=dstatus or None,
        # ★★★ 08-29 (마스터 3번) — ★ 「팔린 것을 목록에서 뺐다」를 되돌린다.
        #   ★ 마스터 — 「두고 딱지만 · 흐리게 · 맨 뒤」.
        #   ★ ★ 얼마에 팔렸는지가 ★ 다음 판단에 쓰인다 (v281 답)
        sold=bool(dstatus == "gone"
                  or str(_sales_status or "").upper() in _sold_words(root)),
        # ★ `gone` 은 ★ 옆의 상태 링크가 ★ 이미 「내려감」이라 적는다 —
        #   ★ 딱지까지 달면 ★ 같은 말이 두 번이다.  ★ 그때는 안 단다.
        #   ★ 흐리게·맨 뒤는 ★ 그대로 걸린다 (`sold` 는 참이다)
        sold_label=_sold_words(root).get(str(_sales_status or "").upper()),
        target_label=tk or "",
        # ★ 세부등급을 못 받았으면 그렇게 적는다.  빈 값으로 두지 않는다 (개정 285)
        trim=(trim if trim and " · " in trim
              else f"{trim} · 세부등급 없음" if trim else ""),
        trim_detail_known=bool(trim and " · " in trim),
        # 옵션 — 「5종 890만」.  ★ 「옵션 있음」 같은 말을 쓰지 않는다 (개정 313)
        option_count=len(_codes) if isinstance(_codes, list) else 0,
        year_month=ym, mileage_km=km,
        color_ext=ce, color_int=ci, axis_chips=chips, price_won=price,
        axis_points=tuple(_pts),
        # ★ 어느 사이트에서 왔는지 매물마다 낸다 (V9-06).
        #   화면이 「엔카」를 글자로 박고 있었다 — 사이트가 둘이 되면 거짓말이다
        site_badge=site_badge(_site, _sell_type, root),
        # ★★★★★ 09-02 마스터 확정 — ★ **판매지역**을 사이트 딱지 옆에 (`S46-225`)
        region_label=region_of(_site, _region, _shop, root),
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
        # ★ 시안의 「시세보다 400만 싸다」 (S46-98 · 마스터 08-26).
        #   ★ 표본이 모자라면 안 낸다 — ★ 「모르는 것을 모른다고 낸다」(개정 325)
        market_gap_label=_market_gap_label(_gap_won, mkt),
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
        # ★★★★★ 09-02 (1부 1-4) — ★ **조용히 비우지 않는다** (`RULES.md` 2).
        #   ★ 「우리가 못 받았다」와 ★ 「그 매물에 없다」를 ★ 가른다
        photo_note=_photo_note(_site, photos, photo_base, photo_sites),
        source_id=sid,
        # ★ source_id 가 없으면 링크를 만들지 않는다.  깨진 주소를 내지 않는다
        # ★★★ 원문 문은 ★ 그 매물의 사이트로 간다 (명령서 72장 · 실측 08-26).
        #   ★ 전에는 엔카 주소 하나로 다 만들어 ★ K카 매물이
        #     `encar.com/…?carid=EC61384014` 로 갔다.  ★ 엔카는 모르는 carid 에도
        #     200 을 준다 — 「200 이면 됐다」로 세지 않는다 (S46-87 과 같은 잣대)
        #   ★ 못 잰 사이트는 ★ **안 낸다.**  ★ 지어내지 않는다 (검산 S46-94)
        encar_url=_source_url(_site, sid, site_tpl, _site_model),
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
    where = load_config(
        os.path.join(root, "config", "scoring.json")).get("penalty_axis") or {}
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


MONTHS_PER_YEAR = 12
KM_PER_MAN = 10_000


def _ym_parts(ym) -> tuple:
    """연식 → (해, 달).  ★ `202207` 도 `2022-07` 도 받는다 [실측 09-03].

    ★ 화면은 ★ `2023-05` 꼴로 들고 있다 — ★ 여섯 자리만 보면 ★ 못 읽는다
    ★ 못 읽으면 ★ `(None, None)` 이다 — ★ 지어내지 않는다
    """
    got = re.sub(r"[^0-9]", "", str(ym or ""))
    if len(got) < 6:
        return None, None
    return int(got[:4]), int(got[4:6])


def _age_label(ym, as_of: str | None = None) -> str:
    """★★★★★ 09-02 — ★ 「연식 2022-07 ★ **(3년 2개월)**」.

    ★ 못 재면 ★ 빈 글자다 — ★ 지어내지 않는다
    """
    from datetime import datetime, timezone

    y0, m0 = _ym_parts(ym)
    if y0 is None:
        return ""
    now = (datetime.fromisoformat(str(as_of).replace("Z", "+00:00"))
           if as_of else datetime.now(timezone.utc))
    n = (now.year - y0) * MONTHS_PER_YEAR + (now.month - m0)
    if n < 0:
        return ""
    y, m = divmod(n, MONTHS_PER_YEAR)
    if y and m:
        return f"{y}년 {m}개월"
    return f"{y}년" if y else f"{m}개월"


def _km_per_year(ym, km, as_of: str | None = None) -> str:
    """★★★★★ 09-02 — ★ 「주행 139,571km ★ **(연 4.4만)**」.

    ★ 마스터 — 「★ **한 해에 얼마나 탔나**가 ★ 많이 탔는지를 가른다」
    ★ 한 해가 안 됐으면 ★ 안 낸다 — ★ 늘려 잡으면 거짓이 된다
    """
    from datetime import datetime, timezone

    y0, m0 = _ym_parts(ym)
    if km is None or y0 is None:
        return ""
    now = (datetime.fromisoformat(str(as_of).replace("Z", "+00:00"))
           if as_of else datetime.now(timezone.utc))
    months = (now.year - y0) * MONTHS_PER_YEAR + (now.month - m0)
    if months < MONTHS_PER_YEAR:
        return ""
    per = float(km) / (months / MONTHS_PER_YEAR)
    return f"연 {per / KM_PER_MAN:.1f}만"


def _pen_top(raw) -> str:
    """★★★★★ 09-02 마스터 확정 — ★ **가장 큰 감점 하나**를 겉에 낸다.

    ★ 마스터 — 「★ 지금 「감점 -40」이라고만 나온다.  ★ **무엇 때문인지 안 낸다**」
    ★ 「상한」 줄은 ★ 되돌린 몫이라 ★ 안 고른다 — ★ 흠이 아니다
    ★ 없으면 ★ 빈 글자다 — ★ 지어내지 않는다
    """
    got = [x for x in _pen_words(raw) if not x["is_cap"]]
    if not got:
        return ""
    one = min(got, key=lambda x: float(x["points"] or 0))
    return f"{one['label']} {one['points']}"


def _view_cfg(key: str, root: str = ".") -> int:
    """화면 표시 정책.  ★ 코드에 박지 않는다 (config/web.json)."""
    return int(load_config(os.path.join(root, "config", "web.json"))[key])


# ★ 개정 433 — 8단계 + 순위를 안 매기는 것 셋 (제외·등급 없음·평가 불가)
GRADE_ORDER = RANK_ORDER + NOT_RANKED
# 가격 분포 칸 수 · 오늘 변동 줄 수.  ★ 표시 정책이라 코드에 박지 않는다
PRICE_BINS = _view_cfg("price_bins")
TRIM_ROWS = _view_cfg("trim_rows")
TODAY_ROWS = _view_cfg("today_rows")
MS_PER_SEC = 1000.0


def _grade_rank_sql() -> str:
    """등급 차례대로 세우는 SQL.  ★ 정본은 `config/labels.json` 이다 (S14).

    ★ 알파벳순이 아니다 — ★ S · A · B · C · D · E · F · G 차례다
    """
    whens = " ".join(f"WHEN '{g}' THEN {i}" for i, g in enumerate(RANK_ORDER))
    return f"(CASE s.grade {whens} ELSE {len(RANK_ORDER)} END) ASC"


# 정렬 1단.  ★ 뒤 3단은 어느 축을 골라도 그대로 붙는다 (STEP 106a · E-3)
ORDER_SQL = {
    # ★ earned/denominator 다.  score_total 은 555 환산이라 분모가 다른
    #   매물이 잘못 섞인다 (E-1 · E-3)
    "rank": "(s.earned * 1.0 / NULLIF(s.denominator, 0)) DESC",
    # ★★★ 08-26 — ★ 전에는 ★ `s.grade ASC` 였다.  ★ **알파벳순**이라
    #   ★ ★ 'S'(최고)가 ★ 'A'~'G' 뒤로 갔다 — ★ 등급순인데 ★ 등급 차례가 아니었다.
    #   ★ 차례의 정본은 ★ `config/labels.json` 의 `GRADE_ORDER` 다 (개정 433 · S14)
    "grade": _grade_rank_sql(),
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
# ★★★ 08-26 — ★ `s.grade IS NULL` 을 ★ 빠뜨리고 있었다.
#   ★ ★ 실측 — ★ 판정 행이 아예 없는 매물이 ★ **9,097건**이다 (`LEFT JOIN`).
#   ★ ★ SQL 에서 ★ `NULL IN (…)` 은 ★ NULL 이라 ★ `CASE` 가 ★ ELSE 0 을 준다 —
#     ★ ★ 곧 ★ 「순위를 매기는 것」으로 세어졌고, ★ `ASC` 에서 ★ NULL 이 맨 앞이라
#     ★ ★ **등급순 첫 쪽이 「평가 불가」 30장**이었다 (마스터 08-26 지적 ②).
#     ★ ★ 그것들은 ★ 순위가 없으므로 ★ 「N위」 자리에 ★ 「순위 없음」이 떴다
ORDER_HEAD = ("(CASE WHEN s.grade IS NULL OR s.grade IN ("
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


# ★★★ 08-29 (마스터 3번) — ★ 팔린 것은 ★ **맨 뒤**다.
#   ★ 빼지 않는다 — ★ 두되 ★ 뒤로 보낸다.  ★ `ORDER_HEAD`(순위 없음)보다
#     ★ **앞에** 둔다 — ★ 그래야 ★ 무엇보다도 뒤로 간다
def _sold_words(root: str = ".") -> dict:
    """★★★★ 「사이트가 준 낱말」 → 「우리 말」.  ★ 정본은 `config/labels.json` 이다 (S14).

    ★★★ 08-30 — ★ 전에는 ★ `('CONTRACT','RESERVED')` 를 ★ **코드에 박고** 있었다.
      ★ ★ 그래서 ★ K카가 주는 ★ `resvYn=Y` **118건**(우리 대상 22건)이
      ★ ★ 화면에 ★ **「판매 중」으로 서 있었다** (마스터 지시 08-30 · 3번).
    ★ 낱말의 근거는 ★ `docs/chapters/11-store/a-key.md` 08-29 절이다 —
      ★ ★ 개발측이 지어 넣지 않는다 (규칙 2)
    """
    try:
        with open(os.path.join(root, "config", "labels.json"),
                  encoding="utf-8") as fp:
            got = json.load(fp).get("SALES_STATUS_SOLD") or {}
    except (OSError, ValueError):
        got = {}
    return {str(k).upper(): v for k, v in got.items()}


def _order_sold(root: str = ".") -> str:
    """팔린 것을 ★ 맨 뒤로 미는 정렬 조각.  ★ 낱말은 설정에서 온다."""
    words = sorted(_sold_words(root))
    if not words:
        return "(CASE WHEN l.status = 'gone' THEN 1 ELSE 0 END)"
    # ★ 낱말에 따옴표가 들어갈 일이 없지만 ★ 그래도 막는다
    lst = ",".join("'" + w.replace("'", "''") + "'" for w in words)
    return ("(CASE WHEN l.status = 'gone'"
            f" OR UPPER(COALESCE(l.sales_status,'')) IN ({lst})"
            " THEN 1 ELSE 0 END)")


ORDER_SOLD = _order_sold()


def order_clause(order: str) -> str:
    """5단 정렬.  ★ 축을 바꿔도 뒤 3단은 남는다.  ★ 팔린 것은 늘 맨 뒤다.

    ★★★★ 08-29 (마스터 지시 4 · 시험자 #101) — ★ `first` 를 ★ `ORDER_HEAD` **앞**으로.
      ★ 시험자 실측 — ★ 「`grade`·`dom` 이 ★ `rank` 와 같은 순서」.
      ★ 재 봤다 (08-29) — ★ `grade` 는 ★ `rank` 와 ★ **여덟 줄이 똑같았다**.
      ★★ 까닭 — ★ 고른 축보다 ★ `ORDER_HEAD`(순위 없음을 뒤로)가 ★ **앞서 있었다**.
        ★ ★ 그러면 ★ 고른 축은 ★ 그 안에서만 갈리고 ★ 뒤 3단(`ORDER_TAIL`)이
          ★ ★ 다시 `rank` 로 끝내 ★ 고른 축이 ★ 안 보인다.
    ★ `ORDER_SOLD` 는 ★ **맨 앞 그대로**다 — ★ 팔린 것은 무엇으로 고르든 뒤다
    """
    first = ORDER_SQL.get(order, ORDER_SQL["rank"])
    # ★★★★★ 09-03 (1부 1-9 · 시험자 101) — ★ **등급순이 점수순과 똑같았다.**
    #   ★ 실측 09-03 — ★ 앞 **200행이 한 자리도 안 다르다**.
    #   ★★ 까닭을 쟀다 — ★ **등급은 점수 비율의 계단 함수**다:
    #     ★ A 0.650~0.724 · B 0.570~0.649 · C 0.500~0.570 · … ★ **구간이 안 겹친다**.
    #     ★ ★ 그러니 ★ 「등급 → (같으면) 점수」는 ★ 「점수」와 ★ **늘 같은 차례**다.
    #   ★★★ 화면 결함이 아니라 ★ **두 이름이 한 차례를 가리키던 것**이다.
    #     ★ 「등급순」이 이름값을 하게 한다 — ★ 같은 등급 안에서는 ★ **값이 싼 차 먼저**.
    #     ★ ★ 등급은 「얼마나 좋은가」고 ★ 그 안에서 고를 잣대는 ★ 값이다.
    #   ★ 여쭐 것에 적었다 (안 ① 정렬을 없앤다 · **안 ② 값으로 가른다 ← 이것으로 갔다**)
    if order == "grade":
        # ★★ 4단(`ORDER_TAIL`)을 ★ **버리지 않는다** (`V6-07`) —
        #   ★ 「E 뒤로 → 비율 → 가격 → listing_id」가 ★ 마지막 잣대다.
        #   ★ ★ 값을 ★ **그 앞**에 끼워 ★ 같은 등급 안에서 값이 먼저 갈리게 한다
        return (f"{ORDER_SOLD}, {first}, {ORDER_HEAD},"
                f" l.price_current_won ASC, {ORDER_TAIL}")
    return f"{ORDER_SOLD}, {first}, {ORDER_HEAD}, {ORDER_TAIL}"


def _site_detail_urls(root: str = ".") -> dict:
    """★★★ 사이트별 원문 주소 꼴 (명령서 72장).  ★ 코드에 박지 않는다.

    ★ 못 잰 사이트는 값이 None 이다 — ★ 「모른다」다.  ★ 링크를 안 낸다
    ★★★★★ 09-04 (4-8) — ★ `config/endpoints.json` 의 ★ **`web_url`** 도 읽는다.
      ★★★ 가이드 실측 09-04 — 「★ 링크·사진은 ★ **없는 게 아니라 ★ 안 낸 것**이었다」.
        ★ 리볼트 `https://www.revolt.kr/cars/{source_id}` ·
        ★ 볼보셀렉트 `https://selekt.volvocars.co.kr{detail_path}` 를 ★ 넣어 두셨다.
      ★★ `web.json` 이 ★ **먼저**다 — ★ 거기 값이 있으면 ★ 안 덮는다.
        ★ ★ 두 벌로 적지 않으려고 ★ **가이드가 잰 자리를 그대로 읽는다** (`S14`)
      ★ `{detail_path}` 는 ★ 그 사이트의 ★ `paths.detail` 로 편다 —
        ★ ★ 볼보는 `/kr/vehicles/volvo/{model}/{source_id}` 이고
        ★ ★ ★ `{model}` 은 ★ 우리 `site_model` 이다 (`xc40` · `v60-cross-country`).
        ★ ★ ★ ★ 그러면 ★ `_source_url` 의 ★ **두 칸 틀**이 그대로 받는다
    """
    got = dict(load_config(
        os.path.join(root, "config", "web.json")).get("site_detail_url") or {})
    ends = load_config(os.path.join(root, "config", "endpoints.json")) or {}
    for site, spec in ends.items():
        if site.startswith("_") or not isinstance(spec, dict):
            continue
        if got.get(site):
            continue                      # ★ web.json 이 먼저다
        web = spec.get("web_url")
        if not web:
            continue
        web = str(web)
        if "{detail_path}" in web:
            path = str((spec.get("paths") or {}).get("detail") or "")
            if not path:
                continue                  # ★ 펼 길이 없다 — ★ 지어내지 않는다
            web = web.replace("{detail_path}",
                              path.replace("{model}", "{site_model}"))
        got[site] = web
    return got


def _source_url(site: str, source_id: str, tpl: dict | None,
                site_model: str | None = None) -> str | None:
    """그 매물의 사이트로 가는 원문 주소.  ★ 없으면 None (명령서 72장).

    ★★★★★ 09-02 명령서 13 (`S46-94`) — ★ **두 칸**으로 늘렸다.
      ★ 「주소는 ★ 가이드가 다 쟀다 — ★ 너희는 재지 마라.  ★ 고칠 것은 하나 —
        ★ ★ `volvo_selekt` 틀에 `{site_model}` 이 더 든다」.
      ★ ★ 볼보는 ★ `…/xc40/b4-awd-…` 처럼 ★ **차종이 길에 든다**
        ★ ★ (실측 09-02 — `site_model` 이 `xc40` · `v60-cross-country`).
    ★★ 틀이 안 쓰는 칸은 ★ `format` 이 그냥 버린다 — ★ 나머지 열 사이트는 그대로다.
    ★ 틀이 바라는 칸이 ★ **비어 있으면** ★ `None` 이다 —
      ★ ★ `…/None/b4-awd-…` 같은 ★ **깨진 주소를 만들지 않는다** (금지 12)
    ★ `kcar` 는 ★ robots 가 막아 ★ 틀이 `None` 이다 (명령서 13) — ★ 그대로 둔다.
      ★ ★ 화면이 ★ 「그 사이트는 주소를 아직 못 쟀습니다」를 낸다 (명령서 14)
    """
    if not site or not source_id or not tpl:
        return None
    one = tpl.get(site)
    if not one:
        return None
    one = str(one)
    if "{site_model}" in one and not site_model:
        return None
    try:
        return one.format(source_id=source_id, site_model=site_model or "")
    except (KeyError, IndexError):
        # ★ 틀에 우리가 모르는 칸이 있다.  ★ 깨진 주소 대신 ★ **없다**로 낸다
        return None


def _view_str(key: str, root: str = ".") -> str:
    """화면 표시 정책 중 문자열.  ★ 코드에 박지 않는다 (config/web.json)."""
    return str(load_config(os.path.join(root, "config", "web.json"))[key])


def _lease_kinds(root: str = ".") -> tuple:
    """목록에서 뺄 리스·렌트 (개정 420).  ★ 값은 config 가 갖는다 (S14)."""
    cfg = load_config(f"{root}/config/web.json")
    return (list(cfg["lease_advertisement_types"]),
            list(cfg["lease_sell_types"]))


def paused_hidden(conn, flt: ListingFilter, root: str = ".") -> tuple:
    """★★★★★ 09-03 (1부 1-11) — ★ **쉬는 사이트 때문에 뺀 건수**.

    ★ 「몇 건을 안 보여 줬는지」를 안 적으면 ★ 사람은 ★ 「합이 안 맞는다」고 본다
    ★ 반환   (건수, 사이트 이름들)
    """
    from dataclasses import replace as _replace

    off = _paused_sites(root)
    if not off:
        return 0, ()
    # ★★ 조건과 값은 ★ **짝을 지어** 다뤄야 한다 — ★ 조건만 빼면 ★ 값이 밀린다.
    #   ★ 실측 09-03 — ★ 그렇게 했다가 ★ **0건**이 나왔다.
    #   ★ 그래서 ★ 「쉬는 사이트만」을 ★ 조건으로 걸어 ★ 그 사이트를 직접 센다
    try:
        where, args = _listings_where(_replace(flt, site=off[0]))
        keep, keep_args, i = [], [], 0
        for w in where:
            n_q = w.count("?")
            take = args[i:i + n_q]
            i += n_q
            if w == "l.site = ?":
                continue          # ★ 한 곳이 아니라 ★ 쉬는 곳 **전부**를 센다
            keep.append(w)
            keep_args.extend(take)
        n_all = int(conn.execute(
            "SELECT COUNT(*) FROM core_listing l"
            " LEFT JOIN result_score s ON s.listing_id = l.listing_id"
            " WHERE " + " AND ".join(keep)
            + " AND l.site IN (" + ",".join("?" * len(off)) + ")",
            [*keep_args, *off]).fetchone()[0])
    except sqlite3.Error:
        return 0, ()
    labels = _site_labels(root)
    return n_all, tuple(labels.get(s, s) for s in off)


def _topic(word: str) -> str:
    """★ 「보배드림**는**」은 틀린 말이다.  ★ 받침이 있으면 「은」이다.

    ★ 한글 낱자 셈 — ★ (코드 − 0xAC00) % 28 이 0 이 아니면 받침이 있다
    """
    last = (word or " ")[-1]
    if "가" <= last <= "힣" and (ord(last) - 0xAC00) % 28:
        return "은"
    return "는"


def paired_count(conn, flt: ListingFilter, root: str = ".") -> int:
    """★★★★★ 09-03 (1부 1-1 ① · `CROSS_SITE_COMPARE` 3b-2 · `S46-254`) —
    ★ **지금 걸린 조건 안에서** ★ 짝지어진 차가 몇 대인가.

    ★ 왜 수를 내나 — ★ 화면 글이 ★ 「「3곳」 배지를 누르면 추적으로」인데
      ★ ★ **1쪽에 배지가 하나도 없다** — ★ 그러면 그 글이 ★ **거짓말**이 된다.
      ★ ★ ★ 배지 대상의 가장 앞 차례가 ★ **233위**다 [실측 09-02].
    ★★ **전체 수가 아니다** — ★ 지금 걸린 조건 안에서 센다 (규격 「필수」).
    ★ 세는 자는 ★ 카드의 배지·거르개와 ★ **같은 것**이다 —
      ★ ★ 다르면 ★ 「N대」와 ★ 걸러 본 수가 어긋난다
    """
    from dataclasses import replace as _replace

    try:
        where, args = _listings_where(_replace(flt, paired=True))
        return int(conn.execute(
            "SELECT COUNT(*) FROM core_listing l"
            " LEFT JOIN result_score s ON s.listing_id = l.listing_id"
            " WHERE " + " AND ".join(where), args).fetchone()[0])
    except sqlite3.Error:
        return 0


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


def _option_blind_sites(root: str = ".") -> list:
    """옵션이 ★ 매물을 못 가르는 사이트 (마스터 확정 08-25).

    ★★ 현대인증 16가지는 ★ **인증 조건**이다 — ★ 없는 차는 인증을 못 받는다.
      ★ ★ 1,114건 ★ 전건이 같다 — ★ 거르개로 쓰면 ★ 통째로 걸린다
    ★ 점수·표시에는 ★ 그대로 쓴다 — ★ **거르개에서만** 뺀다
    ★ 사전 `discriminative: false` 가 정본이다 (S14)
    """
    import os as _o
    path = _o.path.join(root, "config", "dictionaries", "option_names.json")
    if not _o.path.isfile(path):
        return []
    got = load_config(path)
    return [k for k, v in (got.get("by_site") or {}).items()
            if v.get("discriminative") is False]


def _option_group_match(key: str, root: str = ".") -> list:
    """옵션 묶음의 말조각 (마스터 확정 08-25).

    ★ `config/dictionaries/option_names.json` 이 정본이다 (S14) —
      ★ 코드에 옵션 이름을 박지 않는다
    """
    import os as _o
    path = _o.path.join(root, "config", "dictionaries", "option_names.json")
    if not _o.path.isfile(path):
        return []
    got = load_config(path)
    return list(((got.get("groups") or {}).get(key) or {}).get("match") or ())


def fuel_groups(root: str = ".") -> list:
    """연료 갈래.  ★ 정본은 `config/web.json` 의 `fuel_groups` 다 (S14)."""
    import os as _o

    try:
        return list(load_config(
            _o.path.join(root, "config", "web.json")).get("fuel_groups") or ())
    except (OSError, ValueError):
        return []


def _fuel_where(key: str, root: str = ".") -> tuple:
    """★★ 연료 갈래 → (SQL, 값).  ★ 명령서 87장 (마스터 08-28).

    ★ 「전기만」은 ★ **정확히 `전기`·`EV`** 다 — ★ `가솔린+전기`(하이브리드)와
      ★ `수소+전기`(연료전지)는 ★ 안 든다.  ★ 검사 `S46-102` 가 지킨다
    ★ 갈래가 아니면 ★ 옛대로 ★ 값 하나로 견준다 (칩에서 눌러 온 것)
    """
    for one in fuel_groups(root):
        if one.get("key") != key:
            continue
        vals = one.get("values") or []
        if vals:
            marks = ",".join("?" * len(vals))
            return f"l.fuel_raw IN ({marks})", list(vals)
        sql, args = [], []
        ors = " OR ".join("l.fuel_raw LIKE ?" for _ in one.get("match") or [])
        if ors:
            sql.append("(" + ors + ")")
            args += [f"%{m}%" for m in one["match"]]
        for no in one.get("not") or []:
            sql.append("l.fuel_raw NOT LIKE ?")
            args.append(f"%{no}%")
        return " AND ".join(sql) or "1=1", args
    return "l.fuel_raw = ?", [key]


def _paused_sites(root: str = ".") -> tuple:
    """★ 쉬는 사이트 (`status: paused`).  ★ 정본은 `config/sites.json` 이다.

    ★ `paused` — ★ 「받았었으나 지금은 안 받는다」.  ★ `planned`(아직 안 받았다)와 다르다.
      ★ ★ 낱말 셋(`active`·`paused`·`planned`)은 ★ 규격이 정한다 (`S46-41`)
    """
    got = load_config(f"{root}/config/sites.json") or {}
    return tuple(sorted(
        k for k, v in got.items()
        if isinstance(v, dict) and v.get("status") == "paused"))


# ★★★★★ 09-03 (1부 1-1 · 브라우저 실측) — ★ **「살아 있다」의 자는 하나다.**
#   ★ 목록 본체는 ★ `l.status <> 'gone'` 으로 거른다 (아래 `_listings_where`).
#   ★ ★ 그런데 ★ 짝 맞추기 · 「N곳」 배지 · 같은 차 접기만 ★ `status='active'` 였다 —
#   ★ ★ ★ **자가 두 개였다.**
#   ★★ 실측 09-03 (브라우저로 배포를 열어 쟀다 · `tools/browser_verify.py`) —
#     ★ `/listings` 의 「짝지어진 차 N대」가 ★ **빈칸**이고 ★ 「N곳」 배지가 ★ **0개**이고
#     ★ ★ `?paired=1` 이 ★ **카드 0개**였다.  ★ 8회차째 안 닫힌 자리다.
#   ★★★ 까닭 — ★ 매물의 대부분이 ★ `new` 다 (`new` 4,963 ↔ `active` 871).
#     ★ ★ 짝을 ★ `active` 끼리만 맞추니 ★ **사이트 넘은 짝이 0쌍**이었다.
#     ★ ★ ★ 같은 자(`<> 'gone'`)로 재면 ★ **94쌍**이다.
#   ★★★★ 더 나쁜 것 — ★ 같은 차 접기가 ★ `active` 대표를 못 찾으면
#     ★ ★ 그 매물이 ★ **목록에서 아예 사라진다** (조건이 거짓이 된다).
#     ★ ★ ★ 번호판이 있는 살아 있는 매물이 ★ 1,526건인데 ★ `active` 는 871건뿐이다
# ★ 「팔린 것」은 ★ 여전히 짝이 아니다 — ★ `gone` 을 뺀다 (철학 ② 가 매긴다)
LIVE_STATUS_SQL = "status <> 'gone'"


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
    else:
        # ★★★★★ 09-01 마스터 확정 — ★ **쉬는 사이트는 화면에 안 낸다.**
        #   ★ 마스터 — 「★ 보배를 빼고 여기(리볼트) 것 쓰자」
        #   ★★ **행도 원문도 안 지운다** (P3) — ★ 여기서만 뺀다.
        #     ★ ★ 「보배만 보기」로 콕 집으면 ★ 그때는 나온다 (위 `flt.site`) —
        #     ★ ★ ★ **숨기는 것이 아니라 ★ 기본에서 빼는 것**이다
        #   ★ 정본은 ★ `config/sites.json` 의 `status` 다 — ★ 코드에 이름을 안 박는다
        off = _paused_sites()
        if off:
            where.append("l.site NOT IN (" + ",".join("?" * len(off)) + ")")
            args.extend(off)
    if getattr(flt, "sell_type", None):
        where.append("l.sell_type = ?")
        args.append(flt.sell_type)
    if not where:
        where.append("1=1")
    if flt.target_key:
        where.append("l.target_key = ?")
        args.append(flt.target_key)
    # ★★ 옵션 이름 (마스터 확정 08-25 · B) — ★ 이름을 주는 사이트에서만 걸린다.
    #   ★ 엔카는 ★ 숫자 코드만 준다 — ★ 그 매물은 ★ 안 걸린다 (거짓 양성이 없다)
    # ★★ 옵션 묶음 (마스터 확정 08-25) — ★ 말조각 어느 하나라도 들면 걸린다
    if getattr(flt, "option_group", None):
        got = _option_group_match(flt.option_group)
        if got:
            where.append("(" + " OR ".join(
                "l.options_standard_json LIKE ?" for _ in got) + ")")
            args.extend(f"%{m}%" for m in got)
    # ★★ 옵션으로 거를 때는 ★ 「전건이 같은」 사이트를 뺀다 (마스터 확정 08-25).
    #   ★ 안 빼면 ★ 현대인증 1,114건이 ★ 어느 옵션에나 걸린다
    if getattr(flt, "option_group", None) or getattr(flt, "option_name", None):
        blind = _option_blind_sites()
        if blind:
            where.append("l.site NOT IN (%s)" % ",".join("?" * len(blind)))
            args.extend(blind)
    if getattr(flt, "option_name", None):
        where.append("(l.options_standard_json LIKE ?"
                     " OR l.options_choice_json LIKE ?)")
        like = f'%{flt.option_name}%'
        args.extend([like, like])
    if getattr(flt, "mismatch", False):
        where.append(record_mismatch_sql())
    if getattr(flt, "paired", False):
        # ★★★★★ 09-03 (1부 1-1 ③) — ★ **짝지어진 것만.**
        #   ★ 「같은 차」의 자는 ★ 카드의 「N곳」 배지와 ★ **같아야 한다** —
        #   ★ ★ 번호판 **또는** 차대로 ★ 두 사이트 넘게 올라온 것이다.
        #   ★ ★ ★ 다른 자를 쓰면 ★ 「N대」와 ★ 걸러진 수가 어긋난다
        where.append(
            "(EXISTS (SELECT 1 FROM core_listing x"
            f"        WHERE x.{LIVE_STATUS_SQL}"
            "         AND x.plate_hash IS NOT NULL"
            "         AND x.plate_hash = l.plate_hash AND x.site <> l.site)"
            " OR EXISTS (SELECT 1 FROM core_listing y"
            f"        WHERE y.{LIVE_STATUS_SQL}"
            "         AND y.vin_hash IS NOT NULL"
            "         AND y.vin_hash = l.vin_hash AND y.site <> l.site))")
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
    # ★★ 같은 차가 여러 곳에 있으면 ★ **낮은 값 하나만** 낸다
    #   (마스터 확정 08-24 · v3_listings_시안 · S46-57).
    #   ★ ★ 두 번 나오면 안 된다 — ★ 다 펴는 자리는 ★ `/track` 이다
    #   ★ 매물 하나만 집을 때(상세·비교)는 ★ 접지 않는다 — ★ 그 줄을 못 찾는다
    if (getattr(flt, "listing_id", None) is None
            and not getattr(flt, "listing_ids", ())):
        where.append(
            "(l.plate_hash IS NULL OR l.listing_id = ("
            "  SELECT l2.listing_id FROM core_listing l2"
            "   WHERE l2.plate_hash = l.plate_hash"
            f"    AND l2.{LIVE_STATUS_SQL}"
            "   ORDER BY l2.price_current_won, l2.listing_id LIMIT 1))")
    # ★ 매물 하나만 (개정 427 상세).  ★ 맨 앞에 둔다 — 가장 좁은 조건이다
    # ★★★★ 08-28 — ★ 팔린 것 · 내려간 것 · 계약·예약중은 ★ **목록에 안 낸다**.
    #   ★★★ 가이드 — 「★ 팔리거나 취소된 매물이 ★ 왜 목록에 계속 보이나」 (두 번 물으셨다).
    #   ★ 시안이 정본이다 (마스터 08-28 ④) — ★ `v4m_listings_시안` 은
    #     ★ ★ 카드마다 ★ **「게시중」만** 낸다.  ★ 팔린 것도 예약중도 없다.
    #   ★ 실측 08-28 — ★ 목록 5,244건 안에 ★ 내려간 것 136 · 예약중 17 = ★ 153건이 섞여 있었다.
    #   ★ 지우지는 않는다 — ★ `gone_at` 이 「얼마에 팔렸나」의 근거다 (`store/core.mark_gone`).
    #     ★ ★ **목록에만 안 낸다.**  ★ 상세·추적으로는 그대로 볼 수 있다
    #   ★ 매물 하나만 집을 때는 접지 않는다 — ★ 그 줄을 못 찾는다
    # ★★★ 08-29 (마스터 3번) — ★ 되돌린다.  ★ 08-28 에 ★ 목록에서 뺐던 것을
    #   ★ ★ **다시 낸다** — ★ 「두고 딱지만 · 흐리게 · 맨 뒤」.
    #   ★ 까닭 — ★ 「얼마에 팔렸나」가 ★ 다음 판단의 재료다 (마스터 v281 답).
    #   ★ ★ 그 확정은 ★ 08-30 에 ★ 다시 뒤집혔다 — ★ 아래를 보라 (30-2)
    # ★★★★★ 08-30 (`UI_REVIEW` 30-2 · 마스터 확정 물음 #31·#35) —
    #   ★ 마스터 — 「★ **목록에는 있으나 ★ 화면 조회 목록에는 안 보여야 돼.
    #     ★ 다만 판매완료 목록과 통계에는 나와야 되고**」
    #   ★ 그래서 ★ **뜻이 뒤집힌다** — ★ 08-25 「두고 딱지만」을 ★ 이 확정이 대신한다.
    #   ★ ★ 기본이 ★ **안 보임**이고 · ★ `with_sold=1` 이면 ★ 함께 본다
    #     ★ ★ (거르개 「함께 보기」는 남긴다 — ★ 정보를 빼지 않는다 · 마스터 08-25)
    #   ★ 지우지 않는다 — ★ `core_listing` 에 남고 ★ `/sold` 와 통계에 나온다 (P3)
    #   ★ 매물 하나만 집을 때는 안 접는다 — ★ 그 줄을 못 찾는다
    if (not getattr(flt, "with_sold", False)
            and getattr(flt, "listing_id", None) is None
            and not getattr(flt, "listing_ids", ())):
        # ★ 낱말의 정본은 `config/labels.json` 이다 (S14).
        #   ★ 이 함수는 `root` 를 안 받는다 — ★ 기본 자리에서 읽는다
        words = sorted(_sold_words())
        where.append("l.status <> 'gone'")
        if words:
            marks = ",".join("?" * len(words))
            where.append("(l.sales_status IS NULL"
                         f" OR UPPER(l.sales_status) NOT IN ({marks}))")
            args.extend(words)
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
    # ★★ 08-28 (#8) — ★ `d.dealer_region` 은 ★ **없는 칸**이라 500 이었다.
    #   ★ `core_dealer` 에 있는 것은 `region` 이고, ★ 지역이 실제로 채워져 있는
    #     곳은 ★ `core_listing.dealer_region` 이다 (14,260건 · 실측 08-28).
    #   ★ `l` 을 쓰면 ★ 세는 쿼리에도 딜러 조인이 필요 없다
    for field, col in (("color_ext", "l.color_ext_raw"),
                       ("color_int", "l.color_int_raw"),
                       ("region", "l.dealer_region")):
        got = getattr(flt, field, None)
        if got:
            where.append(f"{col} = ?")
            args.append(got)
    # ★★ 연료는 ★ 갈래로 건다 (명령서 87장) — ★ 위 `_fuel_where` 참고
    if getattr(flt, "fuel", None):
        sql, vals = _fuel_where(flt.fuel)
        where.append("(" + sql + ")")
        args.extend(vals)
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
    # ★★ 08-28 (#10) — ★ `option_min` 이 ★ **어디에도 안 걸려 있었다.**
    #   ★ 화면에 칸이 있고 (`listings.html` 「깡통 빼기 N종 이상」)
    #     ★ `web/views.py` 가 받아서 필터에 담기까지 하는데
    #     ★ ★ WHERE 를 만드는 여기서 ★ 쓰지 않아 ★ 건수가 안 변했다.
    #   ★ 선택 옵션은 JSON 배열이다 — `["1050","1046",…]` (실측).
    #     ★ `json_valid` 로 감싼다 — ★ 배열이 아닌 행에서 죽지 않게
    if getattr(flt, "option_min", None) is not None:
        where.append("(json_valid(l.options_choice_json)"
                     " AND json_array_length(l.options_choice_json) >= ?)")
        args.append(flt.option_min)
    if getattr(flt, "no_bare", False):
        # ★★★★★ 09-03 (1부 1-10) — ★ **깡통 빼기.**
        #   ★ 「깡통」은 ★ 옵션가가 `bare_option_won` 이하인 차다 (마스터 확정 08-24).
        #   ★★ 옵션가는 ★ 코드 목록(`options_choice_json`)에 ★ 값을 곱해야 나온다 —
        #     ★ ★ SQL 로는 못 곱한다.  ★ 그래서 ★ **종 수**로 가른다:
        #     ★ ★ ★ 옵션이 ★ **하나도 없으면** ★ 그것이 깡통이다.
        #   ★ ★ ★ 값까지 보려면 ★ 판정이 낸 `option_price_won` 을 저장해야 한다 —
        #     ★ ★ ★ 그것은 규격 물음이라 ★ 회차에 적었다 (여쭐 것)
        where.append("(json_valid(l.options_choice_json)"
                     " AND json_array_length(l.options_choice_json) > 0)")
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
        cond = f"s.grade IN ({','.join('?' * len(ok))})"
        args += ok
        # ★★ 08-28 (#11) — ★ 「확인 못 한 것도 함께 보기」가 ★ **아무 일도 안 했다.**
        #   ★ 화면에 체크상자가 있는데 (`listings.html` 78행)
        #     ★ ★ 필터에 칸조차 없어 ★ 눌러도 건수가 그대로였다.
        #   ★ 뜻 — ★ 등급 거르개를 걸면 ★ 아직 등급이 안 매겨진 매물이 함께 빠진다.
        #     ★ 그것까지 보겠다는 것이다.  ★ 등급 목록은 config 가 정본이다 (S14)
        if getattr(flt, "unknown_too", False):
            und = [g for g in NOT_RANKED if g not in ok]
            cond = (f"({cond} OR s.grade IS NULL"
                    f" OR s.grade IN ({','.join('?' * len(und))}))")
            args += und
        where.append(cond)
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


def model_counts(conn: sqlite3.Connection, flt: ListingFilter) -> list:
    """차종 드롭다운의 건수 — ★ 목록과 ★ 같은 조건으로 센다.

    ★★★ 08-28 (#14 · #16) — ★ 드롭다운이 `KOLEOS_HEV (336건)` 이라 해 놓고
      ★ 고르면 ★ **183건**이 나왔다.  ★ 19종을 다 더하면 9,563 인데
      ★ 화면이 낼 수 있는 최대는 6,182 였다 (차 3,381).
    ★ 까닭 — ★ 옛 `store.core.listing_models` 는 ★ `status='active'` ★ 하나만 보고
      ★ 세었다.  ★ 목록은 ★ 리스 · 관문 제외 · 같은 차 접기 · 팔린 것 ·
      ★ 계약·예약중 · 범위 밖을 ★ 전부 뺀다 — ★ **두 수가 다른 것을 세고 있었다.**
    ★ 이제 ★ `_listings_where` 를 ★ 그대로 쓴다 —
      ★ 세는 것과 뽑는 것이 ★ 같은 조건이어야 한다 (V11-55 와 같은 뜻).
    ★ 차종 조건만 뺀다 — ★ 하나를 고르면 ★ 나머지가 0 이 되어 ★ 바꿔 고를 수 없다
    """
    from dataclasses import replace

    base = replace(flt, model=None, target_key=None)
    where, args = _listings_where(base)
    return [(k, n) for k, n in conn.execute(
        "SELECT l.target_key, COUNT(*) FROM core_listing l"
        " LEFT JOIN result_score s ON s.listing_id = l.listing_id"
        "  AND s.calc_version = ?"
        " LEFT JOIN core_dealer d ON d.dealer_id = l.dealer_id"
        f" WHERE {' AND '.join(where)} AND l.target_key IS NOT NULL"
        " GROUP BY l.target_key ORDER BY COUNT(*) DESC",
        [base.calc_version, *args])]


def count_listings(conn: sqlite3.Connection, flt: ListingFilter) -> int:
    """조건에 맞는 전체 건수 (V11-55).  ★ 쪽을 나누려면 전체를 알아야 한다.

    쿼리 1개를 더 쓴다 — 「몇 건 중 몇 건」을 못 내는 것보다 낫다 (V11-34 여유 안)
    """
    where, args = _listings_where(flt)
    # ★★ 08-28 (#9) — ★ 정직도(`d.trust_score`)로 거르면 ★ 여기서 500 이었다.
    #   ★ 뽑는 쿼리(`view_listings`)에는 ★ `core_dealer d` 조인이 있는데
    #     ★ ★ 세는 쿼리에는 없어 ★ 「없는 칸」이 됐다.
    #   ★ 조건을 만드는 곳이 하나면 ★ 조인도 같아야 한다 (이 함수 설명의 V11-55)
    return conn.execute(
        "SELECT COUNT(*) FROM core_listing l LEFT JOIN result_score s"
        " ON s.listing_id = l.listing_id AND s.calc_version = ?"
        " LEFT JOIN core_dealer d ON d.dealer_id = l.dealer_id"
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
        " l.spec_fuel_economy_kmpl, l.spec_seats,"
        # ★★ 「3곳」 배지 — ★ 같은 차가 올라간 사이트의 수 (v3_listings_시안).
        #   ★ 누르면 ★ `/track` 으로 간다.  ★ 1 이면 안 낸다
        # ★★ 값 폭 (가이드 지시 08-24) — ★ 「3곳 · 2,890~3,260만」.
        #   ★ 곳 수만 내면 ★ **얼마나 벌어졌는지 모른다**
        # ★★ 08-25 — ★ 서브쿼리 ★ **셋을 조인 하나로** 묶었다 (V11-34).
        #   ★ ★ 셋을 따로 두면 ★ 한 쪽에 ★ 쿼리가 셋씩 는다 —
        #     ★ ★ 실측 ★ 상한을 넘었다 (28).  ★ 값은 그대로다
        # ★ 09-02 — ★ 둘 중 **많이 잡은 쪽**을 쓴다 (위 주석 참고)
        "  MAX(COALESCE(dp.sites,1), COALESCE(dv.sites,1)),"
        "  MIN(COALESCE(dp.low_won, dv.low_won),"
        "      COALESCE(dv.low_won, dp.low_won)),"
        "  MAX(COALESCE(dp.high_won, dv.high_won),"
        "      COALESCE(dv.high_won, dp.high_won)),"
        # ★★★ 08-29 (마스터 3번) — ★ 팔린 것을 ★ 목록에 되돌린다.
        #   ★ 딱지를 달려면 ★ 「팔렸는지」를 ★ 행이 알아야 한다
        " l.sales_status,"
        # ★★★★★ 09-02 마스터 확정 — ★ **판매지역** (`S46-225`).
        #   ★ 엔카·KB 는 ★ 지역이 온다 · ★ K카·리본카·볼보는 ★ 지점 이름만 온다 —
        #   ★ ★ 그때는 ★ 규격 표(`dealer_region.json`)를 본다
        " l.dealer_region, l.dealer_shop,"
        # ★★★★★ 09-02 명령서 13 (`S46-94`) — ★ 볼보 원문 주소에 ★ **차종이 든다**
        #   (`…/xc40/b4-awd-…`).  ★ 칸을 **맨 뒤**에 붙였다 —
        #   ★ ★ 가운데 넣으면 ★ 아래 풀기의 번호가 전부 밀린다
        " l.site_model"
        " FROM core_listing l LEFT JOIN result_score s"
        " ON s.listing_id = l.listing_id AND s.calc_version = ?"
        " LEFT JOIN core_dealer d ON d.dealer_id = l.dealer_id"
        # ★ 같은 차 묶음 — ★ 곳 수·값 폭을 ★ 한 번에 받는다 (색인 `ix_listing_plate`)
        # ★★★★★ 09-02 (1부 1-1 · **8회차째**) — ★ **차대번호도 본다.**
        #   ★ 전에는 ★ **번호판만** 봤다.  ★ 그런데 ★ 추적 화면(`/track`)은
        #   ★ ★ **번호판＋차대**를 이어 붙여 짝을 짓는다 (`_pair_rows` 의 union-find).
        #   ★ ★ ★ 같은 「같은 차」를 ★ **두 자로 재고 있었다** — ★ 이 판의 가장 큰 실패다
        #     ★ ★ ★ (「선언과 실제의 괴리」 · `docs/guide/00_개요.md`).
        #   ★★ 실측 09-02 — ★ 번호판만 **154행** → ★ 번호판 또는 차대 **161행**.
        #     ★ ★ `/track` 의 176대와는 ★ 아직 다르다 — ★ union-find 는
        #       ★ ★ 「A—번호판—B—차대—C」까지 잇는데 ★ SQL 한 판으로는 못 잇는다.
        #       ★ ★ ★ 그 차이(15대)는 ★ 회차에 적었다 — ★ 지어내 메우지 않는다
        " LEFT JOIN (SELECT plate_hash k,"
        "                   COUNT(DISTINCT site) sites,"
        "                   MIN(price_current_won) low_won,"
        "                   MAX(price_current_won) high_won"
        "              FROM core_listing"
        f"            WHERE {LIVE_STATUS_SQL} AND plate_hash IS NOT NULL"
        "             GROUP BY plate_hash) dp"
        "   ON dp.k = l.plate_hash"
        " LEFT JOIN (SELECT vin_hash k,"
        "                   COUNT(DISTINCT site) sites,"
        "                   MIN(price_current_won) low_won,"
        "                   MAX(price_current_won) high_won"
        "              FROM core_listing"
        f"            WHERE {LIVE_STATUS_SQL} AND vin_hash IS NOT NULL"
        "             GROUP BY vin_hash) dv"
        "   ON dv.k = l.vin_hash"
        f" WHERE {' AND '.join(where)}"
        f" ORDER BY {order_clause(flt.order)}"
        " LIMIT ? OFFSET ?")
    labels = _labels(root)
    # all=1 은 전체다.  페이지 크기는 정책값이라 config 에 둔다 (STEP 106)
    if page_size is None:
        # ★ 출처는 web.rows_per_page 하나다 (E-5).
        #   옛 판은 scoring 쪽에도 같은 값이 있어 화면마다 갈렸다
        page_size = int(
            load_config(f"{root}/config/web.json")["rows_per_page"])
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
    site_tpl = _site_detail_urls(root)
    km_unit = _view_cfg("km_bucket", root)
    monthly_unit = _view_cfg("monthly_bucket_won", root)
    dep_cfg = load_config(os.path.join(root, "config", "depreciation.json"))
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
    # ★★★★★ 09-02 (1부 1-4 · `V11-34`) — ★ **빈 사진이 있을 때만** 센다.
    #   ★ 늘 세면 ★ 쪽마다 쿼리가 하나씩 는다 —
    #   ★ ★ 실측 09-02 — ★ `/` 가 21 → **22** 로 상한을 넘었다.
    #   ★★ 거의 모든 쪽은 ★ 사진이 다 있다 — ★ 그때는 ★ **한 번도 안 센다**
    _psites = (photo_ready_sites(conn)
               if any(not r[16] for r in recs) else frozenset())
    return [_row(conn, r, labels, fin_cfg, first + i + 1, flt.calc_version,
                 opt_prices, axes, changes, base, site_tpl, _psites, km_unit,
                 monthly_unit, dep_cfg, state_by, market_by, high_km, root)
            for i, r in enumerate(recs)]



def _market_gap_label(gap_won, market_won) -> str | None:
    """「시세보다 400만 싸다」.  ★ 시세를 모르면 ★ 아무 말도 안 한다.

    ★★ 08-26 마스터 지시 — ★ 시안에 있는데 ★ 화면에 없던 줄이다 (`S46-98`).
    ★ 화면은 「시세차 −11.3% · 시세 3,370만」으로 내고 있었다 —
      ★ ★ 뜻은 같으나 ★ **시안의 말이 아니다.**  ★ 시안이 정본이다
    ★ 같으면 「시세와 같다」다 — ★ 0원을 「싸다」라고 하지 않는다
    """
    if gap_won is None or not market_won:
        return None
    man = abs(int(gap_won)) // WON_PER_MANWON
    if not man:
        return "시세와 같다"
    return f"시세보다 {man:,}만 " + ("싸다" if gap_won < 0 else "비싸다")


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


# ★★★ 갈래별 만점은 ★ config 가 그대로면 ★ 늘 같은 값이다.
#   ★★ 실측 08-29 (cProfile · `/detail`) — ★ `_score_bars` 가 ★ **행마다**
#     ★ 이것을 불러 ★ 성분 × 접두사를 ★ 전수로 훑고 있었다.
#     ★ ★ 한 화면(1,551줄)에 ★ 제너레이터 ★ **645,216회** ·
#       ★ `startswith` ★ 486,421회 · ★ `os.stat` ★ 27,393회.
#   ★ `load_config` 는 ★ 파일이 그대로면 ★ **같은 객체**를 준다 —
#     ★ 그것을 `is` 로 견준다.  ★ mtime 을 또 보지 않는다.
#   ★ 파일이 바뀌면 ★ 객체가 새로 생기므로 ★ 다음 요청이 다시 센다
_GROUP_CAPS_CACHE: dict = {}


def _group_caps(root: str = ".") -> dict:
    """갈래별 만점.  ★ config/scoring.json groups 가 정본이다 (S14)."""
    cfg = load_config(os.path.join(root, "config", "scoring.json"))
    hit = _GROUP_CAPS_CACHE.get(root)
    if hit is not None and hit[0] is cfg:
        return hit[1]
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
    # ★ 돌려준 것을 고치지 않는다 — 같은 객체를 나눠 쓴다 (`load_config` 와 같다)
    _GROUP_CAPS_CACHE[root] = (cfg, out)
    return out


def _view_list(key: str, root: str = ".") -> list:
    # ★ 베껴서 낸다 — 받은 쪽이 고쳐도 캐시가 안 더럽혀지게 (load_config 설명)
    return list(load_config(os.path.join(root, "config", "web.json"))[key])


def _view_dict(key: str, root: str = ".") -> dict:
    # ★ 베껴서 낸다 (위와 같은 까닭)
    return dict(load_config(os.path.join(root, "config", "web.json"))[key])


def _soh_low(root: str) -> float:
    """이보다 낮으면 「배터리가 닳았다」를 싼 이유로 낸다 (개정 296).

    ★ 실측 08-17 — 30건의 SOH 가 91.1~96.8, 중앙 94.4 다
    """
    return float(load_config(f"{root}/config/scoring.json")
                 ["axis_rules"]["value"]["battery_soh_low"])


def _view_int(key: str, root: str) -> int:
    """화면 임계값은 config 다 (V4-13 · V4-17)."""
    return int(load_config(f"{root}/config/web.json")[key])


def _bucket(value, step: int):
    """값을 그 단위로 올려 잡는다.  ★ 없으면 None — 빈 주소를 만들지 않는다."""
    if value is None:
        return None
    return ((int(value) + step - 1) // step) * step


def _high_km(root: str) -> int:
    """이만큼 넘으면 「많이 달렸다」를 싼 이유로 낸다 (개정 299 ⑤).

    ★ 정책값이라 config 에 둔다 — 코드에 박지 않는다 (V4-13)
    """
    return int(load_config(f"{root}/config/scoring.json")
               ["axis_rules"]["value"]["high_mileage_km"])


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
        # ★★★★★ 09-02 마스터 물음 ① — ★ 「★ **보험 건수가 있으면 「무사고」라 쓰지 마라**」.
        #   ★ 이 축이 좋다는 것은 ★ **보험 이력이 없다**는 뜻이다 — ★ 그렇게 적는다
        parts.append("보험 이력이 없고")
    if (full.get("history.use") or _EMPTY).tone == TONE_GOOD:
        parts.append("렌트 이력이 없고")
    if (full.get("warranty.site") or _EMPTY).tone == TONE_GOOD:
        parts.append("사이트가 우수등급을 준")
    if not parts:
        return ""
    # ★ 조사를 이어 한 문장으로 만든다.  「무사고 엔카가 보증합니다」는 말이 아니다
    last = parts[-1]
    tail = {"싸고": "쌉니다", "보험 이력이 없고": "보험 이력이 없습니다",
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
                          f"/listings?excluded=1&reason={quote(str(k), safe='')}")
            for k, v in sorted(counts.items(), key=lambda kv: -kv[1])]


def view_why(account: Account, conn, listing_id: int, calc_version: str,
             fin_cfg: dict, policy: dict, root: str = "."):
    """L1 — 9장 STEP 90 L1 항목 전건.

    ★ 「이 사이트가 안 주는 축」은 ★ 여기서만 켠다 — ★ 그 절이 여기 있다
    """
    return render_listing(conn, listing_id, calc_version, fin_cfg, policy, root,
                          site_blind=True)


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
                    "url": f"/market?target={quote(str(target_key), safe='')}"
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
                       f"/listings?target={quote(str(target_key), safe='')}")]
    width = (hi - lo) / bins
    out = []
    for i in range(bins):
        a = int(lo + width * i)
        b = int(lo + width * (i + 1)) if i < bins - 1 else hi
        got = [p for p in prices if a <= p <= b]
        out.append(Bucket("", a, b, len(got), _median(got),
                          f"/listings?target={quote(str(target_key), safe='')}"
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
                          f"/listings?target={quote(str(target_key), safe='')}&year={ym}", enough))
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
                          f"/listings?target={quote(str(target_key), safe='')}"
                          f"&trim={quote(trim, safe='')}", enough))
    return out


def _other_targets(conn, target_key: str) -> list:
    return [Bucket(tk, None, None, cnt, None,
                   f"/market?target={quote(str(tk), safe='')}")
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


def region_of(site: str | None, region: str | None, shop: str | None,
              root: str = ".") -> str | None:
    """★★★★★ 09-02 마스터 확정 — ★ **판매지역**.

    ★ 마스터 — 「★ 판매지역을 표시했으면 해.  ★ 딜러의 지역을
      ★ **도시 또는 서울인 경우는 구로** ★ 전체적으로」
    ★★ 차례 — ① ★ **사이트가 주소를 주면 ★ 표를 안 본다** (엔카 `contact.address`)
      ★ ② 안 주면 ★ **지점 이름 표**를 본다 (`dealer_region.json` — K카 19 · 리본카 10 · 볼보 6)
      ★ ③ 표에 없으면 ★ **지점 이름을 그대로 낸다** — ★ 짐작으로 안 넣는다 (금지 6)
      ★ ④ 아무것도 없으면 ★ `None` — ★ 화면이 「지역 —」이라 적는다
    ★ 서울이면 ★ 구까지 · 그 밖은 ★ 시까지 (규격 `_rule`)
    """
    if region:
        return _region_short(str(region))
    if not shop:
        return None
    table = load_config(f"{root}/config/dictionaries/dealer_region.json") or {}
    one = table.get(str(site or "")) or {}
    for name, got in one.items():
        if name.startswith("_"):
            continue
        if name in str(shop):
            return str(got)
    # ★ 표에 없다 — ★ **이름을 그대로 낸다.**  ★ 가이드께 올린다 (`S46-226`)
    return str(shop)


def _region_short(got: str) -> str:
    """「서울 강서구」 → 「강서구」 · 「경기 수원시 영통구」 → 「수원」.

    ★ 규격 — ★ 서울이면 ★ **구까지** · 그 밖은 ★ **시까지**.
    ★ 온 만큼만 낸다 — ★ 「경기」만 오면 ★ 「경기」다.  ★ 시를 지어내지 않는다
    """
    part = str(got).split()
    if not part:
        return got
    if part[0].startswith("서울"):
        for one in part[1:]:
            if one.endswith("구"):
                return one
        return part[-1] if len(part) > 1 else part[0]
    for one in part[1:]:
        if one.endswith("시"):
            return one[:-1]
    return " ".join(part[:2]) if len(part) > 1 else part[0]


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
        # ★★ 1절 「오늘」 (v3_dashboard_시안) — ★ 오늘 하루의 넷.
        #   ★ ★ 한 쿼리다 — ★ 넷을 ★ 서브쿼리로 묶어 받는다 (V11-34)
        **_today_counts(conn),
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
    # ★★ 팔린 차도 ★ 지우지 않는다 — ★ 「팔렸다」로 남긴다 (명령서 1-7).
    #   ★ `view_listings` 는 ★ active 만 낸다 — ★ 사라진 것을 따로 받는다
    gone_by = dict(conn.execute(
        "SELECT listing_id, gone_at FROM core_listing"
        " WHERE status = 'gone' AND listing_id IN (%s)"
        % ",".join("?" * len(rows)), [r[1] for r in rows])) if rows else {}
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
    # ★★ 담을 때의 값 — ★ 변경 이력에서 ★ 담은 날 뒤 ★ 첫 변경의 `old_value` 다.
    #   ★ 변경이 없으면 ★ 지금 값이 담을 때 값이다 (안 바뀌었다는 뜻)
    at_add = dict(conn.execute(
        "SELECT listing_id, old_value FROM ("
        "  SELECT listing_id, old_value, changed_at,"
        "         ROW_NUMBER() OVER (PARTITION BY listing_id"
        "                            ORDER BY changed_at) rn"
        "    FROM core_listing_change"
        "   WHERE change_kind = 'price' AND listing_id IN (%s))"
        " WHERE rn = 1" % ",".join("?" * len(rows)),
        [r[1] for r in rows])) if rows else {}
    out = []
    for wid, lid, target, added, closed, memo in rows:
        listing = by_id.get(lid)
        if listing is None:
            continue          # 아직 채점 전이다 — 조용히 빼지 않고 다음 회차에
        got = times.get(vids.get(lid)) or {}
        was = at_add.get(lid)
        try:
            was = int(was) if was is not None else None
        except (TypeError, ValueError):
            was = None
        now = listing.price_won
        delta = (now - was) if (was is not None and now is not None) else None
        gone_at = gone_by.get(lid)
        out.append(WatchRow(watch_id=wid, listing=listing,
                            target_price_won=target, added_at=added,
                            closed_at=closed, memo=memo,
                            price_at_add_won=was, price_delta_won=delta,
                            days_watched=_days_since(added),
                            gone=bool(gone_at), gone_at=gone_at,
                            # ★ 값이 바뀌었거나 팔렸으면 ★ 위로 간다
                            changed=bool(gone_at) or bool(delta),
                            spark=spark.get(lid, ()),
                            relist_times=got.get("times", 0),
                            # ★ 값이 안 바뀌었으면 안 낸다 — 같은 값을
                            #   「3,200만 → 3,200만」이라 내면 읽는 사람이 헷갈린다
                            relist_low_won=(got.get("low_won")
                                            if got.get("low_won")
                                            != got.get("high_won") else None),
                            relist_high_won=got.get("high_won"),
                            chg_cls=_chg(delta, gone_at)[0],
                            chg_text=_chg(delta, gone_at)[1],
                            gap_cls=_gap(listing.market_gap_won)[0],
                            gap_text=_gap(listing.market_gap_won)[1]))
    # ★★ ② 바뀐 것이 위로 (명령서 1-7) — ★ 값 내린 것 · 팔린 것이 먼저.
    #   ★ 그 안에서는 ★ 많이 내린 것부터.  ★ 나머지는 ★ 담은 날 새 것부터
    out.sort(key=lambda w: (not w.changed, w.price_delta_won or 0,
                            w.added_at or ""))
    # ★★ 한 쪽에 30장 (마스터 확정 08-26 · `UI_REVIEW` 16장 · S46-74).
    #   ★ 가이드 — 「관심은 담은 차가 스무 대라 쪽이 안 생긴다」.
    #   ★ ★ 그래도 ★ 수를 맞춰 둔다 — ★ 「화면마다 다르면 헷갈린다」
    return out[:_view_cfg("rows_per_page", root)]


# ★★ v4m 관심 시안 (마스터 확정 08-25) — ★ 카드 맨 앞 줄.
#   ★ 「담은 뒤 무엇이 바뀌었나」가 ★ 이 화면의 이유다 (시안 「지켜야 하는 것」)
def _man(won: int | None) -> str:
    """원 → 「400만」 · 「1억 200만」.  ★ 부호는 안 붙인다 — ★ 말로 적는다."""
    if won in (None, ""):
        return "—"
    n = abs(int(won))
    if n >= 100_000_000:
        eok, rest = divmod(n, 100_000_000)
        man = rest // 10_000
        return f"{eok}억" + (f" {man:,}만" if man else "")
    if n >= 10_000:
        return f"{n // 10_000:,}만"
    return f"{n:,}원"


def _mmdd(at: str | None) -> str:
    """ISO → 「8월 23일」.  ★ 못 읽으면 빈 글자다 — ★ 지어내지 않는다."""
    if not at:
        return ""
    got = str(at)[:10].split("-")
    if len(got) != 3:
        return ""
    try:
        return f"{int(got[1])}월 {int(got[2])}일"
    except ValueError:
        return ""


def _chg(delta: int | None, gone_at: str | None) -> tuple:
    """★ 담은 뒤 무엇이 바뀌었나 — (css, 글).

    ★ 팔린 것이 먼저다.  ★ 팔렸으면 값이 얼마나 움직였는지는 이제 뜻이 없다
    """
    if gone_at:
        day = _mmdd(gone_at)
        return "gone", "✕ 팔렸다" + (f" · {day}" if day else "")
    if delta and delta < 0:
        return "dn", f"↓ {_man(delta)} 내렸다"
    if delta and delta > 0:
        return "up", f"↑ {_man(delta)} 올랐다"
    return "same", "— 담을 때와 같다"


def _gap(gap_won: int | None) -> tuple:
    """★ 시세차 한 줄 — (css, 글).

    ★★ 표본이 모자라 중앙값을 못 만들면 ★ **그것을 적는다**.
      ★ 금지 — ★ 0 으로 내는 것 (「시세와 같다」로 보인다)
    """
    if gap_won is None:
        return "dim", "표본이 모자라 시세를 못 만든다"
    if gap_won < 0:
        return "dn", f"시세보다 {_man(gap_won)} 싸다"
    if gap_won > 0:
        return "up", f"시세보다 {_man(gap_won)} 비싸다"
    return "dim", "시세와 같다"


def _days_since(at: str | None) -> int:
    """담은 날부터 며칠째인가 (명령서 1-7 ③).  ★ 못 읽으면 0 이다."""
    if not at:
        return 0
    from datetime import datetime, timezone
    try:
        got = datetime.fromisoformat(str(at).replace("Z", "+00:00"))
    except ValueError:
        return 0
    if got.tzinfo is None:
        got = got.replace(tzinfo=timezone.utc)
    return max(0, (datetime.now(timezone.utc) - got).days)


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
        field_unclassified=n_field,
        # ★★ 세 줄 (UI_REVIEW 14-7) — ★ 「여쭐 것」이 맨 위다
        **_notready_counts(conn))


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
    # ★★ 11절 「중복매물」 (명령서 1-3) — ★ 10절 뒤에 붙인다.
    #   ★ 열 절 차례는 안 바꾼다 (V11-159)
    dupes = duplicate_listings(conn, listing_id, calc_version, root)
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
        # ★★ 11절 「중복매물」 (명령서 1-3) — ★ 빈 것이면 절을 안 낸다
        "dupes": dupes,
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


# ═══ 추적 — 같은 차가 여러 사이트에 (명령서 1-2 · v3_track_시안) ═══
# ★★ 마스터 확정 08-24 — ★ **합치지 않는다.  ★ 갈린 것을 갈린 채로 보여 준다**
#   ★ 우리가 어느 쪽으로 정하지 않는다 — ★ 사는 사람이 원문 셋을 열어 보고 정한다
# ★ 짝이 없는 매물은 ★ 여기 안 낸다 — ★ 견주는 자리다
TRACK_BIG_GAP_PCT = 30.0        # ★ 이만큼 갈리면 ★ 짝짓기가 틀렸을 자리다


def _grade_order(root: str = ".") -> tuple:
    """등급 차례.  ★ 코드에 박지 않는다 — ★ `config/scoring.json` 이 정본이다 (S14).

    ★ 실측 08-24 — ★ `grade_cuts` 가 ★ S·A·B·C·D·E·F·G 여덟이다 (개정 433).
      ★ ★ 여섯으로 박아 두면 ★ F·G 가 ★ 「모르는 등급」이 되어 ★ 갈린 것을 못 센다
    ★ 자른 값이 큰 것이 ★ 좋은 등급이다 — ★ 그 차례로 늘어놓는다
    """
    import json as _j
    import os as _o
    with open(_o.path.join(root, "config", "scoring.json"),
              encoding="utf-8") as f:
        cuts = _j.load(f).get("grade_cuts") or {}
    return tuple(k for k, _v in sorted(cuts.items(), key=lambda x: -x[1]))


def _grade_step(grades, order: tuple) -> int:
    """등급이 몇 칸 갈렸는가.  ★ 차례에 없는 값(EXCLUDED 등)은 안 센다."""
    got = [order.index(g) for g in grades if g in order]
    return (max(got) - min(got)) if len(got) > 1 else 0


def _miss_axes_bulk(conn, listing_ids: list, calc_version: str,
                    labels: dict) -> dict:
    """빠진 축 — ★ **한 번에** 받는다 (명령서 1-2 · V11-34).

    ★★ 갈래는 ★ `config/labels.json` 의 `MISS_KIND` 가 정본이다 —
      ★ f-table 434·476행에서 옮겼다.  ★ 표에 없는 축은 ★ **갈래를 안 붙인다**
      ★ ★ 지어내지 않는다 (금지 6)
    ★★ ★ 08-25 — ★ 전에는 ★ **매물마다 한 번씩** 불렀다 —
      ★ ★ 짝 44대 × 사이트 셋이면 ★ 쿼리가 ★ **253** 이 됐다 (상한 20).
      ★ ★ 행마다 따로 조회하지 않는다 (V11-34)
    """
    if not listing_ids:
        return {}
    kind = labels.get("MISS_KIND", {})
    al = labels.get("AXIS_LABELS", {})
    marks = ",".join("?" * len(listing_ids))
    out: dict = {}
    for lid, axis in conn.execute(
        f"SELECT listing_id, axis FROM result_axis"
        f" WHERE listing_id IN ({marks}) AND calc_version = ?"
        f"   AND (value IS NULL OR excluded = 1)"
        f" ORDER BY listing_id, max_points DESC, axis",
        (*listing_ids, calc_version)
    ):
        got = out.setdefault(lid, [])
        if len(got) < 4:
            got.append(f"{al.get(axis, axis)} {kind.get(axis, '')}".strip())
    return {k: tuple(v) for k, v in out.items()}


# ── 팔린 차 (`/sold` · UI_REVIEW 30장 · 마스터 확정 08-29 요구 134) ──────
# ★★★ 마스터 — 「★ 별도의 화면 메뉴를 만들어서 ★ 판매 완료된 차에 대해서는
#   ★ 목록 아래에서 정리했으면 좋겠어.  ★ 그래서 ★ **어떠한 가격일 때
#   ★ 잘 팔렸는지 통계**를 내놨으면」
# ★ 「목록에서 사라진 것이 ★ 다 팔린 것은 아니다」 — ★ 그것을 화면에 적고
#   ★ ★ 카드마다 ★ `said_sold` 로 가른다 (30-3 금지)

# ★ 시세 대비 네 칸.  ★ 시안 그대로다 — ★ 개발측이 경계를 새로 정하지 않는다
SOLD_BINS: tuple = (
    ("−10% 아래 (싸다)", None, -10.0),
    ("−10% ~ 시세", -10.0, 0.0),
    ("시세 ~ +10%", 0.0, 10.0),
    ("+10% 위 (비싸다)", 10.0, None),
)
# ★ 표본이 이보다 적으면 ★ 분포를 내지 않는다 — ★ `f-table` 과 같은 잣대 (30-3 필수)
SOLD_MIN_SAMPLE = 5


def _sold_int(v):
    """★ 자취(`core_listing_change.old_value`)는 글자다 — ★ 수로 만든다."""
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return None


def _sold_where(root: str = ".") -> tuple[str, list]:
    """팔린 것·계약 중을 고르는 조건.  ★ 낱말은 `config/labels.json` 이 정본이다."""
    words = sorted(_sold_words(root))
    if not words:
        return "l.status = 'gone'", []
    marks = ",".join("?" * len(words))
    return (f"(l.status = 'gone'"
            f" OR UPPER(COALESCE(l.sales_status,'')) IN ({marks}))"), list(words)


def _days_between(a: str | None, b: str | None) -> int | None:
    """★ 며칠 만에 팔렸나.  ★ 둘 중 하나가 없으면 ★ 안 낸다 (지어내지 않는다)."""
    from datetime import datetime

    if not a or not b:
        return None
    try:
        d0 = datetime.fromisoformat(str(a).replace("Z", "+00:00"))
        d1 = datetime.fromisoformat(str(b).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    n = (d1 - d0).days
    return n if n >= 0 else None


def view_sold(account: Account, conn, root: str = ".", limit: int = 30,
              target_key: str | None = None) -> SoldView:
    """팔린 차 화면 (STEP · UI_REVIEW 30장).

    ★ 지어내지 않는다 — ★ 우리가 가진 것만 낸다 (`first_seen`·`gone_at`·
      `price_current_won`·`core_listing_change`).
    ★ 표본 다섯 미만인 칸은 ★ 「표본 부족」으로 낸다 (30-3 필수)
    """
    del account
    where, args = _sold_where(root)
    total = conn.execute(
        f"SELECT COUNT(*) FROM core_listing l WHERE {where}", args).fetchone()[0]

    pick, pick_args = where, list(args)
    if target_key:
        pick += " AND l.target_key = ?"
        pick_args.append(target_key)
    rows = conn.execute(
        "SELECT l.listing_id, l.target_key, l.site, l.site_model, l.trim_badge,"
        "       l.year_month, l.mileage_km, l.color_ext_raw, l.fuel_raw,"
        "       l.price_current_won, l.photo_main, l.first_seen, l.gone_at,"
        "       l.sales_status, l.status, l.source_id"
        f"  FROM core_listing l WHERE {pick}"
        "  ORDER BY COALESCE(l.gone_at, l.last_seen) DESC, l.listing_id DESC"
        "  LIMIT ?", (*pick_args, int(limit))).fetchall()

    lids = [r[0] for r in rows]
    market = _bulk_market(conn, lids, root) if lids else {}
    # ★ 처음 값 — ★ `core_listing_change` 에 자취가 있을 때만 낸다.
    #   ★ 없으면 ★ 그 줄을 뺀다 (시안 「아직 못 내는 것」)
    first_won: dict = {}
    if lids:
        marks = ",".join("?" * len(lids))
        for lid, old in conn.execute(
            "SELECT listing_id, old_value FROM core_listing_change"
            f" WHERE field='price_current_won' AND listing_id IN ({marks})"
            "  ORDER BY changed_at ASC", tuple(lids)):
            first_won.setdefault(lid, _sold_int(old))

    words = _sold_words(root)
    detail_urls = _site_detail_urls(root)
    out = []
    for (lid, tk, site, model, trim, ym, km, color, fuel, price, photo,
         seen, gone, ss, st, sid) in rows:
        mkt, mkt_n = market.get(lid, (None, 0))
        gap = (round((price - mkt) / mkt * 100, 1)
               if (mkt and price and mkt_n >= _view_cfg("market_min_sample", root))
               else None)
        said = str(ss or "").upper() in words
        spec = " · ".join(str(x) for x in (
            ym, f"{km:,}km" if km else None, color, fuel) if x)
        tpl = detail_urls.get(site)
        out.append(SoldRow(
            listing_id=lid, target_key=tk, site=site,
            site_badge=site_badge(site, None, root),
            region_label=None,
            title=" ".join(str(x) for x in (model, trim) if x) or str(tk or ""),
            spec=spec, price_won=price, price_first_won=first_won.get(lid),
            photo_url=photo, first_seen=seen, gone_at=gone,
            days=_days_between(seen, gone), gap_pct=gap,
            said_sold=said,
            said_label=words.get(str(ss or "").upper()),
            detail_url=(tpl.format(source_id=sid) if tpl and sid else None)))

    bins, bins_for, note = _sold_bins(conn, root, target_key)
    missing = []
    if not first_won:
        missing.append("처음 값 → 마지막 값 — 값이 바뀐 자취(`core_listing_change`)가 "
                       "있는 매물만 낼 수 있습니다.  지어내지 않습니다")
    if note:
        missing.append(note)
    return SoldView(rows=out, total=total, shown=len(out), bins=bins,
                    bins_for=bins_for, bins_note=note, missing=missing)


def _sold_bins(conn, root: str = ".", target_key: str | None = None):
    """★ 「어떤 가격일 때 잘 팔렸나」 — ★ 시세 대비 네 칸 (30-3).

    ★ 표본 다섯 미만인 칸은 ★ 수를 안 낸다 — ★ 「표본 부족」이라 적는다
    ★ 시세는 ★ **그때 그 차종·연식의 중앙값**이 정본이지만, ★ 우리가 가진 것은
      ★ **지금** 중앙값뿐이다 — ★ 그것을 화면에 적는다 (지어내지 않는다)
    """
    where, args = _sold_where(root)
    pick, pick_args = where, list(args)
    if target_key:
        pick += " AND l.target_key = ?"
        pick_args.append(target_key)
    rows = conn.execute(
        "SELECT l.listing_id, l.first_seen, l.gone_at"
        f"  FROM core_listing l WHERE {pick}"
        "   AND l.price_current_won IS NOT NULL"
        "   AND l.target_key IS NOT NULL", pick_args).fetchall()
    lids = [r[0] for r in rows]
    market = _bulk_market(conn, lids, root) if lids else {}
    need = _view_cfg("market_min_sample", root)
    prices = {r[0]: r[1] for r in conn.execute(
        "SELECT listing_id, price_current_won FROM core_listing"
        " WHERE price_current_won IS NOT NULL")} if lids else {}

    buckets: dict = {label: [] for label, _lo, _hi in SOLD_BINS}
    for lid, seen, gone in rows:
        mkt, mkt_n = market.get(lid, (None, 0))
        price = prices.get(lid)
        if not (mkt and price and mkt_n >= need):
            continue
        pct = (price - mkt) / mkt * 100
        for label, lo, hi in SOLD_BINS:
            if (lo is None or pct >= lo) and (hi is None or pct < hi):
                buckets[label].append(_days_between(seen, gone))
                break

    out, any_enough = [], False
    for label, _lo, _hi in SOLD_BINS:
        got = buckets[label]
        days = [d for d in got if d is not None]
        enough = len(got) >= SOLD_MIN_SAMPLE
        any_enough = any_enough or enough
        # ★★★★ 08-30 — ★ 「평균 며칠」의 표본은 ★ `sold_n` 이 **아니다.**
        #   ★ `first_seen` 과 `gone_at` 이 ★ 둘 다 있어야 센다 —
        #   ★ ★ 실측 499건 중 107건뿐이다.  ★ 그 수로 다시 잰다.
        #   ★ ★ 안 그러면 ★ 「136건이 평균 5일」로 읽혀 ★ 거짓이 된다
        out.append(SoldBin(
            label=label, sold_n=len(got),
            days_avg=(round(sum(days) / len(days), 1)
                      if len(days) >= SOLD_MIN_SAMPLE else None),
            enough=enough, days_n=len(days)))
    note = None
    if not any_enough:
        note = (f"표본이 모자랍니다 — 어느 칸도 {SOLD_MIN_SAMPLE}건이 안 됩니다. "
                "수집이 쌓이면 냅니다")
    return out, (target_key or "전체 차종"), note


def _pair_rows(raw: list) -> list:
    """★★★★★ 09-02 마스터 확정 — ★ 짝을 ★ **VIN 이 이기게** 묶는다 (`S46-216`).

    ★ 규격 — 「★ 둘 다 VIN 이 있으면 ★ **VIN 으로** 짝짓는다 ·
      ★ 한쪽이라도 없으면 ★ 차량번호로 내린다」
    ★★ 재는 법 — ★ 번호판으로 모으고 ★ **VIN 이 같은 묶음을 이어 붙인다**.
      ★ ★ 번호판이 바뀌어도(교체·이전) ★ VIN 이 같으면 ★ 한 대다.
    ★ 두 사이트 넘게 있는 묶음만 돌려준다 — ★ 짝이 없으면 견줄 것이 없다
    ★ 돌려주는 꼴은 ★ 옛 것과 같다 — ★ 첫 칸이 ★ 묶음 열쇠다
    """
    parent: dict = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for r in raw:
        plate, lid, vin = r[0], r[1], r[11]
        me = f"l:{lid}"
        find(me)
        if plate:
            union(f"p:{plate}", me)
        if vin:
            union(f"v:{vin}", me)
    groups: dict = {}
    for r in raw:
        groups.setdefault(find(f"l:{r[1]}"), []).append(r)
    out = []
    for key, got in groups.items():
        if len({x[2] for x in got}) < 2:
            continue                  # ★ 한 사이트뿐 — ★ 견줄 것이 없다
        for r in got:
            # ★ 뒤에 ★ **진짜 번호판**을 붙여 둔다 — ★ 앞의 `key` 는 ★ 묶는 데만 쓴다.
            #   ★ 화면에 낼 것은 ★ 번호판이지 ★ 내부 열쇠가 아니다
            out.append((key, *r[1:11], r[0]))
    return out


def _lease_words(root: str = ".") -> tuple:
    """★★★★★ 09-02 마스터 확정 — ★ **리스·렌트** 낱말.

    ★ 마스터 — 「★ **왜 리스가 비교가 되니?**」
    ★ 낱말의 정본은 ★ `config/labels.json` 이다 — ★ 코드에 안 박는다 (`S14`)
    ★ 없으면 ★ 빈 짝이다 — ★ 그때는 안 거른다 (다 지워 버리지 않는다)
    """
    got = load_config(f"{root}/config/labels.json") or {}
    words = got.get("LEASE_SELL_TYPES")
    if isinstance(words, (list, tuple)) and words:
        return tuple(str(x) for x in words)
    return ()


def view_track(account: Account, conn, calc_version: str,
               order: str = "gap", root: str = ".") -> "TrackView":
    """추적 (명령서 1-2 · v3_track_시안).

    ★★ 분모는 ★ **910 으로 같다** (마스터 정정 08-24) — ★ 갈리는 것은 `earned` 다
    ★ 정렬 기본은 ★ 「차액 큰 순」 — ★ 짝짓기가 틀린 것이 먼저 보인다
    """
    del account
    labels = _labels(root)
    order_of = _grade_order(root)
    # ★★★★★ 09-02 마스터 확정 — ★ 짝의 열쇠를 ★ **차대번호(VIN)**로 올린다.
    #   ★ 「★ 차량번호는 ★ 바뀐다(번호판 교체·이전).  ★ 차대번호는 ★ 평생 안 바뀐다」
    #   ★★ 둘 다 VIN 이 있으면 ★ **VIN 으로** · ★ 한쪽이라도 없으면 ★ 번호로 내린다
    #   ★★★ 그리고 ★ **리스·렌트를 뺀다** — ★ 마스터 「★ 왜 리스가 비교가 되니?」
    #     ★ ★ 「엔카 3,200만 ↔ K카 리스 승계 1,900만」은 ★ **같은 값이 아니다**.
    #     ★ ★ ★ 매물 화면에는 ★ 남긴다 — ★ 여기서만 뺀다 (`S46-217`)
    lease = _lease_words(root)
    no_lease = ""
    lease_args: list = []
    if lease:
        marks = ",".join("?" * len(lease))
        no_lease = (" AND (l.sell_type IS NULL"
                    f" OR l.sell_type NOT IN ({marks}))")
        lease_args = list(lease)
    # ★★ 규격 — 「★ **둘 다 VIN 이 있으면 VIN 으로** · ★ 한쪽이라도 없으면 번호로 내린다」.
    #   ★ 그래서 ★ `COALESCE(vin, plate)` 로 뭉뚱그리면 ★ **틀린다** —
    #   ★ ★ 한쪽만 VIN 이 있으면 ★ 열쇠가 갈려 ★ 짝이 깨진다 [실측 09-03 · 180 → 32].
    #   ★★ 그래서 ★ 번호판으로 모으고 ★ **VIN 이 같으면 이어 붙인다** (union) —
    #     ★ ★ 번호판이 바뀌어도 ★ VIN 이 같으면 ★ 한 대다.  ★ VIN 이 이긴다
    raw_rows = conn.execute(
        "SELECT l.plate_hash, l.listing_id, l.site, l.sell_type,"
        "       l.target_key, l.trim_badge, l.price_current_won,"
        "       s.grade, s.earned, s.denominator, l.photo_list_json,"
        "       l.vin_hash"
        "  FROM core_listing l"
        "  LEFT JOIN result_score s ON s.listing_id = l.listing_id"
        "   AND s.calc_version = ?"
        " WHERE (l.plate_hash IS NOT NULL OR l.vin_hash IS NOT NULL)"
        "   AND l.status = 'active'" + no_lease +
        " ORDER BY l.price_current_won",
        (calc_version, *lease_args)).fetchall()
    rows = _pair_rows(raw_rows)
    # ★ VIN 을 가진 매물 — ★ 「VIN ○」 딱지를 달지 가른다
    vin_ids = {r[1] for r in raw_rows if r[11]}

    by_plate: dict = {}
    for r in rows:
        by_plate.setdefault(r[0], []).append(r)
    # ★★ 빠진 축 · 사고 갈림을 ★ **한 번에** 받는다 (V11-34) —
    #   ★ 매물마다 부르면 ★ 짝 44대에 ★ 쿼리가 253 이 된다
    all_ids = [x[1] for r in rows for x in (r,)]
    miss_by = _miss_axes_bulk(conn, all_ids, calc_version, labels)
    acc_by = _accident_bulk(conn, all_ids, calc_version)

    pairs, big, two = [], 0, 0
    for plate, got in by_plate.items():
        prices = [x[6] for x in got if x[6]]
        if not prices:
            continue
        low, high = min(prices), max(prices)
        gap = high - low
        pct = round(gap / low * 100, 1) if low else 0.0
        grades = tuple(x[7] for x in got if x[7])
        # ★★ 08-26 — ★ 튜플이 아니라 ★ **이름 있는 칸**으로 낸다.
        #   ★★ 실측 — ★ 틀은 ★ `{{ s.0 }}` 꼴로 ★ 튜플을 못 짚는다
        #     (`web/template.py` `_step` — ★ 점 뒤는 ★ 늘 글자다).
        #   ★ ★ 그래서 ★ 추적 2절의 ★ 사이트·등급·점수 칸이 ★ **전건 비어 있었다**.
        #     ★ ★ 상세 링크도 ★ `/detail/` 로 나갔다 — ★ 눌러도 아무 데도 안 간다
        #   ★ 이름으로 짚으면 ★ 그런 일이 안 생긴다
        sites = tuple(
            # ★★ 08-29 (#75 뒤) — ★ 분모를 함께 낸다.
            #   ★ 화면이 `/910` 을 박아 두고 있었다 — ★ `total_points` 가
            #     바뀌면 ★ 읽는 쪽이 거짓말을 한다 (마스터 08-29 ①)
            {"badge": site_badge(x[2], x[3], root), "listing_id": x[1],
             "price_won": x[6], "grade": x[7], "earned": x[8],
             "denominator": x[9],
             "misses": miss_by.get(x[1], ())}
            for x in got)
        step = _grade_step(grades, order_of)
        if pct >= TRACK_BIG_GAP_PCT:
            big += 1
        if step >= 2:
            two += 1
        pairs.append(TrackPair(
            plate_hash=plate,
            target_label=str(got[0][4] or "차종 미정"),
            trim=str(got[0][5] or ""),
            sites=sites, site_count=len({x[2] for x in got}),
            low_won=low, high_won=high, gap_won=gap, gap_pct=pct,
            # ★★★★★ 09-02 — ★ 시안 `.v4-thumb` (`S46-98`).  ★ 짝의 첫 사진이다
            # ★★★★★ 09-02 — ★ 차량번호는 ★ **감춘 값**이다 (STEP 35) —
            #   ★ 원본을 안 낸다.  ★ 앞 여섯 자로 ★ 「이 차」임을 가린다
            plate_label=str(next((x[11] for x in got if len(x) > 11 and x[11]),
                                 "") or "")[:6],
            # ★ VIN 으로 이었나 — ★ 짝의 매물이 ★ 다 VIN 을 가졌을 때다
            has_vin=all(x[1] in vin_ids for x in got),
            photo_url=next((_first_photo(x[10], root) for x in got
                            if len(x) > 10 and x[10]), None),
            grades=grades, grade_split=step > 0,
            # ★ 틀은 `>=` 를 못 한다 (V11-104) — ★ 여기서 정한다.
            #   ★ 30% 넘으면 ★ 짝짓기가 틀렸을 자리다 (v4m 추적 시안)
            big_gap=pct >= TRACK_BIG_GAP_PCT,
            gap_cls=("up" if pct >= TRACK_BIG_GAP_PCT else "dim"),
            # ★ 사고 판정이 갈렸는가 — ★ 축 하나를 사이트끼리 견준다
            accident_split=len({acc_by[x[1]] for x in got
                                if x[1] in acc_by}) > 1))

    keys = {"gap": lambda p: -p.gap_won,
            "grade": lambda p: -_grade_step(p.grades, order_of),
            "sites": lambda p: -p.site_count}
    pairs.sort(key=keys.get(order, keys["gap"]))
    # ★★ 한 쪽에 30장 (마스터 확정 08-26 · `UI_REVIEW` 16장 · S46-74).
    #   ★ 「관심·추적·미판정도 같이 30장 — 화면마다 다르면 헷갈린다」
    #   ★★ 자르되 ★ 합(`total_pairs`)은 ★ 전건을 센다 — ★ 자른 것을 합으로
    #     내면 ★ 「이게 전부」로 읽힌다 (검토 17 · `_unmatched_rows` 와 같은 규칙)
    per = _view_cfg("rows_per_page", root)
    return TrackView(
        pairs=pairs[:per],
        grade_split=[p for p in pairs if p.grade_split][:per],
        accident_split=[p for p in pairs if p.accident_split][:per],
        total_pairs=len(pairs), big_gap=big, two_step=two, order=order,
        page_rows=per, cut=len(pairs) > per,
        # ★ 「지금 눌린 것」을 여기서 정한다 — ★ 틀은 `==` 를 못 한다 (V11-104)
        orders=[{"key": k, "label": v, "on": k == order}
                for k, v in (("gap", "차액 큰 순"), ("grade", "등급 차 큰 순"),
                             ("sites", "사이트 많은 순"))])


def _accident_bulk(conn, listing_ids: list, calc_version: str) -> dict:
    """사고 판정 — ★ **한 번에** 받는다 (V11-34).

    ★ 갈린 채로 보여 주려면 ★ 먼저 찾아야 한다 — ★ 매물마다 부르지 않는다
    """
    if not listing_ids:
        return {}
    marks = ",".join("?" * len(listing_ids))
    return {lid: bool(v and v > 0) for lid, v in conn.execute(
        f"SELECT listing_id, value FROM result_axis"
        f" WHERE listing_id IN ({marks}) AND calc_version = ?"
        f"   AND axis = 'state.accident' AND value IS NOT NULL",
        (*listing_ids, calc_version))}


def duplicate_listings(conn, listing_id: int, calc_version: str,
                       root: str = ".") -> tuple:
    """상세 11절 「중복매물」 — ★ 이 차가 다른 곳에도 있으면 나란히 낸다.

    ★ 명령서 1-3 · `v3_detail_시안` 맨 아래.  ★ 10절 뒤에 붙인다 —
      ★ **열 절 차례는 안 바꾼다** (V11-159 는 그 열 절을 뜻한다)
    ★★ 합치지 않는다 — ★ 갈린 채로 낸다 (마스터 확정 08-24)
    ★ 짝이 없으면 ★ 빈 것이다 — ★ 절을 안 낸다
    """
    # ★★ 08-25 (V11-34) — ★ 번호판을 따로 안 묻는다.  ★ 조인 한 번으로 가른다.
    #   ★ ★ 짝이 없는 매물이 ★ 대부분인데 ★ 그때도 두 쿼리를 썼다
    labels = _labels(root)
    out = []
    rows = conn.execute(
        "SELECT l.listing_id, l.site, l.sell_type, l.price_current_won,"
        "       s.grade, l.mileage_km, l.warranty_body_month"
        "  FROM core_listing l"
        "  LEFT JOIN result_score s ON s.listing_id=l.listing_id"
        "   AND s.calc_version=?"
        "  JOIN core_listing me ON me.listing_id = ?"
        "   AND me.plate_hash IS NOT NULL AND l.plate_hash = me.plate_hash"
        " WHERE l.status='active' AND l.listing_id<>?"
        " ORDER BY l.price_current_won",
        (calc_version, listing_id, listing_id)).fetchall()
    # ★★ 사고 축을 ★ **한 번에** 받는다 (V11-34) — ★ 매물마다 부르면
    #   ★ ★ 짝이 셋이면 ★ 쿼리가 셋 는다.  ★ `/detail` 이 상한(26)을 넘었다 (28)
    ids = [r[0] for r in rows]
    acc_by: dict = {}
    if ids:
        marks = ",".join("?" * len(ids))
        acc_by = {r[0]: (r[1], r[2], r[3]) for r in conn.execute(
            f"SELECT listing_id, value, excluded, source FROM result_axis"
            f" WHERE listing_id IN ({marks}) AND calc_version = ?"
            f"   AND axis = 'state.accident'", (*ids, calc_version))}
    for lid, site, sell, price, grade, km, w_month in rows:
        got = acc_by.get(lid)
        acc = chip("state.accident", got[0] if got else None,
                   bool(got[1]) if got else True, labels,
                   source=got[2] if got else None)
        out.append({"listing_id": lid,
                    "site_badge": site_badge(site, sell, root),
                    "price_won": price, "grade": grade,
                    # ★ 줄표만 있는 칸을 두지 않는다 (V11-106 · 부록 G-4) —
                    #   ★ 「못 받은 것」인지 「없는 것」인지를 감춘다.
                    #   ★ 기호는 남기되 ★ 모를 때는 ★ **말로 적는다**
                    "accident_mark": ("확인 못 함"
                                      if acc.tone == TONE_UNKNOWN else acc.mark),
                    "accident_tone": acc.tone,
                    "mileage_km": km, "warranty_month": w_month})
    return tuple(out)


def _today_counts(conn) -> dict:
    """1절 「오늘」 — ★ 새로 뜬 것 · 값 내린 것 · 사라진 것 · 마지막 재판정.

    ★ v3_dashboard_시안 1절.  ★ 「오늘」은 ★ 마지막 하루다 (UTC 자정 기준이 아니다) —
      ★ 수집이 하루 한 번이라 ★ 자정으로 자르면 ★ 갓 받은 것이 안 보인다
    ★ 못 세면 0 이다 — ★ 지어내지 않는다
    """
    from datetime import datetime, timedelta, timezone

    since = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    one = conn.execute(
        "SELECT"
        "  (SELECT COUNT(*) FROM core_listing WHERE first_seen >= ?),"
        "  (SELECT COUNT(*) FROM core_listing_change"
        "    WHERE change_kind = 'price' AND changed_at >= ?"
        "      AND CAST(new_value AS INTEGER) < CAST(old_value AS INTEGER)),"
        "  (SELECT COUNT(*) FROM core_listing"
        "    WHERE status = 'gone' AND gone_at >= ?),"
        "  (SELECT MAX(calculated_at) FROM result_score)",
        (since, since, since)).fetchone()
    return {"new_today": one[0] or 0, "dropped_today": one[1] or 0,
            "gone_today": one[2] or 0, "last_recalc_at": one[3]}


def _notready_counts(conn) -> dict:
    """미판정 세 줄 (UI_REVIEW 14-7 · 개정 724).

    ★★ 「미분류」가 ★ 두 뜻으로 읽혔다 (개발측 지적 · 오판 114) —
      ★ ① 차종 이름을 ★ 모르는 매물 · ★ ② 아직 ★ 아무 처리도 안 된 매물
    ★ ★ 마스터께서 ★ 정하실 것은 ★ ② 뿐이다 — ★ 그것을 ★ 맨 위에 낸다
    ★ 나머지 둘은 ★ 쌓인 것이 아니라 ★ **갈무리된 것**이다 — ★ 건수만 낸다
    """
    one = conn.execute(
        "SELECT"
        "  (SELECT COUNT(*) FROM core_listing"
        "    WHERE target_key IS NULL AND status = 'new'),"
        "  (SELECT COUNT(*) FROM core_listing"
        "    WHERE target_key IS NULL AND status = 'out_of_scope'),"
        "  (SELECT COUNT(*) FROM core_listing"
        "    WHERE target_key IS NULL AND status = 'gone')").fetchone()
    return {"ask_count": one[0] or 0, "folded_count": one[1] or 0,
            "gone_count": one[2] or 0}


def axis_zero_rates(conn, calc_version: str) -> dict:
    """축마다 ★ 전체 매물 가운데 ★ 0점·모름이 몇 건인가 (가이드 지시 08-25).

    ★★ 왜 — ★ 사는 사람이 ★ 「**내 차만 0 인가**」를 알아야 한다.
      ★ ★ `state.consumable` 은 ★ 4,784건 ★ 전건 0 이다 — ★ 규격대로다 (f-table ⑤).
        ★ ★ 그것을 모르면 ★ 「내 차가 나쁘다」로 읽는다
    ★ 0(없다)과 ★ NULL(모른다)을 ★ 갈라서 센다 — ★ 섞으면 v1 사고가 되풀이된다
    """
    out = {}
    for axis, n, zero, nul in conn.execute(
        "SELECT a.axis, COUNT(*),"
        "       SUM(CASE WHEN a.value = 0 THEN 1 ELSE 0 END),"
        "       SUM(CASE WHEN a.value IS NULL THEN 1 ELSE 0 END)"
        "  FROM result_axis a JOIN core_listing l"
        "    ON l.listing_id = a.listing_id"
        " WHERE l.status = 'active' AND a.calc_version = ?"
        " GROUP BY 1", (calc_version,)
    ):
        if not n:
            continue
        out[axis] = {"total": n, "zero": zero or 0, "unknown": nul or 0,
                     "zero_pct": round((zero or 0) / n * 100, 1),
                     # ★ 전건 0 이면 ★ 「내 차 탓이 아니다」 — ★ 그것을 말한다
                     "all_zero": (zero or 0) == n}
    return out


# ★★★★★ 09-01 (규격 `docs/RECOMMEND_SCREEN.md` · `S46-201`) — ★ 추천 화면.
#   ★ 마스터 — 「★ 등급 무시하고 ★ 내가 선호하는 색과 예산 점수 및 킬로와 연식 점수에
#     ★ 근접하는 차야 … ★ 모두 가격에 있는 항목이니 점수로 소팅하면 되지?」
#   ★★ 「그렇다」 — ★ 넷 다 이미 `result_axis` 에 있다.  ★ **새로 셈하지 않는다**
#   ★★★★★ 09-02 명령서 11 (`S46-98`·`S46-242`) — ★ **크기·내장색을 더한다.**
#     ★ 시안 `v4m_recommend_시안.html` 이 ★ 「크기 (전장)」을 낸다 —
#     ★ ★ 마스터 09-01 「★ 크기·내장색 축이 화면에 안 보인다」.
#     ★ ★ ★ 이것도 ★ **이미 `result_axis` 에 있다** — ★ 새로 셈하지 않는다
RECOMMEND_AXES: tuple = ("value.budget", "value.mileage", "state.year",
                         "taste.color", "taste.color_int", "taste.size")
RECOMMEND_TABS: tuple = ("1", "2", "3")


def _recommend_year_from(root: str = ".") -> dict:
    """★ 추천에 낼 ★ **가장 이른 연식** (4-3 · `recommend_year_from`).

    ★ 정본은 ★ `config/targets.json` 이다 — ★ 코드에 차종도 연식도 안 박는다 (`S14`).
    ★ 지금은 ★ `MODEL_Y = 2025-01`(주니퍼) 하나뿐이다 — ★ 늘면 그대로 걸린다
    """
    got = load_config(f"{root}/config/targets.json") or {}
    return {k: v["recommend_year_from"] for k, v in got.items()
            if isinstance(v, dict) and v.get("recommend_year_from")
            and not k.startswith("_")}


def _recommend_models(conn, where: list, args: list, picked: list,
                      names: dict, now: tuple = (),
                      calc_version: str | None = None) -> tuple:
    """★★★★★ 09-02 — ★ 시안 `.rc-models` — ★ **차종 고르개**.

    ★ 마스터 — 「★ **시안 `v4m_recommend_시안.html` 에 맞추어서 빨리 작업해**」
    ★ 시안이 보이는 것 — 「테슬라 모델Y **286**」처럼 ★ 이름 ＋ **건수**.
      ★ ★ 건수가 0 인 차종은 ★ **`off`(흐리게)** 로 ★ **남겨 둔다** —
      ★ ★ ★ **지우지 않는다.**  ★ 「없다」가 아니라 ★ 「지금 재고가 없다」다
    ★ 차례는 ★ 건수 많은 것부터 (시안이 그렇다) · ★ 0 은 뒤로
    """
    # ★★★★★ 09-04 — ★ **세는 자와 뽑는 자가 같아야 한다** (`V11-55` 와 같은 뜻).
    #   ★★★ 마스터 — 「★ 차종은 수집했는데 ★ **목록이 없는 건 뭐지**」.
    #   ★★ 실측 09-04 (브라우저) — ★ 단추가 ★ 「폭스바겐 ID.4 **33**」이라 해 놓고
    #     ★ ★ 누르면 ★ **카드가 0개**였다.  ★ 머리글도 ★ 「33건 중 **0점**」이라 했다.
    #   ★ 까닭 — ★ 단추는 ★ `result_score` 를 ★ **LEFT JOIN** 으로 세어
    #     ★ ★ **점수가 없는 것까지** 셌고, ★ 목록은 ★ `result_axis` 를
    #     ★ ★ ★ **INNER JOIN** 으로 뽑는다 — ★ 자가 두 개였다.
    #   ★★ 시안도 ★ 그것을 안다 — ★ `v4m_recommend_시안` 은 ★ ID.4 · ID.5 · iX3 ·
    #     ★ ★ EV4 를 ★ **0건 무리**(흐리게)에 둔다.  ★ 「없다」가 아니라 ★ 「재고가 없다」다
    axis_marks = ",".join("?" * len(RECOMMEND_AXES))
    ver = [calc_version] if calc_version else []
    got = dict(conn.execute(
        "SELECT l.target_key, COUNT(DISTINCT l.listing_id) FROM core_listing l"
        " JOIN result_axis a ON a.listing_id = l.listing_id"
        + ("  AND a.calc_version = ?" if calc_version else "")
        + f"  AND a.axis IN ({axis_marks})"
        " LEFT JOIN result_score s ON s.listing_id = l.listing_id"
        " WHERE " + " AND ".join(where) + " GROUP BY 1",
        [*ver, *RECOMMEND_AXES, *args]))
    out = []
    for i, key in enumerate(picked):
        n = int(got.get(key) or 0)
        # ★★ 스위치다 — ★ 켜져 있으면 ★ 그것을 **뺀 주소**를 준다 (끄기).
        #   ★ 꺼져 있으면 ★ 그것을 **더한 주소**를 준다 (켜기)
        rest = [x for x in now if x != key] if key in now else [*now, key]
        out.append({"key": key, "label": names.get(key) or key, "n": n,
                    "on": key in now, "off": n == 0,
                    "q": "".join(f"&model={quote(x)}" for x in rest),
                    # ★ 같은 건수면 ★ `targets.json` 차례를 지킨다 (`S46-100`)
                    "_i": i})
    # ★★ 건수 많은 것부터 — ★ 시안이 그렇다.  ★ 0 건은 뒤로 간다.
    #   ★★★★★ 09-02 — ★ 0 건 안에서는 ★ **브랜드로 묶는다** (시안 실측).
    #     ★ 시안 — 「볼보 XC40 리차지 · 폭스바겐 ID.4 · 폭스바겐 ID.5 ·
    #       ★ BMW iX3 · 기아 EV4」 — ★ **같은 브랜드가 붙어 있다.**
    #     ★ ★ 가나다순도 `targets.json` 차례도 아니었다 [실측 09-02].
    #   ★ 브랜드 차례는 ★ **이미 나온 브랜드가 먼저**다 (C40 볼보 → XC40 볼보).
    #     ★ ★ 그다음은 ★ `targets.json` 차례를 따른다
    #   ★★ 브랜드 차례 — ① 이미 나온 브랜드가 먼저 (C40 볼보 → XC40 볼보)
    #     ★ ② 그다음은 ★ **차종이 많은 브랜드가 먼저** (폭스바겐 ID.4·ID.5 둘)
    #     ★ ③ 그래도 같으면 ★ `targets.json` 차례.
    #   ★ 시안 실측 09-02 — ★ 「XC40 · ID.4 · ID.5 · iX3 · EV4」가 그 꼴이다
    seen_brand: dict = {}
    for one in sorted(out, key=lambda x: (-x["n"], x["_i"])):
        if one["n"]:
            seen_brand.setdefault(str(one["label"]).split()[0], len(seen_brand))
    many: dict = {}
    for one in out:
        b = str(one["label"]).split()[0]
        many[b] = many.get(b, 0) + 1
    out.sort(key=lambda x: (
        -x["n"],
        seen_brand.get(str(x["label"]).split()[0], 99),
        -many.get(str(x["label"]).split()[0], 0),
        x["_i"]))
    return tuple(out)


# ★ 차종이 아닌 자리 — ★ 사양표 기본값이다 (`targets.json` 안에 함께 산다)
NOT_TARGETS = ("SPEC_DEFAULT_ON", "SPEC_DEFAULT_OFF")


def _active_targets(root: str = ".") -> list:
    """★★★★★ 09-02 마스터 정정 — ★ **추천에 내는 차종** (`recommend`).

    ★★★ 마스터 — 「★ 내가?  ★ 왜 제네시스랑 그랜저는 쉬게 해?
      ★ ★ **추천에서 뺀 거지 ★ 수집에서 뺀 거니?**」
    ★★ 내가 09-01 에 ★ 추천을 좁히려고 ★ `active` 를 썼다 —
      ★ ★ 그것은 ★ 「받는가」다.  ★ 수집·판정·매물 화면까지 멈춘다 (오판 237).
      ★ ★ ★ 가른다 — ★ `active` 는 **받는가**(32종) · `recommend` 는 **추천에 내는가**(10종)
    ★ 키가 없으면 ★ **낸다** — ★ 뺄 것만 ★ `recommend=false` 로 적는다 (`S46-229`)
    ★ 정본은 `config/targets.json` 이다 — ★ 코드에 차종을 박지 않는다 (`S14` · 금지 6)
    ★ `targets.json` 의 차례를 그대로 둔다 — ★ 시안의 고르개가 그 차례다 (`S46-100`)
    """
    got = load_config(f"{root}/config/targets.json") or {}
    return [k for k, v in got.items()
            if not k.startswith("_") and isinstance(v, dict)
            and k not in NOT_TARGETS
            and v.get("recommend", True)]


def view_recommend_tabs(account: Account, conn: sqlite3.Connection,
                        calc_version: str, flt: ListingFilter,
                        tab: str = "1", root: str = ".",
                        page_size: int = 60,
                        models_on: tuple = ()) -> "RecommendView":
    """추천 — ★ 탭 (규격 `RECOMMEND_SCREEN.md` · `S46-201`).

    ★★★★★ 09-01 — ★ `/recommend` 는 ★ **이미 있었다** (「추천 대상만 · 이유가 있는 것」).
      ★ 규격이 ★ 그 자리를 ★ **탭 화면으로 다시 정의**한다.
      ★★ 옛 `view_recommend` 는 ★ **안 지운다** (개정 427 「화면을 지우지 않는다」) —
        ★ ★ 길만 이 함수로 바꾼다.  ★ 옛 것을 탭 2 로 할지는 ★ 마스터께서 정하신다

    ★★★ 탭 1 — ★ **여섯 축의 합**으로 세운다 (09-04 — ★ 규격 20줄).
      ★ 예산 95 · 주행 107 · 연식 80 · 색 15.
      ★ ★ **등급을 안 본다** — ★ 거르지도 않고 더하지도 않는다 (규격 「금지」)
    ★★ 탭 2·3 — ★ **탭만 만든다.**  ★ 안을 지어내지 않는다 (규격 2장)
    ★ 목록 줄은 ★ `/listings` 와 ★ 같은 부품(`_listings_where`)을 쓴다
    """
    del account
    tab = str(tab or "1")
    if tab not in RECOMMEND_TABS:
        tab = "1"
    if tab != "1":
        # ★ 마스터께서 정하실 자리다 — ★ 이름도 안 짓는다
        return RecommendView(tab=tab, rows=[], total=0, axes=(), full=0,
                             empty_note="아직 정하지 않았습니다", title="")

    where, args = _listings_where(flt)
    # ★★★★★ 09-01 마스터 지시 — 「★ 추천 화면에서 ★ 내가 고르지 않은 차들을
    #   ★ 보게 하는 거지?  ★ **내가 고른 차종만 보이게 지금 당장 바꿔**」
    #   ★★ 실측 09-01 — ★ 화면에 24가지가 들었고 ★ 그중 15가지 · **3,660건**이
    #     ★ ★ 고르신 열셋 밖이었다 (G80_25T 1,412 · GLC 676 · 차종 미정 200 …).
    #   ★★ 정본은 ★ `config/targets.json` 의 `active` 다 — ★ 코드에 안 박는다 (S14).
    #     ★ ★ **지우지 않는다** — ★ `/listings` 는 그대로 다 본다.
    #     ★ ★ ★ 추천에서만 ★ 고르신 것으로 좁힌다
    picked = _active_targets(root)
    # ★★★★★ 09-02 명령서 ② — ★ 「★ 차종 단추는 ★ **켜고 끄는 스위치** ·
    #   ★ ★ **여럿 켜면 OR** · ★ 「전체」를 맨 앞에」
    #   ★ 고르지 않은 차종은 ★ 안 받는다 — ★ 주소로 억지로 넣어도 안 걸린다
    on = tuple(x for x in (models_on or ()) if x in picked)
    # ★ 화면에 낼 이름은 ★ `targets.json` 의 `label` 이다 (「G80 2.5T」) —
    #   ★ 열쇠(`G80_25T`)를 그대로 내면 ★ 사람이 읽는 이름이 아니다
    names = {k: (v.get("label") or k)
             for k, v in (load_config(f"{root}/config/targets.json")
                          or {}).items()
             if not k.startswith("_") and isinstance(v, dict)}
    if picked:
        where = [*where, "l.target_key IN (" + ",".join("?" * len(picked)) + ")"]
        args = [*args, *picked]
    # ★★★★★ 09-04 (4-3 · `S46-269`) — ★ **`recommend_year_from` 을 읽는다.**
    #   ★★★ 마스터 확정 09-03 — 「★ 전기차랑 ★ **(모델Y는 주니퍼만)** ＋ 그랑콜레오스
    #     ★ ＋ GV70 가솔린만 보이게 해줘」.
    #   ★ 주니퍼는 ★ **2025-01 부터**다 (제원 실측 09-02 — 초기형 4,751 / 주니퍼 4,790).
    #   ★★ 값은 ★ `config/targets.json` 이 정본이고 ★ 가이드가 넣었다 —
    #     ★ ★ 그런데 ★ **아무도 안 읽고 있었다.**
    #     ★ ★ ★ 실측 09-04 — ★ 추천에 든 모델Y **782대** 가운데
    #       ★ ★ ★ ★ **518대가 초기형·연식 모름**이었다 (주니퍼는 264대).
    #   ★ 연식을 ★ **모르는 것도 뺀다** — ★ 「주니퍼만」이라 하셨다.
    #     ★ ★ 모르는 것을 넣으면 ★ 「아마 주니퍼일 것」이 된다 (금지 6)
    #   ★ 연식 꼴이 두 가지다 — ★ `2025-01` 과 ★ `202501` (K카).  ★ 하이픈을 떼고 견준다
    for _key, _since in _recommend_year_from(root).items():
        if _key not in picked:
            continue
        where = [*where,
                 "(l.target_key <> ? OR (l.year_month IS NOT NULL"
                 "   AND REPLACE(l.year_month, '-', '') >= ?))"]
        args = [*args, _key, str(_since).replace("-", "")[:6]]
    # ★ 고르개로 하나를 누르셨으면 ★ 그것만.  ★ 건수는 ★ **누르기 전 것**을 센다 —
    #   ★ 안 그러면 ★ 누른 차종만 남고 ★ 나머지가 다 0 이 된다
    model_where, model_args = list(where), list(args)
    if on:
        # ★ 여럿이면 ★ **OR** 다 — ★ 「이것들 중 아무거나」
        where = [*where, "l.target_key IN (" + ",".join("?" * len(on)) + ")"]
        args = [*args, *on]
    marks = ",".join("?" * len(RECOMMEND_AXES))
    sql = (
        "SELECT l.listing_id, l.target_key,"
        " l.trim_badge, l.year_month, l.mileage_km, l.color_ext_raw,"
        " l.price_current_won, l.site, s.grade, l.color_int_raw,"
        " l.photo_list_json, l.source_id, l.sell_type,"
        " l.dealer_region, l.dealer_shop,"
        " SUM(a.value) AS got, SUM(a.max_points) AS full,"
        # ★★★★★ 09-02 명령서 13 (`S46-94`) — ★ 볼보 원문 주소에 ★ 차종이 든다.
        #   ★ **맨 뒤**에 붙였다 — ★ `r[15]`(`got`)·`r[16]`(`full`) 을 안 민다.
        #   ★ ★ 앞에 끼우면 ★ 합 두 칸이 밀려 ★ 점수가 통째로 어긋난다
        " l.site_model"
        " FROM core_listing l"
        " JOIN result_axis a ON a.listing_id = l.listing_id"
        "  AND a.calc_version = ? AND a.axis IN (" + marks + ")"
        " LEFT JOIN result_score s ON s.listing_id = l.listing_id"
        "  AND s.calc_version = ?"
        " WHERE " + " AND ".join(where) +
        " GROUP BY l.listing_id"
        # ★ 높은 것이 위다 (규격 「필수」)
        " ORDER BY got DESC, l.price_current_won ASC"
        " LIMIT ?")
    rows = list(conn.execute(
        sql, [calc_version, *RECOMMEND_AXES, calc_version, *args, page_size]))
    # ★ 축을 따로 낸다 — ★ 「왜 위에 있는지」가 보여야 한다 (규격 「필수」)
    per = _recommend_axes(conn, calc_version, [r[0] for r in rows])
    # ★ 빈 사진이 있을 때만 센다 — ★ 늘 세면 ★ 쪽마다 쿼리가 하나 는다 (`V11-34`)
    _psites = (photo_ready_sites(conn)
               if any(not _first_photo(r[10], root) for r in rows)
               else frozenset())
    labels = _labels(root)
    sites = _site_labels(root)
    # ★★★★★ 09-01 — ★ `V11-69` · `V11-120`.  ★ `/listings` 가 쓰는 것을 그대로 쓴다
    # ★ 원문 주소 틀은 ★ `web.json` 의 `site_detail_url` 이다 — ★ `sites.json` 이 아니다
    site_tpl = _site_detail_urls(root)
    site_cfg = load_config(f"{root}/config/sites.json") or {}
    fin_cfg = load_config(f"{root}/config/finance.json") or {}

    def _buy(site, price, tkey):
        from report.finance import purchase_cost
        return purchase_cost(site, price, fin_cfg, site_cfg, tkey)

    def _buy_of(site, price, tkey):
        got = _buy(site, price, tkey)
        return got.total_won if got else None

    def _buy_est(site, price, tkey):
        got = _buy(site, price, tkey)
        return bool(got and got.estimated)

    # ★ 시안 — ★ 「등급 C · **등급은 안 봅니다**」.  ★ 무엇이 「낮은가」는 config 다
    cuts = load_config(f"{root}/config/scoring.json").get("grade_cuts") or {}
    top = [g for g, _v in sorted(cuts.items(), key=lambda kv: -float(kv[1]))][:3]
    out = []
    # ★★★★★ 09-02 명령서 11 — ★ **1부터 차례로** (`S46-242`).
    #   ★ 이 화면은 ★ `LIMIT` 만 쓰고 ★ **쪽을 안 넘긴다** (`OFFSET` 이 없다) —
    #   ★ ★ 그래서 ★ 1부터다.  ★ 쪽 넘김이 생기면 ★ 여기부터 고쳐야 한다
    for _i, r in enumerate(rows, start=1):
        lid = r[0]
        # ★ 시안은 ★ **정수**다 — 「271 / 297」·「예산 89/95」 (브라우저로 대조 09-01)
        got = round(float(r[15] or 0))
        full = round(float(r[16] or 0))
        out.append(RecommendRow(
            listing_id=lid,
            target_label=str(names.get(r[1]) or labels.get(r[1])
                             or r[1] or "차종 미정"),
            trim=r[2], year_month=r[3], mileage_km=r[4], color_ext=r[5],
            price_won=r[6], site=r[7], grade=r[8],
            got=got, full=full,
            # ★ 틀은 나눗셈을 못 한다 (V11-104) — ★ 여기서 낸다
            pct=round(got / (full or 1) * 100, 1),
            # ★ 시안 `.v4-spec` — ★ 「2023-04 · 21,400km · 청색 / 검정색 계열 · 볼보셀렉트」
            spec=" · ".join(x for x in (
                _ym_dash(r[3]),
                f"{int(r[4]):,}km" if r[4] is not None else None,
                " / ".join(y for y in (r[5], r[9]) if y) or None,
                sites.get(r[7], r[7])) if x),
            photo_url=_first_photo(r[10], root),
            # ★ 09-04 — ★ 빈 자리에 ★ 까닭을 낸다 (목록과 같은 부품을 쓴다)
            photo_note=_photo_note(r[7], r[10],
                                   _view_str("photo_base_url", root), _psites),
            ignored=bool(r[8]) and r[8] not in top,
            # ★★★★★ 09-01 — ★ `V11-69`.  ★ `/listings` 와 ★ **같은 부품**을 쓴다.
            #   ★ 원문 문은 ★ 그 매물의 사이트로 간다 (S46-94) —
            #   ★ ★ 못 잰 사이트는 ★ **안 낸다.**  ★ 지어내지 않는다
            site_badge=site_badge(r[7], r[12], root),
            # ★★★★★ 09-02 마스터 확정 — ★ 판매지역 (`S46-225`)
            region_label=region_of(r[7], r[13], r[14], root),
            # ★★★★★ 09-02 마스터 확정 — ★ 연식·거리에 셈을 함께
            age_label=_age_label(r[3]),
            km_per_year_label=_km_per_year(r[3], r[4]),
            encar_url=_source_url(r[7], r[11], site_tpl, r[17]),
            # ★ 「그 사이트에서 사면 얼마를 내는가」 (개정 353 · `V11-120`)
            total_cost_won=(_buy_of(r[7], r[6], r[1]) or None),
            buy_estimated=_buy_est(r[7], r[6], r[1]),
            rank=_i,
            axes=per.get(lid, ())))
    # ★ 화면에 든 전건 — ★ 거르개는 `s.` 를 쓰므로 ★ 같은 이음을 걸어야 한다
    # ★ 「N건 중」도 ★ **같은 잣대**로 센다 — ★ 안 그러면 화면이 거짓말을 한다
    # ★★★★★ 09-04 — ★ 위 주석이 ★ 「같은 잣대로 센다」인데 ★ **안 그랬다.**
    #   ★ 목록은 ★ `result_axis` 를 ★ INNER JOIN 으로 뽑는데
    #   ★ ★ 여기는 ★ `result_score` 를 ★ LEFT JOIN 으로 셌다.
    #   ★★ 실측 09-04 (브라우저) — ★ `?model=ID4_EV` 가 ★ 「**33건** 중」이라 해 놓고
    #     ★ ★ 카드는 ★ **0개**였다.  ★ 마스터 — 「★ 목록이 없는 건 뭐지」
    _amarks = ",".join("?" * len(RECOMMEND_AXES))
    total = conn.execute(
        "SELECT COUNT(DISTINCT l.listing_id) FROM core_listing l"
        " JOIN result_axis a ON a.listing_id = l.listing_id"
        "  AND a.calc_version = ?"
        f"  AND a.axis IN ({_amarks})"
        " LEFT JOIN result_score s ON s.listing_id = l.listing_id"
        " WHERE " + " AND ".join(where),
        [calc_version, *RECOMMEND_AXES, *args]).fetchone()[0]
    full = sum(x.full for x in (out[0].axes if out else ())) if out else 0
    if not full:
        # ★ 한 건도 없을 때 ★ 「합(0점)」이라 적으면 ★ 배점이 0인 것처럼 보인다.
        #   ★ 만점은 ★ 매물이 있든 없든 ★ 같다 — ★ 표에서 그대로 읽는다
        full = conn.execute(
            "SELECT COALESCE(SUM(m), 0) FROM (SELECT MAX(max_points) m"
            "   FROM result_axis WHERE calc_version = ?"
            f"    AND axis IN ({_amarks}) GROUP BY axis)",
            [calc_version, *RECOMMEND_AXES]).fetchone()[0]
    # ★ 시안 `.rc-head` — 「차종 13종」.  ★ 정본은 `config/targets.json` 이다
    targets = len(picked)
    models = _recommend_models(conn, model_where, model_args, picked, names,
                               on, calc_version)
    return RecommendView(tab=tab, rows=out, total=total,
                         axes=RECOMMEND_AXES, full=round(full, 1),
                         empty_note=None, title="내 기준에 가까운 차",
                         # ★★★★★ 09-01 — ★ `V11-69` 정렬.  ★ 지금은 ★ 규격이 정한
                         #   ★ 「합이 높은 차례 · 같으면 싼 차가 앞」 하나뿐이다.
                         #   ★★ **없는 차례를 지어내지 않는다** (금지 6) —
                         #     ★ ★ 있는 것을 ★ 적어 보여 줄 뿐이다
                         orders=({"key": "score", "label":
                                  "합이 높은 차례 (같으면 싼 차가 앞)",
                                  "on": True},),
                         models=models, model=on,
                         targets=targets)


def _ym_dash(ym) -> str | None:
    """연식을 ★ 시안 꼴 「2023-04」로.  ★ K카는 `202209` 로 준다 (실측 09-01)."""
    got = str(ym or "")
    if len(got) == 6 and got.isdigit():
        return f"{got[:4]}-{got[4:]}"
    return got or None


def _first_photo(raw, root: str = ".") -> str | None:
    """★ 사진 한 장 — ★ 시안 `.v4-thumb`.  ★ 없으면 「사진」 자리만 둔다.

    ★★ 새로 짜지 않는다 — ★ 목록이 쓰는 `photo_url()` 을 ★ 그대로 쓴다.
      ★ ★ 원문이 ★ `{"type","location","ordering"}` 꼴이라 ★ 첫 칸을 그냥 쓰면
      ★ ★ ★ dict 가 통째로 주소 자리에 들어간다 (실측 09-01 — 내가 그렇게 냈다)
    """
    return photo_url(raw, _view_str("photo_base_url", root))


def _site_labels(root: str = ".") -> dict:
    """사이트 이름 — ★ 정본은 `config/sites.json` 이다 (코드에 안 박는다)."""
    got = load_config(f"{root}/config/sites.json") or {}
    return {k: (v.get("label") or k) for k, v in got.items()
            if isinstance(v, dict)}


def _recommend_axes(conn, calc_version: str, ids: list) -> dict:
    """매물마다 ★ 네 축을 따로.  ★ 한 번에 받는다 (V11-34 — 줄마다 부르지 않는다)."""
    if not ids:
        return {}
    marks = ",".join("?" * len(ids))
    ax = ",".join("?" * len(RECOMMEND_AXES))
    out: dict = {}
    for lid, axis, value, mx in conn.execute(
        f"SELECT listing_id, axis, value, max_points FROM result_axis"
        f" WHERE calc_version=? AND listing_id IN ({marks})"
        f"   AND axis IN ({ax})",
        [calc_version, *ids, *RECOMMEND_AXES]
    ):
        out.setdefault(lid, {})[axis] = (value, mx)
    order = {a: i for i, a in enumerate(RECOMMEND_AXES)}
    got: dict = {}
    for lid, per in out.items():
        got[lid] = tuple(sorted(
            (RecommendAxis(axis=a, label=AXIS_LABEL.get(a, a),
                           got=round(float(v or 0)),
                           full=round(float(m or 0)),
                           # ★ 시안 `.rc-ax.hi` — ★ 만점이면 노랗게
                           hi=bool(m) and float(v or 0) >= float(m))
             for a, (v, m) in per.items()),
            key=lambda x: order.get(x.axis, 99)))
    return got


# ★ 화면 글 — ★ 마스터께서 부르신 이름 그대로 (규격 1장 표)
# ★★★★★ 09-02 명령서 11 (`S46-98`) — ★ **`config/labels.json` 이 원천이다** (`S14`).
#   ★ 전에는 ★ 넷을 ★ **코드에 박아** 뒀다.  ★ 축이 둘 늘자
#   ★ ★ 「크기 (전장)」·「색상 (내장)」이 ★ **이름을 못 찾아** 화면에서 사라졌다
#   ★ ★ ★ (실측 09-02 — ★ `AXIS_LABEL.get("taste.size")` 가 `None` 이었다).
#   ★★ 못 찾으면 ★ 축 코드를 그대로 낸다 — ★ **조용히 빼지 않는다** (금지 12)
def _axis_labels() -> dict:
    """★ 축 이름 표.  ★ 정본은 `config/labels.json` 의 `AXIS_LABELS` 다 (`S14`)."""
    import json as _j
    import os as _o
    _p = _o.path.join(_ROOT_LBL, "config", "labels.json")
    with open(_p, encoding="utf-8") as _f:
        return dict(_j.load(_f).get("AXIS_LABELS") or {})


AXIS_LABEL = _axis_labels()
