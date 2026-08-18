# 10장. 활용 — 화면 (STEP 93–110)

## 10장 정의서

**v1 웹앱(Flask · 화면 10 + `/notready` = 11개)을 준용한다. 화면 구성은 유지하고 데이터 계약만 v2 규격으로 바꾼다.**

```
근거   app.py 1,750줄 · templates 11개.  실제 운영된 화면이다
방침   화면을 새로 설계하지 않는다.  같은 정보를 일관된 규격으로 표출한다
```

### 화면 목록 — v1 그대로

| # | 경로 | 이름 | 층 | STEP |
|:--:|---|---|:--:|:--:|
| 1 | `/` | 현황 (대시보드) | L3+L2 | 95 |
| 2 | `/recommend` | 후보 | L2 | 96 |
| 3 | `/listings` | 매물 | L2 | 97 |
| 4 | `/watch` | 관심 | **L1 요약 × N** | 11장 |
| 5 | `/compare` | 비교 | L1×N | 98 |
| 6 | `/dealers` | 딜러 | L2 | 99 |
| 7 | `/market` | 시세 | L2 | 100 |
| 8 | `/run` | 수집 | L3 | 101 |
| 9 | `/reports` | 리포트 | — | 102 |
| 10 | `/why/<listing_id>` | 판정 근거 | **L1** | 103 |

```
/notready   데이터 미비 시 안내.  판정 결과를 빈 값으로 보여주지 않는다
```

### 구조체 — 화면 전용

```python
@dataclass(frozen=True)
class ListingRow:              # /listings · /recommend 목록 1행
    listing_id: str
    grade: str                 # S~E · NOT_RATED
    rank: int | None           # NOT_RATED 는 None
    target_label: str
    trim: str | None
    year_month: str | None
    mileage_km: int | None
    color_ext: str | None
    color_int: str | None
    axis_chips: list[AxisChip] # HUD · 보증 · 사고 · 보험 · 렌트
    price_won: int              # 표시가
    total_cost_won: int | None  # 실구매가 = 표시가 + 취득 부대비용
    loan_principal_won: int | None   # 실구매가 − 선납금
    monthly_won: int | None     # 월 납입 (48개월 5.5%)
    price_gap_pct: float | None
    price_change_cnt: int
    days_on_market: int | None
    dealer_shop: str | None     # 상호.  개인 실명(dealer_name)은 쓰지 않는다
    dealer_honesty: float | None
    note: str | None
    versions: VersionStamp

@dataclass(frozen=True)
class AxisChip:                # 목록의 축 요약 칩
    axis: str
    label: str                 # 「있음」·「없음」·「해당 없음」·「미확인」
    tone: str                  # good · bad · muted · unknown
    filter_url: str            # 그 값으로 목록을 거르는 링크
```

**`AxisChip.label` 은 9장 STEP 91 값 표시 대조표를 따른다.**
**목록과 상세가 다른 문구를 쓰면 안 된다.**

### 함수

| 이름 | 입력 | 출력 |
|---|---|---|
| `view_dashboard` | `calc_version` | `DashboardView` |
| `view_listings` | `ListingFilter` | `list[ListingRow]` |
| `view_recommend` | `ListingFilter` | `list[ListingRow]` |
| `view_why` | `listing_id, calc_version` | `ScoreView` |
| `view_compare` | `list[listing_id]` | `CompareView` |
| `view_market` | `target_key` | `MarketView` |
| `view_dealers` | `filter` | `list[DealerRow]` |
| `view_run` | `run_id \| None` | `RunReport` |

### 화면 구조체 — 하위

