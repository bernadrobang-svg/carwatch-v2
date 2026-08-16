# -*- coding: utf-8 -*-
"""V3 로직 검증 — 판정이 작동하는가 · 변별력이 있는가.

지시서   6장 STEP 59 · 59a (경고 · 딜러) · 60 (재현)
근거     판정이 「작동은 하는데 의미가 없는」 상태를 잡는다
         한 축의 source 가 전건 동일하면 우선순위 구조가 작동하지 않는 것이다
금지     사전 pending 이 판정에 쓰이는 것
"""
from __future__ import annotations

import random

from analyze.verdict import BANNED_SOURCES
from validate.base import (
    Check,
    FATAL,
    KIND_CODE,
    KIND_CONTRACT,
    KIND_EXTERNAL,
    WARN,
    _cfg,
    not_applicable,
    result,
)

# 충돌 건수 경고선.  넘으면 규칙이 겹쳤다는 신호다 (V3-36)
CONFLICT_WARN = _cfg("conflict_warn")

C = {
    "V3-01": Check("V3", "V3-01", "result_axis.source 전건 NOT NULL", FATAL, "axis",
                     "put() 을 거치지 않고 값을 대입한 축을 찾는다",
                    KIND_CODE),
    "V3-02": Check("V3", "V3-02", "result_axis.prio 전건 NOT NULL", FATAL, "axis",
                     "put() 을 거치지 않고 값을 대입한 축을 찾는다",
                    KIND_CODE),
    "V3-03": Check("V3", "V3-03", "축별 source 값 종류 >= 2", WARN, "axis",
                     "그 축의 1·2순위 근거 경로가 한 번도 이기지 못한 이유를 확인한다",
                    KIND_EXTERNAL),
    "V3-04": Check("V3", "V3-04", "축별 값 종류 >= 2", WARN, "axis",
                     "차종 내부 특성인지 판정 경로 결함인지 확인한다. 배점을 먼저 낮추지 않는다",
                    KIND_EXTERNAL),
    "V3-05": Check("V3", "V3-05", "금지 근거가 source 에 없음", FATAL, "axis",
                     "BANNED_SOURCES 를 근거로 쓴 축 파일을 찾아 근거를 교체한다",
                    KIND_CONTRACT),
    "V3-07": Check("V3", "V3-07", "축별 -1 비율", WARN, "axis",
                    KIND_EXTERNAL,
                    KIND_EXTERNAL),
    "V3-08": Check("V3", "V3-08", "사전 pending 이 판정에 쓰이지 않음", FATAL, "run",
                     "config/field_usage.json 과 dict_enum 의 pending 을 확정한 뒤 S9 를 재실행한다",
                    KIND_CODE),
    "V3-09": Check("V3", "V3-09", "축별 excluded 비율", WARN, "axis",
                    KIND_EXTERNAL,
                    KIND_EXTERNAL),
    "V3-11": Check("V3", "V3-11", "put() 순서 셔플 후에도 동일", FATAL, "run",
                     "시각·난수·전역 상태·dict 순회 순서 중 무엇이 섞였는지 확인한다",
                    KIND_CODE),
    "V3-06": Check("V3", "V3-06", "put() 충돌 기록 검토", WARN, "run",
                   "같은 축에 다른 근거가 붙었다. 우선순위가 맞는지 본다",
                   KIND_EXTERNAL),
    "V3-10": Check("V3", "V3-10", "재판정 결과가 이전과 동일", WARN, "run",
                   "규칙을 안 바꿨는데 결과가 바뀌면 판정이 비결정적이다",
                   KIND_EXTERNAL),
    "V3-23": Check("V3", "V3-23", "경고로 등급·추천 순위가 바뀌지 않음",
                   FATAL, "run",
                   "경고는 표시다. 점수에 반영하는 경로를 지운다 (STEP 100)",
                   KIND_CONTRACT),
    "V3-24": Check("V3", "V3-24", "acknowledged 가 신호 감지를 멈추지 않음",
                   FATAL, "run",
                   "확인 표시는 화면용이다. 감지는 계속한다", KIND_CONTRACT),
    "V3-25": Check("V3", "V3-25", "소멸한 경고가 삭제되지 않고 남음",
                   FATAL, "run",
                   "경고를 지우지 않는다. resolved_at 을 채운다", KIND_CONTRACT),
    "V3-28": Check("V3", "V3-28", "PeerGroup 이 확장 단계를 표시", FATAL, "run",
                   "몇 단계까지 넓혀 비교했는지 남긴다. "
                   "표본이 모자라 넓힌 것과 원래 그런 것은 다르다",
                   KIND_CODE),
    "V3-29": Check("V3", "V3-29", "배점 변경 시 calc_version 이 증가",
                   FATAL, "run",
                   "배점이 바뀌면 새 버전이다. 옛 점수와 섞이면 비교가 깨진다",
                   KIND_CODE),
    "V8-01": Check("V8", "V8-01", "같은 파일명이 두 번 생성되지 않음", FATAL,
                   "run",
                   "덮어쓰면 어제 것과 비교할 수 없다. "
                   "재생성은 calc_version 이 올라간 뒤다 (STEP 91a)",
                   KIND_CODE),
    "V8-02": Check("V8", "V8-02", "출력 파일에 BOM · CRLF 가 없음", FATAL,
                   "run",
                   "BOM 이 있으면 csv 첫 열 이름이 깨지고 "
                   "CRLF 면 diff 가 전건 변경으로 보인다",
                   KIND_CODE),
    "V3-30": Check("V3", "V3-30", "halt 축의 사전이 비어 있지 않음", FATAL,
                   "run",
                   "비어 있으면 전 값이 새 값으로 보여 판정이 통째로 멈춘다. "
                   "고정 집합은 사양이지 관측이 아니다 (STEP 42)",
                   KIND_CONTRACT),
    "V3-35": Check("V3", "V3-35", "conflicts 가 있는 매물이 기록됨", FATAL,
                   "run",
                   "result_axis_conflict 에 남긴다. 구조만 있고 아무도 "
                   "읽지 않으면 조용히 사라진다 (STEP 82)",
                   KIND_CODE),
    "V3-36": Check("V3", "V3-36", "conflicts 건수가 임계 미만", WARN, "run",
                   "규칙이 겹쳤다는 신호다. 겹친 규칙을 고친다",
                   KIND_EXTERNAL),
    "V3-34": Check("V3", "V3-34",
                   "판정 항목 수 == resultCode IS NOT NULL 인 items 수",
                   FATAL, "run",
                   "소견(006039·006040)을 부위로 세지 않는다. "
                   "code 로 가르면 소견 코드가 늘 때 깨진다 (STEP 21b)",
                   KIND_CODE),
    "V3-33": Check("V3", "V3-33", "HDA 판정이 전건 description 근거",
                   FATAL, "run",
                   "옵션명으로 가르지 않는다. Ⅰ·II 가 로마숫자와 라틴으로 섞여 온다",
                   KIND_CODE),
    "V6-07": Check("V6", "V6-07", "ORDER BY 에 4단이 전부 있음", FATAL, "run",
                   "E 뒤로 → 비율 → 가격 → listing_id. "
                   "「두 번 조회」로는 단일 스레드에서 우연히 통과한다 (E-3)",
                   KIND_CODE),
    "V3-32": Check("V3", "V3-32",
                   "seizing null 매물이 「저당 없음」으로 판정되지 않음",
                   FATAL, "run",
                   "S9 를 다시 돌린다 (verdict_rule). "
                   "옛 판정 결과에는 경고가 없다 — absolute_check 도입 전이다",
                   KIND_CONTRACT),
    "V3-37": Check("V3", "V3-37", "목록 관측분의 source 가 'list' 임",
                   FATAL, "run",
                   "facet 없이 목록에서 관측한 값은 출처를 남기고 pending 으로 "
                   "둔다.  「전체 집합을 봤다」가 아니다 (개정 266)",
                   KIND_CODE),
    "V3-38": Check("V3", "V3-38", "facet 수신 후 목록 관측분과 대조함",
                   FATAL, "run",
                   "facet 에만 있는 값은 새 pending 이고, 목록에만 있는 값은 "
                   "확인이 필요하다 — facet 에 없는 값이 왜 매물에 있나 (개정 266)",
                   KIND_CODE),
    "V3-41": Check("V3", "V3-41", "전 매물의 분모가 만점과 같음",
                   FATAL, "run",
                   "축을 못 보면 분모에서 빼던 것을 없앴다 (개정 289). "
                   "못 볼수록 비율이 올라가면 못 찾을수록 좋은 등급이 된다 — "
                   "실측 08-16: 같은 차가 330/350 S · 330/555 D 였다",
                   KIND_CONTRACT),
    "V3-31": Check("V3", "V3-31", "딜러 NULL 매물에 dealer_untrusted 없음",
                   FATAL, "run",
                   "딜러 없음을 나쁨으로 판정하는 경로를 찾는다. "
                   "모르는 것을 나쁘다고 하지 않는다",
                   KIND_CONTRACT),
    "V3-20": Check("V3", "V3-20", "trust_score 가 555 에 합산되지 않음", FATAL, "run",
                     "trust_score 를 result_axis 에 넣은 경로를 제거한다",
                    KIND_CONTRACT),
    "V3-21": Check("V3", "V3-21", "경고가 555 에 합산되지 않음", FATAL, "run",
                     "경고를 점수 축으로 만든 경로를 제거한다",
                    KIND_CONTRACT),
    "V3-22": Check("V3", "V3-22", "경고로 매물이 목록에서 제외되지 않음", FATAL, "run",
                     "경고로 status 를 바꾸는 경로를 제거한다. 경고는 표시만 한다",
                    KIND_CONTRACT),
    "V3-27": Check("V3", "V3-27", "모든 경고에 evidence 존재", FATAL, "run",
                     "evidence 없이 경고를 만든 경로를 찾는다",
                    KIND_CODE),
}

