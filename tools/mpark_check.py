# -*- coding: utf-8 -*-
"""★ 성능점검기록부를 ★ **원문 그대로** 읽는다 (P-3 ②).

★★★ 09-10 실측 — ★ 엔카 성능점검은 ★ 서버에서 407 이다.
  ★ 그런데 ★ **KB 상세가 그 기록부의 주소를 그대로 적어 둔다**:
    `<a id="btnCarCheckView1" data-link-url="https://www.m-park.co.kr/popup/performance/{번호}">`
  ★ ★ 그 쪽은 ★ **막히지 않는다.**  ★ 엔카가 막은 것을 ★ KB 쪽으로 돌아 받는다.

★★ 다만 ★ 그 쪽은 ★ **빈 양식**으로 그려진다 — ★ 글자만 읽으면
  ★ ★ 「없음있음」이 나란히 있어 ★ **어느 쪽이 체크됐는지 모른다**.
  ★ ★ ★ 체크는 ★ DOM 에 있다 (`mdi-checkbox-marked` ↔ `mdi-checkbox-blank`).
★ 그래서 ★ 브라우저로 그려 ★ **체크된 칸만** 읽는다.

★ 마스터 기준 ④ — 「단순교환까지.  ★ **골격에 안 갔으면 통과**」.
  ★ 그 답이 ★ 「13.부위별 이상여부 · 주요골격 없음/있음」에 있다.

돌리는 법
    python3.11 tools/mpark_check.py 26081410090
    python3.11 tools/mpark_check.py --all      ★ 가진 KB 상세를 다 훑는다
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

BASE = "https://www.m-park.co.kr/popup/performance/"
RE_LINK = re.compile(r'data-link-url="([^"]*?/popup/performance/(\d+))"')

# ★ 체크된 칸만 낸다.  ★ 앞뒤 글자로 ★ 어느 줄인지 가른다
JS = r"""
() => {
  const out = [];
  for (const box of document.querySelectorAll('.v-input--selection-controls')) {
    const icon = box.querySelector('.v-icon');
    if (!icon || !/checkbox-marked/.test(icon.className)) continue;
    let row = box.closest('tr,li,div');
    for (let i = 0; i < 3 && row; i++) row = row.parentElement;
    out.push({
      said: (box.textContent || '').trim().slice(0, 24),
      row: (row ? (row.textContent || '') : '').replace(/\s+/g, ' ').slice(0, 90)
    });
  }
  return out;
}"""


def link_of(html: str) -> str | None:
    """KB 상세 → 성능점검기록부 번호."""
    got = RE_LINK.search(html or "")
    return got.group(2) if got else None


def read(number: str, wait: int = 2500) -> dict:
    """기록부 한 장 → ★ 우리가 쓰는 말로."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_context(viewport={"width": 900, "height": 1600}).new_page()
        pg.goto(BASE + str(number), wait_until="networkidle")
        pg.wait_for_timeout(wait)
        text = " ".join(pg.inner_text("body").split())
        marks = pg.evaluate(JS)
        br.close()
    return judge(marks, text)


def judge(marks: list, text: str) -> dict:
    """체크된 칸 → ★ 골격·외판·용도.  ★ 못 읽으면 ★ 「미조회」다 (금지 12)."""
    got: dict = {"골격": None, "외판1랭크": None, "외판2랭크": None,
                 "사고이력": None, "단순수리": None, "부위": [], "용도": []}
    # ★ 「13.부위별 이상여부」 줄에서 ★ 나온 차례가 ★ 1랭크 · 2랭크 · 주요골격이다
    rank_row = [m for m in marks if "외판부위 1랭크" in m.get("row", "")]
    said = [m["said"] for m in rank_row]
    for key, i in (("외판1랭크", 0), ("외판2랭크", 1), ("골격", 2)):
        if len(said) > i and said[i] in ("있음", "없음"):
            got[key] = (said[i] == "있음")
    # ★ 사고이력 · 단순수리
    for m in marks:
        row = m.get("row", "")
        if "단순수리" in row and m["said"] in ("있음", "없음"):
            got.setdefault("_두줄", []).append(m["said"])
    two = got.pop("_두줄", [])
    if len(two) >= 2:
        got["사고이력"], got["단순수리"] = two[0] == "있음", two[1] == "있음"
    # ★ 교환·판금 부위 이름
    got["부위"] = [m["said"] for m in marks
                   if "교환,판금 등 이상 부위" in m.get("row", "")]
    # ★ 용도이력 (렌트·영업)
    got["용도"] = [m["said"] for m in marks
                   if m["said"] in ("렌트", "영업용", "관용")]
    got["주행"] = None
    km = re.search(r"현재 주행거리\s*:\s*\[([\d,]+)km\]", text)
    if km:
        got["주행"] = int(km.group(1).replace(",", ""))
    no = re.search(r"자동차등록번호\s*([0-9]{2,3}[가-힣][0-9]{4})", text)
    got["차번호"] = no.group(1) if no else None
    return got


