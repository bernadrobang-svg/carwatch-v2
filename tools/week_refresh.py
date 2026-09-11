# -*- coding: utf-8 -*-
"""★ 받은 것을 ★ **표와 답까지** 밀어 올린다 (이번 주 과제).

★★ 받기만 하면 ★ 원문이 쌓일 뿐 ★ 답이 안 바뀐다 —
  ★ 실측 09-11 — ★ 성능점검 원문이 10,662장인데 ★ 표에는 2,109장만 있었다.
★ 한 줄로 ★ 상세 → 곁표 → 사고 갈래 → 답까지 민다.
★ 시간 맞춰 돌리면 ★ 사람이 없어도 답이 새것이 된다 (N 자동화와 같은 뜻)

돌리는 법
    python3.11 tools/week_refresh.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

SITES = ("encar", "kbchachacha")


def run() -> int:
    from tools.fill_accident_parts import run as fill_accident
    from tools.load_sides import run as load_sides
    from tools.reparse_stored import run as reparse
    from tools.week_task import main as say

    print("① 상세 → core_listing", flush=True)
    for k, v in sorted(reparse(list(SITES), write=True).items()):
        print(f"   {k:26} {v:,}")
    print("② 성능점검·보험 → 제 표", flush=True)
    for k, v in sorted(load_sides(list(SITES)).items()):
        print(f"   {k:26} {v:,}")
    print("③ 교환·판금·골격 갈래", flush=True)
    for k, v in sorted(fill_accident(write=True).items()):
        print(f"   {k:26} {v:,}")
    print("④ 답", flush=True)
    return say()


if __name__ == "__main__":
    raise SystemExit(run())
