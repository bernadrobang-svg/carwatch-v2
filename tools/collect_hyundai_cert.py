#!/usr/bin/env python3.11
"""현대·제네시스 인증중고차 목록 수집 (명령서 `ORDER_20260822_r515.md` 3장 · 단계 11).

    python3.11 tools/collect_hyundai_cert.py --count       건수만 (조건 없이)
    python3.11 tools/collect_hyundai_cert.py [--dry]       목록을 끝까지 받아 저장
    python3.11 tools/collect_hyundai_cert.py --detail [N]  ★ 상세까지 받는다 (N건만)

지시서   `docs/HYUNDAI_CERTIFIED_API.md`
근거     ★ robots 가 ★ 금지 경로를 하나도 두지 않았다 (Allow: /)
        ★ 인증·토큰·암호화 ★ 없다.  `tmnlId` 는 ★ 빈 문자열이어도 된다 (실측)
값규칙   ★ 목록 응답은 ★ HTML 조각이다.  매물번호는 `data-favContsNo` 에 있다
        ★ `data-id` 가 ★ 아니다 — 개정 480 이 잘못 적었고 485 가 고쳤다
        ★ 차종이 안 걸리면 ★ 「차종 미정」으로 두고 ★ 버리지 않는다
금지     ★ 못 받은 것을 「없음」으로 저장하는 것
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from parse.hyundai_cert.mapping import (  # noqa: E402
    cards,
    parse_card,
    parse_detail_all,
)
from parse.target_rules import target_by_rules  # noqa: E402
from store.raw import link_raws as raw_link_raws  # noqa: E402
from store.raw import open_db  # noqa: E402

# ★★★★★ 이 수집기는 ★ **팔린 차를 목록으로 안 거른다** (마스터 지시 08-30 · S46-117).
#   ★ 낱말 `SWEEP_OFF` 를 ★ 검사가 본다 — ★ 「안 거른다」와 「못 거른다」를 가른다
SWEEP_OFF = (
    "08-29 — 목록에 없다고 죽이면 살아 있는 차를 죽인다"
    " (11-store/a-key 08-29 절).  상세로 확인한 뒤 죽이는 꼴로 바꾼 뒤 다시 켠다")

SITE_CODE = "hyundai_cert"
BASE = "https://certified.hyundai.com"
LIST_PATH = "/m/search/results/selling"
COUNT_PATH = "/api/search/vehicle/count/selling?srchType=srchFilter"
DETAIL_PATH = "/m/goods/goodsDetail.do?goodsNo={goods_no}"
ROWS = 100
MAX_PAGES = 60
# ★ 목록에 연료가 없어 ★ 상세로 채울 최대 건수 (2d-1).  ★ 실측 08-29 는 5건이다.
#   ★ 이보다 많으면 ★ 목록 파싱이 바뀐 것이다 — ★ 조용히 수백 번 부르지 않는다
FUEL_FILL_MAX = 40
INTERVAL = 1.0

# ★ 매물번호 — 영문 3 + 숫자 12 (개정 485 정정)
RE_GOODS = re.compile(r'data-favContsNo="([A-Z]{3}\d{12})"')

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Linux; Android 14; SM-S928N) "
                   "AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36"),
    "Content-Type": "application/json",
    "Referer": f"{BASE}/m/search/vehicle?srchType=srchFilter",
    "X-Requested-With": "XMLHttpRequest",
}

# ★ 브라우저가 보내는 본문 그대로 (HYUNDAI_CERTIFIED_API 5장)
BODY = {
    "type": None, "sortType": "popularity", "srchType": "srchFilter",
    "recentYn": "N", "tmnlId": "", "mbrNo": None, "siteNo": None,
    "saleCorpCd": None, "rowsPerPage": ROWS, "pageIdx": 1,
    "startNo": None, "listCnt": None, "searchWord": None,
    "lowPrice": None, "highPrice": None, "lowMileage": None,
    "highMileage": None, "lowModelYear": 2017, "highModelYear": None,
    "sdStatCd": None,
}


def target_of(parsed: dict) -> str | None:
    """사이트 차종 → 우리 차종 키.

    ★★ 개정 540 — ★ 쓰는 자리는 `config/dictionaries/target_map.json` 하나다.
      ★ 전에는 sites.json 에도 같은 표가 있었다 — ★ 두 곳이면 어긋난다
    ★ 표에 없으면 ★ None 이다 — 「차종 미정」이고 ★ 버리지 않는다
    ★★ 갈래(2.5T·LPG…)는 ★ `targets.json` 이 고른다 — ★ 새 규칙을 만들지 않는다
       (HYUNDAI_CERTIFIED_API 2d).  ★ 제목에 차종·연료·배기량이 다 있어
       ★ 상세가 없어도 갈린다 — ★ 전수 1,113건에 걸어 ★ 170건이 붙는다
    """
    got = target_by_rules(
        SITE_CODE, parsed.get("site_model_group"), parsed.get("fuel_raw"),
        parsed.get("site_model"), parsed.get("displacement_cc"))
    return got.target_key if got else None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _post(url: str, payload: dict) -> str | None:
    data = json.dumps(payload).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=data, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as f:    # noqa: S310
            return f.read().decode("utf-8", "replace")
    except OSError:
        return None


def _get(url: str) -> str | None:
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": HEADERS["User-Agent"],
                          "Referer": BASE + "/"})
        with urllib.request.urlopen(req, timeout=30) as f:    # noqa: S310
            return f.read().decode("utf-8", "replace")
    except OSError:
        return None


def fetch_detail(goods_no: str) -> tuple | None:
    """상세 하나 → (core_listing 몫, core_record 몫, 원문).

    ★ 짧으면 ★ 「못 받음」이다 — ★ 「없음」으로 내려가지 않는다
    돌려줌  (core_listing 몫, core_record 몫, ★ 원문 글자) 또는 None
    """
    body = _get(BASE + DETAIL_PATH.format(goods_no=goods_no))
    got = parse_detail_all(body or "", SITE_CODE, goods_no)
    # ★★ 원문도 함께 돌려준다 — ★ 부르는 쪽이 `raw_response` 에 남긴다
    #   (명령서 3-2 필수 「갈래를 넓히시면 다시 판다」)
    return None if got is None else (got[0], got[1], body)


def load_filters(root: str = ROOT) -> list:
    """★ 좁히는 조건 — ★ config 가 정본이다 (HYUNDAI_CERTIFIED_API 2e).

    ★ 차종군 코드를 ★ 코드에 박지 않는다 (S14 · 금지 6)
    """
    # ★★ 08-25 — ★ 좁히는 코드는 ★ `targets.json` 의 `site_query` **하나**가 정본이다
    #   (명령서 3-1 · 「코드는 각 사이트 규격에 있다.  targets.json 으로 옮겨라」).
    #   ★ ★ 전에는 ★ `sites.json` 의 `collect_filters` 에 따로 있어 ★ 두 곳이 갈렸다
    with open(os.path.join(root, "config", "targets.json"), encoding="utf-8") as f:
        rows = json.load(f)
    got, seen = [], set()
    for key, one in rows.items():
        if key.startswith("_") or not isinstance(one, dict):
            continue
        q = (one.get("site_query") or {}).get(SITE_CODE)
        if not isinstance(q, dict):
            continue
        # ★ 같은 부름을 두 번 하지 않는다 (G70_20T · G70_25T 가 같다)
        pick = {k: q[k] for k in ("mdlGrpList", "fuelList") if q.get(k)}
        mark = tuple(sorted(pick.items()))
        if not pick or mark in seen:
            continue
        seen.add(mark)
        got.append({**{k: [v] for k, v in pick.items()}, "for": key})
    if got:
        return got
    # ★ 옛 자리 — ★ targets.json 이 비면 그때만 본다
    with open(os.path.join(root, "config", "sites.json"), encoding="utf-8") as f:
        old = (json.load(f).get(SITE_CODE) or {}).get("collect_filters") or {}
    return old.get("groups") or []


def total_count(params: str = "") -> int | None:
    """★ 조건을 주면 그 조건의 건수다.  ★ 안 주면 전체다."""
    try:
        url = BASE + COUNT_PATH + (("&" + params) if params else "")
        req = urllib.request.Request(url,
                                     headers={"User-Agent": HEADERS["User-Agent"]})
        with urllib.request.urlopen(req, timeout=20) as f:    # noqa: S310
            got = json.loads(f.read().decode("utf-8"))
        return int(got.get("body") or 0)
    except (OSError, ValueError):
        return None


def walk(extra: dict | None = None, seen: set | None = None) -> tuple:
    """목록을 끝까지 받는다.  ★ pageIdx 로 쪽을 넘긴다.

    ★ 카드까지 파싱해서 돌려준다 — ★ 매물번호만 넣으면 껍데기가 된다
    ★ `extra` 가 ★ 차종군 조건이다 (2e).  ★ 없으면 전량이다
    """
    seen, rows, pages = (set() if seen is None else seen), [], 0
    base = dict(BODY, **(extra or {}))
    # ★★★ 08-29 (개정 838) — ★ 「끝까지 받았나」를 함께 돌려준다.
    #   ★ 새 카드가 없어 멈췄을 때만 참이다 — ★ 못 받았거나(body None) ·
    #     ★ MAX_PAGES 를 다 쓴 것은 ★ 끝이 아니다
    done = False
    for page in range(1, MAX_PAGES + 1):
        body = _post(BASE + LIST_PATH, dict(base, pageIdx=page))
        pages = page
        if body is None:
            print(f"  {page}쪽 — ★ 못 받았다.  ★ 저장하지 않는다")
            break
        fresh = 0
        for chunk in cards(body):
            got = parse_card(chunk, SITE_CODE)
            if got and got["source_id"] not in seen:
                seen.add(got["source_id"])
                rows.append(got)
                fresh += 1
        if not fresh:
            done = True                 # ★ 새 카드가 없다 — ★ 끝까지 받았다
            break
        time.sleep(INTERVAL)
    return rows, pages, done


def main() -> int:
    args = sys.argv[1:]
    said = total_count()
    print(f"사이트가 말한 건수 — {said if said is not None else '못 받았다'}")
    if "--count" in args:
        return 0

    groups = load_filters()
    if "--all" in args or not groups:
        if not groups:
            print("★ config 에 collect_filters 가 없다 — ★ 전량을 받는다")
        ids, pages, _d = walk()
        done_groups = [(_d, {o["source_id"] for o in ids})]
        print(f"목록 {pages}쪽 · 매물 {len(ids):,}건")
        if said and len(ids) != said:
            print(f"  ★ 어긋난다 — 사이트 {said} vs 받은 {len(ids)}")
    else:
        # ★★ 차종군마다 ★ 따로 부른다 — ★ 여섯 번이다 (2e).
        #   ★ 한 번에 부르면 ★ fuelList 가 ★ 전체에 걸려 389건이 온다 (규격 실측)
        ids, pages, seen = [], 0, set()
        # ★★★ 08-29 (개정 838) — ★ 차종군마다 ★ 「끝까지 받았나」를 들고 간다
        done_groups: list = []
        print(f"★ 좁혀 받는다 — 차종군 {len(groups)}개 (전량 {said} 중)")
        for g in groups:
            cond = {k: g[k] for k in ("mdlGrpList", "fuelList") if g.get(k)}
            q = "&".join(f"{k}={v}" for k in cond for v in cond[k])
            said_n = total_count(q)
            got, pg, _d = walk(cond, seen)
            done_groups.append((_d, {o["source_id"] for o in got}))
            for one in got:
                # ★ 제목에 연료 낱말이 없는 것은 ★ 전동화 전용 차종군이다.
                #   ★ 우리가 그 부름에서 달라고 한 연료를 쓴다 — ★ 짐작이 아니다
                if not one.get("fuel_raw") and g.get("fuel"):
                    one["fuel_raw"] = g["fuel"]
            pages += pg
            ids.extend(got)
            # ★★★★ 08-30 — ★ `expect` 가 **없을 때**도 「규격과 다르다」를 냈다.
            #   ★ 묶음은 ★ `targets.json` 의 `site_query` 에서 온다 (`load_filters`) —
            #   ★ ★ 거기에는 `expect` 가 없다.  ★ 옛 자리(`config/sites.json`)에만 있었다.
            #   ★ ★ 그래서 ★ **견줄 근거가 없는데 「다르다」**를 여섯 줄 다 냈다.
            #   ★ 없으면 ★ 다르다고 말하지 않는다 — ★ 「모른다」와 「틀리다」를 가른다
            exp = g.get("expect")
            if exp is None:
                mark, tail = "", ""
            else:
                mark = "" if said_n == exp else "  ★ 규격과 다르다"
                tail = f" (규격 {exp})"
            print(f"  {g['for']:22} {q:32} 사이트 {said_n:>4} · 받은 {len(got):>4}"
                  f"{tail}{mark}")
            time.sleep(INTERVAL)
        print(f"목록 {pages}쪽 · 매물 {len(ids):,}건  ← ★ 전량 {said} 을 받지 않았다")

    # ★★★★★ 08-29 (ORDER r879 1c · `HYUNDAI_CERTIFIED_API.md` 2d-1) —
    #   ★ **전동화(`_V`) 묶음은 ★ 목록 제목에 연료가 없다.**
    #   ★ 실측 — `mdlGrpList=1389_V` 카드 4건의 제목에 「전기」·「가솔린」이 0회다.
    #   ★ ★ 그래서 `fuel_match: ["전기"]` 인 차종 셋(`GV70_EV`·`GV60`·`G80_EV`)이
    #   ★ ★ 다 ★ **「차종 미정」**으로 저장됐다 — ★ 화면에서 안 잡힌다.
    #   ★ 상세에는 있다 — `fetch_detail(…)` → `fuel_raw: "전기"` (실측 08-29).
    #   ★★ 그래서 ★ **연료가 빈 것만** ★ 상세를 받아 채운다.  ★ `--detail` 을
    #   ★ ★ 안 줘도 한다 — ★ 안 하면 ★ 그 다섯 대가 ★ **영영 차종 미정**이다.
    #   ★ 짐작하지 않는다 — ★ 사이트가 상세에 적어 준 값을 그대로 쓴다
    need = [o for o in ids if not o.get("fuel_raw")]
    if need and "--dry" not in args:
        if len(need) > FUEL_FILL_MAX:
            print(f"★ 연료가 빈 것이 {len(need):,}건이다 — {FUEL_FILL_MAX}건을 넘는다."
                  "  ★ 목록 파싱이 바뀐 것일 수 있어 멈춘다 (상세를 안 받는다)")
            need = []
        else:
            print(f"★ 연료가 빈 것 {len(need)}건 — 상세로 채운다 (2d-1)")
        filled = 0
        for one in need:
            pair = fetch_detail(one["source_id"])
            if pair is not None and pair[0].get("fuel_raw"):
                one["fuel_raw"] = pair[0]["fuel_raw"]
                filled += 1
            time.sleep(INTERVAL)
        if need:
            print(f"  ★ 채운 것 {filled}/{len(need)}건")

    hit: dict = {}
    for one in ids:
        one["target_key"] = target_of(one)
        k = one["target_key"] or "차종 미정"
        hit[k] = hit.get(k, 0) + 1
    for k, n in sorted(hit.items(), key=lambda kv: -kv[1]):
        print(f"  {k:16} {n:>5}건")

    want_detail = "--detail" in args
    limit = 0
    if want_detail:
        i = args.index("--detail")
        if i + 1 < len(args) and args[i + 1].isdigit():
            limit = int(args[i + 1])

    if "--dry" in args:
        print("★ --dry 라 저장하지 않았다")
        return 0

    from store.core import resolve_listing_id, split_pii, upsert_core
    from store.pii import load_key
    from store.raw import commit, save_site_raw

    conn = open_db(os.path.join(ROOT, "carwatch.db"))
    at = _now()
    key = load_key()
    for one in ids:
        one["listing_id"] = resolve_listing_id(conn, SITE_CODE,
                                               one["source_id"], at)
        upsert_core(conn, split_pii(conn, one, SITE_CODE, key, at), at)
    commit(conn)
    # ★★★★★ 08-29 (개정 838 · 오판 161) — ★ 팔린 차를 거른다 (`S46-117`).
    #   ★ 저장한 **뒤에** 부른다 — ★ 새 매물이 차종을 갖고 있어야 한다

    # ★ 넣기가 끝났다 — ★ 원문을 매물에 잇는다 (S46-97 · 08-29)
    raw_link_raws(conn, SITE_CODE)
    # ★★★★★ 08-30 정정 (마스터 0c) — ★ **이 목록으로는 gone 을 못 매긴다.  ★ 껐다**
    #   ★ K카가 살아 있는 12대를 죽인 것과 ★ **같은 함정**이다 (0a).
    #   ★★ 실측 08-30 — ★ 08-29 에 gone 으로 매긴 것을 ★ **표본으로 눌러 봤다** —
    #   ★ ★ 표본 10건 중 ★ **10건이 다 살아 있었다**
    #   ★★★ 까닭 — ★ 「끝까지 받았나」 가드는 ★ 「이 창구를 끝까지 받았나」를 재지
    #     ★ ★ **「이 창구가 전량인가」를 안 잰다.**  ★ 우리는 ★ 차종으로 좁혀 받는다 —
    #     ★ ★ 좁힌 목록에 없다고 ★ 사이트에서 사라진 것이 아니다.
    #   ★ 되돌리는 길은 ★ `tools/undo_wrong_gone.py` 다 (눌러서 살아 있는 것만 되돌린다)
    _got = {}
    print(f"★ 팔린 차를 목록으로 안 거른다 — {SWEEP_OFF}")
    _dn = sum(1 for d, _i in done_groups if d)
    print(f"★ 목록에 없어 gone 으로 매긴 것 {sum(_got.values())}건 "
          f"({len(_got)}차종 · 끝까지 받은 묶음 {_dn}/{len(done_groups)})")
    if len(done_groups) - _dn:
        print("  ★ 끝까지 못 받은 묶음이 건드린 차종은 안 매겼다")
    print(f"★ 저장 {len(ids):,}건 · site='{SITE_CODE}'")

    if not want_detail:
        print("★ 상세는 --detail 로 받는다")
        return 0

    todo = ids[:limit] if limit else ids
    got = {"정상": 0, "못 받음": 0}
    from store.core import upsert_child

    for one in todo:
        pair = fetch_detail(one["source_id"])
        if pair is None:
            # ★ 못 받은 것을 ★ 「없음」으로 저장하지 않는다 (금지 12)
            got["못 받음"] += 1
            time.sleep(INTERVAL)
            continue
        deep, record, body = pair
        # ★★ 원문을 ★ 먼저 남긴다 (명령서 3-2 필수)
        save_site_raw(conn, SITE_CODE, "detail", one["source_id"],
                      BASE + DETAIL_PATH.format(goods_no=one["source_id"]),
                      body, at)
        # ★★ 08-29 (개정 857) — ★ 곧바로 커밋한다.
        #   ★ 통신·`sleep` 이 ★ 트랜잭션 안에 들면 ★ 잠금 창이 분 단위가 된다
        #   (KB 실측 — 100건 × 1.2초 = 120초 · 잠금 38.4초 · locked 로 죽었다)
        commit(conn)
        deep["listing_id"] = one["listing_id"]
        upsert_core(conn, split_pii(conn, deep, SITE_CODE, key, at), at)
        # ★ 사고·소유자 이력은 ★ core_record 의 칸이다 (A-2)
        record["listing_id"] = one["listing_id"]
        record["collected_at"] = at
        upsert_child(conn, "core_record", record, "p1", at)
        got["정상"] += 1
        # ★ 자기 전에 커밋한다 — ★ 넣기가 sleep 을 넘지 않게 (개정 857)
        commit(conn)
        time.sleep(INTERVAL)
    commit(conn)
    print("★ 상세 — " + " · ".join(f"{k} {v}" for k, v in got.items()))
    from tools.daily_enqueue import enqueue_after_store
    enqueue_after_store(os.path.join(ROOT, "carwatch.db"), SITE_CODE,
                        got.get("정상", 0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
