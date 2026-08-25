# -*- coding: utf-8 -*-
"""RAW 저장소 (L2).  원문 무손실.  삭제 금지.

지시서   3장 STEP 33 (스키마) · 2장 STEP 18 (거부) · 5장 STEP 50a (추가만)
근거     result_* 는 버려도 된다.  raw_* 는 절대 버리지 않는다.
         재실행 시 raw_* 는 추가만 한다.  덮어쓰지 않는다.
금지     민감 정보 저장 — 인증 토큰 · 쿠키 · 세션 · Authorization.
         화이트리스트로 거른다.  블랙리스트 방식은 쓰지 않는다.
"""
from __future__ import annotations

import json
import os
import sqlite3

from contracts import FORMAT_FACET, FORMAT_JSON, EndpointSpec, FetchResult
# ★ 형식 검증은 수집 계약이다.  store 는 「저장」만 한다 (STEP 15a).
#   호출자가 검증한 결과를 넘긴다 — 아래 save_raw 의 verify 인자

# 요청 헤더 화이트리스트 (STEP 33 「무손실」의 범위).
# 여기 없는 헤더는 저장하지 않는다.  재현에 필요한 것만 남긴다.
SAFE_REQUEST_HEADERS: frozenset[str] = frozenset({"User-Agent", "Accept", "Accept-Language"})

ORIGIN_COLLECTOR = "collector"
ORIGIN_MASTER = "master_manual"
# 밖에서 받아 넣은 목록 (13장 STEP 136a).  ★ collector 와 절대 섞지 않는다
ORIGIN_IMPORT = "import"
# 브라우저가 사용자 회선으로 받은 것 (13장 STEP 136c).  ★ 서버가 받은 것이 아니다
ORIGIN_BROWSER = "browser"


# 단계 트랜잭션 중인 연결.  sqlite3.Connection 은 임의 속성을 받지 않는다
_IN_BATCH: set[int] = set()


def batch(conn: sqlite3.Connection):
    """단계 단위 트랜잭션 (STEP 33 정정).

    ★ CORE 쓰기는 행마다 커밋하지 않는다.  커밋은 fsync 라 행 수만큼 느려진다.
    안전   RAW 가 이미 저장돼 있어 중간에 죽어도 재파싱으로 복구된다
           (재처리 결정표의 parse_rule — 재수집 없음)
    금지   RAW 저장에 쓰는 것.  원문은 건별로 커밋한다 (P3)
    사용   with batch(conn): ...
    """
    from contextlib import contextmanager

    @contextmanager
    def _ctx():
        _IN_BATCH.add(id(conn))
        try:
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            _IN_BATCH.discard(id(conn))

    return _ctx()


def commit(conn: sqlite3.Connection) -> None:
    """batch 안이면 커밋하지 않는다.  밖이면 즉시 커밋한다."""
    if id(conn) not in _IN_BATCH:
        conn.commit()


def open_db(path: str, ddl_dir: str = "sql/ddl") -> sqlite3.Connection:
    """DDL 은 sql/ddl/*.sql 이 정본이다.  코드가 문서를 파싱하지 않는다 (STEP 32a)."""
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    # ★ 쓰기 성능.  RAW 무손실(P3)은 그대로다 — WAL 도 커밋되면 디스크에 있다.
    #   synchronous=NORMAL 은 OS 크래시에만 마지막 커밋을 잃는다.
    #   프로세스가 죽는 경우는 잃지 않는다 (SQLite 문서)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    for name in sorted(os.listdir(ddl_dir)):
        if name.endswith(".sql"):
            with open(os.path.join(ddl_dir, name), encoding="utf-8") as f:
                conn.executescript(f.read())
    conn.commit()
    return conn


def _safe_headers(headers: dict[str, str]) -> str:
    return json.dumps(
        {k: v for k, v in headers.items() if k in SAFE_REQUEST_HEADERS},
        ensure_ascii=False,
    )


