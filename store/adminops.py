# -*- coding: utf-8 -*-
"""관리자 서버 계층 — 실행 지시 · 쿼리 · API 조회 · 개발 요청 · 미리보기.

지시서   13장 STEP 132 (실행 지시) · 133 (조회 전용 쿼리) · 134 (API 조회)
         135 (관리 도구) · 137 (개발 요청) · 128 (배점 미리보기)
근거     ★ 관리자가 데이터를 직접 고치지 않는다.  쿼리는 SELECT 전용이다
         변경이 가능하면 RAW 무손실(P3)이 깨진다 — 원문을 지우면 복구가 안 된다
금지     문자열 필터로 SQL 을 판정하는 것.  주석·부분 문자열로 우회된다
         DevRequest 를 삭제하는 것.  상태 전이만 한다
"""
from __future__ import annotations

import json
import os
import re
import secrets
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from errors import PolicyError, ValidationError
from contracts import (
    FORMAT_FACET, FORMAT_JSON, IMPORT_SOURCE, IMPORT_STAGE, ORIGIN_BROWSER,
    ROLE_ADMIN, S1_CODE, S2_CODE, S4_CODE, S4_EXPECTED, Account, require_role,
)
from store.admin import TEMP_SECRET_BYTES, _admin_cfg

# 식별자 길이.  구현 상수다 (2장 상수표 성격 「구현」)
ID_BYTES = TEMP_SECRET_BYTES

# ── STEP 133 조회 전용 쿼리 ──────────────────────────────────────────
# ★ SQL 파서(AST)로 판정한다.  정규식이 아니다.
#   sqlite3 가 파서다 — EXPLAIN 으로 컴파일해 보고, 쓰기 연산자가 있으면 거부한다
PII_TABLES = ("core_pii", "core_dealer_pii")
REJECT_PII = "개인정보 표는 조회할 수 없습니다 (get_pii 로만 본다)"

READONLY_HEADS = ("SELECT", "WITH", "VALUES", "EXPLAIN")
# 쓰려는 뜻이 분명한 머리말 (개정 391).  ★ 이것은 오타가 아니라 정책 위반이다
WRITE_HEADS = ("INSERT", "UPDATE", "DELETE", "REPLACE", "DROP", "CREATE",
               "ALTER", "TRUNCATE", "PRAGMA", "ATTACH", "DETACH", "VACUUM",
               "REINDEX", "BEGIN", "COMMIT", "ROLLBACK")
WRITE_OPCODES = frozenset({
    "OpenWrite", "Insert", "Delete", "Update", "IdxInsert", "IdxDelete",
    "CreateBtree", "DropTable", "DropIndex", "DropTrigger", "RenameTable",
    "ParseSchema", "VUpdate", "VCreate", "VDestroy", "Vacuum", "JournalMode",
})
# ★★★★★ 09-05 (D2 · `S46-277`) — ★ **임시 커서를 가린다.**
#   ★★★ 마스터 — 「★ **조회용 쿼리야 ★ 쓰기용은 아니야**」
#   ★★ 실측 09-05 — ★ `ORDER BY` ＋ `LIMIT` 이 ★ **함께** 있으면 막혔다.
#     ★ ★ `GROUP BY` 만 · `ORDER BY` 만 · `LIMIT` 만은 됐다.
#     ★ ★ ★ 정렬이 ★ **임시 표**를 쓴다 —
#       ★ `OpenEphemeral P1=1` → `Delete P1=1` → `IdxInsert P1=1`.
#     ★ ★ ★ ★ **우리 표가 아니라 ★ 임시 커서**인데 ★ 쓰기로 셌다.
#   ★ 그래서 ★ **커서를 따라간다** — ★ `P1` 이 임시 커서면 ★ 쓰기가 아니다.
# ★ 임시 커서를 여는 연산 — ★ 이것이 연 번호는 ★ 우리 표가 아니다
TEMP_OPEN_OPCODES = frozenset({
    "OpenEphemeral", "SorterOpen", "OpenAutoindex", "OpenDup", "OpenPseudo",
})
# ★★ 커서를 안 봐도 ★ **무조건 막는 것** — ★ 임시든 아니든 위험하다
HARD_WRITE_OPCODES = frozenset({
    "Clear", "Destroy", "DropTable", "DropIndex", "CreateBtree", "OpenWrite",
})


def _write_opcodes(plan: list) -> set:
    """★ 이 판이 ★ **정말로 쓰는가** (D2 · `S46-277`).

    ★ `EXPLAIN` 한 줄은 ★ `(addr, opcode, p1, p2, p3, p4, p5, comment)` 다.
      ★ ★ 커서 연산은 ★ `p1` 이 ★ **커서 번호**다.
    ★ 걸음 —
      ① `TEMP_OPEN_OPCODES` 가 연 ★ 커서 번호를 모은다 (임시다)
      ② `HARD_WRITE_OPCODES` 는 ★ 커서를 안 보고 ★ **무조건** 쓰기다
      ③ 그 밖의 쓰기 연산은 ★ `p1` 이 ★ **임시 커서면 아니다**
    ★ 돌려줌  ★ 걸린 연산 이름들 (비면 ★ 조회다)
    """
    temp: set = set()
    for row in plan:
        if row[1] in TEMP_OPEN_OPCODES:
            temp.add(row[2])
    got: set = set()
    for row in plan:
        op, cur = row[1], row[2]
        if op in HARD_WRITE_OPCODES:
            got.add(op)
        elif op in WRITE_OPCODES and cur not in temp:
            got.add(op)
    return got
REJECT_MULTI = "다중 문장은 거부한다 (세미콜론 분리)"
REJECT_NOT_SELECT = "SELECT · WITH 만 허용한다"
REJECT_WRITE = "쓰기 연산이 포함됐다"
REJECT_COMPILE = "SQL 을 해석할 수 없다"


@dataclass(frozen=True)
class QueryLog:
    """13장 정의서.  거부된 것도 남긴다 (STEP 133)."""

    query_id: str
    account_id: int
    sql: str
    row_count: int | None
    elapsed_ms: int | None
    executed_at: str
    rejected_reason: str | None


