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


# ★★★ 원문을 압축해 둔다 (마스터 지시 08-28).
#
#   ★ 왜 — ★ 이 장비는 t4g.small · 램 1,841MB 인데 ★ DB 가 1.00GB 다.
#     ★ 페이지 캐시에 안 들어가서 ★ 화면이 차가울 때 10초, 더울 때 0.7초였다
#     (14배 · outputs v285).  ★ `raw_response` 가 ★ 그 DB 의 77% 다.
#   ★ 실측 08-28 — ★ 표본 400건에 ★ zlib 로 ★ 3.6배 줄었다
#
#   ★★ 규격을 어기지 않는다 — 「원문 무손실 · 삭제 금지 · 추가만」
#     (chapters/01-arch.md:17 · 13-pipeline.md:401).
#     ★ 압축은 ★ 무손실이다.  ★ 글자 하나 안 바뀐다 — ★ 되돌리면 그대로다.
#     ★ `tools/compress_raw.py` 가 ★ 옮길 때 ★ 전건을 되돌려 대조한다
#
#   ★ 어떻게 — ★ `body` 칸에 ★ 압축 바이트(BLOB)를 그대로 넣는다.
#     ★ 칸을 새로 만들지 않는다 — ★ 그래야 ★ `body IS NOT NULL` 을 쓰는
#       여섯 자리가 ★ 그대로 산다 (`store/core.py` · `validate/v0_guide.py` ·
#       `tools/fill_photos.py` · `sql/ddl/01_raw.sql` 의 부분 색인)
#     ★ 가른다 — ★ 글자(str)면 옛 꼴, ★ 바이트(BLOB)면 압축된 것이다.
#       ★ 앞에 표식을 둔다 — ★ 남의 BLOB 을 잘못 풀지 않기 위해서다
#     ★ 섞여 있어도 된다 — ★ 옮기는 중에도 읽는 쪽이 안 깨진다
#
#   ★ 읽는 자리는 ★ 전부 `raw_body()` 를 거친다.  ★ 안 거치면 bytes 가 그대로
#     나와 ★ `json.loads` 가 죽는다 — ★ 조용히 틀리지 않고 ★ 곧바로 터진다.
#     ★ 그것이 낫다 (선언과 실제의 괴리를 막는 것이 이 프로젝트의 목표다)
BODY_MAGIC = b"CWZ1"


def _compress_cfg(key: str, fallback):
    """압축 설정.  ★ 정본은 `config/web.json` 이다 (S14)."""
    try:
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(here, "config", "web.json"),
                  encoding="utf-8") as f:
            return json.load(f)[key]
    except (OSError, ValueError, KeyError, TypeError):
        return fallback


def pack_body(text):
    """저장할 꼴로 만든다.  ★ None 은 None 이다.

    ★ 작은 것은 안 줄인다 — ★ 압축 머리글이 도리어 커진다.
      ★ 경계는 `config/web.json` 의 `raw_body_compress_min_bytes` 다
    """
    if text is None:
        return None
    if not isinstance(text, str):
        return text                       # 이미 바이트다.  손대지 않는다
    data = text.encode("utf-8")
    if not _compress_cfg("raw_body_compress", True):
        return text
    if len(data) < int(_compress_cfg("raw_body_compress_min_bytes", 1024)):
        return text
    import zlib

    return BODY_MAGIC + zlib.compress(
        data, int(_compress_cfg("raw_body_compress_level", 6)))


def raw_body(value):
    """저장된 body 를 ★ 원문 글자로 되돌린다.

    ★★ `raw_response.body` 를 읽는 자리는 ★ 전부 이것을 거친다.
    ★ 옛 행(글자)은 그대로 돌려준다 — ★ 섞여 있어도 된다
    """
    if isinstance(value, (bytes, bytearray, memoryview)):
        raw = bytes(value)
        if raw.startswith(BODY_MAGIC):
            import zlib

            return zlib.decompress(raw[len(BODY_MAGIC):]).decode("utf-8")
        # ★ 우리가 압축한 것이 아니다.  ★ 지어내지 않고 글자로만 돌린다
        return raw.decode("utf-8")
    return value


