# -*- coding: utf-8 -*-
"""관리 화면 동작 시험 (13장 · 14장).

★ 화면이 뜨는지가 아니라 「값을 넣으면 판정이 바뀌는지」를 본다.
  render 200 은 아무것도 보장하지 않는다 — 실측 08-15 에 화면이 뜨는데
  값을 안 넘겨 빈 표가 나왔고, 저장 단추가 저장을 안 했다

시험 방식
  사본 DB · 사본 config 위에서 실제 핸들러를 부른다
  단계마다 「무엇이 달라졌는가」를 DB · 파일에서 다시 읽어 확인한다
금지   함수를 직접 부르고 화면을 건너뛰는 것.  화면이 통로다
"""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from contracts import Account, ROLE_ADMIN, ROLE_USER  # noqa: E402
from errors import PolicyError, ValidationError  # noqa: E402

FAIL: list = []
T = "2026-08-15T00:00:00+00:00"


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  {detail}" if detail else ""))
    if not ok:
        FAIL.append(name)


def _env():
    """사본 DB + 사본 config.  ★ 실제 DB 를 고치지 않는다."""
    root = tempfile.mkdtemp()
    shutil.copytree(os.path.join(ROOT, "config"), os.path.join(root, "config"))
    db = os.path.join(root, "carwatch.db")
    # ★ 운영 DB 를 복사하지 않는다 (0장 · S24 · 개정 246).
    #   거기 남은 상태가 시험 결과를 바꾼다 — 실측 08-16
    from seed import build_seed_db

    build_seed_db(db, root)
    conn = sqlite3.connect(db)
    from store.admin import create_account

    aid, _ = create_account(conn, "마스터", ROLE_ADMIN, T)
    return conn, root, Account(aid, ROLE_ADMIN, "마스터")


def _cfg(root: str, name: str) -> dict:
    with open(os.path.join(root, "config", name), encoding="utf-8") as f:
        return json.load(f)


def _post(fn, conn, acc, form, root, **kw):
    return fn(conn, acc, {"query": {}, "form": dict(form), "method": "POST"},
              root=root, csrf="t", **kw)


def _get(fn, conn, acc, root, query=None, **kw):
    return fn(conn, acc, {"query": dict(query or {}), "form": {},
                          "method": "GET"}, root=root, csrf="t", **kw)


# ── 1  설정 변경이 파일과 이력에 남는가 (STEP 127) ────────────────────
def flow_config(conn, acc, root) -> None:
    from web.views import admin_config

    before = _cfg(root, "web.json")["rows_per_page"]
    _post(admin_config, conn, acc,
          {"csrf": "t", "previewed": "1", "file": "web.json",
           "key_path": "rows_per_page", "value": "150",
           "reason": "한 쪽을 짧게"}, root)
    after = _cfg(root, "web.json")["rows_per_page"]
    check("설정 — 값이 파일에 반영된다", after == 150, f"{before} → {after}")

    row = conn.execute(
        "SELECT key_path, before_value, after_value, reason "
        "FROM config_change ORDER BY rowid DESC LIMIT 1").fetchone()
    check("설정 — 사유와 함께 이력이 남는다",
          row is not None and row[0] == "rows_per_page"
          and row[3] == "한 쪽을 짧게", str(row))

    try:
        _post(admin_config, conn, acc,
              {"csrf": "t", "previewed": "1", "file": "web.json",
               "key_path": "rows_per_page", "value": "99"}, root)
        check("설정 — 사유 없이 저장되지 않는다", False, "저장됐다")
    except (PolicyError, ValidationError):
        check("설정 — 사유 없이 저장되지 않는다", True)

    try:
        _post(admin_config, conn, acc,
              {"csrf": "t", "previewed": "1", "file": "../secrets.json",
               "key_path": "x", "value": "1", "reason": "탈출"}, root)
        check("설정 — 목록 밖 파일을 고칠 수 없다", False, "고쳐졌다")
    except (PolicyError, ValidationError):
        check("설정 — 목록 밖 파일을 고칠 수 없다", True)


