# -*- coding: utf-8 -*-
"""
car_monitor / web / app.py
------------------------------------------------------------------
로컬 대시보드.  (지시서 7장)

    /           오늘 요약 · 차종별 현황 · 최근 이벤트
    /listings   매물 목록 (필터 · 정렬)
    /watch      관심매물 + 가격 추이
    /dealers    딜러 4분면
    /market     시세 추이

실행:
    python web/app.py
    → http://127.0.0.1:5001
"""
from __future__ import annotations

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from flask import Flask, jsonify, redirect, render_template, request  # noqa: E402

import collect     # noqa: E402
import config      # noqa: E402
import db          # noqa: E402
import photo       # noqa: E402
import runner      # noqa: E402
import store       # noqa: E402
from analyzer import stats                           # noqa: E402

app = Flask(__name__, template_folder=str(_HERE / "templates"))
app.config["JSON_AS_ASCII"] = False


# ──────────────────────────────────────────────────────────────
# 템플릿 필터
# ──────────────────────────────────────────────────────────────
@app.template_filter("manwon")
def f_manwon(v):
    """32900000 → '3,290'"""
    if v is None:
        return "—"
    try:
        return f"{int(v) // 10_000:,}"
    except (TypeError, ValueError):
        return "—"


@app.template_filter("km")
def f_km(v):
    if v is None:
        return "—"
    try:
        return f"{int(v):,}"
    except (TypeError, ValueError):
        return "—"


@app.template_filter("pct")
def f_pct(v, digits=1):
    if v is None:
        return "—"
    try:
        return f"{float(v):+.{digits}f}%"
    except (TypeError, ValueError):
        return "—"


@app.template_filter("ym")
def f_ym(v):
    """'2022-07' → '22/07'"""
    if not v:
        return "—"
    s = str(v)
    return f"{s[2:4]}/{s[5:7]}" if len(s) >= 7 else s


# ──────────────────────────────────────────────────────────────
# 공통
# ──────────────────────────────────────────────────────────────
def latest_snapshot(conn) -> str | None:
    r = conn.execute(
        "SELECT MAX(snapshot_date) d FROM price_history").fetchone()
    return r["d"] if r and r["d"] else None


@app.errorhandler(Exception)
def _on_error(e):
    """
    화면이 500 으로 죽지 않게 한다.

    ★ 수집 중에는 DB 가 잠길 수 있다.
      그때마다 흰 화면이 뜨면 진행 상황을 볼 수 없다.
      무슨 일인지 알려주고 새로고침을 안내한다.
    """
    import sqlite3 as _sq
    import traceback
    if isinstance(e, _sq.OperationalError) and "locked" in str(e):
        return (
            "<div style='font-family:sans-serif;padding:40px;"
            "max-width:520px;margin:60px auto;line-height:1.7'>"
            "<h3>잠시 기다려 주십시오</h3>"
            "<p>수집이 데이터를 쓰는 중입니다.<br>"
            "몇 초 뒤 자동으로 다시 열립니다.</p>"
            "<p style='color:#888;font-size:13px'>"
            "수집을 멈출 필요는 없습니다.</p>"
            "<meta http-equiv='refresh' content='4'></div>"), 503

    tb = traceback.format_exc()
    return (
        "<div style='font-family:sans-serif;padding:40px;line-height:1.7'>"
        f"<h3>화면 오류</h3><p><code>{e!r}</code></p>"
        f"<pre style='font-size:12px;color:#666;white-space:pre-wrap'>"
        f"{tb[-1500:]}</pre></div>"), 500


def schema_ready(conn) -> bool:
    """
    스키마가 있는지 확인한다.
    ★ init 없이 서버를 켜면 SQLite 가 빈 파일을 만들고 500 이 난다.
      500 대신 '무엇을 해야 하는지' 를 보여준다.
    """
    r = conn.execute(
        "SELECT COUNT(*) c FROM sqlite_master "
        " WHERE type='table' AND name IN "
        " ('listings','collection_log','market_daily')").fetchone()
    return r["c"] >= 3


def not_ready():
    return render_template("notready.html",
                           db_path=str(config.DB_PATH),
                           reload_sec=None, now=datetime.now()
                           .strftime("%Y-%m-%d %H:%M")), 200


def photo_url(it: dict, base: str | None) -> str | None:
    return photo.build(base, it.get("photo_url"))


def photo_alts(it: dict) -> str:
    """
    브라우저 폴백용 후보 목록.
    서버가 고른 주소가 틀려도 브라우저가 순서대로 다시 시도한다.
    """
    import json as _j
    return _j.dumps(photo.candidates_for(it.get("photo_url")),
                    ensure_ascii=False)


app.jinja_env.globals["photo_url"] = photo_url
app.jinja_env.globals["photo_alts"] = photo_alts


