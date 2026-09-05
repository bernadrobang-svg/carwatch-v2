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

from adapters.heydealer import (  # noqa: E402
    PAGE_SIZE,
    SITE_CODE,
    HeydealerAdapter,
    schema,
)
from parse.heydealer.mapping import (  # noqa: E402
    parse_list_item,
)
# ★★★★★ 09-01 마스터 지시 — ★ 받기는 ★ **파일만** 쓴다 (`S46-204`)
from store.rawfile import save as save_file  # noqa: E402

MAX_PAGES = 40          # ★ 안전장치.  ★ 10건 미만이 오면 그 전에 멈춘다


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get(req, endpoint: str | None = None, source_id=None,
         page: int | None = None) -> tuple[int, object]:
    """★ 받는다.  ★ 돌려줌 `(코드, 푼 묶음 또는 None)`.

    ★★★★★ 09-05 (지시 1번 · `S46-278` · `STEP 53-⑤`) — ★ **막힌 응답도 원문이다.**
      ★ 전에는 ★ 실패하면 ★ **몸통을 버렸다** — ★ 「어떻게 막혔나」를 뒤에 못 봤다
    """
    from collect.rawfetch import keep_blocked

    r = urllib.request.Request(req.url, headers=req.headers)
    try:
        with urllib.request.urlopen(r, timeout=req.timeout_sec) as res:
            raw = res.read()
            return res.status, json.loads(raw)
    except urllib.error.HTTPError as e:
        if endpoint:
            try:
                keep_blocked(SITE_CODE, endpoint, source_id, req.url,
                             e.read(), page=page, http_code=e.code, root=ROOT)
            except OSError:
                pass
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
        # ★★★★★ 09-02 — ★ **쉬는 차종은 안 받는다** (`S46-215` · 마스터 실측).
        #   ★ 매물을 지우지 않는다 — ★ 받으러 가지만 않는다
        if not one.get("active"):
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
            code, body = _get(adapter.list_url(None, page, pick),
                              endpoint="list", page=page)
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

    # ★★★★★ 09-01 마스터 지시 — ★ **받기 걸음은 파일만 쓴다.  ★ DB 를 안 연다.**
    #   ★ 넣기는 ★ `python3.11 tools/load_raw.py heydealer --write` 가 한다.
    #   ★★ 이력·판·부위 사전도 ★ 넣기 걸음이 한다 — ★ 여기서는 ★ 원문만 남긴다
    at = _now()
    for one in got_all.values():
        save_file(SITE_CODE, "list", one["source_id"],
                  adapter.detail_urls(one["source_id"])[0].url,
                  json.dumps(one, ensure_ascii=False), at, root=ROOT)
    _dn = sum(1 for d, _i in done_groups if d)
    print(f"★ 팔린 차를 목록으로 안 거른다 — {SWEEP_OFF}")
    print(f"★ 목록 {len(got_all):,}건을 파일로 남겼다 · "
          f"끝까지 받은 차종 {_dn}/{len(done_groups)}")

    # ★ 상세 — ★ 연료·차량번호가 여기에만 있다.
    #   ★★ 09-01 — ★ 「이미 받았나」는 ★ **파일로 안다** (DB 를 안 연다)
    # ★★★★★ 09-03 — ★ **껍데기는 「받은 것」으로 안 센다.**
    #   ★ 파일이 있다는 것만 보고 건너뛰면 ★ 오류 안내 198바이트가
    #     ★ ★ 영영 상세 자리를 차지한다 (실측 18건).
    #   ★ 원문 파일은 ★ **지우지 않는다** — ★ 세는 자리에서만 가른다
    from store.rawfile import read as _read
    from store.rawfile import walk as _walk

    _spec_have = schema("detail")
    have, _shell = set(), 0
    for x in _walk(site=SITE_CODE, endpoint="detail", root=ROOT):
        _sid = os.path.basename(x).split("__")[0][:-5]
        _env = _read(x) or {}
        try:
            _b = json.loads(_env.get("body") or "null")
        except ValueError:
            _b = None
        if isinstance(_b, dict) and all(k in _b for k in _spec_have.required_keys):
            have.add(_sid)
        else:
            _shell += 1
    if _shell:
        print(f"★ 껍데기 원문 {_shell}건 — 상세로 안 세고 다시 받는다")
    todo = [o for o in got_all.values() if o["source_id"] not in have]
    print(f"★ 상세 — 받을 것 {len(todo)}건 "
          f"(원문 파일이 있는 것 {len(got_all) - len(todo)}건은 건너뛴다)")
    seen = {"정상": 0, "못 받음": 0, "껍데기": 0}
    _spec = schema("detail")
    for one in todo:
        code, body = _get(adapter.detail_urls(one["source_id"])[0],
                          endpoint="detail",
                          source_id=one["source_id"])
        if code != 200 or not isinstance(body, dict):
            seen["못 받음"] += 1
            time.sleep(interval)
            continue
        # ★★★★★ 09-03 — ★ **200 이라고 상세가 아니다.**
        #   ★ 실측 — ★ 18건이 ★ HTTP 200 · dict 인데 ★ 본문이
        #     ★ `{"code":null,"message":null,"toast":{"message":"서버 오류가
        #        발생했습니다…"}}` ★ 198바이트짜리 ★ **오류 안내**였다.
        #   ★★ 그것을 상세로 세어 ★ 「상세 99 · 파싱 81」이 났다 —
        #     ★ ★ 상세가 99가 아니라 ★ **81** 이었다.
        #   ★★★ 규격의 관문을 여기서도 건다 — `required_keys` 는
        #     ★ `adapters/heydealer.py` 의 `hash_id`·`detail_info` 다
        #     ★ (2장 STEP 18 「저장 직전에 건다」).
        #   ★ 「받았다」와 「제대로 받았다」를 가른다 — ★ 껍데기를 안 남긴다
        if not all(k in body for k in _spec.required_keys):
            _miss = ",".join(k for k in _spec.required_keys if k not in body)
            seen["껍데기"] = seen.get("껍데기", 0) + 1
            print(f"    ⨯ {one['source_id']} — required_keys 누락: {_miss}")
            time.sleep(interval)
            continue
        save_file(SITE_CODE, "detail", one["source_id"],
                  adapter.detail_urls(one["source_id"])[0].url,
                  json.dumps(body, ensure_ascii=False), at, root=ROOT)
        seen["정상"] += 1
        time.sleep(interval)
    print("★ 상세 — " + " · ".join(f"{k} {v}" for k, v in seen.items()))
    print(f"★ 넣기 — python3.11 tools/load_raw.py {SITE_CODE} --write")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
