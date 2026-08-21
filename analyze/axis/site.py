# -*- coding: utf-8 -*-
"""⑤ 사이트 보증 50 · ⑦ 제조사 보증 50 (일반 20 + 동력계 30).

지시서   7장 STEP 72 · STEP 79 · `docs/chapters/30-score/f-table.md` ⑤ · ⑦ (개정 365)
근거     마스터 확정 — 「K카는 무조건 보증이니 50점이고, 엔카는 엔카검증 10점 ·
        엔카보증 10점 · 엔카보증++ 이 30점」
        ★ 이것으로 「사이트마다 분모를 달리한다」가 필요 없어진다
값규칙   사이트마다 「무엇이 몇 점인가」가 다르다 — config/sites.json 이 정본
금지     코드에 사이트 이름을 박는 것 (V3-55)
금지     사이트 이름만으로 점수를 주는 것 — 원문에 근거가 있어야 한다
"""
from __future__ import annotations

from analyze.axes import AxisContext
from analyze.axis._util import months_between
from analyze.curve import descending
from analyze.verdict import PRIO_MANUFACTURER, PRIO_OBSERVED, Verdict, put

# ⑦ 제조사 보증 — 일반·차체와 동력계를 따로 낸다 (개정 365 · V3-70)
GENERAL = "warranty.general"
POWER = "warranty.power"
SITE = "warranty.site"
MONTHS_PER_YEAR = 12


def remaining_months(months, km_limit, elapsed, mileage, km_per_month):
    """잔여 = min(보증월 − 경과월, (보증km − 주행km) ÷ 월주행).

    ★ 보증은 둘 중 먼저 닿는 쪽에서 끝난다 (개정 365 · V3-71)
    """
    if months is None or elapsed is None:
        return None
    by_time = months - elapsed
    if km_limit is None or mileage is None:
        return by_time
    return min(by_time, (km_limit - mileage) / km_per_month)


def warranty_points(site_flags: dict, items: list, evidence) -> tuple:
    """사이트 보증 점수와 무엇으로 받았는지 (개정 365).

    반환   (점수, [항목 이름]) · 근거를 못 받았으면 (None, [])
    ★ 항목을 더한다.  하나만 있으면 그만큼만이다
    ★ 원문을 못 받았으면 0 점이 아니라 「확인 안 됨」이다 (개정 325)
    """
    if evidence is None:
        return None, []
    got, why = 0, []
    for one in items:
        need = one.get("when") or {}
        if not need:
            continue
        ok = True
        for field, want in need.items():
            have = site_flags.get(field)
            if have is None:
                ok = False
                break
            ok = (str(have) == str(want) if isinstance(want, str)
                  else str(have) == str(want))
            if not ok:
                break
        if ok:
            got += int(one.get("points") or 0)
            why.append(one.get("key") or "?")
    return got, why


def warranty_grade(flags: dict, grades: list) -> tuple:
    """④ 사이트 검증 52 — **단계**다 (개정 428).  더하지 않는다.

    ★ 전에는 엔카검증 10 + 엔카보증 10 + 보증++ 30 을 더했다 (개정 365).
      개정 428 이 단계로 바꿨다 — 위 단계 하나만 준다
    ★ 위에서부터 본다.  먼저 맞는 것이 그 매물의 단계다
    """
    for one in grades:
        ok = True
        for key, want in (one.get("when") or {}).items():
            have = flags.get(key)
            if not (bool(have) if want in (1, True) else str(have) == str(want)):
                ok = False
                break
        if ok:
            return int(one.get("points") or 0), one.get("key") or "?"
    return 0, "no_warranty"


def _site(ctx: AxisContext, v: Verdict) -> None:
    """④ 사이트 검증 52 — **단계**다 (개정 428).

    ★ 더하지 않는다.  엔카진단++ 52 · 엔카진단+ 40 · 엔카진단 26 · 없음 0
    화면에 무엇으로 받았는지 낸다 — 「엔카진단+ 40 / 52」
    """
    s = ctx.snapshot
    cfg = ctx.target_config.get("site_warranty") or {}
    items = cfg.get("warranty_items") or []
    field = cfg.get("warranty_evidence")
    flags = dict(s.site_flags or {}, diagnosis_car=s.diagnosis_car)
    if not items:
        put(v, SITE, 0, PRIO_OBSERVED, "rule_or_source_missing")
        return
    grades = cfg.get("warranty_grades")
    if grades:
        # ★ 개정 428 — 단계다.  더하지 않는다
        got, why = warranty_grade(flags, grades)
        put(v, SITE, got, PRIO_OBSERVED, why)
        return
    got, why = warranty_points(flags, items, flags.get(field))
    if got is None:
        put(v, SITE, 0, PRIO_OBSERVED, "missing")
        return
    put(v, SITE, got, PRIO_OBSERVED,
        "+".join(why) if why else "no_warranty")


def _maker(ctx: AxisContext, v: Verdict) -> None:
    """⑦ 제조사 보증 50 — 일반 20 · 동력계 30 을 따로 낸다 (V3-70).

    ★ 전기차는 배터리·모터를 동력계로 본다 (개정 293)
    """
    s, r = ctx.snapshot, ctx.policy.rule("warranty")
    elapsed = months_between(s.first_registration_date or s.year_month,
                             ctx.target_config.get("as_of"))
    pairs = ((GENERAL, s.warranty_body_month, s.warranty_body_km,
              "general_curve", "encar_warranty_general"),
             (POWER, s.warranty_power_month, s.warranty_power_km,
              "power_curve", "encar_warranty_power"))
    for axis, months, km, curve, src in pairs:
        left = remaining_months(months, km, elapsed, s.mileage_km,
                                r["km_per_month"])
        if left is None:
            put(v, axis, 0, PRIO_MANUFACTURER, "missing")
            continue
        put(v, axis, round(descending(max(left, 0), r[curve])),
            PRIO_MANUFACTURER, src)


def analyze_site(ctx: AxisContext, v: Verdict) -> None:
    _maker(ctx, v)
    _site(ctx, v)
