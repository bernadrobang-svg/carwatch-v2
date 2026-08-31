# -*- coding: utf-8 -*-
"""1걸음 — ★ **받은 것을 파일로만 쓴다.  ★ DB 를 안 연다.**

지시서   `docs/ARCHITECTURE_20260830.md` 2장 (다섯 걸음) · 4장 (파일 꼴) · 9장 (P3 뒤집힘)
근거     ★★★★★ 마스터 지시 09-01 —
         「★ 자리   `raw/{site}/{endpoint}/{YYYY-MM-DD}/{source_id}.json`
          ★        `raw/{site}/{endpoint}/{YYYY-MM-DD}/page-{NNNN}.json`   ← 목록
          ★ 지킬 것 ★ **받기 걸음은 파일만 쓴다.  ★ DB 를 안 연다 — 잠금이 아예 안 생긴다**
          ★        ★ 넣기 걸음은 그 폴더를 읽어 `raw_response` ＋ `core_listing` 에 넣는다」

★★★ 왜 이것이 필요한가 — ★ 실측 09-01.
  ★ 내가 리볼트를 받으면서 ★ 한 건마다 ★ `save_site_raw()` ＋ `commit()` 을 했다.
  ★ ★ 그 사이에 ★ `check_all` 이 ★ **`OperationalError: database is locked`** 로
    ★ ★ ★ **통째로 죽었다** (통과 466 · fatal 16 · 그중 10이 잠금).
  ★ ★ 규격이 「본 DB 와 잠금을 안 다툰다」라 적어 둔 ★ 바로 그 자리였다.
  ★★ ★ **받기가 DB 를 안 열면 ★ 잠금이 아예 안 생긴다** — ★ 그것이 이 파일의 전부다

금지     ★ 이 모듈에서 ★ `sqlite3` 를 들이는 것.  ★ 검산 `S46-202`
금지     ★ 반쪽 파일을 남기는 것 — ★ `.part` 로 쓰고 `os.replace` 로 옮긴다
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

# ★ 원문 몸통은 ★ 본 DB 와 ★ **같은 꼴로 누른다** (`CWZ1`) — ★ 새로 만들지 않는다
from store.raw import pack_body, raw_body

ORIGIN_COLLECTOR = "collector"
PART = ".part"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def root_dir(root: str = ".") -> str:
    """원문 파일이 사는 곳.  ★ 코드에 안 박는다 — `config/deploy.json` 의 `work_dir`."""
    try:
        with open(os.path.join(root, "config", "deploy.json"),
                  encoding="utf-8") as f:
            base = json.load(f).get("work_dir") or root
    except (OSError, ValueError):
        base = root
    return os.path.join(base, "raw")


def day_dir(site: str, endpoint: str, at: str | None = None,
            root: str = ".") -> str:
    """`raw/{site}/{endpoint}/{YYYY-MM-DD}` — ★ 마스터께서 주신 자리 그대로."""
    day = (at or _now())[:10]
    return os.path.join(root_dir(root), site, endpoint, day)


def _write(path: str, payload: dict) -> str:
    """★ `.part` 로 쓰고 ★ `os.replace` 로 옮긴다 — ★ 반쪽을 안 남긴다 (규격 4장)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + PART
    with open(tmp, "wb") as f:
        f.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    os.replace(tmp, path)
    return path


def _uniq(path: str) -> str:
    """이미 있으면 ★ 덮어쓰지 않는다 — ★ `__HHMMSS` 를 붙인다 (규격 4장 · P3)."""
    if not os.path.exists(path):
        return path
    head, ext = os.path.splitext(path)
    return f"{head}__{datetime.now(timezone.utc).strftime('%H%M%S')}{ext}"


def save(site: str, endpoint: str, source_id: str | None, url: str,
         body, at: str | None = None, http_code: int = 200,
         status: str = "ok", origin: str = ORIGIN_COLLECTOR,
         run_id: str | None = None, page: int | None = None,
         root: str = ".") -> str | None:
    """★ 받은 것을 ★ **파일 하나**로 남긴다.  ★ DB 를 안 연다.

    ★ 목록은 ★ `page-{NNNN}.json` · 그 밖은 ★ `{source_id}.json` (마스터 지시)
    ★ 몸통이 없으면 ★ 아무것도 안 쓴다 — ★ 「없음」으로 저장하지 않는다 (금지 12)
    돌려줌  쓴 파일 경로 · 또는 None
    """
    if body is None or body == "" or body == b"":
        return None
    at = at or _now()
    if isinstance(body, bytes):
        body = body.decode("utf-8", "replace")
    elif not isinstance(body, str):
        body = json.dumps(body, ensure_ascii=False)
    name = (f"page-{int(page):04d}.json" if page is not None
            else f"{source_id}.json")
    path = _uniq(os.path.join(day_dir(site, endpoint, at, root), name))
    packed = pack_body(body)
    return _write(path, {
        "site": site, "endpoint": endpoint,
        "source_id": None if source_id is None else str(source_id),
        "url": url, "http_code": http_code, "status": status,
        "origin": origin, "run_id": run_id, "fetched_at": at,
        # ★ 누른 채로 담는다 — ★ 읽는 쪽이 `raw_body()` 를 거친다
        "body_b64": packed.hex() if isinstance(packed, bytes) else None,
        "body": None if isinstance(packed, bytes) else packed,
    })


def read(path: str) -> dict | None:
    """파일 하나 → ★ 봉투 dict.  ★ `body` 는 ★ **원문 글자**로 되돌려 준다."""
    try:
        with open(path, "rb") as f:
            got = json.loads(f.read().decode("utf-8"))
    except (OSError, ValueError):
        return None
    if got.get("body_b64"):
        got["body"] = raw_body(bytes.fromhex(got["body_b64"]))
    got.pop("body_b64", None)
    return got


def walk(site: str | None = None, endpoint: str | None = None,
         day: str | None = None, root: str = ".") -> list:
    """폴더를 훑어 ★ 파일 경로를 낸다.  ★ `.part` 는 안 낸다 (규격 4장)."""
    base = root_dir(root)
    out: list = []
    if not os.path.isdir(base):
        return out
    for s in sorted(os.listdir(base)):
        if site and s != site:
            continue
        sdir = os.path.join(base, s)
        if not os.path.isdir(sdir):
            continue
        for e in sorted(os.listdir(sdir)):
            if endpoint and e != endpoint:
                continue
            edir = os.path.join(sdir, e)
            if not os.path.isdir(edir):
                continue
            for d in sorted(os.listdir(edir)):
                if day and d != day:
                    continue
                ddir = os.path.join(edir, d)
                if not os.path.isdir(ddir):
                    continue
                for n in sorted(os.listdir(ddir)):
                    if n.endswith(PART) or not n.endswith(".json"):
                        continue
                    out.append(os.path.join(ddir, n))
    return out
