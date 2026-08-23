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


# ★ 원문이 참인가.  ★ 원문은 문자열 '0' · '1' 로 온다 (실측 08-23)
FALSE_WORDS = ("", "0", "n", "no", "false", "none", "null")


def _truthy(value) -> bool:
    """★ 원문 값이 참인가 (개정 491 ⓔ).

    ★★ 전에는 bool(value) 였다.  ★ 원문이 문자열 '0' 이라 ★ 참이 됐다 —
      실측 08-23: `warranty_extend='0'` 인 522건이 ★ 엔카진단++ 만점을 받았다.
      ★ 「진단 미조회인데 만점」의 진짜 까닭이 이것이다
    """
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() not in FALSE_WORDS


def warranty_grade(flags: dict, grades: list) -> tuple:
    """④ 사이트 검증 52 — **단계**다 (개정 428).  더하지 않는다.

    ★ 전에는 엔카검증 10 + 엔카보증 10 + 보증++ 30 을 더했다 (개정 365).
      개정 428 이 단계로 바꿨다 — 위 단계 하나만 준다
    ★ 위에서부터 본다.  먼저 맞는 것이 그 매물의 단계다
    """
    for one in grades:
        ok = True
        # ★★ 개정 491 ⓔ — ★ 그 근거를 정말 받았는가.
        #   ★ 미조회인데 만점을 주면 「누가 확인했는가」가 거짓이 된다.
        #   ★ 실측 08-23 — 엔카진단++ 43건이 ★ 전부 진단 미조회였다
        need_ok = one.get("needs_ok")
        if need_ok and str(flags.get(need_ok) or "") != "ok":
            continue
        for key, want in (one.get("when") or {}).items():
            have = flags.get(key)
            if not (_truthy(have) if want in (1, True)
                    else str(have) == str(want)):
                ok = False
                break
        if ok:
            return int(one.get("points") or 0), one.get("key") or "?"
    return 0, "no_warranty"


def _seller_only(snapshot) -> bool:
    """점검을 ★ 판매자가 올렸는가 (개정 300 · 491).

    ★ 성능점검이 사진(IMAGE)뿐이고 표(TABLE)가 없으면 판매자가 올린 것이다
    """
    fmt = str(getattr(snapshot, "inspection_formats", "") or "")
    return "IMAGE" in fmt and "TABLE" not in fmt


def _one_step_down(grades: list, got: int, why: str) -> tuple:
    """단계를 한 칸 낮춘다.  ★ 맨 아래면 그 아래는 0 이다."""
    pts = [int(one.get("points") or 0) for one in grades]
    keys = [one.get("key") or "?" for one in grades]
    for i, one in enumerate(pts):
        if one == got:
            if i + 1 < len(pts):
                return pts[i + 1], f"{keys[i + 1]}(판매자점검)"
            return 0, "no_warranty(판매자점검)"
    return got, why


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
        # ★★ 개정 491 — ★ 판매자가 올린 점검이면 ★ 만점을 주지 않는다.
        #   ★ 감점이 아니라 ★ 단계를 한 칸 낮춘다 (f-table 「사이트 검증」).
        #   ★ 「누가 확인했는가」가 이 축의 뜻이다 — 딜러 말뿐이면 그만큼만이다
        if _seller_only(s) and got:
            got, why = _one_step_down(grades, got, why)
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
    # ★★ 명령서 r515 2-3 — 원문이 보증 개월을 안 주면 ★ 차종 속성으로 채운다.
    #   ★ 안 채우면 보증 잔여가 0 이 되어 ★ 수입차가 전부 바닥에 깔린다
    #   ★ 원문이 있으면 ★ 원문이 이긴다.  ★ 표는 대체값일 뿐이다
    fallback = _maker_default(ctx, r)
    for axis, months, km, curve, src in pairs:
        if months is None and fallback:
            key = "general" if axis == GENERAL else "power"
            months = fallback.get(f"{key}_month")
            km = km if km is not None else fallback.get(f"{key}_km")
            if months is not None:
                src = "maker_default"
        left = remaining_months(months, km, elapsed, s.mileage_km,
                                r["km_per_month"])
        if left is None:
            put(v, axis, 0, PRIO_MANUFACTURER, "missing")
            continue
        put(v, axis, round(descending(max(left, 0), r[curve])),
            PRIO_MANUFACTURER, src)


def _maker_default(ctx: AxisContext, rules: dict) -> dict:
    """제조사 보증 기간표 (명령서 r515 2-3).

    ★ 표는 ★ 차종 키로 찾는다.  ★ 코드에 브랜드를 박지 않는다 (V3-55)
    ★ 표에 없는 차종은 ★ 빈 것이다.  ★ 지어내지 않는다 (금지 6)
    ★ 브랜드가 아니라 차종으로 적는 까닭 — 축 함수가 target_config 에서
      매물 값을 읽으면 V4-24 가 문다.  ★ 차종 키는 스냅숏이 준다
    """
    table = ((rules.get("maker_default") or {}).get("by_target") or {})
    if not table:
        return {}
    # ★★ V4-24 — target_config 에서 ★ 매물 값을 캐지 않는다.
    #   ★ 차종 키는 ★ 스냅숏이 준다.  표도 ★ 차종 키로 찾는다
    got = table.get(getattr(ctx.snapshot, "target_key", None) or "") or {}
    if isinstance(got, dict):
        return got
    # ★★ 연식으로 갈리는 브랜드가 있다 (명령서 16-2 ⓑ · 개정 633) —
    #   ★ 아우디는 ★ 21년식부터 5년/15만km 이고 ★ 그 전은 값이 다르다.
    #   ★ 그래서 ★ 줄을 여럿 두고 ★ 「연식 이상」으로 고른다
    #   ★ 맞는 줄이 없으면 ★ 빈 것이다 — ★ 0 이 아니라 ★ 「모름」이다 (개정 325)
    year = getattr(ctx.snapshot, "form_year", None)
    if year is None:
        ym = getattr(ctx.snapshot, "year_month", None)
        year = int(str(ym)[:4]) if ym and str(ym)[:4].isdigit() else None
    if year is None:
        return {}
    best = {}
    for row in got:
        if not isinstance(row, dict):
            continue
        floor = row.get("year_from")
        if floor is None or int(year) >= int(floor):
            if not best or int(floor or 0) >= int(best.get("year_from") or 0):
                best = row
    return {k: v for k, v in best.items() if k != "year_from"}


def analyze_site(ctx: AxisContext, v: Verdict) -> None:
    _maker(ctx, v)
    _site(ctx, v)
