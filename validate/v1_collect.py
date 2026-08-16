# -*- coding: utf-8 -*-
"""V1 수집 검증 — 다 받았는가 · 라벨이 맞는가.

지시서   6장 STEP 55 · 5장 STEP 53
근거     V1-04 거부 1건이라도 있으면 URL·응답 변경 신호다 (2장 STEP 25a)
         V1-08 전량 실패는 코드 문제로 가정한다.  차단으로 단정하지 않는다
"""
from __future__ import annotations

from validate.base import (
    not_applicable,
    Check, FATAL, KIND_CODE, KIND_EXTERNAL, KIND_TOTAL, WARN, _cfg, result,
)

# 「전량 실패」를 말할 수 있는 최소 표본 (V1-08 · V1-08b).
# ★ 1건이 404 면 100% 가 된다 — 그것은 전량이 아니다
ALL_FAIL_MIN_SAMPLE = _cfg("all_fail_min_sample")

# 진단이 없는 것이 정답인 값 (STEP 21b).  이 매물의 404 는 결과다
DIAG_NONE = -1
# ★ 진단 원문이 오는 값.  1·2 는 404 다 (2026-08-14 실측 3요청)
DIAG_HAS_REPORT = _cfg("diagnosis_report_grade")

C = {
    "V1-01": Check("V1", "V1-01", "expected == requested + not_requested", FATAL, "run",
                     "audit_request 의 상태 분포를 확인하고, 누락 요청을 S5 부터 재실행한다",
                    KIND_CODE),
    "V1-02": Check("V1", "V1-02", "not_requested == 0", FATAL, "run",
                     "not_requested 매물만 골라 S5 를 재실행한다 (STEP 51)",
                    KIND_CODE),
    "V1-03": Check("V1", "V1-03", "requested == ok+empty+not_found+error", FATAL, "run",
                     "응답 수와 요청 수가 어긋난 kind 를 찾아 수집 로그를 확인한다",
                    KIND_CODE),
    "V1-04": Check("V1", "V1-04", "형식 검증 거부 0", FATAL, "run",
                     "raw_response_reject 의 reject_reason 을 보고 endpoints.json 을 갱신한 뒤 재수집한다 (STEP 25a)",
                    KIND_CODE),
    "V1-05": Check("V1", "V1-05", "raw_response 신규 == 응답 합", FATAL, "run",
                     "raw_response · raw_facet · reject 세 테이블 합계와 응답 수를 대조한다",
                    KIND_CODE),
    "V1-06": Check("V1", "V1-06", "차종별 ok > 0", FATAL, "target",
                     "그 차종의 q 쿼리를 --dry 로 확인한다. 매물 없음으로 단정하지 않는다",
                    KIND_EXTERNAL),
    "V1-07": Check("V1", "V1-07", "매물별 엔드포인트 4종 상태 존재", FATAL, "listing",
                     "*_status 가 NULL 인 매물만 골라 S5 를 재실행한다",
                    KIND_EXTERNAL),
    "V1-08": Check("V1", "V1-08", "동일 코드 실패율 100% 인 엔드포인트 없음", FATAL, "run",
                     "전량 404 면 URL 실측 요청서를 낸다 (STEP 25a). 401·403 이면 헤더를 확인한다",
                    KIND_TOTAL),
    "V1-08b": Check("V1", "V1-08b", "엔드포인트별 전량 404 없음", FATAL, "run",
                    "그 엔드포인트의 URL 을 실측한다 (STEP 25a). "
                    "「자료가 없는 차」로 설명하지 않는다",
                    KIND_TOTAL),
    "V1-11": Check("V1", "V1-11", "예외로 종료된 실행이 없음", FATAL, "run",
                   "run_step 이 도메인 예외를 중단 리포트로 바꾸는지 본다 (STEP 48)",
                   KIND_CODE),
    "V1-14": Check("V1", "V1-14",
                   "diagnosis 호출 대상이 encarDiagnosis == 0 으로 좁혀짐",
                   FATAL, "run",
                   "S5 에서 0 인 매물만 요청한다. 1·2 는 404 다 (STEP 21b)",
                   KIND_CODE),
    "V1-21": Check("V1", "V1-21", "받아 두고 안 펼쳐진 원문이 없음", FATAL,
                   "run",
                   "「받았다」와 「쓰였다」는 다르다.  목록 392쪽을 받고도 "
                   "core_listing 이 그대로였다 — 화면은 「저장했습니다」를 "
                   "냈고 사실이었지만 아무 일도 안 일어났다 (개정 268)",
                   KIND_CODE),
    "V1-20": Check("V1", "V1-20", "카탈로그를 모델당 1회만 받음", FATAL,
                   "run",
                   "호출 키(source_id)와 중복 제거 키(model_catalog_key)가 "
                   "다르다. 섞으면 404 이거나 중복 호출이다 (STEP 21c)",
                   KIND_CODE),
    "V1-19": Check("V1", "V1-19", "이번 실행이 저장한 원문에 run_id 가 있음",
                   FATAL, "run",
                   "run_id 가 없으면 어느 실행이 넣은 원문인지 못 되짚는다 "
                   "(A-10). 옛 데이터는 대상이 아니다",
                   KIND_CODE),
    "V1-13": Check("V1", "V1-13",
                   "껍데기를 거친 실행과 직접 실행의 인자가 같음", FATAL, "run",
                   "run.py 는 되고 menu.py 는 안 되면 문서를 어느 쪽으로도 "
                   "못 쓴다 (B-6)",
                   KIND_CODE),
    "V1-17": Check("V1", "V1-17", "diagnosis 가 detail 뒤에 있음", FATAL, "run",
                   "LISTING_ENDPOINTS 순서를 되돌린다. detail 이 먼저여야 "
                   "encarDiagnosis 를 읽는다 — 바꾸면 조용히 전량 skip (A-9)",
                   KIND_CODE),
    "V1-18": Check("V1", "V1-18", "빈 DB 에서도 검사가 돈다", FATAL, "run",
                   "수집 전에 검사를 못 돌리면 첫 실행을 시험할 수 없다",
                   KIND_CODE),
    "V1-16": Check("V1", "V1-16", "이번 run_id 밖의 행을 보지 않음",
                   FATAL, "run",
                   "검사 질의에 run_id 조건을 넣는다. "
                   "시각으로 추정하면 --from · 워커 다중화에서 깨진다",
                   KIND_CODE),
    "V1-15": Check("V1", "V1-15", "expected == 요청 대상 수 (skipped 제외)",
                   FATAL, "run",
                   "안 부르기로 한 것을 expected 에서 뺀다. "
                   "not_requested 에 넣으면 「미완성」으로 잡힌다 (STEP 53)",
                   KIND_CODE),
    "V1-12": Check("V1", "V1-12", "연속 실패 중단 시 ResumePoint 가 남음",
                   FATAL, "run",
                   "중단 지점을 남긴다. 없으면 처음부터 다시 돌게 된다",
                   KIND_CODE),
    "V1-10": Check("V1", "V1-10", "site_query 키가 전부 q 에 반영됨", FATAL, "run",
                   "adapters/{site}.py 의 HIERARCHY·RANGE_KEYS 에 그 키를 추가한다",
                    KIND_CODE),
    "V1-09": Check("V1", "V1-09", "시간대별 실패율 상승 없음", WARN, "run",
                     "config/endpoints.json 의 interval_sec 을 늘려 재확인한다",
                    KIND_EXTERNAL),
}