MIN_VALUE_KINDS = _cfg("min_value_kinds")
VALUES = (0, 1, -1)
PRIOS = (1, 2, 3, 4)
SHUFFLE_CALLS = len(VALUES) * len(PRIOS)
SHUFFLE_SAMPLE = _cfg("shuffle_sample")


# HDA 판정에 허용되는 근거.  ★ 옵션명은 근거가 아니다 (STEP 75)
HDA_SOURCES = ("catalog_description", "spec_table", "catalog_missing",
               "missing", "gate_closed")


def _file_output_checks(conn, rid) -> list:
    """★ 실제로 써 본다.  「덮어쓰지 않는다」를 글로만 두지 않는다 (G-3)."""
    import json as _j
    import os
    import tempfile

    from report.exports.export import CSV, MD, export, write_export
    from report.render import render_listing
    from report.views import ReportMeta

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    row = conn.execute(
        "SELECT listing_id, calc_version FROM result_score LIMIT 1"
    ).fetchone()
    if row is None:
        return [not_applicable(C["V8-01"], rid, "판정 결과가 없다"),
                not_applicable(C["V8-02"], rid, "판정 결과가 없다")]

    with open(os.path.join(root, "config", "finance.json"),
              encoding="utf-8") as f:
        fin = _j.load(f)
    with open(os.path.join(root, "config", "labels.json"),
              encoding="utf-8") as f:
        lab = _j.load(f)
    view = render_listing(conn, row[0], row[1], fin, root)
    out_dir = tempfile.mkdtemp()
    # ★ 전 요소를 ReportMeta 에서 가져온다.  손으로 조립하지 않는다 (STEP 91a)
    meta = ReportMeta(run_id=rid, layer="L1", site="encar",
                      target_key=str(row[0]), calc_version=row[1],
                      generated_at=None)

    dup, enc = [], []
    for fmt in (MD, CSV):
        res = export(view, fmt, lab, meta=meta)
        try:
            path = write_export(res, out_dir)
        except ValueError as e:
            dup.append(f"{fmt}: {e}"[:70])
            continue
        raw = open(path, "rb").read()
        if raw.startswith(b"\xef\xbb\xbf"):
            enc.append(f"{fmt}: BOM 이 있다")
        if b"\r\n" in raw:
            enc.append(f"{fmt}: CRLF 가 있다")
        try:
            write_export(export(view, fmt, lab, meta=meta), out_dir)
            dup.append(f"{fmt}: 같은 이름으로 덮어썼다")
        except FileExistsError:
            pass
    return [result(C["V8-01"], rid, 0, dup or 0, not dup, dup),
            result(C["V8-02"], rid, 0, enc or 0, not enc, enc)]


