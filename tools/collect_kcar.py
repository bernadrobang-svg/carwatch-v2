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
import urllib.error
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from adapters.kcar import SITE_CODE, KcarAdapter, load_config  # noqa: E402

# ★★ 점검 경로 (`MULTISITE_MAPPING.md` 08-29 절 · 실측 08-30).
#   ★ `config/endpoints.json` 의 `kcar.paths` 에 아직 없다 — ★ 규격이 넣으면 그때 옮긴다.
#   ★ 개발측이 `docs/` 를 안 고친다 (규칙 2) — ★ 여기에 근거를 적어 둔다
# ★★★★★ 이 수집기는 ★ **팔린 차를 목록으로 안 거른다** (마스터 지시 08-30 · S46-117).
#   ★ 낱말 `SWEEP_OFF` 를 ★ 검사가 본다 — ★ 「안 거른다」와 「못 거른다」를 가른다
SWEEP_OFF = (
    "08-30 — `stock_list` 는 전량이 아니다 (487건뿐 · 총계도 487)."
    "  목록에 없다고 죽여 살아 있는 차 12대를 죽였다.  상세가"
    " 「없는 매물」이라 답할 때만 죽인다")

INSP_PATH = "/bc/car-insp/photo/cm?i_sCarCd={source_id}"
from parse.kcar.mapping import (parse_list_item,  # noqa: E402
                                )
from store.dictionary import collect_group_of, match_target_name  # noqa: E402
# ★★★★★ 09-01 마스터 지시 — ★ 받기는 ★ **파일만** 쓴다 (`S46-204`)
from store.rawfile import save as save_file  # noqa: E402

# ① ★ 없는 매물도 200 이다.  ★ 크기로 한 번 · carCd 로 한 번 가른다
MIN_BYTES = 10_000
# ② ★ 규격이 아는 사고 값 셋.  ★ 넷째가 나오면 멈춘다
KNOWN_ACCIDENT = ("무사고", "단순수리", "사고")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch(url: str, headers: dict, timeout: float,
          want_text: bool = False, endpoint: str | None = None,
          source_id=None, page: int | None = None) -> tuple:
    """반환 (본문 bytes 길이, JSON 또는 None[, 원문 글자]).

    ★★ 08-28 — ★ `want_text` 를 붙였다.  ★ 재고 목록 봉투(887KB)를
      ★ ★ **그냥 버리고 있었다** — ★ P3(원문 무손실) 어긋남이다.
      ★ ★ 다시 만들지 않는다.  ★ 받은 글자를 ★ 그대로 남긴다
    """
    from collect.rawfetch import keep_blocked

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as f:   # noqa: S310
            raw = f.read()
    except urllib.error.HTTPError as e:
        # ★★★★★ 09-05 (지시 1번 · `S46-278` · `STEP 53-⑤`) —
        #   ★ **막힌 응답도 원문이다.**  ★ 전에는 몸통을 버렸다
        if endpoint:
            try:
                keep_blocked(SITE_CODE, endpoint, source_id, url, e.read(),
                             page=page, http_code=e.code, root=ROOT)
            except OSError:
                pass
        return (0, None, None) if want_text else (0, None)
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
                             endpoint="stock_list",
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

    # ★★★★★ 09-01 마스터 지시 — ★ **받기 걸음은 파일만 쓴다.  ★ DB 를 안 연다.**
    #   ★ 넣기는 ★ `python3.11 tools/load_raw.py kcar --write` 가 한다
    at = _now()
    # ★★ 08-28 — ★ 받은 목록 봉투를 ★ **먼저 남긴다** (명령서 3-2 · P3)
    if stock_body:
        save_file(SITE_CODE, "stock_list", None, stock_url, stock_body, at,
                  root=ROOT)
        print(f"★ 목록 원문을 남겼다 ({len(stock_body):,}자)")
    # ★★ 3-2 걸러 저장은 ★ **넣기 걸음**이 한다 — ★ 받기는 다 남길 뿐이다
    for one in parsed:
        save_file(SITE_CODE, "list", one["source_id"], stock_url or "",
                  json.dumps(one, ensure_ascii=False), at, root=ROOT)
    print(f"★ 목록 {len(parsed)}건을 파일로 남겼다 "
          f"(우리 대상으로 보이는 것 {len(ours)}건)")
    # ★★★★★ 08-30 정정 — ★ 「목록에 없으면 죽인다」는 ★ **여기서 안 한다.**
    #   ★ 08-29 에 켰다가 ★ **살아 있는 차 12대를 죽였다** (마스터 0a 지적).
    #   ★ 그 자리는 ★ `tools/list_diff_check.py` 다 — ★ 상세로 확인한 뒤에 죽인다
    print(f"★ 팔린 차를 목록으로 안 거른다 — {SWEEP_OFF}")
    print(f"★ 넣기 — python3.11 tools/load_raw.py {SITE_CODE} --write")
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
        size, body = fetch(req.url, req.headers, req.timeout_sec,
                           endpoint="detail", source_id=cd)
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

    # ★★★★★ 09-01 마스터 지시 — ★ **받기 걸음은 파일만 쓴다.  ★ DB 를 안 연다.**
    #   ★ 펼치기(`parse_detail`·`record_of`)는 ★ 넣기 걸음이 한다
    at = _now()
    for cd, body in ok_rows:
        save_file(SITE_CODE, "detail", cd, "",
                  body if isinstance(body, str)
                  else json.dumps(body, ensure_ascii=False), at, root=ROOT)
    print(f"★ 상세 {len(ok_rows)}건을 파일로 남겼다 — "
          f"raw/{SITE_CODE}/detail/{at[:10]}/")
    print("★ 성능점검은 ★ 사진뿐이라 ★ 골격·외판 축은 ★ 안 채웠다 (④ · 규격 4장)")
    print(f"★ 넣기 — python3.11 tools/load_raw.py {SITE_CODE} --write")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
