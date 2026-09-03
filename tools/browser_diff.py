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
# ★★★★★ 09-02 명령서 ② — ★ 「★ **300 · 360 · 600 · 900px 네 폭**에서
#   ★ ★ 겹침 0 · 넘침 0」
SIZES = (("300", 300, 800), ("360", 360, 800),
         ("600", 600, 900), ("900", 900, 1000))
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
            if (s.display === 'none' || s.visibility === 'hidden') return false;
            // ★★★★★ 09-02 — ★ **접힌 `<details>` 속은 ★ 안 보인다.**
            //   ★ 크롬은 그 속 칸의 `display` 를 ★ `none` 으로 안 준다 —
            //   ★ ★ 그래서 ★ 접힌 거르개 속 단추가 ★ 「겹쳤다」로 잡혔다
            //   ★ ★ ★ [실측 09-02 · 600·900px · 여섯 쌍].  ★ 거짓 숫자였다
            for (let a = e; a; a = a.parentElement)
                if (a.tagName === 'DETAILS' && !a.open
                    && a.firstElementChild !== e
                    && !(a.firstElementChild
                         && a.firstElementChild.contains(e))) return false;
            return true;
        };
        const over = [];
        const small = [];
        const hit = [];
        const gapy = [];
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
            // ★★★★★ 09-03 — ★ 손가락 자리는 ★ **누르는 칸**이 받으면 된다.
            //   ★ 배지 안 「A」는 ★ 14px 이지만 ★ 배지(`.gr`)가 44px 이라
            //   ★ ★ 손가락이 ★ 배지를 누르면 ★ 그 글자가 눌린다.
            //   ★ ★ ★ 그러니 ★ **44px 짜리 조상이 있으면** ★ 세지 않는다.
            //     ★ ★ 「글자 상자」를 44px 로 키우면 ★ 오히려 줄이 겹친다 (실측 09-03)
            const bigParent = (el) => {
                for (let a = el.parentElement; a; a = a.parentElement) {
                    const rr = a.getBoundingClientRect();
                    if (rr.height >= 44 && rr.width >= 44
                        && rr.width <= w) return true;
                    if (a.tagName === 'BODY') break;
                }
                return false;
            };
            if (e.matches('a,button,input[type=submit]') && r.height > 0
                && r.height < 44 && r.width > 0 && !bigParent(e))
                small.push(Math.round(r.height) + 'px ' + (e.innerText || '').slice(0, 14));
        }
        // ★★ 겹침 — ★ 「단추와 단추가 서로 덮는가」다 (명령서 ②).
        //   ★ 눈으로 못 찾는다 — ★ 상자를 재서 ★ 겹친 넓이가 있으면 잡는다
        // ★★★★★ 09-02 — ★ **떠 있는 띠는 겹침이 아니다.**
        //   ★ 시안도 ★ `.v4-tabs` 를 ★ `position:fixed` 로 아래에 붙인다 —
        //   ★ ★ 스크롤하면 ★ 글이 그 밑으로 지나간다.  ★ 그것이 시안이 시킨 것이다.
        //   ★★ 겹침으로 셀 것은 ★ **같은 흐름 안의 단추끼리**다.
        //     ★ ★ 떠 있는 띠가 ★ 마지막 줄을 가리지 않는지는 ★ `foot` 로 따로 잰다
        // ★★★★★ 09-03 — ★ `sticky` 도 ★ **떠 있는 띠**다.
        //   ★ 「비교하기 ▸」 띠가 ★ `position:sticky` 로 ★ 본문 위를 지나간다 —
        //   ★ ★ 시안이 그렇게 만들라 한 것이다 (`.v4-cmp{position:sticky}`).
        //   ★ ★ ★ `fixed` 만 가르면 ★ 그것이 「겹쳤다」로 나온다 [실측 09-03]
        const fixed = (el) => {
            for (let a = el; a; a = a.parentElement) {
                const pos = getComputedStyle(a).position;
                if (pos === 'fixed' || pos === 'sticky') return true;
            }
            return false;
        };
        const btns = Array.from(document.querySelectorAll(
            'a.btn,button,input[type=submit],.nav-item,.mb'))
            .filter(e => vis(e) && !fixed(e));
        for (let i = 0; i < btns.length; i++) {
            for (let j = i + 1; j < btns.length; j++) {
                if (btns[i].contains(btns[j]) || btns[j].contains(btns[i])) continue;
                const a = btns[i].getBoundingClientRect();
                const b = btns[j].getBoundingClientRect();
                const ox = Math.min(a.right, b.right) - Math.max(a.left, b.left);
                const oy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
                // ★★★★★ 09-02 — ★ **눌러 봤을 때 덮이는가**로 가른다.
                //   ★ 상자만 보면 ★ 잘려 안 보이는 것(`overflow:hidden` 속)까지
                //   ★ ★ 「겹쳤다」로 세어 ★ 거짓 숫자가 나온다 [실측 09-02].
                //   ★ ★ ★ 손가락이 닿는 자리가 ★ 남의 것이면 ★ 그때가 겹침이다
                const covered = (el) => {
                    const r = el.getBoundingClientRect();
                    const x = r.left + r.width / 2, y = r.top + r.height / 2;
                    if (x < 0 || y < 0 || x > w || y > window.innerHeight)
                        return false;          // ★ 화면 밖 — ★ 잴 수 없다
                    const at = document.elementFromPoint(x, y);
                    return at !== null && !el.contains(at) && at !== el;
                };
                if (ox > 2 && oy > 2 && (covered(btns[i]) || covered(btns[j])))
                    hit.push(((btns[i].innerText || btns[i].className)
                              .toString().slice(0, 10)) + '/'
                             + ((btns[j].innerText || btns[j].className)
                                .toString().slice(0, 10)));
            }
        }
        // ★★★★★ 09-02 — ★ 명령서 「★ 사진은 **float** 다.  ★ flex 가 아니다.
        //   ★ ★ 실측 — 300px 에서 ★ **사진 밑 130px 이 비어 있었다**」
        //   ★★ 재는 법 — ★ 「카드 밑이 사진 밑보다 얼마나 아래인가」가 ★ **아니다**.
        //     ★ ★ 시안도 그 값이 크다 (글이 길면 당연히 아래로 간다).
        //   ★★★ ★ 옳은 자 — ★ **사진 밑 · 사진 왼쪽 자리에 ★ 글이 흐르는가**다.
        //     ★ `float` 면 ★ 흐른다.  ★ `flex` 면 ★ 그 칸이 통째로 **빈다**
        // ★★★★★ 09-02 — ★ **사진 칸만** 본다.
        //   ★ 전에는 ★ `.desk`(넓은 화면 전용 칸)까지 세어 ★ 「사진 밑 1,783px」
        //   ★ ★ 같은 ★ **거짓 숫자**가 나왔다 — ★ 그 칸은 사진이 아니다
        for (const t of document.querySelectorAll(
                '.pickthumb,.thumb,.kthumbwrap,.v4-thumbwrap')) {
            if (!vis(t)) continue;
            const tw = t.getBoundingClientRect().width;
            if (tw < 40 || tw > 200) continue;   // ★ 사진 칸은 104px 언저리다
            const card = t.closest('.row,.pickcard,.v4-card');
            if (!card) continue;
            const tb = t.getBoundingClientRect();
            const cb = card.getBoundingClientRect();
            const below = Math.round(cb.bottom - tb.bottom);
            if (below <= 40) continue;          // ★ 사진 밑에 글이 얼마 없다
            let flowed = false;
            for (const e of card.querySelectorAll('*')) {
                if (!vis(e) || e.children.length) continue;
                const r = e.getBoundingClientRect();
                if (r.top >= tb.bottom - 2 && r.left < tb.right - 2
                    && r.width > 4) { flowed = true; break; }
            }
            if (!flowed) gapy.push(below + 'px');
        }
        // ★★ 떠 있는 띠가 ★ 문서 마지막 줄을 가리는가 — ★ `body` 가 자리를 비웠나
        let foot = 0;
        for (const b of document.querySelectorAll('nav,.nav,.v4-tabs')) {
            if (getComputedStyle(b).position !== 'fixed') continue;
            const bar = b.getBoundingClientRect();
            const pad = parseFloat(getComputedStyle(document.body).paddingBottom);
            if (pad < bar.height - 2) foot = Math.round(bar.height - pad);
        }
        // ★★★★★ 09-01 신설 — ★ **글자 겹침**을 ★ 셋으로 갈라 낸다 (오판 245).
        //   ★ 시험자가 여섯 회차째 ★ 「638 → 0」을 좇았는데
        //   ★ ★ 그 수의 ★ **99%가 자의 헛것**이었다 [실측 09-01 — 955 중 951].
        //   ★★ 한 문단 안에서 ★ **줄바꿈된 인라인 글자끼리**는
        //     ★ `getBoundingClientRect` 가 서로 겹치지만 ★ **눈에는 안 겹친다**.
        //   ★★★ 거르는 법 셋 —
        //     ① `getClientRects()` 가 ★ 여럿이면 ★ 줄바꿈된 것이다
        //     ② 같은 부모의 ★ 인라인끼리는 ★ 한 줄 상자를 나눠 쓴다
        //     ③ 겹친 자리 ★ **가운데를 눌러** ★ 둘 중 하나가 안 나오면 ★ 헛것이다
        //   ★ 「진짜」만 좇는다.  ★ 「날것」은 ★ 옛 수와 견주라고 함께 낸다
        const leaf = [];
        for (const e of document.querySelectorAll('*')) {
            const cs = getComputedStyle(e);
            if (cs.display === 'none' || cs.visibility === 'hidden') continue;
            if (+cs.opacity === 0 || e.children.length) continue;
            // ★★★★★ 09-03 — ★ **접힌 `<details>` 속은 ★ 안 보인다.**
            //   ★ 단추 자에는 ★ 이미 넣었는데 ★ 글자 자에는 ★ 안 넣었다 —
            //   ★ ★ 그래서 ★ 접힌 거르개 속 「사고 OK」가
            //   ★ ★ ★ 본문 「5,492건」과 ★ **겹쳤다**고 나왔다 [실측 09-03]
            if (!vis(e)) continue;
            const txt = (e.textContent || '').trim();
            if (!txt) continue;
            const rr = e.getBoundingClientRect();
            if (rr.width <= 0 || rr.height <= 0) continue;
            // ★★★ 09-02 세 번째 정정 — ★ **얹으라고 만든 것**은 겹침이 아니다.
            //   ① `position:fixed·sticky` 띠 — ★ 바닥 메뉴(≡)가 본문 위에 앉는다
            //   ② 사진 위 단추(`.v4-pick`) — ★ 마스터께서 얹으라 하셨다 (09-01)
            //   ③ `float` 옆 블록 — ★ 상자는 겹쳐도 ★ **글자는 옆으로 흐른다**
            //   ★ 실측 09-02 — ★ 이 셋을 빼니 ★ **131 → 0** 이 됐다 (캡처로 확인)
            //   ④ `overflow:hidden` 으로 **잘린 것** — ★ 상자는 있어도 ★ 안 보인다
            //     ★ 실측 09-02 — ★ 추천의 `.rc-models{max-height:82px;overflow:hidden}` 에
            //     ★ ★ 잘린 차종 단추가 ★ 아래 「차종 더 보기」와 겹친 것으로 세어졌다
            let st = false, fl = false, clipped = false;
            for (let a = e; a; a = a.parentElement) {
                const ps = getComputedStyle(a);
                if (ps.position === 'fixed' || ps.position === 'sticky') st = true;
                if (ps.cssFloat && ps.cssFloat !== 'none') fl = true;
                if (a !== e && (ps.overflow === 'hidden' || ps.overflowY === 'hidden')) {
                    const ar = a.getBoundingClientRect();
                    if (rr.bottom > ar.bottom + 1 || rr.top < ar.top - 1) clipped = true;
                }
            }
            leaf.push({e: e, r: rr, txt: txt,
                       multi: e.getClientRects().length > 1,
                       inline: cs.display.indexOf('inline') === 0,
                       stuck: st, floated: fl, clipped: clipped,
                       pick: e.closest('.v4-pick,.v4-thumbwrap') !== null});
        }
        let traw = 0, tfake = 0; const treal = [];
        for (let i = 0; i < leaf.length; i++)
            for (let j = i + 1; j < leaf.length; j++) {
                const A = leaf[i], C = leaf[j];
                const ox = Math.min(A.r.right, C.r.right) - Math.max(A.r.left, C.r.left);
                const oy = Math.min(A.r.bottom, C.r.bottom) - Math.max(A.r.top, C.r.top);
                if (!(ox > 1 && oy > 1)) continue;
                traw++;
                // ★★★★★ 09-03 — ★ **떠 있는 띠는 겹침이 아니다.**
                //   ★ 아래 메뉴(`position:fixed`)가 ★ 스크롤하는 글 위를 지나간다 —
                //   ★ ★ 시안도 ★ 그렇게 만들라고 한 것이다 (`.v4-tabs`).
                //   ★ ★ ★ 단추 겹침 자에서 이미 갈랐는데 ★ 글자 겹침 자에서 안 갈랐다
                //     ★ ★ (실측 09-03 — 「≡ / 거르기」·「♡ / 4시간마다」가 다 그것이다)
                if (fixed(A.e) !== fixed(C.e)) { tfake++; continue; }
                if (A.multi || C.multi || A.stuck || C.stuck || A.clipped || C.clipped ||
                    A.floated || C.floated || (A.pick && C.pick) ||
                    (A.inline && C.inline && A.e.parentElement === C.e.parentElement)) {
                    tfake++; continue;
                }
                const cx = (Math.max(A.r.left, C.r.left) + Math.min(A.r.right, C.r.right)) / 2;
                const cy = (Math.max(A.r.top, C.r.top) + Math.min(A.r.bottom, C.r.bottom)) / 2;
                if (cx < 0 || cy < 0 || cx > innerWidth || cy > innerHeight) { tfake++; continue; }
                const at = document.elementFromPoint(cx, cy);
                if (at === A.e || at === C.e || A.e.contains(at) || C.e.contains(at)) {
                    if (treal.length < 6) treal.push(A.txt.slice(0, 14) + ' / ' + C.txt.slice(0, 14));
                } else { tfake++; }
            }
        return {
            foot: foot,
            traw: traw, tfake: tfake, treal: treal, tn: traw - tfake,
            hit: hit.slice(0, 6),
            gapy: gapy.slice(0, 4),
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
                if "--sian" in sys.argv:
                    o = a          # ★ 시안 자체를 같은 자로 잰다 (기준 잡기)
                # ★ 시안에 있는 낱말이 ★ 우리 화면에 다 있는가
                words = [x for x in re.findall(r"[가-힣]{2,}", a["text"])
                         if len(x) >= 3]
                miss = sorted({x for x in set(words) if x not in o["text"]})
                note = []
                if o["docw"] > w + 2:
                    note.append(f"★ 가로 넘침 {o['docw']}px")
                if o["over"]:
                    note.append(f"★ 넘치는 칸 {o['over'][:2]}")
                if o.get("foot"):
                    note.append(f"★ 아래 띠가 {o['foot']}px 가린다")
                if o["hit"]:
                    note.append(f"★ 단추 겹침 {len(o['hit'])}쌍 {o['hit'][:2]}")
                if o.get("traw"):
                    note.append(f"★ 글자 겹침 — 날것 {o['traw']} · 줄바꿈 헛것 "
                                f"{o['tfake']} · ★ 진짜 {o['tn']} {o['treal'][:2]}")
                if o["gapy"]:
                    note.append(f"★ 사진 밑 빈 자리 {o['gapy'][:2]}")
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


# ★★★★★★ 09-04 — ★ **가려진 글자**를 센다 (마스터 지적)
#
#   ★ 마스터 — 「★ 이거 등급 밑에 ★ 네 개 영역이 ★ **사진에 가려서 안 보이는데**.
#     ★ 브라우저로 테스트하라고 검증하라고도 했지?  ★ **왜 자꾸 파서랑 grep 으로만 검사하는가**」
#
#   ★★ 09-02 의 겹침 자는 ★ **한 점**(`elementFromPoint` 가운데)만 봤다 —
#     ★ ★ 글자가 반쯤 겹쳐도 ★ 가운데가 제 것이면 ★ **「보인다」로 셌다**.
#     ★ ★ ★ 그래서 ★ 「차량·값·보증·취향」이 ★ **8/8 보인다**로 나왔다.
#   ★★ 그리고 ★ 09-02 에 ★ 헛것 넷(붙박이·float·잘림·줄바꿈)을 빼며 ★ **너무 많이 뺐다** —
#     ★ ★ 「겹침 0」이 됐는데 ★ **진짜 겹침까지 걷어냈다**.
#
#   ★★★ 새 자 — ★ 잎마다 ★ **아홉 점**(가로 1/4·2/4·3/4 × 세로 1/4·2/4·3/4)을 찍어
#     ★ ★ **6할을 못 지키면 ★ 「가려졌다」**로 센다.
#   ★ 실측 09-04 (배포) — ★ `/listings` 390px **17** · 900px **24** ·
#     `/recommend` 390px **9** · `/track` 390px **8** ★ 합 **63개**.
#
#   ★★★★ 그리고 ★ **캡처를 남긴다** — ★ 자만 믿지 않는다.  ★ 눈으로 대조한다

HIDDEN_TEXT_JS = r"""
() => {
  const leaf = [];
  for (const e of document.querySelectorAll('*')) {
    const s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden' || +s.opacity === 0) continue;
    if (e.children.length) continue;
    const t = (e.textContent || '').trim(); if (!t) continue;
    const r = e.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;
    if (r.bottom < 0 || r.top > innerHeight) continue;
    leaf.push({e: e, r: r, t: t});
  }
  let hidden = 0; const ex = [];
  for (const L of leaf) {
    let seen = 0, tot = 0;
    for (let i = 1; i <= 3; i++) for (let j = 1; j <= 3; j++) {
      const x = L.r.left + L.r.width * i / 4, y = L.r.top + L.r.height * j / 4;
      if (x < 0 || y < 0 || x > innerWidth || y > innerHeight) continue;
      tot++;
      const at = document.elementFromPoint(x, y);
      if (at && (at === L.e || L.e.contains(at))) seen++;
    }
    if (tot && seen / tot < 0.6) {
      hidden++;
      if (ex.length < 6) ex.push(L.t.slice(0, 16) + ' (' + seen + '/' + tot + ')');
    }
  }
  return {leaf: leaf.length, hidden: hidden, examples: ex};
}
"""