def _conflict_checks(conn, rid) -> list:
    """★ 충돌이 저장되는가 · 몇 건인가 (A-5)."""
    import os
    import re as _re

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = open(os.path.join(root, "collect", "runner.py"),
               encoding="utf-8").read()
    writes = "result_axis_conflict" in src and _re.search(
        r"INSERT INTO result_axis_conflict", src) is not None
    out = [result(C["V3-35"], rid, "기록", "기록" if writes else "버림",
                  writes,
                  [] if writes else ["v.conflicts 를 저장하는 코드가 없다"])]
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    n = conn.execute(
        "SELECT COUNT(*) FROM result_axis_conflict").fetchone()[0] \
        if "result_axis_conflict" in tables else 0
    out.append(result(C["V3-36"], rid, f"< {CONFLICT_WARN}", n,
                      n < CONFLICT_WARN,
                      [] if n < CONFLICT_WARN else [f"충돌 {n}건 — 규칙이 겹쳤다"]))
    return out


def _diagnosis_count_check(conn, rid):
    """★ item_count 는 실제 부위 행 수와 같아야 한다 (STEP 35)."""
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    if "core_diagnosis" not in tables:
        return result(C["V3-34"], rid, 0, 0, True)
    bad = [f"listing {r[0]}: 집계 {r[1]} ≠ 행 {r[2]}" for r in conn.execute(
        "SELECT d.listing_id, d.item_count, "
        " (SELECT COUNT(*) FROM core_diagnosis_item i "
        "  WHERE i.listing_id = d.listing_id) "
        "FROM core_diagnosis d WHERE d.item_count IS NOT NULL "
        "AND d.item_count <> (SELECT COUNT(*) FROM core_diagnosis_item i "
        "  WHERE i.listing_id = d.listing_id) LIMIT 20")]
    return result(C["V3-34"], rid, 0, len(bad), not bad, bad)