def save_raw(
    conn: sqlite3.Connection,
    res: FetchResult,
    spec: EndpointSpec,
    site: str,
    listing_id: str | None,
    request_url: str,
    request_headers: dict[str, str],
    verify,
    reason,
    origin: str = ORIGIN_COLLECTOR,
    run_id: str | None = None,
) -> str:
    """형식 검증을 통과하면 raw_response, 아니면 raw_response_reject 로 보낸다.

    verify   (res, spec) -> bool   형식 검증.  ★ 수집 계약이라 주입받는다
    reason   (res, spec) -> str    거부 사유
    반환   'stored' · 'rejected'
    금지   거부분을 조용히 버리는 것.  쌓이면 그 자체가 URL 변경 신호다 (STEP 33)
    근거   store 는 「저장」만 한다.  검증을 import 하면 층이 거꾸로 간다 (STEP 15a)
    """
    body = None if res.raw is None else json.dumps(res.raw, ensure_ascii=False)
    at = res.fetched_at.isoformat()

    if not verify(res, spec):
        conn.execute(
            "INSERT INTO raw_response_reject"
            "(site,listing_id,endpoint,request_url,http_code,body,reject_reason,fetched_at)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (site, listing_id, res.kind, request_url, res.http_code, body,
             (reason(res, spec) if reason else None), at),
        )
        conn.commit()
        return "rejected"

    conn.execute(
        "INSERT INTO raw_response"
        "(run_id,site,listing_id,source_id,endpoint,request_url,request_meta,"
        "http_code,"
        " response_meta,status,body,origin,fetched_at)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (run_id, site, listing_id, res.source_id, res.kind, request_url,
         _safe_headers(request_headers), res.http_code, None, res.status,
         body, origin, at),
    )
    conn.commit()
    return "stored"


def save_site_raw(
    conn: sqlite3.Connection,
    site: str,
    endpoint: str,
    source_id: str | None,
    request_url: str,
    body: str | None,
    fetched_at: str,
    http_code: int = 200,
    listing_id: int | None = None,
    run_id: str | None = None,
) -> str:
    """★★ 사이트 수집기가 ★ 받은 원문을 ★ 그대로 남긴다 (명령서 3-2 필수).

    ★★ 명령서 — 「★ `raw_response` 에는 남긴다 — ★ 갈래를 넓히시면 ★ 다시 판다.
      ★ ★ 다시 받을 일이 없다.  ★ 그것이 ★ 「보관만 한다」는 뜻이다」
    ★★ ★ 왜 `save_raw` 를 안 쓰나 — ★ 그것은 ★ 엔카의 수집 계약(`EndpointSpec` ·
      `FetchResult` · `verify`)에 맞춰 있다.  ★ 사이트 도구는 ★ 몸통 글자만 든다.
      ★ ★ 껍데기를 지어 맞추면 ★ 「검증했다」는 거짓말이 된다 — ★ 여기서는 ★ 안 한다
    ★★ ★ 못 받은 것은 ★ 부르지 않는다 — ★ `body` 가 없으면 ★ 아무것도 안 넣는다.
      ★ ★ 「없음」으로 저장하지 않는다 (금지 12 · 개정 289)
    ★ 같은 원문을 두 번 넣지 않는다 — ★ 같은 자리(site·endpoint·source_id)에
      ★ 이미 있으면 ★ 건너뛴다.  ★ 회차를 나눠 받으므로 ★ 다시 부를 수 있다
    돌려줌  'stored' · 'skipped'(몸통이 없다) · 'dup'(이미 있다)
    """
    if body is None or body == "":
        return "skipped"
    if source_id is not None and conn.execute(
        "SELECT 1 FROM raw_response WHERE site=? AND endpoint=? AND source_id=?"
        " LIMIT 1", (site, endpoint, str(source_id))
    ).fetchone():
        return "dup"
    conn.execute(
        "INSERT INTO raw_response"
        "(run_id,site,listing_id,source_id,endpoint,request_url,request_meta,"
        " http_code,response_meta,status,body,origin,fetched_at)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (run_id, site, listing_id,
         None if source_id is None else str(source_id), endpoint,
         request_url, None, http_code, None, "ok", body,
         ORIGIN_COLLECTOR, fetched_at),
    )
    return "stored"


def save_import_raw(
    conn: sqlite3.Connection,
    site: str,
    text: str,
    fmt: str,
    at: str,
    run_id: str | None = None,
    source_name: str | None = None,
    endpoint: str = "list",
) -> int:
    """반입 원문을 그대로 남긴다 (13장 STEP 136a · P3).

    ★ 사람이 넣은 것도 우리가 받은 것이다.  글자 하나 고치지 않고 넣는다.
      가공한 결과(core_listing)만 남기면 「무엇을 받았나」를 되짚을 수 없다
    ★ request_url 은 NULL 이다.  없는 URL 을 지어내면 수집분처럼 보인다
      site_raw=false 가 「사이트 원문이 아니다」를 말한다 (STEP 136a ②)
    금지   origin 을 'collector' 로 넣는 것 — 「우리가 받았다」가 된다
    반환   raw_response.id
    """
    meta = json.dumps({"format": fmt, "site_raw": fmt == FORMAT_JSON,
                       "source_name": source_name}, ensure_ascii=False)
    cur = conn.execute(
        "INSERT INTO raw_response"
        "(run_id,site,listing_id,source_id,endpoint,request_url,request_meta,"
        " http_code,response_meta,status,body,origin,fetched_at)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (run_id, site, None, None, endpoint, None, None,
         None, meta, "ok", text, ORIGIN_IMPORT, at),
    )
    conn.commit()
    return cur.lastrowid


