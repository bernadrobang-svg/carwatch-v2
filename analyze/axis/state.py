# -*- coding: utf-8 -*-
"""② 상태 150 — 차가 성한가 (docs/ref/F-scoring.md ②).

지시서   7장 STEP 76 · 77 · `docs/ref/F-scoring.md` ② (개정 329)
근거     마스터 지적 — 「등급 산정에 넣어야 하는 항목이 너무 한정적이다」
        17축은 임의로 좁힌 것이었다.  원문에 있는 것을 다 넣는다
축      사고 40 · 골격 30 · 외판 20 · 수리비 20
        특수사고 15 · 누유 10 · 소모품 10 · 진정성 5
금지     부위명 문자열로 골격을 판정하는 것.  RANK_A/B/C 를 쓴다
        원문이 없는데 「없음」으로 두는 것 — 「확인 안 됨」이다 (개정 323)
"""
from __future__ import annotations

import json

from analyze.axes import AxisContext
from analyze.curve import ascending, step_down
from analyze.verdict import PRIO_OBSERVED, Verdict, put

ACCIDENT = "state.accident"
FRAME = "state.frame"
OUTER = "state.outer"
REPAIR = "state.my_cost"
SPECIAL = "state.special"
LEAK = "state.leak"
CONSUMABLE = "state.consumable"
# 그 사이트가 아예 안 주는 축의 사유 (개정 306).
# ★ contracts 가 정본이다 — analyze 는 store 를 부르지 않는다 (V4-22)
from contracts import SITE_UNAVAILABLE  # noqa: E402

# sites.json 은 한 실행 안에서 안 바뀐다.  한 번만 읽는다
_SITES: dict | None = None
INTEGRITY = "state.integrity"

# 상태 문구 — 원문 그대로 (실측).  ★ 코드를 쓰지 않는다 — 사이트가 바꿀 수 있다
SWAP_TITLES = ("교환(교체)", "용접,절단")
SHEET_TITLES = ("판금/용접",)
# 누유 — statusItemTypes 가 「없음 · 미세누유 · 누유」다
LEAK_MINOR = ("미세누유", "미세누수")
LEAK_BAD = ("누유", "누수")


def _panels(snap):
    return snap.inspection_panels


def _rank_worst(panels, ranks, titles) -> int:
    """그 랭크의 판 중 titles 상태인 판 수.  ★ 판 단위로 한 번만 센다."""
    n = 0
    for el in panels:
        if not any(a in ranks for a in (el.get("attributes") or [])):
            continue
        got = [t.get("title") for t in (el.get("statusTypes") or [])]
        if any(t in titles for t in got):
            n += 1
    return n


def insurance_trace(snap) -> bool:
    """보험에 「고친 흔적」이 있는가 (개정 414).

    ★ 회수와 금액 둘 다 본다.  금액만 보면 「1회 · 0원」이 새어 나간다
    """
    return bool((snap.accident_my_cost or 0) > 0
                or (snap.accident_my_cnt or 0) > 0)


def panel_trace(panels) -> bool:
    """성능부에 교환·용접 흔적이 있는가 (개정 414 ②-1 의 B).

    ★ 랭크를 안 가린다.  「어딘가 손댔다」만 본다 — 최소 1회로 세는 용도다
    """
    for el in panels or []:
        got = [t.get("title") for t in (el.get("statusTypes") or [])]
        if any(t in SWAP_TITLES or t in SHEET_TITLES for t in got):
            return True
    return False


def worse_step(key: str, order: list) -> str:
    """한 단계 내린다 (개정 414).  ★ 0점으로 떨어뜨리지 않는다."""
    if key not in order:
        return key
    return order[min(order.index(key) + 1, len(order) - 1)]