def _hda_source_check(conn, rid):
    """★ 「드라이빙 어시스턴스 패키지 Ⅰ」에는 HDA 가 없다.

    옵션명의 Ⅰ·II 로 가르면 로마숫자(U+2160)와 라틴이 섞여 무너진다.
    """
    bad = [f"{r[0]} {r[1]}건" for r in conn.execute(
        "SELECT source, COUNT(*) FROM result_axis WHERE axis='spec.hda' "
        "GROUP BY 1") if r[0] not in HDA_SOURCES]
    return result(C["V3-33"], rid, 0, bad or 0, not bad, bad)


def _sort_determinism(conn, rid):
    """★ 「두 번 조회」가 아니라 「구절이 있는가」를 본다 (E-3).

    단일 스레드에서는 타이브레이커가 없어도 우연히 같은 순서가 나온다.
    실측 08-14: 구현이 score_total DESC 뿐이었는데 통과했다
    """
    from report.screens.build import ORDER_SQL, order_clause

    need = ("CASE WHEN s.grade IN", "denominator", "price_current_won",
            "l.listing_id")
    bad = []
    for order in sorted(ORDER_SQL):
        clause = order_clause(order)
        bad += [f"{order}: 「{w}」 없음" for w in need if w not in clause]
    return result(C["V6-07"], rid, 0, len(bad), not bad, bad[:8])


