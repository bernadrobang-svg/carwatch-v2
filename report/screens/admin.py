# -*- coding: utf-8 -*-
"""관리자 화면 — 표현 계층 (13장 STEP 138 · 138a).

지시서   STEP 138 (메뉴 3분류 · 잠금 단위) · 138a (감사 조회) · 136 (문서 뷰어)
근거     ★ 잠금 단위가 메뉴 단위와 같아야 한다.
         실행 중에 배점을 바꾸면 그 실행의 결과가 어느 버전인지 모르게 된다
금지     미리보기 없이 저장 버튼을 여는 것 (STEP 138)
         문서 뷰어에 편집 경로를 두는 것 (V10-10)
         이력 삭제 버튼 (STEP 138a)
"""
from __future__ import annotations

import os

from dataclasses import dataclass, field

from report.screens.views import ViewerState
from contracts import ROLE_ADMIN, Account, require_role
from store.admin import running_job

# 메뉴 3분류.  잠금 단위와 일치시킨다 (STEP 138)
GROUP_OPS, GROUP_TUNE, GROUP_EXPLORE = "운영", "조정", "탐색"

# ★ 탐색은 잠그지 않는다.  읽기만 하므로 안전하다
LOCKED_GROUPS = (GROUP_TUNE,)

# 단위 환산.  ★ 임계값이 아니라 규격이다 (2장 상수표 성격 「단위」)
SEC_PER_MIN = 60


@dataclass(frozen=True)
class AdminMenuItem:
    group: str
    path: str
    title: str
    step_ref: str          # ★ 근거 STEP 링크.  전 화면이 갖는다 (STEP 138 검산)
    locked: bool = False
    lock_reason: str | None = None


# ★★ 개정 427 — 상단에서 내린 화면 여섯.  ★ 지우지 않는다.  여기로 들어간다
#   ★★ 개정 551 — ★ MENU 에 ★ 넣는다 (명령서 1-1 ⓑ).
#     전에는 「13장 표에 없다」며 안 넣었는데 ★ 그래서 ★ 들어가는 문이 하나도 없었다.
#     ★ 마스터 지시 08-23 「관리 페이지들이 모두 어디로 간 거야」
#   ★ 이름은 web/app.py LABELS 가 정본이다 — ★ 지어내지 않는다
GROUP_SCREENS = "화면"

MENU: tuple[tuple[str, str, str, str], ...] = (
    ("", "/admin", "현황", "STEP 138"),
    (GROUP_OPS, "/admin/run", "실행 지시 · 큐", "STEP 132"),
    (GROUP_OPS, "/admin/audit", "감사 조회", "STEP 138a"),
    (GROUP_OPS, "/admin/status", "진행 지켜보기", "STEP 136f"),
    (GROUP_OPS, "/admin/import", "목록 반입", "STEP 136a · 136b"),
    (GROUP_OPS, "/admin/collect", "브라우저 수집", "STEP 136c"),
    (GROUP_TUNE, "/admin/scoring", "배점 조정", "STEP 128 · 129"),
    (GROUP_TUNE, "/admin/targets", "차종 추가 · 수정", "STEP 130"),
    (GROUP_TUNE, "/admin/registry", "등록부 분류", "STEP 131"),
    (GROUP_TUNE, "/admin/dict", "사전 확정", "STEP 136e"),
    (GROUP_TUNE, "/admin/config", "config 편집 · 이력", "STEP 127"),
    (GROUP_EXPLORE, "/admin/query", "조회 쿼리", "STEP 133"),
    (GROUP_EXPLORE, "/admin/api", "API 조회 · 저장", "STEP 134"),
    (GROUP_EXPLORE, "/admin/tools", "관리 도구", "STEP 135"),
    (GROUP_EXPLORE, "/admin/docs", "문서 뷰어", "STEP 136"),
    (GROUP_EXPLORE, "/admin/requests", "개발 요청", "STEP 137"),
    # ★★ 상단에서 내린 화면 여섯 (개정 427 · 551).  ★ 여기가 들어가는 문이다
    (GROUP_SCREENS, "/recommend", "후보", "개정 427"),
    (GROUP_SCREENS, "/compare", "비교", "개정 427"),
    (GROUP_SCREENS, "/market", "시세", "개정 427"),
    (GROUP_SCREENS, "/dealers", "딜러", "개정 427"),
    (GROUP_SCREENS, "/reports", "리포트", "개정 427"),
    (GROUP_SCREENS, "/notready", "미판정", "개정 427"),
)


@dataclass(frozen=True)
class AdminHome:
    viewer: ViewerState
    menu: list[AdminMenuItem]
    running: str | None
    progress: tuple | None   # (step, done, total, detail) · 없으면 None
    unclassified: int
    pending_requests: int
    queued_jobs: int
    # ★ 조치가 필요한 것 · 최근 실행 · 되돌릴 수 있는 변경 (G-1).
    #   「무엇을 하면 되나」가 관리 화면의 전부다
    todos: list = field(default_factory=list)
    recent_runs: list = field(default_factory=list)
    recent_changes: list = field(default_factory=list)


@dataclass(frozen=True)
class SaveGate:
    """★ 미리보기를 본 뒤에만 저장 버튼이 열린다 (STEP 128 · 138)."""

    previewed: bool
    reason_given: bool
    locked: bool
    lock_reason: str | None = None

    @property
    def can_save(self) -> bool:
        return self.previewed and self.reason_given and not self.locked


@dataclass(frozen=True)
class AuditTab:
    key: str
    title: str
    rows: list
    actions: tuple[str, ...] = ()


@dataclass(frozen=True)
class AuditView:
    tabs: list[AuditTab]
    # ★ 되돌리기는 config_change 에서만 나온다 (STEP 138a 검산)
    revert_tab: str = "config"


