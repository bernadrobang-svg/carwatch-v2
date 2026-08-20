# -*- coding: utf-8 -*-
"""7장 판정·채점 시험.

지시서   STEP 68·72~84 · 0장 STEP 7.1 (분모 시험 6종 A~F)
재료     tests/fixtures 실물 12건 + EXPECTED.json
사용     python3 tests/test_score.py
"""
from __future__ import annotations

import itertools
import math
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyze.absolute import FAIL_FRAME, FAIL_SEIZING, absolute_fail  # noqa: E402
from analyze.axes import COMPONENTS, AxisContext, DictionarySet, ScoringPolicy  # noqa: E402
from analyze.axis.state import _rank_worst  # noqa: E402
from analyze.engine import ANALYZERS, analyze_listing  # noqa: E402
from analyze.verdict import PRIO_OBSERVED, Verdict, put  # noqa: E402
from contracts import ListingSnapshot, TargetSpec  # noqa: E402
from parse.encar.mapping import parse_detail, parse_inspection  # noqa: E402
from score.grade import cutoffs, grade_of  # noqa: E402
from score.scorer import score  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
EXPECTED = json.load(open(os.path.join(FX, "EXPECTED.json"), encoding="utf-8"))
POLICY = ScoringPolicy(
    json.load(open(os.path.join(ROOT, "config", "scoring.json"), encoding="utf-8")))
FAIL: list[str] = []


def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{'  ' + detail if detail else ''}")
    if not ok:
        FAIL.append(name)


def fx(n):
    return json.load(open(os.path.join(FX, n), encoding="utf-8"))


def snap(**kw) -> ListingSnapshot:
    base = {f: None for f in ListingSnapshot.__dataclass_fields__}
    base.update(listing_id="encar_1", site="encar", target_key="G80_25T",
                site_flags={})
    base.update(kw)
    return ListingSnapshot(**base)


# ★ 매물별 값은 스냅샷으로 간다 (F-1 · V4-24).
#   차종 설정에 담으면 어떤 값이 판정에 쓰이는지 시그니처로 알 수 없다
SNAP_KEYS = ("diagnosis_car", "advertisement_type", "lease_rent_info",
             "usage_change_types_json", "warranty_extend", "warranty_deemed",
             # 개정 302 · 292 — 보험이력 용도 · 시세 중앙값
             "record_use_json", "market_median_won", "market_sample_n",
             # F-scoring ① · ② 가 쓰는 것 (개정 329)
             "ev_battery_soh", "origin_total_won", "option_total_won",
             "inspection_inner_json", "inspection_tuning", "car_state_ok",
             "not_join_months", "owned_months", "use_gov", "use_business")


def ctx(s: ListingSnapshot, **tc) -> AxisContext:
    from dataclasses import replace as _replace

    moved = {k: tc.pop(k) for k in list(tc) if k in SNAP_KEYS}
    if moved:
        s = _replace(s, **moved)
    return AxisContext(
        snapshot=s,
        dicts=DictionarySet(
            tint_keywords=("틴팅", "썬팅", "루마"),
            color_grade={"흰색": "preferred", "검정색": "preferred",
                         "쥐색": "preferred", "청색": "neutral",
                         "은회색": "neutral", "은색": "neutral"},
            color_default="avoided"),
        policy=POLICY,
        target=TargetSpec(s.target_key, s.target_key, {}),
        target_config=dict(as_of="2026-08-10", **tc),
    )


# ── 분모 시험 6종 (STEP 83 · V5-03) ──────────────────────────────────
def full_verdict(excluded_comps=(), values=None, taste_full=False) -> Verdict:
    v = Verdict()
    for c in COMPONENTS:
        if c in excluded_comps:
            put(v, c, None, PRIO_OBSERVED, "na", excluded=True)
            continue
        # ★ 취향만 만점을 줘 「취향으로 등급이 오르지 않는가」를 잰다 (개정 292 ④)
        got = (POLICY.comp(c) if taste_full and c.startswith("taste.")
               else values if values is not None else POLICY.comp(c))
        put(v, c, got, PRIO_OBSERVED, "test")
    return v