# ── 2  배점을 바꾸면 등급이 바뀌는가 (STEP 128) ★ 핵심 ───────────────
def flow_scoring(conn, acc, root) -> None:
    from web.views import admin_scoring

    pol = _cfg(root, "scoring.json")
    before_total = pol["total_points"]
    # ★ 축 이름을 박지 않는다 — 개정 292 로 배점이 통째로 바뀌었다
    axis = "state"
    before_war = {k: v for k, v in pol["components"].items()
                  if k.startswith(axis + ".")}

    _post(admin_scoring, conn, acc,
          {"csrf": "t", "previewed": "1", "action": "axis",
           "target": axis, "value": "120",
           "reason": "상태를 더 본다"}, root)
    pol = _cfg(root, "scoring.json")
    after_war = {k: v for k, v in pol["components"].items()
                 if k.startswith(axis + ".")}
    check("배점 — 축 총점이 비율로 재배분된다",
          sum(after_war.values()) == 120,
          f"{before_war} → {after_war}")
    check("배점 — total_points 가 성분 합과 같다",
          pol["total_points"] == sum(
              v if isinstance(v, int) else v.get("points", 0)
              for k, v in pol["components"].items()
              if not (isinstance(v, dict) and v.get("skipped"))),
          f"{before_total} → {pol['total_points']}")

    _post(admin_scoring, conn, acc,
          {"csrf": "t", "previewed": "1", "action": "skip",
           "target": "taste.sunroof", "value": "true",
           "reason": "원문에 언급이 없다"}, root)
    pol = _cfg(root, "scoring.json")
    check("배점 — 스킵은 빼지 않고 표시한다",
          pol["components"]["taste.sunroof"].get("skipped") is True,
          str(pol["components"]["taste.sunroof"]))

    try:
        _post(admin_scoring, conn, acc,
              {"csrf": "t", "previewed": "1", "action": "axis",
               # ★ 개정 292 로 spec 은 트림 45 · 옵션 30 둘뿐이다.
               #   1 로 줄이면 옵션이 0 이 된다
               "target": "spec", "value": "1", "reason": "0점 시험"}, root)
        check("배점 — 0 이 되는 성분을 만들지 않는다", False, "만들어졌다")
    except (PolicyError, ValidationError) as e:
        check("배점 — 0 이 되는 성분을 만들지 않는다", "스킵" in str(e),
              str(e)[:40])

    # ★ 여기가 핵심 — 바꾼 배점으로 실제 재채점하면 등급이 달라지는가
    changed = _rescore(conn, root)
    # ★ 등급은 절대 기준이라 (개정 324) 배점을 옮겨도 같은 칸일 수 있다.
    #   화면 입력이 판정까지 갔는지는 「점수가 달라졌는가」로 본다
    check("배점 — 바꾼 값으로 재채점하면 점수가 달라진다",
          changed is not None and changed[2] != changed[3],
          f"{changed[2]} → {changed[3]}" if changed else "재채점 못 함")


def _rescore(conn, root: str):
    """실제로 다시 채점한다.  ★ 화면 입력이 판정까지 가는지 본다.

    ★ 등급 판정은 score.grade 가 정본이다.  여기서 다시 만들지 않는다 —
      다시 만들면 시험이 「자기 구현」을 검사하게 된다
    """
    from analyze.axes import ScoringPolicy
    from score.grade import grade_of
    from score.scorer import ScoreResult

    ver = conn.execute(
        "SELECT MAX(calc_version) FROM result_score").fetchone()[0]
    if not ver:
        return None
    before = _dist(conn, ver)

    pol_raw = _cfg(root, "scoring.json")
    policy = ScoringPolicy(pol_raw)

    rows = conn.execute(
        "SELECT listing_id, axis, score, max_points, excluded "
        "FROM result_axis WHERE calc_version = ?", (ver,)).fetchall()
    comps = pol_raw["components"]
    got: dict = {}
    for lid, axis, score, _max_points, excluded in rows:
        spec = comps.get(axis)
        if spec is None:
            continue
        # ★ 스킵된 성분은 총점에도 분모에도 안 들어간다 (STEP 128)
        if isinstance(spec, dict) and spec.get("skipped"):
            continue
        full = spec if isinstance(spec, int) else spec.get("points", 0)
        e, d = got.setdefault(lid, [0.0, 0.0])
        if excluded:
            continue          # 그 매물만 제외 — 분모에서 뺀다
        got[lid] = [e + (score or 0), d + full]

    new_ver = f"{ver}x"
    for lid, (earned, denom) in got.items():
        fail, notr, dver = conn.execute(
            "SELECT absolute_fail, not_rated_reason, dict_version "
            "FROM result_score WHERE listing_id=? AND calc_version=?",
            (lid, ver)).fetchone()
        res = ScoreResult(score_total=0.0, denominator=denom,
                          applicable=denom, earned=earned,
                          grade="NOT_RATED" if notr else None,
                          absolute_fail=fail, by_axis={},
                          not_rated_reason=notr)
        conn.execute(
            "INSERT OR REPLACE INTO result_score(listing_id,calc_version,"
            "dict_version,score_total,earned,denominator,grade,"
            "absolute_fail,not_rated_reason,calculated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (lid, new_ver, dver, 0.0, earned, denom,
             grade_of(res, policy), fail, notr, T))
    conn.commit()
    # ★ 점수도 함께 돌려준다 (개정 324).  등급은 절대 기준이라
    #   배점을 옮겨도 같은 칸에 머물 수 있다 — 그래도 채점은 달라져야 한다
    return before, _dist(conn, new_ver), _sum(conn, ver), _sum(conn, new_ver)