def nav_context(conn) -> dict:
    """★ 빌드 번호를 모든 화면에 넣는다.
      '고쳤다는데 같은 오류가 난다'는 대개 이전 버전을 쓰는 것이다."""
    run = conn.execute(
        "SELECT * FROM collection_log ORDER BY run_date DESC LIMIT 1"
    ).fetchone()
    base = config.PHOTO_BASE_OVERRIDE or photo.get_base(conn)
    return {
        "build": config.BUILD,
        "photo_base": base,
        "targets": config.active_targets(),
        "last_run": dict(run) if run else None,
        "reload_sec": config.WEB["auto_reload_sec"],
        "now": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


# ──────────────────────────────────────────────────────────────
# 1. 대시보드
# ──────────────────────────────────────────────────────────────
@app.route("/")
def dashboard():
    with db.connect() as conn:
        if not schema_ready(conn):
            return not_ready()
        ctx = nav_context(conn)
        snap = latest_snapshot(conn)
        ctx["snapshot"] = snap

        if snap is None:
            ctx["empty"] = True
            return render_template("dashboard.html", **ctx)

        # 오늘 이벤트 요약
        ev = conn.execute("""
            SELECT event_type, COUNT(*) c FROM events
             WHERE event_date = ? GROUP BY event_type
        """, (snap,)).fetchall()
        ctx["events"] = {r["event_type"]: r["c"] for r in ev}

        # ★ 조건 충족 현황 (v2 8.1) — 최상단
        ctx["cond"] = [dict(r) for r in conn.execute("""
            SELECT * FROM condition_summary WHERE snapshot_date=?
        """, (snap,)).fetchall()]
        for c in ctx["cond"]:
            c["label"] = config.TARGETS.get(c["target_key"], {}).get(
                "label", c["target_key"])
            try:
                c["top_fail"] = json.loads(c["top_fail_json"] or "[]")
            except (ValueError, TypeError):
                c["top_fail"] = []
            c["drought"] = stats.grade_a_drought(conn, c["target_key"])

        # ★ 조건 완화 시뮬레이션 (v2 5.3)
        ctx["relax"] = {}
        for c in ctx["cond"]:
            rows = [dict(r) for r in conn.execute("""
                SELECT * FROM relax_simulation
                 WHERE target_key=? AND snapshot_date=?
                 ORDER BY gain DESC LIMIT 5
            """, (c["target_key"], snap)).fetchall()]
            for r in rows:
                r["label"] = config.RELAX_LABELS.get(
                    r["relax_axis"], r["relax_axis"])
            if rows:
                ctx["relax"][c["target_key"]] = rows

        # 축별 미달 합계
        # 사진 URL 확보 여부 — 안 나오면 CDN 형식이 틀린 것이다
        ph = conn.execute("""
            SELECT COUNT(*) t, SUM(CASE WHEN photo_url IS NOT NULL
                   THEN 1 ELSE 0 END) p FROM listings WHERE status='active'
        """).fetchone()
        ctx["photo_stat"] = {"total": ph["t"] or 0, "with": ph["p"] or 0}

        pa = conn.execute("""
            SELECT COUNT(*) c FROM listings
             WHERE status='active' AND price_anomaly=1
        """).fetchone()["c"]
        ctx["price_anomaly_cnt"] = pa
        ci = conn.execute("""
            SELECT
              SUM(CASE WHEN color_int IS NULL THEN 1 ELSE 0 END) unknown,
              SUM(CASE WHEN color_int_group='nonpref' THEN 1 ELSE 0 END) fail,
              SUM(CASE WHEN color_int_group='pref' THEN 1 ELSE 0 END) ok
              FROM listings WHERE status='active'
        """).fetchone()
        ctx["color_int_stats"] = dict(ci) if ci else {}
        cs = conn.execute("""
            SELECT
              SUM(CASE WHEN encar_cert='certified' THEN 1 ELSE 0 END) certified,
              SUM(CASE WHEN encar_cert='none' THEN 1 ELSE 0 END) none,
              SUM(CASE WHEN encar_cert='unknown' OR encar_cert IS NULL
                       THEN 1 ELSE 0 END) unknown
              FROM listings WHERE status='active'
        """).fetchone()
        ctx["cert_stat"] = dict(cs) if cs else {}
        gh = conn.execute("""
            SELECT
              SUM(CASE WHEN status='active' THEN 1 ELSE 0 END) active,
              SUM(CASE WHEN status='gone'
                   AND DATE(gone_at)=DATE('now') THEN 1 ELSE 0 END) today,
              SUM(CASE WHEN status='gone'
                   AND IFNULL(gone_reason,'') LIKE '%상세%'
                   AND DATE(gone_at)=DATE('now')
                   THEN 1 ELSE 0 END) by_detail
              FROM listings WHERE site='encar'
        """).fetchone()
        ctx["gone_stat"] = dict(gh) if gh else {}
        dp = conn.execute("""
            SELECT COUNT(*) t,
                   SUM(CASE WHEN insp_fetched_at IS NOT NULL
                            OR record_fetched_at IS NOT NULL
                       THEN 1 ELSE 0 END) d
              FROM listings WHERE status='active'
        """).fetchone()
        ctx["detail_progress"] = (
            {"total": dp["t"] or 0, "done": dp["d"] or 0,
             "pct": round((dp["d"] or 0) / (dp["t"] or 1) * 100)}
            if dp else {})
        ctx["parse_alerts"] = [dict(r) for r in conn.execute("""
            SELECT field, ratio, level, cause FROM parse_health
             WHERE check_date = (SELECT MAX(check_date) FROM parse_health)
               AND level <> 'OK'
             ORDER BY CASE level WHEN 'CRITICAL' THEN 0 ELSE 1 END,
                      ratio DESC LIMIT 5
        """).fetchall()]
        ctx["grade_badge"] = config.GRADE_BADGE
        ctx["grade_label"] = config.GRADE_LABEL
        ctx["verify_stat"] = dict(conn.execute("""
            SELECT COUNT(*) t,
                   SUM(CASE WHEN verified=1 THEN 1 ELSE 0 END) v,
                   SUM(CASE WHEN record_fetched_at IS NOT NULL
                            THEN 1 ELSE 0 END) r,
                   SUM(CASE WHEN record_open=0 THEN 1 ELSE 0 END) rc
              FROM listings WHERE status='active'
        """).fetchone())
        ctx["finals"] = [dict(r) for r in conn.execute("""
            SELECT c.slot_no, c.new_car_key, c.selected_reason,
                   l.listing_id, l.target_key, l.year_month,
                   l.current_price, l.monthly_total, l.recommend_rank
              FROM comparison c
              LEFT JOIN listings l ON l.listing_id = c.listing_id
             WHERE c.is_final = 1 ORDER BY c.slot_no
        """).fetchall()]
        ctx["cmp_count"] = conn.execute(
            "SELECT COUNT(*) c FROM comparison").fetchone()["c"]
        ctx["lease_cnt"] = conn.execute("""
            SELECT COUNT(*) c FROM listings
             WHERE status='active' AND is_lease=1
        """).fetchone()["c"]

        ctx["fails"] = [dict(r) for r in conn.execute("""
            SELECT bucket, SUM(count) c FROM condition_stats
             WHERE axis='fail' AND snapshot_date=?
             GROUP BY bucket ORDER BY c DESC LIMIT 10
        """, (snap,)).fetchall()]
        for f in ctx["fails"]:
            f["label"] = config.RELAX_LABELS.get(f["bucket"], f["bucket"])

        ctx["relax_labels"] = config.RELAX_LABELS

        # 차종별 현황 (7일 전 대비)
        prev = (datetime.strptime(snap, "%Y-%m-%d")
                - timedelta(days=7)).strftime("%Y-%m-%d")
        rows = []
        for tkey, tcfg in config.active_targets().items():
            cur = conn.execute("""
                SELECT * FROM market_daily
                 WHERE target_key=? AND snapshot_date=?
            """, (tkey, snap)).fetchone()
            if not cur:
                rows.append({"key": tkey, "label": tcfg["label"],
                             "missing": True})
                continue
            old = conn.execute("""
                SELECT price_median FROM market_daily
                 WHERE target_key=? AND snapshot_date<=?
                 ORDER BY snapshot_date DESC LIMIT 1
            """, (tkey, prev)).fetchone()
            d = dict(cur)
            d["key"] = tkey
            d["label"] = tcfg["label"]
            d["trend"] = None
            if old and old["price_median"] and cur["price_median"]:
                d["trend"] = round(
                    (cur["price_median"] - old["price_median"])
                    / old["price_median"] * 100, 1)
            rows.append(d)
        ctx["market"] = rows

        # 최근 이벤트 (가격 변동 · 재등록)
        ctx["recent"] = [dict(r) for r in conn.execute("""
            SELECT e.*, l.model_group, l.year_month, l.mileage,
                   l.color_ext, l.url, l.dealer_id
              FROM events e JOIN listings l ON l.listing_id = e.listing_id
             WHERE e.event_type IN ('PRICE_DOWN','PRICE_UP','RELIST','GONE')
             ORDER BY e.event_date DESC, e.event_id DESC LIMIT 25
        """).fetchall()]

        # 관심매물 알림
        ctx["watch_alerts"] = [dict(r) for r in conn.execute("""
            SELECT w.listing_id, l.model_group, l.year_month, l.first_price,
                   l.current_price, l.status, l.url, l.first_seen,
                   l.price_change_count
              FROM watchlist w JOIN listings l ON l.listing_id = w.listing_id
             WHERE l.price_change_count > 0 OR l.status <> 'active'
             ORDER BY l.updated_at DESC LIMIT 10
        """).fetchall()]

        # 플래그 집계
        ctx["flags"] = [dict(r) for r in conn.execute("""
            SELECT f.flag_code, f.flag_label, COUNT(*) c
              FROM listing_flags f
              JOIN listings l ON l.listing_id = f.listing_id
             WHERE f.resolved=0 AND l.status='active'
             GROUP BY f.flag_code ORDER BY c DESC
        """).fetchall()]

        # 수집 로그
        ctx["site_runs"] = [dict(r) for r in conn.execute("""
            SELECT * FROM site_run_log WHERE run_date=?
             ORDER BY site, target_key
        """, (snap,)).fetchall()]

    return render_template("dashboard.html", **ctx)


# ──────────────────────────────────────────────────────────────
# 2. 매물 목록
# ──────────────────────────────────────────────────────────────
@app.route("/listings")
def listings():
    tkey = request.args.get("target") or None
    order = request.args.get("order", "rank")
    show_all = request.args.get("all") == "1"     # E등급(추천배제) 포함
    grade = request.args.get("grade") or None
    fail = request.args.get("fail") or None       # 특정 축 미달만
    rank = request.args.get("rank", type=int)
    axis = request.args.get("axis") or None       # 축 이름 (예: accident_code)
    bucket = request.args.get("bucket") or None   # 값 (예: AC4)

    with db.connect() as conn:
        if not schema_ready(conn):
            return not_ready()
        ctx = nav_context(conn)
        sql = """
            SELECT l.*, d.honesty_score, d.quadrant, d.sample_sufficient,
                   d.total_listings AS d_total
              FROM listings l
              LEFT JOIN dealers d ON d.dealer_id = l.dealer_id
             WHERE l.status='active'
        """
        args: list = []
        if not show_all:
            sql += " AND (l.condition_grade IS NULL OR l.condition_grade <> 'E')"
        if tkey:
            sql += " AND l.target_key=?"
            args.append(tkey)
        if grade:
            sql += " AND l.condition_grade=?"
            args.append(grade)
        if rank:
            sql += " AND l.recommend_rank=?"
            args.append(rank)
        if fail:
            # fail_reasons 는 콤마 구분 문자열이다.
            # LIKE '%X%' 는 COLOR_EXT 가 COLOR_EXT_GROUP 을 잡는 식의
            # 부분일치 오탐이 나므로 앞뒤에 콤마를 붙여 정확히 맞춘다.
            sql += " AND (',' || IFNULL(l.fail_reasons,'') || ',') LIKE ?"
            args.append(f"%,{fail},%")
        if axis and bucket:
            col = {
                "grade": "condition_grade", "hud": "opt_hud",
                "warranty": "warranty_code", "mileage": "mileage_band",
                "color_ext": "color_ext_group", "color_int": "color_int_group",
                "rental": "rental_status", "rental_type": "rental_type",
                "accident": "accident_code", "insurance": "insurance_grade",
                "rank": "recommend_rank",
            }.get(axis)
            if col:
                if bucket == "unknown":
                    sql += f" AND l.{col} IS NULL"
                else:
                    sql += f" AND l.{col}=?"
                    args.append(bucket)

        order_map = {
            "rank": ("l.recommend_rank ASC NULLS LAST,"
                     " IFNULL(l.score_total,0) DESC,"
                     " l.current_price ASC"),
            "score": "IFNULL(l.score_total,0) DESC, l.current_price ASC",
            "safety": "IFNULL(l.safety_pct,0) DESC, l.current_price ASC",
            "spec": "IFNULL(l.spec_pct,0) DESC, l.current_price ASC",
            "grade": "l.condition_grade ASC, l.current_price ASC",
            "price": "l.current_price ASC",
            "price_desc": "l.current_price DESC",
            "mileage": "l.mileage ASC",
            "year": "l.year_month DESC",
            "new": "l.first_seen DESC",
            "dom": "l.first_seen ASC",
        }
        sql += f" ORDER BY {order_map.get(order, order_map['rank'])} LIMIT 300"

        pbase = ctx.get("photo_base")
        items = [dict(r) for r in conn.execute(sql, args).fetchall()]

        # 플래그 붙이기
        for it in items:
            it["flags"] = [r["flag_label"] for r in conn.execute(
                "SELECT flag_label FROM listing_flags "
                " WHERE listing_id=? AND resolved=0", (it["listing_id"],))]
            it["in_watch"] = bool(conn.execute(
                "SELECT 1 FROM watchlist WHERE listing_id=?",
                (it["listing_id"],)).fetchone())
            it["dom"] = _days_since(it["first_seen"])
            it["_photo_full"] = photo.build(pbase, it.get("photo_url"))
            it["fail_codes"] = [f for f in
                                (it["fail_reasons"] or "").split(",") if f]
            it["fails"] = [config.RELAX_LABELS.get(f, f)
                           for f in it["fail_codes"]]

        # 필터 요약 — 무엇으로 걸러진 화면인지 항상 보이게 한다
        chips = []
        if tkey:
            chips.append(config.TARGETS.get(tkey, {}).get("label", tkey))
        if grade:
            chips.append(f"{grade}등급")
        if rank:
            chips.append(f"{rank}순위")
        if fail:
            chips.append(f"미달: {config.RELAX_LABELS.get(fail, fail)}")
        if axis and bucket:
            lbl = {**config.ACCIDENT_CODES, **config.INSURANCE_CODES,
                   **config.WARRANTY_CODES}.get(bucket, bucket)
            chips.append(f"{axis}={lbl}")

        ctx.update({"items": items, "target": tkey, "order": order,
                    "show_all": show_all, "grade": grade,
                    "fail": fail, "rank": rank, "axis": axis,
                    "bucket": bucket, "chips": chips,
                    "relax_labels": config.RELAX_LABELS,
                    "count": len(items),
                    "codes": {"acc": config.ACCIDENT_CODES,
                              "ins": config.INSURANCE_CODES,
                              "war": config.WARRANTY_CODES}})
    return render_template("listings.html", **ctx)


def peek_data(it: dict) -> str:
    """
    마우스 오버 미리보기용 JSON.
    표에서 읽기 어려운 것(사진·설명·미달 사유)을 여기 담는다.
    """
    price = it.get("current_price")
    tags: list[list[str]] = []
    g = it.get("condition_grade")
    if g:
        tags.append([f"{g}등급",
                     "amber" if g == "A" else "down" if g == "B"
                     else "up" if g == "E" else ""])
    if it.get("recommend_rank"):
        tags.append([f"{it['recommend_rank']}순위", "down"])
    # ★ 근거를 함께 보여준다.
    #   '왜 있다고 판단했는지'를 물어보지 않아도 되게 한다.
    _hs = {"option_choice": "실장착 확인", "selling_point": "셀링포인트",
           "option_api": "옵션 목록", "trim": "트림", "year": "연식",
           "package": "패키지", "ad_words": "딜러 기재",
           "single": "단일 사양"}.get(it.get("opt_hud_source"))
    _hv = it.get("opt_hud")
    tags.append([("차종 미제공" if _hv == -1
                  else "HUD 있음" if _hv == 1 else "HUD 없음")
                 + (f" ({_hs})" if _hs else ""),
                 "amber" if it.get("opt_hud") else ""])
    if it.get("warranty_code"):
        tags.append([f"보증 {it['warranty_code']}",
                     "down" if it["warranty_code"] == "W1" else ""])
    ac = it.get("accident_code")
    if ac:
        tags.append([config.ACCIDENT_CODES.get(ac, ac),
                     "down" if ac == "AC1"
                     else "up" if ac in config.ACCIDENT_MAJOR else ""])
    # ★ 외판 교환은 판수를 보여준다  (지시서 5.4-C)
    #   1판과 4판은 다르다. 뭉뚱그리면 판단이 안 된다.
    _do = it.get("damage_outer")
    if ac == "AC2" and _do:
        tags.append([f"외판 {_do}판 교환",
                     "up" if _do >= 3 else ""])
    ins = it.get("insurance_grade")
    if ins:
        # ★ 금액 0원인데 사고가 있으면 그렇게 표시한다 (지시서 5.4-D)
        #   '내차 피해 없음'은 금액이 없다는 뜻이지
        #   사고가 없다는 뜻이 아니다.
        _an = it.get("my_accident_cnt") or 0
        if ins == "I0" and _an > 0:
            tags.append([f"보험 0원 · 사고 {_an}건 (제조사 처리 의심)",
                         "up"])
        else:
            tags.append([f"보험 {config.INSURANCE_CODES.get(ins, ins)}",
                         "down" if ins == "I0"
                         else "up" if ins == "I3" else ""])
    rs = it.get("rental_status")
    if rs:
        tags.append(["비렌트" if rs == "none"
                     else "법인렌트" if it.get("rental_type") == "corporate"
                     else "개인렌트" if it.get("rental_type") == "personal"
                     else "렌트 이력", "" if rs == "none" else "up"])

    # ★ 엔카 진단 — 엔카가 직접 점검한 차량.
    #   딜러 신고보다 신뢰도가 높다.
    # ★ 연식과 등록연도가 다르면 알린다.
    #   2023-11 등록인데 2024년식이면 시세가 다르다.
    fy = it.get("form_year")
    ym = str(it.get("year_month") or "")
    if fy and ym[:4].isdigit() and int(ym[:4]) != int(fy):
        tags.append([f"{fy}년식 ({ym} 등록)", ""])

    # ★ 압류·저당은 거래 자체가 막힌다. 가장 먼저 알린다.
    if (it.get("seizing_count") or 0) > 0:
        tags.append([f"★ 압류 {it['seizing_count']}건", "up"])
    if (it.get("pledge_count") or 0) > 0:
        tags.append([f"★ 저당 {it['pledge_count']}건", "up"])

    if it.get("is_duplicate"):
        tags.append(["엔카 중복표시", "dim"])
    if it.get("encar_diagnosis"):
        tags.append([f"엔카진단 {it['encar_diagnosis']}", "amber"])
    elif it.get("encar_cert") == "none":
        tags.append(["엔카인증 없음", "up"])
    if it.get("trust_extend"):
        tags.append(["연장보증", "down"])
    elif it.get("trust_warranty"):
        tags.append(["엔카보증", "down"])

    g = it.get("condition_grade")
    if g in ("S", "A"):
        tags.append([f"{config.GRADE_BADGE.get(g, '')} {g}등급 "
                     f"{config.GRADE_LABEL.get(g, '')}",
                     "amber" if g == "S" else "down"])
    if it.get("record_open"):
        mc = it.get("my_accident_cost") or 0
        oc = it.get("other_accident_cost") or 0
        tot = mc + oc
        rt = it.get("insurance_ratio")
        label = f"내차 손해 {tot // 10000:,}만"
        if rt:
            label += f" ({rt:.1%})"
        tags.append([label, "down" if not tot
                     else "up" if it.get("insurance_grade") == "I3"
                     else ""])
        if mc and oc:
            tags.append([f"내보험 {mc // 10000:,}만 + "
                         f"타차보험 {oc // 10000:,}만", ""])
        elif oc:
            tags.append([f"타차보험 처리 {oc // 10000:,}만", ""])
        if it.get("unrepaired_confirmed"):
            tags.append(["사고 기록 있으나 수리비 0원 (손상 확인)", "up"])
        elif it.get("unrepaired_suspect"):
            tags.append(["사고 기록 있으나 수리비 0원", "up"])
    # ★ 총점과 소계  (부록 Q.9.1)
    tot = it.get("score_total")
    if tot:
        tags.append([f"{tot}점", "amber" if tot >= 351 else ""])
        st = ((it.get("score_warranty") or 0) + (it.get("score_mileage") or 0)
              + (it.get("score_color") or 0) + (it.get("score_history") or 0))
        tags.append([f"상태 {st} · 가격 {it.get('score_price') or 0}"
                     f" · 사양 {it.get('score_spec') or 0}"
                     f" · 안전 {it.get('score_safety') or 0}", "dim"])
    if it.get("opt_tinting") == 0:
        tags.append(["틴팅 미시공 (약 100만원)", ""])

    wl = it.get("warranty_gen_left")
    if wl is not None:
        tags.append([f"보증 {wl}개월",
                     "down" if wl >= 24 else "up" if wl < 6 else ""])
    if it.get("damage_frame"):
        tags.append([f"골격 손상 {it['damage_frame']}부위", "up"])
    elif it.get("damage_outer"):
        # ★ f-string 안에서 줄을 바꾸면 Python 3.11 에서 SyntaxError 다.
        #   3.12 부터 허용되므로 낮은 버전에서도 되게 밖으로 뺀다.
        is_exchange = it.get("accident_code") == "AC2"
        kind_txt = "교환" if is_exchange else "판금"
        tags.append([f"외판 {it['damage_outer']}부위 ({kind_txt})",
                     "" if is_exchange else "up"])
    if it.get("damage_corrosion"):
        tags.append([f"부식 {it['damage_corrosion']}부위 (노후)", ""])
    elif it.get("record_fetched_at"):
        tags.append(["이력 비공개", "up"])
    else:
        tags.append(["이력 미조회", ""])
    if not it.get("verified"):
        tags.append(["미검증", ""])
    if it.get("is_lease"):
        tags.append(["리스·렌트 승계", "up"])
    if it.get("price_anomaly"):
        tags.append([it.get("price_anomaly_why") or "가격 이상", "up"])
    if it.get("opt_fetched_at"):
        tags.append(["옵션 확인", "down"])
    if it.get("insp_fetched_at"):
        tags.append(["점검부 확인", "down"])
    if it.get("insp_usage_change"):
        tags.append([f"용도변경 {it['insp_usage_change']}", "up"])
    gap = it.get("insp_mileage_gap")
    if gap is not None and abs(gap) >= 3000:
        tags.append([f"주행 불일치 {gap:+,}", "up"])

    bits = []
    if it.get("opt_names_json"):
        try:
            _n = json.loads(it["opt_names_json"])
            if _n:
                bits.append("옵션 " + "·".join(_n[:3]))
        except (ValueError, TypeError):
            pass
    if it.get("vin"):
        bits.append(f"VIN {it['vin'][-6:]}")
    if it.get("mileage"):
        bits.append(f"{it['mileage']:,}km")
    if it.get("year_month"):
        bits.append(f"{it['year_month']}식")
    if it.get("color_ext"):
        bits.append(f"외장 {it['color_ext']}")
    if it.get("color_int"):
        bits.append(f"내장 {it['color_int']}")
    if it.get("dealer_id"):
        bits.append(str(it["dealer_id"]).replace("encar:", ""))
    fails = [config.RELAX_LABELS.get(f, f)
             for f in (it.get("fail_reasons") or "").split(",") if f]
    if fails:
        bits.append("미달 " + "·".join(fails[:3]))

    return json.dumps({
        "photo": it.get("_photo_full"),
        "alts": photo.candidates_for(it.get("photo_url")),
        "title": f"{it.get('model_group') or ''} {it.get('trim') or ''}".strip(),
        "price": f"{price // 10000:,}" if price else "",
        "tags": tags,
        "desc": " · ".join(bits),
    }, ensure_ascii=False)


app.jinja_env.globals["peek_data"] = peek_data


def _days_since(d: str | None) -> int | None:
    if not d:
        return None
    try:
        return (datetime.now()
                - datetime.strptime(d[:10], "%Y-%m-%d")).days
    except ValueError:
        return None


# ──────────────────────────────────────────────────────────────
# 3. 관심매물
# ──────────────────────────────────────────────────────────────
@app.route("/watch")
def watch():
    with db.connect() as conn:
        if not schema_ready(conn):
            return not_ready()
        ctx = nav_context(conn)
        items = [dict(r) for r in conn.execute("""
            SELECT w.*, l.model_group, l.trim, l.year_month, l.mileage,
                   l.color_ext, l.color_int, l.first_price, l.current_price,
                   l.lowest_price, l.status, l.url, l.first_seen,
                   l.dealer_id, l.price_change_count, l.target_key,
                   l.photo_url, l.condition_grade, l.recommend_rank,
                   l.opt_hud, l.warranty_code, l.accident_code,
                   l.insurance_grade, l.rental_status, l.rental_type,
                   l.fail_reasons
              FROM watchlist w JOIN listings l ON l.listing_id=w.listing_id
             ORDER BY w.added_date DESC
        """).fetchall()]
        pbase = ctx.get("photo_base")
        for it in items:
            it["_photo_full"] = photo.build(pbase, it.get("photo_url"))
            hist = conn.execute("""
                SELECT snapshot_date, price FROM price_history
                 WHERE listing_id=? ORDER BY snapshot_date
            """, (it["listing_id"],)).fetchall()
            it["history"] = [(r["snapshot_date"], r["price"]) for r in hist]
            it["spark"] = _sparkline([r["price"] for r in hist])
            it["dom"] = _days_since(it["first_seen"])
        ctx["items"] = items
    return render_template("watch.html", **ctx)


@app.route("/watch/add/<listing_id>", methods=["POST"])
def watch_add(listing_id):
    """
    관심 등록 = '이 매물을 매일 추적하라'는 표시.

    등록하면 아래를 매일 확인하고, 변화가 있으면 알린다.
      · 가격이 내렸는가
      · 사라졌는가 (팔렸는가 / 딜러가 내렸는가)
      · 며칠째 안 팔리고 있는가 (협상 시점 판단)

    등록하지 않은 매물도 수집·분류는 되지만 개별 추적 알림은 없다.
    """
    memo = request.form.get("memo") or None
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO watchlist(listing_id, added_date, memo) "
            "VALUES(?,?,?) ON CONFLICT(listing_id) DO UPDATE SET "
            "memo=COALESCE(excluded.memo, watchlist.memo)",
            (listing_id, db.today(), memo))
    return redirect(request.referrer or "/listings")


