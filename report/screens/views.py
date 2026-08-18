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
    # ★ 축 이름만.  카드에서 「HUD 있음」을 라벨로 쓰면 값이 두 번 나온다
    head: str = ""
    # ★ O 있음 · - 없음 · ? 확인 못 함 — 「없음」과 「모름」을
    #   같은 기호로 내면 v1 사고가 되풀이된다 (STEP 149f)
    mark: str = "?"
    # ★ 축 칸에는 상태를 낸다.  점수를 내지 않는다 (STEP 149n · 개정 280).
    #   「HUD 0 은 있다는 거야 없다는 거야」 — 점수는 툴팁으로 옮긴다
    #   빈 문자면 화면이 mark 를 쓴다 (아직 상태를 못 만든 축)
    state: str = ""


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
    # ★ 그 사이트에서 사면 실제로 내는 돈 (개정 353).  차량가가 아니다
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
    # 어느 사이트에서 왔는가 — 「엔카」 · 「K카 직영」 · 「K카 직거래」
    # ★ 사이트가 둘 이상이면 값의 뜻이 사이트에 달려 있다 (50-multisite)
    site_badge: str = ""
    # 총액이 우리가 계산한 것인가 (개정 353).  ★ 「추정」을 숨기지 않는다
    buy_estimated: bool = False
    status_label: str | None = None  # gone → 「목록에서 사라짐」 (V6-06)
    # ★ 비율이 크게 · 원점수/분모가 작게 (STEP 149f).
    #   분모가 다른 매물을 눈으로 갈라야 한다
    earned: float | None = None
    denominator: float | None = None
    ratio_pct: float | None = None
    denom_short: bool = False
    # 확인율 — 「555 중 350점을 확인했습니다 (63%)」 (개정 298 I).
    # ★ 분모로 등급을 막지 않는 대신 얼마나 봤는지를 낸다
    confirmed_points: float | None = None
    confirm_pct: float | None = None
    # 전기차 배터리 진단 — SOH · 등급 (개정 296)
    battery_soh: float | None = None
    battery_grade: str | None = None
    # ★ 부록 G 10·11 — 시세 대비 % · 신차가 대비 % (개정 332)
    market_gap_pct: float | None = None
    origin_gap_pct: float | None = None
    # 트림 세부등급 · 옵션 종수 (개정 313)
    trim_detail_known: bool = False
    option_count: int = 0
    # 신차가 = 등급기준 + 선택옵션 (개정 301).  ★ 셋을 다 낸다
    option_price_won: int | None = None
    origin_total_won: int | None = None
    # 플랫폼 신뢰도 (개정 300) — 높음 · 보통 · 낮음 · 없음
    platform_trust: str | None = None
    platform_trust_why: list = field(default_factory=list)
    # 「왜 싼가」 (개정 299 · V3-52).  ★ 못 찾으면 그것도 낸다
    # 순위용 — 취향까지 넣은 555 기준 (개정 292 ④).  등급은 505 다
    rank_earned: float | None = None
    rank_total: float | None = None
    # 왜 이 순위인가 — 한 문장 (개정 304).  ★ 태그 나열이 아니다
    recommend_reason: str = ""
    why_cheap: str | None = None
    why_cheap_reasons: list = field(default_factory=list)
    # 대표 사진 주소 (개정 274).  ★ 우리가 내려받지 않는다 — ci.encar.com 을
    #   그대로 부른다.  없으면 None 이고 화면은 thumb-none 으로 자리를 채운다.
    #   ★ 판정에 쓰지 않는다.  보는 사람을 위한 것이다
    photo_url: str | None = None
    # 엔카 원문 (STEP 149q).  ★ 우리 판정은 참고다.  실제 매물은 엔카에 있다
    source_id: str | None = None
    encar_url: str | None = None
    # 「이 값으로 걸러 보기」에 쓰는 파생 (STEP 149p).
    # ★ 화면이 계산하지 않는다.  여기서 만들어 내려준다
    year: str | None = None           # 연식 4자리
    # ★ 시세차 — 이 도구가 하는 일이 「시세보다 싼 차 찾기」다 (개정 277 · 278).
    #   기대가 = 신차가 × 감가계수(경과년) × 차종 보정계수 (7장 STEP 70).
    #   음수면 시세보다 싸다.  가격 축이 excluded 면 None 이다 — 지어내지 않는다
    expected_price_won: int | None = None
    price_gap_won: int | None = None
    # ★ 셋을 나란히 낸다 (STEP 149n-3 · 개정 283).
    #   신차가 = 원문 category.originPrice · 시세 = 같은 차종·트림·연식 중앙값
    #   ★ 차이만 내면 무엇에서 뺀 것인지 모른다
    origin_price_won: int | None = None
    market_price_won: int | None = None   # 실제 매물 중앙값
    market_sample: int = 0                # 그 중앙값의 표본 수
    market_gap_won: int | None = None     # 가격 − 시세
    # 첫 게시가 대비 증감 (음수 = 내렸다).  변동이 없으면 None
    price_change_won: int | None = None
    # 딜러 정직도.  ★ 표본이 모자라면 None 이다 — 0 으로 내지 않는다
    dealer_trust: float | None = None
    dealer_quadrant: str | None = None
    # E등급 사유 등 비고
    note_tags: tuple = ()
    # 「확인 못 한 축을 채우면 얼마나 오를 수 있나」 (시안 v2_recommend .pbar).
    # ★ 지금 비율만 보면 「이 차가 끝인가」를 모른다
    got_pct: float = 0.0        # 지금 받은 몫 (만점 대비)
    may_pct: float = 0.0        # 채우면 더 받을 수 있는 몫
    upside_points: float = 0.0  # 확인 못 한 축의 배점 합
    km_bucket: int | None = None      # 주행 상한 (만km 단위로 올림)
    monthly_bucket_won: int | None = None   # 월납입 상한 (10만 단위로 올림)
    # ★ 값을 누르면 그 조건으로 걸러진다 (부록 G).  빈 주소를 만들지 않는다
    price_bucket_won: int | None = None
    mileage_bucket_km: int | None = None
    status_key: str | None = None

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
    # ★ 비면 「전부」다 (개정 306).  「엔카만」 「K카 직영만」 「전부」
    site: str | None = "encar"
    # 판매 유형 — 「K카 직영만」 (sites.json sell_type_labels)
    sell_type: str | None = None
    target_key: str | None = None
    grade: str | None = None
    axis: str | None = None  # Component 이름 'spec.hud'
    bucket: str | None = None
    # ★ 시세 막대를 누르면 그 구간 매물로 간다 (STEP 97).
    #   없으면 링크는 200 을 내지만 필터가 안 걸려 전건이 나온다
    price_min: int | None = None
    price_max: int | None = None
    # ★ 값을 누르면 그 조건으로 (STEP 149g · 149p).  절반만 링크면
    #   사람이 「누를 수 있는 것」과 「없는 것」을 구분 못 한다 (개정 276)
    dealer: str | None = None       # 그 딜러 매물만
    year: str | None = None         # 연식 4자리
    km_max: int | None = None       # 주행 상한 (구간)
    monthly_max: int | None = None  # 월납입 상한 — 가격 상한으로 환산한다
    listing_status: str | None = None
    # ★ 「A 이상만」 한 번에 (STEP 149s).  C·D 가 비율 순으로 앞에 섞인다
    min_grade: str | None = None
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
    # 가격 추이 막대 (시안 v2_watch .spark).  ★ 「지금 얼마」만으로는
    #   내려가는 중인지 올라가는 중인지 모른다.  각 칸은 {pct, dn, now}
    spark: tuple = ()


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
    # ★ 옵션 차이만 낸다.  같은 것은 접는다 (61-web 「비교」).
    #   같은 트림이면 옵션이 값을 가른다 — 이것이 비교 화면의 핵심이다
    option_same: tuple = ()
    option_only: tuple = ()


