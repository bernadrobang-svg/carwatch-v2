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
            // ★★★★★ 09-02 — ★ **미는 상자 안은 넘친 것이 아니다.**
            //   ★ 실측 09-02 — ★ 관심 화면의 표를 ★ `overflow-x:auto` 로 감쌌는데
            //   ★ ★ 그 안의 `THEAD`·`TBODY` 가 ★ 여전히 「넘친다」로 잡혔다.
            //   ★ ★ ★ 「좁으니 그 표만 옆으로 민다」가 ★ 규격이 시킨 것이다
            //     ★ ★ (`V11-70`·`V11-71` — ★ **몸통**이 밀리면 안 된다는 뜻이다).
            //   ★★ 그러므로 ★ 조상 중에 ★ 미는 상자가 있으면 ★ 세지 않는다.
            //     ★ ★ 쪽 전체가 넘치는 것은 ★ `docw` 가 따로 잡는다
            const scrollable = (el) => {
                for (let a = el.parentElement; a; a = a.parentElement) {
                    const ox = getComputedStyle(a).overflowX;
                    if (ox === 'auto' || ox === 'scroll') return true;
                }
                return false;
            };
            if (r.width > w + 2 && e.children.length < 3 && !scrollable(e))
                over.push(e.tagName + '.' + (e.className || '').toString().slice(0, 24));
            if (e.matches('a,button,input[type=submit]') && r.height > 0
                && r.height < 44 && r.width > 0)
                small.push(Math.round(r.height) + 'px ' + (e.innerText || '').slice(0, 14));
        }
        return {
            // ★★★★★ 09-02 — ★ `innerText` 는 ★ **접힌 `<details>` 속 글을 안 준다**.
            //   ★ 실측 09-02 — ★ 「거르개」·「낮은순」이 ★ 화면에 **있는데**
            //   ★ ★ 「시안에만 있는 말」로 나왔다.  ★ 거짓 어긋남이다.
            //   ★★ 낱말을 견줄 때는 ★ `textContent` 다 — ★ 접힌 것도 센다.
            //     ★ ★ 자리·크기는 ★ 어차피 ★ `getBoundingClientRect` 로 잰다
            // ★ `textContent` 는 ★ 칸 사이를 안 띄운다 —
            //   ★ 「관리」＋「리포트」가 ★ 「관리리포트」로 붙는다 [실측 09-02].
            //   ★ 그래서 ★ **덩이 칸마다 사이를 넣어** 잇는다
            text: Array.from(document.body.querySelectorAll(
                    'p,li,td,th,h1,h2,h3,div,span,a,button,option,summary'))
                  .map(e => e.textContent || '').join(' ')
                  .replace(/\\s+/g, ' ').trim(),
            docw: document.documentElement.scrollWidth,
            over: over.slice(0, 4),
            small: small.slice(0, 12),
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
                    if "--detail" in sys.argv:
                        note.append("  " + " | ".join(o["small"][:8]))
                # ★★★★★ 09-02 — ★ **자리 결함과 낱말을 갈라 센다.**
                #   ★ 시안의 글에는 ★ **표본 값**이 섞여 있다 —
                #   ★ ★ 「폴스타」·「진주색」·「롱레인지」는 ★ 시안이 지어 넣은 차다.
                #   ★ ★ ★ 우리 DB 에 그 차가 없는 것은 ★ **결함이 아니다.**
                #   ★★ 그래서 ★ 「어긋난 자리」는 ★ **가로 넘침 · 넘치는 칸 ·
                #     ★ 44px 미만**만 센다.  ★ 낱말은 ★ 곁에 적어 ★ 사람이 본다 —
                #     ★ ★ **숨기지 않는다.**  ★ 세는 자리만 다르다
                if note:
                    bad += 1
                if miss[:6]:
                    note.append(f"살펴볼 말 {miss[:6]}")
                print(f"   {name:<14} " + ("  ·  ".join(note) if note else "맞다"))
            pg.close()
        b.close()
    print(f"\n★ 어긋난 자리 {bad}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
