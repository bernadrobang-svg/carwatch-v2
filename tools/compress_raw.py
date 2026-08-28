# -*- coding: utf-8 -*-
"""원문(raw_response.body)을 눌러 둔다 (마스터 지시 2026-08-28).

지시서   3장 STEP 33 「원문 무손실 · 삭제 금지 · 추가만」
근거     이 장비는 t4g.small · 램 1,841MB 인데 DB 가 1.00GB 다.
         페이지 캐시에 안 들어가 화면이 차가울 때 10초 · 더울 때 0.7초로
         14배 갈렸다 (outputs v285).  raw_response 가 그 DB 의 77% 다.
★        무손실이다.  한 줄마다 ★ 되돌려 대조한 뒤에만 쓴다.
         하나라도 다르면 그 줄을 건드리지 않고 세어서 보고한다
★        섞여 있어도 된다 — 읽는 쪽은 store.raw.raw_body 가 가른다.
         중간에 끊겨도 다시 돌리면 이어서 한다 (아직 글자인 줄만 고른다)
사용     python3.11 tools/compress_raw.py [carwatch.db] [--dry-run]
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from store.raw import ORIGIN_BROWSER, pack_body, raw_body  # noqa: E402


def _cfg(key, fallback):
    try:
        with open(os.path.join(ROOT, "config", "web.json"),
                  encoding="utf-8") as f:
            return json.load(f)[key]
    except (OSError, ValueError, KeyError, TypeError):
        return fallback


def main() -> int:
    args = [a for a in sys.argv[1:]]
    dry = "--dry-run" in args
    args = [a for a in args if not a.startswith("--")]
    db = args[0] if args else os.path.join(ROOT, "carwatch.db")
    if not os.path.isfile(db):
        print(f"[X] {db} 가 없다")
        return 2

    batch = int(_cfg("db_batch_commit_rows", 100))
    ms = int(_cfg("db_busy_timeout_ms", 30000))
    conn = sqlite3.connect(db, timeout=ms / 1000)
    conn.execute(f"PRAGMA busy_timeout = {ms}")

    before = os.path.getsize(db)
    todo = conn.execute(
        "SELECT COUNT(*) FROM raw_response WHERE body IS NOT NULL"
        " AND typeof(body) = 'text'").fetchone()[0]
    print(f"DB {db}  {before / 1024 ** 3:.2f} GB")
    print(f"아직 글자인 원문 {todo:,}건" + ("   ★ --dry-run" if dry else ""))
    if not todo:
        print("할 것이 없다")
        return 0

    done = packed = same = mismatch = 0
    src = dst = 0
    t0 = time.time()
    # ★ id 로 훑는다.  ★ 한 묶음씩 읽고 쓴다 — 전건을 램에 올리지 않는다
    last = 0
    while True:
        # ★★ `response_meta` 가 JSON 이 아닌 브라우저 행은 ★ 안 누른다.
        #   ★ `V11-47` 이 ★ 「한 번에 보낸 바이트」를 재는데,
        #     ★ meta 에 그 값을 못 넣는 행이라 ★ LENGTH(body) 로 재야 한다.
        #     ★ 누르면 ★ 그 길이가 ★ 거짓이 된다 (55건 · 실측 08-28)
        rows = conn.execute(
            "SELECT id, body FROM raw_response WHERE id > ?"
            " AND body IS NOT NULL AND typeof(body) = 'text'"
            " AND NOT (origin = ? AND response_meta IS NOT NULL"
            "          AND NOT json_valid(response_meta))"
            " ORDER BY id LIMIT ?",
            (last, ORIGIN_BROWSER, batch)).fetchall()
        if not rows:
            break
        writes = []
        for rid, text in rows:
            last = rid
            done += 1
            src += len(text.encode("utf-8"))
            new = pack_body(text)
            if not isinstance(new, bytes):
                same += 1                      # 작아서 안 눌렀다
                dst += len(text.encode("utf-8"))
                continue
            # ★★ 쓰기 전에 되돌려 대조한다.  ★ 다르면 안 건드린다
            if raw_body(new) != text:
                mismatch += 1
                dst += len(text.encode("utf-8"))
                continue
            writes.append((new, rid))
            packed += 1
            dst += len(new)
        if writes and not dry:
            conn.executemany(
                "UPDATE raw_response SET body = ? WHERE id = ?", writes)
            conn.commit()
        if done % (batch * 50) == 0:
            el = time.time() - t0
            print(f"  {done:,}/{todo:,}  눌림 {packed:,} · 그대로 {same:,}"
                  f"  {src / 1024 ** 2:,.0f}MB → {dst / 1024 ** 2:,.0f}MB"
                  f"  {el:,.0f}초")

    # ★★ 브라우저 원문의 「보낸 바이트」를 meta 에 남긴다 (V11-47).
    #   ★ 눌러 두면 LENGTH(body) 가 압축 크기가 되어 검사가 조용히 통과한다
    filled = 0
    browser = conn.execute(
        "SELECT id, body, response_meta FROM raw_response"
        " WHERE origin = ? AND body IS NOT NULL"
        " AND (response_meta IS NULL"
        "      OR (json_valid(response_meta)"
        "          AND json_extract(response_meta,'$.bytes') IS NULL))",
        (ORIGIN_BROWSER,)).fetchall()
    for rid, body, meta in browser:
        try:
            n = len(raw_body(body).encode("utf-8"))
        except (ValueError, TypeError, UnicodeDecodeError):
            continue
        try:
            got = json.loads(meta) if meta else {}
            if not isinstance(got, dict):
                continue
        except ValueError:
            continue
        got["bytes"] = n
        if not dry:
            conn.execute("UPDATE raw_response SET response_meta = ?"
                         " WHERE id = ?",
                         (json.dumps(got, ensure_ascii=False), rid))
        filled += 1
    if not dry:
        conn.commit()

    print()
    print(f"본 것        {done:,}건")
    print(f"  눌렀다     {packed:,}")
    print(f"  그대로 뒀다 {same:,}  (작아서)")
    print(f"  ★ 안 맞아 건드리지 않음 {mismatch:,}")
    print(f"  브라우저 meta.bytes 채움 {filled:,}")
    print(f"본문 {src / 1024 ** 2:,.0f}MB → {dst / 1024 ** 2:,.0f}MB"
          f"  ({src / dst if dst else 1:.1f}배)")
    print(f"{time.time() - t0:,.0f}초")
    if dry:
        print("★ --dry-run 이라 아무것도 안 썼다")
    else:
        print("★ VACUUM 은 따로 돌린다 — 지운 자리는 그때 돌아온다")
    return 1 if mismatch else 0


if __name__ == "__main__":
    raise SystemExit(main())
