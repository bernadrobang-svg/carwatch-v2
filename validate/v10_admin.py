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
    "V10-33": Check("V10", "V10-33", "컴파일 실패가 PolicyError 로 안 감",
                    FATAL, "run",
                    "마스터 실측 — 「조회」를 눌렀는데 「아직 저장할 수 "
                    "없습니다」가 떴다.  컬럼 이름 하나 틀린 것에 「개발 "
                    "요청으로 낸다」가 붙었다.  ★ 컴파일 실패는 정책 위반이 "
                    "아니라 사용자 오타다 (개정 391)",
                    KIND_CODE),
    "V10-34": Check("V10", "V10-34", "거부 응답에 고칠 재료가 있음",
                    FATAL, "run",
                    "고치라 하면서 무엇으로 고치는지를 안 주면 같은 잘못이다 "
                    "(개정 367).  그 표의 실제 컬럼 목록을 낸다 (개정 391)",
                    KIND_CODE),
    "V10-35": Check("V10", "V10-35", "query_log 가 compile · policy 로 갈림",
                    FATAL, "run",
                    "오타와 정책 위반을 같은 자리에 쌓으면 거부 통계가 "
                    "오염된다 (개정 391)",
                    KIND_CODE),
    "V10-36": Check("V10", "V10-36", "표를 누르면 컬럼이 보임", FATAL, "run",
                    "화면이 컬럼을 안 보여 주니 마스터가 칠 수밖에 없었다. "
                    "created_at 은 표마다 있고 없다 (개정 391)",
                    KIND_CODE),
    "V10-37": Check("V10", "V10-37", "결과 표 위에 복사 단추가 있음",
                    FATAL, "run",
                    "마스터가 결과를 다른 곳에 옮겨 보신다 (개정 358 "
                    "「내가 보려고 만든 창」). ★ 붙여넣어 바로 쓸 수 있는 "
                    "형태여야 한다 — 탭 구분 (개정 401)",
                    KIND_CODE),
    "V10-26": Check("V10", "V10-26", "목록 저장 후 큐에 작업이 들어감",
                    FATAL, "run",
                    "마스터가 「이어서 해라」를 말하지 않아도 되게 한다 "
                    "(STEP 136g)",
                    KIND_CODE),
    "V10-27": Check("V10", "V10-27", "중간 실패에서 다음 단계로 안 넘어감",
                    FATAL, "run",
                    "상세가 반만 왔는데 판정하면 등급이 틀린다 (STEP 136g)",
                    KIND_CODE),
    "V10-28": Check("V10", "V10-28", "타이머가 겹쳐 돌지 않음",
                    FATAL, "run",
                    "겹쳐 돌면 원문이 꼬인다.  이미 도는 것이 있으면 "
                    "건너뛴다 (STEP 136h)",
                    KIND_CODE),
    "V10-29": Check("V10", "V10-29", "목록 저장이 전건 재수집을 안 부름",
                    FATAL, "run",
                    "3,470건 × 9종 = 3만 호출이다.  매일 할 일이 아니다. "
                    "상세는 새로 뜬 것 · 가격이 바뀐 것만 (개정 315)",
                    KIND_CODE),
    "V10-30": Check("V10", "V10-30", "재판정이 수집 없이 돎",
                    FATAL, "run",
                    "배점을 고쳤으면 ③ 재판정만 돈다.  다시 안 받는다 "
                    "— 그것을 몰라서 매번 다시 받으면 하루가 간다 (개정 315)",
                    KIND_CODE),
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