```python
@dataclass(frozen=True)
class ListingFilter:
    site: str
    target_key: str | None
    grade: str | None
    axis: str | None          # Component 이름 'spec.hud'
    bucket: str | None        # '1' · '0' · 'na' · 'unknown'
    order: str                # rank · grade · price · price_desc · mileage · year · new · dom
    show_all: bool
    page: int
    calc_version: str

@dataclass(frozen=True)
class DashboardView:
    meta: ReportMeta
    finalists: list[ListingRow]
    target_stats: list[TargetStat]        # 차종 · 전체 · S~E · 1순위 · A중앙가
    relax_sim: list[RelaxRow]             # 조건 완화 시뮬레이션
    axis_shortfall: list[AxisStat]        # 축별 미달 건수
    market: list[MarketRow]
    recent_changes: list[ChangeRow]
    watch_summary: list[ListingRow]
    attention: list[AttentionItem]        # pending · unclassified · warn · 미확정
    recent_runs: list[StepReport]

@dataclass(frozen=True)
class CompareView:
    rows: list[ListingRow]
    axes: list[str]                       # 17 Component
    cells: dict[tuple[str,str], AxisView] # (listing_id, axis) → AxisView
    denominator_mismatch: bool            # 분모가 다르면 경고
    version_mismatch: bool                # 버전이 다르면 비교 불가

@dataclass(frozen=True)
class MarketView:
    target_key: str
    rows: list[MarketRow]                 # 날짜 · 매물 · 적격 · 최저 · 25% · 중앙 · 75% · 최고
    coefficient_history: list[CoefficientChange]
    curve: list[tuple[int,float]]         # 경과년 → 잔가율

@dataclass(frozen=True)
class DealerRow:
    dealer_id: str
    dealer_shop: str | None               # 상호 (partnership.dealer.firm.name)
    # dealer_name(개인 실명)은 core_dealer_pii 에 있다.  화면에 쓰지 않는다
    dealer_region: str | None             # 지역 (OfficeCityState)
    years: int | None
    quadrant: str
    honesty_score: float | None
    sample_sufficient: bool
    volume: int
    sold_total: int | None
    sold_1y: int | None
```

**`AttentionItem` · `TargetStat` · `RelaxRow` · `MarketRow` · `ChangeRow` 도 같은 방식으로 정의한다.**
**문서에 1회만 등장하는 타입 이름을 남기지 않는다** (0장 STEP 5.3).

```
금지   화면 함수가 판정·채점을 계산하는 것 (9장)
허용   표시용 파생 — 순위 · 백분위 · 색상 톤 · 필터 링크
```

---

## STEP 93 — 화면 공통 규칙

### 전 화면 공통 표시

```
필수   Account (role · display_name).  비로그인은 anonymous
      화면이 Account 를 받아 역할별로 분기한다 (13장 STEP 126)
      금지 — 화면 숨김만으로 권한을 대신하는 것.  서버가 막는다
필수   VersionStamp (parse · dict · calc · coefficient)
필수   데이터 기준 시각 (마지막 수집 시각)
필수   미확정 항목이 판정에 쓰였으면 표시
```

### 값 표기 — 9장 STEP 91 을 그대로 따른다

| 내부 | 화면 | 톤 |
|---|---|---|
| `1` | 있음 | good |
| `0` | 없음 | bad |
| `-1` + `excluded` | **해당 없음** | muted |
| `NULL` + `excluded` | **미확인** | unknown |
| `NOT_RATED` | **평가 불가** | muted |
| `gone` | **목록에서 사라짐** | muted |

```
금지   목록에서는 「—」, 상세에서는 「없음」처럼 화면마다 다르게 쓰는 것
필수   AxisChip.label 하나로 전 화면이 같은 문구를 쓴다
```

### 필터 파라미터 — 전 화면 공통

```
target      차종
grade       등급 (S·A·B·C·D·E·NOT_RATED)
axis        축 이름 (Component 단위.  'spec.hud')
bucket      그 축의 값 (1 · 0 · na · unknown)
order       rank · grade · price · price_desc · monthly · total_cost · mileage · year · new · dom
all         전체 표시 (기본은 추천 대상만)
```

**v1 이 쓰던 파라미터 이름을 유지한다.** 북마크·링크가 깨지지 않는다.

```
필수   axis 값은 Component 이름을 쓴다.  화면 라벨이 아니다
      /listings?axis=spec.hud&bucket=1
```

---

## STEP 94 — 화면 ↔ 리포트 층 대응

```
L1 매물   /why/<id>              9장 STEP 90 L1 항목 전건
L2 차종   /listings · /recommend · /market · /dealers
L3 실행   /run · / (현황 일부)
```

**화면이 리포트보다 적게 보여주는 것은 되지만, 더 계산하면 안 된다.**

---

## STEP 95 — `/` 현황

**v1 블록 구성을 유지한다.**

