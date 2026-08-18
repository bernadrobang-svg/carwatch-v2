# -*- coding: utf-8 -*-
"""V3 로직 검증 — 판정이 작동하는가 · 변별력이 있는가.

지시서   6장 STEP 59 · 59a (경고 · 딜러) · 60 (재현)
근거     판정이 「작동은 하는데 의미가 없는」 상태를 잡는다
         한 축의 source 가 전건 동일하면 우선순위 구조가 작동하지 않는 것이다
금지     사전 pending 이 판정에 쓰이는 것
"""
from __future__ import annotations

import os as _os

# ★ 검사 사본을 /tmp 에 두지 않는다 — 921MB tmpfs 인데 DB 가 484MB 다.
#   실측 08-17: 「database or disk is full」로 검사가 통째로 죽었다
CHECK_TMP = _os.path.join(
    _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
    "outputs", "check-tmp")

import collections
import random
import re

from analyze.axis.history import RENT_AD_TYPES
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
    "V3-58": Check("V3", "V3-58", "배터리 SOH 가 축이 아니라 가점임",
                   FATAL, "run",
                   "마스터 확정 — 「그게 있는 데 있고 대부분이 없는데. "
                   "그건 가점이니 필수는 아닌 듯해」.  전기차 778건 중 33건만 "
                   "있다 — 축으로 두면 745건이 억울하다 (개정 380)",
                   KIND_CODE),
    "V3-59": Check("V3", "V3-59", "가점이 분모를 늘리지 않음", FATAL, "run",
                   "분모는 675 그대로다.  가점이 크면 100%를 넘고 그대로 낸다. "
                   "★ 없다고 감점하지도 않는다 (개정 380)",
                   KIND_CONTRACT),
    "V3-72": Check("V3", "V3-72", "SOH 가점이 곡선대로 붙음", FATAL, "run",
                   "97%→+30 · 94%→+24 · 87%→+10 · 85% 이하 0. "
                   "화면에 「배터리 SOH 94.6% (+24)」로 따로 낸다 (개정 380)",
                   KIND_CODE),
    "V3-75": Check("V3", "V3-75", "트림 점수를 신차가로 잼", FATAL, "run",
                   "마스터 지적 — 「트림의 신차 가격이 중요해.  그게 차량의 "
                   "가격 차이야」.  순위(k/n)로 재면 700만 차이가 한 칸이 된다 "
                   "(개정 382)",
                   KIND_CODE),
    "V3-41": Check("V3", "V3-41", "전 매물의 분모가 만점과 같음",
                   FATAL, "run",
                   "축을 못 보면 분모에서 빼던 것을 없앴다 (개정 289). "
                   "못 볼수록 비율이 올라가면 못 찾을수록 좋은 등급이 된다 — "
                   "실측 08-16: 같은 차가 330/350 S · 330/555 D 였다",
                   KIND_CONTRACT),
    "V3-40": Check("V3", "V3-40", "핵심 축이 excluded 인데 등급을 매기지 않음",
                   FATAL, "run",
                   "가격 축을 못 보고도 등급이 나오면 그 등급은 뜻이 없다 "
                   "(개정 287)",
                   KIND_CONTRACT),
    "V3-47": Check("V3", "V3-47", "축별 차종 간 결측률 편차가 상한 안",
                   FATAL, "run",
                   "한 차종만 그 축을 못 받으면 그 차종이 통째로 불리해진다 "
                   "— 실측 08-17: 전기차의 safety.warranty_product 가 0% (개정 293)",
                   KIND_EXTERNAL),
    "V3-39": Check("V3", "V3-39", "이론가와 실제 중앙값의 차가 상한 안",
                   FATAL, "run",
                   "이론가가 실제 시장보다 높으면 전부 「싸다」로 나온다. "
                   "그러면 「싸다」가 아무 뜻이 없다 (개정 282)",
                   KIND_EXTERNAL),
    "V3-62": Check("V3", "V3-62", "원문이 없는데 값을 만든 축이 없음",
                   FATAL, "run",
                   "원문이 없으면 「확인 못 함」이지 「없음」이 아니다 — "
                   "v1 의 「[] 가 NULL 로」와 같은 유형 (개정 323)",
                   KIND_CONTRACT),
    "V3-64": Check("V3", "V3-64", "등급 경계가 절대 기준", FATAL, "run",
                   "백분위는 상대 기준이라 전체가 나쁘면 나쁜 차가 S 가 된다 "
                   "— S 90 · A 80 · B 70 · C 60 · D 50 (개정 324)",
                   KIND_CONTRACT),
    "V3-65": Check("V3", "V3-65", "확인율이 근거 있는 축만 셈", FATAL, "run",
                   "「안 받아서 0점」을 확인했다고 하면 화면이 거짓말한다 "
                   "— 「카탈로그 미조회」인데 「확인율 100%」였다 (개정 325)",
                   KIND_CONTRACT),
    "V3-55": Check("V3", "V3-55", "사이트 보증 축이 config 규칙을 읽는가",
                   FATAL, "run",
                   "사이트마다 우수등급의 뜻이 다르다 — 엔카 진단+우수등급 · "
                   "K카 등록됨.  코드에 사이트 이름을 박지 않는다 (개정 306)",
                   KIND_CONTRACT),
    "V3-56": Check("V3", "V3-56", "배점 합이 605", FATAL, "run",
                   "합이 안 맞으면 비율이 뜻을 잃는다 (개정 306)",
                   KIND_CONTRACT),
    "V3-57": Check("V3", "V3-57", "등급이 555 기준", FATAL, "run",
                   "취향 50 은 순위에만 쓴다 — 등급은 ①②③⑤ 555 다 (개정 306)",
                   KIND_CONTRACT),
    "V3-70": Check("V3", "V3-70", "일반·동력계 보증을 따로 냄",
                   FATAL, "run",
                   "긴 쪽 하나로 뭉치면 「일반은 끝났고 동력계만 남았다」를 "
                   "못 본다.  일반 20 · 동력계 30 (개정 365)",
                   KIND_CONTRACT),
    "V3-71": Check("V3", "V3-71", "보증 잔여가 기간·거리 중 낮은 쪽임",
                   FATAL, "run",
                   "보증은 둘 중 먼저 닿는 쪽에서 끝난다 — "
                   "기간만 보면 주행이 많은 차를 과대평가한다 (개정 365)",
                   KIND_CODE),
    "V3-68": Check("V3", "V3-68", "부록 F 전 24축이 구현돼 있음",
                   FATAL, "run",
                   "축 목록을 코드에 박지 않는다 — 부록 F 「축 목록 — 전 24축」"
                   "을 읽어 배점표와 맞춘다.  축 하나가 빠지면 그 배점만큼 "
                   "전건이 0점인데 아무도 모른다 (개정 329 전수 검증)",
                   KIND_CONTRACT),
    "V3-52": Check("V3", "V3-52", "「싸다」에 이유가 붙어 있음", FATAL, "run",
                   "이유 없이 싼 차는 없다.  못 찾았으면 그렇게 적는다 "
                   "— 마스터 지적 「엔카 보증이 없는 것이 가격이 왜 싼지가 "
                   "중요해」 (개정 299)",
                   KIND_CONTRACT),
    "V3-53": Check("V3", "V3-53", "점검 출처가 판정에 반영됨", FATAL, "run",
                   "엔카직영 점검과 판매자 등록 점검은 다르다 — "
                   "「모든 책임은 판매자에게 있습니다」 (개정 300)",
                   KIND_CONTRACT),
    "V3-54": Check("V3", "V3-54", "렌트 이력을 세 곳에서 대조", FATAL, "run",
                   "advertisementType 만 보면 「지금 리스 상품인가」다. "
                   "과거 렌트는 점검부 용도변경과 보험이력에 있다 "
                   "— 실측 08-17: 「렌트 아님」이라 한 144건이 렌트였다 (개정 302)",
                   KIND_CONTRACT),
    "V3-45": Check("V3", "V3-45", "배점 합이 만점과 같음", FATAL, "run",
                   "합이 안 맞으면 비율이 뜻을 잃는다 (개정 292)",
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
    out_dir = tempfile.mkdtemp(dir=_ensure_tmp())
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
    """V3-38 — facet 을 받았으면 목록 관측분과 대조했는가 (개정 266 · 12-dict).

    ★ 값으로 대조한다.  `source_endpoint` 로 대조하면 안 된다 —
      그 컬럼은 「어디서 처음 봤나」지 「facet 에 있나」가 아니다.
      facet 이 늦게 오면 이미 목록에서 본 값은 'list' 로 남는다.
      둘을 같은 것으로 읽어 이 검사가 41건을 「facet 에 없다」고 하고 있었다.
      실측 08-18 — 값으로 견주니 facet 에 없는 값은 0건이었다.
      ★ 「있는 것을 없다고」 한 것이라 놓친 것보다 나쁘다
    양쪽을 다 본다 (12-dict)
      facet 에만 있는 값   새 pending 으로 들어와야 한다
      목록에만 있는 값     ★ 확인이 필요하다 — facet 에 없는 값이 왜 매물에 있나
    """
    import json as _j

    from tools.build_dict import LIST_FALLBACK, facet_value_set

    del _j
    n_facet = conn.execute("SELECT COUNT(*) FROM raw_facet").fetchone()[0]
    if not n_facet:
        return not_applicable(C["V3-38"], rid, "facet 을 아직 못 받았다")
    bad, left, added = [], 0, 0
    for axis in sorted(LIST_FALLBACK):
        theirs = facet_value_set(conn, axis)
        if not theirs:
            # facet 이 그 축을 안 준다 — 목록에서 뽑는 것이 맞다 (trim 이 그렇다)
            continue
        mine = {v for (v,) in conn.execute(
            "SELECT value FROM dict_enum WHERE axis=?", (axis,))}
        only = sorted(mine - theirs)
        left += len(only)
        added += len(theirs & mine)
        if only:
            bad.append(f"{axis}: facet 에 없는 값 {len(only)}건 "
                       f"— {', '.join(only[:4])}.  왜 매물에 있나")
        missing = sorted(theirs - mine)
        if missing:
            bad.append(f"{axis}: facet 이 준 값 {len(missing)}건이 사전에 "
                       f"안 들어왔다 — {', '.join(missing[:4])}")
    return result(C["V3-38"], rid, "대조 완료",
                  f"facet 과 맞은 값 {added} · 목록에만 있는 값 {left}",
                  not bad, bad[:6])


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


# 이것을 못 보고 매긴 등급은 뜻이 없다 (개정 287 · 292 배점 기준)
CORE_AXES = ("value.market", "value.depreciation", "state.accident")


def _core_axis_check(conn, rid):
    """V3-40 — 핵심 축이 excluded 인데 등급을 매겼는가 (개정 287).

    ★ 가격을 못 보고 매긴 등급은 뜻이 없다.  숫자로 낸다
    """
    bad = []
    for axis in CORE_AXES:
        n = conn.execute(
            "SELECT COUNT(*) FROM result_axis a JOIN result_score s"
            " ON s.listing_id=a.listing_id AND s.calc_version=a.calc_version"
            " WHERE a.axis=? AND a.excluded=1"
            " AND s.grade IS NOT NULL AND s.grade NOT IN ('NOT_RATED','E')",
            (axis,)).fetchone()[0]
        if n:
            bad.append(f"{axis} 를 못 봤는데 등급을 매긴 것 {n}건")
    return result(C["V3-40"], rid, 0, len(bad), not bad, bad)


def _rental_cross_check(conn, rid):
    """V3-54 — 렌트를 세 곳에서 대조했는가 (개정 302).

    ★ 셋 중 하나라도 렌트라 하는데 「렌트 아님」으로 점수를 준 것을 센다
    """
    bad = []
    # ★ 지금 채점본만 본다.  옛 calc_version 의 잔재는 V3-41 이 따로 잡는다
    cv = conn.execute("SELECT calc_version FROM result_score"
                      " ORDER BY calculated_at DESC LIMIT 1").fetchone()
    cv = cv[0] if cv else ""
    # ★ 리스는 10점이 맞다 (개정 292).  「자가용 25점」이라 한 것만 잡는다
    private = conn.execute(
        "SELECT COUNT(*) FROM result_axis a JOIN core_listing l"
        " ON l.listing_id = a.listing_id"
        " WHERE a.axis = 'history.usage' AND a.source = 'checked_three'"
        " AND a.calc_version = ? AND l.advertisement_type IN"
        f" ({','.join('?' * len(RENT_AD_TYPES))})",
        (cv, *sorted(RENT_AD_TYPES))).fetchone()[0]
    if private:
        bad.append(f"광고형태가 렌트·리스인데 「자가용」 {private}건")
    n = conn.execute(
        "SELECT COUNT(*) FROM result_axis a JOIN core_inspection i"
        " ON i.listing_id = a.listing_id"
        " WHERE a.axis = 'history.usage' AND a.source = 'checked_three'"
        " AND a.calc_version = ?"
        " AND i.usage_change_types_json LIKE '%\"렌트\"%'", (cv,)).fetchone()[0]
    if n:
        bad.append(f"점검부 용도변경이 렌트인데 「렌트 아님」 {n}건")
    # 근거 이름에 세 곳이 다 등장하는가 — 한 곳만 보고 있으면 여기서 걸린다
    seen = {r[0] for r in conn.execute(
        "SELECT DISTINCT source FROM result_axis"
        " WHERE axis='history.usage' AND calc_version=?", (cv,))}
    for want in ("advertisement_type", "usage_change_types", "record_use"):
        if not any(want in got for got in seen):
            bad.append(f"근거에 {want} 가 한 번도 안 나온다")
    return result(C["V3-54"], rid, 0, len(bad), not bad, bad)


def _why_cheap_check(conn, rid):
    """V3-52 · V3-53 — 「왜 싼가」와 점검 출처 (개정 299 · 300).

    ★ 화면이 「시세차 −1,100만」만 내고 끝내면 안 된다
    """
    import json

    from analyze.trust import TRUST_LOW, TRUST_NONE, platform_trust
    from report.why_cheap import NOT_FOUND

    bad52, bad53 = [], []
    seen = collections.Counter()
    for fmt, diag, ext, deemed in conn.execute(
        "SELECT inspection_formats_json, diagnosis_car, warranty_extend,"
        " warranty_deemed FROM core_listing WHERE status='active'"
    ):
        trust, _why = platform_trust(json.loads(fmt) if fmt else None, diag,
                                     bool(ext and ext != '0')
                                     or bool(deemed and deemed != '0'))
        seen[trust] += 1
    if not seen:
        return [not_applicable(C["V3-52"], rid, "매물이 없다"),
                not_applicable(C["V3-53"], rid, "매물이 없다")]
    # V3-53 — 출처가 갈리는가.  전부 한 값이면 안 가르고 있는 것이다
    if len([k for k in seen if k]) < 2:
        bad53.append(f"신뢰도가 한 값뿐이다 — {dict(seen)}")
    if TRUST_LOW not in seen and TRUST_NONE not in seen:
        bad53.append("판매자 등록 점검을 하나도 못 가렸다")
    # V3-52 — 화면 문구가 있는가.
    # ★ 부록 G 로 「왜 싼가」가 상세 ③절로 갔다 (개정 332).
    #   목록은 요약이라 이유는 상세에 둔다
    html = _rendered_why()
    if html is None:
        bad52.append("렌더 결과가 없다 — tools/render_screens.py 를 돌린다")
    elif "싼 이유" not in html and NOT_FOUND not in html:
        bad52.append("상세 ③절에 「왜 싼가」가 없다")
    return [result(C["V3-52"], rid, 0, len(bad52), not bad52, bad52),
            result(C["V3-53"], rid, "출처가 갈린다",
                   dict(seen) if not bad53 else bad53, not bad53, bad53)]


def _source_before_value_check(conn, rid):
    """V3-62 — 원문이 없는데 축에 값을 만들었는가 (개정 323).

    ★ 마스터 지적 — 「보험이력도 성능기록도 없는데 왜 S 냐」
    ★ 셋을 가른다 — 원문에 「없음」이 적혔다 / 원문이 없다 / 항목이 없다.
      셋을 같은 값으로 저장하면 여기서 끝난다
    """
    cv = conn.execute("SELECT calc_version FROM result_score"
                      " ORDER BY calculated_at DESC LIMIT 1").fetchone()
    cv = cv[0] if cv else ""
    bad = []
    for axis, table in (("state.accident", "core_record"),
                        ("state.repair", "core_record"),
                        ("state.frame", "core_inspection")):
        # ★ 「0점 + 확인 안 됨」은 값을 만든 것이 아니다 (개정 325).
        #   source 가 missing 이면 우리가 「모른다」고 말한 것이다
        n = conn.execute(
            "SELECT COUNT(*) FROM result_axis a WHERE a.axis=?"
            " AND a.calc_version=? AND a.excluded=0 AND a.source <> 'missing'"
            f" AND NOT EXISTS (SELECT 1 FROM {table} t"
            "   WHERE t.listing_id = a.listing_id AND t.row_status='ok')",
            (axis, cv)).fetchone()[0]
        if n:
            bad.append(f"{axis} — {table} 원문 없이 값 {n}건")
    return result(C["V3-62"], rid, 0, len(bad), not bad, bad)


def _absolute_cut_check(rid):
    """V3-64 — 등급 경계가 절대 기준인가 (개정 324)."""
    import json
    import os

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, "config", "scoring.json"),
              encoding="utf-8") as f:
        cuts = json.load(f)["grade_cuts"]
    # ★ 규격의 표에서 읽는다.  코드에 두 벌 두면 어느 쪽이 정본인지 모른다.
    #   ★ 지시서 전체를 훑지 않는다 — 다른 글의 「A   50 으로 되돌린다」
    #     같은 줄을 주워 헛걸린다 (실측 08-18 · guide/04_질의.md)
    from validate.base import canon_text

    text = canon_text("등급", root)
    want = {g: int(n) / 100
            for g, n in re.findall(
                r"^\s*(?:필수\s+)?([SABCD])\s+(\d{2})%?\s*(?:이상)?", text,
                re.M)}
    # 규격에서 읽은 등급 수 — S·A·B·C·D.  ★ E 는 절대 배제라 경계가 없다
    if len(want) < len(cuts):
        return not_applicable(C["V3-64"], rid, "규격에서 경계를 못 읽었다")
    # ★ 백분율을 정수로 견준다.  실수 비교 오차를 만들지 않는다
    bad = [f"{g} {cuts.get(g)} != {v}" for g, v in sorted(want.items())
           if round(float(cuts.get(g, 0)) * 100) != round(v * 100)]
    got = " · ".join(f"{g}{int(v * 100)}" for g, v in sorted(want.items()))
    return result(C["V3-64"], rid, got,
                  "맞다" if not bad else bad, not bad, bad)