@app.route("/watch/memo/<listing_id>", methods=["POST"])
def watch_memo(listing_id):
    with db.connect() as conn:
        conn.execute("UPDATE watchlist SET memo=? WHERE listing_id=?",
                     (request.form.get("memo") or None, listing_id))
    return redirect(request.referrer or "/watch")


@app.route("/watch/alert/<listing_id>", methods=["POST"])
def watch_alert(listing_id):
    f = request.form
    with db.connect() as conn:
        conn.execute("""
            UPDATE watchlist SET alert_on_drop=?, alert_on_sold=?,
                   alert_on_dom=?, dom_threshold=?
             WHERE listing_id=?
        """, (1 if f.get("drop") else 0, 1 if f.get("sold") else 0,
              1 if f.get("dom") else 0,
              int(f.get("dom_days") or 30), listing_id))
    return redirect(request.referrer or "/watch")


@app.route("/watch/remove/<listing_id>", methods=["POST"])
def watch_remove(listing_id):
    with db.connect() as conn:
        conn.execute("DELETE FROM watchlist WHERE listing_id=?", (listing_id,))
    return redirect(request.referrer or "/watch")


def _sparkline(vals: list[int], w: int = 120, h: int = 28) -> dict:
    """가격 추이 SVG 좌표. 값이 2개 미만이면 그리지 않는다."""
    vals = [v for v in vals if v is not None]
    if len(vals) < 2:
        return {"points": "", "flat": True, "n": len(vals)}
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1
    n = len(vals)
    pts = []
    for i, v in enumerate(vals):
        x = i * (w - 2) / (n - 1) + 1
        y = h - 3 - (v - lo) / span * (h - 6)
        pts.append(f"{x:.1f},{y:.1f}")
    return {"points": " ".join(pts), "flat": hi == lo, "n": n,
            "min": lo, "max": hi, "w": w, "h": h}


