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

# ★★ 점검 경로 (`MULTISITE_MAPPING.md` 08-29 절 · 실측 08-30).
#   ★ `config/endpoints.json` 의 `kcar.paths` 에 아직 없다 — ★ 규격이 넣으면 그때 옮긴다.
#   ★ 개발측이 `docs/` 를 안 고친다 (규칙 2) — ★ 여기에 근거를 적어 둔다
INSP_PATH = "/bc/car-insp/photo/cm?i_sCarCd={source_id}"
from parse.kcar.mapping import (parse_detail, parse_list_item,  # noqa: E402
                                record_of)
from parse.target_rules import fill_target_key  # noqa: E402
from store.dictionary import collect_group_of, match_target_name  # noqa: E402
from store.raw import open_db  # noqa: E402

# ① ★ 없는 매물도 200 이다.  ★ 크기로 한 번 · carCd 로 한 번 가른다
MIN_BYTES = 10_000
# ② ★ 규격이 아는 사고 값 셋.  ★ 넷째가 나오면 멈춘다
KNOWN_ACCIDENT = ("무사고", "단순수리", "사고")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch(url: str, headers: dict, timeout: float,
          want_text: bool = False) -> tuple:
    """반환 (본문 bytes 길이, JSON 또는 None[, 원문 글자]).

    ★★ 08-28 — ★ `want_text` 를 붙였다.  ★ 재고 목록 봉투(887KB)를
      ★ ★ **그냥 버리고 있었다** — ★ P3(원문 무손실) 어긋남이다.
      ★ ★ 다시 만들지 않는다.  ★ 받은 글자를 ★ 그대로 남긴다
    """
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as f:   # noqa: S310
            raw = f.read()
    except OSError:
        return (0, None, None) if want_text else (0, None)
    try:
        text = raw.decode("utf-8")
        doc = json.loads(text)
    except (ValueError, UnicodeDecodeError):
        text, doc = None, None
    return (len(raw), doc, text) if want_text else (len(raw), doc)


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


def fetch_stock(adapter: KcarAdapter) -> tuple:
    """재고 목록을 ★ 한 번에 받는다 (명령서 18-1).

    ★ `data.listCount` 가 ★ 총건수다.  ★ 쪽마다 더하지 않는다
    ★ 반환 (줄 목록, 원문 글자, 부른 주소) — ★ 원문을 남기려면 글자가 있어야 한다
    """
    req = adapter.stock_list_url()
    size, body, text = fetch(req.url, req.headers, req.timeout_sec,
                             want_text=True)
    if not body:
        print(f"  ★ 목록을 못 받았다 ({size}B)")
        return [], None, req.url, False
    data = body.get("data") or {}
    rows = data.get("list") or []
    said = data.get("listCount")
    print(f"목록 — 사이트가 말한 총 {said}건 · 받은 {len(rows)}건 · {size:,}B")
    # ★★★★ 08-29 (개정 838) — ★ 「끝까지 받았나」.
    #   ★ 사이트가 말한 총계와 ★ 받은 수가 ★ 같을 때만 참이다.
    #   ★ 총계를 안 주면 ★ 끝을 모른다 — ★ 거짓이다 (반만 보고 gone 을 매기지 않는다)
    done = said is not None and len(rows) == int(said)
    if said is not None and len(rows) != int(said):
        print(f"  ★ 어긋난다 — {int(said) - len(rows)}건을 못 받았다")
    return rows, text, req.url, done


