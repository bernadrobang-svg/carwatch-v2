#!/usr/bin/env python3.11
"""보배드림 수집 (명령서 7단계 · `docs/BOBAEDREAM_API.md`).

    python3.11 tools/collect_bobaedream.py --pages N [--dry] [--interval S]

지시서   `docs/BOBAEDREAM_API.md` · 명령서 3-0 「전량을 받지 않는다」
근거     ★ 목록이 ★ 차명을 준다 — ★ 우리 차종만 골라 ★ 상세를 받는다.
        ★ `maker_no` 코드표는 ★ facet 을 못 받았다 (규격 5장) — ★ 지어내지 않는다.
        ★ 대신 ★ 목록의 차명으로 ★ 미리 거른다.  ★ 상세를 3,307번 부르지 않는다
값규칙   ★ 「무사고」 문구를 ★ 쓰지 않는다 — ★ 판매자 글이다 (규격 3장 ①)
        ★ 보험이력 「미공개」는 ★ NULL 이다.  ★ 0 이 아니다
금지     ★ `www.` 로 부르는 것 (EUC-KR · 다른 화면이다)
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

from adapters.bobaedream import (  # noqa: E402
    SITE_CODE,
    BobaedreamAdapter,
    load_config,
)
from parse.bobaedream.mapping import list_items  # noqa: E402
from store.dictionary import target_map  # noqa: E402
# ★★★★★ 09-01 마스터 지시 — ★ 받기는 ★ **파일만** 쓴다 (`S46-204`)
from store.rawfile import save as save_file  # noqa: E402

MAX_PAGES = 80


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get(url: str, headers: dict, timeout: float,
         endpoint: str | None = None, source_id=None,
         page: int | None = None) -> str | None:
    """★ 받는다.  ★ 못 받으면 `None` 이다.

    ★★★★★ 09-05 (지시 1번 · `S46-278` · `STEP 53-⑤`) — ★ **막힌 응답도 원문이다.**
      ★ 전에는 ★ 실패하면 ★ **몸통을 버렸다** — ★ 「어떻게 막혔나」를 뒤에 못 봤다
    """
    from collect.rawfetch import keep_blocked

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as f:   # noqa: S310
            # ★ 모바일은 UTF-8 이다 (규격 1장).  ★ PC(EUC-KR)와 섞지 않는다
            return f.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        if endpoint:
            try:
                keep_blocked(SITE_CODE, endpoint, source_id, url, e.read(),
                             page=page, http_code=e.code, root=ROOT)
            except OSError:
                pass
        return None
    except OSError:
        return None


def target_names(root: str = ROOT) -> list:
    """우리가 보는 차종 이름.  ★ `target_map.json` 이 정본이다 — ★ 코드에 안 박는다."""
    out = set()
    for site in target_map():
        for name in target_map(site):
            out.add(name)
    return sorted(out, key=len, reverse=True)


def wanted(title: str, names: list) -> str | None:
    """목록의 차명에 ★ 우리 차종 이름이 들어 있는가.  ★ 없으면 None."""
    for n in names:
        if n and n in (title or ""):
            return n
    return None


def _elapsed(year_month: str | None, at: datetime) -> int | None:
    if not year_month or len(str(year_month)) < 6:
        return None
    y, m = int(str(year_month)[:4]), int(str(year_month)[4:6])
    return max(0, (at.year - y) * 12 + (at.month - m))


def load_filters(root: str = ROOT) -> list:
    """좁히는 코드 — ★ `targets.json` 의 `site_query` 가 정본이다 (명령서 3-1).

    ★ 같은 부름을 두 번 하지 않는다 — ★ 차종 둘이 같은 코드를 쓸 수 있다
    """
    import json as _j

    with open(os.path.join(root, "config", "targets.json"), encoding="utf-8") as f:
        rows = _j.load(f)
    got, seen = [], set()
    for key, one in rows.items():
        if key.startswith("_") or not isinstance(one, dict):
            continue
        # ★★★★★ 09-02 마스터 실측 — ★ 「★ 실패 1건 — `G80_25T/list` 저장 500 …
        #   ★ 뭐지?」  ★ `G80_25T` 는 ★ 09-01 에 **쉬게 한 차종**이다 —
        #   ★ ★ 받으러 갈 까닭이 없었다.  ★ 쉬는 차종은 ★ **안 받는다** (`S46-215`).
        #   ★ 매물을 지우지 않는다 — ★ 받지만 않는다
        if not one.get("active"):
            continue
        q = (one.get("site_query") or {}).get(SITE_CODE)
        if not isinstance(q, dict) or not q.get("maker_no"):
            continue
        # ★★ 실측 08-25 — ★ `model_no` 를 함께 주면 ★ **목록이 빈다** (매물 0).
        #   ★ ★ `maker_no` 만 주면 ★ 먹는다 — ★ 제네시스 1010 → 매물 50 · 차명 확인
        #   ★ ★ 그러므로 ★ 제조사로 좁히고 ★ 차종은 ★ 우리가 이름으로 거른다
        mark = q["maker_no"]
        if mark in seen:
            continue
        seen.add(mark)
        got.append({"for": key, "maker_no": q["maker_no"], "model_no": None})
    return got


def _walk_plan(groups: list, pages: int):
    """★ 어느 조건으로 ★ 몇 쪽까지 도는가.  ★ 조건이 없으면 ★ 전량이다."""
    if not groups:
        for page in range(1, pages + 1):
            yield None, page
        return
    for g in groups:
        for page in range(1, pages + 1):
            yield g, page


def main() -> int:
    args = sys.argv[1:]

    def opt(name: str, default):
        if name in args:
            i = args.index(name)
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                return type(default)(args[i + 1])
        return default

    cfg = load_config(ROOT)
    gap = opt("--interval", 0.0) or float(cfg.get("interval_sec") or 1.2)
    adapter = BobaedreamAdapter(cfg)
    names = target_names()
    # ★★★★ 08-29 (규격 `docs/BOBAEDREAM_API.md` · 마스터가 정했다) —
    #   ★ **빈 쪽이 오면 끝이다.**  ★ 우리가 쪽 수를 정하지 않는다.
    #   ★ 보배가 33건뿐이라 ★ 다섯 쪽 한정은 뜻이 없었다.
    #   ★ 기본값에서 `--pages` 를 없앤다 — ★ 빈 쪽까지 간다 (MAX_PAGES 가 울타리다).
    #   ★ 사람이 `--pages` 를 준 때는 ★ 시험용이라 ★ `done=False` 다
    pages = opt("--pages", MAX_PAGES)
    groups = load_filters()
    if groups:
        print(f"★ 좁혀 받는다 — 차종 {len(groups)}종 "
              f"(maker_no ＋ model_no · 가이드 확인 08-25)")
    else:
        print(f"★ 우리 차종 이름 {len(names)}가지로 목록에서 미리 거른다")

    hits, seen, scanned = [], set(), 0
    # ★ 조건마다 ★ 「빈 쪽을 만났나」를 센다 — ★ 그것이 끝의 근거다
    ended: set = set()
    walked: set = set()
    for g, page in _walk_plan(groups, min(pages, MAX_PAGES)):
        gk = (g or {}).get("model_no") or (g or {}).get("maker_no") or "*"
        if gk in ended:
            continue                    # ★ 이 조건은 이미 끝났다
        walked.add(gk)
        req = adapter.list_url(None, page=page,
                              maker=g.get("maker_no") if g else None,
                              model=g.get("model_no") if g else None)
        body = _get(req.url, req.headers, req.timeout_sec,
                    endpoint="list")
        if body is None:
            print(f"  {page}쪽 — ★ 못 받았다.  ★ 저장하지 않는다")
            break                       # ★ 못 받았다 — ★ `ended` 에 안 넣는다
        got = list_items(body)
        if not got:
            # ★★ 빈 쪽 — ★ 사이트가 「더 없다」고 말한 것이다.  ★ 이 조건은 끝났다
            ended.add(gk)
            continue
        for no, title in got:
            if no in seen:
                continue
            seen.add(no)
            scanned += 1
            name = wanted(title, names)
            if name:
                hits.append((no, title, name))
        time.sleep(gap)
    print(f"목록 {page}쪽 · 훑은 매물 {scanned}건 · ★ 우리 차종 {len(hits)}건")
    for no, title, name in hits[:10]:
        print(f"    {no}  [{name}] {title[:44]}")
    if not hits:
        print("★ 이 쪽들에 우리 차종이 없다")
        return 0
    if "--dry" in args:
        print("★ --dry 라 상세를 안 받았다")
        return 0

    # ★★★★★ 09-01 마스터 지시 — ★ **받기 걸음은 파일만 쓴다.  ★ DB 를 안 연다.**
    #   ★ 넣기는 ★ `python3.11 tools/load_raw.py bobaedream --write` 가 한다
    #   ★★ 보배는 ★ 09-01 마스터 확정으로 ★ **쉰다** (`sites.json` `paused`) —
    #     ★ 그래도 ★ 받는 길은 ★ 같은 꼴로 남겨 둔다 (다시 켤 때를 위해)
    at = _now()
    kept = {"저장": 0, "못 받음": 0}
    for no, _title, _name in hits:
        d = adapter.detail_urls(no)[0]
        html = _get(d.url, d.headers, d.timeout_sec,
                    endpoint="detail", source_id=no)
        if not html:
            kept["못 받음"] += 1
            time.sleep(gap)
            continue
        # ★★ 원문을 남긴다 (명령서 3-2 필수) — ★ 「갈래를 넓히시면 다시 판다」
        save_file(SITE_CODE, "detail", no, d.url, html, at, root=ROOT)
        # ★ 목록이 준 차명은 ★ 상세에 없다 — ★ 곁들여 남긴다 (지어낸 것이 아니다)
        save_file(SITE_CODE, "list", no, d.url, json.dumps(
            {"source_id": no, "title": _title, "site_model_group": _name},
            ensure_ascii=False), at, root=ROOT)
        kept["저장"] += 1
        time.sleep(gap)
    print("★ " + " · ".join(f"{k} {v}" for k, v in kept.items()))
    print(f"★ 넣기 — python3.11 tools/load_raw.py {SITE_CODE} --write")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