def _accident(ctx: AxisContext, v: Verdict) -> None:
    """2-1 사고 이력 40 — 무사고 40 · 1회 22 · 2회 10 · 3회 이상 0."""
    s, r = ctx.snapshot, ctx.policy.rule("state")
    my, other = s.accident_my_cnt, s.accident_other_cnt
    from_panel = 1 if panel_trace(_panels(s)) else 0
    if my is None and other is None and not from_panel:
        # ★ 원문이 없으면 「확인 안 됨」이다.  「무사고」가 아니다 (개정 323)
        put(v, ACCIDENT, 0, PRIO_OBSERVED, "missing")
        return
    # ★★ 나쁜 쪽을 믿는다 (개정 414).  회수 = max(보험 회수, 성능부 흔적→1)
    #   ★ 성능부에 교환·용접이 있는데 보험이 0회면 보험이 못 본 것이다
    #   ★ 보험 원문이 아예 없어도 성능부 흔적이 있으면 「확인 안 됨」이 아니다 —
    #     손댄 자리를 눈으로 보고도 「모른다」 하는 것이 「나쁜 쪽」에 어긋난다
    #     (실측 08-21 — 그런 매물이 148건이었다)
    from_record = (my or 0) + (other or 0)
    n = max(from_record, from_panel)
    why = ("record_accident_count" if from_record >= from_panel
           else "panel_trace_min_one")
    put(v, ACCIDENT, round(step_down(n, r["accident_curve"])),
        PRIO_OBSERVED, why)


def _frame(ctx: AxisContext, v: Verdict) -> None:
    """2-2 골격 30 — 이상없음 30 · 판금1 18 · 판금2+ 8 · 용접·교환 0."""
    s, r = ctx.snapshot, ctx.policy.rule("state")
    if _panels(s) is None:
        put(v, FRAME, 0, PRIO_OBSERVED, "missing")
        return
    ranks = ctx.policy.rule("absolute_fail")["frame_ranks"]
    if _rank_worst(_panels(s), ranks, SWAP_TITLES):
        key = "swap"
    else:
        n = _rank_worst(_panels(s), ranks, SHEET_TITLES)
        key = "none" if not n else ("sheet1" if n == 1 else "sheet2")
    # ★ 성능부가 「이상 없음」인데 보험에 수리비가 있으면 한 단계 내린다 (개정 414)
    why = f"frame_{key}"
    if r.get("worse_of_inspection") and key == "none" and insurance_trace(s):
        key = worse_step(key, r["frame_worse_order"])
        why = f"frame_{key}_insurance_trace"
    put(v, FRAME, r["frame_points"][key], PRIO_OBSERVED, why)


def _outer(ctx: AxisContext, v: Verdict) -> None:
    """2-3 외판 20 — 골격과 따로 센다.  외판 교환은 값을 깎는다."""
    s, r = ctx.policy.rule("state"), None
    snap = ctx.snapshot
    if _panels(snap) is None:
        put(v, OUTER, 0, PRIO_OBSERVED, "missing")
        return
    ranks = ctx.policy.rule("absolute_fail")["outer_ranks"]
    if _rank_worst(_panels(snap), ranks, SWAP_TITLES):
        key = "swap"
    else:
        n = _rank_worst(_panels(snap), ranks, SHEET_TITLES)
        key = "none" if not n else ("paint12" if n <= 2 else "paint3")
    why = f"outer_{key}"
    if s.get("worse_of_inspection") and key == "none" \
            and insurance_trace(snap):
        key = worse_step(key, s["outer_worse_order"])
        why = f"outer_{key}_insurance_trace"
    put(v, OUTER, s["outer_points"][key], PRIO_OBSERVED, why)
    del r


def _repair(ctx: AxisContext, v: Verdict) -> None:
    """2-4 자차 수리비 20 — 0원 20 · 50만 16 · 100만 12 · 200만 8 · 500만 4."""
    s, r = ctx.snapshot, ctx.policy.rule("state")
    if s.accident_my_cost is None:
        put(v, REPAIR, 0, PRIO_OBSERVED, "missing")
        return
    put(v, REPAIR, round(step_down(s.accident_my_cost, r["repair_curve"],
                                   r["repair_min"])),
        PRIO_OBSERVED, "record_my_cost")


def _special(ctx: AxisContext, v: Verdict) -> None:
    """2-5 특수 사고 15 — 전손 · 침수 · 도난.  하나라도 있으면 0."""
    s, r = ctx.snapshot, ctx.policy.rule("state")
    got = (s.total_loss_cnt, s.flood_total_cnt, s.flood_part_cnt)
    if all(x is None for x in got):
        put(v, SPECIAL, 0, PRIO_OBSERVED, "missing")
        return
    bad = any(x for x in got if x)
    put(v, SPECIAL, r["special_bad"] if bad else r["special_ok"],
        PRIO_OBSERVED, "record_special")