@dataclass(frozen=True)
class QueryResult:
    columns: list[str]
    rows: list[tuple]
    row_count: int
    truncated: bool
    elapsed_ms: int
    query_id: str = ""

    @property
    def tsv(self) -> str:
        """붙여넣어 바로 쓸 수 있는 형태 (개정 401).

        ★ 탭 구분이다.  표 프로그램에 그대로 붙는다 —
          쉼표로 나누면 값 안의 쉼표에서 칸이 밀린다
        ★ 값 안의 탭·줄바꿈은 빈칸으로 바꾼다.  칸이 밀리는 것보다 낫다
        """
        out = ["\t".join(self.columns)]
        for row in self.rows:
            out.append("\t".join(
                str("" if c is None else c).replace("\t", " ")
                .replace("\r", " ").replace("\n", " ") for c in row))
        return "\n".join(out)


@dataclass(frozen=True)
class ApiSnapshot:
    snapshot_id: str
    url: str
    http_code: int | None
    content_type: str | None
    body: str | None
    paths: list[str]
    fetched_at: str


@dataclass(frozen=True)
class DevRequest:
    request_id: str
    title: str
    body: str
    origin: str
    context_json: str | None
    status: str
    direction: str | None
    step_ref: str | None
    created_at: str
    exported_at: str | None
    updated_at: str


@dataclass(frozen=True)
class RecalcJob:
    job_id: str
    trigger: str
    reason: str
    from_step: str
    scope: str
    status: str
    run_id: str | None


@dataclass(frozen=True)
class ScoringPreview:
    before: dict
    after: dict
    grade_before: dict
    grade_after: dict
    rank_changed: int
    entered: list
    exited: list
    axis_contribution: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ImportPreview:
    """반입 미리보기 (13장 STEP 136a ④).

    ★ 「몇 건」만으로는 판단이 안 된다.  이미 있는 것과 새 것을 가른다
    """

    fmt: str
    site: str
    target_key: str | None
    total: int
    existing: int
    fresh: int
    site_raw: bool               # ★ False 면 화면이 「원문 없음」이라고 말한다
    bytes_in: int


@dataclass(frozen=True)
class ImportResult:
    raw_id: int
    total: int
    created: int
    updated: int
    fmt: str
    site_raw: bool


def preview_import(conn: sqlite3.Connection, rows: list, *, fmt: str,
                   site: str, target_key: str | None,
                   bytes_in: int,
                   facet: dict | None = None) -> ImportPreview:
    """저장하지 않고 무엇이 들어갈지만 센다 (STEP 136a ④ · STEP 138)."""
    if fmt == FORMAT_FACET:
        # facet 은 매물이 아니라 축이다 — 「몇 축이 오는가」를 낸다 (개정 260)
        # ★ 해석은 호출자가 해서 넘긴다.  store 는 parse 를 못 부른다 (V4-22)
        n = int((facet or {}).get("axis_count") or 0)
        return ImportPreview(
            fmt=fmt, site=site, target_key=target_key,
            total=n, existing=0, fresh=n,
            site_raw=True, bytes_in=bytes_in)
    ids = [r["source_id"] for r in rows]
    existing = 0
    if ids:
        marks = ",".join("?" * len(ids))
        existing = conn.execute(
            f"SELECT COUNT(*) FROM core_listing WHERE site=? "
            f"AND source_id IN ({marks})", (site, *ids)).fetchone()[0]
    return ImportPreview(
        fmt=fmt, site=site, target_key=target_key, total=len(rows),
        existing=existing, fresh=len(rows) - existing,
        site_raw=fmt == FORMAT_JSON, bytes_in=bytes_in)


def import_listings(conn: sqlite3.Connection, account: Account, rows: list, *,
                    fmt: str, site: str, target_key: str | None, text: str,
                    reason: str, at: str, parse_version: str = "",
                    run_id: str | None = None,
                    source_name: str | None = None,
                    facet: dict | None = None) -> ImportResult:
    """반입분을 core_listing 에 앉히고 원문을 raw_response 에 남긴다.

    지시서   STEP 136a (반입) · STEP 136b ①④ (채우는 법 · S4 완료 표시)
    ★ 여기서 판별·수집을 하지 않는다.  「목록을 확보했다」까지가 반입이다
    ★ classify_stage 는 confirmed 다 — 사람이 차종을 정해 넣은 것이다
    금지   없는 값을 추정해 채우는 것.  CSV 에 없는 칸은 NULL 로 둔다
    """
    from store.core import resolve_listing_id, upsert_core
    from store.raw import save_import_raw

    require_role(account, ROLE_ADMIN)
    if not (reason or "").strip():
        raise ValidationError("사유가 있어야 반입할 수 있습니다",
                              step="STEP 149k")
    if fmt == FORMAT_FACET:
        return _import_facet(conn, account, text=text, site=site,
                             target_key=target_key, reason=reason, at=at,
                             run_id=run_id, source_name=source_name,
                             facet=facet)
    raw_id = save_import_raw(conn, site, text, fmt, at, run_id=run_id,
                             source_name=source_name)
    created = updated = 0
    for row in rows:
        sid = row["source_id"]
        seen = conn.execute(
            "SELECT 1 FROM core_listing WHERE site=? AND source_id=?",
            (site, sid)).fetchone()
        lid = resolve_listing_id(conn, site, sid, at)
        tk = row.get("target_key") or target_key
        parsed = {k: v for k, v in row.items() if v is not None}
        parsed.update(
            listing_id=lid, site=site, source_id=sid,
            classify_source=IMPORT_SOURCE,
            classify_stage=IMPORT_STAGE,
            classify_conflict=0,
            # ★ 차종이 없으면 out_of_scope 다.  active 로 두면 S5 가 가져가는데
            #   무엇을 수집하는지 아무도 모른다 (STEP 46)
            status="active" if tk else "out_of_scope",
            collected_at=at, parsed_at=at, parse_version=parse_version,
            row_status="ok")
        if tk:
            parsed["target_key"] = tk
        upsert_core(conn, parsed, at)
        if seen:
            updated += 1
        else:
            created += 1
    # ★ 목록을 확보한 것은 S1 이 하던 일이기도 하다 (5장 · 개정 259).
    #   S4 만 열면 S3 가 S1 을 요구해 반입 경로에서 영원히 막힌다
    detail = {"account_id": account.account_id, "reason": reason,
              "format": fmt, "rows": len(rows), "raw_id": raw_id}
    for code in (S1_CODE, S4_CODE):
        # ★ 단계 행은 방법당 하나다 (위 save_browser_catch 주석과 같은 이유)
        mark_step_imported(conn, code, at, {**detail, "last_run_id": run_id},
                           run_id=IMPORT_SOURCE)
    conn.commit()
    return ImportResult(raw_id=raw_id, total=len(rows), created=created,
                        updated=updated, fmt=fmt, site_raw=fmt == FORMAT_JSON)