def collect_list(adapter: KcarAdapter, cfg: dict, args: list) -> int:
    """목록 전량 저장 → ★ 우리 대상만 상세 (명령서 18-3)."""
    rows, stock_body, stock_url, list_done = fetch_stock(adapter)
    if not rows:
        return 1
    parsed, ours = [], []
    unparsed = 0
    for one in rows:
        got = parse_list_item(one, SITE_CODE)
        if not got:
            # ★ 못 읽은 것은 ★ 「본 것」에 못 넣는다 — ★ 그 매물번호를 모른다.
            #   ★ 그러면 ★ 살아 있는데 목록에 없는 꼴이 되어 ★ gone 이 된다
            unparsed += 1
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

    from store.core import mark_gone, resolve_listing_id, split_pii, upsert_core
    from store.pii import load_key
    from store.raw import commit, save_site_raw

    conn = open_db(os.path.join(ROOT, "carwatch.db"))
    at, key = _now(), load_key()
    # ★★ 08-28 — ★ 받은 목록 봉투를 ★ **먼저 남긴다** (명령서 3-2 · P3).
    #   ★ 전에는 ★ 887KB 를 ★ 그냥 버렸다 — ★ `raw_response` 에 `stock_list` 가 0건이었다.
    #   ★ ★ 갈래를 넓히시면 ★ 이 봉투로 ★ 다시 판다.  ★ 다시 받을 일이 없다
    if stock_body:
        got = save_site_raw(conn, SITE_CODE, "stock_list", None,
                            stock_url, stock_body, at)
        print(f"★ 목록 원문을 남겼다 ({len(stock_body):,}자 · {got})")
    # ★★ 3-2 걸러 저장 (마스터 확정 08-25) — ★ 우리 대상만 ★ `core_listing` 에 넣는다.
    #   ★ K카는 ★ 목록이 `enc` 라 ★ 좁힐 길이 없다 — ★ 다 받되 ★ 걸러 넣는다
    #   ★ ★ 원문(`raw_response`)에는 남는다 — ★ 갈래를 넓히면 다시 판다
    keep = ours if "--all" not in args else parsed
    print(f"★ 저장할 것 {len(keep)}건 · ★ 안 넣는 것 {len(parsed) - len(keep)}건 "
          f"(원문은 남는다)")
    for one in keep:
        one["listing_id"] = resolve_listing_id(conn, SITE_CODE,
                                               one["source_id"], at)
        # ★ 넣기 직전에 ★ 차종을 붙인다 (마스터 지시 08-30) — ★ 안 붙이면 판정에 안 들어간다
        fill_target_key(SITE_CODE, one)
        upsert_core(conn, split_pii(conn, one, SITE_CODE, key, at), at)
    commit(conn)
    print(f"★ 목록 저장 {len(parsed)}건 · site='{SITE_CODE}'")
    # ★★★★★ 08-29 (ORDER r879 1b · `S46-117`) — ★ 팔린 것을 가른다.
    #   ★ 앞서는 ★ 상세를 다시 받아 「없는 매물」이 나올 때만 gone 이었다.
    #   ★ ★ 그런데 ★ `todo` 가 `detail_status='ok'` 를 빼므로
    #   ★ ★ **한 번 받은 매물은 다시 안 본다** — ★ 영영 gone 에 안 닿았다.
    #   ★ 목록에 없으면 팔린 것이다 — ★ 보배(`collect_bobaedream.py`) 꼴로 한다
    from store.raw import link_raws as raw_link_raws

    raw_link_raws(conn, SITE_CODE)
    # ★★★★★ 08-30 정정 — ★ **이 목록으로는 gone 을 못 매긴다.  ★ 껐다**
    #   ★ 08-29 에 켰다가 ★ **살아 있는 차 12대를 죽였다** (마스터 0a 지적).
    #   ★★ 실측 08-30 — ★ 08-29 에 gone 으로 매긴 19건을 ★ **하나씩 눌러 봤다** —
    #     ★ ★ **12건이 아직 살아 있었다** (`statCdNm` 「판매중」) · 7건만 정말 팔렸다.
    #   ★★★ 까닭 — ★ `stock_list` 는 ★ **전량이 아니다.**
    #     ★ `pageSize=1000` 으로 불러도 ★ 487건이고 ★ 사이트가 말한 총계도 487 이다 —
    #     ★ ★ **잘린 것이 아니라 ★ 이 창구가 담는 범위가 그것뿐이다.**
    #     ★ ★ 살아 있는 12건은 ★ `statCd`·`sellDcd` 어느 갈래로도 ★ 이 목록에 안 온다.
    #   ★ 「끝까지 받았나」가 참이어도 ★ **「목록이 전량인가」가 거짓**이면
    #     ★ ★ gone 을 매기면 안 된다 — ★ 반만 보고 매기면 산 차를 죽인다 (오판 161).
    #   ★ K카의 gone 은 ★ **상세를 눌러 「없는 매물」이 나올 때만** 매긴다 (아래).
    #     ★ ★ 그것은 사이트가 직접 「없다」고 답한 것이라 ★ 근거가 있다
    _got = {}
    del list_done, unparsed
    print("★ 목록으로는 gone 을 안 매긴다 — 이 창구가 전량이 아니다 "
          "(실측 08-30 · 살아 있는 12대를 죽였다).  상세가 「없는 매물」이라 할 때만 매긴다")

    # ★ 상세는 ★ 우리 대상만 ★ 뒤에 받는다 (18-3 ③).  ★ 이미 받은 것은 건너뛴다
    # ★★ `--all` 이면 ★ **527건 전부** 받는다 (가이드 지시 08-24 · 오판 98).
    #   ★ ★ 까닭 — ★ `cno`(차량번호)가 ★ **목록에 없고 상세에만 있다.**
    #     ★ `cno` 가 없으면 ★ `plate_hash` 가 없고 ★ 5a 짝짓기가 안 된다
    want = parsed if "--all" in args else ours
    limit = 0
    if "--detail" in args:
        i = args.index("--detail")
        limit = int(args[i + 1]) if i + 1 < len(args) and args[i + 1].isdigit() else 0
    done = {r[0] for r in conn.execute(
        "SELECT source_id FROM core_listing WHERE site=? AND detail_status='ok'",
        (SITE_CODE,))}
    todo = [o for o in want if o["source_id"] not in done]
    if limit:
        todo = todo[:limit]
    print(f"★ 상세 — 받을 것 {len(todo)}건 (이미 받은 것 {len(done)}건은 건너뛴다)")
    got = {"정상": 0, "없는 매물": 0, "못 받음": 0}
    gone = 0
    for one in todo:
        req = adapter.detail_urls(one["source_id"])[0]
        size, body = fetch(req.url, req.headers, req.timeout_sec)
        state = classify(size, body)
        got[state] = got.get(state, 0) + 1
        if state != "정상":
            # ★★ 「없는 매물」은 ★ **팔린 것**이다 (가이드 지시 08-24).
            #   ★ 지우지 않는다 — ★ `gone_at` 이 ★ 「얼마에 팔렸나」의 근거다
            if state == "없는 매물":
                mark_gone(conn, one["listing_id"], at)
                gone += 1
            time.sleep(float(cfg.get("interval_sec") or 1.5))
            continue
        # ★★ 원문을 ★ 먼저 남긴다 (명령서 3-2 필수) — ★ 「갈래를 넓히시면 다시 판다」.
        #   ★ K카 상세는 ★ JSON 이다 — ★ 글자로 되돌려 넣는다
        save_site_raw(conn, SITE_CODE, "detail", one["source_id"], req.url,
                      json.dumps(body, ensure_ascii=False), at)
        # ★★ 08-29 (개정 857) — ★ 곧바로 커밋한다.
        #   ★ 통신·`sleep` 이 ★ 트랜잭션 안에 들면 ★ 잠금 창이 분 단위가 된다
        #   (KB 실측 — 100건 × 1.2초 = 120초 · 잠금 38.4초 · locked 로 죽었다)
        commit(conn)
        deep = parse_detail(body, SITE_CODE, one["source_id"])
        if deep:
            deep["listing_id"] = one["listing_id"]
            deep["detail_status"] = "ok"
            # ★ 넣기 직전에 ★ 차종을 붙인다 (마스터 지시 08-30) — ★ 안 붙이면 판정에 안 들어간다
            fill_target_key(SITE_CODE, deep)
            upsert_core(conn, split_pii(conn, deep, SITE_CODE, key, at), at)
        # ★ 자기 전에 커밋한다 — ★ 넣기가 sleep 을 넘지 않게 (개정 857)
        commit(conn)
        time.sleep(float(cfg.get("interval_sec") or 1.5))
    commit(conn)
    print("★ 상세 — " + " · ".join(f"{k} {v}" for k, v in got.items())
          + (f"  ★ 팔린 것 {gone}건을 gone 으로" if gone else ""))

    # ★★★★★ 08-30 (마스터 지시 1 · `DEDUP_CROSS_SITE` 1장) — ★ 점검 경로로 `cno` 를 얻는다.
    #   ★★ 마스터 — 「★ 여섯 축은 못 채워도 ★ **`cno` 가 짝짓기 열쇠**다.
    #     ★ ★ 지금 같은 차 짝이 0건이고 ★ 그것이 이 도구의 심장이다」
    #   ★ 실측 08-30 — ★ `GET /bc/car-insp/photo/cm?i_sCarCd={id}` → 200 · 462B ·
    #     ★ ★ `inspDetail.cno` 에 번호판이 있다.  ★ 부위별 값은 없다 (사진뿐)
    #   ★★ **번호판 원문을 `core_listing` 에 안 넣는다** (마스터 지시 · STEP 35) —
    #     ★ `_pii_plate_no` 로 넘기면 ★ `split_pii` 가 ★ `plate_hash` 만 남기고
    #     ★ ★ 원문은 `core_pii` 로 간다
    need_plate = [o for o in ours
                  if not conn.execute(
                      "SELECT plate_hash FROM core_listing"
                      " WHERE site=? AND source_id=?",
                      (SITE_CODE, o["source_id"])).fetchone()[0]]
    print(f"★ 점검 경로로 번호판 — 받을 것 {len(need_plate)}건 "
          f"(우리 대상 {len(ours)}건 중 · 이미 있는 것은 안 받는다)")
    ins = {"받음": 0, "번호판 없음": 0, "못 받음": 0}
    for one in need_plate:
        url = (cfg["base_url"] + INSP_PATH.format(source_id=one["source_id"]))
        size, body = fetch(url, adapter.headers(), float(cfg.get("timeout_sec") or 30))
        del size
        if not isinstance(body, dict):
            ins["못 받음"] += 1
            time.sleep(float(cfg.get("interval_sec") or 1.5))
            continue
        save_site_raw(conn, SITE_CODE, "inspection", one["source_id"], url,
                      json.dumps(body, ensure_ascii=False), at,
                      listing_id=one.get("listing_id"))
        commit(conn)
        det = ((body.get("data") or {}).get("inspDetail") or {})
        plate = (det.get("cno") or "").strip()
        if not plate:
            ins["번호판 없음"] += 1
            time.sleep(float(cfg.get("interval_sec") or 1.5))
            continue
        # ★ 이 매물의 다른 칸을 안 건드린다 — ★ 번호판만 얹는다
        row = {"site": SITE_CODE, "source_id": one["source_id"],
               "listing_id": one.get("listing_id"),
               "_pii_plate_no": plate,
               "inspection_status": "ok"}
        upsert_core(conn, split_pii(conn, row, SITE_CODE, key, at), at)
        commit(conn)
        ins["받음"] += 1
        time.sleep(float(cfg.get("interval_sec") or 1.5))
    print("★ 점검 경로 — " + " · ".join(f"{k} {v}" for k, v in ins.items()))
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

    from store.core import (resolve_listing_id, split_pii, upsert_child,
                            upsert_core)
    from store.pii import load_key
    from store.raw import commit

    conn = open_db(os.path.join(ROOT, "carwatch.db"))
    at = _now()
    key = load_key()
    stored, empty, records = 0, 0, 0
    for cd, body in ok_rows:
        # ★★ `data` 를 벗긴다 — ★ 안 벗기면 ★ 전건 NULL 이다 (명령서 6단계)
        deep = parse_detail(body, SITE_CODE, cd)
        if not deep:
            empty += 1
            continue
        lid = resolve_listing_id(conn, SITE_CODE, cd, at)
        deep["listing_id"] = lid
        deep["detail_status"] = "ok"
        # ★ 넣기 직전에 ★ 차종을 붙인다 (마스터 지시 08-30) — ★ 안 붙이면 판정에 안 들어간다
        fill_target_key(SITE_CODE, deep)
        upsert_core(conn, split_pii(conn, deep, SITE_CODE, key, at), at)
        # ★★★ 08-28 — ★ 이력은 ★ `core_record` 의 칸이다 (규격 3-2·3-3).
        #   ★ 전에는 ★ `core_listing` 만 썼다 — ★ 그래서 상세를 받아도
        #     ★ ★ `state.accident` 51점이 ★ 0/34 로 비어 있었다 (실측 08-28).
        #   ★ 엔카는 5,603행인데 ★ K카는 0행이었다
        rec = record_of(body, SITE_CODE)
        if rec:
            rec["listing_id"] = lid
            rec["collected_at"] = at
            upsert_child(conn, "core_record", rec, "p1", at)
            records += 1
        stored += 1
    commit(conn)
    print(f"★ 저장 {stored}건 · ★ 이력(core_record) {records}건 · site='{SITE_CODE}'"
          + (f" · ★ 매핑이 빈 것 {empty}건" if empty else ""))
    print("★ 성능점검은 ★ 사진뿐이라 ★ 골격·외판 축은 ★ 안 채웠다 (④ · 규격 4장)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
