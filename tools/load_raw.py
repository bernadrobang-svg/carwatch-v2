# -*- coding: utf-8 -*-
"""넣기 걸음 — ★ **파일 폴더를 읽어 `raw_response` ＋ `core_listing` 에 넣는다.**

지시서   `docs/ARCHITECTURE_20260830.md` 2장 · 마스터 지시 09-01
★★★ 마스터 — 「★ 받기 걸음은 ★ **파일만 쓴다.  ★ DB 를 안 연다** — 잠금이 아예 안 생긴다.
   ★ ★ **넣기 걸음은 그 폴더를 읽어 ★ `raw_response` ＋ `core_listing` 에 넣는다**」

★★ 곧 ★ **DB 를 여는 곳은 여기 하나다.**  ★ 통신은 하나도 안 한다 —
  ★ 그래서 ★ 한 번에 몰아 넣고 ★ 곧바로 끝난다.  ★ 잠금 창이 짧다

★★★★★ 09-04 (지시문 r1124 · 0-1·0-2·0-4 · `S46-265`) — ★ **적재 DB 를 거친다.**

```
① 받기      raw/{site}/{endpoint}/{날짜}/…      ★ 파일만.  DB 를 안 연다
② ★ 적재    tmp/load-{run_id}.db                ★ **본 DB 가 아니다**
③ 파싱      core_* · result_*                   ★ 제 표로
④ 원문 표   ★ 본 DB 에 ★ **안 쌓는다**            ★ 그래야 DB 가 안 부푼다
⑤ ★ 치운다  tmp/load-{run_id}.db 를 지운다        ★ 판이 끝나면
```

★ 전에는 ★ ②가 ★ **본 DB 의 `raw_response`** 였다.  ★ 그것이 ★ 372,571행 · 425MB 로
  ★ 자라 ★ DB 를 ★ **1.08 GiB** 로 만들었고 ★ 장비(RAM 1,841MB)를 ★ **세 번** 죽였다.
★ ★ 원문은 ★ **파일에 남는다** — ★ 적재 DB 는 ★ 그저 ★ 한 판의 발판이다

돌리는 법
    python3.11 tools/load_raw.py revolt            ★ 잰다
    python3.11 tools/load_raw.py revolt --write    ★ 넣는다
    python3.11 tools/load_raw.py revolt --write --day 2026-08-31
    python3.11 tools/load_raw.py revolt --write --keep-load-db   ★ 적재 DB 를 안 지운다
"""
from __future__ import annotations

import json
import os
import sys
import json as _j
from collections import Counter
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from store.rawfile import read, walk  # noqa: E402