@dataclass(frozen=True)
class DocView:
    """문서 뷰어는 읽기 전용이다.  지시서는 세션에서 갱신된다 (STEP 136)."""

    title: str
    body: str
    editable: bool = False
    toc: list = field(default_factory=list)
    # ★ 열 수 있는 문서 목록.  색인 하나만 내면 「내용이 없다」로 보인다
    files: list = field(default_factory=list)


def menu_for(conn, account: Account) -> list[AdminMenuItem]:
    """실행 중에는 조정 메뉴가 잠긴다 (STEP 132 · 138)."""
    job = running_job(conn)
    out = []
    for group, path, title, step in MENU:
        locked = bool(job) and group in LOCKED_GROUPS
        out.append(AdminMenuItem(
            group, path, title, step, locked,
            f"재계산 {job} 실행 중" if locked else None))
    return out


def view_admin_home(account: Account, conn) -> AdminHome:
    require_role(account, ROLE_ADMIN)
    from report.screens.build import viewer_state

    return AdminHome(
        viewer=viewer_state(account),
        menu=menu_for(conn, account),
        running=running_job(conn),
        progress=conn.execute(
            "SELECT current_step, step_done, step_total, detail "
            "FROM recalc_job WHERE status='running' LIMIT 1").fetchone(),
        unclassified=conn.execute(
            "SELECT COUNT(*) FROM meta_field_usage WHERE usage='unclassified'"
        ).fetchone()[0],
        pending_requests=conn.execute(
            "SELECT COUNT(*) FROM dev_request WHERE status IN "
            "('draft','requested','in_progress')").fetchone()[0],
        queued_jobs=conn.execute(
            "SELECT COUNT(*) FROM recalc_job WHERE status IN "
            "('queued','running')").fetchone()[0],
        todos=_todos(conn),
        recent_runs=_recent_runs(conn),
        recent_changes=_recent_changes(conn))


def _todos(conn) -> list:
    """조치가 필요한 것.

    ★ 「17건」이 아니라 「무엇이 막히고 어디로 가면 되나」를 낸다 (G-1).
      건수만 보면 사람이 아무것도 못 한다
    """
    # ★ 네 물음을 한 번에 센다 (V11-34 · B-2)
    row = conn.execute(
        "SELECT (SELECT COUNT(*) FROM dict_enum WHERE status='pending'), "
        "       (SELECT COUNT(*) FROM meta_field_usage "
        "        WHERE usage='unclassified'), "
        "       (SELECT COUNT(DISTINCT listing_id) FROM result_axis "
        "        WHERE excluded=1 AND source='catalog_missing'), "
        "       (SELECT COUNT(*) FROM dev_request WHERE status IN "
        "        ('draft','requested','in_progress'))").fetchone()
    out = []
    n = row[0]
    if n:
        out.append(Todo("사전 미검토", n,
                        "그 축의 판정이 멈춰 있습니다",
                        "원문 표본을 확인해 confirmed 로 올린 뒤 S9 재실행",
                        "/notready"))
    n = row[1]
    if n:
        out.append(Todo("등록부 미분류", n,
                        "판정에 쓰지 않는 경로입니다 — 급하지 않습니다",
                        "등록부에서 구분을 정합니다", "/admin/registry"))
    n = row[2]
    if n:
        out.append(Todo("카탈로그 미조회", n,
                        "사양 축이 판정되지 않아 분모가 줄어 있습니다",
                        "카탈로그를 수집하면 등급이 오를 수 있습니다",
                        "/admin/run"))
    n = row[3]
    if n:
        out.append(Todo("처리 중인 요청", n, "개발 요청이 열려 있습니다",
                        "요청 화면에서 상태를 봅니다", "/admin/requests"))
    return out


def _recent_runs(conn, limit: int | None = None) -> list:
    """최근 실행.  ★ 「돌았다」가 아니라 「무엇이 나왔나」를 낸다."""
    limit = _cfg_rows("recent_rows") if limit is None else limit
    # ★ 실행마다 3쿼리를 돌면 5회에 15쿼리다.  두 번에 묶는다 (V11-34)
    runs = conn.execute(
        "SELECT run_id, MIN(requested_at), COUNT(*), SUM(elapsed_ms) "
        "FROM audit_request GROUP BY run_id "
        "ORDER BY MIN(requested_at) DESC LIMIT ?", (limit,)).fetchall()
    ids = [r[0] for r in runs]
    marks = ",".join("?" * len(ids)) or "''"
    fails: dict = {}
    if ids:
        for rid_, sev, cnt in conn.execute(
            f"SELECT run_id, severity, COUNT(*) FROM audit_validation "
            f"WHERE run_id IN ({marks}) AND passed=0 GROUP BY 1, 2",
            tuple(ids)
        ):
            fails.setdefault(rid_, {})[sev] = cnt
    out = []
    for rid, at, n, ms in runs:
        ms = ms or 0
        bad = fails.get(rid, {}).get("fatal", 0)
        warn = fails.get(rid, {}).get("warn", 0)
        verdict = "정상" if not bad else f"fatal {bad}"
        if not bad and warn:
            verdict = f"경고 {warn}"
        out.append(RunRow(at or "-", f"요청 {n:,}건", rid, ms / MS_PER_SEC,
                          verdict))
    return out


def _recent_changes(conn, limit: int | None = None) -> list:
    """되돌릴 수 있는 변경.  ★ config_change 에서만 나온다 (STEP 138a)."""
    limit = _cfg_rows("recent_rows") if limit is None else limit
    return [ChangeRow(cid, at, f"{key} {before} → {after}", reason,
                      reverted is None)
            for cid, at, key, before, after, reason, reverted in conn.execute(
                "SELECT change_id, applied_at, key_path, before_value, "
                "after_value, reason, reverted_at FROM config_change "
                "ORDER BY change_id DESC LIMIT ?", (limit,))]


def save_gate(conn, previewed: bool, reason: str | None,
              group: str = GROUP_TUNE) -> SaveGate:
    job = running_job(conn)
    locked = bool(job) and group in LOCKED_GROUPS
    return SaveGate(previewed, bool(reason), locked,
                    f"재계산 {job} 실행 중" if locked else None)


