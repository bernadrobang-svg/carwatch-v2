"""KB 봇 차단을 ★ 묶음 크기별로 잰다 (1순위 5 · 마스터 「다시 재고 나서」)."""
import subprocess, sys, time

for n in (10, 20, 30):
    print(f"★ 5분 쉰다 (BURST_REST_SEC) — 다음은 {n}건", flush=True)
    time.sleep(300)
    p = subprocess.run([sys.executable, "tools/collect_kbchachacha.py",
                        "--probe", str(n)], capture_output=True, text=True)
    line = [x for x in (p.stdout or "").splitlines() if "봇 차단 실측" in x]
    print(f"  묶음 {n:2d}건 → {line[-1] if line else (p.stdout or p.stderr)[-200:]}",
          flush=True)
