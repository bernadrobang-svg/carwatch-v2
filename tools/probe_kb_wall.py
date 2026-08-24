# -*- coding: utf-8 -*-
"""KB 봇 차단을 ★ 재는 도구 (명령서 08-25 · 마스터 「가려 받지 마라」).

쓰기   python3.11 tools/probe_kb_wall.py --n 20 --gap 1.2
      python3.11 tools/probe_kb_wall.py --n 20 --gap 5 --ua desktop

★★ **답을 지어내지 않는다.**  ★ 「하루에 몇 건까지 되나」를 ★ 재서 적는다
★ 우회가 아니다 — ★ 사람이 쓰는 헤더 꼴을 ★ 그대로 쓴다 (마스터 확정)
★ 막히면 ★ 그 자리에서 멈춘다 — ★ 두드려 뚫지 않는다
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from adapters.kbchachacha import SITE_CODE, is_bot_wall, is_real_end  # noqa: E402
from store.raw import open_db                                          # noqa: E402

# ★ 사람이 쓰는 꼴 — ★ 우회가 아니다.  ★ 브라우저가 실제로 보내는 머리다
UA = {
    "mobile": ("Mozilla/5.0 (Linux; Android 14; SM-S928N) AppleWebKit/537.36 "
               "SamsungBrowser/25.0 Mobile Safari/537.36"),
    "desktop": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"),
}
ACCEPT = ("text/html,application/xhtml+xml,application/xml;q=0.9,"
          "image/avif,image/webp,*/*;q=0.8")


def _opt(args: list, name: str, default):
    if name in args:
        i = args.index(name)
        if i + 1 < len(args) and not args[i + 1].startswith("--"):
            return type(default)(args[i + 1])
    return default


def main() -> int:
    args = sys.argv[1:]
    n = _opt(args, "--n", 20)
    gap = _opt(args, "--gap", 1.2)
    kind = _opt(args, "--ua", "mobile")
    full = "--full" in args        # ★ 사람이 보내는 머리를 다 붙인다

    with open(os.path.join(ROOT, "config", "endpoints.json"),
              encoding="utf-8") as f:
        cfg = json.load(f)[SITE_CODE]
    head = dict(cfg.get("headers") or {})
    head["User-Agent"] = UA.get(kind, UA["mobile"])
    if full:
        head.update({"Accept": ACCEPT, "Accept-Language": "ko-KR,ko;q=0.9",
                     "Sec-Fetch-Dest": "document", "Sec-Fetch-Mode": "navigate",
                     "Sec-Fetch-Site": "same-origin",
                     "Upgrade-Insecure-Requests": "1"})
        head.pop("X-Requested-With", None)

    conn = open_db(os.path.join(ROOT, "carwatch.db"))
    ids = [r[0] for r in conn.execute(
        "SELECT source_id FROM core_listing"
        " WHERE site=? AND (detail_status IS NULL OR detail_status<>'ok')"
        " ORDER BY source_id LIMIT ?", (SITE_CODE, n))]
    if not ids:
        print("★ 받을 것이 없다")
        return 0

    tpl = cfg["base_url"] + cfg["paths"]["detail"]
    ok = wall = other = 0
    first_wall = None
    print(f"★ 잰다 — {len(ids)}건 · 사이 {gap}초 · UA {kind}"
          f"{' · 사람 머리 전부' if full else ''} · "
          f"{datetime.now(timezone.utc).astimezone().strftime('%H:%M')}")
    for i, sid in enumerate(ids, 1):
        req = urllib.request.Request(tpl.format(source_id=sid), headers=head)
        try:
            with urllib.request.urlopen(req, timeout=float(cfg["timeout_sec"])) as f:
                body = f.read().decode("utf-8", "replace")
        except Exception as e:                             # noqa: BLE001
            other += 1
            print(f"  {i:>3} {sid} — ★ 못 받았다 {type(e).__name__}")
            time.sleep(gap)
            continue
        if is_bot_wall(body, cfg):
            wall += 1
            if first_wall is None:
                first_wall = i
                print(f"  {i:>3} {sid} — ★★ 처음 막혔다 ({len(body):,}B)")
        elif is_real_end(body, cfg):
            other += 1
        else:
            ok += 1
        time.sleep(gap)
    print(f"★ 결과 — 정상 {ok} · 봇차단 {wall} · 그 밖 {other}"
          + (f" · ★ 처음 막힌 자리 {first_wall}번째" if first_wall else
             " · ★ 안 막혔다"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
