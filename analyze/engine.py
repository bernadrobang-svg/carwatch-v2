# -*- coding: utf-8 -*-
"""판정 실행 (L6).  축 함수를 순서 무관하게 호출한다.

지시서   7장 정의서 · 0장 STEP 7 (불변식 ①)
근거     호출 순서를 뒤섞어도 결과가 같아야 한다.  put() 이 그것을 보장한다
금지     여기서 값을 가공하는 것.  각 축 파일이 자기 규칙을 전부 갖는다
"""
from __future__ import annotations

from analyze.axes import AxisContext
from analyze.axis.history import analyze_history
from analyze.axis.site import analyze_site
from analyze.axis.state import analyze_state
from analyze.axis.taste import analyze_taste
from analyze.axis.trim import analyze_trim
from analyze.axis.value import analyze_value
from analyze.verdict import Verdict

# ★ 개정 329 로 24축이 됐다 (docs/ref/F-scoring.md).
#   값 250 · 상태 150 · 이력 80 · 사양 45 · 보증 30 · 취향 50 = 605.
#   옛 축 함수(analyze_price · analyze_spec 등)는 그 안에서 재료로 쓰인다
# ★★★★★ 09-05 (0-1e · 마스터 확정) — ★ `taste.trim` 20 이 ★ `taste.interior` 20 이 됐다.
#   ★ 그것은 ★ **차종 고정값**이라 ★ `analyze_taste` 가 낸다.
#   ★ `analyze_trim` 은 ★ 남는다 — ★ 그 갈래가 ★ `taste.option` 30 도 내기 때문이다.
#   ★ 09-05 실측 — 이것을 뺐더니 ★ 옵션 축이 18,808건 통째로 안 생겼다
ANALYZERS = (
    analyze_value, analyze_state, analyze_history,
    analyze_site, analyze_taste, analyze_trim,
)


def analyze_listing(ctx: AxisContext, order=None) -> Verdict:
    v = Verdict()
    for fn in (order or ANALYZERS):
        fn(ctx, v)
    return v