def _query_error_checks(conn, rid):
    """V10-33 ~ V10-36 — 쿼리 오류 분류 (개정 391).

    마스터 실측 — 「조회」를 눌렀는데 「아직 저장할 수 없습니다」가 떴다.
    컬럼 이름 하나 틀린 것에 「개발 요청으로 낸다 (STEP 137)」이 붙었다
    ★ 컴파일 실패는 정책 위반이 아니다.  사용자 오타다
    """
    import sqlite3 as _s

    from contracts import ROLE_ADMIN, Account
    from errors import PolicyError, ValidationError
    from store.adminops import KIND_COMPILE, KIND_POLICY, run_query

    probe = _s.connect(":memory:")
    conn.backup(probe)
    acc = Account(1, ROLE_ADMIN, "마스터")
    bad33, bad34, bad35 = [], [], []
    # (쿼리, 기대 예외, 기대 갈래)
    # ★ 규격의 표 그대로 (개정 391 §2-2)
    #   오타 · SELECT 아님 · 여러 문장  → ValidationError · STEP 137 안 붙음
    #   쓰기 연산 · PII 조회            → PolicyError    · STEP 137 붙음
    cases = (
        ("SELECT created_at FROM raw_response LIMIT 1",
         ValidationError, KIND_COMPILE),
        ("SELECT 1; SELECT 2", ValidationError, KIND_COMPILE),
        ("DELETE FROM core_listing", PolicyError, KIND_POLICY),
        ("SELECT * FROM core_pii LIMIT 1", PolicyError, KIND_POLICY),
    )
    for sql, want, kind in cases:
        try:
            run_query(probe, acc, sql)
            bad33.append(f"거부돼야 하는데 통과한다: {sql[:40]}")
            continue
        except (PolicyError, ValidationError) as e:
            got = e
        if not isinstance(got, want):
            bad33.append(f"{sql[:34]} → {type(got).__name__} "
                         f"({want.__name__} 여야 한다)")
        # V10-34 — 거부 응답에 고칠 재료가 있는가
        if kind == KIND_COMPILE and not (getattr(got, "action", "") or ""):
            bad34.append(f"{sql[:34]} — 고칠 재료(컬럼 목록)가 없다")
        # ★ 오타에 「개발 요청으로 낸다」를 붙이지 않는다
        if kind == KIND_COMPILE and "STEP 137" in str(got):
            bad33.append(f"{sql[:34]} — 오타에 「개발 요청」이 붙는다")
    # V10-35 — query_log 가 갈래를 나누는가
    kinds = {r[0] for r in probe.execute(
        "SELECT reject_kind FROM query_log WHERE reject_kind IS NOT NULL")}
    if not {KIND_COMPILE, KIND_POLICY} <= kinds:
        bad35.append(f"갈래가 안 나뉜다: {sorted(kinds)}")
    probe.close()

    # V10-36 — 표를 누르면 컬럼이 보이는가
    bad36 = []
    path = os.path.join(ROOT, "outputs", "render", "admin_query.html")
    if os.path.isfile(path):
        html = open(path, encoding="utf-8").read()
        if "컬럼" not in html:
            bad36.append("쿼리 화면에 표별 컬럼이 없다")
    # V10-37 — 결과 표 위에 「그대로 복사」 (개정 401)
    import re

    bad37 = []
    tpl = os.path.join(ROOT, "web", "templates", "admin_query.html")
    if not os.path.isfile(tpl):
        bad37.append("쿼리 화면이 없다")
    else:
        html = open(tpl, encoding="utf-8").read()
        head = html.find("<h2>결과</h2>")
        table = html.find("<table", head) if head >= 0 else -1
        chunk = html[head:table] if 0 <= head < table else ""
        # ★ 「복사」라는 글자가 어딘가 있는 것으로는 안 된다.
        #   실측 — 안내 문구에 「복사」가 있어 단추를 떼도 통과했다.
        #   ★ 누를 수 있는 것이어야 한다
        if not re.search(r"<button[^>]*>[^<]*복사", chunk):
            bad37.append("결과 표 위에 복사 단추가 없다")
        # ★ 붙여넣어 바로 쓸 수 있는 형태 — 탭 구분이어야 한다
        if ".tsv" not in html and "tsv" not in chunk:
            bad37.append("탭 구분 값을 안 낸다 — 붙여넣어 바로 못 쓴다")
    from store.adminops import QueryResult

    q = QueryResult(["a", "b"], [(1, "x\ty")], 1, False, 0, "q")
    if q.tsv.splitlines()[0] != "a\tb":
        bad37.append("tsv 머리말이 탭 구분이 아니다")
    if "\t" in q.tsv.splitlines()[1].replace("1\t", "", 1):
        bad37.append("값 안의 탭을 안 치웠다 — 칸이 밀린다")
    return [
        result(C["V10-37"], rid, "복사 단추",
               "있다" if not bad37 else "없다", not bad37, bad37[:4]),
        result(C["V10-33"], rid, "갈라 던진다",
               "맞다" if not bad33 else "틀리다", not bad33, bad33[:4]),
        result(C["V10-34"], rid, "고칠 재료",
               "있다" if not bad34 else "없다", not bad34, bad34[:4]),
        result(C["V10-35"], rid, "compile · policy",
               "나뉜다" if not bad35 else "안 나뉜다", not bad35, bad35),
        result(C["V10-36"], rid, "컬럼이 보인다",
               "보인다" if not bad36 else "안 보인다", not bad36, bad36),
    ]


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
    out += _automation_checks(conn, rid)
    # 쿼리 오류 분류 (개정 391)
    out += _query_error_checks(conn, rid)
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