# ──────────────────────────────────────────────────────────────
# 4. 딜러
# ──────────────────────────────────────────────────────────────
@app.route("/dealers")
def dealers():
    with db.connect() as conn:
        if not schema_ready(conn):
            return not_ready()
        ctx = nav_context(conn)
        q = request.args.get("q") or None
        if q:
            rows = [dict(r) for r in conn.execute("""
                SELECT * FROM dealers WHERE dealer_id LIKE ?
                 ORDER BY honesty_score DESC NULLS LAST LIMIT 300
            """, (f"%{q}%",)).fetchall()]
        else:
            rows = [dict(r) for r in conn.execute("""
                SELECT * FROM dealers
                 ORDER BY sample_sufficient DESC,
                          honesty_score DESC NULLS LAST LIMIT 300
            """).fetchall()]
        ctx["q"] = q
        ctx["dealers"] = rows
        ctx["scored"] = [r for r in rows if r["sample_sufficient"]]
        q = {}
        for r in rows:
            q[r["quadrant"] or "?"] = q.get(r["quadrant"] or "?", 0) + 1
        ctx["quadrants"] = q
        ctx["min_listings"] = config.DEALER_MIN_LISTINGS
    return render_template("dealers.html", **ctx)


# ──────────────────────────────────────────────────────────────
# 5. 시세 추이
# ──────────────────────────────────────────────────────────────
@app.route("/market")
def market():
    with db.connect() as conn:
        if not schema_ready(conn):
            return not_ready()
        ctx = nav_context(conn)
        # ★ 데이터가 없는 차종도 표시한다.
        #   빠져 있으면 '수집이 안 된 것'인지 '매물이 없는 것'인지
        #   구분할 수 없다 (조용한 실패 금지).
        series = {}
        for tkey, tcfg in config.active_targets().items():
            rows = conn.execute("""
                SELECT snapshot_date, count_total, count_eligible,
                       price_min, price_p25, price_median, price_p75,
                       price_max, volume_tier
                  FROM market_daily WHERE target_key=?
                 ORDER BY snapshot_date
            """, (tkey,)).fetchall()
            live = conn.execute("""
                SELECT COUNT(*) c FROM listings
                 WHERE target_key=? AND status='active'
            """, (tkey,)).fetchone()["c"]
            runlog = conn.execute("""
                SELECT status, skip_reason, collected FROM site_run_log
                 WHERE target_key=? ORDER BY run_date DESC LIMIT 1
            """, (tkey,)).fetchone()
            series[tkey] = {
                "label": tcfg["label"],
                "rows": [dict(r) for r in rows],
                "live": live,
                "empty": not rows,
                "last_run": dict(runlog) if runlog else None,
                "tier": tcfg.get("volume_tier"),
                "spark": _sparkline(
                    [r["price_median"] for r in rows], w=200, h=40)
                if rows else {"points": "", "n": 0},
            }
        ctx["series"] = series
        snap = latest_snapshot(conn)
        axes = {}
        if snap:
            for r in conn.execute("""
                SELECT * FROM condition_stats
                 WHERE snapshot_date=? AND axis<>'fail'
                 ORDER BY target_key, axis, bucket
            """, (snap,)):
                d = dict(r)
                axes.setdefault(d["target_key"], {}).setdefault(
                    d["axis"], []).append(d)
        ctx["axes"] = axes
        ctx["snapshot"] = snap
        ctx["axis_label"] = {
            "grade": "등급", "hud": "HUD", "warranty": "보증",
            "accident": "사고", "insurance": "보험", "rental": "렌트",
            "color_ext": "외장색", "color_int": "내장색",
            "mileage": "주행", "rank": "순위", "rental_type": "렌트유형",
            "war_band": "보증잔여",
        }
        ctx["bucket_label"] = {
            **config.ACCIDENT_CODES, **config.INSURANCE_CODES,
            **config.WARRANTY_CODES,
            "1": "있음", "0": "없음", "none": "비렌트",
            "current_rental": "렌트", "past_rental": "허→일반",
            "mono": "무채색", "blue": "청색", "red": "레드", "etc": "기타",
            "pref": "선호", "nonpref": "비선호", "unknown": "불명",
            "1": "있음", "0": "없음", "None": "불명",
            **{c: lb for c, _, _, lb in config.WARRANTY_BANDS},
        }
    return render_template("market.html", **ctx)


