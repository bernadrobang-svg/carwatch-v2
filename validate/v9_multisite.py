# -*- coding: utf-8 -*-
"""V9 — 다중 사이트 (`docs/chapters/50-multisite.md`).

지시서   50-multisite 「출처를 밝힌다」
근거     ★ 사이트가 둘 이상이면 값의 뜻이 사이트에 달려 있다.
        「자차 미가입 10개월」이 엔카 것인지 K카 것인지에 따라 뜻이 다르다
값규칙   사이트 이름을 코드에 박지 않는다 — `config/sites.json` 이 정본이다
금지     출처 없이 값만 내는 것
"""
from __future__ import annotations

import json
import os
import re

from validate.base import (
    FATAL,
    KIND_CODE,
    Check,
    not_applicable,
    result,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDER = os.path.join(ROOT, "outputs", "render")
# 매물이 나오는 화면 — 배지가 있어야 한다 (50-multisite 「전부」)
LISTING_SCREENS = ("listings", "recommend", "watch", "compare",
                   "why_listing_id")
# 한 행이 매물임을 알려 주는 자리.  ★ 이 수만큼 배지가 있어야 한다
ROW_MARK = 'data-href="/why/'

C: dict[str, Check] = {
    "V9-06": Check("V9", "V9-06", "매물마다 사이트 배지가 있음", FATAL, "run",
                   "사이트가 둘 이상이면 값의 뜻이 사이트에 달려 있다. "
                   "목록 · 추천 · 관심 · 비교 · 상세 전부에 낸다. "
                   "★ 화면이 「엔카」를 글자로 박고 있었다 — 사이트가 둘이 "
                   "되는 순간 거짓말이 된다 (50-multisite)",
                   KIND_CODE),
    "V9-10": Check("V9", "V9-10", "사이트 보증 항목의 합이 만점과 같음",
                   FATAL, "run",
                   "엔카는 검증 10 + 보증 10 + 보증++ 30 = 50. "
                   "합이 만점과 다르면 그 사이트는 만점을 못 받거나 넘는다 "
                   "(개정 365)",
                   KIND_CODE),
    "V9-01": Check("V9", "V9-01", "축 × 사이트 표가 있음", FATAL, "run",
                   "축마다 사이트별 채움률.  어느 축이 어느 사이트에만 있는지 "
                   "알아야 사이트를 늘릴 값이 있는지 판단한다 (개정 306)",
                   KIND_CODE),
    "V9-02": Check("V9", "V9-02", "site_unavailable 이 화면에 나옴",
                   FATAL, "run",
                   "「우리가 못 받았다」와 「그 사이트가 아예 안 준다」는 다르다. "
                   "뒤는 우리 잘못이 아니다 — 사람이 「그럼 K카에서 찾아볼까」를 "
                   "할 수 있어야 한다 (개정 306)",
                   KIND_CODE),
    "V9-09": Check("V9", "V9-09", "같은 점수에서 사이트 보증이 높은 쪽이 앞",
                   FATAL, "run",
                   "마스터 — 「최고급 우선이야」.  그 우선이 정렬에도 들어간다. "
                   "★ 사이트 이름으로 올리지 않는다 — ⑤ 사이트 보증 축의 "
                   "점수로 올린다.  K카 직거래까지 올리면 안 된다 (개정 306)",
                   KIND_CODE),
    "V9-07": Check("V9", "V9-07", "합친 값에 출처가 붙어 있음", FATAL, "run",
                   "「자차 미가입 10개월 (K카 제공)」처럼 어느 사이트 원문에서 "
                   "온 값인지 사람이 알아야 한다.  값이 다르면 둘 다 낸다 "
                   "(50-multisite)",
                   KIND_CODE),
}


def _sites() -> dict:
    with open(os.path.join(ROOT, "config", "sites.json"),
              encoding="utf-8") as f:
        return json.load(f)


def live_sites() -> list:
    """쓰는 사이트.  ★ store 의 것을 쓴다 — 같은 이름의 공개 함수를
    두 모듈에 두지 않는다 (V4-21).  「active」의 뜻은 store 가 정한다."""
    from store.crosssite import active_sites

    return active_sites(_sites())


def _labels() -> set:
    """사이트 배지에 나올 수 있는 말.  ★ 코드에 이름을 박지 않는다."""
    out = set()
    for one in _sites().values():
        if not isinstance(one, dict):
            continue
        label = one.get("label")
        if not label:
            continue
        out.add(label)
        for tail in (one.get("sell_type_labels") or {}).values():
            out.add(f"{label} {tail}")
    return out


def _badge_check(rid):
    """V9-06 — 매물이 나오는 화면마다 사이트 배지가 있는가.

    ★ 렌더 결과를 본다.  템플릿에 있어도 값이 안 실리면 빈 배지가 나온다
    ★ 행 수와 배지 수를 견준다 — 하나만 있으면 「있다」가 아니다
    """
    if not os.path.isdir(RENDER):
        return not_applicable(C["V9-06"], rid, "렌더 결과가 없다")
    words = _labels()
    if not words:
        return not_applicable(C["V9-06"], rid, "sites.json 에 label 이 없다")
    bad, seen = [], 0
    for name in LISTING_SCREENS:
        path = os.path.join(RENDER, f"{name}.html")
        if not os.path.isfile(path):
            continue
        html = open(path, encoding="utf-8").read()
        rows = html.count(ROW_MARK)
        got = [x for x in re.findall(r'<span class="tag"[^>]*>\s*([^<]*?)\s*'
                                     r"</span>", html) if x]
        marks = [x for x in got if x in words]
        if rows and not marks:
            bad.append(f"{name} — 매물 {rows}행인데 사이트 배지가 없다")
        elif rows and len(marks) < rows:
            bad.append(f"{name} — 매물 {rows}행인데 배지 {len(marks)}개")
        stray = [x for x in got if x not in words and "카" in x]
        if stray:
            bad.append(f"{name} — sites.json 에 없는 배지 {stray[0]}")
        seen += 1
    if not seen:
        return not_applicable(C["V9-06"], rid, "매물 화면 렌더가 없다")
    bad += _hardcoded_badges(words)
    return result(C["V9-06"], rid, 0, len(bad), not bad, bad[:6])


def _hardcoded_badges(words: set) -> list:
    """★ 배지 자리에 사이트 이름을 글자로 박았는가.

    실측 08-18 — 목록이 「엔카」를 박고 있었다.  사이트가 둘이 되는 순간
    K카 매물에도 「엔카」가 찍힌다.  「엔카에서 보기」 같은 링크 글은
    사이트 이름이 맞으므로 배지 자리(class="tag")만 본다
    """
    base = os.path.join(ROOT, "web", "templates")
    if not os.path.isdir(base):
        return []
    out = []
    for name in sorted(os.listdir(base)):
        if not name.endswith(".html"):
            continue
        body = open(os.path.join(base, name), encoding="utf-8").read()
        for got in re.finditer(r'<span class="tag"[^>]*>\s*([^<{]+?)\s*'
                               r"</span>", body):
            if got.group(1) in words:
                out.append(f"templates/{name} — 배지에 「{got.group(1)}」을 "
                           "글자로 박았다.  sites.json 이 정본이다")
    return out


def _origin_check(conn, rid):
    """V9-07 — 합친 값에 출처가 붙어 있는가.

    ★ 사이트가 하나뿐이면 합칠 것이 없다 — 그때는 「해당 없음」이다.
      「사이트가 하나라서 통과」와 「출처를 붙였으니 통과」는 다르다
    """
    live = live_sites()
    if len(live) < 2:
        return not_applicable(
            C["V9-07"], rid,
            f"쓰는 사이트가 {len(live)}곳이라 합친 값이 없다 "
            f"({', '.join(live) or '없음'})")
    # 두 사이트 이상에서 온 매물 — 값이 갈리면 둘 다 내야 한다
    mixed = conn.execute(
        "SELECT COUNT(*) FROM (SELECT vin FROM core_listing"
        " WHERE vin IS NOT NULL GROUP BY vin HAVING COUNT(DISTINCT site) > 1)"
    ).fetchone()
    n = mixed[0] if mixed else 0
    if not n:
        return not_applicable(C["V9-07"], rid,
                              "두 사이트에 같이 올라온 매물이 없다")
    bad = []
    path = os.path.join(RENDER, "why_listing_id.html")
    if os.path.isfile(path):
        html = open(path, encoding="utf-8").read()
        if "제공" not in html:
            bad.append("상세에 「(K카 제공)」 같은 출처 표시가 없다")
    return result(C["V9-07"], rid, 0, len(bad), not bad, bad[:4])


def _warranty_sum_check(rid):
    """V9-10 — 사이트마다 보증 항목의 합이 만점과 같은가 (개정 365)."""
    import json as _j

    with open(os.path.join(ROOT, "config", "scoring.json"),
              encoding="utf-8") as f:
        full = _j.load(f)["components"].get("warranty.site")
    full = full if isinstance(full, int) else (full or {}).get("points")
    if not full:
        return not_applicable(C["V9-10"], rid, "scoring 에 warranty.site 가 없다")
    bad = []
    for name, one in _sites().items():
        if not isinstance(one, dict) or one.get("status") == "planned":
            continue
        items = one.get("warranty_items") or []
        if not items:
            bad.append(f"{name} — warranty_items 가 없다")
            continue
        got = sum(int(x.get("points") or 0) for x in items)
        if got != full:
            bad.append(f"{name} — 항목 합 {got} != 만점 {full}")
    return result(C["V9-10"], rid, full, "맞다" if not bad else "다르다",
                  not bad, bad[:4])


def _tie_break_check(conn, rid):
    """V9-09 — 같은 점수에서 사이트 보증이 높은 쪽이 앞인가 (개정 306).

    마스터 — 「최고급 우선이야」.  그 우선이 정렬에도 들어간다
    ★ 사이트 이름으로 올리지 않는다 — ⑤ 사이트 보증 축의 점수로 올린다
    ★ 「정렬식에 들어 있다」로 통과시키지 않는다.  실제로 앞서는지 본다
    """
    from report.screens.build import SITE_WARRANTY_ORDER, order_clause

    bad = []
    if "warranty.site" not in order_clause("rank"):
        bad.append("정렬에 사이트 보증이 없다")
        return result(C["V9-09"], rid, "앞선다", "없다", False, bad)
    del SITE_WARRANTY_ORDER
    # ★ 같은 비율인 짝을 찾아 실제 순서를 본다
    rows = conn.execute(
        "SELECT s.listing_id,"
        " ROUND(s.earned * 1.0 / NULLIF(s.denominator, 0), 6) AS r,"
        " (SELECT a.score FROM result_axis a"
        "    WHERE a.listing_id = s.listing_id"
        "      AND a.calc_version = s.calc_version"
        "      AND a.axis = 'warranty.site') AS w"
        " FROM result_score s WHERE s.denominator > 0"
        " ORDER BY r DESC, w DESC, s.listing_id").fetchall()
    pairs = 0
    for i in range(len(rows) - 1):
        a, b = rows[i], rows[i + 1]
        if a[1] != b[1] or a[2] is None or b[2] is None:
            continue
        pairs += 1
        if a[2] < b[2]:
            bad.append(f"매물 {a[0]}(보증 {a[2]}) 이 {b[0]}(보증 {b[2]}) 보다 앞")
    if not pairs:
        return not_applicable(C["V9-09"], rid,
                              "비율이 같은 매물 짝이 없다 — 잴 것이 없다")
    return result(C["V9-09"], rid, "앞선다", f"{pairs}짝", not bad, bad[:4])


def _axis_site_check(conn, rid):
    """V9-01 · V9-02 — 축 × 사이트 표 · site_unavailable 이 화면에 나오는가.

    ★ 「우리가 못 받았다(missing)」와 「그 사이트가 아예 안 준다」는 다르다.
      뒤는 우리 잘못이 아니고, 사람이 「그럼 다른 사이트에서」를 할 수 있다
    ★ 분모는 안 줄인다 — 사이트별로 분모를 달리하면 사이트끼리 비교가 안 된다
    """
    from store.crosssite import (
        SITE_UNAVAILABLE, axes_by_site, site_only_axes,
    )

    sites = _sites()
    table = axes_by_site(conn, sites)
    bad1 = [] if table else ["축 × 사이트 표가 비었다"]
    a = result(C["V9-01"], rid, "있다", f"축 {len(table)}", not bad1, bad1)

    # V9-02 — 그 사유가 실제로 붙고 화면에 나오는가
    declared = {ax for one in sites.values() if isinstance(one, dict)
                for ax in (one.get("axes_not_provided") or [])}
    if not declared:
        return [a, not_applicable(C["V9-02"], rid,
                                  "안 주는 축이라 적어 둔 것이 없다")]
    bad2 = []
    used = {r[0] for r in conn.execute(
        "SELECT DISTINCT axis FROM result_axis WHERE source = ?",
        (SITE_UNAVAILABLE,))}
    for ax in sorted(declared - used):
        bad2.append(f"{ax} 를 「안 준다」고 적어 두고 판정은 missing 이라 한다")
    # ★ 화면에 사람 말로 나오는가.  코드에만 있으면 사람은 모른다
    path = os.path.join(ROOT, "outputs", "render", "why_listing_id.html")
    if used and os.path.isfile(path):
        html = open(path, encoding="utf-8").read()
        if "제공하지 않습니다" not in html:
            bad2.append("상세에 「제공하지 않습니다」가 안 나온다")
    got = site_only_axes(conn, sites)
    return [a, result(C["V9-02"], rid, "나온다",
                      f"{len(used)}축 · 사이트만 있는 축 {len(got)}",
                      not bad2, bad2[:4])]


def run(conn, ctx) -> list:
    rid = ctx.run_id
    return [_badge_check(rid), _origin_check(conn, rid),
            _warranty_sum_check(rid), _tie_break_check(conn, rid),
            *_axis_site_check(conn, rid)]