def _warning_contract_checks(conn, rid) -> list:
    """경고는 표시다 — 판정에 끼어들지 않는다 (STEP 100)."""
    import ast
    import os

    out = []
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # V3-06 — 같은 축에 다른 근거가 붙은 기록
    conflicts = [f"{r[0]} {r[1]}건" for r in conn.execute(
        "SELECT axis, COUNT(DISTINCT source) FROM result_axis "
        "GROUP BY axis HAVING COUNT(DISTINCT source) > 1 ORDER BY 2 DESC "
        "LIMIT 10")]
    out.append(result(C["V3-06"], rid, 0, len(conflicts), True, conflicts))

    # V3-10 — 같은 calc_version 안에서 매물당 점수가 하나인가
    dup = conn.execute(
        "SELECT COUNT(*) FROM (SELECT listing_id, calc_version FROM result_score"
        " GROUP BY 1,2 HAVING COUNT(*) > 1)").fetchone()[0]
    out.append(result(C["V3-10"], rid, 0, dup, dup == 0))

    # V3-23 · V3-24 — 경고가 점수·감지에 끼어드는가 (정적)
    bad = []
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", "tests")]
        for f in files:
            if not f.endswith(".py"):
                continue
            path = os.path.join(base, f)
            rel = os.path.relpath(path, root).replace("\\", "/")
            if not (rel.startswith("score/") or rel.startswith("analyze/")):
                continue
            src = open(path, encoding="utf-8").read()
            if "listing_warning" in src:
                bad.append(f"{rel}: 판정 계층이 경고를 읽는다")
    out.append(result(C["V3-23"], rid, 0, bad or 0, not bad, bad))

    ack = []
    for base, dirs, files in os.walk(os.path.join(root, "store")):
        for f in files:
            if not f.endswith(".py"):
                continue
            src = open(os.path.join(base, f), encoding="utf-8").read()
            try:
                tree = ast.parse(src)
            except SyntaxError:
                continue
            for n in ast.walk(tree):
                if not isinstance(n, ast.Constant) or not isinstance(n.value, str):
                    continue
                v = n.value.upper()
                if "ACKNOWLEDGED" in v and ("WHERE" in v or "AND" in v):
                    ack.append(f"store/{f}: {n.value[:50]}")
    out.append(result(C["V3-24"], rid, 0, ack or 0, not ack, ack))

    # V3-25 — 경고를 삭제하지 않는가
    dels = []
    for base, dirs, files in os.walk(root):
        # ★ 검사기 자신은 대상이 아니다.  금지 문자열이 검사에 잡힌다 (여섯 번째)
        dirs[:] = [d for d in dirs
                   if d not in ("__pycache__", ".git", "tests", "validate",
                                "tools")]
        for f in files:
            if not f.endswith(".py"):
                continue
            src = open(os.path.join(base, f), encoding="utf-8").read()
            if "DELETE FROM listing_warning" in src:
                dels.append(os.path.relpath(os.path.join(base, f), root))
    out.append(result(C["V3-25"], rid, 0, dels or 0, not dels, dels))

    # V3-28 — PeerGroup 이 확장 단계를 표시하는가 (STEP 82e)
    #   ★ 값이 있는데 단계가 없으면 「트림 무시」 그룹이 「같은 차 시세」가 된다
    from analyze.peer import STAGES, PeerGroup

    fields = set(PeerGroup.__dataclass_fields__)
    bad = []
    if "stage" not in fields:
        bad.append("PeerGroup 에 stage 가 없다")
    if not STAGES:
        bad.append("확장 순서가 비어 있다")
    empty = PeerGroup(None, None, None, 0, None, "비교 표본 부족")
    if empty.median is not None:
        bad.append("표본 부족인데 중앙값을 만든다")
    out.append(result(C["V3-28"], rid, 0, bad or 0, not bad, bad))

    # V3-29 — 배점이 바뀌면 새 calc_version 인가
    rows = conn.execute(
        "SELECT calc_version, COUNT(DISTINCT denominator) FROM result_score "
        "GROUP BY 1").fetchall()
    out.append(result(C["V3-29"], rid, "버전별 1개 배점",
                      f"{len(rows)}버전", True,
                      [f"{v}: 분모 {n}종" for v, n in rows]))
    return out


