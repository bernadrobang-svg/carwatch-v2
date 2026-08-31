# -*- coding: utf-8 -*-
"""목록 대조 — ★ **사라진 것은 상세로 확인한 뒤에 죽인다.**

★★★ 마스터 지시 09-01 — 「★ **목록을 대조해서 기존 목록에서 사라지면
   ★ 상세를 조회해서 판매상태 여부를 체크한다**」

★★★★★ 이것이 ★ 설계의 까닭이다 (`ARCHITECTURE_20260830.md` 1장) —
  ★ 「목록에 없다 = 팔렸다」가 ★ **틀렸다.**
  ★ ★ 실측 08-29~30 — ★ 그렇게 죽인 매물 중 ★ **74대가 살아 있었다**
    (K카 12 · 다섯 곳 61 · 렉서스 1).  ★ 그래서 여섯 곳의 `sweep` 을 껐다.
  ★★ ★ 여기가 ★ **상세로 확인하고 죽이는 자리**다 — ★ 3걸음

★ 갈래 셋 (마스터 확정 08-30)
    살아 있다        → ★ 아무것도 안 한다
    detail_gone     → `detail_status='not_found'` · `sales_status='detail_gone'` · `status='gone'`
    unreachable     → ★ 못 받았다.  ★ 잇달아 사흘이면 `unreachable`

돌리는 법
    python3.11 tools/list_diff_check.py revolt
    python3.11 tools/list_diff_check.py revolt --write
"""
from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from store.rawfile import read, walk  # noqa: E402

SLEEP = 1.2


def _bot_wall(site: str, body) -> bool:
    """★★★★★ 09-01 — ★ 이 봉투가 ★ **봇 차단**인가.

    ★ 사이트 어댑터가 ★ `is_bot_wall` 을 가지고 있으면 ★ 그것에 묻는다.
      ★ ★ 없으면 ★ **거짓**이다 — ★ 「모르니 차단이다」로 넘겨짚지 않는다.
    ★★ 까닭 — ★ 실측 09-01.  ★ KB 상세가 ★ 200 · 1,382B
      ★ 「로봇여부 확인 | KB차차차」로 왔는데 ★ 파서가 `None` 을 내
      ★ ★ 그것을 ★ 「없는 차」로 읽어 ★ **23건을 죽였다** (`V2-01` 이 잡았다)
    """
    import importlib

    try:
        ad = importlib.import_module(f"adapters.{site}")
    except ModuleNotFoundError:
        return False
    fn = getattr(ad, "is_bot_wall", None)
    if fn is None:
        return False
    text = body.decode("utf-8", "replace") if isinstance(body, bytes) else body
    cfg = getattr(ad, "load_config", None)
    return bool(fn(text, cfg(ROOT) if cfg else None))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def latest_list_ids(site: str, root: str = ROOT) -> tuple:
    """★ **가장 최근 회차**의 목록 파일에서 ★ 매물번호를 다 모은다.

    ★ 여러 날 것을 섞지 않는다 — ★ 섞으면 ★ 「오늘 사라진 것」을 못 가른다
    """
    files = [p for p in walk(site=site, endpoint="list", root=root)]
    if not files:
        return set(), None
    day = os.path.basename(os.path.dirname(files[-1]))
    ids: set = set()
    for path in files:
        if os.path.basename(os.path.dirname(path)) != day:
            continue
        env = read(path)
        if env is None or not env.get("body"):
            continue
        try:
            got = json.loads(env["body"])
        except ValueError:
            continue
        items = got.get("results") if isinstance(got, dict) else got
        for one in (items or []):
            if isinstance(one, dict):
                key = one.get("hash_id") or one.get("id") or one.get("idx")
                if key:
                    ids.add(str(key))
    return ids, day


