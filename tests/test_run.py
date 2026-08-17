# -*- coding: utf-8 -*-
"""S0~S3 종단 시험 (모의 응답).

지시서   STEP 18a (봉투) · STEP 23 (facet 2요청 · 필수 축) · STEP 53 (자동 점검)
근거     api.encar.com 에 접속할 수 없는 환경에서도 조립 · 저장 · 검증 경로를
         끝까지 확인한다.  실제 응답 확인은 마스터 PC 에서 한다.
사용     python3 tests/test_run.py
"""
from __future__ import annotations

import json
import os
import random
import sys
import tempfile
from datetime import datetime, timezone
from urllib.parse import unquote

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adapters.encar import EncarAdapter  # noqa: E402
from collect.pipeline import run_pipeline  # noqa: E402
from collect.runner import (  # noqa: E402
    collect_groups, load_targets, make_executors, make_score_executors,
    make_registry_executor, make_validate_executor,
)
from contracts import Response, RunContext  # noqa: E402
from store.raw import open_db  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAIL: list[str] = []
AXES = ("Options", "JatoOptions", "FuelType", "Color", "SeatColor",
        "Condition", "SellType", "LeaseType")


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{'  ' + detail if detail else ''}")
    if not ok:
        FAIL.append(name)


DETAIL = {
    "category": {"originPrice": 7000, "gradeName": "2.5T AWD",
                 "jatoVehicleId": 843925,
                 "warranty": {"bodyMonth": 60, "bodyMileage": 100000,
                              "transmissionMonth": 60,
                              "transmissionMileage": 100000}},
    "spec": {"displacement": 2497, "mileage": 30000, "colorName": "블랙",
             "fuelName": "가솔린", "tradeType": "매매"},
    "options": {"standard": ["010", "095"], "choice": [], "etc": None},
    "condition": {"seizing": {"seizingCount": 0, "pledgeCount": 0},
                  "accident": {"recordView": True, "resumeView": False},
                  # ★ TABLE 엔카직영 · IMAGE 판매자가 사진으로 올린 것 (개정 300)
                  "inspection": {"formats": ["TABLE"]}},
    "advertisement": {"price": 5000, "diagnosisCar": True,
                      "encarPassType": "PASS",
                      "encarPassCategoryType": "CLEAR"},
    "view": {"encarDiagnosis": "P1"},
    "manage": {"registDateTime": "2026-03-05T11:22:33", "viewCount": 10,
               "subscribeCount": 2, "dummy": False},
    "partnership": {"dealer": {"name": "홍길동",
                               "firm": {"name": "OO모터스", "code": "F1"}}},
    "contact": {"no": "010-0000-0000", "address": "서울"},
    "contents": {"text": "틴팅 시공"},
    "vin": "KMH123", "vehicleNo": "12가3456",
}

INSPECTION = {
    "master": {"accdient": "N", "simpleRepair": "N",
               "detail": {"vin": "KMH123", "mileage": 30000,
                          "firstRegistrationDate": "2023-05-02T00:00:00",
                          "waterlog": "N", "motorType": "G"}},
    "outers": [{"type": {"code": "P022", "title": "프론트 휀더(우)"},
                "statusTypes": [{"code": "X", "title": "교환(교체)"}],
                "attributes": ["RANK_ONE"]}],
    "inners": [], "etcs": [], "images": [],
}

RECORD = {
    "carNo": "12가3456", "openData": True, "firstDate": "2023-05-02",
    "myAccidentCnt": 1, "myAccidentCost": 1500000,
    "otherAccidentCnt": 0, "otherAccidentCost": 0, "accidentCnt": 1,
    "accidents": [{"type": "2", "date": "2026-02-03",
                   "insuranceBenefit": 19440000}],
    "ownerChangeCnt": 1, "carNoChangeCnt": 0,
    # ★ 보험이력 용도 변경이력 — 렌트를 세 곳에서 대조한다 (개정 302)
    "use": "2", "carInfoUse1s": ["2"], "carInfoUse2s": ["1"],
    "fuel": "하이브리드", "maker": "삼성",
}


