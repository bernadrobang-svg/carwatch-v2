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
# ★ 배점 정본이 어디인지는 config/checks.json 이 안다 (개정 342).
#   경로를 박아 두면 문서가 옮겨진 날 손계산이 조용히 빈 표를 읽는다
#   (실측 08-18 — 부록 F 가 11줄짜리 폐기 안내로 바뀌자 6건이 어긋났다)
def _spec_text() -> str:
    import json as _j

    with open(os.path.join(ROOT, "config", "checks.json"),
              encoding="utf-8") as f:
        got = (_j.load(f).get("canon") or {}).get("배점") or []
    out = []
    for one in got:
        path = os.path.join(ROOT, "docs", one)
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as f:
                out.append(f.read())
    return "\n\n".join(out)
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
# 점검부 「차량 상태」가 이 글자일 때만 구조 상태가 확인된 것이다
CAR_STATE_OK = "양호"
# 등급 차례 (개정 324 · 절대 기준 S90 · A80 · B70 · C60 · D50)
GRADE_ORDER = ("S", "A", "B", "C", "D", "E")


def spec_tables() -> dict:
    """부록 F 의 구간표를 읽는다.  ★ config 를 읽지 않는다 — 규격이 정본이다."""
    body = _spec_text()
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
    """그 축이 실제 근거로 판정된 매물 표본.  ★ 「확인 안 됨」은 뺀다.

    ★ source='missing' 은 「0점 · 확인 안 됨」이다 (개정 325).
      excluded 로는 안 걸린다 — 여기서 뺀다.  안 빼면 「손 30 · 저장 0」
      같은 헛 대조가 나온다 (실측 08-18)
    """
    return conn.execute(
        "SELECT a.listing_id, a.value, a.source FROM result_axis a"
        " WHERE a.axis=? AND a.source LIKE ? AND a.excluded=0"
        " AND a.source<>'missing' ORDER BY a.listing_id LIMIT ?",
        (axis, source_like, SAMPLE_PER_AXIS)).fetchall()


def _flag(value) -> bool:
    """원문의 「0」은 문자열이다.  ★ 파이썬에서 "0" 은 참이다 —
    그대로 쓰면 전건이 「있음」으로 뒤집힌다 (실측 08-18 — 자가용이 관용이 됐다)."""
    if value in (None, "", 0, "0", "N", "false", "False"):
        return False
    return bool(value)


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


def _warranty_left(conn, lid, months_col, km_col):
    """보증 잔여 개월 — min(기간 잔여, 잔여km ÷ 월주행) (개정 365)."""
    row = conn.execute(
        f"SELECT l.{months_col}, l.{km_col}, l.mileage_km,"
        " COALESCE(i.first_registration_date, l.year_month)"
        " FROM core_listing l LEFT JOIN core_inspection i"
        " ON i.listing_id=l.listing_id WHERE l.listing_id=?",
        (lid,)).fetchone()
    if not row or row[0] is None or not row[3]:
        return None
    got = [int(x) for x in str(row[3])[:ISO_YM_END].split("-") if x.isdigit()]
    if len(got) < 2:
        return None
    at = conn_now()
    elapsed = (at[0] - got[0]) * MONTHS_PER_YEAR + (at[1] - got[1])
    left = row[0] - elapsed
    if row[1] is not None and row[2] is not None:
        left = min(left, (row[1] - row[2]) / _km_per_month())
    return max(left, 0)


def hand_warranty_general(conn, lid) -> float | None:
    """⑦-1 일반·차체 보증 20 — 손으로."""
    return _warranty_left(conn, lid, "warranty_body_month", "warranty_body_km")


def hand_warranty_power(conn, lid) -> float | None:
    """⑦-2 동력계 보증 30 — 손으로."""
    return _warranty_left(conn, lid, "warranty_power_month",
                          "warranty_power_km")


def hand_site_warranty(conn, lid) -> float | None:
    """⑤ 사이트 보증 50 — 손으로: sites.json 의 항목을 더한다 (개정 365)."""
    import json as _j

    with open(os.path.join(ROOT, "config", "sites.json"),
              encoding="utf-8") as f:
        sites = _j.load(f)
    row = conn.execute(
        "SELECT site, diagnosis_car, site_pass_grade, warranty_deemed,"
        " warranty_extend, sell_type, platform_verified"
        " FROM core_listing WHERE listing_id=?", (lid,)).fetchone()
    if not row:
        return None
    one = sites.get(row[0] or "") or {}
    items = one.get("warranty_items") or []
    flags = {"diagnosis_car": row[1], "site_pass_grade": row[2],
             "warranty_deemed": row[3], "warranty_extend": row[4],
             "sell_type": row[5], "platform_verified": row[6]}
    if flags.get(one.get("warranty_evidence")) is None:
        return None
    got = 0.0
    for item in items:
        need = item.get("when") or {}
        if need and all(flags.get(k) is not None
                        and str(flags.get(k)) == str(v)
                        for k, v in need.items()):
            got += float(item.get("points") or 0)
    return got


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


