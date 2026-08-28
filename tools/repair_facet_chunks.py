# -*- coding: utf-8 -*-
"""낱개로 저장된 facet 조각을 이어붙인다 (개정 307 사고 복구).

지시서   5장 개정 307 · V11-98
사고     2026-08-17 10:48 (01:48 UTC).  마스터가 전 차종 수집을 눌렀을 때
        화면(JS)은 새 코드라 바이트를 나눠 보냈는데
        서버(web/views.py)는 재시작 전이라 옛 코드였다.
        ★ 이어붙이는 쪽이 없어 조각 55개가 낱개로 저장됐다
        ★ 「실패 0건」으로 보였지만 자료는 반쪽이었다 —
          가이드 지적 「실패 안 났다와 제대로 들어왔다는 다르다」가 그대로 맞았다
값규칙   조각을 지우지 않는다.  이어붙인 것을 새로 넣고 조각은 표시만 바꾼다 (P3)
        이어붙인 결과가 유효한 JSON 이 아니면 아무것도 하지 않는다
금지     조각을 지우는 것.  덜 온 것을 저장하는 것
사용     python3.11 tools/repair_facet_chunks.py [--apply]
"""
from __future__ import annotations

import collections
import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# 이 시각 이후에 들어온 것만 본다 (UTC).  ★ 그 앞의 온전한 facet 을 안 건드린다
SINCE = "2026-08-17T01:40"
# 조각이 아니라 온전한 응답이면 이만큼보다 크다.  실측 — 조각은 22~30KB
WHOLE_MIN_BYTES = 60_000
# 이어붙인 뒤 있어야 할 최소 노드 수 (iNav.Nodes).  실측 55
MIN_NODES = 20
# ★ 조각에 남기는 표시.  ★ 글자는 앞판과 같게 둔다 — 사람이 찾던 말이다
FRAGMENT_NOTE = "조각이다 — 이어붙인 것이 따로 있다 (개정 307 복구)"


def meta_of(text) -> dict:
    """`response_meta` 를 dict 로 읽는다.  ★ JSON 이 아니면 되살린다.

    ★★ 08-28 — ★ 이 도구의 앞판이 ★ JSON 뒤에 ` | 조각이다 …` 를
      ★ 글자로 이어붙여 ★ `response_meta` 가 ★ JSON 이 아니게 됐다 (55건).
      ★ 그러면 ★ `json_extract` 가 ★ 「malformed JSON」으로 죽고,
      ★ `V11-47` 이 ★ 그 행의 「보낸 바이트」를 ★ 못 잰다
      (★ 원문 압축 v287 을 하다 드러났다).
    ★ 앞의 JSON 만 떼어 읽고 ★ 뒤 글은 `note` 로 옮긴다 — ★ 버리지 않는다
    """
    if not text:
        return {}
    try:
        got = json.loads(text)
        return got if isinstance(got, dict) else {"note": str(text)}
    except ValueError:
        pass
    head, sep, tail = str(text).partition(" | ")
    try:
        got = json.loads(head)
    except ValueError:
        return {"note": str(text)}
    if not isinstance(got, dict):
        return {"note": str(text)}
    if sep:
        got["note"] = tail
    return got


def fix_meta(conn, apply: bool) -> int:
    """★ JSON 이 아닌 `response_meta` 를 ★ JSON 으로 되돌린다.

    ★ 뜻은 그대로다 — ★ 이어붙였던 글이 ★ `note` 칸으로 들어갈 뿐이다
    """
    bad = []
    for rid, meta in conn.execute(
        "SELECT id, response_meta FROM raw_response"
        " WHERE response_meta IS NOT NULL AND NOT json_valid(response_meta)"
    ).fetchall():
        bad.append((rid, meta))
    for rid, meta in bad:
        if apply:
            conn.execute(
                "UPDATE raw_response SET response_meta = ? WHERE id = ?",
                (json.dumps(meta_of(meta), ensure_ascii=False), rid))
    if apply and bad:
        conn.commit()
    return len(bad)


def groups(conn) -> dict:
    got: dict = collections.OrderedDict()
    for rid, url, body in conn.execute(
        "SELECT id, request_url, body FROM raw_response"
        " WHERE endpoint='facet' AND status='ok' AND fetched_at >= ?"
        " ORDER BY id", (SINCE,)
    ):
        from store.raw import raw_body

        got.setdefault(url, []).append((rid, raw_body(body)))

    return got


def join(parts: list) -> tuple:
    """(온전한 원문, 사유).  ★ 유효한 JSON 이 아니면 원문이 아니다."""
    body = "".join(b for _rid, b in parts)
    try:
        doc = json.loads(body)
    except (ValueError, TypeError) as e:
        return None, f"이어붙였는데 JSON 이 아니다 — {e}"
    nodes = (doc.get("iNav") or {}).get("Nodes") or []
    if len(nodes) < MIN_NODES:
        return None, f"노드가 {len(nodes)}개뿐이다 — 조각이 빠졌다"
    return body, f"Count={doc.get('Count')} · 노드 {len(nodes)}"