# 단계 트랜잭션 중인 연결.  sqlite3.Connection 은 임의 속성을 받지 않는다
_IN_BATCH: set[int] = set()
# ★ batch 안에서 ★ 몇 줄 썼나 — ★ 잠금 창을 자르는 셈이다 (08-26)
_BATCH_ROWS: dict[int, int] = {}
# ★ tick 이 마지막으로 끊은 행 번호 (08-26)
_BATCH_TICK: dict[int, int] = {}


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
        _BATCH_ROWS[id(conn)] = 0
        _BATCH_TICK[id(conn)] = 0
        try:
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            _IN_BATCH.discard(id(conn))
            _BATCH_ROWS.pop(id(conn), None)
            _BATCH_TICK.pop(id(conn), None)

    return _ctx()


def tick(conn: sqlite3.Connection, rows: int) -> None:
    """★★ batch 안에서 ★ **처리한 행 수**로 ★ 잠금 창을 끊는다 (08-26).

    ★★★ `commit()` 만으로는 모자랐다.  ★ 그것은 ★ **쓴 행**에서만 불린다 —
      ★ ★ 다시 파싱해 ★ 바뀐 것이 없으면 ★ `upsert_core` 가 ★ 일찍 돌아가고
      ★ ★ `commit()` 이 ★ 안 불린다.  ★ 그런데 ★ 앞서 쓴 것 때문에
      ★ ★ **트랜잭션은 열려 있고** ★ 쓰기 잠금은 ★ 그대로 잡혀 있다.
    ★ 실측 08-26 — ★ 볼보 137건을 받은 뒤 S6 이 도는 동안
      ★ ★ 쓰기가 ★ **0/6** 이었다 (8초씩 기다리고 다 실패).
      ★ ★ 그 바람에 ★ 리본카 수집기가 ★ 「database is locked」로 죽었다.
    ★ 그래서 ★ 진행 표시 자리에서 ★ 이것을 부른다 — ★ 몇 행을 처리했든 끊긴다.
    ★ ★ `commit()` 과 ★ 같은 셈을 쓴다 — ★ 쓴 행이든 지나간 행이든 ★ 한 칸이다.
    ★ batch 밖이면 ★ 아무것도 안 한다 (이미 건별 커밋이다)
    """
    if id(conn) not in _IN_BATCH:
        return
    every = _batch_commit_rows()
    if not every:
        return
    # ★ `rows` 는 ★ 「지금 몇 행째인가」다.  ★ 그 행수마다 한 번 끊는다.
    #   ★ 진행 표시가 20행마다 부르므로 ★ 셈으로 세면 200이 4,000행이 된다 —
    #   ★ ★ 그러면 ★ 창이 10초에 한 번밖에 안 열린다 (실측 08-26: 8초 대기가 다 실패)
    last = _BATCH_TICK.get(id(conn), 0)
    if int(rows) - last >= every:
        _BATCH_TICK[id(conn)] = int(rows)
        conn.commit()


