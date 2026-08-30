# -*- coding: utf-8 -*-
"""KB차차차 상세 → `core_record` (명령서 r1007 · 1-5 · 로드맵 차례 1).

★★★★★ 08-31 — ★ 상세 안에 ★ **보험사고정보 한 덩이**가 있다 [실측 · 표본 295건 중 272].

    보험사고정보 사고없음 전손이력 없음 침수이력 없음 용도이력 없음 소유자변경 없음
    보험사고정보 조회일자 : 2026.08.12
    … 보험이력 0건 …

★ 값이 ★ 낱말로 온다 — ★ 「없음」·「N회」·「N건」·「있음」.
  ★ ★ 실측 갈래 — ★ 전손 없음 271 · 침수 없음 272 · 용도 있음 176 / 없음 96 ·
    ★ ★ 소유자 없음 68 · 1회 133 · 2회 44 · 3회 13 · 4회 6 · 5회 7 · 6회 1

★★★ ★ **「용도이력 있음」은 ★ 어느 용도인지 안 알려 준다.**
  ★ ★ 그래서 ★ 「자가용」으로 매기지 않는다 — ★ 사실만 남기고 ★ 용도 축을 안 연다.
  ★ ★ 「없음」일 때만 ★ 관문을 연다 (렌트·영업·관용이 다 아니라는 뜻이다)

★★★ ★ **KB 는 ★ 「내 차 피해」와 ★ 「남의 차 가해」를 ★ 안 가른다** — ★ 한 수로 온다.
  ★ ★ 사고 축은 ★ `내차 + 타차` 를 ★ 회수로 쓴다 (`analyze/axis/state.py:_accident`) —
  ★ ★ 그래서 ★ 그 한 수를 ★ 회수로 넣는다.  ★ 금액은 ★ 안 온다 (자차 수리비는 NULL)
  ★ ★ ★ **마스터께 올린다** — ★ 가르는 자리가 규격에 없다
"""
from __future__ import annotations

import re

SITE_CODE = "kbchachacha"
RE_TAG = re.compile(r"<script.*?</script>|<style.*?</style>|<[^>]+>", re.S)
RE_BLOCK = re.compile(r"보험사고정보\s*(.{0,220}?)보험사고정보\s*조회일자", re.S)
RE_ACCIDENT = re.compile(r"사고(없음|\s*(\d+)\s*건)")
RE_INSURANCE = re.compile(r"보험이력\s*(\d+)\s*건")
RE_OWNER = re.compile(r"소유자변경\s*(없음|\d+\s*회)")
RE_N = re.compile(r"(\d+)")
LABELS = {"전손이력": "total_loss_cnt", "침수이력": "flood_total_cnt"}


def text(html: str) -> str:
    return re.sub(r"\s+", " ", RE_TAG.sub(" ", html or ""))


def _none_or_n(word: str) -> int | None:
    """「없음」 → 0 · 「2회」 → 2 · 그 밖 → None (★ 지어내지 않는다)."""
    if not word:
        return None
    if "없음" in word:
        return 0
    got = RE_N.search(word)
    return int(got.group(1)) if got else None


def record_of(html: str, site: str = SITE_CODE) -> dict | None:
    """상세 → `core_record` 한 줄.  ★ 덩이가 없으면 ★ None (「못 봤다」)."""
    t = text(html)
    got = RE_BLOCK.search(t)
    if not got:
        return None
    seg = got.group(1)
    out: dict = {"listing_id": None, "site": site, "row_status": "ok",
                 "collected_at": None, "record_open": 1}

    acc = RE_ACCIDENT.search(seg)
    ins = RE_INSURANCE.search(t)
    n = None
    if acc:
        n = 0 if acc.group(1) == "없음" else _none_or_n(acc.group(1))
    elif ins:
        n = int(ins.group(1))
    if n is not None:
        # ★ KB 는 ★ 내차·타차를 ★ 안 가른다 — ★ 한 수가 ★ 총 회수다
        out["accident_total_cnt"] = n
        out["accident_my_cnt"] = n
    for label, col in LABELS.items():
        m = re.search(label + r"\s*(\S+)", seg)
        if not m:
            continue
        v = _none_or_n(m.group(1))
        if v is not None:
            out[col] = v
        # ★ 날짜가 오면 ★ 「있었다」다 — ★ 1 로 센다 (실측 「전손이력 20260620」)
        elif re.match(r"\d{6,8}", m.group(1)):
            out[col] = 1

    own = RE_OWNER.search(seg)
    if own:
        v = _none_or_n(own.group(1))
        if v is not None:
            out["owner_change_cnt"] = v

    use = re.search(r"용도이력\s*(\S+)", seg)
    if use and "없음" in use.group(1):
        # ★ 렌트·영업·관용이 ★ 다 아니다 — ★ 관문 셋을 함께 연다
        out["use_gov"] = 0
        out["use_business"] = 0
        out["plate_history_hash_json"] = "[]"
    elif use:
        # ★★ 「있음」 — ★ 어느 용도인지 ★ 모른다.  ★ 축을 안 연다 (지어 주지 않는다)
        out["use_cd"] = f"kbchachacha:용도이력={use.group(1)}"
    return out
