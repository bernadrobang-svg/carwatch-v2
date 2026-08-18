# -*- coding: utf-8 -*-
"""가벼운 점검 — 4시간마다 (개정 335 · S29-0).

지시서   0장 S29 · `inbox/ORDER_light_check_4h.md` · `check_light_every_h`
근거     마스터 지시 — 「4시간 간격으로 하자」
        ★ 1시간이면 하루 24번이라 기록이 쌓여 안 보게 된다.
          하루 한 번이면 밤에 깨진 것을 저녁에야 안다
필수     ★ 어긋난 것이 있을 때만 기록한다 — 늘 남기면 하루 6개가 쌓인다
필수     무엇이 늘고 줄었는지 낸다.  「fatal 4 → 6」이 신호다
필수     수집이 도는 중이면 건너뛴다 — 원문이 들어오는 중에 세면 흔들린다
금지     ★ 고치는 것.  재는 것만 한다 — 고치면 마스터의 작업을 끊는다
금지     서비스를 재시작하는 것 (개정 308)
사용     systemd timer 가 부른다.  손으로는 python3.11 tools/light_check.py
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

DB = os.path.join(ROOT, "carwatch.db")
OUT = os.path.join(ROOT, "outputs", "light")
# ★ 「지난 번」 숫자.  이것과 견줘야 「늘었다」를 말할 수 있다
STATE = os.path.join(OUT, "last.json")
# 단위 환산 — UTC 를 한국 날짜로 (2장 상수표 · V4-13)
KST_OFFSET_HOURS = 9
# 이만큼 안에 원문이 들어왔으면 수집이 도는 중이다
COLLECTING_WINDOW_SEC = 300


def _cfg() -> dict:
    with open(os.path.join(ROOT, "config", "web.json"), encoding="utf-8") as f:
        return json.load(f)


def _run(*cmd) -> str:
    got = subprocess.run([sys.executable, *cmd], cwd=ROOT, check=False,
                         capture_output=True, text=True)
    return got.stdout + got.stderr


def collecting(conn) -> str:
    """수집·재계산이 도는 중인가.  ★ 도는 중이면 숫자가 흔들린다."""
    row = conn.execute(
        "SELECT MAX(fetched_at) FROM raw_response").fetchone()
    if row and row[0]:
        try:
            at = datetime.fromisoformat(str(row[0]).replace("Z", "+00:00"))
        except ValueError:
            at = None
        if at is not None:
            gap = (datetime.now(timezone.utc) - at).total_seconds()
            if gap < COLLECTING_WINDOW_SEC:
                return f"수집이 도는 중이다 — 마지막 원문 {int(gap)}초 전"
    got = conn.execute(
        "SELECT COUNT(*) FROM recalc_job WHERE status IN ('queued','running')"
    ).fetchone()
    if got and got[0]:
        return f"재계산이 도는 중이다 — {got[0]}건"
    return ""


def screen_counts() -> dict:
    """화면에서 세는 것 — 「—」 · 계산식 · 템플릿 문법.

    ★ 렌더 결과를 본다.  템플릿만 보면 필터가 만드는 줄표를 못 본다
    """
    base = os.path.join(ROOT, "outputs", "render")
    dash, calc, leak, pages = 0, 0, 0, 0
    cell = re.compile(r"<(td|dd)\b[^>]*>(.*?)</\1>", re.S)
    if not os.path.isdir(base):
        return {"화면": 0, "—": 0, "계산식": 0, "템플릿 문법": 0}
    for name in sorted(os.listdir(base)):
        if not name.endswith(".html"):
            continue
        pages += 1
        html = open(os.path.join(base, name), encoding="utf-8").read()
        for got in cell.finditer(html):
            if re.sub(r"<[^>]+>", "", got.group(2)).strip() in ("—",
                                                                "–"):
                dash += 1
        body = re.sub(r"<(script|style)\b.*?</\1>", "", html, flags=re.S)
        text = re.sub(r"<[^>]+>", " ", body)
        calc += len(re.findall(r"\d[\d,]*\s*/\s*\d[\d,]*", text))
        leak += len(re.findall(r"\{[%{#]", html))
    return {"화면": pages, "—": dash, "계산식": calc, "템플릿 문법": leak}


def db_counts(conn) -> dict:
    def one(sql):
        try:
            return conn.execute(sql).fetchone()[0]
        except sqlite3.Error:
            return None

    return {
        "raw_response": one("SELECT COUNT(*) FROM raw_response"),
        "core_listing": one("SELECT COUNT(*) FROM core_listing"),
        "result_score": one("SELECT COUNT(*) FROM result_score"),
    }


def measure() -> dict:
    """재기만 한다.  ★ 고치지 않는다."""
    # ★ 색인 넷을 먼저 갱신한다 (개정 343).  파일이 늘거나 줄면
    #   색인이 함께 바뀌어야 한다 — 손으로 적으면 빠진다
    _run(os.path.join(ROOT, "tools", "build_index.py"))
    checks = _run(os.path.join(ROOT, "tools", "check_all.py"))
    tests = _run(os.path.join(ROOT, "tools", "run_tests.py"))
    _run(os.path.join(ROOT, "tools", "render_screens.py"))
    got = re.search(r"통과 (\d+) · fatal (\d+) · warn (\d+)", checks)
    fails = re.search(r"결과: 실패 — (.+)", tests)
    out = {
        "통과": int(got.group(1)) if got else None,
        "fatal": int(got.group(2)) if got else None,
        "warn": int(got.group(3)) if got else None,
        "시험 실패": len([x for x in fails.group(1).split(",")]) if fails else 0,
    }
    out.update(screen_counts())
    out.update(index_counts())
    return out


def index_counts() -> dict:
    """색인 넷의 숫자 (개정 343 · 344).  ★ 검사가 몇 개인지 늘 보인다."""
    got = _run(os.path.join(ROOT, "tools", "check_spec.py"))
    out = {}
    for code, key in (("S28-9", "800줄 넘는 문서"),
                      ("S28-8", "부록에 있는 기준")):
        # ★ 「S28-9 본문 파일이 800줄 이하 3 [...]」 — 제목의 800 이 아니라
        #   그 뒤의 건수다.  앞의 숫자를 주우면 늘 800 이 된다 (실측 08-18)
        hit = re.search(rf"^{code} .*?(\d+) \[", got, re.M)
        if hit:
            out[key] = int(hit.group(1))
    body = ""
    path = os.path.join(ROOT, "docs", "CHECKS.md")
    if os.path.isfile(path):
        body = open(path, encoding="utf-8").read()
    for key, pat in (("검사", r"검사 \*\*(\d+)개\*\*"),
                     ("죽은 검사", r"죽은 검사[^|]*\| \*\*(\d+)\*\*"),
                     ("검사 없는 규격", r"코드에 없는 검사 \| \*\*(\d+)\*\*")):
        hit = re.search(pat, body)
        if hit:
            out[key] = int(hit.group(1))
    return out


def changed(now: dict, was: dict) -> list:
    """무엇이 늘고 줄었는가.  ★ 이것이 신호다 — 숫자 자체보다 변화다."""
    out = []
    for key, value in now.items():
        before = was.get(key)
        if before is None or value is None or before == value:
            continue
        mark = "  ★ 늘었다" if _worse(key, before, value) else ""
        out.append(f"{key} {before} → {value}{mark}")
    return out


# 늘어나면 나쁜 것 · 줄어들면 나쁜 것
WORSE_WHEN_UP = ("fatal", "warn", "시험 실패", "—", "계산식", "템플릿 문법",
                 "죽은 검사", "검사 없는 규격", "800줄 넘는 문서",
                 "부록에 있는 기준")


def _worse(key: str, before, now) -> bool:
    return now > before if key in WORSE_WHEN_UP else now < before


def main() -> int:
    at = datetime.now(timezone.utc)
    started = time.monotonic()
    os.makedirs(OUT, exist_ok=True)
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        busy = collecting(conn)
        if busy:
            print(f"건너뛴다 — {busy}")
            return 0
        now = {**measure(), **db_counts(conn)}
    finally:
        conn.close()
    took = time.monotonic() - started

    was = {}
    if os.path.isfile(STATE):
        try:
            with open(STATE, encoding="utf-8") as f:
                was = json.load(f).get("숫자", {})
        except (ValueError, OSError):
            was = None or {}
    diff = changed(now, was)

    budget = float(_cfg().get("check_light_budget_sec") or 0)
    over = budget and took > budget
    stamp = {"at": at.isoformat()[:19] + "Z", "숫자": now, "바뀐 것": diff,
             "걸린 초": round(took, 1), "예산 초": budget}
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(stamp, f, ensure_ascii=False, indent=1)

    day = (at + timedelta(hours=KST_OFFSET_HOURS)).strftime("%Y-%m-%d_%H%M")
    # ★ 어긋난 것이 있을 때만 기록한다.  늘 남기면 하루 6개가 쌓인다
    if diff or now.get("fatal") or now.get("시험 실패"):
        lines = [f"# 가벼운 점검 — {day}", "",
                 f"자동 실행 (개정 335 · S29-0) · {at.isoformat()[:19]}Z · "
                 f"{took:.0f}초", "",
                 "## 바뀐 것 — ★ 이것이 신호다", ""]
        lines += [f"- {x}" for x in diff] or ["- 지난 번과 같다"]
        lines += ["", "## 지금 숫자", "", "```json",
                  json.dumps(now, ensure_ascii=False, indent=1), "```", ""]
        if over:
            lines += [f"★ 예산 {budget:.0f}초를 넘겼다 ({took:.0f}초). "
                      "check_all 과 run_tests 가 각각 70초대다", ""]
        path = os.path.join(OUT, f"{day}.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"가벼운 점검 → {path}")
    else:
        print("가벼운 점검 — 어긋난 것이 없다.  기록을 남기지 않는다")

    print(f"  fatal {now.get('fatal')} · 시험 실패 {now.get('시험 실패')} · "
          f"「—」 {now.get('—')} · {took:.0f}초"
          + (f"  ★ 예산 {budget:.0f}초 초과" if over else ""))
    for one in diff:
        print(f"  · {one}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