class StubEncar:
    """페이지네이션 · facet 2요청 · 매물 4종을 흉내낸다."""

    def __init__(self, total: int = 45, drop_badge: bool = False,
                 id_base: int = 0):
        self.total = total
        self.drop_badge = drop_badge
        # ★ 씨앗 DB 는 ID 대역을 옮긴다 — 0·1·2 는 다른 시험이 쓰는
        #   탐색 URL(/readside/vehicle/1)과 겹친다 (실측 08-16)
        self.id_base = id_base
        self.list_calls = 0
        self.facet_calls = 0
        self.detail_calls = 0
        self.catalog_ids: list[str] = []

    def get(self, url: str, headers):
        u = unquote(url)
        # ★ 개정 296·297 로 늘어난 6종 (docs/ENCAR_API.md).
        #   시험이 실물과 다르면 시험이 아니다 — 실측한 모양 그대로 준다.
        #   ★ 긴 경로를 먼저 본다 — /record/…/summary 가 /record/ 에 먼저 걸린다
        for path, doc in (
            ("/summary", None),
            ("/clean-encar/", {"vehicleId": 1, "cleaned": True}),
            ("/sellingpoint", {"vehicleId": 1, "sellingPoint": None}),
            ("/ev-battery/", {"ensolRawInfo": None, "jatoBatteryInfo": None,
                              "encarComputedInfo": None}),
        ):
            if path not in u:
                continue
            if path == "/summary":
                doc = ({"vehicleId": 1, "outers": [], "outerSummarys": [],
                        "inspName": "시험 점검원"}
                       if "/inspection/" in u
                       else {"carNo": "12가3456", "use": "1", "year": "2023",
                             "fuel": "가솔린", "ownerChangeCnt": 0,
                             "totalLossCnt": 0, "floodTotalLossCnt": 0,
                             "robberCnt": 0, "loan": 0, "business": 0,
                             "government": 0, "accidentCnt": 0})
            self.detail_calls += 1
            return Response(200, json.dumps(doc, ensure_ascii=False),
                            "application/json", "utf-8")
        # 진단은 「받지 않은 차」가 정상이다.  200 + 빈 응답 → empty (STEP 21b)
        for path, doc in (("/inspection/", INSPECTION), ("/record/", RECORD),
                          ("/diagnosis/", {})):
            if path not in u:
                continue
            self.detail_calls += 1
            # ★ 렌트 근거 셋을 다 나오게 섞는다 (개정 302).
            #   전건이 자가용이면 「보험이력으로도 잡는가」를 시험할 수 없다
            if path == "/record/":
                import copy as _c

                doc = _c.deepcopy(doc)
                vid = u.rstrip("/open").rsplit("/", 1)[-1]
                if vid.isdigit() and int(vid) % 4 == 0:
                    doc["carInfoUse1s"] = ["3", "2"]     # 영업용 → 자가용
            elif path == "/inspection/":
                import copy as _c

                doc = _c.deepcopy(doc)
                vid = u.rsplit("/", 1)[-1].split("?")[0]
                if vid.isdigit() and int(vid) % 6 == 0:
                    doc["master"]["detail"]["usageChangeTypes"] = [
                        {"code": "1", "title": "렌트"}]
            return Response(200, json.dumps(doc, ensure_ascii=False),
                            "application/json", "utf-8")
        if "/options/choice" in u:
            # ★ 매물 ID 로 온다 — jatoVehicleId 가 아니다 (실측)
            self.catalog_ids.append(u.split("/car/")[1].split("/")[0])
            self.detail_calls += 1
            return Response(200, json.dumps(
                [{"optionCd": "1044", "optionName": "드라이빙 어시스턴스 패키지 II",
                  "price": 200,
                  "description": "고속도로 주행 보조 2(차로 변경 보조 제어 기능 포함)"}],
                ensure_ascii=False), "application/json", "utf-8")
        if "/readside/vehicle/" in u:
            self.detail_calls += 1
            # ★ 전건이 같은 값이면 「모른다」와 「없다」가 구분되지 않는다.
            #   실물처럼 섞는다 — 일부는 저당 정보 자체가 없다 (V2-25)
            import copy

            doc = copy.deepcopy(DETAIL)
            vid = u.split("/vehicle/")[1].split("?")[0]
            # ★ 점검 출처와 광고 형태를 섞는다 — 실물이 섞여 있다 (개정 300·302).
            #   전건이 같으면 「가르는가」를 시험할 수 없다
            n = int(vid) if vid.isdigit() else 0
            if n % 5 == 0:
                doc["condition"]["inspection"] = {"formats": ["IMAGE"]}
            elif n % 5 == 1:
                doc["condition"]["inspection"] = {"formats": []}
            if n % 7 == 0:
                doc["advertisement"]["advertisementType"] = "RENT_SUCCESSION"
            elif n % 7 == 1:
                doc["advertisement"]["advertisementType"] = "OPERATING_LEASE"
            if vid.isdigit() and int(vid) % 3 == 0:
                doc["condition"].pop("seizing", None)      # 모른다
            elif vid.isdigit() and int(vid) % 3 == 1:
                doc["condition"]["seizing"] = {"seizingCount": 1,
                                               "pledgeCount": 0}
            self.detail_calls += 1
            return Response(200, json.dumps(doc, ensure_ascii=False),
                            "application/json", "utf-8")
        if "inav=" in u:
            self.facet_calls += 1
            # ★ facet 은 계층의 다음 단계만 준다.  Badge 는 오지 않는다 (실측)
            names = [{"Name": n, "Type": "Aspect",
                      "Facets": [{"Value": f"{n}_v", "Count": 0}]}
                     for n in AXES]
            names.append({"Name": "Price", "Type": "RangeAction"})
            names.append({"Name": "Model", "Type": "Aspect",
                          "Facets": [{"Value": "G80 (RG3)", "Count": 3}]})
            if self.drop_badge:      # 필수 축 하나를 뺀 경우
                names = names[1:]
            body = {"Count": self.total, "SearchResults": [],
                    "iNav": {"Nodes": names}}
            return Response(200, json.dumps(body, ensure_ascii=False),
                            "application/json", "utf-8")

        self.list_calls += 1
        offset = int(u.split("|MobileModifiedDate|")[1].split("|")[0])
        limit = int(u.split("|MobileModifiedDate|")[1].split("|")[1].split("&")[0])
        # ★ 전건이 같은 값이면 분포가 없다 — 히스토그램·등급 분포가
        #   한 칸에 몰려 「화면이 도는지」를 못 본다 (S24 씨앗 · 개정 246)
        items = [{
            "Id": str(self.id_base + offset + i),
            "ModelGroup": "G80", "Model": "G80 (RG3)",
            "Manufacturer": "제네시스", "Badge": "2.5 터보", "FuelType": "가솔린",
            # ★ 0번은 원래 값을 지킨다 — 환산·형식 시험이 그 행을 본다
            "Year": 202305.0 if offset + i == 0 else 202301.0 + (offset + i) % 3,
            "FormYear": 2023,
            "Mileage": 30000 if offset + i == 0
                       else 20000 + ((offset + i) % 6) * 9000,
            "Price": 5000.0 if offset + i == 0
                     else 4200.0 + ((offset + i) % 6) * 260,
            "Color": "블랙", "ColorExpression": "#000;#000",
            "SeatColor": "블랙", "Transmission": "오토", "SellType": "일반",
            "SalesStatus": "ADVERTISE", "ServiceCopyCar": "ORIGINAL",
            "OfficeCityState": "서울특별시", "Photos": [], "Trust": [],
        } for i in range(min(limit, max(0, self.total - offset)))]
        body = {"Count": self.total, "SearchResults": items}
        return Response(200, json.dumps(body, ensure_ascii=False),
                        "application/json", "utf-8")


