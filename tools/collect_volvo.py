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

# ★★★★★ 09-01 마스터 지시 — ★ 받기는 ★ **파일만** 쓴다 (`S46-204`)
from store.rawfile import save as save_file  # noqa: E402

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
        # ★★★★★ 09-02 — ★ **쉬는 차종은 안 받는다** (`S46-215` · 마스터 실측).
        #   ★ 매물을 지우지 않는다 — ★ 받으러 가지만 않는다
        if not one.get("active"):
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

    # ★★★★★ 09-01 마스터 지시 — ★ **받기 걸음은 파일만 쓴다.  ★ DB 를 안 연다.**
    #   ★ 「★ 넣기 걸음은 그 폴더를 읽어 `raw_response` ＋ `core_listing` 에 넣는다」
    #   ★★ `open_db`·`upsert_core`·`sweep_gone_groups` 를 ★ **뺐다** —
    #     ★ 넣기는 ★ `python3.11 tools/load_raw.py volvo_selekt --write`
    at = _now()
    # ★★ 원문을 남긴다 (명령서 3-2 필수) — ★ 「갈래를 넓히시면 다시 판다」.
    #   ★ 쪽마다 한 줄이다 — ★ 매물번호가 없으니 ★ 겹침을 안 접는다
    for _n, (_u, _b) in enumerate(pages, 1):
        # ★★★★★ 09-01 — ★ 이름을 ★ `list` 로 맞춘다 (`S46-97`).
        #   ★ `listpage` 는 ★ 나만 쓰던 이름이라
        #   ★ ★ 「매물 봉투가 아니다」 목록에서 빠져
        #   ★ ★ ★ 「source_id 가 비었다」로 20건이 걸렸다
        save_file(SITE_CODE, "list", None, _u, _b, at, page=_n, root=ROOT)
    # ★★ 목록에서 뽑은 줄은 ★ 매물마다 한 파일로 남긴다 —
    #   ★ 볼보 목록은 ★ 매물번호와 슬러그만 준다 (나머지는 상세가 준다).
    #   ★ ★ 줄을 **만드는 자리**는 ★ `parse/volvo_selekt/mapping.py` 다 (여기가 아니다)
    for sid, (slug, url) in ours.items():
        save_file(SITE_CODE, "list", sid, url, json.dumps({
            "source_id": sid, "slug": slug, "url": url,
            "site_model_group": _known_name(ours_map[slug]) or ours_map[slug],
        }, ensure_ascii=False), at, root=ROOT)
    by_slug: dict = {}
    for _sid, (_slug, _u) in seen.items():
        by_slug[_slug] = by_slug.get(_slug, 0) + 1
    print("★ 슬러그별 받은 수 — " + " · ".join(
        f"{k} {v}" for k, v in sorted(by_slug.items(), key=lambda x: -x[1])))
    print(f"★ 목록 {len(ours)}건을 파일로 남겼다 — "
          f"raw/{SITE_CODE}/list/{at[:10]}/  ·  끝까지 받았나 "
          f"{'예' if done else '아니오'}")
    # ★★★★★ 09-01 — ★ 「목록에 없으면 죽인다」는 ★ **여기서 안 한다.**
    #   ★ 그 자리는 ★ `tools/list_diff_check.py` 다 — ★ 상세로 확인한 뒤에 죽인다
    #   ★ ★ 마스터 지시 — 「★ 목록 대조해서 사라지면 ★ 상세를 조회해서 판매상태를 본다」
    print(f"★ 넣기 — python3.11 tools/load_raw.py {SITE_CODE} --write")


    # ★★★★★ 08-30 (마스터 지시 4·5 · 규격 0b · 개정 887) —
    #   ★ 앞서는 ★ `--detail` 을 줘야만 상세를 받았다.  ★ 그래서
    #   ★ ★ 값·주행·연식이 ★ **목록에는 없고** ★ 상세에만 있는데
    #   ★ ★ **15건이 값이 빈 채로 남아 있었다** (`status='new'` · `target_key` 없음).
    #   ★ ★ 그 15건은 ★ 오늘 목록에 ★ **다 있다** — ★ 죽을 것이 아니라
    #   ★ ★ **상세를 못 받은 것**이었다 (눌러서 확인 08-30).
    #   ★ 이제 ★ **원문이 없는 것만** 스스로 받는다 — ★ 전건을 다시 안 받는다.
    #   ★ ★ `--detail` 을 주면 ★ 옛 꼴대로 ★ 전건을 받는다
    limit = 0
    if "--detail" in args:
        i = args.index("--detail")
        limit = int(args[i + 1]) if i + 1 < len(args) and args[i + 1].isdigit() else 0
        todo = list(ours.items())[:limit] if limit else list(ours.items())
    else:
        # ★★★★★ 09-01 — ★ **이미 받은 것은 파일로 안다** (DB 를 안 연다).
        #   ★ 앞서는 ★ `raw_response` 를 물어 봤다 — ★ 그것이 DB 를 여는 자리였다
        from store.rawfile import walk as _walk

        have = {os.path.basename(x).split("__")[0][:-5]
                for x in _walk(site=SITE_CODE, endpoint="detail", root=ROOT)}
        todo = [(sid, v) for sid, v in ours.items() if sid not in have]
        print(f"★ 상세 — 받을 것 {len(todo)}건 "
              f"(우리 대상 {len(ours)}건 중 · 원문 파일이 있는 것 "
              f"{len(ours) - len(todo)}건은 안 받는다)")
        if not todo:
            return 0
    got = {"정상": 0, "못 받음": 0}
    for sid, (_slug, url) in todo:
        body = _get(url, head, timeout)
        if not body:
            # ★ 못 받은 것을 ★ 「없음」으로 저장하지 않는다 (금지 12)
            got["못 받음"] += 1
            time.sleep(interval)
            continue
        save_file(SITE_CODE, "detail", sid, url, body, at, root=ROOT)
        got["정상"] += 1
        time.sleep(interval)
    print("★ 상세 — " + " · ".join(f"{k} {v}" for k, v in got.items()))
    print(f"★ 넣기 — python3.11 tools/load_raw.py {SITE_CODE} --write")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
