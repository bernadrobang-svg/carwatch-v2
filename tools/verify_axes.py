# -*- coding: utf-8 -*-
"""손계산 대조 — 축마다 표본 3건 (개정 329 전수검증 · V3-66).

지시서   `docs/ref/F-scoring.md` 전수 검증
근거     가이드 지시 — 「「구현했습니다」가 아니라 「손계산과 맞습니다」로 보고」
값규칙   ★ 부록 F 의 표를 여기 다시 적지 않는다.
        표를 읽어 스스로 계산하고 저장된 값과 견준다 —
        코드가 쓴 구간표를 그대로 쓰면 「자기 구현을 검사」하는 것이다
금지     analyze/ 의 함수를 불러 대조하는 것.  그것은 대조가 아니다
사용     python3.11 tools/verify_axes.py
"""
from __future__ import annotations

import os
import re
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

DB = os.path.join(ROOT, "carwatch.db")
SPEC = os.path.join(ROOT, "docs", "ref", "F-scoring.md")
# 축마다 몇 건을 손으로 재는가 (개정 329)
SAMPLE_PER_AXIS = 3
MONTHS_PER_YEAR = 12
# 부록 F 가 정한 것 — 시세 표본 하한 · 경과 연수 하한
MARKET_MIN_SAMPLE = 5
MIN_YEARS = 0.5
# ISO 날짜에서 연·월을 끊는 자리 (2026-08-17 → 2026 · 08)
ISO_YM_END = 7
# 판정 시각.  ★ main 이 DB 에서 읽어 덮어쓴다
_AS_OF: tuple = ()
# 숫자가 없지만 0 을 뜻하는 칸 (부록 F 표).  ★ 버리면 그 줄이 빠진다
WORD_ZERO = ("무사고", "없음", "이상 없음", "0건", "0회")
WON_PER_MANWON = 10_000


def spec_tables() -> dict:
    """부록 F 의 구간표를 읽는다.  ★ config 를 읽지 않는다 — 규격이 정본이다."""
    body = open(SPEC, encoding="utf-8").read()
    out: dict = {}
    for head, block in re.findall(r"^## ([\d\-e.]+\. [^\n]+)\n(.*?)(?=^## |\Z)",
                                  body, re.S | re.M):
        # ★ 한 절에 표가 둘일 수 있다 (1-3 은 주행 + 전기차 SOH).
        #   빈 줄로 끊어 첫 표만 쓴다 — 둘을 섞으면 대조가 통째로 틀린다
        rows, seen = [], False
        for line in block.splitlines():
            got = re.match(r"^\| *([^|]+?) *\| *(-?\d+) *\|$", line)
            if got:
                seen = True
                if not got.group(1).startswith("-") \
                        and "점수" not in got.group(1):
                    rows.append((got.group(1), int(got.group(2))))
            elif seen and not line.strip().startswith("|"):
                break                    # 첫 표가 끝났다
        if rows:
            out[head.split(".")[0].strip()] = rows
    return out


def _num(text: str) -> float | None:
    """「≥ +25%」 · 「≤ 5,000」 · 「1회」 → 숫자.

    ★ %는 소수로 바꾼다.  25% 와 25 를 같게 두면 대조가 통째로 틀린다
    ★ 부호는 「−」(U+2212)도 쓴다 — 원문 그대로다
    """
    body = text.replace("−", "-").replace("–", "-")
    # ★ 「무사고」·「0원」처럼 숫자가 없는 칸이 있다.  버리면 그 줄이 빠져
    #   대조가 통째로 어긋난다 — 뜻을 0 으로 읽는다 (실측 08-18)
    if not re.search(r"\d", body):
        return 0.0 if any(w in body for w in WORD_ZERO) else None
    got = re.search(r"(-?[\d,]+(?:\.\d+)?)", body)
    if not got:
        return None
    value = float(got.group(1).replace(",", ""))
    return value / 100 if "%" in body else value


def pick(conn, axis: str, source_like: str) -> list:
    """그 축이 실제 근거로 판정된 매물 표본.  ★ 「확인 안 됨」은 뺀다."""
    return conn.execute(
        "SELECT a.listing_id, a.value, a.source FROM result_axis a"
        " WHERE a.axis=? AND a.source LIKE ? AND a.excluded=0"
        " ORDER BY a.listing_id LIMIT ?",
        (axis, source_like, SAMPLE_PER_AXIS)).fetchall()


