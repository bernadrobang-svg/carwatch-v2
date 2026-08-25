# -*- coding: utf-8 -*-
"""V1 수집 검증 — 다 받았는가 · 라벨이 맞는가.

지시서   6장 STEP 55 · 5장 STEP 53
근거     V1-04 거부 1건이라도 있으면 URL·응답 변경 신호다 (2장 STEP 25a)
         V1-08 전량 실패는 코드 문제로 가정한다.  차단으로 단정하지 않는다
"""
from __future__ import annotations

import os as _os

# ★ 검사 사본을 /tmp 에 두지 않는다 — 921MB tmpfs 인데 DB 가 484MB 다.
#   실측 08-17: 「database or disk is full」로 검사가 통째로 죽었다
CHECK_TMP = _os.path.join(
    _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
    "outputs", "check-tmp")

from validate.base import (
    not_applicable,
    Check, FATAL, KIND_CODE, KIND_CONTRACT, KIND_EXTERNAL, KIND_TOTAL, WARN,
    _cfg, result,
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
    # ★ V1-23·V1-24 는 규격이 카탈로그 조합 전수에 배정했다 (개정 327).
    #   개발측이 만든 이 검사는 V1-25 로 옮긴다 — 번호는 규격이 정한다 (규칙 2)
    "V1-25": Check("V1", "V1-25", "ok 로 저장된 원문이 온전한가", FATAL, "run",
                   "조각을 이어붙이지 못하고 낱개로 저장한 자리를 찾는다 "
                   "— 실측 08-17: facet 55조각이 ok 로 들어와 있었다. "
                   "「실패 안 났다」와 「제대로 들어왔다」는 다르다 (개정 307)",
                   KIND_CODE,
                   # ★ 누적이다.  조각으로 저장된 원문은 실행이 끝난 뒤에도
                   #   DB 에 그대로 남는다.  이번 실행분만 보면 08-17 의
                   #   facet 55조각을 영영 못 찾는다
                   cumulative=True),
    "V1-23": Check("V1", "V1-23", "필요한 조합 대비 받은 카탈로그 비율",
                   FATAL, "run",
                   "매물에서 나온 것만 받지 않는다 — 필요한 조합을 먼저 세고 "
                   "못 받은 것은 사유를 남긴다.  not_called 는 우리 잘못이다. "
                   "마스터 지적 「카탈로그가 왜 없어. 수집하다가 버린 거겠지」 "
                   "(개정 327)",
                   KIND_CODE),
    "V1-27": Check("V1", "V1-27", "확인 안 됨을 ①②③④ 로 가른 표가 있음",
                   FATAL, "run",
                   "개정 434 — 「확인 안 됨」이 한 덩어리면 딜러 부실과 "
                   "★ 우리 부실이 섞인다. 섞인 채로는 배점도 컷도 뜻을 "
                   "못 갖는다. ★ 마스터 — 「너가 전체를 못 찾은 것을 "
                   "먼저 정리해야지」",
                   KIND_CONTRACT),
    "V1-28": Check("V1", "V1-28", "② ③ 건수가 지난번보다 안 늘었음",
                   FATAL, "run",
                   "개정 434 — ★ 우리 잘못이 늘면 실패다. 줄지 않는 것은 "
                   "봐주되 ★ 느는 것은 못 본다. 이력이 없으면 「줄었다」를 "
                   "말로만 하게 된다",
                   KIND_CONTRACT),
    "V1-26": Check("V1", "V1-26", "판정 축이 통째로 비지 않음", FATAL, "run",
                   "★ 개정 289 가 「못 본 축은 0점 + 확인 안 됨」이라 정했다. "
                   "그래서 축이 통째로 비어도 화면은 조용히 「확인 안 됨」을 "
                   "내고 등급만 낮아진다 — 아무도 안 놀란다 (개정 413 · S42 ①). "
                   "★ 개정 413 은 이것을 V1-24 라 했으나 그 번호는 개정 327 이 "
                   "이미 썼다 — 번호는 가이드 판단 대기다",
                   KIND_CONTRACT),
    "V1-24": Check("V1", "V1-24", "받은 카탈로그가 매물과 이어짐",
                   FATAL, "run",
                   "받았는데 매물과 안 이어지면 받은 것이 아니다 — "
                   "매칭 키를 검사한다 (개정 327)",
                   KIND_CODE),
    "V1-21": Check("V1", "V1-21", "받아 두고 안 펼쳐진 원문이 없음", FATAL,
                   "run",
                   "「받았다」와 「쓰였다」는 다르다.  목록 392쪽을 받고도 "
                   "core_listing 이 그대로였다 — 화면은 「저장했습니다」를 "
                   "냈고 사실이었지만 아무 일도 안 일어났다 (개정 268)",
                   KIND_CODE,
                   # ★ 누적이다.  이번 실행에서 목록을 안 받아도 어제 받아
                   #   둔 봉투가 안 펼쳐져 있으면 그것이 결함이다.
                   #   run_id 를 걸면 「안 받은 실행」에서 늘 통과가 된다
                   cumulative=True),
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



def _unknown_split_checks(conn, rid):
    """V1-27 · V1-28 — 확인 안 됨을 ①②③④ 로 가른 표 (개정 434 · 435).

    ★ 표가 「있는가」만 보지 않는다.  ★ 합이 맞는가를 본다 —
      ① + ② + ③ + ④ + 모름 = 확인 안 됨.  안 맞으면 어딘가를 안 센 것이다
    ★ ④ 는 개정 435 가 새로 가른 것이다 — 계산 쪽이 못 만드는 것
    ★ 표는 tools/unknown_split.py --write 가 만든다.  손으로 안 적는다
    """
    import json as _j
    import os as _o

    root = _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__)))
    hist = _o.path.join(root, "outputs", "unknown_split_history.json")
    if not _o.path.isfile(hist):
        return [not_applicable(C["V1-27"], rid,
                               "아직 안 돌렸다 — tools/unknown_split.py --write"),
                not_applicable(C["V1-28"], rid, "견줄 지난번이 없다")]
    with open(hist, encoding="utf-8") as f:
        runs = (_j.load(f).get("runs") or [])
    if not runs:
        return [not_applicable(C["V1-27"], rid, "이력이 비었다"),
                not_applicable(C["V1-28"], rid, "견줄 지난번이 없다")]
    now = runs[-1]

    # V1-27 — 24축이 다 있고 갈래 합이 맞는가
    with open(_o.path.join(root, "config", "scoring.json"),
              encoding="utf-8") as f:
        axes = set(_j.load(f)["components"])
    with open(_o.path.join(root, "config", "unknown_split.json"),
              encoding="utf-8") as f:
        mapped = set(_j.load(f)["axes"])
    bad27 = [f"{a} — 갈래표에 없다" for a in sorted(axes - mapped)]
    for axis, one in (now.get("by_axis") or {}).items():
        got = (one["1"] + one["2"] + one["3"]
               + one.get("4", 0) + one["?"])
        if got != one["n"]:
            bad27.append(f"{axis} — ①②③④모름 합 {got} "
                         f"!= 확인 안 됨 {one['n']}")

    # V1-28 — ② ③ 이 늘었는가.  ★ 준 것은 통과다
    if len(runs) < 2:
        v28 = not_applicable(C["V1-28"], rid,
                             f"1회째다 — 다음 실행부터 견준다 "
                             f"(② {now['kind2']} · ③ {now['kind3']} "
                             f"· ④ {now.get('kind4', 0)})")
    else:
        was = runs[-2]
        # ★★ 갈래별로 견주면 **갈래를 새로 나눌 때마다 실패**한다 —
        #   실측 08-21: 개정 435 가 ④ 를 신설하자 ④ 0 → 450 이 「늘었다」로
        #   잡혔다.  실제로는 ② 에 있던 450건이 ④ 로 옮겨간 것이다.
        #   ★ 우리 잘못의 **합**으로 본다.  갈래별 움직임은 곁들여 적는다
        def ours(one):
            return (one.get("kind2", 0) + one.get("kind3", 0)
                    + one.get("kind4", 0))

        # ★★ 실측 08-22 — 매물이 3,841 → 3,916 으로 늘자 ③ 도 75건 늘어
        #   「우리 잘못이 늘었다」로 잡혔다.  ★ 매물이 늘면 건수는 늘 늘어난다 —
        #   ★ 건수가 아니라 ★ 비율로 견준다.  「확인 안 됨」 대비 몫이다
        def share(one):
            base = one.get("unknown") or 0
            return (ours(one) / base) if base else 0.0

        up = []
        tol28 = 0.001          # ★ 반올림 흔들림만 눈감는다
        if share(now) > share(was) + tol28:
            up.append(f"★ 우리 잘못 몫이 {share(was):.1%} → {share(now):.1%} 로 "
                      f"늘었다 (건수 {ours(was)} → {ours(now)} · "
                      f"확인 안 됨 {was.get('unknown')} → {now.get('unknown')})")
        moved = [f"{name} {was.get(k, 0)} → {now.get(k, 0)}"
                 for k, name in (("kind2", "② 못 읽는다"),
                                 ("kind3", "③ 안 받는다"),
                                 ("kind4", "④ 계산이 못 만든다"))
                 if now.get(k, 0) != was.get(k, 0)]
        v28 = result(C["V1-28"], rid,
                     f"합 {ours(was)}",
                     f"합 {ours(now)} (② {now['kind2']} · ③ {now['kind3']} "
                     f"· ④ {now.get('kind4', 0)})", not up, up + moved)
    return [
        result(C["V1-27"], rid, f"{len(mapped)}축",
               f"확인 안 됨 {now['unknown']} · ② {now['kind2']} "
               f"· ③ {now['kind3']} · ④ {now.get('kind4', 0)}",
               not bad27, bad27[:6]),
        v28,
    ]


