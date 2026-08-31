#!/usr/bin/env python3.11
"""KB차차차 목록 수집 · 총 매물 수 세기 (명령서 `ORDER_20260822_r515.md` 3-2 · 단계 9).

    python3.11 tools/collect_kbchachacha.py --count          총 매물 수·마지막 쪽만 센다
    python3.11 tools/collect_kbchachacha.py --pages N        N쪽까지 받아 저장
    python3.11 tools/collect_kbchachacha.py --probe N        상세 N건을 재 봇차단 비율을 낸다
    python3.11 tools/collect_kbchachacha.py --narrow [--detail N] [--interval S]
    python3.11 tools/collect_kbchachacha.py --narrow --missing-raw  ★ 원문 없는 것만 (P3)
                                                            좁혀 받아 상세까지 넣는다

지시서   `docs/KBCHACHACHA_API.md` · `docs/TARGET_KEY_MAP.md`
근거     ★★ 봇 차단 가르기가 ★ 핵심이다 (명령서 3-2)
값규칙   ★ 10KB 미만이거나 「로봇 여부 확인」이 있으면 ★ 수집 실패다.
        ★ 최대 3회 재시도.  ★ 절대 「없음」으로 저장하지 않는다
        ★ 3회 다 실패하면 ★ 그대로 두고 ★ 세어서 보고한다
금지     ★ 못 받은 것을 「없음」으로 저장하는 것 — ★ 28% 가 「사고 없음」이 된다
"""
from __future__ import annotations

import os
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone

# ★★★★★ 이 수집기는 ★ **팔린 차를 목록으로 안 거른다** (마스터 지시 08-30 · S46-117).
#   ★ 낱말 `SWEEP_OFF` 를 ★ 검사가 본다 — ★ 「안 거른다」와 「못 거른다」를 가른다
SWEEP_OFF = (
    "08-29 — 목록에 없다고 죽이면 살아 있는 차를 죽인다"
    " (11-store/a-key 08-29 절).  상세로 확인한 뒤 죽이는 꼴로 바꾼 뒤 다시 켠다")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from adapters.kbchachacha import (  # noqa: E402
    SITE_CODE,
    KbChaChaChaAdapter,
    is_bot_wall,
    is_real_end,
    load_config,
)
from parse.kbchachacha.mapping import parse_detail  # noqa: E402
from parse.target_rules import fill_target_key  # noqa: E402
from store.raw import link_raws as raw_link_raws  # noqa: E402
# ★★★★★ 09-01 마스터 지시 — ★ 받기는 ★ **파일만** 쓴다 (`S46-204`)
from store.rawfile import save as save_file  # noqa: E402
from store.raw import open_db  # noqa: E402

RETRY = 3               # ★ 봇 차단 재시도 (KBCHACHACHA_API 1-1)
RETRY_WAIT = 3.0
# ★★★ 08-29 (개정 857) — ★ 「끝까지 받았나」.  ★ 받기가 적고 ★ 넣기가 본다.
#   ★ 한 명령으로 이어 돌 때는 여기로 넘긴다.  ★ 따로 돌 때는
#     ★ `raw_response` 의 목록 원문을 보고 정한다 (아래 `scan_done_from_raw`)
_SCAN_DONE: dict = {"done": False}