| 블록 | 내용 | 출처 |
|---|---|---|
| 최종후보 | 확정 후보 카드 | `watch_candidate` (11장) |
| 조건 충족 현황 | 차종별 전체 · A · B · C · D · E · 1순위 · A중앙가 | L2 |
| **조건 완화 시뮬레이션** | 조건을 낮추면 몇 건이 되는가 | L2 파생 |
| 축별 미달 건수 | 어느 축에서 떨어지는가 | L2 |
| 차종별 시세 | 중앙값 · 계수 | L2 |
| 최근 변동 | 신규 · 소멸 · 가격 변경 | `core_listing_change` |
| 관심매물 | 요약 | 11장 |
| **확인 필요** | 미확정 · `pending` · `unclassified` · 검증 warn | **L3** |
| 수집 로그 | 최근 실행 | L3 |

```
★ 「확인 필요」 블록을 v2 에서 강화한다
   사전 pending · 등록부 unclassified · 검증 warn · 미확정 항목
   → v1 은 이런 것이 조용히 지나갔다.  첫 화면에 띄운다
```

---

## STEP 96 — `/recommend` 후보

```
대상   추천 순위 1~3 · 등급 A 이상
정렬   추천 순위 → 점수
제외   E · NOT_RATED (목록 하단에 별도 표시)
```

**「왜 이 매물이 후보인가」를 한 줄로 낸다.**

```
예   A · 1순위 · 기대가 대비 −11% · 무사고 · 비렌트 · 보증 29개월
근거  ScoreView.axes 에서 상위 기여 축 3개를 뽑는다.  새로 계산하지 않는다
```

---

## STEP 97 — `/listings` 매물

### 컬럼 — v1 유지

```
등급 · 순위 · 차종 · 트림 · 연식 · 주행 · 외장 · 내장
HUD · HDA · 선루프 · 보증 · 사고 · 보험 · 렌트
가격 · 실구매가 · 월 납입 · 시세차 · 변동 · 경과
딜러 · 정직도 · 경고 · 비고
```

### ★ 가격 옆에 할부가를 함께 낸다

```
표시 형식   3,470만  (현금 1,500만 · 월 51.5만)

           3,470만     표시가
           현금 1,500만  초기 부담.  취득 부대비용 포함.  고정
           월 51.5만    할부 원금(표시가 − 차값 선납)을 48개월 5.5% 로
```

```
필수   세 값을 한 셀에 함께 낸다.  목록에서 바로 비교되게
필수   월 납입에 「추정」 표시.  이율·조건이 실제 승인과 다를 수 있다
필수   표시가 + 부대비용 ≤ 선납금 이면 「전액 현금」
       ★ 부대비용 = 취득세 · 등록비 · 사이트 수수료 (개정 353 sites.json)
~~필수   부대비용 > 선납금 이면 부족액을 표시한다~~ ★ 폐기 — 개정 400

★★ 08-19 마스터 확정 — VW-027
「선납금은 1500만원으로 고정했어.  그 안에 취득세 등록비 사이트 수수료 포함이야.
 따라 이 기능은 필요없어.  1500만원에 모두 해결되면 전액 현금이 되겠지.
 1500은 사정을 봐서 일괄로 바꾸는 기준값으로」

필수 [마스터]   1,500만은 **총액 상한**이다.  그 안에 부대비용이 들어간다
필수 [마스터]   화면에는 「전액 현금」인가 아닌가 둘뿐이다.  ★ 부족액을 내지 않는다
필수 [마스터]   1,500만은 **일괄로 바꾸는 기준값**이다 — config.finance.cash_limit 하나
금지 [마스터]   부족액 · 모자란 금액 · 「380만 부족」 같은 표시
검산            V11-151  부족액 문구가 화면에 있는가 (있으면 실패)
                V11-152  cash_limit 이 config 한 곳에서만 읽히는가
금지   표시가만 보여주는 것
      → 취득 부대비용이 차종·가격대마다 달라 순위가 뒤집힐 수 있다
근거   예산은 표시가가 아니라 월 납입으로 관리한다 (마스터 확정)
```

### 경고 표시 — 목록에서 바로 보인다

```
경고 배지   block  붉은 배지 · warn  주황 배지 · info  회색 점
확인 처리   배지 옆 체크.  acknowledged=1 이면 흐리게
필터       warning · ack 파라미터로 거를 수 있다
금지       경고를 이유로 목록에서 빼는 것
```

### v2 변경점

| 항목 | v1 | v2 |
|---|---|---|
| `HUD` 칩 | 있음/없음 | **있음 · 없음 · 해당 없음 · 미확인** 4종 |
| 축 칩 | HUD 만 | **HUD · HDA · 선루프** 3개로 확장 (사양 60점) |
| 정렬 `rank` | 등급 우선 | `NOT_RATED` 는 순위 없음 → 하단 |
| 필터 `axis` | 화면 라벨 | **Component 이름** (`spec.hud`) |
| 버전 | 없음 | **VersionStamp 표시** |