def _axis_empty_check(conn, rid):
    """V1-26 — 판정 축이 통째로 비지 않는가 (개정 413).

    두 가지를 함께 낸다
      ① 축 전건이 「확인 안 됨」인가        ← 이것이 fatal 이다
      ② 파서가 읽는 경로 중 어디서도 값이 안 오는 것  ← 목록으로 낸다

    ★ ②만으로 fatal 을 내지 않는다.  실측 08-19 — `floodDate` ·
      `robberDate` 는 침수·도난이 **일어난 매물에만** 채워지는 날짜다.
      한 건도 없으면 전건 null 이 맞다.  거짓 경보는 검사가 아니다
    ★ ①은 다르다.  축 하나가 통째로 비면 그 배점이 전건에서 사라진다
    """
    from parse.encar.paths import parser_paths
    from store.core import axis_paths_empty

    rows = conn.execute(
        "SELECT axis, COUNT(*), SUM(excluded) FROM result_axis"
        " GROUP BY axis").fetchall()
    if not rows:
        return not_applicable(C["V1-26"], rid, "판정 결과가 없다")
    bad = [f"{axis} — {n}건 전부 「확인 안 됨」이다.  축이 통째로 비었다"
           for axis, n, exc in rows if n and (exc or 0) >= n]
    empty = axis_paths_empty(conn, parser_paths())
    note = [f"{g['leaf']} — 어디서도 값이 안 온다 ({' · '.join(g['paths'])})"
            for g in empty]
    return result(C["V1-26"], rid, f"{len(rows)}축",
                  f"통째로 빈 축 {len(bad)} · 값이 안 오는 경로 {len(note)}",
                  not bad, (bad + note)[:8])