def hand_market(conn, lid) -> float | None:
    """1-1 시세 대비 — 손으로: r = (중앙값 − 가격) / 중앙값."""
    row = conn.execute(
        "SELECT price_current_won FROM core_listing WHERE listing_id=?",
        (lid,)).fetchone()
    med = _median_for(conn, lid)
    if not row or not row[0] or not med:
        return None
    return (med - row[0]) / med


def _median_for(conn, lid) -> float | None:
    """같은 차종·트림·연식 실매물 중앙값 — 손으로 다시 센다."""
    key = conn.execute(
        "SELECT target_key, trim_badge, substr(year_month,1,4)"
        " FROM core_listing WHERE listing_id=?", (lid,)).fetchone()
    if not key:
        return None
    prices = [r[0] for r in conn.execute(
        "SELECT price_current_won FROM core_listing"
        " WHERE status='active' AND price_current_won IS NOT NULL"
        " AND target_key=? AND trim_badge=? AND substr(year_month,1,4)=?"
        " AND (advertisement_type IS NULL OR advertisement_type='NORMAL')"
        " ORDER BY price_current_won", key)]
    if len(prices) < MARKET_MIN_SAMPLE:
        return None
    mid = len(prices) // 2
    return (prices[mid] if len(prices) % 2
            else (prices[mid - 1] + prices[mid]) / 2)


def hand_mileage(conn, lid) -> float | None:
    """1-3 주행 대비 — 손으로: 연평균 = 주행 ÷ 경과 연수."""
    row = conn.execute(
        "SELECT l.mileage_km, COALESCE(i.first_registration_date,"
        " l.year_month) FROM core_listing l"
        " LEFT JOIN core_inspection i ON i.listing_id=l.listing_id"
        " WHERE l.listing_id=?", (lid,)).fetchone()
    if not row or row[0] is None or not row[1]:
        return None
    years = _years(str(row[1]))
    return None if not years else row[0] / years


def _years(ymd: str) -> float | None:
    got = [int(x) for x in ymd[:ISO_YM_END].split("-") if x.isdigit()]
    if len(got) < 2:
        return None
    at = conn_now()
    months = (at[0] - got[0]) * MONTHS_PER_YEAR + (at[1] - got[1])
    return max(MIN_YEARS, months / MONTHS_PER_YEAR)


def conn_now() -> tuple:
    """판정 시각.  ★ 지금이 아니라 그때로 잰다 — 결과가 흔들리면 대조가 아니다."""
    return _AS_OF


def lookup(table: list, value: float, descending: bool) -> float:
    """구간표에서 점수.  ★ 구간 사이는 선형 보간 (부록 F 0절)."""
    rows = [(_num(a), float(b)) for a, b in table if _num(a) is not None]
    if not rows:
        return 0.0
    if descending:
        rows.sort(key=lambda kv: -kv[0])
    else:
        rows.sort(key=lambda kv: kv[0])
    if (descending and value >= rows[0][0]) or \
            (not descending and value <= rows[0][0]):
        return rows[0][1]
    if (descending and value <= rows[-1][0]) or \
            (not descending and value >= rows[-1][0]):
        return rows[-1][1]
    for (a1, p1), (a2, p2) in zip(rows, rows[1:], strict=False):
        lo, hi = (min(a1, a2), max(a1, a2))
        if lo <= value <= hi:
            if a2 == a1:
                return p1
            return p1 + (p2 - p1) * (value - a1) / (a2 - a1)
    return rows[-1][1]


def hand_accident(conn, lid) -> float | None:
    """2-1 사고 이력 — 손으로: 내차 + 상대 피해 건수."""
    row = conn.execute(
        "SELECT accident_my_cnt, accident_other_cnt FROM core_record"
        " WHERE listing_id=?", (lid,)).fetchone()
    if not row or (row[0] is None and row[1] is None):
        return None
    return (row[0] or 0) + (row[1] or 0)


def hand_repair(conn, lid) -> float | None:
    """2-4 자차 수리비 — 손으로: 내차 피해 금액."""
    row = conn.execute(
        "SELECT accident_my_cost FROM core_record WHERE listing_id=?",
        (lid,)).fetchone()
    return None if not row or row[0] is None else float(row[0])


