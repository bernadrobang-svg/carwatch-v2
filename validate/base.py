# -*- coding: utf-8 -*-
"""검증 계약.

지시서   6장 정의서 · STEP 54 (5차 개요) · STEP 66 (저장 · Gate)
근거     검증은 「맞는지 보는 것」이 아니라 「틀렸을 때 멈추는 것」이다.
         v1 은 전 구간이 조용히 지나갔고 사고는 전부 사후에 발견됐다.
금지     검증 결과를 화면에만 출력하는 것.  audit_validation 에 남긴다.
         fatal 을 임시로 warn 으로 낮춰 통과시키는 것.
"""
from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime


# 프로젝트 뿌리.  ★ 작업 디렉터리에 기대지 않는다 (A-7).
#   서비스로 띄우면 cwd 가 어디일지 모른다 — 실측: cd /tmp 에서 임포트만 해도 죽었다
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cfg(key, path: str = "config/scoring.json"):
    """검증 임계는 config 다 (V4-13).

    ★ 상대 경로를 받으면 뿌리에 붙인다.  절대 경로는 그대로 쓴다
    """
    if not os.path.isabs(path):
        path = os.path.join(ROOT, path)
    with open(path, encoding="utf-8") as f:
        return json.load(f)["validation"][key]

FATAL = "fatal"
WARN = "warn"

# ── 성격 4분류 (STEP 54) ─────────────────────────────────────────────
# ★ fatal 은 우리 결함에만.  외부 데이터로 멈추지 않는다.
#   판단이 어려우면 fatal 로 두는 것을 금지한다 — 11회 재실행이 그렇게 나왔다
KIND_CODE = "code"          # 코드 결함        → fatal
KIND_CONTRACT = "contract"  # 계약 위반        → fatal
KIND_EXTERNAL = "external"  # 외부 데이터      → 축 제외 또는 warn
KIND_TOTAL = "total"        # 전량 실패        → fatal

SEVERITY_OF: dict[str, str] = {
    KIND_CODE: FATAL, KIND_CONTRACT: FATAL,
    KIND_TOTAL: FATAL, KIND_EXTERNAL: WARN,
}

# 위반 사례를 남기는 최대 건수 (STEP 66).  config.scoring.validation.sample_limit
SAMPLE_LIMIT = _cfg("sample_limit")


@dataclass(frozen=True)
class Check:
    """★ 「조치」를 Check 마다 미리 정해 둔다 (9장 STEP 90).

    검사를 만들 때 「이게 걸리면 무엇을 하나」를 함께 적는다.
    걸린 뒤에 생각하면 매번 다르게 대응하게 된다.
    조치는 사람이 할 수 있는 행동으로 쓴다 —
      O  suggested.json 을 확인·수정해 field_usage.json 으로 옮긴 뒤 재실행
      X  미분류를 해소하십시오
    """

    phase: str  # V1 · V2 · V3 · V4 · V5
    code: str  # 'V1-03'
    title: str
    severity: str  # fatal · warn  — kind 가 있으면 kind 가 이긴다
    scope: str  # run · target · listing · axis
    action: str = ""  # 이 검사가 걸리면 사람이 할 행동
    kind: str = ""  # code · contract · external · total (STEP 54)

    def __post_init__(self) -> None:
        """★ 성격이 등급을 정한다.  손으로 적은 등급과 어긋나면 성격을 따른다.

        새 검사를 만들 때 4분류 중 어디인지 먼저 정한다 (STEP 54).
        """
        if not self.kind:
            raise ValueError(
                f"{self.code}: 성격을 정하지 않았다. "
                f"code · contract · external · total 중 하나다 (STEP 54). "
                f"판단이 어려우면 fatal 로 두는 것을 금지한다")
        if SEVERITY_OF[self.kind] != self.severity:
            object.__setattr__(self, "severity", SEVERITY_OF[self.kind])


