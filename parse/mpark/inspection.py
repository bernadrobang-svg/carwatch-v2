# -*- coding: utf-8 -*-
"""m-park 성능점검 창구 → 우리 꼴 (로드맵 차례 4 · KB 점검표).

★★★★★ 09-03 — ★ **창구를 브라우저로 잡았다.  ★ 지어내지 않았다.**
  ★ 앞 회차에 ★ 「주소가 원문 어디에도 없다」고 적고 ★ 멈췄다 (명령서 금지 —
  ★ ★ 「호출부에 없는 주소를 지어내는 것」).  ★ 이번에 ★ 그 쪽을 열어 ★ 실제 호출을 봤다.

    GET https://api.m-park.co.kr/home/api/v1/wb/searchmycar/
        carcheckdetailinfo/get?checkNo={번호}
    ★ 200 · 2,634B · JSON · ★ 칸 103개 [실측 09-03]
    ★ 헤더 — User-Agent · Referer 만

★★ 여기서 읽는 것은 ★ **누유뿐**이다 (`state.leak` 15점).
  ★ ★ 칸 이름이 ★ 뜻을 그대로 말한다 — `atOilLeak` · `breakOilLeak` · `etcGasLeak` …
  ★ ★ ★ 값도 ★ 우리말 그대로다 — 「없음」·「누유」·「미세누유」
금지  ★ `carCheckGbn1`(8자리) · `carCheckGbn2`(11자리)를 ★ **짐작으로 옮기는 것**.
      ★ ★ 외판 8부위·골격 11부위와 ★ 수는 맞지만 ★ **자리 차례를 못 확인했다**.
      ★ ★ ★ 규격이 자리 표를 주면 ★ 그때 연다 (`v332` 물음 12)
"""
from __future__ import annotations

BASE = ("https://api.m-park.co.kr/home/api/v1/wb/searchmycar/"
        "carcheckdetailinfo/get?checkNo=")
HEADERS = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"),
           "Referer": "https://www.m-park.co.kr/"}

# ★ 누유를 말하는 칸 — ★ 이름이 뜻이다 [실측 09-03 · 칸 103개 가운데]
LEAK_FIELDS = (
    ("atOilLeak", "자동변속기 오일"),
    ("mtOilLeak", "수동변속기 오일"),
    ("steeringOilVolumeLeak", "동력조향 오일"),
    ("breakOilLeak", "브레이크 오일"),
    ("brakeMasterCylinderOilLeak", "브레이크 마스터실린더"),
    ("etcGasLeak", "냉각수·가스"),
    ("oilPan", "오일팬"),
)


def check_no(url: str | None) -> str | None:
    """점검표 주소 → `checkNo`.  ★ 못 읽으면 ★ `None` (지어내지 않는다)."""
    import re

    got = re.search(r"/performance/(\d+)", str(url or ""))
    return got.group(1) if got else None


def inners(body) -> list | None:
    """m-park 응답 → 엔카 `inspection_inner_json` 과 **같은 꼴**.

    ★ 같은 꼴로 만들면 ★ `leak_state()` 가 ★ 그대로 읽는다 —
      ★ ★ 축을 안 고친다.  ★ 판정 규칙은 한 자리에만 있다
    ★ 값이 빈 칸은 ★ **안 낸다** — ★ 「없음」으로 지어내지 않는다 (금지 12)
    ★ 응답이 우리가 아는 꼴이 아니면 ★ `None` — ★ 빈 목록(「이상 없음」)과 다르다
    """
    import json

    if isinstance(body, (bytes, bytearray)):
        body = body.decode("utf-8", "replace")
    try:
        got = json.loads(body) if isinstance(body, str) else body
    except (ValueError, TypeError):
        return None
    if not isinstance(got, dict):
        return None
    rows = got.get("data")
    if not isinstance(rows, list) or not rows:
        return None
    one = rows[0]
    if not isinstance(one, dict):
        return None
    seen = False
    out = []
    for key, name in LEAK_FIELDS:
        if key not in one:
            continue
        seen = True
        val = str(one.get(key) or "").strip()
        if not val:
            continue          # ★ 안 준 칸 — ★ 「없음」으로 안 만든다
        out.append({"type": {"code": key, "title": name},
                    "statusType": {"code": val, "title": val},
                    "children": []})
    return out if seen else None