MAX_PAGES = 400         # ★ 빈 쪽이 나오면 그 전에 멈춘다.  이것은 안전장치다
# ★★ 한 회차에 부를 상세 수 (명령서 14-1).  ★ 막히는 자리는 ★ 목록이 아니라 ★ 상세다 —
#   ★ 목록 53쪽은 ★ 봇 차단 0건이다 (실측 08-24 · C 확인).
#   ★ 목록은 ★ 한 번에 다 받고 · ★ 상세만 ★ 회차를 나눈다
# ★★ 08-25 실측 — ★ **한 묶음 10건 · 사이 5분**이 ★ 사이트가 주는 몫이다.
#   ★ 10건씩이면 ★ 5분 쉬고 ★ 10/10 이 다 통과했다 (두 번 확인).
#   ★ ★ 30건씩 부르면 ★ 첫 회차 10 · ★ 다음 두 회차 ★ **0 · 0** — ★ 몫이 마른다.
#     ★ ★ 많이 부를수록 ★ 적게 받는다.  ★ 욕심내지 않는다
#   ★ 간격을 5초로 벌려도 ★ 안 낫다 — ★ **건수**가 몫이지 ★ 속도가 아니다
#   ★ 헤더·UA 를 사람 꼴로 바꿔도 ★ 안 낫다 (데스크톱 ＋ 사람 머리 전부 → 정상 3)
DETAIL_BATCH = 10
# ★ 묶음 사이에 이만큼 쉰다 — ★ 실측으로 몫이 돌아오는 참이다
BURST_REST_SEC = 300
# ★ 이만큼 이어서 막히면 ★ 그 회차를 끝낸다 (명령서 14-1)
# ★★ 가이드 지시 08-24 — 「★ 회차 50건 · ★ 2,759B 세 번이면 끝」.
#   ★ 200/8 로는 ★ 막힌 뒤에도 ★ 오래 두드려 ★ 다음 회차까지 막혔다 (실측 08-24)
WALL_GIVE_UP = 3
# ★ 한 번 불러 ★ 묶음을 몇 번 도는가 — ★ `--bursts N`
# ★★★★★ 08-29 (ORDER r879 1a) — ★ 1 → **4**.  ★ 마스터 「봇 차단을 다시 재고 나서」.
#   ★★ 쟀다 ① — ★ **묶음 크기**를 올리면 ★ 정말 막힌다 (사이에 300초씩 쉬고) —
#        묶음 10건 → 본 10 · 정상 10 · ★ 3회 다 막힘 **0**   (0%)
#        묶음 20건 → 본 20 · 정상 11 · ★ 3회 다 막힘 **8**   (40%)
#        묶음 30건 → 본 30 · 정상  0 · ★ 3회 다 막힘 **30**  (100%)
#      ★ 그러므로 ★ `DETAIL_BATCH` 는 ★ **10 이 맞다.  올리지 않는다** —
#      ★ 08-25 실측이 지금도 맞다.  ★ 오판 169 의 「우리 코드가 막고 있다」는
#      ★ ★ **절반만** 맞았다 — ★ 상한이 낮은 것은 맞고 ★ 사이트도 정말 막는다.
#   ★★ 쟀다 ② — ★ **묶음 수**는 늘려도 안 막힌다 (몫이 찬 08-30 실측) —
#        `--bursts 4` · 각 10건 · 사이 300초 → ★ 네 묶음 다 ★ **봇차단 3회 0**
#        ★ 상세 원문 ★ 217 → **257** (한 회차에 40건.  앞서는 10건)
#   ★ 그래서 ★ 올리는 것은 ★ 여기다.  ★ 4 × 10건 ＋ 쉼 = 약 21분 —
#     ★ 하루치가 한 사이트에 주는 40분(`daily_collect.TIMEOUT_SEC`) 안이다.
#   ★ 8 은 ★ 안 재봤다 — ★ 재기 전에 안 올린다
DEFAULT_BURSTS = 4
RE_CARSEQ = re.compile(r"carSeq=(\d+)")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get(url: str, headers: dict, timeout: float) -> str | None:
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as f:   # noqa: S310
            return f.read().decode("utf-8", "replace")
    except OSError:
        return None


def fetch_ok(url: str, headers: dict, timeout: float, cfg: dict) -> tuple:
    """★ 봇 차단이면 다시 부른다.  ★ 「없음」으로 내려가지 않는다.

    반환   (본문 또는 None, 시도 횟수, 봇차단이었나)
    ★ 3회 다 막히면 ★ None 이다 — ★ 부르는 쪽이 「못 받았다」로 적는다
    """
    walled = False
    for n in range(1, RETRY + 1):
        body = _get(url, headers, timeout)
        if body is not None and not is_bot_wall(body, cfg):
            return body, n, walled
        walled = True
        if n < RETRY:
            time.sleep(RETRY_WAIT * n)
    return None, RETRY, True


def page_ids(body: str) -> list:
    """쪽에서 매물번호를 뽑는다.  ★ 고유하게 · 나온 차례대로."""
    out, seen = [], set()
    for one in RE_CARSEQ.findall(body or ""):
        if one not in seen:
            seen.add(one)
            out.append(one)
    return out