# ══ 여기부터 나머지 축 (부록 F 전수 검증 · 24축) ═══════════════════
# ★ 표가 말로 된 축은 「그 줄의 이름」을 손으로 골라 표에서 점수를 읽는다.
#   숫자 표는 위와 같이 값을 재서 보간한다.
#   ★ 어느 쪽이든 부록 F 를 읽는다 — 구간표를 여기 다시 적지 않는다



def residual_spec() -> tuple:
    """부록 F ①-2 의 기준 잔가율.  ★ 숫자를 여기 적지 않는다 — 읽는다.

    「기준 잔가율 e = 1년 0.88 · 2년 0.78 · 3년 0.67
      4년 이상 = 0.67 − (y−3)×0.07,  하한 0.15」
    """
    text = spec_section("1-2")
    by_year = {int(y): float(v)
               for y, v in re.findall(r"(\d+)년 +(0\.\d+)", text)}
    step = re.search(r"[×x]\s*(0\.\d+)", text)
    floor = re.search(r"하한 *(0\.\d+)", text)
    return (by_year,
            float(step.group(1)) if step else 0.0,
            float(floor.group(1)) if floor else 0.0)
FRAME_SWAP = ("교환(교체)", "용접,절단")
FRAME_SHEET = ("판금/용접",)
LEAK_LEAK = ("누유", "누수")
LEAK_MINOR = ("미세누유", "미세누수")
RANK_OUTER = ("RANK_ONE", "RANK_TWO")
OUTER_PAINT_MANY = 3
FRAME_SHEET_MANY = 2
LEAK_MINOR_MANY = 2
OPTION_PCTL = 0.90
SAMPLE_MIN = 5


def _json(conn, table: str, col: str, lid):
    import json as _j

    row = conn.execute(f"SELECT {col} FROM {table} WHERE listing_id=?",
                       (lid,)).fetchone()
    if not row or not row[0]:
        return None
    try:
        return _j.loads(row[0])
    except ValueError:
        return None