def leak_state(inners) -> str:
    """누유 상태 — 원동기·변속기·동력전달 (F ②-6).

    ★ 상태 문구를 그대로 본다.  코드를 쓰면 사이트가 바꿀 때 조용히 틀린다
    """
    minor = bad = 0
    stack = list(inners or [])
    while stack:
        node = stack.pop()
        if not isinstance(node, dict):
            continue
        title = ((node.get("statusType") or {}).get("title") or "")
        if title in LEAK_BAD:
            bad += 1
        elif title in LEAK_MINOR:
            minor += 1
        stack.extend(node.get("children") or [])
    if bad:
        return "leak"
    return "none" if not minor else ("minor1" if minor == 1 else "minor2")


def _is_ev(ctx: AxisContext) -> bool:
    """전기차인가.  ★ 하이브리드는 ★ **아니다** (규격 「하이브리드엔 쓰지 마라」).

    ★ 연료 낱말의 정본은 ★ `config/labels.json` 이다 — ★ 코드에 안 박는다 (`S14`).
    ★ 못 읽으면 ★ 거짓이다 — ★ 만점을 지어 주지 않는다 (금지 12)
    """
    got = str(getattr(ctx.snapshot, "fuel_raw", "") or "")
    if not got:
        return False
    words = _ev_words()
    if not words:
        return False
    # ★ 「하이브리드」가 들면 ★ 전기차가 아니다 — ★ 「전기」가 함께 들어 있어도
    for no in words.get("not_ev", ()):
        if no and no in got:
            return False
    return any(w and w in got for w in words.get("ev", ()))


_EV_WORDS: dict | None = None


def _ev_words() -> dict:
    """연료 낱말 표 (`config/labels.json` `EV_FUEL_WORDS`)."""
    global _EV_WORDS
    if _EV_WORDS is None:
        import json as _j
        import os as _o

        root = _o.path.dirname(_o.path.dirname(_o.path.dirname(
            _o.path.abspath(__file__))))
        try:
            with open(_o.path.join(root, "config", "labels.json"),
                      encoding="utf-8") as f:
                _EV_WORDS = _j.load(f).get("EV_FUEL_WORDS") or {}
        except (OSError, ValueError):
            _EV_WORDS = {}
    return _EV_WORDS


def _leak(ctx: AxisContext, v: Verdict) -> None:
    s, r = ctx.snapshot, ctx.policy.rule("state")
    # ★★★★★ 09-02 마스터 확정 — ★ **전기차는 누유 만점**이다 (`leak_ev_full`).
    #   ★ 「★ 전기차엔 ★ 엔진오일·미션오일·냉각수 누유가 ★ **구조상 없다**」
    #   ★ ★ 하이브리드엔 ★ **쓰지 마라** — ★ 콜레오스는 그대로 잰다.
    #   ★ ★ ★ 「없어서 0점」이 아니라 ★ 「없을 수가 없어서 만점」이다
    if r.get("leak_ev_full") and _is_ev(ctx):
        put(v, LEAK, ctx.policy.comp(LEAK), PRIO_OBSERVED, "leak_ev_none")
        return
    raw = s.inspection_inner_json
    if raw is None:
        put(v, LEAK, 0, PRIO_OBSERVED, "missing")
        return
    key = leak_state(json.loads(raw))
    put(v, LEAK, r["leak_points"][key], PRIO_OBSERVED, f"leak_{key}")


def _site_never(ctx: AxisContext, axis: str) -> bool:
    """이 사이트가 그 축을 아예 안 주는가 (config/sites.json).

    ★ 사이트 이름을 코드에 박지 않는다 (V3-55).  정본이 표를 갖는다
    """
    site = getattr(ctx.snapshot, "site", None)
    if not site:
        return False
    one = _sites_table().get(site) or {}
    return axis in (one.get("axes_not_provided") or [])


def _sites_table() -> dict:
    """config/sites.json.  ★ 매물마다 파일을 열지 않는다 — 3,528건이다."""
    global _SITES
    if _SITES is None:
        import json as _j
        import os as _o

        root = _o.path.dirname(_o.path.dirname(_o.path.dirname(
            _o.path.abspath(__file__))))
        path = _o.path.join(root, "config", "sites.json")
        try:
            with open(path, encoding="utf-8") as f:
                _SITES = _j.load(f)
        except (OSError, ValueError):
            _SITES = {}
    return _SITES