```
필수   시세차는 기대가 대비 % 다.  절대 금액과 함께 낸다
필수   「월」은 금융 계산값이며 「추정」 표시 (9장 금융)
```

---

## STEP 98 — `/compare` 비교

```
대상   선택 매물 2~5건
행     항목 · 열   매물
고정   첫 열 고정 (v1 sticky 유지)
```

### 비교 항목

```
표시가 · 실구매가 · 월 납입 · 기대가 · 시세차
등급 · 총점 / 분모 · 축별 17 Component
연식 · 주행 · 트림 · 색상
사고 · 보험 · 렌트 · 보증
딜러 · 정직도
버전
```

```
★ 분모가 다른 매물을 나란히 놓을 때 경고를 낸다
   「이 두 매물은 수집된 항목이 달라 총점을 직접 비교할 수 없습니다」
   근거   8장 STEP 89 · 7장 STEP 83
필수   버전이 다르면 비교 불가로 막는다 (9장 STEP 91)
```

---

## STEP 99 — `/dealers` 딜러

```
정직도 × 물량   산점도 (v1 4분면 유지)
목록           딜러 · 상호 · 지역 · 경력 · 분면 · 정직도 · 물량 · 누적판매 · 최근1년
```

```
★ 정직도 산출 근거를 화면에 낸다
   v1 은 honesty_score 만 있고 계산 근거가 화면에 없었다
필수   표본 부족(sample_sufficient=False) 딜러는 점수를 흐리게 표시
      적은 표본으로 만든 점수를 확정처럼 보여주지 않는다
```

**딜러 지역은 `dealer_region` 이다** (2장 STEP 19 — v1 은 `dealer_shop` 에 지역이 들어가 있었다).

---

## STEP 100 — `/market` 시세

```
차종별 시세   날짜 · 매물 · 적격 · 최저 · 25% · 중앙 · 75% · 최고
```

### v2 추가

```
계수 이력    coefficient_history 를 함께 표시
            언제 얼마로 바뀌었고 표본이 몇 건이었는가
기대가 곡선   실측 잔가율 (7장 STEP 70) 과 실매물 분포를 겹쳐 표시
```

**「시세가 변했나」와 「계수가 변했나」를 구분해 보여준다** (6장 STEP 65).

---

## STEP 101 — `/run` 수집

```
수집 실행 · 진행 로그 · 알림 · 최근 수집
최근 수집 표   날짜 · 상태 · 수집 · 신규 · 소진 · 시작 · 종료
```

### v2 추가 — L3 리포트를 그대로 붙인다

```
StepReport      expected · requested · ok · empty · not_found · error
               not_requested · rejected · halted
검증 V1~V5      code · passed · severity · samples
전일 GAP        increase · decrease · change · anomaly
```

```
★ halted 실행은 붉게 표시하고 halt_reason 을 낸다
   v1 은 실패가 로그에만 남아 화면에서 보이지 않았다
```

---

## STEP 102 — `/reports` 리포트

```
파일 · 종류 · 크기 · 생성 · 내려받기
```

```
필수   파일명 규격 {run_id}_{layer}_{target|ALL}_{calc_version}.{ext} 를 파싱해
      층 · 차종 · 버전 컬럼으로 분해해 보여준다
```

---

## STEP 103 — `/why` 판정 근거 ★ 핵심 화면

**v1 의 9개 블록을 유지하고 v2 규격으로 채운다.**

| 블록 | v1 | v2 |
|---|---|---|
| **무엇을 조회했는가** | 미조회 항목 경고 | 엔드포인트 4개 × `*_status` 5종 · `not_requested` 강조 |
| **축별 판정** | 축 목록 | **17 Component × (값 · 획득/배점 · `source` · `prio` · `excluded`)** |
| 왜 N순위인가 | 순위 근거 | 상위 기여 축 3개 + 감점 축 3개 |
| 주요 옵션 | 옵션 목록 | `options.standard` + `choice` + 카탈로그 이름 |
| 시세 위치 | 백분위 | 기대가 · 계수 · 구간 점수 |
| 금융 | 할부 계산 | 실구매가 내역 · 선납 1,500만 · 할부 원금 · 월 납입 · 총 이자 |
| 월 총액 | 유지비 | 자동차세 · 보험 · 유류 · 정비 (**추정 표시**) |
| 자동차이력정보 | 이력 | 사고 `type` 1·2/3 구분 · 랭크별 손상 |
| 참고 자료 | 링크 | 원문 · 점검부 · 이력 |
| 플래그 | 상태 | E등급 사유 · 미확정 항목 |