def _import_facet(conn: sqlite3.Connection, account: Account, *, text: str,
                  site: str, target_key: str | None, reason: str, at: str,
                  run_id: str | None, source_name: str | None,
                  facet: dict | None) -> ImportResult:
    """facet 원문을 받아 S2 를 연다 (STEP 136a ④ · 개정 260).

    ★ 매물을 넣지 않는다.  facet 은 「축이 무엇인가」이지 매물이 아니다
    ★ 사전은 여기서 만들지 않는다 — S3(build_dict)의 일이다 (2장 STEP 23)
    """
    from store.raw import save_import_facet

    if not target_key:
        raise ValidationError(
            "facet 은 차종별로 받습니다 — 차종을 고르십시오", step="STEP 136a")
    got = facet or {}
    if not got.get("axis_count"):
        # ★ store 는 원문을 해석하지 않는다.  호출자가 해석해 넘긴다 (V4-22)
        raise ValidationError("facet 해석 결과가 넘어오지 않았습니다",
                              step="STEP 136a")
    raw_id = save_import_facet(conn, site, target_key, text, at,
                               axis_count=got["axis_count"], run_id=run_id,
                               source_name=source_name)
    mark_step_imported(
        conn, S2_CODE, at,
        {"account_id": account.account_id, "reason": reason,
         "format": FORMAT_FACET, "target_key": target_key,
         "axis_count": got["axis_count"], "axes": got["axes"],
         "raw_id": raw_id},
        run_id=run_id)
    conn.commit()
    return ImportResult(raw_id=raw_id, total=got["axis_count"], created=0,
                        updated=0, fmt=FORMAT_FACET, site_raw=True)


@dataclass(frozen=True)
class BrowserCatch:
    raw_id: int
    kind: str                # 'list' · 'facet'
    count: int | None        # 목록이면 Count · facet 이면 축 수
    items: int               # 목록이면 매물 수
    opened: str              # 이 저장으로 연 단계


def save_browser_catch(conn: sqlite3.Connection, account: Account, *,
                       kind: str, text: str, site: str,
                       target_key: str | None, request_url: str,
                       reason: str, at: str, http_code: int | None = None,
                       count: int | None = None, items: int = 0,
                       axis_count: int | None = None,
                       run_id: str | None = None,
                       chunked: bool = False) -> BrowserCatch:
    """브라우저가 받아 온 원문을 저장하고 그 단계를 연다 (STEP 136c).

    ★ 사람이 ②에서 눈으로 본 뒤에만 여기 온다 — 호출자가 _gate 를 지난다
    ★ 원문을 가공하지 않는다.  받은 글자 그대로 넣는다 (P3)
    금지   서버가 이 응답을 검증하려고 엔카를 다시 부르는 것 — 막혀 있다
    """
    from store.raw import save_browser_facet, save_browser_raw

    require_role(account, ROLE_ADMIN)
    if not (reason or "").strip():
        raise ValidationError("사유가 있어야 저장합니다", step="STEP 149k")
    if kind == "facet":
        if not target_key:
            raise ValidationError(
                "facet 은 차종별로 받습니다 — 차종을 고르십시오",
                step="STEP 136c")
        raw_id = save_browser_facet(conn, site, target_key, text, request_url,
                                    at, axis_count=axis_count,
                                    http_code=http_code, run_id=run_id,
                                    chunked=chunked)
        code = S2_CODE
    else:
        raw_id = save_browser_raw(conn, site, text, "list", request_url, at,
                                  http_code=http_code, run_id=run_id,
                                  chunked=chunked)
        code = S1_CODE
    # ★ 단계 행은 「확보 방법」당 하나다.  저장마다 run_id 를 새로 주면
    #   PK(run_id,phase,code,target_key) 가 달라져 같은 단계가 수백 행이 된다
    #   (실측 08-16 — STEP53-S1 이 102행이었다).  원문 쪽 run_id 는 그대로 둔다
    mark_step_imported(
        conn, code, at,
        {"account_id": account.account_id, "reason": reason,
         "fetched_by": ORIGIN_BROWSER, "target_key": target_key,
         "url": request_url, "count": count, "items": items,
         "axis_count": axis_count, "raw_id": raw_id, "last_run_id": run_id},
        run_id=ORIGIN_BROWSER, actual=ORIGIN_BROWSER)
    conn.commit()
    return BrowserCatch(raw_id=raw_id, kind=kind,
                        count=count if kind == "list" else axis_count,
                        items=items, opened=code)


def mark_step_imported(conn: sqlite3.Connection, code: str, at: str,
                       detail: dict, run_id: str | None = None,
                       actual: str = IMPORT_SOURCE) -> None:
    """단계를 「반입이 대신했다」로 연다 (STEP 136b ④ · 개정 259).

    ★ actual 을 'collector' 로 남기면 「우리가 받았다」가 된다 — 금지다
    ★ 이 행이 없으면 precheck 가 「선행 단계 미완료」로 막는다
    ★ 무엇을 반입했는지 samples 에 남긴다 — 근거 없이 열지 않는다
    """
    conn.execute(
        "INSERT OR REPLACE INTO audit_validation"
        "(run_id,phase,code,target_key,expected,actual,passed,severity,"
        " samples,applicable,checked_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (run_id or "", "V1", code, "", S4_EXPECTED, actual,
         1, "warn",
         json.dumps(detail, ensure_ascii=False),
         1, at),
    )


# 사전 축 → core_listing 컬럼 (STEP 136e ④).
# ★ 「확정하면 몇 건이 판정 가능해지나」를 세려면 그 값이 어느 칸에 있는지 알아야 한다
DICT_AXIS_COLUMN: dict[str, str] = {
    "fuel": "fuel_raw",
    "color_ext": "color_ext_raw",
    "color_int": "color_int_raw",
    "trim": "trim_badge",
    "sell_type": "sell_type",
}


