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


def _hits(text: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for pat in PATS:
        for m in pat.finditer(text):
            n = int(m.group(1).replace(",", ""))
            if not 3000 <= n <= 5500:
                continue
            lo = max(0, m.start() - 40)
            out.append((str(n), " ".join(text[lo:m.end() + 20].split())))
    return out


def fetch(url: str) -> None:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1280, "height": 2000})
        try:
            pg.goto(url, timeout=45000, wait_until="networkidle")
        except Exception as e:  # noqa: BLE001 ★ 조용히 넘기지 않는다 — 무엇이 막혔는지 낸다
            print(f"  ✗ {url}\n     {type(e).__name__}: {str(e)[:90]}")
            b.close()
            return
        # ★ 제원표가 접혀 있는 쪽이 많다 — ★ 「제원」 단추를 눌러 본다
        for word in ("제원", "사양", "스펙", "Specifications"):
            try:
                el = pg.get_by_text(word, exact=False).first
                if el.is_visible(timeout=1500):
                    el.click(timeout=2500)
                    pg.wait_for_timeout(1200)
                    break
            except Exception as e:  # noqa: BLE001 ★ 그 단추가 없는 쪽이 흔하다
                _ = e  # ★ 다음 낱말로 넘어간다 — ★ 이것은 실패가 아니다
        text = pg.inner_text("body")
        b.close()
    hits = _hits(text)
    if not hits:
        print(f"  ✗ {url}\n     못 찾았다 (글자 {len(text)}자)")
        return
    seen: dict[str, str] = {}
    for n, ctx in hits:
        seen.setdefault(n, ctx)
    print(f"  ● {url}")
    for n, ctx in sorted(seen.items(), key=lambda x: -int(x[0]))[:4]:
        print(f"     {n}mm   … {ctx[:100]}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    for u in sys.argv[1:]:
        fetch(u)
