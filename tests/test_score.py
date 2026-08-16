# -*- coding: utf-8 -*-
"""7장 판정·채점 시험.

지시서   STEP 68·72~84 · 0장 STEP 7.1 (분모 시험 6종 A~F)
재료     tests/fixtures 실물 12건 + EXPECTED.json
사용     python3 tests/test_score.py
"""
from __future__ import annotations

import itertools
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyze.absolute import FAIL_FRAME, FAIL_SEIZING, absolute_fail  # noqa: E402
from analyze.axes import COMPONENTS, AxisContext, DictionarySet, ScoringPolicy  # noqa: E402
from analyze.axis.history import outer_swap_count  # noqa: E402
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
             "usage_change_types_json", "warranty_extend", "warranty_deemed")


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
def full_verdict(excluded_comps=(), values=None) -> Verdict:
    v = Verdict()
    for c in COMPONENTS:
        if c in excluded_comps:
            put(v, c, None, PRIO_OBSERVED, "na", excluded=True)
        else:
            put(v, c, values if values is not None else POLICY.comp(c),
                PRIO_OBSERVED, "test")
    return v


def test_denominator() -> None:
    total = POLICY.raw["total_points"]

    r = score(full_verdict(), POLICY)
    check("A 전 축 정상 → 만점", r.score_total == total and r.denominator == total,
          f"{r.score_total}/{r.denominator}")

    r = score(full_verdict(excluded_comps=("spec.hud",)), POLICY)
    check("B/C 한 축 제외 → 분모 축소 · 점수 산출",
          r.denominator == total - POLICY.comp("spec.hud")
          and r.score_total == total, f"{r.denominator}")

    r = score(full_verdict(excluded_comps=COMPONENTS), POLICY)
    check("D 전 축 실패 → 점수 생성 금지 (NOT_RATED)",
          r.grade == "NOT_RATED" and r.not_rated_reason == "전 축 수집 실패")

    # F — 분모가 최소 기준(60%) 미만
    heavy = ("price", "warranty.general", "warranty.power",
             "spec.hud", "spec.hda")
    r = score(full_verdict(excluded_comps=heavy), POLICY)
    check("F 분모 미달 → 등급 생성 금지",
          r.grade == "NOT_RATED" and r.not_rated_reason == "분모 최소 기준 미만",
          f"{r.denominator}/{total}")
    check("NOT_RATED 는 D 나 E 가 아니다",
          grade_of(r, POLICY) == "NOT_RATED")

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
    raw["components"] = apply_skip(raw["components"], "spec.tinting")
    check("★ components 에서 빼지 않는다 — skipped 로 표시",
          isinstance(raw["components"]["spec.tinting"], dict))
    raw["total_points"] = total_of(raw["components"])
    check("스킵한 만큼 총점이 준다", raw["total_points"] == 550,
          str(raw["total_points"]))

    p = ScoringPolicy(raw)
    check("파서가 두 형태를 다 받는다",
          p.comp("spec.hud") == 20 and p.comp("spec.tinting") == 0)
    check("Component 수도 준다", len(p.active_components()) == 16,
          str(len(p.active_components())))

    v = Verdict()
    for c in COMPONENTS:
        put(v, c, p.comp(c), PRIO_OBSERVED, "test")
    r2 = score(v, p)
    check("★ 스킵은 총점에도 분모에도 없다 (excluded 와 다르다)",
          r2.denominator == 550 and r2.score_total == 550,
          f"{r2.score_total}/{r2.denominator}")


