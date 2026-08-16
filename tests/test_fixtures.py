# -*- coding: utf-8 -*-
"""실물 표본 시험 — v1 원문 12건.

지시서   2장 STEP 20·21·21a·22 · 4장 STEP 46 (전기차) · 7장 STEP 76~78
근거     모의 응답이 아니라 실물이다.  경로가 틀리면 여기서 걸린다.
         v1 은 outers[].children[] 라는 존재하지 않는 경로를 읽어
         inspection_panel_json 이 전건 NULL 이었고 사고 20점이 죽어 있었다.
         그 경로로 되돌리면 outers_len 이 5 → 0 이 되어 이 시험이 깨진다.
재료     tests/fixtures/*.json + EXPECTED.json (마스터 실측 기대값)
사용     python3 tests/test_fixtures.py
"""
from __future__ import annotations

import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parse.classify import classify, validate_targets  # noqa: E402
from parse.encar.mapping import (  # noqa: E402
    parse_detail, parse_inspection, parse_record,
)

HERE = os.path.dirname(os.path.abspath(__file__))
FX = os.path.join(HERE, "fixtures")
ROOT = os.path.dirname(HERE)
EXPECTED = json.load(open(os.path.join(FX, "EXPECTED.json"), encoding="utf-8"))
FAIL: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{'  ' + detail if detail else ''}")
    if not ok:
        FAIL.append(name)


def fx(name: str):
    return json.load(open(os.path.join(FX, name), encoding="utf-8"))


# ★ 시험이 변환 로직을 다시 구현하면 둘 다 틀려도 통과한다 (STEP 6a).
#   EXPECTED 의 _core 값과 직접 비교한다.


# ── 점검부 5종 (STEP 21) ─────────────────────────────────────────────
INSPECTIONS = ("inspection_clean.json", "inspection_frame.json",
               "inspection_outer_swap.json", "inspection_outer_paint.json",
               "inspection_weld.json")


def test_inspection() -> None:
    for name in INSPECTIONS:
        want = EXPECTED[name]
        p = parse_inspection(fx(name), "encar", "1")
        panels = json.loads(p["inspection_panel_json"])

        check(f"{name[11:-5]:12} outers {want['outers_len']}판 원문 그대로",
              len(panels) == want["outers_len"], f"{len(panels)}판")

        ranks = collections.Counter(
            a for el in panels for a in (el.get("attributes") or []))
        check(f"{name[11:-5]:12} 랭크 분포", dict(ranks) == want["ranks"],
              f"{dict(ranks)} / {want['ranks']}")

        sts = collections.Counter(
            s.get("title") for el in panels
            for s in (el.get("statusTypes") or []))
        check(f"{name[11:-5]:12} 상태 분포", dict(sts) == want["statusTypes"],
              f"{dict(sts)} / {want['statusTypes']}")

        check(f"{name[11:-5]:12} 최초등록일 → EXPECTED._core 직접 비교",
              p["first_registration_date"] == want["firstRegistrationDate_core"],
              f'{p["first_registration_date"]} / {want["firstRegistrationDate_core"]}')
        check(f"{name[11:-5]:12} 주행거리",
              p["inspection_mileage_km"] == want["mileage"],
              str(p["inspection_mileage_km"]))
        check(f"{name[11:-5]:12} usageChangeTypes (record 아니라 점검부)",
              json.loads(p["usage_change_types_json"]) == want["usageChangeTypes"],
              str(p["usage_change_types_json"]))


def test_frame_vs_outer() -> None:
    """골격/외판 판정은 부위명이 아니라 attributes(RANK_*) 로 한다 (STEP 44)."""
    frame = json.loads(
        parse_inspection(fx("inspection_frame.json"), "encar", "1")
        ["inspection_panel_json"])
    swap = json.loads(
        parse_inspection(fx("inspection_outer_swap.json"), "encar", "1")
        ["inspection_panel_json"])

    def has_frame(panels):
        return any(a in ("RANK_A", "RANK_B", "RANK_C")
                   for el in panels for a in (el.get("attributes") or []))

    def outer_swap_count(panels):
        return sum(
            1 for el in panels
            if any(a in ("RANK_ONE", "RANK_TWO")
                   for a in (el.get("attributes") or []))
            and any(s.get("title") == "교환(교체)"
                    for s in (el.get("statusTypes") or [])))

    check("★ RANK_B 1건 → 골격 (외판 4판보다 우선)",
          has_frame(frame) is EXPECTED["inspection_frame.json"]["골격"])
    check("골격 판정에 부위명 문자열을 쓰지 않는다", not has_frame(swap))
    check("외판 교환 판수 — frame",
          outer_swap_count(frame)
          == EXPECTED["inspection_frame.json"]["외판교환_판수"],
          str(outer_swap_count(frame)))
    check("외판 교환 판수 — outer_swap 5판",
          outer_swap_count(swap)
          == EXPECTED["inspection_outer_swap.json"]["외판교환_판수"],
          str(outer_swap_count(swap)))
    paint = json.loads(
        parse_inspection(fx("inspection_outer_paint.json"), "encar", "1")
        ["inspection_panel_json"])
    check("판금/용접만 → 교환 0판", outer_swap_count(paint) == 0)