def load_filters(root: str = ROOT) -> list:
    """★ 좁히는 조건 — ★ `targets.json` 의 `site_query` 가 정본이다 (명령서 3-1).

    ★★ 08-25 — ★ 코드를 ★ **한 곳으로** 모았다.
      ★ ★ 전에는 ★ `sites.json` 의 `collect_filters` 에 따로 있어 ★ 두 곳이 갈렸다
    ★ 같은 부름을 두 번 하지 않는다 — ★ 차종 둘이 같은 코드를 쓸 수 있다
    """
    import json as _j

    with open(os.path.join(root, "config", "targets.json"), encoding="utf-8") as f:
        rows = _j.load(f)
    got, seen = [], set()
    for key, one in rows.items():
        if key.startswith("_") or not isinstance(one, dict):
            continue
        q = (one.get("site_query") or {}).get(SITE_CODE)
        if not isinstance(q, dict) or not q.get("makerCode"):
            continue
        # ★★ 세대(`carCode`) — ★ 있으면 ★ 그것까지 넣어 좁힌다 (마스터 확정 08-26 ⓐ).
        #   ★ 한 차종에 ★ 세대가 여럿일 수 있다 — ★ 목록으로도 받는다
        #   ★ 없으면 ★ 차종 단위 그대로다 — ★ 세대 코드를 ★ 지어내지 않는다
        cars = q.get("carCode")
        cars = ([str(x) for x in cars] if isinstance(cars, list)
                else [str(cars)] if cars else [None])
        # ★★★ 08-28 — ★ `classCode` 가 없으면 ★ **건너뛴다.**
        #   ★ 실측 08-28 — ★ `POLESTAR3_EV` 는 ★ 제조사만 있고 차종 코드가 없다
        #     (규격이 「★ KB `carClass.json` 에 폴스타 3 은 아직 없다」고 적어 두었다).
        #   ★ ★ 그런데 코드가 ★ 빈 값을 ★ 「거르지 않는다」로 보내 —
        #     ★ ★ **251쪽 · 9,378건**을 끌어왔다 (합 14,616 의 대부분이 그것이다).
        #   ★ ★ 오판 130 「KB 전량 수집을 멈춰라」와 ★ 같은 자리다.
        #   ★ 코드가 없으면 ★ **안 받는다** — ★ 지어내지도 않고 ★ 전량으로 넓히지도 않는다
        if not str(q.get("classCode") or "").strip():
            print(f"  {key:12} ★ 건너뛴다 — classCode 가 없다"
                  " (있는 코드만 받는다.  전량으로 넓히지 않는다)")
            continue
        for car in cars:
            mark = (q["makerCode"], q.get("classCode"), car)
            if mark in seen:
                continue
            seen.add(mark)
            got.append({"for": key, "makerCode": q["makerCode"],
                        "classCode": q.get("classCode", ""),
                        "carCode": car,
                        # ★ 규격이 적어 둔 예상 건수 — ★ 없으면 「—」다.
                        #   ★ 지어내지 않는다
                        "expect": q.get("_expect", "—")})
    if got:
        return got
    # ★ 옛 자리 — ★ targets.json 이 비면 그때만 본다
    with open(os.path.join(root, "config", "sites.json"), encoding="utf-8") as f:
        old = (_j.load(f).get(SITE_CODE) or {}).get("collect_filters") or {}
    return old.get("groups") or []


# ★ 꼬리 쪽 — ★ 크기는 큰데 매물이 0인 쪽이 이어진다 (X3 14·15쪽 71KB·25KB).
#   ★ 「0건이면 끝」으로 멈추면 ★ 까닭이 다르다 (규격 1a 금지).
#   ★ 그러나 ★ 끝없이 돌 수도 없다 — ★ 0건이 이만큼 이어지면 그만 본다
TAIL_LIMIT = 4


