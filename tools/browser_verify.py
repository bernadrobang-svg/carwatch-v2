"""★★★★★ 09-02 — ★ **배포를 브라우저로 확인한다** (`S46-253`).

★★★ 가이드 지적 09-02 — 「★ 1-1·1-2·1-4·1-8 을 ★ **안 닫혔다**로 되돌린다.
  ★ ★ **무엇으로 쟀는가**를 적어라 — ★ DB 가 아니라 ★ **브라우저**다」

★ 내가 쟀던 것 (그대로 적는다) —
    1-1  `curl | grep`                     ★ 브라우저가 아니다
    1-2  **로컬** `outputs/render/*.html`   ★ 배포도 아니다
    1-4  `curl | grep`                     ★ 브라우저가 아니다
    1-8  파이썬으로 처리기 직접 호출        ★ 배포도 브라우저도 아니다
★★ `curl` 은 ★ **글자**를 본다.  ★ 브라우저는 ★ **보이는 것**을 본다 —
  ★ ★ CSS 가 감추면 ★ `curl` 에는 있고 ★ 사람 눈에는 없다.
  ★ ★ ★ 「끝」은 ★ 배포에서 확인한 것만이다 (지키는 법 ②)

쓰기   python3.11 tools/browser_verify.py            ★ 다 잰다
      python3.11 tools/browser_verify.py --json     ★ 검사가 읽을 꼴로
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIZES = (360, 900, 1200)


def _base() -> str:
    with open(os.path.join(ROOT, "config", "deploy.json"), encoding="utf-8") as f:
        return str(json.load(f)["base_url"]).rstrip("/")


# ★ 「보이는가」를 재는 자바스크립트.  ★ `offsetParent` 가 `None` 이면 안 보인다.
#   ★ `display:none`·`visibility:hidden`·크기 0 을 다 거른다 — ★ `curl` 은 못 가른다
_SEEN = """(sel) => {
  const out = [];
  document.querySelectorAll(sel).forEach(e => {
    const r = e.getBoundingClientRect();
    const cs = getComputedStyle(e);
    if (r.width < 1 || r.height < 1) return;
    if (cs.display === 'none' || cs.visibility === 'hidden'
        || parseFloat(cs.opacity || '1') < 0.05) return;
    out.push({t: (e.innerText || '').trim().slice(0, 40),
              w: Math.round(r.width), h: Math.round(r.height)});
  });
  return out;
}"""


def _open(b, url: str, width: int = 900):
    pg = b.new_page(viewport={"width": width, "height": 1000})
    pg.goto(url, wait_until="load", timeout=60000)
    pg.wait_for_timeout(900)
    return pg


def check_1_1(b, base: str) -> dict:
    """1-1 ★ 짝지어진 차를 ★ **찾을 수 있는가** (`CROSS_SITE_COMPARE` 3b-2).

    ★★ 「배지가 1쪽에 보이는가」를 ★ **안 본다** — ★ 규격이
      ★ ★ 「★ 짝이 있다고 ★ 위로 올리지 마라」고 ★ **금지**한다.
      ★ ★ ★ 배지 대상은 ★ 평균 38점 낮아 ★ 1쪽에 올 수가 없다.
    ★ 규격이 시키는 셋을 본다 — ① 머리에 수 ② 배지는 그대로 ③ 거르개
    """
    import re as _re

    got = {}
    for q in ("", "?paired=1", "?order=price"):
        pg = _open(b, f"{base}/listings{q}")
        seen = pg.evaluate(_SEEN, ".nsite")
        cards = len(pg.evaluate(_SEEN, ".cardbody"))
        body = " ".join(pg.inner_text("body").split())
        m = _re.search(r"짝지어진 차 ([0-9,]+)대", body)
        pg.close()
        got[q or "(기본)"] = {"배지": len(seen), "카드": cards,
                              "머리수": m.group(1) if m else "",
                              "보기": [x["t"] for x in seen[:2]]}
    return got


def check_1_2(b, base: str) -> dict:
    """1-2 ★ 사진이 ★ **폭 따라 커지는가** — ★ 배포에서 잰다."""
    got = {}
    for page in ("listings", "recommend", "track"):
        per = {}
        for w in SIZES:
            pg = _open(b, f"{base}/{page}", w)
            box = pg.evaluate(_SEEN, ".thumb, .pickthumb, .kthumbwrap .thumb")
            per[w] = f"{box[0]['w']}x{box[0]['h']}" if box else "없다"
            pg.close()
        got[page] = per
    return got


def check_1_4(b, base: str) -> dict:
    """1-4 ★ 빈 자리의 ★ **까닭이 눈에 보이는가**."""
    got = {}
    for site in ("bobaedream", "heydealer", "encar"):
        pg = _open(b, f"{base}/listings?site={site}")
        why = pg.evaluate(_SEEN, ".photo-why, .lst-why-empty, .rc-why-empty")
        cards = len(pg.evaluate(_SEEN, ".cardbody"))
        pg.close()
        got[site] = {"까닭": len(why), "카드": cards,
                     "글": (why[0]["t"] if why else "")}
    return got


CHECKS = {"1-1": check_1_1, "1-2": check_1_2, "1-4": check_1_4}


def run(only: str | None = None) -> dict:
    from playwright.sync_api import sync_playwright

    base = _base()
    out: dict = {"_주소": base}
    with sync_playwright() as p:
        b = p.chromium.launch()
        try:
            for key, fn in CHECKS.items():
                if only and key != only:
                    continue
                try:
                    out[key] = fn(b, base)
                except Exception as exc:  # noqa: BLE001 ★ 한 줄이 죽어도 나머지는 잰다
                    out[key] = {"_못 쟀다": f"{type(exc).__name__}: {exc}"[:120]}
        finally:
            b.close()
    return out


if __name__ == "__main__":
    got = run(sys.argv[2] if len(sys.argv) > 2 else None)
    if "--json" in sys.argv:
        print(json.dumps(got, ensure_ascii=False, indent=2))
    else:
        print(f"★ 배포 {got['_주소']} 를 ★ 브라우저로 열어 쟀다")
        for k, v in got.items():
            if k.startswith("_"):
                continue
            print(f"  {k}  {json.dumps(v, ensure_ascii=False)}")