def say(got: dict) -> str:
    """한 줄로.  ★ 마스터 기준 ④ 를 그 자리에서 말한다."""
    if got.get("골격") is None:
        return "골격 미조회"
    if got["골격"]:
        return "★ 골격 상함 — 마스터 기준에서 벗어난다"
    tail = f" (교환·판금 {' · '.join(got['부위'])})" if got.get("부위") else ""
    rent = " · 렌트이력" if "렌트" in (got.get("용도") or ()) else ""
    return f"골격 무사고 — 통과{tail}{rent}"


def all_kb() -> list:
    """가진 KB 상세에서 ★ 기록부 번호를 뽑는다."""
    from store.rawfile import read as raw_read

    out = []
    for path in sorted(glob.glob(os.path.join(
            ROOT, "raw", "kbchachacha", "detail", "*", "*.json"))):
        body = (raw_read(path) or {}).get("body") or b""
        if isinstance(body, bytes):
            body = body.decode("utf-8", "replace")
        num = link_of(body)
        if num:
            out.append((os.path.basename(path)[:-5], num))
    return out


if __name__ == "__main__":
    if "--all" in sys.argv:
        for sid, num in all_kb():
            print(f"{sid}  {num}", flush=True)
        raise SystemExit(0)
    want = [a for a in sys.argv[1:] if a.isdigit()]
    for one in want:
        got = read(one)
        print(json.dumps(got, ensure_ascii=False))
        print("  →", say(got))


def into_db(db: str = "carwatch.db", limit: int = 0) -> dict:
    """읽은 기록부를 ★ `core_listing` 의 사고 칸에 담는다 (M-3 과 같은 칸).

    ★ 「주요골격 있음」이면 ★ 골격 1 이상이다 — ★ 몇 곳인지는 ★ 양식이 안 준다.
      ★ ★ 그래서 ★ **1** 로 둔다.  ★ 지어내지 않는다 — ★ 0 이 아니라는 것만 안다.
    ★ 「외판 1·2랭크 있음」은 ★ 단순수리다 — ★ 부위 이름을 그대로 담는다
    """
    import sqlite3

    conn = sqlite3.connect(os.path.join(ROOT, db))
    mine = {r[0] for r in conn.execute(
        "SELECT source_id FROM core_listing WHERE site = 'kbchachacha'")}
    tally = {"읽음": 0, "담음": 0, "못 읽음": 0}
    for n, (sid, num) in enumerate(all_kb(), 1):
        if sid not in mine or (limit and n > limit):
            continue
        try:
            got = read(num)
        except Exception:                      # noqa: BLE001
            tally["못 읽음"] += 1
            continue
        tally["읽음"] += 1
        if got.get("골격") is None:
            continue
        parts = [{"part": p, "kind": "교환·판금", "frame": False}
                 for p in (got.get("부위") or ())]
        conn.execute(
            "UPDATE core_listing"
            "   SET accident_frame_cnt = ?, accident_swap_cnt = ?,"
            "       accident_weld_cnt = 0, accident_parts_json = ?,"
            "       site_inspection = COALESCE(site_inspection, 'KB 성능점검')"
            " WHERE site = 'kbchachacha' AND source_id = ?",
            (1 if got["골격"] else 0, len(parts),
             json.dumps(parts, ensure_ascii=False), sid))
        tally["담음"] += 1
    conn.commit()
    conn.close()
    return tally
