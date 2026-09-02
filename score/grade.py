# -*- coding: utf-8 -*-
"""등급 (L7).

지시서   7장 STEP 84
근거     비율 기준이라 총점이 바뀌어도 등급 의미가 유지된다
값규칙   분모 미달은 NOT_RATED.  D 나 E 가 아니다.  순위도 매기지 않는다
         ★★ 근거 있는 축의 합이 분모의 절반 아래면 PENDING(「판정 중」)이다.
            ★ F·G 로 내리지 않는다 (명령서 67장 · 검산 S46-90)
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
# ★★ 개정 771 · 명령서 67장 — 「판정 중」.  ★ 근거가 절반도 없다.
#   ★ 낮은 등급이 아니다.  상세가 들어오면 그때 등급이 난다
PENDING = "PENDING"
# 「근거 있는 축의 합」이 분모의 이 비율 아래면 판정 중.  ★ config 가 정본
# ★★★ 08-28 — ★ 가이드가 ★ `pending_rule.evidence_ratio_below` 로 ★ 새로 넣었다
#   (`config/scoring.json` · r788).  ★ 값은 ★ **0.60** 이다.
#   ★ 까닭 — ★ 「절반(455)으로는 ★ 볼보 399 · 현대인증 481 이 갈리지 않는다」.
#   ★ ★ 등급은 ★ 「차의 좋고 나쁨」이지 ★ 「우리가 아는 정도」가 아니다.
#   ★ 옛 열쇠(`pending_confirmed_ratio`)는 ★ 뒤에 둔다 — ★ 새 것이 있으면 그것이 정본이다
PENDING_RULE_KEY = "pending_rule"
PENDING_RATIO_KEY = "pending_confirmed_ratio"


def pending_ratio(policy) -> float:
    """「판정 중」 문턱.  ★ 정본은 `config/scoring.json` 이다 (S14).

    ★ `pending_rule.evidence_ratio_below` 가 있으면 ★ 그것이다.
    ★ 없으면 옛 열쇠 `pending_confirmed_ratio` 를 쓴다.  ★ 둘 다 없으면 0.5
    """
    rule = policy.raw.get(PENDING_RULE_KEY)
    if isinstance(rule, dict) and rule.get("evidence_ratio_below") is not None:
        return float(rule["evidence_ratio_below"])
    return float(policy.raw.get(PENDING_RATIO_KEY, 0.5))
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


def _rank_of(grade: str, policy: ScoringPolicy) -> int:
    """★ 등급 차례에서 몇째인가.  ★ 0 이 가장 좋다.  ★ 모르면 맨 뒤다."""
    order = [g for g, _cut in cutoffs(policy)]
    return order.index(grade) if grade in order else len(order)


def _state_ok_floor(result: "ScoreResult", policy: ScoringPolicy) -> str | None:
    """★ 상태 축이 다 정상이면 ★ 바닥 등급을 준다 (`grade_gates.state_ok_floor`).

    ★ 「정상」의 뜻 — ★ 그 축이 ★ **만점의 `need_ratio` 이상**을 받았는가.
      ★ ★ 못 잰 축(0점)은 ★ 「흠이 있다」가 아니다 — ★ 그러나 ★ **정상도 아니다**.
      ★ ★ ★ 그래서 ★ 「몇 개가 정상인가」의 비율로 본다 (규격 `need_ratio`).
    ★ 규칙이 없으면 ★ `None` 이다 — ★ 코드가 지어내지 않는다 (`S14` · 금지 6)
    """
    # ★ 규격은 ★ `policy.raw` 안에 그대로 있다 — ★ 코드에 안 박는다 (`S14`)
    raw = getattr(policy, "raw", None) or {}
    gate = (raw.get("grade_gates") or {}).get("state_ok_floor")
    if not isinstance(gate, dict):
        return None
    axes = list(gate.get("state_axes") or ())
    if not axes:
        return None
    need = float(gate.get("need_ratio") or 1.0)
    ok = 0
    for a in axes:
        full = policy.comp(a)
        if not full:
            continue
        if float((result.by_axis or {}).get(a) or 0.0) >= full * need:
            ok += 1
    return gate.get("grade") if ok >= len(axes) * need else None


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
    # ★★ 개정 771 · 명령서 67장 · UI_REVIEW 18장 — ★ 근거 있는 축의 합이
    #   분모의 절반 아래면 「판정 중」이다.  ★ F·G 로 내리지 않는다.
    #   실측 08-27 — X3 264/910 F · G80 670/910 A.  까닭은 차가 나빠서가
    #   아니라 ★ 상세를 못 받아서다 (사고 0/51 · 용도 0/22 · 자차 0/18 ·
    #   소유자 0/11).  「모르는 것을 모른다고 낸다」(개정 325)
    # ★★ 분모는 ★ 910 그대로다 (가이드 확정 08-25).  ★ 「근거 있는 축 N / 910」
    #   이라 UI_REVIEW 18장이 못 박았다.  ★ 채워질 수 없는 축(소모품)을 분모에서
    #   빼면 절반선이 447.5 로 내려가 ★ 근거 450 짜리가 0.3%p 차로 G 에 남는다 —
    #   실측 08-25: 판정 중 3,590 → 1,670 으로 줄고 ★ 상세 없는 G 1,288 이 남았다.
    #   ★ 소모품은 「무엇이 비었나」 목록에서만 뺀다 (67장-4 · report/render.py)
    base = float(result.denominator)
    cut = pending_ratio(policy)
    if base > 0 and float(result.confirmed or 0.0) < base * cut:
        return PENDING
    # ★ earned 와 denominator 는 같은 자 (실배점).  score_total 은 555 환산값이다.
    #   섞으면 분모가 작을수록 부풀려진다 — 245/455=53.8%(D) 가
    #   298.85/455=65.7%(C) 로 한 등급 올라갔다 (실측 · E-1)
    # ★ 등급은 850 으로 매긴다 (개정 452).  취향도 들어간다 — 개정 292 는 폐기다
    if result.grade_base:
        ratio = result.grade_earned / result.grade_base
    else:
        ratio = result.earned / result.denominator
    got = NO_GRADE
    for g, cut in cutoffs(policy):
        if ratio >= cut:
            got = g
            break
    # ★★★★★ 09-03 (2부 S9 · 개정 1093) — ★ **차가 멀쩡하면 바닥이 C 다.**
    #   ★★★ 마스터 09-02 — 「★ 내가 원하는 것은 ★ **등급의 현실화**다.
    #     ★ **차가 멀쩡하면 C** 라고 하고 ★ 나머지는 **가격과 취향**으로 하라」
    #   ★★ 까닭 — ★ 분모 910 은 ★ **새 차에 가까운 완벽한 차** 기준이다.
    #     ★ 3,000만원대 4~5년 차는 ★ 주행·보증·사고·소모품이 ★ 시작부터 0 이라
    #     ★ ★ 그 잣대로는 ★ **영원히 D·E** 였다 (실측 09-03 — D 이하 **59.3%**).
    #   ★★★ 규칙은 ★ `config/scoring.json` `grade_gates.state_ok_floor` 가 정본이다 —
    #     ★ ★ **코드에 등급도 축 이름도 안 박는다** (`S14`).
    #     ★ ★ ★ 검사(`S46-248`)는 ★ 그 규칙이 **있는지**만 봤다 —
    #       ★ ★ ★ ★ 판정 코드는 ★ **한 번도 안 읽고 있었다** [실측 09-03].
    #   ★ 상태에 흠이 있으면 ★ 이 바닥을 안 준다 — ★ D 아래로 내려간다
    floor = _state_ok_floor(result, policy)
    if floor and _rank_of(floor, policy) < _rank_of(got, policy):
        return floor
    if got != NO_GRADE:
        return got
    # ★ 개정 433 — 맨 아래 컷(G 10%)에도 못 미치면 「등급 없음」이다.
    #   전에는 D 를 돌려줬다 — 5단계 시절엔 D 가 맨 아래였기 때문이다.
    #   ★ 이제 맨 아래는 G 다.  D 를 돌려주면 40% 자리에 10% 미만이 섞인다
    return NO_GRADE
