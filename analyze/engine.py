# -*- coding: utf-8 -*-
"""판정 실행 (L6).  축 함수를 순서 무관하게 호출한다.

지시서   7장 정의서 · 0장 STEP 7 (불변식 ①)
근거     호출 순서를 뒤섞어도 결과가 같아야 한다.  put() 이 그것을 보장한다
금지     여기서 값을 가공하는 것.  각 축 파일이 자기 규칙을 전부 갖는다
"""
from __future__ import annotations

from analyze.axes import AxisContext
from analyze.axis.color import analyze_color
from analyze.axis.history import analyze_history
from analyze.axis.mileage import analyze_mileage
from analyze.axis.price import analyze_price
from analyze.axis.safety import analyze_safety
from analyze.axis.spec import analyze_spec
from analyze.axis.warranty import analyze_warranty
from analyze.verdict import Verdict

ANALYZERS = (
    analyze_price, analyze_warranty, analyze_spec, analyze_history,
    analyze_safety, analyze_color, analyze_mileage,
)


def analyze_listing(ctx: AxisContext, order=None) -> Verdict:
    v = Verdict()
    for fn in (order or ANALYZERS):
        fn(ctx, v)
    return v