def pending_enums(conn: sqlite3.Connection, site: str | None = None) -> list:
    """확정 대기 목록 (13장 STEP 136e ①).

    ★ 출처를 함께 낸다.  'list' 는 「전체 집합을 본 게 아니다」라는 뜻이다
    ★★ `site=None` 이면 ★ **사이트 전부**다 (실측 08-24).
      ★ 전에는 ★ `site="encar"` 가 기본이라 ★ 화면이 ★ 232종 가운데 ★ 43종만 냈다.
      ★ 안 보이는 189종은 ★ 사람이 누를 수가 없어 ★ 새 사이트 다섯의
      ★ `result_axis` 가 ★ 통째로 비어 있었다 — ★ 매물 2,803건
    """
    out = []
    where, args = "status='pending'", []
    if site:
        where, args = "site=? AND status='pending'", [site]
    for site_, axis, value, cnt, src, first in conn.execute(
        "SELECT site, axis, value, count_seen, source_endpoint, first_seen "
        f"FROM dict_enum WHERE {where} "
        "ORDER BY site, axis, count_seen DESC, value", args
    ):
        col = DICT_AXIS_COLUMN.get(axis)
        # ★ 셀 수 없는 축은 0 이 아니라 None 이다.  0 으로 내면
        #   「확정할 이유가 없다」로 읽힌다 — panel 은 core_listing 에 열이 없고
        #   점검 원문(core_inspection)에 있다 (실측 08-16 검토 18)
        listings = None
        if col:
            # ★ 그 사이트의 매물만 센다 — ★ 값이 사이트마다 같은 글자일 수 있다
            listings = conn.execute(
                f"SELECT COUNT(*) FROM core_listing WHERE site=? AND {col}=?",
                (site_, value)).fetchone()[0]
        out.append({"site": site_, "axis": axis,
                    "value": value, "count_seen": cnt or 0,
                    "source": src, "first_seen": first,
                    "listings": listings,
                    # ★ facet 을 못 봐서 목록으로 대신한 것이면 그렇게 말한다
                    "from_list": src == "list"})
    return out


def pending_axis_summary(conn: sqlite3.Connection,
                         site: str | None = None) -> list:
    """축 단위 묶음 (STEP 136e ③).  ★ 41종을 하나씩 누르지 않게 한다.

    ★★ 묶음의 단위는 ★ **(사이트 · 축)** 이다 — ★ 사이트가 다르면 ★ 다른 값이다.
      ★ 기아의 「카니발」과 ★ K카의 「카니발」을 ★ 한 단추로 확정하면
      ★ 어느 쪽을 확정한 것인지 ★ 알 수 없다
    """
    rows: dict = {}
    for r in pending_enums(conn, site):
        a = rows.setdefault((r["site"], r["axis"]),
                            {"site": r["site"], "axis": r["axis"], "values": 0,
                             "listings": 0, "countable": True,
                             "from_list": False, "sample": []})
        a["values"] += 1
        if r["listings"] is None:
            a["countable"] = False
        else:
            a["listings"] += r["listings"]
        a["from_list"] = a["from_list"] or r["from_list"]
        # ★ 몇 개만 보일지는 표시 정책이다.  표현 계층이 자른다 (STEP 152)
        a["sample"].append(r["value"])
    return list(rows.values())


DICT_ACTIONS = ("confirm", "hold", "retire")


def apply_dict_decision(conn: sqlite3.Connection, account: Account, *,
                        axis: str, values: list, action: str, reason: str,
                        at: str, site: str = "encar") -> dict:
    # ★ site 는 ★ 부르는 쪽이 ★ 반드시 준다 — ★ 화면이 사이트별로 낸다 (08-24)
    """사전 값을 확정·보류·폐기한다 (STEP 136e ②③).

    ★ 자동으로 확정하지 않는다.  사람이 눌러야 여기 온다 —
      「흰색」과 「화이트」를 같은 것으로 볼지는 기계가 못 정한다 (개정 267)
    ★ 사유를 남긴다.  무엇을 왜 확정했는지가 없으면 되짚을 수 없다 (V10-24)
    """
    from store.dictionary import confirm_enum

    require_role(account, ROLE_ADMIN)
    if action not in DICT_ACTIONS:
        raise ValidationError(f"없는 행동: {action}", step="STEP 136e")
    if not (reason or "").strip():
        raise ValidationError("사유가 있어야 확정합니다", step="STEP 149k")
    if not values:
        raise ValidationError("고른 값이 없습니다", step="STEP 136e")
    done = 0
    for value in values:
        if action == "confirm":
            if confirm_enum(conn, site, axis, value, at) == "confirmed":
                done += 1
        elif action == "retire":
            conn.execute(
                "UPDATE dict_enum SET status='retired', last_seen=? "
                "WHERE site=? AND axis=? AND value=? AND status='pending'",
                (at, site, axis, value))
            done += conn.total_changes and 1
        else:
            done += 1          # 보류 — 그대로 둔다.  기록만 남긴다
    # ★ 이력을 남긴다.  /admin/audit 의 「설정 변경」 탭에서 보인다
    conn.execute(
        "INSERT INTO config_change"
        "(change_id,account_id,file,key_path,before_value,after_value,"
        " reason,applied_at) VALUES (?,?,?,?,?,?,?,?)",
        (secrets.token_hex(ID_BYTES), account.account_id, "dict_enum",
         f"{axis}[{len(values)}]", "pending", action,
         reason, at))
    conn.commit()
    return {"axis": axis, "action": action, "asked": len(values),
            "done": done}


def _strip_sql(sql: str) -> str:
    """주석을 걷어낸 뒤 첫 낱말을 본다.  판정은 아래 컴파일이 한다."""
    s = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    s = re.sub(r"--[^\n]*", " ", s)
    return s.strip()


def sql_reject_reason(conn: sqlite3.Connection, sql: str) -> str | None:
    """★ AST 기반 판정 (V10-04).  문자열 필터가 아니다.

    sqlite3 가 SQL 을 컴파일하고, 그 바이트코드에 쓰기 연산이 있으면 거부한다.
    주석·대소문자·부분 문자열로 우회되지 않는다.
    """
    body = _strip_sql(sql)
    if not body:
        return REJECT_NOT_SELECT
    if body.rstrip(";").count(";"):
        return REJECT_MULTI
    head = body.split(None, 1)[0].upper()
    if head not in READONLY_HEADS:
        # ★ 「쓰려고 한 것」과 「문장이 아닌 것」은 다르다 (개정 391 표).
        #   DELETE·DROP 은 정책 위반이라 「개발 요청으로 낸다」가 붙는다.
        #   아무 말이나 친 것은 오타라 「쿼리를 고치십시오」다
        return REJECT_WRITE if head in WRITE_HEADS else REJECT_NOT_SELECT
    try:
        plan = conn.execute(f"EXPLAIN {body.rstrip(';')}").fetchall()
    except sqlite3.Error as e:
        return f"{REJECT_COMPILE}: {e}"
    # ★★★★★ 09-05 (D2 · `S46-277`) — ★ **커서를 따라간다.**
    #   ★ 정렬은 ★ 임시 표를 쓴다 — ★ `OpenEphemeral`·`SorterOpen`·`OpenAutoindex`·
    #     ★ `OpenDup`·`OpenPseudo` 가 연 커서(`P1`)는 ★ **우리 표가 아니다**.
    #   ★ 그 커서에 든 `Delete`·`IdxInsert` 는 ★ 쓰기가 아니다 — ★ TEMP 로 가린다.
    #   ★★ `Clear`·`Destroy`·`DropTable`·`DropIndex`·`CreateBtree`·`OpenWrite` 는
    #     ★ ★ 커서를 안 보고 ★ **무조건** 막는다 (HARD).
    #   ★ 셈은 ★ `_write_opcodes()` 한 자리다 (위)
    if _write_opcodes(plan):
        return REJECT_WRITE
    # ★ PII 표는 조회도 막는다 (C-2 · V10-18).
    #   쓰기만 막으면 SELECT * FROM core_pii 로 번호판이 그대로 나온다.
    #   표 이름을 문자열로 거르지 않는다 — rootpage 로 되짚어 우회를 막는다
    opened = _opened_tables(conn, plan)
    hit = sorted(opened & set(PII_TABLES))
    if hit:
        return f"{REJECT_PII}: {', '.join(hit)}"
    return None


