# -*- coding: utf-8 -*-
"""V5 수치 검증 — 기준값이 맞는가 · 보정이 타당한가.

지시서   6장 STEP 63 · 64 (계수 보정) · 65 (변동 원인 분리)
근거     점수가 「계산은 됐는데 의미가 틀린」 상태를 잡는다
금지     계수 산출에 result_* 를 쓰는 것 — 점수로 계수를 만들고 그 계수로
         다시 점수를 내면 순환이다 (V5-08)
"""
from __future__ import annotations

from validate.base import (
    Check, FATAL, KIND_CODE, KIND_EXTERNAL, WARN, _cfg, result,
)

C = {
    "V5-01": Check("V5", "V5-01", "배점 합계 == config 총점", FATAL, "run",
                     "config/scoring.json 의 components 합과 total_points 를 맞춘다",
                    KIND_CODE),
    "V5-02": Check("V5", "V5-02", "표시용 등급 점수가 비율과 일치", FATAL, "run",
                     "config/scoring.json 의 grade_cuts 비율을 확인한다",
                    KIND_CODE),
    "V5-03": Check("V5", "V5-03", "분모 시험 A·D·E·G·H·I 통과", FATAL, "run",
                     "실패한 항목(A·D·E·G·H·I)의 축 판정을 확인한다 (개정 298)",
                    KIND_CODE),
    "V5-04": Check("V5", "V5-04", "점수 범위 위반 없음", FATAL, "run",
                     "점수 범위를 벗어난 축의 배점 곡선을 확인한다",
                    KIND_CODE),
    "V5-05": Check("V5", "V5-05", "등급 분포가 극단적이지 않음", WARN, "run",
                     "축별 평균을 분해해 0 이거나 만점인 축을 먼저 본다",
                    KIND_EXTERNAL),
    "V5-06": Check("V5", "V5-06", "기준값 대비 실측 이탈", WARN, "run",
                     "config/depreciation.json 의 계수를 STEP 64 절차로 재산출한다",
                    KIND_EXTERNAL),
    "V5-07": Check("V5", "V5-07", "계수 보정 타당성", FATAL, "run",
                     "계수가 가드 밖인 차종의 가격 축이 excluded 인지 확인한다",
                    KIND_CODE),
    "V5-12": Check("V5", "V5-12", "NOT_RATED 인데 not_rated_reason 이 NULL 인 행 없음",
                   FATAL, "run",
                   "왜 판정 못 했는지 3종 중 하나를 채운다. 등급만 내지 않는다",
                   KIND_CODE),
    "V5-09": Check("V5", "V5-09", "등급이 earned / denominator 로 산출됨",
                   FATAL, "run",
                   "earned 와 denominator 는 같은 자다. "
                   "score_total(555 환산)과 섞으면 부풀려진다 (STEP 84)",
                   KIND_CODE),
    "V5-10": Check("V5", "V5-10", "같은 비율 · 다른 분모가 같은 등급",
                   FATAL, "run", "등급 판정에 분모를 반영한다", KIND_CODE),
    "V5-11": Check("V5", "V5-11", "분모 최대값으로도 S 가 불가능한 매물 없음",
                   WARN, "run",
                   "절대컷이 남아 있다. 비율 판정으로 바꾼다", KIND_EXTERNAL),
    "V5-08": Check("V5", "V5-08", "계수 산출 입력에 result_* 없음", FATAL, "run",
                     "계수 산출 입력에서 result_* 를 제거한다. 순환이다",
                    KIND_CODE),
}

# 한 등급이 이 비율을 넘으면 경고 (STEP 63)
DOMINANT_RATIO = _cfg("grade_dominant_ratio")


