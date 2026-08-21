#!/usr/bin/env python3.11
"""배포 확인 — ★ 「소스가 맞다」와 「마스터 화면이 맞다」는 다른 말이다.

08-22 실측.  소스는 08-21 에 고쳤는데 carwatch.service 는 08-20 08:46 에
뜬 그대로였다.  ★ V11-157(상단 메뉴 넷 이하)은 통과였다 — 검사가
menu_items() 를 직접 불렀고 소스는 옳았기 때문이다.
그런데 마스터 화면에는 메뉴가 27개였다.  ★ 돌고 있는 것이 옛 코드였다.

★ 검사 250개 중 어느 것도 「돌고 있는 서버」를 보지 않는다.  이것이 그 구멍이다.
★ 규격 코드는 가이드가 준다.  여기서 지어내지 않는다 (규칙 2) —
  지금은 도구로만 두고, 코드를 받으면 check_all 에 붙인다.

    python3.11 tools/deploy_check.py
"""
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNIT = "carwatch"
# ★ 배포에 영향을 주는 것만 본다.  outputs/ · docs/ 는 서버가 안 읽는다
WATCH = ("web", "report", "store", "score", "collect", "parse",
         "validate", "contracts.py", "run.py", "config")


def _newest() -> tuple[float, str]:
    """소스에서 가장 최근에 손댄 파일 (mtime, 경로)."""
    best = (0.0, "")
    for one in WATCH:
        path = os.path.join(ROOT, one)
        if os.path.isfile(path):
            got = os.path.getmtime(path)
            best = max(best, (got, path))
            continue
        for dirpath, dirnames, names in os.walk(path):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for name in names:
                if name.endswith((".pyc", ".bak")):
                    continue
                full = os.path.join(dirpath, name)
                best = max(best, (os.path.getmtime(full), full))
    return best


def _started() -> float:
    """서비스가 뜬 시각.  ★ 못 읽으면 0 이다 — 통과로 넘기지 않는다."""
    out = subprocess.run(
        ["systemctl", "show", UNIT, "-p", "ActiveEnterTimestampMonotonic"],
        capture_output=True, text=True, check=False).stdout.strip()
    usec = out.split("=", 1)[-1]
    if not usec.isdigit() or usec == "0":
        return 0.0
    # monotonic(usec) → 벽시계.  ★ 부팅 이후 초를 뺀다
    with open("/proc/uptime", encoding="utf-8") as f:
        up = float(f.read().split()[0])
    return time.time() - up + int(usec) / 1_000_000


def main() -> int:
    mtime, path = _newest()
    started = _started()
    rel = os.path.relpath(path, ROOT)
    if not started:
        print(f"✗ {UNIT} 이 안 돈다 — 마스터 화면이 없다")
        return 1
    stale = mtime - started
    if stale > 0:
        print(f"✗ 배포 안 됨 — {rel} 을 서비스가 뜬 뒤에 고쳤다 "
              f"({stale / 60:.0f}분 늦음)")
        print(f"  sudo systemctl restart {UNIT}")
        print("  ★ 그 전에 마스터가 쓰고 있는지 본다 — "
              f'sudo journalctl -u {UNIT} --since "-10min" | grep POST')
        return 1
    print(f"○ 배포됨 — 가장 최근 소스 {rel} 보다 "
          f"{-stale / 60:.0f}분 뒤에 서비스가 떴다")
    return 0


if __name__ == "__main__":
    sys.exit(main())
