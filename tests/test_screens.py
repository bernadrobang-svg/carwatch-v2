# -*- coding: utf-8 -*-
"""10장 화면 시험.

지시서   STEP 93 (공통 규칙) · 97 (목록) · 98 (비교) · 104 (notready)
         105 (데이터 계약) · 107 (화면 검증 V6-01~06)
사용     python3 tests/test_screens.py
"""
from __future__ import annotations

import ast
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from report.screens.build import (  # noqa: E402
    CHIP_AXES, chip, view_compare, view_dashboard, view_dealers, view_listings,
    view_market, view_notready, view_recommend, view_run, view_why,
)
from report.screens.views import ListingFilter  # noqa: E402
from contracts import (  # noqa: E402
    ANONYMOUS, ROLE_ADMIN, ROLE_USER, Account,
)

ADMIN = Account(1, ROLE_ADMIN, "마스터")
USER = Account(2, ROLE_USER, "사용자")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABELS = json.load(open(os.path.join(ROOT, "config", "labels.json"),
                        encoding="utf-8"))
FIN = json.load(open(os.path.join(ROOT, "config", "finance.json"),
                     encoding="utf-8"))
POLICY = json.load(open(os.path.join(ROOT, "config", "scoring.json"),
                        encoding="utf-8"))
DEP = json.load(open(os.path.join(ROOT, "config", "depreciation.json"),
                     encoding="utf-8"))
FAIL: list[str] = []


def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{'  ' + detail if detail else ''}")
    if not ok:
        FAIL.append(name)


def _pipeline():
    from collect.pipeline import run_pipeline
    from tests.test_run import setup

    conn, ctx, ex, _s, _c, _t = setup(total=3)
    run_pipeline(conn, ctx, ex,
                 steps=("S0", "S1", "S2", "S3", "S4", "S5", "S6", "S6a",
                        "S7", "S8", "S8.5", "S9", "S10"))
    return conn, ctx


# ── STEP 93 값 표기 · V6-02 ──────────────────────────────────────────
def test_chip() -> None:
    vl = LABELS["VALUE_LABELS"]
    allowed = set(vl.values())
    cases = ((1, False, "1"), (0, False, "0"), (-1, True, "na"),
             (None, True, "unknown"), (None, False, "unknown"))
    for value, ex, bucket in cases:
        c = chip("spec.hud", value, ex, LABELS)
        check(f"chip value={value} excluded={ex} → {vl[bucket]}",
              c.label.endswith(vl[bucket]), c.label)
        check(f"  필터 링크가 Component 이름을 쓴다",
              "axis=spec.hud" in c.filter_url and f"bucket={bucket}" in c.filter_url,
              c.filter_url)

    check("★ V6-02 — VALUE_LABELS 밖의 문구를 쓰지 않는다",
          all(any(c.label.endswith(v) for v in allowed)
              for c in [chip("spec.hud", v, e, LABELS)
                        for v, e, _ in cases]))
    check("★ 「해당 없음」과 「없음」이 다른 톤",
          chip("spec.hud", -1, True, LABELS).tone
          != chip("spec.hud", 0, False, LABELS).tone)


# ── STEP 97 목록 · V6-04 ─────────────────────────────────────────────
def test_listings() -> None:
    conn, ctx = _pipeline()
    flt = ListingFilter(calc_version=ctx.calc_version)
    rows = view_listings(ADMIN, conn, flt, FIN, ROOT)
    check("목록이 나온다", len(rows) == 3, f"{len(rows)}행")

    r = rows[0]
    check("축 칩 5종", len(r.axis_chips) == len(CHIP_AXES))
    check("★ 전 화면에 VersionStamp (V6-01)",
          r.versions.calc_version == ctx.calc_version)
    check("비용이 목록에도 붙는다",
          r.total_cost_won and r.monthly_won, f"{r.monthly_won}")

    for row in rows:
        if row.grade == "NOT_RATED":
            check("★ V6-04 — NOT_RATED 에 순위 없음", row.rank is None)
            break
    else:
        check("★ V6-04 — 등급이 있으면 순위가 있다",
              all(x.rank for x in rows), str([x.rank for x in rows]))

    hit = view_listings(ADMIN, conn, ListingFilter(
        calc_version=ctx.calc_version, axis="spec.hud", bucket="1"), FIN, ROOT)
    miss = view_listings(ADMIN, conn, ListingFilter(
        calc_version=ctx.calc_version, axis="spec.hud", bucket="0"), FIN, ROOT)
    check("★ 축·버킷 필터가 실제로 거른다",
          len(hit) + len(miss) == len(rows), f"{len(hit)}+{len(miss)}")

    na = view_listings(ADMIN, conn, ListingFilter(
        calc_version=ctx.calc_version, axis="spec.hda", bucket="unknown"),
        FIN, ROOT)
    check("미확정 축(spec.hda)은 unknown 버킷으로 걸린다",
          len(na) == len(rows), f"{len(na)}행")

    rec = view_recommend(ADMIN, conn, flt, FIN, ROOT)
    check("추천에는 E · NOT_RATED 가 없다",
          all(x.grade not in ("E", "NOT_RATED") for x in rec))