def run(conn, ctx) -> list:
    rid = ctx.run_id
    policy = ctx.policy_raw
    out = []

    total = policy["total_points"]
    # ★ 스킵된 성분은 총점에서 뺀다 (13장 STEP 128)
    from score.adjust import total_of

    s = total_of(policy["components"])
    out.append(result(C["V5-01"], rid, total, s, s == total))

    from score.grade import cutoffs
    from analyze.axes import ScoringPolicy

    # ★ 판정은 비율이다.  「555 기준」 점수는 표시용이다 (STEP 84).
    #   여기서 검사하는 것은 표시용 점수가 비율과 맞는가다
    from score.grade import grade_cut_points

    pol = ScoringPolicy(policy)
    _ = cutoffs(pol)
    # ★ 등급컷은 505(취향 제외) 기준이다 (개정 292).  555 로 재면 어긋난다
    base = float(policy.get("grade_base_points") or total)
    bad = [f"{g}:{c}" for g, c in grade_cut_points(pol)
           if abs(c - base * policy["grade_cuts"][g]) > 1]
    out.append(result(C["V5-02"], rid, "일치", bad or "일치", not bad, bad))

    out.append(_denominator_suite(rid, policy))

    n = conn.execute(
        "SELECT COUNT(*) FROM result_score WHERE score_total > ? "
        "OR denominator > ?", (total, total)).fetchone()[0]
    out.append(result(C["V5-04"], rid, 0, n, n == 0))

    dist = dict(conn.execute(
        "SELECT grade, COUNT(*) FROM result_score GROUP BY grade").fetchall())
    n_all = sum(dist.values())
    warn = []
    if n_all:
        top = max(dist.values())
        if top / n_all > DOMINANT_RATIO:
            warn.append(f"한 등급이 {top}/{n_all}")
        if not {"S", "A", "B", "C"} & set(dist):
            warn.append("S~C 가 0건 — 축이 안 붙는 것을 의심한다")
    out.append(result(C["V5-05"], rid, "고르게 분포", warn or dist, not warn, warn))

    dep = ctx.depreciation or {}
    rng = dep.get("coefficient_sane_range")
    outside = []
    if rng:
        outside = [f"{k}:{v}" for k, v in (dep.get("coefficient") or {}).items()
                   if not (rng[0] <= v <= rng[1])]
    out.append(result(C["V5-06"], rid, "범위 내", outside or "정상", True, outside))
    # 가드 밖 계수는 그대로 쓰지 않는다 — 가격 축이 excluded 여야 한다 (STEP 70)
    leak = []
    for item in outside:
        tk = item.split(":")[0]
        n = conn.execute(
            "SELECT COUNT(*) FROM result_axis a JOIN core_listing l "
            "ON l.listing_id=a.listing_id WHERE l.target_key=? AND a.axis='price' "
            "AND a.excluded=0", (tk,)).fetchone()[0]
        if n:
            leak.append(f"{tk}: 가격 축 {n}건이 excluded 아님")
    out.append(result(C["V5-07"], rid, 0, leak or 0, not leak, leak))

    # 계수 이력에 점수·등급이 섞이면 순환이다
    bad_reason = [r[0] for r in conn.execute(
        "SELECT reason FROM coefficient_history WHERE reason LIKE '%score%' "
        "OR reason LIKE '%grade%'")]
    out.append(result(C["V5-08"], rid, 0, bad_reason or 0, not bad_reason,
                      bad_reason))
    out += _grade_ratio_checks(conn, rid, policy)

    # V5-12 — 「왜 판정 못 했나」가 비어 있으면 화면이 설명하지 못한다
    cols = {r[1] for r in conn.execute("PRAGMA table_info(result_score)")}
    if "not_rated_reason" in cols:
        n = conn.execute(
            "SELECT COUNT(*) FROM result_score WHERE grade = 'NOT_RATED' "
            "AND (not_rated_reason IS NULL OR not_rated_reason = '')"
        ).fetchone()[0]
        out.append(result(C["V5-12"], rid, 0, n, n == 0))
    else:
        out.append(result(C["V5-12"], rid, "컬럼", "없음", False,
                          ["result_score 에 not_rated_reason 이 없다"]))
    return out


# 축이 빠진 매물을 흉내 내는 분모 비율 (V5-09·10)
MIN_DENOM_PROBE = _cfg("grade_denom_probe")