# ── 이력 2종 (STEP 21a) ──────────────────────────────────────────────
def test_record() -> None:
    for name in ("record_clean.json", "record_with_accident.json"):
        want = EXPECTED[name]
        p = parse_record(fx(name), "encar", "1")
        acc = json.loads(p["accidents_json"] or "[]")
        check(f"{name[7:-5]:14} 번호판 원본이 CORE 에 없다 (STEP 35)",
              "record_plate_no" not in p and p["_pii_record_plate_no"]
              == want["carNo"])
        check(f"{name[7:-5]:14} accidents 원문 그대로",
              len(acc) == want["accidents_len"], f"{len(acc)}건")
        check(f"{name[7:-5]:14} type 목록 (파싱이 합산·필터하지 않는다)",
              [a.get("type") for a in acc] == want["types"])
        check(f"{name[7:-5]:14} myAccidentCost",
              p["accident_my_cost"] == want["myAccidentCost"])
        check(f"{name[7:-5]:14} otherAccidentCnt",
              p["accident_other_cnt"] == want["otherAccidentCnt"])

    # ★ type 3 = 타 차 가해.  내 차 피해 금액이 아니다 (STEP 77 검산 재료)
    want = EXPECTED["record_with_accident.json"]
    check("★ type 3 만 있는데 myAccidentCost 0 · otherAccidentCnt 1",
          want["types"] == ["3"] and want["myAccidentCost"] == 0
          and want["otherAccidentCnt"] == 1)


# ── 상세 4종 (STEP 20) ───────────────────────────────────────────────
DETAILS = ("detail_ev_tesla.json", "detail_gasoline_genesis.json",
           "detail_hybrid_renault.json", "detail_lpg_hyundai.json")


def test_detail() -> None:
    for name in DETAILS:
        want = EXPECTED[name]
        p = parse_detail(fx(name), "encar", "1")
        tag = name[7:-5]
        check(f"{tag:18} originPrice 만원 → 원",
              p["price_origin_won"] == want["originPrice"] * 10000,
              str(p["price_origin_won"]))
        check(f"{tag:18} displacement", p["displacement_cc"] == want["displacement"])
        check(f"{tag:18} fuelName", p["fuel_detail"] == want["fuelName"])
        check(f"{tag:18} 보증 개월",
              p["warranty_body_month"] == want["warranty"]["bodyMonth"]
              and p["warranty_power_month"] == want["warranty"]["transmissionMonth"])
        check(f"{tag:18} choice 길이 (빈 배열은 '[]')",
              len(json.loads(p["options_choice_json"] or "null") or [])
              == want["options_choice_len"])
        check(f"{tag:18} 상사명 = firm.name",
              p["dealer_shop"] == want["dealer_firm"], str(p["dealer_shop"]))


def test_classify_real() -> None:
    from collect.runner import load_targets
    tg = load_targets(os.path.join(ROOT, "config", "targets.json"))
    check("전기차 target 은 displacement_range 가 null", validate_targets(tg) == [],
          str(validate_targets(tg)))

    # ★ 전기차 displacement 180 은 쓰레기값이다.  분류에 쓰지 않는다
    ev = parse_detail(fx("detail_ev_tesla.json"), "encar", "1")
    r = classify(tg, "encar:MODEL_Y", "전기", None, ev["trim_grade_name"],
                 ev["displacement_cc"])
    check("★ 모델Y displacement 180 이어도 confirmed",
          r.target_key == "MODEL_Y" and r.stage == "confirmed", r.reason)

    g = parse_detail(fx("detail_gasoline_genesis.json"), "encar", "1")
    r = classify(tg, "encar:G80", "가솔린", "2.5 터보", g["trim_grade_name"],
                 g["displacement_cc"])
    check("G80 2497 → G80_25T", r.target_key == "G80_25T", r.reason)

    # ★ 목록만 보면 통과한다.  2단 분류가 걸러야 할 사례다
    h = parse_detail(fx("detail_hybrid_renault.json"), "encar", "1")
    check("콜레오스 표본은 1969 가솔린 (1.5 하이브리드가 아니다)",
          h["displacement_cc"] == 1969 and h["fuel_detail"] == "가솔린")
    r = classify(tg, "encar:KOLEOS", h["fuel_detail"], None,
                 h["trim_grade_name"], h["displacement_cc"])
    check("★ 2.0 가솔린 콜레오스 → KOLEOS_HEV 아님",
          r.target_key is None and not r.conflict, f"{r.target_key} / {r.reason}")

    lpg = parse_detail(fx("detail_lpg_hyundai.json"), "encar", "1")
    r = classify(tg, "encar:GRANDEUR", "LPG(일반인 구입)", None,
                 lpg["trim_grade_name"], lpg["displacement_cc"])
    check("그랜저 LPG 3470 → GRANDEUR_LPG", r.target_key == "GRANDEUR_LPG",
          r.reason)


