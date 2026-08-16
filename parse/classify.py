# -*- coding: utf-8 -*-
"""분류 2단 — target_key 판정.

지시서   4장 STEP 46 · STEP 43 (완전 일치)
근거     목록 응답에는 배기량이 없다.  배기량만으로 분류하면 상세 A 미확보분이
         전부 미분류가 된다 (v1 실측 1,364건 · 28.7%).
금지     부분 문자열로 연료를 판정하는 것.  임의 필터를 승인 없이 추가하는 것.
         v1 은 trim_exclude:("2.0",) 를 추측으로 넣었다가 철회했다.
         충돌을 배제로 처리하는 것 — conflict 로 표시하고 통과시킨다.
"""
from __future__ import annotations

from dataclasses import dataclass

STAGE_PROVISIONAL = "provisional"
STAGE_CONFIRMED = "confirmed"

SOURCE_LIST = "list_fuel_badge"  # 딜러 입력 (목록)
SOURCE_SPEC = "spec_displacement"  # 제조사 사양 (상세 A)


@dataclass(frozen=True)
class ClassifyResult:
    target_key: str | None
    stage: str
    source: str
    conflict: bool
    reason: str


def _fuel_ok(target: dict, fuel: str | None) -> bool:
    """완전 일치.  부분 검색 금지 (STEP 43).

    "LPG" in fuel 로 쓰면 LPG(일반인 구입) 과 가솔린+LPG 를 구분하지 못한다.
    "하이브리드" 로 쓰면 엔카가 가솔린+전기 로 주므로 0건이 된다.
    """
    want = target.get("fuel_match") or []
    return bool(want) and fuel in want


def _trim_ok(target: dict, trim_texts: list[str]) -> bool | None:
    """반환   True · False · None(판단 근거 없음)"""
    inc = target.get("trim_include") or []
    exc = target.get("trim_exclude") or []
    joined = " ".join(t for t in trim_texts if t)
    if not joined:
        return None
    if any(x in joined for x in exc):
        return False
    if not inc:
        return None
    return any(x in joined for x in inc)


EV_FUEL = "전기"


def is_ev(target: dict) -> bool:
    return EV_FUEL in (target.get("fuel_match") or [])


def _disp_ok(target: dict, cc: int | None) -> bool | None:
    """★ 전기차에는 배기량 분류를 쓰지 않는다 (STEP 46).

    실측   모델Y 의 spec.displacement 가 22종이다.  딜러 입력값이라 의미가 없다.
    금지   전기차에 displacement_range 를 걸어 분류하는 것
           → 값이 22종이라 대부분 미분류가 된다
    """
    if is_ev(target):
        return None
    rng = target.get("displacement_range")
    if cc is None or not rng:
        return None
    return rng[0] <= cc <= rng[1]


def validate_targets(targets: dict[str, dict]) -> list[str]:
    """검산 — fuel_match 에 「전기」가 있으면 displacement_range 는 null 인가."""
    return [
        f"{k}: 전기차인데 displacement_range 가 있다"
        for k, v in targets.items()
        if is_ev(v) and v.get("displacement_range")
    ]


def classify(targets: dict[str, dict], collect_group: str, fuel: str | None,
             trim_badge: str | None, trim_grade_name: str | None,
             displacement_cc: int | None) -> ClassifyResult:
    """1단 잠정(목록) → 2단 확정(상세 A).

    같은 collect_group 안의 target 후보만 본다.  수집이 그 단위이기 때문이다.
    """
    cands = {
        k: v for k, v in targets.items() if v.get("collect_group") == collect_group
    }
    if not cands:
        return ClassifyResult(None, STAGE_PROVISIONAL, SOURCE_LIST, False,
                              f"collect_group 미정의: {collect_group}")

    trims = [trim_badge, trim_grade_name]
    hits: list[str] = []
    for key, spec in cands.items():
        if not _fuel_ok(spec, fuel):
            continue
        t = _trim_ok(spec, trims)
        if t is False:
            continue
        hits.append(key)

    if displacement_cc is None:
        # 상세 A 미확보.  잠정으로 남긴다.  버리지 않는다
        if len(hits) == 1:
            return ClassifyResult(hits[0], STAGE_PROVISIONAL, SOURCE_LIST, False,
                                  "목록 필드로 단일 후보")
        return ClassifyResult(None, STAGE_PROVISIONAL, SOURCE_LIST, len(hits) > 1,
                              f"후보 {len(hits)}종. 상세 A 대기")

    # 2단 — 제조사 사양이 확정한다
    confirmed = [k for k in hits if _disp_ok(cands[k], displacement_cc) is not False]
    exact = [k for k in hits if _disp_ok(cands[k], displacement_cc) is True]
    if len(exact) == 1:
        return ClassifyResult(exact[0], STAGE_CONFIRMED, SOURCE_SPEC, False,
                              "배기량 · 연료 일치")
    if not hits:
        # 배기량은 대상인데 연료가 제외 — 딜러 오등록 또는 대상 외
        near = [k for k in cands if _disp_ok(cands[k], displacement_cc) is True]
        if near:
            return ClassifyResult(near[0], STAGE_CONFIRMED, SOURCE_SPEC, True,
                                  f"배기량은 대상 · 연료 불일치({fuel})")
        return ClassifyResult(None, STAGE_CONFIRMED, SOURCE_SPEC, False, "대상 외")
    if len(confirmed) == 1:
        why = ("전기차 — 배기량 분류 안 씀"
               if is_ev(cands[confirmed[0]]) else "배기량 범위 미정 · 연료로 확정")
        return ClassifyResult(confirmed[0], STAGE_CONFIRMED, SOURCE_SPEC, False, why)
    return ClassifyResult(None, STAGE_CONFIRMED, SOURCE_SPEC, True,
                          f"후보 {len(hits)}종 · 배기량 {displacement_cc}")
