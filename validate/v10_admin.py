# -*- coding: utf-8 -*-
"""V10 관리자 검증.

지시서   13장 STEP 139
근거     위험한 기능일수록 검증이 같은 회차에 있어야 한다.
         run_query 는 화면 없이도 완결된다 — AST 판정 · 상한 · QueryLog
금지     화면 숨김만으로 권한을 대신하는 것 (V10-02)
"""
from __future__ import annotations

import os as _os

# ★ 검사 사본을 /tmp 에 두지 않는다 — 921MB tmpfs 인데 DB 가 484MB 다.
#   실측 08-17: 「database or disk is full」로 검사가 통째로 죽었다
CHECK_TMP = _os.path.join(
    _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
    "outputs", "check-tmp")

import ast
import os

from validate.base import (
    Check, FATAL, KIND_CODE, KIND_CONTRACT, KIND_EXTERNAL, WARN,
    not_applicable, result,
)

C = {
    "V10-01": Check("V10", "V10-01", "admin 전용을 user 로 호출 시 PolicyError",
                    FATAL, "run", "그 함수 첫 줄에 require_role 을 넣는다",
                    KIND_CONTRACT),
    "V10-02": Check("V10", "V10-02", "서버 권한 검증 존재 (화면 숨김 아님)",
                    FATAL, "run", "화면 함수에 require_role 을 넣는다",
                    KIND_CONTRACT),
    "V10-03": Check("V10", "V10-03", "run_query 가 SELECT 외를 전건 거부",
                    FATAL, "run", "sql_reject_reason 의 허용 목록을 확인한다",
                    KIND_CONTRACT),
    "V10-04": Check("V10", "V10-04", "run_query 판정이 AST 기반 (정규식 아님)",
                    FATAL, "run", "정규식 판정을 제거하고 EXPLAIN 으로 본다",
                    KIND_CONTRACT),
    "V10-05": Check("V10", "V10-05", "config 변경이 ConfigChange 없이 안 일어남",
                    FATAL, "run", "파일 쓰기를 apply_config 로 모은다",
                    KIND_CONTRACT),
    "V10-06": Check("V10", "V10-06", "배점 저장 시 Σ == total_points",
                    FATAL, "run", "components 를 다시 배분한다 (STEP 128)",
                    KIND_CODE),
    "V10-07": Check("V10", "V10-07", "성분 추가가 선택 가능 목록 안에서만",
                    FATAL, "run", "STEP 129 목록에 없는 성분을 지운다",
                    KIND_CODE),
    "V10-08": Check("V10", "V10-08", "관리 도구가 core_* 를 UPDATE 하지 않음",
                    FATAL, "run", "데이터 수정은 재처리로 푼다 (STEP 50a)",
                    KIND_CONTRACT),
    "V10-09": Check("V10", "V10-09", "DevRequest 가 삭제되지 않음",
                    FATAL, "run", "DELETE 를 지우고 상태 전이로 바꾼다",
                    KIND_CONTRACT),
    "V10-10": Check("V10", "V10-10", "문서 뷰어에 편집 경로 없음",
                    FATAL, "run", "쓰기 경로를 지운다. 지시서는 세션에서 갱신된다",
                    KIND_CONTRACT),
    "V10-11": Check("V10", "V10-11", "실행 중 config 변경이 잠김",
                    FATAL, "run", "running_job() 확인을 apply_config 에 건다",
                    KIND_CODE),
    "V10-12": Check("V10", "V10-12", "배점 조정 후 0점 성분 없음",
                    WARN, "run", "스킵을 쓴다. 0점 성분과 스킵은 다르다",
                    KIND_EXTERNAL),
    "V10-13": Check("V10", "V10-13", "웹에서 전면 재수집이 큐에 안 들어감",
                    FATAL, "run", "CLI 로 실행한다 (python run.py collect --full)",
                    KIND_CONTRACT),
    "V10-14": Check("V10", "V10-14", "components.{axis}.{component} 경로 읽기·쓰기",
                    FATAL, "run", "키에 점이 있다. 경로 탐색을 고친다",
                    KIND_CODE),
    "V10-15": Check("V10", "V10-15", "저장 전 배점 합 검사",
                    FATAL, "run", "apply_config 의 값 검증을 확인한다",
                    KIND_CODE),
    "V10-16": Check("V10", "V10-16",
                    "must_change_secret 계정이 다른 화면에 접근 못 함",
                    FATAL, "run",
                    "guard 예외는 /login · /logout · /password · /static 뿐이다",
                    KIND_CONTRACT),
    "V10-17": Check("V10", "V10-17", "admin 수가 0 이 되는 변경이 거부됨",
                    FATAL, "run",
                    "마지막 관리자의 역할 변경·중지를 막는다. "
                    "0 명이면 CLI 로만 복구된다 (STEP 149n)",
                    KIND_CONTRACT),
    "V10-18": Check("V10", "V10-18",
                    "core_pii · core_dealer_pii 조회가 거부됨", FATAL, "run",
                    "바이트코드 rootpage 로 본다. 문자열 필터는 별칭·주석·"
                    "서브쿼리로 우회된다 (STEP 133 · C-2)",
                    KIND_CONTRACT),
    "V10-19": Check("V10", "V10-19",
                    "중지·비밀번호 변경 후 옛 세션이 anonymous",
                    FATAL, "run",
                    "session_account 가 disabled_at 을 본다 · "
                    "change_secret 이 다른 세션을 폐기한다 (C-3 · C-4)",
                    KIND_CONTRACT),
    "V10-22": Check("V10", "V10-22", "queued 를 소비하는 코드가 있음", FATAL,
                    "run",
                    "넣기만 하고 아무도 안 가져가면 화면이 거짓말을 한다. "
                    "두 번 갇혔다 (STEP 132a · 개정 261)",
                    KIND_CODE),
    "V10-23": Check("V10", "V10-23", "오래된 queued 가 화면에 표시됨", WARN,
                    "run",
                    "「N분째 대기 중 — 실행기가 도는지 확인하십시오」를 낸다 "
                    "(STEP 132a)",
                    KIND_CODE),
    "V10-24": Check("V10", "V10-24", "사전 확정에 사유가 남음", FATAL, "run",
                    "무엇을 왜 확정했는지가 없으면 되짚을 수 없다 "
                    "(STEP 136e · 149k)",
                    KIND_CONTRACT),
    "V10-25": Check("V10", "V10-25", "'list' 출처가 화면에 표시됨", FATAL, "run",
                    "facet 없이 목록에서 관측한 것은 전체 집합이 아니다. "
                    "화면이 그렇게 말해야 한다 (STEP 136e)",
                    KIND_CODE),
    "V10-20": Check("V10", "V10-20", "로그인 실패 상한이 config 대로 돎",
                    FATAL, "run",
                    "config.admin.login_fail_limit 를 그대로 따른다. "
                    "★ S36 (개정 359) — 마스터 지시로 지금은 0(안 잠금)이다. "
                    "검사가 「잠긴다」를 박아 두면 규격을 못 따른다. "
                    "0 이면 「안 잠긴다」가 통과다",
                    KIND_CONTRACT),
}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADMIN_ONLY = ("apply_config", "revert_config", "classify_field", "run_query",
              "fetch_api", "create_dev_request", "enqueue_recalc", "view_run")
