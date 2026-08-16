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
SHOT_WIDTHS = (360, 1400)
# 찍을 화면.  ★ 전 화면을 찍으면 t4g.small 에서 몇 분씩 걸린다 —
#   모양이 다른 것만 고른다.  나머지는 outputs/render/ 의 HTML 로 본다
SHOT_PATHS = ("/listings", "/why/{listing_id}", "/market", "/dealers",
              "/recommend", "/", "/notready")
SHOT_TIMEOUT_SEC = 180
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


def shoot(base: str = "http://127.0.0.1:8765") -> int:
    """돌고 있는 서비스를 실제 브라우저로 찍는다 (가이드 요청 B안).

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
    made = []
    for path in SHOT_PATHS:
        url_path = path.replace("{listing_id}", SAMPLE["listing_id"] or "1")
        name = (url_path.strip("/").replace("/", "_") or "home")
        for w in SHOT_WIDTHS:
            out = os.path.join(SHOT_DIR, f"{name}_{w}.png")
            # ★ 프로필을 새로 만든다.  안 그러면 옛 CSS 가 캐시로 남아
            #   고친 것이 안 보인다 (실측 08-16)
            with tempfile.TemporaryDirectory() as prof:
                env = dict(os.environ, MOZ_HEADLESS="1")
                subprocess.run(
                    [ff, "--headless", "--profile", prof, "--screenshot", out,
                     f"--window-size={w},{SHOT_HEIGHT}", f"{base}{url_path}"],
                    env=env, timeout=SHOT_TIMEOUT_SEC,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    check=False)
            if os.path.isfile(out):
                made.append((url_path, w, os.path.getsize(out)))
    lines = ["# 스크린샷 — 실제로 보이는 모습", "",
             "`python3.11 tools/render_screens.py --shot` 로 만든다.",
             "", "★ 돌고 있는 서비스를 headless firefox 로 찍은 것이다.",
             "", "| 화면 | 폭 | 파일 | 크기 |", "|---|--:|---|--:|"]
    for path, w, size in made:
        name = (path.strip("/").replace("/", "_") or "home")
        lines.append(f"| `{path}` | {w} | [{name}_{w}.png]({name}_{w}.png) "
                     f"| {size:,}B |")
    with open(os.path.join(SHOT_DIR, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"스크린샷 {len(made)}장 → outputs/shot/")
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    rc = main(args[0] if args else "carwatch.db")
    if "--shot" in sys.argv:
        rc = shoot() or rc
    sys.exit(rc)