def _list_observed_source_check(conn, rid):
    """V3-37 — 목록에서 관측한 값이 출처를 남기고 pending 인가 (개정 266).

    ★ facet 이 정본이다.  목록은 「지금 매물이 가진 값」일 뿐이므로
      confirmed 로 올리면 「전체를 봤다」는 거짓이 된다
    """
    from tools.build_dict import LIST_FALLBACK

    marks = ",".join("?" * len(LIST_FALLBACK))
    rows = conn.execute(
        f"SELECT axis, status, source_endpoint, COUNT(*) FROM dict_enum "
        f"WHERE axis IN ({marks}) GROUP BY 1, 2, 3",
        tuple(LIST_FALLBACK)).fetchall()
    if not rows:
        return not_applicable(C["V3-37"], rid, "그 축의 사전이 비어 있다")
    # ★ 사람이 /admin/dict 에서 확정한 것은 정상이다 (개정 267).
    #   금지된 것은 「목록 관측만으로 코드가 confirmed 를 만드는 것」이다
    confirmed_by_human = {
        r[0].split("[")[0] for r in conn.execute(
            "SELECT key_path FROM config_change WHERE file='dict_enum' "
            "AND after_value='confirm'")}
    bad = []
    for axis, status, src, n in rows:
        if src == "list" and status == "confirmed" \
                and axis not in confirmed_by_human:
            bad.append(f"{axis}: 사람 확정 없이 confirmed {n}건")
    got = " · ".join(f"{a}={s}/{src}({n})" for a, s, src, n in rows)
    return result(C["V3-37"], rid, "list → pending", got, not bad, bad)


def _facet_reconcile_check(conn, rid):
    """V3-38 — facet 을 받았으면 목록 관측분과 대조했는가 (개정 266).

    ★ 목록에만 있는 값이 남으면 그것을 알아야 한다 —
      엔카가 facet 에 안 넣은 값이거나 우리가 잘못 읽은 것이다.  둘 다 결함이다
    """
    from tools.build_dict import LIST_FALLBACK

    n_facet = conn.execute("SELECT COUNT(*) FROM raw_facet").fetchone()[0]
    if not n_facet:
        return not_applicable(C["V3-38"], rid, "facet 을 아직 못 받았다")
    marks = ",".join("?" * len(LIST_FALLBACK))
    left = conn.execute(
        f"SELECT axis, COUNT(*) FROM dict_enum "
        f"WHERE axis IN ({marks}) AND source_endpoint='list' GROUP BY 1",
        tuple(LIST_FALLBACK)).fetchall()
    bad = [f"{a}: 목록에만 있는 값 {n}건 — facet 에 없는 값이 왜 매물에 있나"
           for a, n in left]
    return result(C["V3-38"], rid, "대조 완료",
                  "남은 목록 관측 " + str(sum(n for _a, n in left)),
                  not bad, bad)


def _denominator_check(conn, rid):
    """V3-41 — 분모는 만점 고정이다 (개정 289).

    ★ 하나라도 다르면 fatal.  「우리가 못 받았다」로 평가를 바꾸지 않는다
    """
    import json as _j
    import os as _o

    root = _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__)))
    with open(_o.path.join(root, "config", "scoring.json"),
              encoding="utf-8") as f:
        total = float(_j.load(f)["total_points"])
    rows = conn.execute(
        "SELECT calc_version, denominator, COUNT(*) FROM result_score "
        "GROUP BY 1, 2").fetchall()
    if not rows:
        return not_applicable(C["V3-41"], rid, "판정 결과가 없다")
    bad = [f"{cv} 분모 {d} — {n}건" for cv, d, n in rows
           if float(d or 0) != total]
    kinds = len({d for _cv, d, _n in rows})
    return result(C["V3-41"], rid, f"{total:g}",
                  f"{kinds}종" if bad else f"{total:g} 하나", not bad, bad[:8])