def view_audit(account: Account, conn, limit: int = 100) -> AuditView:
    """쌓기만 하고 보는 자리가 없으면 이력이 없는 것과 같다 (STEP 138a).

    ★ 읽기 전용.  이력을 고치지 않는다.  삭제 버튼이 없다
    """
    require_role(account, ROLE_ADMIN)
    tabs = [
        AuditTab("config", "설정 변경", conn.execute(
            "SELECT change_id, account_id, file, key_path, before_value,"
            " after_value, reason, applied_at, reverted_at FROM config_change"
            " ORDER BY applied_at DESC LIMIT ?", (limit,)).fetchall(),
            ("revert",)),
        AuditTab("query", "쿼리", conn.execute(
            "SELECT query_id, account_id, sql_text, row_count, elapsed_ms,"
            " rejected_reason, executed_at FROM query_log"
            " ORDER BY executed_at DESC LIMIT ?", (limit,)).fetchall(),
            ("rerun",)),
        AuditTab("job", "작업", conn.execute(
            "SELECT job_id, trigger, reason, from_step, scope, status, run_id,"
            " queued_at FROM recalc_job ORDER BY queued_at DESC LIMIT ?",
            (limit,)).fetchall(), ("retry",)),
        # ★ 「통과」와 「미실행」을 가른다.  안 돈 검사를 통과로 보이면
        #   검사한 줄 알고 넘어간다 (A-7 · S5-8 · 실측 08-15)
        AuditTab("validation", "검증", [
            (rid, phase, code,
             "미실행" if not applicable
             else ("통과" if passed else "실패"),
             severity, at)
            for rid, phase, code, passed, severity, at, applicable
            in conn.execute(
                "SELECT run_id, phase, code, passed, severity, checked_at,"
                " applicable FROM audit_validation "
                "ORDER BY checked_at DESC LIMIT ?", (limit,))
        ], ("open_report",)),
    ]
    return AuditView(tabs)


# 지시서가 놓일 수 있는 자리.  ★ 장 파일이 정본이다 (v3 T-001 분리)
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
# ★ 뿌리 기준이다 (A-7)
DOC_CANDIDATES = (os.path.join(_ROOT, "docs", "INDEX.md"),
                  os.path.join(_ROOT, "개발지시서.md"))


def view_docs(account: Account, path: str | None = None,
              root: str = ".") -> DocView:
    """★ 웹에서 지시서를 고치지 않는다.  뷰어는 읽기 전용 (V10-10).

    ★ 문서가 장별로 나뉜 뒤에도 뷰어가 죽지 않는다.
      단일 파일 전제를 두면 분리 직후 화면이 500 이 된다
    """
    import re

    require_role(account, ROLE_ADMIN)
    # ★ DOC_CANDIDATES 는 이미 절대 경로다.  root 를 또 붙이면 못 찾아
    #   색인이 비었다 — A-7 을 고치며 생긴 결함이다 (실측 08-15)
    if path is None:
        cands = [os.path.join(root, "docs", "INDEX.md"), *DOC_CANDIDATES]
        path = next((p for p in cands if os.path.isfile(p)), cands[0])
    if os.path.isabs(path):
        full = path
    else:
        full = os.path.join(root, path)
        if not os.path.isfile(full):
            full = os.path.join(_ROOT, path)
    if not os.path.isfile(full):
        return DocView(title="문서를 찾지 못했습니다", body="", editable=False,
                       toc=[f"{p} 가 없다" for p in DOC_CANDIDATES])
    with open(full, encoding="utf-8") as f:
        body = f.read()
    toc = [m.group(0) for m in re.finditer(r"^#{1,2} .+$", body, re.M)]
    return DocView(title=os.path.basename(path), body=body, editable=False,
                   toc=toc, files=_doc_files(root))


def _doc_files(root: str = ".") -> list:
    """열 수 있는 문서 목록 (STEP 139).

    ★ 색인 하나만 내면 「내용이 없다」로 보인다.  장 파일이 정본이다
    ★ 목록을 만드는 자리와 여는 자리가 같은 뿌리를 봐야 한다 —
      갈리면 목록엔 있는데 열면 없다 (실측 08-15)
    """
    import glob

    base = root if os.path.isdir(os.path.join(root, "docs")) else _ROOT
    root_dir = os.path.join(base, "docs")
    out = []
    for path in sorted(glob.glob(os.path.join(root_dir, "**", "*.md"),
                                 recursive=True)):
        rel = os.path.relpath(path, base)
        out.append({"path": rel, "name": os.path.relpath(path, root_dir),
                    "lines": sum(1 for _ in open(path, encoding="utf-8"))})
    return out


@dataclass(frozen=True)
class Todo:
    """조치가 필요한 것 (시안 v2_admin).

    ★ 건수만 내면 사람이 무엇을 할지 모른다.  무엇이 막히는지와
      어디로 가면 되는지를 함께 낸다
    """
    label: str
    count: int
    why: str
    action: str
    url: str


@dataclass(frozen=True)
class RunRow:
    """최근 실행 한 줄."""
    at: str
    reason: str
    steps: str
    seconds: float
    verdict: str


@dataclass(frozen=True)
class ChangeRow:
    """되돌릴 수 있는 변경 (STEP 138a).

    ★ 되돌리기는 config_change 에서만 나온다 — 무엇을 되돌리는지가 분명해야 한다
    """
    change_id: int
    at: str
    what: str
    reason: str
    revertible: bool = True


# 밀리초 → 초.  ★ 시간 단위 환산은 상수로 둔다
MS_PER_SEC = 1000.0


# ── 관리 화면 공용 데이터 (STEP 128~138 · 시안 v2_admin_*) ──────────
# ★ 화면마다 다른 표를 보지만 「무엇이 언제 왜 바뀌었나」는 같은 물음이다