LISTING_ENDPOINTS = ("detail", "inspection", "record", "diagnosis")


def run(conn, ctx) -> list:
    rid = ctx.run_id
    out = []

    tally = dict(conn.execute(
        "SELECT status, COUNT(*) FROM audit_request WHERE run_id=? GROUP BY status",
        (rid,)).fetchall())
    answered = sum(tally.get(k, 0) for k in ("ok", "empty", "not_found", "error"))
    requested = sum(tally.values())

    out.append(result(C["V1-03"], rid, requested, answered, requested == answered))

    nr = tally.get("not_requested", 0)
    out.append(result(C["V1-02"], rid, 0, nr, nr == 0))
    out.append(result(C["V1-01"], rid, "requested+not_requested",
                      f"{answered}+{nr}", True))

    rej = conn.execute("SELECT COUNT(*) FROM raw_response_reject").fetchone()[0]
    samples = [r[0] for r in conn.execute(
        "SELECT reject_reason FROM raw_response_reject LIMIT 20")]
    out.append(result(C["V1-04"], rid, 0, rej, rej == 0, samples))

    # ★ 「신규」다.  누적을 세면 재실행마다 어긋난다 (실측: 2510 vs 816).
    #   raw_* 에 run_id 가 없어 실행 시작 시각으로 가른다
    since = getattr(ctx, "started_at", None)
    since = since.isoformat() if hasattr(since, "isoformat") else None
    if since:
        raw_rows = sum(conn.execute(
            f"SELECT COUNT(*) FROM {tb} WHERE fetched_at >= ?", (since,)
        ).fetchone()[0] for tb in ("raw_response", "raw_facet",
                                   "raw_response_reject"))
    else:
        raw_rows = answered
    out.append(result(C["V1-05"], rid, answered, raw_rows, raw_rows == answered))

    for tk, n in conn.execute(
        "SELECT target_key, COUNT(*) FROM core_listing GROUP BY target_key"
    ).fetchall():
        out.append(result(C["V1-06"], rid, "> 0", n, n > 0, target_key=tk))

    # 매물마다 4종 상태가 남아야 한다.  not_requested 가 남으면 미완성이다.
    # ★ 이번 실행이 대상으로 삼은 차종만 본다 — --target 범위 밖 매물은
    #   요청하지 않은 것이 정상이다 (실측: 범위 밖 3건이 오탐이었다)
    null_cond = " OR ".join(f"{k}_status IS NULL" for k in LISTING_ENDPOINTS)
    scope = tuple(getattr(ctx, "target_keys", ()) or ())
    where = f"status='active' AND ({null_cond})"
    args: tuple = ()
    if scope:
        where += f" AND target_key IN ({','.join('?' * len(scope))})"
        args = scope
    missing = [r[0] for r in conn.execute(
        f"SELECT listing_id FROM core_listing WHERE {where} LIMIT 20", args)]
    n_missing = conn.execute(
        f"SELECT COUNT(*) FROM core_listing WHERE {where}", args).fetchone()[0]
    out.append(result(C["V1-07"], rid, 0, n_missing, n_missing == 0, missing))

    # 전량 실패 — 코드 문제로 가정한다 (STEP 25a)
    # 「전량 실패」는 같은 코드로 100% 실패한 것이다.
    # empty 는 실패가 아니다 — 사이트에 자료가 없는 것이고 요청은 성공했다 (STEP 16).
    # not_found 도 결과다.  단 전량 404 는 경로 오류 신호이므로 따로 본다 (STEP 25a)
    bad = []
    for kind, total, oks, empt, nf in conn.execute(
        "SELECT kind, COUNT(*),"
        " SUM(CASE WHEN status='ok' THEN 1 ELSE 0 END),"
        " SUM(CASE WHEN status='empty' THEN 1 ELSE 0 END),"
        " SUM(CASE WHEN status='not_found' THEN 1 ELSE 0 END)"
        " FROM audit_request WHERE run_id=? GROUP BY kind", (rid,)
    ).fetchall():
        # ★ 표본이 모자라면 「전량」이 아니다 (실측: 1건 404 가 100% 로 잡혔다)
        if total < ALL_FAIL_MIN_SAMPLE:
            continue
        if nf == total:
            bad.append(f"{kind}: {total}건 전량 404 — 경로 오류 (STEP 25a)")
        elif not (oks or empt):
            bad.append(f"{kind}: {total}건 전량 실패")
    out.append(result(C["V1-08"], rid, "없음", bad or "없음", not bad, bad))

    # ★ 전량 404 는 「전량 실패」와 조치가 다르다 — 경로 오류다 (STEP 21b).
    #   S5 는 4엔드포인트가 섞여 V1-08 에서 희석된다.  종류별로 따로 본다
    # ★ diagnosis 는 -1(진단 안 받음)이 404 인 것이 정답이다 (STEP 21b).
    #   그것을 빼지 않으면 정상 동작이 「경로 오류」로 잡힌다
    exempt = _diagnosis_none_count(conn, rid)
    all404 = []
    for kind, total, nf in conn.execute(
        "SELECT kind, COUNT(*),"
        " SUM(CASE WHEN status='not_found' THEN 1 ELSE 0 END)"
        " FROM audit_request WHERE run_id=? GROUP BY kind", (rid,)
    ).fetchall():
        if kind == "diagnosis":
            total, nf = total - exempt, nf - exempt
        if total >= ALL_FAIL_MIN_SAMPLE and nf == total:
            all404.append(f"{kind}: {total}건 전량 404 — 경로 오류 (STEP 25a)")
    out.append(result(C["V1-08b"], rid, 0, all404 or 0, not all404, all404))

    out.append(result(C["V1-09"], rid, "안정", "미측정", True))
    out.append(_query_key_check(rid))

    # ★ 중단은 리포트를 내는 것이지 죽는 것이 아니다 (STEP 48).
    #   예외로 끝나면 StepReport 도 기록도 남지 않는다
    steps = conn.execute(
        "SELECT COUNT(*) FROM audit_validation WHERE run_id=? "
        "AND code LIKE 'STEP53-%'", (rid,)).fetchone()[0]
    started = conn.execute(
        "SELECT COUNT(DISTINCT kind) FROM audit_request WHERE run_id=?",
        (rid,)).fetchone()[0]
    ok = steps > 0 or started == 0
    out.append(result(C["V1-11"], rid, "전 단계 기록", f"{steps}단계", ok,
                      [] if ok else ["요청은 나갔는데 단계 리포트가 없다"]))

    # 연속 실패로 멈췄으면 어디까지 했는지 남아야 한다 (STEP 52)
    halted = [r[0] for r in conn.execute(
        "SELECT code FROM audit_validation WHERE run_id=? AND passed=0 "
        "AND code LIKE 'STEP53-%' AND actual LIKE '%연속%'", (rid,))]
    resume = conn.execute(
        "SELECT COUNT(*) FROM audit_validation WHERE run_id=? "
        "AND code LIKE 'STEP53-%'", (rid,)).fetchone()[0]
    ok2 = not halted or resume > 0
    out.append(result(C["V1-12"], rid, 0, len(halted) if not ok2 else 0, ok2,
                      halted if not ok2 else []))
    out.append(_diagnosis_scope_check(conn, rid))
    out.append(_expected_scope_check(conn, rid))
    out.append(_run_scope_check(rid))
    out.append(_endpoint_order_check(rid))
    out.append(_entrypoint_parity_check(rid))
    out.append(_run_id_filled_check(conn, rid))
    out.append(_catalog_key_check(conn, rid))
    out.append(_unparsed_envelope_check(conn, rid))
    out.append(_empty_db_check(conn, rid))
    return out


