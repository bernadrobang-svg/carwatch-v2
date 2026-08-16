# -*- coding: utf-8 -*-
"""화면 전용 DTO.

지시서   10장 정의서 · STEP 93 (공통 규칙) · 105 (데이터 계약)
근거     v1 화면 구성을 유지하고 데이터 계약만 v2 규격으로 바꾼다
금지     화면 함수가 판정·채점을 계산하는 것
         화면이 raw_* 를 직접 조회하는 것 (V6-03)
허용     표시용 파생 — 순위 · 백분위 · 색상 톤 · 필터 링크
"""
from __future__ import annotations

from dataclasses import dataclass, field

from report.views import AxisView, CoefficientChange, ReportMeta, VersionStamp

# 톤 (STEP 93).  값 표기는 9장 STEP 91 대조표를 그대로 따른다
TONE_GOOD, TONE_BAD, TONE_MUTED, TONE_UNKNOWN = "good", "bad", "muted", "unknown"

# 필터 파라미터 이름 — v1 것을 유지한다.  북마크·링크가 깨지지 않는다
ORDERS = ("rank", "grade", "price", "price_desc", "monthly", "total_cost",
          "mileage", "year", "new", "dom")
BUCKETS = ("1", "0", "na", "unknown")

# ★ 목록 기본 건수는 정책이다 → config.web.rows_per_page (STEP 106 · E-5).
#   출처가 둘이면 갈린다 — 실측: scoring 200 과 web 300 이 화면마다 달랐다
#   코드 상수로 두면 두 곳이 갈린다


@dataclass(frozen=True)
class AxisChip:
    """label 은 9장 STEP 91 값 표시 대조표를 따른다.

    목록과 상세가 다른 문구를 쓰면 안 된다 (V6-02).
    """

    axis: str
    label: str
    tone: str
    filter_url: str
    # ★ O 있음 · · 없음 · ? 확인 못 함 — 「없음」과 「모름」을
    #   같은 기호로 내면 v1 사고가 되풀이된다 (STEP 149f)
    mark: str = "?"


@dataclass(frozen=True)
class ListingRow:
    listing_id: int
    grade: str
    rank: int | None
    # NOT_RATED 는 None (V6-04)
    target_label: str
    trim: str | None
    year_month: str | None
    mileage_km: int | None
    color_ext: str | None
    color_int: str | None
    axis_chips: list[AxisChip]
    price_won: int | None
    total_cost_won: int | None
    loan_principal_won: int | None
    monthly_won: int | None
    price_gap_pct: float | None
    price_change_cnt: int
    days_on_market: int | None
    dealer_shop: str | None  # ★ 상호다.  실명은 화면에 쓰지 않는다 (STEP 35)
    dealer_honesty: float | None
    note: str | None
    versions: VersionStamp
    status_label: str | None = None  # gone → 「목록에서 사라짐」 (V6-06)
    # ★ 비율이 크게 · 원점수/분모가 작게 (STEP 149f).
    #   분모가 다른 매물을 눈으로 갈라야 한다
    earned: float | None = None
    denominator: float | None = None
    ratio_pct: float | None = None
    denom_short: bool = False

    # ★ tone 으로 나눈다.  화면이 판정하지 않는다 (STEP 152)
    @property
    def strengths(self) -> list:
        return [c for c in self.axis_chips if c.tone == TONE_GOOD]

    @property
    def weaknesses(self) -> list:
        return [c for c in self.axis_chips if c.tone == TONE_BAD]

    @property
    def unknowns(self) -> list:
        """확인 못 한 축.  채우면 오를 수 있다 (STEP 105)."""
        return [c for c in self.axis_chips if c.tone == TONE_MUTED]


@dataclass(frozen=True)
class ListingFilter:
    site: str = "encar"
    target_key: str | None = None
    grade: str | None = None
    axis: str | None = None  # Component 이름 'spec.hud'
    bucket: str | None = None
    # ★ 시세 막대를 누르면 그 구간 매물로 간다 (STEP 97).
    #   없으면 링크는 200 을 내지만 필터가 안 걸려 전건이 나온다
    price_min: int | None = None
    price_max: int | None = None
    order: str = "rank"
    show_all: bool = False
    page: int = 1
    calc_version: str = "c1"


@dataclass(frozen=True)
class WatchRow:
    """관심 한 줄 (STEP 111).

    ★ ListingRow 만 내면 watch_id 가 없어 목표가 저장 · 추적 종료를
      아예 못 누른다 — action="/watch/" 가 된다 (실측 08-15)
    """
    watch_id: int
    listing: "ListingRow"
    target_price_won: int | None
    added_at: str
    closed_at: str | None
    memo: str | None


@dataclass(frozen=True)
class TargetStat:
    target_key: str
    total: int
    grades: dict[str, int]
    rank1: int
    median_price_a_won: int | None


@dataclass(frozen=True)
class RelaxRow:
    condition: str
    current: int
    relaxed: int


@dataclass(frozen=True)
class MarketRow:
    observed_at: str
    listing_count: int
    eligible_count: int
    min_won: int | None
    p25_won: int | None
    median_won: int | None
    p75_won: int | None
    max_won: int | None


@dataclass(frozen=True)
class ChangeRow:
    listing_id: int
    field: str
    old_value: str | None
    new_value: str | None
    change_kind: str
    changed_at: str


@dataclass(frozen=True)
class AttentionItem:
    kind: str  # pending · unclassified · warn · undecided
    detail: str
    count: int
    action: str


