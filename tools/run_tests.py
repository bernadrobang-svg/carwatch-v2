# -*- coding: utf-8 -*-
"""시험 전체 실행.

지시서   0장 STEP 7 (불변식) · 6장 (검증 5차)
사용     python3 tools/run_tests.py
종료     0 통과 · 1 실패
"""
from __future__ import annotations

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS = os.path.join(ROOT, "tests")


# 정적 검사 규칙 (부록 E · S22).
# ★ 훅에 없으면 아무도 돌리지 않는다.  실측: F821 6건이 살아 있었다 (B-1)
RUFF_RULES = "F821,F811,B905,F841,DTZ005,F401"


def _ruff_missing(detail: str) -> bool:
    """검사기가 없다.  ★ 건너뛰지 않고 실패로 낸다 (부록 E · S22).

    근거   S22 는 F821 · F811 · B905 를 fatal 로 둔다.
           검사기가 없으면 그 fatal 은 「통과」가 아니라 「판정 안 됨」이다.
           느슨한 검사는 검사 없는 것보다 나쁘다 (부록 A · STEP 5.2b)
    실사고 08-16 — python3.11 에 ruff 가 없어 6종이 전부 무검사인 채
           「통과」로 집계됐다.  zip(strict=) 강제(B905)가 죽어 있었다
    """
    print(f"  {'ruff':18} 실패  ({RUFF_RULES})")
    print(f"      검사기가 없다 — S22 를 판정하지 못했다  ({detail})")
    print("      ★ 건너뛴 것이지 통과한 것이 아니다.  B905 (zip strict) 가 죽는다")
    print(f"      설치  {sys.executable} -m pip install --user ruff")
    return False


def _ruff_ok() -> bool:
    """ruff 를 시험의 일부로 돌린다.

    ★ 없으면 실패다 — 조용히 통과시키지 않는다 (부록 E · S22)
    """
    try:
        r = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "--select", RUFF_RULES,
             "--output-format", "concise", "."],
            cwd=ROOT, capture_output=True, text=True)
    except OSError as e:
        return _ruff_missing(type(e).__name__)
    if "No module named" in (r.stderr or ""):
        return _ruff_missing("No module named ruff")
    ok = r.returncode == 0
    print(f"  {'ruff':18} {'통과' if ok else '실패'}  ({RUFF_RULES})")
    if not ok:
        for line in (r.stdout or "").splitlines()[:8]:
            print(f"      {line}")
    return ok


# 시험이 만드는 임시 자리 이름.  ★ 검사가 디스크를 채우면 안 된다 —
# 실측 08-15: DB 사본 63MB 가 실행마다 쌓여 디스크가 100% 가 됐고
# 그 뒤 전 시험이 한꺼번에 깨졌다.  「검사 때문에 검사가 못 도는」 상태다
# 이번 실행이 만든 것만 치운다.  ★ 남의 임시 파일을 지우지 않는다
SWEEP_WINDOW_SEC = 60


# 한 시간은 몇 초인가 (2장 상수표 · V4-13)
SEC_PER_HOUR = 3600


def _stale_hours() -> float:
    """죽은 실행이 남긴 것으로 볼 나이.  ★ config 가 정본이다 (V4-13)."""
    import json as _j

    with open(os.path.join(ROOT, "config", "checks.json"),
              encoding="utf-8") as f:
        return float(_j.load(f)["temp_stale_hours"])


def _sweep_temp() -> int:
    """시험이 남긴 임시 DB 를 치운다.  ★ 남의 것은 건드리지 않는다."""
    import shutil
    import tempfile
    import time

    root = tempfile.gettempdir()
    now = time.time()
    cutoff = now - SWEEP_WINDOW_SEC
    # ★★ 죽은 실행이 남긴 것도 치운다 (개정 395 실측).
    #   전에는 「이번 실행이 만든 것」만 치웠다 — 끊긴 실행이 남긴 것은
    #   영영 쌓여 2,155개가 되고 /tmp 921M 이 꽉 찼다.
    #   ★ 그러면 다음 검사가 아예 못 돈다.  「검사가 디스크를 채우지 않는다」가
    #     지켜지려면 남의 잔해도 치워야 한다
    stale = now - _stale_hours() * SEC_PER_HOUR
    n = 0
    for name in os.listdir(root):
        path = os.path.join(root, name)
        if not name.startswith("tmp") or not os.path.isdir(path):
            continue
        try:
            made = os.path.getmtime(path)
            if made < cutoff and made > stale:
                continue          # 남의 것이고 아직 쓸 수 있다
            if not any(f.endswith(".db") for f in os.listdir(path)):
                continue
            shutil.rmtree(path, ignore_errors=True)
            n += 1
        except OSError:
            pass
    return n


def main() -> int:
    names = sorted(f for f in os.listdir(TESTS)
                   if f.startswith("test_") and f.endswith(".py"))
    failed = []
    for name in names:
        r = subprocess.run([sys.executable, os.path.join(TESTS, name)],
                           cwd=ROOT, capture_output=True, text=True)
        tail = [x for x in r.stdout.splitlines() if x.startswith("결과:")]
        mark = "통과" if r.returncode == 0 else "실패"
        print(f"  {name[:-3]:18} {mark}")
        if r.returncode != 0:
            failed.append(name)
            for line in r.stdout.splitlines():
                if "FAIL" in line:
                    print(f"      {line.strip()}")
            if r.stderr.strip():
                print(f"      {r.stderr.strip().splitlines()[-1]}")
        _ = tail
    if not _ruff_ok():
        failed.append("ruff")
    swept = _sweep_temp()
    if swept:
        print(f"\n  임시 DB {swept}개 치움 (검사가 디스크를 채우지 않는다)")
    print("\n결과:", "통과" if not failed else "실패 — " + ", ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
