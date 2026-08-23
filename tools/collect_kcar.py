#!/usr/bin/env python3.11
"""K카 상세 수집 (명령서 `ORDER_20260822_r515.md` 3-3 · 단계 10).

    python3.11 tools/collect_kcar.py --car EC61393706 [EC61377663 …]
    python3.11 tools/collect_kcar.py --file carcds.txt        한 줄에 하나
    python3.11 tools/collect_kcar.py --check EC61393706       재기만 한다 (저장 없음)
    python3.11 tools/collect_kcar.py --list [--detail N]     ★ 재고 목록 전량 → 저장

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
from parse.kcar.mapping import parse_detail, parse_list_item  # noqa: E402
from store.dictionary import collect_group_of, match_target_name  # noqa: E402
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


def fetch_stock(adapter: KcarAdapter) -> list:
    """재고 목록을 ★ 한 번에 받는다 (명령서 18-1).

    ★ `data.listCount` 가 ★ 총건수다.  ★ 쪽마다 더하지 않는다
    """
    req = adapter.stock_list_url()
    size, body = fetch(req.url, req.headers, req.timeout_sec)
    if not body:
        print(f"  ★ 목록을 못 받았다 ({size}B)")
        return []
    data = body.get("data") or {}
    rows = data.get("list") or []
    said = data.get("listCount")
    print(f"목록 — 사이트가 말한 총 {said}건 · 받은 {len(rows)}건 · {size:,}B")
    if said is not None and len(rows) != int(said):
        print(f"  ★ 어긋난다 — {int(said) - len(rows)}건을 못 받았다")
    return rows


def collect_list(adapter: KcarAdapter, cfg: dict, args: list) -> int:
    """목록 전량 저장 → ★ 우리 대상만 상세 (명령서 18-3)."""
    rows = fetch_stock(adapter)
    if not rows:
        return 1
    parsed, ours = [], []
    for one in rows:
        got = parse_list_item(one, SITE_CODE)
        if not got:
            continue
        # ★ 사이트가 ★ 꾸밈말·세대를 붙여 준다 — ★ 아는 이름이 들어 있으면 그것이다
        named = match_target_name(SITE_CODE, got.get("site_model_group"))
        if named:
            # ★ 우리가 아는 이름으로 ★ 적어 둔다 — ★ dict_enum 이 한 이름으로 모인다
            got["site_model_group"] = named
        parsed.append(got)
        if named and collect_group_of(SITE_CODE, named):
            ours.append(got)
    print(f"★ 우리 대상 — {len(ours)}건 / {len(parsed)}건")
    if "--dry" in args:
        print("★ --dry 라 저장하지 않았다")
        return 0

    from store.core import resolve_listing_id, split_pii, upsert_core
    from store.pii import load_key
    from store.raw import commit

    conn = open_db(os.path.join(ROOT, "carwatch.db"))
    at, key = _now(), load_key()
    for one in parsed:
        one["listing_id"] = resolve_listing_id(conn, SITE_CODE,
                                               one["source_id"], at)
        upsert_core(conn, split_pii(conn, one, SITE_CODE, key, at), at)
    commit(conn)
    print(f"★ 목록 저장 {len(parsed)}건 · site='{SITE_CODE}'")

    # ★ 상세는 ★ 우리 대상만 ★ 뒤에 받는다 (18-3 ③).  ★ 이미 받은 것은 건너뛴다
    limit = 0
    if "--detail" in args:
        i = args.index("--detail")
        limit = int(args[i + 1]) if i + 1 < len(args) and args[i + 1].isdigit() else 0
    done = {r[0] for r in conn.execute(
        "SELECT source_id FROM core_listing WHERE site=? AND detail_status='ok'",
        (SITE_CODE,))}
    todo = [o for o in ours if o["source_id"] not in done]
    if limit:
        todo = todo[:limit]
    print(f"★ 상세 — 받을 것 {len(todo)}건 (이미 받은 것 {len(done)}건은 건너뛴다)")
    got = {"정상": 0, "없는 매물": 0, "못 받음": 0}
    for one in todo:
        req = adapter.detail_urls(one["source_id"])[0]
        size, body = fetch(req.url, req.headers, req.timeout_sec)
        state = classify(size, body)
        got[state] = got.get(state, 0) + 1
        if state != "정상":
            time.sleep(float(cfg.get("interval_sec") or 1.5))
            continue
        deep = parse_detail(body, SITE_CODE, one["source_id"])
        if deep:
            deep["listing_id"] = one["listing_id"]
            deep["detail_status"] = "ok"
            upsert_core(conn, split_pii(conn, deep, SITE_CODE, key, at), at)
        time.sleep(float(cfg.get("interval_sec") or 1.5))
    commit(conn)
    print("★ 상세 — " + " · ".join(f"{k} {v}" for k, v in got.items()))
    n = conn.execute("SELECT COUNT(*) FROM core_listing WHERE site=?",
                     (SITE_CODE,)).fetchone()[0]
    print(f"★ 저장된 K카 매물 — {n}건")
    conn.close()
    # ★ 저장했으면 ★ 재판정을 함께 큐에 넣는다 (명령서 14-3 ④)
    from tools.daily_enqueue import enqueue_after_store
    enqueue_after_store(os.path.join(ROOT, "carwatch.db"), SITE_CODE, len(parsed))
    return 0


def main() -> int:
    args = sys.argv[1:]
    cfg = load_config(ROOT)
    adapter = KcarAdapter(cfg)

    if "--list" in args:
        return collect_list(adapter, cfg, args)

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

    from store.core import resolve_listing_id, split_pii, upsert_core
    from store.pii import load_key
    from store.raw import commit

    conn = open_db(os.path.join(ROOT, "carwatch.db"))
    at = _now()
    key = load_key()
    stored, empty = 0, 0
    for cd, body in ok_rows:
        # ★★ `data` 를 벗긴다 — ★ 안 벗기면 ★ 전건 NULL 이다 (명령서 6단계)
        deep = parse_detail(body, SITE_CODE, cd)
        if not deep:
            empty += 1
            continue
        deep["listing_id"] = resolve_listing_id(conn, SITE_CODE, cd, at)
        deep["detail_status"] = "ok"
        upsert_core(conn, split_pii(conn, deep, SITE_CODE, key, at), at)
        stored += 1
    commit(conn)
    print(f"★ 저장 {stored}건 · site='{SITE_CODE}'"
          + (f" · ★ 매핑이 빈 것 {empty}건" if empty else ""))
    print("★ 성능점검은 ★ 사진뿐이라 ★ 골격·외판 축은 ★ 안 채웠다 (④ · 규격 4장)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