def _spec_files():
    import glob
    import os

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return [(f, open(f, encoding="utf-8").read())
            for f in sorted(glob.glob(os.path.join(root, "docs", "**", "*.md"),
                                      recursive=True))]


def _confirm_ratio_check(conn, rid):
    """V3-65 — 확인율이 근거 있는 축만 세는가 (개정 325).

    ★ 「안 받아서 0점」을 확인했다고 하면 화면이 거짓말한다
    """
    cv = conn.execute("SELECT calc_version FROM result_score"
                      " ORDER BY calculated_at DESC LIMIT 1").fetchone()
    cv = cv[0] if cv else ""
    bad = []
    n = conn.execute(
        "SELECT COUNT(*) FROM result_score WHERE calc_version=?"
        " AND confirmed_points IS NULL", (cv,)).fetchone()[0]
    if n:
        bad.append(f"확인율을 안 낸 매물 {n}건")
    # ★ 근거가 없는 축이 있는데 확인율이 만점이면 거짓이다
    n = conn.execute(
        "SELECT COUNT(*) FROM result_score s WHERE s.calc_version=?"
        " AND s.confirmed_points >= s.denominator"
        " AND EXISTS (SELECT 1 FROM result_axis a"
        "   WHERE a.listing_id=s.listing_id AND a.calc_version=s.calc_version"
        "   AND (a.excluded=1 OR a.source IN"
        "        ('missing','na','unknown','gate_closed',"
        "         'market_sample_short','expected_unavailable')))",
        (cv,)).fetchone()[0]
    if n:
        bad.append(f"근거 없는 축이 있는데 확인율이 만점인 매물 {n}건")
    return result(C["V3-65"], rid, 0, len(bad), not bad, bad)