def _sum(conn, ver: str) -> float:
    got = conn.execute(
        "SELECT ROUND(SUM(earned), 2) FROM result_score WHERE calc_version=?",
        (ver,)).fetchone()[0]
    return float(got or 0)


def _dist(conn, ver: str) -> dict:
    return dict(conn.execute(
        "SELECT grade, COUNT(*) FROM result_score WHERE calc_version=? "
        "GROUP BY 1 ORDER BY 2 DESC", (ver,)))


# ── 3  차종 추가 (STEP 130) ──────────────────────────────────────────
def flow_targets(conn, acc, root) -> None:
    from web.views import admin_targets

    f = {"csrf": "t", "previewed": "1", "action": "add",
         "target_key": "SONATA_HEV", "label": "쏘나타 HEV",
         "collect_group": "SONATA", "site_query": "(And.Hidden.N.)", "origin_type": "Y",
         "reason": "후보 추가"}
    _post(admin_targets, conn, acc, f, root)
    spec = _cfg(root, "targets.json").get("SONATA_HEV") or {}
    check("차종 — 확인 대기로 들어간다",
          spec.get("status") == "pending_review", str(spec.get("status")))

    try:
        _post(admin_targets, conn, acc, {**f, "action": "confirm"}, root)
        check("차종 — 배기량 확인 전에는 확정되지 않는다", False, "확정됐다")
    except (PolicyError, ValidationError):
        check("차종 — 배기량 확인 전에는 확정되지 않는다", True)

    blob = _cfg(root, "targets.json")
    blob["SONATA_HEV"]["displacement_range"] = [1900, 2100]
    with open(os.path.join(root, "config", "targets.json"), "w",
              encoding="utf-8") as fp:
        json.dump(blob, fp, ensure_ascii=False, indent=2)
    _post(admin_targets, conn, acc, {**f, "action": "confirm"}, root)
    check("차종 — 배기량을 확인하면 확정된다",
          _cfg(root, "targets.json")["SONATA_HEV"]["status"] == "active")

    try:
        _post(admin_targets, conn, acc, f, root)
        check("차종 — 같은 키를 두 번 넣지 않는다", False, "중복 등록됨")
    except (PolicyError, ValidationError):
        check("차종 — 같은 키를 두 번 넣지 않는다", True)


