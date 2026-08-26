# -*- coding: utf-8 -*-
"""리포트 DTO (L9).

지시서   9장 정의서 · STEP 90 (4층)
근거     출력은 판정 결과를 그대로 보여주는 것이지 여기서 새로 계산하지 않는다.
금지     Reporter 가 점수·판정을 계산하는 것.  표시용 파생값(순위·백분위)은 허용.
         Reporter 가 DB 를 직접 조회하는 것 — DTO 를 받아 형식만 바꾼다.
"""
from __future__ import annotations

from contracts import RegressionReport  # noqa: F401

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class VersionStamp:
    """coefficient 는 값만으로 부족하다.  coefficient_id 로 이력 행을 가리킨다."""

    parse_version: str
    dict_version: str
    calc_version: str
    coefficient: float | None
    coefficient_id: int | None
    calculated_at: datetime | None


@dataclass(frozen=True)
class ReportMeta:
    run_id: str
    layer: str  # 'L0' · 'L1' · 'L2' · 'L3'
    site: str
    target_key: str | None
    calc_version: str
    generated_at: datetime | None


@dataclass(frozen=True)
class AxisView:
    axis: str  # 'price' · 'spec.hud' 처럼 점 표기
    label: str
    value: int | None
    points: float
    max_points: int
    excluded: bool
    source: str
    prio: int
    # ★ 사람이 읽을 사유 (개정 306).  「missing」과 「site_unavailable」은 다르다 —
    #   앞은 우리가 못 받은 것이고 뒤는 그 사이트가 아예 안 주는 것이다.
    #   사람이 「그럼 K카에서 찾아볼까」를 할 수 있어야 한다
    why: str = ""
    # ★ 사람이 읽을 근거 (명령서 13-2 ④).  ★ 코드는 `source` 에 그대로 남는다 —
    #   ★ 화면은 이것을 내고 ★ 코드는 `title=` 로 뒤에 둔다
    source_label: str = ""
    # ★ 0 을 셋으로 가른 기호 (명령서 13-2 ⑤ · UI_REVIEW 5a).
    #   ★ 목록·상세는 이것을 내고 · `/why` 는 숫자를 그대로 낸다
    #   OK 확인했고 좋다 · × 확인했고 없다/나쁘다 · — 확인 못 했다
    mark: str = ""
    mark_why: str = ""


@dataclass(frozen=True)
class FinanceView:
    """점수가 아니라 비용이다 (STEP 91).  점수 축에 넣지 않는다.

    ★ 선납금 1,500만은 취득 부대비용을 포함한 초기 현금 부담이다.
      표시가에 취득세를 더하고 거기서 선납금을 빼면 취득세가 두 번 반영된다.
      배분이 먼저다 — 차값 선납 = 선납금 − 부대비용, 원금 = 표시가 − 차값 선납.
    검산   차값 선납 + 할부 원금 == 표시가
    """

    price_listed_won: int
    acquisition_cost_won: int
    down_payment_won: int  # 현금 상한 (개정 400).  표시가와 무관하게 고정
    vehicle_down_won: int  # 차값 선납 = 선납금 − 부대비용
    loan_principal_won: int
    monthly_payment_won: int
    total_interest_won: int
    cash_only: bool  # ★ 개정 400 — 화면은 이것 하나로 갈린다
    estimated_items: tuple[str, ...]


@dataclass(frozen=True)
class PurchaseCostItem:
    """구매비용 한 줄 (개정 353)."""

    label: str
    won: int
    estimated: bool  # 우리가 계산한 것인가


