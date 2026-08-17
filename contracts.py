# -*- coding: utf-8 -*-
"""계층 간 계약 — Protocol · DTO.

지시서   0장 STEP 2 (부작용 주입) · 1장 STEP 11 (어댑터) · STEP 12 (원문 획득)
근거     계층 간 전달은 DTO 로만 한다.  DB Row 를 상위 계층으로 넘기지 않는다 (STEP 1).
         v1 은 352컬럼 Row 를 그대로 함수에 넘겨, 어떤 컬럼이 판정에 쓰이는지
         시그니처만으로 알 수 없었다.
금지     전역 가변 상태로 원문을 전달하는 것 (STEP 8-④ · v1 last_raw 사고).
         분석 계층이 Clock · Fetcher 를 아는 것 (STEP 2).
"""
from __future__ import annotations

import json

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Protocol, runtime_checkable

# ── 부작용 주입 (0장 STEP 2) ──────────────────────────────────────────
# 시각 · 난수 · HTTP 는 주입한다.  now() 를 직접 호출하지 않는다 (STEP 8-⑤).


@dataclass(frozen=True)
class Response:
    """Fetcher 가 돌려주는 것.  해석하지 않은 상태 그대로다."""

    http_code: int
    body_text: str
    content_type: str | None
    encoding: str | None


@runtime_checkable
class Clock(Protocol):
    def now(self) -> datetime: ...


@runtime_checkable
class Fetcher(Protocol):
    def get(self, url: str, headers: dict[str, str]) -> Response: ...


@runtime_checkable
class Rng(Protocol):
    def random(self) -> float: ...


# ── 수집 계약 (2장 정의서 · 1장 STEP 11·12) ───────────────────────────


@dataclass(frozen=True)
class Request:
    method: str  # 'GET'
    url: str
    headers: dict[str, str]
    timeout_sec: float


@dataclass(frozen=True)
class EndpointSpec:
    """어댑터가 스스로 선언한다.  required_keys 가 형식 검증의 근거다 (STEP 18)."""

    kind: str  # 'list'·'detail'·'inspection'·'record'·'diagnosis'·'catalog'·'facet'
    scope: str  # 'target'·'listing'·'model'
    required_keys: list[str]  # 라벨↔내용 검증
    root_type: str  # 'object'·'array'
    per_call: str  # 무엇 하나당 1회인가


@dataclass(frozen=True)
class FetchResult:
    """raw 는 이 호출의 응답만 담는다.  공유 변수를 쓰지 않는다 (STEP 12)."""

    kind: str
    source_id: str | None
    status: str  # ok·empty·not_found·error
    raw: dict | list | None
    http_code: int | None
    error: str | None
    fetched_at: datetime


@dataclass(frozen=True)
class TargetSpec:
    target_key: str  # 'KOLEOS_HEV'
    label: str
    site_query: dict  # 사이트별 쿼리 재료.  어댑터가 해석한다


# ── 상태 열거 (2장 STEP 16 · 3장 STEP 39) ─────────────────────────────
# 세 집합은 서로 다르다.  같은 이름이라고 같은 값이 아니다 (STEP 39).

FETCH_STATUS: frozenset[str] = frozenset(
    {"ok", "empty", "not_found", "error", "not_requested"}
)
LISTING_STATUS: frozenset[str] = frozenset(
    {"new", "active", "gone", "relisted", "out_of_scope"}
)
ROW_STATUS: frozenset[str] = frozenset({"ok", "partial", "error"})

# 반입 형식 (13장 STEP 136a).  ★ ①이 원칙이다 — 원문 JSON 이 아니면
# 사이트 원문이 없는 것이고, 화면이 「원문 없음」이라고 말해야 한다
FORMAT_JSON, FORMAT_IDS, FORMAT_CSV = "json", "ids", "csv"
# ④ facet 원문 (개정 260).  ★ color_ext · color_int · fuel 사전은 여기서만 나온다
FORMAT_FACET = "facet"
IMPORT_FORMATS: frozenset[str] = frozenset(
    {FORMAT_JSON, FORMAT_IDS, FORMAT_CSV, FORMAT_FACET}
)
# CSV 열 이름.  ★ 순서가 아니라 머리글로 읽는다 — 열이 바뀌면 값이 밀린다
CSV_COLUMNS: tuple[str, ...] = (
    "source_id", "target_key", "trim", "year_month", "mileage_km", "price_won",
)
# 반입분 표시 (STEP 136b ①④).  ★ 수집분과 섞이지 않게 하는 값들이다
IMPORT_SOURCE = "import"
# 브라우저가 사용자 회선으로 받은 것 (13장 STEP 136c).  ★ 서버가 받은 것이 아니다
ORIGIN_BROWSER = "browser"
IMPORT_STAGE = "confirmed"       # 사람이 정한 것이다.  잠정(provisional)이 아니다
# S4 완료 행의 expected.  actual 이 collector 인지 import 인지로 갈린다
S4_EXPECTED = "collector 또는 import"
S4_CODE = "STEP53-S4"
# 반입이 대신할 수 있는 단계 (5장 · 개정 259).  ★ /search/ 가 407 인 자리다
S1_CODE = "STEP53-S1"        # 목록 확보
S2_CODE = "STEP53-S2"        # facet (분류 축)
IMPORT_STEP_CODES = (S1_CODE, S2_CODE, S4_CODE)