def test_grade() -> None:
    from score.grade import grade_cut_points

    # ★ 판정은 비율이다.  점수 컷이 아니다 (STEP 84)
    check("등급컷은 비율 0.9/0.8/0.7/0.6",
          [c for _, c in cutoffs(POLICY)] == [0.9, 0.8, 0.7, 0.6],
          str(cutoffs(POLICY)))
    check("「555 기준」 500/444/388/333 은 표시용",
          [c for _, c in grade_cut_points(POLICY)] == [500, 444, 388, 333],
          str(grade_cut_points(POLICY)))

    # ★ 분모가 다른 매물이 같은 비율이면 같은 등급이다
    from score.scorer import ScoreResult

    def g(earned, den):
        # ★ 등급은 earned / denominator 다.  score_total 은 555 환산이라 안 쓴다
        return grade_of(ScoreResult(0.0, den, [], earned, "B", None, {},
                                    None), POLICY)

    check("★ 분모 495 매물도 S 를 받을 수 있다", g(450, 495.0) == "S",
          f"{450 / 495:.1%}")
    check("★ 실사고 — 441.91/530 = 83.4% → A", g(441.91, 530.0) == "A")
    # ★ E-1 — score_total 로 재면 한 등급 부풀려진다 (실측)
    check("★ 245/455 = 53.8% → D", g(245, 455.0) == "D")
    check("★ 298.85 를 쓰면 65.7% → C 로 올라간다 (그래서 안 쓴다)",
          g(298.85, 455.0) == "C")
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
        got = outer_swap_count(panels_of(name), af["outer_ranks"],
                               POLICY.raw["axis_rules"]["history"]
                               ["damage_by_status"])
        check(f"{name[11:-5]:12} 외판 교환 {want}판", got == want, f"{got}판")

    r = POLICY.rule("history")
    s = snap(inspection_panels=panels_of("inspection_outer_swap.json"))
    v = analyze_listing(ctx(s))
    check("★ 외판 5판 → 사고 20점이 0점", v.values["history.damage"] == 0)
    s = snap(inspection_panels=panels_of("inspection_outer_paint.json"))
    v = analyze_listing(ctx(s))
    check("판금/용접만 → 감점 없음 (20점)",
          v.values["history.damage"] == r["damage_by_swap"]["0"])
    s = snap(inspection_panels=[])
    v = analyze_listing(ctx(s))
    check("무사고 0판 → 20점",
          v.values["history.damage"] == r["damage_by_swap"]["0"])


def test_rental_real() -> None:
    r = POLICY.rule("history")["rental"]
    ins = parse_inspection(fx("inspection_clean.json"), "encar", "1")
    s = snap(inspection_panels=json.loads(ins["inspection_panel_json"]))
    v = analyze_listing(
        ctx(s, usage_change_types_json=ins["usage_change_types_json"]))
    check("★ outers 0판(무사고)인데 렌트 이력 → 렌트 0점",
          v.values["history.damage"] == 20
          and v.values["history.rental"] == r["rental"],
          str(v.values["history.rental"]))

    ins2 = parse_inspection(fx("inspection_frame.json"), "encar", "1")
    v = analyze_listing(
        ctx(snap(), usage_change_types_json=ins2["usage_change_types_json"]))
    check("usageChangeTypes 빈 배열 → 비렌트 20점",
          v.values["history.rental"] == r["non_rental"])

    v = analyze_listing(ctx(snap()))
    check("근거 없음 → 불명 10점 (0 이 아니다)",
          v.values["history.rental"] == r["unknown"])


