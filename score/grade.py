# -*- coding: utf-8 -*-
"""등급 (L7).

지시서   7장 STEP 84
근거     비율 기준이라 총점이 바뀌어도 등급 의미가 유지된다
값규칙   분모 미달은 NOT_RATED.  D 나 E 가 아니다.  순위도 매기지 않는다
금지     NOT_RATED 를 D 나 E 로 대체하는 것.  낮은 등급이 아니다
         버전이 다른 결과를 한 목록에 섞어 정렬하는 것

★★ 개정 433 — 등급이 8단계가 되고 관문 배제가 등급에서 빠졌다.
   S80 · A70 · B60 · C50 · D40 · E30 · F20 · G10 · 10% 미만은 등급 없음

   ★ 서로 다른 셋을 섞지 않는다 —
     EXCLUDED   관문 배제.  리스·골격 사고·침수·전손.  ★ 점수와 무관하다
     NO_GRADE   10% 미만.  점수는 매겼는데 등급이 없다
     NOT_RATED  분모 미달.  잴 수가 없었다
   금지   E 를 배제로 쓰는 것.  ★ 개정 433 부터 E 는 30~40% 자리다
"""
from __future__ import annotations

import math

from analyze.axes import ScoringPolicy
from score.scorer import ScoreResult

NOT_RATED = "NOT_RATED"
# ★ 개정 433 — 관문 배제.  등급 문자가 아니다.  화면 문구는 config/labels.json
EXCLUDED = "EXCLUDED"
# ★ 개정 433 — 10% 미만.  「등급 없음」이다.  NOT_RATED(분모 미달)와 다르다
NO_GRADE = "NO_GRADE"
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
    """화면 설명용 「505 기준」 점수.  ★ 판정에 쓰지 않는다 (STEP 84).

    ★ display_points 로 부르지 않는다 — report.views 에 같은 이름이 있다.
      역할이 다르다 (여기는 등급컷, 저기는 축 점수 「—/20」 표기)
    """
    # ★ 등급컷 기준은 grade_base_points 다 (개정 452 — 850)
    total = float(policy.raw.get("grade_base_points")
                  or policy.raw["total_points"])
    out = []
    for g, ratio in policy.raw["grade_cuts"].items():
        raw = total * float(ratio)
        # S 는 499.5 를 올림한 500.  나머지는 내림
        out.append((g, math.ceil(raw) if g == GRADE_S else math.floor(raw)))
    return sorted(out, key=lambda kv: -kv[1])


def grade_of(result: ScoreResult, policy: ScoringPolicy) -> str:
    # ★★ 개정 433 — 관문 배제는 등급이 아니다.  「제외」로 따로 둔다.
    #   전에는 E 를 돌려줬는데, 8단계로 내리면서 E 가 30~40% 자리가 됐다.
    #   ★ 배제를 점수로 표현하지 않는다 — 관문은 통과/탈락이다
    if result.absolute_fail:
        return EXCLUDED
    if result.grade == NOT_RATED:
        return NOT_RATED
    if not result.denominator:
        return NOT_RATED
    # ★ earned 와 denominator 는 같은 자 (실배점).  score_total 은 555 환산값이다.
    #   섞으면 분모가 작을수록 부풀려진다 — 245/455=53.8%(D) 가
    #   298.85/455=65.7%(C) 로 한 등급 올라갔다 (실측 · E-1)
    # ★ 등급은 850 으로 매긴다 (개정 452).  취향도 들어간다 — 개정 292 는 폐기다
    if result.grade_base:
        ratio = result.grade_earned / result.grade_base
    else:
        ratio = result.earned / result.denominator
    for g, cut in cutoffs(policy):
        if ratio >= cut:
            return g
    # ★ 개정 433 — 맨 아래 컷(G 10%)에도 못 미치면 「등급 없음」이다.
    #   전에는 D 를 돌려줬다 — 5단계 시절엔 D 가 맨 아래였기 때문이다.
    #   ★ 이제 맨 아래는 G 다.  D 를 돌려주면 40% 자리에 10% 미만이 섞인다
    return NO_GRADE