def _grade_ratio_checks(conn, run_id, policy_raw: dict) -> list:
    """★ 등급은 비율이다.  절대컷이면 분모 495 매물이 S 를 못 받는다 (STEP 84)."""
    from analyze.axes import ScoringPolicy
    from score.grade import grade_of
    from score.scorer import ScoreResult

    policy = ScoringPolicy(policy_raw)

    def g(earned, den):
        # ★ score_total 은 555 환산값이라 등급 판정에 쓰지 않는다
        return grade_of(ScoreResult(0.0, den, [], earned, "B", None, {},
                                    None), policy)

    # ★ 표본을 비율에서 만든다.  점수를 손으로 적으면 컷이 바뀔 때 어긋난다
    cuts = policy_raw["grade_cuts"]
    total = float(policy_raw["total_points"])
    out = []
    bad = []
    for grade, ratio in cuts.items():
        for den in (total, total * MIN_DENOM_PROBE):
            got = g(float(ratio) * den, den)
            if got != grade:
                bad.append(f"{ratio:.0%}·분모{den:g} → {got} (기대 {grade})")
    out.append(result(C["V5-09"], run_id, 0, bad or 0, not bad, bad))

    # 같은 비율 · 다른 분모는 같은 등급이어야 한다
    top = max(float(v) for v in cuts.values())
    same = g(top * total, total) == g(top * total * MIN_DENOM_PROBE,
                                      total * MIN_DENOM_PROBE)
    out.append(result(C["V5-10"], run_id, "일치",
                      "일치" if same else "불일치", same))

    cuts = policy_raw["grade_cuts"]
    top = max(float(v) for v in cuts.values())
    stuck = [f"listing {r[0]} 분모 {r[1]:g}" for r in conn.execute(
        "SELECT listing_id, denominator FROM result_score "
        "WHERE denominator > 0 AND ? * denominator > denominator LIMIT 20",
        (top,))]
    out.append(result(C["V5-11"], run_id, 0, len(stuck), not stuck, stuck))
    return out


def _denominator_suite(run_id: str, policy: dict):
    """분모 시험 A·D·E·G·H·I (0장 STEP 7.1 · 개정 298).

    ★ B · C · F 는 폐기됐다.  「분모를 줄이되 최소치를 두자」가 절반만 맞았다
      분모를 줄이면 못 찾을수록 비율이 오른다
    남는다  A 전 축 정상 · D 전 축 수집 실패 · E 금지 근거만 존재
    새로   G 분모는 늘 만점 · H 못 본 축은 0점 · I 확인율을 함께 낸다
    """
    from analyze.axes import COMPONENTS, ScoringPolicy
    from analyze.verdict import PRIO_OBSERVED, Verdict, put
    from score.scorer import score

    p = ScoringPolicy(policy)

    def build(excluded=()):
        v = Verdict()
        for c in COMPONENTS:
            if c in excluded:
                put(v, c, None, PRIO_OBSERVED, "na", excluded=True)
            else:
                put(v, c, p.comp(c), PRIO_OBSERVED, "test")
        return v

    total = float(policy["total_points"])
    # ★ 성분 이름을 박지 않는다.  배점이 바뀌면 시험이 먼저 죽는다 (개정 292 실측)
    probe = p.active_components()[0]
    fails = []
    if score(build(), p).grade == "NOT_RATED":
        fails.append("A 전 축 정상인데 등급이 안 났다")
    if score(build(COMPONENTS), p).grade != "NOT_RATED":
        fails.append("D 전 축 수집 실패인데 등급이 났다")
    if score(build(), p, absolute=["침수"]).absolute_fail is None:
        fails.append("E 금지 근거를 실었는데 안 남았다")

    # G — 분모는 늘 만점이다.  어떤 축을 빼도 555 다 (개정 298)
    heavy = ("price", "warranty.general", "warranty.power", "spec.hud")
    for excl in ((), (probe,), heavy):
        if score(build(excl), p).denominator != total:
            fails.append(f"G 분모가 만점이 아니다 ({len(excl)}축 제외)")

    # H — 못 본 축은 0점이다.  분모가 아니라 획득이 줄어야 한다
    r_one = score(build((probe,)), p)
    if r_one.earned != score(build(), p).earned - p.comp(probe):
        fails.append("H 못 본 축이 0점으로 안 남았다")

    # I — 확인율을 낼 수 있다.  applicable 이 「확인한 배점 합」이다
    if r_one.applicable != total - p.comp(probe):
        fails.append("I 확인율을 낼 수 없다")
    return result(C["V5-03"], run_id, "A·D·E·G·H·I 전건",
                  fails or "통과", not fails, fails)
