"""사이트 × 칸 채움율을 재고, 구멍이 있으면 붉게 낸다 (09-08 마스터 지시).

마스터 — 「이제 자동화를 하자. 클로드가 없더라도 알아서 수행하는 것으로.
  모든 소스의 최적화가 이루어지고 자동 처리가 되어야 돼.
  아직도 안 도는 파서는 없어야 하고, 아직도 반영 안 된 페이지는 없어야 돼」

이 자는 사람이 눈으로 보지 않아도 구멍을 잡는다.
  ① 사이트마다 칸이 몇 % 찼는지 잰다
  ② 한 칸이 0% 면 그 파서는 그 칸을 못 읽는 것이다 — 붉다
  ③ 지난번보다 줄었으면 붉다 (되돌아간 것이다)

돌리기  python3 -c "from tools.fill_gate import run; run('배포주소')"
"""
import json
import os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs", "fill_gate.json")
DOC = os.path.join(ROOT, "outputs", "FILL_GATE.md")

# 사이트마다 반드시 차야 하는 칸. 0% 면 그 파서가 그 칸을 못 읽는 것이다.
COLS = ("상세", "원문", "값", "주행", "연식", "색", "사진", "트림", "옵션")


def run(base_url: str) -> dict:
    from tools.browser_diff import all_sites_report

    all_sites_report(base_url)
    with open(os.path.join(ROOT, "outputs", "all_sites.json"), encoding="utf-8") as f:
        cur = json.load(f)

    sites = sorted({k.split(".")[0] for k in cur if "." in k})
    rows, holes, dropped = [], [], []

    old_n = {}
    if os.path.exists(OUT):
        try:
            with open(OUT, encoding="utf-8") as f:
                _was = json.load(f) or {}
            old_n = _was.get("건수") or {}
        except Exception:  # noqa: BLE001
            old_n = {}

    rate, count = {}, {}
    for s in sites:
        total = cur.get(f"{s}.매물") or 0
        if not total:
            continue
        row = {"사이트": s, "매물": total}
        for c in COLS:
            n = cur.get(f"{s}.{c}")
            if n is None:
                continue
            pct = round(n / total * 100, 1)
            row[c] = pct
            rate[f"{s}.{c}"] = pct
            count[f"{s}.{c}"] = n
            if n == 0:
                holes.append(f"{s}.{c}")
            # ★★★★★★ 09-09 (r1208 N-4) — ★ **건수로 견준다.  비율로 안 본다.**
            #   ★ 가이드 개정 1061 — 「★ 건수가 달라도 검사를 실패시키지 마라 —
            #     ★ ★ **매물은 날마다 는다**」.
            #   ★ 실측 09-09 — ★ 리볼트 상세가 ★ **57건 그대로**인데
            #     ★ ★ 매물이 74 → 90 이 되어 ★ 77% → 63% 로 「떨어졌다」고 잡혔다.
            #     ★ ★ ★ 되돌아간 것이 아니라 ★ **분모가 큰 것**이다.
            #   ★★ 그러므로 ★ 「받아 놓은 것이 줄었나」를 ★ **건수**로 본다.
            #     ★ ★ 비율은 ★ 보이기 위한 것이지 ★ 잣대가 아니다
            was_n = old_n.get(f"{s}.{c}")
            if was_n is not None and n < was_n:
                dropped.append(f"{s}.{c} {was_n:,}건 → {n:,}건")
        rows.append(row)

    out = {
        "_잰_때": datetime.now(timezone.utc).isoformat(),
        "_잰_곳": base_url,
        "채움율": rate,
        "건수": count,
        "구멍": holes,
        "되돌아간_것": dropped,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    head = "| 사이트 | 매물 | " + " | ".join(COLS) + " |"
    sep = "|---|--:|" + "--:|" * len(COLS)
    lines = ["# 사이트 × 칸 채움율", "",
             "`python3 -c \"from tools.fill_gate import run; run('배포주소')\"` 가 만든다.",
             "", f"구멍(0%) **{len(holes)}칸** · 되돌아간 것 **{len(dropped)}칸**", "",
             head, sep]
    for r in rows:
        cells = []
        for c in COLS:
            v = r.get(c)
            cells.append("—" if v is None else ("**0**" if v == 0 else f"{v}"))
        lines.append(f"| {r['사이트']} | {r['매물']:,} | " + " | ".join(cells) + " |")
    if holes:
        lines += ["", "## 구멍 — 그 파서가 그 칸을 못 읽는다", ""]
        lines += [f"- `{h}`" for h in holes]
    if dropped:
        lines += ["", "## 되돌아간 것", ""] + [f"- {d}" for d in dropped]
    with open(DOC, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"사이트 {len(rows)} · 구멍 {len(holes)}칸 · 되돌아감 {len(dropped)}칸 → {DOC}")
    return out