# ──────────────────────────────────────────────────────────────
# 6. 실행 — 수집을 웹에서 시작하고 진행을 실시간으로 본다
# ──────────────────────────────────────────────────────────────
@app.route("/run")
def run_page():
    with db.connect() as conn:
        ready = schema_ready(conn)
        ctx = nav_context(conn) if ready else {
            "targets": config.active_targets(), "last_run": None,
            "reload_sec": None,
            "now": datetime.now().strftime("%Y-%m-%d %H:%M")}
        ctx["schema_ready"] = ready
        if ready:
            ctx["today_done"] = store.is_collected_today(conn, db.today())
            ctx["recent_runs"] = [dict(r) for r in conn.execute("""
                SELECT * FROM collection_log
                 ORDER BY run_date DESC LIMIT 7
            """).fetchall()]
            # ★ 마지막 실패와 traceback.
            #   웹 로그는 새 실행 때 비워지고 콘솔은 스크롤이 밀린다.
            #   '왜 멈췄나'를 나중에 보려면 화면에 남아 있어야 한다.
            _le = conn.execute(
                "SELECT value, updated_at FROM meta WHERE key='last_error'"
            ).fetchone()
            ctx["last_error"] = dict(_le) if _le else None
            _lf = conn.execute("""
                SELECT run_date, status, error_msg FROM collection_log
                 WHERE status='failed' AND IFNULL(error_msg,'') <> ''
                 ORDER BY run_date DESC LIMIT 1
            """).fetchone()
            ctx["last_fail"] = dict(_lf) if _lf else None
        else:
            ctx["today_done"] = False
            ctx["recent_runs"] = []
    ctx["reload_sec"] = None          # 이 화면은 JS 로 갱신한다
    ctx["state"] = runner.snapshot()
    import notifier
    ctx["notify_on"] = notifier.enabled()
    import scheduler
    with db.connect() as conn2:
        ctx["sched"] = scheduler.decide(conn2)
    ctx["warnings"] = config.config_warnings()
    ctx["notices"] = config.config_notices()
    return render_template("run.html", **ctx)


@app.route("/api/run/start", methods=["POST"])
def api_run_start():
    job = (request.json or {}).get("job", "collect") \
        if request.is_json else request.form.get("job", "collect")
    force = str((request.json or {}).get("force", "")).lower() in ("1", "true") \
        if request.is_json else request.form.get("force") == "1"
    target = (request.json or {}).get("target") if request.is_json \
        else request.form.get("target")

    if runner.is_running():
        return jsonify({"ok": False,
                        "error": "이미 실행 중입니다"}), 409

    config.ensure_dirs()
    with db.connect() as conn:
        if not schema_ready(conn):
            db.init_db()
            try:
                import vehicle_spec
                with db.connect() as c2:
                    vehicle_spec.seed(c2)
            except Exception:
                pass

    if job == "collect":
        def _work():
            collect.LOG_SINK = runner.emit
            collect.PHASE_SINK = runner.set_phase
            try:
                return collect.run(db.today(), force=force,
                                   only=target or None, dry_run=False)
            finally:
                collect.LOG_SINK = None
                collect.PHASE_SINK = None
    elif job == "dryrun":
        def _work():
            collect.LOG_SINK = runner.emit
            collect.PHASE_SINK = runner.set_phase
            try:
                return collect.run(db.today(), force=True,
                                   only=target or None, dry_run=True)
            finally:
                collect.LOG_SINK = None
                collect.PHASE_SINK = None
    elif job == "analyze":
        def _work():
            """수집 없이 분류·통계만 다시 돌린다."""
            from analyzer import classify, dealer, stats
            d = db.today()
            runner.set_phase("딜러 지표", 20)
            with db.connect() as conn:
                dl = dealer.rebuild(conn, d)
            runner.emit(f"딜러 {dl.get('dealers', 0)}명 / "
                        f"점수 {dl.get('scored', 0)}명")
            runner.set_phase("7축 분류", 50)
            with db.connect() as conn:
                cl = classify.rebuild(conn, d)
            g = cl.grades
            runner.emit(" / ".join(f"{k} {g.get(k, 0)}"
                                   for k in config.GRADE_ORDER))
            runner.set_phase("축별 통계", 75)
            with db.connect() as conn:
                st = stats.rebuild(conn, d)
            runner.emit(f"차종 {st['targets']}종 / 집계 {st['rows']}행")
            runner.set_phase("완화 시뮬레이션", 92)
            with db.connect() as conn:
                classify.rebuild_relax(conn, d)
            runner.emit("완화 시뮬레이션 갱신")
            return {"status": "done", "grades": g}
    else:
        return jsonify({"ok": False, "error": f"알 수 없는 작업: {job}"}), 400

    ok, msg = runner.start(job, _work)
    return jsonify({"ok": ok, "message": msg}), (200 if ok else 409)


@app.route("/api/run/status")
def api_run_status():
    since = request.args.get("since", type=int, default=0)
    st = runner.snapshot()
    st["logs"] = runner.logs_since(since)
    return jsonify(st)


