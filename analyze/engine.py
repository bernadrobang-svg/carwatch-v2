# -*- coding: utf-8 -*-
"""판정 실행 (L6).  축 함수를 순서 무관하게 호출한다.

지시서   7장 정의서 · 0장 STEP 7 (불변식 ①)
근거     호출 순서를 뒤섞어도 결과가 같아야 한다.  put() 이 그것을 보장한다
금지     여기서 값을 가공하는 것.  각 축 파일이 자기 규칙을 전부 갖는다
"""
from __future__ import annotations

from analyze.axes import AxisContext
from analyze.axis.site import analyze_site
from analyze.axis.state import analyze_state
from analyze.axis.taste import analyze_taste
from analyze.axis.trim import analyze_trim
from analyze.axis.value import analyze_value
from analyze.verdict import Verdict

# ★ 개정 292·306 으로 축이 다시 짜였다 —
#   값 250 · 상태 180 · 사양 75 · 사이트 보증 50 · 취향 50 = 605.
#   옛 축 함수(analyze_price · analyze_spec 등)는 그 안에서 재료로 쓰인다
ANALYZERS = (
    analyze_value, analyze_state, analyze_trim, analyze_site, analyze_taste,
)


def analyze_listing(ctx: AxisContext, order=None) -> Verdict:
    v = Verdict()
    for fn in (order or ANALYZERS):
        fn(ctx, v)
    return v