# 부록 F 축 목록 표의 「축」 이름 ↔ 코드의 축 코드
SPEC_AXIS_NAMES = {
    "시세 대비": "value.market", "신차가 대비": "value.depreciation",
    "주행 대비": "value.mileage",
    # ★ 부록 F 축 목록에서 배점이 「(30)」 괄호다 — 따로 선 축이 아니라
    #   전기차일 때 주행 70 을 주행 40 + SOH 30 으로 나눈 것이다 (1-3 · 개정 318)
    "배터리 SOH": "value.mileage",
    "사고 이력": "state.accident", "골격": "state.frame",
    "외판": "state.outer", "자차 수리비": "state.repair",
    "특수 사고": "state.special", "누유": "state.leak",
    "소모품": "state.consumable", "진정성": "state.integrity",
    "용도": "history.usage", "자차 미가입": "history.not_join",
    "소유자 변경": "history.owner", "압류·저당": "history.lien",
    "트림": "spec.trim", "옵션": "spec.options",
    "사이트 보증": "warranty.site", "일반·차체": "warranty.general",
    "동력계": "warranty.power", "HUD": "taste.hud",
    "지정 옵션": "taste.picked", "색상": "taste.color",
    "선루프": "taste.sunroof",
}


def _warranty_checks(conn, rid):
    """V3-70 · V3-71 — 제조사 보증을 둘로 · 낮은 쪽으로 (개정 365)."""
    import json
    import os

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, "config", "scoring.json"),
              encoding="utf-8") as f:
        pol = json.load(f)
    comp = pol["components"]
    bad70 = [x for x in ("warranty.general", "warranty.power")
             if x not in comp]
    if "warranty.maker" in comp:
        bad70.append("warranty.maker 가 남아 있다 — 개정 365 로 둘로 갈렸다")
    # V3-71 — 기간만 보면 주행 많은 차가 과대평가된다.  식을 직접 재 본다
    from analyze.axis.site import remaining_months

    per = float(pol["axis_rules"]["warranty"]["km_per_month"])
    # 기간은 넉넉한데 거리를 다 쓴 차 — 낮은 쪽(거리)이 나와야 한다.
    # ★ 견본 값은 config 에 둔다 (V4-13) — 검사가 숫자를 박지 않는다
    with open(os.path.join(root, "config", "checks.json"),
              encoding="utf-8") as f:
        probe = json.load(f)["warranty_probe"]
    got = remaining_months(probe["months"], probe["km_limit"],
                           probe["elapsed"], probe["mileage"], per)
    want = min(probe["months"] - probe["elapsed"],
               (probe["km_limit"] - probe["mileage"]) / per)
    bad71 = ([] if got is not None and abs(got - want) < float(probe["eps"])
             else [f"기간·거리 중 낮은 쪽이 아니다 — {got} != {want}"])
    return [result(C["V3-70"], rid, 0, len(bad70), not bad70, bad70[:4]),
            result(C["V3-71"], rid, "낮은 쪽",
                   "맞다" if not bad71 else "아니다", not bad71, bad71)]


