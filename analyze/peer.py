# -*- coding: utf-8 -*-
"""유사군 — 「이런 차가 보통 얼마인가」 (7장 STEP 82e).

지시서   STEP 82e
근거     기대가는 감가 곡선 기반이고, 유사군은 실매물 기반이다.
         둘이 크게 다르면 곡선이나 originPrice 를 의심한다
금지     확장 단계를 표시하지 않고 중앙값만 내는 것 (V3-28)
         「트림 무시」로 넓힌 그룹을 「같은 차 시세」로 표시하는 것
         표본이 모자라면 중앙값을 만들어내지 않는다 — NULL 이다
"""
from __future__ import annotations

from dataclasses import dataclass

# 넓히는 순서를 고정한다 (STEP 82e).  단계마다 무엇을 포기했는지 이름에 남긴다
STAGE_EXACT = "트림일치·연식±1·주행±1만"
STAGE_YEAR = "트림일치·연식±2"
STAGE_NO_TRIM = "트림무시·연식±2"
STAGE_TARGET = "차종 전체"
STAGES = (STAGE_EXACT, STAGE_YEAR, STAGE_NO_TRIM, STAGE_TARGET)

# 분위수는 정책이다 → config.scoring.peer_percentiles


@dataclass(frozen=True)
class PeerGroup:
    """★ stage 가 없으면 화면에 낼 수 없다.  무엇으로 넓혔는지가 뜻을 바꾼다."""

    p25: int | None
    median: int | None
    p75: int | None
    sample_size: int
    stage: str | None          # None 이면 표본 부족 — 중앙값도 None 이다
    reason: str | None = None


def quantile(sorted_values: list[int], q: float) -> int:
    idx = int(round((len(sorted_values) - 1) * q))
    return sorted_values[idx]


def stage_conditions(snap, policy_raw: dict) -> list[tuple]:
    """넓히는 순서를 고정한다 (STEP 82e).  ★ 조회는 store 가 한다.

    반환   [(stage, 조건 dict)]  — 분석 계층은 DB 를 모른다 (STEP 2)
    """
    year_win = int(policy_raw["peer_year_window"])
    mile_win = int(policy_raw["peer_mileage_window"])
    year = int(str(snap.year_month)[:4]) if snap.year_month else None
    tk, trim = snap.target_key, snap.trim_badge

    out = []
    if year is not None and snap.mileage_km is not None:
        out.append((STAGE_EXACT, {"target_key": tk, "trim_badge": trim,
                                  "year_from": year - 1, "year_to": year + 1,
                                  "mileage": snap.mileage_km,
                                  "mileage_window": mile_win}))
    if year is not None:
        out.append((STAGE_YEAR, {"target_key": tk, "trim_badge": trim,
                                 "year_from": year - year_win,
                                 "year_to": year + year_win}))
        out.append((STAGE_NO_TRIM, {"target_key": tk,
                                    "year_from": year - year_win,
                                    "year_to": year + year_win}))
    out.append((STAGE_TARGET, {"target_key": tk}))
    return out


def build_peer_group(prices: list[int], stage: str,
                     policy_raw: dict) -> PeerGroup:
    """가격 목록 → PeerGroup.  ★ 순수 함수다."""
    lo, mid, hi = policy_raw["peer_percentiles"]
    rows = sorted(prices)
    return PeerGroup(quantile(rows, lo), quantile(rows, mid),
                     quantile(rows, hi), len(rows), stage)


def empty_peer_group() -> PeerGroup:
    """★ 만들어내지 않는다.  「비교 표본 부족」이 사실이다."""
    return PeerGroup(None, None, None, 0, None, "비교 표본 부족")