# ──────────────────────────────────────────────────────────────
# 7. 후보군 — 순위별 카드 목록 (지시서 8.2)
# ──────────────────────────────────────────────────────────────
@app.route("/recommend")
def recommend_page():
    tkey = request.args.get("target") or None
    rank = request.args.get("rank", type=int)
    # ★ 기본은 3순위까지. D 로 목록이 채워지면 1순위가 묻힌다 (K.4)
    rank_limit = request.args.get("limit", type=int) \
        or config.DEFAULT_RANK_LIMIT

    with db.connect() as conn:
        if not schema_ready(conn):
            return not_ready()
        ctx = nav_context(conn)
        sql = """
            SELECT l.*, d.honesty_score, d.quadrant, d.sample_sufficient,
                   d.total_listings AS d_total
              FROM listings l
              LEFT JOIN dealers d ON d.dealer_id = l.dealer_id
             WHERE l.status='active' AND l.recommend_rank IS NOT NULL
               AND IFNULL(l.is_duplicate, 0) = 0
               AND IFNULL(l.is_best_price, 1) = 1
               AND l.recommend_rank <= ?
               AND IFNULL(l.price_anomaly, 0) = 0
               AND IFNULL(l.is_lease, 0) = 0
               AND IFNULL(l.is_lease_product, 0) = 0
        """
        args: list = [rank_limit]
        if tkey:
            sql += " AND l.target_key=?"
            args.append(tkey)
        if rank:
            sql += " AND l.recommend_rank=?"
            args.append(rank)
        # ★ 같은 순위·비슷한 가격이면 보증이 많이 남은 쪽이 낫다.
        #   '보증 30개월 남은 3,500만'과 '3개월 남은 3,400만' 중
        #   실제로 싼 쪽은 전자다. 실질가격으로 정렬한다.
        # ★ 실질가격 = 표시가 − 남은 보증 + 없는 장비 시공비
        #   '틴팅 있는 3,520만'과 '없는 3,480만' 중 어느 쪽이 싼지는
        #   시공비를 넣어봐야 안다.
        # ★ 동순위 안에서만 정렬한다 (A.1.2).
        #   전부 "높을수록 좋음 = DESC / 낮을수록 좋음 = ASC" 로 통일.
        # ★ 총점이 곧 순위다  (부록 Q.11)
        sql += (" ORDER BY l.recommend_rank ASC,"
                " IFNULL(l.score_total, 0) DESC,"
                " IFNULL(l.score_price, 0) DESC,"
                # ★ 보증 차감 없이 실제 가격으로 정렬 [가이드 4.1]
                " l.current_price ASC,"
                " l.mileage ASC,"
                " IFNULL(l.warranty_gen_left, 0) DESC"
                " LIMIT 200")

        pbase = ctx.get("photo_base")
        pbase = ctx.get("photo_base")
        items = [dict(r) for r in conn.execute(sql, args).fetchall()]
        for it in items:
            it["_photo_full"] = photo.build(pbase, it.get("photo_url"))
            it["fail_codes"] = [f for f in
                                (it["fail_reasons"] or "").split(",") if f]
            it["fails"] = [config.RELAX_LABELS.get(f, f)
                           for f in it["fail_codes"]]
            it["flags"] = [r["flag_label"] for r in conn.execute(
                "SELECT flag_label FROM listing_flags "
                " WHERE listing_id=? AND resolved=0", (it["listing_id"],))]
            it["in_watch"] = bool(conn.execute(
                "SELECT 1 FROM watchlist WHERE listing_id=?",
                (it["listing_id"],)).fetchone())
            it["dom"] = _days_since(it["first_seen"])
            it["_photo_full"] = photo.build(pbase, it.get("photo_url"))
            it["label"] = config.TARGETS.get(
                it["target_key"], {}).get("label", it["target_key"])
            # ★ 보증 가치를 가격에서 빼지 않는다  [가이드 4.1 금지]
            #   보증은 100점 축으로 이미 반영된다. 이중 계산이다.
            #   정렬도 표시가도 실제 판매가를 쓴다.
            it["net_price"] = it.get("current_price") or 0

        by_rank: dict[int, list] = {1: [], 2: [], 3: []}
        for it in items:
            by_rank.setdefault(it["recommend_rank"], []).append(it)

        ctx.update({"items": items, "by_rank": by_rank,
                    "target": tkey, "rank": rank, "rank_limit": rank_limit,
                    "grade_badge": config.GRADE_BADGE,
                    "grade_label": config.GRADE_LABEL,
                    "count": len(items),
                    "codes_acc": config.ACCIDENT_CODES,
                    "codes_ins": config.INSURANCE_CODES,
                    "relax_labels": config.RELAX_LABELS})
    return render_template("recommend.html", **ctx)


