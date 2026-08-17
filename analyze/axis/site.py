# -*- coding: utf-8 -*-
"""⑤ 사이트 보증 50점 — 우수등급 30 · 점검 출처 12 · 플랫폼 보증 잔여 8.

지시서   7장 STEP 79 · 5장 「배점 605 — 사이트 보증 축 신설」 (개정 306)
근거     마스터 지시 — 「엔카는 진단 + 우수등급이 있으면 신뢰성이 우선하도록」
        실측 08-17
          296가7288  엔카진단 없음 · 판매자가 점검부 사진 등록 · 렌트 이력
                     그런데 우리는 A · 89.9% 를 줬다
          157호6282  엔카진단 있음 · 프레임/외부패널 전항목 정상
        ★ 둘을 같은 잣대로 보면 안 된다
값규칙   사이트마다 「무엇이 우수등급인가」가 다르다 — config/sites.json 이 정본
        엔카 진단+우수등급 · K카 등록됨 · 현대·기아 인증중고차 등록됨
금지     코드에 사이트 이름을 박는 것 (개정 285 · CORE 열 사이트명 제거와 같은 이유)
★ 사이트가 하나뿐일 때도 이 축을 쓴다 — 같은 엔카 안에서도 진단 유무가 갈린다
"""
from __future__ import annotations

from analyze.axes import AxisContext
from analyze.axis._util import months_between
from analyze.axis.warranty import _remaining_months
from analyze.trust import FORMAT_OFFICIAL, FORMAT_SELLER, inspection_source
from analyze.verdict import PRIO_OBSERVED, Verdict, put

CERTIFIED = "site.certified"
INSPECTION = "site.inspection"
WARRANTY = "site.warranty"


def certified(site_flags: dict, rule: dict, evidence: bool) -> bool | None:
    """그 사이트의 최상위 인증을 받았는가 (개정 306).

    ★ 규칙은 config/sites.json 의 site_grade_rule 이다.
      「등록된 것 자체가 우수등급」인 사이트는 조건이 비어 있다 —
      그때는 매물이 있다는 사실만으로 참이다
    ★ evidence 는 「그 원문을 받았는가」다.  받았는데 값이 없으면
      「인증이 없다」다 — 실측 08-17: 우수등급은 3,470 중 490건뿐이고
      나머지는 필드 자체가 안 온다.  그것을 전부 excluded 로 두면 축이 죽는다
    금지   여기서 사이트 이름으로 갈래를 트는 것
    """
    need = rule.get("all_of")
    if need is None:
        return None                  # 그 사이트 규칙이 아직 없다.  「없다」가 아니다
    if not evidence:
        return None                  # 원문을 못 받았다.  0 점이 아니라 excluded 다
    if not need:
        return True                  # 등록된 것 자체가 우수등급 (K카 · 인증중고차)
    for field, want in need.items():
        have = site_flags.get(field)
        ok = (str(have) == str(want) if isinstance(want, str)
              else bool(have) == bool(want))
        if not ok:
            return False
    return True


def _certified(ctx: AxisContext, v: Verdict) -> None:
    s = ctx.snapshot
    rule = (ctx.target_config.get("site_grade_rule") or {})
    # ★ 진단 여부는 상세 원문에서 온다.  그것이 곧 「원문을 받았는가」다
    got = certified(dict(s.site_flags or {}, diagnosis_car=s.diagnosis_car),
                    rule, s.diagnosis_car is not None)
    if got is None:
        put(v, CERTIFIED, None, PRIO_OBSERVED, "rule_or_source_missing",
            excluded=True)
        return
    # ★ 우수등급이 없으면 30 점을 못 받는다.  그것이 「왜 싼가」의 첫 답이다
    put(v, CERTIFIED, ctx.policy.comp(CERTIFIED) if got else 0,
        PRIO_OBSERVED, "site_grade_rule")


def _inspection(ctx: AxisContext, v: Verdict) -> None:
    """점검 출처 12 — 플랫폼 직영 12 · 판매자 등록 4 · 없음 0 (개정 300)."""
    r = ctx.policy.rule("site")
    src = inspection_source(ctx.snapshot.inspection_formats)
    if src is None:
        put(v, INSPECTION, None, PRIO_OBSERVED, "missing", excluded=True)
        return
    table = {FORMAT_OFFICIAL: r["inspection_official"],
             FORMAT_SELLER: r["inspection_seller"], "": r["inspection_none"]}
    put(v, INSPECTION, table[src], PRIO_OBSERVED, f"inspection_{src or 'none'}")


def _warranty(ctx: AxisContext, v: Verdict) -> None:
    """플랫폼 보증 잔여 8 — 엔카보증 등.  기간에 비례 (개정 306).

    ★ 제조사 보증(② 상태 15점)과 다른 것이다.  이건 플랫폼이 얹은 상품이다
    """
    s = ctx.snapshot
    ext, deemed = s.warranty_extend, s.warranty_deemed
    if ext is None and deemed is None:
        put(v, WARRANTY, None, PRIO_OBSERVED, "missing", excluded=True)
        return
    has = bool(ext and str(ext) != "0") or bool(deemed and str(deemed) != "0")
    if not has:
        put(v, WARRANTY, 0, PRIO_OBSERVED, "no_platform_warranty")
        return
    # 기간에 비례한다.  ★ 원문에 기간이 없으면 「있다」만 인정해 절반을 준다
    wr = ctx.policy.rule("warranty")
    elapsed = months_between(s.first_registration_date or s.year_month,
                             ctx.target_config.get("as_of"))
    remain = _remaining_months(s.warranty_body_month, s.warranty_body_km,
                               elapsed, s.mileage_km, wr["km_per_month"])
    full, cap = float(wr["full_months"]), ctx.policy.comp(WARRANTY)
    if remain is None:
        put(v, WARRANTY, round(cap / 2), PRIO_OBSERVED, "present_no_term")
        return
    put(v, WARRANTY, 0 if remain <= 0 else round(min(remain, full) / full * cap),
        PRIO_OBSERVED, "platform_warranty_term")


def analyze_site(ctx: AxisContext, v: Verdict) -> None:
    _certified(ctx, v)
    _inspection(ctx, v)
    _warranty(ctx, v)
