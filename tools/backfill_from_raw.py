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
        # ★★★★★ 08-31 (차례 4) — ★ **쉬면서 두드린다.**
        #   ★ 앞서는 ★ 성공했을 때만 잤다 — ★ 실패하면 ★ 쉬지 않고 다음을 쳤다.
        #   ★ ★ 그래서 ★ 같은 집을 ★ 251번 몰아쳤고 ★ 못 받음이 ★ 53 → **92** 로 늘었다
        #     (실측 08-31 — ★ 두 번째 바퀴가 더 많이 실패했다.  ★ 우리가 막힌 것이다)
        #   ★ ★ 한 번 더 두드려 본다 — ★ 그래도 안 되면 ★ **넘어간다** (지어내지 않는다)
        body = None
        for tryn in range(2):
            try:
                body = urllib.request.urlopen(urllib.request.Request(
                    url, headers={"User-Agent": UA}), timeout=30).read()
                break
            except (urllib.error.URLError, OSError, TimeoutError) as e:
                last = type(e).__name__
                time.sleep(1.5 * (tryn + 1))
        if body is None:
            got[f"못 받음 ({last})"] += 1
            time.sleep(0.6)
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
        time.sleep(0.6)
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
        if keys:
            got["★ 보증을 다시 넣었다"] += 1
            got["  총량 (달)"] += sum(int(deep[k]) for k in keys) // len(keys)
            if write:
                conn.execute(
                    "UPDATE core_listing SET "
                    + ", ".join(f"{k}=?" for k in keys)
                    + " WHERE listing_id=?", [deep[k] for k in keys] + [lid])
        else:
            got["보증 글이 없다"] += 1
        # ★★★★★ 08-31 (로드맵 차례 3 · `V2-01`) — ★ **`detail_status` 를 적는다.**
        #   ★ 실측 — ★ 「마지막 원문이 `ok` 인데 ★ CORE 는 `detail_status` 가 NULL」인
        #     ★ ★ 현대인증 매물이 ★ **210건** 있었다.  ★ 원문은 받아 두고 ★ 펼친 자국을 안 남겼다.
        #   ★ ★ 여기서 ★ **파싱이 실제로 줄을 냈을 때만** 적는다 — ★ 「받았다」가 아니라
        #     ★ ★ 「펼쳤다」가 근거다 (선언과 실제의 괴리를 막는 것이 이 프로젝트의 목표다)
        got["★ 펼쳤다 (detail_status=ok)"] += 1
        if write:
            conn.execute(
                "UPDATE core_listing SET detail_status='ok'"
                " WHERE listing_id=? AND (detail_status IS NULL"
                "   OR detail_status IN ('error','not_requested'))", (lid,))
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


def out_of_scope(conn, write: bool) -> Counter:
    """★★★★★ 08-30 (마스터 확정 r990 ④) — ★ `out_of_scope` 의 ★ **판정만 지운다.**

    ★★ `core_listing` 행은 ★ **안 지운다** (금지).  ★ 원문도 ★ 안 지운다 (P3).
    ★ 지우는 것은 ★ `result_axis` · `result_score` 뿐이다 — ★ 다시 만들 수 있는 것이다.
    ★★ 까닭 — ★ 재판정은 우리 차종만 다시 매긴다.  ★ 화면 밖 매물의 판정은
      ★ ★ **낡은 채로 남아** ★ 배점이 바뀌어도 옛 값이 그대로다.
      ★ ★ 실측 08-31 — ★ `V3-86` 이 잡았다 — ★ `value.market` 이 ★ 배점 0 인데
      ★ ★ ★ 값 30 인 행이 남아 있었다 (마스터께서 그 축을 끄셨는데도)
    """
    got: Counter = Counter()
    ids = [r[0] for r in conn.execute(
        "SELECT listing_id FROM core_listing WHERE status='out_of_scope'")]
    got["화면 밖 매물"] = len(ids)
    if not ids:
        return got
    marks = ",".join("?" * len(ids))
    for table in ("result_axis", "result_score"):
        got[f"{table} 지울 행"] = conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE listing_id IN ({marks})",
            ids).fetchone()[0]
    if write:
        for table in ("result_axis", "result_score"):
            conn.execute(
                f"DELETE FROM {table} WHERE listing_id IN ({marks})", ids)
        conn.commit()
        got["★ 지웠다"] = 1
        # ★ 행은 그대로인지 ★ 곧바로 대본다 (선언과 실제의 괴리를 막는다)
        got["core_listing 행 (그대로여야 한다)"] = conn.execute(
            "SELECT COUNT(*) FROM core_listing WHERE status='out_of_scope'"
        ).fetchone()[0]
        got["원문 봉투 (그대로여야 한다)"] = conn.execute(
            "SELECT COUNT(*) FROM raw_response").fetchone()[0]
    return got