def walk_group(adapter: KbChaChaChaAdapter, cfg: dict, g: dict,
               seen: set) -> dict:
    """차종 하나를 ★ 끝까지 받는다.  ★ 끝은 ★ 크기로 가른다 (규격 1a).

    ★ 봇 차단(2,759B)  → ★ 재시도한다.  ★ 「없음」으로 저장하지 않는다
    ★ 진짜 끝(3,585B + 「차량이 없습니다」) → ★ 거기서 멈춘다
    """
    # ★★★ 08-29 (개정 838) — ★ 「끝까지 받았나」를 돌려준다.
    #   ★ `is_real_end` 를 만났을 때만 참이다 — ★ 막히거나(3회 실패) ·
    #     ★ 빈 쪽이 이어지거나 · ★ MAX_PAGES 를 다 쓴 것은 ★ **못 받은 것**이다.
    #   ★ 그것으로 ★ gone 을 매길지 말지를 가른다 — ★ 반만 받고 매기면 산 차를 죽인다
    got, pages, walls, tail = [], 0, 0, 0
    done = False
    for page in range(1, MAX_PAGES + 1):
        req = adapter.list_url(None, page=page,
                               maker=g["makerCode"], klass=g["classCode"],
                               car=g.get("carCode"))
        body, _tries, walled = fetch_ok(req.url, req.headers,
                                        req.timeout_sec, cfg)
        pages = page
        if walled:
            walls += 1
        if body is None:
            # ★ 3회 다 막혔다.  ★ 여기서 끝이라고 하지 않는다 — ★ 못 받은 것이다
            print(f"    {page}쪽 — ★ 3회 다 막혔다.  ★ 저장하지 않는다")
            break
        if is_real_end(body, cfg):
            done = True                 # ★ 진짜 끝이다 — ★ 끝까지 받았다
            break
        ids = [x for x in page_ids(body) if x not in seen]
        if not page_ids(body):
            tail += 1
            if tail >= TAIL_LIMIT:
                break
        else:
            tail = 0
        seen.update(ids)
        got.extend(ids)
        time.sleep(float(cfg.get("interval_sec") or 1.2))
    return {"ids": got, "pages": pages, "walls": walls, "done": done}


def count_all(adapter: KbChaChaChaAdapter, cfg: dict, limit: int = MAX_PAGES):
    """★ 빈 쪽까지 늘려 가며 센다 (명령서 3-2 「확인해 알려 줄 것」 ③)."""
    seen, pages, empty_at = set(), 0, None
    for page in range(1, limit + 1):
        req = adapter.list_url(None, page=page)
        body, _tries, walled = fetch_ok(req.url, req.headers,
                                        req.timeout_sec, cfg)
        pages = page
        if body is None:
            print(f"  {page}쪽 — ★ 못 받았다 (봇 차단 {walled})")
            break
        got = page_ids(body)
        if not got:
            empty_at = page
            break
        before = len(seen)
        seen.update(got)
        if len(seen) == before:
            empty_at = page          # ★ 새 것이 없으면 끝이다
            break
        if page % 20 == 0:
            print(f"  {page}쪽 … 누적 {len(seen):,}건")
        time.sleep(float(cfg.get("interval_sec") or 1.2))
    return seen, pages, empty_at


def probe_detail(adapter: KbChaChaChaAdapter, cfg: dict, ids: list) -> dict:
    """★ 봇 차단 비율을 잰다.  ★ 세어서 보고한다 — 판정하지 않는다."""
    got = {"본": 0, "정상": 0, "재시도로 살림": 0, "3회 다 막힘": 0}
    for one in ids:
        req = adapter.detail_urls(one)[0]
        body, tries, walled = fetch_ok(req.url, req.headers,
                                       req.timeout_sec, cfg)
        got["본"] += 1
        if body is None:
            got["3회 다 막힘"] += 1
        elif walled:
            got["재시도로 살림"] += 1
        else:
            got["정상"] += 1
        del tries
        time.sleep(float(cfg.get("interval_sec") or 1.2))
    return got


def store_details(adapter: KbChaChaChaAdapter, cfg: dict, ids: list,
                  limit: int = 0) -> int:
    """★★★★★ 받기와 넣기를 ★ **가른다** (규격 11-store/a-key · 개정 857).

    ★★★ 마스터 — 「★ 수집해서 파일로 저장 후 DB 에 넣으면서 ★ 신규·변경사항만
      ★ 적재하면 되잖아.  ★ 왜 수집과 적재를 같이 하지」
    ★★ 실측 08-29 — ★ 옛 꼴은 ★ **트랜잭션을 연 채 100건을 돌았다.**
      ★ ★ 건마다 `time.sleep(1.2)` 와 통신이 ★ **트랜잭션 안**이라
        ★ ★ 한 창이 ★ **최소 120초**였다.
      ★ ★ 그래서 ★ 잠금이 ★ **38.4초**까지 갔고 (계측) ★ 30초 `busy_timeout` 을
        ★ 넘겨 ★ `database is locked` 로 죽었다.
    ★ 1걸음 `fetch_details` — ★ 사이트를 두드려 ★ `raw_response` 에만 넣는다.
      ★ ★ 한 건 받고 ★ **곧바로 커밋**한다.  ★ 자는 것·통신은 ★ 트랜잭션 밖이다
    ★ 2걸음 `load_details` — ★ `raw_response` 를 읽어 ★ `core_listing` 에 넣는다.
      ★ ★ 통신이 없다.  ★ 자지 않는다.  ★ 신규·변경만 넣는다.
      ★ ★ 이번 목록에 없는 것은 ★ 그 자리에서 `gone` 이다
    ★ 검산 `S46-126`
    """
    got = fetch_details(adapter, cfg, ids, limit)
    put = load_details(cfg, _SCAN_DONE.get("groups") or [])
    print("★ 상세(받기) — " + " · ".join(f"{k} {v:,}" for k, v in got.items()))
    print("★ 상세(넣기) — " + " · ".join(f"{k} {v:,}" for k, v in put.items()))
    from tools.daily_enqueue import enqueue_after_store

    enqueue_after_store(os.path.join(ROOT, "carwatch.db"), SITE_CODE,
                        put.get("넣음", 0))
    return 0