def _consumable(ctx: AxisContext, v: Verdict) -> None:
    """2-7 소모품 10 — 타이어 트레드 잔량.

    ★ 실측 08-17 — 엔카 점검 원문 300건에 트레드가 하나도 없다.
      그러면 「확인 안 됨 · 0점」이다.  0mm 로 두면 없는 것을 있다고 하는 것이다
    """
    s, r = ctx.snapshot, ctx.policy.rule("state")
    # ★★★★★ 08-30 (마스터 확정 08-29 밤 · r992 ②) — ★ **이 축이 꺼졌다.**
    #   ★ 마스터 — 「소모품을 뺀다.  ★ 있으면 나중에 가점으로」
    #   ★ 배점이 0 이면 ★ 값도 0 이어야 한다 (`analyze/axis/value.py:_market` 과 같다)
    if not ctx.policy.comp(CONSUMABLE):
        put(v, CONSUMABLE, 0, PRIO_OBSERVED, "site_unavailable")
        return
    tread = getattr(s, "tire_tread_mm", None)
    if tread is None:
        # ★ 「우리가 못 받았다」와 「그 사이트가 아예 안 준다」는 다르다 (개정 306).
        #   엔카는 트레드를 unified-report 에만 두고 그 경로가 401 이다 —
        #   로그인 없이는 못 받는다.  우리 잘못이 아니다.
        #   ★ 그래도 분모는 안 줄인다 — 사이트별로 분모를 달리하면
        #     사이트끼리 비교가 안 된다 (규격 금지)
        put(v, CONSUMABLE, 0, PRIO_OBSERVED,
            SITE_UNAVAILABLE if _site_never(ctx, CONSUMABLE) else "missing")
        return
    put(v, CONSUMABLE, round(ascending(-float(tread),
                                       [[-a, b] for a, b in r["tread_curve"]])),
        PRIO_OBSERVED, "tire_tread")


def _integrity(ctx: AxisContext, v: Verdict) -> None:
    """2-8 진정성 5 — 계기판 교환 2 · 불법 구조변경 2 · 튜닝 1.

    ★ 계기판 교환은 주행거리를 못 믿는다는 뜻이다
    ★ 실측 08-17 — 엔카 점검 원문 400건에 mileageStateType 이 전건 null 이다.
      그 2점은 못 준다.  「없다」가 아니라 「모른다」라 0 이다 (개정 325)
    """
    s, r = ctx.snapshot, ctx.policy.rule("state")
    table = r["integrity"]
    if s.inspection_tuning is None:
        put(v, INTEGRITY, 0, PRIO_OBSERVED, "missing")
        return
    got, why = 0, []
    if not s.inspection_tuning:
        got += table["tuning"]
    else:
        why.append("튜닝")
    if s.car_state_ok:
        got += table["structure"]
    elif s.car_state_ok is not None:
        why.append("구조 상태 불량")
    # ★★ 개정 435 — 계기판 상태는 **원문에 있다**.
    #   전에는 「원문에 없다」고 적고 조건 없이 「확인 못 함」을 달았다.
    #   ★ mileageStateType 을 보고 있었는데 그것은 800건 전부 null 이다.
    #     실제 값은 boardStateType 에 있다 (757/800 · v193 실측)
    if s.board_state_ok:
        got += table["cluster"]
    elif s.board_state_ok is None:
        why.append("계기판 확인 못 함")     # 점검부가 없거나 그 칸이 빈 것
    else:
        why.append("계기판 이상")
    # ★ 흠이 없으면 「integrity_」로 꼬리만 남는다 — 읽을 수 없다.  ok 라 적는다
    put(v, INTEGRITY, got, PRIO_OBSERVED,
        "integrity_" + ("+".join(why) if why else "ok"))


def analyze_state(ctx: AxisContext, v: Verdict) -> None:
    _accident(ctx, v)
    _frame(ctx, v)
    _outer(ctx, v)
    _repair(ctx, v)
    _special(ctx, v)
    _leak(ctx, v)
    _consumable(ctx, v)
    _integrity(ctx, v)
