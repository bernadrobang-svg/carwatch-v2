# -*- coding: utf-8 -*-
"""5장 수집 순서 시험.

지시서   STEP 47 (단계) · 48 (선행) · 50a (재처리 결정표) · 51 (재조회)
         52 (재개) · 53 (expected · 자동 점검 6종)
사용     python3 tests/test_pipeline.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contracts import RunContext  # noqa: E402
from collect.pipeline import (  # noqa: E402
    REPROCESS_TABLE,
    run_pipeline,
    build_run_context_fields,
    expected_for,
    halt_if,
    precheck,
    reprocess_plan,
    resume_point,
    should_refetch,
    stale_rows,
    step_report,
)
from store.raw import open_db  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAIL: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{'  ' + detail if detail else ''}")
    if not ok:
        FAIL.append(name)


def db():
    return open_db(os.path.join(tempfile.mkdtemp(), "t.db"),
                   os.path.join(ROOT, "sql", "ddl"))


# ── STEP 53 expected ─────────────────────────────────────────────────
def test_expected() -> None:
    check("S1 은 collect_group 수 × 페이지",
          expected_for("S1", collect_group_count=8, page_count=10) == 80)
    check("★ S2 는 collect_group × 1 (Badge 요청은 같은 결과)",
          expected_for("S2", collect_group_count=8) == 8)
    check("S5 는 매물 × 엔드포인트 4종 (진단 포함)",
          expected_for("S5", active_listings=208, endpoint_kinds=4) == 832)
    check("S9 는 매물 × Component 17",
          expected_for("S9", active_listings=100, components=17) == 1700)


# ── STEP 53 자동 점검 6종 ────────────────────────────────────────────
def test_halt() -> None:
    ok = step_report("S5", "G80_25T", 100,
                     {"ok": 90, "empty": 5, "not_found": 3, "error": 2}, 0, 1.0)
    r = halt_if(ok, raw_rows=100)
    check("정상 → 통과", not r.halted, r.halt_reason or "")

    v1 = step_report("S5", None, 208, {"ok": 76}, 0, 1.0)
    r = halt_if(v1, raw_rows=76)
    check("v1 사고 (208 중 76) → 중단", r.halted and "⑥" in r.halt_reason)

    rj = step_report("S1", None, 10, {"ok": 10}, 1, 1.0)
    check("거부 1건 → 중단", halt_if(rj, 10).halted)

    z = step_report("S1", None, 10, {"error": 10}, 0, 1.0)
    check("ok 0건 → 중단", halt_if(z, 10).halted)

    miss = step_report("S1", None, 10, {"ok": 10}, 0, 1.0)
    check("⑤ 저장 누락 → 중단", halt_if(miss, raw_rows=7).halted)


# ── STEP 50a 재처리 결정표 ───────────────────────────────────────────
def test_reprocess() -> None:
    check("결정표 9행", len(REPROCESS_TABLE) == 9, f"{len(REPROCESS_TABLE)}행")
    check("배점 변경 → S10 만 · 재수집 없음",
          reprocess_plan("scoring").steps == ("S10",)
          and not reprocess_plan("scoring").refetch)
    check("사전 변경 → S9·S10", reprocess_plan("dictionary").steps == ("S9", "S10"))
    check("파싱 규칙 → S6부터 · 재수집 없음",
          reprocess_plan("parse_rule").steps[0] == "S6"
          and not reprocess_plan("parse_rule").refetch)
    check("응답 형태 변경만 전면 재수집",
          reprocess_plan("site_response_shape").refetch
          and reprocess_plan("site_response_shape").steps[0] == "S1")
    check("계수 보정 → S8.5 부터",
          reprocess_plan("coefficient").steps[0] == "S8.5")
    from errors import ValidationError as _ValidationError

    try:
        reprocess_plan("그냥_처음부터")
        check("표 밖의 사유 → 거부", False)
    except _ValidationError:
        # ★ 입력 오류다 — 400 으로 나가야 한다.  ValueError 면 500 이 된다 (C-2)
        check("표 밖의 사유 → 거부", True)


# ── STEP 51 재조회 ───────────────────────────────────────────────────
def test_refetch() -> None:
    check("not_requested · error 만 재조회",
          [should_refetch(s) for s in
           ("not_requested", "error", "empty", "not_found", "ok")]
          == [True, True, False, False, False])


# ── STEP 48 선행 조건 ────────────────────────────────────────────────
def test_precheck() -> None:
    conn = db()
    ok, why = precheck(conn, "S1", done=set())
    check("S1 은 S0 을 요구한다", not ok and "S0" in why, why)
    ok, _ = precheck(conn, "S2", done=set())
    check("S2 는 독립 — 선행 없음", ok)

    conn.execute("INSERT INTO raw_response_reject"
                 "(site,endpoint,request_url,reject_reason,fetched_at)"
                 " VALUES ('encar','list','u','키 없음','t')")
    conn.commit()
    ok, why = precheck(conn, "S3", done={"S1", "S2"})
    check("거부 1건이면 S3 착수 금지", not ok and "거부" in why, why)

    ok, why = precheck(conn, "S5", done={"S4"})
    check("active 매물 0건이면 S5 착수 금지", not ok, why)

    # ★ 부위명(panel)은 표시 전용이다.  판정을 막지 않는다 (STEP 44) —
    #   막으면 새 부위명 하나에 전 매물이 멈춘다 (실측 08-15)
    conn.execute("INSERT INTO dict_enum"
                 "(site,axis,value,display,count_seen,status,"
                 "source_endpoint,dict_version,first_seen,last_seen)"
                 " VALUES "
                 "('encar','panel','x','x',1,'pending','inspection',"
                 "'d1','t','t')")
    conn.commit()
    ok, why = precheck(conn, "S9", done={"S6", "S6a", "S8", "S8.5"})
    check("표시 전용 축 pending 은 S9 를 막지 않는다", ok, why)

    conn.execute("INSERT INTO dict_enum"
                 "(site,axis,value,display,count_seen,status,"
                 "source_endpoint,dict_version,first_seen,last_seen)"
                 " VALUES "
                 "('encar','panel_rank','RANK_Z','RANK_Z',1,'pending',"
                 "'inspection','d1','t','t')")
    conn.commit()
    ok, why = precheck(conn, "S9", done={"S6", "S6a", "S8", "S8.5"})
    check("판정 축 pending 은 S9 착수 금지",
          not ok and "panel_rank" in why, why)

    # ★ 컬럼을 적는다.  VALUES 만 쓰면 컬럼이 늘 때마다 시험이 먼저 깨진다
    conn.execute(
        "INSERT INTO audit_validation"
        "(run_id,phase,code,target_key,expected,actual,passed,severity,"
        " samples,checked_at) VALUES "
        "('r1','V1','V1-04','G80','0','1',0,'fatal',NULL,'t')")
    conn.commit()
    ok, why = precheck(conn, "S12", done={"S10", "S11"})
    check("fatal 있으면 S12 착수 금지", not ok, why)


# ── STEP 52 재개 · 버전 ──────────────────────────────────────────────
def test_resume_and_version() -> None:
    conn = db()
    check("이력 없으면 재개점 없음", resume_point(conn, "r1") is None)
    for kind, sid in (("list", None), ("detail", "42473896")):
        conn.execute(
            "INSERT INTO audit_request(run_id,site,kind,source_id,url,status,"
            "requested_at) VALUES ('r1','encar',?,?,'u','ok','t')", (kind, sid))
    conn.commit()
    rp = resume_point(conn, "r1")
    check("마지막 성공에서 좌표 산출",
          rp.step == "S5" and rp.source_id == "42473896" and rp.endpoint == "detail",
          str(rp))

    conn.execute("INSERT INTO core_listing(site,source_id,status,first_seen,"
                 "last_seen,row_status,parse_version) VALUES "
                 "('encar','1','active','t','t','ok','p1')")
    conn.commit()
    check("버전 낮은 행만 고른다",
          stale_rows(conn, "parse_version", "p2") == [1]
          and stale_rows(conn, "parse_version", "p1") == [])

    h = build_run_context_fields(os.path.join(ROOT, "config"))
    check("설정 해시 3종", len(h) == 3 and all(len(v) == 16 for v in h.values()))
    h2 = build_run_context_fields(os.path.join(ROOT, "config"))
    check("같은 설정이면 같은 해시", h == h2)


# ── STEP 49 · 50 실행 순서 ───────────────────────────────────────────
def test_run_pipeline() -> None:
    from datetime import datetime, timezone

    conn = db()
    ctx = RunContext("r1", "encar", datetime(2026, 8, 10, tzinfo=timezone.utc),
                     "p1", "d1", "c1", "h", "h", "h", [])

    def good(step):
        def _f(conn, ctx):
            return step_report(step, None, 1, {"ok": 1}, 0, 0.1), 1
        return _f

    def bad(conn, ctx):
        return step_report("S2", None, 10, {"ok": 3}, 0, 0.1), 3

    ex = {s: good(s) for s in ("S0", "S1", "S2", "S3")}
    reps = run_pipeline(conn, ctx, ex, steps=("S0", "S1", "S2", "S3"))
    check("4단계 전부 실행", len(reps) == 4 and not any(r.halted for r in reps))

    conn2 = db()
    ex2 = dict(ex)
    ex2["S1"] = bad
    reps = run_pipeline(conn2, ctx, ex2, steps=("S0", "S1", "S2", "S3"))
    check("중단되면 이후 단계를 실행하지 않는다",
          len(reps) == 2 and reps[-1].halted, str(len(reps)))

    n = conn2.execute("SELECT COUNT(*) FROM audit_validation").fetchone()[0]
    check("StepReport 는 테이블에 남는다 (화면 출력만 하지 않는다)", n == 2, f"{n}행")

    conn3 = db()
    reps = run_pipeline(conn3, ctx, {}, steps=("S0",))
    check("실행기 미등록도 조용히 넘어가지 않는다", reps[0].halted)


# ── STEP 132 재계산 지시 ─────────────────────────────────────────────
def test_recalc() -> None:
    from errors import PolicyError
    from collect.pipeline import (
        CLI_ONLY_REASONS, ORIGIN_CLI, ORIGIN_WEB, from_step_for, plan_recalc,
        web_reasons,
    )

    check("★ 관리자는 단계를 고르지 않는다 — 결정표가 준다",
          from_step_for("scoring") == "S10"
          and from_step_for("dictionary") == "S9"
          and from_step_for("parse_rule") == "S6")
    check("재계산이 필요 없는 사유는 None", from_step_for("labels") is None)

    check("★ 전면 재수집만 CLI 전용", CLI_ONLY_REASONS == {"site_response_shape"},
          str(CLI_ONLY_REASONS))
    check("웹 목록에 전면 재수집이 없다",
          "site_response_shape" not in web_reasons(), str(web_reasons()))
    check("개별 매물 재수집은 웹에서 가능 (전면이 아니다)",
          "listing_updated" in web_reasons() and "raw_missing" in web_reasons())

    conn = db()
    try:
        plan_recalc(conn, "site_response_shape", "all", ORIGIN_WEB)
        check("★ V10-13 — 웹에서 전면 재수집 큐잉 차단", False)
    except PolicyError as e:
        check("★ V10-13 — 웹에서 전면 재수집 큐잉 차단",
              "CLI" in str(e) and "--full" in str(e))
    p = plan_recalc(conn, "site_response_shape", "all", ORIGIN_CLI)
    check("CLI 에서는 허용", p["from_step"] == "S1" and p["refetch"])

    p = plan_recalc(conn, "scoring", "all", ORIGIN_WEB)
    check("배점 변경은 S10 만 · 재수집 없음",
          p["steps"] == ["S10"] and not p["refetch"])


def test_pii_orphan() -> None:
    from validate.base import run_phase

    conn = db()
    try:
        conn.execute("INSERT INTO core_pii(listing_id,plate_no,created_at) "
                     "VALUES (999,'12가3456','t')")
        check("FK 가 고아를 1차로 막는다", False)
    except Exception:
        check("FK 가 고아를 1차로 막는다", True)

    # FK 가 꺼진 환경·마이그레이션에서도 잡아야 한다
    conn.rollback()
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("INSERT INTO core_pii(listing_id,plate_no,created_at) "
                 "VALUES (999,'12가3456','t')")
    conn.commit()

    class _V:
        run_id = "r1"
        policy_raw = json.load(open(os.path.join(ROOT, "config",
                                                 "scoring.json"),
                                    encoding="utf-8"))
        depreciation = {}

    res = run_phase(conn, _V(), "V2")
    v217 = [r for r in res if r.check.code == "V2-17"][0]
    check("★ V2-17 — 대리키 없는 PII 고아 행을 잡는다", not v217.passed,
          v217.actual)
    check("조치가 붙어 있다", "flush_pii" in v217.check.action)


# ── 예외가 새어 나가지 않는다 (STEP 90) ──────────────────────────────
def test_exception_becomes_halt() -> None:
    from datetime import datetime, timezone

    from collect.pipeline import run_step
    from errors import ValidationError

    conn = db()

    def boom(_conn, _ctx):
        raise ValidationError("panel_rank 에 새 값: 'RANK_Z'", step="STEP 41")

    ctx = RunContext("r1", "encar", datetime(2026, 8, 10, tzinfo=timezone.utc),
                     "p1", "d1", "c1", "h", "h", "h", [])
    rep = run_step(conn, ctx, "S3", {"S0", "S1", "S2"}, {"S3": boom})
    check("★ 도메인 예외 → 중단 리포트 (죽지 않는다)",
          rep.halted and "RANK_Z" in (rep.halt_reason or ""), rep.halt_reason)
    saved = conn.execute(
        "SELECT actual FROM audit_validation WHERE code='STEP53-S3'").fetchone()
    check("★ 중단도 기록에 남는다", saved is not None)


def test_fixed_enum_bootstrap() -> None:
    """★ 첫 수집에 사전이 비어 있어도 halt 축이 멈추지 않는다 (STEP 41)."""
    from store.dictionary import upsert_enum
    from tools.build_dict import build_dict

    conn = db()
    # ★ S3 이 실제로 부르는 경로로 시험한다.
    #   seed_fixed_enums 를 직접 부르면 「build_dict 가 부르는가」를 못 잡는다
    build_dict(conn, "encar", "d1", "t")
    rows = dict(conn.execute(
        "SELECT axis, COUNT(*) FROM dict_enum GROUP BY axis").fetchall())
    check("★ build_dict(S3) 가 고정 집합을 먼저 심는다",
          rows.get("panel_rank") == 5 and rows.get("panel_status") == 4
          and rows.get("accident_type") == 3, str(rows))
    build_dict(conn, "encar", "d1", "t")
    again = dict(conn.execute(
        "SELECT axis, COUNT(*) FROM dict_enum GROUP BY axis").fetchall())
    check("재실행해도 늘지 않는다", again == rows, str(again))
    check("★ 고정 집합 안의 값은 통과",
          upsert_enum(conn, "encar", "panel_rank", "RANK_B", "RANK_B", 1,
                      "inspection", "d1", "t") == "seen")
    try:
        upsert_enum(conn, "encar", "panel_rank", "RANK_Z", "RANK_Z", 1,
                    "inspection", "d1", "t")
        check("★ 목록 밖 새 값은 여전히 중단", False)
    except Exception as e:
        check("★ 목록 밖 새 값은 여전히 중단", "RANK_Z" in str(e))


# ── STEP 50a S4 봉투 범위 ────────────────────────────────────────────
def test_envelope_scope() -> None:
    from collect.pipeline import (
        ENVELOPE_ALL, ENVELOPE_THIS_RUN, envelope_scope,
    )

    check("★ 신규 수집은 이번 실행 봉투만",
          envelope_scope("listing_updated") == ENVELOPE_THIS_RUN
          and envelope_scope("raw_missing") == ENVELOPE_THIS_RUN)
    check("★ 파싱 규칙 변경은 전체 — 그것이 재파싱의 목적이다",
          envelope_scope("parse_rule") == ENVELOPE_ALL
          and envelope_scope("site_response_shape") == ENVELOPE_ALL)
    check("사유가 없으면 신규 수집으로 본다",
          envelope_scope(None) == ENVELOPE_THIS_RUN)
    from errors import ValidationError as _VE

    try:
        envelope_scope("없는사유")
        check("표에 없는 사유는 거부", False)
    except _VE:
        # ★ 입력 오류다 — 400 으로 나가야 한다 (C-2)
        check("표에 없는 사유는 거부", True)


if __name__ == "__main__":
    print("5장 수집 순서 시험")
    test_expected()
    test_halt()
    test_reprocess()
    test_refetch()
    test_precheck()
    test_resume_and_version()
    test_run_pipeline()
    test_recalc()
    test_pii_orphan()
    test_envelope_scope()
    test_exception_becomes_halt()
    test_fixed_enum_bootstrap()
    print()
    print("결과:", "통과" if not FAIL else "실패 — " + " / ".join(FAIL))
    sys.exit(1 if FAIL else 0)
