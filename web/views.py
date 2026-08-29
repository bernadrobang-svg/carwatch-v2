# -*- coding: utf-8 -*-
"""화면 어댑터 (14장 STEP 142 · 152).

지시서   STEP 142 (라우팅) · 152 (경계)
근거     ★ 10장·13장 화면 함수는 그대로다.  14장이 그것을 감싼다.
         view_* 시그니처를 바꾸지 않는다
금지     여기서 점수·등급을 만드는 것.  DTO 를 받아 템플릿에 넘기기만 한다
"""
from __future__ import annotations

import json
import os
import sqlite3
# ★★ 주소에 넣는 값은 ★ 다 인코딩한다 (마스터 지적 08-25 · 오판 119).
#   ★ `| url` 필터는 ★ 템플릿에만 닿는다 — ★ 파이썬이 만드는 주소는 여기서 한다
from urllib.parse import quote

from contracts import ROLE_ANONYMOUS, ROLE_PENDING, ROLE_USER
from errors import PolicyError, ValidationError, WiringError
from report.screens.views import ListingFilter
from web.app import build_page
from web.context import HTTP_OK
from web.template import render

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 한 화면에 낼 행 수 → config.web.rows_per_page (STEP 106a)


def _rows_per_page(root: str = ROOT) -> int:
    return int(_cfg("web.json", root)["rows_per_page"])


def _cfg(name: str, root: str = ROOT) -> dict:
    with open(os.path.join(root, "config", name), encoding="utf-8") as f:
        return json.load(f)


def _versions(conn: sqlite3.Connection) -> dict:
    """★ 조회는 store 가 한다.  화면에 SQL 을 두지 않는다 (V11-01).

    ★ 한 요청 안에서 여러 번 부른다 — 뷰가 한 번, 뼈대가 한 번.
      그때마다 4쿼리를 돌면 화면마다 8쿼리를 헛되이 쓴다 (V11-34 · B-2).
      연결 객체에 붙여 둔다 — 연결이 끝나면 함께 사라진다
    """
    from store.core import current_versions

    got = getattr(conn, "_cw_versions", None)
    if got is None:
        got = current_versions(conn)
        try:
            conn._cw_versions = got
        except AttributeError:
            pass          # 캐시를 못 붙이는 연결이면 그냥 매번 조회한다
    return got


def page_extras(root: str = ROOT) -> dict:
    """page() 가 전 화면에 얹어 주는 값 (STEP 144).

    ★ 여기 한 곳이 정본이다.  검사(V11-38)도 이것을 부른다 —
      각자 목록을 들면 「아무도 안 넘긴다」는 거짓 경보가 난다
    """
    return {"points": _points(root)}


def _points(root: str = ROOT) -> dict:
    """배점.  ★ config 가 정본이다 — 화면에 숫자를 박지 않는다 (V4-13).

    total   전체 만점
    grade   등급을 매기는 기준 점수
    taste   그 차이.  ★ 개정 431 부터 0 이다 — 등급에서 빼는 갈래가 없다
    cuts    ★ 등급 경계 문장 (개정 433 — 8단계).  화면에 숫자를 박지 않는다
    """
    raw = _cfg("scoring.json", root)
    total = int(raw["total_points"])
    grade = int(raw.get("grade_base_points") or total)
    # ★★ 개정 433 — 화면에 「S 90 · A 80 …」을 박아 두면 컷이 바뀌어도 그대로다.
    #   실제로 그랬다 — 개정 431 로 분모가 675 가 된 뒤에도 목록 설명은
    #   「취향 N점을 뺀」과 「S 90」을 그대로 내고 있었다.  config 에서 만든다
    cuts = sorted(((g, float(r)) for g, r in raw["grade_cuts"].items()),
                  key=lambda kv: -kv[1])
    return {"total": total, "grade": grade, "taste": total - grade,
            "cuts": " · ".join(f"{g} {r * 100:.0f}" for g, r in cuts),
            "n_cuts": len(cuts),
            "axes": len(raw.get("components") or {})}


def page(conn, account, title: str, template: str, ctx: dict, *,
         csrf: str = "", flashes=None, root: str = ROOT,
         flash_key: str = "-", refresh_sec: int = 0) -> tuple:
    """부분 템플릿 → PageContext → base.html.  반환 (status, headers, bytes)."""
    ver = _versions(conn)
    # ★ 부분 템플릿도 page 를 본다.  폼의 {{ page.csrf_token }} 이 여기서 채워진다.
    #   먼저 렌더하면 토큰이 빈 문자열이 되어 전 POST 가 403 이 된다 (실측)
    from web.app import take_flashes

    flashes = list(flashes or []) + take_flashes(flash_key)
    # ★ 화면 이름은 부분 템플릿 이름에서 온다 — 손으로 적지 않는다.
    #   listings.html → s-listings.  시안의 화면별 규칙이 여기에 걸린다
    screen = "s-" + template.removesuffix(".html").replace("_", "-")
    p = build_page(conn, account, title, "", csrf=csrf, flashes=flashes,
                   refresh_sec=refresh_sec, screen=screen, **ver)
    # ★ 배점을 화면에 박지 않는다.  배점이 바뀌면 화면이 거짓말이 된다.
    #   실측 08-19 — 목록이 「총점 605 중 555 기준」이라 적고 있었다.
    #   개정 365 로 675/625 가 된 지 하루가 지났는데 화면만 옛말을 했다
    extra = page_extras(root)
    body = render(template, {"page": p, **extra, **ctx})
    p = build_page(conn, account, title, body, csrf=csrf, flashes=flashes,
                   refresh_sec=refresh_sec, screen=screen, **ver)
    html = render("_page.html", {"page": p, **extra, **ctx})
    return HTTP_OK, {}, html.encode("utf-8")


# ── 화면별 어댑터 ────────────────────────────────────────────────────
def sold(conn, account, req, root: str = ROOT, csrf: str = "",
         flash_key: str = "-", **_kw) -> tuple:
    """팔린 차 (`/sold` · UI_REVIEW 30장 · 마스터 확정 08-29 요구 134).

    ★ 마스터 — 「★ 별도의 화면 메뉴를 만들어서 ★ 판매 완료된 차에 대해서는
      ★ 목록 아래에서 정리했으면 좋겠어.  ★ 그래서 ★ 어떠한 가격일 때
      ★ 잘 팔렸는지 통계를 내놨으면」
    ★ 목록(`/listings`)에서는 안 보인다 — ★ 여기와 통계에만 나온다 (30-2)
    """
    from report.screens.build import view_sold

    q = req.get("query", {})
    tk = (q.get("target") or "").strip() or None
    v = view_sold(account, conn, root, target_key=tk)
    return page(conn, account, "팔린 차", "sold.html",
                {"v": v, "sold": v, "target": tk}, csrf=csrf, root=root,
                flash_key=flash_key)


def listings(conn, account, req, root: str = ROOT, csrf: str = "", flash_key: str = "-",
         **_kw) -> tuple:
    from report.screens.build import axis_heads, view_listings

    ver = _versions(conn)
    # ★ 필터 조립은 _filter 하나다 (STEP 106a)
    flt = _filter(conn, req.get("query", {}), ver, root)
    rows = view_listings(account, conn, flt, _cfg("finance.json", root), root)
    return page(conn, account, "매물", "listings.html",
                {"rows": rows, "count": len(rows), "filter": flt,
                 # 사이트별로 거르는 단추 (개정 306).
                 # ★ 쓰는 사이트가 하나면 안 낸다 — 늘 켜진 단추는 조작이 아니다
                 "site_buttons": _site_buttons(flt, root, conn),
                 # ★ 「3,471건 중 200건 · 1/18쪽」 (V11-55).
                 #   200건만 보이면서 전체를 안 적으면 3,471건을 못 본다
                 "paging": _paging(conn, flt, len(rows), root),
                 "axis_heads": axis_heads(root),
                 # ★ 조건 단추는 위에.  누르면 켜지고 다시 누르면 꺼진다 (149t)
                 "buttons": _filter_buttons(flt),
                 # 차종·가격대·리스 (개정 420).  ★ 고른 조건을 문장으로 낸다
                 "models": _model_menu(conn, flt),
                 "pick": _pick_state(flt, root),
                 "carry_pick": _carry_pick(flt),
                 "lease_hidden": _lease_hidden(conn, flt, root),
                 # ★ 배지 설명도 config 에서 (개정 433).  「여섯 등급」이 박혀 있었다
                 "grade_help": _grade_help(root),
                 # ★ 관문 배제로 뺀 건수 (개정 433).  조용히 빼지 않는다
                 "excluded_hidden": _excluded_hidden(conn, flt, root),
                 # ★ 사유별 — 「몇 건」보다 왜인지가 먼저다
                 "excluded_why": _excluded_why(conn, flt),
                 # ★ ＋12 선택지 — DB 에 있는 값만 낸다 (개정 427)
                 "km_options": _km_options(flt, root),
                 "grade_options": _grade_options(flt, root),
                 "judge_buttons": _judge_buttons(flt, root),
                 "option_buttons": _option_name_buttons(flt, root),
                 # ★★ 색은 옵션 절에 (마스터 확정 08-25) — ★ 다섯씩 · 나머지는 접는다
                 #   ★★ 08-25 — ★ 한 번만 조회한다.  ★ 전에는 ★ `_split_top` 을
                 #     ★ ★ 두 번씩 불러 ★ 색 조회가 ★ **여섯 번**이었다 (V11-34)
                 **_color_menus(conn, flt),
                 # ★★ 명령서 87장 — ★ 연료는 ★ **갈래**로 고른다 (33가지 원값이 아니다)
                 "fuel_options": _fuel_options(flt.fuel, root),
                 "region_options": _distinct_options(
                     conn, "dealer_region", flt.region),
                 # 정렬 드롭다운 8종 + 지금 조건을 들고 갈 hidden (개정 277)
                 "orders": _order_menu(flt),
                 "carry": _carry(flt),
                 # ★ 지금 조건을 칩으로 낸다.  누른 값이 보이지 않으면
                 #   무엇으로 걸렀는지 알 수 없다 (STEP 149d · 149g)
                 "chips": _filter_chips(flt),
                 "query_string": _query_string(flt),
                 # ★ 조건·정렬·건수를 문장으로 낸다 (STEP 149g · B-8)
                 "condition_sentence": _condition_sentence(flt, len(rows)),
                 "order_label": _order_label(flt.order)},
                root=root, csrf=csrf,
                flash_key=flash_key)


def why(conn, account, req, path_vars: dict, root: str = ROOT,
         csrf: str = "", flash_key: str = "-",
         **_kw) -> tuple:
    """★ 없는 매물이라고 500 을 내지 않는다.  안내를 낸다 (STEP 149)."""
    from report.screens.build import view_why

    ver = _versions(conn)
    try:
        # ★ 숫자가 아니면 그런 매물이 없는 것이다.  200 을 내지 않는다 (E-8)
        raw = str(path_vars.get("listing_id", ""))
        if not raw.isdigit():
            raise KeyError(raw)
        v = view_why(account, conn, int(raw),
                     ver["calc_version"], _cfg("finance.json", root),
                     _cfg("scoring.json", root), root)
    except (KeyError, ValueError):
        # ★ 없는 매물은 404 다.  200 으로 내면 링크가 살아 있는 줄 안다 (E-8).
        #   「수집 전」과 「그 매물이 없다」도 다르다
        from web.context import HTTP_NOT_FOUND

        miss = {"title": "그 매물의 판정 결과가 없습니다",
                "reason": "내려갔거나 아직 채점되지 않은 매물입니다.",
                "action": "매물 목록에서 다시 고른다  (/listings)"}
        _st, hd, body = page(conn, account, "판정 근거", "_missing.html",
                             {"miss": miss}, root=root, csrf=csrf,
                             flash_key=flash_key)
        return HTTP_NOT_FOUND, hd, body
    # ★ 받은 원문은 따로 넘긴다 — 「v.raw_sections」는 이름이 겹쳐
    #   ScoreView 의 다른 절과 헷갈린다 (개정 378)
    # ★★ 「내 차만 0 인가」 (가이드 지시 08-25) — ★ 축마다 ★ 전체가 몇 %가 0 인지.
    #   ★ `state.consumable` 은 ★ 전건 0 이다 (f-table ⑤) — ★ 내 차 탓이 아니다
    from report.screens.build import axis_zero_rates

    rates = axis_zero_rates(conn, _versions(conn)["calc_version"])
    mine = []
    for one in v.axes:
        got = rates.get(one.axis)
        if not got:
            continue
        mine.append({"axis": one.axis, "label": one.label,
                     "value": one.value, "max_points": one.max_points,
                     "zero": got["zero"], "total": got["total"],
                     "zero_pct": got["zero_pct"], "all_zero": got["all_zero"],
                     # ★ 내 차가 0 인데 ★ 남들은 아닌가 — ★ 그것이 판단 재료다
                     "only_me": bool((one.value in (0, None))
                                     and not got["all_zero"])})
    return page(conn, account, "판정 근거", "why.html",
                {"v": v, "rep_raw": v.raw_sections, "zero_rates": mine},
                csrf=csrf, root=root, flash_key=flash_key)



def detail(conn, account, req, path_vars: dict, root: str = ROOT,
           csrf: str = "", flash_key: str = "-", **_kw) -> tuple:
    """/detail/<id> — 11절 (개정 427 · STEP 97a).

    ★ 없는 매물이라고 500 을 내지 않는다.  404 와 안내를 낸다 (E-8)
    """
    from report.screens.build import view_detail

    ver = _versions(conn)
    try:
        raw = str(path_vars.get("listing_id", ""))
        if not raw.isdigit():
            raise KeyError(raw)
        got = view_detail(account, conn, int(raw), ver["calc_version"],
                          _cfg("finance.json", root),
                          _cfg("scoring.json", root), root)
        if got.get("row") is None:
            raise KeyError(raw)
    except (KeyError, ValueError):
        from web.context import HTTP_NOT_FOUND

        miss = {"title": "그 매물의 판정 결과가 없습니다",
                "reason": "내려갔거나 아직 채점되지 않은 매물입니다.",
                "action": "매물 목록에서 다시 고른다  (/listings)"}
        _st, hd, body = page(conn, account, "상세", "_missing.html",
                             {"miss": miss}, root=root, csrf=csrf,
                             flash_key=flash_key)
        return HTTP_NOT_FOUND, hd, body
    return page(conn, account, "상세", "detail.html",
                {**got, "grade_help": _grade_help(root)}, csrf=csrf,
                root=root, flash_key=flash_key)


def _grade_help(root: str = ROOT) -> str:
    """등급 설명 — ★ config 에서 만든다.  화면에 컷을 박지 않는다."""
    got = _points(root)
    return (f"등급 {got['n_cuts']}단계입니다. 절대 기준 — {got['cuts']}. "
            "「제외」는 등급이 아니라 관문 배제입니다")


def notready(conn, account, req, root: str = ROOT, csrf: str = "", flash_key: str = "-",
         **_kw) -> tuple:
    from report.screens.build import view_notready

    ver = _versions(conn)
    nr = view_notready(account, conn, ver["calc_version"], ver["run_id"])
    return page(conn, account, "미판정", "notready.html", {"nr": nr, "n": nr}, csrf=csrf,
                root=root, flash_key=flash_key)


def dashboard(conn, account, req, root: str = ROOT, csrf: str = "", flash_key: str = "-",
         **_kw) -> tuple:
    from report.screens.build import view_dashboard

    ver = _versions(conn)
    if not ver["calc_version"]:
        # ★ 판정 전에는 대시보드 대신 안내를 낸다 (STEP 149)
        return page(conn, account, "현황", "empty.html", {}, csrf=csrf,
                root=root, flash_key=flash_key)
    dv = view_dashboard(account, conn, ver["run_id"], ver["calc_version"],
                        _cfg("finance.json", root), root)
    # ★★ 개정 427 — 현황이 시세를 흡수한다.  /market 의 차종별 표가 여기로 온다
    #   ★ /market 화면은 안 지운다.  관리로 내렸다 (V11-158 이 확인한다)
    #   ★ 표는 view_dashboard 가 같은 쿼리로 만들었다 — 다시 안 받는다 (V11-34)
    return page(conn, account, "현황", "dashboard.html",
                {"d": dv, "market_rows": dv.market_rows,
                 "buttons": _filter_buttons(
                    ListingFilter(calc_version=ver["calc_version"]),
                    base="/listings")},
                csrf=csrf, root=root, flash_key=flash_key)


