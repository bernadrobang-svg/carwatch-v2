# -*- coding: utf-8 -*-
"""주간 일제 점검 — 금 02:00 · 개발측 몫 (개정 334 · S29).

지시서   0장 S29 · 부록 E · `check_weekly_at`
근거     마스터 지시 — 「금요일 새벽 2시부터 너희들이 서로 일괄로 점검하게」
        ★ 「서로」가 핵심이다.  각자 자기를 검사하면 같은 맹점을 넘긴다
이 파일  개발측 → 가이드 (규격을 검사한다).  ★ 고치지 않는다 (규칙 2)
가이드 몫 같은 파일에 가이드가 이어 쓴다
필수     02:00 에 개발측 몫이 먼저 — 04:00 수집보다 앞이다.
        결과를 보고 수집한다
금지     서비스를 재시작하는 것 (개정 308)
사용     systemd timer 가 부른다.  손으로는 python3.11 tools/weekly_check.py
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 단위 환산 — UTC 를 한국 날짜로 (2장 상수표 · V4-13).
# ★ 「오늘의 기록」은 사람이 보는 날짜여야 한다
KST_OFFSET_HOURS = 9
sys.path.insert(0, ROOT)

OUT = os.path.join(ROOT, "outputs", "weekly")
# 미확정이 이만큼 오래가면 그것도 결함이다 (S29)
STALE_WEEKS = 2


def _run(*cmd) -> str:
    got = subprocess.run([sys.executable, *cmd], cwd=ROOT, check=False,
                         capture_output=True, text=True)
    return got.stdout + got.stderr


def spec_findings(text: str) -> list:
    """S28 이 잡은 것.  ★ 개발측이 고치지 않는다 — 가이드에게 넘긴다."""
    return [x.strip() for x in text.splitlines()
            if x.startswith("S28") and not x.rstrip().endswith("0 []")]


def unfinished_spec() -> list:
    """★ 「미확정」으로 남은 것 — 몇 주째인지 함께 (S29)."""
    path = os.path.join(ROOT, "docs", "guide", "02_미확정.md")
    if not os.path.isfile(path):
        return []
    out = []
    for line in open(path, encoding="utf-8"):
        got = re.match(r"\| *([^|]+?) *\| *(\d{2}-\d{2}) *\|", line)
        if got and "---" not in got.group(1):
            out.append(f"{got.group(1)} (등재 {got.group(2)})")
    return out


def missing_checks() -> list:
    """규격이 요구했는데 코드에 없는 검사 (docs/CHECKS.md)."""
    path = os.path.join(ROOT, "docs", "CHECKS.md")
    if not os.path.isfile(path):
        return []
    body = open(path, encoding="utf-8").read()
    block = body.split("## ★ 규격이 요구했는데 코드에 없는 검사", 1)
    if len(block) < 2:
        return []
    return [x.strip("- ").strip() for x in block[1].splitlines()
            if x.startswith("- ")][:20]


def idle_checks() -> list:
    """자료가 없어 못 도는 검사.  ★ 오래가면 수집을 고쳐야 한다는 뜻이다."""
    text = _run(os.path.join(ROOT, "tools", "check_all.py"))
    return [x.strip() for x in text.splitlines()
            if "자료 없" in x or "미실행" in x][:12]


def unused_config() -> list:
    """폐기 후보 — 코드가 안 읽는 config 키."""
    import json

    out = []
    cfg_dir = os.path.join(ROOT, "config")
    src = ""
    for base, dirs, files in os.walk(ROOT):
        if any(p in base for p in (".git", "outputs", "docs", "ref")):
            continue
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git")]
        for f in files:
            if f.endswith(".py"):
                src += open(os.path.join(base, f), encoding="utf-8").read()
    for name in sorted(os.listdir(cfg_dir)):
        if not name.endswith(".json"):
            continue
        try:
            got = json.load(open(os.path.join(cfg_dir, name), encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if not isinstance(got, dict):
            continue
        for key in got:
            if key.startswith("_") or f'"{key}"' in src or f"'{key}'" in src:
                continue
            out.append(f"{name}:{key}")
    return out[:20]


def main() -> int:
    at = datetime.now(timezone.utc)
    day = (at + timedelta(hours=KST_OFFSET_HOURS)).strftime("%Y-%m-%d")
    os.makedirs(OUT, exist_ok=True)
    spec = _run(os.path.join(ROOT, "tools", "check_spec.py"))

    lines = [
        f"# 주간 일제 점검 — {day}", "",
        f"자동 실행 (S29 · 개정 334) · {at.isoformat()[:19]}Z", "",
        "**★ 「서로」 점검입니다. 아래는 개발측 몫 —",
        "개발측이 규격을 검사한 것입니다. 고치지 않았습니다 (규칙 2).**", "",
        "---", "",
        "## 1. 개발측 → 가이드 · 규격 점검 (S28)", "",
    ]
    got = spec_findings(spec)
    lines += [f"- {x}" for x in got] or ["- S28-1~7 전부 통과했습니다"]

    lines += ["", "## 2. ★ 「미확정」으로 남은 것", ""]
    left = unfinished_spec()
    lines += [f"- {x}" for x in left] or ["- 없습니다"]
    if left:
        lines += ["", f"★ {STALE_WEEKS}주 넘게 미확정이면 그것도 결함입니다 "
                      "— 위 항목의 등재일을 보십시오"]

    lines += ["", "## 3. 규격이 요구했는데 코드에 없는 검사", ""]
    lines += [f"- {x}" for x in missing_checks()] or ["- 없습니다"]

    lines += ["", "## 4. 자료가 없어 못 도는 검사", "",
              "★ 「자료 없음」이 오래가면 수집을 고쳐야 한다는 뜻입니다", ""]
    lines += [f"- {x}" for x in idle_checks()] or ["- 없습니다"]

    lines += ["", "## 5. 폐기 후보 — 코드가 안 읽는 config 키", ""]
    lines += [f"- {x}" for x in unused_config()] or ["- 없습니다"]

    lines += [
        "", "---", "",
        "## 6. 가이드 몫 — 여기에 이어 쓰십시오", "",
        "```",
        "필수   전 화면 스크린샷 → 부록 G 항목 대조",
        "필수   부록 F 로 배점 대조 — 축 수 · 배점 합 · 구간 경계",
        "필수   v1 대조 (V11-68 · V11-69)",
        "필수   지난 주 지적 중 안 고쳐진 것",
        "```", "",
        "## 7. 함께 — 다음 주 우선순위 셋", "",
        "1. ", "2. ", "3. ", "",
    ]
    path = os.path.join(OUT, f"{day}_주간점검.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"주간 점검 (개발측 몫) → {path}")
    print(f"  S28 지적 {len(got)}건 · 미확정 {len(left)}건")
    return 0


if __name__ == "__main__":
    sys.exit(main())