def _cfg_rows(key: str, root: str = ".") -> int:
    """관리 화면이 내는 줄 수.  ★ 코드에 박지 않는다 (config/admin.json)."""
    import json as _j
    import os as _o

    path = _o.path.join(root, "config", "admin.json")
    with open(path, encoding="utf-8") as f:
        return int(_j.load(f)[key])


def config_history(conn, limit: int | None = None) -> list:
    """설정 변경 이력.  ★ 사유 없이 바뀐 것이 있으면 그것이 보여야 한다."""
    limit = _cfg_rows("list_rows") if limit is None else limit
    return [{"at": at, "key": key, "before": before, "after": after,
             "reason": reason or "— 사유 없음",
             "reverted": bool(reverted)}
            for at, key, before, after, reason, reverted in conn.execute(
                "SELECT applied_at, key_path, before_value, after_value, "
                "reason, reverted_at FROM config_change "
                "ORDER BY change_id DESC LIMIT ?", (limit,))]


def query_history(conn, limit: int | None = None) -> list:
    """최근 쿼리.  ★ 거부된 것도 남긴다 — 무엇을 막았는지가 신호다."""
    limit = _cfg_rows("list_rows") if limit is None else limit
    return [{"at": at, "sql": (sql or "")[:120], "rows": rows,
             "ms": ms, "rejected": reason}
            for at, sql, rows, ms, reason in conn.execute(
                "SELECT executed_at, sql_text, row_count, elapsed_ms, "
                "rejected_reason FROM query_log "
                "ORDER BY query_id DESC LIMIT ?", (limit,))]





def db_tables(conn) -> list:
    """표 목록과 컬럼.  ★ 쿼리를 쓰려면 무엇이 있는지부터 봐야 한다.

    ★ 표마다 PRAGMA + COUNT 를 돌면 43개 표에 86 쿼리다 (V11-34 · B-2).
      컬럼은 pragma_table_info 를 조인해 한 번에, 행수는 UNION ALL 로 한 번에
    """
    # 컬럼을 몇 개까지 보일까.  ★ 수를 코드에 박지 않는다 (V4-17)
    shown = _cfg_rows("table_cols_shown")
    cols: dict = {}
    for name, joined in conn.execute(
        "SELECT m.name, group_concat(p.name) FROM sqlite_master m "
        "JOIN pragma_table_info(m.name) p "
        "WHERE m.type='table' AND m.name NOT LIKE 'sqlite_%' "
        "GROUP BY m.name ORDER BY m.name"
    ):
        cols[name] = (joined or "").split(",")
    if not cols:
        return []
    union = " UNION ALL ".join(
        f"SELECT '{n}' AS t, COUNT(*) AS c FROM {n}" for n in cols)
    counts = {t: c for t, c in conn.execute(union)}
    return [{"name": n,
             "columns": " · ".join(c[:shown]),
             "rows": counts.get(n, 0)}
            for n, c in cols.items()]


# 쿼리 예제.  ★ 사람이 처음에 무엇을 물어야 할지 모른다 (시안 v2_admin_query)
QUERY_EXAMPLES = (
    {"label": "분모별 매물 수",
     "sql": "SELECT denominator, COUNT(*) FROM result_score GROUP BY 1"},
    {"label": "축별 제외 건수",
     "sql": "SELECT axis, SUM(excluded) FROM result_axis GROUP BY 1"},
    {"label": "제외 사유",   # ★ 개정 433 — E등급이 아니라 「제외」다
     "sql": "SELECT absolute_fail, COUNT(*) FROM result_score "
            "WHERE grade='EXCLUDED' GROUP BY 1"},
    {"label": "엔드포인트별 응답 코드",
     "sql": "SELECT kind, http_code, COUNT(*) FROM audit_request GROUP BY 1,2"},
)


def api_snapshots(conn, limit: int | None = None) -> list:
    limit = _cfg_rows("list_rows") if limit is None else limit
    # ★ snapshot_id 를 함께 낸다.  없으면 링크가 빈 값이 되어 못 연다 (A-5)
    return [{"snapshot_id": sid, "at": at, "url": (url or "")[:80],
             "code": code, "size": len(body or "")}
            for sid, at, url, code, body in conn.execute(
                "SELECT snapshot_id, fetched_at, url, http_code, body "
                "FROM admin_api_snapshot ORDER BY snapshot_id DESC LIMIT ?",
                (limit,))]


def account_activity(conn, limit: int | None = None) -> list:
    """계정 활동.  ★ 로그인 시도는 거부도 남는다 (C-5)."""
    limit = _cfg_rows("activity_rows") if limit is None else limit
    rows = []
    for at, name, ok, reason in conn.execute(
        "SELECT attempted_at, display_name, succeeded, reason "
        "FROM auth_login_attempt ORDER BY attempt_id DESC LIMIT ?", (limit,)
    ):
        rows.append({"at": at, "who": name,
                     "what": "로그인" if ok else f"로그인 실패 — {reason}"})
    return rows


# 연료 이름 → 차종 키 꼬리 (STEP 149r).  ★ 사람이 짓지 않는다
FUEL_SUFFIX = (("전기", "EV"), ("가솔린+전기", "HEV"), ("하이브리드", "HEV"),
               ("LPG", "LPG"), ("디젤", "DSL"), ("가솔린", "G"))


def make_target_key(model_group: str, fuel: str) -> str:
    """고른 값에서 차종 키를 만든다 (STEP 149r · 마스터 지적 ⑧).

    ★ 「KOLEOS_HEV」를 사람이 외워 치게 하지 않는다.
      한글 모델군은 로마자가 없으므로 영문·숫자만 남기고,
      비면 site_model 의 영문 조각을 쓴다 — 그래도 비면 사람이 적는다
    """
    tail = ""
    for word, suffix in FUEL_SUFFIX:
        if word in (fuel or ""):
            tail = suffix
            break
    head = "".join(ch for ch in (model_group or "").upper()
                   if ch.isascii() and ch.isalnum())
    if not head:
        return ""
    return f"{head}_{tail}" if tail else head