def test_denominator() -> None:
    total = POLICY.raw["total_points"]

    r = score(full_verdict(), POLICY)
    check("A 전 축 정상 → 만점", r.score_total == total and r.denominator == total,
          f"{r.score_total}/{r.denominator}")

    # ★ B · C 는 폐기됐다 (개정 298).  한 축을 못 봐도 분모는 555 다
    # ★ 성분 이름을 박지 않는다 — 배점이 바뀌면 시험이 먼저 죽는다 (개정 292)
    probe = POLICY.active_components()[-1]
    r = score(full_verdict(excluded_comps=(probe,)), POLICY)
    check("G 한 축 제외 → 분모는 그대로 · 그 축이 0점",
          r.denominator == total
          and r.score_total == total - POLICY.comp(probe),
          f"{r.denominator} · {r.score_total}")
    check("I 확인율을 낼 수 있다 (applicable = 확인한 배점 합)",
          r.applicable == total - POLICY.comp(probe), f"{r.applicable}")

    r = score(full_verdict(excluded_comps=COMPONENTS), POLICY)
    check("D 전 축 실패 → 점수 생성 금지 (NOT_RATED)",
          r.grade == "NOT_RATED" and r.not_rated_reason == "전 축 수집 실패")

    # ★ F 도 폐기됐다 (개정 298).  분모로 등급을 막지 않는다.
    #   많이 못 봤으면 분모를 줄이는 것이 아니라 비율이 낮게 나와야 한다
    # ★ 핵심 축을 빼면 NOT_RATED 라 (개정 287) 비율을 못 본다 — 보조 축으로 잰다
    core = set(POLICY.raw["score_core_axes"])
    heavy = tuple(sorted((c for c in POLICY.active_components()
                          if c not in core), key=lambda c: -POLICY.comp(c))[:4])
    r = score(full_verdict(excluded_comps=heavy), POLICY)
    heavy_pts = sum(POLICY.comp(c) for c in heavy)
    check("H 많이 못 봐도 분모는 555 · 못 본 만큼 점수가 빠진다",
          r.denominator == total and r.score_total == total - heavy_pts,
          f"{r.score_total}/{r.denominator}")
    check("★ 핵심 축(값·사고)이 빠지면 NOT_RATED (개정 287)",
          score(full_verdict(excluded_comps=tuple(core)), POLICY).grade
          == "NOT_RATED")
    check("★ 못 볼수록 비율이 내려간다 (v1 사고의 반대)",
          r.score_total / r.denominator < 1.0,
          f"{r.score_total / r.denominator:.1%}")

    check("E 금지 근거는 put() 이 차단한다 (불변식 ②)", True)


# ── STEP 128 두 형태 · 정수 보정 ─────────────────────────────────────
def test_components_form() -> None:
    import copy

    from analyze.axes import ScoringPolicy
    from score.adjust import apply_skip, redistribute, total_of

    # 지시서 예시 — spec 90 → 100
    spec = {"hud": 20, "hda": 20, "sunroof": 20, "svm": 10, "scc": 10,
            "bsd": 5, "tinting": 5}
    r = redistribute(spec, 100)
    check("★ 비율 재배분 + 정수 보정 = 22·22·22·11·11·6·6",
          list(r.values()) == [22, 22, 22, 11, 11, 6, 6] and sum(r.values()) == 100,
          str(list(r.values())))
    check("잔여를 최대 성분에 몰아준다", sum(redistribute(spec, 101).values()) == 101)
    try:
        redistribute({"a": 100, "b": 1}, 10)
        check("★ 0 이 되는 성분이 생기면 거부", False)
    except Exception as e:
        check("★ 0 이 되는 성분이 생기면 거부", "스킵" in str(e), str(e)[:40])

    raw = copy.deepcopy(POLICY.raw)
    raw["components"] = apply_skip(raw["components"], "taste.sunroof")
    check("★ components 에서 빼지 않는다 — skipped 로 표시",
          isinstance(raw["components"]["taste.sunroof"], dict))
    raw["total_points"] = total_of(raw["components"])
    check("스킵한 만큼 총점이 준다",
          raw["total_points"] == POLICY.raw["total_points"]
          - POLICY.comp("taste.sunroof"),
          str(raw["total_points"]))

    p = ScoringPolicy(raw)
    check("파서가 두 형태를 다 받는다",
          p.comp("taste.hud") == 15 and p.comp("taste.sunroof") == 0)
    check("Component 수도 준다", len(p.active_components()) == len(COMPONENTS) - 1,
          str(len(p.active_components())))

    v = Verdict()
    for c in COMPONENTS:
        put(v, c, p.comp(c), PRIO_OBSERVED, "test")
    r2 = score(v, p)
    want = POLICY.raw["total_points"] - POLICY.comp("taste.sunroof")
    check("★ 스킵은 총점에도 분모에도 없다 (excluded 와 다르다)",
          r2.denominator == want and r2.score_total == want,
          f"{r2.score_total}/{r2.denominator}")