# ── STEP 98 비교 · V6-05 ─────────────────────────────────────────────
def test_compare() -> None:
    conn, ctx = _pipeline()
    ids = [r[0] for r in conn.execute(
        "SELECT listing_id FROM core_listing LIMIT 2")]
    cv = view_compare(ADMIN, conn, ids, ctx.calc_version, FIN, POLICY, ROOT)
    check("비교 — 17 Component", len(cv.axes) == 17, f"{len(cv.axes)}축")
    check("셀이 (listing_id, axis) 로 채워진다",
          len(cv.cells) == len(ids) * 17, f"{len(cv.cells)}칸")
    check("같은 버전이면 비교 가능", not cv.version_mismatch)
    check("★ V6-05 — 분모가 같으면 경고 없음", not cv.denominator_mismatch,
          str({r.denominator for r in [
              view_why(ADMIN, conn, i, ctx.calc_version, FIN, POLICY, ROOT)
              for i in ids]}))


# ── STEP 95 · 104 ────────────────────────────────────────────────────
def test_dashboard_notready() -> None:
    conn, ctx = _pipeline()
    dv = view_dashboard(ADMIN, conn, ctx.run_id, ctx.calc_version, FIN, ROOT)
    check("현황 — 차종 통계", bool(dv.target_stats))
    check("★ 주의 항목에 조치가 붙는다",
          all(a.action for a in dv.attention), str([a.kind for a in dv.attention]))
    conn.execute("INSERT INTO meta_field_usage(site,endpoint,json_path,usage,"
                 "reason,first_seen,last_seen) VALUES "
                 "('encar','detail','새필드','unclassified','시험','t','t')")
    conn.commit()
    dv2 = view_dashboard(ADMIN, conn, ctx.run_id, ctx.calc_version, FIN, ROOT)
    check("★ 등록부 미분류가 주의로 뜬다",
          any(a.kind == "unclassified" for a in dv2.attention))
    # ★ hda Gate 가 열려 미확정이 줄었다.  기전을 시험하려면 하나 만든다
    conn.execute("UPDATE result_axis SET excluded=1, value=NULL, "
                 "source='gate_closed' WHERE axis='spec.hda'")
    conn.commit()
    dv3 = view_dashboard(ADMIN, conn, ctx.run_id, ctx.calc_version, FIN, ROOT)
    check("미확정 축도 주의로 뜬다",
          any(a.kind == "undecided" for a in dv3.attention),
          str([a.kind for a in dv3.attention]))

    nr = view_notready(ADMIN, conn, ctx.calc_version, ctx.run_id)
    check("★ notready — 사유와 조치를 낸다",
          bool(nr.reasons) and bool(nr.actions), str(nr.reasons[:1]))

    mv = view_market(ADMIN, conn, "G80_25T", DEP)
    check("시세 — 감가 곡선 6구간", len(mv.curve) == 6)
    check("시세 — 분위수", mv.rows[0].median_won is not None)

    dl = view_dealers(ADMIN, conn)
    check("딜러 목록", bool(dl))
    check("★ 표본 부족 딜러는 점수를 확정 표시하지 않는다 (V3-26)",
          all(d.honesty_score is None for d in dl if not d.sample_sufficient))

    rr = view_run(ADMIN, conn, ctx.run_id, ctx.calc_version)
    check("실행 화면 = L3 리포트", rr.meta.layer == "L3")


