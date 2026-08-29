"""0a 계측 — 한 단계가 쓰기 트랜잭션을 몇 초 쥐는가 (사본에서 잰다)."""
import os, sys, threading, time, sqlite3
sys.path.insert(0, ".")
DB = os.environ["MDB"]

import run as R
R.DB_PATH = DB
from collect.pipeline import run_recalc
import collect.pipeline as P

conn = sqlite3.connect(DB)
conn.execute("PRAGMA busy_timeout = 30000")

held = {}          # step -> 쥔 시간 합계
mx = {}            # step -> ★ 한 번에 가장 오래 쥔 초
cuts = {}          # step -> 끊긴 횟수
cur = {"step": None}
stop = threading.Event()

def watch():
    """10ms 마다 in_transaction 을 본다 — 쥔 구간의 길이를 더한다."""
    was, t0 = False, 0.0
    while not stop.is_set():
        now = conn.in_transaction
        if now and not was:
            t0 = time.monotonic()
        elif was and not now:
            s = cur["step"]
            if s:
                d = time.monotonic() - t0
                held[s] = held.get(s, 0.0) + d
                mx[s] = max(mx.get(s, 0.0), d)
                cuts[s] = cuts.get(s, 0) + 1
        was = now
        time.sleep(0.01)

orig = P.run_step
wall = {}
def traced(c, ctx, step, done, ex, prog):
    cur["step"] = step
    t = time.monotonic()
    try:
        return orig(c, ctx, step, done, ex, prog)
    finally:
        wall[step] = time.monotonic() - t
        print(f"  {step:5s} 벽시계 {wall[step]:7.1f}s · 합계 "
              f"{held.get(step,0.0):7.1f}s · ★한번에 최대 {mx.get(step,0.0):6.1f}s"
              f" · 끊김 {cuts.get(step,0)}회", flush=True)
P.run_step = traced

th = threading.Thread(target=watch, daemon=True); th.start()
ctx = R.make_worker_ctx()
ex = R.make_worker_executors("raw_missing")
t0 = time.monotonic()
run_recalc(conn, ctx, ex, "raw_missing", "cli")
total = time.monotonic() - t0
stop.set(); th.join(1)
print(f"\n합계 벽시계 {total:.1f}s")
print("단계 | 벽시계 | 쥔 합계 | ★한번에 최대 | 끊김")
for s in sorted(mx, key=lambda x: -mx[x]):
    print(f"  {s:5s} {wall.get(s,0):7.1f}s {held.get(s,0):7.1f}s "
          f"{mx[s]:7.1f}s {cuts.get(s,0):6d}회")
top = max(mx.values()) if mx else 0
print(f"\n★ 한 번에 가장 오래 쥔 시간 = {top:.1f}s  "
      f"({'30초를 넘는다 — 0a 가 까닭이다' if top > 30 else '30초 아래다 — 0a 는 까닭이 아니다'})")