def run(conn, ctx) -> list:
    rid = ctx.run_id
    out = [_axis_empty_check(conn, ctx.run_id)]
    out += _unknown_split_checks(conn, ctx.run_id)

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
    out.append(_whole_body_check(conn, rid))
    out += _catalog_checks(conn, rid)
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
    probe = open_db(os.path.join(tempfile.mkdtemp(dir=_ensure_tmp()), "empty.db"),
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


def _sql_groups(body: str) -> list:
    """붙어 있는 문자열 리터럴을 한 덩어리로 묶는다 (파이썬 암묵 연결).

    ★ SQL 한 문장이 소스에서는 조각 넷일 수 있다.  조각 하나만 보면
      뒤 조각의 `WHERE run_id = ?` 를 놓친다
    ★ 반대로 함수 전체를 보면 안 된다 — 인자 이름이 `run_id` 라는 이유로
      전부 통과했다 (실측 08-18 · 되살림 시험에서 지렛대가 안 들었다)
    돌려줌   [(소스 위치, 이어붙인 글), …]
    """
    import io as _io
    import token as _token
    import tokenize as _tokenize

    off, n = [0], 0
    for line in body.splitlines(keepends=True):
        n += len(line)
        off.append(n)
    out, cur, pos = [], [], 0
    skip = (_token.NL, _token.NEWLINE, _token.COMMENT, _token.INDENT,
            _token.DEDENT)
    for tk in _tokenize.generate_tokens(_io.StringIO(body).readline):
        if tk.type == _token.STRING:
            if not cur:
                pos = off[tk.start[0] - 1] + tk.start[1]
            cur.append(tk.string)
            continue
        if tk.type in skip:
            continue
        if cur:
            out.append((pos, "".join(cur)))
            cur = []
    if cur:
        out.append((pos, "".join(cur)))
    return out


def _cumulative_codes() -> set:
    """「누적」이라고 적어 둔 검사 코드 (b-v1v2 「V1-16 의 대상」).

    ★ 규격이 요구하는 것은 「검사마다 이번 실행분인가 누적인가를 적는 것」이지
      모든 조회에 run_id 를 거는 것이 아니다 —
      「전 검사에 run_id 를 일괄로 거는 것.  누적 검사가 무의미해진다」
    """
    return {code for code, chk in C.items() if chk.cumulative}


def _run_scope_check(run_id: str):
    """★ 검사가 옛 실행분을 보면 정상 동작이 결함으로 잡힌다 (실측 V1-14).

    ★ 「누적」이라 적어 둔 검사는 대상이 아니다.  V1-21(안 펼쳐진 봉투)·
      V1-25(조각으로 저장된 원문)는 어제 받은 것에서도 찾아야 한다.
      실측 08-18 — 이 둘을 걸러 내지 않아 V1-16 이 계속 fatal 이었다.
      ★ 「누적이라 적었는가」를 보는 것이지 「run_id 가 없어도 봐준다」가 아니다
    """
    import os
    import re

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    known = _cumulative_codes()
    bad = []
    for base, dirs, files in os.walk(os.path.join(root, "validate")):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in sorted(files):
            if f not in RUN_SCOPED_PHASES:
                continue
            body = open(os.path.join(base, f), encoding="utf-8").read()
            for pos, sql in _sql_groups(body):
                hit = [t for t in RUN_SCOPED
                       if re.search(rf"\bFROM {t}\b", sql)]
                if not hit or "run_id" in sql:
                    continue
                # ★ 그 조회가 든 함수가 내는 검사가 전부 「누적」이면 대상이
                #   아니다.  검사를 하나도 안 내는 함수는 그대로 대상이다 —
                #   「어디에도 안 적혔다」를 봐주면 규격이 무의미해진다
                head = _enclosing_def(body, pos)
                mine = set(re.findall(r'C\["([\w-]+)"\]', head))
                if mine and mine <= known:
                    continue
                where = f" ({', '.join(sorted(mine))})" if mine else ""
                bad.append(f"{f}: {hit[0]} 에 run_id 조건이 없다{where}")
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
            # ★★ `KNOWN_QUERY_KEYS` 는 ★ **엔카** 조립 규칙이다 (adapters/encar.py).
            #   ★ 다른 사이트에 대면 ★ 그 사이트 말이 죄다 「모르는 키」가 된다
            if site != "encar":
                continue
            # ★★ 한 차종에 ★ 질의가 여럿일 수 있다 (명령서 37-3 ③ —
            #   ★ 헤이딜러 G80 은 ★ 「더 올 뉴 G80 FL」·「더 올 뉴 G80」 둘이다).
            #   ★ ★ 그때는 ★ 리스트로 온다 — ★ 실측 08-24
            for one in (sq if isinstance(sq, list) else [sq]):
                if not isinstance(one, dict):
                    continue
                # ★ `_` 로 시작하는 키는 ★ 메모다 (`_확인` 등) — ★ 조건이 아니다
                real = {k for k in one if not str(k).startswith("_")}
                for k in sorted(real - KNOWN_QUERY_KEYS):
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


def _whole_probe() -> int:
    """최근 몇 건을 볼 것인가.  ★ 임계값은 config 다 (V4-13)."""
    import json as _json
    import os as _os

    root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    with open(_os.path.join(root, "config", "checks.json"),
              encoding="utf-8") as f:
        return int(_json.load(f)["whole_body_probe"])


def _whole_body_check(conn, rid):
    """V1-25 — ok 원문이 통째로 들어왔는가 (개정 307).

    ★ 사고 08-17 — 화면은 바이트를 나눠 보냈는데 서버가 이어붙일 줄 몰라
      조각 55개가 각각 「ok」로 저장됐다.  수집 화면은 「실패 0건」이라 했다
    ★ JSON 을 받는 자리는 JSON 이어야 한다.  그것이 「온전하다」의 뜻이다
    금지   길이로만 판단하는 것 — 조각도 2만 바이트는 넘는다
    """
    import json as _json

    bad = []
    for kind in ("facet", "list"):
        # ★★ 08-26 — ★ 엔카 원문만 본다.  ★ 다른 사이트의 목록은 ★ HTML 이라
        #   ★ 「JSON 이 아니다」로 잡히면 ★ 거짓 실패가 된다 (명령서 3-2)
        for raw_id, body in conn.execute(
            "SELECT id, body FROM raw_response"
            " WHERE endpoint=? AND status='ok' AND site='encar'"
            " ORDER BY id DESC LIMIT ?", (kind, _whole_probe())
        ):
            try:
                _json.loads(body)
            except (ValueError, TypeError):
                bad.append(f"{kind} raw {raw_id} 이 JSON 이 아니다 "
                           f"({len(body):,}B) — 조각일 수 있다")
                break
    return result(C["V1-25"], rid, 0, len(bad), not bad, bad[:6])


# 카탈로그 조합 전수 조회는 store 에 있다 (개정 327).
# ★ report 화면도 같은 것을 쓴다 — report 는 validate 를 못 부른다 (V4-22)
from store.core import OUR_FAULT, catalog_coverage   # noqa: E402


def _catalog_checks(conn, rid):
    """V1-23 · V1-24 — 카탈로그 조합 전수 (개정 327).

    ★ 마스터 지적 「카탈로그가 왜 없어. 수집하다가 버린 거겠지」.
      147건을 받았는데 필요한 조합이 몇 개인지 센 적이 없었다
    ★ 비율을 「내는가」가 검산이다.  100%를 요구하는 것이 아니다 —
      엔카가 안 주는 조합이 있다 (실측 08-18: 22조합이 `[]` 다).
      우리 잘못(not_called · http_error · parse_failed)에만 걸린다
    """
    got = catalog_coverage(conn)
    need, ok = got["need"], got["ok"]
    if not need:
        return [not_applicable(C["V1-23"], rid, "매물에 카탈로그 키가 없다"),
                not_applicable(C["V1-24"], rid, "매물에 카탈로그 키가 없다")]
    ratio = len(ok & need) / len(need)
    lines, ours = [], []
    for why, keys in sorted(got["why"].items(),
                            key=lambda kv: -sum(got["weight"].get(k, 0)
                                                for k in kv[1])):
        if not keys:
            continue
        rows = sum(got["weight"].get(k, 0) for k in keys)
        note = f"{why} {len(keys)}조합 · 매물 {rows:,}건 (예: {keys[0]})"
        if why in OUR_FAULT:
            ours.append(note + "  ★ 우리 잘못이다")
        else:
            lines.append(note)
    blind = sum(n for k, n in got["weight"].items() if k not in got["linked"])
    actual = (f"{len(ok & need)}조합 · {ratio * 100:.1f}% · "
              f"카탈로그 없는 매물 {blind:,}건"
              + (f" · 사이트가 안 줌 {'; '.join(lines)}" if lines else ""))
    # V1-24 — 받았는데 매물과 안 이어진 것.  받은 것이 아니다
    bad24 = []
    stray = got["linked"] - need
    if stray:
        bad24.append(f"사전에 있는데 매물과 안 이어지는 조합 {len(stray)}개"
                     f" (예: {sorted(stray)[0]})")
    lost = sorted(ok & need - got["linked"])
    if lost:
        bad24.append(f"ok 로 받았는데 사전에 안 들어간 조합 {len(lost)}개"
                     f" (예: {lost[0]}) — 받은 것이 아니다")
    return [
        result(C["V1-23"], rid, f"{len(need)}조합", actual, not ours, ours[:6]),
        result(C["V1-24"], rid, 0, len(bad24), not bad24, bad24[:4]),
    ]


def _unparsed_envelope_check(conn, rid):
    """V1-21 — 받아 두고 안 펼쳐진 목록 원문이 있는가 (개정 268).

    ★ 「받았다」와 「쓰였다」를 가른다.  raw_response 에 있는데 그 안의
      매물이 core_listing 에 없으면, 저장은 됐고 아무 일도 안 일어난 것이다
    ★ 원문을 전부 펼쳐 보지 않는다 — 봉투마다 첫 매물 하나만 대조한다.
      전건을 펼치면 검사가 파이프라인만큼 무거워진다
    """
    import json as _j

    rows = conn.execute(
        # ★ 엔카 봉투(`SearchResults`)를 펼친 것인지 본다 — ★ 엔카만이다
        "SELECT id, origin, body FROM raw_response "
        "WHERE endpoint='list' AND status='ok' AND origin <> 'import'"
        "  AND site='encar'"
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


def _ensure_tmp() -> str:
    """검사 사본 자리.  ★ /tmp(tmpfs)가 아니라 디스크에 둔다."""
    _os.makedirs(CHECK_TMP, exist_ok=True)
    return CHECK_TMP