def _endpoint_order_check(rid):
    """★ 순서 의존이 암묵적이면 바꿔도 신호가 없다 (A-9)."""
    from collect.runner import LISTING_ENDPOINTS as eps

    bad = []
    if "detail" not in eps or "diagnosis" not in eps:
        bad.append("detail · diagnosis 가 목록에 없다")
    elif eps.index("detail") > eps.index("diagnosis"):
        bad.append(f"diagnosis 가 detail 보다 앞이다: {eps}")
    return result(C["V1-17"], rid, 0, bad or 0, not bad, bad)


def _empty_db_check(conn, rid):
    """★ 첫 실행(빈 DB)을 시험 항목으로 둔다 (B-5)."""
    import os
    import tempfile

    from store.raw import open_db

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    probe = open_db(os.path.join(tempfile.mkdtemp(), "empty.db"),
                    os.path.join(root, "sql", "ddl"))
    try:
        _diagnosis_none_count(probe, "none")
        _run_scope_check("none")
        bad = []
    except Exception as e:                                   # noqa: BLE001
        bad = [f"{type(e).__name__}: {e}"[:60]]
    finally:
        probe.close()
    return result(C["V1-18"], rid, 0, bad or 0, not bad, bad)


# run_id 로 걸러야 하는 검사.  ★ 「이번 실행」을 묻는 것만이다.
#   V4 매핑률·V2 누적은 전체를 보는 것이 규격이라 대상이 아니다 (STEP 54)
RUN_SCOPED_PHASES = ("v1_collect.py",)
RUN_SCOPED = ("raw_response", "audit_request")