# ── Store → Analyzer 계약 (3장 정의서) ───────────────────────────────
# ★ 판정에 쓰는 필드는 전부 명시한다.  dict 안에 숨기지 않는다.
#   record_summary: dict 같은 통짜 필드는 352컬럼 Row 를 dict 하나로 바꾼 것에 불과하다.
#   ListingSnapshot 에 없는 필드는 판정에 쓸 수 없다.
#   축을 추가하려면 이 DTO 를 먼저 고친다.


@dataclass(frozen=True)
class ListingSnapshot:
    """Analyzer 입력.  core_* 조인 결과.  Row 를 직접 넘기지 않는다."""

    listing_id: int
    site: str
    target_key: str
    price_current_won: int | None
    price_origin_won: int | None
    year_month: str | None
    mileage_km: int | None
    displacement_cc: int | None
    warranty_body_month: int | None
    warranty_body_km: int | None
    warranty_power_month: int | None
    warranty_power_km: int | None
    first_registration_date: date | None
    options_standard: list[str] | None
    options_choice: list[str] | None
    inspection_panels: list[dict] | None  # outers 원문 배열
    # ── E등급 절대조건 필드는 dict 에 숨기지 않고 명시한다 (7장 STEP 82) ──
    flood_total_cnt: int | None
    flood_part_cnt: int | None
    total_loss_cnt: int | None
    airbag_deployed: int | None
    seizing_cnt: int | None
    pledge_cnt: int | None
    accident_my_cost: int | None
    accident_my_cnt: int | None
    accident_other_cnt: int | None
    inspection_waterlog: int | None
    sales_status: str | None
    lease_present: bool | None
    lease_type: str | None
    not_join_json: str | None
    owner_change_cnt: int | None
    plate_use_char: str | None   # 허·하·호 (7장 STEP 78)
    plate_history_hash_json: str | None
    color_ext_raw: str | None
    color_ext_hex: str | None
    sell_type: str | None
    plate_hash: str | None  # ★ 원본은 core_pii.  마스킹 컬럼은 없다 (STEP 35)
    ad_body_text: str | None
    site_flags: dict  # 사이트 고유값.  어댑터 사전을 통해서만 읽는다
    # ★ 매물별 판정 값 6종 (F-1 · V4-24).
    #   target_config 에 담으면 어떤 값이 판정에 쓰이는지 시그니처로 알 수 없다
    diagnosis_car: int | None = None
    advertisement_type: str | None = None
    lease_rent_info: str | None = None
    usage_change_types_json: str | None = None
    warranty_extend: int | None = None
    warranty_deemed: int | None = None
    # ★ 보험이력 용도 변경이력 (개정 302).  렌트를 세 곳에서 대조한다
    record_use_json: str | None = None
    # ★ 같은 차종·트림·연식 실매물 중앙값과 그 표본 수 (개정 292 ①).
    #   매물별 값이라 target_config 에 숨기지 않는다 (F-1 · V4-24)
    market_median_won: int | None = None
    market_sample_n: int | None = None
    # ★ 점검 출처 — TABLE 플랫폼 직영 · IMAGE 판매자 등록 (개정 300 · 306)
    inspection_formats: list | None = None
    # ★ 자차 미가입 개월 · 보유 개월 (개정 294 · 322).
    #   「기간이 있다」가 아니라 「보유 기간의 몇 %인가」가 흠이다
    not_join_months: int | None = None
    owned_months: int | None = None
    # ★ F-scoring ② 가 쓰는 것 (개정 329).  없으면 「확인 안 됨」이다
    inspection_inner_json: str | None = None
    inspection_tuning: int | None = None
    car_state_ok: bool | None = None
    tire_tread_mm: float | None = None
    # 신차가 = 등급기준 + 선택옵션가 합 (개정 301) — ①-2 가 이것을 쓴다
    origin_total_won: int | None = None
    ev_battery_soh: float | None = None
    # ★ 용도 축 (F-scoring ③-1).  관용 · 영업용은 보험이력에 있다
    use_gov: int | None = None
    use_business: int | None = None
    # 선택 옵션가 합 (원).  ★ 카탈로그가 없으면 None — 「0원」이 아니다
    option_total_won: int | None = None