# ── V6-03 · V6-06 정적 검사 ──────────────────────────────────────────
def test_static_rules() -> None:
    src = ""
    for name in ("build.py", "views.py"):
        with open(os.path.join(ROOT, "report", "screens", name),
                  encoding="utf-8") as f:
            src += f.read()
    tree = ast.parse(src)
    # 주석·독스트링의 「금지」 서술은 위반이 아니다.  SQL 문자열만 본다
    sql = [n.value for n in ast.walk(tree)
           if isinstance(n, ast.Constant) and isinstance(n.value, str)
           and ("SELECT " in n.value or "FROM " in n.value)]
    check("★ V6-03 — 화면이 raw_* 를 직접 조회하지 않는다",
          not any("raw_" in s for s in sql),
          str([s[:40] for s in sql if "raw_" in s]))

    shown = [n.value for n in ast.walk(tree)
             if isinstance(n, ast.Constant) and isinstance(n.value, str)
             and "SELECT " not in n.value and "FROM " not in n.value]
    check("★ V6-06 — 「판매됨」을 화면 문구로 쓰지 않는다",
          not any("판매됨" in s for s in shown))
    check("gone 은 STATUS_LABELS 를 통해 표기된다",
          "STATUS_LABELS" in src
          and "판매" not in LABELS["STATUS_LABELS"]["gone"],
          LABELS["STATUS_LABELS"]["gone"])

    calls = {n.func.attr for n in ast.walk(tree)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    check("화면이 판정 함수를 호출하지 않는다",
          not {"put", "analyze_listing", "score"} & calls, str(calls & {"put"}))


# ── STEP 105 · 126 화면과 Account ────────────────────────────────────
def test_account() -> None:
    from errors import PolicyError

    from report.screens.build import view_run, view_watch, viewer_state

    conn, ctx = _pipeline()
    flt = ListingFilter(calc_version=ctx.calc_version)

    check("★ 판정은 계정과 무관하다 — 같은 차는 누가 봐도 같은 등급",
          [r.grade for r in view_listings(ANONYMOUS, conn, flt, FIN, ROOT)]
          == [r.grade for r in view_listings(ADMIN, conn, flt, FIN, ROOT)])

    v = viewer_state(ANONYMOUS)
    check("비로그인 — 조회만", not v.can_watch and not v.can_admin)
    check("일반 — 관심 등록 가능 · 관리 불가",
          viewer_state(USER).can_watch and not viewer_state(USER).can_admin)
    check("관리자 — 전부", viewer_state(ADMIN).can_admin)

    for who in (ANONYMOUS, USER):
        try:
            view_run(who, conn, ctx.run_id, ctx.calc_version)
            check(f"★ 실행 화면은 관리자만 — {who.role} 차단", False)
        except PolicyError:
            check(f"★ 실행 화면은 관리자만 — {who.role} 차단", True)
    try:
        view_watch(ANONYMOUS, conn, FIN, ctx.calc_version, ROOT)
        check("★ 비로그인은 관심 목록을 못 본다", False)
    except PolicyError:
        check("★ 비로그인은 관심 목록을 못 본다", True)
    check("일반은 관심 목록 조회 가능 (비어 있어도 예외가 아니다)",
          view_watch(USER, conn, FIN, ctx.calc_version, ROOT) == [])

    conn.execute("UPDATE result_axis SET excluded=1, value=NULL, "
                 "source='gate_closed' WHERE axis='spec.hda'")
    conn.commit()
    dv = view_dashboard(ADMIN, conn, ctx.run_id, ctx.calc_version, FIN, ROOT)
    check("★ 화면에 로그인 상태 · 역할이 나온다",
          dv.viewer.role == ROLE_ADMIN and dv.viewer.display_name == "마스터")
    check("주의 항목은 관리자만 — 조치가 관리자 행동이다", bool(dv.attention),
          str([a.kind for a in dv.attention]))
    dv2 = view_dashboard(USER, conn, ctx.run_id, ctx.calc_version, FIN, ROOT)
    check("일반에게는 주의 항목이 없다", dv2.attention == [])


if __name__ == "__main__":
    print("10장 화면 시험")
    test_chip()
    test_listings()
    test_compare()
    test_dashboard_notready()
    test_account()
    test_static_rules()
    print()
    print("결과:", "통과" if not FAIL else "실패 — " + " / ".join(FAIL))
    sys.exit(1 if FAIL else 0)
