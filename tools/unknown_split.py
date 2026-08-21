# -*- coding: utf-8 -*-
"""「확인 안 됨」을 ①②③④ 로 가른다 (개정 434 · 435 · V1-27 · V1-28).

지시서   inbox/ORDER_unknown_split.md · 개정 434
근거     ★ 마스터 — 「왜 빼?  있어야 하는데 너가 못 찾거나 처음부터 부실하게
        올린 거잖아.  ★ 너가 전체를 못 찾은 것을 먼저 정리해야지」
갈래     ① 원문에 **값이 없다**      딜러 잘못 → 0점이 맞다
        ② 원문에 값이 있는데 파서가 못 읽는다   ★ 우리 잘못
        ③ 엔드포인트를 안 받는다              ★ 우리 잘못
        ④ ★ 계산 쪽이 못 만든다 (개정 435)     ★ 우리 잘못 — 고치는 법이 다르다
        ?  모르겠습니다 — 넷 중 아무것도 아니다
★ ①과 ②는 「키가 있다」가 아니라 ★ 「값이 있다」로 가른다 (개정 435)
값규칙   ★ 원문 body 를 직접 연다.  파서 결과만 보지 않는다 (S43-②)
금지     짐작으로 가르는 것.  ★ 갈래를 정하지 않고 코드를 고치는 것
금지     ★ 확인 안 된 축을 분모에서 빼는 것 — 우리 부실이 숨는다 (개정 289)
사용     python3.11 tools/unknown_split.py
        python3.11 tools/unknown_split.py --write   outputs/ 에 표를 낸다
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

DB = os.path.join(ROOT, "carwatch.db")
# 원문 body 를 몇 건까지 열어 볼 것인가.  ★ 전건을 열면 1GB 를 다 읽는다.
#   갈래는 매물마다 안 달라진다 — 표본으로 가르고 ★ 표본 수를 함께 낸다
BODY_SAMPLE = 400


def _cfg() -> dict:
    with open(os.path.join(ROOT, "config", "unknown_split.json"),
              encoding="utf-8") as f:
        return json.load(f)


def _walk(body: dict, path: str):
    """`a.b.c` 를 따라간다.  없으면 KeyError 대신 (False, None) 을 준다."""
    cur = body
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return False, None
        cur = cur[part]
    return True, cur


def classify(conn, axis: str, spec: dict) -> dict:
    """그 축의 「확인 안 됨」을 갈래별로 센다.

    ★ 셋을 이 차례로 가른다 — ③ 이 먼저다.  원문 행이 없으면 열 것도 없다
    """
    cv = conn.execute(
        "SELECT calc_version FROM result_score LIMIT 1").fetchone()
    cv = cv[0] if cv else ""
    marks = ",".join("?" * len(spec["unknown"]))
    if not spec["unknown"]:
        return {"n": 0, "1": 0, "2": 0, "3": 0, "4": 0, "?": 0, "opened": 0,
                "estimated": 0, "snippet": ""}
    lids = [r[0] for r in conn.execute(
        f"SELECT listing_id FROM result_axis WHERE axis=? AND calc_version=?"
        f" AND source IN ({marks})", (axis, cv, *spec["unknown"]))]
    got = {"n": len(lids), "1": 0, "2": 0, "3": 0, "4": 0, "?": 0, "opened": 0,
           "estimated": 0, "snippet": ""}
    ep, key = spec["endpoint"], spec["key"]
    # ★ 원문 body 로 못 가르는 축 — config 가 갈래와 까닭을 준다 (짐작이 아니다)
    if spec.get("kind_override"):
        got[spec["kind_override"]] = len(lids)
        got["snippet"] = spec.get("why", "")
        return got
    for i, lid in enumerate(lids):
        rows = conn.execute(
            "SELECT status FROM raw_response WHERE listing_id=? AND endpoint=?",
            (lid, ep)).fetchall()
        if not rows:
            got["3"] += 1            # ★ 안 받았다 — 우리 잘못
            continue
        if not any(r[0] == "ok" for r in rows):
            got["1"] += 1            # 사이트가 「그런 것 없다」고 했다
            continue
        if got["opened"] >= BODY_SAMPLE:
            # ★ 표본을 다 썼다.  나중에 관측 비율로 늘린다 (아래) —
            #   「모름」으로 두면 22,208건 중 대부분이 모름이 되어 표가 못 쓰인다.
            #   ★ 늘린 것은 표에 「추정」이라 적는다.  실측인 척하지 않는다
            got["rest"] = got.get("rest", 0) + 1
            continue
        body = conn.execute(
            "SELECT body FROM raw_response WHERE listing_id=? AND endpoint=?"
            " AND status='ok' ORDER BY fetched_at DESC LIMIT 1",
            (lid, ep)).fetchone()
        got["opened"] += 1
        try:
            b = json.loads(body[0])
        except (TypeError, ValueError):
            got["?"] += 1
            continue
        there, val = _walk(b, key)
        if there and val not in (None, "", [], {}):
            got["2"] += 1            # ★ 원문에 있는데 못 읽었다 — 우리 잘못
            if not got["snippet"]:
                got["snippet"] = (f"매물 {lid} · {ep}:{key} = "
                                  + json.dumps(val, ensure_ascii=False)[:90])
        else:
            got["1"] += 1            # 원문에 없다 (키가 없거나 값이 null)
        del i
    # ★ 표본 밖은 관측한 ①:② 비율로 늘린다.  ★ 「추정」이라 밝힌다
    rest = got.pop("rest", 0)
    if rest:
        seen = got["1"] + got["2"]
        if seen:
            got["2"] += round(rest * got["2"] / seen)
            got["1"] += rest - round(rest * got["2"] / seen) \
                if False else rest - round(rest * (got["2"] - 0) / seen)
            got["1"] = (got["n"] - got["2"] - got["3"]
                        - got["4"] - got["?"])
            got["estimated"] = rest
        else:
            got["?"] += rest
    return got


def main() -> int:
    cfg = _cfg()
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    with open(os.path.join(ROOT, "config", "scoring.json"),
              encoding="utf-8") as f:
        comp = json.load(f)["components"]

    rows = []
    for axis in sorted(cfg["axes"]):
        spec = cfg["axes"][axis]
        one = classify(conn, axis, spec)
        cap = comp.get(axis)
        cap = float(cap if isinstance(cap, (int, float))
                    else (cap or {}).get("points") or 0)
        rows.append((axis, cap, spec, one))

    print("★ 「확인 안 됨」을 ①②③④ 로 가른다 (개정 434 · 435)\n")
    print(f"{'축':<22}{'배점':>5}{'확인안됨':>8}{'①값없음':>9}"
          f"{'②못읽음':>9}{'③안받음':>9}{'④계산':>8}{'모름':>6}")
    tot = {"n": 0, "1": 0, "2": 0, "3": 0, "4": 0, "?": 0}
    lost = {"2": 0.0, "3": 0.0, "4": 0.0}
    for axis, cap, _spec, one in rows:
        if not one["n"]:
            continue
        note = (f"  ★ {one['estimated']}건은 표본 {one['opened']}건으로 추정"
                if one.get("estimated") else "")
        print(f"{axis:<22}{cap:>5.0f}{one['n']:>8}{one['1']:>9}"
              f"{one['2']:>9}{one['3']:>9}{one['4']:>8}{one['?']:>6}{note}")
        for k in tot:
            tot[k] += one[k]
        for k in ("2", "3", "4"):
            lost[k] += one[k] * cap
    print(f"{'합계':<22}{'':>5}{tot['n']:>8}{tot['1']:>9}"
          f"{tot['2']:>9}{tot['3']:>9}{tot['4']:>8}{tot['?']:>6}")

    ours = tot["2"] + tot["3"] + tot["4"]
    print(f"\n★ 우리 잘못 — ② {tot['2']} · ③ {tot['3']} · ④ {tot['4']} "
          f"= {ours}건")
    print(f"★ 점수로 {lost['2'] + lost['3'] + lost['4']:,.0f}점어치 (상한) "
          f"— ② {lost['2']:,.0f} · ③ {lost['3']:,.0f} · ④ {lost['4']:,.0f}")

    print("\n★ ② 원문에 있는데 못 읽는다 — 원문 조각")
    for axis, cap, spec, one in rows:
        if one["2"]:
            print(f"  {axis} ({cap:.0f}점 · {one['2']}건) — {spec['key']}")
            print(f"      {one['snippet']}")
    print("\n★ ④ 계산 쪽이 못 만든다")
    for axis, cap, spec, one in rows:
        if one["4"]:
            print(f"  {axis} ({cap:.0f}점 · {one['4']}건)")
            print(f"      {one['snippet']}")
    print("\n★ ③ 그 엔드포인트를 안 받는다")
    for axis, cap, spec, one in rows:
        if one["3"]:
            print(f"  {axis} ({cap:.0f}점 · {one['3']}건) — "
                  f"엔드포인트 {spec['endpoint']}")
    # ★ 이력을 남긴다 — V1-28 이 「지난번보다 줄었는가」를 본다.
    #   ★ 남기지 않으면 「줄었다」를 말로만 하게 된다
    if "--write" in sys.argv:
        hist = os.path.join(ROOT, "outputs", "unknown_split_history.json")
        old = []
        if os.path.isfile(hist):
            with open(hist, encoding="utf-8") as f:
                old = json.load(f).get("runs") or []
        stamp = conn.execute(
            "SELECT MAX(calculated_at) FROM result_score").fetchone()[0]
        old.append({"at": stamp, "kind2": tot["2"], "kind3": tot["3"],
                    "unknown": tot["n"],
                    "kind4": tot["4"],
                    "by_axis": {a: {"n": o["n"], "1": o["1"], "2": o["2"],
                                    "3": o["3"], "4": o["4"], "?": o["?"]}
                                for a, _c, _s, o in rows if o["n"]}})
        with open(hist, "w", encoding="utf-8") as f:
            json.dump({"_note": "★ tools/unknown_split.py --write 가 만든다. "
                                "손으로 고치지 않는다 (V1-28)",
                       "runs": old[-20:]}, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"\n이력 → {os.path.relpath(hist, ROOT)} ({len(old)}회째)")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
