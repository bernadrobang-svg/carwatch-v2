# -*- coding: utf-8 -*-
"""추적표 「상태」를 사실로 (개정 349 · 350 · S34).

지시서   `docs/trace/*.md` · `inbox/ORDER_trace_verify.md`
근거     마스터 지시 — 「개발 여부를 네가 1차로 채우고 그걸 확인하게 하자」
        ★ 가이드가 1차로 채웠다.  짐작이 섞여 있다
        ★ 「○ 라 한 것 중 아닌 것을 찾으면 그것이 가장 값진 결과다」
하는 것   ① 검사 칸이 가리키는 검사를 실제로 돌려 본다
        ② ○ 인데 그 검사가 실패하면 「의심」으로 낸다
        ③ 빈 칸을 센다 — 소스 · 화면 · 검사 · 테스트
금지     추적표를 개발측이 고치는 것.  ★ 사실을 내고 가이드가 고친다 (S35)
사용     python3.11 tools/trace_verify.py
"""
from __future__ import annotations

import glob
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

TRACE = os.path.join(ROOT, "docs", "trace")
# 한 줄에 몇 칸이면 온전한 추적 행인가 (| 로 잘랐을 때)
FULL_COLS = 12
# 칸 차례 — 0 은 빈 앞머리다.  ★ 표 머리말 그대로 세운다
COL_ORDER = ("R", "요구", "출처", "규격", "소스", "화면", "검사",
             "테스트", "결함", "상태")
COL = {name: i + 1 for i, name in enumerate(COL_ORDER)}
CHECK_PAT = re.compile(r"\b([VS]\d+(?:-\d+[a-z]?)?)\b")


def rows() -> list:
    """추적표의 모든 행.  ★ 표 모양이 셋이다 — 온전한 것만 칸을 읽는다."""
    out = []
    for path in sorted(glob.glob(os.path.join(TRACE, "*.md"))):
        if path.endswith("INDEX.md"):
            continue
        chapter = os.path.basename(path)
        for line in open(path, encoding="utf-8"):
            if not line.startswith("| R-"):
                continue
            cols = line.rstrip("\n").split("|")
            got = {"chapter": chapter, "wide": len(cols) == FULL_COLS,
                   "R": cols[COL["R"]].strip()}
            for key, i in COL.items():
                got[key] = cols[i].strip() if i < len(cols) - 1 else ""
            got["상태"] = cols[-2].strip().strip("*") if len(cols) > 3 else ""
            out.append(got)
    return out


def check_results() -> dict:
    """검사마다 통과인가 실패인가 · 아예 없는가.

    ★ 「있는 검사」는 색인(CHECKS.md)에서 읽는다.  check_all 출력에는
      실패한 것만 나오므로, 그것만 보면 통과한 검사가 「코드에 없다」가 된다
      (실측 08-18 — 173건이 그렇게 잘못 나왔다)
    ★ 「지금 실패하는가」만 돌려서 본다
    """
    out: dict = {}
    index = os.path.join(ROOT, "docs", "CHECKS.md")
    if os.path.isfile(index):
        for line in open(index, encoding="utf-8"):
            got = re.match(r"^\| `([VS][\w-]+)` \|(.*)$", line)
            if got:
                # ★ 코드에 없는 검사는 색인이 「★ 코드에 없다」로 적는다
                out[got.group(1)] = "코드에 없다" not in got.group(2)
    known = dict(out)
    got = subprocess.run([sys.executable,
                          os.path.join(ROOT, "tools", "check_all.py")],
                         cwd=ROOT, capture_output=True, text=True,
                         check=False).stdout
    block = got.split("■ FATAL", 1)
    if len(block) > 1:
        for part in block[1].split("\n■")[0:2]:
            for code in re.findall(r"^\s{2}(\S+)\s", part, re.M):
                if known.get(code):
                    out[code] = False
    src = subprocess.run([sys.executable,
                          os.path.join(ROOT, "tools", "check_src.py")],
                         cwd=ROOT, capture_output=True, text=True,
                         check=False).stdout
    for code, mark in re.findall(r"^(S[\w-]+) .*?(통과|부분|실패)", src, re.M):
        if mark == "실패":
            out[code] = False
        else:
            out.setdefault(code, True)
    return out


def main() -> int:
    got = rows()
    wide = [r for r in got if r["wide"]]
    blank = {k: sum(1 for r in wide if not r[k])
             for k in ("소스", "화면", "검사", "테스트")}
    results = check_results()

    suspect, missing = [], []
    for one in wide:
        codes = CHECK_PAT.findall(one["검사"])
        if not codes:
            continue
        # ★ 색인에 없거나, 색인이 「코드에 없다」로 적은 것
        unknown = [c for c in codes if results.get(c) is None]
        gone = [c for c in codes if results.get(c) is False
                and c not in results or False]
        del gone
        failing = [c for c in codes if results.get(c) is False]
        if unknown:
            missing.append(f"{one['R']} {one['요구'][:34]} — "
                           f"검사 {'·'.join(unknown)} 가 코드에 없다")
        if one["상태"] == "○" and failing:
            suspect.append(f"{one['R']} {one['요구'][:34]} — ○ 인데 "
                           f"{'·'.join(failing)} 가 실패한다")
        if one["상태"] == "✗" and codes and not failing and not unknown:
            suspect.append(f"{one['R']} {one['요구'][:34]} — ✗ 인데 "
                           f"{'·'.join(codes)} 가 통과한다")

    print(f"추적표 {len(got)}행 (온전한 표 {len(wide)}행)\n")
    print("빈 칸")
    for key, n in blank.items():
        print(f"  {key:<6} {n:>4} / {len(wide)}")
    print(f"\n★ 검사가 가리키는 것 중 코드에 없는 것 {len(missing)}건")
    for one in missing[:12]:
        print(f"  · {one}")
    print(f"\n★★ 상태가 의심스러운 것 {len(suspect)}건")
    for one in suspect[:20]:
        print(f"  · {one}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