@dataclass(frozen=True)
class MarketView:
    target_key: str
    rows: list[MarketRow]
    coefficient_history: list[CoefficientChange]
    curve: list[tuple[int, float]]
    # 가격 분포 · 연식별 중앙값 · 트림별.  ★ 표본 5건 미만은 내지 않는다
    price_bins: list = field(default_factory=list)
    by_year: list = field(default_factory=list)
    # 연식별 중앙값 선 (개정 340) — {year · won · x · y}
    year_line: list = field(default_factory=list)
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
    # 4분면 좌표 (시안 v2_dealers .quad).  ★ 표본이 모자라면 None 이다 —
    #   0 으로 찍으면 「정직도 0」인 딜러가 된다
    quad_x: float | None = None    # 매물 수 (가로)
    quad_y: float | None = None    # 정직도 (세로)
    # 이 딜러가 가진 차종 분포 — 「G80 12 · GV70 8」 (마스터 지적 ⑤).
    # ★ 건수만 보면 「무엇을 파는 딜러인가」를 모른다
    targets: tuple = ()


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
    # ★ 차종이 안 붙은 매물 — 모델명·배지를 낸다 (개정 271 · V2-32).
    #   건수만 내면 targets.json 을 고칠지 규칙을 고칠지 못 정한다
    unmatched: list = field(default_factory=list)
    unmatched_total: int = 0
    matched_total: int = 0


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
    # 막대 높이 (%).  ★ 화면이 최대값을 못 찾는다 — 여기서 계산해 내려준다.
    #   ★ 자리를 앞에 끼우지 않는다 — 위치 인자로 만드는 곳이 어긋난다 (실측)
    #   「막대를 누르면」이라 적어 놓고 막대가 없으면 거짓말이다 (검토 14)
    height_pct: int = 0


@dataclass(frozen=True)
class ExcludedGroup:
    """후보에서 뺀 것 (시안 v2_recommend).  ★ 왜 뺐는지가 판단 재료다."""
    reason: str
    count: int
    note: str
    filter_url: str | None = None


@dataclass(frozen=True)
class ReportFile:
    """리포트 파일 한 줄 (개정 357)."""

    name: str
    layer: str  # L1 매물 · L2 차종 · L3 실행
    ext: str  # md · csv · json
    bytes: int
    made_at: str
    label: str  # 사람이 읽을 이름


@dataclass(frozen=True)
class ReportsView:
    """★ 목록만 내고 내용을 못 보게 하지 않는다 (개정 357).

    마스터 확정 — 「목록을 보고 클릭하면 내용을 볼 수 있게 팝업 박스로.
    다운로드 누를 때 다운로드」
    ★ 휴대폰에서 내려받으면 볼 도구가 마땅치 않다
    """

    files: tuple
    open_name: str | None = None
    open_ext: str = ""
    open_text: str = ""  # md · json 은 그대로
    open_rows: tuple = ()  # csv 는 표로
    open_head: tuple = ()
    truncated: bool = False  # 앞부분만 냈는가
    open_bytes: int = 0