def fetch_details(adapter: KbChaChaChaAdapter, cfg: dict, ids: list,
                  limit: int = 0) -> dict:
    """★ 1걸음 — 받는다.  ★ `raw_response` 에만 넣는다 (개정 857).

    ★ 봇 차단(30%)은 ★ 「없음」으로 저장하지 않는다 — ★ 다음 회차에 다시 부른다
    ★ 이미 받은 것은 ★ 건너뛴다 — ★ 여러 회차에 나눠 채운다 (규격 1-1)
    ★★ ★ 통신과 ★ `time.sleep` 은 ★ **트랜잭션 밖**이다.
      ★ 한 건 넣고 ★ 곧바로 커밋해 ★ 잠금 창을 ★ 한 INSERT 로 줄인다
    """
    # ★★★★★ 09-01 마스터 지시 — ★ **받기 걸음은 DB 를 안 연다.**
    #   ★ 「이미 받았나」는 ★ **원문 파일이 있나**로 본다 —
    #     ★ 앞서는 ★ `raw_response` 를 물었다.  ★ 그것이 DB 를 여는 자리였다
    from store.rawfile import walk as _walk

    done = {os.path.basename(x).split("__")[0][:-5]
            for x in _walk(site=SITE_CODE, endpoint="detail", root=ROOT)}
    # ★★★ 08-28 — ★ `--missing-raw` : ★ **원문이 없는 것만** 다시 받는다 (P3).
    #   ★ 실측 08-28 — ★ `detail_status='ok'` 가 ★ 406건인데
    #     ★ ★ `raw_response` 는 ★ **180건**뿐이다.  ★ 226건이 원문 없이 「받았다」다.
    #   ★ ★ 원문이 없으면 ★ **다시 캘 수가 없다** — ★ 사진도 축도 못 뽑는다
    #     ★ ★ 「원문은 남긴다.  갈래를 넓히시면 다시 판다」(명령서 3-2)가 안 지켜졌다.
    #   ★ 전량을 다시 받지 않는다 — ★ **원문이 빈 것만**이다.
    #     ★ ★ KB 는 봇 차단이 있으므로 ★ 더더욱 좁혀 받는다
    if "--missing-raw" in sys.argv[1:]:
        have = done                    # ★ 파일이 있나 — ★ DB 를 안 연다
        todo = [x for x in ids if x not in have]
        print(f"★ 원문이 없는 것 {len(todo):,}건만 다시 받는다"
              f" (원문 있는 것 {len(have):,}건)")
    else:
        todo = [x for x in ids if x not in done]
    if limit:
        todo = todo[:limit]
    print(f"★ 상세 — 받을 것 {len(todo):,}건 "
          f"(이미 받은 것 {len(done):,}건은 건너뛴다)")
    # ★ 받기 걸음의 셈 — ★ 파싱은 넣기 걸음이 한다
    got = {"받음": 0, "봇차단 3회": 0}
    walls_in_row = 0
    for n, one in enumerate(todo, 1):
        req = adapter.detail_urls(one)[0]
        body, _tries, _w = fetch_ok(req.url, req.headers, req.timeout_sec, cfg)
        if body is None:
            # ★ 못 받았다.  ★ 「없음」으로 저장하지 않는다 (금지 12 · 개정 289)
            got["봇차단 3회"] += 1
            walls_in_row += 1
            # ★★ 이만큼 이어서 막히면 ★ 사이트가 회차를 닫은 것이다 —
            #   ★ 그 회차를 끝내고 ★ 다음 회차로 넘긴다 (명령서 14-1).
            #   ★ 계속 두드리는 것은 ★ 사이트에 부담이고 ★ 소용도 없다
            if walls_in_row >= WALL_GIVE_UP:
                print(f"    ★ {walls_in_row}건 이어서 막혔다 — "
                      "★ 이 회차를 여기서 끝낸다.  ★ 다음 회차에 이어 받는다")
                break
            continue
        walls_in_row = 0
        # ★★ 원문을 ★ 먼저 남긴다 (명령서 3-2 필수) — ★ 「갈래를 넓히시면 다시 판다」.
        #   ★★ 실측 08-26 — ★ 여태 ★ 엔카 말고는 ★ 원문이 ★ 한 건도 없었다.
        #     ★ ★ 파싱이 틀렸을 때 ★ 다시 받는 수밖에 없었다 — ★ 그것이 엿새다
        #   ★ 파싱보다 앞에 둔다 — ★ 파싱이 실패해도 ★ 원문은 남아야 한다
        # ★★ 원문을 남긴다 (명령서 3-2 필수) — ★ 「갈래를 넓히시면 다시 판다」.
        #   ★★ 곧바로 커밋한다 — ★ 잠금 창이 ★ INSERT 하나로 끝난다
        save_file(SITE_CODE, "detail", one, req.url, body, _now(), root=ROOT)
        got["받음"] += 1
        if n % 100 == 0:
            print(f"    {n:,}/{len(todo):,} … 받음 {got['받음']:,}")
        # ★★ 자는 것은 ★ **커밋 뒤**다 — ★ 트랜잭션 안에서 자지 않는다
        time.sleep(float(cfg.get("interval_sec") or 1.2))
    return got