class Clock:
    def now(self):
        return datetime(2026, 8, 10, tzinfo=timezone.utc)


def setup(total=45, drop_badge=False, one_group=True, root=None):
    cfg = json.load(open(os.path.join(ROOT, "config", "endpoints.json"),
                         encoding="utf-8"))["encar"]
    cfg = dict(cfg)
    cfg["interval_sec"] = [0.0, 0.0]  # 시험에서는 대기하지 않는다
    targets = load_targets(os.path.join(ROOT, "config", "targets.json"))
    if one_group:
        targets = {k: v for k, v in targets.items()
                   if v["collect_group"] == "encar:G80"}
    adapter = EncarAdapter(cfg)
    stub = StubEncar(total, drop_badge)
    conn = open_db(os.path.join(tempfile.mkdtemp(), "t.db"),
                   os.path.join(ROOT, "sql", "ddl"))
    ctx = RunContext("r1", "encar", Clock().now(), "p1", "d1", "c1",
                     "h", "h", "h", [])
    ex = make_executors(adapter, stub, Clock(), cfg, targets,
                        rng=random.Random(1), root_dir=root or ROOT)
    # ★ 사본 root 를 주면 그 config 를 읽는다.
    #   ROOT 로 고정하면 「config 를 고치면 판정이 바뀌는가」를 못 본다
    base = root or ROOT
    ex.update(make_score_executors(
        base, Clock(), targets,
        json.load(open(os.path.join(base, "config", "scoring.json"),
                       encoding="utf-8")),
        json.load(open(os.path.join(base, "config", "depreciation.json"),
                       encoding="utf-8"))))
    ex.update(make_registry_executor(
        base, Clock(),
        json.load(open(os.path.join(base, "config", "field_usage.json"),
                       encoding="utf-8"))))
    ex.update(make_validate_executor(
        json.load(open(os.path.join(base, "config", "scoring.json"),
                       encoding="utf-8")),
        json.load(open(os.path.join(base, "config", "depreciation.json"),
                       encoding="utf-8"))))
    return conn, ctx, ex, stub, cfg, targets


def test_envelope() -> None:
    conn, ctx, ex, stub, cfg, _ = setup(total=45)
    reps = run_pipeline(conn, ctx, ex, steps=("S0", "S1"))
    s1 = reps[-1]
    check("S1 정상 종료", not s1.halted, s1.halt_reason or "")

    # page_size 20 · Count 45 → 3페이지
    check("Count 로 페이지 수를 확정한다", stub.list_calls == 3,
          f"{stub.list_calls}회")

    rows = conn.execute(
        "SELECT COUNT(*) FROM raw_response WHERE endpoint='list'").fetchone()[0]
    check("★ 봉투 1건 = 1행.  매물 수가 아니다 (STEP 18a)", rows == 3,
          f"{rows}행 / 매물 45건")

    bodies = [json.loads(r[0]) for r in conn.execute(
        "SELECT body FROM raw_response WHERE endpoint='list'")]
    check("Count 가 원문에 남는다", all(b["Count"] == 45 for b in bodies))
    check("Σ len(SearchResults) == Count",
          sum(len(b["SearchResults"]) for b in bodies) == 45)
    check("expected == requested", s1.expected == s1.requested,
          f"{s1.expected}/{s1.requested}")

    n = conn.execute(
        "SELECT COUNT(*) FROM audit_request WHERE kind='list'").fetchone()[0]
    check("요청 로그가 남는다", n == 3, f"{n}행")