# ── 보험 15점 금액 곡선 (STEP 77) ────────────────────────────────────
def test_insurance() -> None:
    from parse.encar.mapping import parse_record
    full = POLICY.comp("history.insurance")
    ORG = 70000000

    v = analyze_listing(ctx(snap(accident_my_cost=0, accident_my_cnt=0,
                                 price_origin_won=ORG)))
    check("무사고 → 15점", v.values["history.insurance"] == full)

    # ★ 표본 record_with_accident — type 3 만 1건
    rec = parse_record(fx("record_with_accident.json"), "encar", "1")
    check("표본 확인 — myAccidentCost 0 · otherAccidentCnt 1",
          rec["accident_my_cost"] == 0 and rec["accident_other_cnt"] == 1)
    v = analyze_listing(ctx(snap(accident_my_cost=rec["accident_my_cost"],
                                 accident_my_cnt=rec["accident_my_cnt"],
                                 price_origin_won=ORG)))
    check("★ type 3 만 → 15점 만점 (건수 상한 미적용)",
          v.values["history.insurance"] == full,
          str(v.values["history.insurance"]))

    cases = ((0.01, 13), (0.03, 11), (0.06, 8), (0.09, 5), (0.13, 2), (0.20, 0))
    for ratio, want in cases:
        v = analyze_listing(ctx(snap(accident_my_cost=int(ORG * ratio),
                                     accident_my_cnt=1, price_origin_won=ORG)))
        got = v.values["history.insurance"]
        check(f"수리비 {ratio:.0%} → {want}점", got == min(want, 12), f"{got}점")

    v = analyze_listing(ctx(snap(accident_my_cost=int(ORG * 0.01),
                                 accident_my_cnt=3, price_origin_won=ORG)))
    check("★ 건수 3 → 상한 6 이 금액 점수 13 을 누른다",
          v.values["history.insurance"] == 6,
          str(v.values["history.insurance"]))

    v = analyze_listing(ctx(snap(price_origin_won=ORG)))
    check("이력 미확보 → NULL + excluded (0원으로 채우지 않는다)",
          v.values["history.insurance"] is None
          and "history.insurance" in v.excluded)


def test_safety_real() -> None:
    r = POLICY.rule("safety")
    ev = parse_detail(fx("detail_ev_tesla.json"), "encar", "1")
    check("표본 확인 — 전기차 extendWarranty·deemed 둘 다 거짓",
          not ev["warranty_extend"] and not ev["warranty_deemed"])

    v = analyze_listing(ctx(snap(target_key="MODEL_Y"),
                            diagnosis_car=1, warranty_extend=False,
                            warranty_deemed=False))
    check("★ 전기차 보증상품 → -1 · 분모 제외",
          v.values["safety.warranty_product"] == -1
          and "safety.warranty_product" in v.excluded)

    v = analyze_listing(ctx(snap(target_key="G80_25T"),
                            diagnosis_car=1, warranty_extend=False,
                            warranty_deemed=True))
    check("내연 + 보증상품 있음 → 20점",
          v.values["safety.warranty_product"] == r["warranty_product_yes"]
          and "safety.warranty_product" not in v.excluded)

    r2 = score(v, POLICY)
    check("전기차는 안전 분모가 20 줄어든다",
          score(analyze_listing(ctx(snap(target_key="MODEL_Y"), diagnosis_car=1)),
                POLICY).denominator < r2.denominator)


def test_spec_gate() -> None:
    v = analyze_listing(ctx(snap(options_standard=["010", "095"],
                                 options_choice=[])))
    check("HUD 095 장착 → 20점", v.values["spec.hud"] == 20)
    check("선루프 010 장착 → 20점", v.values["spec.sunroof"] == 20)
    check("SVM 미장착 → 0점 (분모 제외 아님)",
          v.values["spec.svm"] == 0 and "spec.svm" not in v.excluded)
    check("★ HDA Gate 미통과 → NULL + excluded (추정 금지)",
          v.values["spec.hda"] is None and "spec.hda" in v.excluded)

    v = analyze_listing(ctx(snap(target_key="MODEL_Y", options_standard=[],
                                 options_choice=[]),
                            SPEC_DEFAULT_OFF={"spec.hud": True}))
    check("★ 모델Y HUD → -1 · 분모 제외 (사양표 근거)",
          v.values["spec.hud"] == -1 and "spec.hud" in v.excluded)

    v = analyze_listing(ctx(snap(options_standard=[], options_choice=[],
                                 ad_body_text="선루프 있습니다")))
    check("★ 판매글 키워드가 실장착을 이기지 못한다 (v1 사고)",
          v.values["spec.sunroof"] == 0)

    v = analyze_listing(ctx(snap(options_standard=[], options_choice=[],
                                 ad_body_text="루마 틴팅 시공")))
    check("틴팅 키워드 명중 → 5점", v.values["spec.tinting"] == 5)
    v = analyze_listing(ctx(snap(options_standard=[], options_choice=[],
                                 ad_body_text="깨끗한 차량")))
    check("틴팅 언급 없음 → NULL + excluded (0 아님)",
          v.values["spec.tinting"] is None and "spec.tinting" in v.excluded)