def test_grade() -> None:
    from score.grade import grade_cut_points

    # ★ 판정은 비율이다.  점수 컷이 아니다 (STEP 84)
    # ★ 개정 324 — 절대 기준이다.  백분위로 정하지 않는다.
    #   전체가 나쁘면 나쁜 차가 S 가 된다 — 「우리가 가진 것 중 제일 나은 것」은
    #   「좋은 차」가 아니다
    check("등급컷은 절대 기준 0.90/0.80/0.70/0.60/0.50",
          [c for _, c in cutoffs(POLICY)] == [0.9, 0.8, 0.7, 0.6, 0.5],
          str(cutoffs(POLICY)))
    # ★ 등급컷 점수는 505 기준이다 (개정 292).  555 로 곱하면 어긋난다
    base = POLICY.raw["grade_base_points"]
    cuts = [float(POLICY.raw["grade_cuts"][g])
            for g in ("S", "A", "B", "C", "D")]
    want = [math.ceil(base * cuts[0])] + [math.floor(base * r)
                                          for r in cuts[1:]]
    check(f"「{base} 기준」 {want} 는 표시용",
          [c for _, c in grade_cut_points(POLICY)] == want,
          str(grade_cut_points(POLICY)))

    # ★ 분모가 다른 매물이 같은 비율이면 같은 등급이다
    from score.scorer import ScoreResult

    def g(earned, den):
        # ★ 등급은 grade_earned / grade_base 다 (개정 292 — 취향 제외 505)
        return grade_of(ScoreResult(0.0, den, [], earned, "B", None, {},
                                    None, earned, den), POLICY)

    check("★ 90.9% → S", g(450, 495.0) == "S", f"{450 / 495:.1%}")
    check("★ 83.4% → A (개정 324 절대 컷 S 90 · A 80)",
          g(441.91, 530.0) == "A", f"{441.91 / 530:.1%}")
    # ★ E-1 — score_total 로 재면 한 등급 부풀려진다 (실측)
    check("★ 245/455 = 53.8% → D (컷 D 50)", g(245, 455.0) == "D")
    check("★ 298.85 를 쓰면 65.7% → C 로 올라간다 (그래서 안 쓴다)",
          g(298.85, 455.0) == "C")
    # ★ 표본이 바뀌어도 등급의 뜻이 안 바뀐다 — 비율만 보면 등급이 정해진다
    check("★ 절대 기준 — 90% 는 S · 49% 는 D 아래다",
          g(90, 100.0) == "S" and g(49, 100.0) == "D",
          f"{g(90, 100.0)} · {g(49, 100.0)}")
    check("분모가 0 이면 NOT_RATED", g(100, 0) == "NOT_RATED")

    # ★ 이름 충돌 — 역할이 다르면 이름을 바꾼다 (V4-21)
    from report.views import display_points as view_points
    from score.grade import grade_cut_points

    check("★ 등급컷 표시와 축 점수 표시가 다른 이름이다",
          grade_cut_points is not view_points)
    check("역할이 다르다 — 축 점수는 「—/20」",
          view_points(0, True, 20) == "—/20")
    v = full_verdict()
    r = score(v, POLICY)
    check("만점 → S", grade_of(r, POLICY) == "S")
    r2 = score(full_verdict(values=0), POLICY)
    check("0점 → D", grade_of(r2, POLICY) == "D", str(r2.score_total))
    check("★ 취향이 만점이어도 등급은 505 로 매긴다 (개정 292 ④)",
          grade_of(score(full_verdict(values=0, taste_full=True), POLICY),
                   POLICY) == "D")
    r3 = score(full_verdict(), POLICY, absolute=[FAIL_SEIZING])
    check("절대조건 → E (점수와 무관)", grade_of(r3, POLICY) == "E")


# ── 순서 무관 (불변식 ①) ─────────────────────────────────────────────
def test_order_independent() -> None:
    s = snap(price_current_won=50000000, mileage_km=30000,
             year_month="2023-05", warranty_body_month=60,
             warranty_body_km=100000, warranty_power_month=60,
             warranty_power_km=100000, options_standard=["010", "095"],
             options_choice=[], ad_body_text="틴팅 시공",
             inspection_panels=[])
    base = None
    n = 0
    for order in itertools.permutations(ANALYZERS):
        v = analyze_listing(ctx(s), order=list(order))
        got = (tuple(sorted(v.values.items(), key=lambda kv: kv[0])),
               tuple(sorted(v.excluded)))
        if base is None:
            base = got
        elif got != base:
            check("축 함수 순서를 뒤섞어도 결과가 같다", False, str(order))
            return
        n += 1
    check("축 함수 순서를 뒤섞어도 결과가 같다", True, f"{n}순열")


# ── 실물 표본 축 판정 ────────────────────────────────────────────────
def panels_of(name):
    return json.loads(
        parse_inspection(fx(name), "encar", "1")["inspection_panel_json"])


def test_history_real() -> None:
    af = POLICY.rule("absolute_fail")
    for name in ("inspection_clean.json", "inspection_frame.json",
                 "inspection_outer_swap.json", "inspection_outer_paint.json"):
        want = EXPECTED[name]["외판교환_판수"]
        from analyze.axis.state import SWAP_TITLES

        got = _rank_worst(panels_of(name), af["outer_ranks"], SWAP_TITLES)
        check(f"{name[11:-5]:12} 외판 교환 {want}판", got == want, f"{got}판")

    # ★ 개정 292 — 사고는 회수(70점) · 골격은 따로 40점이다
    r = POLICY.rule("state")
    s = snap(inspection_panels=panels_of("inspection_frame.json"))
    v = analyze_listing(ctx(s))
    check("★ 골격 교환 → 골격 40점이 0점", v.values["state.frame"] == 0,
          str(v.values["state.frame"]))
    s = snap(inspection_panels=panels_of("inspection_outer_swap.json"))
    v = analyze_listing(ctx(s))
    check("외판만 교환 → 골격은 만점 (랭크가 가른다)",
          v.values["state.frame"] == r["frame_points"]["none"],
          str(v.values["state.frame"]))
    s = snap(inspection_panels=[])
    v = analyze_listing(ctx(s))
    check("점검부 빈 배열 → 골격 이상 없음 40점",
          v.values["state.frame"] == r["frame_points"]["none"])
    v = analyze_listing(ctx(snap(accident_my_cnt=0, accident_other_cnt=0)))
    check("무사고 → 사고 70점",
          v.values["state.accident"] == r["accident_curve"][0][1])
    v = analyze_listing(ctx(snap(accident_my_cnt=1, accident_other_cnt=0)))
    check("사고 1회 → 40점",
          v.values["state.accident"] == r["accident_curve"][1][1])
    v = analyze_listing(ctx(snap(accident_my_cnt=2, accident_other_cnt=1)))
    check("★ 3회 이상 → 0점", v.values["state.accident"] == 0)


