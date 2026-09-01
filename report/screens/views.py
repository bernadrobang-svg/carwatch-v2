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
    # ★ 관문에 걸렸는가.  ★ 템플릿이 == 비교를 못 한다 (V11-104) —
    #   값으로 정해서 내려준다 (STEP 152 「화면이 문자열을 만들지 않는다」)
    blocked: bool = False


@dataclass(frozen=True)
class ScoreBar:
    """★ 목록의 시그니처 — 네 묶음 점수 막대 (개정 427 · STEP 97).

    ★ 사이트는 이것을 못 한다 — 자기 매물을 채점할 수 없다
    ★ 늘 같은 자리 · 같은 개수 · 같은 색이다.  행마다 달라지면 스캔이 깨진다
    """

    key: str          # car · value · warranty · taste
    label: str        # 차량 · 값 · 보증 · 취향
    css: str          # b1~b4 — ★ 색이다.  늘 같은 갈래가 같은 색이어야 한다
    pct: int          # 0~100.  ★ 막대 높이다
    earned: float     # 받은 점수
    cap: float        # 그 묶음 만점


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
    # ★★★★★ 09-02 마스터 확정 — ★ **판매지역** (사이트 딱지 옆 · `S46-225`).
    #   ★ 못 받으면 ★ `None` — ★ 화면이 「지역 —」이라 적는다
    region_label: str | None = None
    # ★ 세 값을 한 셀에 (41-view) — 표시가 · 현금 · 월.
    #   금지 「표시가만 보여주는 것」 — 부대비용이 차종마다 달라 순위가 뒤집힌다
    down_payment_won: int | None = None
    cash_only: bool = False
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
    # ★★★★★ 09-01 — ★ 부록 G A-3 막대의 ★ **둘째 칸** (`.may`).
    #   ★ 「근거는 있는데 아직 못 받은 몫」 = 확인율 − 받은 비율.
    #   ★★ 틀은 ★ 뺄셈을 못 한다 (`V11-04`) — ★ 여기서 낸다
    confirm_extra_pct: float = 0.0
    # 전기차 배터리 진단 — SOH · 등급 (개정 296)
    battery_soh: float | None = None
    battery_grade: str | None = None
    # ★ 부록 G 10·11 — 시세 대비 % · 신차가 대비 % (개정 332)
    market_gap_pct: float | None = None
    origin_gap_pct: float | None = None
    # ★ 성능부와 보험이력이 어긋난다 (V3-50 · 30-score/d-history).
    #   「성능 기록부에는 흔적이 없는데 보험 이력에는 수리 비용이 있었다」
    record_mismatch: bool = False
    # 트림 세부등급 · 옵션 종수 (개정 313)
    trim_detail_known: bool = False
    option_count: int = 0
    # 신차가 = 등급기준 + 선택옵션 (개정 301).  ★ 셋을 다 낸다
    option_price_won: int | None = None
    origin_total_won: int | None = None
    # 플랫폼 신뢰도 (개정 300) — 높음 · 보통 · 낮음 · 없음
    platform_trust: str | None = None
    platform_trust_why: list = field(default_factory=list)
    # ★★ 네 묶음 막대 (개정 427 · V11-163).  ★ 목록의 시그니처다
    bars: list = field(default_factory=list)
    # ★★ 감점 (개정 491 · 명령서 1-2 ⓑⓒ).  ★ 조용히 깎지 않는다 —
    #   목록에 딱지로 · 막대 옆에 「막대 합 − 감점 = 등급 점수」로 낸다
    penalty_won: int = 0          # ★ 상한을 먹인 뒤의 합 (음수)
    penalty_labels: list = field(default_factory=list)
    # ★★★★★ 09-02 마스터 확정 — ★ **가장 큰 감점 하나**를 겉에 낸다.
    #   ★ 「감점 -40 ★ (렌트 이력 -22)」 — ★ 무엇 때문인지 접힌 채로 보인다
    penalty_top: str = ""
    # ★★★★★ 09-02 마스터 확정 — ★ 「★ 연식·거리에 ★ **셈을 함께** 낸다」
    #   ★ 「연식 2022-07 ★ (3년 2개월)」 · 「주행 139,571km ★ (연 4.4만)」
    #   ★ ★ **한 해에 얼마나 탔나**가 ★ 많이 탔는지를 가른다 —
    #   ★ ★ ★ 총 거리만으로는 모른다.  ★ 못 재면 ★ 빈 글자다 (지어내지 않는다)
    age_label: str = ""
    km_per_year_label: str = ""
    # ★ 상세 조회가 안 끝난 매물 — 등급 옆에 「잠정」 (STEP 97)
    provisional: bool = False
    # ★ 등급 문구 — 「제외」는 등급 문자가 아니다 (개정 433)
    grade_label: str = ""
    # ★ 색 점 (시안 .swatch).  원문은 이름만 준다 — 없으면 안 찍는다
    color_ext_hex: str | None = None
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
    # ★★ 제원 둘 (마스터 확정 08-24 · UI_REVIEW 10) — ★ **비교 화면에만** 쓴다.
    #   ★ 목록 카드에는 안 낸다 (S46-45).  ★ 축이 아니다 — 판정에 안 들어간다
    #   ★ 원문에 없으면 None — ★ 0 이 아니다.  ★ 화면에는 「—」
    spec_fuel_economy_kmpl: float | None = None
    spec_seats: int | None = None
    # ★★ 「3곳」 배지 — ★ 같은 차가 올라간 사이트의 수 (v3_listings_시안).
    #   ★ 1 이면 겹친 것이 없다 — ★ 배지를 안 낸다
    site_count: int = 1
    # ★★ 템플릿은 ★ `>` 비교를 못 한다 (V11-104) — ★ 판단은 여기서 한다.
    #   ★ 실측 08-24 — ★ `{% if r.site_count > 1 %}` 가 ★ 늘 참이라 ★ 「1곳」이 다 나왔다
    multi_site: bool = False
    # ★★ 값 폭 (가이드 지시 08-24) — ★ 「3곳 · 2,890~3,260만」.
    #   ★ 곳 수만 내면 ★ 얼마나 벌어졌는지 모른다
    dupe_low_won: int | None = None
    dupe_high_won: int | None = None
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
    # ★★ 08-26 — ★ 시안의 「시세보다 400만 싸다」다 (`v4m_listings_시안` · S46-98).
    #   ★ 값이 아니라 ★ **말**이다 — ★ 「−400만」은 사람이 한 번 더 읽어야 한다.
    #   ★ 판단을 템플릿에 두지 않는다 — ★ 여기서 만들어 넘긴다
    market_gap_label: str | None = None
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
    # ★★★ 08-29 (마스터 3번) — ★ 팔린 것을 목록에 두고 ★ 딱지만 단다
    sold: bool = False
    sold_label: str | None = None

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
    # ★★ 실측 08-24 — ★ 기본값이 `"encar"` 라 ★ **주석과 정반대**였다.
    #   ★ ★ 그래서 ★ `/listings` 가 ★ 엔카 3,259건만 냈다 (전부는 5,319건).
    #     ★ ★ 매물 2,060건이 ★ 받아 놓고도 ★ 화면에 안 나왔다
    #   ★ ★ `/detail/{id}` 가 ★ 엔카 아닌 매물에서 ★ 404 이던 것도 ★ 같은 뿌리다 —
    #     ★ 상세가 이 거르개를 그대로 쓴다 (`view_detail`)
    site: str | None = None
    # 판매 유형 — 「K카 직영만」 (sites.json sell_type_labels)
    sell_type: str | None = None
    target_key: str | None = None
    grade: str | None = None
    # ★★ 옵션 이름으로 거른다 (마스터 확정 08-25 · B).
    #   ★ 엔카는 숫자 코드만 준다 — ★ 이름을 주는 사이트에서만 걸린다.
    #   ★ ★ 축이 아니라 거르개다 (HDA 축 폐기와 어긋나지 않는다)
    option_name: str | None = None
    # ★ 묶음으로 건다 — ★ 이름이 사이트마다 다르다 (마스터 확정 08-25)
    option_group: str | None = None
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
    # ★ 성능부 ↔ 보험이 어긋난 것만 (V3-50).  「사람이 그것만 따로 볼 수 있게」
    mismatch: bool = False
    # ★ 리스·렌트 (개정 420).  기본은 숨김 — 마스터 「리스는 목록에서 아예 뺀다」
    #   ★ 지우는 것이 아니다.  ?lease=1 로 볼 수 있다
    lease: bool = False
    # ★★ 관문 배제 (개정 433).  기본은 숨김 — 「기본 목록에 안 나온다」
    #   ★ 지우는 것이 아니다.  ?excluded=1 로 볼 수 있다 (리스와 같은 방식)
    #   ★ 배제는 등급이 아니다 — 사유를 함께 낸다 (리스 · 골격 사고 · 침수 · 전손)
    excluded: bool = False
    # ★★ 개정 427 — 필터는 반대로 두껍게 (STEP 97).
    #   ★ 실측 — 보배드림 15종(옵션 79) · KB차차차 16종 · K카 7종 · 우리 5개.
    #     사이트는 복잡함을 필터에 몰아넣고 목록을 단순히 둔다.  우리는 반대였다
    #   칩 7 — 차종·가격·주행·외장색·내장색·등급·리스제외
    # ★ 매물 하나만 집을 때 (개정 427 상세).  ★ 전건을 읽고 파이썬에서
    #   고르면 쿼리도 메모리도 통째로 든다 (실측 08-21 — V11-34 29쿼리)
    listing_id: int | None = None
    # ★ 여러 매물을 집을 때 (비교).  ★ 전건을 읽고 파이썬에서 고르면
    #   **첫 쪽 50건 밖의 매물이 조용히 빠진다** (실측 08-21 — 비교가 빈 표였다)
    listing_ids: tuple = ()
    color_ext: str | None = None
    color_int: str | None = None
    #   ＋ 12 — 연식·옵션·트림·연료·사이트·정직도·경과일·가격변동
    #           ·보증잔여·지역·★점수 필터·정렬
    fuel: str | None = None
    trim: str | None = None
    option_min: int | None = None       # 선택 옵션 종수 하한
    honesty_min: float | None = None    # 딜러 정직도 하한
    days_max: int | None = None         # 경과일 상한
    price_dropped: bool = False         # 가격이 내린 것만
    # ★★ 08-28 (#11) — 「확인 못 한 것도 함께 보기」.  ★ 화면에 체크상자는
    #   있는데 ★ 이 칸이 없어 ★ 눌러도 아무 일이 없었다 (listings.html 78행).
    #   ★ 등급 거르개를 걸면 아직 등급이 안 매겨진 매물이 함께 빠진다 —
    #     ★ 그것까지 보겠다는 뜻이다
    unknown_too: bool = False
    # ★★★ 08-29 (마스터 3번) — ★ 거르개 「뺀 것」의 ★ 「팔린 것 숨기기」.
    #   ★ 기본은 ★ **안 숨긴다** — ★ 두고 딱지만 다는 것이 정본이다
    # ★ 08-30 (30-2) — ★ 뜻이 뒤집혔다.  ★ 기본이 「안 보임」이고
    #   ★ 이것을 켜면 ★ 팔린 것·계약 중을 ★ **함께** 본다
    with_sold: bool = False
    warranty_month_min: int | None = None
    region: str | None = None
    # ★★ 점수 필터 — 화면의 막대를 그대로 조건으로 쓴다 (V11-164).
    #   ★ SQL 로 건다.  밖에서 걸면 건수가 어긋난다 (실측 v189 — 집계 66ms)
    score_value_min: int | None = None
    score_car_min: int | None = None
    score_warranty_min: int | None = None
    score_taste_min: int | None = None
    # 차종 · 가격대 (개정 420).  ★ 차를 사는 사람이 제일 먼저 쓰는 조건이다
    model: str | None = None
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
    # ★ 내렸다 다시 올린 것은 그 자체가 정보다 (V7-14 · 개정 355).
    #   묶되 「N번 재등록」을 낸다.  값이 바뀌었으면 함께 낸다
    relist_times: int = 0
    relist_low_won: int | None = None
    relist_high_won: int | None = None
    # ★★ 「지켜보는 곳」 셋 (명령서 1-7 · UI_REVIEW 14-4 · v3_watch_시안).
    #   ★ ① 담은 뒤 무엇이 바뀌었나 — ★ 「담을 때 3,260만 → 지금 2,990만」
    #   ★ ② 바뀐 것이 위로 · ★ ③ 담은 날 — 「8월 17일부터 지켜봄 · 7일째」
    #   ★★ 팔린 차도 ★ 지우지 않는다 — ★ 「팔렸다」로 남긴다
    price_at_add_won: int | None = None
    price_delta_won: int | None = None      # ★ 음수면 내렸다
    days_watched: int = 0
    gone: bool = False
    gone_at: str | None = None
    # ★ 담은 뒤 값이 바뀌었거나 팔렸는가 — ★ 이것이 위로 간다
    changed: bool = False
    # ★★ v4m 관심 시안 (마스터 확정 08-25) — ★ 카드 맨 앞 줄과 ★ 시세차 줄.
    #   ★★ 화면이 계산하지 않는다 — ★ 틀은 `>` 비교를 못 한다 (V11-104).
    #     ★ 실측 08-24 — ★ 그것을 잊어 ★ 「1곳」이 전건 나왔다
    #   ★ chg_cls  dn 내렸다 · up 올랐다 · gone 팔렸다 · same 그대로
    chg_cls: str = "same"
    chg_text: str = ""
    # ★ 시세차 한 줄 — ★ 「시세보다 400만 싸다」.  ★ 표본이 없으면 그것을 적는다
    gap_cls: str = "dim"
    gap_text: str = ""


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
    # ★★ 1절 「오늘」 (v3_dashboard_시안) — ★ 넷을 한 줄로 낸다.
    #   ★ 새로 뜬 것 · 값 내린 것 · 사라진 것 · 마지막 재판정
    new_today: int = 0
    dropped_today: int = 0
    gone_today: int = 0
    last_recalc_at: str | None = None
    steps: list = field(default_factory=list)
    # ★★ 개정 427 — 현황이 시세를 흡수한다.  차종별 사분위표가 여기로 온다
    #   ★ /market 화면은 안 지웠다 — 관리로 내렸다
    market_rows: list = field(default_factory=list)
    # ★★ 개정 427 — 사라짐 목록 · 진행률 (STEP 95)
    #   ★ gone 을 「팔렸다」로 적지 않는다 — 목록에서 사라진 것이다 (V6-06)
    gone_rows: list = field(default_factory=list)
    progress: dict = field(default_factory=dict)


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
    # ★★ 개정 427 — 한 줄 결론.  「A는 취향이 낫고 B는 값이 낫습니다」
    #   ★ 표를 눈으로 훑게 두지 않는다.  ★ 무엇이 갈랐는지를 말로 쓴다
    conclusion: str = ""