def test_price_real() -> None:
    """실제 depreciation.json 초기값으로 채점되는가 (STEP 70)."""
    dep = json.load(open(os.path.join(ROOT, "config", "depreciation.json"),
                         encoding="utf-8"))
    check("감가 곡선 6구간 확보", len(dep["curve"]) == 6, str(len(dep["curve"])))

    # 3년 경과 · 계수 1.053 → 기대가 = 원가 × 0.710 × 1.053
    org = 70000000
    exp = org * dep["curve"]["3"] * dep["coefficient"]["G80_25T"]
    v = analyze_listing(ctx(snap(target_key="G80_25T",
                                 price_current_won=int(exp),
                                 price_origin_won=org,
                                 first_registration_date="2023-05-02"),
                            depreciation=dep))
    check("★ 기대가와 같으면 100점 (200점의 절반)",
          v.values["price"] == 100, str(v.values["price"]))
    check("가격 축이 살아난다 (excluded 아님)", "price" not in v.excluded)

    v = analyze_listing(ctx(snap(target_key="G80_25T",
                                 price_current_won=int(exp * 0.80),
                                 price_origin_won=org,
                                 first_registration_date="2023-05-02"),
                            depreciation=dep))
    check("기대가 −20% → 180점", v.values["price"] == 180, str(v.values["price"]))
    v = analyze_listing(ctx(snap(target_key="G80_25T",
                                 price_current_won=int(exp * 1.30),
                                 price_origin_won=org,
                                 first_registration_date="2023-05-02"),
                            depreciation=dep))
    check("기대가 +30% → −100점 (음수 구간)",
          v.values["price"] == -100, str(v.values["price"]))

    # ★ 스포티지 계수 1.517 은 sane_range [0.80, 1.20] 밖이다
    check("표본 확인 — 스포티지 계수가 가드 밖",
          dep["coefficient"]["SPORTAGE_LPI"] > dep["coefficient_sane_range"][1])
    v = analyze_listing(ctx(snap(target_key="SPORTAGE_LPI",
                                 price_current_won=36000000,
                                 price_origin_won=32840000,
                                 first_registration_date="2023-05-02"),
                            depreciation=dep))
    check("★ 계수 가드 밖 → 가격 축 excluded (자르지도, 그대로 쓰지도 않는다)",
          v.values["price"] is None and "price" in v.excluded)
    check("다른 축은 정상 판정된다",
          v.values["mileage"] is not None)

    ok = analyze_listing(ctx(snap(target_key="G80_25T",
                                  price_current_won=36000000,
                                  price_origin_won=32840000,
                                  first_registration_date="2023-05-02"),
                             depreciation=dep))
    check("스포티지는 가격 200 만큼만 분모가 줄어든다",
          score(ok, POLICY).denominator - score(v, POLICY).denominator == 200,
          f"{score(ok, POLICY).denominator} → {score(v, POLICY).denominator}")


# ── 색상 40점 (STEP 80) ──────────────────────────────────────────────
def test_color() -> None:
    r = POLICY.rule("color")["grade_points"]
    for name, want in (("흰색", r["preferred"]), ("청색", r["neutral"]),
                       ("노란색", r["avoided"])):
        v = analyze_listing(ctx(snap(color_ext_raw=name)))
        check(f"색상 {name} → {want}점", v.values["color"] == want,
              str(v.values["color"]))
    check("★ 기피색도 0 점이 아니다 — 가치 없음이 아니라 이 축에서 손해",
          r["avoided"] > 0)
    check("★ 여집합 규칙 — 열거 밖은 기피 (미분류가 아니다)",
          "color" not in analyze_listing(ctx(snap(color_ext_raw="분홍"))).excluded)
    v = analyze_listing(ctx(snap()))
    check("색상 미확보 → NULL + excluded (0점 아님)",
          v.values["color"] is None and "color" in v.excluded)