REJECT_SAMPLES = (
    "INSERT INTO core_listing(site) VALUES ('x')",
    "UPDATE core_listing SET status='gone'",
    "DELETE FROM raw_response",
    "DROP TABLE core_listing",
    "PRAGMA foreign_keys=OFF",
    "SELECT 1; DELETE FROM raw_response",
    "-- 주석\nDELETE FROM raw_response",
    "/* c */ UPDATE account SET role='admin'",
    "CREATE TABLE x (a TEXT)",
    "ALTER TABLE account RENAME TO b",
)
ALLOW_SAMPLES = (
    "SELECT COUNT(*) FROM core_listing",
    "WITH t AS (SELECT 1 AS a) SELECT a FROM t",
    "SELECT l.listing_id FROM core_listing l JOIN result_score s "
    "ON s.listing_id=l.listing_id",
)


def _sources() -> dict[str, str]:
    out = {}
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git",
                                                "tests", "tools")]
        for f in files:
            # ★ 검사기 자신은 대상이 아니다.  거부 표본(REJECT_SAMPLES)이
            #   검사에 잡히면 검사를 만들 수 없다 — V4-13 과 같은 함정
            if f == "v10_admin.py":
                continue
            if f.endswith(".py"):
                rel = os.path.relpath(os.path.join(base, f), ROOT)
                out[rel.replace("\\", "/")] = open(
                    os.path.join(base, f), encoding="utf-8").read()
    return out