@dataclass
class CheckResult:
    check: Check
    run_id: str
    target_key: str | None
    expected: str
    actual: str
    passed: bool
    samples: list[str] = field(default_factory=list)
    checked_at: datetime | None = None
    # ★ 이번 실행에서 그 단계를 돌았는가 (STEP 54 · V1-16).
    #   --from S9 로 돌면 S5 검사는 볼 것이 없다.
    #   통과로 내면 「전건 통과」가 거짓이 되고, 실패로 내면 --from 이 못 쓴다
    applicable: bool = True

    @property
    def state(self) -> str:
        if not self.applicable:
            return "미실행"
        return "통과" if self.passed else "실패"


# 요약 문자열 상한.  전량은 samples 가 갖는다
ACTUAL_MAX = _cfg("actual_max")


def _short(value, total: int | None = None) -> str:
    """★ actual 을 통째로 찍으면 화면과 로그가 도배된다.
    실측: V4-01 이 200건을 그대로 출력해 리포트를 못 읽었다.
    전량은 samples 가 갖는다 — 여기는 요약이다
    """
    if isinstance(value, (list, tuple, set)):
        n = len(value)
        head = ", ".join(str(v) for v in list(value)[:3])
        return f"{n}건" + (f" (예: {head})" if head else "")
    s = str(value)
    return s if len(s) <= ACTUAL_MAX else s[:ACTUAL_MAX] + f"… ({len(s)}자)"


def result(chk: Check, run_id: str, expected, actual, passed: bool,
           samples=None, target_key=None, at=None,
           applicable: bool = True) -> CheckResult:
    return CheckResult(chk, run_id, target_key, _short(expected),
                       _short(actual), passed,
                       [str(s)[:ACTUAL_MAX] for s in (samples or [])][:SAMPLE_LIMIT],
                       at, applicable)


def not_applicable(chk: Check, run_id: str, why: str) -> CheckResult:
    """★ 이번 실행에서 안 돈 단계.  통과로도 실패로도 세지 않는다."""
    return result(chk, run_id, "—", why, True, applicable=False)


def save_results(conn: sqlite3.Connection, results: list[CheckResult],
                 at: str) -> None:
    """전일 비교(STEP 57)가 이 테이블 위에서 돈다.  화면 출력만 하지 않는다."""
    for r in results:
        conn.execute(
            "INSERT OR REPLACE INTO audit_validation"
            "(run_id,phase,code,target_key,expected,actual,passed,severity,"
            " samples,applicable,checked_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (r.run_id, r.check.phase, r.check.code, r.target_key or "",
             r.expected, r.actual, 1 if r.passed else 0, r.check.severity,
             json.dumps(r.samples, ensure_ascii=False),
             # ★ 화면이 「미실행」이면 DB 도 「미실행」이어야 한다 (A-7).
             #   전일 비교가 이 표 위에서 돈다
             1 if r.applicable else 0, at))
    conn.commit()


def gate(results: list[CheckResult]) -> list[CheckResult]:
    """fatal 이 1건이라도 실패하면 다음 단계를 실행하지 않는다 (STEP 66).

    반환   막은 항목 목록.  빈 목록이면 통과
    """
    return [r for r in results
            if not r.passed and r.check.severity == FATAL]


def run_phase(conn: sqlite3.Connection, ctx, phase: str) -> list[CheckResult]:
    """한 차수 실행.  V1 → V2·V4 → V3 → V5 순이다 (STEP 54)."""
    from validate import (
        v1_collect, v2_load, v3_logic, v4_mapping, v5_value, v7_watch,
        v10_admin, v11_web,
    )

    runner = {"V1": v1_collect, "V2": v2_load, "V3": v3_logic,
              "V4": v4_mapping, "V5": v5_value, "V7": v7_watch,
              "V10": v10_admin, "V11": v11_web}[phase]
    return runner.run(conn, ctx)


PHASE_ORDER: tuple[str, ...] = ("V1", "V2", "V4", "V3", "V5", "V7",
                                "V10", "V11")