def _spec_axis_check(conn, rid):
    """V3-68 — 부록 F 전 24축이 구현돼 있는가.

    ★ 축 이름을 여기 적지 않는다.  부록 F 「축 목록」 표를 읽는다 —
      규격이 축을 더하면 이 검사가 먼저 걸린다
    """
    import json
    import os

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # ★ 정본 위치는 config/checks.json 이 안다 (개정 342)
    from validate.base import canon_text

    body = canon_text("배점", root)
    if not body:
        return not_applicable(C["V3-68"], rid, "배점 정본을 못 찾았다")
    head = body.find("# 축 목록")
    if head < 0:
        return not_applicable(C["V3-68"], rid, "부록 F 에 축 목록이 없다")
    block = body[head:body.find("\n#", head + 1)]
    want = []
    for line in block.splitlines():
        got = re.match(r"^\| *[\w]+ *\| *[^|]+? *\| *([^|]+?) *\|", line)
        if got and got.group(1) not in ("축", "---"):
            want.append(got.group(1))
    if not want:
        return not_applicable(C["V3-68"], rid, "축 목록 표를 못 읽었다")
    with open(os.path.join(root, "config", "scoring.json"),
              encoding="utf-8") as f:
        have = set(json.load(f)["components"])
    bad = []
    for name in want:
        code = SPEC_AXIS_NAMES.get(name)
        if code is None:
            bad.append(f"부록 F 의 축 「{name}」을 코드 이름으로 못 잇는다")
        elif code not in have:
            bad.append(f"{name} ({code}) 이 scoring.json 에 없다")
    return result(C["V3-68"], rid, len(want), len(want) - len(bad),
                  not bad, bad[:8])