def hand_option_won(conn, lid) -> float:
    """선택 옵션가 합 (개정 301).

    ★ 같은 코드가 카탈로그마다 여러 줄이다 — 코드마다 중앙값을 쓴다.
      그냥 이으면 값이 몇 배로 부푼다 (실측 — 옵션 합이 4.7억이 됐다)
    """
    import json as _j
    import statistics

    row = conn.execute(
        "SELECT options_choice_json, model_catalog_key, site"
        " FROM core_listing WHERE listing_id=?", (lid,)).fetchone()
    if not row or not row[1]:
        return 0.0
    try:
        codes = _j.loads(row[0] or "[]")
    except ValueError:
        return 0.0
    # ★ 코드별 중앙값을 카탈로그를 가리지 않고 낸다.
    #   ★ 부록 F 는 어느 카탈로그의 값인지 말하지 않는다 —
    #     차의 카탈로그로만 재면 못 찾는 코드가 생겨 옵션가가 낮아진다
    #     (실측 08-18 — 272만이 184만이 됐다).  6절에 물어 뒀다
    total = 0.0
    for code in codes if isinstance(codes, list) else []:
        prices = [r[0] for r in conn.execute(
            "SELECT price_manwon FROM dict_model_option"
            " WHERE option_code=? AND price_manwon IS NOT NULL", (str(code),))]
        if prices:
            # ★ 짝수 개면 위쪽 가운데를 쓴다.  부록 F 는 중앙값 이야기를
            #   하지 않는다 — 카탈로그 중복을 지우려고 쓰는 장치다.
            #   여기서 갈리면 1점이 흔들려 대조가 흐려진다
            got = sorted(int(x) for x in prices)
            total += got[len(got) // 2]
    del row, statistics
    return total * WON_PER_MANWON


def hand_depreciation(conn, lid) -> float | None:
    """1-2 신차가 대비 — 손으로: d = 기준잔가율 − 실제잔가율.

    ★ 신차가는 등급기준 + 선택옵션가 합이다 (개정 301).
      등급기준만 쓰면 잔가율이 높게 나와 점수가 통째로 어긋난다
    """
    row = conn.execute(
        "SELECT l.price_current_won, l.price_origin_won,"
        " COALESCE(i.first_registration_date, l.year_month)"
        " FROM core_listing l LEFT JOIN core_inspection i"
        " ON i.listing_id=l.listing_id WHERE l.listing_id=?", (lid,)).fetchone()
    if not row or not row[0] or not row[1] or not row[2]:
        return None
    years = _years(str(row[2]))
    if not years:
        return None
    # ★ 반올림이 아니라 버림이다.  1.67년은 2년이 아니라 1년으로 본다
    #   (실측 08-18 — 반올림으로 재니 46점이 11점으로 나왔다)
    by_year, drop, floor = residual_spec()
    if not by_year:
        return None
    step = max(1, int(years))
    want = by_year.get(step)
    if want is None:
        last = max(by_year)
        want = max(floor, by_year[last] - (step - last) * drop)
    origin = row[1] + hand_option_won(conn, lid)
    return want - row[0] / origin


def hand_frame(conn, lid):
    """2-2 골격 — 손으로: 주요골격(A·B·C랭크) 상태."""
    panels = _json(conn, "core_inspection", "inspection_panel_json", lid)
    if panels is None:
        return None
    sheet = 0
    for one in panels:
        ranks = one.get("attributes") or []
        if not any(str(x).startswith("RANK_") and str(x) not in RANK_OUTER
                   for x in ranks):
            continue
        titles = [(x.get("title") or "") for x in one.get("statusTypes") or []]
        if any(t in FRAME_SWAP for t in titles):
            return "용접·교환 있음"
        if any(t in FRAME_SHEET for t in titles):
            sheet += 1
    if sheet >= FRAME_SHEET_MANY:
        return "판금 2부위 이상"
    return "판금 1부위" if sheet else "이상 없음"


def hand_outer(conn, lid):
    """2-3 외판 — 손으로: 외판부위(1·2랭크) 상태."""
    panels = _json(conn, "core_inspection", "inspection_panel_json", lid)
    if panels is None:
        return None
    paint = 0
    for one in panels:
        ranks = [str(x) for x in one.get("attributes") or []]
        if not any(x in RANK_OUTER for x in ranks):
            continue
        titles = [(x.get("title") or "") for x in one.get("statusTypes") or []]
        if any(t in FRAME_SWAP for t in titles):
            return "교환 있음"
        if any(t in FRAME_SHEET for t in titles):
            paint += 1
    if paint >= OUTER_PAINT_MANY:
        return "판금 3 이상"
    return "판금 1~2" if paint else "교환·판금 없음"


def _leak_states(node, out: list) -> None:
    if isinstance(node, dict):
        got = node.get("statusType") or {}
        if got.get("title"):
            out.append(got["title"])
        for kid in node.get("children") or []:
            _leak_states(kid, out)
    elif isinstance(node, list):
        for kid in node:
            _leak_states(kid, out)


def hand_leak(conn, lid):
    """2-6 누유 — 손으로: 원동기·변속기·동력전달 누유 항목."""
    inners = _json(conn, "core_inspection", "inspection_inner_json", lid)
    if inners is None:
        return None
    seen: list = []
    _leak_states(inners, seen)
    if any(t in LEAK_LEAK for t in seen):
        return "누유 있음"
    minor = sum(1 for t in seen if t in LEAK_MINOR)
    if minor >= LEAK_MINOR_MANY:
        return "미세누유 2곳 이상"
    return "미세누유 1곳" if minor else "누유·미세누유 없음"


def hand_lien(conn, lid):
    """3-4 압류·저당 — 손으로: 압류 + 저당 건수."""
    row = conn.execute(
        "SELECT seizing_cnt, pledge_cnt FROM core_listing WHERE listing_id=?",
        (lid,)).fetchone()
    if not row or (row[0] is None and row[1] is None):
        return None
    return "있음" if (row[0] or 0) + (row[1] or 0) else "0건"


def hand_not_join(conn, lid) -> float | None:
    """3-2 자차 미가입 — 손으로: 미가입 개월 ÷ 보유 개월."""
    import json as _j

    row = conn.execute(
        "SELECT not_join_json, record_first_date FROM core_record"
        " WHERE listing_id=?", (lid,)).fetchone()
    if not row or not row[0] or not row[1]:
        return None
    try:
        spans = _j.loads(row[0])
    except ValueError:
        return None
    if not isinstance(spans, list):
        return None
    # 원문은 「202412~202502」 꼴의 글이다 (실측)
    months = 0
    for one in spans:
        got = re.match(r"(\d{6})\s*~\s*(\d{6})", str(one or ""))
        if not got:
            continue
        a, b = got.group(1), got.group(2)
        months += ((int(b[:4]) - int(a[:4])) * MONTHS_PER_YEAR
                   + int(b[4:6]) - int(a[4:6]))
    held = _years(str(row[1]))
    if not held:
        return None
    return months / (held * MONTHS_PER_YEAR)


def hand_trim(conn, lid) -> float | None:
    """4-1 트림 — 손으로: 그 차종의 트림을 신차가로 줄 세운 순위 ÷ 전체."""
    row = conn.execute(
        "SELECT target_key, price_origin_won FROM core_listing"
        " WHERE listing_id=?", (lid,)).fetchone()
    if not row or not row[0] or not row[1]:
        return None
    # ★ 부록 F 「그 차종의 트림」 — 트림 단위다.  매물 단위가 아니다.
    #   status 로 거르지 않는다 (사라진 매물도 그 차종의 트림이다)
    ladder = sorted({r[0] for r in conn.execute(
        "SELECT DISTINCT price_origin_won FROM core_listing"
        " WHERE target_key=? AND price_origin_won IS NOT NULL",
        (row[0],)) if r[0]})
    if not ladder:
        return None
    if len(ladder) == 1:
        return 1.0
    return (ladder.index(row[1]) + 1) / len(ladder)


def hand_special(conn, lid):
    """2-5 특수 사고 — 손으로: 전손 · 침수 · 도난 중 하나라도 있는가."""
    row = conn.execute(
        "SELECT total_loss_cnt, flood_total_cnt, flood_part_cnt, robber_cnt"
        " FROM core_record WHERE listing_id=?", (lid,)).fetchone()
    if not row or all(x is None for x in row):
        return None
    return "있음" if any(x or 0 for x in row) else "없음"


def spec_section(sec: str) -> str:
    """부록 F 의 그 절 본문.  ★ 규칙이 말로 적힌 축은 여기서 숫자를 읽는다."""
    body = _spec_text()
    got = re.search(rf"^## {re.escape(sec)}\.[^\n]*\n(.*?)(?=^## |\Z)",
                    body, re.S | re.M)
    return got.group(1) if got else ""


def spec_head_points(sec: str) -> float:
    """「## 4-1. 트림 25」의 25.  ★ 만점을 코드에 적지 않는다."""
    body = _spec_text()
    got = re.search(rf"^## {re.escape(sec)}\. *[^\n]*?(\d+) *$", body, re.M)
    return float(got.group(1)) if got else 0.0


def lookup_label(table: list, label: str) -> float | None:
    """말로 된 표에서 그 줄의 점수.  ★ 줄 이름을 부록 F 그대로 쓴다."""
    for name, points in table:
        if name.strip() == label:
            return float(points)
    return None


def hand_integrity(conn, lid) -> float | None:
    """2-8 진정성 — 손으로: 계기판 · 구조변경 · 튜닝.  점수는 부록 F 에서 읽는다."""
    text = spec_section("2-8")
    parts = dict(re.findall(r"^(\S[^\n]*?없음|\S[^\n]*?없다)\s+(\d+)$",
                            text, re.M))
    if not parts:
        return None
    row = conn.execute(
        "SELECT inspection_tuning, inspection_car_state FROM core_inspection"
        " WHERE listing_id=?", (lid,)).fetchone()
    if not row or row[0] is None:
        return None
    got = 0.0
    for name, points in parts.items():
        if "튜닝" in name:
            if not _flag(row[0]):
                got += float(points)
        elif "계기판" in name:
            # ★ 원문에 계기판 교환 칸이 없다 (mileageStateType 전건 null).
            #   「없다」가 아니라 「모른다」라 0 이다 (개정 325)
            continue
        elif str(row[1] or "") == CAR_STATE_OK:
            got += float(points)         # 구조 상태가 「양호」로 확인된 때만
    return got


def hand_special_points(conn, lid) -> float | None:
    """2-5 특수 사고 — 손으로: 셋 다 없으면 만점 · 하나라도 있으면 0."""
    got = hand_special(conn, lid)
    if got is None:
        return None
    full = re.search(r"셋 다 없으면 (\d+)", spec_section("2-5"))
    return 0.0 if got == "있음" else (float(full.group(1)) if full else None)


def _taste_points(name: str) -> tuple:
    """⑥ 취향 절에서 「HUD 15」 같은 줄을 읽는다."""
    body = _spec_text()
    got = re.search(r"^# ⑥ 취향[^\n]*\n(.*?)(?=^# |\Z)", body, re.S | re.M)
    if not got:
        return ()
    line = re.search(rf"^{re.escape(name)}\s*(\d+)([^\n]*)$", got.group(1),
                     re.M)
    return (float(line.group(1)), line.group(2)) if line else ()


def _has_option(conn, lid, words) -> bool | None:
    """옵션 목록에 그 말이 있는가.

    ★ 원문은 코드다 (「10004」).  이름은 사전에 있다 —
      코드를 글자로 찾으면 전건 「없음」이 된다 (실측 08-18)
    """
    import json as _j

    row = conn.execute(
        "SELECT options_choice_json, options_standard_json,"
        " options_etc_json, model_catalog_key, site FROM core_listing"
        " WHERE listing_id=?", (lid,)).fetchone()
    if not row or not row[3]:
        return None
    codes: list = []
    for one in row[:3]:
        try:
            got = _j.loads(one) if one else []
        except ValueError:
            got = []
        if isinstance(got, list):
            codes += [str(x) for x in got if not isinstance(x, (dict, list))]
    if not codes:
        return False
    marks = ",".join("?" * len(codes))
    names = [r[0] for r in conn.execute(
        "SELECT option_name FROM dict_model_option"
        f" WHERE site=? AND model_catalog_key=? AND option_code IN ({marks})",
        (row[4], row[3], *codes))]
    if not names:
        return None                       # 사전이 없어 이름을 못 본다
    body = " ".join(names)
    return any(w in body for w in words)


def hand_color(conn, lid) -> float | None:
    """⑥ 색상 — 손으로: 흰·검정 / 회색·은색 / 그 밖."""
    got = _taste_points("색상")
    if not got:
        return None
    row = conn.execute(
        "SELECT color_ext_raw FROM core_listing WHERE listing_id=?",
        (lid,)).fetchone()
    if not row or not row[0]:
        return None
    name = str(row[0])
    # 「흰·검정 10 · 회색·은색 7 · 그 밖 3」 — 무리와 점수를 짝지어 읽는다.
    #   ★ 「·」가 무리 안에도 무리 사이에도 쓰인다.  숫자로 끊는다
    tail = 0.0
    for words, points in re.findall(r"([^\d]+?)\s*(\d+)", got[1]):
        names = [w.strip() for w in re.split(r"[·、,]", words) if w.strip()]
        if any(w == "그 밖" for w in names):
            tail = float(points)
            continue
        if any(w and w in name for w in names):
            return float(points)
    return tail


def hand_usage(conn, lid):
    """3-1 용도 — 손으로: 광고 유형 · 점검부 용도변경 · 보험 용도이력 셋 대조."""
    row = conn.execute(
        "SELECT l.advertisement_type, l.lease_rent_info_json,"
        " i.usage_change_types_json, r.use_gov, r.use_business,"
        " r.plate_use_char, r.use1_json"
        " FROM core_listing l"
        " LEFT JOIN core_inspection i ON i.listing_id=l.listing_id"
        " LEFT JOIN core_record r ON r.listing_id=l.listing_id"
        " WHERE l.listing_id=?", (lid,)).fetchone()
    if not row or all(x is None for x in row):
        return None
    body = " ".join(str(x) for x in row if x is not None)
    if "RENT" in body.upper() or "렌트" in body or "대여" in body:
        return "대여용(렌트)"
    if "LEASE" in body.upper() or "리스" in body:
        return "리스"
    if _flag(row[3]):
        return "관용"
    if _flag(row[4]) or "영업" in body or "택시" in body:
        return "영업용(택시 등)"
    return "자가용만"


def hand_site_grade(conn, lid):
    """5-2 사이트 우수등급 — 손으로: 진단 · 우수등급 · 직영/직거래."""
    row = conn.execute(
        "SELECT site, diagnosis_car, site_pass_grade, site_diagnosis_grade,"
        " sell_type FROM core_listing WHERE listing_id=?", (lid,)).fetchone()
    if not row:
        return None
    site, diag, pass_grade, diag_grade, sell = row
    # ★ 우수등급과 진단등급은 다르다.  site_diagnosis_grade 는 진단 결과이지
    #   「우수」가 아니다 — 그것으로 재면 진단만 받은 차가 10점이 된다
    good = _flag(pass_grade)
    del diag_grade
    if not _flag(diag):
        return "무진단"
    if str(site) == "kcar":
        return ("K카 직영 · 엔카 진단+우수" if "직영" in str(sell or "")
                else "K카 직거래 (진단 있음)")
    return "K카 직영 · 엔카 진단+우수" if good else "엔카 진단만"


def hand_inspection_src(conn, lid):
    """5-3 점검 출처 — 손으로: 플랫폼 직영 점검 · 판매자 등록 · 없음."""
    row = conn.execute(
        "SELECT inspection_formats_json, inspector_name, platform_verified"
        " FROM core_listing WHERE listing_id=?", (lid,)).fetchone()
    if not row:
        return None
    body = str(row[0] or "")
    if not body or body in ("[]", "null"):
        return "없음"
    return "플랫폼 직영 점검" if "TABLE" in body.upper() else "판매자 등록"


def hand_hud(conn, lid) -> float | None:
    """⑥ HUD — 손으로: 옵션 목록에 HUD 가 있는가."""
    got = _taste_points("HUD")
    has = _has_option(conn, lid, ("HUD", "헤드업"))
    if not got or has is None:
        return None
    return got[0] if has else 0.0


def hand_sunroof(conn, lid) -> float | None:
    """⑥ 선루프 — 손으로: 옵션 목록에 선루프가 있는가."""
    got = _taste_points("선루프")
    has = _has_option(conn, lid, ("선루프", "SUNROOF", "파노라마"))
    if not got or has is None:
        return None
    return got[0] if has else 0.0


def hand_picked(conn, lid) -> float | None:
    """⑥ 지정 옵션 — 손으로: 아무것도 안 골랐으면 만점 (부록 F)."""
    got = _taste_points("지정 옵션")
    if not got:
        return None
    picked = conn.execute(
        "SELECT COUNT(*) FROM user_picked_option").fetchone() \
        if _has_table(conn, "user_picked_option") else None
    if picked and picked[0]:
        return None                      # 고른 것이 있으면 비율 계산이 필요하다
    return got[0]


def _has_table(conn, name: str) -> bool:
    return bool(conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,)).fetchone())


