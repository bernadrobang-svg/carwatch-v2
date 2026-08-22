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

# 가점 키 (개정 380).  ★ 점수는 config 에 있다 (V4-13)
BATTERY_SOH = "battery_soh"

# 흠 → config/scoring.json 의 penalties 키.  ★ 점수는 코드에 없다 (V4-13)
RENTAL = "rental_history"
NO_SITE_GRADE = "no_site_grade"
NOT_JOIN = "not_join_ratio"
FRAME_SHEET = "frame_sheet"
FRAME_SWAP = "frame_swap"
LIEN = "lien"
# ★ 상한을 걸어 되돌려 준 몫.  ★ 「깎인 합 → 상한」을 화면이 그대로 낸다 (개정 491)
CAP_PREFIX = "cap:"

# 화면 문구.  ★ 무엇을 왜 뺐는지가 보여야 한다
LABELS = {
    RENTAL: "렌트·영업용 이력",
    NO_SITE_GRADE: "사이트 우수등급 없음",
    NOT_JOIN: "자차 미가입 기간이 김",
    FRAME_SHEET: "골격 판금",
    FRAME_SWAP: "골격 용접·교환",
    LIEN: "압류·저당 있음",
    "illegal_structure": "불법 구조변경",
    "cluster_swap": "계기판 교체",
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
    if "history.usage" not in excluded and values.get("history.usage") == 0:
        add(RENTAL)
    # 사이트 우수등급 — ★ 「확인 못 함」과 「없음」을 가른다 (개정 323)
    if "warranty.site" not in excluded and values.get("warranty.site") == 0:
        add(NO_SITE_GRADE)
    # ★★ 개정 491 — 「점검을 판매자가 올렸다」는 ★ 감점이 아니다.
    #   ★ warranty.site 의 **단계를 낮춘다** (analyze/axis/site.py).
    #   ★ 만점을 주고 같은 사실로 또 깎으면 앞뒤가 안 맞는다 (f-table 「사이트 검증」)
    # ★ 압류·저당 — 있으면 소유권 이전이 막힌다 (F-scoring 마이너스)
    if verdict.sources.get("history.lien") == "detail_seizing" \
            and values.get("history.lien") == 0:
        add(LIEN)
    # 골격
    frame_src = verdict.sources.get("state.frame") or ""
    if frame_src.startswith("frame_sheet"):
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


def bonuses_of(policy, snapshot) -> list:
    """더할 것들 (키, 점수, 문구) — 개정 380.

    마스터 확정 — 「그게 있는 데 있고 대부분이 없는데.
    그건 가점이니 필수는 아닌 듯해」
    ★ 축이 아니다.  있으면 더하고 없으면 아무 일도 없다
    ★ 없다고 감점하지 않는다 — 엔카가 진단 안 한 죄를 차에 묻는 것이다
    ★ 분모를 안 늘린다.  가점이 크면 100%를 넘고 그대로 낸다
    """
    if snapshot is None:
        return []
    table = policy.raw.get("bonus") or {}
    full = table.get(BATTERY_SOH)
    soh = getattr(snapshot, "ev_battery_soh", None)
    if not full or soh is None:
        return []
    curve = (policy.raw.get("axis_rules", {}).get("value", {})
             or {}).get("soh_curve")
    if not curve:
        return []
    # ★ 곡선은 내림차순 [[97,30],[95,26],…].  닿는 첫 칸이 그 점수다
    got = 0
    for edge, pts in curve:
        if float(soh) >= float(edge):
            got = int(pts)
            break
    if not got:
        return []
    got = min(got, int(full))
    return [(BATTERY_SOH, got, f"배터리 SOH {float(soh):g}%")]


def cap_penalties(items: list, policy) -> list:
    """★ 감점 상한 (개정 491 · 마스터 확정).

    ★ 뜻 — 그 축에 문제가 있으면 ★ 그 축을 통째로 잃되
           ★ 다른 축에서 번 점수까지 갉아먹지 않는다
    ★ 축별로 ★ 묶어 합산한 뒤 ★ 그 축 배점에서 자른다.  ★ 하나씩 자르지 않는다
    ★ 자른 것을 ★ 감추지 않는다 — 되돌린 몫을 「cap:축」 줄로 함께 낸다.
      그래서 화면이 「골격 −162 → 상한 −43」을 그대로 낼 수 있다
    ★ 겹치는 축이 없는 감점(계기판 교체)은 ★ 상한을 두지 않는다
    """
    where = {k: v for k, v in (policy.raw.get("penalty_axis") or {}).items()
             if not k.startswith("_")}
    comps = policy.raw.get("components") or {}
    by_axis: dict = {}
    for key, pts, _label in items:
        axis = where.get(key)
        if axis:
            by_axis.setdefault(axis, []).append(pts)
    out = list(items)
    for axis, got in sorted(by_axis.items()):
        raw = sum(got)
        one = comps.get(axis)
        full = one if isinstance(one, (int, float)) else (one or {}).get("points")
        if full is None:
            continue
        cap = -abs(int(full))
        if raw >= cap:                 # ★ 상한 안이면 그대로 둔다
            continue
        back = cap - raw               # ★ 되돌려 주는 몫 (양수)
        out.append((f"{CAP_PREFIX}{axis}", back,
                    f"{AXIS_WORDS.get(axis, axis)} {raw} → 상한 {cap}"))
    return out


# 상한 줄에 쓸 축 이름.  ★ 코드에 배점을 박지 않는다 — 이름만이다
AXIS_WORDS = {
    "state.frame": "골격",
    "history.usage": "용도",
    "history.not_join": "자차 미가입",
    "history.lien": "압류·저당",
    "warranty.site": "사이트 검증",
}
