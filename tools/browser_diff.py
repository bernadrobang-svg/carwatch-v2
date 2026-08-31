# -*- coding: utf-8 -*-
"""★★★★★ 09-01 마스터 지시 — ★ **브라우저로 시안과 화면을 대조한다.**

★ 마스터 — 「★ 이제 모든 화면이 시안과 일치하는지를 ★ **브라우저를 통해서** 대조를 해.
   ★ ★ **모바일용 태블릿용으로 나누어서** ★ 제대로 되는지 · 일치하는지 확인해」

★★ 왜 브라우저인가 — ★ 글자만 견주면 ★ **보이는 것을 못 본다.**
  ★ 실측 09-01 — ★ 내가 표로 만든 추천 화면은 ★ 글자 대조를 통과했는데
    ★ ★ 브라우저로 여니 ★ 시안은 ★ **카드**였다.  ★ 사진 주소 자리에 ★ dict 가 통째로 들어가 있었다

돌리는 법
    python3.11 tools/browser_diff.py              ★ 다 본다
    python3.11 tools/browser_diff.py recommend    ★ 하나만
"""
from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

SIAN = os.path.join(ROOT, "ref", "screens")
RENDER = os.path.join(ROOT, "outputs", "render")
# ★ 마스터 지시 — ★ **모바일용·태블릿용으로 나눈다**
SIZES = (("모바일", 390, 844), ("태블릿", 820, 1180))
# ★ 재는 것 — ★ 보이는 글·가로 넘침·눌러야 닿는 크기
TAP_MIN = 44          # ★ 손가락이 닿는 최소 (UI_REVIEW · 시안 `.v4-btn`)


def pairs() -> list:
    """시안 ↔ 렌더 짝.  ★ 손으로 나열하지 않는다 (D-2)."""
    out = []
    for name in sorted(os.listdir(SIAN)):
        m = re.match(r"v4m_(.+?)_시안\.html$", name)
        if not m:
            continue
        got = os.path.join(RENDER, m.group(1) + ".html")
        if os.path.isfile(got):
            out.append((m.group(1), os.path.join(SIAN, name), got))
    return out


def look(pg, url: str) -> dict:
    """한 쪽을 열어 ★ **보이는 것**을 잰다.

    ★★★★★ 09-01 — ★ 렌더는 ★ `/static/app.css` 를 ★ 절대 경로로 부른다.
      ★ `file://` 로 열면 ★ **CSS 가 안 붙는다** — ★ 실측 09-01 (`minHeight: 0px`).
      ★ ★ 그러면 ★ 「44px 미만」·「가로 넘침」이 ★ **다 거짓**이 된다.
      ★ ★ ★ 그래서 ★ 그 자리에 ★ 우리 CSS 를 ★ 끼워 넣고 잰다
    """
    pg.goto("file://" + url)
    pg.add_style_tag(path=os.path.join(ROOT, "web", "static", "app.css"))
    return pg.evaluate("""() => {
        const w = document.documentElement.clientWidth;
        const vis = e => {
            const s = getComputedStyle(e);
            return s.display !== 'none' && s.visibility !== 'hidden';
        };
        const over = [];
        const small = [];
        for (const e of document.querySelectorAll('*')) {
            if (!vis(e)) continue;
            const r = e.getBoundingClientRect();
            if (r.width > w + 2 && e.children.length < 3)
                over.push(e.tagName + '.' + (e.className || '').toString().slice(0, 24));
            if (e.matches('a,button,input[type=submit]') && r.height > 0
                && r.height < 44 && r.width > 0)
                small.push(Math.round(r.height) + 'px ' + (e.innerText || '').slice(0, 14));
        }
        return {
            text: (document.body.innerText || '').replace(/\\s+/g, ' ').trim(),
            docw: document.documentElement.scrollWidth,
            over: over.slice(0, 4),
            small: small.slice(0, 4),
        };
    }""")


def main() -> int:
    only = next((a for a in sys.argv[1:] if not a.startswith("-")), None)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("★ playwright 가 없다 — pip3.11 install --user playwright")
        return 2
    got = pairs()
    if only:
        got = [g for g in got if g[0] == only]
    if not got:
        print("★ 짝이 없다"); return 1
    bad = 0
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for label, w, h in SIZES:
            pg = b.new_page(viewport={"width": w, "height": h})
            print(f"\n★★ {label} ({w}×{h})")
            for name, sian, ours in got:
                a = look(pg, sian)
                o = look(pg, ours)
                # ★ 시안에 있는 낱말이 ★ 우리 화면에 다 있는가
                words = [x for x in re.findall(r"[가-힣]{2,}", a["text"])
                         if len(x) >= 3]
                miss = sorted({x for x in set(words) if x not in o["text"]})
                note = []
                if o["docw"] > w + 2:
                    note.append(f"★ 가로 넘침 {o['docw']}px")
                if o["over"]:
                    note.append(f"★ 넘치는 칸 {o['over'][:2]}")
                if o["small"]:
                    note.append(f"★ 44px 미만 {len(o['small'])}개")
                if miss[:6]:
                    note.append(f"★ 시안에만 있는 말 {miss[:6]}")
                if note:
                    bad += 1
                print(f"   {name:<14} " + ("  ·  ".join(note) if note else "맞다"))
            pg.close()
        b.close()
    print(f"\n★ 어긋난 자리 {bad}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
