# -*- coding: utf-8 -*-
"""원문 파일·행의 살림 — ★ 마스터 지시 09-01.

★★★ 마스터 — 「★ **모든 것이 정리되면 `raw_response` 를 지운다.**
   ★ **파일은 수집 후 보관하다 7일이 지나면 지운다.**
   ★ **목록을 대조해서 기존 목록에서 사라지면 상세를 조회해서 판매상태 여부를 체크한다**」

★★★★★ ★ **규격과 어긋나는 자리가 있어 여쭙는다 (규칙 2)** —
  ★ `docs/ARCHITECTURE_20260830.md` 9장은 ★ 「금지 — ★ **원문 파일을 지우는 것**」이고
    ★ ★ 검산 `S46-185` 가 ★ 그것을 본다.
  ★ ★ 마스터께서는 ★ 「파일은 7일 지나면 지운다」라 하셨다.
  ★★ ★ **그래서 이 도구는 ★ 세기만 하고 ★ `--write` 없이는 아무것도 안 지운다.**
    ★ ★ ★ 어느 쪽이 정본인지 ★ 정해 주시면 ★ 그때 켠다

돌리는 법
    python3.11 tools/raw_lifecycle.py                 ★ 잰다 (아무것도 안 지운다)
    python3.11 tools/raw_lifecycle.py --drop-rows --write   ★ 행을 지운다 (파일 대조 뒤)
    python3.11 tools/raw_lifecycle.py --drop-files --write  ★ ★ 7일 지난 파일 (마스터 확답 뒤)

★★★★★ 0-3 — ★ **원문 표를 비운다** (지시문 r1124 · `S46-265`)

    python3.11 tools/raw_lifecycle.py --purge-bodies --write
    python3.11 tools/raw_lifecycle.py --vacuum --write

★ 왜 두 걸음인가 — ★ 실측 09-03 · ★ `raw_response` 는 ★ **372,571행**인데
  ★ ★ `raw/` 파일은 ★ **8,410개**뿐이었다.  ★ ★ 옛 행은 ★ **파일이 없다**.
  ★ ★ ★ 규격은 ★ 「금지 — ★ 파일이 없는 것을 지우는 것」이다.
★ ★ 그래서 ★ **한 행마다 ★ ① 파일로 내보내고 ★ ② 그 행을 지운다** —
  ★ ★ 파일이 먼저 자리를 잡은 뒤에 지우므로 ★ **P3 무손실**이고 ★ 도중에 끊겨도 안전하다
"""
from __future__ import annotations

import os
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from store.rawfile import read, walk  # noqa: E402

KEEP_DAYS = 7          # ★ 마스터 지시 09-01 — 「수집 후 보관하다 7일이 지나면」


def _file_keys(files: list) -> set:
    """이미 파일에 있는 것.  ★ 경로에서 뽑는다 — ★ 8,410개를 열지 않는다.

    ★ `raw/{site}/{endpoint}/{day}/{source_id}.json` · `__HHMMSS` 는 떼어 낸다
    """
    keys = set()
    for path in files:
        name = os.path.splitext(os.path.basename(path))[0].split("__")[0]
        day = os.path.basename(os.path.dirname(path))
        endpoint = os.path.basename(os.path.dirname(os.path.dirname(path)))
        site = os.path.basename(os.path.dirname(os.path.dirname(
            os.path.dirname(path))))
        keys.add((site, endpoint, day, name))
    return keys


def _next_page(seen: dict, site: str, endpoint: str, day: str) -> int:
    """목록·facet 은 ★ `source_id` 가 없다.  ★ `page-NNNN` 을 이어 붙인다."""
    key = (site, endpoint, day)
    seen[key] = seen.get(key, 0) + 1
    return seen[key]


def purge_bodies(conn, files: list, write: bool, batch: int = 200) -> int:
    """0-3 — ★ 원문을 ★ **파일로 내보낸 뒤** ★ 그 행을 지운다 (`S46-265`).

    ★ 한 묶음씩 읽는다 — ★ 전건을 RAM 에 올리면 ★ 이 도구가 서버를 죽인다.
      ★ ★ 실측 09-03 — ★ 그렇게 죽은 것이 ★ **세 번**이다
    """
    from store.raw import raw_body
    from store.rawfile import save

    have = _file_keys(files)
    seen: dict = {}
    n0, mb0 = conn.execute(
        "SELECT COUNT(*), SUM(LENGTH(body))/1e6 FROM raw_response"
        " WHERE body IS NOT NULL AND body <> ''").fetchone()
    print(f"★ 몸통 있는 행 {n0:,}개 · {mb0 or 0:,.1f}MB — ★ 파일로 내보내고 지운다")
    if not write:
        print("   ★ `--write` 가 없다.  ★ 아무것도 안 한다")
        return 0
    wrote = gone = skipped = 0
    while True:
        rows = conn.execute(
            "SELECT id, site, endpoint, source_id, request_url, http_code,"
            "       status, origin, run_id, fetched_at, body"
            "  FROM raw_response"
            " WHERE body IS NOT NULL AND body <> ''"
            " ORDER BY id LIMIT ?", (batch,)).fetchall()
        if not rows:
            break
        for (rid, site, endpoint, sid, url, code, status, origin,
             run_id, at, body) in rows:
            day = (at or "")[:10]
            key = (site, endpoint, day,
                   str(sid) if sid is not None else None)
            if sid is not None and key in have:
                # ★ 이미 파일에 있다 — ★ 또 쓰지 않는다.  ★ 행만 지운다
                conn.execute("DELETE FROM raw_response WHERE id=?", (rid,))
                skipped += 1
                gone += 1
                continue
            text = raw_body(body) if isinstance(body, bytes) else body
            page = (None if sid is not None
                    else _next_page(seen, site, endpoint, day))
            path = save(site, endpoint, sid, url, text, at=at,
                        http_code=code or 200, status=status or "ok",
                        origin=origin or "collector", run_id=run_id,
                        page=page, root=ROOT)
            if path is None:
                # ★ 못 쓴 것은 ★ 안 지운다 — ★ 원문을 잃지 않는다
                continue
            conn.execute("DELETE FROM raw_response WHERE id=?", (rid,))
            wrote += 1
            gone += 1
            if sid is not None:
                have.add(key)
        conn.commit()
        print(f"   … 내보냄 {wrote:,} · 이미 있어 건너뜀 {skipped:,} ·"
              f" 지운 행 {gone:,}", flush=True)
    left = conn.execute(
        "SELECT COUNT(*) FROM raw_response"
        " WHERE body IS NOT NULL AND body <> ''").fetchone()[0]
    print(f"★ 끝 — 파일로 내보냄 {wrote:,} · 이미 있었음 {skipped:,} ·"
          f" 지운 행 {gone:,} · 못 내보낸 행 {left:,}")
    return gone