def test_last_page_exact() -> None:
    conn, ctx, ex, stub, _, _ = setup(total=40)
    run_pipeline(conn, ctx, ex, steps=("S0", "S1"))
    check("Count 가 페이지 크기의 배수여도 안 도는다 (빈 응답까지 안 감)",
          stub.list_calls == 2, f"{stub.list_calls}회")


def test_facet() -> None:
    conn, ctx, ex, stub, _, _ = setup()
    reps = run_pipeline(conn, ctx, ex, steps=("S0", "S1", "S2"))
    s2 = reps[-1]
    check("S2 정상 종료", not s2.halted, s2.halt_reason or "")
    check("★ collect_group 당 1요청 (Badge 요청 폐지)",
          stub.facet_calls == 1, f"{stub.facet_calls}회")
    rows = conn.execute(
        "SELECT request_kind, axis_count FROM raw_facet").fetchall()
    check("미지정 1행", len(rows) == 1 and rows[0][0] == "unspecified",
          str(rows))
    check("expected = group × 1", s2.expected == 1, str(s2.expected))


def test_facet_missing_axis() -> None:
    conn, ctx, ex, _, _, _ = setup(drop_badge=True)
    reps = run_pipeline(conn, ctx, ex, steps=("S0", "S1", "S2"))
    s2 = reps[-1]
    check("★ 필수 축 누락 → S2 중단 (fatal)",
          s2.halted and "필수 축" in (s2.halt_reason or ""), s2.halt_reason or "")
    check("중단되면 S3 을 실행하지 않는다", len(reps) == 3)


def test_dict_step() -> None:
    conn, ctx, ex, _, _, _ = setup()
    reps = run_pipeline(conn, ctx, ex, steps=("S0", "S1", "S2", "S3"))
    check("S0~S3 전부 정상", not any(r.halted for r in reps),
          " / ".join(f"{r.step}:{r.halt_reason}" for r in reps if r.halted))

    n = conn.execute(
        "SELECT COUNT(*) FROM dict_enum WHERE axis='fuel'").fetchone()[0]
    check("facet 값이 사전에 들어간다 (Count=0 포함)", n == 1, f"{n}종")
    st = conn.execute(
        "SELECT status FROM dict_enum WHERE axis='fuel'").fetchone()
    check("facet 선언 열거값은 confirmed", st == ("confirmed",), str(st))
    tr = conn.execute(
        "SELECT value FROM dict_enum WHERE axis='trim'").fetchone()
    check("★ trim 사전은 목록 응답의 Badge 필드에서 나온다",
          tr == ("2.5 터보",), str(tr))

    v = conn.execute(
        "SELECT COUNT(*) FROM audit_validation WHERE run_id='r1'").fetchone()[0]
    check("단계별 StepReport 가 테이블에 남는다", v == 4, f"{v}행")


def test_all_groups() -> None:
    conn, ctx, ex, stub, _, targets = setup(total=5, one_group=False)
    reps = run_pipeline(conn, ctx, ex, steps=("S0", "S1", "S2"))
    g = len(collect_groups(targets, "encar"))
    check("8 collect_group 전부 순회", stub.list_calls == g, f"{stub.list_calls}회")
    check("facet 은 group × 1", stub.facet_calls == g, f"{stub.facet_calls}회")
    check("S1·S2 정상", not any(r.halted for r in reps),
          " / ".join(r.halt_reason or "" for r in reps if r.halted))