# ──────────────────────────────────────────────────────────────
# 8. 리포트 — 검증용 파일 내려받기
# ──────────────────────────────────────────────────────────────
@app.route("/reports")
def reports_page():
    with db.connect() as conn:
        ctx = nav_context(conn) if schema_ready(conn) else {
            "targets": config.active_targets(), "last_run": None,
            "now": datetime.now().strftime("%Y-%m-%d %H:%M")}
    ctx["reload_sec"] = None
    files = []
    if config.REPORT_DIR.exists():
        for f in sorted(config.REPORT_DIR.iterdir(), reverse=True):
            if f.is_file() and f.suffix in (".md", ".json"):
                files.append({
                    "name": f.name,
                    "size": f.stat().st_size,
                    "mtime": datetime.fromtimestamp(
                        f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "kind": "진단 (검증용)" if f.name.startswith("diagnostic")
                            else "일일 리포트",
                })
    ctx["files"] = files
    ctx["report_dir"] = str(config.REPORT_DIR)
    return render_template("reports.html", **ctx)


@app.route("/reports/<path:name>")
def report_file(name):
    """리포트 파일 내려받기. 디렉토리 밖은 막는다."""
    from flask import send_from_directory, abort
    safe = Path(name).name
    target = config.REPORT_DIR / safe
    if not target.exists() or not target.is_file():
        abort(404)
    return send_from_directory(str(config.REPORT_DIR), safe,
                               as_attachment=True)


# ★ f-string 안에서 줄을 바꾸면 Python 3.11 에서 SyntaxError 다.
#   3.12 부터 허용되므로, 개발 환경에서만 통과하고 실행 환경에서 죽는다.
#   dict 조회 같은 긴 식은 함수로 뺀다.
HUD_SOURCE_LABEL = {
    "ad_words": "딜러 광고문구 — 확인 필요",
    "selling_point": "실장착 옵션 확인",
    "selling_point": "장착 옵션 확인",
    "option_api": "옵션 API",
    "trim": "트림으로 확정",
    "year": "연식 기본장착 추정",
    "single": "문구",
    "none": "차종 미탑재",
    "unknown": "판정 불가 — 상세 조회 필요",
}


def _site_prices(vehicle_id: str) -> list:
    """같은 차량의 사이트별 가격.  (설계서 8.4)"""
    from analyzer import vehicle as _v
    try:
        with db.connect() as conn:
            rows = _v.site_prices(conn, vehicle_id)
    except Exception:
        return []
    return rows if len(rows) > 1 else []


def _price_rows(rec: dict, ev: dict) -> list:
    """
    기대가 산출 근거.  (부록 S.7)

    ★ 마스터가 근거를 확인할 수 있어야 한다.
      '기대가 3,680만'만 보여주면 믿을 수 없다.
    """
    from analyzer import baseline

    e = baseline.expected_price(rec)
    p = e.get("parts") or {}
    exp = e.get("expected")
    price = rec.get("current_price") or 0

    rows = [("실매물가", f"{price // 10000:,}만", 0, 100)]
    if not exp:
        rows.append(("기대가", e.get("why") or "산출 불가", 0, 100))
        return rows

    diff = price - exp
    rows.append((
        "기대가",
        f"{exp // 10000:,}만  ({diff // 10000:+,}만 · {diff / exp:+.1%})",
        ev.get("score_price") or 0, 100))
    if p.get("base"):
        rows.append(("  트림 기본가", f"{p['base'] // 10000:,}만", 0, 0))
    if p.get("option"):
        rows.append(("  옵션", f"+{p['option'] // 10000:,}만", 0, 0))
    if p.get("months") is not None:
        rows.append((f"  경과 {p['months']}개월",
                     f"× {p.get('residual')}", 0, 0))
    if p.get("brand") and p["brand"] != 1.0:
        rows.append(("  브랜드 계수", f"× {p['brand']}", 0, 0))
    if p.get("mileage") and p["mileage"] != 1.0:
        rows.append((f"  주행 {(rec.get('mileage') or 0):,}km",
                     f"× {p['mileage']}", 0, 0))
    return rows


def _score_rows(ev: dict) -> list:
    """
    사양·안전 항목별 표시.  (부록 P.7.2)

    ★ 두 축을 섞지 않는다. 성격이 다르다.
    """
    miss_s = set((ev.get("spec_missing") or "").split(","))
    miss_f = set((ev.get("safety_missing") or "").split(","))
    tk = ev.get("target_key") or ""
    on = config.SPEC_DEFAULT_ON.get(tk, [])
    off = config.SPEC_DEFAULT_OFF.get(tk, [])

    rows = []
    for opt, pen in config.SPEC_PENALTY.items():
        lab = config.SPEC_LABEL.get(opt, opt)
        if opt in on:
            rows.append(("spec", lab, "차종 기본 장착", 0, False))
            continue
        if opt in off:
            rows.append(("spec", lab, "차종 미탑재", pen, True))
            continue
        v = ev.get(f"opt_{opt}")
        if v == 1:
            rows.append(("spec", lab, "있음", 0, False))
        elif opt in miss_s or v == 0:
            cost = config.SPEC_FIX_COST.get(opt)
            note = "없음" + (f" (약 {cost // 10000}만원)" if cost else "")
            rows.append(("spec", lab, note, pen, True))
        else:
            cost = config.SPEC_FIX_COST.get(opt)
            note = "불명" + (f" (없으면 약 {cost // 10000}만원)"
                           if cost else "")
            rows.append(("spec", lab, note, 0, False))

    for opt, pen in config.SAFETY_PENALTY.items():
        lab = config.SAFETY_LABEL.get(opt, opt)
        if opt in miss_f:
            rows.append(("safety", lab, "없음", pen, True))
        elif ev.get("encar_cert") == "unknown":
            rows.append(("safety", lab, "미수집", 0, False))
        else:
            rows.append(("safety", lab, "있음", 0, False))
    rows["build"] = config.BUILD
    return rows


def _hud_text(ev: dict) -> str:
    """
    HUD 판정 결과와 근거.

    ★ '있음'만 보여주면 딜러 광고를 믿은 건지 알 수 없다.
      실측(2026-08-06)에서 광고문구를 근거로
      실제로 없는 HUD 를 있다고 판정했다.
    """
    v = ev.get("opt_hud")
    state = "있음" if v == 1 else "없음" if v == 0 else "불명"
    src = ev.get("opt_hud_source") or "unknown"
    label = HUD_SOURCE_LABEL.get(src, src)
    return state + " (" + label + ")"


@app.route("/why/<listing_id>")
def why_page(listing_id):
    """매물 하나의 판정 근거. 등급만 보면 왜 그런지 알 수 없다."""
    from analyzer import classify as _cf
    with db.connect() as conn:
        if not schema_ready(conn):
            return not_ready()
        ctx = nav_context(conn)
        row = conn.execute("SELECT * FROM listings WHERE listing_id=?",
                           (listing_id,)).fetchone()
        if not row:
            row = conn.execute(
                "SELECT * FROM listings WHERE source_id=?",
                (listing_id,)).fetchone()
        if not row:
            return render_template("notready.html",
                                   msg=f"매물 없음: {listing_id}", **ctx), 404
        rec = dict(row)
        ctx["flags"] = [dict(r) for r in conn.execute(
            "SELECT flag_code, flag_label FROM listing_flags "
            " WHERE listing_id=? AND resolved=0", (rec["listing_id"],))]

    ev = _cf.evaluate(rec)
    rec["_photo_full"] = photo.build(ctx.get("photo_base"),
                                     rec.get("photo_url"))

    from analyzer import finance as _fin, market as _mkt
    with db.connect() as conn:
        ctx["pos"] = _mkt.price_position(conn, rec)
        drop = conn.execute("""
            SELECT MIN(delta) d FROM events
             WHERE listing_id=? AND event_type='PRICE_DOWN'
               AND event_date >= date('now','-7 day')
        """, (rec["listing_id"],)).fetchone()
    rec["_recent_drop"] = drop["d"] if drop else None
    ctx["fin"] = _fin.compare_with_new(
        rec.get("current_price"), rec["target_key"], rec.get("fuel"),
        rec.get("trim"), rec.get("year_month"))
    ctx["chips"] = _mkt.reason_chips(rec, ev)
    with db.connect() as conn:
        ctx["refs"] = [dict(r) for r in conn.execute("""
            SELECT * FROM reference_links
             WHERE target_key=? AND is_active=1
             ORDER BY importance DESC, link_id
        """, (rec["target_key"],)).fetchall()]
    ctx["weighted"] = [
        (config.SPEC_LABEL[c], ev.get(f"opt_{c}"),
         config.SPEC_PENALTY[c])
        for c in config.SPEC_PENALTY
    ]
    fails = set(ev["fails"])
    ctx.update({
        "it": rec, "ev": ev,
        "label": config.TARGETS.get(rec["target_key"], {}).get(
            "label", rec["target_key"]),
        # ★ 사양·안전은 등급 축이 아니다. 따로 보여준다 (P.7.2)
        "ad_words": rec.get("ad_words"),
        # ★ 마스터가 실물로 확인한 매물이면 표시한다
        "known_truth": next(
            (t for t in config.KNOWN_TRUTH
             if t["id"] in str(rec.get("listing_id") or "")), None),
        # ★ 같은 차가 여러 사이트에 있으면 가격을 비교해 보여준다
        "site_prices": (_site_prices(rec.get("vehicle_id"))
                        if rec.get("vehicle_id") else []),
        "score_rows": _score_rows({**rec, **ev}),
        "score_parts": [
            # ★ 가격이 최대 축이라 먼저 보여준다 (설계서 6.1)
            ("가격", ev.get("score_price") or 0, 200,
             _price_rows(rec, ev)),
            ("차량 상태", (ev.get("score_warranty") or 0)
             + (ev.get("score_mileage") or 0)
             + (ev.get("score_color") or 0)
             + (ev.get("score_history") or 0), 175, [
                ("보증 잔여",
                 f"{ev.get('warranty_gen_left') or 0}개월",
                 ev.get("score_warranty") or 0, 50),
                ("주행거리", f"{(rec.get('mileage') or 0):,}km",
                 ev.get("score_mileage") or 0, 30),
                ("색상",
                 f"{rec.get('color_ext') or '?'}/"
                 f"{rec.get('color_int') or '?'}",
                 ev.get("score_color") or 0, 40),
                ("이력",
                 f"{ev.get('accident_code') or '?'} · "
                 f"{ev.get('rental_status') or '?'}",
                 ev.get("score_history") or 0, 55),
             ]),
            ("사양", ev.get("score_spec") or 0, 75, []),
            ("거래 안전", ev.get("score_safety") or 0, 40, []),
        ],
        "score_total": ev.get("score_total"),
        "score_max": config.SCORE_TOTAL,
        "score_potential": ev.get("score_potential"),
        "unknown_loss": ev.get("unknown_loss"),
        "spec_total": config.SPEC_TOTAL,
        "safety_total": config.SAFETY_TOTAL,
        "axes": [

            ("2 보증", f"{ev['warranty_code'] or '?'} · 일반 "
             f"{ev.get('warranty_gen_left')}개월 · 엔진 "
             f"{ev.get('warranty_engine_left')}개월",
             bool({"WAR_GEN", "WAR_PWR"} & fails)),
            ("3 주행거리", f"{(rec.get('mileage') or 0):,}km "
             f"({ev['mileage_band']})", "MILEAGE" in fails),
            # ★ 원본을 함께 보여준다.
            #   엔카 값과 실제가 다를 수 있어 사람이 확인해야 한다.
            # ★ 이름·원본·색상코드를 함께 보여준다.
            #   엔카 값과 실제가 다를 수 있어 사람이 봐야 한다.
            ("4 색상",
             f"외 {rec.get('color_ext')}"
             + (f" {rec['color_ext_raw']}" if rec.get("color_ext_raw")
                else "")
             + (f" {str(rec['color_ext_hex']).split(';')[0]}"
                if rec.get("color_ext_hex") else "")
             + f"  /  내 {rec.get('color_int')}"
             + (f" {rec['color_int_raw']}" if rec.get("color_int_raw")
                else "")
             + (f" {str(rec['color_int_hex']).split(';')[0]}"
                if rec.get("color_int_hex") else ""),
             bool({"COLOR_EXT", "COLOR_INT"} & fails)),
            ("5 렌트", f"{ev['rental_status']} / {ev['rental_type']}",
             bool({"RENT_CORP", "RENT_PERSONAL"} & fails)),
            ("6 사고", f"{ev['accident_code']} "
             f"{config.ACCIDENT_CODES.get(ev['accident_code'], '')}",
             bool({"ACCIDENT_MINOR", "ACCIDENT_MAJOR"} & fails)),
            ("7 보험", f"{ev['insurance_grade']} "
             f"{config.INSURANCE_CODES.get(ev['insurance_grade'], '')}",
             bool({"REPAIR_MINOR", "REPAIR_MAJOR", "UNREPAIRED"} & fails)),
        ],
        "fetched": [
            ("성능점검기록부", rec.get("insp_fetched_at"), "사고 부위·상태"),
            ("자동차이력정보", rec.get("record_fetched_at"),
             "보험처리액·번호판 이력"),
            ("엔카 자체진단", rec.get("diag_fetched_at"), "외판 부위별 판정"),
            ("선택 옵션", rec.get("opt_fetched_at"), "HUD 등 장착 옵션"),
        ],
    })
    return render_template("why.html", **ctx)


# ══════════════════════════════════════════════════════════
# 비교 화면  (지시서 3장 · D.4)
#
#   관심매물 (무제한) → 비교후보 (최대 10) → 최종후보 (최대 3)
#   ★ 항목을 줄이지 않는다. 화면이 좁으면 가로 스크롤한다.
# ══════════════════════════════════════════════════════════
COMPARISON = {"max_slots": 10, "max_final": 3}


def _cmp_rows(conn):
    rows = [dict(r) for r in conn.execute("""
        SELECT c.*, l.* FROM comparison c
          LEFT JOIN listings l ON l.listing_id = c.listing_id
         ORDER BY c.slot_no
    """).fetchall()]
    out = []
    for r in rows:
        if r.get("new_car_key"):
            out.append(_new_car_col(r))
        elif r.get("listing_id"):
            out.append(_used_col(r))
    return out


def _new_car_col(r):
    """신차는 매물이 아니다. 스펙과 가격만 표시한다 (3.3)."""
    from analyzer import finance as _fin
    key = r["new_car_key"]
    spec = config.NEW_CAR_PRICE.get(key) or {}
    if "trims" in spec:
        base = spec.get("base_trim") or next(iter(spec["trims"]))
        row = dict(spec["trims"][base])
        row["trim"] = base
    else:
        row = dict(spec)
    price = row.get("real_price") or row.get("price")
    f = _fin.calc(price, key, _target_fuel(key), None, is_new=True)
    return {
        "slot_no": r["slot_no"], "is_new": True,
        "label": config.TARGETS.get(key, {}).get("label", key),
        "trim": row.get("trim"), "price": price,
        "subsidy": row.get("subsidy"),
        "fin": f, "is_final": r.get("is_final"),
        "new_car_key": key,
    }


def _target_fuel(target_key):
    t = config.TARGETS.get(target_key, {})
    return t.get("fuel") or "가솔린"


def _used_col(r):
    from analyzer import finance as _fin, market as _mkt
    import json as _j
    chips = []
    try:
        chips = _j.loads(r.get("reason_chips") or "[]")
    except (ValueError, TypeError):
        pass
    return {
        "slot_no": r["slot_no"], "is_new": False,
        "listing_id": r["listing_id"],
        "label": config.TARGETS.get(r.get("target_key"), {}).get(
            "label", r.get("target_key")),
        "it": r, "chips": chips,
        "is_final": r.get("is_final"),
        "selected_reason": r.get("selected_reason"),
    }


@app.route("/compare")
def compare_page():
    with db.connect() as conn:
        if not schema_ready(conn):
            return not_ready()
        ctx = nav_context(conn)
        cols = _cmp_rows(conn)
    ctx["cols"] = cols
    ctx["used_cols"] = [c for c in cols if not c["is_new"]]
    ctx["max_slots"] = COMPARISON["max_slots"]
    ctx["max_final"] = COMPARISON["max_final"]
    ctx["best"] = _mark_best(ctx["used_cols"])
    return render_template("compare.html", **ctx)


def _mark_best(cols):
    """
    행별 최우수 값.  (A.5)
    ★ 신차 열은 제외한다. 등급·보증이 '-'라 비교가 성립하지 않는다.
    """
    if not cols:
        return {}
    best = {}
    MIN_KEYS = ["current_price", "monthly_total", "total_cost_10y",
                "mileage", "price_diff", "monthly_used"]
    MAX_KEYS = ["safety_pct", "spec_pct", "warranty_gen_left",
                "peer_count"]
    for k in MIN_KEYS:
        vals = [(c["it"].get(k), c["slot_no"]) for c in cols
                if c["it"].get(k) is not None]
        if vals:
            best[k] = min(vals)[1]
    for k in MAX_KEYS:
        vals = [(c["it"].get(k), c["slot_no"]) for c in cols
                if c["it"].get(k) is not None]
        if vals:
            best[k] = max(vals)[1]
    ranks = [(c["it"].get("recommend_rank") or 9, c["slot_no"])
             for c in cols]
    if ranks:
        best["recommend_rank"] = min(ranks)[1]
    order = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4}
    gr = [(order.get(c["it"].get("condition_grade"), 9), c["slot_no"])
          for c in cols]
    if gr:
        best["condition_grade"] = min(gr)[1]
    return best


