# -*- coding: utf-8 -*-
"""관리 도구 (13장 STEP 135).

★ 도구는 읽기 또는 config 변경만 한다.  데이터를 고치지 않는다.
  데이터 수정은 재파싱·재판정으로 한다 (STEP 50a)
금지   도구가 core_* 를 직접 UPDATE 하는 것
★ 도구 결과는 제안이다.  적용은 별도 버튼이다 —
  「계수를 산출했다」와 「계수를 바꿨다」는 다르다
"""
from __future__ import annotations

import sqlite3

from contracts import ROLE_ADMIN, Account
from errors import ValidationError
from store.admin import require_role

from store.admin import _admin_cfg

# 표본이 이보다 적으면 제안하지 않는다.  ★ 적은 표본으로 임계를 정하면
# 그 값이 근거처럼 보이지만 다음 수집에 뒤집힌다 (config/admin.json)
MIN_SAMPLE = int(_admin_cfg("tool_min_sample"))
QUANTILES = tuple(_admin_cfg("tool_quantiles"))
# 만원 단위.  ★ 화면이 만원으로 읽으므로 여기서 나눈다
WON_PER_MANWON = 10_000


def run_tool(conn: sqlite3.Connection, account: Account, key: str,
             root: str = ".") -> dict:
    """도구 하나를 돌린다.  ★ 결과는 표다 — 적용하지 않는다."""
    require_role(account, ROLE_ADMIN)
    fn = _TOOLS.get(key)
    if fn is None:
        raise ValidationError(f"없는 도구: {key}", step="STEP 135")
    return fn(conn, root)


def _grade_dist(conn, root: str) -> dict:
    ver = conn.execute(
        "SELECT MAX(calc_version) FROM result_score").fetchone()[0]
    rows = [{"등급": g, "건수": n} for g, n in conn.execute(
        "SELECT grade, COUNT(*) FROM result_score WHERE calc_version=? "
        "GROUP BY grade ORDER BY 2 DESC", (ver,))]
    return {"title": f"등급 분포 · {ver}", "rows": rows,
            "note": "배점을 바꾸면 여기가 먼저 달라집니다"}


def _validate(conn, root: str) -> dict:
    rid = (conn.execute("SELECT run_id FROM audit_validation "
                        "ORDER BY checked_at DESC LIMIT 1").fetchone()
           or ("-",))[0]
    rows = [{"코드": c, "기대": e, "실제": a, "등급": s}
            for c, e, a, s in conn.execute(
                "SELECT code, expected, actual, severity FROM audit_validation"
                " WHERE run_id=? AND passed=0 AND applicable=1 "
                "ORDER BY severity, code", (rid,))]
    return {"title": f"검증 실패 · {rid}", "rows": rows,
            "note": "통과 항목은 내지 않습니다 — 무엇이 실패했나가 먼저입니다"}


def _mapping(conn, root: str) -> dict:
    rows = [{"엔드포인트": k, "요청": n, "성공": ok or 0,
             "일치율": f"{(ok or 0) * 100 // max(n, 1)}%"}
            for k, n, ok in conn.execute(
                "SELECT kind, COUNT(*), "
                "SUM(CASE WHEN status='ok' THEN 1 ELSE 0 END) "
                "FROM audit_request GROUP BY kind ORDER BY 2 DESC")]
    return {"title": "엔드포인트별 응답", "rows": rows,
            "note": "「없음(not_found)」은 실패가 아닙니다"}


def _paths(conn, root: str) -> dict:
    rows = [{"경로": p, "구분": u, "컬럼": c or "—"}
            for p, u, c in conn.execute(
                "SELECT json_path, usage, core_column FROM meta_field_usage "
                "ORDER BY usage, json_path LIMIT 200")]
    return {"title": f"등록부 경로 {len(rows)}", "rows": rows,
            "note": "unclassified 가 있으면 판정이 멈춥니다"}


def _threshold(conn, root: str) -> dict:
    prices = [r[0] for r in conn.execute(
        "SELECT price_current_won FROM core_listing "
        "WHERE price_current_won IS NOT NULL ORDER BY price_current_won")]
    if len(prices) < MIN_SAMPLE:
        return {"title": "임계 제안", "rows": [],
                "note": f"표본 {len(prices)}건 — {MIN_SAMPLE}건 미만이라 "
                        f"제안하지 않습니다"}
    rows = [{"분위수": f"p{int(q * 100)}",
             "값": f"{prices[int(len(prices) * q)] // WON_PER_MANWON:,}만"}
            for q in QUANTILES]
    return {"title": f"가격 분위수 · 표본 {len(prices):,}건", "rows": rows,
            "note": "★ 제안입니다. 적용은 설정 화면에서 사유와 함께 합니다"}


_TOOLS = {"validate": _validate, "grade_dist": _grade_dist,
          "mapping": _mapping, "paths": _paths, "threshold": _threshold}