def _site_axis_checks(conn, rid):
    """V3-55 · V3-56 · V3-57 — 사이트 보증 축과 605 배점 (개정 306)."""
    import json
    import os

    from analyze.axes import GRADE_EXCLUDED_AXES, axis_of

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, "config", "scoring.json"), encoding="utf-8") as f:
        pol = json.load(f)
    with open(os.path.join(root, "config", "sites.json"), encoding="utf-8") as f:
        sites = json.load(f)

    # V3-55 — 규칙이 config 에 있고 코드에 사이트 이름이 없는가
    bad55 = []
    active = [k for k, v in sites.items()
              if isinstance(v, dict) and v.get("status") == "active"]
    for site in active:
        items = sites[site].get("warranty_items")
        if not isinstance(items, list) or not items:
            bad55.append(f"{site} — warranty_items 가 없다 (개정 365)")
    src = open(os.path.join(root, "analyze", "axis", "site.py"),
               encoding="utf-8").read()
    body = "\n".join(ln for ln in src.splitlines()
                     if not ln.lstrip().startswith("#"))
    body = body.split('"""', 2)[-1]        # 파일 머리 설명은 뺀다
    for site in sites:
        if f'"{site}"' in body or f"'{site}'" in body:
            bad55.append(f"코드에 사이트 이름 {site} 이 박혀 있다")

    # V3-56 — 배점 합
    total = sum(v if isinstance(v, int) else v.get("points", 0)
                for v in pol["components"].values()
                if not (isinstance(v, dict) and v.get("skipped")))
    want = int(pol["total_points"])

    # V3-57 — 등급 기준은 취향을 뺀 합인가
    base = sum(v if isinstance(v, int) else v.get("points", 0)
               for k, v in pol["components"].items()
               if axis_of(k) not in GRADE_EXCLUDED_AXES
               and not (isinstance(v, dict) and v.get("skipped")))
    want_base = int(pol.get("grade_base_points") or 0)
    return [
        result(C["V3-55"], rid, 0, len(bad55), not bad55, bad55[:6]),
        result(C["V3-56"], rid, want, total, total == want),
        result(C["V3-57"], rid, want_base, base, base == want_base),
    ]