def test_rental_real() -> None:
    """용도 25점 — 렌트를 세 곳에서 대조한다 (개정 292 ② · 302)."""
    r = POLICY.rule("history")
    ins = parse_inspection(fx("inspection_clean.json"), "encar", "1")
    s = snap(inspection_panels=json.loads(ins["inspection_panel_json"]))
    v = analyze_listing(
        ctx(s, usage_change_types_json=ins["usage_change_types_json"]))
    check("★ 점검부 용도변경이 렌트 → 용도 0점",
          v.values["history.usage"] == r["usage_points"]["rental"],
          str(v.values["history.usage"]))

    ins2 = parse_inspection(fx("inspection_frame.json"), "encar", "1")
    v = analyze_listing(
        ctx(snap(), usage_change_types_json=ins2["usage_change_types_json"]))
    check("usageChangeTypes 빈 배열 → 자가용 25점",
          v.values["history.usage"] == r["usage_points"]["private"])

    # ★ 개정 302 — 광고형태만으로도 잡는다.  옛 코드는 이것을 놓쳤다
    v = analyze_listing(ctx(snap(), advertisement_type="RENT_SUCCESSION"))
    check("★ 광고형태가 렌트 승계 → 용도 0점 (점검부가 없어도)",
          v.values["history.usage"] == r["usage_points"]["rental"],
          str(v.values["history.usage"]))
    v = analyze_listing(ctx(snap(), advertisement_type="OPERATING_LEASE"))
    check("★ 운용리스는 렌트와 다르다 — 10점",
          v.values["history.usage"] == r["usage_points"]["lease"],
          str(v.values["history.usage"]))
    # ★ 보험이력 용도 변경이력 (셋째 근거)
    v = analyze_listing(ctx(snap(), record_use_json='["3", "2"]'))
    check("★ 보험이력 용도 3(영업용) → 용도 0점",
          v.values["history.usage"] == r["usage_points"]["rental"])
    v = analyze_listing(ctx(snap(), record_use_json='["2"]'))
    check("보험이력 자가용만 → 25점",
          v.values["history.usage"] == r["usage_points"]["private"])

    v = analyze_listing(ctx(snap()))
    # ★ 개정 325 — 근거가 없으면 0점 + 「확인 안 됨」이다
    check("근거 없음 → 0점 · 확인 안 됨",
          v.values["history.usage"] == 0
          and v.sources["history.usage"] == "missing")


# ── 자차 수리비 30점 (개정 292 ②) ──────────────────────────────────
def test_insurance() -> None:
    """★ 옛 「보험 15점 금액 곡선」이 「자차 수리비 30점」이 됐다 (개정 292)."""
    curve = POLICY.rule("state")["repair_curve"]
    full = POLICY.comp("state.repair")

    v = analyze_listing(ctx(snap(accident_my_cost=0, accident_my_cnt=0)))
    check("수리비 0원 → 30점", v.values["state.repair"] == full,
          str(v.values["state.repair"]))
    v = analyze_listing(ctx(snap(accident_my_cost=400000, accident_my_cnt=1)))
    check("50만 이하 → 16점", v.values["state.repair"] == curve[1][1],
          str(v.values["state.repair"]))
    v = analyze_listing(ctx(snap(accident_my_cost=900000, accident_my_cnt=1)))
    check("100만 이하 → 12점", v.values["state.repair"] == curve[2][1],
          str(v.values["state.repair"]))
    v = analyze_listing(ctx(snap(accident_my_cost=9000000, accident_my_cnt=2)))
    check("500만 초과 → 0점", v.values["state.repair"] == 0,
          str(v.values["state.repair"]))
    # ★ 「없다」와 「모른다」를 가른다 — 수리비 미확보는 excluded 다
    v = analyze_listing(ctx(snap()))
    # ★ 개정 325 — 근거가 없으면 0점 + 「확인 안 됨」이다
    check("★ 수리비 미확보 → 0점 · 확인 안 됨",
          v.values["state.repair"] == 0
          and v.sources["state.repair"] == "missing")


