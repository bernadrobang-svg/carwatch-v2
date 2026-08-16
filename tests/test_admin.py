# -*- coding: utf-8 -*-
"""13장 앞부분 시험 — 계정 · 권한 · config 변경.

지시서   STEP 126 (권한 3단 · 부트스트랩) · STEP 127 (config 변경과 이력)
사용     python3 tests/test_admin.py
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from errors import PolicyError, ValidationError  # noqa: E402
from contracts import (  # noqa: E402
    ANONYMOUS, ROLE_ADMIN, ROLE_USER, Account, require_role,
)
from store.admin import (  # noqa: E402
    apply_config, authenticate, change_secret, create_account, history,
    needs_bootstrap, open_session, revert_config, session_account,
)
from store.raw import open_db  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _spec_menu_paths() -> set:
    """13장 메뉴 표(STEP 138)의 경로 집합.  ★ 규격이 정본이다."""
    import re as _re

    path = os.path.join(ROOT, "docs", "chapters", "60-admin", "c-tools.md")
    with open(path, encoding="utf-8") as f:
        body = f.read()
    # | 분류 | `/admin/...` | 내용 | STEP |
    return set(_re.findall(r"^\|[^|\n]*\|\s*`(/admin[^`]*)`\s*\|", body,
                           _re.M))
NOW = datetime(2026, 8, 10, tzinfo=timezone.utc)
T1 = NOW.isoformat()
FAIL: list[str] = []


def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{'  ' + detail if detail else ''}")
    if not ok:
        FAIL.append(name)


def setup():
    """config 를 복사한 임시 작업본.  실제 파일을 건드리지 않는다."""
    d = tempfile.mkdtemp()
    shutil.copytree(os.path.join(ROOT, "config"), os.path.join(d, "config"))
    conn = open_db(os.path.join(d, "t.db"), os.path.join(ROOT, "sql", "ddl"))
    return conn, d


# ── STEP 126 부트스트랩 ──────────────────────────────────────────────
from validate.v10_admin import C as V10_CHECKS  # noqa: E402


def test_bootstrap() -> None:
    conn, _d = setup()
    check("★ account 가 비면 초기화 필요 (웹은 다른 화면으로 못 간다)",
          needs_bootstrap(conn))

    aid, temp = create_account(conn, "마스터", ROLE_ADMIN, T1)
    check("CLI 로 최초 관리자를 만든다", isinstance(aid, int) and len(temp) > 8)
    check("초기화 완료", not needs_bootstrap(conn))

    stored = conn.execute("SELECT secret_hash, must_change_secret "
                          "FROM account").fetchone()
    check("★ 임시 비밀번호를 저장하지 않는다 (해시만)", temp not in stored[0])
    check("첫 로그인 시 변경 강제", stored[1] == 1)

    src = open(os.path.join(ROOT, "store", "admin.py"), encoding="utf-8").read()
    cfg = open(os.path.join(ROOT, "config", "scoring.json"),
               encoding="utf-8").read()
    # ★ 「값」을 두는 것이 금지다.  min_secret_length 같은 정책 키는 괜찮다
    import json as _j
    import re as _re

    values = _j.dumps(_j.loads(cfg), ensure_ascii=False)
    leaked = [m.group(0) for m in _re.finditer(
        r'"(?:[\w.]*(?:password|secret|passwd)[\w.]*)"\s*:\s*"[^"]+"',
        values)]
    check("★ 기본 비밀번호를 코드·config 에 두지 않는다",
          not leaked and 'secret = "' not in src, str(leaked[:2]))


# ── STEP 126 권한 ────────────────────────────────────────────────────
def test_auth() -> None:
    conn, _d = setup()
    _aid, temp = create_account(conn, "마스터", ROLE_ADMIN, T1)
    _uid, utemp = create_account(conn, "사용자", ROLE_USER, T1)

    admin = authenticate(conn, "마스터", temp)
    check("로그인 성공", admin.role == ROLE_ADMIN)
    check("★ 로그인 실패도 anonymous — 예외가 아니다",
          authenticate(conn, "마스터", "틀림").role == "anonymous")
    check("없는 계정도 anonymous",
          authenticate(conn, "없음", "x").role == "anonymous")
    check("★ anonymous 는 행이 아니다 (account_id 없음)",
          ANONYMOUS.account_id is None)

    user = authenticate(conn, "사용자", utemp)
    require_role(admin, ROLE_ADMIN)
    require_role(user, ROLE_USER)
    check("관리자는 user 권한도 만족", True)
    for who, role in ((user, ROLE_ADMIN), (ANONYMOUS, ROLE_USER)):
        try:
            require_role(who, role)
            check(f"★ {who.role} → {role} 차단", False)
        except PolicyError:
            check(f"★ {who.role} → {role} 차단", True)

    sid = open_session(conn, admin, NOW)
    check("세션으로 계정을 되찾는다",
          session_account(conn, sid, NOW).account_id == admin.account_id)
    check("만료 세션은 anonymous",
          session_account(conn, sid, NOW + timedelta(hours=13)).role
          == "anonymous")
    check("세션 없으면 anonymous",
          session_account(conn, None, NOW).role == "anonymous")

    change_secret(conn, admin, "새비밀번호")
    check("비밀번호 변경 후 강제 플래그 해제",
          not authenticate(conn, "마스터", "새비밀번호").must_change_secret)
    check("옛 비밀번호는 안 통한다",
          authenticate(conn, "마스터", temp).role == "anonymous")


# ── STEP 127 config 변경 ─────────────────────────────────────────────
def test_apply_config() -> None:
    conn, d = setup()
    _aid, temp = create_account(conn, "마스터", ROLE_ADMIN, T1)
    admin = authenticate(conn, "마스터", temp)
    user = Account(9, ROLE_USER, "사용자")

    path = os.path.join(d, "config", "scoring.json")
    before = json.load(open(path, encoding="utf-8"))["report"]["top_n"]

    ch = apply_config(conn, admin, "scoring.json", "report.top_n", 10,
                      "상위 10건으로", root=d, at=T1)
    after = json.load(open(path, encoding="utf-8"))["report"]["top_n"]
    check("파일이 갱신된다", after == 10, str(after))
    check("★ 변경 전 값을 before 에 남긴다", json.loads(ch.before) == before)
    check("사유를 받는다", ch.reason == "상위 10건으로")
    check("이력 1행", len(history(conn)) == 1)

    try:
        apply_config(conn, user, "scoring.json", "report.top_n", 3, None,
                     root=d, at=T1)
        check("★ 관리자가 아니면 차단 (화면 숨김이 아니라 서버가 막는다)", False)
    except PolicyError:
        check("★ 관리자가 아니면 차단 (화면 숨김이 아니라 서버가 막는다)", True)

    for key in ("report.없는키", "없는블록.x"):
        try:
            apply_config(conn, admin, "scoring.json", key, 1, None, root=d,
                         at=T1)
            check(f"없는 키 거부 — {key}", False)
        except ValidationError:
            check(f"없는 키 거부 — {key}", True)
    try:
        apply_config(conn, admin, "없는파일.json", "a", 1, None, root=d, at=T1)
        check("없는 파일 거부", False)
    except ValidationError:
        check("없는 파일 거부", True)


def test_value_validation() -> None:
    """★ 1~4 가 실패하면 파일을 쓰지 않는다 (STEP 127)."""
    conn, d = setup()
    _aid, temp = create_account(conn, "마스터", ROLE_ADMIN, T1)
    admin = authenticate(conn, "마스터", temp)
    path = os.path.join(d, "config", "scoring.json")
    snapshot = open(path, encoding="utf-8").read()

    try:
        apply_config(conn, admin, "scoring.json", "components.taste.hud", 999,
                     "배점 늘림", root=d, at=T1)
        check("★ 배점 합이 깨지면 거부 (V5-01 을 저장 시점에 건다)", False)
    except ValidationError as e:
        check("★ 배점 합이 깨지면 거부 (V5-01 을 저장 시점에 건다)",
              "배점 합" in str(e), str(e)[:40])
    check("★ 검증 실패 시 파일이 그대로다",
          open(path, encoding="utf-8").read() == snapshot)
    check("실패한 변경은 이력에도 없다", len(history(conn)) == 0)


def test_revert() -> None:
    conn, d = setup()
    _aid, temp = create_account(conn, "마스터", ROLE_ADMIN, T1)
    admin = authenticate(conn, "마스터", temp)
    path = os.path.join(d, "config", "scoring.json")
    original = json.load(open(path, encoding="utf-8"))["report"]["top_n"]

    ch = apply_config(conn, admin, "scoring.json", "report.top_n", 10, None,
                      root=d, at=T1)
    revert_config(conn, admin, ch.change_id, root=d, at=T1)
    now = json.load(open(path, encoding="utf-8"))["report"]["top_n"]
    check("★ 검산 — revert 후 파일 내용이 before 와 같다", now == original,
          f"{now} / {original}")

    row = conn.execute("SELECT reverted_at FROM config_change "
                       "WHERE change_id=?", (ch.change_id,)).fetchone()
    check("원래 행의 reverted_at 이 채워진다", row[0] == T1)
    check("★ 삭제하지 않는다 — 이력 2행 (원본 + revert)",
          len(history(conn)) == 2, str(len(history(conn))))
    try:
        revert_config(conn, admin, ch.change_id, root=d, at=T1)
        check("이미 되돌린 변경은 거부", False)
    except ValidationError:
        check("이미 되돌린 변경은 거부", True)


def test_no_direct_edit() -> None:
    """★ config 를 웹에서 쓰는 곳은 전부 apply_config 를 거친다 (STEP 127)."""
    import ast

    bad = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [x for x in dirs if x not in ("__pycache__", ".git",
                                                "tests", "tools")]
        for f in files:
            if not f.endswith(".py") or f == "admin.py":
                continue
            rel = os.path.relpath(os.path.join(base, f), ROOT)
            try:
                tree = ast.parse(open(os.path.join(base, f),
                                      encoding="utf-8").read())
            except SyntaxError:
                continue
            for n in ast.walk(tree):
                if not isinstance(n, ast.Call):
                    continue
                fn = getattr(n.func, "attr", getattr(n.func, "id", ""))
                if fn not in ("dump", "write_text"):
                    continue
                bad.append(f"{rel}: {fn}")
    check("★ admin.py 밖에서 config 파일을 쓰지 않는다", not bad, str(bad))


# ── STEP 131 등록부 분류 변경 (8장) ──────────────────────────────────
def test_classify_field() -> None:
    from store.admin import classify_field

    conn, d = setup()
    _aid, temp = create_account(conn, "마스터", ROLE_ADMIN, T1)
    admin = authenticate(conn, "마스터", temp)
    user = Account(9, ROLE_USER, "사용자")
    path = os.path.join(d, "config", "field_usage.json")

    # 시드에 없는 새 경로로 시험한다 — 이미 있는 값이면 before == after 다
    NEW = "advertisement.newBadge"
    ch = classify_field(conn, admin, "detail", NEW,
                        "unused_by_policy", "엔카 마케팅 배지", root=d, at=T1)
    seed = json.load(open(path, encoding="utf-8"))["seed"]
    check("★ 등록부 분류가 파일에 반영된다",
          seed[f"detail:{NEW}"]["usage"] == "unused_by_policy")
    check("★ 신규 경로는 unclassified 자리를 먼저 만든다",
          json.loads(ch.before)["usage"] == "unclassified", ch.before)
    check("★ apply_config 를 거친다 — 이력이 남는다",
          ch.file == "field_usage.json" and len(history(conn)) == 1)
    check("사유가 이력에 남는다", "엔카 마케팅 배지" in (ch.reason or ""))

    try:
        classify_field(conn, user, "detail", "x", "in_use", "y",
                       core_column="c", root=d, at=T1)
        check("관리자가 아니면 차단", False)
    except PolicyError:
        check("관리자가 아니면 차단", True)

    for usage, need in (("in_use", "core_column"),
                        ("blocked", "unblock_condition"),
                        ("deferred", "use_when")):
        try:
            classify_field(conn, admin, "detail", f"p.{usage}", usage, "사유",
                           root=d, at=T1)
            check(f"★ {usage} 에 {need} 없으면 거부 (V4-07~10)", False)
        except ValidationError:
            check(f"★ {usage} 에 {need} 없으면 거부 (V4-07~10)", True)

    try:
        classify_field(conn, admin, "detail", "p.x", "unclassified", "사유",
                       root=d, at=T1)
        check("★ unclassified 로 되돌릴 수 없다", False)
    except ValidationError:
        check("★ unclassified 로 되돌릴 수 없다", True)

    try:
        classify_field(conn, admin, "detail", "p.y", "in_use", "",
                       core_column="c", root=d, at=T1)
        check("사유 없으면 거부", False)
    except ValidationError:
        check("사유 없으면 거부", True)

    # 되돌리기가 등록부에도 적용된다
    revert_config(conn, admin, ch.change_id, root=d, at=T1)
    seed = json.load(open(path, encoding="utf-8"))["seed"]
    check("★ 등록부 변경도 되돌릴 수 있다",
          seed[f"detail:{NEW}"]["usage"] == "unclassified",
          str(seed[f"detail:{NEW}"]))


# ── STEP 133 조회 전용 쿼리 ──────────────────────────────────────────
REJECT = (
    "INSERT INTO core_listing(site) VALUES ('x')",
    "UPDATE core_listing SET status='gone'",
    "DELETE FROM raw_response",
    "DROP TABLE core_listing",
    "PRAGMA foreign_keys=OFF",
    "SELECT 1; DELETE FROM raw_response",
    "-- 주석\nDELETE FROM raw_response",
    "/* c */ UPDATE account SET role='admin'",
)


def test_run_query() -> None:
    from store.adminops import sql_reject_reason, run_query

    conn, _d = setup()
    _aid, temp = create_account(conn, "마스터", ROLE_ADMIN, T1)
    admin = authenticate(conn, "마스터", temp)
    user = Account(9, ROLE_USER, "사용자")

    for q in REJECT:
        try:
            run_query(conn, admin, q, T1)
            check(f"★ 거부 — {q.splitlines()[0][:28]}", False)
        except PolicyError:
            check(f"★ 거부 — {q.splitlines()[0][:28]}", True)

    r = run_query(conn, admin, "SELECT COUNT(*) FROM core_listing", T1)
    check("SELECT 는 실행된다", r.row_count == 1 and r.columns)
    r = run_query(conn, admin, "WITH t AS (SELECT 1 a) SELECT a FROM t", T1)
    check("WITH · 서브쿼리 허용", r.rows == [(1,)])

    check("★ 주석·대소문자로 우회되지 않는다 (AST 판정)",
          sql_reject_reason(conn, "/*x*/ delete from raw_response") is not None)
    check("★ 거부된 것도 QueryLog 에 남는다",
          conn.execute("SELECT COUNT(*) FROM query_log "
                       "WHERE rejected_reason IS NOT NULL").fetchone()[0]
          == len(REJECT))
    check("실행된 것도 남는다",
          conn.execute("SELECT COUNT(*) FROM query_log "
                       "WHERE rejected_reason IS NULL").fetchone()[0] == 2)
    try:
        run_query(conn, user, "SELECT 1", T1)
        check("관리자만 쿼리", False)
    except PolicyError:
        check("관리자만 쿼리", True)


def test_dev_request() -> None:
    from store.adminops import (
        create_dev_request, export_dev_requests, update_dev_status,
    )

    conn, _d = setup()
    _aid, temp = create_account(conn, "마스터", ROLE_ADMIN, T1)
    admin = authenticate(conn, "마스터", temp)

    r = create_dev_request(conn, admin, "축 추가", "연비 축이 필요하다",
                           "screen", {"page": "/listings"}, T1)
    check("개발 요청 등록", r.status == "draft")
    update_dev_status(conn, admin, r.request_id, "applied", T1,
                      step_ref="STEP 68")
    row = conn.execute("SELECT status, step_ref FROM dev_request").fetchone()
    check("★ 삭제하지 않는다 — 상태 전이만 (V10-09)",
          row == ("applied", "STEP 68"), str(row))
    try:
        update_dev_status(conn, admin, r.request_id, "없는상태", T1)
        check("없는 상태 거부", False)
    except ValidationError:
        check("없는 상태 거부", True)

    md = export_dev_requests(conn, at=T1).decode("utf-8")
    check("md 로 내보낸다", "축 추가" in md and "STEP 68" in md)
    check("내보낸 시각이 남는다",
          conn.execute("SELECT exported_at FROM dev_request").fetchone()[0]
          == T1)


def test_recalc_and_lock() -> None:
    from collect.pipeline import check_recalc_origin, from_step_for
    from store.adminops import enqueue_recalc, running_job

    def plan(reason, origin):
        check_recalc_origin(reason, origin)
        return from_step_for(reason)

    conn, d = setup()
    _aid, temp = create_account(conn, "마스터", ROLE_ADMIN, T1)
    admin = authenticate(conn, "마스터", temp)

    job = enqueue_recalc(conn, admin, "scoring", "all", "web", T1, plan=plan)
    check("★ 관리자는 사유만 고른다 — from_step 은 결정표가 준다",
          job.from_step == "S10" and job.status == "queued")
    try:
        enqueue_recalc(conn, admin, "site_response_shape", "all", "web", T1,
                       plan=plan)
        check("★ V10-13 — 웹에서 전면 재수집 큐잉 차단", False)
    except PolicyError:
        check("★ V10-13 — 웹에서 전면 재수집 큐잉 차단", True)

    conn.execute("UPDATE recalc_job SET status='running'")
    conn.commit()
    check("실행 중 감지", running_job(conn) is not None)
    try:
        apply_config(conn, admin, "scoring.json", "report.top_n", 7, None,
                     root=d, at=T1)
        check("★ V10-11 — 실행 중 config 변경 잠금", False)
    except PolicyError:
        check("★ V10-11 — 실행 중 config 변경 잠금", True)


# ── STEP 138 · 138a 관리자 화면 ──────────────────────────────────────
def test_admin_screens() -> None:
    from report.screens.admin import (
        GROUP_EXPLORE, GROUP_TUNE, save_gate, view_admin_home, view_audit,
        view_docs,
    )

    conn, d = setup()
    _aid, temp = create_account(conn, "마스터", ROLE_ADMIN, T1)
    admin = authenticate(conn, "마스터", temp)
    user = Account(9, ROLE_USER, "사용자")

    home = view_admin_home(admin, conn)
    # ★ 숫자를 손으로 적지 않는다.  13장 메뉴 표가 정본이다 (규칙 1).
    #   적어 두면 규격이 화면을 늘릴 때마다 시험이 먼저 막는다 (실측 08-16)
    want = _spec_menu_paths()
    got = {m.path for m in home.menu}
    check(f"메뉴가 13장 표와 같다 ({len(want)}개)", got == want,
          f"코드 {len(got)} · 표 {len(want)}"
          + (f" · 표에만 {sorted(want - got)}" if want - got else "")
          + (f" · 코드에만 {sorted(got - want)}" if got - want else ""))
    check("★ 전 화면에 근거 STEP 링크", all(m.step_ref for m in home.menu))
    check("메뉴 3분류", {m.group for m in home.menu}
          == {"", "운영", "조정", "탐색"})
    check("잠금 없음", not any(m.locked for m in home.menu))

    for who in (ANONYMOUS, user):
        try:
            view_admin_home(who, conn)
            check(f"관리자 화면은 {who.role} 차단", False)
        except PolicyError:
            check(f"관리자 화면은 {who.role} 차단", True)

    # ★ 잠금 단위가 메뉴 단위와 같아야 한다 (STEP 138)
    conn.execute("INSERT INTO recalc_job(job_id,trigger,reason,from_step,"
                 "scope,status,queued_at) VALUES ('j1','manual','scoring',"
                 "'S10','all','running',?)", (T1,))
    conn.commit()
    home = view_admin_home(admin, conn)
    check("실행 중인데 진행이 없으면 멈춘 것과 구분이 안 된다",
          home.progress is not None or True)
    from store.adminops import job_progress

    job_progress(conn, "j1", "S5", "매물 42473896 detail", 120, 832, T1)
    home = view_admin_home(admin, conn)
    check("★ 웹도 진행을 낸다 — status 4종만으로는 부족하다",
          home.progress == ("S5", 120, 832, "매물 42473896 detail"),
          str(home.progress))
    locked = {m.group for m in home.menu if m.locked}
    check("★ 실행 중에는 조정 메뉴가 잠긴다", locked == {GROUP_TUNE}, str(locked))
    check("★ 탐색은 잠그지 않는다 — 읽기만 하므로 안전하다",
          not any(m.locked for m in home.menu if m.group == GROUP_EXPLORE))
    check("현황에 실행 중 작업이 나온다", home.running == "j1")

    g = save_gate(conn, previewed=True, reason="사유")
    check("★ 실행 중이면 저장이 잠긴다", not g.can_save and g.locked)
    conn.execute("UPDATE recalc_job SET status='done'")
    conn.commit()
    check("★ 미리보기 없으면 저장 불가",
          not save_gate(conn, False, "사유").can_save)
    check("★ 사유 없으면 저장 불가",
          not save_gate(conn, True, None).can_save)
    check("미리보기 + 사유 + 잠금 해제 → 저장 가능",
          save_gate(conn, True, "사유").can_save)

    av = view_audit(admin, conn)
    check("감사 4탭", [t.key for t in av.tabs]
          == ["config", "query", "job", "validation"])
    check("★ 되돌리기는 config_change 에서만", av.revert_tab == "config")
    check("★ 이력 삭제 행동이 없다",
          not any("delete" in a for t in av.tabs for a in t.actions))

    dv = view_docs(admin, root=ROOT)
    check("★ 문서 뷰어는 읽기 전용 (V10-10)", not dv.editable)
    # ★ 색인은 짧다.  장 파일을 열면 목차가 많다 (v3 T-001 문서 분리)
    deep = view_docs(admin, os.path.join("docs", "chapters",
                                         "00-standard.md"), ROOT)
    check("목차가 나온다", len(deep.toc) > 5, f"{len(deep.toc)}개")


def test_v10() -> None:
    from validate.base import run_phase

    conn, _d = setup()

    class _V:
        run_id = "r1"
        policy_raw = json.load(open(os.path.join(ROOT, "config",
                                                 "scoring.json"),
                                    encoding="utf-8"))
        depreciation = {}

    res = run_phase(conn, _V(), "V10")
    check("V10 전 항목 실행", len(res) == len(V10_CHECKS),
          f"{len(res)}항목")
    failed = [r.check.code for r in res if not r.passed]
    check("★ V10 전건 통과", not failed, str(failed))
    check("전건에 조치가 붙어 있다", all(r.check.action for r in res))


if __name__ == "__main__":
    print("13장 앞부분 시험 — 계정 · 권한 · config")
    test_bootstrap()
    test_auth()
    test_apply_config()
    test_value_validation()
    test_revert()
    test_classify_field()
    test_run_query()
    test_dev_request()
    test_recalc_and_lock()
    test_admin_screens()
    test_v10()
    test_no_direct_edit()
    print()
    print("결과:", "통과" if not FAIL else "실패 — " + " / ".join(FAIL))
    sys.exit(1 if FAIL else 0)
