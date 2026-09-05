# -*- coding: utf-8 -*-
"""리본카 수집 — 사이트맵 전량 → 우리 쪽에서 거른다 (명령서 39).

쓰기   python3.11 tools/collect_reborncar.py --count     몇 건인지만
      python3.11 tools/collect_reborncar.py             전량 (1,036건)
      python3.11 tools/collect_reborncar.py --limit 50  앞에서 N건만
      python3.11 tools/collect_reborncar.py --missing-raw  ★ 원문이 없는 우리 차종만 (P3)
★ 목록 API 는 robots 가 막았다 — ★ 사이트맵이 목록이다 (1b장)
★ 차종 좁히기가 없다 — ★ K카와 같이 ★ **전량을 받아 우리가 거른다**
★ 모바일 UA 로 받는다 — ★ 데스크톱은 값이 거짓이다 (2a장)
★ 503 이 나면 다시 두드린다 — ★ 한 번 났다가 살아났다 (명령서 39)
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import http.cookiejar
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from parse.reborncar.mapping import (  # noqa: E402
    option_keys, options_of,
)
# ★★★★★ 09-01 마스터 지시 — ★ 받기는 ★ **파일만** 쓴다 (`S46-204`)
from store.rawfile import save as save_file  # noqa: E402

# ★★★★★ 이 수집기는 ★ **팔린 차를 목록으로 안 거른다** (마스터 지시 08-30 · S46-117).
#   ★ 낱말 `SWEEP_OFF` 를 ★ 검사가 본다 — ★ 「안 거른다」와 「못 거른다」를 가른다
SWEEP_OFF = (
    "08-29 — 목록에 없다고 죽이면 살아 있는 차를 죽인다"
    " (11-store/a-key 08-29 절).  상세로 확인한 뒤 죽이는 꼴로 바꾼 뒤 다시 켠다")

SITE_CODE = "reborncar"
RE_LOC = re.compile(r"<loc>([^<]+)</loc>")
RETRY = 3                 # ★ 503 은 한 번 났다가 살아났다 (명령서 39)
RETRY_WAIT = 3.0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


OPTION_PATH = "/api/v1/car/carOption.rb"


def _option_body(cfg, source_id: str, html: str):
    """★ 옵션 창구 몸통만 받는다 (r1007 1b · 09-01 파일 걸음).

    ★★ **DB 를 안 연다** — ★ 받아서 몸통을 돌려줄 뿐이다.  ★ 저장은 부르는 쪽이 한다
    """
    tok, csrf = option_keys(html)
    if not tok or not csrf:
        return None
    base = cfg["base_url"]
    head = dict(cfg.get("headers") or {})
    head["Accept"] = "application/json, text/javascript, */*; q=0.01"
    head.update({"X-Ajax-call": "true", "Authorization": tok,
                 "X-CSRF-TOKEN": csrf, "X-Requested-With": "XMLHttpRequest",
                 "Referer": base + cfg["paths"]["detail"].format(
                     source_id=source_id),
                 "Origin": base,
                 "Content-Type":
                     "application/x-www-form-urlencoded; charset=UTF-8"})
    data = urllib.parse.urlencode({"productId": source_id}).encode()
    try:
        with _OPENER.open(urllib.request.Request(base + OPTION_PATH,
                                                 data=data, headers=head),
                          timeout=float(cfg["timeout_sec"])) as res:
            return res.read()
    except (urllib.error.URLError, OSError, TimeoutError):
        return None


def _options_old(conn, cfg, source_id: str, html: str, at: str, lid):
    """★ 옵션 창구 (r1007 1b).  ★ 못 받으면 ★ None — ★ 「없다」로 안 적는다.

    ★ 원문은 ★ 남긴다 (P3) — ★ 받은 것도 못 받은 것도
    """

    tok, csrf = option_keys(html)
    if not tok or not csrf:
        return None
    base = cfg["base_url"]
    url = base + OPTION_PATH
    head = dict(cfg.get("headers") or {})
    # ★★ 창구는 ★ JSON 을 준다 — ★ 상세 쪽의 `Accept: text/html` 을 그대로 쓰면
    #   ★ ★ 안 준다 (실측 08-31 — 표본 5건 전건 「창구가 안 줌」)
    head["Accept"] = "application/json, text/javascript, */*; q=0.01"
    head.update({"X-Ajax-call": "true", "Authorization": tok,
                 "X-CSRF-TOKEN": csrf, "X-Requested-With": "XMLHttpRequest",
                 "Referer": base + cfg["paths"]["detail"].format(
                     source_id=source_id),
                 "Origin": base,
                 "Content-Type":
                     "application/x-www-form-urlencoded; charset=UTF-8"})
    data = urllib.parse.urlencode({"productId": source_id}).encode()
    try:
        with _OPENER.open(urllib.request.Request(url, data=data, headers=head),
                          timeout=float(cfg["timeout_sec"])) as res:
            body = res.read()
    except (urllib.error.URLError, OSError, TimeoutError):
        return None
    save_file(SITE_CODE, "option", source_id, url, body, at,
                  listing_id=lid)
    # ★★★ 08-31 (`S46-126`) — ★ 원문을 남겼으면 ★ **곧바로 커밋한다.**
    #   ★ 통신·`sleep` 이 ★ 트랜잭션 안에 들면 ★ 잠금 창이 분 단위가 된다 (개정 857)
    from store.raw import commit as _commit
    _commit(conn)
    return options_of(body)


# ★★★★★ 08-31 (r1007 · 1b) — ★ **쿠키를 잇는다.**
#   ★ 옵션 창구(`/api/v1/car/carOption.rb`)는 ★ 상세 쪽을 받은 ★ **그 세션**이라야 준다.
#   ★ ★ 가이드 창에서 ★ 999(봇 차단)가 난 까닭이 ★ 이것으로 보인다 —
#     ★ ★ 토큰만 옮기고 ★ `JSESSIONID` 를 안 이으면 ★ 막힌다 (실측 08-31)
_JAR = http.cookiejar.CookieJar()
_OPENER = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(_JAR))


def _get(url: str, headers: dict, timeout: float,
         endpoint: str | None = None, source_id=None,
         page: int | None = None) -> str | None:
    """★ 받는다.  ★ 못 받으면 `None` 이다.

    ★★★★★ 09-05 (지시 1번 · `S46-278` · `STEP 53-⑤`) — ★ **막힌 응답도 원문이다.**
      ★ 전에는 ★ 실패하면 ★ **몸통을 버리고** `None` 을 냈다 —
      ★ ★ 그래서 ★ 「언제부터 · 어떻게 막혔나」를 ★ 뒤에 못 봤다.
      ★ ★ ★ 창구를 알려 주면 ★ `status="blocked"` 로 ★ **남긴다** (파싱은 안 한다)
    """
    from collect.rawfetch import keep_blocked

    for _ in range(RETRY):
        try:
            req = urllib.request.Request(url, headers=headers)
            with _OPENER.open(req, timeout=timeout) as res:
                return res.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code != 503:
                if endpoint:
                    try:
                        keep_blocked(SITE_CODE, endpoint, source_id, url,
                                     e.read(), page=page, http_code=e.code,
                                     root=ROOT)
                    except OSError:
                        pass
                return None
            time.sleep(RETRY_WAIT)
        except Exception:
            return None
    return None


def codes(cfg: dict) -> list:
    """사이트맵에서 매물번호를 뽑는다 (1b장)."""
    raw = _get(cfg["base_url"] + cfg["paths"]["sitemap"],
               cfg["headers"], float(cfg["timeout_sec"]))
    if not raw:
        print("★ 사이트맵을 못 받았다")
        return []
    locs = RE_LOC.findall(raw)
    det = [u for u in locs if "/smartbuy/SB1002/" in u]
    got = sorted({u.rstrip("/").rsplit("/", 1)[-1] for u in det})
    print(f"사이트맵 {len(raw):,}B · <loc> {len(locs):,}개 · "
          f"★ 매물 {len(got):,}건 (중복 {len(det) - len(got)})")
    return got


def main() -> int:
    args = sys.argv[1:]
    with open(os.path.join(ROOT, "config", "endpoints.json"), encoding="utf-8") as f:
        cfg = json.load(f)[SITE_CODE]
    got = codes(cfg)
    if not got:
        return 1
    if "--count" in args:
        return 0
    if "--options" in args:
        # ★★★★★ 08-31 (r1007 · 1b) — ★ **옵션만 받는다.**
        #   ★ 이미 받아 둔 상세로는 안 된다 — ★ `RB_TOKEN` 이 ★ 30분짜리라
        #     ★ ★ 저장된 원문의 토큰은 ★ 이미 죽어 있다.
        #   ★ 그래서 ★ 상세 쪽을 ★ 다시 한 번 받아 ★ 그 세션으로 창구를 두드린다.
        #   ★ ★ 상세 원문도 ★ 함께 새로 남긴다 (P3 — 잃는 것이 없다)
        # ★★★★★ 09-01 — ★ 옵션도 ★ **받기 걸음**에서 파일로 남긴다.
        #   ★ 옛 `_options_only` 는 ★ DB 를 열었다 — ★ 걷어냈다
        print("★ --options 는 없어졌다 — ★ 상세를 받을 때 함께 받는다.\n"
              "  python3.11 tools/collect_reborncar.py  ·  "
              "그다음 python3.11 tools/load_raw.py reborncar --write")
        return 0
    # ★★★ 08-29 (개정 838) — ★ 「끝까지 받았나」.
    #   ★ 리본카는 ★ **사이트맵 한 번**으로 전부를 준다 — ★ 쪽넘김이 없다.
    #   ★ 그러나 ★ `--limit` 으로 자르면 ★ 전부가 아니다 — ★ 그때는 안 매긴다
    _done = bool(got)
    _all_ids = set(got)
    if "--limit" in args:
        i = args.index("--limit")
        if i + 1 < len(args) and args[i + 1].isdigit():
            got = got[:int(args[i + 1])]
            _done = False

    # ★★★★★ 09-01 마스터 지시 — ★ **받기 걸음은 파일만 쓴다.  ★ DB 를 안 연다.**
    #   ★ 넣기는 ★ `python3.11 tools/load_raw.py reborncar --write` 가 한다.
    #   ★★ 「이미 받았나」도 ★ **파일로 안다** — ★ 앞서는 `core_listing` 을 물었다
    from store.rawfile import walk as _walk

    at = _now()
    interval = float(cfg.get("interval_sec") or 1.0)
    have = {os.path.basename(x).split("__")[0][:-5]
            for x in _walk(site=SITE_CODE, endpoint="detail", root=ROOT)}
    todo = [x for x in got if x not in have]
    if "--limit" in args:
        k = args.index("--limit")
        if k + 1 < len(args) and args[k + 1].isdigit():
            todo = todo[:int(args[k + 1])]
    print(f"★ 상세 — 받을 것 {len(todo)}건 "
          f"(원문 파일이 있는 것 {len(got) - len(todo)}건은 건너뛴다)")
    seen = {"정상": 0, "못 받음": 0, "옵션": 0}
    for one in todo:
        url = cfg["base_url"] + cfg["paths"]["detail"].format(source_id=one)
        html = _get(url, cfg["headers"], float(cfg["timeout_sec"]),
                    endpoint="detail", source_id=one)
        if not html:
            seen["못 받음"] += 1
            time.sleep(interval)
            continue
        save_file(SITE_CODE, "detail", one, url, html, at, root=ROOT)
        seen["정상"] += 1
        # ★★★★★ 08-31 (r1007 · 1b) — ★ 옵션 창구.  ★ 열쇠 둘이 ★ 상세 쪽 안에 있다.
        #   ★ ★ **같은 세션**이라야 준다 — ★ 그래서 받기 걸음에 있어야 한다
        opt = _option_body(cfg, one, html)
        if opt is not None:
            save_file(SITE_CODE, "option", one,
                      cfg["base_url"] + OPTION_PATH, opt, at, root=ROOT)
            seen["옵션"] += 1
        time.sleep(interval)
    print("★ 상세 — " + " · ".join(f"{k} {v}" for k, v in seen.items()))
    print(f"★ 넣기 — python3.11 tools/load_raw.py {SITE_CODE} --write")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