def commit(conn: sqlite3.Connection) -> None:
    """batch 밖이면 즉시 커밋한다.  ★ 안이면 ★ 정해진 행수마다 한 번 커밋한다.

    ★★★ 08-26 — ★ 전에는 ★ batch 안에서 ★ **아무것도 안 했다.**  ★ 그래서
      ★ S6(130,040행) 같은 단계가 ★ 쓰기 잠금을 ★ 몇 분씩 쥐었고
      ★ ★ 그동안 ★ `POST /login` 이 ★ 500 이었다 — ★ 마스터께서 담아 두신 차를
      ★ 못 보셨다 (명령서 74장 ② · 08-26 지시 ②).
    ★★ ★ `busy_timeout` 만으로는 ★ 안 됐다 — ★ 30초를 기다려도 ★ 여전히 잠겨 있었다.
      ★ ★ 떼어내도(③) 안 낫는다 — ★ SQLite 는 ★ **파일**을 잠근다.
    ★ 그래서 ★ 잠금 창을 ★ 잘라 낸다.  ★ 행마다 커밋하던 옛 결함으로는 안 돌아간다
      (★ 커밋은 fsync 라 행 수만큼 느려진다 — ★ 그것이 batch 를 만든 까닭이다).
    ★ 안전 — ★ 원문(RAW)이 이미 있어 ★ 중간에 죽어도 ★ 재파싱으로 복구된다.
      ★ ★ 다만 ★ 되돌리기(rollback)가 ★ 마지막 커밋까지만 간다 — ★ 가이드께 알린다
    ★ 행수의 정본은 `config/web.json` 의 `db_batch_commit_rows` 다 (S14).  ★ 0 이면 안 자른다
    """
    if id(conn) not in _IN_BATCH:
        conn.commit()
        return
    every = _batch_commit_rows()
    if not every:
        return
    _BATCH_ROWS[id(conn)] = _BATCH_ROWS.get(id(conn), 0) + 1
    if _BATCH_ROWS[id(conn)] >= every:
        _BATCH_ROWS[id(conn)] = 0
        conn.commit()


def _batch_commit_rows() -> int:
    """batch 안에서 ★ 몇 줄마다 커밋하나.  ★ 정본은 `config/web.json` 이다 (S14)."""
    try:
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(here, "config", "web.json"), encoding="utf-8") as f:
            return int(json.load(f)["db_batch_commit_rows"])
    except (OSError, ValueError, KeyError, TypeError):
        return 2000


def _busy_timeout_ms() -> int:
    """잠금을 기다리는 시간 (ms).  ★ 정본은 `config/web.json` 이다 (S14)."""
    try:
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(here, "config", "web.json"), encoding="utf-8") as f:
            return int(json.load(f)["db_busy_timeout_ms"])
    except (OSError, ValueError, KeyError, TypeError):
        # ★ config 를 못 읽어도 ★ 0 으로 두지 않는다 — ★ 0 이 이번 결함의 값이었다
        return 30000


def connect_db(path: str) -> sqlite3.Connection:
    """DB 를 연다 — ★ **PRAGMA 까지 붙여서**.  DDL 은 안 돌린다.

    ★★★ 08-29 — ★ `collect/worker.py` 가 ★ `sqlite3.connect` 를 맨으로 불렀다.
      ★ 그래서 ★ `busy_timeout` 이 ★ 기본 0 이었다 — ★ 잠금을 만나면
      ★ ★ 기다리지 않고 ★ 그 자리에서 죽는다.  ★ `open_db` 를 쓰면 되지만
      ★ ★ 그것은 ★ 부를 때마다 ★ `sql/ddl/*.sql` 을 ★ 전부 다시 돌린다 —
      ★ ★ 몇 초마다 도는 폴링 자리에는 ★ 무겁다.
    ★ 그래서 ★ 여는 규칙만 여기 모은다 — ★ `open_db` 도 이것을 쓴다.
    금지   `sqlite3.connect` 를 맨으로 부르는 것 (S46-124)
    """
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    # ★★★ 잠금을 만나면 ★ 곧바로 죽지 않고 ★ 기다린다 (08-26).
    #   ★ SQLite 기본값은 ★ 0 이다 — ★ 한 번 부딪히면 ★ 그 자리에서 실패한다.
    #   ★ 실측 08-26 — ★ 파이프라인이 웹과 같은 프로세스에서 돌며 쓰기를 쥐자
    #     ★ `POST /login` 이 ★ 500 이 됐다 (auth_login_attempt INSERT 가 막혔다).
    #     ★ 읽기는 WAL 이라 200 이었다 — ★ 쓰기만 골라 죽었다.
    #   ★ 값의 정본은 `config/web.json` 의 `db_busy_timeout_ms` 다 (S14)
    conn.execute(f"PRAGMA busy_timeout = {_busy_timeout_ms()}")
    # ★ 쓰기 성능.  RAW 무손실(P3)은 그대로다 — WAL 도 커밋되면 디스크에 있다.
    #   synchronous=NORMAL 은 OS 크래시에만 마지막 커밋을 잃는다.
    #   프로세스가 죽는 경우는 잃지 않는다 (SQLite 문서)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def open_db(path: str, ddl_dir: str = "sql/ddl") -> sqlite3.Connection:
    """DDL 은 sql/ddl/*.sql 이 정본이다.  코드가 문서를 파싱하지 않는다 (STEP 32a)."""
    conn = connect_db(path)
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
         pack_body(body), origin, at),
    )
    conn.commit()
    return "stored"