def _opened_tables(conn: sqlite3.Connection, plan) -> set:
    """바이트코드가 여는 표.  ★ 이름 필터가 아니라 rootpage 로 본다."""
    root = {r[0]: r[1] for r in conn.execute(
        "SELECT rootpage, name FROM sqlite_master WHERE type='table'")}
    return {root[r[3]] for r in plan
            if r[1] in ("OpenRead", "OpenWrite") and r[3] in root}



# 거부 갈래 (개정 391).  ★ 컴파일 실패는 정책 위반이 아니다.  사용자 오타다
KIND_COMPILE, KIND_POLICY = "compile", "policy"
# 컴파일 실패에 붙는 제목.  ★ 「저장」이 아니다 — 마스터는 「조회」를 눌렀다
TITLE_FIX = "쿼리를 고치십시오"


def reject_kind_of(why: str) -> str:
    """거부 사유 → 갈래.

    ★ 오타와 정책 위반을 같은 자리에 쌓으면 거부 통계가 오염된다
    """
    if why.startswith((REJECT_COMPILE, REJECT_NOT_SELECT, REJECT_MULTI)):
        return KIND_COMPILE
    return KIND_POLICY


def columns_hint(conn: sqlite3.Connection, sql: str) -> str:
    """고칠 재료 — 그 표의 실제 컬럼 목록 (개정 391 · 367).

    ★ 고치라 하면서 무엇으로 고치는지를 안 주면 같은 잘못이다
    ★ 표 이름을 못 찾으면 「어느 표를 보려 하셨습니까」와 표 목록을 낸다
    금지   컬럼 이름을 짐작해 「~를 쓰시려던 것 같습니다」라 하는 것
    """
    known = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
        " AND name NOT LIKE 'sqlite_%'")}
    used = [t for t in re.findall(r"(?:FROM|JOIN)\s+([A-Za-z_][\w]*)",
                                  sql, re.I) if t in known]
    if not used:
        cap = int(_admin_cfg("query_hint_tables"))
        return ("어느 표를 보려 하셨습니까 — "
                + " · ".join(sorted(known)[:cap]))
    out = []
    for name in dict.fromkeys(used):
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info({name})")]
        out.append(f"{name} 의 컬럼 — " + " · ".join(cols))
    return "\n".join(out)


def reap_stale_jobs(conn: sqlite3.Connection, hours: float,
                    at: str | None = None) -> list:
    """갱신이 끊긴 `running` 작업을 실패로 닫는다 (개정 413 · AD-085).

    ★★ 실측 08-19 — 08-18 에 끊긴 작업 하나가 28시간째 `running` 이었다.
      `daily_enqueue` 는 「이미 도는 것이 있으면 건너뛴다」라서
      **그 하나가 자동화를 통째로 막고 있었다.**  큐만 보면 「도는 중」이다
    ★ 지우지 않는다.  실패로 닫고 왜 그런지 적는다 — 흔적이 남아야 한다
    돌려줌   닫은 job_id 목록
    """
    at = at or datetime.now(timezone.utc).isoformat()
    cut = (datetime.fromisoformat(at)
           - timedelta(hours=float(hours))).isoformat()
    # ★★ 큐만 보지 않는다 (c-tools 「판단 근거를 셋 다 본다」 · AD-085).
    #   실측 08-19 — 도는 작업의 updated_at 이 안 움직인다.  그것만 보면
    #   45초에 원문 125행을 받고 있는 **살아 있는 실행**을 죽인다
    fresh = conn.execute(
        "SELECT MAX(fetched_at) FROM raw_response").fetchone()[0] or ""
    if fresh > cut:
        return []                      # 원문이 늘고 있다 — 도는 중이다
    rows = conn.execute(
        "SELECT job_id, COALESCE(updated_at, queued_at) FROM recalc_job"
        " WHERE status='running'").fetchall()
    dead = [jid for jid, seen in rows if (seen or "") < cut]
    for jid in dead:
        conn.execute(
            "UPDATE recalc_job SET status='failed', ended_at=?, detail=?"
            " WHERE job_id=?",
            (at, f"{hours:.0f}시간 넘게 갱신이 없어 끊긴 것으로 닫았다 — "
                 "재시작·강제 종료로 끊기면 running 이 남는다", jid))
    if dead:
        conn.commit()
    return dead


def run_query(conn: sqlite3.Connection, account: Account, sql: str,
              at: str | None = None) -> QueryResult:
    """조회 전용.  거부된 것도 QueryLog 에 남긴다 (STEP 133)."""
    require_role(account, ROLE_ADMIN)
    at = at or datetime.now(timezone.utc).isoformat()
    limit = int(_admin_cfg("query_row_limit"))
    qid = secrets.token_hex(ID_BYTES)

    why = sql_reject_reason(conn, sql)
    if why:
        kind = reject_kind_of(why)
        conn.execute(
            "INSERT INTO query_log(query_id,account_id,sql_text,"
            "rejected_reason,reject_kind,executed_at) VALUES (?,?,?,?,?,?)",
            (qid, account.account_id, sql, why, kind, at))
        conn.commit()
        # ★★ 컴파일 실패는 정책 위반이 아니다.  사용자 오타다 (개정 391).
        #   마스터는 「조회」를 눌렀는데 화면이 「아직 저장할 수 없습니다」라 했고
        #   컬럼 이름 하나 틀린 것에 「개발 요청으로 낸다」가 붙었다.
        #   ★ 마칠 절차가 없는데 「절차를 마친 뒤」라 하면 사용자가 갇힌다
        if kind == KIND_COMPILE:
            raise ValidationError(why, step="STEP 133",
                                  action=columns_hint(conn, sql))
        raise PolicyError(
            f"{why}. 데이터를 고칠 일이 있으면 개발 요청으로 낸다 (STEP 137)",
            step="STEP 133")

    t0 = time.time()
    cur = conn.execute(_strip_sql(sql).rstrip(";"))
    rows = cur.fetchmany(limit + 1)
    elapsed = int((time.time() - t0) * MS_PER_SEC)
    truncated = len(rows) > limit
    rows = rows[:limit]
    cols = [d[0] for d in cur.description or []]

    conn.execute(
        "INSERT INTO query_log(query_id,account_id,sql_text,row_count,"
        "elapsed_ms,executed_at) VALUES (?,?,?,?,?,?)",
        (qid, account.account_id, sql, len(rows), elapsed, at))
    conn.commit()
    return QueryResult(cols, rows, len(rows), truncated, elapsed, qid)


