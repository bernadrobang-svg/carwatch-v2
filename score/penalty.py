# -*- coding: utf-8 -*-
"""마이너스 점수 (개정 322).

지시서   5장 「등급 상한 폐기 — 마이너스 점수로」 (개정 322)
근거     마스터 정정 — 「이런 것 필요없어.  이것은 모두 마이너스 점수 주면 돼」
        ★ 상한은 점수제 밖의 규칙이라 뜻이 흐려진다
값규칙   총점에서 뺀다.  0 아래로도 내려간다 —
        「0점이 바닥」이 아니다.  흠이 겹치면 음수다
필수     화면에 뺀 것을 낸다 — 「렌트 이력 −50 · 우수등급 없음 −30」
금지     상한 같은 별도 장치를 늘리는 것.
        E 등급 절대 배제만 남긴다 — 그건 「살 수 없는 것」이다
"""
from __future__ import annotations

# 흠 → config/scoring.json 의 penalties 키.  ★ 점수는 코드에 없다 (V4-13)
RENTAL = "rental_history"
NO_SITE_GRADE = "no_site_grade"
NOT_JOIN = "not_join_ratio"
SELLER_INSPECTION = "seller_inspection"
ACCIDENT_EACH = "accident_each"
FRAME_SHEET = "frame_sheet"
FRAME_SWAP = "frame_swap"

# 화면 문구.  ★ 무엇을 왜 뺐는지가 보여야 한다
LABELS = {
    RENTAL: "렌트·영업용 이력",
    NO_SITE_GRADE: "사이트 우수등급 없음",
    NOT_JOIN: "자차 미가입 기간이 김",
    SELLER_INSPECTION: "점검을 판매자가 등록",
    ACCIDENT_EACH: "사고",
    FRAME_SHEET: "골격 판금",
    FRAME_SWAP: "골격 용접·교환",
}


def penalties_of(verdict, policy, snapshot) -> list:
    """뺄 것들 (키, 점수, 문구).  ★ 원문이 없으면 빼지 않는다.

    ★ 우리가 못 받은 것으로 벌을 주지 않는다 (개정 323).
      벌은 「그 차에 흠이 있다」를 원문으로 확인했을 때만이다
    """
    table = policy.raw.get("penalties") or {}
    out = []

    def add(key: str, times: int = 1, note: str = "") -> None:
        pts = table.get(key)
        if not pts or not times:
            return
        out.append((key, int(pts) * times,
                    f"{LABELS[key]}{note}"))

    values, excluded = verdict.values, verdict.excluded
    # 렌트·영업용 — 셋 중 하나라도 렌트면 (개정 302)
    if "state.usage" not in excluded and values.get("state.usage") == 0:
        add(RENTAL)
    # 사이트 우수등급 — ★ 「확인 못 함」과 「없음」을 가른다 (개정 323)
    if "site.certified" not in excluded and values.get("site.certified") == 0:
        add(NO_SITE_GRADE)
    # 점검을 판매자가 올렸다 (개정 300)
    src = verdict.sources.get("site.inspection") or ""
    if src.endswith("IMAGE"):
        add(SELLER_INSPECTION)
    # 사고 1회당 — 누적
    n = (snapshot.accident_my_cnt or 0) + (snapshot.accident_other_cnt or 0)
    if "state.accident" not in excluded and n:
        add(ACCIDENT_EACH, n, f" {n}회")
    # 골격
    frame_src = verdict.sources.get("state.frame") or ""
    if frame_src == "frame_sheet":
        add(FRAME_SHEET)
    elif frame_src == "frame_swap":
        add(FRAME_SWAP)
    # 자차 미가입 — 보유 기간 대비 비율 (개정 294)
    ratio = _not_join_ratio(snapshot)
    if ratio is not None and ratio >= float(table.get("not_join_ratio_limit", 1)):
        add(NOT_JOIN, 1, f" {ratio:.0%}")
    return out


def _not_join_ratio(snapshot) -> float | None:
    """자차 미가입 개월 ÷ 보유 개월.  ★ 기간을 모르면 벌하지 않는다."""
    months = getattr(snapshot, "not_join_months", None)
    owned = getattr(snapshot, "owned_months", None)
    if not months or not owned:
        return None
    return min(1.0, months / owned)
