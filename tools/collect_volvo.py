# -*- coding: utf-8 -*-
"""볼보 셀렉트 수집 — xhr-results 쪽넘김 (명령서 1a).

★ 한 쪽에 링크 12개가 상한이다 — ★ 12 면 다음 쪽이 있다
★ 총건수는 ★ 화면 글자 「총 N」에서 읽는다 — ★ 링크를 세면 늘 12 다
★ 슬러그로 거른다 — ★ 우리 차종만 (xc60 · s60 · xc40 · v60-cross-country)
★ 503 이 잦다 — ★ 재시도 (규격 _note)

★★ 08-26 — ★ `--detail` 을 붙였다 (마스터 지시 ② · 볼보 차례).
  ★ 전에는 「볼보는 상세가 없다」고 적혀 있었으나 ★ 규격 0b 가 「★ 뚫렸다」다.
  ★ 실측 08-26 — `/kr/vehicles/volvo/{모델}/{source_id}` → 200 · 70,924B

사용   python3.11 tools/collect_volvo.py             목록만
      python3.11 tools/collect_volvo.py --detail [N]  ★ 상세까지 (N건만)
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from store.raw import commit, open_db                       # noqa: E402

SITE_CODE = "volvo_selekt"
PAGE_LINKS = 12                # ★ 한 쪽 상한
MAX_PAGES = 40
RETRY, RETRY_WAIT = 3, 3.0
RE_LINK = re.compile(r'href="(/kr/vehicles/volvo/([a-z0-9-]+)/([^"/]+))"')
# ★★ 총건수 — ★ `data-found` 가 정본이다 (가이드 실측 · 명령서 1a).
#   ★ 없으면 ★ 받은 매물번호를 센다 — ★ 「총 N」 글자는 ★ **다른 수**다
#   ★ ★ 실측 08-24 — ★ 「총 180」이라 적혀 있으나 ★ 매물번호는 ★ 221개였다.
#     ★ ★ 180 을 믿었으면 ★ 41건을 조용히 버릴 뻔했다
RE_TOTAL = re.compile(r'data-found="(\d+)"')
def _known_name(target_key: str) -> str | None:
    """`target_key` → ★ 등록부가 아는 차종 이름 (`target_map.json`).

    ★ 사이트 이름과 우리 키를 잇는 표가 정본이다 — ★ 코드에 안 박는다
    """
    from store.dictionary import target_map

    for site in target_map():
        for name, one in target_map(site).items():
            if name.startswith("_") or not isinstance(one, dict):
                continue
            if one.get("target_key") == target_key:
                return name
    return None


def load_slugs(root: str = ROOT) -> dict:
    """우리 차종의 슬러그 — ★ `targets.json` 의 `site_query` 가 정본이다 (명령서 3-1).

    ★ 코드에 차종을 안 박는다 (S14 · 금지 6).  ★ 슬러그 → 우리가 쓰는 이름
    """
    import json as _j

    with open(os.path.join(root, "config", "targets.json"), encoding="utf-8") as f:
        rows = _j.load(f)
    out: dict = {}
    for key, one in rows.items():
        if key.startswith("_") or not isinstance(one, dict):
            continue
        q = (one.get("site_query") or {}).get(SITE_CODE)
        if not isinstance(q, dict):
            continue
        # ★ 우리가 쓰는 차종 이름은 ★ `target_map.json` 이 정본이다 (S14) —
        #   ★ `classify_stored` 가 그 이름으로 갈래를 찾는다
        for slug in q.get("slug") or ():
            out[str(slug)] = key
    return out


# ★ 옛 자리 — ★ `targets.json` 이 비면 그때만 쓴다
OURS_FALLBACK = {"xc60": "XC60", "s60": "S60", "xc40": "XC40",
                 "v60-cross-country": "V60 크로스 컨트리",
                 "v60cc": "V60 크로스 컨트리"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get(url: str, headers: dict, timeout: float) -> str | None:
    for _ in range(RETRY):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as res:
                return res.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503):
                return None
            time.sleep(RETRY_WAIT)
        except Exception:
            return None
    return None


def main() -> int:
    args = sys.argv[1:]
    with open(os.path.join(ROOT, "config", "endpoints.json"), encoding="utf-8") as f:
        cfg = json.load(f)[SITE_CODE]
    head = cfg.get("headers") or {}
    timeout = float(cfg.get("timeout_sec") or 40)
    interval = float(cfg.get("interval_sec") or 1.0)
    base = cfg["base_url"]

    said, seen = None, {}
    # ★★ 목록 쪽 원문을 들고 간다 (명령서 3-2 필수) —
    #   ★ 볼보는 ★ 상세가 없다.  ★ 목록 쪽이 ★ 원문의 전부다
    pages: list = []
    done = False
    for page in range(1, MAX_PAGES + 1):
        raw = _get(f"{base}/kr/vehicles/xhr-results/{page}", head, timeout)
        pages.append((f"{base}/kr/vehicles/xhr-results/{page}", raw))
        if not raw:
            print(f"  {page}쪽 — ★ 못 받았다.  멈춘다")
            break
        if said is None:
            got = RE_TOTAL.search(raw)
            said = int(got.group(1)) if got else None
        links = RE_LINK.findall(raw)
        for path, slug, sid in links:
            seen[sid] = (slug, base + path)
        # ★★★★ 08-29 (규격 `VOLVO_SELEKT_API.md` 개정 854 · 마스터가 재 주셨다) —
        #   ★ 「끝까지 받았나」의 근거는 ★ **빈 쪽**이다.
        #   ★★ 실측 08-29 (저장된 원문 20쪽) —
        #     ★ `data-found` 가 ★ **우리 창구에 아예 없다** (20쪽 전부 「없음」).
        #       ★ 마스터께서 보신 것은 ★ 모델 화면(`/kr/vehicles/volvo/s90?...`)이고
        #       ★ 우리는 ★ `xhr-results` 를 쓴다 — ★ 창구가 다르다.
        #     ★ ★ 그래서 ★ `said` 가 ★ **늘 None** 이었고 ★ 늘 안 매겼다.
        #   ★ 쪽마다 매물 12건이 고르게 오고 ★ 19쪽에 8건 · ★ 20쪽에 **0건**이다.
        #     ★ ★ 빈 쪽이 ★ 사이트가 「더 없다」고 말한 것이다 (보배와 같은 잣대).
        #   ★ 맞춤 확인 — ★ 우리가 센 `s90` 이 ★ **21건**이고
        #     ★ 마스터께서 브라우저에서 보신 `data-found` 도 ★ **21** 이다
        if not links:
            done = True                 # ★ 빈 쪽 — ★ 끝까지 받았다
            break
        time.sleep(interval)
    else:
        done = False                    # ★ MAX_PAGES 를 다 썼다 — ★ 끝이 아니다
    ours_map = load_slugs() or OURS_FALLBACK
    ours = {k: v for k, v in seen.items() if v[0] in ours_map}
    print(f"★ data-found {said if said is not None else '없다'} · "
          f"받은 매물번호 {len(seen)}건 · 쪽 {page}")
    if said is not None and said != len(seen):
        print(f"  ★ 어긋난다 — {said - len(seen):+d}건")
    print(f"★ 우리 대상 — {len(ours)}건 "
          f"(슬러그 {sorted({v[0] for v in ours.values()})} · "
          f"targets.json {len(ours_map)}가지)")
    if "--dry" in args or not ours:
        print("★ --dry 라 저장하지 않았다" if "--dry" in args else "★ 우리 대상이 없다")
        return 0

    from store.core import resolve_listing_id, upsert_core
    from store.raw import save_site_raw

    conn = open_db(os.path.join(ROOT, "carwatch.db"))
    at = _now()
    # ★★ 원문을 남긴다 (명령서 3-2 필수) — ★ 「갈래를 넓히시면 다시 판다」.
    #   ★ 쪽마다 한 줄이다 — ★ 매물번호가 없으니 ★ 겹침을 안 접는다
    for _u, _b in pages:
        save_site_raw(conn, SITE_CODE, "list", None, _u, _b, at)
    for sid, (slug, url) in ours.items():
        row = {"site": SITE_CODE, "source_id": sid, "price_unit": "won",
               # ★ 사전이 아는 이름으로 적는다 — ★ 없으면 target_key 를 그대로
               "site_model_group": _known_name(ours_map[slug]) or ours_map[slug],
               "site_model": slug,
               "detail_status": "not_requested"}
        row["listing_id"] = resolve_listing_id(conn, SITE_CODE, sid, at)
        upsert_core(conn, row, at)
    commit(conn)
    # ★★★★★ 08-29 (개정 838 · 오판 161) — ★ 팔린 차를 거른다 (`S46-117`).
    #   ★ 「끝까지 받았나」 — ★ 사이트가 적어 준 `data-found`(said)와
    #     ★ 받은 매물번호 수가 ★ **같아야** 참이다.
    #   ★ 못 받은 쪽이 있거나 · 수가 어긋나면 ★ 안 매긴다 —
    #     ★ 반만 받고 매기면 ★ 산 차를 죽인다
    from store.core import sweep_gone_groups

    # ★ 슬러그(차종)별로 몇 건을 받았는지 낸다 — ★ 마스터께서 차종별로 견주라 하셨다.
    #   ★ `data-found` 가 우리 창구에 없으므로 ★ 이 수를 모델 화면과 견주면 된다
    by_slug: dict = {}
    for _sid, (_slug, _u) in seen.items():
        by_slug[_slug] = by_slug.get(_slug, 0) + 1
    print("★ 슬러그별 받은 수 — " + " · ".join(
        f"{k} {v}" for k, v in sorted(by_slug.items(), key=lambda x: -x[1])))
    _got = sweep_gone_groups(conn, SITE_CODE, [(done, set(ours))], at)
    print(f"★ 목록에 없어 gone 으로 매긴 것 {sum(_got.values())}건 "
          f"({len(_got)}차종) · 끝까지 받았나 {'예' if done else '아니오'}"
          f" (빈 쪽까지 갔나)")
    if not done:
        print("  ★ 빈 쪽까지 못 갔다 — 안 매겼다.  반만 보고 매기면 산 차를 죽인다")
    n = conn.execute("SELECT COUNT(*) FROM core_listing WHERE site=?",
                     (SITE_CODE,)).fetchone()[0]
    print(f"★ 저장 {len(ours)}건 · 저장된 볼보 매물 {n:,}건")

    if "--detail" not in args:
        print("★ 상세는 --detail 로 받는다")
        return 0

    # ★★ 상세 (마스터 지시 08-26 ② · 규격 0b).  ★ 원문을 먼저 남긴다 (P3)
    from parse.volvo_selekt.mapping import parse_detail, photos

    i = args.index("--detail")
    limit = int(args[i + 1]) if i + 1 < len(args) and args[i + 1].isdigit() else 0
    todo = list(ours.items())[:limit] if limit else list(ours.items())
    got = {"정상": 0, "못 받음": 0}
    for sid, (_slug, url) in todo:
        body = _get(url, head, timeout)
        if not body:
            # ★ 못 받은 것을 ★ 「없음」으로 저장하지 않는다 (금지 12)
            got["못 받음"] += 1
            time.sleep(interval)
            continue
        save_site_raw(conn, SITE_CODE, "detail", sid, url, body, at)
        # ★★ 08-29 (개정 857) — ★ 곧바로 커밋한다.
        #   ★ 통신·`sleep` 이 ★ 트랜잭션 안에 들면 ★ 잠금 창이 분 단위가 된다
        #   (KB 실측 — 100건 × 1.2초 = 120초 · 잠금 38.4초 · locked 로 죽었다)
        commit(conn)
        row = parse_detail(body, SITE_CODE, sid)
        if row:
            row["listing_id"] = resolve_listing_id(conn, SITE_CODE, sid, at)
            pics = photos(body, sid)
            if pics:
                # ★ 상대경로다 — ★ 주소의 정본은 endpoints.json 의 base_url 이다
                pics = [base + one if one.startswith("/") else one for one in pics]
                row["photo_main"] = pics[0]
                row["photo_list_json"] = json.dumps(pics, ensure_ascii=False)
            upsert_core(conn, row, at)
            got["정상"] += 1
        # ★ 자기 전에 커밋한다 — ★ 넣기가 sleep 을 넘지 않게 (개정 857)
        commit(conn)
        time.sleep(interval)
    commit(conn)
    print("★ 상세 — " + " · ".join(f"{k} {v}" for k, v in got.items()))
    from tools.daily_enqueue import enqueue_after_store
    enqueue_after_store(os.path.join(ROOT, "carwatch.db"), SITE_CODE,
                        got.get("정상", 0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
