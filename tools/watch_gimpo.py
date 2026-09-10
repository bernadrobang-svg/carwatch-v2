# -*- coding: utf-8 -*-
"""★ P-7 — 김포 `42497136` 을 ★ **한 시간마다** 지켜본다 (지시 r1216).

★★★ 앞 손님 결정이 **9/15**, 마스터 환불 기한이 **9/16** — ★ **하루 차이**다.
  ★ 매물이 내려가는 순간을 놓치면 ★ 마스터가 정하실 시간이 없다.

★★ **404 와 407 을 가른다** (v399 에서 갈라 둔 그대로) —
  ★ 200        살아 있다.  ★ 값·상태가 그대로면 조용하다
  ★ **404**     팔렸다 (또는 내려갔다) — ★ **그 즉시 알린다**
  ★ 407        「지금 막혔다」다.  ★ **팔린 것이 아니다** — ★ 다음 시간에 다시
  ★ 값이 바뀜   ★ 그 자리에서 알린다

★ 다른 걸음과 같이 돌리지 않는다 — ★ 조리개에 걸린다.  ★ **따로, 한 시간에 한 번**.
★ 본 것은 ★ `outputs/gimpo_watch.json` 에 쌓는다 — ★ 그것이 자취다.

돌리는 법
    python3.11 tools/watch_gimpo.py           ★ 한 번 두드린다
    python3.11 tools/watch_gimpo.py --loop    ★ 한 시간마다 (systemd timer 가 낫다)
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

WATCH = os.path.join(ROOT, "outputs", "gimpo_watch.json")
EVERY = 3600.0


def _cfg() -> tuple:
    with open(os.path.join(ROOT, "config", "week_task.json"),
              encoding="utf-8") as fh:
        w = json.load(fh)
    said = w.get("지켜볼_매물") or {}
    return (str(said.get("source_id") or "42497136"),
            str(said.get("site") or "encar"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def book() -> list:
    try:
        with open(WATCH, encoding="utf-8") as fh:
            return json.load(fh) or []
    except (OSError, ValueError):
        return []


def _put(row: dict) -> None:
    got = book()
    got.append(row)
    tmp = WATCH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(got[-500:], fh, ensure_ascii=False, indent=1)
    os.replace(tmp, WATCH)


def knock() -> dict:
    """한 번 두드린다 → ★ 무슨 일이 있었나."""
    sid, site = _cfg()
    with open(os.path.join(ROOT, "config", "endpoints.json"),
              encoding="utf-8") as fh:
        e = json.load(fh)[site]
    url = e["base_url"] + e["paths"]["detail"].format(source_id=sid)
    row = {"때": _now(), "매물": sid}
    try:
        req = urllib.request.Request(url, headers=e["headers"])
        with urllib.request.urlopen(req, timeout=25) as r:
            body = json.loads(r.read())
        ad = body.get("advertisement") or {}
        row.update({"코드": 200, "값": ad.get("price"),
                    "상태": (body.get("manage") or {}).get("status")
                    or ad.get("status"),
                    "말": "살아 있다"})
    except urllib.error.HTTPError as ex:
        row["코드"] = ex.code
        # ★★ 404 만 ★ 「팔렸다」다.  ★ 407 은 ★ 「지금 막혔다」다
        row["말"] = ("★ 팔렸다 (또는 내려갔다)" if ex.code == 404
                     else "지금 막혔다 — 팔린 것이 아니다")
    except OSError as ex:
        row.update({"코드": None, "말": f"못 두드렸다 ({type(ex).__name__})"})
    _put(row)
    return row


def changed(row: dict) -> str | None:
    """앞과 달라진 것.  ★ 없으면 ★ None — ★ 조용히 있는다."""
    past = [x for x in book()[:-1] if x.get("코드") == 200]
    if row.get("코드") == 404:
        return "★ 김포가 내려갔다 — 404"
    if row.get("코드") != 200 or not past:
        return None
    was = past[-1]
    if was.get("값") != row.get("값"):
        return f"★ 김포 값이 바뀌었다 — {was.get('값')} → {row.get('값')}"
    if was.get("상태") != row.get("상태"):
        return f"★ 김포 상태가 바뀌었다 — {was.get('상태')} → {row.get('상태')}"
    return None


def main() -> int:
    while True:
        row = knock()
        said = changed(row)
        print(f"{row['때'][:19]}  {row.get('코드')}  {row['말']}"
              f"  값 {row.get('값')}  상태 {row.get('상태')}", flush=True)
        if said:
            print(f"  {said}", flush=True)
        if "--loop" not in sys.argv:
            return 0
        time.sleep(EVERY)


if __name__ == "__main__":
    raise SystemExit(main())