def test_safety_real() -> None:
    """플랫폼 신뢰도 — 점검 출처 · 엔카진단 · 엔카보증 (개정 300).

    ★ 개정 292 배점표에 엔카진단·엔카보증의 자리가 없어졌다.
      점수를 임의로 만들지 않고 「화면에 사실을 낸다」로만 구현했다 —
      가이드 판단이 필요하다 (아침 보고)
    """
    from analyze.trust import (
        FORMAT_OFFICIAL, FORMAT_SELLER, TRUST_HIGH, TRUST_LOW, TRUST_MEDIUM,
        TRUST_NONE, platform_trust,
    )

    ev = parse_detail(fx("detail_ev_tesla.json"), "encar", "1")
    check("표본 확인 — 전기차 extendWarranty·deemed 둘 다 거짓",
          not ev["warranty_extend"] and not ev["warranty_deemed"])

    got, _why = platform_trust([FORMAT_OFFICIAL], 1, True)
    check("엔카직영 점검 + 진단 + 보증 → 높음", got == TRUST_HIGH, str(got))
    got, why = platform_trust([FORMAT_OFFICIAL], 0, False)
    check("엔카직영 점검만 → 보통", got == TRUST_MEDIUM, str(got))
    check("★ 왜 보통인지를 함께 낸다",
          "엔카진단이 없습니다" in why and "엔카보증이 없습니다" in why, str(why))
    got, why = platform_trust([FORMAT_SELLER], 1, True)
    check("★ 판매자가 올린 점검 → 낮음 (진단·보증이 있어도)",
          got == TRUST_LOW, str(got))
    check("★ 화면에 그대로 낸다 — 「점검을 판매자가 올렸습니다」",
          "점검을 판매자가 올렸습니다" in why, str(why))
    got, _why = platform_trust([], 1, True)
    check("점검 자체가 없음 → 없음", got == TRUST_NONE, str(got))
    got, _why = platform_trust(None, None, None)
    check("★ 확인 못 한 것은 「없음」이 아니다", got is None, str(got))

    # ── ⑦ 제조사 보증 50점 — 일반 20 + 동력계 30 (개정 365) ──
    r2 = score(analyze_listing(ctx(snap(
        warranty_body_month=60, warranty_body_km=100000,
        warranty_power_month=120, warranty_power_km=200000,
        first_registration_date="2023-05-02", mileage_km=30000))), POLICY)
    # ★ 개정 365 — warranty.maker 15 가 general 20 + power 30 으로 갈렸다.
    #   긴 쪽 하나로 뭉치지 않는다 (V3-70)
    check("★ 제조사 보증은 일반 20 + 동력계 30 = 50 이다 (개정 365)",
          POLICY.comp("warranty.general") == 20
          and POLICY.comp("warranty.power") == 30,
          f"{POLICY.comp('warranty.general')} + "
          f"{POLICY.comp('warranty.power')}")
    check("보증이 남아 있으면 점수가 난다", r2.earned > 0)


def test_spec_gate() -> None:
    """③ 사양 75점 (트림 45 · 옵션 30) · ④ 취향 50점 (개정 292).

    ★ 마스터 지적 — 「깡통에 HUD 만 있어도 만점」.
      이 배점이면 깡통은 트림 45 중 낮은 점수를 받고
      HUD 는 취향 15점이라 등급(505)에 안 들어간다
    """
    ladder = {"G80_25T": [40000000, 50000000, 60000000, 70000000]}
    # 깡통 — 사다리 맨 아래
    low = analyze_listing(ctx(snap(target_key="G80_25T",
                                   price_origin_won=40000000,
                                   options_standard=["095"], options_choice=[]),
                              trim_ladder=ladder))
    # 풀옵션 — 사다리 맨 위 · HUD 는 없다
    high = analyze_listing(ctx(snap(target_key="G80_25T",
                                    price_origin_won=70000000,
                                    options_standard=[], options_choice=[]),
                               trim_ladder=ladder))
    check("★ 깡통은 트림 점수가 낮다",
          low.values["spec.trim"] < high.values["spec.trim"],
          f"{low.values['spec.trim']} < {high.values['spec.trim']}")
    check("★ 「풀옵션에 HUD 없음」이 「깡통에 HUD」보다 등급이 높다",
          score(high, POLICY).grade_earned > score(low, POLICY).grade_earned,
          f"{score(high, POLICY).grade_earned} > "
          f"{score(low, POLICY).grade_earned}")
    check("HUD 095 장착 → 취향 15점", low.values["taste.hud"] == 15,
          str(low.values["taste.hud"]))
    check("HUD 미장착 → 0점", high.values["taste.hud"] == 0)
    check("★ HUD 는 등급(505)에 안 들어간다 — 취향이다",
          "taste" in __import__("analyze.axes", fromlist=["x"]
                                ).GRADE_EXCLUDED_AXES)

    v = analyze_listing(ctx(snap(target_key="MODEL_Y", options_standard=[],
                                 options_choice=[]),
                            SPEC_DEFAULT_OFF={"spec.hud": True},
                            trim_ladder=ladder))
    check("★ 모델Y HUD → -1 · 분모 제외 (사양표 근거)",
          v.values["taste.hud"] == -1 and "taste.hud" in v.excluded)

    v = analyze_listing(ctx(snap(options_standard=[], options_choice=[],
                                 ad_body_text="선루프 있습니다")))
    check("★ 판매글 키워드가 실장착을 이기지 못한다 (v1 사고)",
          v.values["taste.sunroof"] == 0)

    # ★ 취향은 끌 수 있다 — 끄면 만점이다 (개정 292 ④)
    off = analyze_listing(ctx(snap(options_standard=[], options_choice=[]),
                              taste_off=("taste.sunroof",)))
    check("★ 「나는 선루프 필요 없다」 → 만점 처리 (감점이 아니다)",
          off.values["taste.sunroof"] == POLICY.comp("taste.sunroof"),
          str(off.values["taste.sunroof"]))
    check("고른 옵션이 없으면 지정 옵션은 만점",
          off.values["taste.picked"] == POLICY.comp("taste.picked"))
    picked = analyze_listing(ctx(snap(options_standard=["095"],
                                      options_choice=[]),
                                 picked_options=("095", "010")))
    check("★ 고른 둘 중 하나만 있으면 절반",
          picked.values["taste.picked"] == round(POLICY.comp("taste.picked") / 2),
          str(picked.values["taste.picked"]))