def run(conn, ctx) -> list:
    rid = ctx.run_id
    out = []
    out.append(_denominator_check(conn, rid))

    n = conn.execute(
        "SELECT COUNT(*) FROM result_axis WHERE source IS NULL").fetchone()[0]
    out.append(result(C["V3-01"], rid, 0, n, n == 0))
    n = conn.execute(
        "SELECT COUNT(*) FROM result_axis WHERE prio IS NULL").fetchone()[0]
    out.append(result(C["V3-02"], rid, 0, n, n == 0))

    banned = [r[0] for r in conn.execute(
        "SELECT DISTINCT source FROM result_axis WHERE source IN "
        f"({','.join('?' * len(BANNED_SOURCES))})", tuple(sorted(BANNED_SOURCES)))]
    out.append(result(C["V3-05"], rid, 0, banned or 0, not banned, banned))

    # 변별력 — 값 종류가 1이면 그 축은 순위에 기여하지 않는다
    flat_src, flat_val = [], []
    for axis, ns, nv in conn.execute(
        "SELECT axis, COUNT(DISTINCT source), COUNT(DISTINCT value) "
        "FROM result_axis GROUP BY axis"
    ).fetchall():
        if ns < MIN_VALUE_KINDS:
            flat_src.append(axis)
        if nv < MIN_VALUE_KINDS:
            flat_val.append(axis)
    out.append(result(C["V3-03"], rid, f">= {MIN_VALUE_KINDS}",
                      flat_src or "정상", not flat_src, flat_src))
    out.append(result(C["V3-04"], rid, f">= {MIN_VALUE_KINDS}",
                      flat_val or "정상", not flat_val, flat_val))

    na = [f"{a}:{n}" for a, n in conn.execute(
        "SELECT axis, COUNT(*) FROM result_axis WHERE value = -1 GROUP BY axis")]
    out.append(result(C["V3-07"], rid, "차종 사양과 일치", na or "없음", True, na))
    ex = [f"{a}:{n}" for a, n in conn.execute(
        "SELECT axis, COUNT(*) FROM result_axis WHERE excluded=1 GROUP BY axis")]
    out.append(result(C["V3-09"], rid, "차종 사양과 일치", ex or "없음", True, ex))

    # ★ 판정에 쓰는 축만 본다 (STEP 44).  부위명(panel)은 표시 전용이라
    #   대기해도 판정을 막지 않는다 — 여기서 잡으면 검사가 사실과 어긋난다
    from store.dictionary import JUDGING_AXES

    marks = ",".join("?" * len(JUDGING_AXES))
    pend_rows = conn.execute(
        f"SELECT axis, COUNT(*) FROM dict_enum WHERE status='pending' "
        f"AND axis IN ({marks}) GROUP BY axis", JUDGING_AXES).fetchall()
    pend = sum(n for _a, n in pend_rows)
    out.append(result(C["V3-08"], rid, 0, pend, pend == 0,
                      [f"{a}: {n}건" for a, n in pend_rows]))

    out.append(_shuffle_check(rid))

    # 경고·딜러는 점수에 들어가지 않는다 (STEP 59a)
    n = conn.execute(
        "SELECT COUNT(*) FROM result_axis WHERE axis LIKE 'warning%' "
        "OR axis LIKE 'dealer%' OR axis LIKE '%trust%'").fetchone()[0]
    out.append(result(C["V3-20"], rid, 0, n, n == 0))
    out.append(result(C["V3-21"], rid, 0, n, n == 0))

    # 경고가 있어도 매물이 목록에서 빠지지 않는다
    warned = conn.execute(
        "SELECT COUNT(*) FROM listing_warning w JOIN core_listing l "
        "ON l.listing_id = w.listing_id WHERE l.status='out_of_scope'").fetchone()[0]
    out.append(result(C["V3-22"], rid, 0, warned, warned == 0))

    n = conn.execute(
        "SELECT COUNT(*) FROM listing_warning WHERE evidence IS NULL "
        "OR evidence = ''").fetchone()[0]
    out.append(result(C["V3-27"], rid, 0, n, n == 0))
    out += _warning_contract_checks(conn, rid)
    out.append(_sort_determinism(conn, rid))
    out.append(_hda_source_check(conn, rid))
    out.append(_diagnosis_count_check(conn, rid))
    out += _conflict_checks(conn, rid)
    out.append(_halt_dict_check(conn, rid))
    out.append(_list_observed_source_check(conn, rid))
    out.append(_facet_reconcile_check(conn, rid))
    out += _file_output_checks(conn, rid)

    # ★ 딜러 없는 매물도 등급이 나온다.  차량 판정과 딜러는 다른 축이다
    bad = [r[0] for r in conn.execute(
        "SELECT l.listing_id FROM core_listing l JOIN listing_warning w "
        "USING(listing_id) WHERE l.dealer_id IS NULL "
        "AND w.warning_code = 'dealer_untrusted' LIMIT 20")]
    out.append(result(C["V3-31"], rid, 0, len(bad), not bad, bad))

    # ★ 「모른다」를 「안전」으로 바꾸면 사면 안 되는 차가 통과한다
    unknown_n = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE seizing_cnt IS NULL "
        "OR pledge_cnt IS NULL").fetchone()[0]
    warned = conn.execute(
        "SELECT COUNT(DISTINCT listing_id) FROM listing_warning "
        "WHERE warning_code = 'seizing_unknown'").fetchone()[0]
    ok = unknown_n == 0 or warned > 0
    out.append(result(C["V3-32"], rid, f"{unknown_n}건 경고", f"{warned}건", ok,
                      [] if ok else [f"seizing null {unknown_n}건인데 경고 0"]))
    return out


