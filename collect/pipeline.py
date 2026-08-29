# -*- coding: utf-8 -*-
"""실행 순서 · 중단 · 재처리 · 재개.

지시서   5장 STEP 47 (단계) · 48 (선행 조건) · 49 (순서) · 50 (중단)
         50a (재처리 결정표 ★ 단일 출처) · 51 (재조회) · 52 (재개) · 53 (산출 보고)
근거     조건 미충족 시 그 단계를 건너뛰지 않는다.  중단하고 보고한다.
금지     「조용히 넘어가기」.  v1 은 모든 사고가 조용히 지나간 뒤 발견됐다.
         진행 상태를 메모리·전역 변수에만 두는 것 (0장 STEP 8-④).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import sqlite3
from dataclasses import dataclass

from contracts import ResumePoint, StepReport
from errors import CarWatchError, PolicyError, ValidationError

# ── STEP 47 단계 목록 ────────────────────────────────────────────────
# S2 는 읽기 전용이라 S0 승인과 무관하게 먼저 돌 수 있다.
# ★ 네트워크가 없는 단계.  단계 하나를 한 트랜잭션으로 묶는다 (STEP 33).
#   금지   수집 단계(S1·S2·S5·S7)를 넣는 것 — 원문은 건별로 커밋한다 (P3)
BATCH_STEPS: frozenset[str] = frozenset({"S4", "S6", "S6a", "S8", "S9", "S10"})

# ★ S4 가 훑는 봉투 범위 (STEP 50a).  결정표에 함께 적는다.
#   없으면 매번 다르게 판단한다 — 실측: expected 가 257 → 513 으로 늘었다
ENVELOPE_ALL = "all"
ENVELOPE_THIS_RUN = "this_run"
ENVELOPE_SCOPE: dict[str, str] = {
    "listing_updated": ENVELOPE_THIS_RUN,   # 옛 봉투는 이미 CORE 에 있다
    "raw_missing": ENVELOPE_THIS_RUN,
    "parse_rule": ENVELOPE_ALL,             # 재파싱의 목적이 그것이다
    "site_response_shape": ENVELOPE_ALL,
}


def envelope_scope(reason: str | None) -> str:
    """반환   'all' · 'this_run'.  사유가 없으면 신규 수집으로 본다."""
    if reason is None:
        return ENVELOPE_THIS_RUN
    if reason not in REPROCESS_TABLE:
        # ★ 화면이 고른 값이 표에 없는 것은 입력 오류다.  500 을 내면
        #   사용자가 무엇이 틀렸는지 모른다 (C-2 · 실측 08-15)
        raise ValidationError(f"재처리 결정표에 없는 사유: {reason}",
                              step="STEP 50a")
    return ENVELOPE_SCOPE.get(reason, ENVELOPE_THIS_RUN)

STEPS: tuple[str, ...] = (
    "S0", "S1", "S2", "S3", "S4", "S5", "S6",
    "S6a", "S7", "S8", "S8.5", "S9", "S10", "S11", "S12",
)

# 단계 → 선행 단계 (STEP 47 표)
PRECEDES: dict[str, tuple[str, ...]] = {
    "S0": (),
    "S1": ("S0",),
    "S2": (),
    "S3": ("S1", "S2"),
    "S4": ("S1", "S3"),
    "S5": ("S4",),
    "S6": ("S5", "S3"),
    "S6a": ("S6",),
    "S7": ("S6",),
    "S8": ("S7",),
    "S8.5": ("S6",),
    "S9": ("S6", "S6a", "S8", "S8.5"),
    "S10": ("S9",),
    "S11": (),
    "S12": ("S10", "S11"),
}

# 재개 좌표 구성 (STEP 52)
RESUME_AXES: dict[str, tuple[str, ...]] = {
    "S1": ("target_key", "page"),
    "S5": ("target_key", "source_id", "endpoint"),
    "S6": ("target_key", "source_id"),
    "S7": ("source_id",),
    "S9": ("target_key", "source_id"),
    "S10": ("target_key", "source_id"),
}


# ── STEP 50a 재처리 결정표 ★ 단일 출처 ───────────────────────────────
# 42곳에 흩어져 있으면 개발자가 매번 다르게 판단한다.
# 이 표 밖의 이유로 재수집하지 않는다.
@dataclass(frozen=True)
class Reprocess:
    version_key: str | None
    steps: tuple[str, ...]
    refetch: bool


REPROCESS_TABLE: dict[str, Reprocess] = {
    "site_response_shape": Reprocess(None, STEPS[1:], True),
    # ★★ S4(목록 대조)가 빠져 있었다 (실측 08-20).  마스터가 브라우저로 받아 온
    #   목록 141봉투 · 새 매물 189건이 core 에 안 들어오고, 대신 S5 가
    #   기존 32,949 매물 전건을 다시 받고 있었다 —
    #   규격이 「목록 저장이 전건 재수집을 부르지 않는다」로 금지한 것이다.
    #   ★ 규격 순서 그대로다 — 대조 → 상세 → 새 5종 → 판정 (STEP 136g)
    "listing_updated": Reprocess(None, ("S4", "S5", "S6", "S9", "S10"), True),
    "raw_missing": Reprocess(None, ("S5", "S6", "S9", "S10"), True),
    "parse_rule": Reprocess("parse_version", ("S6", "S9", "S10"), False),
    "dictionary": Reprocess("dict_version", ("S9", "S10"), False),
    "verdict_rule": Reprocess("dict_version", ("S9", "S10"), False),
    "coefficient": Reprocess("coefficient_id", ("S8.5", "S9", "S10"), False),
    "scoring": Reprocess("calc_version", ("S10",), False),
    "labels": Reprocess(None, (), False),
}


# 전건을 다시 던지는 사유.  ★ 이 하나뿐이다 (c-tools 「그래서 이렇게 한다」).
#   「전체 재수집」은 사람이 명시할 때만 한다 — 3,470건 × 9종 = 3만 호출이다.
#   그 밖의 사유는 **아직 답을 못 받은 것만** 던진다 (should_refetch)
FULL_REFETCH_REASONS: tuple[str, ...] = ("site_response_shape",)


def refetch_all(reason: str) -> bool:
    """그 사유가 전건을 다시 던지는가.

    ★ False 면 `resume` 방식으로 돈다 — ok·empty·not_found 는 이미 답을
      받은 것이라 안 던지고, error·미요청만 던진다.
      그것이 규격의 「새로 뜬 것 · 가격이 바뀐 것만」이다
    """
    return reason in FULL_REFETCH_REASONS


def reprocess_plan(reason: str) -> Reprocess:
    """무엇이 바뀌면 어디부터 다시 도는가.

    금지   「확실하지 않으니 처음부터」 — 4,700건 × 4엔드포인트가 다시 나간다
    """
    if reason not in REPROCESS_TABLE:
        raise ValidationError(
            f"재처리 사유 미정의: {reason}. "
            f"STEP 50a 표 밖의 이유로 재수집하지 않는다", step="STEP 50a"
        )
    return REPROCESS_TABLE[reason]


# ── STEP 51 재조회 규칙 ──────────────────────────────────────────────
REFETCH_STATUS: frozenset[str] = frozenset({"not_requested", "error"})


def should_refetch(status: str) -> bool:
    """not_requested · error 만 재조회한다.

    empty   사이트에 자료가 없다
    not_found  404.  없는 자원이다
    ok      이미 있다
    """
    return status in REFETCH_STATUS


# ── STEP 53 expected 산출 ────────────────────────────────────────────
# 코드가 스스로 계산한다.  사람이 입력하지 않는다.
def expected_for(step: str, *, collect_group_count: int = 0,
                 page_count: int = 0, active_listings: int = 0,
                 endpoint_kinds: int = 0, dict_axes: int = 0,
                 catalog_keys: int = 0, ok_raw_rows: int = 0,
                 coefficient_targets: int = 0, components: int = 0) -> int:
    """단계별 expected.

    ★ S1 · S2 는 차종 수가 아니라 collect_group 수로 센다 (2장 STEP 23).
      S2 를 빠뜨리면 Badge 요청 누락이 V1-01 을 통과한다.
    """
    if step == "S1":
        # ★ S1 만 예외다.  페이지 수는 첫 요청의 Count 로 확정된다 (STEP 18a).
        #   요청 전에 못 정한다.  1페이지 응답 후 갱신한다
        return collect_group_count * page_count
    if step == "S2":
        # ★ 1요청이다.  Badge 요청은 미지정과 같은 결과를 준다 (실측)
        return collect_group_count
    if step == "S3":
        return dict_axes
    if step == "S5":
        return active_listings * endpoint_kinds
    if step == "S6":
        return ok_raw_rows
    if step == "S7":
        return catalog_keys
    if step == "S8.5":
        return coefficient_targets
    if step == "S9":
        return active_listings * components
    if step == "S10":
        return active_listings
    return 0


def step_report(step: str, target_key: str | None, expected: int,
                tally: dict[str, int], rejected: int, elapsed_sec: float,
                not_requested: int | None = None) -> StepReport:
    """단계 종료 시 남긴다.  화면 출력만 하지 않는다."""
    requested = sum(tally.get(k, 0)
                    for k in ("ok", "empty", "not_found", "error"))
    nr = expected - requested if not_requested is None else not_requested
    return StepReport(
        step=step, target_key=target_key, expected=expected, requested=requested,
        ok=tally.get("ok", 0), empty=tally.get("empty", 0),
        not_found=tally.get("not_found", 0), error=tally.get("error", 0),
        not_requested=nr, rejected=rejected, elapsed_sec=elapsed_sec,
        halted=False, halt_reason=None,
    )


def halt_if(rep: StepReport, raw_rows: int) -> StepReport:
    """자동 점검 6종.  하나라도 어긋나면 다음 단계를 실행하지 않는다 (STEP 53).

    ①⑥ 이 핵심이다.  v1 은 「애초에 안 던진 것」을 아무도 세지 않았다.
    """
    answered = rep.ok + rep.empty + rep.not_found + rep.error
    bad = []
    if rep.expected == 0 and rep.requested == 0:
        # 처리할 것이 없었다.  expected 는 코드가 계산한 값이므로
        # 0 은 「할 일이 없음」이지 「수집 0건」이 아니다 (STEP 53)
        return rep
    if rep.requested + rep.not_requested != rep.expected:
        bad.append(
            f"① expected {rep.expected} != requested {rep.requested}"
            f" + not_requested {rep.not_requested}"
        )
    if rep.requested != answered:
        bad.append(f"② requested {rep.requested} != 응답 합 {answered}")
    if rep.rejected:
        bad.append(f"③ 형식 검증 거부 {rep.rejected}건 — URL·응답 변경 의심")
    if rep.ok == 0:
        bad.append("④ ok 0건 — 수집 0건은 성공이 아니다")
    if raw_rows != answered:
        bad.append(f"⑤ raw_response 신규 {raw_rows} != 응답 합 {answered}")
    if rep.not_requested:
        bad.append(f"⑥ not_requested {rep.not_requested}건 — 미완성 매물이 남았다")
    if bad:
        rep.halted = True
        rep.halt_reason = " / ".join(bad)
    return rep


# ── STEP 48 선행 조건 ────────────────────────────────────────────────
def precheck(conn: sqlite3.Connection, step: str,
             done: set[str]) -> tuple[bool, str]:
    """조건 미충족 시 건너뛰지 않는다.  중단하고 보고한다.

    반환   (통과, 사유)
    """
    missing = [s for s in PRECEDES.get(step, ()) if s not in done]
    if missing:
        return False, f"선행 단계 미완료: {','.join(missing)}"

    if step == "S3":
        n = conn.execute("SELECT COUNT(*) FROM raw_response_reject").fetchone()[0]
        if n:
            return False, f"형식 검증 거부 {n}건 (2장 STEP 25a)"
    if step == "S4":
        n = conn.execute(
            "SELECT COUNT(*) FROM dict_enum WHERE axis IN ('fuel','trim') "
            "AND status='pending'").fetchone()[0]
        if n:
            return False, f"분류에 쓰는 사전에 pending {n}건"
    if step == "S5":
        n = conn.execute(
            "SELECT COUNT(*) FROM core_listing WHERE status='active'").fetchone()[0]
        if not n:
            return False, "active 매물 0건"
    if step == "S9":
        # ★ 판정에 쓰는 축만 막는다 (STEP 44).
        #   panel(부위명)은 표시 전용이다 — 새 부위명 하나에 전 매물이
        #   멈추면 수집할수록 판정이 안 도는 구조가 된다 (실측 08-15)
        from store.dictionary import JUDGING_AXES

        marks = ",".join("?" * len(JUDGING_AXES))
        rows = conn.execute(
            f"SELECT axis, COUNT(*) FROM dict_enum WHERE status='pending' "
            f"AND axis IN ({marks}) GROUP BY axis", JUDGING_AXES).fetchall()
        if rows:
            detail = " · ".join(f"{a} {n}건" for a, n in rows)
            return False, f"사전 pending — 판정에 쓰는 축이 확정되지 않았다: {detail}"
    if step == "S10":
        n = conn.execute(
            "SELECT COUNT(*) FROM result_axis WHERE source IS NULL OR prio IS NULL"
        ).fetchone()[0]
        if n:
            return False, f"result_axis 근거 NULL {n}건 — put() 미경유"
    if step == "S12":
        n = conn.execute(
            "SELECT COUNT(*) FROM audit_validation WHERE severity='fatal' "
            "AND passed=0").fetchone()[0]
        if n:
            return False, f"fatal 검증 실패 {n}건"
    return True, ""


# ── STEP 52 재개 ─────────────────────────────────────────────────────
def resume_point(conn: sqlite3.Connection, run_id: str) -> ResumePoint | None:
    """audit_request 의 마지막 성공 행에서 계산한다.

    금지   진행 상태를 메모리·전역 변수에만 두는 것
    """
    row = conn.execute(
        "SELECT kind, source_id FROM audit_request "
        "WHERE run_id=? AND status='ok' ORDER BY id DESC LIMIT 1",
        (run_id,),
    ).fetchone()
    if row is None:
        return None
    kind, source_id = row
    step = {"list": "S1", "facet": "S2", "catalog": "S7"}.get(kind, "S5")
    return ResumePoint(step=step, target_key=None, page=None,
                       source_id=source_id,
                       endpoint=kind if step == "S5" else None)


# ── 설정 해시 (5장 정의서) ───────────────────────────────────────────
def config_hash(path: str) -> str:
    """선언한 버전과 실제 내용이 어긋나는 것을 잡는다."""
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def build_run_context_fields(config_dir: str = "config") -> dict[str, str]:
    return {
        "endpoint_config_hash": config_hash(os.path.join(config_dir, "endpoints.json")),
        "target_config_hash": config_hash(os.path.join(config_dir, "targets.json")),
        "scoring_config_hash": config_hash(os.path.join(config_dir, "scoring.json")),
    }


# ── 부분 재처리 대상 선별 (STEP 50a) ─────────────────────────────────
def stale_rows(conn: sqlite3.Connection, version_key: str,
               current: str) -> list[str]:
    """버전이 낮은 행만 고른다.  전건을 다시 돌리지 않는다."""
    table, column = {
        "parse_version": ("core_listing", "parse_version"),
        "dict_version": ("result_axis", "dict_version"),
        "calc_version": ("result_score", "calc_version"),
    }[version_key]
    return [
        r[0] for r in conn.execute(
            f"SELECT DISTINCT listing_id FROM {table} WHERE {column} IS NOT ? "
            f"OR {column} <> ?", (current, current))
    ]


def save_step_report(conn: sqlite3.Connection, run_id: str,
                     rep: StepReport) -> None:
    """검증 결과를 테이블에 남긴다 (STEP 66 · audit_validation)."""
    conn.execute(
        "INSERT OR REPLACE INTO audit_validation"
        "(run_id,phase,code,target_key,expected,actual,passed,severity,"
        " samples,checked_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (run_id, "V1", f"STEP53-{rep.step}", rep.target_key or "",
         str(rep.expected),
         json.dumps({
             "requested": rep.requested, "ok": rep.ok, "empty": rep.empty,
             "not_found": rep.not_found, "error": rep.error,
             "not_requested": rep.not_requested, "rejected": rep.rejected,
         }, ensure_ascii=False),
         0 if rep.halted else 1,
         "fatal" if rep.halted else "warn",
         rep.halt_reason, ""),
    )
    conn.commit()


# ── STEP 49 실행 순서 ────────────────────────────────────────────────
# 한 차종을 끝내고 다음으로 간다.  8차종을 동시에 돌리면 실패 원인이 섞인다.
# 실행 본체는 주입한다 — 이 모듈은 순서 · 조건 · 중단만 책임진다 (0장 STEP 2).
def rss_mb() -> float:
    """★ 지금 이 프로세스가 쥐고 있는 메모리 (MB).

    ★★ 08-26 — ★ 장비가 통째로 멈췄는데 ★ **메모리 탓인지 못 갈랐다**
      (명령서 75장).  ★ 저널이 끊겨 마지막 순간이 안 남았고,
      ★ 그 전까지 ★ **메모리를 아무도 안 재고 있었다**.
    ★ 그래서 ★ 단계마다 찍는다 — ★ 다음에는 ★ 잰 것으로 말할 수 있어야 한다.
    ★ 파이프라인은 ★ 웹 서버와 ★ 같은 프로세스에서 돈다 (`collect/worker.py`).
      ★ 이 숫자가 곧 ★ 마스터 화면이 쥔 메모리다
    ★ /proc 이 없으면 0.0 — 잴 수 없는 것을 지어내지 않는다
    """
    try:
        with open("/proc/self/statm", encoding="utf-8") as f:
            pages = int(f.read().split()[1])
    except (OSError, ValueError, IndexError):
        return 0.0
    return pages * (os.sysconf("SC_PAGE_SIZE") / (1024 * 1024))


def run_step(conn: sqlite3.Connection, ctx, step: str, done: set[str],
             executors: dict, progress=None) -> StepReport:
    """단계 1회.

    조건 미충족은 건너뛰기가 아니라 중단이다 (STEP 48).
    """
    progress = progress or silent_progress
    progress(step, f"시작 · 메모리 {rss_mb():,.0f}MB")
    ok, why = precheck(conn, step, done)
    if not ok:
        rep = step_report(step, None, 0, {}, 0, 0.0)
        rep.halted = True
        rep.halt_reason = f"선행 조건 미충족: {why}"
        save_step_report(conn, ctx.run_id, rep)
        return rep

    run = executors.get(step)
    if run is None:
        rep = step_report(step, None, 0, {}, 0, 0.0)
        rep.halted = True
        rep.halt_reason = f"실행기 미등록: {step}"
        save_step_report(conn, ctx.run_id, rep)
        return rep

    t0 = time.time()
    # ★ 도메인 예외가 새어 나가면 리포트도 기록도 남지 않는다.
    #   중단은 리포트를 내는 것이지 죽는 것이 아니다 (9장 STEP 90)
    try:
        return _execute(conn, ctx, step, run, progress)
    except CarWatchError as e:
        rep = step_report(step, None, 0, {}, 0, time.time() - t0)
        rep.halted = True
        rep.halt_reason = f"{type(e).__name__}: {e}"
        save_step_report(conn, ctx.run_id, rep)
        progress(step, f"중단 — {e}", 0, 0)
        return rep


def _execute(conn, ctx, step, run, progress) -> StepReport:
    t0 = time.time()
    if step in BATCH_STEPS:
        # ★ 행마다 커밋하지 않는다.  커밋은 fsync 라 행 수만큼 느려진다.
        #   RAW 가 이미 있으므로 중간에 죽어도 재파싱으로 복구된다 (STEP 50a)
        from store.raw import batch

        with batch(conn):
            rep, raw_rows = run(conn, ctx)
    else:
        rep, raw_rows = run(conn, ctx)
    rep = halt_if(rep, raw_rows)
    save_step_report(conn, ctx.run_id, rep)
    # ★ 메모리를 함께 찍는다 — ★ 어느 단계에서 부푸는지 봐야 한다 (명령서 75장)
    progress(step, f"완료 · {time.time() - t0:.1f}초 · 메모리 {rss_mb():,.0f}MB",
             rep.ok, rep.expected)
    return rep


def completed_steps(conn: sqlite3.Connection) -> set[str]:
    """지난 실행에서 정상 종료한 단계.

    ★ 이어서 돌 때 앞 단계를 다시 요청하지 않기 위한 것이다.
      매번 S1 부터 돌면 수집이 끝난 뒤에도 재수집이 반복된다.
    근거   audit_validation 의 STEP53-* 가 단계별 결과다 (STEP 53)
    """
    return {r[0].split("-", 1)[1] for r in conn.execute(
        "SELECT code FROM audit_validation "
        "WHERE code LIKE 'STEP53-%' AND passed = 1")}


def run_pipeline(conn: sqlite3.Connection, ctx, executors: dict,
                 steps: tuple[str, ...] = STEPS,
                 progress=None, done: set[str] | None = None
                 ) -> list[StepReport]:
    """전체 실행.  중단이 나오면 이후 단계를 실행하지 않는다 (STEP 50).

    done   이미 끝난 단계.  이어서 돌 때 선행 조건 검사에 쓴다
    금지   「조용히 넘어가기」.  v1 은 모든 사고가 조용히 지나간 뒤 발견됐다
    """
    done = set(done or ())
    out: list[StepReport] = []
    for step in steps:
        try:
            rep = run_step(conn, ctx, step, done, executors, progress)
        except (KeyboardInterrupt, SystemExit) as stop:
            # ★★ 중단은 리포트를 내는 것이지 죽는 것이 아니다 (STEP 48).
            #   밖에서 끊겨도 「어디까지 갔는지」가 남아야 한다 —
            #   실측 08-19 — 내가 프로세스를 죽였더니 요청 5,000건은 남고
            #   단계 리포트가 하나도 안 남아 V1-11 이 걸렸다.
            #   그때 「무엇이 돌다 끊겼나」를 아무도 몰랐다
            rep = step_report(step, None, 0, {}, 0, 0.0)
            rep.halted = True
            rep.halt_reason = f"밖에서 끊겼다 ({type(stop).__name__})"
            save_step_report(conn, ctx.run_id, rep)
            out.append(rep)
            raise
        out.append(rep)
        if rep.halted:
            break
        done.add(step)
    return out


# ── 재계산 지시 (5장 STEP 50a · 13장 STEP 132) ───────────────────────
# ★ 관리자가 단계를 직접 고르지 않는다.  「무엇이 바뀌었나」만 고르면
#   재처리 결정표가 from_step 을 준다.
ORIGIN_WEB, ORIGIN_CLI = "web", "cli"


# ── 진행 표시 (STEP 53) ──────────────────────────────────────────────
# ★ 단계가 끝나야 한 줄이 나오면 멈춘 것과 구분이 안 된다.
#   S1 은 8그룹 × 페이지 × 간격 2~5초라 수 분이 걸린다.
#   진행은 「무엇을 몇 번째로 하고 있는가」를 낸다.  판정이 아니다
# 화면 폭 (형식).  진행 표시가 줄바꿈되지 않게 한다
PROGRESS_DETAIL_WIDTH = 52
PROGRESS_LINE_PAD = 24
DONE_MARK = "완료"


def print_progress(step: str, detail: str, done: int = 0,
                   total: int = 0) -> None:
    """진행은 덮어쓰고, 완료는 줄을 남긴다.

    ★ 파일로 넘길 때는 덮어쓰지 않는다.  \r 이 로그를 한 줄로 만든다
    """
    bar = f"{done}/{total}" if total else f"{done}"
    line = f"    {step:5} {bar:>11}  {detail[:PROGRESS_DETAIL_WIDTH]}"
    tty = sys.stdout.isatty()
    if detail.startswith(DONE_MARK) or not tty:
        end = "\n"
        pad = ""
    else:
        end = ""
        pad = "\r"
    sys.stdout.write(f"{pad}{line:<{PROGRESS_DETAIL_WIDTH + PROGRESS_LINE_PAD}}{end}")
    sys.stdout.flush()


def silent_progress(step: str, detail: str, done: int = 0,
                    total: int = 0) -> None:
    """시험에서 쓴다.  화면을 더럽히지 않는다."""

# 전면 재수집은 CLI 전용이다 (STEP 132).
#   비용   4,700 × 4 = 18,800 요청.  간격 2~5초라 수 시간.  되돌릴 수 없다
#   성격   「무엇이 바뀌었나」가 아니라 「사이트가 달라졌다」는 판단이다
#   금지   웹에 전면 재수집 버튼 — 있으면 「일단 눌러보자」가 된다
CLI_ONLY_REASONS: frozenset[str] = frozenset(
    r for r, plan in REPROCESS_TABLE.items() if plan.refetch and plan.steps
    and plan.steps[0] == STEPS[1]
)


def from_step_for(reason: str) -> str | None:
    """바뀐 것 → 재계산 시작 단계.  None 이면 재계산이 필요 없다."""
    plan = reprocess_plan(reason)
    return plan.steps[0] if plan.steps else None


# ★★★★ 08-29 (UI_REVIEW 25-3 · 개정 837) — ★ 사유의 ★ **쉬운 말**.
#   ★★ 마스터 — 「★ `raw_missing` 이 무슨 뜻인가.  ★ 내가 이해를 못 하겠어」
#   ★ (이름, 무엇을 하나 · 무엇이 바뀌나) 다.
#   ★ 단계 이름(S9…)은 ★ 여기 안 적는다 — ★ 화면이 뒤에 작게 낸다
REASON_PLAIN = {
    "listing_updated": ("처음부터",
                        "목록부터 다시 받는다 · 가장 오래 걸린다"),
    "raw_missing": ("원문이 없다",
                    "받다 만 것만 다시 받는다 · 이미 받은 것은 그대로"),
    "scoring": ("다시 판정",
                "받은 것은 그대로 · 점수만 다시 낸다 (배점을 고친 뒤)"),
    "parse_rule": ("상세만",
                   "목록은 그대로 · 상세만 다시 펼친다"),
    "verdict_rule": ("판정 규칙이 바뀌었다",
                     "받은 것은 그대로 · 등급을 다시 매긴다"),
    "coefficient": ("계수가 바뀌었다",
                    "받은 것은 그대로 · 값 계산을 다시 한다"),
    "dictionary": ("사전이 바뀌었다",
                   "받은 것은 그대로 · 이름·코드를 다시 붙인다"),
    "labels": ("이름표만 바뀌었다",
               "점수도 매물도 그대로 · 화면 글자만 다시 만든다"),
}


def web_reasons() -> list[str]:
    """웹에서 고를 수 있는 사유.  전면 재수집은 빠진다."""
    return sorted(r for r in REPROCESS_TABLE if r not in CLI_ONLY_REASONS)


def check_recalc_origin(reason: str, origin: str) -> None:
    """웹 경로에서 전면 재수집 사유가 큐에 들어가면 막는다 (V10-13).

    화면은 판단 재료를 낸다.  실행하지 않는다.
    """
    if origin == ORIGIN_WEB and reason in CLI_ONLY_REASONS:
        raise PolicyError(
            f"{reason} 는 CLI 전용이다. 원문 확인 후 "
            "python run.py collect --full 로 실행한다 (STEP 25a · 132)",
            step="STEP 132")


def plan_recalc(conn: sqlite3.Connection, reason: str, scope: str,
                origin: str = ORIGIN_CLI) -> dict:
    """재계산 계획.  실행하지 않는다 — run_pipeline 이 실행한다."""
    check_recalc_origin(reason, origin)
    plan = reprocess_plan(reason)
    return {
        "reason": reason,
        "from_step": from_step_for(reason),
        "steps": list(plan.steps),
        "refetch": plan.refetch,
        "version_key": plan.version_key,
        "scope": scope,
        "stale": (stale_rows(conn, plan.version_key, _current(conn, plan))
                  if plan.version_key else []),
    }


def _current(conn: sqlite3.Connection, plan: Reprocess) -> str:
    row = conn.execute(
        "SELECT MAX(calc_version) FROM result_score").fetchone()
    return row[0] if row and row[0] else ""


def run_recalc(conn: sqlite3.Connection, ctx, executors: dict, reason: str,
               scope: str = "all", origin: str = ORIGIN_CLI) -> list[StepReport]:
    """RecalcJob 이 run_pipeline 을 부른다 (STEP 47 · 132).

    관리자는 「무엇이 바뀌었나」만 고른다.  단계는 결정표가 정한다.
    """
    plan = plan_recalc(conn, reason, scope, origin)
    if not plan["steps"]:
        return []
    # ★★ 이어서 도는 것이다.  앞 단계는 이미 끝나 있다 —
    #   done 을 안 넘기면 S5 의 선행 S4 가 영원히 「미완료」다.
    #   실측 08-18 — 웹·예약으로 넣은 재계산 60건이 전부
    #   「S5: 선행 조건 미충족: 선행 단계 미완료: S4」로 죽어 있었다.
    #   ★ 한 번도 성공한 적이 없다.  큐는 도는데 일이 안 된 것이다
    #   ★ diagnose() 는 처음부터 completed_steps 를 쓴다 — 여기만 빠져 있었다
    return run_pipeline(conn, ctx, executors, steps=tuple(plan["steps"]),
                        done=completed_steps(conn))


# ── STEP 50b 진단 모드 ───────────────────────────────────────────────
@dataclass(frozen=True)
class Defect:
    code: str
    step: str
    severity: str
    count: int
    samples: list
    action: str
    root: str | None = None


@dataclass(frozen=True)
class DefectReport:
    run_id: str
    steps: list
    defects: list
    roots: dict


# 뿌리 후보.  ★ 기계가 완전히 판정하지는 못한다 — 묶어 내고 사람이 확인한다
ROOT_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("범위 불일치 — 검사와 대상이 다른 것을 센다",
     ("V1-05", "V1-07", "V4-06", "V4-06b")),
    ("등록부 미분류 — 시드를 채우면 함께 풀린다", ("V4-06", "V4-11", "V4-11b")),
    ("사전 미확정 — 검토를 끝내면 함께 풀린다", ("V3-08", "V3-30")),
    ("PII 분리 — 키·경로가 어긋난다", ("V2-09", "V2-11", "V2-17", "V4-01")),
    ("변별력 — 한 차종만 봐서 값 종류가 1이다", ("V3-03", "V3-04", "V2-08")),
)

# 진단은 읽기다.  수집도 판정 저장도 하지 않는다
DIAGNOSE_SKIP: frozenset[str] = frozenset({"S0", "S1", "S2", "S5", "S7"})


def diagnose(conn: sqlite3.Connection, ctx, executors: dict,
             steps: tuple[str, ...] = STEPS, progress=None,
             refetch: bool = False) -> DefectReport:
    """한 번 돌면서 전 결함을 모은다 (STEP 50b).

    ★ fatal 을 만나도 그 단계까지 기록하고 다음으로 간다.
      고치고 다시 돌기를 반복하면 수집이 매번 다시 나간다 — 11회 겪었다.
    금지   결함을 자동으로 고치는 것.  config 를 바꾸는 것.  result_* 를 쓰는 것
    """
    say = progress or silent_progress
    done = completed_steps(conn)
    reports: list[StepReport] = []
    for step in steps:
        if not refetch and step in DIAGNOSE_SKIP and step in done:
            # RAW 가 있으면 다시 던지지 않는다.  결함은 대부분 파싱 이후다
            say(step, "건너뜀 — RAW 가 있다", 0, 0)
            continue
        rep = run_step(conn, ctx, step, done, executors, progress)
        reports.append(rep)
        done.add(step)          # ★ 중단해도 다음 단계로 간다
    return DefectReport(ctx.run_id, reports, *_collect_defects(conn, ctx))


@dataclass
class _DiagCtx:
    """검증 문맥.  RunContext 는 policy_raw 를 갖지 않는다 (13장 S11 과 같다)."""

    run_id: str
    policy_raw: dict
    depreciation: dict
    target_keys: tuple = ()
    started_at: object = None


def _collect_defects(conn: sqlite3.Connection, ctx) -> tuple[list, dict]:
    from validate.base import PHASE_ORDER, run_phase

    if not hasattr(ctx, "policy_raw"):
        import json
        import os

        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        def load(name):
            with open(os.path.join(root, "config", name),
                      encoding="utf-8") as f:
                return json.load(f)

        ctx = _DiagCtx(ctx.run_id, load("scoring.json"),
                       load("depreciation.json"),
                       tuple(getattr(ctx, "target_keys", ()) or ()),
                       getattr(ctx, "started_at", None))

    found: dict[str, Defect] = {}
    for phase in PHASE_ORDER:
        try:
            results = run_phase(conn, ctx, phase)
        except Exception as e:                       # noqa: BLE001
            found[phase] = Defect(phase, phase, "fatal", 1,
                                  [f"{type(e).__name__}: {e}"],
                                  "검사가 예외로 죽었다. 그 검사를 먼저 고친다")
            continue
        for r in results:
            if r.passed:
                continue
            found[r.check.code] = Defect(
                r.check.code, r.check.phase, r.check.severity, 1,
                list(r.samples)[:3], r.check.action)

    for rep in conn.execute(
        "SELECT code, actual FROM audit_validation "
        "WHERE run_id=? AND passed=0 AND code LIKE 'STEP53-%'", (ctx.run_id,)
    ).fetchall():
        found[rep[0]] = Defect(rep[0], rep[0].split("-", 1)[1], "fatal", 1,
                               [str(rep[1])[:80]], "해당 단계의 중단 사유를 본다")

    roots: dict[str, list[str]] = {}
    for label, codes in ROOT_RULES:
        hit = [c for c in codes if c in found]
        if len(hit) > 1:
            roots[label] = hit
            for c in hit:
                found[c] = Defect(found[c].code, found[c].step,
                                  found[c].severity, found[c].count,
                                  found[c].samples, found[c].action, label)
    return list(found.values()), roots


def format_defects(rep: DefectReport) -> str:
    """뿌리를 먼저 낸다.  「A 를 고치면 5건이 함께 풀린다」."""
    out = [f"■ 진단 — run {rep.run_id}", ""]
    fatal = [d for d in rep.defects if d.severity == "fatal"]
    warn = [d for d in rep.defects if d.severity != "fatal"]
    out.append(f"결함 {len(rep.defects)}건 (fatal {len(fatal)} · warn "
               f"{len(warn)}) · 뿌리 {len(rep.roots)}개")
    if rep.roots:
        out += ["", "■ 뿌리 — 하나를 고치면 묶인 것이 함께 풀린다", ""]
        for label, codes in rep.roots.items():
            out.append(f"  {label}")
            out.append(f"    → {', '.join(codes)}  ({len(codes)}건)")
    for title, rows in (("■ FATAL", fatal), ("■ warn", warn)):
        if not rows:
            continue
        out += ["", title, ""]
        for d in rows:
            mark = f"  [{d.root}] " if d.root else "  "
            out.append(f"{mark}{d.code:9} {d.action[:60]}")
            if d.samples:
                out.append(f"      {str(d.samples)[:90]}")
    if not fatal:
        out += ["", "fatal 없음 — 다음 단계로 갈 수 있다"]
    return "\n".join(out)