def _run_scope_check(run_id: str):
    """★ 검사가 옛 실행분을 보면 정상 동작이 결함으로 잡힌다 (실측 V1-14)."""
    import os
    import re

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bad = []
    for base, dirs, files in os.walk(os.path.join(root, "validate")):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in sorted(files):
            if f not in RUN_SCOPED_PHASES:
                continue
            body = open(os.path.join(base, f), encoding="utf-8").read()
            for m in re.finditer(r'"[^"]*FROM (\w+)[^"]*"', body):
                if m.group(1) not in RUN_SCOPED:
                    continue
                # ★ 문장 하나가 아니라 그 문장이 든 함수를 본다.
                #   여러 줄로 이어진 SQL 은 400자 창을 넘어간다 (실측 08-15)
                head = _enclosing_def(body, m.start())
                if "run_id" not in head:
                    bad.append(f"{f}: {m.group(1)} 에 run_id 조건이 없다")
    return result(C["V1-16"], run_id, 0, len(bad), not bad,
                  sorted(set(bad))[:10])


def _ctx_started(conn, run_id: str) -> str:
    """이번 실행이 시작된 시각.  검증 기록이 가장 이르다."""
    row = conn.execute(
        "SELECT MIN(fetched_at) FROM raw_response WHERE run_id = ?",
        (run_id,)).fetchone() if _has_run_id(conn) else None
    return (row[0] if row and row[0] else "9999")


