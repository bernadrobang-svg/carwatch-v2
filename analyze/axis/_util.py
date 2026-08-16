# -*- coding: utf-8 -*-
"""축 공용 도우미.

지시서   7장 STEP 72 (경과월) · STEP 70 (경과년)
근거     판정 로직을 두지 않는다.  각 축 파일이 자기 규칙을 전부 갖는다
금지     여기서 임계값을 다루는 것.  임계는 config 다 (V4-13)
"""
from __future__ import annotations

import json

MONTHS_PER_YEAR = 12


def months_between(ym_from: str | None, ym_to: str | None) -> int | None:
    """`2023-05` · `2023-05-02` → 경과 개월.  시각을 직접 읽지 않는다."""
    if not ym_from or not ym_to:
        return None
    a = [int(x) for x in str(ym_from)[:7].split("-")]
    b = [int(x) for x in str(ym_to)[:7].split("-")]
    return (b[0] - a[0]) * MONTHS_PER_YEAR + (b[1] - a[1])


def jload(text: str | None):
    return None if text is None else json.loads(text)


def panels(snap) -> list[dict] | None:
    return snap.inspection_panels
