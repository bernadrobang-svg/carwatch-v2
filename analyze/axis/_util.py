# -*- coding: utf-8 -*-
"""축 공용 도우미.

지시서   7장 STEP 72 (경과월) · STEP 70 (경과년)
근거     판정 로직을 두지 않는다.  각 축 파일이 자기 규칙을 전부 갖는다
금지     여기서 임계값을 다루는 것.  임계는 config 다 (V4-13)
"""
from __future__ import annotations

import json

MONTHS_PER_YEAR = 12


def _ym(said: str | None) -> tuple | None:
    """`2023-05` · `2023-05-02` · ★ `202305` → (해, 달).  ★ 못 읽으면 None.

    ★★ 실측 08-24 — ★ `202212` 를 ★ 못 읽고 있었다.
       ★ `MULTISITE_MAPPING` 5a② 가 ★ 「`year_month` 는 YYYYMM 6자리다」라 못 박았고
       ★ 새 사이트 다섯(KB·K카·보배·기아·현대)이 ★ 그대로 넣는다.
       ★ 엔카만 ★ `2024-12` 꼴이라 ★ 엔카만 돌고 있었다 —
       ★ 새 사이트 매물은 ★ 축이 ★ 한 개도 안 나왔다 (실측 result_axis 0행)
    ★ 「2023」처럼 달이 없는 값은 ★ 모른다고 한다 — ★ 추정한 달을 넣지 않는다
    """
    if not said:
        return None
    text = str(said).strip()
    if "-" in text:
        got = [int(x) for x in text[:7].split("-") if x.isdigit()]
        return (got[0], got[1]) if len(got) >= 2 else None
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) >= 6:
        return int(digits[:4]), int(digits[4:6])
    return None


def months_between(ym_from: str | None, ym_to: str | None) -> int | None:
    """`2023-05` · `2023-05-02` · `202305` → 경과 개월.  시각을 직접 읽지 않는다."""
    a, b = _ym(ym_from), _ym(ym_to)
    if a is None or b is None:
        return None
    return (b[0] - a[0]) * MONTHS_PER_YEAR + (b[1] - a[1])


def jload(text: str | None):
    return None if text is None else json.loads(text)


def panels(snap) -> list[dict] | None:
    return snap.inspection_panels
