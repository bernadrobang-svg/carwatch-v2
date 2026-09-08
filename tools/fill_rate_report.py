# -*- coding: utf-8 -*-
"""★ M-14 — 「사이트 × 칸」 채움율 표 (규격 `docs/GV70_TAB4.md` 12장).

★★★ 마스터 잣대 —
```
0% 인 칸이 있으면 fatal      — 받아 놓고 안 쓰는 것이다
지난 회차보다 떨어지면 fatal  — 새 사이트가 물을 탄 것이다
```
★ 지난 회차 수는 ★ `outputs/fill_rate.json` 에 남긴다 — ★ 다음에 견준다.
★ 분모는 ★ **살아 있는 매물**이다 (`active`·`new`·`relisted`) — ★ 유리한 분모로 안 잰다

돌리는 법   python3.11 tools/fill_rate_report.py
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

REPORT = "outputs/fill_rate.json"
LIVE = "status IN ('active','new','relisted')"
# ★ 칸 이름은 ★ 마스터께서 부르시는 말이다 — ★ 화면과 같은 말을 쓴다
COLS = (
    ("가격", "price_current_won"),
    ("연식", "year_month"),
    ("주행", "mileage_km"),
    ("트림", "trim_grade_name"),
    ("색", "color_ext_raw"),
    ("사진", "photo_list_json"),
    ("신차가", "price_origin_won"),
    ("옵션", "options_choice_json"),
    ("보증", "warranty_body_month"),
    ("카탈로그", "model_catalog_key"),
    ("VIN", "vin"),
    ("배달", "delivery_nationwide"),
    ("사이트진단", "site_inspection"),
    ("상세", "detail_status"),
)


def run(db: str = "carwatch.db") -> dict:
    conn = sqlite3.connect(os.path.join(ROOT, db))
    have = {r[1] for r in conn.execute("PRAGMA table_info(core_listing)")}
    sites = [r[0] for r in conn.execute(
        f"SELECT site, COUNT(*) FROM core_listing WHERE {LIVE}"
        " GROUP BY 1 ORDER BY 2 DESC")]
    out: dict = {"_잰_때": _now(), "사이트": {}}
    for site in sites:
        n = conn.execute(
            f"SELECT COUNT(*) FROM core_listing WHERE {LIVE} AND site = ?",
            (site,)).fetchone()[0]
        row: dict = {"매물": n}
        for label, col in COLS:
            if col not in have:
                continue
            got = conn.execute(
                f"SELECT COUNT({col}) FROM core_listing"
                f" WHERE {LIVE} AND site = ?", (site,)).fetchone()[0]
            row[label] = round(got * 100 / n) if n else 0
        out["사이트"][site] = row
    conn.close()
    return out


def _now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()[:16].replace("T", " ")


def compare(now: dict) -> list:
    """★ 0% 인 칸 · ★ 지난 회차보다 떨어진 칸을 낸다."""
    path = os.path.join(ROOT, REPORT)
    was = {}
    if os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as f:
                was = (json.load(f).get("사이트") or {})
        except (OSError, ValueError):
            was = {}
    bad = []
    for site, row in now["사이트"].items():
        for label, pct in row.items():
            if label == "매물":
                continue
            if pct == 0:
                bad.append(f"{site}.{label} 0% — 받아 놓고 안 쓴다")
            old = (was.get(site) or {}).get(label)
            if old is not None and pct < old:
                bad.append(f"{site}.{label} {old}% → {pct}% 떨어졌다")
    return bad


if __name__ == "__main__":
    got = run()
    bad = compare(got)
    head = ["사이트"] + [c for c, k in COLS]
    print("  " + " ".join(f"{h:>6}" for h in head))
    for site, row in got["사이트"].items():
        cells = [f"{site[:10]:>6}"] + [
            f"{row.get(c, '-')!s:>6}" for c, _k in COLS]
        print("  " + " ".join(cells))
    print()
    if bad:
        print(f"★ fatal {len(bad)}건")
        for b in bad[:20]:
            print("   ", b)
    else:
        print("★ 0% 도 · 떨어진 것도 없다")
    with open(os.path.join(ROOT, REPORT), "w", encoding="utf-8") as f:
        json.dump(got, f, ensure_ascii=False, indent=2)
    print(f"★ 적었다 — {REPORT}")
