# -*- coding: utf-8 -*-
"""등급 (L7).

지시서   7장 STEP 84
근거     비율 기준이라 총점이 바뀌어도 등급 의미가 유지된다
값규칙   분모 미달은 NOT_RATED.  D 나 E 가 아니다.  순위도 매기지 않는다
금지     NOT_RATED 를 D 나 E 로 대체하는 것.  낮은 등급이 아니다
         버전이 다른 결과를 한 목록에 섞어 정렬하는 것
"""
from __future__ import annotations

import math

from analyze.axes import ScoringPolicy
from score.scorer import ScoreResult

NOT_RATED = "NOT_RATED"
GRADE_E = "E"
GRADE_D = "D"
GRADE_S = "S"


def cutoffs(policy: ScoringPolicy) -> list[tuple[str, float]]:
    """등급컷 비율.  ★ 점수가 아니라 비율이다 (STEP 84).

    금지   total_points × 비율로 절대컷을 만드는 것
    근거   분모가 매물마다 다르다.  축이 빠질수록 절대컷이 불리해진다
          분모 495 매물은 500점을 받을 수 없다 — 최대가 495 다
    """
    return sorted(((g, float(r)) for g, r in policy.raw["grade_cuts"].items()),
                  key=lambda kv: -kv[1])


def grade_cut_points(policy: ScoringPolicy) -> list[tuple[str, int]]:
    """화면 설명용 「555 기준」 점수.  ★ 판정에 쓰지 않는다 (STEP 84).

    ★ display_points 로 부르지 않는다 — report.views 에 같은 이름이 있다.
      역할이 다르다 (여기는 등급컷, 저기는 축 점수 「—/20」 표기)
    """
    total = float(policy.raw["total_points"])
    out = []
    for g, ratio in policy.raw["grade_cuts"].items():
        raw = total * float(ratio)
        # S 는 499.5 를 올림한 500.  나머지는 내림
        out.append((g, math.ceil(raw) if g == GRADE_S else math.floor(raw)))
    return sorted(out, key=lambda kv: -kv[1])


def grade_of(result: ScoreResult, policy: ScoringPolicy) -> str:
    if result.absolute_fail:
        return GRADE_E
    if result.grade == NOT_RATED:
        return NOT_RATED
    if not result.denominator:
        return NOT_RATED
    # ★ earned 와 denominator 는 같은 자 (실배점).  score_total 은 555 환산값이다.
    #   섞으면 분모가 작을수록 부풀려진다 — 245/455=53.8%(D) 가
    #   298.85/455=65.7%(C) 로 한 등급 올라갔다 (실측 · E-1)
    ratio = result.earned / result.denominator
    for g, cut in cutoffs(policy):
        if ratio >= cut:
            return g
    return GRADE_D