def save_browser_raw(
    conn: sqlite3.Connection,
    site: str,
    text: str,
    endpoint: str,
    request_url: str,
    at: str,
    http_code: int | None = None,
    run_id: str | None = None,
    chunked: bool = False,
) -> int:
    """브라우저가 받아 온 원문 (13장 STEP 136c).

    ★ 사이트가 실제로 준 응답이다 — 반입과 다르다.  URL 도 있다
    ★ 서버가 이 응답을 다시 검증하려고 엔카를 부르지 않는다.  막혀 있다
    ★ chunked 는 「여러 POST 를 이어붙였다」다 (개정 307).
      한 번에 보낸 것이 아니라는 사실을 남긴다 — V11-47 이 그것으로 가른다
    금지   origin 을 'collector' 로 넣는 것 — 서버가 받은 것이 아니다
    반환   raw_response.id
    """
    meta = json.dumps({"fetched_by": "browser", "http_code": http_code,
                       "transfer": "chunked" if chunked else "single"},
                      ensure_ascii=False)
    cur = conn.execute(
        "INSERT INTO raw_response"
        "(run_id,site,listing_id,source_id,endpoint,request_url,request_meta,"
        " http_code,response_meta,status,body,origin,fetched_at)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (run_id, site, None, None, endpoint, request_url, None,
         http_code, meta, "ok", text, ORIGIN_BROWSER, at),
    )
    conn.commit()
    return cur.lastrowid


def save_browser_facet(
    conn: sqlite3.Connection,
    site: str,
    target_key: str,
    text: str,
    request_url: str,
    at: str,
    axis_count: int | None = None,
    http_code: int | None = None,
    run_id: str | None = None,
    chunked: bool = False,
) -> int:
    """브라우저가 받아 온 facet.  S3 이 읽는 자리에도 넣는다 (STEP 136c)."""
    conn.execute(
        "INSERT INTO raw_facet"
        "(site,target_key,request_kind,request_url,axis_count,body,fetched_at)"
        " VALUES (?,?,?,?,?,?,?)",
        (site, target_key, "unspecified", request_url, axis_count, text, at),
    )
    rid = save_browser_raw(conn, site, text, "facet", request_url, at,
                           http_code=http_code, run_id=run_id,
                           chunked=chunked)
    conn.commit()
    return rid


def save_import_facet(
    conn: sqlite3.Connection,
    site: str,
    target_key: str,
    text: str,
    at: str,
    axis_count: int | None = None,
    run_id: str | None = None,
    source_name: str | None = None,
) -> int:
    """반입한 facet 원문 (13장 STEP 136a ④ · 개정 260).

    ★ 두 자리에 넣는다 — 뜻이 다르다.
      raw_facet     S3(build_dict)가 사전을 만들 때 읽는 자리
      raw_response  「누가 어디서 받아 왔나」를 남기는 자리 (origin='import')
    ★ raw_facet.request_url 을 NULL 로 둔다.  URL 이 있으면 우리가 부른 것이다
    반환   raw_response.id
    """
    conn.execute(
        "INSERT INTO raw_facet"
        "(site,target_key,request_kind,request_url,axis_count,body,fetched_at)"
        " VALUES (?,?,?,?,?,?,?)",
        (site, target_key, "unspecified", None, axis_count, text, at),
    )
    rid = save_import_raw(conn, site, text, FORMAT_FACET, at, run_id=run_id,
                          source_name=source_name, endpoint="facet")
    conn.commit()
    return rid


def save_facet(
    conn: sqlite3.Connection,
    res: FetchResult,
    site: str,
    target_key: str,
    request_kind: str,
    request_url: str,
    axis_count: int | None,
) -> None:
    """응답 원문 전량을 저장한다.  축을 골라 저장하지 않는다 (STEP 23).

    request_kind 가 PK 에 있어야 미지정 응답과 Badge 응답을 분간할 수 있다.
    """
    conn.execute(
        "INSERT INTO raw_facet"
        "(site,target_key,request_kind,request_url,axis_count,body,fetched_at)"
        " VALUES (?,?,?,?,?,?,?)",
        (site, target_key, request_kind, request_url, axis_count,
         json.dumps(res.raw, ensure_ascii=False), res.fetched_at.isoformat()),
    )
    conn.commit()