def admin_home(conn, account, req, root: str = ROOT, csrf: str = "", flash_key: str = "-",
         **_kw) -> tuple:
    from report.screens.admin import view_admin_home

    home = view_admin_home(account, conn)
    # ★ 마스터는 금요일 아침에 /admin 을 열면 된다 (S29 · 개정 334).
    #   가벼운 점검은 4시간마다다 (개정 335) — 밤에 깨져도 아침에 안다
    return page(conn, account, "관리", "admin.html",
                {"h": home, "checks": _check_reports(root)},
                csrf=csrf, root=root, flash_key=flash_key)


def _unclassified_split(conn, root: str = ROOT, rows=None) -> dict:
    """미분류를 원인별로 (개정 341 · V4-26).

    ★ 원문을 훑는 일이라 가볍지 않다.  미분류가 없으면 아예 안 돈다
    ★ SQL 은 web/ 에 두지 않는다 (V11-01) — store 가 센다
    """
    from store.core import classify_unclassified, has_unclassified

    if not has_unclassified(conn):
        return {}
    rows = list(rows if rows is not None else classify_unclassified(conn))
    top = _rows_of("split_rows", root)
    kinds: dict = {}
    for one in rows:
        kinds[one["kind"]] = kinds.get(one["kind"], 0) + 1
    mine = [r for r in rows if r["kind"].startswith("④")]
    return {
        "total": len(rows),
        "kinds": [{"kind": k, "n": n} for k, n in sorted(kinds.items())],
        "need": len(mine),
        "done": len(rows) - len(mine),
        "top": [{"endpoint": r["endpoint"], "path": r["path"],
                 "hits": r["hits"], "total": r["total"], "hint": r["hint"]}
                for r in mine[:top]],
        "more": max(0, len(mine) - top),
    }


def _rows_of(key: str, root: str) -> int:
    """관리 화면이 내는 줄 수.  ★ 코드에 박지 않는다 (config/admin.json)."""
    import json as _j
    import os as _o

    with open(_o.path.join(root, "config", "admin.json"),
              encoding="utf-8") as f:
        return int(_j.load(f)[key])


def _check_reports(root: str) -> dict:
    """마지막 점검 기록.  ★ 「언제 봤는가」가 없으면 점검이 아니다 (S29).

    ★ 기록은 프로젝트에 쌓인다.  렌더용 임시 root 를 보면 늘 「없음」이다
    """
    import os as _o

    del root
    home = _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__)))
    out = {}
    # ★ 가벼운 점검은 「어긋난 것이 있을 때만」 기록한다 (개정 335) —
    #   기록이 0건인 것이 정상이다.  그래서 건수만으로 판단하지 않는다
    for key, sub in (("light", "light"), ("daily", "daily"),
                     ("weekly", "weekly")):
        base = _o.path.join(home, "outputs", sub)
        got = sorted(f for f in _o.listdir(base)
                     if f.endswith(".md")) if _o.path.isdir(base) else []
        got = [f for f in got if f != "last.json"]
        out[key] = {"name": got[-1][:-3] if got else None,
                    "count": len(got)}
    return out


def admin_audit(conn, account, req, root: str = ROOT, csrf: str = "", flash_key: str = "-",
         **_kw) -> tuple:
    from report.screens.admin import view_audit

    from report.screens.admin import validation_runs

    av = view_audit(account, conn)
    # ★ 절만 만들고 값을 안 넘기면 화면이 빈 채로 뜬다 (실측 08-15)
    ctx = {"a": av, "runs": validation_runs(conn)}
    return page(conn, account, "감사 조회", "audit.html", ctx, csrf=csrf,
                root=root, flash_key=flash_key)


def admin_docs(conn, account, req, root: str = ROOT, csrf: str = "",
               flash_key: str = "-", **_kw) -> tuple:
    from report.screens.admin import view_docs

    # ★ 목록에 있는 문서만 연다.  임의 경로를 받으면 파일이 새 나간다
    want = (req.get("query", {}).get("path") or "").strip() or None
    dv = view_docs(account, root=root)
    if want:
        allowed = {f["path"] for f in dv.files}
        if want not in allowed:
            raise ValidationError(f"열 수 없는 문서입니다: {want}",
                                  step="STEP 136")
        dv = view_docs(account, path=want, root=root)
    # ★ 뷰어는 읽기 전용이다 (V10-10).  본문이 크면 앞부분만 낸다 —
    #   목차만 내면 「내용이 없다」로 보인다 (실측 08-15)
    # 화면에 낼 본문 길이.  ★ 전문을 내면 한 쪽이 수백 KB 가 된다 (V4-17)
    body = dv.body[:int(_cfg("web.json", root)["doc_body_chars"])]
    return page(conn, account, "문서", "docs.html",
                {"doc": {"title": dv.title, "toc": dv.toc,
                         "editable": dv.editable, "files": dv.files,
                         "body": body}},
                root=root, csrf=csrf, flash_key=flash_key)


def _int_param(q: dict, name: str, default, minimum: int = 1):
    """★ 잘못된 값은 400 이다.  500 은 「우리 결함」이라는 뜻이다 (E-7)."""
    from errors import ValidationError

    raw = (q.get(name) or "").strip()
    if not raw:
        return default
    if not raw.isdigit() or int(raw) < minimum:
        raise ValidationError(
            f"{name} 은 {minimum} 이상 숫자여야 합니다: {raw[:20]}",
            step="STEP 106a")
    return int(raw)


# 화면에 칩으로 낼 조건.  ★ 정렬은 조건이 아니라 순서다 — 따로 낸다
# (필드, URL 이름, 라벨).  ★ 필드 이름과 URL 이름이 다르다 —
# 한쪽만 적으면 링크는 걸리는데 필터가 안 걸린다.
# 실측 08-16: 쪽 넘김이 target_key= 로 내보내는데 읽는 이름은 target 이라
# 차종 필터가 2쪽에서 통째로 풀렸다 (V11-58 이 grade 만 봐서 놓쳤다)
CHIP_FIELDS_FULL = (
    ("target_key", "target", "차종"),
    ("grade", "grade", "등급"),
    ("min_grade", "min_grade", "등급 하한"),
    ("axis", "axis", "축"),
    ("bucket", "bucket", "구간"),
    ("dealer", "dealer", "딜러"),
    ("year", "year", "연식"),
    ("km_max", "km_max", "주행 상한"),
    ("monthly_max", "monthly_max", "월납입 상한"),
    ("listing_status", "status", "상태"),
)
CHIP_FIELDS = tuple((f, lb) for f, _u, lb in CHIP_FIELDS_FULL)
URL_NAME = {f: u for f, u, _lb in CHIP_FIELDS_FULL}
# ★ 가격 상·하한은 한 칩이다.  × 하나로 둘 다 빠져야 한다 (STEP 149d · B-3)
PRICE_FIELDS = ("price_min", "price_max")
# 만원 단위.  ★ 화면이 만원으로 읽으므로 여기서 한 번만 나눈다 (V4-13)
WON_PER_MANWON = 10_000


def _manwon(won) -> str:
    """원 → 「N,NNN만」.  ★ 화면 표기를 한 자리에 모은다."""
    return f"{(won or 0) // WON_PER_MANWON:,}만"


def _site_buttons(flt, root: str = ROOT, conn=None) -> list:
    """사이트별로 거르는 단추 (개정 306 — 「엔카만」 「K카 직영만」 「전체」).

    ★ 사이트 이름을 코드에 박지 않는다.  config/sites.json 이 정본이다
    ★ 쓰는 사이트가 하나뿐이면 단추를 안 낸다 —
      늘 켜져 있는 단추 하나는 조작이 아니다
    ★★ 08-24 마스터 지적 — ★ 「기아가 ★ **안 받은 것처럼 보인다**」.
      ★ ★ 기아 CPO 1,020건은 ★ 다 받았고 ★ 전부 ★ 범위 밖이다 (우리 대상 0건).
      ★ ★ 그래서 ★ 단추에 ★ 「범위 밖 N건」을 ★ 함께 낸다 — ★ 0 만 보이면
        ★ 「못 받았다」로 읽힌다.  ★ 받은 것과 못 받은 것은 ★ 다른 말이다
    """
    # ★ SQL 은 store 에 있다 — ★ web/ 은 문자열을 못 쓴다 (V11-01)
    from store.core import site_counts

    scoped = site_counts(conn) if conn is not None else {}
    from store.crosssite import active_sites, load_sites

    import os as _o

    sites = load_sites(_o.path.join(root, "config", "sites.json"))
    live = active_sites(sites)
    if len(live) < 2:
        return []
    # ★ 「전체」 줄에도 ★ 같은 칸을 둔다 — ★ 없으면 템플릿이 빈 이름을 읽는다 (V11-38)
    # ★★★ 08-28 마스터 지적 — 「★ 목록 ★ 「전체」와 ★ 「전부」가 ★ 둘 다 2,856 이다.
    #   ★ ★ **왜 둘로 나뉘어 있나**」 (오판 #130 「전체의 테두리」와 같은 자리다)
    #   ★★ ★ 「거르지 않음」은 ★ **「전체」 한 낱말**로 한다 —
    #     ★ ★ 차종 전체 · 등급 전체 · 사이트 전체.  ★ 같은 뜻에 같은 말이다
    #   ★ ★ 「전부 지우기」는 ★ **동작**이라 ★ 「조건 지우기」로 갈랐다
    out = [{"label": "전체", "q": "all", "sell": "",
            "on": not flt.site, "live": None, "out_of_scope": None}]
    for name in live:
        one = sites.get(name) or {}
        label = one.get("label") or name
        tails = one.get("sell_type_labels") or {}
        if not tails:
            live_n, oos_n = scoped.get(name, (None, None))
            out.append({"label": f"{label}만", "q": name, "sell": "",
                        "on": flt.site == name and not flt.sell_type,
                        # ★ 「0」과 「안 받았다」를 가른다
                        "live": live_n, "out_of_scope": oos_n})
            continue
        for key, tail in tails.items():
            live_n, oos_n = scoped.get(name, (None, None))
            out.append({"label": f"{label} {tail}만", "q": name, "sell": key,
                        "on": flt.site == name and flt.sell_type == key,
                        "live": live_n, "out_of_scope": oos_n})
    return out


def _filter_chips(flt) -> list:
    """지금 걸린 조건.  ★ × 를 누르면 그 조건만 빠진다 (STEP 149d)."""
    import urllib.parse as _u

    def _rest(drop: tuple) -> dict:
        got = {URL_NAME[k]: getattr(flt, k) for k, _lb in CHIP_FIELDS
               if getattr(flt, k, None) and k not in drop}
        got.update({k: getattr(flt, k) for k in PRICE_FIELDS
                    if getattr(flt, k, None) is not None and k not in drop})
        if flt.order != "rank":
            got["order"] = flt.order
        return got

    out = []
    for key, label in CHIP_FIELDS:
        value = getattr(flt, key, None)
        if not value:
            continue
        rest = _rest((key,))
        out.append({"key": key, "label": label, "value": value,
                    "remove_url": "/listings?" + _u.urlencode(rest)
                    if rest else "/listings"})

    # ★ 가격은 상·하한을 묶어 한 칩으로 낸다 (B-3)
    lo, hi = flt.price_min, flt.price_max
    if lo is not None or hi is not None:
        rest = _rest(PRICE_FIELDS)
        span = (f"{_manwon(lo)} ~ {_manwon(hi)}" if hi is not None
                else f"{_manwon(lo)} 이상")
        out.append({"key": "price", "label": "가격", "value": span,
                    "remove_url": "/listings?" + _u.urlencode(rest)
                    if rest else "/listings"})
    return out


ORDER_LABELS = {
    "rank": "순위", "ratio": "비율", "price": "가격", "monthly": "월납입",
    "mileage": "주행거리", "year": "연식", "recent": "최근 등록",
    "gap": "시세 차이", "total": "총비용", "grade": "등급",
}

# 정렬 드롭다운 8종 — v1 이 낸 것 그대로 (STEP 149o · 개정 277).
# ★ 화면에 문구를 박지 않는다.  키는 ORDER_SQL 에 있는 것만 쓴다
# ★★ 08-28 — ★ 차례를 시안대로 맞췄다 (명령서 82장 · `v4m_listings_시안`).
#   ★ 시안 — ★ 추천 순위 → ★ **가격 낮은순** → ★ 등급순
#   ★ 전에는 ★ 추천 순위 → 등급순 → 가격 낮은순 이었다 — ★ `S46-100` 이 잡았다
ORDER_MENU = (
    ("rank", "추천 순위"), ("price", "가격 낮은순"), ("grade", "등급순"),
    ("price_desc", "가격 높은순"),
    ("mileage", "주행거리"), ("year", "연식 최신"),
    ("new", "등록 최신"), ("dom", "오래된 매물"),
)


def _order_menu(flt) -> list:
    """정렬 드롭다운.  ★ JS 가 꺼져도 <noscript> 단추로 낸다 (개정 248)."""
    return [{"key": k, "label": lb, "on": flt.order == k}
            for k, lb in ORDER_MENU]


def _carry(flt) -> list:
    """정렬 폼이 지금 조건을 그대로 들고 간다.
    ★ 정렬을 바꿨더니 필터가 풀리면 무엇을 보는지 알 수 없다 (V11-58)"""
    got = {URL_NAME[k]: getattr(flt, k) for k, _lb in CHIP_FIELDS
           if getattr(flt, k, None)}
    got.update({k: getattr(flt, k) for k in PRICE_FIELDS
                if getattr(flt, k, None) is not None})
    return [{"name": k, "value": v} for k, v in got.items()]


def _order_label(order: str) -> str:
    return ORDERS_LABELS_GET(order)


def ORDERS_LABELS_GET(order: str) -> str:
    return ORDER_LABELS.get(order, order)


def _condition_sentence(flt, count: int) -> str:
    """지금 조건을 사람 말로 (STEP 149g · B-8).

    ★ 조건이 없으면 「전체」다.  빈 문자열로 두면 무엇을 보고 있는지 모른다
    """
    parts = []
    for key, label in CHIP_FIELDS:
        value = getattr(flt, key, None)
        if value:
            parts.append(f"{label} {value}")
    lo, hi = flt.price_min, flt.price_max
    if lo is not None or hi is not None:
        parts.append("가격 " + (f"{_manwon(lo)} 이상" if hi is None
                              else f"{_manwon(lo)}~{_manwon(hi)}"))
    cond = " · ".join(parts) if parts else "전체"
    return (f"{cond} · {_order_label(flt.order)}순 · {count:,}건")


def _query_string(flt) -> str:
    """지금 조건을 그대로 다음 행동에 넘긴다 (STEP 149g)."""
    import urllib.parse as _u

    got = {URL_NAME[k]: getattr(flt, k) for k, _lb in CHIP_FIELDS
           if getattr(flt, k, None)}
    got.update({k: getattr(flt, k) for k in PRICE_FIELDS
                if getattr(flt, k, None) is not None})
    if flt.order != "rank":
        got["order"] = flt.order
    return _u.urlencode(got)