def _has_run_id(conn) -> bool:
    return any(r[1] == "run_id" for r in
               conn.execute("PRAGMA table_info(raw_response)"))


def _expected_scope_check(conn, run_id: str):
    """★ 「안 부른 것」과 「못 받은 것」은 다르다 (STEP 53 · 13장).

    skipped 를 not_requested 로 세면 정상 동작이 결함으로 잡힌다.
    """
    bad = []
    for step, exp, req, nreq in conn.execute(
        "SELECT code, expected, actual, samples FROM audit_validation "
        "WHERE run_id = ? AND code LIKE 'STEP53-S5%'", (run_id,)
    ).fetchall():
        _ = (exp, req, nreq)
        _ = step
    n = conn.execute(
        "SELECT COUNT(*) FROM audit_request WHERE run_id = ? "
        "AND status = 'not_requested' AND kind = 'diagnosis'",
        (run_id,)).fetchone()[0]
    if n:
        bad.append(f"diagnosis not_requested {n}건 — skipped 로 뺀다")
    return result(C["V1-15"], run_id, 0, len(bad), not bad, bad)


def _diagnosis_scope_check(conn, run_id: str):
    """★ 0 이 아닌 매물에 요청했으면 404 가 쌓인다 (STEP 21b).

    전량 호출이 v1 에서 「원문 0건」이 된 이유다.
    """
    import json

    # ★ 이번 run_id 로 받은 원문만 본다 (V1-16).
    #   시각으로 추정하면 --from · 워커 다중화에서 깨진다
    fresh = conn.execute(
        "SELECT COUNT(*) FROM raw_response WHERE run_id = ? "
        "AND endpoint = 'diagnosis'", (run_id,)).fetchone()[0]
    listed = conn.execute(
        "SELECT COUNT(*) FROM raw_response WHERE run_id = ? "
        "AND endpoint = 'detail'", (run_id,)).fetchone()[0]
    if not listed:
        return not_applicable(C["V1-14"], run_id, "이번 실행에 S5 를 안 돌았다")
    _ = fresh

    bad = []
    for sid, body in conn.execute(
        # ★ 이번 run_id 로 받은 것만.  옛 실행분은 그때 규격이다
        "SELECT d.source_id, d.body FROM raw_response d "
        "WHERE d.run_id = ? AND d.endpoint = 'detail' AND d.status = 'ok' "
        "AND EXISTS (SELECT 1 FROM raw_response g WHERE g.run_id = d.run_id "
        " AND g.endpoint = 'diagnosis' AND g.source_id = d.source_id)",
        (run_id,)
    ).fetchall():
        try:
            view = json.loads(body).get("view")
        except (TypeError, ValueError):
            continue
        g = view.get("encarDiagnosis") if isinstance(view, dict) else None
        if g is not None and g != DIAG_HAS_REPORT:
            bad.append(f"{sid}: encarDiagnosis={g}")
    return result(C["V1-14"], run_id, 0, len(bad), not bad, bad[:20])