def _rendered_why():
    import os

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, "outputs", "render", "why_listing_id.html")
    if not os.path.isfile(path):
        return None
    return open(path, encoding="utf-8").read()


def _rendered_listings():
    import os

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, "outputs", "render", "listings.html")
    if not os.path.isfile(path):
        return None
    return open(path, encoding="utf-8").read()


def _fill_gap_check(conn, rid):
    """V3-47 — 축별 차종 간 결측률 편차 (개정 293).

    ★ 한 차종만 그 축을 못 받으면 그 차종이 통째로 불리해진다.
      배점을 차종별로 둘지 정하려면 편차를 먼저 봐야 한다
    """
    import json as _j
    import os as _o

    root = _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__)))
    with open(_o.path.join(root, "config", "checks.json"),
              encoding="utf-8") as f:
        cap = float(_j.load(f)["fill_rate_gap_max"])
    rows = conn.execute(
        "SELECT a.axis, l.target_key,"
        " SUM(CASE WHEN a.excluded=0 THEN 1 ELSE 0 END) * 1.0 / COUNT(*)"
        " FROM result_axis a JOIN core_listing l"
        " ON l.listing_id = a.listing_id"
        " WHERE l.target_key IS NOT NULL GROUP BY 1, 2").fetchall()
    by: dict = {}
    for axis, tk, rate in rows:
        by.setdefault(axis, []).append((rate, tk))
    bad = []
    for axis, got in sorted(by.items()):
        hi = max(r for r, _t in got)
        lo = min(got)
        if hi - lo[0] > cap:
            bad.append(f"{axis} — {lo[1]} 가 {lo[0] * 100:.0f}% 인데 "
                       f"최고는 {hi * 100:.0f}%")
    return result(C["V3-47"], rid, f"편차 <= {cap * 100:.0f}%p",
                  f"{len(bad)}축", not bad, bad[:8])


def _points_sum_check(rid):
    """V3-45 — 배점 합이 만점과 같은가 (개정 292)."""
    import json as _j
    import os as _o

    root = _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__)))
    with open(_o.path.join(root, "config", "scoring.json"),
              encoding="utf-8") as f:
        pol = _j.load(f)
    total = float(pol["total_points"])
    comps = pol.get("components") or {}
    got = sum(float(v) for v in comps.values())
    bad = ([] if got == total
           else [f"배점 합 {got:g} != 만점 {total:g}"])
    return result(C["V3-45"], rid, f"{total:g}", f"{got:g}", not bad, bad)