@dataclass(frozen=True)
class ViewerState:
    """화면 상단에 로그인 상태 · 역할을 낸다 (STEP 93 · 13장 STEP 126).

    ★ 판정은 계정과 무관하다.  개인화는 「무엇을 보는가」이지 「점수」가 아니다
    """

    role: str
    display_name: str
    can_watch: bool      # 관심 등록 · 알림 설정
    can_admin: bool      # 실행 · 배점 · 등록부 · 쿼리
    must_change_secret: bool = False


@dataclass(frozen=True)
class DashboardView:
    meta: ReportMeta
    viewer: ViewerState | None = None
    finalists: list[ListingRow] = field(default_factory=list)
    target_stats: list[TargetStat] = field(default_factory=list)
    relax_sim: list[RelaxRow] = field(default_factory=list)
    axis_shortfall: list = field(default_factory=list)
    market: list[MarketRow] = field(default_factory=list)
    recent_changes: list[ChangeRow] = field(default_factory=list)
    watch_summary: list[ListingRow] = field(default_factory=list)
    attention: list[AttentionItem] = field(default_factory=list)
    recent_runs: list = field(default_factory=list)
    # ★ 등급 분포 · E 사유 — 「몇 건인가」보다 「왜 그런가」다 (G-1)
    grade_counts: dict = field(default_factory=dict)
    # ★ 템플릿 엔진이 대괄호 첨자를 못 읽는다 — (등급, 건수) 쌍으로 넘긴다
    grade_rows: list = field(default_factory=list)
    grade_total: int = 0
    e_reasons: dict = field(default_factory=dict)
    # 오늘 변동 · 수집 단계.  ★ 사람이 「무엇이 달라졌나」를 먼저 본다
    today_changes: list = field(default_factory=list)
    steps: list = field(default_factory=list)


@dataclass(frozen=True)
class CompareView:
    rows: list[ListingRow]
    axes: list[str]  # 17 Component
    cells: dict[tuple[str, str], AxisView]
    denominator_mismatch: bool  # 분모가 다르면 경고 (V6-05)
    version_mismatch: bool  # 버전이 다르면 비교 불가
    # ★ 「이 셋 중에서」 — 축별로 누가 앞서는지를 낸다
    axis_winner: dict = field(default_factory=dict)


@dataclass(frozen=True)
class MarketView:
    target_key: str
    rows: list[MarketRow]
    coefficient_history: list[CoefficientChange]
    curve: list[tuple[int, float]]
    # 가격 분포 · 연식별 중앙값 · 트림별.  ★ 표본 5건 미만은 내지 않는다
    price_bins: list = field(default_factory=list)
    by_year: list = field(default_factory=list)
    by_trim: list = field(default_factory=list)
    other_targets: list = field(default_factory=list)


@dataclass(frozen=True)
class DealerRow:
    dealer_id: int
    dealer_shop: str | None  # ★ 상호다.  실명은 화면에 쓰지 않는다 (STEP 35)
    dealer_region: str | None
    years: float | None
    quadrant: str | None
    honesty_score: float | None
    sample_sufficient: bool
    volume: int
    sold_total: int | None
    sold_1y: int | None


@dataclass(frozen=True)
class NotReadyView:
    """판정 결과를 빈 값으로 보여주지 않는다 (STEP 104)."""

    meta: ReportMeta
    reasons: list[str]
    actions: list[str]
    # ★ 「사전에 없는 값」을 축·값·건수로 낸다.  「17건」만 내면 못 고친다
    pending_values: list = field(default_factory=list)
    # 이미 된 것 — 「아무것도 안 됐다」와 「등급만 없다」는 다르다
    done: list = field(default_factory=list)


@dataclass(frozen=True)
class TodayChange:
    """오늘 변동 한 줄 (시안 v2_dashboard)."""
    kind: str          # 인하 · 인상 · 신규 · 사라짐
    target_key: str
    trim: str | None
    # ★ 값으로 낸다.  「−180만」 같은 문자열은 화면이 만든다 (STEP 1)
    delta_won: int | None = None
    price_won: int | None = None
    listing_id: int | None = None


@dataclass(frozen=True)
class StepRow:
    """수집 단계 한 줄.  ★ 「없음」과 「실패」를 나눈다 — 뜻이 다르다."""
    step: str
    label: str
    requested: int
    ok: int
    missing: int | None
    failed: int
    seconds: float
    verdict: str


def _min_sample(root: str = ".") -> int:
    """표본이 이보다 적으면 중앙값을 내지 않는다.

    ★ 3건으로 「시세」라고 하면 사람이 그것을 시세로 믿는다 (시안 v2_market).
      정책값이라 config 에 둔다
    """
    import json as _j
    import os as _o

    with open(_o.path.join(root, "config", "web.json"),
              encoding="utf-8") as f:
        return int(_j.load(f)["market_min_sample"])


MIN_SAMPLE = _min_sample()


@dataclass(frozen=True)
class PendingValue:
    """사전에 없는 값 (시안 v2_notready).

    ★ 「17건」만 내면 사람이 무엇을 할지 모른다.
      어느 축을 막고 있는지까지 내야 판단이 된다
    """
    axis: str
    value: str
    count: int
    blocks: str


@dataclass(frozen=True)
class Bucket:
    """구간 한 칸 — 가격 분포 · 연식별 · 트림별 공용.

    ★ 만원 문자열을 여기서 만들지 않는다.  화면 문자열 생성은 Presentation 이다
      (STEP 1).  값으로 넘기고 템플릿이 |won 으로 찍는다
    """
    label: str
    min_won: int | None = None
    max_won: int | None = None
    count: int = 0
    median_won: int | None = None
    filter_url: str | None = None
    enough: bool = True


@dataclass(frozen=True)
class ExcludedGroup:
    """후보에서 뺀 것 (시안 v2_recommend).  ★ 왜 뺐는지가 판단 재료다."""
    reason: str
    count: int
    note: str
    filter_url: str | None = None