@dataclass(frozen=True)
class TrackPair:
    """★ 한 대의 차가 ★ 여러 사이트에 올라간 것 (명령서 1-2 · v3_track_시안).

    ★★ 합치지 않는다.  ★ 갈린 것을 ★ 갈린 채로 보여 준다 (마스터 확정 08-24)
    ★ 짝이 없는 매물은 ★ 여기 안 낸다 — ★ 견주는 자리다
    """

    plate_hash: str
    target_label: str
    trim: str
    # ★ 칸마다 이름이 있다 — badge · listing_id · price_won · grade · earned · misses
    #   ★★ 08-26 — ★ 전에는 튜플이었다.  ★ 틀이 `{{ s.0 }}` 를 못 읽어
    #     ★ ★ 화면이 ★ **빈 칸으로 나갔다**.  ★ 이름으로 짚는다
    sites: tuple
    site_count: int
    low_won: int
    high_won: int
    gap_won: int
    gap_pct: float
    grades: tuple
    # ★ 등급이 갈렸는가 · 사고 판정이 갈렸는가
    grade_split: bool = False
    accident_split: bool = False
    # ★★★★★ 09-02 — ★ 시안 `v4m_track_시안.html` 이 ★ **사진 자리**를 둔다
    #   (`.v4-thumbwrap` · `.v4-thumb`).  ★ 우리 화면에 없었다 (`S46-98`).
    #   ★ ★ 없으면 ★ 「사진」이라 적은 빈 자리다 — ★ 지어내지 않는다
    photo_url: str | None = None
    # ★★ 틀은 `>=` 비교를 못 한다 (V11-104) — ★ 판단은 build 가 한다.
    #   ★ 30% 넘으면 ★ 짝짓기가 틀렸을 자리다 (v4m 추적 시안)
    big_gap: bool = False
    gap_cls: str = "dim"