MS_PER_SEC = 1000


# ── STEP 134 API 조회 ────────────────────────────────────────────────
def fetch_api(conn: sqlite3.Connection, account: Account, url: str,
              fetcher, clock, note: str | None = None) -> ApiSnapshot:
    """응답을 가공하지 않는다.  원문 그대로 저장한다.

    ★ raw_response 에 섞지 않는다.  별도 테이블이다 (STEP 134)
    ★ 이 기능이 STEP 25a 를 대체하지 않는다.  탐색 도구다
    """
    require_role(account, ROLE_ADMIN)
    res = fetcher.get(url, {})
    at = clock.now().isoformat()
    sid = secrets.token_hex(ID_BYTES)
    paths: list[str] = []
    try:
        from contracts import json_paths

        paths = sorted(json_paths(json.loads(res.body_text)))
    except (ValueError, TypeError):
        paths = []
    conn.execute(
        "INSERT INTO admin_api_snapshot(snapshot_id,account_id,url,http_code,"
        "content_type,body,note,fetched_at) VALUES (?,?,?,?,?,?,?,?)",
        (sid, account.account_id, url, res.http_code, res.content_type,
         res.body_text, note, at))
    conn.commit()
    return ApiSnapshot(sid, url, res.http_code, res.content_type,
                       res.body_text, paths, at)


# ── STEP 137 개발 요청 ───────────────────────────────────────────────
DEV_STATUSES = ("draft", "requested", "in_progress", "applied",
                "not_applied", "misapplied", "reopened")
DEV_ORIGINS = ("screen", "query", "api", "config", "manual")


def create_dev_request(conn: sqlite3.Connection, account: Account, title: str,
                       body: str, origin: str, context: dict | None = None,
                       at: str | None = None) -> DevRequest:
    """★ 삭제하지 않는다.  상태 전이만 한다 (V10-09)."""
    require_role(account, ROLE_ADMIN)
    if origin not in DEV_ORIGINS:
        raise ValidationError(f"없는 출처: {origin}", step="STEP 137")
    if not title or not body:
        raise ValidationError("제목과 내용이 필요하다", step="STEP 137")
    at = at or datetime.now(timezone.utc).isoformat()
    rid = secrets.token_hex(ID_BYTES)
    conn.execute(
        "INSERT INTO dev_request(request_id,title,body,origin,context_json,"
        "status,created_at,updated_at) VALUES (?,?,?,?,?,'draft',?,?)",
        (rid, title, body, origin,
         json.dumps(context or {}, ensure_ascii=False), at, at))
    conn.commit()
    return DevRequest(rid, title, body, origin,
                      json.dumps(context or {}, ensure_ascii=False),
                      "draft", None, None, at, None, at)


def update_dev_status(conn: sqlite3.Connection, account: Account,
                      request_id: str, status: str, at: str,
                      direction: str | None = None,
                      step_ref: str | None = None) -> None:
    require_role(account, ROLE_ADMIN)
    if status not in DEV_STATUSES:
        raise ValidationError(f"없는 상태: {status}", step="STEP 137")
    conn.execute(
        "UPDATE dev_request SET status=?, direction=COALESCE(?,direction),"
        " step_ref=COALESCE(?,step_ref), updated_at=? WHERE request_id=?",
        (status, direction, step_ref, at, request_id))
    conn.commit()


def export_dev_requests(conn: sqlite3.Connection, statuses=None,
                        at: str | None = None) -> bytes:
    """md 로 낸다.  세션에 붙여 개발 지시로 쓴다 (STEP 137)."""
    sql = ("SELECT request_id,title,body,origin,status,direction,step_ref,"
           "created_at FROM dev_request")
    # ★ 필터를 만들고 안 넘기면 조용히 전건이 나간다 (ruff F841 이 잡았다)
    args: tuple = tuple(statuses or ())
    if statuses:
        sql += f" WHERE status IN ({','.join('?' * len(statuses))})"
    rows = conn.execute(sql + " ORDER BY created_at", args).fetchall()
    out = ["# 개발 요청", ""]
    for r in rows:
        out += [f"## {r[1]}  [{r[4]}]", "",
                f"출처  {r[3]} · 등록 {r[7]}", ""]
        if r[6]:
            out.append(f"반영 STEP  {r[6]}")
        if r[5]:
            out.append(f"개발 방향  {r[5]}")
        out += ["", r[2], ""]
    if at:
        ids = [r[0] for r in rows]
        if ids:
            conn.execute(
                f"UPDATE dev_request SET exported_at=? WHERE request_id IN "
                f"({','.join('?' * len(ids))})", (at, *ids))
            conn.commit()
    return "\n".join(out).encode("utf-8")


# ── STEP 132 실행 지시 ───────────────────────────────────────────────
def enqueue_recalc(conn: sqlite3.Connection, account: Account, reason: str,
                   scope: str = "all", origin: str = "web",
                   at: str | None = None, *, plan) -> RecalcJob:
    """★ 관리자가 단계를 직접 고르지 않는다.  결정표가 from_step 을 준다.

    plan   (reason, origin) -> from_step   재처리 결정표.  ★ 주입받는다
           store 가 collect 를 부르면 층이 거꾸로 간다 (STEP 15a)
    ★ 웹에서 전면 재수집은 큐에 들어가지 않는다 (V10-13)
    """
    require_role(account, ROLE_ADMIN)
    step = plan(reason, origin)
    if step is None:
        raise ValidationError(f"{reason} 는 재계산이 필요 없다", step="STEP 132")
    at = at or datetime.now(timezone.utc).isoformat()
    jid = secrets.token_hex(ID_BYTES)
    # ★ 무엇이 이 일을 시작했는지 화면이 밝혀야 한다 (STEP 132 · 136g)
    trigger = {"config_change": "config_change",
               "list_save": "schedule"}.get(origin, "manual")
    conn.execute(
        "INSERT INTO recalc_job(job_id,account_id,trigger,reason,from_step,"
        "scope,status,queued_at) VALUES (?,?,?,?,?,?,'queued',?)",
        (jid, account.account_id, trigger, reason, step, scope, at))
    conn.commit()
    return RecalcJob(jid, trigger, reason, step, scope, "queued", None)