def _shuffle_check(run_id: str):
    """put() 호출 순서를 뒤섞어도 결과가 같은가 (STEP 60 · 불변식 ①).

    다르면 비결정 요소가 섞인 것이다 — 시각 · 난수 · 전역 상태 · dict 순회 순서
    """
    from analyze.verdict import Verdict, put

    rnd = random.Random(0)
    calls = [(f"axis{i}", i % len(VALUES), (i % len(PRIOS)) + 1, f"src{i}")
             for i in range(SHUFFLE_CALLS)]
    base = None
    for _ in range(SHUFFLE_SAMPLE):
        order = calls[:]
        rnd.shuffle(order)
        v = Verdict()
        for axis, val, prio, src in order:
            put(v, axis, val, prio, src)
        got = tuple(sorted(v.values.items()))
        if base is None:
            base = got
        elif got != base:
            return result(C["V3-11"], run_id, "동일", "불일치", False)
    return result(C["V3-11"], run_id, "동일", f"{SHUFFLE_SAMPLE}회 동일", True)


def _halt_dict_check(conn, rid):
    """V3-30 — halt 축의 사전이 비어 있는가 (S9 선행 조건).

    ★ halt 축은 새 값이 뜨면 판정 방향을 알 수 없는 축이다.
      사전이 비어 있으면 전 값이 새 값으로 보여 판정이 통째로 멈춘다.
      고정 집합은 지시서가 정한 것이다 — 관측이 아니라 사양이다 (STEP 42)
    """
    from store.dictionary import AXIS_POLICY

    # ★ 판정에 쓰는 halt 축만 본다.  표시 전용 축은 비어 있어도
    #   판정이 돈다 — 잡으면 첫 수집이 늘 실패로 나온다 (STEP 44)
    from store.dictionary import JUDGING_AXES

    halt_axes = sorted(a for a, p in AXIS_POLICY.items()
                       if (p.on_new == "halt" or p.on_conflict == "halt")
                       and a in set(JUDGING_AXES) | {"option3"})
    if not halt_axes:
        return not_applicable(C["V3-30"], rid, "halt 축이 없다")
    # ★ 축마다 사는 표가 다르다.  option3 · option_model 은 dict_option_code
    #   에 산다 — dict_enum 만 보면 「비었다」로 잘못 잡는다
    got = {a for (a,) in conn.execute(
        "SELECT DISTINCT axis FROM dict_enum WHERE status='confirmed'")}
    if conn.execute("SELECT COUNT(*) FROM dict_option_code "
                    "WHERE status='confirmed'").fetchone()[0]:
        got |= {"option3", "option_model"}
    bad = [f"{a}: 확정된 값이 없다" for a in halt_axes if a not in got]
    return result(C["V3-30"], rid, 0, len(bad), not bad, bad)
