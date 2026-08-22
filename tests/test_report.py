# -*- coding: utf-8 -*-
"""9장 리포트 시험.

지시서   STEP 90 (4층) · 91 (표시 규칙 · 금융) · 92 (내보내기)
사용     python3 tests/test_report.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyze.axes import COMPONENTS  # noqa: E402
from report.exports.export import export, filename  # noqa: E402
from report.finance import build_finance, monthly_payment  # noqa: E402
from report.render import (  # noqa: E402
    render_halt, render_listing, render_run, render_target,
)
from report.views import ReportMeta, display_points, display_value  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABELS = json.load(open(os.path.join(ROOT, "config", "labels.json"),
                        encoding="utf-8"))
FIN = json.load(open(os.path.join(ROOT, "config", "finance.json"),
                     encoding="utf-8"))
POLICY = json.load(open(os.path.join(ROOT, "config", "scoring.json"),
                        encoding="utf-8"))
FAIL: list[str] = []


def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{'  ' + detail if detail else ''}")
    if not ok:
        FAIL.append(name)


# ── STEP 91 금융 ─────────────────────────────────────────────────────
def test_finance() -> None:
    # 지시서 STEP 91 표 (취득세 7% · 부대 0)
    for listed, tax, vdown, principal, monthly in (
        (32000000, 2240000, 12760000, 19240000, 447000),
        (34700000, 2429000, 12571000, 22129000, 515000),
        (35000000, 2450000, 12550000, 22450000, 522000),
        (43780000, 3064600, 11935400, 31844600, 741000),
    ):
        f = build_finance(listed, FIN, "GRANDEUR_LPG")
        man = listed // 10000
        check(f"검산 {man}만 — 취득세",
              abs(f.acquisition_cost_won - tax) <= 1, f"{f.acquisition_cost_won:,}")
        check(f"검산 {man}만 — 차값 선납",
              abs(f.vehicle_down_won - vdown) <= 1, f"{f.vehicle_down_won:,}")
        check(f"검산 {man}만 — 월 {monthly // 10000}.{monthly % 10000 // 1000}만",
              abs(f.monthly_payment_won - monthly) < 5000,
              f"{f.monthly_payment_won:,}")
        check(f"검산 {man}만 — 차값 선납 + 원금 == 표시가",
              f.vehicle_down_won + f.loan_principal_won == listed)
        check(f"검산 {man}만 — 초기 현금은 현금 상한 고정",
              f.down_payment_won == FIN["cash_limit"])

    # ★ 배분식과 가산식은 대수적으로 같다 —
    #   표시가 − (선납금 − 부대비용)  ==  (표시가 + 부대비용) − 선납금
    #   갈리는 곳은 부대비용 > 현금 상한 인 경계뿐이다
    f = build_finance(34700000, FIN, "GRANDEUR_LPG")
    same = 34700000 + f.acquisition_cost_won - FIN["cash_limit"]
    check("★ 배분식 == 가산식 (부대비용 ≤ 선납금 구간)",
          f.loan_principal_won == same, f"{f.loan_principal_won:,} / {same:,}")

    # ★ 표시가에서 선납금을 그냥 빼면 부대비용만큼 어긋난다
    naive = monthly_payment(34700000 - FIN["cash_limit"],
                            FIN["loan_rate_annual"], FIN["loan_months"])
    check("★ 표시가 − 선납금 은 틀린다 (부대비용 누락)",
          f.monthly_payment_won - naive > 40000,
          f"{f.monthly_payment_won:,} vs {naive:,}")

    f = build_finance(50000000, FIN, "MODEL_Y")
    check("전기차는 취득세 감면 (ev_tax_exempt)", f.acquisition_cost_won == 0)

    f = build_finance(10000000, FIN, "G80_25T")
    check("표시가 + 부대비용 <= 선납금 → 전액 현금",
          f.cash_only and f.loan_principal_won == 0 and f.monthly_payment_won == 0)

    # ★ 개정 400 — 부대비용이 현금 상한을 넘어도 「부족액」을 내지 않는다.
    #   화면은 「전액 현금」인가 아닌가 둘뿐이다 (V11-151)
    fin2 = dict(FIN, fee_transfer=20000000)
    f = build_finance(30000000, fin2, "G80_25T")
    check("★ 부대비용 > 현금 상한 — 차값 선납 0 · 전액 현금 아님",
          f.vehicle_down_won == 0 and not f.cash_only
          and f.loan_principal_won == 30000000,
          f"{f.loan_principal_won:,}")
    check("★ 부족액 칸이 없다 (개정 400)",
          not hasattr(f, "shortfall_won"))


# ── STEP 91 값 표시 대조표 ───────────────────────────────────────────
def test_display() -> None:
    vl = LABELS["VALUE_LABELS"]
    check("value=1 → 있음", display_value(1, False, vl) == "있음")
    check("value=0 → 없음", display_value(0, False, vl) == "없음")
    check("★ -1 + excluded → 해당 없음",
          display_value(-1, True, vl) == "해당 없음")
    check("★ NULL + excluded → 미확인",
          display_value(None, True, vl) == "확인 불가")
    check("★ 「해당 없음」과 「없음」이 다른 기호",
          display_value(-1, True, vl) != display_value(0, False, vl))
    check("★ 제외 축을 0점으로 쓰지 않는다",
          display_points(0, True, 20) == "—/20"
          and display_points(0, False, 20) == "0/20")


# ── 4층 리포트 ───────────────────────────────────────────────────────
def _pipeline():
    from collect.pipeline import run_pipeline
    from tests.test_run import Clock, setup  # noqa: F401

    conn, ctx, ex, _stub, _cfg, _tg = setup(total=3)
    reps = run_pipeline(conn, ctx, ex,
                        steps=("S0", "S1", "S2", "S3", "S4", "S5", "S6", "S6a",
                               "S7", "S8", "S8.5", "S9", "S10"))
    return conn, ctx, reps


def test_layers() -> None:
    conn, ctx, reps = _pipeline()
    lid = conn.execute("SELECT listing_id FROM core_listing LIMIT 1").fetchone()[0]

    v = render_listing(conn, lid, ctx.calc_version, FIN, POLICY, ROOT)
    check(f"L1 — {len(COMPONENTS)} Component 전건",
          len(v.axes) == len(COMPONENTS), f"{len(v.axes)}축")
    check("★ 축마다 source · prio 를 낸다",
          all(a.source and a.prio for a in v.axes))
    check("L1 에 비용이 붙는다", v.finance is not None)
    # ★ hda Gate 가 열려 미확정이 줄었다.  기전을 시험하려면 하나 만든다
    conn.execute("UPDATE result_axis SET excluded=1, value=NULL, "
                 "source='gate_closed' WHERE axis='spec.options'")
    conn.commit()
    v2 = render_listing(conn, v.listing_id, ctx.calc_version, FIN, POLICY,
                        ROOT)
    check("★ 미확정 항목을 숨기지 않는다", bool(v2.pending_items),
          str(v2.pending_items))
    check("버전을 함께 낸다", v.versions.calc_version == ctx.calc_version)

    tr = render_target(conn, "G80_25T", ctx.run_id, ctx.calc_version, FIN,
                       POLICY, root=ROOT)
    check("L2 — *_status 5종 × 컬럼 4개",
          set(tr.collect.status_counts) == {"detail", "inspection", "record",
                                            "diagnosis"}
          and all(len(c) == 5 for c in tr.collect.status_counts.values()))
    check("★ 값 종류 수를 낸다", all(a.distinct_values >= 0 for a in tr.axes))
    check("값 종류 1이면 경고", any("값 종류" in w for w in tr.warnings),
          str(tr.warnings[:2]))

    rr = render_run(conn, ctx.run_id, ctx.calc_version)
    check("L3 — 등록부 미분류 건수를 낸다",
          rr.unclassified_count >= 0, str(rr.unclassified_count))
    check("L3 — 사전 변동", rr.dict_changes.confirmed >= 0)


def test_halt_layer() -> None:
    from validate.base import gate, run_phase

    conn, ctx, reps = _pipeline()

    class _V:
        run_id = ctx.run_id
        policy_raw = POLICY
        depreciation = {}

    # ★ 외부 데이터 성격은 이제 warn 이라 gate 에 안 걸린다 (STEP 54).
    #   L0 구조를 시험하려면 코드 결함 성격을 하나 만든다
    conn.execute("UPDATE meta_field_usage SET core_column=NULL "
                 "WHERE usage='in_use'")
    conn.commit()
    blocked = gate(run_phase(conn, _V(), "V4"))
    rep = render_halt(conn, ctx.run_id, ctx.calc_version, blocked, reps,
                      artifacts=["config/field_usage.suggested.json"])
    check("L0 — fatal 만 담는다", bool(rep.failures))
    check("★ 조치가 Check 에 미리 정해져 있다",
          all(rep.actions.get(r.check.code) for r in rep.failures),
          str(list(rep.actions.values())[:1]))
    # ★ 낱말 목록으로 보면 새 조치가 나올 때마다 시험이 깨진다.
    #   「무엇을 한다」로 끝나는가 — 동사형인지를 본다
    import re as _re

    bad = [a for a in rep.actions.values()
           if not _re.sub(r"\s*\([^)]*\)\s*$", "", a).rstrip(" .").endswith(
               ("다", "라", "오"))
           or "해소" in a or "조치하" in a]
    check("★ 조치는 사람이 할 행동으로 쓴다 (「해소하십시오」가 아니다)",
          not bad, str(bad[:2]))
    check("★ 진행분을 낸다 — 처음부터 다시 도는 것이 아니다",
          len(rep.completed_steps) >= 10, f"{len(rep.completed_steps)}단계")
    check("생성물 경로를 함께 낸다", rep.artifacts)

    md = export(rep, "md").content.decode("utf-8")
    check("L0 md — 사유·조치·진행분",
          "## 사유" in md and "## 조치" in md and "진행분" in md)


# ── STEP 92 내보내기 ─────────────────────────────────────────────────
def test_export() -> None:
    conn, ctx, _reps = _pipeline()
    lid = conn.execute("SELECT listing_id FROM core_listing LIMIT 1").fetchone()[0]
    v = render_listing(conn, lid, ctx.calc_version, FIN, POLICY, ROOT)

    m1 = ReportMeta(ctx.run_id, "L1", "encar", v.target_key,
                    ctx.calc_version, None)
    md = export(v, "md", LABELS, meta=m1)
    check("md 파일명 규격",
          md.filename.endswith(f"_{ctx.calc_version}.md")
          and "_L1_" in md.filename, md.filename)
    body = md.content.decode("utf-8")
    # ★ 개정 325 — 「확인 안 됨」은 excluded 가 아니라 0점이다.
    #   그래도 「몇 점 만점 중 몇 점」은 나와야 한다
    check("★ 축이 「점수/배점」으로 나온다", "/" in body and "calc=" in body)
    check("버전이 본문에 있다", "calc=" in body)

    cs = export([v], "csv", meta=m1).content.decode("utf-8")
    # ★★ 배점 숫자를 박지 않는다 — 개정 428 에서 전부 바뀌었다.  config 를 본다
    # ★ COMPONENTS 는 축 **이름 목록**이다 (dict 가 아니다).  배점은 policy 가 준다
    _cap = m1.policy.comp if hasattr(m1, "policy") else None
    if _cap is None:
        import json as _j
        with open(os.path.join(ROOT, "config", "scoring.json"),
                  encoding="utf-8") as _f:
            _c = _j.load(_f)["components"]

            def _cap(name):
                one = _c[name]
                return one if isinstance(one, (int, float)) \
                    else one.get("points", 0)
    check("★ csv 헤더에 배점을 표기한다",
          f"value.budget({_cap('value.budget'):g})" in cs
          and f"taste.hud({_cap('taste.hud'):g})" in cs,
          cs.splitlines()[0][:60])

    js = json.loads(export(v, "json", meta=m1).content.decode("utf-8"))
    check("json 에 VersionStamp 포함", "versions" in js)
    check("★ 화면 문구가 아니라 값과 코드로 낸다",
          all(isinstance(a["value"], (int, type(None)))
              and isinstance(a["axis"], str) for a in js["axes"])
          and not any("있음" in str(a["value"]) for a in js["axes"]))

    meta = ReportMeta("20260810T0930", "L2", "encar", "KOLEOS_HEV", "c3", None)
    check("파일명은 ReportMeta 에서 나온다",
          filename(meta, "md") == "20260810T0930_L2_KOLEOS_HEV_c3.md",
          filename(meta, "md"))
    check("target_key 가 없으면 ALL",
          filename(ReportMeta("r", "L3", "encar", None, "c3", None), "md")
          == "r_L3_ALL_c3.md")


if __name__ == "__main__":
    print("9장 리포트 시험")
    test_finance()
    test_display()
    test_layers()
    test_halt_layer()
    test_export()
    print()
    print("결과:", "통과" if not FAIL else "실패 — " + " / ".join(FAIL))
    sys.exit(1 if FAIL else 0)