# ★★★ 사이트 도구 한 번의 실행에 ★ 이름을 준다 (`V1-19` · A-10).
#   ★★ 08-27 실측 — ★ `save_site_raw` 가 ★ `run_id` 를 ★ NULL 로 넣고 있었다.
#     ★ ★ `V1-19` 가 ★ 159건으로 잡았다 — 「★ run_id 가 없으면 ★ 어느 실행이
#       ★ 넣은 원문인지 ★ 못 되짚는다」.  ★ 내 결함이다
#   ★ 꼴은 ★ `run.py:59` 와 같다 (`%Y%m%dT%H%M%S`) — ★ 두 꼴을 만들지 않는다
#   ★ 한 프로세스에 하나다 — ★ 한 번 부른 것이 ★ 한 실행이다
_PROC_RUN_ID: str | None = None


def proc_run_id() -> str:
    """★ 이 프로세스의 실행 이름.  ★ 처음 부를 때 정해 ★ 끝까지 같다."""
    global _PROC_RUN_ID

    if _PROC_RUN_ID is None:
        from datetime import datetime, timezone
        _PROC_RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    return _PROC_RUN_ID


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
    # ★★ 둘 다 둔다 (마스터 지시 08-26 · 검사 `S46-97`).
    #   ★ 잇는 정본은 `source_id`(사이트 매물번호)다.  ★ `listing_id`(우리 번호)는
    #   ★ 지우지 않고 ★ 아는 자리에서 함께 채운다 — ★ 주소에서 되뽑지 않는다.
    #   ★ 아직 매물이 안 만들어졌으면 NULL 이 맞다 (뒤에 S46-97 이 메운다)
    if listing_id is None and source_id is not None:
        row = conn.execute(
            "SELECT listing_id FROM core_listing WHERE site=? AND source_id=?",
            (site, str(source_id))).fetchone()
        if row:
            listing_id = row[0]
    conn.execute(
        "INSERT INTO raw_response"
        "(run_id,site,listing_id,source_id,endpoint,request_url,request_meta,"
        " http_code,response_meta,status,body,origin,fetched_at)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (run_id or proc_run_id(), site, listing_id,
         None if source_id is None else str(source_id), endpoint,
         request_url, None, http_code, None, "ok", pack_body(body),
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
         None, meta, "ok", pack_body(text), ORIGIN_IMPORT, at),
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
    # ★★ `bytes` — ★ 브라우저가 ★ 한 번에 보낸 ★ 원문 바이트 수 (V11-47).
    #   ★ 전에는 검사가 `LENGTH(body)` 로 쟀는데 ★ body 를 압축하면서
    #     ★ 그것이 ★ 「압축된 크기」가 되어 ★ 상한 검사가 조용히 통과하게 된다.
    #   ★ 그래서 ★ 잰 값을 ★ 여기 남긴다 — ★ 이쪽이 뜻도 더 곧다
    #     (「보낸 크기」이지 「저장된 크기」가 아니다)
    meta = json.dumps({"fetched_by": "browser", "http_code": http_code,
                       "transfer": "chunked" if chunked else "single",
                       "bytes": len(text.encode("utf-8"))},
                      ensure_ascii=False)
    cur = conn.execute(
        "INSERT INTO raw_response"
        "(run_id,site,listing_id,source_id,endpoint,request_url,request_meta,"
        " http_code,response_meta,status,body,origin,fetched_at)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (run_id, site, None, None, endpoint, request_url, None,
         http_code, meta, "ok", pack_body(text), ORIGIN_BROWSER, at),
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