@dataclass(frozen=True)
class AxisResult:
    axis: str
    value: int | None
    source: str
    prio: int
    denominator_excluded: bool


# ── 계정 · 권한 (13장 STEP 126) ──────────────────────────────────────
# ★ 계층 횡단이다.  화면(10장) · 관리자(13장) · watch_item(11장) 이 모두 쓴다.
#   store/admin.py 에 두면 표현 계층이 저장 계층을 import 하게 된다 (1장 계층 규칙)
ROLE_ANONYMOUS, ROLE_USER, ROLE_ADMIN = "anonymous", "user", "admin"
# 승인 전.  ★ 로그인은 되지만 관심 등록은 못 한다 (STEP 126 · 승인제).
#   anonymous 보다는 위다 — 자기 계정 화면은 볼 수 있어야 한다
ROLE_PENDING = "pending"
ROLE_RANK = {ROLE_ANONYMOUS: 0, ROLE_PENDING: 1, ROLE_USER: 2, ROLE_ADMIN: 3}


@dataclass(frozen=True)
class Account:
    """★ anonymous 는 행이 아니다.  메모리에서 만든다 (STEP 126).

    FK 가 걸린 곳(watch_item)에 anonymous 가 들어가면 안 된다.
    """

    account_id: int | None
    role: str
    display_name: str
    created_at: datetime | None = None
    last_seen_at: datetime | None = None
    must_change_secret: bool = False


ANONYMOUS = Account(None, ROLE_ANONYMOUS, "비로그인")


def require_role(account: Account, role: str) -> None:
    """서버가 막는다.  화면 숨김은 권한이 아니다 (STEP 126 · V10-02).

    I/O 가 없는 순수 판정이라 계약 계층에 둔다.
    화면이 이것 하나 때문에 저장 계층을 import 하지 않게 한다.
    """
    from errors import PolicyError

    if ROLE_RANK.get(account.role, 0) < ROLE_RANK[role]:
        raise PolicyError(
            f"권한 부족: {account.role} < {role}", step="STEP 126")


# ── 실행 계약 (5장 정의서) ───────────────────────────────────────────


@dataclass(frozen=True)
class RunContext:
    """한 실행의 좌표.  버전과 설정 해시가 함께 있어야 재현된다.

    설정 파일이 바뀌었는데 버전을 올리지 않으면 재현이 깨진다.
    해시를 함께 남겨 「선언한 버전」과 「실제 내용」이 어긋나는 것을 잡는다.
    """

    run_id: str
    site: str
    started_at: datetime
    parse_version: str
    dict_version: str
    calc_version: str
    endpoint_config_hash: str
    target_config_hash: str
    scoring_config_hash: str
    targets: list[TargetSpec]


@dataclass
class StepReport:
    """단계 1회의 산출.  화면 출력만 하지 않는다.

    expected 가 핵심이다.  이것이 없으면 「애초에 안 던진 것」을 검증할 수 없다.
    v1 은 208건 중 76건만 요청하고도 리포트가 정상으로 보였다.
    rejected 는 ok 의 부분집합이다.  별도 상태가 아니다.
    """

    step: str
    target_key: str | None
    expected: int
    requested: int
    ok: int
    empty: int
    not_found: int
    error: int
    not_requested: int
    rejected: int
    elapsed_sec: float
    halted: bool
    halt_reason: str | None


@dataclass(frozen=True)
class ResumePoint:
    """재개 좌표.  단계 이름만으로는 재개할 수 없다.

    수집 단위가 차종 × 페이지, 매물 × 엔드포인트이기 때문이다.
    """

    step: str
    target_key: str | None
    page: int | None
    source_id: str | None
    endpoint: str | None


# ── 계층 횡단 순수 함수 (STEP 15a) ───────────────────────────────────
# ★ 두 층 이상이 쓰는데 한쪽에 있으면 의존이 거꾸로 간다.
#   지금 넘는 것만 내린다 — 미리 옮기면 여기가 잡동사니가 된다