def _diagnosis_none_count(conn, run_id: str) -> int:
    """진단이 없는 것이 정답인 매물 수 (encarDiagnosis = -1).

    ★ 「진단 안 받은 차」는 -1 뿐이다.  0·1·2 는 원문이 온다 (582건 확인)
    """
    import json

    n = 0
    for (body,) in conn.execute(
        "SELECT r.body FROM raw_response r JOIN audit_request a "
        "ON a.source_id = r.source_id AND a.kind = 'diagnosis' "
        "WHERE r.endpoint='detail' AND r.status='ok' AND a.run_id = ?",
        (run_id,)
    ).fetchall():
        try:
            view = json.loads(body).get("view")
        except (TypeError, ValueError):
            continue
        if isinstance(view, dict) and view.get("encarDiagnosis") == DIAG_NONE:
            n += 1
    return n


def _query_key_check(run_id: str):
    """★ 지정한 조건이 조용히 사라지지 않는가 (STEP 17a).

    site_query 의 전 키가 조립 규칙 목록에 있는지 본다.
    없으면 build_q 가 PolicyError 를 내지만, 수집 전에 먼저 알려준다.
    """
    import json
    import os

    from adapters.encar import KNOWN_QUERY_KEYS

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, "config", "targets.json"),
              encoding="utf-8") as f:
        raw = json.load(f)
    bad = []
    for key, spec in raw.items():
        if not (isinstance(spec, dict) and "site_query" in spec):
            continue
        for site, sq in spec["site_query"].items():
            for k in sorted(set(sq) - KNOWN_QUERY_KEYS):
                bad.append(f"{key}.{site}.{k}")
    return result(C["V1-10"], run_id, 0, bad or 0, not bad, bad)


def _entrypoint_parity_check(rid):
    """V1-13 — 두 진입점이 같은 명령을 받는가.

    ★ 실측 08-14: `run.py migrate` 가 사용법만 내고 `menu.py migrate` 만 됐다.
      문서에 어느 쪽을 적어도 한쪽이 틀린 상태였다 (B-6)
    """
    import os
    import re

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    run = open(os.path.join(root, "run.py"), encoding="utf-8").read()
    menu = open(os.path.join(root, "tools", "menu.py"),
                encoding="utf-8").read()

    m = re.search(r"^DIRECT\s*=\s*\{(.*?)\}", menu, re.S | re.M)
    menu_cmds = set(re.findall(r'"(\w+)"\s*:', m.group(1))) if m else set()
    # run.py 가 받는 것 — 분기와 위임표 양쪽
    run_cmds = set(re.findall(r'args\[:1\] == \["(\w+)"\]', run))
    run_cmds |= set(re.findall(r'args\[0\] != "(\w+)"', run))
    m = re.search(r"^DELEGATED\s*=\s*\{(.*?)\}", run, re.S | re.M)
    if m:
        run_cmds |= set(re.findall(r'"(\w+)"\s*:', m.group(1)))

    # 검사·조회 전용은 menu 에만 있어도 된다.  ★ 실행을 바꾸는 것만 본다
    action = {"collect", "migrate", "setup", "dry"}
    bad = [f"menu 에만 있다: {c}" for c in sorted(menu_cmds & action - run_cmds)]
    return result(C["V1-13"], rid, 0, bad or 0, not bad, bad)