# ★★★★★ 09-01 — ★ **열 사이트를 다 받는다** (마스터 지시).
#   ★ 파서 이름은 같은데 ★ **부르는 꼴이 사이트마다 다르다** (실측 09-01) —
#     `parse_detail(html, site, source_id)`  · 대부분
#     `parse_detail(html, source_id)`        · BMW
#     `parse_detail(body: dict, …)`          · K카 · 리볼트 · 렉서스
#     `parse_detail_all(html, site, sid)`    · 현대인증 (줄 ＋ 이력을 함께 낸다)
#   ★ ★ 그래서 ★ **어떻게 부르는지**를 여기 표로 적는다 — ★ 짐작으로 부르지 않는다
#   ★ `json` — 몸통을 JSON 으로 풀어 넘길지 (아니면 글자 그대로)
LOADERS: dict = {
    "revolt": {"mod": "parse.revolt.mapping", "json": True,
               "list_one": True},
    "heydealer": {"mod": "parse.heydealer.mapping", "json": True},
    "kcar": {"mod": "parse.kcar.mapping", "json": True},
    "lexus_certified": {"mod": "parse.lexus_certified.mapping", "json": True,
                        "list_one": True},
    "kia_cpo": {"mod": "parse.kia_cpo.mapping", "json": True},
    "bobaedream": {"mod": "parse.bobaedream.mapping", "json": False},
    "kbchachacha": {"mod": "parse.kbchachacha.mapping", "json": False},
    "reborncar": {"mod": "parse.reborncar.mapping", "json": False},
    # ★ 볼보 목록 줄은 ★ 우리가 만든 JSON 이다 (`parse_list_item`) —
    #   ★ 상세는 ★ HTML 이다.  ★ `json` 은 ★ **목록에만** 걸린다
    "volvo_selekt": {"mod": "parse.volvo_selekt.mapping", "json": False,
                     "list_json": True},
    # ★ BMW 목록 줄은 ★ 우리가 만든 JSON 이다 · 상세는 ★ HTML 이다
    "bmw_bps": {"mod": "parse.bmw_bps.mapping", "json": False,
                "list_json": True, "detail_args": "sid_only"},
    "hyundai_cert": {"mod": "parse.hyundai_cert.mapping", "json": False,
                     "detail_fn": "parse_detail_all"},
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def query_target(site: str, url: str, root: str = ROOT) -> str | None:
    """★★★★★ 09-01 — ★ **받을 때 쓴 질의가 차종을 말해 준다.**

    ★ 자리 — ★ 파일에 남은 `url` 에 ★ `?model_hash_id=…` 가 들어 있다.
      ★ ★ `targets.json` 의 `site_query.{site}` 를 ★ 거꾸로 뒤져 ★ 우리 키를 낸다
    ★★ 까닭 — ★ 리볼트 목록 항목에는 ★ `model_hash_id` 가 ★ **없다** [실측 09-01].
      ★ ★ 있는 것은 영문 `model_name` 뿐이라 ★ 이름을 옮기다 ★ 264/270건을 놓쳤다.
      ★ ★ ★ **질의로 받았으면 ★ 옮길 것이 없다** — ★ 사이트가 이미 갈라 줬다
    ★ 표에 없으면 ★ `None` 이다 — ★ **짐작으로 짓지 않는다** (금지 6)
    """
    if not url:
        return None
    from urllib.parse import parse_qs, urlparse

    q = parse_qs(urlparse(url).query)
    if not q:
        return None
    with open(os.path.join(root, "config", "targets.json"),
              encoding="utf-8") as f:
        rows = json.load(f)
    for tkey, spec in rows.items():
        if tkey.startswith("_") or not isinstance(spec, dict):
            continue
        want = (spec.get("site_query") or {}).get(site)
        if not isinstance(want, dict):
            continue
        hit = False
        for name, val in want.items():
            if name.startswith("_") or name not in q:
                continue
            allowed = {str(x) for x in
                       (val if isinstance(val, list) else [val])}
            if set(q[name]) & allowed:
                hit = True
        if hit:
            return tkey
    return None


def body_target(site: str, env: dict, root: str = ROOT) -> str | None:
    """★★★★★ 09-01 — ★ **상세 본문의 열쇠**로 차종을 짚는다.

    ★ 규격 `docs/REVOLT_API.md` 100줄 —
      ★ 「차종 이름은 `car_info.brand_name` ＋ `model_name` ＋ `model_hash_id` 다」
    ★★ 상세에는 ★ 질의가 없다 — ★ 목록은 `?model_hash_id=` 로 갈랐지만
      ★ ★ 상세 URL 은 `/cars/{hash_id}/` 라 ★ 열쇠가 안 붙는다.
      ★ ★ ★ 그래서 ★ **본문에서 읽는다** — ★ 이름을 옮기지 않는다
    ★ 표에 없으면 ★ `None` 이다 (금지 6)
    """
    body = env.get("body")
    if not body:
        return None
    try:
        got = json.loads(body)
    except (ValueError, TypeError):
        return None
    if not isinstance(got, dict):
        return None
    info = got.get("car_info") if isinstance(got.get("car_info"), dict) else got
    mid = info.get("model_hash_id")
    if not mid:
        return None
    return query_target(site, f"?model_hash_id={mid}", root)


def _rows_from(site: str, env: dict, mod, spec: dict) -> tuple:
    """봉투 하나 → (core 줄들, 이력, 판).  ★ 목록이면 여러 줄이 나온다.

    ★★ 사이트마다 ★ 부르는 꼴이 다르다 — ★ `LOADERS` 표가 정본이다
    """
    body = env.get("body")
    if not body:
        return [], None, None
    got = body
    if spec.get("json") or (spec.get("list_json")
                            and env.get("endpoint") == "list"):
        # ★★★★★ 09-03 — ★ **이미 풀린 묶음이 들어올 수 있다.**
        #   ★ 파일 봉투는 ★ 글월을 주고 ★ 표 봉투(`_envs_from_db`)는
        #   ★ ★ **이미 `json.loads` 한 묶음**을 준다 —
        #   ★ ★ ★ 그때 다시 풀면 ★ `TypeError: … not dict` 로 죽는다 [실측 09-03].
        #   ★ 글월일 때만 푼다.  ★ 못 풀면 ★ 조용히 버리지 않고 ★ 빈 줄을 낸다
        if isinstance(body, (str, bytes, bytearray)):
            try:
                got = json.loads(body)
            except ValueError:
                return [], None, None
    sid = env.get("source_id")

    if env.get("endpoint") == "list":
        fn = getattr(mod, "parse_list_item", None)
        if fn is None:
            return [], None, None      # ★ 목록 파서가 없다 — ★ 원문만 남는다
        # ★★★★★ 09-01 — ★ 목록 몸통이 ★ 세 꼴로 온다 (실측) —
        #   ⓐ 배열                        · 리볼트 (`page-0001.json` 한 쪽 20건)
        #   ⓑ `{"results": [...]}`        · 감싸 주는 곳
        #   ⓒ ★ **항목 하나짜리 dict**     · 렉서스 (`{source_id}.json` 한 건씩)
        #   ★★ 앞서는 ⓒ 를 ★ `got.get("results")` 로 물어 ★ **`None`** 을 받았다 —
        #     ★ ★ 그래서 ★ 144개를 읽고도 ★ 줄이 0 이었다 (실측 09-01)
        if isinstance(got, list):
            items = got
        elif isinstance(got, dict):
            items = got.get("results")
            if items is None:
                items = [got]          # ⓒ ★ 한 건짜리다
        else:
            return [], None, None
        if not isinstance(items, list):
            return [], None, None
        rows = []
        for x in items:
            if not isinstance(x, dict):
                continue
            # ★ 사이트 인자를 ★ 받는 것과 ★ 안 받는 것이 있다 (렉서스는 안 받는다)
            try:
                rows.append(fn(x, site))
            except TypeError:
                rows.append(fn(x))
        return [r for r in rows if r], None, None

    name = spec.get("detail_fn") or "parse_detail"
    fn = getattr(mod, name, None)
    if fn is None:
        return [], None, None
    if spec.get("detail_args") == "sid_only":
        deep = fn(got, sid)            # ★ BMW
    else:
        deep = fn(got, site, sid)
    rec = None
    if isinstance(deep, tuple):
        # ★ 현대인증 — ★ (줄, 이력) 을 함께 낸다
        deep, rec = (list(deep) + [None, None])[:2]
    if rec is None and hasattr(mod, "record_of"):
        try:
            rec = mod.record_of(got, site)
        except TypeError:
            rec = mod.record_of(got)
    pan = None
    if hasattr(mod, "panels_of"):
        try:
            pan = mod.panels_of(got)
        except (TypeError, ValueError, AttributeError):
            pan = None
    return ([deep] if deep else []), rec, pan


def _envs_from_db(site: str, day: str | None) -> list:
    """★ 09-03 (S6) — ★ `raw_response` 표의 원문을 ★ 파일과 **같은 꼴**로 낸다.

    ★ 파일 봉투(`store.rawfile.read`)와 ★ 열쇠 이름을 맞춘다 —
      ★ ★ 그래야 ★ 아래 넣기 고리를 ★ **하나도 안 고치고** 쓴다
    ★ 못 읽는 몸통은 ★ 건너뛴다 — ★ 「없음」으로 안 만든다 (금지 12)
    """
    import sqlite3 as _sq

    db = os.path.join(ROOT, "carwatch.db")
    if not os.path.isfile(db):
        return []
    from store.raw import raw_body

    conn = _sq.connect(f"file:{db}?mode=ro", uri=True)
    sql = ("SELECT endpoint, source_id, request_url, body, fetched_at, http_code"
           "  FROM raw_response WHERE site=? AND status='ok'"
           "    AND endpoint <> 'list' AND body IS NOT NULL")
    args: list = [site]
    if day:
        sql += " AND substr(fetched_at,1,10)=?"
        args.append(day)
    out = []
    try:
        for ep, sid, url, body, at, code in conn.execute(sql, args):
            # ★★★★★ 09-03 — ★ **원문이 다 JSON 은 아니다.**
            #   ★ 현대인증·K카·보배드림 상세는 ★ **HTML 쪽**이다 [실측 09-03].
            #   ★ ★ 그것이 그 사이트의 ★ **바른 원문**이다 — ★ 파서가 그렇게 받는다.
            #   ★ ★ ★ JSON 으로만 읽으려다 ★ 셋을 통째로 버리고 있었다
            raw = raw_body(body)
            try:
                doc = _j.loads(raw)
            except (ValueError, TypeError):
                doc = raw          # ★ HTML 은 글월 그대로 넘긴다
            out.append({"endpoint": ep, "source_id": sid, "url": url or "",
                        "body": doc, "fetched_at": at,
                        "http_code": int(code or 200)})
    except _sq.Error:
        return []
    finally:
        conn.close()
    return out


def main() -> int:
    args = sys.argv[1:]
    site = next((a for a in args if not a.startswith("-")), None)
    if site not in LOADERS:
        print("쓰는 법 — python3.11 tools/load_raw.py "
              f"<{' | '.join(LOADERS)}> [--write] [--day YYYY-MM-DD]")
        return 2
    write = "--write" in args
    day = None
    if "--day" in args:
        i = args.index("--day")
        if i + 1 < len(args):
            day = args[i + 1]

    import importlib

    spec = LOADERS[site]
    mod = importlib.import_module(spec["mod"])
    files = walk(site=site, day=day, root=ROOT)
    print(f"★ {site} — 파일 {len(files):,}개"
          + ("" if write else "  ★ 재기만 한다"))
    # ★★★★★ 09-03 (2부 S6) — ★ **원문이 파일에만 있는 게 아니다.**
    #   ★ 실측 09-03 — ★ 현대인증·K카·보배드림은 ★ 상세 원문이
    #   ★ ★ `raw/` 폴더가 아니라 ★ **`raw_response` 표**에 있다
    #   ★ ★ ★ (현대인증 detail 225 · K카 115 · 보배 225).
    #   ★★ `walk()` 는 ★ 폴더만 본다 — ★ 그래서 ★ 그 셋이 ★ `parsed_at` **0** 이었다.
    #   ★ 표에 있는 것도 ★ **같은 길로** 넣는다 — ★ 새 길을 만들지 않는다
    from_db = _envs_from_db(site, day)
    if from_db:
        print(f"  ＋ 표에 있는 원문 {len(from_db):,}개 (raw_response)")
    got: Counter = Counter()
    if not write:
        for path in files:
            env = read(path)
            if env is None:
                got["못 읽음"] += 1
                continue
            rows, rec, pan = _rows_from(site, env, mod, spec)
            got[env.get("endpoint") or "?"] += 1
            got["  줄"] += len(rows)
            if rec:
                got["  이력"] += 1
            if pan is not None:
                got["  판"] += 1
        for k, v in got.most_common():
            print(f"   {k:<20}{v:>7,}")
        return 0

    from parse.target_rules import fill_target_key
    from store.core import resolve_listing_id, split_pii, upsert_child, upsert_core
    from store.dictionary import known_model_of
    from store.pii import load_key
    from store.raw import commit, open_db, save_site_raw
    from store.raw import link_raws as raw_link_raws

    conn = open_db(os.path.join(ROOT, "carwatch.db"))
    # ★★★★★ 0-1·0-2 — ★ 원문은 ★ **적재 DB** 로 간다.  ★ 본 DB 에 안 쌓는다
    run_id = _now().replace("-", "").replace(":", "")[:15]
    load_dir = os.path.join(ROOT, "tmp")
    os.makedirs(load_dir, exist_ok=True)
    load_path = os.path.join(load_dir, f"load-{run_id}.db")
    load_conn = open_db(load_path)
    print(f"★ 적재 DB — {os.path.relpath(load_path, ROOT)}")
    at = _now()
    key = load_key()
    # ★ 09-03 (S6) — ★ 파일 봉투 ＋ ★ **표 봉투**를 ★ 한 고리로 돈다
    for path in [*files, *from_db]:
        env = path if isinstance(path, dict) else read(path)
        if env is None:
            got["못 읽음"] += 1
            continue
        got[env.get("endpoint") or "?"] += 1
        # ★★ 원문을 ★ 먼저 남긴다 — ★ 파일이 원본이고 ★ 이것은 사본이다 (P3)
        #   ★ 09-03 — ★ 표에서 온 것은 ★ 이미 `raw_response` 에 있다.  ★ 두 번 안 쓴다
        if not isinstance(path, dict):
            # ★ 0-2 — ★ **적재 DB** 에 넣는다 (`conn` 이 아니다).  ★ 본 DB 가 안 부푼다
            save_site_raw(load_conn, site, env["endpoint"],
                          env.get("source_id"), env.get("url") or "",
                          env.get("body"), env.get("fetched_at") or at,
                          http_code=int(env.get("http_code") or 200))
        rows, rec, pan = _rows_from(site, env, mod, spec)
        for row in rows:
            # ★★★★★ 09-01 — ★ **열쇠를 먼저 본다** (이름보다 앞선다).
            #   ★ 목록 — ★ 받을 때 쓴 질의(`?model_hash_id=`)가 말해 준다
            #   ★ 상세 — ★ 본문 `car_info.model_hash_id` 가 말해 준다 (규격 100줄)
            #   ★★ 실측 09-01 — ★ 전에는 ★ 이름(`known_model_of`)이 먼저라
            #     ★ ★ 「ID.4」·「iX3」처럼 ★ **이름이 걸리는 것은 열쇠를 안 봤다**.
            #     ★ ★ ★ 그래서 ★ 7건이 ★ 차종 없이 남았다
            by_q = (query_target(site, env.get("url") or "")
                    or body_target(site, env))
            if by_q:
                row["target_key"] = by_q
            known = known_model_of((row.get("site_model") or "").split()[0]
                                   if row.get("site_model") else None)
            if known:
                row["site_model_group"] = known
            elif not by_q and env.get("endpoint") == "list":
                # ★★★★★ 09-03 (가이드 지시 ③) — ★ **사전에 한 번 더 물어본다.**
                #   ★ `known_model_of` 는 ★ 이름이 **그대로 들어 있는가**만 본다 —
                #   ★ ★ BMW 는 ★ 「X3 20 xDrive M Spt 블루 자동 휘발유」처럼
                #   ★ ★ ★ 차명이 ★ **글월 한 줄**로 온다.
                #   ★★ 실측 09-03 — ★ BMW 목록 820건 중 ★ **701건을 버렸다**.
                #     ★ ★ 그런데 ★ `target_key_of` 는 ★ 그 첫 낱말로
                #     ★ ★ ★ **`X3_IMPORT` 를 제대로 짚는다** (42건 확인).
                #   ★ 사전이 짚으면 ★ 그것을 쓴다 — ★ 못 짚으면 ★ 그때 버린다.
                #     ★ ★ 원문은 ★ 어느 쪽이든 ★ **남는다** (P3)
                from store.dictionary import target_key_of

                _first = (row.get("site_model") or "").split()
                _by_dict = target_key_of(site, _first[0]) if _first else None
                if _by_dict:
                    row["target_key"] = _by_dict
                else:
                    # ★ 우리 차종이 아니다 — ★ **원문은 남고** ★ core 에만 안 넣는다
                    got["  차종을 못 짚음"] += 1
                    continue
            if env.get("endpoint") == "detail":
                # ★★★★★ 09-01 — ★ **상세를 넣었으면 ★ 「받았다」고 적는다** (`V2-01`).
                #   ★ 목록에서 온 줄은 ★ `not_requested` 를 달고 온다 —
                #   ★ ★ 상세를 파싱해 행을 냈으면 ★ 그것은 ★ 더는 사실이 아니다.
                #   ★★ 실측 09-01 — ★ 볼보 148 · 렉서스 49 가
                #     ★ ★ 상세 봉투는 `ok` 인데 ★ 칸은 `not_requested` 였다
                row["detail_status"] = "ok"
            row["listing_id"] = resolve_listing_id(
                conn, site, row["source_id"], at)
            if not row.get("target_key"):
                fill_target_key(site, row)
            if not row.get("target_key"):
                # ★★★★★ 09-01 — ★ **「못 짚었다」를 ★ 「없다」로 저장하지 않는다**
                #   ★ (금지 12).  ★ 키를 빼면 ★ `upsert_core` 가 ★ 그 칸을 안 건드린다
                #   ★★ 실측 09-01 — ★ 옛 전량 목록 파일이 ★ 뒤에 와서
                #     ★ ★ 질의로 짚어 둔 `ID4_EV`·`IX3_EV` 7건을 ★ **다시 비웠다**
                row.pop("target_key", None)
            upsert_core(conn, split_pii(conn, row, site, key, at), at)
            got["  넣음"] += 1
            if rec:
                rec["listing_id"] = row["listing_id"]
                rec["collected_at"] = at
                upsert_child(conn, "core_record", rec, "p1", at)
                got["  이력"] += 1
            if pan is not None:
                upsert_child(conn, "core_inspection", {
                    "listing_id": row["listing_id"], "site": site,
                    "row_status": "ok",
                    "inspection_panel_json": json.dumps(pan,
                                                        ensure_ascii=False),
                    "collected_at": at}, "p1", at)
                got["  판"] += 1
    commit(conn)
    raw_link_raws(conn, site)
    commit(conn)
    for k, v in got.most_common():
        print(f"   {k:<20}{v:>7,}")
    n = conn.execute("SELECT COUNT(*) FROM core_listing WHERE site=?",
                     (site,)).fetchone()[0]
    print(f"★ 저장된 {site} 매물 {n:,}건")
    # ★★★★★ 0-4 — ★ 적재 DB 를 ★ **치운다.**  ★ 안 치우면 디스크가 찬다
    commit(load_conn)
    size = os.path.getsize(load_path) if os.path.isfile(load_path) else 0
    rows = load_conn.execute("SELECT COUNT(*) FROM raw_response").fetchone()[0]
    load_conn.close()
    if "--keep-load-db" in args:
        print(f"★ 적재 DB 를 남겼다 — {os.path.relpath(load_path, ROOT)}"
              f" ({rows:,}행 · {size / 2**20:,.1f} MiB)")
    else:
        os.remove(load_path)
        for tail in ("-wal", "-shm"):
            if os.path.isfile(load_path + tail):
                os.remove(load_path + tail)
        print(f"★ 적재 DB 를 치웠다 — {rows:,}행 · {size / 2**20:,.1f} MiB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