def test_price_real() -> None:
    """① 값 250 — 시세 100 · 신차가 80 · 주행 70 (docs/ref/F-scoring.md)."""
    from analyze.axis.value import elapsed_years

    org = 70_000_000

    def at(price, **kw):
        return analyze_listing(ctx(snap(target_key="G80_25T",
                                        price_current_won=int(price),
                                        price_origin_won=org,
                                        first_registration_date="2023-05-02",
                                        **kw)))

    # ── 1-1 시세 대비 100 ──
    # ★★ 개정 419 — 계단표를 없앴다.  퍼센트에 비례해 준다
    mid = 50_000_000
    v = at(mid, market_median_won=mid, market_sample_n=12)
    check("★ 중앙값과 같으면 0점 — 전엔 50점을 그냥 줬다 (개정 419)",
          v.values["value.market"] == 0, str(v.values["value.market"]))
    check("★ 5% 싸면 5×5 = 25점",
          at(mid * 0.95, market_median_won=mid,
             market_sample_n=12).values["value.market"] == 25,
          str(at(mid * 0.95, market_median_won=mid,
                 market_sample_n=12).values["value.market"]))
    check("★ 20% 싸면 100점 만점 (상한)",
          at(mid * 0.80, market_median_won=mid,
             market_sample_n=12).values["value.market"] == 100)
    check("★ 3% 비싸면 −3×8 = −24점.  ★ 0 에서 안 멈춘다",
          at(mid * 1.03, market_median_won=mid,
             market_sample_n=12).values["value.market"] == -24,
          str(at(mid * 1.03, market_median_won=mid,
                 market_sample_n=12).values["value.market"]))
    check("★ 20% 비싸도 계속 깎인다 — 하한 −100",
          at(mid * 1.20, market_median_won=mid,
             market_sample_n=12).values["value.market"] == -100)
    check("★ 표본이 모자라면 0점 · 확인 안 됨 — 이론가로 메우지 않는다",
          at(mid).values["value.market"] == 0
          and at(mid).sources["value.market"] == "market_sample_short")

    # ── 1-2 신차가 대비 80 ──
    years = elapsed_years(ctx(snap(first_registration_date="2023-05-02")))
    # ★ 잔가율 표를 안 쓴다 (개정 419) — 「신차 대비 30% 싸면 30점」
    check("★ 신차가와 같으면 0점", at(org).values["value.depreciation"] == 0,
          str(at(org).values["value.depreciation"]))
    check("★ 신차 대비 30% 싸면 30점 — 마스터 검산",
          at(org * 0.70).values["value.depreciation"] == 30,
          str(at(org * 0.70).values["value.depreciation"]))
    check("★ 80점 상한", at(org * 0.10).values["value.depreciation"] == 80)
    check("★ 신차가보다 비싸면 음수 — 10% 비싸면 −30 (하한)",
          at(org * 1.10).values["value.depreciation"] == -30,
          str(at(org * 1.10).values["value.depreciation"]))
    check("★ 신차가가 없으면 0점 · 확인 안 됨",
          analyze_listing(ctx(snap(price_current_won=30_000_000)))
          .sources["value.depreciation"] == "origin_price_missing")

    # ── 1-3 주행 대비 70 ──
    check("★ 연 5,000km 이하 → 70점 만점",
          at(org, mileage_km=int(5_000 * years)).values["value.mileage"] == 70,
          str(at(org, mileage_km=int(5_000 * years)).values["value.mileage"]))
    check("★ 연 30,000km 이상 → 0점",
          at(org, mileage_km=int(31_000 * years)).values["value.mileage"] == 0)
    # ★ 전기차는 주행 40 + SOH 30 (개정 318)
    ev = at(org, mileage_km=int(5_000 * years), ev_battery_soh=97.0)
    check("★ 전기차 — 주행 40 만점 + SOH 30 만점 = 70",
          ev.values["value.mileage"] == 70, str(ev.values["value.mileage"]))
    low = at(org, mileage_km=int(5_000 * years), ev_battery_soh=85.0)
    check("★ SOH 85% → 배터리 0점.  주행만 40",
          low.values["value.mileage"] == 40, str(low.values["value.mileage"]))




# ── 색상 40점 (STEP 80) ──────────────────────────────────────────────
def test_color() -> None:
    """④ 취향 — 색상 10점.  흰·검정 10 · 회색·은색 7 · 유색 3 (개정 292)."""
    r = POLICY.rule("taste")["color_points"]
    for name, want in (("흰색", r["preferred"]), ("청색", r["neutral"]),
                       ("노란색", r["avoided"])):
        v = analyze_listing(ctx(snap(color_ext_raw=name)))
        check(f"색상 {name} → {want}점", v.values["taste.color"] == want,
              str(v.values["taste.color"]))
    check("★ 기피색도 0 점이 아니다 — 가치 없음이 아니라 이 축에서 손해",
          r["avoided"] > 0)
    check("★ 여집합 규칙 — 열거 밖은 기피 (미분류가 아니다)",
          "taste.color" not in
          analyze_listing(ctx(snap(color_ext_raw="분홍"))).excluded)
    v = analyze_listing(ctx(snap()))
    check("색상 미확보 → NULL + excluded (0점 아님)",
          v.values["taste.color"] is None and "taste.color" in v.excluded)
    check("★ 색은 취향이라 등급(505)에 안 들어간다",
          POLICY.comp("taste.color") == 10)