# ── S4~S6 파싱 ───────────────────────────────────────────────────────
def test_parse_pipeline() -> None:
    conn, ctx, ex, stub, _, _ = setup(total=3)
    reps = run_pipeline(conn, ctx, ex,
                        steps=("S0", "S1", "S2", "S3", "S4", "S5", "S6"))
    check("S0~S6 전부 정상", not any(r.halted for r in reps),
          " / ".join(f"{r.step}:{r.halt_reason}" for r in reps if r.halted))

    n = conn.execute("SELECT COUNT(*) FROM core_listing").fetchone()[0]
    check("봉투 1행 → 매물 3행 (펼치는 것은 파싱)", n == 3, f"{n}행")

    row = conn.execute(
        "SELECT price_current_won, price_origin_won, year_month, "
        "displacement_cc, dealer_region, dealer_shop, options_choice_json, "
        "classify_stage, target_key, vehicle_id "
        "FROM core_listing LIMIT 1").fetchone()
    (cur, org, ym, cc, region, shop, choice, stage, tk, vk) = row
    check("만원 → 원 환산", cur == 50000000 and org == 70000000, f"{cur}/{org}")
    check("Year 202305.0 → 2023-05", ym == "2023-05", str(ym))
    check("배기량이 상세에서 온다", cc == 2497)
    check("★ OfficeCityState 는 dealer_region", region == "서울특별시", str(region))
    check("★ 상사명은 partnership.dealer.firm.name", shop == "OO모터스", str(shop))
    check("빈 choice 가 '[]' 로 남는다 (NULL 아님)", choice == "[]", str(choice))
    check("2단 분류 confirmed", stage == "confirmed" and tk == "G80_25T",
          f"{stage}/{tk}")
    check("★ vehicle_id 는 대리키 (의미 없는 내부 번호)", isinstance(vk, int), str(vk))
    ident = conn.execute(
        "SELECT kind, value_hash FROM vehicle_identity WHERE vehicle_id=?",
        (vk,)).fetchone()
    check("★ 결합 근거는 vehicle_identity 행이다",
          ident[0] == "plate" and len(ident[1]) == 16, str(ident))
    pii = conn.execute("SELECT plate_no FROM core_pii").fetchone()
    check("★ 원본 번호판은 core_pii 에만 있다", pii == ("12가3456",), str(pii))
    cols = [r[1] for r in conn.execute("PRAGMA table_info(core_listing)")]
    check("★ 마스킹 컬럼을 두지 않는다 (V2-10b)",
          not any(c.endswith("_masked") for c in cols))
    check("확보 여부는 hash IS NOT NULL 로 낸다",
          conn.execute("SELECT COUNT(*) FROM core_listing "
                       "WHERE plate_hash IS NOT NULL").fetchone()[0] == 3)
    rec = conn.execute(
        "SELECT record_plate_hash, plate_use_char FROM core_record LIMIT 1"
    ).fetchone()
    check("★ record 번호판도 해시 + 용도 문자로 분리", rec[0] is not None, str(rec))
    rp = conn.execute("SELECT record_plate_no FROM core_pii LIMIT 1").fetchone()
    check("record 원본은 core_pii 에", rp == ("12가3456",), str(rp))
    dp = conn.execute(
        "SELECT dealer_name, phone FROM core_dealer_pii").fetchone()
    check("★ 실명·연락처는 core_dealer_pii 로 (딜러 단위)",
          dp == ("홍길동", "010-0000-0000"), str(dp))
    shop = conn.execute(
        "SELECT dealer_shop FROM core_listing LIMIT 1").fetchone()
    check("★ core_listing 에는 상호만", shop == ("OO모터스",), str(shop))

    ins = conn.execute(
        "SELECT inspection_panel_json, first_registration_date, "
        "inspection_accident_flag FROM core_inspection LIMIT 1").fetchone()
    panels = json.loads(ins[0])
    check("★ outers 를 원문 배열 그대로 저장",
          panels[0]["attributes"] == ["RANK_ONE"]
          and panels[0]["type"]["code"] == "P022", str(panels)[:60])
    check("firstRegistrationDate → date10", ins[1] == "2023-05-02", str(ins[1]))
    check("원문 철자 accdient 를 그대로 읽는다", ins[2] == "N", str(ins[2]))

    rec = conn.execute(
        "SELECT accidents_json, accident_my_cost, record_fuel, not_join_json "
        "FROM core_record LIMIT 1").fetchone()
    acc = json.loads(rec[0])
    check("★ accidents 를 합산·필터 없이 그대로 저장",
          len(acc) == 1 and acc[0]["type"] == "2", str(acc)[:50])
    check("myAccidentCost 그대로", rec[1] == 1500000)
    check("record.fuel 은 저장하되 분류에 안 쓴다", rec[2] == "하이브리드")
    check("notJoinDate1~5 를 배열로", json.loads(rec[3]) == [None] * 5)

    v = conn.execute(
        "SELECT site_count, listing_count, price_spread_won "
        "FROM core_vehicle LIMIT 1").fetchone()
    check("core_vehicle — 1차엔 site_count 1 이어도 만든다", v[0] == 1, str(v))
    d = conn.execute(
        "SELECT listing_count, sample_sufficient FROM core_dealer").fetchone()
    check("딜러는 독립 개체 · 표본 충분 판정은 7장", d[1] == 0, str(d))
    h = conn.execute("SELECT COUNT(*) FROM core_dealer_history").fetchone()[0]
    check("딜러 이력 스냅샷이 남는다", h == 1, f"{h}행")

    s5 = [r for r in reps if r.step == "S5"][0]
    # ★ 08-14 확정 — 진단은 encarDiagnosis == 0 인 매물만 부른다 (STEP 21b).
    #   안 부른 것은 expected 에서 뺀다.  「미완성」이 아니다
    # ★ 요청 종류가 4 → 9종으로 늘었다 (개정 296·297 · docs/ENCAR_API.md).
    #   진단만 조건부라 매물 3건 × (9 − 1) + 진단 대상 = 실측값을 그대로 쓴다
    check("★ 진단을 뺀 만큼 expected 가 줄어든다",
          s5.expected == 24, str(s5.expected))
    check("★ 안 부른 것은 empty 가 아니다 — 요청 자체를 안 했다",
          s5.empty == 0, str(s5.empty))
    st = conn.execute(
        "SELECT diagnosis_status FROM core_listing LIMIT 1").fetchone()
    check("★ 안 부른 매물은 진단 상태가 비어 있다", st == (None,), str(st))
    # ★ 표시용 표다.  교환 판정은 outers 가 한다 (STEP 21b)
    check("core_diagnosis 가 있다",
          bool(conn.execute("SELECT name FROM sqlite_master "
                            "WHERE name='core_diagnosis'").fetchone()))
    check("★ 진단이 없으면 행도 없다 (빈 행을 만들지 않는다)",
          conn.execute("SELECT COUNT(*) FROM core_diagnosis").fetchone()[0]
          == 0)