@dataclass(frozen=True)
class PurchaseCostView:
    """★ 어디서 사느냐에 따라 실제로 내는 돈이 다르다 (개정 353).

    마스터 확정 — 「케이카로 구매 시 가격이고 엔카 구매 시 가격이잖아.
    사이트별 총합을 내라」
    ★ 표시가가 싼 쪽이 실제로 싼 쪽이 아닐 수 있다
    금지   차량가만 내는 것 · 사이트가 다른 매물을 표시가로만 견주는 것
    금지   점수에 넣는 것 — 가격 축과 이중 계산이 된다
    """

    site: str
    site_label: str
    items: tuple[PurchaseCostItem, ...]
    total_won: int
    from_site: bool  # 사이트가 준 총액인가.  아니면 우리가 계산한 것이다
    benefits: tuple[str, ...]  # 추가 혜택 — 「10년 보증 포함」

    @property
    def estimated(self) -> bool:
        """총액에 「추정」을 붙여야 하는가."""
        return not self.from_site or any(x.estimated for x in self.items)


@dataclass(frozen=True)
class DiagnosisView:
    """엔카 진단 리포트 (2장 STEP 21b).  ★ 사람이 읽을 문장이다."""

    diagnosed_at: str | None
    center_name: str | None
    checker_comment: str | None      # 「외부패널 단순교환 차량」 등
    outer_panel_comment: str | None
    item_count: int | None = None        # 판정 부위 수 (소견 제외)
    replacement_count: int | None = None


@dataclass(frozen=True)
class FetchView:
    """무엇을 조회했는가 (시안 v2_why).

    ★ 「안 부른 것」과 「불렀는데 못 받은 것」은 다르다.
      전자는 우리 잘못이고 후자는 그 매물에 없는 것이다 — 사람이 판단에 쓴다
    """
    endpoint: str
    label: str
    status: str          # 받음 · 없음 · 미조회
    gives: str           # 이 응답이 무엇을 주는가
    impact: str | None = None   # 없으면 어느 축이 막히는가


@dataclass(frozen=True)
class CostRow:
    """비용 비교 한 줄 (시안 v2_why · 중고 ↔ 신차 동일 트림)."""
    label: str
    used_won: int | None
    new_won: int | None
    note: str | None = None


