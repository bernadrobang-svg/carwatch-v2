# -*- coding: utf-8 -*-
"""아홉+한 사이트를 하루 한 번 받는다 (ORDER_20260829 1순위 2 · S46-127).

지시서   ORDER_20260829 — 「`deploy/carwatch-daily.service` ExecStart 가
         `daily_enqueue.py` 뿐이다 — 재판정만 큐에 넣고 수집기를 안 부른다」
근거     실측 08-29 — 수집기 열 개가 저절로 안 돈다.  마스터가 손으로
         터미널에서 돌리셔야 했고, 그래서 렉서스는 08-24 값이 그대로였다
★        엔카는 여기 없다.  목록이 407 이라 마스터가 눌러야 들어온다 (개정 388)
★        한 사이트가 죽어도 나머지를 돌린다 — 하나 때문에 전부를 잃지 않는다
★        재판정은 여기서 안 부른다.  `daily_enqueue.py` 가 큐에 넣고
         웹 서버 안의 소비기가 꺼내 돈다 (STEP 132a)
사용     python3.11 tools/daily_collect.py  [사이트…]
"""
from __future__ import annotations

import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ★ 도는 차례.  ★ 가벼운 것부터 — ★ 앞이 죽어도 뒤가 돈다
SITES: tuple[str, ...] = (
    # ★★★★★ 09-01 마스터 확정 — ★ **보배를 뺐다.  ★ 리볼트를 넣었다**
    #   ★ 마스터 — 「★ 보배를 빼고 여기 것 쓰자 ★ 지금 우선 작업으로」
    #   ★ ★ 보배 매물·원문은 ★ **안 지운다** (P3) — ★ 더 받지 않을 뿐이다
    "lexus", "volvo", "revolt", "heydealer", "bmw",
    "kia_cpo", "reborncar", "hyundai_cert", "kcar", "kbchachacha",
)

# ★★★★ 08-29 — ★ 맨으로 부르면 안 되는 것.  ★ K카는 ★ `--list` 가 없으면
#   ★ 「carCd 를 주어야 한다」로 끝난다 — ★ 목록을 한 건도 안 받는다.
#   ★ 실측 08-29 — ★ 하루치 한 바퀴에서 ★ K카가 늘 0건이었던 까닭이 이것이다
ARGS: dict[str, tuple[str, ...]] = {"kcar": ("--list",)}

# ★ 한 사이트에 주는 시간.  ★ 넘으면 끊고 다음으로 간다 —
#   ★ 하나가 매달려 있으면 ★ 나머지가 하루를 통째로 못 돈다
TIMEOUT_SEC = 40 * 60
# ★ 사이트 사이에 쉰다 — ★ 잠금과 대역을 몰아 쓰지 않는다
GAP_SEC = 5


def run_one(site: str) -> tuple[str, int, str]:
    """수집기 하나를 돌린다.  ★ 죽어도 예외를 안 던진다."""
    path = os.path.join(ROOT, "tools", f"collect_{site}.py")
    if not os.path.exists(path):
        return site, -1, "★ 파일이 없다"
    t0 = time.monotonic()
    # ★★ 수집기가 ★ 저마다 재판정을 큐에 넣지 못하게 한다 (실측 08-29) —
    #   ★ 하나가 넣으면 ★ 소비기가 9분을 돌고 ★ 그 사이 수집기가 잠금에 죽는다.
    #   ★ 재판정은 ★ 다 받은 뒤 ★ `daily_enqueue.py` 가 한 번만 넣는다
    env = dict(os.environ, CARWATCH_DEFER_RECALC="1")
    try:
        p = subprocess.run([sys.executable, path, *ARGS.get(site, ())],
                           cwd=ROOT, env=env,
                           capture_output=True, text=True,
                           timeout=TIMEOUT_SEC, check=False)
    except subprocess.TimeoutExpired:
        return site, -2, f"★ {TIMEOUT_SEC // 60}분을 넘겨 끊었다"
    took = time.monotonic() - t0
    out = (p.stdout or "").strip().splitlines()
    # ★ 마지막 몇 줄이 건수다 — ★ 로그를 다 남기면 journal 이 넘친다
    tail = " · ".join(x.strip() for x in out[-3:]) if out else ""
    if p.returncode != 0:
        err = (p.stderr or "").strip().splitlines()
        tail = (tail + " | " + (err[-1] if err else "")).strip(" |")
    return site, p.returncode, f"{took:.0f}초 · {tail}"


def main() -> int:
    want = [s for s in sys.argv[1:] if not s.startswith("-")] or list(SITES)
    bad = [s for s in want if s not in SITES]
    if bad:
        print(f"★ 모르는 사이트 {bad} — 아는 것 {list(SITES)}")
        return 2
    print(f"★ 하루 한 번 수집 — {len(want)}사이트")
    ok, fail = [], []
    for i, site in enumerate(want):
        name, code, note = run_one(site)
        mark = "✓" if code == 0 else "✗"
        print(f"  {mark} {name:14s} {note}", flush=True)
        (ok if code == 0 else fail).append(name)
        if i + 1 < len(want):
            time.sleep(GAP_SEC)
    print(f"★ 끝 — 성공 {len(ok)} · 실패 {len(fail)}"
          + (f" ({' · '.join(fail)})" if fail else ""))
    # ★★ 하나만 죽었으면 ★ 0 을 낸다 — ★ 그래야 뒤의 재판정이 돈다.
    #   ★ ★ `Restart=on-failure` 라 ★ 여기서 1 을 내면 ★ 4시간 뒤 전부를 다시 돈다
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