def bmw_bps(conn, write: bool) -> Counter:
    """★★ 08-31 (r1007 · 1-8) — ★ BMW.  ★ 통신 없음.

    ★ 칸 이름이 틀려 ★ 압류·저당·차량번호가 ★ 통째로 버려지고 있었다
    """
    from parse.bmw_bps.mapping import parse_detail, record_of
    from store.core import split_pii, upsert_child, upsert_core
    from store.pii import load_key

    at = _now()
    key = load_key()
    got: Counter = Counter()
    for lid, sid, blob in latest_details(conn, "bmw_bps"):
        html = raw_body(blob)
        if isinstance(html, bytes):
            html = html.decode("utf-8", "replace")
        deep = parse_detail(html or "", sid)
        rec = record_of(html or "", "bmw_bps")
        for k in ("seizing_cnt", "pledge_cnt", "_pii_plate_no",
                  "site_home_verify"):
            if deep.get(k) is not None:
                got[f"  {k}"] += 1
        got["★ 상세를 다시 읽었다"] += 1
        if rec:
            got["★ 이력"] += 1
        if not write:
            continue
        deep["listing_id"] = lid
        upsert_core(conn, split_pii(conn, deep, "bmw_bps", key, at), at)
        if rec:
            rec["listing_id"] = lid
            rec["collected_at"] = at
            upsert_child(conn, "core_record", rec, "p1", at)
    if write:
        conn.commit()
    return got


def kcar(conn, write: bool) -> Counter:
    """★★ 08-31 (r1007 · 1-9) — ★ K카 이력 (`f-table` 3c 용도 코드)."""
    from parse.kcar.mapping import record_of
    from store.core import upsert_child

    at = _now()
    got: Counter = Counter()
    for lid, _sid, blob in latest_details(conn, "kcar"):
        try:
            body = json.loads(raw_body(blob))
        except (ValueError, TypeError):
            got["못 읽음"] += 1
            continue
        rec = record_of(body, "kcar")
        if not rec:
            got["이력이 없다"] += 1
            continue
        got["★ 이력"] += 1
        for k in ("use_gov", "not_join_json", "plate_change_cnt",
                  "owner_change_cnt", "use_cd"):
            if rec.get(k) is not None:
                got[f"  {k}"] += 1
        if write:
            rec["listing_id"] = lid
            rec["collected_at"] = at
            upsert_child(conn, "core_record", rec, "p1", at)
    if write:
        conn.commit()
    return got


def _record_site(conn, write, site, fn, keys):
    """★ 상세 원문 → `core_record` 를 ★ 사이트마다 같은 꼴로 넣는다 (r1007 차례 1)."""
    from store.core import upsert_child

    at = _now()
    got: Counter = Counter()
    for lid, _sid, blob in latest_details(conn, site):
        html = raw_body(blob)
        if isinstance(html, bytes):
            html = html.decode("utf-8", "replace")
        rec = fn(html or "", site)
        if not rec:
            got["★ 근거를 못 찾았다 (NULL 로 둔다)"] += 1
            continue
        got["★ 이력"] += 1
        for k in keys:
            if rec.get(k) is not None:
                got[f"  {k}"] += 1
        if write:
            rec["listing_id"] = lid
            rec["collected_at"] = at
            upsert_child(conn, "core_record", rec, "p1", at)
    if write:
        conn.commit()
    return got


def kb_record(conn, write: bool) -> Counter:
    """★ 08-31 (r1007 1-5) — ★ KB 보험사고정보 덩이."""
    from parse.kbchachacha.record import record_of

    return _record_site(conn, write, "kbchachacha", record_of,
                        ("accident_my_cnt", "total_loss_cnt",
                         "flood_total_cnt", "owner_change_cnt",
                         "use_gov", "use_cd"))


def volvo(conn, write: bool) -> Counter:
    """★ 08-31 (r1007 1-6) — ★ 볼보 딜러 글의 ★ **라벨만**."""
    from parse.volvo_selekt.mapping import record_of

    return _record_site(conn, write, "volvo_selekt", record_of,
                        ("accident_my_cnt", "flood_total_cnt",
                         "use_gov", "use_cd"))


