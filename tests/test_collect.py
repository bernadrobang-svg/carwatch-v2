# -*- coding: utf-8 -*-
"""2장 수집 시험.

지시서   STEP 18 (라벨↔내용) · STEP 23 (필수 축 · collect_group)
         STEP 24 (실패 3종) · STEP 27 (수집 검증 훅) · STEP 32 (빈 배열)
사용     python3 tests/test_collect.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adapters.encar import _SCHEMA  # noqa: E402
from collect.fetcher import fetch, reject_reason, verify_shape  # noqa: E402
from collect.runner import (  # noqa: E402
    check_facet_axes,
    collect_check,
    collect_groups,
    facet_axes,
    interpret_failure,
    load_targets,
)
from contracts import FetchResult, Response  # noqa: E402
from store.raw import open_db, save_raw  # noqa: E402

AT = datetime(2026, 8, 10, tzinfo=timezone.utc)
FAIL: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{'  ' + detail if detail else ''}")
    if not ok:
        FAIL.append(name)


def R(kind, status, raw):
    return FetchResult(kind, "42473896", status, raw, 200, None, AT)


# ── STEP 18 ──────────────────────────────────────────────────────────
def test_verify_shape() -> None:
    # ★ 목록은 봉투 기준이다 (STEP 18a)
    env = R("list", "ok", {"Count": 208, "SearchResults": [{"Id": "1"}]})
    check("목록 봉투 통과", verify_shape(env, _SCHEMA["list"]))
    check("요소를 봉투로 착각하면 거부",
          not verify_shape(R("list", "ok", {"Id": "1", "ModelGroup": "G80"}),
                           _SCHEMA["list"]))
    check("빈 SearchResults 도 정상 (마지막 페이지)",
          verify_shape(R("list", "ok", {"Count": 0, "SearchResults": []}),
                       _SCHEMA["list"]))

    ok = R("record", "ok", {"carNo": "12가3456", "openData": True})
    check("record 정상 통과", verify_shape(ok, _SCHEMA["record"]))

    # v1 최대 사고 — 점검부 응답이 record 라벨로 저장된 경우.
    # any() 로 쓰면 통과한다.  all() 이라 걸린다.
    mislabeled = R("record", "ok", {"master": {}, "outers": []})
    check("점검부가 record 라벨 → 거부", not verify_shape(mislabeled, _SCHEMA["record"]))

    half = R("record", "ok", {"carNo": "12가3456"})
    check("required_keys 한쪽만 → 거부", not verify_shape(half, _SCHEMA["record"]))

    arr = R("catalog", "ok", [{"optionCd": "1009"}])
    check("catalog 배열 통과", verify_shape(arr, _SCHEMA["catalog"]))
    check("빈 배열은 정상 (STEP 32)", verify_shape(R("catalog", "ok", []), _SCHEMA["catalog"]))
    check("배열인데 object → 거부", not verify_shape(R("catalog", "ok", {}), _SCHEMA["catalog"]))

    # diagnosis 는 원문 0건이라 required_keys 가 빈 목록이다.  all() 은 공집합에 참.
    check("diagnosis 는 통과 (STEP 21b)", verify_shape(R("diagnosis", "ok", {"x": 1}), _SCHEMA["diagnosis"]))

    for st in ("empty", "not_found", "error"):
        check(f"{st} 는 검증 대상 아님", verify_shape(R("record", st, None), _SCHEMA["record"]))


# ── STEP 24 · fetch ──────────────────────────────────────────────────
class _Stub:
    def __init__(self, code, text):
        self.code, self.text = code, text

    def get(self, url, headers):
        return Response(self.code, self.text, "application/json", "utf-8")


class _Clock:
    def now(self):
        return AT


def test_fetch_status() -> None:
    c = _Clock()
    from contracts import Request

    req = Request("GET", "https://x", {}, 15.0)
    check("200 + 내용 → ok", fetch(req, _Stub(200, '{"Id":1}'), "list", c).status == "ok")
    check("200 + 빈 객체 → empty", fetch(req, _Stub(200, "{}"), "list", c).status == "empty")
    check("404 → not_found", fetch(req, _Stub(404, ""), "record", c).status == "not_found")
    check("500 → error", fetch(req, _Stub(500, ""), "detail", c).status == "error")
    check("JSON 아님 → error", fetch(req, _Stub(200, "<html>"), "list", c).status == "error")
    check("404 는 raw 를 담지 않는다", fetch(req, _Stub(404, ""), "record", c).raw is None)


def test_interpret_failure() -> None:
    check("전량 404 → 경로 오류",
          interpret_failure([404] * 5, 0, 0)[0] == "경로 오류")
    check("전량 403 → 헤더",
          interpret_failure([403] * 5, 0, 0)[0] == "헤더 · 인증")
    check("200인데 결과 0 → 쿼리 오류",
          interpret_failure([200] * 5, 5, 0)[0] == "수집 쿼리 오류")
    check("일부만 실패 → 개별 사유",
          interpret_failure([200, 200, 404], 2, 2)[0] == "개별 매물 사유")


# ── STEP 23 ──────────────────────────────────────────────────────────
def test_facet_axes() -> None:
    body = {
        "iNav": {
            "Nodes": [
                {"Name": "Price", "Type": "RangeAction"},
                {"Name": "Price", "Type": "Aspect", "Facets": []},
                {"Name": "Options", "Type": "Aspect", "Facets": []},
            ]
        }
    }
    ax = facet_axes(body)
    check("(Name, Type) 키 — RangeAction 이 Aspect 를 덮지 않는다",
          ("Price", "RangeAction") in ax and ("Price", "Aspect") in ax,
          f"{len(ax)}개")

    unspec = {"Nodes": [{"Name": n, "Type": "Aspect"} for n in
                        ("Options", "JatoOptions", "FuelType", "Color", "SeatColor",
                         "Condition", "SellType", "LeaseType")]}
    check("필수 축 집합 통과", check_facet_axes(unspec) == [])
    check("★ Badge 는 검사하지 않는다 — facet 이 주지 않는다 (실측)",
          check_facet_axes(unspec) == [])
    check("필수 축 하나 빠지면 위반",
          len(check_facet_axes({"Nodes": unspec["Nodes"][:-1]})) == 1)
    check("축 수가 아니라 집합으로 본다",
          check_facet_axes({"Nodes": unspec["Nodes"]
                            + [{"Name": "Zzz", "Type": "Aspect"}]}) == [])


def test_collect_groups() -> None:
    t = load_targets(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "config", "targets.json"))
    g = collect_groups(t, "encar")
    # ★ 개정 604 (명령서 2-2) — ★ 수입 여덟을 등록해 ★ 10 → 18종이 됐다.
    #   ★ 그런데 ★ 엔카 collect_group 은 ★ 8 그대로다 —
    #   ★ 새 여덟은 ★ `site_query` 가 비어 ★ 엔카 수집에 안 끼어들기 때문이다.
    #   ★ 이 줄이 ★ 그것을 지킨다 (엔카 `ModelGroup` 을 facet 으로 못 확인했다)
    check("target 18 → collect_group 8", len(t) == 18 and len(g) == 8,
          f"{len(t)}/{len(g)}")
    g80 = [x for x in g if x.group_key == "encar:G80"][0]
    check("G80 두 target 이 한 그룹", g80.target_keys == ("G80_25T", "G80_EV"))
    my = [x for x in g if x.group_key == "encar:MODEL_Y"][0]
    check("모델Y CarType=N (빠뜨리면 0건)", my.site_query["CarType"] == "N")


# ── STEP 17a q 문법 ──────────────────────────────────────────────────
def test_build_q() -> None:
    import json as _json

    from adapters.encar import EncarAdapter, escape_value, unescape_value
    from collect.runner import collect_groups as _cg

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg = _json.load(open(os.path.join(root, "config", "endpoints.json"),
                          encoding="utf-8"))["encar"]
    tg = load_targets(os.path.join(root, "config", "targets.json"))
    a = EncarAdapter(cfg)

    # v1 raw_facet 의 RemoveAction 실측값과 문자 단위로 일치해야 한다
    expect = ("(And.Hidden.N._.MultiViewHidden.N._.Year.range(202100..)"
              "._.Price.range(..6000)._.(C.CarType.Y._."
              "(C.Manufacturer.제네시스._.ModelGroup.G80.)))")
    g80 = [g for g in _cg(tg, "encar") if g.group_key == "encar:G80"][0]
    got = a.build_q(g80.site_query)
    check("G80 조립이 실측 원문과 일치", got == expect, got if got != expect else "")

    kg = [g for g in _cg(tg, "encar") if g.group_key == "encar:KOLEOS"][0]
    kol = a.build_q(kg.site_query)
    check("괄호 이스케이프 — 르노코리아(삼성_)", "르노코리아(삼성_)" in kol)
    check("이스케이프 왕복", unescape_value(escape_value("르노코리아(삼성)")) == "르노코리아(삼성)")

    check("같은 입력 → 같은 문자열 (조립 순서 고정)",
          a.build_q(g80.site_query) == got)

    from errors import PolicyError
    try:
        a.build_q({})
        check("빈 조건 → 중단", False)
    except PolicyError:
        check("빈 조건 → 중단", True)

    # ★ 지정한 조건이 조용히 사라지면 안 된다 (V1-10)
    base = g80.site_query
    deep = a.build_q(dict(base, Model="G80 (RG3)"))
    check("★ Model 을 넣으면 4단 계층이 나온다",
          "(C.ModelGroup.G80._.Model.G80 (RG3_).)" in deep, deep[-70:])
    check("괄호 균형", deep.count("(") == deep.count(")"))
    try:
        a.build_q(dict(base, Trim="2.5"))
        check("★ 조립 규칙 없는 키 → 중단 (조용히 무시하지 않는다)", False)
    except PolicyError as e:
        check("★ 조립 규칙 없는 키 → 중단 (조용히 무시하지 않는다)",
              "Trim" in str(e))


# ── STEP 27 ──────────────────────────────────────────────────────────
def test_collect_check() -> None:
    ok = collect_check(100, 100, {"ok": 90, "empty": 5, "not_found": 3, "error": 2}, 100, 0)
    check("정상 → 위반 없음", ok == [])
    v1 = collect_check(208, 76, {"ok": 76}, 76, 0)
    check("v1 사고 (208 중 76) → ⑥ 검출", any(x.startswith("⑥") for x in v1))
    # *_status 를 독립으로 세면 ① 이 일한다.  「전부 던졌다」는 보고와 어긋난다
    v1b = collect_check(208, 76, {"ok": 76}, 76, 0, not_requested=0)
    check("보고와 상태가 어긋나면 → ① 검출", any(x.startswith("①") for x in v1b))
    rj = collect_check(10, 10, {"ok": 10}, 10, 1)
    check("거부 1건 → ③ 검출", any(x.startswith("③") for x in rj))
    z = collect_check(10, 10, {"ok": 0, "error": 10}, 10, 0)
    check("ok 0건 → ④ 검출", any(x.startswith("④") for x in z))


# ── STEP 33 적재 ─────────────────────────────────────────────────────
def test_save_raw() -> None:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with tempfile.TemporaryDirectory() as d:
        conn = open_db(os.path.join(d, "t.db"), os.path.join(root, "sql", "ddl"))
        hdr = {"User-Agent": "ua", "Cookie": "secret", "Authorization": "token"}

        r = save_raw(conn, R("record", "ok", {"carNo": "1", "openData": True}),
                     _SCHEMA["record"], "encar", "encar_1", "https://x", hdr, verify=verify_shape, reason=reject_reason)
        check("정상 → stored", r == "stored")

        r = save_raw(conn, R("record", "ok", {"master": {}, "outers": []}),
                     _SCHEMA["record"], "encar", "encar_2", "https://x", hdr, verify=verify_shape, reason=reject_reason)
        check("라벨 오배정 → rejected", r == "rejected")

        meta = conn.execute("SELECT request_meta FROM raw_response").fetchone()[0]
        check("민감 헤더 미저장 (화이트리스트)",
              "ua" in meta and "secret" not in meta and "token" not in meta)

        why = conn.execute("SELECT reject_reason FROM raw_response_reject").fetchone()[0]
        check("거부 사유에 누락 키 기록", "carNo" in why and "openData" in why, why)

        n = conn.execute("SELECT COUNT(*) FROM raw_response").fetchone()[0]
        save_raw(conn, R("record", "error", None), _SCHEMA["record"],
                 "encar", "encar_3", "https://x", hdr, verify=verify_shape, reason=reject_reason)
        n2 = conn.execute("SELECT COUNT(*) FROM raw_response").fetchone()[0]
        check("실패 응답도 저장한다 (STEP 53-⑤)", n2 == n + 1)


# ── STEP 52 연속 실패 즉시 중단 ──────────────────────────────────────
def test_fail_streak() -> None:
    from collect.runner import FailStreak

    class R:
        def __init__(self, status, code=None):
            self.status, self.http_code = status, code

    s = FailStreak(3)
    for _ in range(3):
        s.observe(R("error", 403))
    check("★ 같은 코드 3회 연속 → 중단", s.tripped, str(s.count))
    check("사유에 코드와 횟수가 남는다",
          "403" in s.reason() and "3회" in s.reason(), s.reason())

    s = FailStreak(3)
    for code in (403, 429, 500):
        s.observe(R("error", code))
    check("★ 코드가 섞이면 안 센다 (차단 판정이 아니다)", not s.tripped,
          str(s.count))

    s = FailStreak(3)
    for _ in range(3):
        s.observe(R("not_found", 404))
    check("★ 404 연속은 중단이다 — 다만 결과일 수 있어 코드가 남는다",
          s.tripped and "404" in s.reason())

    s = FailStreak(3)
    s.observe(R("error", 403))
    s.observe(R("error", 403))
    s.observe(R("ok", 200))
    s.observe(R("error", 403))
    check("★ ok 하나면 카운터가 0 으로 돌아간다", not s.tripped, str(s.count))

    s = FailStreak(3)
    s.observe(R("empty", 200))
    check("empty 는 실패가 아니다", s.count == 0)

    check("limit 0 이면 감시하지 않는다",
          not FailStreak(0).tripped)


# ── V1-08 최소 표본 (실측 사고) ─────────────────────────────────────
def test_all_fail_sample() -> None:
    """★ 1건이 404 면 100% 가 된다.  그것은 「전량」이 아니다."""
    import os
    import tempfile as _tf

    from store.raw import open_db
    from validate.base import run_phase
    from validate.v1_collect import ALL_FAIL_MIN_SAMPLE

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    conn = open_db(os.path.join(_tf.mkdtemp(), "v108.db"),
                   os.path.join(root, "sql", "ddl"))

    def put(kind, n, status):
        for i in range(n):
            conn.execute(
                "INSERT INTO audit_request(run_id,site,kind,source_id,url,"
                "http_code,status,attempt,requested_at) "
                "VALUES ('r','encar',?,?,'u',404,?,1,'t')",
                (kind, f"{kind}{i}", status))
        conn.commit()

    class _V:
        run_id = "r"
        policy_raw: dict = {}
        depreciation: dict = {}
        target_keys: tuple = ()
        started_at = None

    put("record", 1, "not_found")            # 표본 1건
    got = {r.check.code: r for r in run_phase(conn, _V(), "V1")}
    check("★ 표본 1건은 「전량 404」가 아니다",
          got["V1-08b"].passed and got["V1-08"].passed,
          str(got["V1-08b"].samples))

    put("diagnosis", ALL_FAIL_MIN_SAMPLE, "not_found")
    got = {r.check.code: r for r in run_phase(conn, _V(), "V1")}
    check(f"★ {ALL_FAIL_MIN_SAMPLE}건 전량 404 는 잡는다",
          not got["V1-08b"].passed
          and any("diagnosis" in s for s in got["V1-08b"].samples),
          str(got["V1-08b"].samples))


# ── STEP 21b 진단 호출 범위 ─────────────────────────────────────────
def test_diagnosis_scope() -> None:
    """★ encarDiagnosis == 0 인 매물만 부른다.  1·2 는 404 다."""
    from collect.runner import DIAG_HAS_REPORT, LISTING_ENDPOINTS

    check("진단이 엔드포인트에 있다", "diagnosis" in LISTING_ENDPOINTS)
    check("★ 호출 조건은 0 이다", DIAG_HAS_REPORT == 0)

    def called(grade):
        return grade == DIAG_HAS_REPORT

    check("0 → 호출", called(0))
    for g in (-1, 1, 2, None):
        check(f"★ {g} → 건너뜀 (404 가 정답)", not called(g))


if __name__ == "__main__":
    print("2장 수집 시험")
    test_verify_shape()
    test_fetch_status()
    test_interpret_failure()
    test_facet_axes()
    test_collect_groups()
    test_build_q()
    test_collect_check()
    test_save_raw()
    test_fail_streak()
    test_all_fail_sample()
    test_diagnosis_scope()
    print()
    print("결과:", "통과" if not FAIL else "실패 — " + " / ".join(FAIL))
    sys.exit(1 if FAIL else 0)