# 임시 비밀번호로도 열려야 하는 것.  ★ 늘리지 않는다 (V11-31)
MUST_CHANGE_OPEN = ("/login", "/logout", "/password", "/static/{path}")


def _admin_guard_checks(conn, rid) -> list:
    """★ 규칙을 코드가 지키는지 실제로 불러 본다."""
    from contracts import Account, ROLE_ADMIN, ROLE_USER
    from errors import PolicyError
    from web.routes import GET, ROUTES, match
    from web.server import guard

    out = []
    tmp = Account(1, ROLE_ADMIN, "임시", must_change_secret=True)
    leaked = [r.path for r in ROUTES
              if GET in r.methods and r.path not in MUST_CHANGE_OPEN
              and guard(tmp, r) is None]
    blocked = [p for p in MUST_CHANGE_OPEN
               if match(p, GET)[0] is not None
               and guard(tmp, match(p, GET)[0]) is not None]
    bad = [f"열려 있다: {p}" for p in leaked]
    bad += [f"막혀 있다: {p} — 그러면 못 바꾼다" for p in blocked]
    out.append(result(C["V10-16"], rid, 0, len(bad), not bad, bad[:10]))

    # V10-17 — 마지막 관리자를 못 내린다
    import sqlite3 as _sq
    import tempfile as _tf
    import os as _os

    from store.admin import create_account, set_disabled, set_role
    from store.raw import open_db

    root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    probe = open_db(_os.path.join(_tf.mkdtemp(), "v1017.db"),
                    _os.path.join(root, "sql", "ddl"))
    create_account(probe, "확인용", ROLE_ADMIN, "t")
    fails = []
    for fn, name in ((lambda: set_role(probe, 1, ROLE_USER, "t"), "역할 변경"),
                     (lambda: set_disabled(probe, 1, True, "t"), "중지")):
        try:
            fn()
            fails.append(f"{name}가 통과했다 — admin 0 이 된다")
        except PolicyError:
            pass
    probe.close()
    _ = _sq
    out.append(result(C["V10-17"], rid, 0, len(fails), not fails, fails))
    return out


