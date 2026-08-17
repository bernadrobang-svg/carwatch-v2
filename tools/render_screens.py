# -*- coding: utf-8 -*-
"""전 화면을 실제로 렌더해 `outputs/render/` 에 남긴다.

지시서   개정 279 (화면이 본체다) · METHOD_render_output (가이드 요청 A안)
근거     ★ 소스를 읽고 판단하면 틀린다.  실측 08-16 — 가이드가 템플릿을 grep 해
         「{% if %} 로 다 막혀 있다」고 했으나 실제로는 /listings?dealer= 가 5곳이었다.
         결과 HTML 을 저장소에 올리면 가이드가 「나온 것」을 그대로 읽는다.
필수     로그인한 관리자로 · 실제 DB 로 · 실제 데이터로
금지     템플릿을 옮겨 적어 「이렇게 나올 것이다」로 대신하는 것
사용     python3.11 tools/render_screens.py [carwatch.db]
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

OUT_DIR = os.path.join(ROOT, "outputs", "render")
# ★ 구조를 보는 것이 목적이지 3,470건이 필요한 것이 아니다 (가이드 요청).
#   몇 MB 짜리 HTML 을 올리면 아무도 안 읽는다
RENDER_ROWS = 10
# 경로 변수에 넣을 값.  ★ 없으면 그 화면은 아예 안 나온다
SAMPLE = {"listing_id": None, "watch_id": "1", "account_id": "1"}

# 스크린샷 (가이드 요청 B안).  ★ 마스터는 360px 로 본다
SHOT_DIR = os.path.join(ROOT, "outputs", "shot")
def _shot_widths() -> tuple:
    """찍을 폭 (개정 337).  ★ 360·1400 둘만 찍어 가운데를 놓쳤다 —
    마스터가 보는 1200px 대가 아무에게도 안 보였다."""
    import json as _j

    with open(os.path.join(ROOT, "config", "web.json"), encoding="utf-8") as f:
        return tuple(_j.load(f)["shot_widths"])


SHOT_WIDTHS = _shot_widths()
# 넓은 폭까지 찍을 화면.  ★ 마스터가 주로 보는 곳이다
# ★ 저장소가 커밋마다 불어난다.  넓은 폭은 마스터가 PC 로 주로 보는 셋만
# 다섯 폭 전부에서 찍는 화면 (개정 337).
# ★ 매물이 나오는 화면은 폭마다 배치가 통째로 달라진다 —
#   추천 · 관심 · 비교도 넣는다.  목록만 봐서 추천이 깨진 채로 있었다
WIDE_PATHS = ("/listings", "/why/{listing_id}", "/market",
              "/recommend", "/watch", "/compare", "/dealers")
# ★ 나머지는 360 만 찍는다 — 관리 화면도 전부 찍는다 (가이드 요청 검토 14 §7).
#   「관리 UI 가 엉망」이라는 지적을 가이드가 직접 보고 판단할 수 있어야 한다
SHOT_TIMEOUT_SEC = 180
# ★ 「찍었다」가 아니라 「내용이 있는가」다 (개정 279).  이 글이 있으면 빈 장이다
DENY_MARK = "관리자만 볼 수 있습니다"
SHOT_HEIGHT = 1400


def _tmp_root(rows: int) -> str:
    """config 만 바꾼 임시 뿌리.  ★ 운영 config 를 건드리지 않는다.

    실행 중에 죽어도 config/web.json 이 10건짜리로 남으면 안 된다
    """
    tmp = os.path.join(ROOT, ".render_root")
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    shutil.copytree(os.path.join(ROOT, "config"), os.path.join(tmp, "config"))
    with open(os.path.join(tmp, "config", "web.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    cfg["rows_per_page"] = rows
    with open(os.path.join(tmp, "config", "web.json"), "w",
              encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    # ★ 화면이 읽는 산출물도 옮긴다.  안 옮기면 「아직 한 번도 안 돌았습니다」로
    #   찍혀 스크린샷이 실제와 달라진다 (실측 08-18 — 가벼운 점검 결과)
    got = os.path.join(ROOT, "outputs", "light", "last.json")
    if os.path.isfile(got):
        os.makedirs(os.path.join(tmp, "outputs", "light"), exist_ok=True)
        shutil.copy(got, os.path.join(tmp, "outputs", "light", "last.json"))
    return tmp


def main(db: str = "carwatch.db") -> int:
    import sqlite3

    from contracts import ROLE_ADMIN, Account
    from errors import CarWatchError
    from web.routes import GET, ROUTES
    from web.server import guard
    from web.views import HANDLERS

    conn = sqlite3.connect(os.path.join(ROOT, db))
    row = conn.execute(
        "SELECT listing_id FROM result_score ORDER BY listing_id LIMIT 1"
    ).fetchone()
    SAMPLE["listing_id"] = str(row[0]) if row else "1"

    tmp = _tmp_root(RENDER_ROWS)
    shutil.rmtree(OUT_DIR, ignore_errors=True)
    os.makedirs(OUT_DIR)
    acc = Account(1, ROLE_ADMIN, "마스터")
    index, skipped = [], []
    try:
        for route in ROUTES:
            if GET not in route.methods or guard(acc, route) is not None:
                continue
            fn = HANDLERS.get(route.view)
            if fn is None:
                continue
            pv = {}
            if "{" in route.path:
                key = route.path.split("{")[1].split("}")[0]
                if key not in SAMPLE:
                    skipped.append(f"{route.path} — {key} 표본이 없다")
                    continue
                pv = {key: SAMPLE[key]}
            # ★ 파일 이름에 {} 를 남기지 않는다 — 링크가 깨지고 눈에도 거슬린다
            name = (route.path.strip("/").replace("/", "_")
                    .replace("{", "").replace("}", "") or "home")
            try:
                st, _h, body = fn(conn, acc,
                                  {"query": {}, "form": {}, "method": GET},
                                  path_vars=pv, csrf="render", root=tmp)
            except CarWatchError as e:
                skipped.append(f"{route.path} — {type(e).__name__}: {e}")
                continue
            except Exception as e:                           # noqa: BLE001
                skipped.append(f"{route.path} — {type(e).__name__}: "
                               f"{str(e)[:70]}")
                continue
            html = body.decode("utf-8", "replace")
            with open(os.path.join(OUT_DIR, f"{name}.html"), "w",
                      encoding="utf-8") as f:
                f.write(html)
            index.append((route.path, name, int(st), len(html.encode())))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    conn.close()

    lines = [
        "# 렌더 결과 — 실제로 나온 화면",
        "",
        f"`python3.11 tools/render_screens.py` 로 만든다 · 목록은 {RENDER_ROWS}건으로 줄였다.",
        "",
        "★ 템플릿이 아니라 **나온 HTML** 이다. 여기 없는 것은 화면에도 없다.",
        "",
        "| 경로 | 파일 | 상태 | 크기 |",
        "|---|---|--:|--:|",
    ]
    for path, name, st, size in index:
        lines.append(f"| `{path}` | [{name}.html]({name}.html) | {st} | {size:,}B |")
    if skipped:
        lines += ["", "## 못 낸 화면", ""]
        lines += [f"- {s}" for s in skipped]
    with open(os.path.join(OUT_DIR, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"렌더 {len(index)}화면 · 못 낸 것 {len(skipped)} → outputs/render/")
    for s in skipped:
        print(f"  · {s}")
    return 0


def shot_paths() -> list:
    """찍을 화면 — 관리자가 GET 으로 볼 수 있는 전부 (검토 14 §7)."""
    from contracts import ROLE_ADMIN, Account
    from web.routes import GET, ROUTES
    from web.server import guard
    from web.views import HANDLERS

    acc = Account(1, ROLE_ADMIN, "마스터")
    out = []
    for r in ROUTES:
        if GET not in r.methods or guard(acc, r) is not None:
            continue
        if HANDLERS.get(r.view) is None:
            continue
        if "{" in r.path and r.path.split("{")[1].split("}")[0] not in SAMPLE:
            continue
        out.append(r.path)
    return out


# 사진을 몇 장까지 받아 둘 것인가.  ★ 스크린샷이 오래 걸리면 아무도 안 본다
SHOT_IMAGE_MAX = 120
SHOT_IMAGE_TIMEOUT = 8


def _localize_images(html: str, site: str, cache: dict) -> str:
    """원격 사진을 받아 옆에 두고 그것을 가리키게 한다.

    ★ file:// 에서는 https 이미지를 안 받는다.  받아 두지 않으면
      「사진이 안 나온다」로 보이고 검토가 헛돈다 (실측 08-17 —
      가이드가 「빈 회색 상자」라 했는데 실서비스는 멀쩡했다)
    ★ 못 받으면 그대로 둔다 — 없는 사진을 만들지 않는다
    """
    import urllib.request

    for url in dict.fromkeys(re.findall(r'src="(https?://[^"]+)"', html)):
        if url not in cache:
            if len(cache) >= SHOT_IMAGE_MAX:
                break
            name = f"img{len(cache):03d}" + os.path.splitext(url)[1][:5]
            try:
                with urllib.request.urlopen(
                        url, timeout=SHOT_IMAGE_TIMEOUT) as res:  # noqa: S310
                    body = res.read()
                with open(os.path.join(site, name), "wb") as f:
                    f.write(body)
                cache[url] = name
            except Exception as err:                         # noqa: BLE001
                # ★ 조용히 넘기지 않는다.  「사진이 안 나온다」로 보이는데
                #   왜인지 모르면 검토가 헛돈다 (규칙 4)
                cache[url] = None
                print(f"  사진 못 받음 {type(err).__name__} {url[-34:]}")
        if cache.get(url):
            html = html.replace(f'src="{url}"', f'src="{cache[url]}"')
    # ★ loading="lazy" 는 화면 밖 사진을 안 받는다.  한 장으로 찍는
    #   스크린샷에서는 아래쪽 카드가 전부 빈 상자로 나온다
    #   (실측 08-18 — 목록은 나오는데 추천만 빈 상자였다.  CSS 가 아니라
    #    추천 화면이 머리말이 길어 카드가 더 아래에 있어서였다).
    #   ★ 사본에서만 뗀다.  실서비스는 그대로 lazy 다 — 스크롤하면 나온다
    return html.replace(' loading="lazy"', "")


def shoot(base: str = "", paths=None) -> int:
    """★ outputs/render/ 의 HTML 을 그대로 찍는다 (가이드 요청 B안).

    실측 08-16 — 돌고 있는 서비스를 찍었더니 **관리 화면 17장이 전부
    「관리자만 볼 수 있습니다」였다.** 세션 쿠키가 없어서다.
    「36장 찍었다」를 내용 확인 없이 보고했다 — 개정 279 가 말한 그 실패다.

    렌더 결과는 이미 관리자로 만든 것이라 그것을 file:// 로 찍으면
    세션을 흉내 낼 필요가 없다.  ★ 화면과 스크린샷이 같은 HTML 에서 나온다.

    ★ 「반응형으로 했습니다」가 아니라 보이는 것을 낸다.
      실측 08-16 — 스크린샷이 잡은 것:
        한글이 두부로 깨짐(서버에 한글 글꼴이 없었다)
        .btn 이 로그인 시안 것으로 전역 적용돼 조건 단추가 세로로 꽉 참
        카드가 25줄로 늘어짐
      셋 다 HTML 만 봐서는 안 보인다
    필요   firefox (headless) · 한글 글꼴 (google-noto-sans-cjk-ttc-fonts)
    """
    import shutil as _sh
    import subprocess
    import tempfile

    ff = _sh.which("firefox")
    if ff is None:
        print("firefox 가 없다 — 스크린샷을 건너뛴다 (A안 HTML 은 그대로 나온다)")
        return 0
    _sh.rmtree(SHOT_DIR, ignore_errors=True)
    os.makedirs(SHOT_DIR)
    made, empty = [], []
    cache: dict = {}
    with tempfile.TemporaryDirectory() as site:
        _sh.copy(os.path.join(ROOT, "web", "static", "app.css"),
                 os.path.join(site, "app.css"))
        for f in sorted(os.listdir(OUT_DIR)):
            if not f.endswith(".html"):
                continue
            html = open(os.path.join(OUT_DIR, f), encoding="utf-8").read()
            # ★ file:// 에서는 /static 이 안 잡힌다.  같은 CSS 를 옆에 둔다.
            #   ★ ?v=<지문>이 붙는다 (V11-82) — 무늬로 바꾼다.
            #     글자 그대로 바꾸면 지문이 붙는 순간 CSS 가 통째로 빠진다
            #     (실측 08-17: 스크린샷이 전부 민무늬로 나왔다)
            html = re.sub(r'href="/static/app\.css[^"]*"',
                          'href="app.css"', html)
            # ★ file:// 은 원격 이미지를 안 받는다 (실측 08-17 — 사진이 전부
            #   빈 회색 상자였다).  받아서 옆에 두고 그것을 가리킨다 —
            #   ★ 「화면이 멀쩡한데 스크린샷만 문제」면 검토가 계속 헛돈다
            html = _localize_images(html, site, cache)
            open(os.path.join(site, f), "w", encoding="utf-8").write(html)
            name = f[:-5]
            wide = any(name == (p.replace("{listing_id}", SAMPLE["listing_id"]
                                          or "1").strip("/")
                                .replace("/", "_") or "home")
                       for p in WIDE_PATHS)
            for w in (SHOT_WIDTHS if wide else SHOT_WIDTHS[:1]):
                out = os.path.join(SHOT_DIR, f"{name}_{w}.png")
                # ★ 프로필을 새로 만든다.  안 그러면 옛 CSS 가 캐시로 남아
                #   고친 것이 안 보인다 (실측 08-16)
                with tempfile.TemporaryDirectory() as prof:
                    env = dict(os.environ, MOZ_HEADLESS="1")
                    subprocess.run(
                        [ff, "--headless", "--profile", prof,
                         "--screenshot", out, f"--window-size={w},{SHOT_HEIGHT}",
                         f"file://{os.path.join(site, f)}"],
                        env=env, timeout=SHOT_TIMEOUT_SEC,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        check=False)
                # ★ 「찍었다」가 아니라 「내용이 있는가」를 본다 (개정 279)
                if DENY_MARK in html:
                    empty.append(f"{name} — 권한 없음 화면이다")
                elif os.path.isfile(out):
                    made.append((name, w, os.path.getsize(out)))
    lines = ["# 스크린샷 — 실제로 보이는 모습", "",
             "`python3.11 tools/render_screens.py --shot` 로 만든다.",
             "",
             "★ `outputs/render/` 의 HTML 을 그대로 찍은 것이다 —",
             "  그것은 **관리자로** 만든 것이라 관리 화면도 내용이 있다.",
             "  (돌고 있는 서비스를 찍으면 세션이 없어 「권한 없음」만 나온다)",
             "", "| 화면 | 폭 | 파일 | 크기 |", "|---|--:|---|--:|"]
    for name, w, size in made:
        lines.append(f"| `{name}` | {w} | [{name}_{w}.png]({name}_{w}.png) "
                     f"| {size:,}B |")
    if empty:
        lines += ["", "## 내용이 없는 화면", ""] + [f"- {e}" for e in empty]
    with open(os.path.join(SHOT_DIR, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"스크린샷 {len(made)}장 → outputs/shot/"
          + (f" · 내용 없음 {len(empty)}" if empty else ""))
    for e in empty:
        print(f"  · {e}")
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    rc = main(args[0] if args else "carwatch.db")
    if "--shot" in sys.argv:
        rc = shoot() or rc
    sys.exit(rc)