def target_choices(conn, site: str = "encar") -> dict:
    """차종을 「고르게」 하는 값 (STEP 149r · 마스터 지적 ⑧).

    ★ 「KOLEOS_HEV」를 외워 치라는 것은 도구가 아니다.
      우리가 이미 받은 원문에 제조사·모델군·모델·연료·트림이 다 있다.
      facet 은 아직 0건이라(서울 IP 가 /search/ 에 막힘) 목록에서 뽑는다
    """
    def col(name: str) -> list:
        return [{"value": r[0], "count": r[1]} for r in conn.execute(
            f"SELECT {name}, COUNT(*) FROM core_listing "
            f"WHERE site=? AND {name} IS NOT NULL "
            f"GROUP BY 1 ORDER BY 2 DESC", (site,))]

    return {"maker": col("site_manufacturer"),
            "model_group": col("site_model_group"),
            "model": col("site_model"),
            "fuel": col("fuel_raw")}


def target_rows(conn, root: str = ".") -> list:
    """등록된 차종.  ★ 수집된 것과 설정에만 있는 것을 함께 낸다."""
    import json as _j
    import os as _o

    path = _o.path.join(root, "config", "targets.json")
    cfg = {}
    if _o.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            # ★ 「차종」은 site_query 를 가진 항목이다.
        #   SPEC_DEFAULT_ON 같은 공통 설정을 차종으로 세지 않는다
            cfg = {k: v for k, v in _j.load(f).items()
                   if isinstance(v, dict) and "site_query" in v}
    counts = {k: n for k, n in conn.execute(
        "SELECT target_key, COUNT(*) FROM core_listing "
        "WHERE target_key IS NOT NULL GROUP BY 1")}
    out = []
    for key, spec in cfg.items():
        out.append({"key": key,
                    "name": (spec or {}).get("label", key),
                    "count": counts.get(key, 0),
                    "collected": key in counts,
                    # ★ 확인 대기와 확정을 가른다 (STEP 130)
                    "status": (spec or {}).get("status", "active"),
                    # ★ 국산 Y · 수입 N (STEP 130)
                    "origin_type": {"Y": "국산", "N": "수입"}.get(
                        (spec or {}).get("origin_type"), None),
                    "pending": (spec or {}).get("status") == "pending_review"})
    return out


def parse_import_text(text: str, site: str) -> tuple:
    """붙여넣은 것을 해석한다 (13장 STEP 136a).

    ★ web 은 parse 층을 못 부른다 (STEP 15a · LAYER_ALLOW).  여기서 잇는다
    반환   (형식, 행 목록, facet 해석 | None)
    """
    from contracts import FORMAT_FACET
    from parse.importer import detect_format, parse_facet, parse_import

    fmt = detect_format(text)
    # ★ facet 해석도 여기서 한다.  store 는 parse 를 못 부른다 (V4-22)
    facet = parse_facet(text) if fmt == FORMAT_FACET else None
    return fmt, parse_import(text, fmt, site), facet