@app.route("/api/run/clear", methods=["POST"])
def api_run_clear():
    """멈춘 것으로 보이는 실행 상태를 푼다."""
    import scheduler as _s
    with db.connect() as conn:
        n = _s.clear_stale(conn)
    return jsonify({"ok": True, "cleared": n,
                    "message": (f"{n}건 정리했습니다" if n
                                else "정리할 것이 없습니다 (작업이 실제로 실행 중)")})


@app.route("/api/compare/add", methods=["POST"])
def api_compare_add():
    data = request.get_json(silent=True) or {}
    lid = data.get("listing_id")
    nkey = data.get("new_car_key")
    if not lid and not nkey:
        return jsonify({"ok": False, "error": "대상이 없습니다"}), 400

    with db.connect() as conn:
        n = conn.execute("SELECT COUNT(*) c FROM comparison").fetchone()["c"]
        if n >= COMPARISON["max_slots"]:
            return jsonify({
                "ok": False,
                "error": f"비교는 최대 {COMPARISON['max_slots']}대까지입니다"}), 400
        dup = conn.execute(
            "SELECT slot_no FROM comparison WHERE listing_id=? OR "
            "(new_car_key IS NOT NULL AND new_car_key=?)",
            (lid, nkey)).fetchone()
        if dup:
            return jsonify({"ok": True, "message": "이미 담겨 있습니다"})

        slot = conn.execute(
            "SELECT IFNULL(MAX(slot_no),0)+1 s FROM comparison"
        ).fetchone()["s"]
        reason = price = None
        if lid:
            r = conn.execute(
                "SELECT reason_summary, current_price FROM listings "
                " WHERE listing_id=?", (lid,)).fetchone()
            if r:
                reason, price = r["reason_summary"], r["current_price"]
        conn.execute("""
            INSERT INTO comparison(slot_no, listing_id, new_car_key,
                selected_reason, selected_price, added_at)
            VALUES(?,?,?,?,?,?)
        """, (slot, lid, nkey, reason, price, db.now()))
    return jsonify({"ok": True, "slot": slot})


@app.route("/api/compare/remove", methods=["POST"])
def api_compare_remove():
    data = request.get_json(silent=True) or {}
    with db.connect() as conn:
        if data.get("all"):
            conn.execute("DELETE FROM comparison")
        else:
            conn.execute("DELETE FROM comparison WHERE slot_no=?",
                         (data.get("slot_no"),))
    return jsonify({"ok": True})


@app.route("/api/compare/final", methods=["POST"])
def api_compare_final():
    """최종후보 지정 — 최대 3대 (D.4)"""
    data = request.get_json(silent=True) or {}
    slot = data.get("slot_no")
    with db.connect() as conn:
        cur = conn.execute("SELECT is_final FROM comparison WHERE slot_no=?",
                           (slot,)).fetchone()
        if not cur:
            return jsonify({"ok": False, "error": "없는 슬롯"}), 404
        if not cur["is_final"]:
            n = conn.execute(
                "SELECT COUNT(*) c FROM comparison WHERE is_final=1"
            ).fetchone()["c"]
            if n >= COMPARISON["max_final"]:
                return jsonify({
                    "ok": False,
                    "error": f"최종후보는 {COMPARISON['max_final']}대까지"}), 400
        conn.execute("""
            UPDATE comparison SET is_final=?, selected_at=?
             WHERE slot_no=?
        """, (0 if cur["is_final"] else 1, db.now(), slot))
    return jsonify({"ok": True})


@app.route("/api/notify/test", methods=["POST"])
def api_notify_test():
    import notifier
    if not notifier.enabled():
        return jsonify({
            "ok": False,
            "error": "config/.env 에 TELEGRAM_BOT_TOKEN 과 "
                     "TELEGRAM_CHAT_ID 를 넣으십시오"}), 400
    ok, msg = notifier.test()
    return jsonify({"ok": ok, "message": msg}), (200 if ok else 500)


@app.route("/api/report/build", methods=["POST"])
def api_report_build():
    """지금 상태로 리포트를 다시 만든다."""
    from reporter import daily, diagnostic
    try:
        with db.connect() as conn:
            d = latest_snapshot(conn) or db.today()
            p1 = daily.save(conn, d)
            p2 = diagnostic.save(conn, d)
        return jsonify({"ok": True, "files": [p1.name, p2.name]})
    except Exception as e:
        return jsonify({"ok": False, "error": repr(e)}), 500


# ──────────────────────────────────────────────────────────────
# API
# ──────────────────────────────────────────────────────────────
@app.route("/api/summary")
def api_summary():
    with db.connect() as conn:
        if not schema_ready(conn):
            return jsonify({"error": "DB 미초기화. python run.py init"}), 503
        snap = latest_snapshot(conn)
        return jsonify({
            "snapshot": snap,
            "market": [dict(r) for r in conn.execute(
                "SELECT * FROM market_daily WHERE snapshot_date=?",
                (snap,)).fetchall()] if snap else [],
        })


def main() -> int:
    config.ensure_dirs()
    if not config.DB_PATH.exists():
        print("DB 가 없습니다. python run.py init 을 먼저 실행하십시오.")
        return 1
    host, port = config.WEB["host"], config.WEB["port"]
    print("=" * 60)
    print(" car_monitor 대시보드")
    print("=" * 60)
    print(f"  DB   {config.DB_PATH}")
    print(f"  주소  http://{host}:{port}")
    print("  종료  Ctrl+C")
    print("=" * 60)

    # ★ 앱이 뜰 때 오늘 수집이 없으면 자동으로 돌린다 (지시서 4.1)
    #   크론은 PC 가 꺼져 있으면 그냥 지나간다.
    #   '앱을 열 때 확인'이 실제 사용 패턴에 맞다.
    # ★ 프로세스가 죽으면서 DB 에 남은 'running' 을 정리한다.
    #   그대로 두면 수집이 막히고 화면에도 '실행 중'으로 보인다.
    try:
        import scheduler as _sch0
        with db.connect() as _c0:
            n = _sch0.clear_stale(_c0)
        if n:
            print(f"  이전 실행 흔적 {n}건 정리 (프로세스 중단)")
    except Exception as e:
        print(f"  [경고] 상태 정리 실패: {e!r}")

    try:
        import scheduler
        scheduler.start_if_needed(
            auto=config.SCHEDULER.get("auto_start_on_launch", True),
            log_fn=print)
    except Exception as e:
        print(f"  [경고] 스케줄러 기동 실패: {e!r}")

    app.run(host=host, port=port, debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
