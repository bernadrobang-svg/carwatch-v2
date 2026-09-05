# -*- coding: utf-8 -*-
"""1번 — ★ **막힌 응답도 원문으로 남긴다** (지시 r1174 · `S46-278` · `STEP 53-⑤`).

★★★ 마스터 — 「★ **캡차를 하더라도 ★ 받는 건 받아야 하는데 ★ 원문 파일 저장을 안 하나?**」
★ 규격 `STEP 53-⑤` — 「★ **실패 응답도 원문이다**」.

★★ 실측 09-05 — ★ 여덟 수집기가 ★ 다 같은 무늬였다 —
  ★ `_get()` 이 ★ 실패하면 ★ **몸통을 버리고 `None`** 을 낸다 ·
  ★ ★ 부르는 쪽은 ★ 원문 없이 ★ `break`·`continue` 한다.
  ★ ★ ★ 그래서 ★ 「언제부터 · 어떻게 막혔나」를 ★ **뒤에 못 본다** —
    ★ ★ ★ ★ 손으로 두드려야만 알 수 있었다.

★ 여기 한 자리에 둔다 — ★ 여덟 곳이 ★ 같은 것을 쓴다.
★★ **값으로 삼지 않는다** (금지 12) — ★ `status="blocked"` 로 ★ **자취**를 남길 뿐이다.
  ★ ★ 파싱은 안 한다 — ★ 지시 1번이 ★ 「원문만 남긴다」다
"""
from __future__ import annotations

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BLOCKED = "blocked"


def keep_blocked(site: str, endpoint: str, source_id, url: str, body,
                 page: int | None = None, http_code: int = 0,
                 root: str = ROOT) -> str | None:
    """★ 막힌 응답 하나를 ★ 원문 파일로 남긴다.  ★ 돌려줌 ★ 쓴 경로 · 또는 None.

    ★ 몸통이 없으면 ★ 아무것도 안 쓴다 — ★ 「없음」으로 저장하지 않는다 (금지 12).
    ★ 저장이 실패해도 ★ **수집을 죽이지 않는다** — ★ 원문 남기기가 판을 멈추면 안 된다
    """
    if not body:
        return None
    try:
        from store.rawfile import save

        if isinstance(body, (bytes, bytearray)):
            body = body.decode("utf-8", "replace")
        return save(site, endpoint, source_id, url or "", body,
                    status=BLOCKED, http_code=http_code or 0,
                    page=page, root=root)
    except Exception:                                        # noqa: BLE001
        return None