def _page_links(total: int, now: int, shown: int, size: int, links: int,
                url, one_page: bool = False) -> dict:
    """쪽 넘김 한 벌.  ★ 목록과 딜러가 같은 것을 쓴다 —
    두 벌로 두면 한쪽만 고쳐진다 (실측: 조건이 2쪽에서 풀렸다)"""
    pages = 1 if one_page else max(1, -(-total // size)) if size else 1
    now = min(max(1, now), pages)
    lo = max(1, now - links // 2)
    hi = min(pages, lo + links - 1)
    lo = max(1, hi - links + 1)
    return {
        "total": total, "shown": shown, "size": size,
        "page": now, "pages": pages, "many": pages > 1,
        "prev": url(now - 1) if now > 1 else "",
        "next": url(now + 1) if now < pages else "",
        "first": url(1) if lo > 1 else "",
        "last": url(pages) if hi < pages else "",
        "links": [{"n": n, "url": url(n), "on": n == now}
                  for n in range(lo, hi + 1)],
    }


def _simple_paging(total: int, now: int, shown: int, base: str,
                   root: str) -> dict:
    """조건이 없는 목록의 쪽 넘김 (딜러 등)."""
    from report.screens.build import _view_cfg

    return _page_links(total, now, shown, _view_cfg("rows_per_page", root),
                       _view_cfg("page_links", root),
                       lambda n: f"{base}?page={n}")


def _paging(conn, flt, shown: int, root: str) -> dict:
    """「3,471건 중 200건 · 1/18쪽」 + 쪽 넘김 (V11-55 · V11-58).

    ★ 쪽을 넘어도 지금 조건이 그대로 붙는다 — 2쪽에서 필터가 풀리면
      무엇을 보고 있는지 알 수 없다 (V11-58)
    """
    from report.screens.build import _view_cfg, count_listings

    qs = _query_string(flt)
    sep = "&" if qs else ""
    return _page_links(
        count_listings(conn, flt), flt.page, shown,
        _view_cfg("rows_per_page", root), _view_cfg("page_links", root),
        lambda n: f"/listings?{qs}{sep}page={n}", one_page=flt.show_all)


# 자주 쓰는 조건 단추 (STEP 149t).  ★ (필드, 값, 라벨, 설명)
# 누르면 켜지고 다시 누르면 꺼진다 — 켜진 것은 amber
FILTER_BUTTONS = (
    ("min_grade", "A", "A 이상만", "S · A 만 봅니다"),
    ("min_grade", "B", "B 이상만", "S · A · B 만 봅니다"),
    # ★ 위험 축은 「점수를 받았다 = 그 일이 없다」다.  bucket=1 이 양호다
    ("axis", "history.damage", "사고 양호", "사고 이력에서 점수를 받은 매물만"),
    ("axis", "history.rental", "렌트 아님", "렌트 이력에서 점수를 받은 매물만"),
    ("year", "2024", "2024년 이후", "2024년식 이후만"),
)
# ★ 축 단추는 「점수를 받은」 구간이다 — bucket=1.  0 으로 걸면 정반대가 된다
AXIS_BUTTON_BUCKET = "1"


def _filter_buttons(flt, base: str = "/listings") -> list:
    """자주 쓰는 조건을 단추로 (STEP 149t · V11-66 · V11-67).

    ★ 조건을 걸려면 표의 값을 눌러야만 하면 안 된다.
      표를 눌러 거는 것은 그것대로 두되, 위에도 있어야 한다
    ★ base — 매물이 나오는 화면은 조작이 같다 (개정 306 §3).
      추천에서 단추를 누르면 추천 안에서 걸려야 한다
    """
    import urllib.parse as _u

    out = []
    for field, value, label, tip in FILTER_BUTTONS:
        on = getattr(flt, field, None) == value
        got = {URL_NAME[k]: getattr(flt, k) for k, _lb in CHIP_FIELDS
               if getattr(flt, k, None)}
        got.update({k: getattr(flt, k) for k in PRICE_FIELDS
                    if getattr(flt, k, None) is not None})
        # ★ 다시 누르면 꺼진다 — 켜져 있으면 그 조건을 뺀 주소를 준다
        if on:
            got.pop(URL_NAME[field], None)
            if field == "axis":
                got.pop("bucket", None)
        else:
            got[URL_NAME[field]] = value
            if field == "axis":
                got["bucket"] = AXIS_BUTTON_BUCKET
        if flt.order != "rank":
            got["order"] = flt.order
        out.append({"label": label, "tip": tip, "on": on,
                    "url": base + "?" + _u.urlencode(got) if got else base})
    return out


def _model_menu(conn, flt) -> list:
    """차종 드롭다운 — 등록부에 있는 차종만 (개정 420).

    ★ config 의 목록이 아니라 **실제로 매물이 있는 차종**이다.
      없는 차종을 고르게 하면 「0건」만 나온다
    ★ SQL 은 store 가 갖는다 (V11-01)
    """
    # ★★ 08-28 (#14 · #16) — ★ `listing_models` 는 `status='active'` 하나만
    #   보고 세어 ★ 드롭다운 336 · 목록 183 으로 갈렸다.
    #   ★ 목록과 같은 조건으로 센다 (`model_counts`)
    from report.screens.build import model_counts

    now = (flt.model or "")
    return [{"key": k, "label": f"{k} ({n}건)", "on": k == now}
            for k, n in model_counts(conn, flt)]


def _pick_state(flt, root: str = ROOT) -> dict:
    """고른 조건을 문장으로 (개정 420) — 「G80 · 2,000~3,500만 · 리스 제외」."""
    unit = int(_cfg("web.json", root)["price_filter_unit_won"])
    lo = flt.price_min // unit if flt.price_min else ""
    hi = flt.price_max // unit if flt.price_max else ""
    said = []
    if flt.model:
        said.append(flt.model)
    if lo or hi:
        said.append(f"{lo or 0:,}~{hi or '위'}만")
    if getattr(flt, "km_max", None):
        said.append(f"{flt.km_max // 10000}만km 이하")
    for field, fmt in (("color_ext", "외장 {}"), ("color_int", "내장 {}"),
                       ("fuel", "{}"), ("trim", "트림 {}"),
                       ("region", "{}"), ("year", "{}년 이후")):
        got = getattr(flt, field, None)
        if got:
            said.append(fmt.format(got))
    if getattr(flt, "min_grade", None):
        said.append(f"{flt.min_grade} 이상")
    # ★ 점수 필터도 문장에 넣는다 — 「값 220 이상」
    for field, name in (("score_value_min", "값"), ("score_car_min", "차량"),
                        ("score_warranty_min", "보증"),
                        ("score_taste_min", "취향")):
        got = getattr(flt, field, None)
        if got is not None:
            said.append(f"{name} {got} 이상")
    if getattr(flt, "days_max", None) is not None:
        said.append(f"경과 {flt.days_max}일 이내")
    if getattr(flt, "price_dropped", False):
        said.append("가격 내린 것만")
    if getattr(flt, "warranty_month_min", None) is not None:
        said.append(f"보증 잔여 {flt.warranty_month_min}개월 이상")
    if getattr(flt, "honesty_min", None) is not None:
        said.append(f"정직도 {flt.honesty_min} 이상")
    said.append("리스·렌트 포함" if flt.lease else "리스 제외")
    # ★ 개정 433 — 제외를 보고 있으면 문장에 적는다.  안 적으면
    #   「왜 이상한 매물만 나오지」가 된다
    if getattr(flt, "excluded", False):
        said.append("관문 제외만")
    q = _keep_query(flt, lease="1")
    qx = _keep_query(flt, excluded="1")
    # ★ ＋12 의 값도 폼에 되돌려 넣는다 — 걸러면 사라지면 안 된다
    more = {k: (getattr(flt, k, None) if getattr(flt, k, None) is not None
                else "")
            for k in ("model", "km_max", "color_ext", "color_int", "min_grade",
                      "year", "option_min", "trim", "honesty_min", "days_max",
                      "warranty_month_min", "region", "score_value_min",
                      "score_car_min", "score_warranty_min",
                      "score_taste_min")}
    more["price_dropped"] = getattr(flt, "price_dropped", False)
    # ★ 체크상자도 되돌려 넣는다 — 거르면 체크가 풀리면 안 된다 (#11)
    more["unknown_too"] = getattr(flt, "unknown_too", False)
    more["with_sold"] = getattr(flt, "with_sold", False)
    return {**more,
            "price_min": lo, "price_max": hi, "lease": flt.lease,
            "excluded": getattr(flt, "excluded", False),
            "said": " · ".join(said), "lease_url": f"/listings?{q}",
            "excluded_url": f"/listings?{qx}"}



def _option_name_buttons(flt, root: str = ROOT) -> list:
    """옵션 거르개 — ★ **이름으로** 건다 (마스터 확정 08-25 · B).

    ★★ 이름은 ★ `config/dictionaries/option_names.json` 이 정본이다 (S14) —
      ★ 사이트 원문에서 뽑은 것이다.  ★ 지어내지 않는다
    ★ ★ 약자(HDA)로 걸지 않는다 — ★ 이름으로 건다 (가이드 지시)
    ★ ★ 축이 아니라 ★ **거르개**다 — ★ HDA 축 폐기(요구 61)와 어긋나지 않는다
    ★ 사전에 없는 이름은 ★ 단추를 안 낸다 — ★ 눌러도 0건이면 거짓말이다
    """
    import json as _j
    import os as _o
    import urllib.parse as _u

    path = _o.path.join(root, "config", "dictionaries", "option_names.json")
    if not _o.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as f:
        got = _j.load(f)
    have = set()
    for one in (got.get("by_site") or {}).values():
        # ★★ 마스터 확정 08-25 — ★ `discriminative: false` 인 사이트는 ★ 거르개에 안 낸다.
        #   ★ ★ 현대인증 16가지는 ★ **인증 조건**이라 ★ 전건이 같다 — ★ 매물을 못 가른다.
        #     ★ ★ 점수는 그대로 준다 — ★ 거르개에만 안 낸다
        if one.get("discriminative") is False:
            continue
        have |= set(one.get("names") or ())
    now = getattr(flt, "option_name", None)
    out = []
    # ★★ 묶음 먼저 (마스터 확정 08-25) — ★ 이름이 사이트마다 다르니 ★ 묶어서 건다.
    #   ★ ★ 「고속도로 주행 보조(HDA)」도 ★ 현대·기아 매물이 들어오면 ★ 이 묶음에 든다
    for key, one in (got.get("groups") or {}).items():
        hit = [n for n in sorted(have)
               if any(m in n for m in one.get("match") or ())]
        if not hit:
            continue                    # ★ 드는 이름이 없으면 단추를 안 낸다
        on = now == key
        out.append({"label": one.get("label") or key, "on": on,
                    # ★★ 파이썬이 만드는 주소도 ★ 인코딩한다 (마스터 지적 08-25 · 오판 119).
                    #   ★ ★ `| url` 필터는 ★ 템플릿에만 닿는다 — ★ 여기는 안 닿는다
                    "url": ("/listings" if on else
                            f"/listings?option_group={quote(str(key), safe='')}"),
                    "tip": f"「{key}」 묶음 — {len(hit)}가지 이름이 여기 듭니다"})
    for want in _o.environ.get("_", "") and () or OPTION_FILTER_NAMES:
        # ★ 사전에 있는 이름만 낸다 — ★ 부분 일치로 찾는다 (사이트마다 괄호가 다르다)
        hit = next((n for n in sorted(have) if want in n), None)
        if not hit:
            continue
        on = now == hit
        q = {} if on else {"option_name": hit}
        out.append({"label": hit, "on": on,
                    "url": f"/listings?{_u.urlencode(q)}" if q else "/listings",
                    "tip": f"「{hit}」가 있는 매물만 봅니다 (이름을 준 사이트만)"})
    return out


# ★ 거르개로 낼 옵션 — ★ 시안 옵션 절이 요구한 것 ＋ 마스터가 늘 보시는 것
#   ★ 사전에 그 이름이 없으면 ★ 단추가 안 나온다 (지어내지 않는다)
OPTION_FILTER_NAMES = ("고속도로 주행", "차로 유지", "스마트 크루즈",
                       "헤드업 디스플레이", "선루프", "통풍시트")


def _color_menus(conn, flt) -> dict:
    """색 거르개 — ★ 외장·내장을 ★ **한 번씩만** 조회한다 (V11-34).

    ★ 많은 것부터 다섯 · 나머지는 「더 보기 ▾」로 접는다 (마스터 확정 08-25)
    """
    ext = _distinct_options(conn, "color_ext_raw", flt.color_ext)
    ins = _distinct_options(conn, "color_int_raw", flt.color_int)
    ext_top, ext_rest = _split_top(ext)
    int_top, int_rest = _split_top(ins)
    return {"color_ext_top": ext_top, "color_ext_rest": ext_rest,
            "color_int_top": int_top, "color_int_rest": int_rest,
            # ★ 기본 줄의 「전체」 목록도 ★ 같은 조회를 쓴다 — ★ 또 안 부른다
            "color_ext_options": ext, "color_int_options": ins}


def _judge_buttons(flt, root: str = ROOT) -> list:
    """판정 다섯 — ★ 목록 카드의 배지와 ★ **같은 다섯**이다 (v3_listings_시안).

    ★ 축 목록은 ★ `CHIP_AXES` 하나가 정본이다 — ★ 여기서 다시 적지 않는다.
      ★ ★ 갈리면 ★ 카드에는 다섯인데 ★ 거르개는 넷이 된다
    ★ 이름은 `config/labels.json` 이 정본이다 (S14)
    """
    import urllib.parse as _u

    from report.screens.build import CHIP_AXES, _labels

    al = _labels(root)["AXIS_LABELS"]
    out = []
    for axis in CHIP_AXES:
        on = getattr(flt, "axis", None) == axis
        q = {} if on else {"axis": axis, "bucket": AXIS_BUTTON_BUCKET}
        out.append({"label": f"{al.get(axis, axis)} OK", "on": on,
                    "url": f"/listings?{_u.urlencode(q)}" if q else "/listings",
                    "tip": f"{al.get(axis, axis)} 에서 점수를 받은 매물만 봅니다"})
    return out


# ★★ 색은 ★ **옵션 절**에 넣는다 (마스터 확정 08-25 · B).
#   ★ 많은 것부터 다섯씩 내고 ★ 나머지는 「더 보기 ▾」로 접는다 —
#   ★ ★ 스물한 가지를 다 펴면 ★ 옵션 절이 못 읽힌다 (가이드 지시)
COLOR_TOP = 5


def _split_top(rows: list, top: int = COLOR_TOP) -> tuple:
    """많은 것부터 `top` 개 · 나머지.  ★ 자른 것을 말한다 (검토 17)."""
    return rows[:top], rows[top:]



def _fuel_options(picked, root: str = ROOT) -> list:
    """연료 고르개 — ★ 전체 · 전기만 · 하이브리드만 · 가솔린 · 디젤 (명령서 87장 ④).

    ★ 정본은 `config/web.json` 의 `fuel_groups` 다 (S14).  ★ 코드에 안 박는다
    """
    from report.screens.build import fuel_groups

    return [{"key": g["key"], "label": g["label"],
             "on": picked == g["key"]} for g in fuel_groups(root)]


def _distinct_options(conn, col: str, now) -> list:
    """그 칸에 실제로 있는 값 (개정 427 필터).

    ★ SQL 은 store 에 있다 — web/ 은 SQL 문자열을 못 쓴다 (V11-01)
    """
    from store.core import filter_options

    return [{"key": r["value"], "label": f"{r['value']} ({r['count']:,})",
             "on": r["value"] == now}
            for r in filter_options(conn, col)]


def _km_options(flt, root: str = ROOT) -> list:
    """주행 구간.  ★ 구간 값은 config 가 정본이다 (S14)."""
    unit = int(_cfg("web.json", root)["km_bucket"])
    now = getattr(flt, "km_max", None)
    return [{"key": k * unit, "label": f"{k * unit // 10000}만km 이하",
             "on": now == k * unit} for k in (3, 5, 7, 10, 15)]


def _grade_options(flt, root: str = ROOT) -> list:
    """등급 이상.  ★ 차례는 config/labels.json GRADE_ORDER 가 정본이다."""
    order = _cfg("labels.json", root)["GRADE_ORDER"]
    now = getattr(flt, "min_grade", None)
    return [{"key": g, "label": f"{g} 이상", "on": g == now} for g in order]


def _keep_query(flt, **more) -> str:
    """지금 조건을 그대로 들고 간다 (STEP 149g · V11-156).

    ★ 필터가 그대로 요청 파라미터가 된다 — 관심·비교·알림이 같은 조건을 쓴다
    ★ 값이 없는 조건은 안 넣는다
    """
    from urllib.parse import urlencode

    got = {}
    if flt.model:
        got["model"] = flt.model
    if flt.price_min:
        got["price_min"] = flt.price_min
    if flt.price_max:
        got["price_max"] = flt.price_max
    if flt.grade:
        got["grade"] = flt.grade
    if flt.lease:
        got["lease"] = "1"
    if getattr(flt, "excluded", False):
        got["excluded"] = "1"
    got.update(more)
    return urlencode(got)


def _carry_pick(flt) -> list:
    """거르기 폼이 잃지 말아야 할 것 — 정렬은 필터를 걸어도 안 풀린다."""
    got = []
    if flt.order:
        got.append({"name": "order", "value": flt.order})
    if flt.grade:
        got.append({"name": "grade", "value": flt.grade})
    return got


def _lease_hidden(conn, flt, root: str = ROOT) -> int:
    from report.screens.build import lease_hidden

    return lease_hidden(conn, flt, root)


def _excluded_hidden(conn, flt, root: str = ROOT) -> int:
    """관문 배제로 뺀 건수 (개정 433).  ★ 리스와 같은 방식이다."""
    from report.screens.build import excluded_hidden

    return excluded_hidden(conn, flt, root)


def _excluded_why(conn, flt) -> list:
    """★ 왜 뺐는지 (개정 433) — 「리스」 「골격 사고」 「침수」 「전손」.

    ★ 「제외 371건」만 내면 사람이 아무것도 못 한다.  사유가 판단 재료다
    """
    from report.screens.build import excluded_groups

    return excluded_groups(conn, flt.calc_version)


def _filter(conn, q: dict, ver: dict, root: str = ROOT) -> ListingFilter:
    """URL 파라미터 → 필터.  값 해석은 view_* 가 한다 (STEP 106a).

    ★ 목록을 만드는 곳이 여기 하나다.  두 벌로 두면 새 조건이 한쪽에만
      붙어 「링크는 걸리는데 필터는 안 걸린다」가 된다 (실측 08-15)
    """
    # ★ 월납입 상한은 가격 상한으로 되짚는다 — SQL 로 걸어야 쪽·건수가 맞는다
    # ★ 가격대는 만원 단위로 받는다 (개정 420).  사람이 「3,500만」이라 말한다 —
    #   원으로 받으면 0 을 네 번 더 쳐야 한다
    unit = int(_cfg("web.json", root)["price_filter_unit_won"])
    price_min = _int_param(q, "price_min", None, minimum=0)
    price_max = _int_param(q, "price_max", None, minimum=0)
    if price_min is not None:
        price_min *= unit
    if price_max is not None:
        price_max *= unit
    monthly_max = _int_param(q, "monthly_max", None, minimum=0)
    if monthly_max is not None:
        from report.finance import price_for_monthly

        cap = price_for_monthly(monthly_max, _cfg("finance.json", root),
                                q.get("target") or None)
        price_max = cap if price_max is None else min(price_max, cap)
    return ListingFilter(
        # ★ site=all 이면 전부 (개정 306).  ★ 안 주면 ★ **전부**다 —
        #   ★ ★ 전에는 `or "encar"` 라 ★ 엔카만 나왔다 (실측 08-24 · 3,259 / 5,319)
        site=(None if (q.get("site") or "") in ("", "all")
              else q.get("site")),
        sell_type=q.get("sell_type") or None,
        target_key=q.get("target") or None,
        option_name=q.get("option_name") or None,
        option_group=q.get("option_group") or None,
        grade=q.get("grade") or None,
        axis=q.get("axis") or None,
        bucket=q.get("bucket") or None,
        order=q.get("order")
        or ListingFilter.__dataclass_fields__["order"].default,
        # ★ 가격은 0 원도 뜻이 있다 — minimum 0 이다
        price_min=price_min,
        price_max=price_max,
        dealer=q.get("dealer") or None,
        year=q.get("year") or None,
        km_max=_int_param(q, "km_max", None, minimum=0),
        monthly_max=monthly_max,
        listing_status=q.get("status") or None,
        # ★ 성능부 ↔ 보험이 어긋난 것만 (V3-50)
        mismatch=q.get("mismatch") == "1",
        # ★ 리스·렌트는 기본으로 뺀다 (개정 420).  켜면 함께 낸다
        lease=q.get("lease") == "1",
        # ★★ 관문 배제는 기본으로 뺀다 (개정 433).  ?excluded=1 이면 그것만 낸다
        excluded=q.get("excluded") == "1",
        # ══ 개정 427 — 칩 7 · ＋12 (STEP 97) ══
        color_ext=q.get("color_ext") or None,
        color_int=q.get("color_int") or None,
        fuel=q.get("fuel") or None,
        trim=q.get("trim") or None,
        region=q.get("region") or None,
        option_min=_int_param(q, "option_min", None, minimum=0),
        honesty_min=_int_param(q, "honesty_min", None, minimum=0),
        days_max=_int_param(q, "days_max", None, minimum=0),
        price_dropped=q.get("price_dropped") == "1",
        # ★★ 08-28 (#11) — 「확인 못 한 것도 함께 보기」를 받는다
        unknown_too=q.get("unknown_too") == "1",
        # ★★★ 08-29 (마스터 3번) — 「팔린 것 숨기기」
        with_sold=q.get("with_sold") == "1",
        warranty_month_min=_int_param(q, "warranty_month_min", None,
                                      minimum=0),
        # ★ 점수 필터 — 화면의 막대를 그대로 조건으로 (V11-164)
        score_value_min=_int_param(q, "score_value_min", None, minimum=0),
        score_car_min=_int_param(q, "score_car_min", None, minimum=0),
        score_warranty_min=_int_param(q, "score_warranty_min", None,
                                      minimum=0),
        score_taste_min=_int_param(q, "score_taste_min", None, minimum=0),
        model=q.get("model") or None,
        min_grade=q.get("min_grade") or None,
        show_all=q.get("all") == "1",
        page=_int_param(q, "page", 1),
        calc_version=ver["calc_version"])


def recommend(conn, account, req, root: str = ROOT, csrf: str = "", flash_key: str = "-",
         **_kw) -> tuple:
    from report.screens.build import (
        axis_heads, excluded_groups, recommend_funnel, view_recommend,
    )

    ver = _versions(conn)
    flt = _filter(conn, req.get("query", {}), ver)
    rows = view_recommend(account, conn, flt, _cfg("finance.json", root), root)
    # ★ 뺀 것을 숨기지 않는다.  왜 뺐는지가 판단 재료다 (G-1)
    groups = excluded_groups(conn, ver["calc_version"])
    # ★ 단계마다 숫자를 낸다 — 어디서 줄었는지 눈으로 본다 (7번).
    #   ★ SQL 은 web/ 에 두지 않는다 (V11-01)
    funnel = recommend_funnel(conn, ver["calc_version"], len(rows))
    # ★ 매물이 나오는 화면은 조작이 같다 (개정 306 §3 · STEP 148).
    #   목록에만 정렬·단추를 두면 추천이 v1 보다 못해진다
    return page(conn, account, "추천", "recommend.html",
                {"rows": rows, "count": len(rows), "funnel": funnel,
                 # 부록 G 2절 — 후보 카드 6줄이 축 넷이다 (목록과 같은 머리말)
                 "axis_heads": axis_heads(root),
                 "buttons": _filter_buttons(flt, base="/recommend"),
                 "orders": _order_menu(flt),
                 "carry": _carry(flt),
                 "r": {"excluded_groups": groups,
                       "excluded_total": sum(g.count for g in groups)}},
                root=root, csrf=csrf, flash_key=flash_key)


def track(conn, account, req, root: str = ROOT, csrf: str = "",
          flash_key: str = "-", **_kw) -> tuple:
    """/track — ★ 같은 차가 여러 사이트에 (명령서 1-2 · v3_track_시안).

    ★★ 합치지 않는다.  ★ 갈린 것을 갈린 채로 낸다 (마스터 확정 08-24)
    ★ 정렬 기본은 ★ 「차액 큰 순」 — ★ 짝짓기가 틀린 것이 먼저 보인다
    """
    from report.screens.build import view_track

    ver = _versions(conn)
    q = req.get("query", {})
    got = view_track(account, conn, ver["calc_version"],
                     order=(q.get("order") or "gap"), root=root)
    return page(conn, account, "추적", "track.html", {"t": got}, csrf=csrf,
                root=root, flash_key=flash_key)


def compare(conn, account, req, root: str = ROOT, csrf: str = "", flash_key: str = "-",
         **_kw) -> tuple:
    """★ 분모가 다르면 총점을 비교하지 않는다 (STEP 107)."""
    from report.screens.build import view_compare

    ver = _versions(conn)
    q = req.get("query", {})
    raw = (q.get("ids") or "").strip()
    ids = [int(x) for x in raw.split(",") if x.strip().isdigit()]
    # ★ 관심 화면의 체크 상자는 id 를 여러 개 보낸다 (개정 427 — 비교 흡수).
    #   ★ ids= 주소도 그대로 산다 — 링크를 걸어 둔 사람이 있다
    got = q.get("id")
    for one in (got if isinstance(got, list) else [got] if got else []):
        if str(one).isdigit() and int(one) not in ids:
            ids.append(int(one))
    c = view_compare(account, conn, ids, ver["calc_version"],
                     _cfg("finance.json", root), _cfg("scoring.json", root),
                     root)
    return page(conn, account, "비교", "compare.html", {"c": c}, csrf=csrf,
                root=root, flash_key=flash_key)


def market(conn, account, req, root: str = ROOT, csrf: str = "", flash_key: str = "-",
         **_kw) -> tuple:
    from report.screens.build import market_trims, view_market

    q = req.get("query", {})
    target = q.get("target") or _first_target(conn)
    if not target:
        return page(conn, account, "시세", "empty.html", {}, csrf=csrf,
                root=root, flash_key=flash_key)
    # ★ 트림을 고르면 분포도 그 트림만 본다 (V11-83 · 개정 282·285)
    trim = q.get("trim") or None
    m = view_market(account, conn, target, _cfg("depreciation.json", root),
                    trim=trim)
    trims = market_trims(conn, target, root, picked=trim)
    return page(conn, account, "시세", "market.html",
                {"m": m, "trims": trims, "trim": trim,
                 "all_url": f"/market?target={quote(str(target), safe='')}"},
                csrf=csrf, root=root, flash_key=flash_key)


def _first_target(conn):
    from store.core import top_target

    return top_target(conn)


def dealers(conn, account, req, root: str = ROOT, csrf: str = "", flash_key: str = "-",
         **_kw) -> tuple:
    from report.screens.build import count_dealers, view_dealers

    q = req.get("query", {})
    now = _int_param(q, "page", 1)
    rows = view_dealers(account, conn, root=root, page=now)
    # ★ 719곳을 한 번에 보내지 않는다 — 139KB 였다 (검토 15)
    total = count_dealers(conn)
    return page(conn, account, "딜러", "dealers.html",
                {"rows": rows, "count": len(rows),
                 "paging": _simple_paging(total, now, len(rows), "/dealers",
                                          root),
                 # ★ 점이 하나도 없으면 화면이 그렇게 말한다 (V3-26)
                 "plotted": [d for d in rows if d.quad_y is not None],
                 # ★ 매물이 아니라 조건을 지켜본다 (STEP 117a)
                 "queries": _watch_queries(conn, account)},
                root=root, csrf=csrf, flash_key=flash_key)


def watch(conn, account, req, root: str = ROOT, csrf: str = "", flash_key: str = "-",
         **_kw) -> tuple:
    from report.screens.build import view_watch

    ver = _versions(conn)
    rows = view_watch(account, conn, _cfg("finance.json", root),
                      ver["calc_version"], root)
    return page(conn, account, "관심", "watch.html",
                {"rows": rows, "count": len(rows),
                 # ★ 매물이 아니라 조건을 지켜본다 (STEP 117a)
                 "queries": _watch_queries(conn, account),
                 # 진행 메모 (개정 362).  ★ 계약 4단계 대신 들어온 것이다
                 "notes": _watch_notes(conn, account, rows),
                 "note_kinds": _note_kinds()},
                root=root, csrf=csrf, flash_key=flash_key)


def _note_kinds() -> list:
    """진행 갈래.  ★ 순서가 아니다 — 정리하는 이름일 뿐이다 (개정 362)."""
    from store.watch import NOTE_KINDS

    return [{"key": k, "label": v} for k, v in NOTE_KINDS.items()]


def _watch_notes(conn, account, rows) -> list:
    """관심 매물별 진행 메모 (11장 STEP 118 · 개정 362 · V7-15).

    ★ 메모가 없는 매물도 낸다 — 적을 자리가 보여야 적는다
    ★ 남의 메모는 안 보인다 (V7-12).  notes_of 가 account_id 로 막는다
    """
    from store.watch import notes_of

    if account.role == ROLE_ANONYMOUS:
        return []
    mine: dict = {}
    for _nid, lid, _k, _kl, _b, _at in notes_of(conn, account.account_id):
        mine.setdefault(lid, [])
    got = []
    for r in rows:
        lid = r.listing.listing_id
        got.append({
            "listing_id": lid,
            "label": f"{r.listing.target_label} {r.listing.trim or ''}".strip(),
            "notes": [{"note_id": n[0], "kind": n[2], "kind_label": n[3],
                       "body": n[4], "noted_at": n[5]}
                      for n in notes_of(conn, account.account_id, lid)],
        })
    del mine
    return got


def run_view(conn, account, req, root: str = ROOT, csrf: str = "", flash_key: str = "-",
         **_kw) -> tuple:
    from report.screens.build import view_run

    ver = _versions(conn)
    r = view_run(account, conn, ver["run_id"], ver["calc_version"])
    return page(conn, account, "실행", "run.html", {"r": r}, csrf=csrf,
                root=root, flash_key=flash_key)


# ★ 아직 만들지 않은 화면.  「준비 중」을 정직하게 낸다 (STEP 149).
#   라우팅 표에서 빼면 「그런 화면이 없다」가 되어 계획이 사라진다
def login(conn, account, req, root: str = ROOT, csrf: str = "", flash_key: str = "-",
         **_kw):
    """★ 첫 관리자는 CLI 에서만 만든다.  웹 가입을 열면 누구나 관리자가 된다."""
    from store.admin import account_count, authenticate, change_secret

    form, method = req.get("form", {}), req.get("method", "GET")
    if method == "POST":
        from web.app import check_post, redirect

        check_post(req, csrf)
        if form.get("mode") == "change":
            change_secret(conn, account, form.get("secret", ""))
            return redirect("/", "비밀번호를 바꿨습니다", flash_key)
        # ★ 로그인 실패도 anonymous 다 (STEP 126).  예외를 던지지 않는다.
        #   실패를 403 「권한 부족」으로 내면 사람이 무엇이 틀렸는지 모른다
        try:
            acc = authenticate(conn, form.get("name", ""),
                               form.get("secret", ""))
        except PolicyError as e:
            # 시도 제한에 걸린 경우 — 사유를 그대로 낸다 (C-5)
            return _login_again(conn, account, str(e).split(" [")[0],
                                root, csrf, flash_key,
                                form.get("watch_listing_id") or "")
        if acc.role == ROLE_ANONYMOUS:
            return _login_again(conn, account,
                                "이름이나 비밀번호가 맞지 않습니다",
                                root, csrf, flash_key,
                                form.get("watch_listing_id") or "")
        # ★★ 개정 491 ⓗ — ♡ 를 누르고 로그인한 것이면 ★ 그 자리에서 담는다
        return _open_session(conn, acc, req,
                             watch=form.get("watch_listing_id") or "")

    # ★★ 개정 491 ⓗ — ♡ 를 누르고 온 것이면 ★ 그 매물을 들고 간다.
    #   ★ 로그인하면 담겨 있어야 한다.  「로그인하세요」만 내면 누른 것이 사라진다
    _want = str((req.get("query") or {}).get("listing_id") or "")
    ctx = {"no_account": account_count(conn) == 0,
           "must_change": getattr(account, "must_change_secret", False),
           "watch_listing_id": _want if _want.isdigit() else ""}
    return page(conn, account, "로그인", "login.html", ctx, csrf=csrf,
                root=root, flash_key=flash_key)


def _login_again(conn, account, why: str, root: str, csrf: str,
                 flash_key: str, watch: str = "") -> tuple:
    """로그인 화면을 다시 낸다.

    ★ 무엇이 틀렸는지는 말하지 않는다 — 「이름이 없다」와 「비밀번호가 틀렸다」를
      나누면 계정이 있는지 확인하는 데 쓰인다
    """
    from store.admin import account_count

    # ★ 다시 낼 때도 ★ 담으려던 매물을 들고 간다 (개정 491 ⓗ · V11-38)
    ctx = {"no_account": account_count(conn) == 0,
           "must_change": False, "error": why, "watch_listing_id": watch}
    return page(conn, account, "로그인", "login.html", ctx, csrf=csrf,
                root=root, flash_key=flash_key)


def _open_session(conn, acc, req=None, watch: str = ""):
    """세션을 열고 쿠키를 준다.  ★ 쿠키에는 session_id 만 담는다.

    ★ req 를 받는 이유는 하나다 — 지금이 HTTPS 인지 알아야
      Secure 를 붙일지 정할 수 있다 (X-Forwarded-Proto)
    """
    from datetime import datetime, timezone

    from store.admin import open_session
    from web.context import HTTP_SEE_OTHER
    from web.server import load_web_config
    from web.session import is_https, set_cookie

    sid = open_session(conn, acc, datetime.now(timezone.utc))
    cfg = load_web_config(ROOT)
    target = "/login" if acc.must_change_secret else "/"
    # ★★ 개정 491 ⓗ — 담으려던 매물이 있으면 ★ 담고 관심으로 보낸다.
    #   ★ 실패해도 로그인은 살린다 — 담기다 막혀 로그인이 안 되면 더 나쁘다
    if watch.isdigit() and not acc.must_change_secret:
        from errors import AlreadyWatched
        from store.core import vehicle_of
        from store.watch import watch_add as _add

        try:
            vid = vehicle_of(conn, int(watch))
            if vid is not None:
                _add(conn, vid, int(watch), _now(),
                     account_id=acc.account_id)
        except (AlreadyWatched, ValueError, KeyError):
            pass
        target = "/watch"
    return HTTP_SEE_OTHER, {
        "Location": target,
        # ★ HTTPS 로 들어왔으면 Secure 를 붙인다.  평문이면 붙이지 않는다 —
        #   붙이면 쿠키가 아예 안 가서 로그인이 안 된다
        "Set-Cookie": set_cookie(cfg["session_cookie"], sid,
                                 cfg["session_max_age_sec"],
                                 secure=is_https(req)),
    }, b""


def logout(conn, account, req, root: str = ROOT, csrf: str = "", flash_key: str = "-",
         **_kw):
    from web.app import check_post
    from web.context import HTTP_SEE_OTHER
    from web.server import load_web_config
    from web.session import is_https, set_cookie

    check_post(req, csrf)
    cfg = load_web_config(root)
    return HTTP_SEE_OTHER, {
        "Location": "/",
        "Set-Cookie": set_cookie(cfg["session_cookie"], "", 0,
                                 secure=is_https(req)),
    }, b""


# ── 관심 (11장 · 시안 v2_watch) ─────────────────────────────────────
def _watch_queries(conn, account) -> list:
    """조건 목록.  ★ 비로그인은 조건을 갖지 않는다 (STEP 117a)."""
    from store.watch import watch_query_rows

    if getattr(account, "account_id", None) is None:
        return []
    return watch_query_rows(conn, account.account_id)


def watch_query_post(conn, account, req, root: str = ROOT, csrf: str = "",
                     flash_key: str = "-", checked: bool = False, **_kw):
    """조건 알림 등록 (STEP 117a).

    ★ 매물이 아니라 조건을 지켜본다.  매물은 사라지지만 조건은 남는다
    """
    from store.admin import require_role
    from store.watch import add_watch_query
    from web.app import check_post, redirect

    if not checked:
        check_post(req, csrf)
    require_role(account, ROLE_USER)
    form = req.get("form", {})
    cond = {k: v for k, v in (
        ("target_key", form.get("target_key")),
        ("trim_badge", form.get("trim_badge")),
        ("year_min", form.get("year_min")),
        ("mileage_max", _int_or_none(form.get("mileage_max"))),
        # ★ 목록에서 걸어 둔 축 조건을 그대로 넘긴다 (STEP 149g).
        #   다시 묻지 않는다 — 문장에 적어 놓고 안 넘기면 어긋난다
        ("axis", form.get("axis")),
        ("bucket", form.get("bucket")),
    ) if v}
    add_watch_query(conn, account.account_id, form.get("name", ""), cond,
                    _now(), min_grade=form.get("min_grade") or None,
                    max_price_won=_int_or_none(form.get("max_price_won")))
    return redirect("/watch", "조건을 등록했습니다", flash_key)


def _int_or_none(raw):
    return int(raw) if raw and str(raw).isdigit() else None


def watch_add_post(conn, account, req, root: str = ROOT, csrf: str = "", flash_key: str = "-",
         **_kw):
    """★ 관심은 차량 단위다.  매물이 내려가도 추적이 끊기지 않는다 (STEP 111)."""
    from store.watch import watch_add as _add
    from web.app import check_post, redirect

    from store.admin import require_role

    check_post(req, csrf)
    # ★ 조건 등록은 같은 경로로 받는다 (STEP 117a).
    #   라우팅 표에 없는 경로를 만들지 않는다 (V11-12)
    kind = req.get("form", {}).get("kind") or ""
    if kind == "query_close":
        # ★ 지우지 않고 끈다 (STEP 117a).  남의 것은 못 끈다
        from store.watch import close_watch_query

        require_role(account, ROLE_USER)
        raw_q = req.get("form", {}).get("query_id") or ""
        if not raw_q.isdigit():
            raise ValidationError("그 조건이 없습니다", step="STEP 117a")
        close_watch_query(conn, int(raw_q), account.account_id)
        return redirect("/watch", "조건 알림을 껐습니다", flash_key)
    if kind == "query":
        return watch_query_post(conn, account, req, root=root, csrf=csrf,
                                flash_key=flash_key, checked=True)
    if kind in ("note", "note_delete"):
        # 진행 메모 (개정 362).  ★ 새 경로를 만들지 않는다 —
        #   라우팅 표에 없는 경로는 V11-12 가 잡는다
        return _watch_note_post(conn, account, req, kind, flash_key)
    raw = req.get("form", {}).get("listing_id") or ""
    if not raw.isdigit():
        return redirect("/listings", "그 매물은 담을 수 없습니다", flash_key)
    lid = int(raw)          # ★ 대리키는 정수다.  문자열로 넘기면 타입이 어긋난다
    # ★ 승인 전(pending)도 담지 못한다.  anonymous 만 보면 승인제가 뚫린다
    #   — 「승인 전에는 관심 등록 불가」가 규격이다 (STEP 126 · 실측 08-15)
    if account.role == ROLE_PENDING:
        raise PolicyError(
            "승인을 기다리는 중입니다. 승인되면 관심을 담을 수 있습니다",
            step="STEP 126")
    if account.role == ROLE_ANONYMOUS:
        # ★ 담으려던 대상을 보여 준다.  「로그인하세요」만 내면
        #   무엇을 하려 했는지 잊는다 (STEP 149i · E-9)
        return _watch_invite(conn, account, lid, root, csrf, flash_key,
                             req.get("query", {}))
    from store.core import vehicle_of

    vid = vehicle_of(conn, lid)
    if vid is None:
        return redirect("/listings", "차량이 확정되지 않아 담을 수 없습니다",
                        flash_key)
    from errors import AlreadyWatched

    try:
        _add(conn, vid, lid, _now(), account_id=account.account_id)
    except AlreadyWatched:
        # ★ 결함이 아니다.  뒤로가기 재전송에서 흔하다 — 알리고 보낸다
        return redirect("/watch", "이미 관심에 담은 차량입니다", flash_key)
    return redirect("/watch", "관심에 담았습니다", flash_key)


def _watch_note_post(conn, account, req, kind: str, flash_key: str):
    """진행 메모를 적거나 지운다 (11장 STEP 118 · 개정 362).

    ★ 단계를 강제하지 않는다.  「연락함」 없이 「끝」을 적어도 된다
    금지   계약·대행 절차를 넣는 것 (S37-1)
    """
    from store.admin import require_role
    from store.watch import note_add, note_delete
    from web.app import redirect

    require_role(account, ROLE_USER)
    form = req.get("form", {})
    if kind == "note_delete":
        raw = form.get("note_id") or ""
        if not raw.isdigit():
            raise ValidationError("그 메모가 없습니다", step="STEP 118")
        note_delete(conn, int(raw), account.account_id)
        return redirect("/watch", "메모를 지웠습니다", flash_key)
    raw = form.get("listing_id") or ""
    if not raw.isdigit():
        raise ValidationError("그 매물이 없습니다", step="STEP 118")
    note_add(conn, account.account_id, int(raw), form.get("note_kind") or "",
             form.get("body") or "", _now())
    return redirect("/watch", "진행을 적었습니다", flash_key)


def _watch_invite(conn, account, listing_id: int, root: str, csrf: str,
                  flash_key: str, query: dict) -> tuple:
    """관심 등록 로그인 유도 (STEP 149i).

    ★ 등급 · 판정 근거 · 시세는 로그인 없이 본다.
      판정을 보여 주는 것이 이 도구의 목적이지 가입 유도가 아니다
    """
    from report.screens.build import view_listings
    from report.screens.views import ListingFilter

    ver = _versions(conn)
    # ★ 관심에 담으려는 그 매물이다.  리스라고 빼면 담을 수가 없다 (개정 420)
    rows = [r for r in view_listings(
        account, conn,
        ListingFilter(calc_version=ver["calc_version"], lease=True),
        _cfg("finance.json", root), root) if r.listing_id == listing_id]
    back = "&".join(f"{k}={v}" for k, v in (query or {}).items())
    return page(conn, account, "관심 등록", "watch_invite.html",
                {"row": rows[0] if rows else None, "listing_id": listing_id,
                 "back": f"/listings?{back}" if back else "/listings"},
                csrf=csrf, root=root, flash_key=flash_key)


def watch_update_post(conn, account, req, path_vars: dict, root: str = ROOT,
                 csrf: str = "", flash_key: str = "-",
         **_kw):
    """목표가 · 알림 조건 · 빼기."""
    from store.watch import watch_close, watch_update as _upd
    from web.app import check_post, redirect

    check_post(req, csrf)
    form = req.get("form", {})
    raw = path_vars.get("watch_id") or ""
    if not raw.isdigit():
        return redirect("/watch", "그 관심 항목이 없습니다", flash_key)
    wid = int(raw)
    if form.get("action") == "remove":
        # ★ closed_reason 은 bought · lost · dropped 뿐이다 (DDL CHECK)
        watch_close(conn, wid, "dropped", _now(),
                    account_id=account.account_id)
        return redirect("/watch", "관심에서 뺐습니다", flash_key)
    price = form.get("target_price_won")
    _upd(conn, wid, account.account_id,
         target_price_won=int(price) if price else None)
    return redirect("/watch", "목표가를 저장했습니다", flash_key)  # _upd 가 conn.execute


def _now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


# ── 관리자 폼 (13장 · 시안 v2_admin_*) ──────────────────────────────
def _reason_gate(conn, account, req, csrf: str) -> dict:
    """사유만 요구한다 (STEP 126 · D-2).

    ★ 계정 변경에는 미리보기가 뜻이 없다 — 미리 볼 것이 없다.
      그러나 사유는 있어야 한다.  나중에 「왜 이 사람이 중지됐나」의 근거다
    """
    from errors import PolicyError
    from web.app import check_post

    check_post(req, csrf)
    form = req.get("form", {})
    if not (form.get("reason") or "").strip():
        raise ValidationError("사유가 있어야 바꿉니다", step="STEP 126")
    from store.adminops import running_job

    if running_job(conn):
        raise PolicyError("실행 중에는 계정을 바꾸지 않습니다",
                          step="STEP 132")
    return form


def _gate(conn, account, req, csrf: str, group: str | None = None):
    """★ 미리보기 없이 저장이 안 된다 (V11-09 · STEP 138).

    group   이 화면의 메뉴 분류.  ★ 잠금은 「조정」에만 건다 (STEP 132a).
            큐가 밀렸다고 운영·탐색까지 잠그면, 큐를 푸는 화면조차 못 연다 —
            실제로 두 번 갇혔다 (실측 08-16).  화면 표시(LOCKED_GROUPS)는
            조정만 잠근다고 하는데 관문은 전부 잠그고 있었다
    """
    from report.screens.admin import LOCKED_GROUPS, SaveGate
    from store.adminops import running_job
    from web.app import check_post

    check_post(req, csrf)
    form = req.get("form", {})
    locks = group is None or group in LOCKED_GROUPS
    gate = SaveGate(previewed=form.get("previewed") == "1",
                    reason_given=bool(form.get("reason", "").strip()),
                    locked=bool(running_job(conn)) and locks)
    if gate.can_save:
        return form

    from errors import PolicyError

    # ★ 세 가지를 한 문장으로 내면 무엇을 고쳐야 할지 모른다.
    #   잠김은 409(지금이 아닐 뿐) · 절차 미비는 400(내가 안 한 것)이다
    if gate.locked:
        raise PolicyError(
            "수집·재계산이 도는 동안에는 잠깁니다. 끝난 뒤 다시 누르십시오",
            step="STEP 132")
    if not gate.previewed:
        raise PolicyError(
            "미리보기를 먼저 눌러 무엇이 달라지는지 확인하십시오",
            step="STEP 138")
    raise PolicyError("사유를 적어야 저장합니다. "
                      "나중에 「왜 이렇게 됐나」의 근거입니다",
                      step="STEP 138")
    return form


def _first_flag(rows: list) -> list:
    """첫 줄에 표시.  ★ 기본 선택을 「전 차종」에 두지 않는다 (STEP 149l)."""
    return [{**r, "first": i == 0} for i, r in enumerate(rows)]


def _all_hours(conn, root: str) -> str:
    """전 차종에 걸리는 대략 시간 (STEP 149l).

    ★ 「얼마나 오래」를 안 적으면 위험도를 가늠할 수 없다.
      어림값이라 화면에 「약」을 붙여 쓴다 — 단정하지 않는다
    """
    try:
        site = _cfg("endpoints.json", root)["encar"]
        gap = site["interval_sec"]
        per = float(gap[1] if isinstance(gap, list) else gap)
        targets = max(len(_cfg("targets.json", root)), 1)
    except (KeyError, TypeError, ValueError, IndexError):
        # ★ 「—」로 적지 않는다 (부록 G · G-4).  왜 못 내는지를 적는다
        return "설정을 읽지 못했습니다"
    from store.core import collect_scale

    seen, known = collect_scale(conn)
    # 매물마다 상세·점검·이력·진단 4번 부른다 (STEP 21)
    per_target = seen / known
    calls = per_target * targets * ENDPOINTS_PER_LISTING
    return f"{calls * per / SEC_PER_HOUR:.1f}"


# 매물 하나에 부르는 엔드포인트 수 (STEP 21).  ★ 수를 코드에 박지 않는다
ENDPOINTS_PER_LISTING = 4
SEC_PER_HOUR = 3600


def admin_run(conn, account, req, root: str = ROOT, csrf: str = "",
              flash_key: str = "-", plan=None, reason_rows=None,
              resume=None, **_kw):
    """수집 실행 지시.  ★ 단계를 직접 고르지 않는다 — 사유가 정한다."""
    from store.adminops import enqueue_recalc, running_job
    from web.app import redirect

    if req.get("method") == "POST":
        # ★ 중단은 잠금을 「푸는」 행동이다.  잠금에 걸리면 영영 못 멈춘다
        if (req.get("form", {}).get("action") or "") == "halt":
            from web.app import check_post

            check_post(req, csrf)
            form = req.get("form", {})
            if not (form.get("reason") or "").strip():
                raise ValidationError("사유가 있어야 중단합니다",
                                      step="STEP 132")
        else:
            form = _gate(conn, account, req, csrf, group=GROUP_OPS)
        if (form.get("action") or "") == "halt":
            # ★ 중단해도 지금까지 받은 것은 남는다.  재개점을 낸다 (STEP 52)
            from store.adminops import halt_job

            # ★ 재개점 계산기는 주입받는다.  web 은 collect 를 모른다
            #   (STEP 15a · V4-22)
            step = halt_job(conn, account, form.get("job_id") or "",
                            form.get("reason", ""), at=_now(),
                            resume=resume)
            return redirect("/admin/run",
                            f"중단했습니다 — 재개점 {step or '없음'}",
                            flash_key)
        # ★ 위험이 높은 행동은 문구를 직접 입력받는다 (STEP 149l).
        #   라디오 하나로 3.8시간이 도는 것을 막는다 (실측 08-15)
        # ★★★★ 08-29 (UI_REVIEW 25-2 · 개정 837) — ★ `all` 적기를 ★ **없앴다.**
        #   ★★ 마스터 — 「★ 전체가 기본이고 ★ all 사유 같은 것 생략하고」
        #   ★ 「잘못 눌러 3.8시간이 그냥 도는 일을 막으려고」 — ★ 그 걱정은 옳았다.
        #     ★ 그러나 ★ 마스터께서는 ★ 늘 전체를 돌리신다 (26종이 다 마스터 것이다).
        #   ★ ★ **막는 것이 아니라 ★ 알린다** — ★ 화면이 「약 N시간」을 크게 낸다
        if plan is None:
            # ★ 배선 누락이다.  TypeError 로 500 을 내면 원인이 안 보인다
            raise WiringError(
                "재처리 결정표가 주입되지 않았다 — make_app(plan=...) 을 확인한다",
                step="STEP 132")
        enqueue_recalc(conn, account, form.get("reason", ""),
                       form.get("scope") or "all", "web", plan=plan)
        # ★ 시킨 뒤 ★ **보는 화면으로 넘긴다** (25-1 필수)
        return redirect("/admin/status", "실행을 큐에 넣었습니다", flash_key)

    from report.screens.admin import job_log, run_progress, _recent_runs

    ctx = {"reasons": list(reason_rows or ()),
           **run_progress(conn, root),
           "running": running_job(conn),
           "targets": _first_flag(_target_rows(conn)),
           # 전 차종에 걸리는 시간.  ★ 「얼마나 오래」를 안 적으면
           #   위험도를 가늠할 수 없다 (STEP 149l)
           "all_hours": _all_hours(conn, root),
           # ★ 절만 만들고 값을 안 넘기면 화면이 빈 채로 뜬다 (실측 08-15)
           "job_log": job_log(conn),
           "recent_runs": _recent_runs(conn)}
    # ★★★★ 08-29 (UI_REVIEW 25-1 · 개정 837) — ★ **시키는 화면은 안 바뀐다.**
    #   ★★ 마스터 — 「★ 5초마다 리로드 되니 ★ 내가 작업 지시를 못 하잖아」
    #   ★ 도는 것을 보는 자리는 ★ `/admin/status` 다 — ★ 거기서만 5초마다 돈다.
    #   ★ 검산 `S46-115`
    return page(conn, account, "수집 실행", "admin_run.html", ctx, csrf=csrf,
                root=root, flash_key=flash_key, refresh_sec=0)


def _target_rows(conn) -> list:
    from store.core import target_counts

    return target_counts(conn)


# 반입 행동 3종 (STEP 136a ④⑤⑥).  ★ 미리보기는 저장이 아니다
IMPORT_PREVIEW, IMPORT_SAVE, IMPORT_COLLECT = "preview", "import", "collect"

# 이 화면들의 메뉴 분류.  ★ 잠금 단위가 메뉴 단위와 같아야 한다 (STEP 138)
GROUP_OPS = "운영"


def admin_dict(conn, account, req, root: str = ROOT, csrf: str = "",
               flash_key: str = "-", **_kw):
    """사전 확정 (13장 STEP 136e).

    ★ 확정을 자동으로 하지 않는다.  사람이 원문을 보고 누른다 (개정 267)
    ★ 'list' 출처는 「전체 집합이 아니다」를 화면이 말한다 (V10-25)
    """
    from report.screens.admin import dict_state
    from store.adminops import apply_dict_decision
    from web.app import redirect

    if req.get("method") == "POST":
        form = _gate(conn, account, req, csrf)
        axis = (form.get("axis") or "").strip()
        action = (form.get("action") or "").strip()
        # ★ 사이트를 화면이 준다 — ★ 값이 사이트마다 같은 글자일 수 있다 (08-24).
        #   ★ 안 주면 예전처럼 encar 다 — ★ 옛 화면과 옛 시험이 그대로 돈다
        site = (form.get("site") or "encar").strip()
        picked = [v for k, v in form.items()
                  if k.startswith("v_") and v]
        if not picked:
            # 축 단위 묶음 확정 — 그 사이트·축의 대기 전부다 (STEP 136e ③)
            from store.adminops import pending_enums

            picked = [r["value"] for r in pending_enums(conn, site)
                      if r["axis"] == axis]
        got = apply_dict_decision(conn, account, axis=axis, values=picked,
                                  action=action, reason=form.get("reason", ""),
                                  at=_now(), site=site)
        return redirect("/admin/dict",
                        f"{site} {got['axis']} — {got['action']} {got['done']}/"
                        f"{got['asked']}종 처리했습니다", flash_key)

    return page(conn, account, "사전 확정", "admin_dict.html",
                dict_state(conn), csrf=csrf, root=root, flash_key=flash_key)


def admin_status(conn, account, req, root: str = ROOT, csrf: str = "",
                 flash_key: str = "-", **_kw):
    """진행 지켜보기 (13장 STEP 136f).

    ★ 읽기 전용이다.  POST 가 없다 — 실행은 /admin/run 에서만 한다
    ★ JS 를 쓰지 않는다.  meta refresh 라 꺼져 있어도 새로고침으로 보인다
    """
    from report.screens.admin import status_view

    ctx = status_view(conn, root)
    return page(conn, account, "진행", "admin_status.html", ctx,
                csrf=csrf, root=root, flash_key=flash_key,
                refresh_sec=ctx.get("poll_sec", 0))


def admin_collect(conn, account, req, root: str = ROOT, csrf: str = "",
                  flash_key: str = "-", collect_urls=None, plan=None, **_kw):
    """브라우저 수집 (13장 STEP 136c).

    ★ 브라우저가 사용자 회선으로 엔카를 부르고, 서버는 받은 원문을 저장만 한다.
      서버 IP 는 /search/ 가 407 이다 — 그 차이를 메우는 것이 이 화면이다
    ★ ②(사람이 눈으로 확인)를 건너뛰지 않는다.  _gate 가 previewed 를 요구한다
    금지   서버가 이 응답을 다시 검증하려고 엔카를 부르는 것 — 막혀 있다
    """
    from report.screens.admin import collect_state
    from store.adminops import save_browser_catch
    from web.app import redirect

    if req.get("method") == "POST":
        form = _gate(conn, account, req, csrf, group=GROUP_OPS)
        kind = (form.get("kind") or "list").strip()
        body = form.get("body") or ""
        # ★ 조각 전송 (개정 307) — facet 은 하나의 JSON 이라 내용으로 못 나눈다.
        #   바이트를 나누고 여기서 이어붙인다.  원문은 그대로 복원된다 (P3)
        chunked = bool(form.get("chunk_key"))
        if chunked:
            done, body = _take_chunk(form)
            if not done:
                # ★ 조각마다 새 토큰을 실어 보낸다 — 수십 번 POST 한다
                return redirect("/admin/collect", body, flash_key, csrf=csrf)
        if not body.strip():
            raise ValidationError(
                "받은 원문이 비어 있습니다 — 먼저 「조회」를 눌러 확인하십시오",
                step="STEP 136c")
        got = save_browser_catch(
            conn, account, kind=kind, text=body, site=form.get("site") or "encar",
            target_key=(form.get("target_key") or "").strip() or None,
            request_url=form.get("url") or "", reason=form.get("reason", ""),
            at=_now(), http_code=_int_or_none(form.get("http_code")),
            count=_int_or_none(form.get("count")),
            items=_int_or_none(form.get("items")) or 0,
            axis_count=_int_or_none(form.get("axis_count")),
            run_id=_run_stamp("browser"), chunked=chunked)
        # ★ 목록이 들어왔으면 나머지를 서버가 이어서 한다 (STEP 136g · 개정 314).
        #   사람이 「이어서 해라」를 말해야 하는 것을 없앤다
        queued = ""
        if kind == "list" and plan is not None:
            from store.adminops import enqueue_after_list_save

            job = enqueue_after_list_save(conn, account, at=_now(), plan=plan)
            queued = (f" · 나머지를 이어서 합니다 (작업 {job[:8]}) — "
                      "화면을 닫으셔도 됩니다"
                      if job else " · 이미 도는 작업이 있어 큐에 넣지 않았습니다")
        return redirect(
            "/admin/collect",
            f"{kind} 원문을 저장했습니다 — raw_id {got.raw_id} · "
            f"{got.opened} 를 열었습니다 (origin=browser){queued}", flash_key,
            csrf=csrf)

    ctx = collect_state(conn, collect_urls, root=root)
    return page(conn, account, "브라우저 수집", "admin_collect.html", ctx,
                csrf=csrf, root=root, flash_key=flash_key)


def _take_chunk(form: dict) -> tuple:
    """조각을 모은다.  다 오면 (True, 원문) · 아니면 (False, 진행 문구).

    ★ 하나라도 빠지면 저장하지 않는다 — 반쪽을 원문이라 부르지 않는다
    """
    import time

    from store import chunk

    key = form["chunk_key"].strip()
    seq = _int_or_none(form.get("chunk_seq")) or 0
    total = _int_or_none(form.get("chunk_total")) or 1
    raw = form.get("body") or ""
    part = raw.encode("utf-8")
    # ★★ 조각마다 그 자리에서 대조한다 (V11-148).
    #   마지막에 몰아 터지면 어느 조각이 문제인지 알 수 없다.
    #   ★ 「몇 번째 조각인지」를 문구에 적는다
    _verify_part(raw, part, form, seq, total)
    got = chunk.put(key, seq, total, part, time.time(),
                    float(_cfg("web.json", ROOT)["chunk_stale_sec"]))
    if not got["done"]:
        return False, f"{form.get('kind', 'facet')} {got['got']}/{total} 조각"
    want_len = _int_or_none(form.get("chunk_len"))
    want_hash = (form.get("chunk_hash") or "").strip()
    try:
        body = chunk.take(key, want_len, want_hash)
    except ValueError as e:
        raise ValidationError(f"조각을 잇지 못했습니다 — {e}",
                              step="STEP 136c") from e
    text = body.decode("utf-8", "replace")
    # ★ 이어붙인 것이 온전한가 (S42-2).  U+FFFD 가 하나라도 있으면
    #   글자가 깨진 것이다 — 「400 이 안 났다」는 완료 근거가 아니다
    lost = text.count("\ufffd")
    if lost:
        raise ValidationError(
            f"이어붙인 원문에 깨진 글자가 {lost}자 있습니다 — "
            f"조각 절단면이 글자 가운데를 잘랐습니다",
            step="STEP 136c",
            action="화면을 새로 열고 다시 저장하십시오. "
                   "그래도 나면 조각 크기를 줄여야 합니다")
    return True, text


def _verify_part(raw: str, part: bytes, form: dict, seq: int,
                 total: int) -> None:
    """조각 하나가 온 그대로인가 (V11-148 · 개정 395).

    ★ 브라우저가 보낸 길이·해시와 서버가 받은 것을 그 자리에서 견준다.
      어긋나면 그 조각에서 멈춘다 — 「조각 3/9 가 깨졌습니다」
    ★ 안 보내면 안 본다.  옛 화면과도 돈다
    """
    import hashlib

    want_len = _int_or_none(form.get("chunk_part_len"))
    want_hash = (form.get("chunk_part_hash") or "").strip()
    where = f"조각 {seq + 1}/{total}"
    # ★ 글자가 깨졌으면 길이부터 다르다.  먼저 그것을 말한다
    if "\ufffd" in raw:
        raise ValidationError(
            f"{where} 가 깨졌습니다 — 글자 가운데가 잘렸습니다",
            step="STEP 136c",
            action="화면을 새로 열고 다시 저장하십시오 (절단점 규칙이 바뀌었습니다)")
    if want_len is not None and want_len != len(part):
        raise ValidationError(
            f"{where} 가 깨졌습니다 — 길이가 다릅니다 "
            f"(받은 {len(part):,} · 보낸 {want_len:,})",
            step="STEP 136c",
            action="화면을 새로 열고 다시 저장하십시오")
    if want_hash:
        got = hashlib.sha256(part).hexdigest()
        if got != want_hash:
            raise ValidationError(
                f"{where} 가 깨졌습니다 — 해시가 다릅니다 "
                f"(받은 {got[:12]} · 보낸 {want_hash[:12]})",
                step="STEP 136c",
                action="화면을 새로 열고 다시 저장하십시오")


# ★ 이어붙인 원문임을 남긴다 (개정 307).  한 번에 보낸 것이 아니다 —
#   V11-47 은 「한 POST 가 상한을 넘지 않았는가」를 보는 검사다
CHUNKED_MARK = "chunked"


def _run_stamp(prefix: str) -> str:
    """화면이 넣은 원문의 run_id (A-10 · V1-19).

    ★ 파이프라인 실행이 아니어도 「어느 실행이 넣었나」가 있어야 되짚는다.
      접두어로 수집분과 구분한다 — 섞어 보이면 안 된다 (STEP 136a · 136c)
    """
    from datetime import datetime, timezone

    return prefix + "-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")


def _int_or_none(value):
    raw = (value or "").strip()
    return int(raw) if raw.lstrip("-").isdigit() else None


def admin_import(conn, account, req, root: str = ROOT, csrf: str = "",
                 flash_key: str = "-", plan=None, **_kw):
    """목록 반입 (13장 STEP 136a · 136b).

    ★ 반입은 「수집」이다.  탐색이 아니다 — 원문이 raw_response 에 들어간다
    ★ 붙여넣은 것이 어느 형식인지 사람에게 묻지 않는다.  보고 판별한다
    금지   반입분을 수집분과 섞어 「우리가 받았다」로 보이게 하는 것
           origin='collector' · actual='collector' 로 남기는 것
    """
    from report.screens.admin import import_state, parse_import_text
    from store.adminops import import_listings, preview_import
    from web.app import check_post, redirect

    site = (req.get("form", {}).get("site")
            or req.get("query", {}).get("site") or "encar")
    ctx: dict = {"paste": "", "preview": None, "site": site,
                 "reason": "", "target_key": ""}
    if req.get("method") == "POST":
        act = (req.get("form", {}).get("action") or IMPORT_PREVIEW).strip()
        raw_form = req.get("form", {})
        # ★ 붙여넣기가 비면 올린 파일을 쓴다.  둘 다 비면 파서가 말한다
        text = (raw_form.get("paste") or "").strip() \
            or (raw_form.get("upload") or "")
        target_key = (raw_form.get("target_key") or "").strip() or None
        if act == IMPORT_PREVIEW:
            # ★ 미리보기는 저장이 아니다.  _gate 를 지나지 않는다
            check_post(req, csrf)
            fmt, rows, facet = parse_import_text(text, site)
            ctx.update(
                paste=text, site=site, target_key=target_key or "",
                reason=raw_form.get("reason") or "",
                preview=preview_import(conn, rows, fmt=fmt, site=site,
                                       target_key=target_key,
                                       bytes_in=len(text.encode("utf-8")),
                                       facet=facet))
        else:
            # ★ 미리보기 없이 · 사유 없이 저장 못 한다 (STEP 149k · 138)
            form = _gate(conn, account, req, csrf, group=GROUP_OPS)
            fmt, rows, facet = parse_import_text(text, site)
            res = import_listings(
                conn, account, rows, fmt=fmt, site=site,
                target_key=target_key, text=text,
                reason=form.get("reason", ""), at=_now(),
                parse_version=_versions(conn).get("parse_version") or "",
                source_name=form.get("source_name") or None, facet=facet,
                run_id=_run_stamp("import"))
            note = ("원문 있음" if res.site_raw else "원문 없음")
            msg = (f"반입 {res.total}건 — 새 {res.created} · 갱신 "
                   f"{res.updated} · {note} · S4 = 반입(import)")
            if act == IMPORT_COLLECT:
                if plan is None:
                    raise WiringError(
                        "재처리 결정표가 주입되지 않았다 — "
                        "make_app(plan=...) 을 확인한다", step="STEP 132")
                from store.adminops import enqueue_recalc

                # ★ S5 부터다.  S4 는 반입이 대신했다 (STEP 136b ④)
                enqueue_recalc(conn, account, "raw_missing",
                               target_key or "all", "web", plan=plan)
                # ★ 「자동으로 돈다」고 적지 않는다.  큐를 가져가는 실행기가
                #   따로 돈다 — 없으면 큐에만 남는다 (V11-33 · 실측 08-16)
                return redirect(
                    "/admin/import",
                    msg + " · 이어서 수집(S5~)을 큐에 넣었습니다 — "
                    "실행기가 가져가면 시작합니다", flash_key)
            return redirect("/admin/import", msg, flash_key)

    ctx.update(import_state(conn), targets=_first_flag(_target_rows(conn)))
    return page(conn, account, "목록 반입", "admin_import.html", ctx,
                csrf=csrf, root=root, flash_key=flash_key)


def admin_scoring(conn, account, req, root: str = ROOT, csrf: str = "", flash_key: str = "-",
         **_kw):
    """배점 조정.  ★ 합계가 total_points 와 다르면 저장할 수 없다."""
    from store.adminops import preview_scoring
    from web.app import redirect

    pol = _cfg("scoring.json", root)
    if req.get("method") == "POST":
        from contracts import total_of
        from score.adjust import next_components
        from store.admin import apply_config

        form = _gate(conn, account, req, csrf)
        # ★ 규칙은 score 가, 파일 쓰기는 store 가 한다 (STEP 15a).
        #   store 가 score 를 부르면 층이 거꾸로 간다
        new = next_components(pol["components"], form.get("action") or "",
                              form.get("target") or "", form.get("value"))
        # ★ total_points 는 성분 합이다.  직접 받지 않는다 (STEP 128).
        #   한 번에 쓴다 — 따로 쓰면 중간 상태가 「Σ != total」 이라 막힌다
        change = apply_config(conn, account, "scoring.json", "components",
                              new, form.get("reason", ""), root=root,
                              at=_now(), also={"total_points": total_of(new)})
        return redirect("/admin/scoring",
                        f"배점을 바꿨습니다 — {change.key_path} · "
                        f"재판정이 필요합니다", flash_key)

    ver = _versions(conn)
    prev = None
    if req.get("query", {}).get("preview") == "1":
        prev = preview_scoring(conn, pol, pol, ver["calc_version"],
                               int(pol["report"]["top_n"]))
    from score.adjust import _axis_of, _points_of, _skipped

    comps = [{"axis": k, "points": _points_of(v),
              "skipped": _skipped(v), "group": _axis_of(k)}
             for k, v in sorted(pol["components"].items())]
    axes: dict = {}
    for c in comps:
        if not c["skipped"]:
            axes[c["group"]] = axes.get(c["group"], 0) + c["points"]
    axis_rows = [{"axis": k, "points": v} for k, v in sorted(axes.items())]
    total = sum(c["points"] for c in comps if not c["skipped"])
    from report.screens.admin import config_history

    ctx = {"components": comps, "sum": total,
           "total_points": pol["total_points"],
           "gap": total - int(pol["total_points"]), "preview": prev,
           "count": len(comps), "axis_rows": axis_rows,
           "config_history": config_history(conn)}
    return page(conn, account, "배점 조정", "admin_scoring.html", ctx,
                csrf=csrf, root=root, flash_key=flash_key)


def _decide_cards(conn, root: str = ROOT, rows=None) -> list:
    """미분류 항목마다 판단할 재료 (개정 367).

    ★ 조회는 store 가 갖는다 — 화면은 조회를 갖지 않는다 (S15 · V4-22)
    ★ 고를 것을 단추로 준다.  「사람이 봐야 합니다」는 선택지가 아니다
    """
    from store.core import unclassified_cards

    # ★ 한 쪽에 다 내지 않는다.  「120건을 한꺼번에 보라 하면 아무도 안 본다」
    #   ★ 장수는 store 가 config 에서 읽는다 — 여기서 또 정하지 않는다
    # ★ V4-11 · 목록과 같은 자리를 본다 (개정 390).
    #   ★ web 은 parse 를 못 부른다 — report 가 이어 준다 (V4-22)
    from report.screens.admin import blocking_set

    got = unclassified_cards(conn, rows=rows, blocking=blocking_set(conn))
    # ★ 고를 것 셋 — 「쓴다」 「안 쓴다」 「나중에」 (개정 367 ④)
    for one in got:
        one["choices"] = [
            {"usage": "in_use", "label": "쓴다",
             "why": "판정에 씁니다"},
            {"usage": "not_provided", "label": "안 쓴다",
             "why": "사이트가 이 값을 주지 않습니다"},
            {"usage": "deferred", "label": "나중에",
             "why": "지금 정하지 않습니다"},
        ]
    return got


def admin_registry(conn, account, req, root: str = ROOT, csrf: str = "",
                   flash_key: str = "-", **_kw):
    """등록부 분류.  ★ 한 차종 관측으로 「값이 하나뿐」을 판단하지 않는다."""
    from web.app import redirect

    if req.get("method") == "POST":
        from store.admin import classify_field

        form = _gate(conn, account, req, csrf)
        # ★ 실제로 저장한다.  「저장했습니다」만 내면 사람이 바뀐 줄 안다 (V11-33)
        # ★★ 08-28 (#83) — ★ `use_when` 을 ★ 안 넘기고 있었다.
        #   ★ `deferred` 는 ★ `USAGE_REQUIRES` 가 ★ 그것을 요구하는데
        #     ★ 폼에도 없고 ★ 여기서도 안 넘겨 ★ 「나중에」 단추가
        #     ★ 무엇을 채워도 ★ 400 이었다 (store/admin.py:508)
        classify_field(conn, account, form.get("endpoint", ""),
                       form.get("json_path", ""), form.get("usage", ""),
                       form.get("reason", ""),
                       core_column=form.get("core_column") or None,
                       unblock_condition=form.get("unblock_condition") or None,
                       use_when=form.get("use_when") or None,
                       root=root, at=_now())
        return redirect("/admin/registry", "분류를 저장했습니다", flash_key)

    q = req.get("query", {})
    usage = q.get("usage") or "unclassified"
    from store.adminops import registry_counts, registry_rows

    rows = registry_rows(conn, usage, _rows_per_page(root))
    # ★ 미분류를 한 번만 센다.  아래 둘이 나눠 쓴다 (V11-34 — 한 쪽 20쿼리)
    from store.core import classify_unclassified as _cls, has_unclassified

    _seen = _cls(conn) if has_unclassified(conn) else []
    counts = registry_counts(conn)
    from store.admin import USAGE_VALUES

    # ★ 손으로 적게 하면 없는 값을 쓴다 — 화면 안내가 not_used 였고
    #   그대로 하면 400 이었다 (실측 08-15).  실제 값만 고르게 한다
    return page(conn, account, "등록부", "admin_registry.html",
                {"rows": rows, "counts": counts, "usage": usage,
                 "count": len(rows),
                 # ★ 「349건 미분류」라고만 내면 아무도 안 본다 (개정 341).
                 #   원인별로 갈라 「사람이 봐야 할 것」만 남긴다
                 "split": _unclassified_split(conn, root, _seen),
                 # ★ 판단할 재료 다섯 (개정 367 · V4-28).
                 #   마스터 지적 — 「이걸 보고 내가 무엇을 하라는 말이지?」
                 #   ★ 판정을 막는 것만 먼저 낸다 (V4-29)
                 "cards": (_decide_cards(conn, root, _seen)
                           if usage == "unclassified" else []),
                 "usages": [u for u in sorted(USAGE_VALUES)
                            if u != "unclassified"]},
                csrf=csrf, root=root, flash_key=flash_key)


def admin_query(conn, account, req, root: str = ROOT, csrf: str = "", flash_key: str = "-",
         **_kw):
    """조회 쿼리.  ★ 쓰기는 바이트코드로 막는다 (V10-04)."""
    from store.adminops import run_query

    result = None
    if req.get("method") == "POST":
        from web.app import check_post

        check_post(req, csrf)
        result = run_query(conn, account, req.get("form", {}).get("sql", ""))
    from report.screens.admin import (
        QUERY_EXAMPLES, db_tables, query_history,
    )

    return page(conn, account, "쿼리", "admin_query.html",
                {"r": result, "db_tables": db_tables(conn),
                 "query_examples": list(QUERY_EXAMPLES),
                 "query_history": query_history(conn)},
                csrf=csrf, root=root, flash_key=flash_key)


def admin_requests(conn, account, req, root: str = ROOT, csrf: str = "",
                   flash_key: str = "-", **_kw):
    from store.adminops import (
        DEV_ORIGINS, DEV_STATUSES, create_dev_request, dev_request_rows,
        update_dev_status, write_dev_requests,
    )
    from web.app import check_post, redirect

    if req.get("method") == "POST":
        check_post(req, csrf)
        form = req.get("form", {})
        act = form.get("action") or "create"
        if act == "status":
            # ★ 삭제하지 않는다.  상태 전이로만 관리한다 (STEP 137)
            status = form.get("status") or ""
            if status in ("applied", "not_applied", "misapplied") \
                    and not (form.get("direction") or "").strip():
                raise ValidationError(
                    f"{status} 는 사유(direction)가 필요하다", step="STEP 137")
            if status == "applied" and not (form.get("step_ref") or "").strip():
                raise ValidationError(
                    "applied 는 step_ref 가 필요하다 — "
                    "어느 STEP 에 반영됐는가", step="STEP 137")
            update_dev_status(conn, account, form.get("request_id") or "",
                              status, _now(),
                              direction=form.get("direction") or None,
                              step_ref=form.get("step_ref") or None)
            return redirect("/admin/requests", f"상태를 {status} 로 바꿨습니다",
                            flash_key)
        if act == "export":
            # ★ 내보낸 요청은 exported_at 을 갖는다 (STEP 137 검산).
            #   파일 쓰기는 store 가 한다 — web 이 쓰면 층이 거꾸로 간다
            path = write_dev_requests(conn, root, at=_now())
            return redirect("/admin/requests",
                            f"{path} 로 내보냈습니다", flash_key)
        # ★ 출처는 화면이다 (STEP 137).  「web」은 허용 목록에 없다
        create_dev_request(conn, account, form.get("title", ""),
                           form.get("body", ""),
                           form.get("origin") or "screen", None)
        return redirect("/admin/requests", "개발 요청을 남겼습니다", flash_key)

    rows = dev_request_rows(conn, _rows_per_page(root))
    return page(conn, account, "개발 요청", "admin_requests.html",
                {"rows": rows, "count": len(rows),
                 "statuses": list(DEV_STATUSES),
                 "origins": list(DEV_ORIGINS)},
                csrf=csrf, root=root, flash_key=flash_key)



# 관리 화면마다 필요한 공용 자료.  ★ 화면이 「무엇이 언제 왜」를 낸다 (G-1)
ADMIN_EXTRA = {
    "admin_config.html": ("config_history",),
    "admin_query.html": ("db_tables", "query_history"),
    "admin_users.html": ("account_activity",),
    "admin_scoring.html": ("config_history",),
    "admin_targets.html": ("target_rows",),
    "admin_api.html": ("api_snapshots",),
    "admin_tools.html": (),
}


def _admin_extra(conn, template: str, root: str) -> dict:
    from report.screens import admin as A

    out: dict = {}
    for name in ADMIN_EXTRA.get(template, ()):
        fn = getattr(A, name)
        out[name] = fn(conn, root=root) if name == "target_rows" else fn(conn)
    return out


# 웹에서 고칠 수 있는 config 파일 (STEP 127).
# ★ 목록을 코드에 나열하지 않는다 — config/ 를 훑고, 못 고칠 것만 뺀다
CONFIG_LOCKED = ("field_usage.suggested.json",)


def _config_files(root: str) -> list:
    import os as _o

    return sorted(f for f in _o.listdir(_o.path.join(root, "config"))
                  if f.endswith(".json") and f not in CONFIG_LOCKED)


def _config_rows(root: str, file: str) -> list:
    """평탄화한 키 목록.  ★ 값을 바꾸려면 무엇이 있는지부터 보여야 한다."""
    import json as _j
    import os as _o

    path = _o.path.join(root, "config", file)
    if not _o.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as f:
        blob = _j.load(f)

    out: list = []

    def walk(node, prefix: str) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                if k.startswith("_"):
                    continue
                walk(v, f"{prefix}.{k}" if prefix else k)
        elif isinstance(node, (int, float, str, bool)) or node is None:
            out.append({"key": prefix, "value": node,
                        "kind": type(node).__name__})
        else:
            # 목록·중첩은 화면에서 고치지 않는다.  ★ 보여만 준다
            out.append({"key": prefix,
                        "value": _j.dumps(node, ensure_ascii=False)[:80],
                        "kind": "복합 — CLI 로 고칩니다"})

    walk(blob, "")
    return out


def admin_config(conn, account, req, root: str = ROOT, csrf: str = "",
                 flash_key: str = "-", **_kw):
    """설정 변경 (STEP 127).

    ★ 사유 없이 바꾸지 않는다.  무엇을 왜 바꿨는지가 남아야 되돌릴 수 있다
    ★ 실행 중에는 잠근다 — 도는 중에 규칙이 바뀌면 어느 규칙으로 나온
      결과인지 알 수 없다 (apply_config 가 막는다)
    """
    from report.screens.admin import config_history
    from store.admin import apply_config
    from web.app import redirect

    files = _config_files(root)
    if req.get("method") == "POST":
        # ★ 되돌리기는 미리보기를 요구하지 않는다.  이미 있던 값으로
        #   돌아가는 것이라 미리 볼 것이 없다 — 요구하면 화면에서 못 누른다
        #   (실측 08-15).  사유와 잠금은 그대로 본다
        if (req.get("form", {}).get("action") or "") == "revert":
            form = _reason_gate(conn, account, req, csrf)
        else:
            form = _gate(conn, account, req, csrf)
        if (form.get("action") or "") == "revert":
            # ★ 되돌린 것도 이력에 남는다.  원래 행을 지우지 않는다 (STEP 138a)
            from store.admin import revert_config

            change = revert_config(conn, account,
                                   form.get("change_id") or "",
                                   root=root, at=_now())
            return redirect("/admin",
                            f"{change.key_path} 를 되돌렸습니다", flash_key)
        file = form.get("file") or ""
        key = form.get("key_path") or ""
        raw = form.get("value")
        if file not in files:
            raise ValidationError(f"고칠 수 없는 파일: {file}",
                                  step="STEP 127")
        apply_config(conn, account, file, key, _typed(raw),
                     form.get("reason", ""), root=root, at=_now())
        return redirect("/admin/config",
                        f"{file} · {key} 를 바꿨습니다", flash_key)

    file = (req.get("query", {}).get("file") or "scoring.json")
    if file not in files:
        file = files[0] if files else ""
    return page(conn, account, "설정", "admin_config.html",
                {"files": files, "file": file,
                 "rows": _config_rows(root, file),
                 "config_history": config_history(conn)},
                csrf=csrf, root=root, flash_key=flash_key)


def _typed(raw):
    """입력 문자열을 원래 형으로 되돌린다.

    ★ 200 을 "200" 으로 저장하면 다음 판정이 조용히 달라진다
    """
    import json as _j

    if raw is None:
        return None
    text = str(raw).strip()
    try:
        return _j.loads(text)
    except ValueError:
        return text


def admin_api(conn, account, req, root: str = ROOT, csrf: str = "",
              flash_key: str = "-", fetch=None, **_kw):
    """API 조회 · 저장 (STEP 134).

    ★ 응답을 가공하지 않는다.  원문 그대로 저장한다
    ★ raw_response 에 섞지 않는다 — 이건 「탐색」이지 수집이 아니다
    fetch   URL -> (code, content_type, body).  ★ 주입받는다 —
            web 계층이 네트워크를 직접 부르면 층이 거꾸로 간다 (STEP 15a)
    """
    from report.screens.admin import api_snapshots
    from store.adminops import (
        get_api_snapshot, path_table, save_api_snapshot,
    )
    from web.app import redirect

    if req.get("method") == "POST":
        form = _gate(conn, account, req, csrf)
        url = (form.get("url") or "").strip()
        if not url.startswith("https://"):
            raise ValidationError("https:// 로 시작하는 URL 이어야 한다",
                                  step="STEP 134")
        if fetch is None:
            raise WiringError(
                "조회기가 주입되지 않았다 — make_app(fetch=...) 을 확인한다",
                step="STEP 134")
        code, ctype, body = fetch(url)
        save_api_snapshot(conn, account, url, code, ctype, body,
                          form.get("note"), at=_now())
        return redirect("/admin/api", f"{code} · {len(body or '')}바이트 저장",
                        flash_key)

    snaps = api_snapshots(conn)
    sid = req.get("query", {}).get("snapshot")
    row, paths = None, []
    if sid and sid.isdigit():
        got = get_api_snapshot(conn, int(sid))
        if got:
            row = got
            paths = path_table(got["full_body"])
    return page(conn, account, "API 조회", "admin_api.html",
                {"api_snapshots": snaps, "snapshot": row, "paths": paths},
                csrf=csrf, root=root, flash_key=flash_key)


# 차종 등록 상태 (STEP 130).
# ★ 자동 확정하지 않는다.  사람이 확인 버튼을 눌러야 active 가 된다
TARGET_PENDING = "pending_review"
TARGET_ACTIVE = "active"


def _site_query(origin: str, maker: str, model_group: str) -> str:
    """고른 값으로 엔카 검색 조건을 조립한다 (STEP 149r).

    ★ 엔카 쿼리 문법을 사람이 알아야 하는 것이 지적 ⑧ 이었다.
      facet 으로 확인한 값이 있으면 그것이 우선이다 — 여기 것은 초안이다
    """
    if not (maker and model_group):
        return ""
    kind = "Y" if origin == "Y" else "N"
    return (f"(And.Hidden.N._.CarType.{kind}._."
            f"(C.Manufacturer.{maker}._.ModelGroup.{model_group}.))")


def admin_targets(conn, account, req, root: str = ROOT, csrf: str = "",
                  flash_key: str = "-", **_kw):
    """차종 추가 (STEP 130).

    ★ facet 확인 없이 targets.json 에 쓰지 않는다.
      사이트가 열거값을 준다 — 사람이 적으면 표기가 어긋난다 (STEP 42)
    ★ 배기량 범위는 「확인 필요」로 남긴다.  facet 이 배기량을 주지 않는다
    """
    from report.screens.admin import target_choices, target_rows
    from store.admin import add_config_key, apply_config
    from web.app import redirect

    if req.get("method") == "POST":
        form = _gate(conn, account, req, csrf)
        act = form.get("action") or "add"
        # ★ 고른 값에서 만들어 준다.  사람이 적었으면 그것을 쓴다 (STEP 149r)
        from report.screens.admin import make_target_key

        picked_group = (form.get("model_group") or "").strip()
        picked_fuel = (form.get("fuel") or "").strip()
        key = ((form.get("target_key") or "").strip()
               or make_target_key(picked_group, picked_fuel)).upper()
        if not key or not key.replace("_", "").isalnum():
            raise ValidationError(
                "차종 키를 만들지 못했다 — 모델군이 한글뿐이면 로마자가 없다. "
                f"「차종 키」 칸에 직접 적어 주십시오 (예 KOLEOS_HEV): {key}",
                step="STEP 130 · 149r")
        blob = _cfg("targets.json", root)
        if act == "confirm":
            if key not in blob:
                raise ValidationError(f"없는 차종: {key}", step="STEP 130")
            spec = dict(blob[key])
            if not spec.get("displacement_range"):
                raise ValidationError(
                    "배기량 범위를 확인해야 확정할 수 있다 — "
                    "시험 수집 분포에서 경계를 정한다", step="STEP 130")
            spec["status"] = TARGET_ACTIVE
            apply_config(conn, account, "targets.json", key, spec,
                         form.get("reason", ""), root=root, at=_now())
            return redirect("/admin/targets", f"{key} 를 확정했습니다",
                            flash_key)
        if key in blob:
            raise ValidationError(f"이미 있는 차종: {key}", step="STEP 130")
        # ★ status='pending_review' 로 저장한다.  자동 확정하지 않는다
        origin = form.get("origin_type") or ""
        if origin not in ("Y", "N"):
            raise ValidationError(
                "국산(Y)·수입(N) 중 하나를 골라야 한다 — "
                "빠뜨리면 facet 조건이 안 맞아 0건이 나온다",
                step="STEP 130")
        maker = (form.get("maker") or "").strip()
        spec = {
            "label": (form.get("label")
                      or (f"{maker} {picked_group}".strip() if picked_group
                          else key)),
            # ★ 국산 CarType.Y · 수입 CarType.N (STEP 130)
            "origin_type": origin,
            "collect_group": form.get("collect_group") or picked_group or key,
            # ★ 비어 있으면 고른 값으로 조립한다.  그래도 못 만들면 아래에서 막는다
            "site_query": (form.get("site_query")
                           or _site_query(origin, maker, picked_group)),
            "status": TARGET_PENDING,
        }
        if not spec["site_query"]:
            raise ValidationError(
                "site_query 가 없다 — facet 으로 확인한 뒤 넣는다",
                step="STEP 130")
        # ★ 새 키다.  apply_config 는 없는 키를 만들지 않는다 (STEP 127)
        add_config_key(conn, account, "targets.json", key, spec,
                       form.get("reason", ""), root=root, at=_now())
        return redirect("/admin/targets",
                        f"{key} 를 확인 대기로 넣었습니다 — "
                        f"시험 수집 뒤 확정합니다", flash_key)

    return page(conn, account, "차종", "admin_targets.html",
                {"target_rows": target_rows(conn, root=root),
                 # ★ 고르는 칸은 고를 수 있게 (STEP 149r)
                 "choices": target_choices(conn)},
                csrf=csrf, root=root, flash_key=flash_key)


# 관리 도구 (STEP 135).
# ★ 도구는 읽기 또는 config 변경만 한다.  데이터를 고치지 않는다
# 금지   도구가 core_* 를 직접 UPDATE 하는 것
TOOLS = (
    {"key": "validate", "label": "검증 실행",
     "what": "V1~V11 을 지금 돌린다", "step": "6장"},
    {"key": "grade_dist", "label": "등급 분포",
     "what": "현재 배점의 등급 분포", "step": "V5-05"},
    {"key": "mapping", "label": "매핑 대조",
     "what": "원문 값 ↔ CORE 값 일치율", "step": "V4-01"},
    {"key": "paths", "label": "경로 전수",
     "what": "엔드포인트별 경로 · 값 표본", "step": "2장"},
    {"key": "threshold", "label": "임계 제안",
     "what": "분포 분위수 → warnings.json 후보", "step": "STEP 82d"},
)


def admin_tools(conn, account, req, root: str = ROOT, csrf: str = "",
                flash_key: str = "-", **_kw):
    """관리 도구 (STEP 135).

    ★ 도구 결과는 제안이다.  적용은 별도 버튼이다 —
      「계수를 산출했다」와 「계수를 바꿨다」는 다르다
    """
    from store.tools import run_tool

    result, ran = None, None
    if req.get("method") == "POST":
        form = _gate(conn, account, req, csrf)
        ran = form.get("tool") or ""
        result = run_tool(conn, account, ran, root=root)
    return page(conn, account, "도구", "admin_tools.html",
                {"tools": list(TOOLS), "result": result, "ran": ran},
                csrf=csrf, root=root, flash_key=flash_key)


def join(conn, account, req, root: str = ROOT, csrf: str = "",
         flash_key: str = "-", **_kw):
    """★ 승인제가 기본이다.  아무나 계정을 만들면 요청이 늘어난다."""
    from store.admin import ROLE_PENDING, create_account
    from web.app import check_post, redirect

    policy = _cfg("web.json", root)["signup_policy"]
    if req.get("method") == "POST":
        check_post(req, csrf)
        if policy == "closed":
            return redirect("/join", "지금은 가입을 받지 않습니다", flash_key)
        form = req.get("form", {})
        secret = form.get("secret") or ""
        # ★ 본인이 정한다.  임시 비밀번호를 만들고 버리면
        #   사용자가 로그인할 길이 없다 (실측 08-15 · D-1)
        if secret != (form.get("secret2") or ""):
            raise ValidationError("비밀번호가 확인란과 다릅니다",
                                  step="STEP 126")
        role = ROLE_USER if policy == "open" else ROLE_PENDING
        create_account(conn, form.get("name", ""), role, _now(),
                       secret=secret, display_name=form.get("display_name"),
                       email=form.get("email"))
        msg = ("계정을 만들었습니다. 로그인하십시오" if policy == "open"
               else "신청했습니다. 승인되면 알려 드립니다")
        return redirect("/join", msg, flash_key)
    return page(conn, account, "계정 만들기", "join.html",
                {"policy": policy, "closed": policy == "closed",
                 "approval": policy == "approval"},
                csrf=csrf, flash_key=flash_key, root=root)


def password(conn, account, req, root: str = ROOT, csrf: str = "",
             flash_key: str = "-", **_kw):
    """비밀번호 변경.  ★ 임시 비밀번호로는 다른 화면이 열리지 않는다."""
    from store.admin import change_secret
    from web.app import check_post, redirect

    if req.get("method") == "POST":
        check_post(req, csrf)
        change_secret(conn, account, req.get("form", {}).get("secret", ""))
        return redirect("/", "비밀번호를 바꿨습니다", flash_key)
    return page(conn, account, "비밀번호 변경", "password.html",
                {"must": getattr(account, "must_change_secret", False)},
                csrf=csrf, flash_key=flash_key, root=root)


def admin_users(conn, account, req, root: str = ROOT, csrf: str = "",
                flash_key: str = "-", **_kw):
    """★ 관리자를 0명으로 만들 수 없다.  중지는 삭제가 아니다."""
    from store.admin import (
        ROLE_PENDING, account_rows, admin_count, set_disabled, set_role,
    )
    from web.app import redirect

    if req.get("method") == "POST":
        # ★ 사유 없이 역할을 바꾸거나 계정을 중지하지 않는다 (V11-25 · D-2)
        form = _reason_gate(conn, account, req, csrf)
        aid = int(form.get("account_id") or 0)
        act = form.get("action")
        if act == "create":
            # ★ 관리자가 계정을 만든다 (STEP 126).  임시 비밀번호를 한 번만 낸다 —
            #   저장하지 않는다.  첫 로그인 때 본인이 바꾼다
            from store.admin import create_account

            _aid, temp = create_account(
                conn, form.get("name", ""), form.get("role") or ROLE_USER,
                _now(), secret=form.get("secret") or None,
                display_name=form.get("display_name"),
                email=form.get("email"))
            msg = (f"만들었습니다 — 임시 비밀번호 {temp} "
                   f"(이 화면을 벗어나면 다시 볼 수 없습니다)"
                   if not form.get("secret")
                   else "만들었습니다. 정한 비밀번호로 로그인합니다")
            return redirect("/admin/users", msg, flash_key)
        if act == "approve":
            set_role(conn, aid, ROLE_USER, _now())
            msg = "승인했습니다"
        elif act == "disable":
            set_disabled(conn, aid, True, _now())
            msg = "중지했습니다 — 관심 목록과 이력은 남습니다"
        elif act == "enable":
            set_disabled(conn, aid, False, _now())
            msg = "되살렸습니다"
        elif act == "unlock":
            # ★ 마스터 지적 — 「PC 가 없어 CLI 로 못 푼다」.
            #   화면에서 풀 수 있어야 한다 (60-admin/a-auth)
            from store.admin import unlock_account

            who = (form.get("display_name") or "").strip()
            unlock_account(conn, account, who, form.get("reason", ""), _now())
            msg = f"{who} 의 잠금을 풀었습니다 — 시도 기록은 남습니다"
        else:
            set_role(conn, aid, form.get("role") or ROLE_USER, _now())
            msg = "역할을 바꿨습니다"
        return redirect("/admin/users", msg, flash_key)

    rows = account_rows(conn)
    return page(conn, account, "사용자", "admin_users.html",
                {"rows": rows, "count": len(rows),
                 "pending": [r for r in rows if r["role"] == ROLE_PENDING],
                 "admins": admin_count(conn),
                 "policy": _cfg("web.json", root)["signup_policy"],
                 "account_activity": _account_activity(conn)},
                csrf=csrf, flash_key=flash_key, root=root)


def _account_activity(conn) -> list:
    from report.screens.admin import account_activity

    return account_activity(conn)


def reports(conn, account, req, root: str = ROOT, csrf: str = "",
            flash_key: str = "-", **_kw) -> tuple:
    """리포트를 화면에서 읽는다 (개정 357 · V11-122).

    마스터 확정 — 「목록을 보고 클릭하면 내용을 볼 수 있게 팝업 박스로.
    다운로드 누를 때 다운로드」
    ★ 열자마자 내려받지 않는다.  팝업은 JS 없이 닫힌다 — 별도 경로다
    """
    from report.screens.build import view_reports

    want = (req.get("query", {}).get("open") or "").strip() or None
    rv = view_reports(account, open_name=want, root=root)
    return page(conn, account, "리포트", "reports.html", {"rep": rv},
                root=root, csrf=csrf, flash_key=flash_key)


def report_download(conn, account, req, path_vars: dict | None = None,
                    root: str = ROOT, **_kw) -> tuple:
    """누를 때만 내려받는다 (개정 357).

    ★ 목록에 있는 것만 준다.  임의 경로를 받으면 파일이 새 나간다
    """
    from report.exports.export import CONTENT_TYPE, ENCODING, OUTPUT_DIR
    from web.context import HTTP_OK
    from report.screens.build import view_reports

    del conn, req
    name = (path_vars or {}).get("name", "")
    known = {f.name: f for f in view_reports(account, root=root).files}
    one = known.get(name)
    if one is None:
        raise ValidationError(f"없는 리포트입니다: {name[:60]}", step="STEP 91b")
    with open(os.path.join(root, OUTPUT_DIR, one.name), "rb") as f:
        body = f.read()
    return HTTP_OK, {
        "Content-Type": f"{CONTENT_TYPE[one.ext]}; charset={ENCODING}",
        # ★ 파일 이름에 따옴표·줄바꿈이 못 들어간다 — 이름 규칙이 막는다
        "Content-Disposition": f'attachment; filename="{one.name}"',
    }, body


HANDLERS = {
    "view_listings": listings,
    "view_sold": sold,
    "view_why": why,
    "view_detail": detail,
    "view_notready": notready,
    "view_dashboard": dashboard,
    "view_admin": admin_home,
    "view_admin_audit": admin_audit,
    "view_reports": reports,
    "view_report_download": report_download,
    "view_admin_docs": admin_docs,
    "view_recommend": recommend,
    "view_compare": compare,
    "view_track": track,
    "view_market": market,
    "view_dealers": dealers,
    "view_watch": watch,
    "view_login": login,
    "view_join": join,
    "view_password": password,
    "view_admin_users": admin_users,
    "view_logout": logout,
    "watch_add": watch_add_post,
    "watch_update": watch_update_post,
    "view_admin_run": admin_run,
    "view_admin_import": admin_import,
    "view_admin_collect": admin_collect,
    "view_admin_status": admin_status,
    "view_admin_dict": admin_dict,
    "view_admin_scoring": admin_scoring,
    "view_admin_registry": admin_registry,
    "view_admin_query": admin_query,
    "view_admin_requests": admin_requests,
    "view_admin_targets": admin_targets,
    "view_admin_config": admin_config,
    "view_admin_api": admin_api,
    "view_admin_tools": admin_tools,
}