def _sql_strings(src: str) -> list[str]:
    """주석·문서 서술은 대상이 아니다.  SQL 문자열만 본다 (V4-13 함정)."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    return [n.value for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)
            and any(k in n.value for k in ("SELECT ", "INSERT ", "UPDATE ",
                                           "DELETE ", "FROM "))]


def run(conn, ctx) -> list:
    from store.adminops import sql_reject_reason
    from errors import PolicyError

    rid = ctx.run_id
    out = []
    src = _sources()

    # V10-01 · 02 — 서버가 막는가
    bad = [fn for fn in ADMIN_ONLY
           if not any(f"def {fn}(" in s and "require_role" in s
                      for s in src.values())]
    out.append(result(C["V10-01"], rid, 0, bad or 0, not bad, bad))
    out.append(result(C["V10-02"], rid, 0, bad or 0, not bad, bad))

    # V10-03 — 거부 목록이 전건 거부되는가
    passed = [q for q in REJECT_SAMPLES if sql_reject_reason(conn, q) is None]
    blocked_ok = [q for q in ALLOW_SAMPLES if sql_reject_reason(conn, q) is not None]
    out.append(result(C["V10-03"], rid, 0, passed + blocked_ok,
                      not passed and not blocked_ok, passed + blocked_ok))

    # V10-04 — 정규식이 아니라 AST(컴파일) 로 판정하는가
    ops = "store/adminops.py"
    out.append(result(C["V10-04"], rid, "EXPLAIN",
                      "EXPLAIN" if "EXPLAIN" in src.get(ops, "") else "없음",
                      "EXPLAIN" in src.get(ops, "")))

    # V10-05 — config 쓰기가 admin.py 밖에 있는가
    bad = [f for f, s in src.items()
           if f != "store/admin.py" and "config/" in s
           and (".write(" in s or "json.dump(" in s)]
    out.append(result(C["V10-05"], rid, 0, bad or 0, not bad, bad))

    # V10-06 · 15 — 저장 전 배점 합 검사가 있는가
    has = "_validate_blob" in src.get("store/admin.py", "")
    out.append(result(C["V10-06"], rid, "검사 존재", has, has))
    out.append(result(C["V10-15"], rid, "저장 전", has, has))

    # V10-07 — 선택 가능 목록 밖 성분
    from analyze.axes import COMPONENTS

    unknown = [c for c in ctx.policy_raw["components"] if c not in COMPONENTS]
    out.append(result(C["V10-07"], rid, 0, unknown or 0, not unknown, unknown))

    # V10-08 — 관리 계층이 core_* 를 UPDATE 하는가
    bad = []
    for f in ("store/admin.py", "store/adminops.py"):
        for s in _sql_strings(src.get(f, "")):
            up = s.upper()
            if "UPDATE CORE_" in up or "DELETE FROM CORE_" in up:
                bad.append(f"{f}: {s[:40]}")
    out.append(result(C["V10-08"], rid, 0, bad or 0, not bad, bad))

    # V10-09 — DevRequest 삭제 경로
    bad = [f for f, s in src.items()
           for q in _sql_strings(s) if "DELETE FROM dev_request" in q]
    out.append(result(C["V10-09"], rid, 0, bad or 0, not bad, bad))

    # V10-10 — 문서 뷰어가 쓰지 않는가
    doc = src.get("report/screens/admin.py", "")
    bad = []
    if "def view_docs" in doc:
        seg = doc.split("def view_docs", 1)[1]
        if '"w"' in seg or ".write(" in seg or "editable=True" in seg:
            bad.append("view_docs 에 쓰기 경로")
    out.append(result(C["V10-10"], rid, 0, bad or 0, not bad, bad))

    # V10-11 — 실행 중 잠금
    has = "running_job" in src.get("store/admin.py", "")
    out.append(result(C["V10-11"], rid, "잠금 존재", has, has))

    # V10-12 — 0점 성분
    zeros = [k for k, v in ctx.policy_raw["components"].items()
             if (v["points"] if isinstance(v, dict) else v) == 0]
    out.append(result(C["V10-12"], rid, 0, zeros or 0, not zeros, zeros))

    # V10-13 — 웹 전면 재수집
    from collect.pipeline import CLI_ONLY_REASONS, check_recalc_origin

    leaked = []
    for r in CLI_ONLY_REASONS:
        try:
            check_recalc_origin(r, "web")
            leaked.append(r)
        except PolicyError:
            pass
    n = conn.execute(
        "SELECT COUNT(*) FROM recalc_job WHERE reason IN "
        f"({','.join('?' * len(CLI_ONLY_REASONS))}) AND trigger<>'manual'",
        tuple(sorted(CLI_ONLY_REASONS))).fetchone()[0]
    out.append(result(C["V10-13"], rid, 0, leaked or n, not leaked and not n,
                      leaked))

    # V10-14 — 점이 든 키 경로
    from store.admin import get_path

    probe = {"components": {"taste.hud": 15}}
    ok = get_path(probe, "components.taste.hud") == 15
    out.append(result(C["V10-14"], rid, 15,
                      get_path(probe, "components.taste.hud"), ok))
    out += _admin_guard_checks(conn, rid)
    out += _session_checks(rid)
    out.append(_pii_query_check(conn, rid))
    return out


def _session_checks(rid) -> list:
    """★ 실제로 중지·변경해 본다.  「막습니다」를 글로만 두지 않는다."""
    import os
    import tempfile
    from datetime import datetime, timezone

    from contracts import Account, ROLE_USER
    from errors import PolicyError
    from store.admin import (
        authenticate, change_secret, create_account, open_session,
        session_account, set_disabled,
    )
    from store.raw import open_db

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    conn = open_db(os.path.join(tempfile.mkdtemp(dir=_ensure_tmp()), "v1019.db"),
                   os.path.join(root, "sql", "ddl"))
    now = datetime.now(timezone.utc)
    aid, pw = create_account(conn, "검사용", ROLE_USER, now.isoformat())
    acc = Account(aid, ROLE_USER, "검사용")

    bad = []
    sid = open_session(conn, acc, now)
    set_disabled(conn, aid, True, now.isoformat())
    if session_account(conn, sid, now).role != "anonymous":
        bad.append("중지 후에도 세션이 산다")
    set_disabled(conn, aid, False, now.isoformat())

    keep, other = open_session(conn, acc, now), open_session(conn, acc, now)
    change_secret(conn, acc, "newsecret123", now.isoformat(),
                  keep_session=keep)
    if session_account(conn, other, now).role != "anonymous":
        bad.append("비밀번호 변경 후 다른 세션이 산다")
    if session_account(conn, keep, now).role == "anonymous":
        bad.append("지금 쓰는 세션까지 끊었다")
    out = [result(C["V10-19"], rid, 0, bad or 0, not bad, bad)]

    # V10-20 — 상한을 실제로 넘겨 본다
    from store.admin import _admin_cfg

    limit = int(_admin_cfg("login_fail_limit"))
    locked = False
    # ★ 0 이면 잠그지 않는 것이 규격이다 (S36 · 개정 359).
    #   그래도 몇 번 두드려 본다 — 「안 잠긴다」를 눈으로 확인한다
    for _ in range((limit or int(_admin_cfg("login_probe_tries"))) + 2):
        try:
            authenticate(conn, "검사용", "틀린비번", now)
        except PolicyError:
            locked = True
            break
    out.append(_queue_consumer_check(conn, rid))
    out.append(_queue_stale_shown_check(rid))
    out.append(_dict_reason_check(conn, rid))
    out.append(_dict_source_shown_check(rid))
    want = bool(limit)
    out.append(result(
        C["V10-20"], rid, "거부" if want else "안 잠금",
        "거부" if locked else "안 잠금", locked == want,
        [] if locked == want else
        [f"상한 {limit} 인데 {'안 잠긴다' if want else '잠긴다'}"]))
    return out


# PII 표.  ★ 조회 자체가 거부돼야 한다 (STEP 133 · C-2)
PII_TABLES = ("core_pii", "core_dealer_pii")
# 우회 시도 표본.  ★ 별칭 · 뷰 · 서브쿼리 · 주석으로도 못 뚫려야 한다
PII_PROBES = (
    "SELECT * FROM core_pii",
    "SELECT p.* FROM core_pii p",
    "SELECT * FROM core_pii /* 주석 */",
    "SELECT * FROM (SELECT * FROM core_pii)",
    "WITH x AS (SELECT * FROM core_dealer_pii) SELECT * FROM x",
    "SELECT (SELECT COUNT(*) FROM core_pii)",
)


def _pii_query_check(conn, rid):
    """V10-18 — core_pii · core_dealer_pii 조회가 거부되는가.

    ★ 문자열에서 테이블명을 찾지 않는다.  별칭 · 주석으로 우회된다.
      EXPLAIN 의 OpenRead 대상 rootpage 로 실제 열리는 표를 본다
    ★ 거부해도 query_log 에 남는다 — 무엇을 막았는지가 신호다
    """
    import os
    import sqlite3 as _sq

    from contracts import ROLE_ADMIN, Account
    from errors import PolicyError, ValidationError
    from store.adminops import run_query

    # ★ 파일을 복사하지 않는다.  아직 커밋 안 된 스키마가 사본에 안 따라온다
    #   (실측 08-15: 시험용 DB 를 복사했더니 query_log 가 없었다).
    #   sqlite backup 으로 「지금 이 연결이 보는 것」을 그대로 옮긴다
    tmp = os.path.join(_scratch(), "pii.db")
    probe = _sq.connect(tmp)
    conn.backup(probe)
    acc = Account(1, ROLE_ADMIN, "마스터")

    bad = []
    for sql in PII_PROBES:
        try:
            res = run_query(probe, acc, sql)
        except (PolicyError, ValidationError):
            continue          # 거부한 것이다 — 맞다
        except Exception as e:                               # noqa: BLE001
            bad.append(f"{sql[:32]}: {type(e).__name__} {str(e)[:30]}")
            continue
        if not getattr(res, "rejected_reason", None):
            bad.append(f"통과했다: {sql[:40]}")
    # 거부도 남는가.  ★ 표가 없으면 그건 이 검사가 볼 것이 아니다 (V2-22 가 본다)
    has_log = probe.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' "
        "AND name='query_log'").fetchone()[0]
    if has_log:
        logged = probe.execute(
            "SELECT COUNT(*) FROM query_log WHERE rejected_reason IS NOT NULL"
        ).fetchone()[0]
        if not logged:
            bad.append("거부가 query_log 에 남지 않는다")
    probe.close()
    return result(C["V10-18"], rid, 0, len(bad), not bad, bad[:6])


def _scratch() -> str:
    """검사용 임시 자리.  ★ 끝나면 지운다 — 검사가 디스크를 채우면 안 된다.

    실측 08-15: 사본 63MB 가 실행마다 쌓여 디스크가 100% 가 됐고
    그 뒤 전 시험이 한꺼번에 깨졌다
    """
    import atexit
    import shutil
    import tempfile

    path = tempfile.mkdtemp(prefix="cw-check-", dir=_ensure_tmp())
    atexit.register(shutil.rmtree, path, ignore_errors=True)
    return path


def _dict_reason_check(conn, rid):
    """V10-24 — 사전 확정에 사유가 남는가 (STEP 136e).

    ★ 「사유를 받는다」를 폼에만 두지 않는다.  남은 이력을 본다
    """
    rows = conn.execute(
        "SELECT COUNT(*), SUM(CASE WHEN reason IS NULL OR reason='' "
        "THEN 1 ELSE 0 END) FROM config_change WHERE file='dict_enum'"
    ).fetchone()
    n, blank = rows[0] or 0, rows[1] or 0
    if not n:
        return not_applicable(C["V10-24"], rid, "사전 확정 이력이 없다")
    bad = [f"사유 없는 확정 {blank}건"] if blank else []
    return result(C["V10-24"], rid, 0, blank, not bad, bad)


def _dict_source_shown_check(rid):
    """V10-25 — 'list' 출처를 화면이 말하는가 (STEP 136e)."""
    import os as _o

    tpl = _o.path.join(ROOT, "web", "templates", "admin_dict.html")
    if not _o.path.isfile(tpl):
        return result(C["V10-25"], rid, "표시", "화면이 없다", False,
                      ["admin_dict.html 이 없다"])
    html = open(tpl, encoding="utf-8").read()
    bad = []
    if "list" not in html:
        bad.append("출처를 표시하지 않는다")
    if "전체 집합" not in html:
        bad.append("「전체 집합이 아니다」를 말하지 않는다")
    return result(C["V10-25"], rid, "표시",
                  "표시" if not bad else "없음", not bad, bad)


def _queue_consumer_check(conn, rid):
    """V10-22 — 큐를 가져가는 코드가 있는가 (STEP 132a · 개정 261).

    ★ 「만들었다」를 글로 두지 않는다.  소비기가 status 를 바꾸는 코드를 보고,
      실제로 소비된 흔적(done·failed)이 있으면 그것도 함께 센다
    """
    import os as _o

    path = _o.path.join(ROOT, "collect", "worker.py")
    bad = []
    if not _o.path.isfile(path):
        bad.append("collect/worker.py 가 없다 — 큐를 가져가는 코드가 없다")
    else:
        src = open(path, encoding="utf-8").read()
        if "STATUS_QUEUED" not in src or "UPDATE recalc_job" not in src:
            bad.append("소비기가 queued 를 집지 않는다")
        if "run_recalc" not in src:
            bad.append("소비기가 파이프라인을 돌리지 않는다")
    run_py = _o.path.join(ROOT, "run.py")
    if _o.path.isfile(run_py):
        if "start_worker" not in open(run_py, encoding="utf-8").read():
            bad.append("run.py web 이 소비기를 띄우지 않는다")
    taken = conn.execute(
        "SELECT COUNT(*) FROM recalc_job WHERE status IN ('done','failed')"
    ).fetchone()[0]
    return result(C["V10-22"], rid, "있음",
                  f"소비 흔적 {taken}건", not bad, bad)


def _queue_stale_shown_check(rid):
    """V10-23 — 오래 대기한 큐를 화면이 알리는가 (STEP 132a)."""
    import os as _o

    tpl = _o.path.join(ROOT, "web", "templates", "admin_run.html")
    if not _o.path.isfile(tpl):
        return result(C["V10-23"], rid, "표시", "화면이 없다", False,
                      ["admin_run.html 이 없다"])
    html = open(tpl, encoding="utf-8").read()
    bad = []
    if "대기 중" not in html:
        bad.append("오래된 대기를 알리는 문구가 없다")
    return result(C["V10-23"], rid, "표시",
                  "표시" if not bad else "없음", not bad, bad)


def _ensure_tmp() -> str:
    """검사 사본 자리.  ★ /tmp(tmpfs)가 아니라 디스크에 둔다."""
    _os.makedirs(CHECK_TMP, exist_ok=True)
    return CHECK_TMP