# ── S9 · S10 ─────────────────────────────────────────────────────────
def test_score_pipeline() -> None:
    conn, ctx, ex, _, _, _ = setup(total=3)
    reps = run_pipeline(conn, ctx, ex,
                        steps=("S0", "S1", "S2", "S3", "S4", "S5", "S6", "S6a",
                               "S7", "S8", "S8.5", "S9", "S10"))
    reg = [r for r in reps if r.step == "S6a"][0]
    check("S6a 등록부 동기화", not reg.halted, reg.halt_reason or "")
    check("S0~S10 전부 정상", not any(r.halted for r in reps),
          " / ".join(f"{r.step}:{r.halt_reason}" for r in reps if r.halted))

    n = conn.execute("SELECT COUNT(*) FROM result_axis").fetchone()[0]
    from analyze.axes import COMPONENTS
    check("result_axis 는 Component 단위", n == 3 * len(COMPONENTS), f"{n}행")
    bad = conn.execute(
        "SELECT COUNT(*) FROM result_axis WHERE source IS NULL OR prio IS NULL"
    ).fetchone()[0]
    check("source · prio 전건 NOT NULL (V3-01·02)", bad == 0)

    rows = conn.execute(
        "SELECT grade, score_total, denominator, absolute_fail "
        "FROM result_score").fetchall()
    check("매물마다 점수 1행", len(rows) == 3, f"{len(rows)}행")
    g, total, denom, fail = rows[0]
    # ★ 개정 298 — 분모는 늘 만점이다.  못 본 축은 분모가 아니라 점수에서 빠진다.
    #   ★ 숫자를 박지 않는다 — 개정 306 으로 555 → 605 가 됐다
    from analyze.axes import ScoringPolicy

    full = float(ScoringPolicy(json.load(open(
        os.path.join(ROOT, "config", "scoring.json"),
        encoding="utf-8"))).raw["total_points"])
    check(f"분모는 늘 {full:g} 다 (개정 298 G)", denom == full, str(denom))
    check("등급이 매겨진다", g in ("S", "A", "B", "C", "D", "E", "NOT_RATED"),
          f"{g} {total}/{denom}")

    ex_axes = {a for (a,) in conn.execute(
        "SELECT DISTINCT axis FROM result_axis WHERE excluded=1")}
    check("★ 감가 곡선이 들어와 감가 축이 살아났다",
          "value.depreciation" not in ex_axes, str(sorted(ex_axes)))
    check("★ 색상 등급이 확정돼 취향 색상 축이 살아났다",
          "taste.color" not in ex_axes, str(sorted(ex_axes)))
    # ★ 씨앗은 3건뿐이라 시세 표본(5건)이 안 찬다 — 그것이 정답이다.
    #   이론가로 메우지 않는다 (개정 292 ①)
    check("★ 표본이 모자란 시세 축은 excluded — 이론가로 안 메운다",
          "value.market" in ex_axes, str(sorted(ex_axes)))
    # ★ 개정 298 — 분모는 늘 555 다.  개정 287 — 핵심 축을 못 보면 NOT_RATED.
    #   E(절대조건)는 점수와 무관하므로 빼고 본다
    rated = [r for r in rows if r[0] != "E"]
    check(f"★ 전건 분모가 {full:g} 다 (개정 298 G)",
          all(r[2] == full for r in rows), str({r[2] for r in rows}))
    check("★ 핵심 축(시세)을 못 봐 NOT_RATED 다 — 씨앗은 3건이라 표본이 안 찬다",
          all(r[0] == "NOT_RATED" for r in rated) if rated else True,
          str([r[0] for r in rows]))


# ── S11 검증 5차 (6장) ───────────────────────────────────────────────
def test_validate() -> None:
    conn, ctx, ex, _, _, _ = setup(total=3)
    reps = run_pipeline(conn, ctx, ex,
                        steps=("S0", "S1", "S2", "S3", "S4", "S5", "S6", "S6a",
                               "S7", "S8", "S8.5", "S9", "S10", "S11"))
    s11 = [r for r in reps if r.step == "S11"]
    check("S11 이 실행된다", bool(s11))
    rows = conn.execute(
        "SELECT phase, code, passed, severity FROM audit_validation "
        "WHERE phase LIKE 'V%'").fetchall()
    phases = {r[0] for r in rows}
    # ★ 차수를 손으로 적지 않는다.  validate/ 를 훑어 선언된 것과 맞춘다.
    #   손 목록이면 차수가 늘 때마다 시험이 먼저 막힌다 (V8 을 더하며 겪었다)
    declared = set()
    import glob as _glob
    import importlib as _il
    import os as _os

    for _m in sorted(_glob.glob(_os.path.join(ROOT, "validate", "v*_*.py"))):
        mod = _il.import_module(f"validate.{_os.path.basename(_m)[:-3]}")
        declared |= {c.phase for c in getattr(mod, "C", {}).values()}
    check("선언된 전 차수가 돈다", phases == declared,
          f"돈 것 {sorted(phases)} · 선언 {sorted(declared)}")
    check("검증 결과가 테이블에 남는다 (화면 출력만 하지 않는다)",
          len(rows) >= 40, f"{len(rows)}행")

    failed = [(r[1], r[3]) for r in rows if not r[2]]
    fatal = [c for c, sev in failed if sev == "fatal"]
    check("fatal 실패는 중단으로 이어진다",
          bool(fatal) == bool(s11[0].halted),
          f"fatal={fatal} halted={s11[0].halted}")

    codes = {r[1] for r in rows}
    for want in ("V1-04", "V2-06", "V3-01", "V3-11", "V4-12", "V5-03"):
        check(f"{want} 가 실행됐다", want in codes)

    v503 = [r for r in rows if r[1] == "V5-03"][0]
    check("★ 분모 시험 6종 통과 (V5-03)", v503[2] == 1)
    v311 = [r for r in rows if r[1] == "V3-11"][0]
    check("★ put() 셔플 100회 동일 (V3-11)", v311[2] == 1)