@dataclass(frozen=True)
class ScoreView:
    listing_id: int
    target_key: str
    grade: str
    score_total: float          # 555 환산.  ★ 등급 판정에 쓰지 않는다
    earned: float               # 실배점 합.  denominator 와 같은 자다
    denominator: float
    absolute_fail: str | None
    axes: list[AxisView]
    versions: VersionStamp
    finance: FinanceView | None = None
    # ★ {axis · label · points · reason · source} 사전이다.
    #   축 이름만 내면 채우면 얼마나 오르는지 알 수 없다 (STEP 149h)
    pending_items: tuple[dict, ...] = ()
    # ★★ 이 사이트가 ★ 한 매물도 못 채운 축 (마스터 지시 08-27).
    #   ★ 각 칸은 {axis · label · seen} — ★ `seen` 은 그 사이트에서 잰 매물 수다
    site_blind: tuple[dict, ...] = ()
    # ★ 「17 Component」를 화면에 박지 않는다 — 배점이 바뀌면 거짓말이 된다
    component_count: int = 0
    # 어느 사이트에서 왔는가 — 「엔카」 · 「K카 직영」 (50-multisite · V9-06)
    site_badge: str = ""
    # 시세 분포 위의 자리 (개정 340).  ★ 표본이 모자라면 why 만 있다
    market_pos: dict = field(default_factory=dict)
    # 등급 기준 (개정 292 · 306).  ★ 총점과 다르다
    grade_earned: float = 0.0
    grade_base: float = 0.0
    # ★ 근거가 있는 축의 배점 합과 그 비율 (개정 325).
    #   「안 받아서 0점」은 확인한 것이 아니다
    confirmed_points: float = 0.0
    confirm_pct: float = 0.0
    # 뺀 것 (개정 322).  ★ 무엇을 왜 뺐는지가 보여야 한다
    penalties: tuple = ()
    penalty_total: float = 0.0
    # 더한 것 (개정 380).  ★ 축이 아니다 — 분모를 안 늘린다.
    #   ★ 없으면 「배터리 진단 없음」이다.  0점이라 적지 않는다
    bonuses: tuple = ()
    bonus_total: float = 0.0
    ev: bool = False
    # ③ 왜 싼가 / 왜 비싼가 (개정 299 · 부록 G 상세 ③절)
    why_cheap: str | None = None
    why_cheap_reasons: tuple = ()
    # ★ NOT_RATED 사유 3종을 구분한다 (V5-12).  등급만 내지 않는다
    not_rated_reason: str | None = None
    # ★ 표시용이다.  점수에 반영하지 않는다 (STEP 21b).
    #   진단 items 는 outers 와 같은 사실이라 판정에 쓰면 중복 감점이다
    diagnosis: DiagnosisView | None = None
    # ★ 무엇을 조회했는가 — 판정의 근거가 어디서 왔는지가 먼저다 (G-1)
    fetches: tuple[FetchView, ...] = ()
    # 왜 이 순위인가 — 강점 · 약점
    strengths: tuple[str, ...] = ()
    weaknesses: tuple[str, ...] = ()
    rank: int | None = None
    # 비용 (중고 ↔ 신차 동일 트림).  ★ 점수에 반영하지 않는다
    costs: tuple[CostRow, ...] = ()
    # ⑨ 비용 — 사이트별 구매 총액 (개정 353).  ★ 여럿이면 나란히 낸다.
    #   표시가가 싼 쪽이 실제로 싼 쪽이 아닐 수 있다
    purchase_costs: tuple = ()
    # 받아 놓고 아직 판정에 안 쓰는 원문 (개정 378 · V11-134).
    # ★ 마스터 지적 — 「내가 보는 게 우선이지 않니?  그런데 네가 판정을
    #   못 내려서 받아 놓고 안 보이는데 말이 되니?」
    raw_sections: tuple = ()
    # 참고 자료 — 차종 공통 알려진 문제.  ★ 점수에 반영하지 않는다
    known_issues: tuple[dict, ...] = ()
    # ★ 5절 주요 옵션 — 옵션별 탑재 여부 (STEP 149c)
    options: tuple = ()
    # 상세 사진 (개정 375 · V11-132).  ★ 큰 사진 1장 + 썸네일 나머지 전부.
    #   마스터 지적 — 「목록은 간략하게 상세는 최대한 모든 정보가 들어가야 한다」
    #   ★ 실측 08-18 — /why 의 <img> 가 0개였다.  상세인데 실물을 못 봤다
    photos: tuple = ()
    # 엔카 원문 (STEP 149q).  ★ 우리 판정은 참고다.  실제 매물은 엔카에 있다.
    #   사람은 결국 거기서 사진을 보고 전화한다 — 그 길을 막으면 벽이 된다
    source_id: str | None = None
    encar_url: str | None = None
    # 감가 곡선 (시안 v2_why .curve).  ★ 이 차가 곡선의 어디에 있는지를 낸다 —
    #   기대가가 어떻게 나왔는지가 시세차의 근거다 (7장 STEP 70)
    curve: tuple = ()
    # ★ 확인 못 한 축을 채웠을 때의 비율·등급 (STEP 149h · D-2)
    pending_best: dict | None = None
    # ★★ 「판정 중」 — 근거 있는 축의 합이 분모의 절반 아래다 (명령서 67장).
    #   ★ 낮은 등급이 아니다.  ★ 눌러 열면 「무엇이 비었나」를 낸다
    waiting_axes: tuple[str, ...] = ()
    # ★ 「사고 · 용도 · 자차 · 소유자」 — ★ 문자열은 여기서 만든다 (STEP 152)
    waiting_text: str = ""
    # ★★ 제원 둘 (마스터 확정 08-24 · UI_REVIEW 10 · 가이드 답 08-24).
    #   ★ 「살지 말지」에 쓰인다 — ★ 기름값이 총비용이고 ★ 식구 수가 차를 정한다
    #   ★ 원문에 없으면 None 이다 — ★ 0 이 아니다.  ★ 화면에는 「—」
    #   ★ 상세와 비교에만 낸다.  ★ 목록에는 안 낸다 (S46-45)
    #   ★★ 축이 아니다 — ★ 판정에 안 들어간다.  ★ 보여 주기만 한다
    spec_fuel_economy_kmpl: float | None = None
    spec_seats: int | None = None