# ── 4  등록부 분류 (STEP 131) ────────────────────────────────────────
def flow_registry(conn, acc, root) -> None:
    from web.views import admin_registry

    row = conn.execute(
        "SELECT endpoint, json_path FROM meta_field_usage "
        "WHERE usage='unclassified' LIMIT 1").fetchone()
    if row is None:
        check("등록부 — 미분류가 없어 시험하지 않는다", True, "건너뜀")
        return
    _post(admin_registry, conn, acc,
          {"csrf": "t", "previewed": "1", "endpoint": row[0],
           "json_path": row[1], "usage": "unused_by_policy",
           "reason": "판정에 쓰지 않는다"}, root)
    # ★ 정본은 config/field_usage.json 이다.  표는 sync_registry 가 다시 채운다
    seed = _cfg(root, "field_usage.json")["seed"]
    entry = seed.get(f"{row[0]}:{row[1]}") or {}
    check("등록부 — 분류가 config 에 저장된다",
          entry.get("usage") == "unused_by_policy", str(entry))
    check("등록부 — 사유가 함께 남는다", bool(entry.get("reason")),
          str(entry.get("reason")))

    from tools.sync_registry import sync_registry

    sync_registry(conn, _cfg(root, "field_usage.json"), T)
    got = conn.execute(
        "SELECT usage FROM meta_field_usage WHERE endpoint=? AND json_path=?",
        row).fetchone()
    check("등록부 — 재동기화하면 표에도 반영된다",
          got and got[0] == "unused_by_policy", str(got))

    try:
        _post(admin_registry, conn, acc,
              {"csrf": "t", "previewed": "1", "endpoint": row[0],
               "json_path": row[1], "usage": "없는구분", "reason": "x"}, root)
        check("등록부 — 6종 밖의 구분을 받지 않는다", False, "받았다")
    except (PolicyError, ValidationError):
        check("등록부 — 6종 밖의 구분을 받지 않는다", True)


# ── 5  실행 지시 (STEP 132) ──────────────────────────────────────────
def flow_run(conn, acc, root) -> None:
    from web.views import admin_run

    # ★ 재처리 결정표는 함수다 — 사유·출처를 받아 시작 단계를 낸다 (STEP 132)
    def plan(reason, origin):
        return "S9"

    _post(admin_run, conn, acc,
          {"csrf": "t", "previewed": "1", "scope": "all",
                         # ★ 위험이 높은 행동은 문구를 직접 입력한다 (149l)
                         "confirm": "all",
           "reason": "배점을 바꿨다"}, root, plan=plan)
    job = conn.execute(
        "SELECT status, reason, from_step FROM recalc_job "
        "ORDER BY rowid DESC LIMIT 1").fetchone()
    check("실행 — 큐에 들어간다", job is not None and job[0] in
          ("queued", "running"), str(job))

    try:
        from web.views import admin_config

        _post(admin_config, conn, acc,
              {"csrf": "t", "previewed": "1", "file": "web.json",
               "key_path": "rows_per_page", "value": "77",
               "reason": "실행 중 변경"}, root)
        check("실행 — 도는 동안 설정이 잠긴다", False, "바뀌었다")
    except (PolicyError, ValidationError):
        check("실행 — 도는 동안 설정이 잠긴다", True)
    conn.execute("UPDATE recalc_job SET status='done'")
    conn.commit()


# ── 6  쿼리 (STEP 133) ───────────────────────────────────────────────
def flow_query(conn, acc, root) -> None:
    from web.views import admin_query

    _post(admin_query, conn, acc,
          {"csrf": "t", "sql": "SELECT grade, COUNT(*) FROM result_score "
                               "GROUP BY 1"}, root)
    n = conn.execute("SELECT COUNT(*) FROM query_log "
                     "WHERE rejected_reason IS NULL").fetchone()[0]
    check("쿼리 — 실행이 기록된다", n >= 1, f"{n}건")

    for sql in ("DELETE FROM core_listing",
                "SELECT * FROM core_pii",
                "SELECT p.* FROM core_pii p /* 우회 */"):
        try:
            _post(admin_query, conn, acc, {"csrf": "t", "sql": sql}, root)
        except (PolicyError, ValidationError):
            pass
    n = conn.execute("SELECT COUNT(*) FROM query_log "
                     "WHERE rejected_reason IS NOT NULL").fetchone()[0]
    check("쿼리 — 쓰기·PII 는 거부되고 거부도 남는다", n >= 3, f"{n}건 거부")
    alive = conn.execute("SELECT COUNT(*) FROM core_listing").fetchone()[0]
    check("쿼리 — 거부된 DELETE 가 실제로 지우지 않았다", alive > 0,
          f"{alive}건 남음")


