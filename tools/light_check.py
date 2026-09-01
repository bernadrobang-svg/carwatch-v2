# -*- coding: utf-8 -*-
"""가벼운 점검 — 4시간마다 (개정 335 · S29-0).

지시서   0장 S29 · `inbox/ORDER_light_check_4h.md` · `check_light_every_h`
근거     마스터 지시 — 「4시간 간격으로 하자」
        ★ 1시간이면 하루 24번이라 기록이 쌓여 안 보게 된다.
          하루 한 번이면 밤에 깨진 것을 저녁에야 안다
필수     ★ 어긋난 것이 있을 때만 기록한다 — 늘 남기면 하루 6개가 쌓인다
필수     무엇이 늘고 줄었는지 낸다.  「fatal 4 → 6」이 신호다
필수     수집이 도는 중이면 건너뛴다 — 원문이 들어오는 중에 세면 흔들린다
필수     ★ 08-18 정정 (개정 339) — fatal 을 찾으면 그 자리에서 고친다.
        「재기만 한다」는 폐기됐다.  마스터 지적 —
        「4시간마다 돌라고 했으면 잔여 작업이 없어야 하는데」
        고친다   되돌릴 수 있고 규격이 정해진 것 (아래 REPAIRS)
        묻는다   규격이 없는 것 · DB 를 지우는 것 · 배점을 바꾸는 것
                ★ 기록에 적고 다음 점검까지 기다린다
필수     한 번에 REPAIR_MAX 건까지.  ★ 한꺼번에 고치면 무엇이 깨졌는지 모른다
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


def _repair_max() -> int:
    """한 번에 몇 건까지 고칠 것인가 (개정 339 · S29-4)."""
    return int(_cfg().get("check_repair_max") or 0)


# ★ 점검이 스스로 고쳐도 되는 것 (개정 339).
#   되돌릴 수 있고 규격이 정해져 있는 것만이다.
#   (검사 코드 무늬, 무엇을 돌리나, 왜 고쳐도 되나)
REPAIRS: tuple = (
    ("S28-1[0-3]|색인", ("tools", "build_index.py"),
     "색인 넷을 다시 만든다 — 기계가 만드는 파일이라 되돌릴 것이 없다"),
    ("V11-10[469]|V11-11[345]|렌더|스크린샷", ("tools", "render_screens.py"),
     "화면을 다시 그린다 — outputs/ 산출물이라 원문을 안 건드린다"),
    ("V1-25|조각", ("tools", "repair_facet_chunks.py"),
     "facet 조각을 이어 붙인다 — 원문을 지우지 않는다 (P3)"),
)


def _cfg() -> dict:
    with open(os.path.join(ROOT, "config", "web.json"), encoding="utf-8") as f:
        return json.load(f)


# ★★★★★ 09-03 실측 — ★ 한 판이 ★ **33분**을 넘겨 물려 있었다.
#   ★ 예산은 ★ 180초라 적혀 있는데 ★ **시간 상한이 없었다** —
#   ★ ★ `check_all` 이 막히면 ★ 타이머 판이 ★ **영영 안 끝난다**.
#   ★ ★ ★ 그동안 ★ DB 를 물고 있어 ★ 마스터 화면까지 느려진다 (실측 09-03).
#   ★★ 상한을 건다 — ★ 넘으면 ★ **그 걸음만 접고** ★ 남은 걸음을 잇는다.
#     ★ ★ 조용히 넘기지 않는다 — ★ 「몇 초에 끊었다」를 ★ 글로 남긴다
_STEP_LIMIT_SEC = 900


def _run(*cmd) -> str:
    try:
        got = subprocess.run([sys.executable, *cmd], cwd=ROOT, check=False,
                             capture_output=True, text=True,
                             timeout=_STEP_LIMIT_SEC)
    except subprocess.TimeoutExpired:
        name = os.path.basename(str(cmd[0]))
        return (f"★ {name} 이 {_STEP_LIMIT_SEC}초를 넘겨 끊었다 — "
                "★ 이 걸음의 숫자는 이번 판에 없다")
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


# 이번 차례에 돌린 check_all 출력 — ★ 두 번 돌리지 않는다 (예산 180초)
_LAST_CHECKS = [""]


def measure() -> dict:
    """잰다.  ★ 고치는 것은 repair() 가 한다 (개정 339)."""
    # ★ 색인 넷을 먼저 갱신한다 (개정 343).  파일이 늘거나 줄면
    #   색인이 함께 바뀌어야 한다 — 손으로 적으면 빠진다
    _run(os.path.join(ROOT, "tools", "build_index.py"))
    checks = _run(os.path.join(ROOT, "tools", "check_all.py"))
    _LAST_CHECKS[0] = checks
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


def failing(text: str) -> list:
    """check_all 출력에서 ★ fatal 만.

    ★ warn 까지 주우면 「물어야 하는 것」이 열여섯 개가 되어
      진짜 fatal 이 묻힌다 (실측 08-18)
    """
    block = text.split("■ FATAL", 1)
    if len(block) < 2:
        return []
    return re.findall(r"^\s{2}(\S+)\s+.*—", block[1].split("\n■", 1)[0],
                      re.M)


def repair(now: dict) -> tuple:
    """고쳐도 되는 것을 고친다 (개정 339 · S29-4).

    반환   (고친 것, 물어야 하는 것)
    ★ 고쳐도 되는 것만 고친다.  나머지는 적어 두고 기다린다
    ★ 서비스를 재시작하지 않는다 (개정 308)
    """
    # ★ 방금 잰 출력을 쓴다.  다시 돌리면 예산을 두 배로 쓴다
    spec = _run(os.path.join(ROOT, "tools", "check_spec.py"))
    hits = failing(_LAST_CHECKS[0]) + re.findall(
        r"^(S28-\d+) .*?[1-9]\d* \[", spec, re.M)
    if not hits:
        return [], []
    fixed, asked, done = [], [], set()
    for code in hits:
        for pattern, cmd, why in REPAIRS:
            if not re.search(pattern, code) or cmd in done:
                continue
            if len(fixed) >= _repair_max():
                asked.append(f"{code} — 이번 차례 상한({_repair_max()}건)을 "
                             "넘었다.  다음 점검에서 고친다")
                break
            _run(os.path.join(ROOT, *cmd))
            done.add(cmd)
            fixed.append(f"{code} → {cmd[-1]} 를 돌렸다.  {why}")
            break
        else:
            asked.append(f"{code} — 규격이 정한 고치는 법이 없다.  "
                         "사람이 봐야 한다")
    del now
    return fixed, asked


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
        fixed, asked = repair(now)
        if fixed:
            # ★ 고쳤으면 다시 잰다.  고치기 전 숫자를 내면 거짓말이 된다
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
             "고친 것": fixed, "물어야 하는 것": asked[:12],
             "걸린 초": round(took, 1), "예산 초": budget}
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(stamp, f, ensure_ascii=False, indent=1)

    day = (at + timedelta(hours=KST_OFFSET_HOURS)).strftime("%Y-%m-%d_%H%M")
    # ★ 어긋난 것이 있을 때만 기록한다.  늘 남기면 하루 6개가 쌓인다
    if diff or fixed or asked or now.get("fatal") or now.get("시험 실패"):
        lines = [f"# 가벼운 점검 — {day}", "",
                 f"자동 실행 (개정 335 · S29-0) · {at.isoformat()[:19]}Z · "
                 f"{took:.0f}초", "",
                 "## 바뀐 것 — ★ 이것이 신호다", ""]
        lines += [f"- {x}" for x in diff] or ["- 지난 번과 같다"]
        lines += ["", "## 고친 것 — ★ 점검이 그 자리에서 (개정 339)", ""]
        lines += [f"- {x}" for x in fixed] or ["- 없다"]
        lines += ["", "## 물어야 하는 것 — ★ 규격이 정한 고치는 법이 없다", ""]
        lines += [f"- {x}" for x in asked[:12]] or ["- 없다"]
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
          f"「—」 {now.get('—')} · 고침 {len(fixed)} · 물음 {len(asked)} · "
          f"{took:.0f}초"
          + (f"  ★ 예산 {budget:.0f}초 초과" if over else ""))
    for one in fixed:
        print(f"  ✔ {one}")
    for one in diff:
        print(f"  · {one}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