# ── 카탈로그 (STEP 22) ───────────────────────────────────────────────
def test_catalog() -> None:
    items = fx("catalog.json")
    check("루트가 배열이다", isinstance(items, list) and len(items) == 9,
          f"{len(items)}건")
    check("optionCd 1009 = BOSE",
          any(i["optionCd"] == "1009" and "BOSE" in i["optionName"]
              for i in items))
    check("4~5자리 코드다 (3자리 아님)",
          all(len(i["optionCd"]) >= 4 for i in items))


# ── STEP 21b 진단 ───────────────────────────────────────────────────
def test_diagnosis() -> None:
    from parse.encar.mapping import (
        DIAG_CHECKER_CODE, DIAG_PANEL_CODE, parse_diagnosis,
    )

    doc = fx("diagnosis.json")
    p = parse_diagnosis(doc, "encar", doc["vehicleId"])

    check("판정 문장을 뽑는다 (006039)",
          p["checker_comment"] and "진단 판정" in p["checker_comment"],
          str(p["checker_comment"])[:40])
    check("외판 상세를 뽑는다 (006040)", bool(p["outer_panel_comment"]))
    check("센터를 남긴다", p["center_code"] and p["center_name"])
    check("진단 시각", bool(p["diagnosed_at"]))
    # ★ 소견은 부위가 아니다.  집계에서 뺀다 (STEP 35)
    judged = [i for i in doc["items"] if i.get("resultCode")]
    check("★ 소견을 집계에서 뺀다", p["item_count"] == len(judged),
          f'{p["item_count"]} vs {len(judged)}')
    check("교환 + 정상 == 판정 수",
          p["replacement_count"] + p["normal_count"] == p["item_count"])

    from parse.encar.mapping import parse_diagnosis_items

    items = parse_diagnosis_items(doc)
    check("★ 부위는 표로 편다 — 소견은 뺀다",
          len(items) == len(judged) and all(i["result_code"] for i in items))
    check("코멘트 코드가 상수다",
          DIAG_CHECKER_CODE == "006039" and DIAG_PANEL_CODE == "006040")

    # ★ 판정 근거로 쓰지 않는다 — outers 와 같은 사실이다 (582건 확인)
    import os as _os

    root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    # ★ diagnosis_car(불리언)는 원래 쓰던 것이다 — safety.diagnosis.
    #   금지하는 것은 「진단 리포트로 사고를 판정하는 것」이다 (outers 와 겹친다)
    BANNED = ("core_diagnosis", "checker_comment", "REPLACEMENT",
              "items_json")
    bad = []
    for base, dirs, files in _os.walk(_os.path.join(root, "analyze")):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            if not f.endswith(".py"):
                continue
            body = open(_os.path.join(base, f), encoding="utf-8").read()
            bad += [f"{f}: {w}" for w in BANNED if w in body]
    check("★ analyze 가 진단 리포트로 판정하지 않는다 (중복 감점 방지)",
          not bad, str(bad))

    # 없는 값에도 죽지 않는다
    empty = parse_diagnosis({}, "encar", "1")
    check("빈 응답도 파싱된다", empty["item_count"] == 0
          and empty["checker_comment"] is None)


if __name__ == "__main__":
    print("실물 표본 시험 (v1 원문 12건)")
    test_inspection()
    test_frame_vs_outer()
    test_record()
    test_detail()
    test_classify_real()
    test_catalog()
    test_diagnosis()
    print()
    print("결과:", "통과" if not FAIL else "실패 — " + " / ".join(FAIL))
    sys.exit(1 if FAIL else 0)