def status_view(conn, root: str = ".") -> dict:
    """진행 지켜보기 (13장 STEP 136f · 개정 272).

    ★ 읽기 전용이다.  실행 단추를 두지 않는다 — 보다가 또 누르면
      1만 호출이 도는 중에 다시 시작된다
    ★ 「대기 중」과 「멈춘 것」을 가른다.  마지막 진척이 언제인지로 가른다
    """
    import json as _j
    from datetime import datetime, timezone

    base = run_progress(conn, root)
    web = {}
    path = os.path.join(root, "config", "web.json")
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            web = _j.load(f)
    now = datetime.now(timezone.utc)

    def _mins(ts):
        if not ts:
            return None
        try:
            t = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        except ValueError:
            return None
        return int((now - t).total_seconds() // SEC_PER_MIN)

    live = _live_progress(conn, now, root)
    # 마지막으로 처리한 매물 — 「진척이 있나」를 이것으로 가른다
    last = conn.execute(
        "SELECT source_id, endpoint, fetched_at FROM raw_response "
        "ORDER BY id DESC LIMIT 1").fetchone()
    last_min = _mins(last[2]) if last else None
    running = conn.execute(
        "SELECT job_id, reason, scope, current_step, step_done, step_total, "
        "       detail, queued_at, updated_at, run_id FROM recalc_job "
        "WHERE status='running' ORDER BY queued_at DESC LIMIT 1").fetchone()
    recent = [{"job_id": r[0], "status": r[1], "reason": r[2],
               "scope": r[3], "detail": (r[4] or "")[:120],
               "at": r[5], "minutes": _mins(r[5])}
              for r in conn.execute(
                  "SELECT job_id, status, reason, scope, detail, "
                  "       COALESCE(ended_at, queued_at) "
                  "FROM recalc_job ORDER BY COALESCE(ended_at, queued_at) "
                  "DESC LIMIT ?", (_cfg_rows("recent_rows"),))]
    failed = [r for r in recent if r["status"] == "failed"]
    return {
        **base,
        # ★ 4시간마다 저절로 센 결과 (개정 335 · S29-0).
        #   마스터가 「다 했어?」를 묻지 않아도 화면에 남아 있게 한다
        "light": _light_result(root, _mins),
        # ★ 카탈로그는 조합 단위다.  「147건 받았다」로 끝내지 않는다 (개정 327)
        "catalog": _catalog_state(conn),
        "poll_sec": int(web.get("status_poll_sec") or 0),
        "checked_at": now.isoformat(timespec="seconds"),
        "running": ({"job_id": running[0], "reason": running[1],
                     "scope": running[2], "step": running[3] or "-",
                     "done": running[4] or 0, "total": running[5] or 0,
                     "detail": running[6] or "",
                     "elapsed_min": _mins(running[7]),
                     "run_id": running[9] or ""} if running else None),
        "last_item": ({"source_id": last[0], "endpoint": last[1],
                       "at": last[2], "minutes": last_min} if last else None),
        **live,
        # ★ 큐만 보지 않는다.  셋 중 하나라도 참이면 「도는 중」이다 (개정 273).
        #   큐를 안 거친 실행(진입점 직접 호출)도 도는 것이다
        "idle": (running is None and base["queued_waiting"] == 0
                 and not live["live_running"]),
        "stalled_min": (last_min if running is not None else None),
        "recent_jobs": recent,
        "failed_jobs": failed,
    }


def _catalog_state(conn) -> dict:
    """카탈로그 조합 전수 (개정 327 · V1-23 · V1-24).

    ★ 「몇 건 받았다」가 아니라 「몇 개 중 몇 개」와 「왜 못 받았나」를 낸다.
      마스터 지적 「카탈로그가 왜 없어. 수집하다가 버린 거겠지」
    """
    from store.core import catalog_coverage, our_fault

    got = catalog_coverage(conn)
    need, ok, weight = got["need"], got["ok"], got["weight"]
    rows = []
    for why, keys in got["why"].items():
        for key in keys:
            rows.append({"key": key,
                         "label": got["label"].get(key, key),
                         "why": why,
                         "listings": weight.get(key, 0),
                         "ours": our_fault(why)})
    rows.sort(key=lambda r: -r["listings"])
    # 화면에 몇 조합까지 보일 것인가.  ★ 매물 많은 조합부터 (정책값은 config)
    top = _cfg_rows("catalog_rows")
    blind = sum(n for k, n in weight.items() if k not in got["linked"])
    return {
        "need": len(need), "got": len(ok & need),
        "pct": round(len(ok & need) * 100 / len(need), 1) if need else 0,
        "blind": blind,
        "ours": sum(1 for r in rows if r["ours"]),
        "missing": rows[:top],
        "more": max(0, len(rows) - top),
    }


def _light_result(root: str, mins) -> dict | None:
    """가벼운 점검의 마지막 결과 (개정 335).

    ★ 도구가 남긴 것을 읽기만 한다.  화면이 검사를 돌리지 않는다 —
      화면을 열 때마다 150초짜리를 돌릴 수는 없다
    """
    import json as _j

    path = os.path.join(root, "outputs", "light", "last.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            got = _j.load(f)
    except (ValueError, OSError):
        return None
    num = got.get("숫자") or {}
    return {
        "at": got.get("at"),
        "minutes": mins(got.get("at")),
        "fatal": num.get("fatal"),
        "warn": num.get("warn"),
        "tests": num.get("시험 실패"),
        "dash": num.get("—"),
        "calc": num.get("계산식"),
        "leak": num.get("템플릿 문법"),
        "took": got.get("걸린 초"),
        "budget": got.get("예산 초"),
        "over": bool(got.get("예산 초")
                     and (got.get("걸린 초") or 0) > got["예산 초"]),
        "changes": got.get("바뀐 것") or [],
        "clean": not (num.get("fatal") or num.get("시험 실패")
                      or num.get("—") or num.get("템플릿 문법")),
    }


# 매물당 요청 4종 (2장 STEP 25).  ★ 여기서 세지 않는다 — 수집 계약이 정본이다
from report.render import LISTING_ENDPOINTS  # noqa: E402


def _live_window(root: str = ".") -> int:
    """「도는 중」으로 볼 최근 구간(초).  ★ 코드에 박지 않는다 (config.web)."""
    import json as _j

    with open(os.path.join(root, "config", "web.json"),
              encoding="utf-8") as f:
        return int(_j.load(f)["live_window_sec"])


def _live_progress(conn, now, root: str = ".") -> dict:
    """실제로 도는가 · 얼마나 남았나 (개정 273 · STEP 136f).

    ★ recalc_job 만 보면 큐를 안 거친 실행을 「할 일 없음」으로 단정한다.
      실측 08-16 — 터미널은 2,052/13,888 인데 화면은 「도는 것이 없습니다」였다
    ★ 판정 근거 셋 — ① 큐에 running ② 최근에 요청이 늘었나 ③ 마지막 처리 시각
    """
    from datetime import timedelta

    window = _live_window(root)
    since = (now - timedelta(seconds=window)).isoformat()
    recent = conn.execute(
        "SELECT COUNT(*) FROM audit_request WHERE requested_at >= ?",
        (since,)).fetchone()[0]
    row = conn.execute(
        "SELECT run_id, kind, requested_at FROM audit_request "
        "ORDER BY id DESC LIMIT 1").fetchone()
    run_id = row[0] if row else ""
    done = conn.execute(
        "SELECT COUNT(*) FROM audit_request WHERE run_id = ?",
        (run_id,)).fetchone()[0] if run_id else 0
    active = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE status='active'"
    ).fetchone()[0]
    # ★ 상한이다.  진단은 encarDiagnosis==0 인 매물만 부르므로 실제는 더 적다
    total = active * len(LISTING_ENDPOINTS)
    rate = recent / float(window)
    left = max(0, total - done)
    eta_min = int(left / rate / SEC_PER_MIN) if rate else None
    step = {"list": "S1", "facet": "S2", "catalog": "S7"}.get(
        row[1] if row else "", "S5") if row else "-"
    return {
        "live_running": recent > 0,
        "live_recent": recent,
        "live_window": window,
        "live_rate": round(rate, 1),
        "live_step": step,
        "live_run_id": run_id,
        "live_done": done,
        "live_total": total,
        "live_left": left,
        "live_eta_min": eta_min,
        "raw_rows": conn.execute(
            "SELECT COUNT(*) FROM raw_response").fetchone()[0],
    }


def run_progress(conn, root: str = ".") -> dict:
    """실행 진행 (STEP 132 · 132a · 개정 261).

    ★ 「대기 중」과 「멈춘 것」을 가른다.  진행이 없는 동안 빈 화면을 내지 않는다
    ★ 오래 대기한 큐는 그렇게 말한다 — 실행기가 도는지 사람이 확인해야 한다
    """
    import json as _j
    from datetime import datetime, timezone

    web = {}
    path = os.path.join(root, "config", "web.json")
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            web = _j.load(f)
    row = conn.execute(
        "SELECT job_id, status, reason, scope, current_step, step_done, "
        "       step_total, detail, queued_at, updated_at, run_id "
        "FROM recalc_job ORDER BY queued_at DESC LIMIT 1").fetchone()
    waiting = conn.execute(
        "SELECT COUNT(*) FROM recalc_job WHERE status='queued'").fetchone()[0]
    stale_min = 0
    if row and row[1] == "queued":
        try:
            q = datetime.fromisoformat(str(row[8]).replace("Z", "+00:00"))
            stale_min = int(
                (datetime.now(timezone.utc) - q).total_seconds()
                // SEC_PER_MIN)
        except ValueError:
            stale_min = 0
    # 단계별 원문 수 — 「무엇이 얼마나 됐나」를 실측으로 낸다
    got = {k: n for k, n in conn.execute(
        "SELECT endpoint, COUNT(*) FROM raw_response WHERE status='ok' "
        "GROUP BY 1")}
    return {
        "job": ({"job_id": row[0], "status": row[1], "reason": row[2],
                 "scope": row[3], "step": row[4] or "-", "done": row[5] or 0,
                 "total": row[6] or 0, "detail": row[7] or "",
                 "queued_at": row[8], "updated_at": row[9],
                 "run_id": row[10] or ""} if row else None),
        "queued_waiting": waiting,
        "stale_minutes": stale_min,
        "refresh_sec": int(web.get("progress_refresh_sec") or 0),
        "raw_counts": [{"endpoint": k, "n": n} for k, n in sorted(got.items())],
        "listings": conn.execute(
            "SELECT COUNT(*) FROM core_listing").fetchone()[0],
        "judged": conn.execute(
            "SELECT COUNT(*) FROM result_score").fetchone()[0],
    }


def collect_state(conn, collect_urls=None, root: str = ".",
                  limit: int | None = None) -> dict:
    """브라우저 수집 화면 (13장 STEP 136c · 개정 263 · 264 · 265).

    ★ 부를 주소는 어댑터가 만든 것을 그대로 낸다.  화면이 손으로 만들지 않는다
    ★ 이미 받은 쪽을 함께 낸다 — 중간에 실패해도 처음부터 다시 하지 않는다
    """
    import json as _j

    limit = _cfg_rows("recent_rows") if limit is None else limit
    from contracts import ORIGIN_BROWSER

    urls = list(collect_urls() if callable(collect_urls) else (collect_urls or []))
    web = {}
    path = os.path.join(root, "config", "web.json")
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            web = _j.load(f)
    rows = [{"raw_id": rid, "at": at, "endpoint": ep, "bytes": len(body or ""),
             "url": url or "", "code": code}
            for rid, at, ep, body, url, code in conn.execute(
                "SELECT id, fetched_at, endpoint, body, request_url, http_code "
                "FROM raw_response WHERE origin=? ORDER BY id DESC LIMIT ?",
                (ORIGIN_BROWSER, limit))]
    opened = [{"code": c, "actual": a, "at": t} for c, a, t in conn.execute(
        "SELECT code, actual, checked_at FROM audit_validation "
        "WHERE code LIKE 'STEP53-%' AND actual IN (?, 'import') "
        "ORDER BY checked_at DESC", (ORIGIN_BROWSER,))]
    # ★ 차종별로 이미 받은 것 — 재개점이다 (개정 263)
    done: dict = {}
    for r in conn.execute(
        "SELECT endpoint, COUNT(*) FROM raw_response WHERE origin=? "
        "GROUP BY endpoint", (ORIGIN_BROWSER,)
    ):
        done[r[0]] = r[1]
    scopes = []
    for u in urls:
        if u["kind"] == "list":
            scopes.append({"target_key": u["target_key"],
                           "targets": u.get("targets") or u["target_key"]})
    # ★ JS 에 넘길 계획.  화면이 문자열을 손으로 짓지 않게 여기서 만든다.
    #   사용자 입력이 아니라 어댑터가 만든 값이다 (V11-05 RAW_ALLOW)
    plan = _j.dumps([{"kind": u["kind"], "target_key": u["target_key"],
                      "url": u["url"], "url_template": u["url_template"]}
                     for u in urls], ensure_ascii=False)
    return {"collect_urls": urls, "collect_plan_json": plan,
            **received_vs_used(conn),
            "browser_batches": rows,
            "browser_count": len(rows), "opened_steps": opened,
            "scopes": scopes, "scope_count": len(scopes),
            "saved_list": done.get("list", 0), "saved_facet": done.get("facet", 0),
            # ★ 기본값을 코드에 두지 않는다.  없으면 그 자리에서 드러난다
            "rows_per_call": int(web["browser_collect_rows"]),
            "interval_sec": float(web["browser_interval_sec"]),
            "max_form_bytes": int(web["max_form_bytes"])}


def received_vs_used(conn) -> dict:
    """받았다 ↔ 쓰였다 (개정 268).

    ★ 둘을 한 자리에 낸다.  「저장했습니다」는 사실인데 아무 일도 안 일어난
      상태를 화면이 못 보여 주면 사람이 못 잡는다 (실측 08-16 — 392쪽)
    """
    got = conn.execute(
        "SELECT COUNT(*) FROM raw_response WHERE endpoint='list' "
        "AND status='ok'").fetchone()[0]
    items = conn.execute(
        "SELECT COUNT(*) FROM core_listing").fetchone()[0]
    detail = conn.execute(
        "SELECT COUNT(*) FROM raw_response WHERE endpoint='detail' "
        "AND status='ok'").fetchone()[0]
    parsed = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE parse_version IS NOT NULL "
        "AND parse_version <> ''").fetchone()[0]
    return {"got_list_pages": got, "used_listings": items,
            "got_detail": detail, "used_parsed": parsed}


def dict_state(conn) -> dict:
    """사전 확정 화면 (13장 STEP 136e).

    ★ 「몇 종」이 아니라 「무엇을 확정하면 무엇이 열리나」를 낸다
    """
    from store.adminops import pending_axis_summary, pending_enums

    rows = pending_enums(conn)
    # ★ 예시를 몇 개 보일지는 표시 정책이다 (config.web.recent_rows)
    n = _cfg_rows("recent_rows")
    # ★ 자른 것을 말한다.  조용히 자르면 「이게 전부」로 읽힌다 (검토 17)
    axes = [dict(a, sample=" · ".join(a["sample"][:n])
                 + (f"  외 {len(a['sample']) - n}종"
                    if len(a["sample"]) > n else ""))
            for a in pending_axis_summary(conn)]
    # ★ 자주 나온 순.  대기가 많은 축부터 봐야 한 번에 많이 열린다 (검토 15)
    axes.sort(key=lambda a: (-a["values"], a["site"], a["axis"]))
    confirmed = conn.execute(
        "SELECT axis, COUNT(*) FROM dict_enum WHERE status='confirmed' "
        "GROUP BY 1 ORDER BY 1").fetchall()
    return {"pending_rows": rows, "pending_axes": axes,
            "pending_total": len(rows),
            "confirmed_rows": [{"axis": a, "n": n} for a, n in confirmed],
            # ★ facet 없이 목록에서 온 것이 있으면 화면이 그렇게 말한다 (V10-25)
            "has_list_source": any(r["from_list"] for r in rows)}


def import_state(conn, limit: int | None = None) -> dict:
    """반입 현황 — 「이 데이터는 반입분입니다」를 화면이 말하게 한다.

    지시서   STEP 136a 「화면에 「이 데이터는 반입분입니다」를 표시한다」
    ★ 반입분과 수집분을 한 표에서 가른다.  섞어 보이면 금지 사항이다
    """
    limit = _cfg_rows("recent_rows") if limit is None else limit
    from contracts import IMPORT_SOURCE, S4_CODE

    rows = [{"raw_id": rid, "at": at, "bytes": len(body or ""),
             "meta": meta or "", "site": site}
            for rid, at, body, meta, site in conn.execute(
                "SELECT id, fetched_at, body, response_meta, site "
                "FROM raw_response WHERE origin=? "
                "ORDER BY id DESC LIMIT ?", (IMPORT_SOURCE, limit))]
    imported = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE classify_source=?",
        (IMPORT_SOURCE,)).fetchone()[0]
    collected = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE classify_source IS NULL "
        "OR classify_source <> ?", (IMPORT_SOURCE,)).fetchone()[0]
    s4 = conn.execute(
        "SELECT actual, checked_at FROM audit_validation WHERE code=? "
        "ORDER BY checked_at DESC LIMIT 1", (S4_CODE,)).fetchone()
    return {
        **received_vs_used(conn),
        "import_batches": rows,
        "imported_listings": imported,
        "collected_listings": collected,
        # ★ 「S4 · 반입(import)」 으로 표시한다 (STEP 136b ④)
        "s4_actual": (s4[0] if s4 else None),
        "s4_at": (s4[1] if s4 else None),
        "s4_label": ("S4 · 반입(import)" if s4 and s4[0] == IMPORT_SOURCE
                     else ("S4 · 수집(collector)" if s4 else "S4 · 미완료")),
    }


