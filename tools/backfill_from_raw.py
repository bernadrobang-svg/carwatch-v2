# -*- coding: utf-8 -*-
"""★★★★★ 08-30 (명령서 r974 · 0j 4) — ★ Ⓐ 「이미 오는 것을 읽는다」.

★★★ ★ 사이트를 ★ **한 번도 안 두드린다.**  ★ 저장해 둔 원문을 ★ 다시 읽을 뿐이다.
  ★ ★ 파서가 늘어났으므로 ★ 옛 원문에서 ★ 이제야 나오는 칸이 있다 —
  ★ ★ 그것이 ★ 헤이딜러 183점이다 (사고·자차·소유자·용도·특수·보증)

돌리는 법
    python3.11 tools/backfill_from_raw.py heydealer          ★ 잰다 (안 고친다)
    python3.11 tools/backfill_from_raw.py heydealer --write  ★ 넣는다
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from errors import ValidationError  # noqa: E402
from store.raw import raw_body  # noqa: E402


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def latest_details(conn, site: str) -> list:
    """매물마다 ★ 마지막 상세 원문 한 통.  ★ 없는 것은 안 낸다."""
    return list(conn.execute(
        "SELECT listing_id, source_id, body FROM ("
        " SELECT listing_id, source_id, body,"
        "        ROW_NUMBER() OVER (PARTITION BY listing_id"
        "                           ORDER BY fetched_at DESC, id DESC) n"
        "   FROM raw_response"
        "  WHERE site=? AND endpoint='detail' AND listing_id IS NOT NULL"
        ") WHERE n=1", (site,)))


def heydealer(conn, write: bool) -> Counter:
    from parse.heydealer.mapping import (
        UNKNOWN_CODES, panels_of, part_enums, record_of, warranty_of,
    )
    from store.core import upsert_child
    from store.dictionary import upsert_enum

    at = _now()
    got: Counter = Counter()
    for lid, _sid, blob in latest_details(conn, "heydealer"):
        try:
            body = json.loads(raw_body(blob))
        except (ValueError, TypeError):
            got["못 읽음"] += 1
            continue
        if not isinstance(body, dict) or not body.get("detail_info"):
            got["알맹이 없음"] += 1
            continue
        rec = record_of(body, "heydealer")
        war = warranty_of(body)
        parts = part_enums(body)
        if rec:
            got["이력"] += 1
            for k in ("accident_my_cnt", "accident_my_cost", "owner_change_cnt",
                      "use_gov", "use_business", "total_loss_cnt"):
                if rec.get(k) is not None:
                    got[f"  {k}"] += 1
            if rec.get("use_cd"):
                got["  ★ 렌트 (용도 축 안 엶)"] += 1
        if war:
            got["보증"] += 1
        got["부위"] += len(parts)
        # ★★★ 08-30 (r990 1-3) — ★ 골격·외판 (`f-table` 3a·3b 표가 왔다)
        pan = panels_of(body)
        if pan is None:
            got["★ 부위 칸이 없다"] += 1
        elif pan:
            got["★ 판이 있다"] += 1
            got["  판 수"] += len(pan)
        else:
            got["★ 무사고 (확인)"] += 1
        if not write:
            continue
        if rec:
            rec["listing_id"] = lid
            rec["collected_at"] = at
            upsert_child(conn, "core_record", rec, "p1", at)
        if pan is not None:
            # ★ 빈 배열도 넣는다 — ★ 「무사고로 확인했다」는 ★ 사실이다 (3a)
            upsert_child(conn, "core_inspection", {
                "listing_id": lid, "site": "heydealer", "row_status": "ok",
                "inspection_panel_json": json.dumps(pan, ensure_ascii=False),
                "collected_at": at}, "p1", at)
        if war:
            keys = list(war)
            conn.execute(
                "UPDATE core_listing SET "
                + ", ".join(f"{k}=?" for k in keys)
                + " WHERE listing_id=?", [war[k] for k in keys] + [lid])
        for one in parts:
            # ★★★ 08-30 — ★ `part` 축은 ★ **정책 표(STEP 41)에 행이 없다.**
            #   ★ 실측 — `ValidationError: 축 정책 미정의: part`.
            #   ★★ 규격 `HEYDEALER_API.md` 3a ② 는 ★ 「`dict_enum(axis='part')` 에
            #     ★ 넣으라」 하는데 ★ STEP 41 표에 ★ `part` 가 없다 — ★ 규격끼리 어긋난다.
            #   ★★ 내가 표에 행을 더하지 않는다 (규칙 2) — ★ 마스터께 올린다.
            #   ★ ★ 그때까지 ★ 값은 ★ 원문에 그대로 남아 있다 (P3) — ★ 잃지 않는다
            try:
                upsert_enum(conn, "heydealer", "part", one["part"],
                            one["part"], 1, "detail", "d1", at,
                            force_pending=True)
            except ValidationError:
                got["  ★ part 축 정책이 없다 (STEP 41)"] += 1
                break
    if UNKNOWN_CODES:
        got[f"★ 표에 없는 코드 {UNKNOWN_CODES[:3]}"] += len(UNKNOWN_CODES)
    if write:
        conn.commit()
    return got


def kbchachacha(conn, write: bool) -> Counter:
    """★★ KB 부위별 (밀린일 4일째) — ★ 상세에서 ★ 성능점검부 주소를 뽑아 ★ 받는다.

    ★ 저장한 상세 원문은 ★ 다시 쓴다 (통신 없음).
      ★ ★ 성능점검부는 ★ **딴 집(autocafe·carmodoo…)** 이라 ★ 한 번은 두드려야 한다 —
      ★ ★ 받은 것은 ★ 원문으로 남긴다 (P3)
    """
    import time
    import urllib.error
    import urllib.request

    from parse.kbchachacha.inspection import panels, report_url
    from store.core import upsert_child
    from store.raw import save_site_raw

    at = _now()
    got: Counter = Counter()
    todo = []
    for lid, sid, blob in latest_details(conn, "kbchachacha"):
        html = raw_body(blob)
        if isinstance(html, bytes):
            html = html.decode("utf-8", "replace")
        url = report_url(html or "")
        if not url:
            got["성능점검 주소가 없다"] += 1
            continue
        todo.append((lid, sid, url))
    got["성능점검 주소가 있다"] = len(todo)
    for lid, sid, url in todo:
        try:
            body = urllib.request.urlopen(urllib.request.Request(
                url, headers={"User-Agent": UA}), timeout=30).read()
        except (urllib.error.URLError, OSError, TimeoutError) as e:
            got[f"못 받음 ({type(e).__name__})"] += 1
            continue
        text = None
        for enc in ("utf-8", "euc-kr", "cp949"):
            try:
                text = body.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        if text is None:
            got["글자를 못 푼다"] += 1
            continue
        pan = panels(text)
        if pan is None:
            # ★ 우리가 아는 꼴이 아니다 — ★ 「이상 없음」으로 치지 않는다 (금지 12)
            got[f"★ 모르는 꼴 ({url.split('/')[2]})"] += 1
            if write:
                save_site_raw(conn, "kbchachacha", "inspection", sid, url,
                              body, at, listing_id=lid)
            continue
        got["★ 읽었다"] += 1
        got["  판이 있다" if pan else "  이상 없음(확인)"] += 1
        got["  판 수"] += len(pan)
        if not write:
            continue
        save_site_raw(conn, "kbchachacha", "inspection", sid, url, body, at,
                      listing_id=lid)
        upsert_child(conn, "core_inspection", {
            "listing_id": lid, "site": "kbchachacha", "row_status": "ok",
            "inspection_panel_json": json.dumps(pan, ensure_ascii=False),
            "collected_at": at}, "p1", at)
        conn.commit()
        time.sleep(0.4)
    if write:
        conn.commit()
    return got


UA = ("Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 "
      "Chrome/120 Mobile Safari/537.36")

def hyundai_cert(conn, write: bool) -> Counter:
    """★★ 08-30 (r990 1-2) — ★ 보증 「두 번 빼기」를 ★ 저장된 원문으로 다시 넣는다.

    ★ 통신 없음.  ★ 셈만 바뀌었다 — ★ 남은 달 → 총량
    """
    from parse.hyundai_cert.mapping import parse_detail_all

    got: Counter = Counter()
    for lid, sid, blob in latest_details(conn, "hyundai_cert"):
        html = raw_body(blob)
        if isinstance(html, bytes):
            html = html.decode("utf-8", "replace")
        try:
            pair = parse_detail_all(html, "hyundai_cert", sid)
        except (ValueError, TypeError, AttributeError):
            got["못 읽음"] += 1
            continue
        deep = pair[0] if isinstance(pair, tuple) else pair
        if not deep:
            got["알맹이 없음"] += 1
            continue
        keys = [k for k in ("warranty_body_month", "warranty_power_month")
                if deep.get(k) is not None]
        if not keys:
            got["보증 글이 없다"] += 1
            continue
        got["★ 보증을 다시 넣었다"] += 1
        got["  총량 (달)"] += sum(int(deep[k]) for k in keys) // len(keys)
        if write:
            conn.execute(
                "UPDATE core_listing SET "
                + ", ".join(f"{k}=?" for k in keys)
                + " WHERE listing_id=?", [deep[k] for k in keys] + [lid])
    if write:
        conn.commit()
    return got


def reborncar(conn, write: bool) -> Counter:
    """★★ 08-30 (r990 1-4) — ★ 리본카 골격·외판.  ★ 통신 없음.

    ★ 가르는 규칙은 ★ **사이트 제 스크립트**가 적어 준다 (`parse/reborncar/mapping.py`)
    """
    from parse.reborncar.mapping import RB_UNKNOWN, panels_of
    from store.core import upsert_child

    at = _now()
    got: Counter = Counter()
    for lid, _sid, blob in latest_details(conn, "reborncar"):
        html = raw_body(blob)
        if isinstance(html, bytes):
            html = html.decode("utf-8", "replace")
        pan = panels_of(html or "")
        if pan is None:
            got["진단표가 없다"] += 1
            continue
        got["★ 판이 있다" if pan else "★ 손댄 자리 없음 (확인)"] += 1
        got["  판 수"] += len(pan)
        if not write:
            continue
        upsert_child(conn, "core_inspection", {
            "listing_id": lid, "site": "reborncar", "row_status": "ok",
            "inspection_panel_json": json.dumps(pan, ensure_ascii=False),
            "collected_at": at}, "p1", at)
    if RB_UNKNOWN:
        got[f"★ 사이트도 안 세는 부호 {sorted(set(RB_UNKNOWN))[:3]}"] += len(RB_UNKNOWN)
    if write:
        conn.commit()
    return got


SITES = {"heydealer": heydealer, "kbchachacha": kbchachacha,
         "hyundai_cert": hyundai_cert, "reborncar": reborncar}


def main() -> int:
    args = sys.argv[1:]
    site = next((a for a in args if not a.startswith("-")), None)
    if site not in SITES:
        print("쓰는 법 — python3.11 tools/backfill_from_raw.py "
              f"<{' | '.join(SITES)}> [--write]")
        return 2
    write = "--write" in args
    conn = sqlite3.connect(os.path.join(ROOT, "carwatch.db"), timeout=60)
    conn.execute("PRAGMA busy_timeout = 60000")
    print(f"★ {site} — 저장된 상세 원문을 다시 읽는다 "
          f"({'넣는다' if write else '★ 재기만 한다'})")
    got = SITES[site](conn, write)
    for k, v in got.items():
        print(f"   {k:<28} {v:>6,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
