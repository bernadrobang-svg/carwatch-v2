# -*- coding: utf-8 -*-
"""색상 40점.

지시서   7장 STEP 80
근거     재판매성.  hex 는 표기 흔들림이 없어 색상명 문자열보다 정확하다
값규칙   색상 미확보 시 NULL + excluded.  0 점이 아니다
금지     유료 색상 금액을 점수에 넣는 것
등급     선호 40 · 중립 25 · 기피 10.  ★ 0 점을 주지 않는다 —
         기피색도 차의 가치를 없애지 않는다.  「이 축에서 손해」일 뿐이다
여집합   선호·중립에 열거되지 않은 색은 기피다.  추정이 아니라 규칙이다
"""
from __future__ import annotations

from analyze.axes import AxisContext
from analyze.verdict import PRIO_OBSERVED, Verdict, put

AXIS = "color"


def analyze_color(ctx: AxisContext, v: Verdict) -> None:
    r = ctx.policy.rule("color")
    name = ctx.snapshot.color_ext_raw
    if not r.get("gate_open"):
        put(v, AXIS, None, PRIO_OBSERVED, "gate_closed", excluded=True)
        return
    if not name:
        put(v, AXIS, None, PRIO_OBSERVED, "missing", excluded=True)
        return
    grade = ctx.dicts.color_grade.get(name, ctx.dicts.color_default)
    if grade is None:
        put(v, AXIS, None, PRIO_OBSERVED, "unclassified", excluded=True)
        return
    put(v, AXIS, r["grade_points"][grade], PRIO_OBSERVED, "detail_color")
