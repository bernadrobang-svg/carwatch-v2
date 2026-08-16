# -*- coding: utf-8 -*-
"""판정 엔진 — 순서 무관 put().

지시서   1장 STEP 13 (계약) · STEP 14 (금지 근거) · 7장 STEP 69 (구현)
근거     낮은 prio 가 이긴다.  호출 순서가 결과에 영향을 주지 않는다.
         같은 prio 로 다른 값이 오면 conflicts 에 기록하고 첫 값을 유지한다.
금지     BANNED_SOURCES 4종.  주석이 아니라 코드가 막는다.
         v.values 에 직접 대입하는 것.  기록은 put() 으로만 한다 (7장 정의서).
불변식   ① put() 호출 순서를 뒤섞어도 결과가 같다      (0장 STEP 7)
         ② 금지 근거가 판정에 들어가면 실패              (0장 STEP 7)
검증     V3-11 표본 100건 셔플 시험 (6장 STEP 60)
"""
from __future__ import annotations

from dataclasses import dataclass, field

from errors import ValidationError

# ── 금지 근거 등록 (1장 STEP 14) ──────────────────────────────────────
# 도메인 규칙이므로 config 가 아니라 코드에 둔다 (0장 STEP 6 · 2장 상수표).
# 넷 다 v1 에서 실제로 사고를 냈다.
BANNED_SOURCES: frozenset[str] = frozenset(
    {
        "catalog_full_list",  # 모델 전체 옵션 목록 — 매물 장착이 아니다
        "facet_count",  # 집계값 — 매물 단위 사실이 아니다
        "record_fuel",  # API 별 표기 상이 — 분류에 쓰면 안 된다
        "part_name_string",  # 부위명 문자열 — 표기 흔들림에 무너진다
    }
)

# 우선순위 4단 (STEP 13 · 7장 STEP 69).  낮은 숫자가 이긴다.
PRIO_MANUFACTURER = 1  # 제조사 사양 · 사이트가 준 코드값 (RANK_* · displacement)
PRIO_OBSERVED = 2  # 매물 실측 (실장착 옵션 · 점검 결과 · 이력)
PRIO_CLASSIFIER = 3  # 전용 판정기
PRIO_KEYWORD = 4  # 키워드 · 문자열 추정

PRIO_RANGE: tuple[int, ...] = (
    PRIO_MANUFACTURER,
    PRIO_OBSERVED,
    PRIO_CLASSIFIER,
    PRIO_KEYWORD,
)


@dataclass
class Verdict:
    """축(Component) 단위 판정 누적기.

    excluded 는 분모 제외 집합이다.  put(excluded=True) 로만 들어간다.
    채점이 value is None 을 보고 분모를 줄이는 것은 금지다 (7장 STEP 83).
    """

    values: dict[str, int | None] = field(default_factory=dict)
    sources: dict[str, str] = field(default_factory=dict)
    prios: dict[str, int] = field(default_factory=dict)
    excluded: set[str] = field(default_factory=set)
    conflicts: list[tuple[str, int, int]] = field(default_factory=list)


def put(
    v: Verdict,
    axis: str,
    value,
    prio: int,
    src: str,
    excluded: bool = False,
) -> None:
    """축에 판정을 기록한다.  호출 순서에 결과가 의존하지 않는다.

    지시서   1장 STEP 13 · 7장 STEP 69
    excluded 분모에서 뺄 축인가.  판정의 결과다 — 채점이 NULL 을 보고 추측하지 않는다
             put(v,"spec.hud",     -1,   1, "spec_table", excluded=True)  차종 미제공
             put(v,"spec.tinting", None, 4, "unknown",    excluded=True)  언급 없음
             put(v,"spec.sunroof",  0,   2, "installed")                  미장착.  제외 아님
    예외     src 가 BANNED_SOURCES 면 ValidationError (STEP 14)
    """
    if src in BANNED_SOURCES:
        raise ValidationError(f"banned source: {src}", step="STEP 14")
    if value is None and not excluded:
        return  # 값도 없고 제외도 아니면 기록하지 않는다
    cur = v.prios.get(axis)
    if cur is not None:
        if cur < prio:
            return  # 강한 근거가 이긴다
        if cur == prio and v.values.get(axis) != value:
            v.conflicts.append((axis, prio, value))
            return  # 첫 값 유지
    v.values[axis] = value
    v.prios[axis] = prio
    v.sources[axis] = src
    if excluded:
        v.excluded.add(axis)
    else:
        v.excluded.discard(axis)
