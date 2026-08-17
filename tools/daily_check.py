# -*- coding: utf-8 -*-
"""일일 점검 — 매일 23:00 (개정 334 · S29).

지시서   0장 S29 · 부록 E · `check_daily_at`
근거     마스터 지시 — 「작업이 끝나거나 하루 마무리 시점에 일제 점검하게」
필수     어제와 견준다 — 「fatal 4 → 6」 같은 것이 신호다
        ★ 숫자 하나로는 좋아졌는지 나빠졌는지 모른다
필수     미해결 목록 — inbox 미처리 · 검사 실패 · 마스터 지적 중 안 된 것
금지     서비스를 재시작하는 것 (개정 308 — 마스터의 CSRF 가 끊긴다)
사용     systemd timer 가 부른다.  손으로는 python3.11 tools/daily_check.py
"""
from __future__ import annotations

import collections
import json
import os
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 단위 환산 — UTC 를 한국 날짜로 (2장 상수표 · V4-13).
# ★ 「오늘의 기록」은 사람이 보는 날짜여야 한다
KST_OFFSET_HOURS = 9
sys.path.insert(0, ROOT)

DB = os.path.join(ROOT, "carwatch.db")
OUT = os.path.join(ROOT, "outputs", "daily")


def _now():
    return datetime.now(timezone.utc)


def _run(*cmd) -> str:
    got = subprocess.run([sys.executable, *cmd], cwd=ROOT, check=False,
                         capture_output=True, text=True)
    return got.stdout + got.stderr


def counts(text: str) -> dict:
    """check_all 출력에서 숫자를 뽑는다.  ★ 숫자가 없으면 기록이 아니다."""
    got = re.search(r"통과 (\d+) · fatal (\d+) · warn (\d+)", text)
    if not got:
        return {}
    return {"통과": int(got.group(1)), "fatal": int(got.group(2)),
            "warn": int(got.group(3))}


def failed_tests(text: str) -> list:
    got = re.search(r"결과: 실패 — (.+)", text)
    return [x.strip() for x in got.group(1).split(",")] if got else []


def db_numbers() -> dict:
    """수집 · 판정 · 사전 숫자.  ★ DB 를 읽기 전용으로 연다."""
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        def one(sql, *args):
            try:
                return conn.execute(sql, args).fetchone()[0]
            except sqlite3.Error:
                return None

        ver = one("SELECT calc_version FROM result_score"
                  " ORDER BY calculated_at DESC LIMIT 1")
        grades = collections.Counter(
            r[0] for r in conn.execute(
                "SELECT grade FROM result_score WHERE calc_version=?", (ver,)))
        return {
            "매물": one("SELECT COUNT(*) FROM core_listing WHERE status='active'"),
            "원문": one("SELECT COUNT(*) FROM raw_response WHERE status='ok'"),
            "원문 실패": one("SELECT COUNT(*) FROM raw_response"
                          " WHERE status='error'"),
            "판정": sum(grades.values()),
            "등급": dict(grades.most_common()),
            "사전 pending": one("SELECT COUNT(*) FROM dict_model_option"
                              " WHERE status='pending'"),
            "미분류": one("SELECT COUNT(*) FROM meta_field_usage"
                       " WHERE usage='unclassified'"),
            "확인율 평균": one(
                "SELECT ROUND(AVG(confirmed_points*100.0/denominator),1)"
                " FROM result_score WHERE calc_version=? AND denominator>0",
                ver),
        }
    finally:
        conn.close()


def yesterday(path: str) -> dict:
    """어제 기록의 숫자.  ★ 없으면 빈 것 — 첫날은 견줄 것이 없다."""
    if not os.path.isfile(path):
        return {}
    got = re.search(r"```json\n(.*?)\n```", open(path, encoding="utf-8").read(),
                    re.S)
    try:
        return json.loads(got.group(1)) if got else {}
    except (ValueError, AttributeError):
        return {}


def arrow(now, before) -> str:
    """어제와 견준다.  ★ 「4 → 6」이 신호다."""
    if before is None or now is None or now == before:
        return f"{now}"
    return f"{before} → {now}" + ("  ★ 늘었다" if now > before else "")


def open_items() -> list:
    """미해결 — inbox 미처리 · 마스터 지적 중 안 된 것."""
    out = []
    inbox = os.path.join(ROOT, "inbox")
    if os.path.isdir(inbox):
        left = [f for f in sorted(os.listdir(inbox)) if f.endswith(".md")]
        if left:
            out.append(f"inbox 미처리 {len(left)}건 — {', '.join(left[:4])}")
    return out


def main() -> int:
    at = _now()
    day = (at + timedelta(hours=KST_OFFSET_HOURS)).strftime("%Y-%m-%d")   # 한국 날짜로 적는다
    os.makedirs(OUT, exist_ok=True)
    checks = _run(os.path.join(ROOT, "tools", "check_all.py"))
    tests = _run(os.path.join(ROOT, "tools", "run_tests.py"))
    spec = _run(os.path.join(ROOT, "tools", "check_spec.py"))
    now = {**counts(checks), **db_numbers(),
           "시험 실패": len(failed_tests(tests))}
    prev_path = os.path.join(
        OUT, f"{(at + timedelta(hours=KST_OFFSET_HOURS) - timedelta(days=1)):%Y-%m-%d}.md")
    was = yesterday(prev_path)

    lines = [
        f"# 일일 점검 — {day}", "",
        f"자동 실행 (S29 · 개정 334) · {at.isoformat()[:19]}Z", "",
        "## 숫자 — ★ 어제와 견준다", "",
        "| 항목 | 어제 → 오늘 |", "|---|---|",
    ]
    for key in ("통과", "fatal", "warn", "시험 실패", "매물", "원문",
                "원문 실패", "판정", "미분류", "사전 pending", "확인율 평균"):
        lines.append(f"| {key} | {arrow(now.get(key), was.get(key))} |")
    lines += ["", f"등급 분포 — `{now.get('등급')}`", ""]

    fails = [x.strip() for x in checks.splitlines()
             if x.startswith("  V") and "—" in x]
    lines += ["## 실패한 검사", ""]
    lines += [f"- {x}" for x in fails[:20]] or ["- 없습니다"]
    lines += ["", "## 시험", ""]
    lines += [f"- {x}" for x in failed_tests(tests)] or ["- 전부 통과"]
    lines += ["", "## 지시서 점검 (S28) — ★ 가이드가 고칠 것", ""]
    lines += [f"- {x}" for x in spec.splitlines() if x.startswith("S28")
              and not x.endswith("0 []")] or ["- 없습니다"]
    lines += ["", "## 미해결", ""]
    lines += [f"- {x}" for x in open_items()] or ["- 없습니다"]
    lines += ["", "## 다음 점검이 견줄 숫자", "", "```json",
              json.dumps(now, ensure_ascii=False, indent=1), "```", ""]

    path = os.path.join(OUT, f"{day}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"일일 점검 → {path}")
    print(f"  통과 {now.get('통과')} · fatal {now.get('fatal')} · "
          f"시험 실패 {now.get('시험 실패')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