@dataclass(frozen=True)
class TrackView:
    """추적 — ★ 절 셋 (v3_track_시안).

    ★ 1 값이 크게 갈린 것 · 2 등급이 갈린 것 · 3 사고 판정이 갈린 것
    ★★ 분모는 ★ 910 으로 같다 (마스터 정정 08-24) — ★ 갈리는 것은 earned 다
    """

    pairs: list           # 값 갈림 (차액 큰 순)
    grade_split: list     # 등급 갈림
    accident_split: list  # 사고 판정 갈림
    total_pairs: int = 0
    big_gap: int = 0      # 값이 30% 넘게 갈린 것
    two_step: int = 0     # 등급이 두 칸 갈린 것
    order: str = "gap"
    # ★★ 틀은 `==` 비교를 못 한다 (V11-104) — ★ 「지금 눌린 것」을 여기서 정한다.
    #   ★ 실측 08-25 — ★ `{% if t.order == 'gap' %}` 이 ★ 화면에 글자로 샜다
    #   ★ 각 칸은 {key · label · on}
    orders: list = field(default_factory=list)
    # ★★ 한 쪽에 30장 (마스터 확정 08-26 · `UI_REVIEW` 16장 · S46-74).
    #   ★ 「화면마다 다르면 헷갈린다」 — ★ 목록·관심·추적·미판정이 같은 수다
    #   ★★ 자른 것을 ★ 합으로 내지 않는다 — ★ 「이게 전부」로 읽힌다 (검토 17)
    page_rows: int = 30
    cut: bool = False       # ★ 30장을 넘어 잘렸는가


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
class SoldBin:
    """시세 대비 한 칸 — ★ 「어떤 가격일 때 잘 팔렸나」 (UI_REVIEW 30-3)."""

    label: str          # 「−10% 아래 (싸다)」
    sold_n: int         # 그 칸에서 팔린 수
    days_avg: float | None   # 평균 며칠.  ★ 표본이 모자라면 None
    enough: bool        # ★ 표본 다섯 이상인가 (f-table 과 같은 잣대)
    # ★★★★ 08-30 — ★ `sold_n` 과 ★ 「평균 며칠」의 표본이 **다르다.**
    #   ★ 며칠은 ★ `first_seen` 과 `gone_at` 이 ★ **둘 다 있어야** 센다.
    #   ★ 실측 08-30 — ★ 칸에 드는 것 499건 중 ★ **107건만** 셀 수 있다.
    #   ★ ★ 그것을 안 적으면 ★ 「136건이 평균 5일」로 읽힌다 — ★ 거짓이다.
    #   ★ ★ 이 프로젝트가 막는 「선언과 실제의 괴리」가 ★ 바로 그것이다
    days_n: int = 0     # ★ 평균을 낸 표본 수