def job_log(conn, limit: int | None = None) -> list:
    """실행 로그.  ★ 진행 중인 것과 끝난 것을 한 줄로 본다."""
    limit = _cfg_rows("list_rows") if limit is None else limit
    # ★ job_id 를 낸다.  없으면 중단 단추가 어느 실행인지 못 가리킨다
    return [{"job_id": jid, "at": at, "status": status, "step": step or "-",
             "done": done, "total": total, "detail": detail or "",
             "reason": reason or "", "open": status in ("queued", "running")}
            for jid, at, status, step, done, total, detail, reason
            in conn.execute(
                "SELECT job_id, queued_at, status, current_step, step_done, "
                "step_total, detail, reason FROM recalc_job "
                "ORDER BY rowid DESC LIMIT ?", (limit,))]


def validation_runs(conn, limit: int | None = None) -> list:
    """검증 이력.  ★ 통과 수보다 「무엇이 바뀌었나」가 먼저다."""
    limit = _cfg_rows("recent_rows") if limit is None else limit
    out = []
    for rid, at in conn.execute(
        "SELECT run_id, MIN(checked_at) FROM audit_validation "
        "GROUP BY run_id ORDER BY MIN(checked_at) DESC LIMIT ?", (limit,)
    ):
        row = conn.execute(
            "SELECT SUM(passed), "
            " SUM(CASE WHEN passed=0 AND severity='fatal' THEN 1 ELSE 0 END), "
            " SUM(CASE WHEN passed=0 AND severity='warn' THEN 1 ELSE 0 END) "
            "FROM audit_validation WHERE run_id=?", (rid,)).fetchone()
        out.append({"run_id": rid, "at": at, "passed": row[0] or 0,
                    "fatal": row[1] or 0, "warn": row[2] or 0})
    return out


def blocking_set(conn) -> set:
    """판정을 막는 경로 — V4-11 · 목록과 같은 자리 (개정 390).

    ★ store 는 parse 를 못 부른다 (V4-22).  report 가 이어 준다 —
      화면과 검사가 다른 것을 세면 「32건」과 화면의 수가 어긋난다
    """
    from parse.encar.paths import WHOLE_CONTAINERS, parser_paths
    from store.core import blocking_keys

    return blocking_keys(conn, parser_paths(), WHOLE_CONTAINERS)