def main() -> int:
    apply = "--apply" in sys.argv
    conn = sqlite3.connect(os.path.join(ROOT, "carwatch.db"), timeout=30)
    conn.execute("PRAGMA busy_timeout = 30000")
    # ★★ `--fix-meta` — ★ 이 도구의 앞판이 망가뜨린 `response_meta` 만 되돌린다.
    #   ★ 조각을 다시 이어붙이지 않는다 — ★ 그 일은 이미 끝났다 (개정 307)
    if "--fix-meta" in sys.argv:
        n = fix_meta(conn, apply)
        print(f"JSON 이 아닌 response_meta {n}건"
              + ("  → 되돌렸다" if apply else "  (--apply 를 붙여야 쓴다)"))
        left = conn.execute(
            "SELECT COUNT(*) FROM raw_response WHERE response_meta IS NOT NULL"
            " AND NOT json_valid(response_meta)").fetchone()[0]
        print(f"남은 것 {left}건")
        return 1 if (apply and left) else 0
    fixed = skipped = 0
    for url, parts in groups(conn).items():
        if len(parts) == 1 and len(parts[0][1]) >= WHOLE_MIN_BYTES:
            continue                      # 이미 온전하다
        if len(parts) == 1:
            print(f"  건너뜀 조각 1개뿐 — {url[:60]}")
            skipped += 1
            continue
        body, why = join(parts)
        head = f"조각 {len(parts)}개 → {len(''.join(b for _i, b in parts)):,}B"
        if body is None:
            print(f"  ✗ {head}  {why}")
            skipped += 1
            continue
        print(f"  ✓ {head}  {why}")
        fixed += 1
        if not apply:
            continue
        first = parts[0][0]
        row = conn.execute(
            "SELECT run_id, site, endpoint, request_url, request_meta,"
            " http_code, response_meta, origin, fetched_at"
            " FROM raw_response WHERE id = ?", (first,)).fetchone()
        # ★ 「여러 POST 를 이어붙였다」를 남긴다 (개정 307).
        #   한 번에 보낸 것이 아니라는 사실이다 — V11-47 이 그것으로 가른다
        # ★★ 08-28 — ★ 글자를 손질해 만들지 않는다.  ★ JSON 으로 만든다.
        #   ★ 앞판은 `rstrip("}")` 로 잘라 붙였는데 ★ meta 가 이미
        #     JSON 이 아니면 ★ 더 망가진 것을 만든다
        meta = json.dumps({**meta_of(row[6]), "transfer": "chunked"},
                          ensure_ascii=False)
        from store.raw import pack_body

        conn.execute(
            "INSERT INTO raw_response(run_id, site, endpoint, request_url,"
            " request_meta, http_code, response_meta, status, body, origin,"
            " fetched_at) VALUES (?,?,?,?,?,?,?,'ok',?,?,?)",
            (row[0], row[1], row[2], row[3], row[4], row[5], meta,
             pack_body(body), row[7], row[8]))
        # ★ 조각을 지우지 않는다.  「원문이 아니다」로만 표시한다 (P3)
        # ★★ 08-28 — ★ JSON 뒤에 글을 이어붙이지 않는다.  ★ 칸에 담는다.
        #   ★ 앞판의 `|| ' | 조각이다 …'` 가 ★ response_meta 를
        #     ★ JSON 이 아니게 만들었다 (55건 · `meta_of` 설명 참고)
        for _rid, _b in parts:
            _cur = conn.execute(
                "SELECT response_meta FROM raw_response WHERE id = ?",
                (_rid,)).fetchone()
            conn.execute(
                "UPDATE raw_response SET status='error', response_meta = ?"
                " WHERE id = ?",
                (json.dumps({**meta_of(_cur[0] if _cur else None),
                             "note": FRAGMENT_NOTE}, ensure_ascii=False),
                 _rid))
    # ★ raw_facet 에도 같은 조각이 들어가 있다 (store/raw.py 가 둘 다 넣는다).
    #   S3 는 이쪽을 읽는다 — 여기를 안 고치면 파이프라인이 JSON 에서 죽는다
    fixed2 = 0
    facet_groups: dict = collections.OrderedDict()
    for site, tk, kind, url, axis, body, at in conn.execute(
        "SELECT site, target_key, request_kind, request_url, axis_count,"
        " body, fetched_at FROM raw_facet ORDER BY rowid"
    ):
        facet_groups.setdefault((site, tk), []).append(
            (kind, url, axis, body, at))
    for (site, tk), parts in facet_groups.items():
        if len(parts) == 1 and len(parts[0][3]) >= WHOLE_MIN_BYTES:
            continue
        if len(parts) == 1:
            continue
        body, why = join([(0, p[3]) for p in parts])
        if body is None:
            print(f"  ✗ raw_facet {tk} — {why}")
            continue
        print(f"  ✓ raw_facet {tk} 조각 {len(parts)}개 → {len(body):,}B  {why}")
        fixed2 += 1
        if not apply:
            continue
        conn.execute("DELETE FROM raw_facet WHERE site=? AND target_key=?",
                     (site, tk))
        head = parts[0]
        conn.execute(
            "INSERT INTO raw_facet(site,target_key,request_kind,request_url,"
            "axis_count,body,fetched_at) VALUES (?,?,?,?,?,?,?)",
            (site, tk, head[0], head[1], head[2], body, head[4]))
    print(f"raw_facet 이어붙인 것 {fixed2}")

    if apply:
        conn.commit()
    print(f"\n이어붙인 것 {fixed} · 못 한 것 {skipped}"
          + ("" if apply else "   ★ --apply 를 붙여야 실제로 넣는다"))
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