@dataclass(frozen=True)
class SoldRow:
    """팔린 차 한 대."""

    listing_id: int
    target_key: str | None
    site: str
    site_badge: str
    # ★★★★★ 09-02 — ★ 판매지역 (`S46-225`).  ★ 기본값을 주면 뒤 칸이 다 그래야 한다
    region_label: str | None
    title: str
    spec: str                    # 「2022-06 · 48,210km · 흰색 · 가솔린」
    price_won: int | None        # 마지막에 본 값
    price_first_won: int | None  # 처음 본 값 — ★ price_history 가 있어야 낸다
    photo_url: str | None
    first_seen: str | None
    gone_at: str | None
    days: int | None             # gone_at − first_seen
    gap_pct: float | None        # 시세 대비 몇 %
    # ★★ 「사이트가 판매완료라 말한 것」과 ★ 「그냥 사라진 것」을 가른다 (30-3 금지)
    said_sold: bool
    said_label: str | None       # 「판매완료」 · 「예약중」 · None
    detail_url: str | None


@dataclass(frozen=True)
class SoldView:
    """팔린 차 (`/sold` · UI_REVIEW 30장 · 마스터 확정 08-29 요구 134).

    ★ 마스터 — 「★ 별도의 화면 메뉴를 만들어서 ★ 판매 완료된 차에 대해서는
      ★ 목록 아래에서 정리했으면 좋겠어.  ★ 그래서 ★ **어떠한 가격일 때
      ★ 잘 팔렸는지 통계**를 내놨으면」
    ★ 목록에서 사라진 것이 ★ **다 팔린 것은 아니다** — ★ `said_sold` 로 가른다
    """

    rows: list
    total: int                   # 팔린 것 전체
    shown: int                   # 이번 쪽에 낸 것
    bins: list                   # SoldBin — 시세 대비 네 칸
    bins_for: str | None         # 「G80_25T · 2022년식」 — 무엇에 대한 통계인가
    bins_note: str | None        # 표본이 모자랄 때 적는 말
    # ★ 아직 못 내는 것 — ★ 화면에 적는다 (지어내지 않는다)
    missing: list = field(default_factory=list)


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
    # ★★ 「범위 밖」 — ★ 아는 차인데 ★ 갈래(연료·트림)가 다른 것 (마스터 결정 「제외해」).
    #   ★ 묻는 자리가 아니다 — ★ 건수만 내고 ★ 접어 둔다 (`UI_REVIEW` 9a)
    out_of_scope: list = field(default_factory=list)
    out_of_scope_total: int = 0
    # ★ 3절 — ★ 등록부 미분류.  ★ 이것은 ★ 판정을 막는다 (V4-11)
    field_unclassified: int = 0
    # ★★ 세 줄 (UI_REVIEW 14-7 · 개정 724) — ★ 「미분류」가 ★ 두 뜻으로 읽혔다.
    #   ★ ① 여쭐 것 — ★ 마스터께서 정하실 것 (`new`)
    #   ★ ② 접어 둔 것 (`out_of_scope`) · ★ ③ 팔린 것 (`gone`)
    #   ★★ ★ 여쭐 것만 맨 위에 굵게 — ★ 나머지 둘은 건수만 · 접어 둔다
    ask_count: int = 0
    folded_count: int = 0
    gone_count: int = 0


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