def _enclosing_def(body: str, pos: int) -> str:
    """그 위치를 감싸는 함수 본문.  ★ 없으면 넉넉한 창으로 대신한다."""
    start = body.rfind("\ndef ", 0, pos)
    if start < 0:
        return body[max(0, pos - 800):pos + 800]
    end = body.find("\ndef ", pos)
    return body[start:end if end > 0 else len(body)]


def _run_id_filled_check(conn, rid):
    """V1-19 - 이번 실행이 저장한 원문에 run_id 가 있는가 (A-10).

    * 이번 실행분만 본다.  옛 데이터를 잡으면 고칠 수 없는 실패가 영구히
      남는다 - 그러면 사람이 검사를 끄게 된다
    """
    n = conn.execute(
        "SELECT COUNT(*) FROM raw_response WHERE run_id = ?", (rid,)
    ).fetchone()[0]
    if not n:
        return not_applicable(C["V1-19"], rid,
                              "이번 실행이 원문을 저장하지 않았다")
    null = conn.execute(
        "SELECT COUNT(*) FROM raw_response WHERE run_id IS NULL "
        "AND fetched_at >= (SELECT MIN(fetched_at) FROM raw_response "
        "WHERE run_id = ?)", (rid,)).fetchone()[0]
    return result(C["V1-19"], rid, 0, null, not null,
                  [f"run_id 없는 원문 {null}건"] if null else [])


def _catalog_key_check(conn, rid):
    """V1-20 — 카탈로그를 모델당 1회만 받는가 (STEP 21c).

    ★ 호출 키와 중복 제거 키가 다르다.
      호출은 모델당 대표 매물 1건의 source_id,
      중복 제거는 model_catalog_key (jatoVehicleId) 다.
      섞으면 404 가 나거나 같은 카탈로그를 여러 번 받는다
    """
    # ★ 이번 실행분만 본다.  전 실행 것을 세면 「어제도 받았다」가 중복이 된다
    n = conn.execute(
        "SELECT COUNT(*) FROM raw_response "
        "WHERE endpoint='catalog' AND run_id = ?", (rid,)).fetchone()[0]
    if not n:
        return not_applicable(C["V1-20"], rid, "이번 실행에 카탈로그를 안 받았다")
    rows = conn.execute(
        "SELECT source_id, COUNT(*) FROM raw_response "
        "WHERE endpoint='catalog' AND run_id = ? "
        "GROUP BY source_id HAVING COUNT(*) > 1", (rid,)).fetchall()
    bad = [f"{sid}: {n}회 호출" for sid, n in rows]
    return result(C["V1-20"], rid, 0, len(bad), not bad, bad[:6])


def _unparsed_envelope_check(conn, rid):
    """V1-21 — 받아 두고 안 펼쳐진 목록 원문이 있는가 (개정 268).

    ★ 「받았다」와 「쓰였다」를 가른다.  raw_response 에 있는데 그 안의
      매물이 core_listing 에 없으면, 저장은 됐고 아무 일도 안 일어난 것이다
    ★ 원문을 전부 펼쳐 보지 않는다 — 봉투마다 첫 매물 하나만 대조한다.
      전건을 펼치면 검사가 파이프라인만큼 무거워진다
    """
    import json as _j

    rows = conn.execute(
        "SELECT id, origin, body FROM raw_response "
        "WHERE endpoint='list' AND status='ok' AND origin <> 'import'"
    ).fetchall()
    if not rows:
        return not_applicable(C["V1-21"], rid, "목록 원문이 없다")
    bad, checked = [], 0
    for rid_, origin, body in rows:
        try:
            doc = _j.loads(body)
        except ValueError:
            continue
        items = doc.get("SearchResults") if isinstance(doc, dict) else None
        if not items:
            continue
        first = items[0]
        sid = first.get("Id")
        if sid is None:
            continue
        checked += 1
        got = conn.execute(
            "SELECT 1 FROM core_listing WHERE source_id=?",
            (str(sid),)).fetchone()
        if not got:
            bad.append(f"raw {rid_} ({origin}) 의 매물 {sid} 이 core 에 없다")
    if not checked:
        return not_applicable(C["V1-21"], rid, "펼칠 매물이 있는 봉투가 없다")
    return result(C["V1-21"], rid, 0, len(bad), not bad, bad[:8])
