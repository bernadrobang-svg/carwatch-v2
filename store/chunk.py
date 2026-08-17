# -*- coding: utf-8 -*-
"""조각 전송 — 바이트를 나누고 서버가 이어붙인다 (개정 307).

지시서   13장 STEP 136c · 5장 개정 307 · V11-98
근거     ★ 마스터 실측 08-17 — facet 8종이 19~21만 바이트라 한 번에 못 보낸다.
        목록은 SearchResults 배열이라 쪼갤 수 있었지만 (개정 263)
        facet 은 하나의 JSON 이라 「내용」으로는 못 나눈다
값규칙   「내용을 나누는 것」이 아니라 「바이트를 나누는 것」이다.
        원문은 그대로 복원된다 (P3 무손실)
금지     max_form_bytes 를 올려 해결하는 것
        반쪽을 저장하는 것 — 하나라도 빠지면 저장하지 않는다
"""
from __future__ import annotations

import hashlib

# 조각을 모으는 자리.  ★ 완성되면 즉시 비운다 — 서버에 쌓아 두지 않는다
_PENDING: dict = {}

# ★ 반쪽이 영원히 남지 않게 하는 시간은 정책이라 config 에 있다 —
#   web.json 의 chunk_stale_sec.  호출자가 넘긴다 (V4-17)


def digest(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def put(key: str, seq: int, total: int, part: bytes, at: float,
        stale_sec: float = 0) -> dict:
    """조각 하나를 넣는다.  (받은 수, 전체, 완성됐는가) 를 돌려준다.

    ★ 순서가 뒤바뀌어 와도 된다.  seq 로 자리를 잡는다
    """
    _sweep(at, stale_sec)
    got = _PENDING.setdefault(key, {"total": total, "parts": {}, "at": at})
    if got["total"] != total:
        # 같은 전송키에 다른 총수가 오면 앞것을 버린다.  섞으면 원문이 깨진다
        got = _PENDING[key] = {"total": total, "parts": {}, "at": at}
    got["parts"][int(seq)] = part
    got["at"] = at
    return {"got": len(got["parts"]), "total": total,
            "done": len(got["parts"]) == total}


def take(key: str, want_len: int, want_hash: str) -> bytes:
    """이어붙여 돌려주고 자리를 비운다.  ★ 길이·해시가 어긋나면 버린다."""
    got = _PENDING.get(key)
    if got is None:
        raise ValueError("조각이 하나도 없습니다")
    missing = [i for i in range(got["total"]) if i not in got["parts"]]
    if missing:
        raise ValueError(
            f"조각 {missing[0] + 1}/{got['total']} 이 안 왔습니다 "
            f"— 받은 것 {len(got['parts'])}개")
    body = b"".join(got["parts"][i] for i in range(got["total"]))
    if len(body) != want_len:
        _PENDING.pop(key, None)
        raise ValueError(f"길이가 다릅니다 — 받은 {len(body)} · 보낸 {want_len}")
    if digest(body) != want_hash:
        _PENDING.pop(key, None)
        raise ValueError("해시가 다릅니다 — 중간에 바뀌었습니다")
    _PENDING.pop(key, None)
    return body


def pending(key: str) -> dict | None:
    got = _PENDING.get(key)
    return None if got is None else {"got": len(got["parts"]),
                                     "total": got["total"]}


def _sweep(at: float, stale_sec: float) -> None:
    """오래된 반쪽을 버린다.  ★ 중간에 끊기면 받은 조각을 버린다 (개정 307)."""
    if not stale_sec:
        return
    for k in [k for k, v in _PENDING.items() if at - v["at"] > stale_sec]:
        _PENDING.pop(k, None)
