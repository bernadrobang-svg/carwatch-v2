"""원문이 `ok` 인데 규격 열쇠가 없는 것을 되돌린다 (09-03).

쓰기   python3.11 tools/mark_shell_raw.py            재기만 한다
      python3.11 tools/mark_shell_raw.py --write    딱지를 고친다

★★★★★ 왜 필요한가 — 실측 09-03
  ★ 헤이딜러 상세 18건이 ★ HTTP 200 · JSON dict 인데 ★ 본문이
    ★ `{"code":null,"message":null,"toast":{"message":"서버 오류가 …"}}`
    ★ ★ 198바이트짜리 ★ **오류 안내**였다.
  ★ 그것이 `status='ok'` 로 남아 ★ 「상세 99 · 파싱 81」이 났다 —
    ★ ★ 상세가 99가 아니라 ★ **81** 이었다.  ★ 「받았다」가 부풀었다.
  ★★ 규격의 관문은 `collect/fetcher.py:verify_shape()` 다 (2장 STEP 18) —
    ★ ★ `required_keys` 가 없으면 ★ 저장하지 않는다.
    ★ ★ ★ 수집기가 그 관문을 안 거쳐 들어온 것을 여기서 되돌린다.

★ 원문(`body`)은 ★ **지우지 않는다** — ★ 딱지(`status`)만 `error` 로 바꾼다.
★ HTML 창구는 ★ 건드리지 않는다 — ★ 열쇠로 못 잰다 (BMW·현대인증·K카·보배드림).
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from store.raw import raw_body  # noqa: E402

SHELL_NOTE = "09-03 규격 required_keys 누락 — 200 이지만 상세가 아니다"


def _spec_of(site: str):
    """그 사이트 상세 창구의 규격.  못 찾으면 None.

    ★ 어댑터가 두 꼴이다 — ★ 모듈의 `schema(kind)` 와
      ★ 클래스의 `endpoint_schema()`.  ★ 둘 다 본다
    """
    try:
        mod = __import__(f"adapters.{site}", fromlist=["schema"])
    except ImportError:
        return None
    fn = getattr(mod, "schema", None)
    if callable(fn):
        try:
            return fn("detail")
        except Exception:
            pass
    try:
        from run import _adapter_for
        cfg = json.load(open(os.path.join(ROOT, "config", "endpoints.json")))
        return _adapter_for(site)(cfg[site]).endpoint_schema().get("detail")
    except Exception:
        return None


def _body_text(b) -> str | None:
    if isinstance(b, bytes):
        try:
            b = raw_body(b)
        except Exception:
            pass
    if isinstance(b, bytes):
        b = b.decode("utf-8", "replace")
    return b if isinstance(b, str) else None


def shells(conn, site: str, spec) -> list[int]:
    """그 사이트의 껍데기 rowid 목록."""
    out = []
    for rid, b in conn.execute(
        "SELECT rowid, body FROM raw_response "
        "WHERE site=? AND endpoint='detail' AND status='ok'", (site,)):
        txt = _body_text(b)
        try:
            d = json.loads(txt) if txt is not None else None
        except ValueError:
            continue          # ★ JSON 이 아니면 ★ 여기서 안 가른다
        if isinstance(d, list):
            d = d[0] if d else {}
        if not (isinstance(d, dict) and all(k in d for k in spec.required_keys)):
            out.append(rid)
    return out


def main() -> int:
    write = "--write" in sys.argv
    db = os.path.join(ROOT, "carwatch.db")
    conn = sqlite3.connect(db)
    total = 0
    for (site,) in conn.execute(
            "SELECT DISTINCT site FROM raw_response "
            "WHERE endpoint='detail' AND status='ok'").fetchall():
        spec = _spec_of(site)
        if spec is None:
            print(f"  {site:<16} 규격을 못 읽었다 — 건너뛴다")
            continue
        if str(getattr(spec, "root_type", "") or "") == "html":
            print(f"  {site:<16} HTML 창구 — 열쇠로 못 잰다.  건너뛴다")
            continue
        if not spec.required_keys:
            print(f"  {site:<16} required_keys 가 비었다 — 잴 잣대가 없다")
            continue
        rids = shells(conn, site, spec)
        total += len(rids)
        print(f"  {site:<16} 껍데기 {len(rids):>5}건  (열쇠 {spec.required_keys})")
        if write and rids:
            # ★ `body` 는 그대로 둔다 — ★ 딱지만 바꾼다 (원문을 안 지운다)
            conn.executemany(
                "UPDATE raw_response SET status='error' WHERE rowid=?",
                [(r,) for r in rids])
    if write:
        conn.commit()
    print(f"★ 합계 껍데기 {total}건 — " + ("딱지를 고쳤다" if write else "--write 를 주면 고친다"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
