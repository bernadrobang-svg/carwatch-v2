"""★★★★★ 제원(전장)을 ★ **브라우저로** 받는다 — 명령서 10번 (`S46-233`).

★ 까닭   ★ 제네시스 공식 제원표는 ★ JS 로 채워져 ★ `curl` 로는 「-」만 온다
         ★ (실측 09-01).  ★ 그래서 ★ 크로미움으로 ★ **그린 뒤** 글자를 읽는다
★★      ★ **값을 지어내지 않는다** — ★ 쪽에서 못 찾으면 ★ 「못 찾았다」로 낸다.
         ★ 기억으로 박는 것이 ★ 오판 무늬 ㉯ 다 (가이드가 09-01 에 두 번 틀렸다)
쓰기     python3.11 tools/fetch_dimensions.py <URL> [<URL> …]
낸다     ★ URL · 찾은 자리의 글월 · 전장(mm) 후보
"""
from __future__ import annotations

import re
import sys

# ★ 「전장」 뒤 4자리, 또는 「4,715×1,910」 꼴의 첫 수.
#   ★ 3,000~5,500mm 만 본다 — ★ 축거·전폭·가격이 섞여 들어오는 것을 막는다
_NUM = r"([3-5],?\d{3})"
PATS = (
    re.compile(r"전\s*장[^0-9]{0,20}" + _NUM),
    re.compile(r"전장\(mm\)[^0-9]{0,20}" + _NUM),
    re.compile(_NUM + r"\s*[×xX*]\s*1,?\d{3}\s*[×xX*]\s*1,?\d{3}"),
    re.compile(r"[Ll]ength[^0-9]{0,20}" + _NUM),
)


_GEN = re.compile(
    r"(?:First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth)"
    r"\s+generation\s*\(([^)]{0,50})\)")


def _gens(text: str) -> list[str]:
    """★★★★★ 09-02 명령서 17·18 — ★ **세대가 갈리는 「해」**를 뽑는다.

    ★ 까닭   ★ 전장만 있고 ★ 갈림 해가 없으면 ★ `by_year` 를 못 적는다.
             ★ ★ 「2017년식은 어느 세대인가」를 못 가르면 ★ **틀린 점수**다
    ★★      ★ 제원 상자의 「Production」은 ★ 맨 위 상자 것이 섞여 못 쓴다
             ★ (실측 09-02 — X3 가 「2003–present」 하나만 나왔다).
             ★ ★ **차례 머리말**이 곧다 — 「Third generation (G01; 2017)」
    ★        ★ 못 찾으면 ★ **빈 목록**이다 — ★ 해를 지어내지 않는다
    """
    out: list[str] = []
    for m in _GEN.finditer(text):
        g = " ".join(m.group(1).split())
        if g not in out:
            out.append(g)
    return out


def _hits(text: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for pat in PATS:
        for m in pat.finditer(text):
            n = int(m.group(1).replace(",", ""))
            if not 3000 <= n <= 5500:
                continue
            # ★★★★★ 09-02 명령서 17·18 — ★ **갈림 해**가 있어야
            #   ★ `by_year` 를 적을 수 있다.  ★ 위키 제원 상자는
            #   ★ ★ 「Production 2017–2024」를 ★ 전장보다 **앞**에 둔다 —
            #   ★ ★ ★ 그래서 앞을 ★ **넓게** 본다 (40 → 400자).
            #   ★ 해를 못 찾으면 ★ **적지 않는다** — ★ 지어내지 않는다
            lo = max(0, m.start() - 400)
            back = " ".join(text[lo:m.start()].split())
            yrs = re.findall(r"(?:Production|생산)[^0-9]{0,12}"
                             r"(\d{4}\s*[–\-~]\s*(?:\d{4}|present|현재)?"
                             r"|\d{4})", back)
            tail = " ".join(text[m.start():m.end() + 20].split())
            out.append((str(n), (f"[생산 {yrs[-1]}] " if yrs else "") + tail))
    return out


def fetch(url: str) -> None:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1280, "height": 2000})
        try:
            pg.goto(url, timeout=45000, wait_until="load")
            pg.wait_for_timeout(2500)   # ★ 표가 늦게 차는 쪽이 있다
        except Exception as e:  # noqa: BLE001 ★ 조용히 넘기지 않는다 — 무엇이 막혔는지 낸다
            print(f"  ✗ {url}\n     {type(e).__name__}: {str(e)[:90]}")
            b.close()
            return
        # ★★★★★ 09-02 — ★ **먼저 읽고, ★ 못 찾을 때만 누른다.**
        #   ★ 전에는 ★ 무조건 「Specifications」를 눌렀는데 ★ 위키 **각주**가
        #     ★ ★ 걸려 ★ **BMW 보도자료 쪽으로 넘어가** ★ 엉뚱한 글을 읽었다
        #     ★ ★ ★ (실측 09-02 — `BMW_X3_(G01)` 이 ★ 「Login Contact World Wide
        #       ★ ★ ★ Corporate Brands…」를 냈다).  ★ **내 도구가 거짓을 냈다**
        #   ★★ 눌러서 ★ 주소가 바뀌면 ★ **되돌아온다** — ★ 다른 쪽 값을 쓰지 않는다
        text = pg.inner_text("body")
        if not _hits(text):
            here = pg.url
            for word in ("제원", "사양", "스펙", "Specifications"):
                try:
                    el = pg.get_by_text(word, exact=False).first
                    if not el.is_visible(timeout=1500):
                        continue
                    el.click(timeout=2500)
                    pg.wait_for_timeout(1200)
                    if pg.url != here:          # ★ 딴 쪽으로 갔다.  되돌린다
                        pg.go_back(timeout=20000)
                        pg.wait_for_timeout(800)
                        continue
                    if _hits(pg.inner_text("body")):
                        break
                except Exception as e:  # noqa: BLE001 ★ 그 단추가 없는 쪽이 흔하다
                    _ = e   # ★ 다음 낱말로 넘어간다 — ★ 이것은 실패가 아니다
        text = pg.inner_text("body")
        b.close()
    gens = _gens(text)
    if gens:
        print(f"  ○ {url}  세대 — " + " · ".join(gens))
    hits = _hits(text)
    if not hits:
        # ★ 「못 찾았다」만 내면 ★ 쪽이 안 열린 것인지 ★ 제원이 없는 것인지 모른다.
        #   ★ 실측 09-02 — ★ 위키가 2,289자짜리 껍데기를 준 적이 있다
        head = " ".join(text.split())[:160]
        print(f"  ✗ {url}\n     못 찾았다 (글자 {len(text)}자) — {head}")
        return
    seen: dict[str, str] = {}
    for n, ctx in hits:
        seen.setdefault(n, ctx)
    print(f"  ● {url}")
    # ★ 쪽에 나온 **차례대로** 낸다 — ★ 위키는 옛 세대부터 적으므로
    #   ★ 위의 세대 머리말과 ★ 짝을 맞춰 볼 수 있다.  ★ 크기순으로 내면 못 맞춘다
    for n, ctx in list(seen.items())[:12]:
        print(f"     {n}mm   … {ctx[:100]}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    for u in sys.argv[1:]:
        fetch(u)
