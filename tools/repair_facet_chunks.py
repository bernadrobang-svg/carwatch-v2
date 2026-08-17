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


def groups(conn) -> dict:
    got: dict = collections.OrderedDict()
    for rid, url, body in conn.execute(
        "SELECT id, request_url, body FROM raw_response"
        " WHERE endpoint='facet' AND status='ok' AND fetched_at >= ?"
        " ORDER BY id", (SINCE,)
    ):
        got.setdefault(url, []).append((rid, body))
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
    conn = sqlite3.connect(os.path.join(ROOT, "carwatch.db"))
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
        conn.execute(
            "INSERT INTO raw_response(run_id, site, endpoint, request_url,"
            " request_meta, http_code, response_meta, status, body, origin,"
            " fetched_at) VALUES (?,?,?,?,?,?,?,'ok',?,?,?)",
            (row[0], row[1], row[2], row[3], row[4], row[5], row[6], body,
             row[7], row[8]))
        # ★ 조각을 지우지 않는다.  「원문이 아니다」로만 표시한다 (P3)
        conn.execute(
            "UPDATE raw_response SET status='error',"
            " response_meta = COALESCE(response_meta,'')"
            " || ' | 조각이다 — 이어붙인 것이 따로 있다 (개정 307 복구)'"
            f" WHERE id IN ({','.join('?' * len(parts))})",
            tuple(rid for rid, _b in parts))
    if apply:
        conn.commit()
    print(f"\n이어붙인 것 {fixed} · 못 한 것 {skipped}"
          + ("" if apply else "   ★ --apply 를 붙여야 실제로 넣는다"))
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