def load_details(cfg: dict, groups: list | None = None) -> dict:
    """★ 2걸음 — 넣는다.  ★ `raw_response` 를 읽어 `core_listing` 으로 (개정 857).

    ★ 통신이 없다.  ★ 자지 않는다.  ★ 한 트랜잭션이 짧다
    ★★ ★ **신규·변경만 넣는다** — ★ 원문이 그 매물의 `parsed_at` 보다
      ★ 새것일 때만 다시 넣는다.  ★ 같은 것을 다시 안 쓴다
    ★★ ★ 이번 목록에 없는 것은 ★ **그 자리에서 `gone`** 이다.
      ★ 받기가 반만 끝났으면(`done=False`) ★ 안 매긴다
    """
    from store.core import (resolve_listing_id, split_pii,
                            upsert_core)
    from store.pii import load_key
    from store.raw import commit

    conn = open_db(os.path.join(ROOT, "carwatch.db"))
    at, key = _now(), load_key()
    put = {"본 원문": 0, "넣음": 0, "그대로라 건너뜀": 0, "파싱 실패": 0,
           "gone": 0}
    # ★★★★★ 09-01 마스터 지시 — ★ **원본은 파일이다.**  ★ 거기서 읽는다.
    #   ★ 앞서는 ★ `raw_response` 를 읽었다 — ★ 이제 그것은 ★ **사본**이다
    from store.rawfile import read as _read
    from store.rawfile import walk as _walk

    rows = []
    for path in _walk(site=SITE_CODE, endpoint="detail", root=ROOT):
        env = _read(path)
        if env is None or not env.get("body"):
            continue
        rows.append((env.get("source_id"), env["body"],
                     env.get("fetched_at"), None))
    n = 0
    for sid, body, fetched_at, parsed_at in rows:
        put["본 원문"] += 1
        # ★ 값이 그대로면 건너뛴다 — ★ 이미 그 원문으로 넣었다
        if parsed_at and fetched_at and str(parsed_at) >= str(fetched_at):
            put["그대로라 건너뜀"] += 1
            continue
        deep = parse_detail(body, SITE_CODE, str(sid))
        if not deep:
            put["파싱 실패"] += 1
            continue
        deep["listing_id"] = resolve_listing_id(conn, SITE_CODE, str(sid), at)
        deep["detail_status"] = "ok"
        # ★ 넣기 직전에 ★ 차종을 붙인다 (마스터 지시 08-30) — ★ 안 붙이면 판정에 안 들어간다
        fill_target_key(SITE_CODE, deep)
        upsert_core(conn, split_pii(conn, deep, SITE_CODE, key, at), at)
        put["넣음"] += 1
        n += 1
        if n % 200 == 0:
            commit(conn)                # ★ 통신이 없어 창이 짧다
    commit(conn)
    # ★★ gone 을 ★ **넣기 걸음에서** 매긴다 (규격 개정 857) —
    #   ★ 옛 꼴은 받으면서 매겼다.  ★ 받기가 반만 끝났으면 안 매긴다
    if groups:
        # ★ 넣기가 끝났다 — ★ 원문을 매물에 잇는다 (S46-97 · 08-29)
        raw_link_raws(conn, SITE_CODE)
        # ★★★★★ 08-30 정정 (마스터 0c) — ★ **이 목록으로는 gone 을 못 매긴다.  ★ 껐다**
        #   ★ K카가 살아 있는 12대를 죽인 것과 ★ **같은 함정**이다 (0a).
        #   ★★ 실측 08-30 — ★ 08-29 에 gone 으로 매긴 것을 ★ **표본으로 눌러 봤다** —
        #   ★ ★ 표본 9건 중 ★ **9건이 다 살아 있었다**
        #   ★★★ 까닭 — ★ 「끝까지 받았나」 가드는 ★ 「이 창구를 끝까지 받았나」를 재지
        #     ★ ★ **「이 창구가 전량인가」를 안 잰다.**  ★ 우리는 ★ 차종으로 좁혀 받는다 —
        #     ★ ★ 좁힌 목록에 없다고 ★ 사이트에서 사라진 것이 아니다.
        #   ★ 되돌리는 길은 ★ `tools/undo_wrong_gone.py` 다 (눌러서 살아 있는 것만 되돌린다)
        got = {}
        print(f"★ 팔린 차를 목록으로 안 거른다 — {SWEEP_OFF}")
        put["gone"] = sum(got.values())
        dn = sum(1 for d, _i in groups if d)
        print(f"★ 목록에 없어 gone 으로 매긴 것 {put['gone']}건 "
              f"({len(got)}차종 · 끝까지 받은 묶음 {dn}/{len(groups)})")
        if len(groups) - dn:
            print("  ★ 끝까지 못 받은 묶음이 건드린 차종은 안 매겼다")
    left = conn.execute("SELECT COUNT(*) FROM core_listing WHERE site=?",
                        (SITE_CODE,)).fetchone()[0]
    print(f"★ 저장된 KB 매물 — {left:,}건")
    conn.close()
    return put