# ── 7  API 조회 (STEP 134) ───────────────────────────────────────────
def flow_api(conn, acc, root) -> None:
    from web.views import admin_api

    body = ('{"category":{"originPrice":4270,"model":"KOLEOS"},'
            '"options":{"choice":[{"code":"1009"}]}}')
    _post(admin_api, conn, acc,
          {"csrf": "t", "previewed": "1", "reason": "탐색",
           "url": "https://api.encar.com/v1/readside/vehicle/1",
           "note": "가격 경로 확인"}, root,
          fetch=lambda u: (200, "application/json", body))
    sid = conn.execute(
        "SELECT snapshot_id FROM admin_api_snapshot "
        "ORDER BY snapshot_id DESC LIMIT 1").fetchone()
    check("API — 응답이 저장된다", sid is not None, str(sid))

    _st, _h, page = _get(admin_api, conn, acc, root,
                         {"snapshot": str(sid[0])},
                         fetch=lambda u: (200, "", ""))
    html = page.decode("utf-8")
    check("API — 경로 전수가 나온다", "category.originPrice" in html)
    check("API — 배열은 첨자를 접는다", "options.choice[].code" in html)
    check("API — raw_response 에 섞이지 않는다",
          conn.execute("SELECT COUNT(*) FROM raw_response "
                       "WHERE request_url LIKE '%readside/vehicle/1'"
                       ).fetchone()[0] == 0)

    try:
        _post(admin_api, conn, acc,
              {"csrf": "t", "previewed": "1", "reason": "x",
               "url": "file:///etc/passwd"}, root,
              fetch=lambda u: (200, "", ""))
        check("API — https 아닌 URL 을 받지 않는다", False, "받았다")
    except (PolicyError, ValidationError):
        check("API — https 아닌 URL 을 받지 않는다", True)


# ── 8  도구 (STEP 135) ───────────────────────────────────────────────
def flow_tools(conn, acc, root) -> None:
    from web.views import TOOLS, admin_tools

    ran = 0
    for tool in TOOLS:
        _st, _h, page = _post(admin_tools, conn, acc,
                              {"csrf": "t", "previewed": "1",
                               "reason": "점검", "tool": tool["key"]}, root)
        if int(_st) == 200:
            ran += 1
    check("도구 — 전 종류가 실행된다", ran == len(TOOLS),
          f"{ran}/{len(TOOLS)}")

    before = _cfg(root, "warnings.json")
    _post(admin_tools, conn, acc,
          {"csrf": "t", "previewed": "1", "reason": "점검",
           "tool": "threshold"}, root)
    check("도구 — 결과는 제안일 뿐 config 를 바꾸지 않는다",
          _cfg(root, "warnings.json") == before)


# ── 9  계정 (STEP 126) ───────────────────────────────────────────────
def flow_users(conn, acc, root) -> None:
    from store.admin import create_account
    from web.views import admin_users

    uid, _ = create_account(conn, "사용자갑", ROLE_USER, T)
    try:
        _post(admin_users, conn, acc,
              {"csrf": "t", "account_id": str(uid), "action": "disable"},
              root)
        check("계정 — 사유 없이 중지되지 않는다", False, "중지됐다")
    except (PolicyError, ValidationError):
        check("계정 — 사유 없이 중지되지 않는다", True)

    _post(admin_users, conn, acc,
          {"csrf": "t", "account_id": str(uid), "action": "disable",
           "reason": "본인 요청"}, root)
    off = conn.execute("SELECT disabled_at FROM account WHERE account_id=?",
                       (uid,)).fetchone()[0]
    check("계정 — 사유를 주면 중지된다", off is not None)

    from store.admin import open_session, session_account
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    sid = open_session(conn, Account(uid, ROLE_USER, "사용자갑"), now)
    conn.execute("UPDATE account SET disabled_at=? WHERE account_id=?",
                 (T, uid))
    conn.commit()
    check("계정 — 중지된 계정의 세션은 anonymous 다",
          session_account(conn, sid, now).role == "anonymous")

    try:
        _post(admin_users, conn, acc,
              {"csrf": "t", "account_id": str(acc.account_id),
               "action": "role", "role": ROLE_USER,
               "reason": "관리자 0명 시험"}, root)
        n = conn.execute("SELECT COUNT(*) FROM account "
                         "WHERE role='admin' AND disabled_at IS NULL"
                         ).fetchone()[0]
        check("계정 — 관리자를 0명으로 만들지 않는다", n >= 1, f"{n}명")
    except (PolicyError, ValidationError):
        check("계정 — 관리자를 0명으로 만들지 않는다", True)