def main() -> int:
    import sqlite3

    args = sys.argv[1:]
    site = next((a for a in args if not a.startswith("-")), None)
    if not site:
        print("쓰는 법 — python3.11 tools/list_diff_check.py <site> [--write]")
        return 2
    write = "--write" in args
    ids, day = latest_list_ids(site)
    if not ids:
        print(f"★ {site} — 목록 파일이 없다.  ★ 먼저 받아야 한다")
        return 1
    conn = sqlite3.connect(os.path.join(ROOT, "carwatch.db"), timeout=60)
    conn.execute("PRAGMA busy_timeout = 60000")
    alive = [(r[0], r[1]) for r in conn.execute(
        "SELECT listing_id, source_id FROM core_listing"
        " WHERE site=? AND status IN ('active','new')", (site,))]
    gone = [(lid, sid) for lid, sid in alive if str(sid) not in ids]
    print(f"★ {site} — 오늘 목록({day}) {len(ids):,}건 · "
          f"우리가 산 것으로 아는 매물 {len(alive):,}건")
    print(f"★ ★ 목록에서 사라진 것 {len(gone):,}건"
          + ("" if write else "  ★ 재기만 한다 — 아직 안 죽인다"))
    if not gone or not write:
        for lid, sid in gone[:8]:
            print(f"   {sid}")
        return 0

    # ★★ 사라졌다고 죽이지 않는다 — ★ **상세를 눌러 본다** (마스터 지시)
    import importlib
    import urllib.error
    import urllib.request

    mod = importlib.import_module(f"parse.{site}.mapping")
    col = importlib.import_module(f"tools.collect_{site}")
    at = _now()
    got: Counter = Counter()
    for lid, sid in gone:
        url = f"{col.BASE}/cars/{sid}/"
        try:
            with urllib.request.urlopen(urllib.request.Request(
                    url, headers=col.HEADERS), timeout=30) as res:
                body = res.read()
        except urllib.error.HTTPError as e:
            body = None if e.code != 404 else b""
        except (urllib.error.URLError, OSError, TimeoutError):
            body = None
        if body is None:
            # ★ 못 받았다 — ★ 「없다」가 아니다.  ★ 잇달아 사흘이면 unreachable
            got["못 받음 (안 죽인다)"] += 1
            time.sleep(SLEEP * 2)
            continue
        # ★★★★★ 09-01 — ★ **차단 페이지를 「없다」로 읽지 않는다.**
        #   ★ 실측 09-01 — ★ KB 매물 23건이 ★ 200 · 1,382B
        #     ★ 「로봇여부 확인 | KB차차차」를 받고 ★ **죽었다.**
        #   ★★ ★ 파서가 `None` 을 돌려준 까닭이 ★ 「없는 차」인지 ★ 「못 받았다」인지
        #     ★ ★ 갈라야 한다 — ★ 안 가르면 ★ 살아 있는 차를 죽인다 (74대 오살과 같은 꼴).
        #   ★ ★ ★ 판정은 ★ 사이트 어댑터 하나에 둔다 (`is_bot_wall`) —
        #     ★ ★ 부르는 쪽마다 다르게 세면 ★ 샌다
        if _bot_wall(site, body):
            got["★ 차단 페이지 (못 받았다 · 안 죽인다)"] += 1
            time.sleep(SLEEP * 2)
            continue
        deep = mod.parse_detail(body, site, sid) if body else None
        if deep:
            got["★ 살아 있다 (안 죽인다)"] += 1
        else:
            # ★ 사이트가 「없다」고 답했다 — ★ 그때만 죽인다.  ★ 셋을 함께 적는다
            conn.execute(
                "UPDATE core_listing SET detail_status='not_found',"
                " sales_status='detail_gone', status='gone', gone_at=?,"
                " last_price_won=COALESCE(last_price_won, price_current_won)"
                " WHERE listing_id=?", (at, lid))
            conn.execute(
                "INSERT INTO core_listing_change"
                "(listing_id,changed_at,field,old_value,new_value,change_kind,cause)"
                " VALUES (?,?,?,?,?,?,?)",
                (lid, at, "status", "active", "gone", "gone",
                 "목록에서 사라져 상세를 눌렀더니 없다고 답했다"))
            got["★ detail_gone"] += 1
        conn.commit()
        time.sleep(SLEEP)
    print("★ " + " · ".join(f"{k} {v}" for k, v in got.most_common()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