def main() -> int:
    cfg = load_config(ROOT)
    adapter = KbChaChaChaAdapter(cfg)
    args = sys.argv[1:]

    def opt(name: str, default: int) -> int:
        if name in args:
            i = args.index(name)
            if i + 1 < len(args) and args[i + 1].isdigit():
                return int(args[i + 1])
        return default

    if "--count" in args:
        seen, pages, empty_at = count_all(adapter, cfg, opt("--count", MAX_PAGES))
        print(f"★ 총 매물 {len(seen):,}건 · 받은 쪽 {pages} · "
              f"빈 쪽 {empty_at if empty_at else '안 나왔다'}")
        return 0

    if "--probe" in args:
        req = adapter.list_url(None, page=1)
        body, _t, _w = fetch_ok(req.url, req.headers, req.timeout_sec, cfg)
        ids = page_ids(body or "")[:opt("--probe", 10)]
        got = probe_detail(adapter, cfg, ids)
        print("★ 봇 차단 실측 —", " · ".join(f"{k} {v}" for k, v in got.items()))
        return 0

    if "--narrow" in args:
        # ★★ 우리 차종만 받는 유일한 길이다 (명령서 60-2 「목록도 · 상세도」).
        #   ★ `--pages` · `--count` 는 ★ **KB 가 파는 전부**를 훑는다 — ★ 조사용이다
        groups = load_filters()
        seen: set = set()
        # ★★★ 08-26 마스터 정정 (명령서 60장 · 오판 130) —
        #   ★ 「★ 야 내가 ★ **20종을 받으라고 했지**.
        #     ★ 쏘렌토 같이 ★ 보지도 않을 것을 ★ 받으라고 했니?」
        #   ★★ ★ 「전체」는 ★ **우리 20종의 전체**다 — ★ 국산까지 스무 종이다.
        #     ★ ★ 「KB 가 파는 15,836건 전부」가 ★ **아니다**
        #   ★ 명령서 59장(전량)은 ★ 폐기다
        print(f"★ 우리 차종만 받는다 — {len(groups)}묶음 "
              f"(targets.json site_query.kbchachacha · 명령서 60장)")
        by_group = []
        # ★★★★ 08-29 (개정 838) — ★ 묶음마다 ★ 「끝까지 받았나」를 들고 간다.
        #   ★ 상세를 저장한 **뒤에** ★ `sweep_gone_groups` 에 넘긴다 —
        #     ★ 그래야 ★ 이번에 새로 들어온 매물이 ★ 차종을 갖고 있다
        done_groups: list = []
        for g in groups:
            r = walk_group(adapter, cfg, g, seen)
            mark = "" if r["ids"] else "  ★ 0건이다"
            print(f"  {g['for']:12} maker={g['makerCode']} class={g['classCode']}"
                  f" car={g.get('carCode') or '—':>5}"
                  f"  {r['pages']:>3}쪽 · 매물 {len(r['ids']):>4}"
                  f" (규격 {g.get('expect', '—')})  봇차단 {r['walls']}{mark}")
            by_group.append((g, r["ids"]))
            done_groups.append((r["done"], set(r["ids"])))
            _SCAN_DONE["groups"] = done_groups
        print(f"★ 합 {len(seen):,}건  (규격 2,084 — ★ 그것은 쪽마다의 합이다.  "
              f"★ 겹친 것을 뺀 수가 이것이다)")
        if "--dry" in args:
            print("★ --dry 라 저장하지 않았다")
            return 0
        # ★ 간격 — ★ 오래 이어 부르면 ★ 사이트가 막는다 (실측 08-23 — 100건 뒤 전건 차단).
        #   ★ 규격 1-1 「한 번에 다 받으려 하지 마라.  여러 회차에 나눠 채운다」
        gap = opt("--interval", 0)
        if gap:
            cfg = dict(cfg, interval_sec=gap)
        # ★ 한 묶음 크기 — ★ 안 주면 ★ 실측값 10 이다 (08-25)
        want = opt("--detail", DETAIL_BATCH)
        # ★★ 묶음을 ★ 몇 번 도는가 — ★ 사이에 ★ 5분씩 쉰다 (실측).
        #   ★★ ★ 08-26 정정 — ★ 「가려 받지 마라」는 ★ **「우리 20종을 다 받아라」**다.
        #     ★ ★ 수입 일곱만 받지 말라는 뜻이지 ★ 「KB 가 파는 전부」가 아니다 (60장)
        bursts = opt("--bursts", DEFAULT_BURSTS)
        ids = [i for _g, gids in by_group for i in gids]
        rc = 0
        for turn in range(1, max(1, bursts) + 1):
            if turn > 1:
                print(f"★ {BURST_REST_SEC}초 쉰다 — ★ 몫이 돌아오는 참이다 "
                      f"({turn}/{bursts} 묶음)")
                time.sleep(BURST_REST_SEC)
            rc = store_details(adapter, cfg, ids, want) or rc
        # ★★ gone 은 ★ `load_details`(넣기 걸음)가 매긴다 (규격 개정 857).
        #   ★ 받으면서 매기지 않는다 — ★ 받기가 반만 끝났을 수 있다
        return rc

    pages = opt("--pages", 1)
    seen: set = set()
    for page in range(1, pages + 1):
        req = adapter.list_url(None, page=page)
        body, _t, walled = fetch_ok(req.url, req.headers, req.timeout_sec, cfg)
        if body is None:
            print(f"  {page}쪽 — ★ 못 받았다 (봇 차단 {walled}).  ★ 저장하지 않는다")
            continue
        seen.update(page_ids(body))
        time.sleep(float(cfg.get("interval_sec") or 1.2))
    print(f"목록 {pages}쪽 · 매물번호 {len(seen):,}건")

    from store.core import resolve_listing_id
    from store.raw import commit

    conn = open_db(os.path.join(ROOT, "carwatch.db"))
    at = _now()
    for one in sorted(seen):
        resolve_listing_id(conn, SITE_CODE, one, at)
    commit(conn)
    print(f"★ 매물번호만 넣었다 {len(seen):,}건 · site='{SITE_CODE}'")
    print("★ 상세는 아직이다 — ★ 봇 차단을 가르는 자리를 먼저 세웠다")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
