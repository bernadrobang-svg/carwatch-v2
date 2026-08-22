#!/usr/bin/env python3.11
"""K카 상세 수집 (명령서 `ORDER_20260822_r515.md` 3-3 · 단계 10).

    python3.11 tools/collect_kcar.py --car EC61393706 [EC61377663 …]
    python3.11 tools/collect_kcar.py --file carcds.txt        한 줄에 하나
    python3.11 tools/collect_kcar.py --check EC61393706       재기만 한다 (저장 없음)

지시서   `docs/KCAR_API.md` · 명령서 3-3
값규칙   ★ 반드시 지킬 것 넷 (명령서 3-3)
        ① ★ 없는 매물도 200 을 준다 (3,186B).  ★ `data.rvo.carCd` 가 있는지로 가른다
          ★ 10,000B 미만은 ★ 「없음」이 아니라 ★ 「못 받음」이다
        ② ★ 사고 판정은 ★ `acdtHistComnt` — 무사고 · 단순수리 · 사고
          ★ 넷째 값이 나오면 ★ 멈추고 알린다.  ★ 스스로 정하지 않는다
        ③ ★ `npriceFullType` 은 ★ 신차가가 아니다 — ★ 판매가다.  ★ 신차가로 쓰지 않는다
        ④ ★ 성능점검은 사진뿐이다.  ★ 사진을 안 읽고 감점을 주지 않는다
금지     ★ 화면 경로(`/bc/detail/carInfoDtl?` 등)를 두드리는 것 — ★ robots 금지다
금지     ★ 목록 요청의 `enc` 를 푸는 것.  ★ 우회를 만드는 것
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from adapters.kcar import SITE_CODE, KcarAdapter, load_config  # noqa: E402
from store.raw import open_db  # noqa: E402

# ① ★ 없는 매물도 200 이다.  ★ 크기로 한 번 · carCd 로 한 번 가른다
MIN_BYTES = 10_000
# ② ★ 규격이 아는 사고 값 셋.  ★ 넷째가 나오면 멈춘다
KNOWN_ACCIDENT = ("무사고", "단순수리", "사고")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch(url: str, headers: dict, timeout: float) -> tuple:
    """반환 (본문 bytes 길이, JSON 또는 None)."""
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as f:   # noqa: S310
            raw = f.read()
    except OSError:
        return 0, None
    try:
        return len(raw), json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return len(raw), None


def classify(size: int, body: dict | None) -> str:
    """★ ① — 「없다」와 「못 받았다」를 가른다.

    ★ 200 이라고 다 받은 것이 아니다.  ★ KB 봇페이지 2,759B 와 같은 함정이다
    """
    if body is None:
        return "못 받음"
    rvo = ((body.get("data") or {}).get("rvo") or {})
    if not rvo.get("carCd"):
        return "없는 매물"          # ★ 「없다」를 사이트가 200 으로 말한 것
    if size < MIN_BYTES:
        return "못 받음"            # ★ carCd 는 있는데 짧다 — 온전치 않다
    return "정상"


def accident_of(body: dict) -> str | None:
    """★ ② — `acdtHistComnt` 하나로 가른다.

    ★ `smplReprYn` 으로 가르지 않는다 (단순수리와 사고가 둘 다 2 다)
    ★ `acdtHistYn` 으로 가르지 않는다 (표본 12건 전부 1 이다)
    """
    return ((body.get("data") or {}).get("rvo") or {}).get("acdtHistComnt")


def main() -> int:
    args = sys.argv[1:]
    cfg = load_config(ROOT)
    adapter = KcarAdapter(cfg)

    cars: list = []
    if "--car" in args:
        cars = [a for a in args[args.index("--car") + 1:]
                if not a.startswith("--")]
    if "--check" in args:
        cars = [a for a in args[args.index("--check") + 1:]
                if not a.startswith("--")]
    if "--file" in args:
        path = args[args.index("--file") + 1]
        with open(path, encoding="utf-8") as f:
            cars = [ln.strip() for ln in f if ln.strip()]
    if not cars:
        print("★ carCd 를 주어야 한다 — ★ 목록은 못 만든다 (§아래)")
        print("  목록 POST /bc/search/list/drct 는 ★ 요청 본문이 암호화(enc)돼 있다")
        print("  ★ 명령서 금지 — 「enc 를 풀지 마라 · 우회를 만들지 마라」")
        print("  ★ 빈 본문으로 부르면 500 이다 (실측 08-23)")
        return 1

    seen: dict = {"정상": 0, "없는 매물": 0, "못 받음": 0}
    accidents: dict = {}
    unknown_accident: list = []
    ok_rows: list = []
    for cd in cars:
        req = adapter.detail_urls(cd)[0]
        size, body = fetch(req.url, req.headers, req.timeout_sec)
        state = classify(size, body)
        seen[state] += 1
        print(f"  {cd:14} {size:>8}B  {state}")
        if state != "정상":
            continue
        got = accident_of(body)
        accidents[got] = accidents.get(got, 0) + 1
        if got not in KNOWN_ACCIDENT:
            unknown_accident.append((cd, got))
        ok_rows.append((cd, body))
        time.sleep(float(cfg.get("interval_sec") or 1.5))

    print("★ 결과 — " + " · ".join(f"{k} {v}" for k, v in seen.items()))
    if accidents:
        print("★ acdtHistComnt — " + " · ".join(
            f"{k} {v}" for k, v in accidents.items()))
    if unknown_accident:
        # ★ ② — 넷째 값이 나오면 ★ 멈추고 알린다.  ★ 스스로 정하지 않는다
        print("★★ 규격에 없는 사고 값이 나왔다 — ★ 멈춘다.  ★ 가이드에 알린다")
        for cd, got in unknown_accident:
            print(f"    {cd} → {got!r}")
        return 2

    if "--check" in args:
        print("★ --check 라 저장하지 않았다")
        return 0

    from store.core import resolve_listing_id
    from store.raw import commit

    conn = open_db(os.path.join(ROOT, "carwatch.db"))
    at = _now()
    for cd, _body in ok_rows:
        resolve_listing_id(conn, SITE_CODE, cd, at)
    commit(conn)
    print(f"★ 매물번호 {len(ok_rows)}건 · site='{SITE_CODE}'")
    print("★ 27축 매핑은 아직이다 — ★ 성능점검이 사진뿐이라 4-1 표를 붙여야 한다 (④)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