```
★ 「축별 판정」이 이 화면의 핵심이다
   값만 보여주면 v1 과 같아진다.  source 와 prio 를 반드시 낸다

예   HUD    20/20   값 1     installed(2)
    HDA    20/20   값 2     spec_table(1)
    선루프    0/20   값 0     installed(2)    판매글에는 있으나 실장착 없음
    틴팅     —/5    미확인   —(—)           분모 제외
```

```
★ 「무엇을 조회했는가」에 not_requested 가 있으면
   「그 축은 판정할 수 없습니다」를 그대로 유지한다.  v1 의 좋은 설계다
```

---

## STEP 103a — `/dealers` · 경고 표시

```
/why 에 「거래 신뢰도」 블록을 추가한다
```

| 항목 | 내용 |
|---|---|
| 딜러 | 상호 · 지역 · 경력 · 누적판매 · 인증 |
| 신뢰도 | `trust_score` 또는 「표본 부족」 · 4분면 |
| 행태 | 재등록률 · 가격인상률 · 변동성 (각각 나쁜 방향 표시) |
| **경고 신호** | 감지된 신호 목록 + `evidence` |
| 판단 | 「차량 점수 A · 거래 위험 있음」처럼 **두 축을 나란히** |

```
필수   차량 점수와 거래 신뢰도를 한 숫자로 합치지 않는다
      좋은 차를 나쁜 딜러가 팔 수도, 그 반대일 수도 있다
```

---

## STEP 103b — 비중 조정 · 시뮬레이션 ★

**바꿀 수 있는 것과, 바꿔도 되는지 판단하는 것은 다르다.**

### 조정 대상

```
config/scoring.json    축·성분 배점 · 등급컷
config/dealer_trust.json  딜러 지표 가중치
```

### ★ 조정 전 미리보기

```
입력   변경할 배점
출력   현재 vs 변경 후를 나란히
```

| 비교 항목 | 내용 |
|---|---|
| 등급 분포 | S·A·B·C·D·E 각 몇 건에서 몇 건으로 |
| 순위 변동 | 상위 20건 중 몇 건이 바뀌는가 |
| 진입·이탈 | 새로 A 가 된 매물 · A 에서 빠진 매물 |
| 축 기여도 | 각 축이 총점 분산에 얼마나 기여하는가 |

```
필수   적용 전에 미리보기를 낸다.  적용 후 되돌리려면 재계산이 필요하다
필수   적용 시 calc_version 을 올린다.  이전 결과를 덮어쓰지 않는다 (3장 STEP 31)
표시   변동 원인을 「배점 변경」으로 분류해 알림에서 제외한다 (11장 STEP 115)
```

### 축 기여도 — 배점이 적정한지 보는 유일한 수단

```
기여도 = 그 축 점수의 표준편차 × 배점 ÷ 총점 표준편차
낮음   배점만 크고 순위를 못 가른다.  줄일 후보
높음   그 축 하나가 순위를 지배한다.  분산 확인 필요
```

**v1 에서 주행 30점이 전건 만점이라 기여도 0 이었다.**
**이 수치를 봤으면 바로 알았을 것이다.**

---

## STEP 104 — `/notready` 미비 안내

```
조건   그 차종·그 매물의 필수 데이터가 없다
표시   무엇이 없는지 · 언제 채워지는지
금지   빈 값으로 판정 결과를 보여주는 것
```

---

## STEP 105 — 화면 데이터 계약

**모든 화면은 `result_*` 와 `core_*` 만 읽는다.**
**모든 화면 함수는 `Account` 를 첫 인자로 받는다** (13장 STEP 126).

```
view_listings(account, filter)  ·  view_why(account, listing_id, calc_version)
개인화   watch_* 조회에 account_id 를 건다
판정     계정과 무관하다.  같은 차는 누가 봐도 같은 등급이다
```

```
금지   화면이 raw_response 를 직접 파싱
금지   화면이 dict_* 없이 코드를 해석
필수   Component 이름 · 등급 코드 · 상태값은 전부 상수로 공유
```

