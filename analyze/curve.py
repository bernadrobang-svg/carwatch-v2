# -*- coding: utf-8 -*-
"""구간별 점수표 (docs/ref/F-scoring.md).

지시서   `docs/ref/F-scoring.md` — 배점의 유일한 정본 (개정 330)
근거     마스터 지적 — 「항목별 점수 테이블도 없고 배점 룰도 없다」
필수     구간 사이는 선형 보간한다 (F-scoring 0절)
금지     점수를 코드에 박는 것.  표는 config 다 (V4-13)
        본문 배점표를 읽는 것 — 전부 폐기됐다 (개정 330)
"""
from __future__ import annotations


def descending(x, table) -> float:
    """x 가 클수록 점수가 높은 표.  `[[기준, 점수], …]` 내림차순.

    예   시세 대비  [[0.25,100],[0.20,90], … [-0.20,0]]
    ★ 표 밖은 양 끝 값이다.  바깥에서 점수를 만들지 않는다
    """
    rows = [(float(a), float(b)) for a, b in table]
    if x >= rows[0][0]:
        return rows[0][1]
    if x <= rows[-1][0]:
        return rows[-1][1]
    for (a1, p1), (a2, p2) in zip(rows, rows[1:], strict=False):
        if a2 <= x <= a1:
            return _lerp(x, a2, a1, p2, p1)
    return rows[-1][1]


def ascending(x, table) -> float:
    """x 가 작을수록 점수가 높은 표.  `[[기준, 점수], …]` 오름차순.

    예   주행 대비  [[5000,70],[8000,62], … [30000,0]]
    """
    rows = [(float(a), float(b)) for a, b in table]
    if x <= rows[0][0]:
        return rows[0][1]
    if x >= rows[-1][0]:
        return rows[-1][1]
    for (a1, p1), (a2, p2) in zip(rows, rows[1:], strict=False):
        if a1 <= x <= a2:
            return _lerp(x, a1, a2, p1, p2)
    return rows[-1][1]


def step_down(n, table, floor: float = 0.0) -> float:
    """정수 단계표.  보간하지 않는다 — 사고 1회와 2회 사이는 없다.

    예   사고  [[0,40],[1,22],[2,10],[3,0]]
    """
    for edge, pts in table:
        if n <= int(edge):
            return float(pts)
    return float(floor)


def _lerp(x, x0, x1, y0, y1) -> float:
    """구간 사이는 선형 보간 (F-scoring 0절)."""
    if x1 == x0:
        return y0
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
