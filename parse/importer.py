# -*- coding: utf-8 -*-
"""반입 입력 해석 (13장 STEP 136a · 136b).

지시서   STEP 136a (받는 형식) · STEP 136b ① (core_listing 을 어떻게 채우나)
근거     ★ 붙여넣은 것이 무엇인지 사람에게 다시 묻지 않는다.  보고 판별한다.
         고르게 하면 잘못 고른 것을 아무도 못 잡는다
금지     없는 값을 추정하는 것.  CSV 에 없는 칸은 NULL 이다 (STEP 136b ①)
         반입 시점에 fuel_match 로 거르는 것 — 상세를 안 받았으니 근거가 없다
"""
from __future__ import annotations

import csv
import io
import json

from contracts import (
    CSV_COLUMNS, FORMAT_CSV, FORMAT_IDS, FORMAT_JSON, YM_PLAIN,
)
from errors import ValidationError

STEP = "STEP 136a"

# 엔카 목록 응답의 봉투 키.  ★ 하나라도 있으면 원문 JSON 으로 본다
ENVELOPE_KEYS = ("SearchResults", "Count")


def detect_format(text: str) -> str:
    """붙여넣은 내용이 어느 형식인가 (STEP 136a).

    판별 순서가 곧 원칙 순서다 — ① 원문 JSON → ③ CSV → ② ID 목록
    ★ ID 목록을 먼저 보면 숫자 한 열짜리 CSV 를 ID 로 오인한다
    """
    body = (text or "").strip()
    if not body:
        raise ValidationError("넣은 내용이 없습니다", step=STEP)
    if body[0] in "{[":
        return FORMAT_JSON
    head = body.splitlines()[0]
    if "," in head and "source_id" in head:
        return FORMAT_CSV
    return FORMAT_IDS


def parse_import(text: str, fmt: str, site: str) -> list[dict]:
    """형식별로 core_listing 행 후보를 만든다.

    ★ 넣지 않은 칸은 키 자체를 두지 않는다.  None 을 넣으면 「받았는데 없다」가
      되고, 나중에 S6 이 채운 값을 덮어쓸 수 있다 (STEP 136b ①)
    반환   [{'site','source_id', ...}]
    """
    if fmt == FORMAT_JSON:
        return _from_json(text, site)
    if fmt == FORMAT_CSV:
        return _from_csv(text, site)
    return _from_ids(text, site)


def _from_json(text: str, site: str) -> list[dict]:
    """엔카 목록 응답 원문.  ★ 파서는 이미 있다 — 새로 짜지 않는다."""
    from parse.encar.mapping import parse_list_item

    try:
        body = json.loads(text)
    except ValueError as exc:
        raise ValidationError(f"JSON 으로 읽지 못했습니다: {exc}",
                              step=STEP) from exc
    items = body.get("SearchResults") if isinstance(body, dict) else body
    if not isinstance(items, list):
        raise ValidationError(
            "목록을 찾지 못했습니다 — SearchResults 배열이 있어야 합니다",
            step=STEP)
    return [parse_list_item(item, site) for item in items]


def _from_csv(text: str, site: str) -> list[dict]:
    """CSV 6열.  ★ 머리글로 읽는다.  열 순서에 기대지 않는다."""
    reader = csv.DictReader(io.StringIO(text))
    missing = [c for c in CSV_COLUMNS if c not in (reader.fieldnames or [])]
    if missing:
        raise ValidationError(
            f"CSV 에 없는 열: {', '.join(missing)}", step=STEP)
    rows = []
    for n, row in enumerate(reader, start=2):
        sid = (row.get("source_id") or "").strip()
        if not sid:
            raise ValidationError(f"{n}행에 source_id 가 없습니다", step=STEP)
        rows.append({
            "site": site,
            "source_id": sid,
            "target_key": (row.get("target_key") or "").strip() or None,
            "trim_badge": (row.get("trim") or "").strip() or None,
            "year_month": _ym(row.get("year_month"), n),
            "mileage_km": _int(row.get("mileage_km"), "mileage_km", n),
            "price_current_won": _int(row.get("price_won"), "price_won", n),
        })
    if not rows:
        raise ValidationError("CSV 에 자료 행이 없습니다", step=STEP)
    return rows


def _from_ids(text: str, site: str) -> list[dict]:
    """매물 ID 목록.  한 줄에 하나 — 최소 입력이다 (STEP 136a ②)."""
    rows = []
    for n, line in enumerate(text.splitlines(), start=1):
        sid = line.strip()
        if not sid or sid.startswith("#"):
            continue
        if not sid.isdigit():
            raise ValidationError(
                f"{n}행이 매물 ID 가 아닙니다: {sid[:20]}", step=STEP)
        rows.append({"site": site, "source_id": sid})
    if not rows:
        raise ValidationError("매물 ID 가 한 건도 없습니다", step=STEP)
    return rows


def _int(value, field: str, line: int) -> int | None:
    raw = (value or "").strip()
    if not raw:
        return None
    try:
        return int(float(raw))
    except ValueError as exc:
        raise ValidationError(
            f"{line}행 {field} 가 숫자가 아닙니다: {raw[:20]}",
            step=STEP) from exc


def _ym(value, line: int) -> str | None:
    """'2024-12' 로 맞춘다.  ★ core_listing 이 그 형식을 쓴다 (STEP 19)."""
    raw = (value or "").strip()
    if not raw:
        return None
    digits = raw.replace("-", "").replace(".", "").replace("/", "")
    if len(digits) != YM_PLAIN or not digits.isdigit():
        raise ValidationError(
            f"{line}행 year_month 가 YYYY-MM 이 아닙니다: {raw[:20]}",
            step=STEP)
    return f"{digits[:4]}-{digits[4:]}"