def _market_gap_check(conn, rid):
    """V3-39 — 이론가와 실제 중앙값의 차 (개정 282).

    ★ 이론가가 늘 높으면 전부 「싸다」로 나오고 그 말이 뜻을 잃는다.
      차종별로 재서 상한을 넘는 것을 낸다
    """
    import json as _j
    import os as _o
    import statistics

    from analyze.axis._util import months_between
    from analyze.axis.price import coefficient_sane, expected_price

    root = _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__)))
    with open(_o.path.join(root, "config", "depreciation.json"),
              encoding="utf-8") as f:
        dep = _j.load(f)
    with open(_o.path.join(root, "config", "checks.json"),
              encoding="utf-8") as f:
        got = _j.load(f)
    cap = float(got["market_gap_max"])
    need = int(got["market_gap_min_sample"])
    as_of = conn.execute(
        "SELECT MAX(calculated_at) FROM result_score").fetchone()[0]
    if not as_of:
        return not_applicable(C["V3-39"], rid, "판정 결과가 없다")
    bad, worst = [], 0.0
    for (tk,) in conn.execute(
            "SELECT DISTINCT target_key FROM core_listing"
            " WHERE target_key IS NOT NULL ORDER BY 1"):
        coef = (dep.get("coefficient") or {}).get(tk)
        if not coefficient_sane(coef, dep.get("coefficient_sane_range")):
            continue          # 판정에서 안 쓰는 차종이다
        exp, real = [], []
        for price, origin, ym in conn.execute(
                "SELECT price_current_won, price_origin_won, year_month"
                " FROM core_listing WHERE target_key=? AND status='active'"
                " AND price_current_won IS NOT NULL"
                " AND price_origin_won IS NOT NULL", (tk,)):
            got = expected_price(origin, months_between(ym, as_of),
                                 dep.get("curve"), coef,
                                 dep.get("curve_beyond"))
            if got:
                exp.append(got)
                real.append(price)
        if len(exp) < need:
            continue
        te, tm = statistics.median(exp), statistics.median(real)
        gap = (te - tm) / tm
        worst = max(worst, abs(gap))
        if abs(gap) > cap:
            bad.append(f"{tk} 이론가가 실제 중앙값 대비 {gap * 100:+.1f}%")
    return result(C["V3-39"], rid, f"|차| <= {cap * 100:.0f}%",
                  f"최대 {worst * 100:.1f}%", not bad, bad[:8])


def _bonus_checks(conn, rid):
    """V3-58 · V3-59 · V3-72 — 배터리 SOH 가점 (개정 380).

    마스터 확정 — 「그건 가점이니 필수는 아닌 듯해」
    ★ 없다고 감점하지 않는다 — 엔카가 진단 안 한 죄를 차에 묻는 것이다
    ★ 분모를 안 늘린다.  가점이 크면 100%를 넘고 그대로 낸다
    """
    import json as _j
    import os as _os

    root = _os.path.dirname(_os.path.dirname(
        _os.path.abspath(__file__)))

    with open(_os.path.join(root, "config", "scoring.json"),
              encoding="utf-8") as f:
        raw = _j.load(f)
    full = (raw.get("bonus") or {}).get("battery_soh")
    if not full:
        return [result(C["V3-58"], rid, "있다", "없다", False,
                       ["config/scoring.json 에 bonus.battery_soh 가 없다"]),
                not_applicable(C["V3-59"], rid, "가점 표가 없다"),
                not_applicable(C["V3-72"], rid, "가점 표가 없다")]
    # V3-58 — 축이 아니라 가점인가
    bad58 = []
    if "battery_soh" in (raw.get("components") or {}):
        bad58.append("battery_soh 가 components 에 있다 — 축이 아니다")
    a = result(C["V3-58"], rid, "가점", f"+{full}", not bad58, bad58)

    # V3-59 — 없다고 감점하지 않는가.  분모를 안 늘리는가
    bad59 = []
    if "battery_soh" in (raw.get("penalties") or {}):
        bad59.append("battery_soh 가 penalties 에 있다 — 없다고 벌하면 안 된다")
    rows = conn.execute(
        "SELECT COUNT(*), COUNT(DISTINCT denominator) FROM result_score"
        " WHERE bonuses_json NOT IN ('', '[]') AND bonuses_json IS NOT NULL"
    ).fetchone()
    n = rows[0] if rows else 0
    if n:
        # ★ 가점을 받은 매물과 못 받은 매물의 분모가 같아야 한다
        two = conn.execute(
            "SELECT COUNT(DISTINCT denominator) FROM result_score").fetchone()
        if two and two[0] > 1:
            bad59.append(f"분모가 {two[0]}가지다 — 가점이 분모를 늘렸다")
    b = result(C["V3-59"], rid, "한 가지", f"가점 {n}건", not bad59, bad59)

    # V3-72 — 곡선대로 붙는가.  화면에 따로 나오는가
    bad72 = []
    curve = (raw.get("axis_rules", {}).get("value", {}) or {}).get("soh_curve")
    if not curve:
        bad72.append("soh_curve 가 없다")
    for soh, got in conn.execute(
        "SELECT l.ev_battery_soh, s.bonuses_json FROM result_score s"
        " JOIN core_listing l ON l.listing_id = s.listing_id"
        " WHERE l.ev_battery_soh IS NOT NULL LIMIT 40"
    ):
        want = 0
        for edge, pts in (curve or []):
            if float(soh) >= float(edge):
                want = int(pts)
                break
        have = 0
        for _k, p, _w in _j.loads(got or "[]"):
            have += int(p)
        if want != have:
            bad72.append(f"SOH {soh} 는 +{want} 여야 하는데 +{have} 다")
    path = _os.path.join(root, "outputs", "render", "why_listing_id.html")
    if _os.path.isfile(path):
        html = open(path, encoding="utf-8").read()
        if "가점" not in html:
            bad72.append("상세에 가점 절이 없다")
    return [a, b, result(C["V3-72"], rid, "곡선대로",
                         "맞다" if not bad72 else "다르다",
                         not bad72, bad72[:4])]