# ── 10  개발 요청 (STEP 137) ─────────────────────────────────────────
def flow_requests(conn, acc, root) -> None:
    from web.views import admin_requests

    _post(admin_requests, conn, acc,
          {"csrf": "t", "action": "create", "title": "옵션 근거",
           "body": "catalog 에 description 이 없다", "origin": "screen"},
          root)
    rid = conn.execute("SELECT request_id FROM dev_request "
                       "ORDER BY rowid DESC LIMIT 1").fetchone()[0]
    check("요청 — 생성된다", rid is not None)

    try:
        _post(admin_requests, conn, acc,
              {"csrf": "t", "action": "status", "request_id": rid,
               "status": "applied"}, root)
        check("요청 — applied 는 사유·STEP 없이 안 된다", False, "됐다")
    except (PolicyError, ValidationError):
        check("요청 — applied 는 사유·STEP 없이 안 된다", True)

    _post(admin_requests, conn, acc,
          {"csrf": "t", "action": "status", "request_id": rid,
           "status": "applied", "direction": "B 안 채택",
           "step_ref": "STEP 75"}, root)
    got = conn.execute("SELECT status, step_ref, direction FROM dev_request "
                       "WHERE request_id=?", (rid,)).fetchone()
    check("요청 — 사유·STEP 을 주면 전이된다", got == ("applied", "STEP 75",
                                                "B 안 채택"), str(got))

    _post(admin_requests, conn, acc,
          {"csrf": "t", "action": "status", "request_id": rid,
           "status": "requested", "direction": "재요청"}, root)
    _post(admin_requests, conn, acc, {"csrf": "t", "action": "export"}, root)
    out = os.path.join(root, "outputs")
    files = os.listdir(out) if os.path.isdir(out) else []
    check("요청 — md 로 내보내진다", bool(files), str(files[:1]))
    exported = conn.execute(
        "SELECT exported_at FROM dev_request WHERE request_id=?",
        (rid,)).fetchone()[0]
    check("요청 — 내보낸 것은 exported_at 을 갖는다", exported is not None)


# ── 11  권한 — 사용자는 관리 화면을 못 연다 ──────────────────────────
def flow_permission(conn, root) -> None:
    from web.routes import GET, POST, ROUTES
    from web.server import guard

    user = Account(9, ROLE_USER, "사용자")
    admin_routes = [r for r in ROUTES if r.path.startswith("/admin")]
    blocked = [r for r in admin_routes if guard(user, r) is not None]
    check("권한 — 사용자는 전 관리 화면에서 막힌다",
          len(blocked) == len(admin_routes),
          f"{len(blocked)}/{len(admin_routes)}")
    _ = (GET, POST)


def main() -> int:
    conn, root, acc = _env()
    if conn is None:
        print("carwatch.db 가 없어 건너뜁니다")
        return 0
    print("관리 화면 동작 시험 (13장 · 14장)")
    print("\n[1] 설정 변경")
    flow_config(conn, acc, root)
    print("\n[2] 배점 조정 → 재채점")
    flow_scoring(conn, acc, root)
    print("\n[3] 차종 추가")
    flow_targets(conn, acc, root)
    print("\n[4] 등록부 분류")
    flow_registry(conn, acc, root)
    print("\n[5] 실행 지시")
    flow_run(conn, acc, root)
    print("\n[6] 쿼리")
    flow_query(conn, acc, root)
    print("\n[7] API 조회")
    flow_api(conn, acc, root)
    print("\n[8] 도구")
    flow_tools(conn, acc, root)
    print("\n[9] 계정")
    flow_users(conn, acc, root)
    print("\n[10] 개발 요청")
    flow_requests(conn, acc, root)
    print("\n[11] 권한")
    flow_permission(conn, root)
    print()
    print("결과:", "통과" if not FAIL else f"실패 {len(FAIL)} — "
          + " / ".join(FAIL[:6]))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