def _automation_checks(conn, rid):
    """V10-26~30 — 자동화 (STEP 136g · 136h · 개정 315).

    ★ 「타이머를 만들었다」와 「돌고 있다」는 다르다.  실제 기록을 본다
    """
    import json as _j
    import os as _o
    import subprocess as _sp

    # ★ 값을 그대로 쓴다.  store 를 import 하면 시험 DB 로 도는
    #   check_all 에서 경로가 갈린다
    LIST_SAVED_REASON = "listing_updated"

    root = _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__)))
    bad26, bad27, bad28, bad29, bad30 = [], [], [], [], []

    # V10-26 — 목록 저장이 큐에 넣는가.  ★ 코드와 기록을 함께 본다
    src = ""
    hook = _o.path.join(root, "store", "adminops.py")
    if _o.path.isfile(hook):
        src = open(hook, encoding="utf-8").read()
    if LIST_SAVED_REASON not in src:
        bad26.append("목록 저장이 큐에 넣는 자리가 없다 (listing_updated)")
    else:
        # ★ 「listing_updated」는 trigger 가 아니라 reason 이다.
        #   trigger 는 누가 눌렀나(manual · schedule)를 적는다
        # ★ 목록을 받은 적이 없는 DB 에서는 작업이 없는 것이 맞다 —
        #   시험 DB 로 도는 check_all 이 여기 걸렸다 (실측 08-18)
        saved = conn.execute(
            "SELECT COUNT(*) FROM raw_response WHERE endpoint='list'"
            " AND origin='browser'").fetchone()
        got = conn.execute(
            "SELECT COUNT(*) FROM recalc_job WHERE reason=?",
            (LIST_SAVED_REASON,)).fetchone()
        if saved and saved[0] and not (got and got[0]):
            bad26.append(f"목록을 {saved[0]}쪽 받아 두고도 "
                         "listing_updated 로 큐에 든 작업이 없다")

    # ★★ 「큐에 들었다」와 「이어서 돌았다」는 다르다.
    #   실측 08-18 — 큐에는 60건이 들었고 60건 전부
    #   「S5: 선행 단계 미완료: S4」로 죽어 있었다.  한 번도 성공한 적이 없다.
    #   그런데 이 검사는 「큐에 있다」만 보고 통과하고 있었다
    # ★ 「돌 수 있는가」를 본다 — 「돈 적이 있는가」가 아니다.
    #   지금 상태에서 각 사유의 첫 단계가 선행 조건을 통과하는지 실제로 묻는다
    from collect.pipeline import (
        REPROCESS_TABLE, completed_steps, precheck, web_reasons,
    )

    # ★ 큐에 들어갈 수 있는 사유만 본다.  전면 재수집(site_response_shape)은
    #   CLI 전용이고 사람이 S0 부터 돈다 — 그것까지 세면 거짓 경보가 된다
    steps_done = completed_steps(conn)
    if steps_done:
        for _reason in web_reasons():
            _plan = REPROCESS_TABLE[_reason]
            if not _plan.steps:
                continue
            _ok, _why = precheck(conn, _plan.steps[0], steps_done)
            if not _ok:
                bad26.append(f"{_reason} 를 큐에 넣어도 못 돈다 "
                             f"— {_plan.steps[0]}: {_why}")

    # V10-27 — 앞 단계가 안 끝났는데 다음으로 갔는가
    gone = conn.execute(
        "SELECT COUNT(*) FROM recalc_job WHERE status='done'"
        " AND detail LIKE '%선행 단계 미완료%'").fetchone()
    if gone and gone[0]:
        bad27.append(f"선행 단계가 안 끝났는데 done 이 된 작업 {gone[0]}건")

    # V10-28 — 타이머가 겹쳐 돌지 않는가
    if "이미 도는 작업" not in open(
            _o.path.join(root, "tools", "daily_enqueue.py"),
            encoding="utf-8").read():
        bad28.append("daily_enqueue 가 겹침을 안 본다")
    try:
        units = _sp.run(["systemctl", "list-timers", "--all"],
                        capture_output=True, text=True, check=False).stdout
        if "carwatch-daily.timer" not in units:
            bad28.append("carwatch-daily.timer 가 등록돼 있지 않다")
    except OSError:
        pass

    # V10-29 — 목록 저장이 전건 재수집을 부르는가
    with open(_o.path.join(root, "config", "endpoints.json"),
              encoding="utf-8") as f:
        eps = _j.load(f)
    if "detail_refresh_days" not in str(eps):
        bad29.append("detail_refresh_days 가 config 에 없다 — "
                     "무엇을 다시 받을지 기준이 없다")
    full = conn.execute(
        "SELECT COUNT(*) FROM recalc_job WHERE reason=?"
        " AND from_step IN ('S1','S2','S3')", (LIST_SAVED_REASON,)).fetchone()
    if full and full[0]:
        bad29.append(f"목록 저장이 전건 재수집을 부른 작업 {full[0]}건")

    # V10-30 — 재판정이 수집 없이 도는가.
    # ★ 「--only S9」로 판정만 부를 수 있어야 한다.  배점을 고쳤을 때
    #   다시 받지 않고 ③ 재판정만 돌린다 (개정 315)
    run_py = open(_o.path.join(root, "run.py"), encoding="utf-8").read()
    if "--only" not in run_py:
        bad30.append("run.py 가 --only 를 안 받는다 — 단계 하나만 못 돌린다")
    scoring = open(_o.path.join(root, "collect", "runner.py"),
                   encoding="utf-8").read()
    for step in ('"S9"', '"S10"'):
        if step not in scoring:
            bad30.append(f"판정 단계 {step} 를 따로 못 부른다")
    return [
        result(C["V10-26"], rid, 0, len(bad26), not bad26, bad26),
        result(C["V10-27"], rid, 0, len(bad27), not bad27, bad27),
        result(C["V10-28"], rid, 0, len(bad28), not bad28, bad28),
        result(C["V10-29"], rid, 0, len(bad29), not bad29, bad29),
        result(C["V10-30"], rid, 0, len(bad30), not bad30, bad30),
    ]


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