def vacuum(conn, write: bool) -> None:
    """0-3 — ★ 지운 뒤 `VACUUM`.  ★ 안 하면 ★ 파일 크기가 안 준다."""
    path = os.path.join(ROOT, "carwatch.db")
    before = os.path.getsize(path)
    print(f"★ DB {before/2**30:.3f} GiB")
    if not write:
        print("   ★ `--write` 가 없다.  ★ 안 돈다")
        return
    conn.execute("VACUUM")
    after = os.path.getsize(path)
    print(f"★ VACUUM 뒤 {after/2**30:.3f} GiB"
          f" ({(before-after)/2**20:,.0f} MiB 줄었다)")


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def main() -> int:
    import sqlite3

    args = sys.argv[1:]
    write = "--write" in args
    files = walk(root=ROOT)
    conn = sqlite3.connect(os.path.join(ROOT, "carwatch.db"), timeout=60)
    conn.execute("PRAGMA busy_timeout = 60000")

    # ── 0-3 — ★ 원문 표를 비운다 ＋ VACUUM (지시문 r1124 · S46-265)
    if "--purge-bodies" in args:
        purge_bodies(conn, files, write)
        return 0
    if "--vacuum" in args:
        vacuum(conn, write)
        return 0

    # ── ① 파일 ↔ 행 대조 — ★ 옮긴 것만 지울 수 있다 (P3 무손실)
    have = {(r[0], r[1], r[2]) for r in conn.execute(
        "SELECT site, endpoint, source_id FROM raw_response")}
    got: Counter = Counter()
    by_day: Counter = Counter()
    moved: list = []
    for path in files:
        env = read(path)
        if env is None:
            got["★ 못 읽는 파일"] += 1
            continue
        key = (env.get("site"), env.get("endpoint"), env.get("source_id"))
        day = os.path.basename(os.path.dirname(path))
        by_day[day] += 1
        if key in have or env.get("endpoint") == "list":
            got["행으로 옮겨졌다"] += 1
            moved.append((path, day))
        else:
            got["★ 아직 안 옮겨졌다"] += 1
    print(f"★ 원문 파일 {len(files):,}개")
    for k, v in got.most_common():
        print(f"   {k:<22}{v:>7,}")
    print("\n★ 날짜마다")
    for d, n in sorted(by_day.items()):
        print(f"   {d}{n:>8,}")

    # ── ② `raw_response` 행 — ★ 파일로 옮긴 것만 지운다 (P3)
    rows = conn.execute("SELECT COUNT(*), SUM(LENGTH(body))"
                        " FROM raw_response").fetchone()
    print(f"\n★ `raw_response` {rows[0]:,}행 · body {(rows[1] or 0)/1e6:,.1f}MB")
    sites = {os.path.basename(os.path.dirname(os.path.dirname(
        os.path.dirname(p)))) for p in files}
    if sites:
        marks = ",".join("?" * len(sites))
        n = conn.execute(
            f"SELECT COUNT(*) FROM raw_response WHERE site IN ({marks})",
            tuple(sites)).fetchone()[0]
        print(f"   ★ 파일이 있는 사이트({', '.join(sorted(sites))})의 행 {n:,}개")
        if "--drop-rows" in args and write:
            # ★★ 파일에 있는 것만 지운다 — ★ 하나씩 대조한다 (P3 무손실)
            gone = 0
            for path in files:
                env = read(path)
                if env is None or env.get("endpoint") == "list":
                    continue
                gone += conn.execute(
                    "DELETE FROM raw_response WHERE site=? AND endpoint=?"
                    "  AND source_id=?",
                    (env["site"], env["endpoint"], env["source_id"])).rowcount
            conn.commit()
            print(f"   ★ 지운 행 {gone:,}개 (파일에 있는 것만)")

    # ── ③ 7일 지난 파일 — ★ 마스터 확답 전에는 ★ 세기만 한다
    cut = (datetime.now(timezone.utc) - timedelta(days=KEEP_DAYS)
           ).strftime("%Y-%m-%d")
    old = [p for p, d in moved if d < cut]
    print(f"\n★ {KEEP_DAYS}일이 지난 파일 {len(old):,}개 (기준 {cut} 이전)")
    if "--drop-files" in args and write:
        print("   ★★ 규격 9장은 ★ 「원문 파일을 지우는 것」을 ★ **금지**한다"
              " (`S46-185`).")
        print("   ★★ 마스터께서 ★ 「7일 지나면 지운다」 하셨으므로 ★ 여쭙고 켠다 —"
              " ★ 지금은 안 지운다")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
