# -*- coding: utf-8 -*-
"""⑤ 보증 30 — 제조사 보증 15 · 사이트 우수등급 10 · 점검 출처 5.

지시서   7장 STEP 72 · 79 · `docs/ref/F-scoring.md` ⑤ (개정 329)
근거     마스터 지시 — 「엔카는 진단 + 우수등급이 있으면 신뢰성이 우선하도록」
        ★ 같은 값이라도 누가 보증하느냐가 다르다 (개정 300)
값규칙   사이트마다 「무엇이 우수등급인가」가 다르다 — config/sites.json 이 정본
금지     코드에 사이트 이름을 박는 것 (V3-55)
"""
from __future__ import annotations

from analyze.axes import AxisContext
from analyze.axis._util import months_between
from analyze.curve import descending
from analyze.trust import FORMAT_OFFICIAL, FORMAT_SELLER, inspection_source
from analyze.verdict import PRIO_MANUFACTURER, PRIO_OBSERVED, Verdict, put

MAKER = "warranty.maker"
SITE = "warranty.site"
INSPECTION = "warranty.inspection"


def remaining_months(months, km_limit, elapsed, mileage, km_per_month):
    """잔여 = min(보증월 − 경과월, (보증km − 주행km) ÷ 월주행).

    ★ 둘 중 하나라도 지나면 만료다 (실제 보증 약관)
    """
    if months is None or elapsed is None:
        return None
    by_time = months - elapsed
    if km_limit is None or mileage is None:
        return by_time
    return min(by_time, (km_limit - mileage) / km_per_month)


def certified(site_flags: dict, rule: dict, evidence: bool) -> bool | None:
    """그 사이트의 최상위 인증을 받았는가 (개정 306).

    ★ 규칙은 config/sites.json 의 site_grade_rule 이다.
      조건이 비면 「등록된 것 자체가 우수등급」이다 (K카 · 인증중고차)
    ★ 원문을 받았는데 값이 없으면 「인증이 없다」다 —
      실측 08-17: 우수등급은 3,528 중 495건뿐이다
    """
    need = rule.get("all_of")
    if need is None or not evidence:
        return None
    if not need:
        return True
    for field, want in need.items():
        have = site_flags.get(field)
        ok = (str(have) == str(want) if isinstance(want, str)
              else bool(have) == bool(want))
        if not ok:
            return False
    return True


def _maker(ctx: AxisContext, v: Verdict) -> None:
    """5-1 제조사 보증 잔여 15 — 일반·동력계 중 긴 쪽."""
    s, r = ctx.snapshot, ctx.policy.rule("warranty")
    elapsed = months_between(s.first_registration_date or s.year_month,
                             ctx.target_config.get("as_of"))
    got = [remaining_months(m, km, elapsed, s.mileage_km, r["km_per_month"])
           for m, km in ((s.warranty_body_month, s.warranty_body_km),
                         (s.warranty_power_month, s.warranty_power_km))]
    left = [x for x in got if x is not None]
    if not left:
        put(v, MAKER, 0, PRIO_MANUFACTURER, "missing")
        return
    put(v, MAKER, round(descending(max(left), r["maker_curve"])),
        PRIO_MANUFACTURER, "encar_warranty")


def _site(ctx: AxisContext, v: Verdict) -> None:
    """5-2 사이트 우수등급 10 — 진단+우수 10 · 진단만 6 · 무진단 0."""
    s, r = ctx.snapshot, ctx.policy.rule("warranty")
    pts = r["site_points"]
    rule = ctx.target_config.get("site_grade_rule") or {}
    got = certified(dict(s.site_flags or {}, diagnosis_car=s.diagnosis_car),
                    rule, s.diagnosis_car is not None)
    if got is None:
        put(v, SITE, 0, PRIO_OBSERVED, "missing")
        return
    if got:
        put(v, SITE, pts["certified"], PRIO_OBSERVED, "site_grade_rule")
        return
    # ★ 우수등급은 없지만 진단은 받았다 — 둘을 가른다
    put(v, SITE,
        pts["diagnosis_only"] if s.diagnosis_car else pts["none"],
        PRIO_OBSERVED,
        "diagnosis_only" if s.diagnosis_car else "no_diagnosis")


def _inspection(ctx: AxisContext, v: Verdict) -> None:
    """5-3 점검 출처 5 — 플랫폼 직영 5 · 판매자 등록 2 · 없음 0 (개정 300)."""
    r = ctx.policy.rule("warranty")["inspection_points"]
    src = inspection_source(ctx.snapshot.inspection_formats)
    if src is None:
        put(v, INSPECTION, 0, PRIO_OBSERVED, "missing")
        return
    table = {FORMAT_OFFICIAL: r["official"], FORMAT_SELLER: r["seller"],
             "": r["none"]}
    put(v, INSPECTION, table[src], PRIO_OBSERVED,
        f"inspection_{src or 'none'}")


def analyze_site(ctx: AxisContext, v: Verdict) -> None:
    _maker(ctx, v)
    _site(ctx, v)
    _inspection(ctx, v)