# ── 8장 등록부 · 중단 리포트 ─────────────────────────────────────────
def test_registry_gate() -> None:
    from tools.sync_registry import halt_report, list_by_usage
    from validate.base import gate, run_phase

    conn, ctx, ex, _, _, _ = setup(total=3)
    run_pipeline(conn, ctx, ex,
                 steps=("S0", "S1", "S2", "S3", "S4", "S5", "S6", "S6a"))

    n = conn.execute("SELECT COUNT(*) FROM meta_field_usage").fetchone()[0]
    check("RAW 경로 전수가 등록부에 적재된다", n > 100, f"{n}경로")
    # ★ 시드가 다 채워지면 미분류가 0 이다 — 목표 상태다.
    #   기전을 시험하려면 시드에 없는 경로를 하나 넣는다
    conn.execute("INSERT INTO meta_field_usage(site,endpoint,json_path,usage,"
                 "reason,first_seen,last_seen) VALUES "
                 "('encar','detail','새필드','unclassified','시험',?,?)",
                 ("t", "t"))
    conn.commit()
    un = list_by_usage(conn, "unclassified")
    check("★ 시드에 없는 경로는 미분류로 남는다", bool(un), f"{len(un)}건")

    sug = os.path.join(ROOT, "config", "field_usage.suggested.json")
    check("★ 분류 후보 파일이 생성된다", os.path.isfile(sug))
    if os.path.isfile(sug):
        s = json.load(open(sug, encoding="utf-8"))
        check("후보에 근거·관측수·표본이 붙는다",
              all({"suggested_usage", "reason_hint", "observed", "samples"}
                  <= set(v) for v in s["candidates"].values()),
              f"{s['count']}건")
        kinds = {v["suggested_usage"] for v in s["candidates"].values()}
        check("★ 후보 파일은 미분류만 담는다 (지금은 비어 있는 것이 정상)",
              s["count"] == 0 or kinds - {"unclassified"},
              f"{s['count']}건 {sorted(kinds)}")

    class _V:
        run_id = "r1"
        policy_raw = json.load(open(os.path.join(ROOT, "config", "scoring.json"),
                                    encoding="utf-8"))
        depreciation = {}

    res = run_phase(conn, _V(), "V4")
    blocked = gate(res)
    # ★ V4-11 은 「판정에 쓰는 경로가 미분류일 때」만 fatal 이다.
    #   아무도 안 읽는 새 필드까지 막으면 새 차종마다 파이프라인이 죽는다
    codes = {r.check.code for r in res if not r.passed}
    check("★ 미분류 목록은 남는다 (V4-11b · warn)", "V4-11b" in codes,
          str(sorted(codes)))
    check("파이프라인을 막는 것은 fatal 만",
          all(r.check.severity == "fatal" for r in blocked),
          str([r.check.code for r in blocked]))

    rep = halt_report(conn, blocked)
    check("★ 중단해도 빈 화면이 아니다 — 사유·미분류 전량·조치",
          "중단 사유" in rep and "미분류 경로" in rep and "조치" in rep,
          f"{len(rep.splitlines())}줄")


# ── --target 범위가 뒤 단계에도 걸리는가 (STEP 22) ───────────────────
def test_target_scope() -> None:
    """★ S1·S2 만 제한하면 S5 가 DB 의 전 매물을 읽는다.

    실측 사고: 240건을 지정했는데 S5 expected 가 30,580 이었다.
    """
    conn, ctx, ex, _s, _c, targets = setup(total=3)
    run_pipeline(conn, ctx, ex, steps=("S0", "S1", "S2", "S3", "S4"))

    # 범위 밖 차종의 매물이 DB 에 남아 있는 상황을 만든다
    conn.execute("INSERT INTO core_listing(site,source_id,target_key,status,"
                 "first_seen,last_seen,row_status) VALUES "
                 "('encar','999999','SPORTAGE_LPI','active','t','t','ok')")
    conn.commit()
    total = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE status='active'").fetchone()[0]

    only = {"G80_25T": targets["G80_25T"]}
    ex2 = make_executors(EncarAdapter(json.load(open(
        os.path.join(ROOT, "config", "endpoints.json"),
        encoding="utf-8"))["encar"]), _s, Clock(), _c, only,
        rng=random.Random(1), root_dir=ROOT)
    rep, _rows = ex2["S5"](conn, ctx)
    # ★ 진단은 encarDiagnosis == 0 인 매물만이라 표본에서는 빠진다 (STEP 21b)
    from collect.runner import LISTING_ENDPOINTS

    per = len(LISTING_ENDPOINTS) - 1
    check("★ 범위 밖 차종은 S5 가 요청하지 않는다",
          rep.expected == (total - 1) * per,
          f"{rep.expected} (범위 밖 포함 {total * per})")


