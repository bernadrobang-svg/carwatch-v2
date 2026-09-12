#!/usr/bin/env python3
"""한 판 — 재고 · 검사하고 · 붉은 것을 낸다 (09-08 마스터 지시).

마스터 — 「이제 자동화를 하자. 클로드가 없더라도 알아서 수행하는 것으로」

사람이 붙어 있지 않아도 이 하나만 돌리면 된다.
  ① 사이트마다 칸 채움율을 잰다 (tools/fill_gate)
  ② 엔카·KB 수집을 잰다
  ③ 화면을 네 너비로 잰다 (390·600·760·900)
  ④ 검사 전부를 돌린다
  ⑤ 붉은 것만 모아 outputs/ROUND.md 에 낸다 — 담당까지 갈라서

돌리기  python3 tools/round.py 배포주소
크론    0 * * * * cd /path && python3 tools/round.py https://... >> /tmp/round.log
"""
import io
import os
import re
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
OUT = os.path.join(ROOT, "outputs", "ROUND.md")

GUIDE = ("docs/", "ref/screens", "outputs/ORDER", "03_이력", "00_버전",
         "06_오판", "config/targets", "config/vehicle_table", "config/scoring",
         "app.css", "web/templates")
DEV = ("collect/", "store/", "score/", "parse/", "adapters/", "run.py",
       "tools/", "web/views")


def _who(doc: str) -> str:
    g = any(k in doc for k in GUIDE)
    d = any(k in doc for k in DEV)
    if g and d:
        return "둘다"
    return "가이드" if g else ("개발측" if d else "배포·값")


def measure(base_url: str) -> dict:
    got = {}
    for name, fn in (("채움율", "tools.fill_gate:run"),
                     ("엔카", "tools.browser_diff:encar_collect_report"),
                     ("KB", "tools.browser_diff:kb_collect_report")):
        mod, f = fn.split(":")
        try:
            m = __import__(mod, fromlist=[f])
            getattr(m, f)(base_url)
            got[name] = "쟀다"
        except Exception as e:  # noqa: BLE001
            got[name] = f"★ {type(e).__name__}"
    return got


def screens() -> list:
    """시안을 네 너비로 잰다. 사람이 눈으로 안 봐도 가려진 글자를 잡는다."""
    try:
        from playwright.sync_api import sync_playwright
        from tools.browser_diff import HIDDEN_TEXT_JS, BOX_OVERLAP_JS
    except Exception:  # noqa: BLE001
        return []
    bad = []
    d = os.path.join(ROOT, "ref", "screens")
    files = sorted(f for f in os.listdir(d) if f.startswith("v4m_"))
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_context(viewport={"width": 390, "height": 1400}).new_page()
        for f in files:
            for w in (390, 600, 760, 900):
                pg.set_viewport_size({"width": w, "height": 1400})
                pg.goto("file://" + os.path.join(d, f), wait_until="networkidle")
                pg.wait_for_timeout(250)
                h = pg.evaluate(HIDDEN_TEXT_JS)["hidden"]
                o = pg.evaluate(BOX_OVERLAP_JS)["overlap"]
                if h or o:
                    bad.append(f"{f} {w}px — 가려진 {h} · 겹침 {o}")
        br.close()
    return bad


def _freshen() -> None:
    """★ 09-12 (R-1) — ★ `collected_at` 을 ★ **원문에서 되살린다.**

    ★★ 실측 09-12 — ★ 이 칸이 ★ 엔카 말고 ★ **열한 곳 전부 빈칸**이었다.
      ★ 수집은 ★ **돌고 있었는데** (`carwatch-daily` 가 열 곳의 목록을 받는다)
        ★ ★ 그 칸을 ★ 아무도 안 써서 ★ **화면이 「안 돌았다」로 보였다.**
    ★ 한 판마다 되살린다 — ★ 그래야 현황 화면이 ★ 늘 참말이다
    """
    try:
        from tools.fill_collected_at import run as fill

        got = fill(write=True)
        n = sum(v for k, v in got.items() if "원문이 없다" not in k)
        if n:
            print(f"  collected_at 을 {n:,}건 되살렸다", flush=True)
    except Exception as exc:                    # noqa: BLE001
        print(f"  collected_at 되살리기가 실패했다 — {exc}", flush=True)


def run(base_url: str) -> str:
    import validate.v0_guide as V

    src = io.open(os.path.join(ROOT, "validate", "v0_guide.py"),
                  encoding="utf-8").read()
    _freshen()
    got = measure(base_url)
    bad_screens = screens()

    red = []
    for row in V.CHECKS:
        code, name, fn = row[0], row[1], row[2]
        try:
            ok, why = fn()
        except Exception as e:  # noqa: BLE001
            ok, why = False, f"ERR {type(e).__name__}"
        if ok:
            continue
        i = src.find("def " + fn.__name__)
        red.append((code, _who(src[i:i + 3000] if i > 0 else ""), name,
                    re.sub(r"\s+", " ", str(why))[:80]))

    #   ★ 09-10 — ★ 어느 DB 를 봤는지 ★ 함께 낸다.
    #     ★ 가이드 자리에서는 ★ 옛 판(`tmp/load-*.db`)을 본다 — ★ 가늠일 뿐이다.
    #     ★ ★ 참말은 ★ **배포에서 돌린 것**이다.
    try:
        db = str(V._pick_db())
    except Exception:  # noqa: BLE001
        db = "?"
    ver = ""
    m = re.search(r"SPEC-[\d.]+-r\d+",
                  io.open(os.path.join(ROOT, "docs", "guide", "00_버전.md"),
                          encoding="utf-8").read())
    if m:
        ver = m.group(0)

    by = {}
    for c, w, n, why in red:
        by.setdefault(w, []).append((c, n, why))

    lines = [f"# 한 판 · {ver}", "",
             f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC · {base_url}",
             "",
             f"검사 **{len(V.CHECKS)}** · 통과 **{len(V.CHECKS) - len(red)}** · "
             f"붉은 것 **{len(red)}**", ""]
    lines += ["| 잰 것 | 결과 |", "|---|---|",
              f"| 본 DB | `{db}` |"]
    for k, v in got.items():
        lines.append(f"| {k} | {v} |")
    lines.append(f"| 화면 | {'깨끗' if not bad_screens else f'★ {len(bad_screens)}곳'} |")
    if bad_screens:
        lines += ["", "## 화면 결함", ""] + [f"- {b}" for b in bad_screens]
    for w in ("가이드", "개발측", "배포·값", "둘다"):
        if w not in by:
            continue
        lines += ["", f"## {w} — {len(by[w])}개", "",
                  "| 검사 | 무엇 | 지금 |", "|---|---|---|"]
        for c, n, why in by[w]:
            lines.append(f"| `{c}` | {n} | {why} |")
    text = "\n".join(lines) + "\n"
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"검사 {len(V.CHECKS)} · 붉은 것 {len(red)} · 화면 결함 {len(bad_screens)} → {OUT}")
    for w, xs in by.items():
        print(f"  {w}: {len(xs)}개")
    return OUT


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "https://54.180.227.109.sslip.io")