def volvo_detail(conn, write: bool) -> Counter:
    """★★ 08-31 (차례 3 · `V2-01`) — ★ 볼보 상세를 ★ 다시 펼친다.

    ★ 실측 — ★ 마지막 원문이 `ok` 인데 ★ `detail_status` 가 `not_requested` 인 것이 149건.
      ★ ★ 원문은 있는데 ★ **CORE 에 안 펼쳐져 있었다**
    """
    from parse.volvo_selekt.mapping import parse_detail
    from store.core import upsert_core

    at = _now()
    got: Counter = Counter()
    for lid, sid, blob in latest_details(conn, "volvo_selekt"):
        html = raw_body(blob)
        if isinstance(html, bytes):
            html = html.decode("utf-8", "replace")
        deep = parse_detail(html or "", "volvo_selekt", sid)
        if not deep:
            got["★ 못 펼쳤다 (칸이 안 나온다)"] += 1
            continue
        got["★ 펼쳤다 (detail_status=ok)"] += 1
        if write:
            deep["listing_id"] = lid
            upsert_core(conn, deep, at)
    if write:
        conn.commit()
    return got


def lexus_detail(conn, write: bool) -> Counter:
    """★★★★★ 09-01 (차례 3 · `V2-01`) — ★ 렉서스 상세를 ★ 다시 펼친다.

    ★ 실측 09-01 — ★ 마지막 원문이 `ok` 인데 ★ `detail_status` 가
      ★ `not_requested` 인 것이 ★ **49건**.  ★ 원문은 있는데 ★ 안 펼쳐져 있었다.
    ★★ 사이트를 ★ **한 번도 안 두드린다** — ★ 저장해 둔 원문만 읽는다
    """
    from parse.lexus_certified.mapping import parse_detail
    from store.core import upsert_core

    at = _now()
    got: Counter = Counter()
    for lid, sid, blob in latest_details(conn, "lexus_certified"):
        body = raw_body(blob)
        deep = parse_detail(body, "lexus_certified", sid)
        if not deep:
            # ★ 「없는 차」도 200 을 준다 — ★ 200 으로 가르지 않는다 (규격 08-29)
            got["★ 못 펼쳤다 (car_detail 이 없다)"] += 1
            continue
        got["★ 펼쳤다 (detail_status=ok)"] += 1
        if write:
            deep["listing_id"] = lid
            deep["detail_status"] = "ok"
            upsert_core(conn, deep, at)
    if write:
        conn.commit()
    return got


def kb_detail(conn, write: bool) -> Counter:
    """★★★★★ 09-02 (로드맵 차례 1-5 · KB **169점**) — ★ KB 상세를 다시 펼친다.

    ★ 실측 09-02 — ★ `options_standard_json` 이 ★ **578건 전건 NULL** 이었다.
      ★ ★ 원문에는 ★ 「주요옵션」 표가 ★ 그대로 있다 —
      ★ ★ ★ `<li class="optionN">` · ★ `disable` 이면 「없음」.
      ★ ★ ★ ★ 사이트가 안 준 것이 아니라 ★ **우리가 안 읽었다**.
    ★ 그 탓에 ★ `taste.option` 43 · `taste.sunroof` 12 · `taste.hud` 18 이
      ★ ★ 332건 ★ 전건 0점이었다 (합 **73점**)
    ★★ 사이트를 ★ **한 번도 안 두드린다** — ★ 저장해 둔 원문만 읽는다
    """
    from parse.kbchachacha.mapping import parse_detail
    from store.core import upsert_core

    at = _now()
    got: Counter = Counter()
    for lid, sid, blob in latest_details(conn, "kbchachacha"):
        html = raw_body(blob)
        if isinstance(html, bytes):
            html = html.decode("utf-8", "replace")
        deep = parse_detail(html or "", "kbchachacha", sid)
        if not deep:
            got["★ 못 펼쳤다"] += 1
            continue
        if deep.get("options_standard_json"):
            got["★ 옵션을 읽었다"] += 1
        else:
            got["옵션이 없다"] += 1
        got["펼쳤다"] += 1
        if write:
            deep["listing_id"] = lid
            deep["detail_status"] = "ok"
            # ★ DDL 에 없는 칸은 ★ 안 보낸다 — ★ 규격에 없는 칸을 만들지 않는다.
            #   ★ 「없는 옵션」은 ★ 회차 기록에 적고 ★ 가이드께 여쭙는다
            deep.pop("options_absent_json", None)
            upsert_core(conn, deep, at)
    if write:
        conn.commit()
    return got


SITES = {"kb_detail": kb_detail, "volvo_detail": volvo_detail,
         "lexus_detail": lexus_detail,
         "heydealer": heydealer, "kbchachacha": kbchachacha,
         "hyundai_cert": hyundai_cert, "reborncar": reborncar,
         "bmw_bps": bmw_bps, "kcar": kcar, "kb_record": kb_record,
         "volvo": volvo, "out_of_scope": out_of_scope}


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
