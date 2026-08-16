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


@dataclass(frozen=True)
class AdminMenuItem:
    group: str
    path: str
    title: str
    step_ref: str          # ★ 근거 STEP 링크.  전 화면이 갖는다 (STEP 138 검산)
    locked: bool = False
    lock_reason: str | None = None


MENU: tuple[tuple[str, str, str, str], ...] = (
    ("", "/admin", "현황", "STEP 138"),
    (GROUP_OPS, "/admin/run", "실행 지시 · 큐", "STEP 132"),
    (GROUP_OPS, "/admin/audit", "감사 조회", "STEP 138a"),
    (GROUP_OPS, "/admin/import", "목록 반입", "STEP 136a · 136b"),
    (GROUP_TUNE, "/admin/scoring", "배점 조정", "STEP 128 · 129"),
    (GROUP_TUNE, "/admin/targets", "차종 추가 · 수정", "STEP 130"),
    (GROUP_TUNE, "/admin/registry", "등록부 분류", "STEP 131"),
    (GROUP_TUNE, "/admin/config", "config 편집 · 이력", "STEP 127"),
    (GROUP_EXPLORE, "/admin/query", "조회 쿼리", "STEP 133"),
    (GROUP_EXPLORE, "/admin/api", "API 조회 · 저장", "STEP 134"),
    (GROUP_EXPLORE, "/admin/tools", "관리 도구", "STEP 135"),
    (GROUP_EXPLORE, "/admin/docs", "문서 뷰어", "STEP 136"),
    (GROUP_EXPLORE, "/admin/requests", "개발 요청", "STEP 137"),
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
    {"label": "E등급 사유",
     "sql": "SELECT absolute_fail, COUNT(*) FROM result_score "
            "WHERE grade='E' GROUP BY 1"},
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