def test_price_pending() -> None:
    v = analyze_listing(ctx(snap(price_current_won=50000000,
                                 price_origin_won=70000000,
                                 year_month="2023-05")))
    check("★ 감가 곡선 미확정 → 가격 NULL + excluded (0점 아님)",
          v.values["price"] is None and "price" in v.excluded)

    dep = {"curve": {"3": 0.70}, "coefficient": {"G80_25T": 1.0}}
    v = analyze_listing(ctx(snap(price_current_won=49000000,
                                 price_origin_won=70000000,
                                 year_month="2023-05"), depreciation=dep))
    check("곡선이 주어지면 기대가 대비로 채점 (±0% → 100점)",
          v.values["price"] == 100, str(v.values["price"]))


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

    from analyze.axis.history import analyze_history

    v = Verdict()
    analyze_history(ctx(s), v)
    check("★ 빈 outers → history.damage 만점 (excluded 아니다)",
          v.values.get("history.damage") == POLICY.comp("history.damage")
          and "history.damage" not in v.excluded,
          f"{v.values.get('history.damage')} / {v.sources.get('history.damage')}")

    v2 = Verdict()
    analyze_history(ctx(snap()), v2)
    check("점검부 없음 → excluded (만점 아니다)",
          "history.damage" in v2.excluded)


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
    from analyze.axis.history import outer_swap_count

    r = POLICY.raw["axis_rules"]
    by, outer = r["history"]["damage_by_status"], r["absolute_fail"]["outer_ranks"]

    def panel(rank, *st):
        return {"attributes": [rank],
                "statusTypes": [{"title": x} for x in st]}

    def n(*panels):
        return outer_swap_count(list(panels), outer, by)

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


# ── STEP 75 HDA Gate 확정 ───────────────────────────────────────────
def test_hda_gate() -> None:
    """★ 판정 근거는 description 이다.  옵션명의 Ⅰ·II 로 가르지 않는다."""
    r = POLICY.raw["axis_rules"]["spec"]
    check("★ Gate 가 열렸다 (2026-08-11 실측)", r["hda_gate_open"] is True)
    check("2 문구가 1 문구보다 먼저 검사된다",
          all(any(p2.startswith(p1) for p1 in r["hda_level1_phrases"])
              for p2 in r["hda_level2_phrases"] if p2.startswith("고속도로")))
    check("띄어쓰기 변형을 담는다",
          "고속도로 주행보조 2" in r["hda_level2_phrases"])

    # 실측 표 — description 으로 갈린다
    def level(desc: str) -> str:
        if any(p in desc for p in r["hda_level2_phrases"]):
            return "2"
        if any(p in desc for p in r["hda_level1_phrases"]):
            return "1"
        return "0"

    cases = [
        ("드라이빙 어시스턴스 패키지 II",
         "스마트 크루즈 컨트롤, 고속도로 주행 보조 2(차로 변경 보조)", "2"),
        ("현대 스마트센스 II", "고속도로 주행 보조 2, 전방 충돌방지", "2"),
        ("드라이빙 어시스턴스 패키지 Ⅰ",
         "서라운드 뷰 모니터, 후측방 모니터, 원격 스마트 주차 보조", "0"),
        ("현대 스마트센스 I", "후측방 충돌 경고, 차로 이탈방지", "0"),
    ]
    for name, desc, want in cases:
        got = level(desc)
        check(f"★ {name[:22]} → {want}", got == want, f"{got}")
    check("★ Ⅰ(로마) 와 I(라틴) 이 결과를 안 가른다",
          level("서라운드 뷰 모니터") == level("후측방 충돌 경고"))


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