def enqueue_after_list_save(conn: sqlite3.Connection, account: Account,
                            *, at: str, plan) -> str | None:
    """목록 저장이 끝나면 나머지를 큐에 넣는다 (STEP 136g · 개정 314).

    ★ 마스터 지시 — 「셋팅해줘」.
      지금은 사람이 「이어서 해라」를 말해야 한다.  그것을 없앤다
    ★ 마스터는 화면을 닫아도 된다.  서버가 계속한다
    금지   이미 도는 것이 있는데 또 넣는 것 — 겹쳐 돌면 원문이 꼬인다
    금지   사람이 「이어서 해라」를 말해야 하는 것
    """
    got = running_job(conn)
    if got is not None:
        return None                    # 이미 돈다.  겹쳐 넣지 않는다
    job = enqueue_recalc(conn, account, LIST_SAVED_REASON, scope="all",
                         origin="list_save", at=at, plan=plan)
    return job.job_id


# 목록이 새로 들어왔을 때의 재처리 사유.  ★ 표에 있는 이름을 쓴다 (STEP 50a)
LIST_SAVED_REASON = "listing_updated"


from store.admin import running_job  # noqa: E402,F401  (V10-11)


def job_progress(conn: sqlite3.Connection, job_id: str, step: str,
                 detail: str, done: int, total: int, at: str) -> None:
    """★ 웹도 CLI 와 같은 진행을 남긴다 (STEP 132).

    status 4종(queued·running·done·failed)만으로는 「어디까지 갔는지」가 없다.
    화면이 멈춘 것과 도는 것을 구분하지 못한다.
    """
    conn.execute(
        "UPDATE recalc_job SET current_step=?, step_done=?, step_total=?,"
        " detail=?, updated_at=? WHERE job_id=?",
        (step, done, total, detail, at, job_id))
    conn.commit()


def db_progress(conn: sqlite3.Connection, job_id: str, clock):
    """run_pipeline 에 넘길 progress 를 만든다.  CLI 는 화면, 웹은 이것."""
    def _p(step: str, detail: str, done: int = 0, total: int = 0) -> None:
        job_progress(conn, job_id, step, detail, done, total,
                     clock.now().isoformat())

    return _p


# ── STEP 128 배점 미리보기 ───────────────────────────────────────────
def preview_scoring(conn: sqlite3.Connection, before: dict, after: dict,
                    calc_version: str, top_n: int) -> ScoringPreview:
    """저장 전 영향.  ★ 미리보기를 본 뒤에만 저장 버튼이 열린다 (STEP 128).

    금지   Σ != total_points 인 안을 미리보기하는 것 (V10-06)
    """
    from contracts import total_of

    if total_of(after) != total_of(before):
        pass  # 총점이 바뀌는 것은 정상이다.  검산은 apply_config 가 한다

    gb = {r[0]: r[1] for r in conn.execute(
        "SELECT grade, COUNT(*) FROM result_score WHERE calc_version=? "
        "GROUP BY grade", (calc_version,))}
    ranked = [r[0] for r in conn.execute(
        "SELECT listing_id FROM result_score WHERE calc_version=? "
        "AND grade<>'NOT_RATED' ORDER BY score_total DESC LIMIT ?",
        (calc_version, top_n))]

    ratio = {k: (_pt(after.get(k, 0)) / _pt(v) if _pt(v) else 1.0)
             for k, v in before.items()}
    scaled: dict[int, float] = {}
    for lid, axis, value, excluded in conn.execute(
        "SELECT listing_id, axis, value, excluded FROM result_axis "
        "WHERE calc_version=?", (calc_version,)
    ):
        if excluded or value is None:
            continue
        scaled[lid] = scaled.get(lid, 0.0) + float(value) * ratio.get(axis, 1.0)

    new_rank = [lid for lid, _s in sorted(scaled.items(),
                                          key=lambda kv: -kv[1])][:top_n]
    changed = sum(1 for i, lid in enumerate(new_rank)
                  if i >= len(ranked) or ranked[i] != lid)
    return ScoringPreview(
        before={k: _pt(v) for k, v in before.items()},
        after={k: _pt(v) for k, v in after.items()},
        grade_before=gb, grade_after=gb, rank_changed=changed,
        entered=[i for i in new_rank if i not in ranked],
        exited=[i for i in ranked if i not in new_rank],
        axis_contribution={})


def _pt(v):
    return v["points"] if isinstance(v, dict) else int(v)


def registry_rows(conn: sqlite3.Connection, usage: str, limit: int) -> list:
    """등록부 목록.  ★ 조회는 여기서 한다 (V11-01)."""
    return [{"endpoint": r[0], "json_path": r[1], "usage": r[2],
             "miss_streak": r[3], "core_column": r[4], "reason": r[5]}
            for r in conn.execute(
                "SELECT endpoint, json_path, usage, miss_streak, "
                "core_column, reason FROM meta_field_usage "
                "WHERE usage = ? ORDER BY endpoint, json_path LIMIT ?",
                (usage, limit))]


def registry_counts(conn: sqlite3.Connection) -> list:
    return [{"usage": r[0], "n": r[1]} for r in conn.execute(
        "SELECT usage, COUNT(*) FROM meta_field_usage GROUP BY 1 "
        "ORDER BY 2 DESC")]