def hand_owner(conn, lid) -> float | None:
    """3-3 소유자 변경 — 손으로: 변경 횟수.  연식 보정은 아래에서 본다."""
    row = conn.execute(
        "SELECT owner_change_cnt FROM core_record WHERE listing_id=?",
        (lid,)).fetchone()
    return None if not row or row[0] is None else float(row[0])


def hand_maker_warranty(conn, lid) -> float | None:
    """5-1 제조사 보증 잔여 — 손으로: 일반·동력계 중 긴 쪽 (개월)."""
    row = conn.execute(
        "SELECT l.warranty_body_month, l.warranty_body_km,"
        " l.warranty_power_month, l.warranty_power_km, l.mileage_km,"
        " COALESCE(i.first_registration_date, l.year_month)"
        " FROM core_listing l LEFT JOIN core_inspection i"
        " ON i.listing_id=l.listing_id WHERE l.listing_id=?", (lid,)).fetchone()
    if not row or not row[5]:
        return None
    got = [int(x) for x in str(row[5])[:ISO_YM_END].split("-") if x.isdigit()]
    if len(got) < 2:
        return None
    at = conn_now()
    elapsed = (at[0] - got[0]) * MONTHS_PER_YEAR + (at[1] - got[1])
    kpm = _km_per_month()
    left = []
    for months, km in ((row[0], row[1]), (row[2], row[3])):
        if months is None:
            continue
        by_time = months - elapsed
        if km is not None and row[4] is not None:
            by_time = min(by_time, (km - row[4]) / kpm)
        left.append(by_time)
    return max(left) if left else None


def _km_per_month() -> float:
    """월 주행 환산.  ★ 규격이 정한 정책값이다 (7장 STEP 72)."""
    import json as _json

    with open(os.path.join(ROOT, "config", "scoring.json"),
              encoding="utf-8") as f:
        return float(_json.load(f)["axis_rules"]["warranty"]["km_per_month"])


def main() -> int:
    global _AS_OF

    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    at = conn.execute(
        "SELECT MAX(calculated_at) FROM result_score").fetchone()[0] or ""
    # ★ 지금이 아니라 판정한 때로 잰다 — 결과가 흔들리면 대조가 아니다
    _AS_OF = ((int(at[:4]), int(at[5:7])) if len(at) > ISO_YM_END
              else _AS_OF)
    tables = spec_tables()

    checks = [
        ("value.market", "market_median%", "1-1", hand_market, True,
         "시세 대비 (중앙값−가격)/중앙값"),
        ("value.mileage", "mileage_per_year", "1-3", hand_mileage, False,
         "주행 대비 연평균 km"),
        ("state.accident", "record_accident_count", "2-1", hand_accident,
         False, "사고 회수"),
        ("state.repair", "record_my_cost", "2-4", hand_repair, False,
         "자차 수리비 원"),
        ("history.owner", "owner_%", "3-3", hand_owner, False,
         "소유자 변경 횟수"),
        ("warranty.maker", "encar_warranty", "5-1", hand_maker_warranty,
         True, "제조사 보증 잔여 개월"),
    ]
    print(f"손계산 대조 — 부록 F 표를 읽어 스스로 계산했습니다 "
          f"(판정 {at[:10]})\n")
    bad = 0
    for axis, like, sec, fn, desc, label in checks:
        table = tables.get(sec)
        if not table:
            print(f"  {axis:<20} 부록 F {sec} 표를 못 읽었다")
            bad += 1
            continue
        rows = pick(conn, axis, like)
        if not rows:
            print(f"  {axis:<20} 표본이 없다")
            continue
        print(f"★ {axis} — {label} (부록 F {sec})")
        for lid, stored, src in rows:
            got = fn(conn, lid)
            if got is None:
                print(f"    {lid:<6} 손계산 재료가 없다")
                continue
            want = round(lookup(table, got, desc))
            mark = "○" if want == stored else "✗"
            if want != stored:
                bad += 1
            print(f"    {lid:<6} 입력 {got:>12,.4f} → 손 {want:>4} · "
                  f"저장 {stored:>4}  {mark}  ({src})")
        print()
    print("결과:", "손계산과 맞습니다" if not bad else f"어긋난 것 {bad}건")
    conn.close()
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