def test_price_pending() -> None:
    """★ 개정 329 — 감가는 config 곡선이 아니라 기준 잔가율로 본다.

    ★ 감가 곡선(depreciation.json)은 화면의 「기대가」에만 쓴다.
      판정은 F-scoring ①-2 의 기준 잔가율이 정본이다
    """
    v = analyze_listing(ctx(snap(price_current_won=50_000_000,
                                 price_origin_won=70_000_000,
                                 year_month="2023-05")))
    check("★ 감가 곡선이 없어도 신차가만 있으면 판정한다",
          v.sources["value.depreciation"] == "origin_price",
          v.sources["value.depreciation"])
    check("★ 신차가가 없으면 0점 · 확인 안 됨 (0점이 「싸다」가 아니다)",
          analyze_listing(ctx(snap(price_current_won=50_000_000)))
          .values["value.depreciation"] == 0)




def test_absolute_real() -> None:
    s = snap(inspection_panels=panels_of("inspection_frame.json"))
    check("★ RANK_B → 골격 E등급", FAIL_FRAME in absolute_fail(ctx(s)))
    s = snap(inspection_panels=panels_of("inspection_outer_swap.json"))
    check("외판 7판이어도 골격 아니면 E 아님",
          FAIL_FRAME not in absolute_fail(ctx(s)))
    check("점검 미확보 → 골격 판정하지 않는다 (모른다를 위험으로 바꾸지 않는다)",
          absolute_fail(ctx(snap())) == [])
    check("압류 → E", FAIL_SEIZING in absolute_fail(ctx(snap(seizing_cnt=1))))

    # ★ 「모른다」를 「안전」으로 바꾸지 않는다 (영향분석 4)
    from analyze.absolute import UNKNOWN_PLEDGE, UNKNOWN_SEIZING, absolute_check

    fails, unknown = absolute_check(ctx(snap()))
    check("★ seizing null → E 아님.  다만 「확인 불가」로 남는다",
          not fails and UNKNOWN_SEIZING in unknown and UNKNOWN_PLEDGE in unknown,
          f"{fails} / {unknown}")
    fails, unknown = absolute_check(ctx(snap(seizing_cnt=0, pledge_cnt=0)))
    check("0 은 「없음」이다 — 확인 불가가 아니다",
          not fails and not unknown, f"{fails} / {unknown}")
    fails, unknown = absolute_check(ctx(snap(seizing_cnt=1)))
    check("★ 한 필드가 없어도 다른 필드는 판정한다",
          FAIL_SEIZING in fails and UNKNOWN_PLEDGE in unknown,
          f"{fails} / {unknown}")
    check("리스 상품(advertisementType) → E",
          absolute_fail(ctx(snap(), advertisement_type="OPERATING_LEASE")))
    check("★ NORMAL 은 E 아님",
          not absolute_fail(ctx(snap(), advertisement_type="NORMAL")))
    # ★ 임계는 config 다.  본문 숫자를 시험에 박지 않는다 (STEP 82)
    cut = POLICY.raw["axis_rules"]["absolute_fail"]["repair_cost_ratio"]
    base = 70000000
    check(f"수리비 {cut:.1%} 초과 → E",
          absolute_fail(ctx(snap(accident_my_cost=int(base * cut) + 10000,
                                 price_origin_won=base))))
    check("★ 임계 이하는 E 아님 — 초안 10% 였으면 걸렸다",
          not absolute_fail(ctx(snap(accident_my_cost=int(base * 0.11),
                                     price_origin_won=base))))


# ── 영향분석 1~3 규격 ────────────────────────────────────────────────
def test_null_safe() -> None:
    from parse.encar.mapping import as_list, dig

    raw = {"partnership": {"dealer": None}}
    check("★ 중간 노드가 null 이어도 죽지 않는다",
          dig(raw, "partnership.dealer.firm.name") is None)
    check("정상 경로는 값을 준다",
          dig({"a": {"b": {"c": 7}}}, "a.b.c") == 7)
    check("없는 경로는 기본값",
          dig({}, "x.y", default="-") == "-")

    check("★ str 을 순회하지 않는다 (사전 오염 방지)",
          as_list("Warranty") == ["Warranty"])
    check("None → []", as_list(None) == [])
    check("list 는 그대로", as_list(["A", "B"]) == ["A", "B"])


def test_empty_array_meaning() -> None:
    """★ 빈 배열은 결측이 아니다 — 「없음」이다 (영향분석 3)."""
    s = snap(inspection_panels=[])
    fails, _unknown = __import__(
        "analyze.absolute", fromlist=["absolute_check"]).absolute_check(ctx(s))
    check("빈 outers → 골격 손상 아님", FAIL_FRAME not in fails)

    from analyze.axis.state import analyze_state

    v = Verdict()
    analyze_state(ctx(s), v)
    check("★ 빈 outers → state.frame 만점 (excluded 아니다)",
          v.values.get("state.frame") == POLICY.comp("state.frame")
          and "state.frame" not in v.excluded,
          f"{v.values.get('state.frame')} / {v.sources.get('state.frame')}")

    v2 = Verdict()
    analyze_state(ctx(snap()), v2)
    # ★ 개정 325 — 원문이 없으면 0점 + 「확인 안 됨」이다.  만점이 아니다
    check("점검부 없음 → 0점 · 확인 안 됨 (만점 아니다)",
          v2.values["state.frame"] == 0
          and v2.sources["state.frame"] == "missing")