def _option_prices(conn) -> dict:
    """코드별 옵션가 (원).  ★ 한 번만 만든다 — 매물마다 다시 세면 느리다."""
    if _option_prices.cache is None:
        by_code: dict = {}
        for code, mw in conn.execute(
            "SELECT option_code, price_manwon FROM dict_model_option"
            " WHERE price_manwon IS NOT NULL"
        ):
            by_code.setdefault(str(code), []).append(int(mw))
        _option_prices.cache = {
            code: sorted(v)[len(v) // 2] * WON_PER_MANWON
            for code, v in by_code.items()}
    return _option_prices.cache


_option_prices.cache = None


def hand_options(conn, lid) -> float | None:
    """4-2 옵션 — 손으로: 내 옵션가 합 ÷ 그 차종 옵션가 합의 P90 (상한 1)."""
    import json as _j

    row = conn.execute(
        "SELECT target_key, options_choice_json FROM core_listing"
        " WHERE listing_id=?", (lid,)).fetchone()
    if not row or not row[0] or not row[1]:
        return None
    prices = _option_prices(conn)
    try:
        mine = _j.loads(row[1])
    except ValueError:
        return None
    if not isinstance(mine, list) or not mine:
        return None
    got = sum(prices.get(str(x), 0) for x in mine)
    sums = []
    for raw, in conn.execute(
        "SELECT options_choice_json FROM core_listing"
        " WHERE target_key=? AND options_choice_json IS NOT NULL", (row[0],)
    ):
        try:
            codes = _j.loads(raw)
        except ValueError:
            continue
        if not isinstance(codes, list) or not codes:
            continue
        one = sum(prices.get(str(x), 0) for x in codes)
        if one:
            sums.append(one)
    if len(sums) < SAMPLE_MIN:
        return None
    sums.sort()
    base = sums[min(len(sums) - 1, int(len(sums) * OPTION_PCTL))]
    return min(got / base, 1.0) if base else None


def survey(conn) -> None:
    """전수 검증의 나머지 — 축별 확인율 · 등급 분포 (부록 F 「전수 검증」).

    ★ 「구현했습니다」가 아니라 「무엇을 못 봤는가」를 낸다.
      확인 안 됨이 많은 축이 곧 「무엇을 더 받아야 하는가」다 (개정 328)
    ★ 「확인 안 됨」은 source='missing' 만이 아니다 —
      score/scorer.py 의 UNCONFIRMED_SOURCES 가 정본이다 (개정 325).
      missing 만 세면 「시세 표본 부족」이 확인된 것으로 세어진다
    """
    import collections

    from score.scorer import UNCONFIRMED_SOURCES

    ver = conn.execute(
        "SELECT calc_version FROM result_score"
        " ORDER BY calculated_at DESC LIMIT 1").fetchone()
    if not ver:
        print("판정 결과가 없다")
        return
    ver = ver[0]
    print(f"\n── 전수 검증 (판정 {ver}) ──────────────────────────────")

    grades = collections.Counter(r[0] for r in conn.execute(
        "SELECT grade FROM result_score WHERE calc_version=?", (ver,)))
    total = sum(grades.values())
    print(f"\n등급 분포 — 전 {total:,}건 (절대 기준 · 개정 324)")
    for name in GRADE_ORDER:
        got = grades.get(name, 0)
        print(f"  {name}  {got:>6,}  {got * 100 / total:>5.1f}%"
              if total else f"  {name}  0")
    rest = {k: n for k, n in grades.items() if k not in GRADE_ORDER}
    if rest:
        print(f"  그 밖 {rest}")

    rows = conn.execute(
        "SELECT axis, source, COUNT(*), MAX(max_points) FROM result_axis"
        " WHERE calc_version=? GROUP BY axis, source", (ver,)).fetchall()
    by_axis: dict = {}
    for axis, src, n, points in rows:
        got = by_axis.setdefault(axis, {"n": 0, "no": 0, "pt": points or 0})
        got["n"] += n
        if src in UNCONFIRMED_SOURCES:
            got["no"] += n
    print("\n축별 확인 안 됨 — ★ 많은 순.  무엇을 더 받아야 하는가")
    print(f"  {'축':<22}{'확인 안 됨':>12}{'비율':>8}{'배점':>7}"
          f"{'잃은 점':>9}")
    lost = 0.0
    for axis, got in sorted(by_axis.items(),
                            key=lambda kv: -kv[1]["no"] * kv[1]["pt"]):
        share = got["no"] * 100 / got["n"] if got["n"] else 0
        miss = got["no"] * got["pt"] / got["n"] if got["n"] else 0
        lost += miss
        print(f"  {axis:<22}{got['no']:>7,} / {got['n']:<4,}{share:>7.1f}%"
              f"{got['pt']:>7.0f}{miss:>9.1f}")
    print(f"\n  ★ 매물 하나가 「확인 못 해서」 잃는 점수 평균 {lost:.1f}점")

    got = conn.execute(
        "SELECT ROUND(AVG(confirmed_points * 100.0 / denominator), 1)"
        " FROM result_score WHERE calc_version=? AND denominator>0",
        (ver,)).fetchone()
    print(f"  ★ 확인율 평균 {got[0]}%\n")


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
        # 축 · source 무늬 · 부록 F 절 · 손계산 · 방식 · 이름
        #   방식  desc  큰 값이 좋은 숫자 표 (보간)
        #        asc   작은 값이 좋은 숫자 표 (보간)
        #        label 말로 된 표 — 줄 이름을 골라 점수를 읽는다
        #        ratio 비율 × 만점 (부록 F 가 식으로 적은 축)
        #        point 손계산이 점수를 바로 낸다 (규칙이 말로 적힌 축)
        ("value.market", "market_median%", "1-1", hand_market, "desc",
         "시세 대비 (중앙값−가격)/중앙값"),
        ("value.depreciation", "origin_price", "1-2", hand_depreciation,
         "desc", "신차가 대비 기준잔가율 − 실제잔가율"),
        ("value.mileage", "mileage_per_year", "1-3", hand_mileage, "asc",
         "주행 대비 연평균 km"),
        ("value.soh", "%", "1-3", None, "asc", "배터리 SOH (전기차만)"),
        ("state.accident", "record_accident_count", "2-1", hand_accident,
         "asc", "사고 회수"),
        ("state.frame", "frame_%", "2-2", hand_frame, "label", "골격 상태"),
        ("state.outer", "outer_%", "2-3", hand_outer, "label", "외판 상태"),
        ("state.repair", "record_my_cost", "2-4", hand_repair, "asc",
         "자차 수리비 원"),
        ("state.special", "record_special", "2-5", hand_special_points,
         "point", "전손·침수·도난"),
        ("state.leak", "leak_%", "2-6", hand_leak, "label", "누유 상태"),
        ("state.consumable", "%", "2-7", None, "asc", "타이어 트레드 최소값"),
        ("state.integrity", "integrity_%", "2-8", hand_integrity, "point",
         "계기판·구조변경·튜닝"),
        ("history.usage", "%", "3-1", hand_usage, "label", "용도 (셋 대조)"),
        ("history.not_join", "not_join_%", "3-2", hand_not_join, "asc",
         "자차 미가입 비율"),
        ("history.owner", "owner_%", "3-3", hand_owner, "asc",
         "소유자 변경 횟수"),
        ("history.lien", "detail_seizing", "3-4", hand_lien, "label",
         "압류·저당"),
        ("spec.trim", "trim_origin_price", "4-1", hand_trim, "ratio",
         "트림 순위 ÷ 전체"),
        ("spec.options", "options_choice_price", "4-2", hand_options,
         "ratio", "옵션가 ÷ 그 차종 P90"),
        ("warranty.general", "encar_warranty_general", "7-1",
         hand_warranty_general, "desc", "일반·차체 보증 잔여 개월"),
        ("warranty.power", "encar_warranty_power", "7-2",
         hand_warranty_power, "desc", "동력계 보증 잔여 개월"),
        ("warranty.site", "%", "5-0", hand_site_warranty, "point",
         "사이트 보증 (항목 합)"),

        ("taste.hud", "option_codes", "6", hand_hud, "point", "HUD"),
        ("taste.picked", "%", "6", hand_picked, "point", "지정 옵션"),
        ("taste.color", "detail_color", "6", hand_color, "point", "색상"),
        ("taste.sunroof", "option_codes", "6", hand_sunroof, "point",
         "선루프"),
    ]
    print(f"손계산 대조 — 부록 F 표를 읽어 스스로 계산했습니다 "
          f"(판정 {at[:10]})\n")
    bad = 0
    done, skipped = 0, []
    for axis, like, sec, fn, mode, label in checks:
        table = tables.get(sec)
        if fn is None:
            skipped.append(f"{axis} — {label}: 손계산을 못 냈다")
            continue
        if not conn.execute(
                "SELECT 1 FROM result_axis WHERE axis=? LIMIT 1",
                (axis,)).fetchone():
            skipped.append(f"{axis} — {label}: 판정에 이 축의 행이 없다")
            continue
        if mode in ("desc", "asc", "label") and not table:
            skipped.append(f"{axis} — 부록 F {sec} 표를 못 읽었다")
            continue
        rows = pick(conn, axis, like)
        if not rows:
            total = conn.execute(
                "SELECT COUNT(*) FROM result_axis WHERE axis=?"
                " AND source='missing'", (axis,)).fetchone()[0]
            skipped.append(f"{axis} — {label}: 표본이 없다 "
                           f"(전건 확인 안 됨 · missing {total:,}건)")
            continue
        print(f"★ {axis} — {label} (부록 F {sec})")
        seen = 0
        for lid, stored, src in rows:
            got = fn(conn, lid)
            if got is None:
                print(f"    {lid:<6} 손계산 재료가 없다")
                continue
            if mode == "label":
                want = lookup_label(table, got)
                shown = f"{got!s:>14}"
            elif mode == "ratio":
                want = got * spec_head_points(sec)
                shown = f"{got:>14,.4f}"
            elif mode == "point":
                want = got
                shown = f"{got:>14,.4f}"
            else:
                want = lookup(table, got, mode == "desc")
                shown = f"{got:>14,.4f}"
            if want is None:
                print(f"    {lid:<6} 부록 F {sec} 에 「{got}」 줄이 없다")
                bad += 1
                continue
            want = round(want)
            mark = "○" if want == stored else "✗"
            if want != stored:
                bad += 1
            seen += 1
            print(f"    {lid:<6} 입력 {shown} → 손 {want:>4} · "
                  f"저장 {stored:>4}  {mark}  ({src})")
        if seen:
            done += 1
        print()
    print(f"손계산한 축 {done} / 부록 F {len(checks)}축")
    if skipped:
        print("못 한 축 — ★ 왜 못 했는지 적는다")
        for one in skipped:
            print(f"  · {one}")
        print()
    survey(conn)
    print("결과:", "손계산과 맞습니다" if not bad else f"어긋난 것 {bad}건")
    conn.close()
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
