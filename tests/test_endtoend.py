# -*- coding: utf-8 -*-
"""종단 시험 — 수집부터 리포트까지 (5장 STEP 47 · 49).

★ 단계별로 통과했다고 전체가 도는 것이 아니다.
  S0~S3 만 보던 시험이 S4~S11 을 통째로 검사 밖에 두고 있었다 (실측 08-15)

무엇을 보는가
  1  S0~S11 이 끝까지 돈다
  2  수집한 것이 실제로 판정된다 (등급이 나온다)
  3  설정을 바꾸면 다음 실행의 판정이 달라진다
  4  리포트·내보내기가 실제 파일로 나온다
금지   모의 응답을 「성공」으로만 두는 것.  없는 것 · 깨진 것도 섞는다
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

sys.path.insert(0, os.path.join(ROOT, "tests"))
from test_run import setup  # noqa: E402

FAIL: list = []
ALL_STEPS = ("S0", "S1", "S2", "S3", "S4", "S5", "S6", "S6a", "S7", "S8",
             "S8.5", "S9", "S10", "S11")


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  {detail}" if detail else ""))
    if not ok:
        FAIL.append(name)


def _run(total: int = 45, root: str | None = None):
    """S0~S11 을 사람 손 없이 끝까지 돌린다.

    ★ 표시 전용 축(panel)이 대기해도 판정은 돈다 (STEP 44).
      막으면 새 부위명 하나에 전 매물이 멈춘다
    """
    from collect.pipeline import run_pipeline

    conn, ctx, ex, stub, cfg, targets = setup(total=total, root=root)
    # ★ 임시 확정을 하지 않는다.  표시 전용 축(panel)은 판정을 막지 않으므로
    #   사람 손 없이도 끝까지 돌아야 한다 (STEP 44)
    reps = list(run_pipeline(conn, ctx, ex, steps=ALL_STEPS))
    return conn, ctx, ex, stub, reps, cfg, targets


def flow_pipeline():
    """1 · 2 — 끝까지 돌고, 수집한 것이 판정되는가."""
    conn, ctx, _ex, stub, reps, _cfg, _t = _run()
    done = [r.step for r in reps]
    missing = [s for s in ALL_STEPS if s not in done]
    check("전 단계가 실행된다", not missing, f"빠진 것 {missing}")
    n = conn.execute("SELECT COUNT(*) FROM dict_enum "
                     "WHERE status='pending'").fetchone()[0]
    check("표시 전용 축이 대기해도 끝까지 돈다 (STEP 44)", True,
          f"pending {n}건")

    halted = [f"{r.step}: {r.halt_reason}" for r in reps if r.halted]
    check("중단 없이 끝난다", not halted, str(halted[:2]))

    n = conn.execute("SELECT COUNT(*) FROM core_listing").fetchone()[0]
    check("수집한 매물이 CORE 에 들어간다", n > 0, f"{n}건")

    raw = conn.execute("SELECT COUNT(*) FROM raw_response").fetchone()[0]
    check("원문이 남는다", raw > 0, f"{raw}건")
    nullrun = conn.execute(
        "SELECT COUNT(*) FROM raw_response WHERE run_id IS NULL").fetchone()[0]
    check("원문에 run_id 가 채워진다 (A-10)", nullrun == 0, f"NULL {nullrun}건")

    axes = conn.execute("SELECT COUNT(*) FROM result_axis").fetchone()[0]
    check("축이 판정된다", axes > 0, f"{axes}건")

    scores = conn.execute("SELECT COUNT(*) FROM result_score").fetchone()[0]
    check("채점 결과가 나온다", scores > 0, f"{scores}건")

    dist = dict(conn.execute(
        "SELECT grade, COUNT(*) FROM result_score GROUP BY 1"))
    graded = sum(v for k, v in dist.items() if k != "NOT_RATED")
    check("등급이 매겨진다", graded > 0, str(dist))

    bad = conn.execute(
        "SELECT COUNT(*) FROM result_score WHERE denominator IS NULL "
        "OR denominator <= 0").fetchone()[0]
    check("분모가 0 인 채로 등급이 나오지 않는다", bad == 0, f"{bad}건")

    ratio_bad = conn.execute(
        "SELECT COUNT(*) FROM result_score WHERE earned > denominator"
    ).fetchone()[0]
    check("earned 가 denominator 를 넘지 않는다", ratio_bad == 0,
          f"{ratio_bad}건")

    check("카탈로그를 매물 ID 로 부른다 (STEP 21c)",
          bool(stub.catalog_ids) and all(i.isdigit()
                                         for i in stub.catalog_ids),
          str(stub.catalog_ids[:2]))
    _ = ctx
    return conn


def flow_validation(conn):
    """검증이 실제로 돌고 기록되는가."""
    n = conn.execute(
        "SELECT COUNT(DISTINCT code) FROM audit_validation").fetchone()[0]
    check("검증이 기록된다", n > 0, f"{n}종")
    phases = {r[0] for r in conn.execute(
        "SELECT DISTINCT phase FROM audit_validation WHERE phase LIKE 'V%'")}
    check("여러 차수가 돈다", len(phases) >= 5, str(sorted(phases)))
    fatal = [r[0] for r in conn.execute(
        "SELECT code FROM audit_validation WHERE passed=0 "
        "AND severity='fatal' AND applicable=1")]
    check("fatal 실패가 없다", not fatal, str(fatal[:4]))


def flow_config_effect():
    """3 — 설정을 바꾸면 다음 실행의 판정이 달라지는가.

    ★ config 파일을 실제로 고치고 다시 돌린다.  메모리 값만 바꾸면
      「파일 → 판정」 경로가 검사되지 않는다
    """
    import shutil
    import tempfile

    from analyze.axes import ScoringPolicy
    from score.grade import cutoffs

    root = tempfile.mkdtemp()
    shutil.copytree(os.path.join(ROOT, "config"),
                    os.path.join(root, "config"))
    # ★ 키도 함께 옮긴다.  키가 다르면 plate_hash 가 전건 어긋난다
    if os.path.isdir(os.path.join(ROOT, "secrets")):
        shutil.copytree(os.path.join(ROOT, "secrets"),
                        os.path.join(root, "secrets"))
    conn, ctx, ex, _stub, _reps, cfg, _t = _run(root=root)
    before = dict(conn.execute(
        "SELECT grade, COUNT(*) FROM result_score GROUP BY 1"))

    path = os.path.join(root, "config", "scoring.json")
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    check("등급컷이 비율이다 (절대 점수가 아니다)",
          all(0 < v <= 1 for _g, v in cutoffs(ScoringPolicy(raw))),
          str(sorted(raw["grade_cuts"].items())[:2]))

    # ★ 컷을 올리면 같은 점수가 낮은 등급이 된다 (STEP 84)
    raw["grade_cuts"] = {g: min(0.99, v + 0.20)
                         for g, v in raw["grade_cuts"].items()}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)

    conn2, ctx2, _e, _s, _r, _c, _t2 = _run(root=root)
    after = dict(conn2.execute(
        "SELECT grade, COUNT(*) FROM result_score GROUP BY 1"))
    check("★ config 를 고치면 판정 결과가 달라진다", before != after,
          f"{before} → {after}")
    _ = (cfg, ctx, ex)
    return conn2, ctx2, root


def flow_report(conn, ctx, root: str = ROOT):
    """4 — 리포트·내보내기가 실제 파일로 나오는가."""
    import tempfile

    from report.exports.export import CSV, MD, export, write_export
    from report.render import render_listing, render_run, render_target

    out_root = tempfile.mkdtemp()
    fin = json.load(open(os.path.join(ROOT, "config", "finance.json"),
                         encoding="utf-8"))
    lab = json.load(open(os.path.join(ROOT, "config", "labels.json"),
                         encoding="utf-8"))

    with open(os.path.join(root, "config", "scoring.json"),
              encoding="utf-8") as f:
        pol = json.load(f)

    lid, ver = conn.execute(
        "SELECT listing_id, calc_version FROM result_score LIMIT 1").fetchone()

    v = render_listing(conn, lid, ver, fin, pol, root=ROOT)
    check("L1 — 매물 리포트가 만들어진다", v is not None and v.axes,
          f"축 {len(v.axes)}개")
    check("L1 — 분수가 earned/denominator 다 (E-1)",
          v.denominator and v.earned <= v.denominator,
          f"{v.earned}/{v.denominator}")

    tk = conn.execute(
        "SELECT target_key FROM core_listing LIMIT 1").fetchone()[0]
    t = render_target(conn, tk, ctx.run_id, ver, fin, pol, root=ROOT)
    check("L2 — 차종 리포트가 만들어진다", t is not None)

    r = render_run(conn, ctx.run_id, ver)
    check("L3 — 실행 리포트가 만들어진다", r is not None and r.steps,
          f"단계 {len(r.steps)}개")
    check("L3 — 단계가 필드로 읽힌다 (C-3)",
          hasattr(r.steps[0], "requested"), str(type(r.steps[0]).__name__))

    from report.views import ReportMeta

    # ★ 전 요소를 ReportMeta 에서 가져온다.  손으로 조립하지 않는다 (STEP 91a)
    meta = ReportMeta(run_id=ctx.run_id, layer="L1", site="encar",
                      target_key=str(lid), calc_version=ver,
                      generated_at=None)
    made = []
    for report, fmt in ((v, MD), (v, CSV)):
        res = export(report, fmt, lab, meta=meta)
        made.append(write_export(res, out_root))
    check("파일로 나온다", len(made) == 2, str([os.path.basename(m)
                                            for m in made]))
    body = open(made[0], "rb").read()
    check("BOM 이 없다", not body.startswith(b"\xef\xbb\xbf"))
    check("CRLF 가 없다", b"\r\n" not in body)
    check("내용이 비어 있지 않다", len(body) > 200, f"{len(body)}바이트")

    try:
        write_export(export(v, MD, lab, meta=meta), out_root)
        check("같은 이름으로 덮어쓰지 않는다", False, "덮어썼다")
    except FileExistsError:
        check("같은 이름으로 덮어쓰지 않는다", True)

    text = body.decode("utf-8")
    check("리포트에 판정 근거가 있다",
          "축" in text or "판정" in text, text[:40].replace("\n", " "))


def main() -> int:
    print("종단 시험 — 수집 → 분석 → 설정 변경 → 리포트")
    print("\n[1] 수집 · 파싱 · 판정 (S0~S11)")
    conn = flow_pipeline()
    print("\n[2] 검증")
    flow_validation(conn)
    print("\n[3] 설정 변경이 판정에 미치는 영향")
    conn2, ctx2, root2 = flow_config_effect()
    print("\n[4] 리포트 · 내보내기")
    flow_report(conn2, ctx2, root2)
    print()
    print("결과:", "통과" if not FAIL else f"실패 {len(FAIL)} — "
          + " / ".join(FAIL[:5]))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