def _trim_price_check(conn, rid):
    """V3-75 — 트림 점수를 신차가로 재는가 (개정 382).

    마스터 지적 — 「트림의 신차 가격이 중요해.  그게 차량의 가격 차이야」
    ★ 순위(k/n)로 재면 700만 차이가 한 칸이 된다
    """
    from analyze.axis.trim import price_ratio

    from validate.base import canon_text

    bad = []
    # ★ 손계산 표를 코드에 박지 않는다.  규격의 표에서 읽는다 (배점 정본).
    #   「| 스탠다드 | 6,500만 | 0.833 | **20.8** |」 꼴이다
    rows = re.findall(
        r"^\|[^|]+\|\s*([\d,]+)만\s*\|[^|]*\|\s*\*{0,2}([\d.]+)\*{0,2}\s*\|",
        canon_text("배점"), re.M)
    table = [(int(a.replace(",", "")), float(b)) for a, b in rows]
    if len(table) < 2:
        bad.append("배점 정본에 트림 표가 없다 — 손계산을 못 한다")
    else:
        full = max(p for _n, p in table)
        ladder = [n for n, _p in table]
        for man, want in table:
            got = round(price_ratio(man, ladder) * full, 1)
            # ★ 표는 소수 한 자리다.  반올림 자리만큼만 봐준다
            if round(got, 1) != round(want, 1):
                bad.append(f"{man}만 은 {want} 여야 하는데 {got} 다")
    # ★ 실제 판정도 그런가 — 같은 차종에서 신차가가 높으면 점수도 높아야 한다
    rows = conn.execute(
        # ★ 점수는 score 가 비면 value 에 있다 — 둘 중 있는 것을 본다
        "SELECT l.target_key, l.price_origin_won,"
        "       COALESCE(a.score, a.value)"
        " FROM result_axis a JOIN core_listing l ON l.listing_id = a.listing_id"
        " WHERE a.axis = 'spec.trim' AND a.source = 'trim_origin_price'"
        "   AND l.price_origin_won IS NOT NULL"
        " ORDER BY l.target_key, l.price_origin_won").fetchall()
    prev = None
    for tk, price, score in rows:
        if score is None:
            continue          # ★ 점수가 없는 행은 견줄 것이 없다
        if prev and prev[0] == tk and price > prev[1] and score < prev[2]:
            bad.append(f"{tk} — 신차가가 높은데 트림 점수가 낮다 "
                       f"({price:,} {score} < {prev[1]:,} {prev[2]})")
        prev = (tk, price, score)
    return result(C["V3-75"], rid, "신차가 비율",
                  f"{len(rows)}건", not bad, bad[:4])


def run(conn, ctx) -> list:
    rid = ctx.run_id
    out = []
    out.append(_denominator_check(conn, rid))
    # 가점 (개정 380) · 트림 신차가 (개정 382)
    out.extend(_bonus_checks(conn, rid))
    out.append(_trim_price_check(conn, rid))
    out.append(_points_sum_check(rid))
    out.append(_market_gap_check(conn, rid))
    out.append(_core_axis_check(conn, rid))
    out.append(_fill_gap_check(conn, rid))
    out.append(_rental_cross_check(conn, rid))
    out += _why_cheap_check(conn, rid)
    out += _site_axis_checks(conn, rid)
    out.append(_spec_axis_check(conn, rid))
    out += _warranty_checks(conn, rid)
    out.append(_source_before_value_check(conn, rid))
    out.append(_absolute_cut_check(rid))
    out.append(_confirm_ratio_check(conn, rid))

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


def _ensure_tmp() -> str:
    """검사 사본 자리.  ★ /tmp(tmpfs)가 아니라 디스크에 둔다."""
    _os.makedirs(CHECK_TMP, exist_ok=True)
    return CHECK_TMP