# ── S7 카탈로그 호출 키 (실측) ───────────────────────────────────────
def test_catalog_key() -> None:
    """★ 호출은 매물 ID · 중복 제거는 모델 키다."""
    conn, ctx, ex, stub, _c, _t = setup(total=3)
    run_pipeline(conn, ctx, ex,
                 steps=("S0", "S1", "S2", "S3", "S4", "S5", "S6", "S6a", "S7"))
    check("★ 매물 ID 로 호출한다 (jatoVehicleId 아님)",
          all(len(i) <= 10 for i in stub.catalog_ids), str(stub.catalog_ids))
    saved = [r[0] for r in conn.execute(
        "SELECT source_id FROM raw_response WHERE endpoint='catalog'")]
    keys = [r[0] for r in conn.execute(
        "SELECT DISTINCT model_catalog_key FROM core_listing "
        "WHERE model_catalog_key IS NOT NULL")]
    check("★ 저장 키는 모델 키다 (다음 실행의 중복 제거 근거)",
          sorted(saved) == sorted(keys), f"{saved} / {keys}")
    check("모델당 1회", len(saved) == len(set(saved)))


# ── V1-13 껍데기가 인자를 변형하지 않는가 (STEP 116) ─────────────────
def test_wrapper_args() -> None:
    """★ run.bat collect --target X 가 전 차종 수집이 됐던 사고."""
    import subprocess

    def run_dry(argv):
        return subprocess.run(
            [sys.executable, *argv], cwd=ROOT, capture_output=True, text=True,
            env=dict(os.environ, PYTHONIOENCODING="utf-8")).stdout

    direct = run_dry(["run.py", "collect", "--dry", "--target", "KOLEOS_HEV"])
    wrapped = run_dry(["tools/menu.py", "dry", "--target", "KOLEOS_HEV"])
    check("★ 껍데기를 거쳐도 범위가 같다 (V1-13)",
          "차종 1종" in direct and "차종 1종" in wrapped,
          f"직접={('1종' in direct)} 껍데기={('1종' in wrapped)}")

    full = run_dry(["tools/menu.py", "dry"])
    check("범위를 안 주면 전 차종", "차종 10종" in full)

    bad = run_dry(["tools/menu.py", "test", "--target", "X"])
    check("★ 인자를 안 받는 명령은 거부", "인자를 받지 않는다" in bad, bad[:60])

    # ★ 자기 인자를 읽는 명령까지 막으면 안 된다 (실측 사고: checkall)
    for cmd in ("checkall", "migrate", "dict", "req", "facet"):
        outp = run_dry(["tools/menu.py", cmd, "없는.db", "--target", "X"])
        check(f"★ {cmd} 는 인자를 그대로 받는다",
              "인자를 받지 않는다" not in outp, outp[:50])

    # ★ 새 인자가 생겨도 껍데기가 삼키지 않는다 (V1-13).
    #   --target 만 통과시키는 구조라 --only 가 조용히 사라졌다 — 세 번째 사고
    for extra in (["--only", "S11"], ["--from", "S9"]):
        direct = run_dry(["run.py", "collect", "--dry", *extra])
        wrapped = run_dry(["tools/menu.py", "dry", *extra])
        check(f"★ {extra[0]} 도 그대로 전달된다", direct == wrapped,
              f"{len(direct)} vs {len(wrapped)}")


# ── 분류 실패 매물은 out_of_scope (V1-07) ────────────────────────────
def test_unclassified_listing() -> None:
    """★ 대상을 못 정한 매물이 active 로 남으면 V1-07 이 걸린다.

    실측 사고: 53건이 4종 상태 없이 active 였다.
    """
    conn, ctx, ex, _s, _c, _t = setup(total=3)
    run_pipeline(conn, ctx, ex, steps=("S0", "S1", "S2", "S3", "S4"))
    n = conn.execute(
        "SELECT COUNT(*) FROM core_listing "
        "WHERE status='active' AND target_key IS NULL").fetchone()[0]
    check("★ target_key 없는 매물이 active 로 남지 않는다", n == 0, str(n))
    total = conn.execute("SELECT COUNT(*) FROM core_listing").fetchone()[0]
    check("적재 자체는 빠뜨리지 않는다 (out_of_scope 로 남는다)", total > 0)


if __name__ == "__main__":
    print("S0~S3 종단 시험 (모의 응답)")
    test_envelope()
    test_last_page_exact()
    test_facet()
    test_facet_missing_axis()
    test_dict_step()
    test_all_groups()
    test_parse_pipeline()
    test_target_scope()
    test_unclassified_listing()
    test_wrapper_args()
    test_catalog_key()
    test_score_pipeline()
    test_validate()
    test_registry_gate()
    print()
    print("결과:", "통과" if not FAIL else "실패 — " + " / ".join(FAIL))
    sys.exit(1 if FAIL else 0)