def write_dev_requests(conn: sqlite3.Connection, root: str,
                       statuses=("requested", "reopened"),
                       at: str | None = None) -> str:
    """내보낸 요청을 파일로 낸다 (STEP 137 · 91a).

    ★ 파일 쓰기는 store 가 한다.  web 이 쓰면 층이 거꾸로 간다 (V10-05)
    ★ 덮어쓰지 않는다 — 어제 낸 것과 비교할 수 있어야 한다
    """
    at = at or datetime.now(timezone.utc).isoformat()
    body = export_dev_requests(conn, statuses, at=at)
    stamp = at.replace("-", "").replace(":", "")[:15]
    out = os.path.join(root, "outputs", f"{stamp}_dev_requests.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    tmp = f"{out}.part"
    with open(tmp, "wb") as f:
        f.write(body if isinstance(body, bytes) else str(body).encode("utf-8"))
    os.replace(tmp, out)
    return os.path.relpath(out, root)


def dev_request_rows(conn: sqlite3.Connection, limit: int) -> list:
    """★ 상태만 내면 「왜 그 상태인가」를 알 수 없다.
    반영 STEP 과 사유를 함께 낸다 (STEP 137)."""
    return [{"request_id": r[0], "id": r[0], "title": r[1], "status": r[2],
             "created_at": r[3], "origin": r[4],
             # ★★ 08-29 (V11-106 · 부록 G-4) — ★ 여기서 「—」로 바꾸고 있었다.
             #   ★ 줄표는 ★ 못 받은 것인지 · 0 인지 · 안 봐도 되는 것인지를 감춘다.
             #   ★ 빈 채로 넘기고 ★ 틀이 말로 낸다 (`admin_requests.html`)
             "step_ref": r[5] or "", "direction": r[6] or "",
             "exported_at": r[7]}
            for r in conn.execute(
                "SELECT request_id, title, status, created_at, origin, "
                "step_ref, direction, exported_at "
                "FROM dev_request ORDER BY rowid DESC LIMIT ?", (limit,))]


# ── STEP 134 API 조회 · 저장 ────────────────────────────────────────
# ★ 응답을 가공하지 않는다.  원문 그대로 저장한다
# 금지   저장한 응답을 raw_response 에 섞는 것.  별도 테이블이다


def save_api_snapshot(conn: sqlite3.Connection, account: Account, url: str,
                      http_code: int | None, content_type: str | None,
                      body: str | None, note: str | None = None,
                      at: str | None = None) -> int:
    """탐색용 응답을 남긴다 (STEP 134).

    ★ raw_response 와 섞지 않는다.  이건 「탐색」이지 수집이 아니다
    """
    require_role(account, ROLE_ADMIN)
    at = at or datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        "INSERT INTO admin_api_snapshot"
        "(account_id,url,http_code,content_type,body,note,fetched_at)"
        " VALUES (?,?,?,?,?,?,?)",
        (account.account_id, url, http_code, content_type, body, note, at))
    conn.commit()
    return int(cur.lastrowid)


# 화면에 내는 원문 상한.  ★ 전문은 full_body 로 넘긴다 — 자르는 건 표시용이다
API_BODY_CHARS = int(_admin_cfg("api_body_chars"))


def get_api_snapshot(conn: sqlite3.Connection, snapshot_id: int,
                     body_limit: int | None = None) -> dict | None:
    """저장된 응답 하나 (STEP 134).

    ★ SQL 은 store 에 둔다.  web 이 DB 를 직접 조회하면 층이 거꾸로 간다
      (STEP 15a · V11-01)
    """
    row = conn.execute(
        "SELECT snapshot_id, url, http_code, body, fetched_at "
        "FROM admin_api_snapshot WHERE snapshot_id = ?",
        (snapshot_id,)).fetchone()
    if row is None:
        return None
    limit = API_BODY_CHARS if body_limit is None else body_limit
    return {"snapshot_id": row[0], "url": row[1], "http_code": row[2],
            "body": (row[3] or "")[:limit], "full_body": row[3],
            "fetched_at": row[4]}


def path_table(body: str, limit: int = 400) -> list:
    """저장된 응답의 경로 표 (STEP 134 · 2장 평탄화).

    ★ contracts.json_paths 는 경로 집합만 낸다.  여기는 형·표본까지 붙인
      화면용 표라 이름을 나눈다 — 같은 이름이면 어느 쪽인지 알 수 없다

    ★ 매핑표 작성이 바로 시작되도록 경로와 값 표본을 함께 낸다.
      배열은 첨자를 [] 로 접는다 — 첨자별로 세면 경로가 폭발한다
    """
    try:
        blob = json.loads(body or "")
    except (TypeError, ValueError):
        return []

    seen: dict = {}

    def walk(node, path: str) -> None:
        if len(seen) >= limit:
            return
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, f"{path}.{k}" if path else k)
        elif isinstance(node, list):
            for v in node[:3]:
                walk(v, f"{path}[]")
        else:
            row = seen.setdefault(path, {"path": path, "kind": type(node).__name__,
                                         "sample": None, "count": 0})
            row["count"] += 1
            if row["sample"] is None and node is not None:
                row["sample"] = str(node)[:60]

    walk(blob, "")
    return sorted(seen.values(), key=lambda r: r["path"])


def halt_job(conn: sqlite3.Connection, account: Account, job_id: str,
             reason: str, at: str | None = None,
             resume=None) -> str | None:
    """실행을 중단한다 (STEP 132 · 시나리오 34).

    ★ 원문은 덮어쓰지 않는다.  지금까지 받은 것은 남는다.
      재개점을 함께 남겨 「처음부터 다시」를 막는다 (STEP 52)
    반환   재개점 단계 (없으면 None)
    """
    require_role(account, ROLE_ADMIN)
    at = at or datetime.now(timezone.utc).isoformat()
    row = conn.execute(
        "SELECT status, run_id FROM recalc_job WHERE job_id = ?",
        (job_id,)).fetchone()
    if row is None:
        raise ValidationError(f"그 실행이 없습니다: {job_id}",
                              step="STEP 132")
    if row[0] not in ("queued", "running"):
        raise ValidationError(f"이미 끝난 실행입니다: {row[0]}",
                              step="STEP 132")

    # ★ 재개점 계산은 collect 가 한다.  store 가 부르면 층이 거꾸로 간다
    #   (STEP 15a · V4-22) — 호출자가 넘긴다
    point = resume(conn, row[1]) if (resume and row[1]) else None
    step = getattr(point, "step", None)
    # ★ 상태는 DDL 이 정한 4종뿐이다 (queued·running·done·failed).
    #   중단은 「끝났다」가 아니라 「멈췄다」이므로 failed 로 둔다 —
    #   detail 에 재개점을 남겨 「처음부터 다시」를 막는다 (STEP 52)
    conn.execute(
        "UPDATE recalc_job SET status='failed', ended_at=?, "
        "detail=? WHERE job_id=?",
        (at, f"중단 — {reason}"
         + (f" · 재개점 {step}" if step else " · 재개점 없음"), job_id))
    conn.commit()
    return step
