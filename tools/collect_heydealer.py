# -*- coding: utf-8 -*-
"""헤이딜러 수집 — 토큰 → 차종별 목록 → 상세 (명령서 37).

쓰기   python3.11 tools/collect_heydealer.py            차종 15종 전부
      python3.11 tools/collect_heydealer.py --dry      받기만 하고 저장 안 함
      python3.11 tools/collect_heydealer.py --target XC60_IMPORT
★ 토큰은 바퀴마다 새로 받는다 (JWT).  ★ 저장소에 안 적는다 (명령서 37-3)
★ 한 쪽에 10건이 상한이다 — 10 이면 다음 쪽으로 간다
★ 연료는 목록에 없다 — ★ 상세를 받아야 fuel_match 가 걸린다
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

# ★★★★★ 이 수집기는 ★ **팔린 차를 목록으로 안 거른다** (마스터 지시 08-30 · S46-117).
#   ★ 낱말 `SWEEP_OFF` 를 ★ 검사가 본다 — ★ 「안 거른다」와 「못 거른다」를 가른다
SWEEP_OFF = (
    "08-29 — 목록에 없다고 죽이면 살아 있는 차를 죽인다"
    " (11-store/a-key 08-29 절).  상세로 확인한 뒤 죽이는 꼴로 바꾼 뒤 다시 켠다")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from adapters.heydealer import PAGE_SIZE, SITE_CODE, HeydealerAdapter  # noqa: E402
from parse.heydealer.mapping import (  # noqa: E402
    options_of, parse_detail, parse_list_item, part_enums, record_of,
    warranty_of,
)
from parse.target_rules import fill_target_key  # noqa: E402
from store.raw import link_raws as raw_link_raws  # noqa: E402
# ★★★★★ 09-01 마스터 지시 — ★ 받기는 ★ **파일만** 쓴다 (`S46-204`)
from store.rawfile import save as save_file  # noqa: E402
from store.raw import open_db                                          # noqa: E402

MAX_PAGES = 40          # ★ 안전장치.  ★ 10건 미만이 오면 그 전에 멈춘다


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get(req) -> tuple[int, object]:
    r = urllib.request.Request(req.url, headers=req.headers)
    try:
        with urllib.request.urlopen(r, timeout=req.timeout_sec) as res:
            raw = res.read()
            return res.status, json.loads(raw)
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception:
        return 0, None


def _targets(args: list) -> list:
    with open(os.path.join(ROOT, "config", "targets.json"), encoding="utf-8") as f:
        rows = json.load(f)
    want = None
    if "--target" in args:
        i = args.index("--target")
        want = {a for a in args[i + 1:] if not a.startswith("--")}
    out = []
    for key, one in rows.items():
        if key.startswith("_") or not isinstance(one, dict):
            continue
        q = (one.get("site_query") or {}).get(SITE_CODE)
        if not q or (want and key not in want):
            continue
        out.append((key, q if isinstance(q, list) else [q]))
    return out


def walk(adapter, key: str, queries: list, interval: float) -> tuple:
    """한 차종의 매물 전부.  ★ 해시가 둘이면 둘 다 돈다 (G80·그랜저).

    ★★★ 08-29 (개정 838) — ★ 「끝까지 받았나」를 함께 돌려준다.
      ★ 마지막 쪽(`len(body) < PAGE_SIZE`)까지 갔을 때만 참이다 —
      ★ 200 이 아니거나 · MAX_PAGES 를 다 쓴 것은 ★ 끝이 아니다.
      ★ 질의가 여럿이면 ★ **다 끝까지** 가야 참이다
    """
    seen, rows = set(), []
    done = True
    for q in queries:
        # ★★★★★ 08-29 (`HEYDEALER_API.md` 「전기 200건에 무엇이 있나」) —
        #   ★ `fuel` 을 더한다.  ★ 앞서는 셋뿐이라 ★ 연료로만 좁힌 질의가
        #   ★ ★ **빈 dict** 가 되어 ★ 조건 없는 **전량 1,330건**을 끌어왔다
        #   ★ ★ (평소 207).  ★ 마스터 확정 「전량을 받지 않는다」에 어긋난다.
        #   ★ 이제 `fuel=electric` 이 주소에 실려 ★ 200건만 온다 (실측 08-29).
        #   ★★ 그래도 ★ **빈 pick 은 안 부른다** — ★ 아래에서 막는다
        pick = {k: q[k] for k in ("brand", "model-group", "model", "fuel")
                if q.get(k)}
        if not pick:
            # ★ 좁힐 것이 하나도 없으면 ★ 전량이 온다 — ★ 부르지 않는다.
            #   ★ 「받은 것이 없다」가 아니라 ★ 「질의가 비었다」를 말한다
            print(f"    {key} {q.get('_차명', '')} — ★ 좁힐 값이 없다 "
                  "(brand·model-group·model·fuel 이 다 비었다).  ★ 안 부른다")
            done = False
            continue
        for page in range(1, MAX_PAGES + 1):
            code, body = _get(adapter.list_url(None, page, pick))
            if code != 200 or not isinstance(body, list):
                print(f"    {key} {q.get('_차명', '')} {page}쪽 — ★ {code} · 멈춘다")
                done = False            # ★ 못 받았다 — ★ 끝이 아니다
                break
            for one in body:
                got = parse_list_item(one, SITE_CODE)
                if got and got["source_id"] not in seen:
                    seen.add(got["source_id"])
                    rows.append(got)
            if len(body) < PAGE_SIZE:
                break                   # ★ 마지막 쪽이다 — ★ 끝까지 받았다
            time.sleep(interval)
        else:
            done = False                # ★ MAX_PAGES 를 다 썼다 — ★ 더 있을 수 있다
    return rows, done


def main() -> int:
    args = sys.argv[1:]
    with open(os.path.join(ROOT, "config", "endpoints.json"), encoding="utf-8") as f:
        cfg = json.load(f)[SITE_CODE]
    adapter = HeydealerAdapter(cfg)
    adapter.token()                       # ★ 바퀴마다 새로 받는다
    interval = float(cfg.get("interval_sec") or 0.5)

    targets = _targets(args)
    print(f"★ 헤이딜러 — 차종 {len(targets)}종")
    got_all: dict = {}
    # ★★★ 08-29 (개정 838) — ★ 차종마다 ★ 「끝까지 받았나」를 들고 간다
    done_groups: list = []
    for key, queries in targets:
        rows, _d = walk(adapter, key, queries, interval)
        done_groups.append((_d, {r["source_id"] for r in rows}))
        for r in rows:
            got_all[r["source_id"]] = r
        print(f"  {key:<16} 매물 {len(rows):>4}")
    print(f"★ 목록 합 {len(got_all):,}건 (겹친 것을 뺀 수)")
    if "--dry" in args:
        print("★ --dry 라 저장하지 않았다")
        return 0

    from store.core import (
        resolve_listing_id, split_pii, upsert_child, upsert_core,
    )
    from errors import ValidationError
    from store.dictionary import upsert_enum
    from store.pii import load_key
    from store.raw import commit

    conn = open_db(os.path.join(ROOT, "carwatch.db"))
    at, pii_key = _now(), load_key()
    for one in got_all.values():
        one["listing_id"] = resolve_listing_id(conn, SITE_CODE,
                                               one["source_id"], at)
        # ★ 넣기 직전에 ★ 차종을 붙인다 (마스터 지시 08-30) — ★ 안 붙이면 판정에 안 들어간다
        fill_target_key(SITE_CODE, one)
        upsert_core(conn, split_pii(conn, one, SITE_CODE, pii_key, at), at)
    commit(conn)
    # ★★★★★ 08-29 (개정 838 · 오판 161) — ★ 팔린 차를 거른다 (`S46-117`)

    # ★ 넣기가 끝났다 — ★ 원문을 매물에 잇는다 (S46-97 · 08-29)
    raw_link_raws(conn, SITE_CODE)
    # ★★★★★ 08-30 정정 (마스터 0c) — ★ **이 목록으로는 gone 을 못 매긴다.  ★ 껐다**
    #   ★ K카가 살아 있는 12대를 죽인 것과 ★ **같은 함정**이다 (0a).
    #   ★★ 실측 08-30 — ★ 08-29 에 gone 으로 매긴 것을 ★ **표본으로 눌러 봤다** —
    #   ★ ★ 표본 10건 중 ★ **8건이 살아 있었다** (상세가 `hash_id` 를 줬다)
    #   ★★★ 까닭 — ★ 「끝까지 받았나」 가드는 ★ 「이 창구를 끝까지 받았나」를 재지
    #     ★ ★ **「이 창구가 전량인가」를 안 잰다.**  ★ 우리는 ★ 차종으로 좁혀 받는다 —
    #     ★ ★ 좁힌 목록에 없다고 ★ 사이트에서 사라진 것이 아니다.
    #   ★ 되돌리는 길은 ★ `tools/undo_wrong_gone.py` 다 (눌러서 살아 있는 것만 되돌린다)
    _got = {}
    print(f"★ 팔린 차를 목록으로 안 거른다 — {SWEEP_OFF}")
    _dn = sum(1 for d, _i in done_groups if d)
    print(f"★ 목록에 없어 gone 으로 매긴 것 {sum(_got.values())}건 "
          f"({len(_got)}차종 · 끝까지 받은 차종 {_dn}/{len(done_groups)})")
    print(f"★ 목록 저장 {len(got_all):,}건 · site='{SITE_CODE}'")

    # ★ 상세 — ★ 연료·차량번호가 여기에만 있다.  ★ 전건 받는다
    done = {r[0] for r in conn.execute(
        "SELECT source_id FROM core_listing WHERE site=? AND detail_status='ok'",
        (SITE_CODE,))}
    todo = [o for o in got_all.values() if o["source_id"] not in done]
    print(f"★ 상세 — 받을 것 {len(todo)}건 (이미 받은 것 {len(done)}건은 건너뛴다)")
    seen = {"정상": 0, "못 받음": 0}
    for one in todo:
        code, body = _get(adapter.detail_urls(one["source_id"])[0])
        if code != 200 or not isinstance(body, dict):
            seen["못 받음"] += 1
            time.sleep(interval)
            continue
        # ★★ 원문을 ★ 먼저 남긴다 (명령서 3-2 필수) — ★ 「갈래를 넓히시면 다시 판다」
        save_file(SITE_CODE, "detail", one["source_id"],
                      adapter.detail_urls(one["source_id"])[0].url,
                      json.dumps(body, ensure_ascii=False), at)
        deep = parse_detail(body, SITE_CODE, one["source_id"])
        if deep:
            # ★★ 옵션을 ★ **한글 이름으로** 저장한다 (명령서 B · 08-25).
            #   ★ 엔카는 ★ 숫자 코드만 준다 — ★ 헤이딜러가 ★ 이름을 준다.
            #   ★ ★ 이것이 ★ `option_names.json` 의 밑감이다
            got = options_of(body)
            if got:
                deep["options_standard_json"] = json.dumps(
                    [x["name"] for x in got if x["loaded"]], ensure_ascii=False)
                deep["options_etc_json"] = json.dumps(
                    [x["name"] for x in got if not x["loaded"]],
                    ensure_ascii=False)
            deep["listing_id"] = one["listing_id"]
            deep["detail_status"] = "ok"
            # ★★★★★ 08-30 (r974 · 0j 4) — ★ 보증은 ★ 원문에 ★ 이미 와 있다.
            #   ★ 「남은 양」을 ★ 총량으로 바꿔 넣는다 (규격 3-4 · `warranty_of`)
            deep.update(warranty_of(body))
            # ★ 넣기 직전에 ★ 차종을 붙인다 (마스터 지시 08-30) — ★ 안 붙이면 판정에 안 들어간다
            fill_target_key(SITE_CODE, deep)
            upsert_core(conn, split_pii(conn, deep, SITE_CODE, pii_key, at), at)
            # ★★★★★ 08-30 (r974 · 0j 4) — ★ 이력이 ★ 통째로 온다 (규격 3-2).
            #   ★ 사고 51 · 자차 28 · 소유자 11 · 용도 22 · 특수 21 이 ★ 여기서 산다.
            #   ★ ★ 남의 표 칸이므로 ★ `core_record` 에 넣는다 — ★ core 에 넣으면
            #     ★ ★ `upsert_core` 가 ★ 조용히 버린다 (A-2)
            rec = record_of(body, SITE_CODE)
            if rec:
                rec["listing_id"] = one["listing_id"]
                rec["collected_at"] = at
                upsert_child(conn, "core_record", rec, "p1", at)
                seen["이력"] = seen.get("이력", 0) + 1
            # ★ 부위(`part`)는 ★ 원문 그대로 사전에 남긴다 — ★ 우리말로 안 옮긴다 (3a ②)
            for one_p in part_enums(body):
                # ★ `display` 에 ★ 원문을 그대로 둔다 — ★ 우리말로 안 옮긴다 (3a ②).
                #   ★ 등급(RANK) 표가 오면 ★ 그때 골격·외판이 열린다
                # ★★★ `part` 축은 ★ STEP 41 정책 표에 ★ 행이 없다 (실측 08-30).
                #   ★ 내가 표를 안 늘린다 (규칙 2) — ★ 마스터께 올렸다.
                #   ★ ★ 값은 ★ 원문에 그대로 남는다 (P3)
                try:
                    upsert_enum(conn, SITE_CODE, "part", one_p["part"],
                                one_p["part"], 1, "detail", "d1", at,
                                force_pending=True)
                    seen["부위"] = seen.get("부위", 0) + 1
                except ValidationError:
                    seen["부위(축 정책 없음)"] = seen.get("부위(축 정책 없음)", 0) + 1
                    break
            seen["정상"] += 1
        time.sleep(interval)
    commit(conn)
    print("★ 상세 — " + " · ".join(f"{k} {v}" for k, v in seen.items()))
    n = conn.execute("SELECT COUNT(*) FROM core_listing WHERE site=?",
                     (SITE_CODE,)).fetchone()[0]
    print(f"★ 저장된 헤이딜러 매물 — {n:,}건")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