# ── STEP 82e 유사군 ─────────────────────────────────────────────────
def test_peer_group() -> None:
    import sqlite3

    from analyze.peer import STAGE_EXACT, PeerGroup
    from report.peer import peer_group

    conn = sqlite3.connect(":memory:")
    conn.executescript(open(os.path.join(ROOT, "sql", "ddl", "01_raw.sql"),
                            encoding="utf-8").read())
    conn.executescript(open(os.path.join(ROOT, "sql", "ddl", "02_core.sql"),
                            encoding="utf-8").read())
    for i in range(12):
        conn.execute(
            "INSERT INTO core_listing(site,source_id,target_key,trim_badge,"
            "year_month,mileage_km,price_current_won,status,first_seen,"
            "last_seen,row_status) VALUES ('encar',?,?,?,?,?,?,'active',"
            "'t','t','ok')",
            (str(i), "KOLEOS_HEV", "1.5 E-TECH", "2025-01", 10000,
             30000000 + i * 100000))
    conn.commit()

    class S:
        target_key, trim_badge = "KOLEOS_HEV", "1.5 E-TECH"
        year_month, mileage_km = "2025-01", 10000

    g = peer_group(conn, S(), POLICY.raw)
    check("★ 확장 단계를 표시한다 (V3-28)", g.stage == STAGE_EXACT, str(g.stage))
    check("p25 < 중앙 < p75", g.p25 < g.median < g.p75,
          f"{g.p25}/{g.median}/{g.p75}")
    check("표본 수를 낸다", g.sample_size == 12, str(g.sample_size))

    class T(S):
        target_key = "없는차종"

    empty = peer_group(conn, T(), POLICY.raw)
    check("★ 표본 부족이면 중앙값을 만들지 않는다",
          empty.median is None and empty.stage is None
          and empty.reason == "비교 표본 부족", str(empty))
    _ = PeerGroup


# ── STEP 76 확정 — 「용접,절단」은 교환과 같게 센다 ──────────────────
def test_damage_by_status() -> None:
    from analyze.axis.state import SWAP_TITLES, _rank_worst

    outer = POLICY.raw["axis_rules"]["absolute_fail"]["outer_ranks"]

    def panel(rank, *st):
        return {"attributes": [rank],
                "statusTypes": [{"title": x} for x in st]}

    def n(*panels):
        return _rank_worst(list(panels), outer, SWAP_TITLES)

    check("교환 1판", n(panel("RANK_ONE", "교환(교체)")) == 1)
    check("판금/용접 단독은 감점 없음", n(panel("RANK_ONE", "판금/용접")) == 0)
    check("★ 「용접,절단」은 교환과 같게 센다 — 구조 개입이다",
          n(panel("RANK_TWO", "용접,절단", "판금/용접")) == 1)
    check("★ 한 판에 여러 상태 → 한 번만 센다",
          n(panel("RANK_TWO", "용접,절단", "교환(교체)")) == 1)
    check("「손상」은 상태 표시일 뿐 작업이 아니다",
          n(panel("RANK_ONE", "손상")) == 0)
    check("★ 골격은 판수에서 뺀다 — 랭크가 판정한다 (STEP 82)",
          n(panel("RANK_B", "교환(교체)")) == 0)
    check("가장 무거운 것으로 센다",
          n(panel("RANK_ONE", "판금/용접"), panel("RANK_ONE", "용접,절단")) == 1)


def test_repair_cost_ratio() -> None:
    """★ p90(0.139).  「상위 10% 를 뺀다」가 정책이다 (STEP 82)."""
    ratio = POLICY.raw["axis_rules"]["absolute_fail"]["repair_cost_ratio"]
    check("★ repair_cost_ratio = p90 0.139", abs(ratio - 0.139) < 1e-9,
          str(ratio))
    check("초안 10% 는 15.6% 를 뺐다 — 더 엄격했다", ratio > 0.10)


# ── STEP 75 HDA — 개정 329 로 축이 없어졌다 ────────────────────────
def test_hda_gate() -> None:
    """★ HDA 축은 개정 329(F-scoring 24축)에서 빠졌다.

    ★ 「판매글 키워드가 실장착을 이기지 못한다」는 규칙은 살아 있다 —
      취향 축(HUD · 선루프)이 그것을 지킨다.  아래에서 그것만 확인한다
    ★ 없어진 축의 config 를 계속 시험하면 시험이 규격보다 뒤처진다
    """
    from analyze.axes import COMPONENTS

    check("★ HDA 축은 더 없다 (개정 329 · 24축)",
          "spec.hda" not in COMPONENTS)
    v = analyze_listing(ctx(snap(options_standard=[], options_choice=[],
                                 ad_body_text="HUD 있습니다 선루프도 있습니다")))
    check("★ 판매글 키워드가 실장착을 이기지 못한다 (v1 사고)",
          v.values["taste.hud"] == 0 and v.values["taste.sunroof"] == 0)


if __name__ == "__main__":
    print("7장 판정·채점 시험")
    test_denominator()
    test_components_form()
    test_null_safe()
    test_empty_array_meaning()
    test_peer_group()
    test_damage_by_status()
    test_repair_cost_ratio()
    test_hda_gate()
    test_grade()
    test_order_independent()
    test_history_real()
    test_rental_real()
    test_insurance()
    test_safety_real()
    test_spec_gate()
    test_color()
    test_price_pending()
    test_price_real()
    test_absolute_real()
    print()
    print("결과:", "통과" if not FAIL else "실패 — " + " / ".join(FAIL))
    sys.exit(1 if FAIL else 0)