```
공유 상수   AXIS_LABELS · GRADE_LABELS · STATUS_LABELS · VALUE_LABELS
위치       config/labels.json
이유       화면마다 문구가 갈리면 같은 값이 다르게 보인다
```

---

## STEP 106 — 접근성 · 성능

```
목록      기본 200건 · 페이지네이션.  all=1 은 전체
정렬      DB 인덱스가 있는 컬럼만 (3장 STEP 39)
캐시      calc_version 단위.  버전이 바뀌면 무효화
```

---

## STEP 106a [규격] — 정렬 · 페이지네이션 ★

```
목적    목록이 항상 같은 순서로 나오게 한다
원천    result_score
입력    ListingFilter
출력    정렬된 목록 + 페이지 정보
값규칙  정렬 키가 같으면 listing_id 로 결정한다
근거    동점이 많다.  타이브레이커가 없으면 새로고침마다 순서가 바뀐다
금지    NOT_RATED 를 점수 순에 섞는 것
검산    V6-07  같은 조건으로 두 번 조회하면 같은 순서인가
```

### ★ 화면 층에 전역 상태를 두지 않는다 — 08-14

```
금지   함수 속성 · 모듈 전역에 요청별 값을 담는 것
근거   실측 08-14.  _row.calc_version = "c1" 로 두고 요청마다 덮어썼다
      단일 스레드라 지금은 안 터지지만 워커를 늘리면 즉시 섞인다
      「나중에 고친다」가 안 되는 부류다 — 증상이 재현되지 않는다
필수   인자로 넘긴다.  DTO 를 만들기 싫으면 인자를 늘린다
검산   V4-23  모듈 최상위 부작용 (이미 있다.  함수 속성 대입도 본다)
```

### ★ 목록 한 쪽에 쿼리 N 번을 돌지 않는다

```
필수   축 칩은 한 번에 받는다 — WHERE listing_id IN (...) AND axis IN (...)
금지   행마다 축마다 조회하는 것
근거   실측 08-14.  200행 × 5축 + 200 = 1,200 쿼리였다
상한   config.web.max_queries_per_request (기본 20)
검산   V11-34  화면이 요청당 쿼리 상한을 넘지 않는가
```

### ★ 정렬 SQL 에 4단을 다 넣는다 — 08-14

```
필수   ORDER BY 한 줄에 4단이 전부 들어간다
금지   score_total DESC 만 쓰는 것 — 분모가 다른 매물이 잘못 섞인다
금지   타이브레이커 없이 페이지를 나누는 것 — 같은 점수가 페이지마다 다르게 나온다
근거   실측 08-14. 구현이 s.score_total DESC 뿐이었고 V6-07 이 잡지 못했다
검산   V6-07 을 「두 번 조회」가 아니라 「ORDER BY 에 listing_id 가 있는가」로 본다
```

```sql
ORDER BY (CASE WHEN s.grade IN ('E','NOT_RATED') THEN 1 ELSE 0 END),
         (s.earned * 1.0 / NULLIF(s.denominator, 0)) DESC,
         l.price_current_won ASC,
         l.listing_id ASC
```

```
★ 정렬 축을 바꿔도 뒤 3단은 남는다
  「가격순」은 1단만 price 로 바뀌고 나머지는 그대로다
```

### 기본 정렬

```
1  E · NOT_RATED 를 뒤로 보낸다      등급이 아니라 「볼 수 없는 것」이다
2  score_total / denominator 내림차순  ★ 비율이다.  절대점수가 아니다
3  price_current_won 오름차순
4  listing_id 오름차순                타이브레이커
```

```
★ 2가 비율인 이유는 등급과 같다 (7장 STEP 84)
  절대점수로 정렬하면 분모가 큰 매물이 위로 몰린다
```

| `sort` 값 | 뜻 |
|---|---|
| `grade` (기본) | 위 4단계 |
| `price` | 표시가 오름차순 |
| `monthly` | 월 납입 오름차순 |
| `mileage` | 주행거리 오름차순 |
| `recent` | `first_seen` 내림차순 |

```
필수   전 정렬에 listing_id 타이브레이커를 붙인다
금지   표에 없는 sort 값을 받는 것.  기본값으로 되돌리고 경고를 낸다
```

### 페이지네이션