@dataclass(frozen=True)
class CollectSummary:
    listing_count: int
    endpoint_rates: dict[str, float]
    status_counts: dict[str, dict[str, int]]


@dataclass(frozen=True)
class ClassifySummary:
    provisional: int
    confirmed: int
    conflict: int


@dataclass(frozen=True)
class PriceSummary:
    median_actual_won: int
    median_expected_won: int
    coefficient: float | None
    coefficient_id: int | None
    bucket_counts: dict[str, int]


@dataclass(frozen=True)
class AxisStat:
    axis: str
    avg_points: float
    max_points: int
    distinct_values: int  # 1 이면 변별력 0 (6장 V3-04)
    excluded_ratio: float
    source_counts: dict[str, int]


@dataclass(frozen=True)
class CoefficientChange:
    target_key: str
    before: float | None
    after: float
    sample_size: int
    reason: str
    changed_at: str


@dataclass(frozen=True)
class DictChangeSummary:
    pending: int
    confirmed: int
    retired: int
    by_axis: dict[str, int]


@dataclass(frozen=True)
class TargetReport:
    meta: ReportMeta
    collect: CollectSummary
    classify: ClassifySummary
    price: PriceSummary
    axes: list[AxisStat]
    grades: dict[str, int]
    top: list[ScoreView]
    warnings: list[str]


@dataclass(frozen=True)
class RunStep:
    """L3 단계 한 줄 (STEP 53).

    ★ 화면이 필드로 읽는다.  튜플로 넘기면 조용히 빈다 (C-3)
    """
    step: str
    expected: str
    requested: int
    ok: int
    not_found: int
    error: int
    halted: bool


@dataclass(frozen=True)
class RunReport:
    meta: ReportMeta
    steps: list
    checks: list
    day_gap: object | None
    coefficient_changes: list[CoefficientChange]
    dict_changes: DictChangeSummary
    unclassified_count: int


@dataclass(frozen=True)
class HaltReport:
    """L0 — 실패가 아니라 「다음 행동」을 내는 리포트다 (STEP 90).

    completed_steps 를 반드시 낸다.  처음부터 다시 도는 것이 아님을 알 수 있어야 한다.
    """

    meta: ReportMeta
    halted_step: str
    halted_at: datetime | None
    failures: list  # CheckResult · severity='fatal'
    actions: dict[str, str]  # code → 다음 행동
    completed_steps: list  # StepReport · halted=False
    artifacts: list[str]
    versions: VersionStamp


@dataclass(frozen=True)
class FixAction:
    """6장 STEP 62 보정안.  보정은 재파싱으로 한다.  재수집이 아니다."""

    check_code: str
    action: str  # reparse · rescore · recollect · manual
    scope: str
    reason: str


@dataclass(frozen=True)
class NotifyResult:
    """11장 STEP 116 알림.  cause 가 listing 이 아니면 발송하지 않는다."""

    sent: int
    skipped_cause: int
    skipped_duplicate: int
    failed: int


# RegressionReport 는 contracts.py 다 — store/crosssite 도 쓴다 (STEP 15a)


@dataclass(frozen=True)
class ExportResult:
    filename: str
    content: bytes
    content_type: str


# ── 값 표시 대조표 (STEP 91) ─────────────────────────────────────────
# 「해당 없음」과 「없음」을 같은 기호로 쓰지 않는다.
# v1 은 셋을 섞어 수집 실패가 만점·0점으로 둔갑했다.
def display_value(value: int | None, excluded: bool, labels: dict) -> str:
    if value is None and excluded:
        return labels.get("unknown", "미확인")
    if value == -1 and excluded:
        return labels.get("na", "해당 없음")
    if value is None:
        return labels.get("unknown", "미확인")
    return labels.get(str(value), str(value))


def display_points(points: float | None, excluded: bool, max_points: int) -> str:
    """제외 축을 「0점」으로 쓰지 않는다.  — 또는 해당 없음이다."""
    if excluded:
        return f"—/{max_points}"
    return f"{points:g}/{max_points}"