# ★★★★★ 09-01 (규격 `docs/RECOMMEND_SCREEN.md`) — ★ 추천 화면의 칸.
#   ★ 튜플이 아니라 ★ **이름 있는 칸**으로 낸다 — ★ 틀이 `{{ x.0 }}` 을 못 짚는다
#     (`web/template.py` `_step` — ★ 점 뒤는 늘 글자다.  08-26 실측)
@dataclass(frozen=True)
class RecommendAxis:
    axis: str
    label: str
    got: float
    full: float
    # ★ 시안 `.rc-ax.hi` — ★ 만점이면 노랗게 (틀은 `==` 를 못 한다 · V11-104)
    hi: bool = False


@dataclass(frozen=True)
class RecommendRow:
    listing_id: int
    target_label: str
    trim: str | None
    year_month: str | None
    mileage_km: int | None
    color_ext: str | None
    price_won: int | None
    site: str | None
    # ★ 등급은 ★ **보이기만** 한다 — ★ 세우는 데 안 쓴다 (규격 「금지」)
    grade: str | None
    got: float
    full: float
    # ★ 막대는 ★ **비율**을 그린다 (부록 G · A-3) — ★ 틀은 나눗셈을 못 한다
    pct: float
    axes: tuple
    # ★ 시안 `.v4-spec` — ★ 「2023-04 · 21,400km · 청색 / 검정색 계열 · 볼보셀렉트」
    spec: str = ""
    photo_url: str | None = None
    # ★ 시안 — ★ 「등급 C · **등급은 안 봅니다**」.  ★ 낮은 등급일 때만 덧붙인다
    ignored: bool = False
    # ★★★★★ 09-01 — ★ `V11-69` 「v1 이 가진 조작이 v2 에도 있음」.
    #   ★ 제가 시안대로 다시 만들면서 ★ **조작 다섯을 떨어뜨렸다** —
    #   ★ ★ ♡ · 미리보기 · 원문 링크 · 비교 담기 · 정렬.
    #   ★ ★ ★ 시안은 ★ **무엇을 보여 줄지**를 정한 것이지
    #     ★ ★ 「할 수 있던 일을 없애라」가 아니다 (개정 429 「값을 버리지 마라」)
    site_badge: str | None = None
    # ★★★★★ 09-02 — ★ 판매지역 (`S46-225`)
    region_label: str | None = None
    # ★★★★★ 09-02 마스터 확정 — ★ 연식·거리의 셈 (「3년 2개월」·「연 4.4만」)
    age_label: str = ""
    km_per_year_label: str = ""
    encar_url: str | None = None
    total_cost_won: int | None = None
    buy_estimated: bool = False


@dataclass(frozen=True)
class RecommendView:
    tab: str
    rows: list
    total: int
    axes: tuple
    full: float
    # ★ 시안 `.rc-head` — 「차종 13종 · N건 중」
    targets: int = 0
    # ★ 탭 2·3 — ★ 「아직 정하지 않았습니다」.  ★ 오류가 아니다 (규격 2장)
    empty_note: str | None = None
    # ★★★★★ 09-01 — ★ `V11-69` 정렬 드롭다운.  ★ 「지금 눌린 것」은 여기서 정한다
    #   ★ 틀은 `==` 를 못 한다 (V11-104)
    orders: tuple = ()
    # ★★★★★ 09-02 — ★ 시안 `.rc-models` — ★ **차종 고르개** (이름 ＋ 건수).
    #   ★ 건수 0 인 차종도 ★ 흐리게 남긴다 — ★ 「없다」가 아니라 「지금 재고가 없다」
    models: tuple = ()
    model: str | None = None
    # ★ 틀은 ★ `==` 를 못 한다 (`V11-104`) — ★ 머리말을 여기서 정한다
    title: str = ""