```
page      1부터.  0 이나 음수는 1 로
page_size config.web.rows_per_page (기본 200)
초과      마지막 페이지로 보낸다.  빈 페이지를 내지 않는다
표시      「N건 중 a~b」 · 이전 · 다음
```

```
필수   총 건수를 함께 낸다.  「몇 건인지 모르는 목록」을 내지 않는다
★★ 08-18 마스터 확정 — URL 로도 받는다

필수 [마스터]   page_size 를 URL 로 받는다
필수 [마스터]   상한 200.  넘으면 200 으로 자르고 화면에 알린다
필수 [기술]     상한은 config — config.view.page_size_max (기본 200)
금지 [기술]     상한 없이 받는 것.  큰 값이면 서버가 멈춘다
~~금지   page_size 를 URL 로 받는 것.  config 가 정한다~~
근거   큰 값이 들어오면 전건이 나온다
```

### URL 파라미터

```
/listings?target=G80_25T&grade=A&axis=spec.hud&bucket=1&sort=price&page=2
```

```
필수   전 파라미터가 없어도 화면이 뜬다.  기본값이 있다
필수   모르는 파라미터는 무시한다.  오류를 내지 않는다
금지   파라미터로 판정을 바꾸는 것.  거르기만 한다
```

---

## STEP 107 — 화면 검증

| 코드 | 검사 | 등급 |
|---|---|---|
| V6-01 | 전 화면에 `VersionStamp` 존재 | fatal |
| V6-02 | `AxisChip.label` 이 `VALUE_LABELS` 밖의 값을 쓰지 않음 | fatal |
| V6-03 | 화면이 `raw_*` 를 직접 조회하지 않음 | fatal |

```
★ 검사는 문자열 상수만 본다.  주석과 문서 서술은 대상이 아니다
  「raw_* 를 조회하지 않는다」는 금지 조항 자체가 잡히면
  금지를 문서화할수록 검사가 붉어진다
방법   AST 로 문자열 리터럴을 뽑고, SQL 인지 화면 문구인지 나눈다
근거   V4-13 과 같은 함정이다.  정상 코드에서 실패가 나면 검사를 끄게 된다
```
| V6-04 | `NOT_RATED` 에 순위가 부여되지 않음 | fatal |
| V6-05 | 분모가 다른 매물 비교 시 경고 표시 | fatal |
| V6-06 | `gone` 을 「판매됨」으로 표기하지 않음 | fatal |
| V6-07 | 같은 조건 재조회 시 순서가 같음 (타이브레이커) | fatal |

### 파일 출력 (9장 STEP 91a)

| 코드 | 검사 | 성격 | 등급 |
|---|---|---|---|
| V8-01 | 같은 파일명이 두 번 생성되지 않음 | code | fatal |
| V8-02 | 출력 파일에 BOM · CRLF 가 없음 | code | fatal |

---

## STEP 108 — v1 → v2 이관 대응표

| v1 | v2 | 비고 |
|---|---|---|
| `dealer_shop` (지역) | `dealer_region` | **오매핑 정정** |
| `page_status` | `*_status` (컬럼 4 × 값 5종) | 명칭 변경 |
| `weighted_pct` | 폐기 | |
| `hard_reject_reason` | `absolute_fail` | 색상값 오염 제거 |
| `recommend_score` | `score_total` | |
| 축 7개 | **Component 17개** | 표시 단위 확장 |
| 등급 6종 | **7종** (`NOT_RATED` 추가) | |

---

## STEP 109 — 온라인 전환 대비

```
1차   Flask 서버 로컬
전환   같은 View DTO 를 API 로 낸다
```

```
필수   템플릿에 계산 로직을 넣지 않는다.  View DTO 를 그대로 렌더
      → 프런트가 바뀌어도 서버를 다시 쓰지 않는다
금지   Jinja 안에서 점수·등급·순위를 계산하는 것
```

---

## STEP 110 — 화면 미확정

| # | 항목 | 상태 |
|:--:|---|---|
| 1 | 딜러 정직도 산출식 | v1 코드에 있으나 근거 문서 없음. **재도출 대상** |
| 2 | 조건 완화 시뮬레이션 규칙 | v1 화면에 있음. 완화 축·폭 미정의 |
| 3 | `AxisChip` 3개(HUD·HDA·선루프) 외 확장 여부 | 화면 폭 확인 후 |
| 4 | 알림 채널 | 11장에서 확정 |

---

**10장 종료 (STEP 93–110).**

---