VIN_LENGTH = 17  # 표준 형식이다.  임계값이 아니라 규격이다
VIN_FORBIDDEN = frozenset("IOQ")  # 숫자와 헷갈려 규격이 뺐다


def clean_vin(value) -> str | None:
    """형식 위반이면 None.  결합에 쓰지 않는다 (STEP 30)."""
    if value is None:
        return None
    s = str(value).strip().upper()
    if len(s) != VIN_LENGTH or not s.isalnum():
        return None
    if VIN_FORBIDDEN & set(s):
        return None
    return s

def total_of(components: dict) -> int:
    """Σ(skipped 아닌 points).  스킵된 성분의 점수는 총점에서 뺀다."""
    n = 0
    for v in components.values():
        if isinstance(v, dict):
            if not v.get("skipped"):
                n += int(v["points"])
        else:
            n += int(v)
    return n


@dataclass(frozen=True)
class RegressionReport:
    """12장 STEP 124 회귀 시험.  버전이 같으면 결과가 같아야 한다."""

    baseline_calc_version: str
    compared_listings: int
    score_mismatch: int
    grade_mismatch: int
    denominator_mismatch: int
    samples: list[str] = field(default_factory=list)


def json_paths(node, trail: str = "", out: set | None = None) -> set:
    """경로 전수.  배열 요소는 `[]` 로 한 경로로 센다 (STEP 19)."""
    out = out if out is not None else set()
    if isinstance(node, dict):
        for k, v in node.items():
            p = f"{trail}.{k}" if trail else k
            out.add(p)
            json_paths(v, p, out)
    elif isinstance(node, list):
        for el in node:
            json_paths(el, f"{trail}[]", out)
    return out


# 라벨 ↔ 내용 형식 (0장 불변식 ④).
# ★ 「주행거리」 자리에 날짜가 오면 그것은 파싱이 아니라 우연이다.
#   이름이 맞다고 값이 맞는 것이 아니다 — 형식으로 한 번 더 본다
FIELD_SHAPES: dict[str, str] = {
    "mileage_km": "int",
    "price_current_won": "int",
    "price_origin_won": "int",
    "displacement_cc": "int",
    "owner_change_cnt": "int",
    "seizing_cnt": "int",
    "pledge_cnt": "int",
    # ★ 실측 형식이다.  DB 가 정본이지 내 짐작이 아니다 — YYYY-MM 로 저장된다
    "year_month": "ym",
    "diagnosis_car": "bool01",
    # ★ JSON 문자열은 실제로 파싱해 본다.  「문자열이다」만 보면
    #   "not json" 이 통과한다 (불변식 ④ · C-5)
    "options_choice_json": "json",
    "options_standard_json": "json",
    "options_etc_json": "json",
    "options_tuning_json": "json",
    "usage_change_types_json": "json",
    "lease_rent_info_json": "json",
    "plate_history_hash_json": "json",
    "not_join_json": "json",
    "warranty_extend": "bool01",
    "warranty_deemed": "bool01",
}


# 연월 표기 길이.  ★ 실측이 정본이다 — DB 는 '2024-12' 로 저장한다
YM_DASHED = len("2024-12")
YM_PLAIN = len("202412")


def shape_ok(field: str, value) -> bool:
    """라벨이 요구하는 형식인가.

    ★ None 은 통과다.  「값이 없다」와 「형식이 틀렸다」는 다르다 —
      전자는 그 매물에 없는 것이고 후자는 우리가 잘못 읽은 것이다
    """
    shape = FIELD_SHAPES.get(field)
    if shape is None or value is None:
        return True
    if shape == "int":
        # ★ 음수를 받지 않는다.  주행거리 −1 은 값이 아니라 오류다 (C-5)
        return (isinstance(value, int) and not isinstance(value, bool)
                and value >= 0)
    if shape == "json":
        if not isinstance(value, str):
            return False
        try:
            json.loads(value)
        except (TypeError, ValueError):
            return False
        return True
    if shape == "bool01":
        return value in (0, 1, True, False)
    if shape == "ym":
        # 실측: '2024-12' (YM_DASHED).  옛 '202412' (YM_PLAIN) 도 받는다
        if not isinstance(value, str):
            return False
        if len(value) == YM_DASHED and value[4] == "-":
            return value[:4].isdigit() and value[5:].isdigit()
        return len(value) == YM_PLAIN and value.isdigit()
    return True


def shape_violations(row: dict) -> list[str]:
    """형식이 어긋난 필드.  ★ 저장 전에 본다 (불변식 ④)."""
    return [f"{k}={v!r}" for k, v in row.items() if not shape_ok(k, v)]
