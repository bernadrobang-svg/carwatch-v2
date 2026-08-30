# 9장. 출력 · 리포트 (STEP 90–92)

```
version  SPEC-2026.08.30-r1006
follows  `docs/chapters/30-score/f-table.md`
sources  실측 08-22
checks   S46-38 · S46-39
```


## 9장 정의서

**출력은 판정 결과를 그대로 보여주는 것이지, 여기서 새로 계산하지 않는다.**

### 구조체

```python
@dataclass(frozen=True)
class ScoreView:
    listing_id: str
    target_key: str
    grade: str                    # S·A·B·C·D·E·NOT_RATED
    score_total: float
    denominator: float
    absolute_fail: str | None
    axes: list[AxisView]
    versions: VersionStamp

@dataclass(frozen=True)
class AxisView:
    axis: str                     # 'price' · 'spec.hud' 처럼 점 표기
    label: str
    value: int | None
    points: float
    max_points: int
    excluded: bool
    source: str
    prio: int

@dataclass(frozen=True)
class VersionStamp:
    parse_version: str
    dict_version: str
    calc_version: str
    coefficient: float
    coefficient_id: int          # coefficient_history 의 행 ID.  역추적용
    coefficient_measured: bool   # False 면 부트스트랩.  「미보정 차종」 표시
    calculated_at: datetime

@dataclass(frozen=True)
class HaltReport:
    meta: ReportMeta
    halted_step: str
    halted_at: datetime
    failures: list[CheckResult]          # severity='fatal' 인 것
    actions: dict[str, str]              # code → 다음 행동
    completed_steps: list[StepReport]    # halted=False 인 것
    artifacts: list[str]                 # 생성물 경로 (suggested.json 등)

@dataclass(frozen=True)
class ReportMeta:
    run_id: str
    layer: str                   # 'L1' · 'L2' · 'L3'
    site: str
    target_key: str | None       # L1·L2 는 값, L3 는 None
    calc_version: str
    generated_at: datetime

@dataclass(frozen=True)
class TargetReport:
    meta: ReportMeta
    collect: CollectSummary      # 매물 수 · 엔드포인트별 확보율 · *_status 분포
    classify: ClassifySummary    # provisional / confirmed / conflict
    price: PriceSummary          # 중앙값 · 계수 · 구간 분포
    axes: list[AxisStat]         # Component 별 평균 · 값 종류 · 제외 비율
    grades: dict[str, int]       # S~E · NOT_RATED
    top: list[ScoreView]
    warnings: list[str]

@dataclass(frozen=True)
class RunReport:
    meta: ReportMeta
    steps: list[StepReport]
    checks: list[CheckResult]
    day_gap: DayGapReport
    coefficient_changes: list[CoefficientChange]
    dict_changes: DictChangeSummary
    unclassified_count: int

# ── 위에서 참조하는 하위 구조체 ─────────────────────────
@dataclass(frozen=True)
class CollectSummary:
    listing_count: int
    endpoint_rates: dict[str, float]        # 'detail' → 0.99
    status_counts: dict[str, dict[str,int]] # 'detail' → {'ok':n, 'empty':m, ...}

@dataclass(frozen=True)
class ClassifySummary:
    provisional: int
    confirmed: int
    conflict: int

@dataclass(frozen=True)
class PriceSummary:
    median_actual_won: int
    median_expected_won: int
    coefficient: float
    coefficient_id: int
    bucket_counts: dict[str,int]            # '±0%' → 74

@dataclass(frozen=True)
class AxisStat:
    axis: str                                # Component 이름
    avg_points: float
    max_points: int
    distinct_values: int                     # 1 이면 변별력 0 (6장 V3-04)
    excluded_ratio: float
    source_counts: dict[str,int]

@dataclass(frozen=True)
class CoefficientChange:
    target_key: str
    before: float
    after: float
    sample_size: int
    reason: str
    changed_at: datetime

@dataclass(frozen=True)
class DictChangeSummary:
    pending: int
    confirmed: int
    retired: int
    by_axis: dict[str,int]

# ── 보고서 · 결과 구조체 ─────────────────────────────
@dataclass(frozen=True)
class DictBuildReport:
    axis: str
    added: int
    pending: int
    retired: int
    conflicts: list[tuple[str, str, str]]   # (code, 기존 display, 새 display)

@dataclass(frozen=True)
class RegistrySyncReport:
    site: str
    scanned_paths: int
    newly_registered: int      # usage='unclassified'
    ghost_paths: list[str]     # 등록부에 있으나 RAW 에 없는 것 (V4-06b)
    unclassified: list[str]

@dataclass(frozen=True)
class GapCause:
    listing_id: str
    field: str
    cause: str                 # parse_error · source_edit · listing_replaced · schema_change
    evidence: str

@dataclass(frozen=True)
class FixAction:
    check_code: str
    action: str                # reparse · rescore · recollect · manual
    scope: str                 # 대상 범위 (target_key · listing_id 목록)
    reason: str

@dataclass(frozen=True)
class NotifyResult:
    sent: int
    skipped_cause: int         # cause != 'listing' 이라 제외
    skipped_duplicate: int
    failed: int

@dataclass(frozen=True)
class RegressionReport:
    baseline_calc_version: str
    compared_listings: int
    score_mismatch: int
    grade_mismatch: int
    denominator_mismatch: int
    samples: list[str]

@dataclass(frozen=True)
class DictionarySet:
    """Analyzer 가 받는 사전 묶음.  DB 를 직접 조회하지 않는다."""
    version: str
    option3: dict[str, str]                  # code → display
    option_model: dict[tuple[str,str], dict] # (model_key, code) → {name, price}
    enums: dict[str, set[str]]               # axis → 허용값
    spec_default_on: dict[str, dict]         # target_key → {axis: value}
    spec_na: dict[str, set[str]]             # target_key → -1 축 집합

@dataclass(frozen=True)
class ScoringPolicy:
    """config/scoring.json 을 읽은 것.  코드가 숫자를 갖지 않는다."""
    calc_version: str
    total_points: int
    components: dict[str, int]               # 'spec.hud' → 20
    grade_cuts: dict[str, float]             # 'S' → 0.90
    min_denominator_ratio: float
    price_curve: list[tuple[float,int]]      # (기대가 대비, 점수)
    warranty: dict
    finance: dict                            # 선납 · 개월 · 이율

@dataclass(frozen=True)
class DayGapReport:
    """전일 대비 변동 (6장 STEP 57)."""
    run_id: str
    prev_run_id: str | None
    total_before: int
    total_after: int
    increase: int
    decrease: int
    change: int
    anomaly: int
    by_target: dict[str, dict[str,int]]
    samples: list[str]

@dataclass(frozen=True)
class ExportResult:
    filename: str
    content: bytes
    content_type: str
```

**`coefficient` 는 값만으로 부족하다.** `coefficient_id` 로 `coefficient_history` 행을 가리켜야
「어느 보정에서 나온 계수인가」가 역추적된다 (6장 STEP 64).

### 함수

| 이름 | 입력 | 출력 | 목적 |
|---|---|---|---|
| `render_listing` | `listing_id, calc_version` | `ScoreView` | 매물 1건 |
| `render_target` | `target_key, calc_version` | `TargetReport` | 차종 1개 |
| `render_run` | `run_id` | `RunReport` | 실행 1회 전체 |
| `render_halt` | `run_id` | `HaltReport` | **중단 리포트 (L0)** |
| `export` | `report, fmt` | `ExportResult` | md · csv · json. 파일명은 `ReportMeta` 로 생성 |

```
금지   Reporter 가 점수·판정을 계산하는 것
      표시용 파생값(순위·백분위)은 허용.  판정 로직은 불가
필수   모든 화면에 VersionStamp 를 함께 낸다
      「어떤 규칙으로 계산된 점수인가」를 모르면 비교가 무의미하다
```

---

## STEP 90 — 리포트 3층

| 층 | 대상 | 목적 | 형식 |
|---|---|---|---|
| **L1 매물** | 매물 1건 | 왜 이 점수인가 | 화면 · md |
| **L2 차종** | 차종 1개 | 어느 축이 갈리는가 | 화면 · md |
| **L3 실행** | 실행 1회 | 수집·검증이 정상인가 | md · 로그 |
| **L0 중단** | 중단된 실행 | **왜 멈췄고 무엇을 하면 되는가** | 화면 · md |

**네 층은 목적이 다르다. 하나로 합치지 않는다.**

### ★ L0 중단 리포트 — 판정이 없어도 낸다

```
조건   S11 gate 에서 fatal 이 걸려 S12 가 실행되지 않을 때
근거   중단은 리포트를 막는 것이 아니라 판정을 막는 것이다
금지   빈 화면으로 끝내는 것.  「실패」만 찍고 끝내는 것
```

| 항목 | 내용 |
|---|---|
| 사유 | 어느 검사(`code`)가 무엇을 기대했고 실제가 무엇이었는가 |
| 대상 | 위반 사례 전량 — 식별자 · 값 표본 |
| 조치 | 무엇을 고쳐 재실행하면 되는가 · 다른 조치가 필요한가 |
| 진행분 | 어디까지 정상이었는가 (S0~S10 중 완료 단계) |
| 버전 | `VersionStamp` |

```
필수   「조치」는 사람이 할 수 있는 행동으로 쓴다
      O  suggested.json 을 확인·수정해 field_usage.json 으로 옮긴 뒤 재실행
      X  미분류를 해소하십시오
필수   진행분을 낸다.  처음부터 다시 도는 것이 아님을 알 수 있어야 한다
생성물  중단 원인을 사람이 다루기 쉬운 파일로 함께 낸다
       예   config/field_usage.suggested.json  (STEP 87)
```

**L0 는 실패가 아니라 「다음 행동」을 내는 리포트다.**

### L1 매물 리포트 — 필수 항목

```
식별      listing_id · 차종 · 트림 · 연식 · 주행 · 색상 · URL
점수      총점 / 적용 가능 총점 · 등급 · 추천 순위
축별      **17 Component** × (획득 / 배점 · 값 · `source` · `prio` · `excluded`)
         7 Axis 로 집계해 함께 낸다 (7장 STEP 68)
가격      표시가 · 기대가 · 차이(%) · 구간 점수
실구매가   표시가 + 취득세 · 공채 · 이전비 + (틴팅 미시공 시)    ← 더하는 것만
할부      선납 1,500만(취득비 포함) · 48개월 · 5.5%
         차값 선납 = 선납금 − 취득 부대비용 · 할부 원금 = 표시가 − 차값 선납
         월 납입 · 총 이자
월 총액    월 납입 + 자동차세 + 보험료 + 유류비 + 정비 추정
E등급     해당 시 사유와 근거 필드
버전      parse · dict · calc · coefficient
미확정    이 매물 판정에 쓰인 미확정 항목 목록
```

**★ 축별 표에 `source` 와 `prio` 를 반드시 낸다.**

```
값만 보여주면 「왜 그런가」를 알 수 없다.
v1 은 근거를 안 남겨 매번 추측으로 원인을 좁혔다.
```

```
예   HUD  20/20  값 1  근거 installed(prio 2)
    선루프  0/20  값 0  근거 installed(prio 2)   ← 판매글에는 있으나 실장착 없음
    틴팅   —/5   값 NULL  제외  근거 unknown
```

### L2 차종 리포트 — 필수 항목

```
수집      매물 수 · 엔드포인트별 확보율 · `*_status` **5종** 분포
         컬럼 4개 (`detail_status` · `inspection_status` · `record_status` · `diagnosis_status`)
         값 5종 (`ok` · `empty` · `not_found` · `error` · `not_requested`)
분류      provisional / confirmed / conflict 건수
가격      실매물 중앙값 · 기대가 중앙값 · 계수 · 구간 분포
축별      평균 / 배점 · 값 종류 수 · 제외 비율
등급      S·A·B·C·D·E 분포
상위      상위 N건 (점수 · 가격 · 주행 · 연식 · URL)
경고      값 종류 1인 축 · 전건 NULL 컬럼 · 미확정 항목
```

**「값 종류 수」를 반드시 낸다.** 1이면 그 축은 순위에 기여하지 않는다 (6장 V3-04).

### L0 중단 리포트 — 항목

```
헤더      run_id · 중단 단계 · 중단 시각
사유      실패한 Check 전량 (phase · code · expected · actual · severity)
대상      code 별 위반 사례.  config.scoring.validation.sample_limit 만큼
조치      code 별 다음 행동.  Check 정의에 함께 둔다
진행분    StepReport 중 halted=False 인 단계
버전      VersionStamp
```

```
★ 「조치」는 Check 마다 미리 정해 둔다
  검사를 만들 때 「이게 걸리면 무엇을 하나」를 함께 적는다
  걸린 뒤에 생각하면 매번 다르게 대응하게 된다
```

### L3 실행 리포트

```
StepReport 전건    expected · requested · ok · empty · not_found · error
                  not_requested · rejected · elapsed · halted
검증 V1~V5        code · expected · actual · passed · severity · samples
전일 GAP          increase · decrease · change · anomaly
계수 변동          차종별 이전 → 이후 · 표본수 · 사유
사전 변동          pending · confirmed · retired 건수
등록부            unclassified 건수
```

---

## STEP 91 — 표시 규칙

### 금융 — 점수가 아니라 비용이다

**v1 `/why` 화면에 이미 있는 항목이다. 9장에 정식 편입한다.**

### ★ 할부 조건 — 마스터 확정

```
선납금    15,000,000원   ★ 취득 부대비용을 포함한 금액이다
할부 기간  48개월
이율      연 5.5%
```

### ★ 선납금이 취득 부대비용을 포함한다 — 배분이 먼저다

```
마스터 조건   현금으로 1,500만을 낸다.  그 안에 취득세·등록비가 들어 있다
```

**선납금을 먼저 부대비용에 배분하고, 남은 것이 차값 선납이다.**

```
1  취득 부대비용 = 취득세 + 공채 + 이전비 + …
2  차값 선납     = 선납금 − 취득 부대비용
3  할부 원금     = 표시가 − 차값 선납
```

```
초기 현금 부담 = 선납금 15,000,000        고정.  표시가와 무관하다
```

| 산식 | 판정 |
|---|---|
| `표시가 − (선납금 − 부대비용)` | **배분식.** 이것을 쓴다 |
| `(표시가 + 부대비용) − 선납금` | **가산식.** 대수적으로 같다. 결과가 같다 |
| `표시가 − 선납금` | **금지.** 부대비용을 아무도 안 낸 것이 된다 |

```
★ 배분식과 가산식은 같은 값을 낸다.  배분식을 쓰는 이유는 표시 때문이다
  「내 1,500만이 취득세 242만 · 차값 1,257만으로 나뉘었다」가 보인다
  가산식은 「실구매가 3,712만에서 1,500만을 뺐다」가 되어
  현금 부담이 매물마다 다른 것처럼 읽힌다.  실제로는 항상 1,500만이다

★ 경계에서는 달라진다
  부대비용 > 선납금 이면 가산식은 원금이 표시가보다 커진다
  배분식은 차값 선납 0 · 원금 = 표시가 · 부족액 별도 표시
  → 이 경계 처리가 실질 차이다
```

```
검산   차값 선납 + 할부 원금 == 표시가
      선납금 == 취득 부대비용 + 차값 선납
```

### 차값 선납이 음수인 경우

```
조건   취득 부대비용 > 선납금
표시   「선납금이 취득 부대비용보다 적습니다」 · 부족액 표시
동작   할부 원금 = 표시가.  차값 선납 0
금지   음수 선납으로 계산하는 것
```

### 월 납입 산식

```
r = 연이율 ÷ 12
n = 개월
월 납입 = 원금 × r × (1+r)^n ÷ ((1+r)^n − 1)      원리금 균등
총 이자 = 월 납입 × n − 원금
```

```
설정   config/finance.json
        down_payment_won · loan_months · loan_rate_annual · repay_method
근거   선납 · 개월 · 이율은 마스터가 바꿀 수 있는 정책값이다 (0장 STEP 6)
금지   1500 · 48 · 5.5 를 코드에 상수로 두는 것 (V4-13)
```

### 검산 예 — 취득세 7% 가정 (부대비용 0)

| 표시가 | 취득세 | 차값 선납 | 할부 원금 | 월 납입 |
|---:|---:|---:|---:|---:|
| 3,200만 | 224만 | 1,276만 | 1,924만 | **44.7만** |
| 3,470만 | 242만 | 1,257만 | 2,212만 | **51.5만** |
| 3,500만 | 245만 | 1,255만 | 2,245만 | **52.2만** |
| 4,378만 | 306만 | 1,193만 | 3,184만 | **74.1만** |

```
★ 표시가가 오르면 취득세도 올라 차값 선납이 줄어든다
  그래서 할부 원금이 표시가보다 빠르게 늘어난다
  3,200만 → 3,500만 (표시가 +300만) 인데 원금은 +321만 이다
검산   차값 선납 + 할부 원금 == 표시가   (1,276 + 1,924 = 3,200 ✓)
세율   7% 는 예시다.  실제 세율·감면은 config 에 둔다
```

### 월 50만 기준으로 본 상한

```
월 50만  ≈  표시가 3,380만 근처 (취득세 7% · 부대 0 가정)
부대비용이 잡히면 그만큼 차값 선납이 줄어 상한이 내려간다
```

### 경계 2종

```
전액 현금   표시가 + 부대비용 ≤ down_payment_won
           할부 없음.  월 납입 0

선납 부족   부대비용 > down_payment_won
           차값 선납 0 · 할부 원금 = 표시가
           「선납금이 취득 부대비용보다 적습니다」 + 부족액 표시
```

```
금지   음수 원금 · 음수 선납으로 계산하는 것
```

### 표시 항목

| 항목 | 산출 | 성격 |
|---|---|---|
| 취득세 · 공채 · 이전비 | 취득가 기준 | **실구매가에 가산** |
| **선납금** | `config` 고정 | **취득 부대비용 포함** |
| **할부 원금** | 실구매가 − 선납금 | 파생 |
| **월 납입 · 총 이자** | 원리금 균등 · 48개월 · 5.5% | 파생 |
| 자동차세 · 보험료 · 유류비 · 정비 | 추정 | **추정임을 표시** |
| 신차 대비 | 신차가 · 신차 이율 | 비교용 |

```
필수   점수 축에 넣지 않는다.  가격 200점과 이중 계산이 된다
필수   추정 항목은 「추정」으로 표시한다.  실비가 아니다
필수   세율·이율은 config.  코드에 박지 않는다 (0장 STEP 6)
금지   보증 잔여 가치를 실구매가에서 차감하는 것 (7장 STEP 83)
```

### 반드시 지키는 것

| 규칙 | 이유 |
|---|---|
| **버전을 함께 낸다** | 규칙이 다르면 점수를 비교할 수 없다 |
| **제외 축을 「0점」으로 쓰지 않는다** | `—` 또는 `해당 없음`. 0점과 구분 |
| **`평가 불가` 를 낮은 등급으로 쓰지 않는다** | 분모 미달은 D 가 아니다 (7장 STEP 83) |
| **「판매됨」이라 쓰지 않는다** | `gone` 은 목록에서 사라진 것이다 (8장 STEP 87) |
| **미확정 항목을 표시한다** | 그 매물 판정에 쓰인 미확정을 숨기지 않는다 |
| **사이트를 함께 낸다** | 분모가 다른 매물을 같은 등급표로 비교하지 않는다 (8장 STEP 89) |

### 값 표시 대조표

| 내부 | 화면 |
|---|---|
| `value=1` | 있음 |
| `value=0` | 없음 |
| `value=-1`, `excluded=True` | **해당 없음** (차종 미제공) |
| `value=NULL`, `excluded=True` | **미확인** |
| `grade='NOT_RATED'` | **평가 불가** (분모 미달) |
| `status='gone'` | **목록에서 사라짐** |

```
금지   「해당 없음」과 「없음」을 같은 기호로 쓰는 것
      「미확인」을 「없음」으로 쓰는 것
근거   v1 은 셋을 섞어 수집 실패가 만점·0점으로 둔갑했다
```

### 정렬 · 순위

```
기본     추천 순위 → 점수 내림차순
표시     순위는 같은 (dict_version, calc_version) 안에서만 매긴다
금지     버전이 다른 결과를 한 목록에 섞어 정렬하는 것
```

---

## STEP 91a [규격] — 파일 출력 ★

```
목적    리포트 파일이 어디에 어떤 이름으로 남는지 고정한다
원천    ReportMeta
입력    보고서 · 형식
출력    파일 경로
값규칙  덮어쓰지 않는다.  같은 이름이면 실패한다
근거    덮어쓰면 어제 것과 비교할 수 없다.  버전별로 남아야 한다
금지    같은 경로에 재생성.  임의 위치에 쓰는 것
검산    V8-01  같은 파일명이 두 번 생성되지 않는가
```

### 경로와 이름

```
outputs/
  L1_{listing_id}_{calc_version}.md
  L2_{target_key}_{calc_version}.md
  L3_{run_id}.md
  L0_{run_id}_halt.md
  export/{run_id}_{종류}.csv · .json
```

```
필수   전 요소를 ReportMeta 에서 가져온다.  손으로 조립하지 않는다
필수   같은 이름이 있으면 FileExistsError.  덮어쓰지 않는다
       재생성이 필요하면 calc_version 이 올라간 뒤다
디렉터리 없으면 만든다.  경로는 config 가 아니라 고정이다
```

### 인코딩과 줄바꿈

```
필수   UTF-8.  BOM 없음
필수   줄바꿈 LF.  Windows 에서도 LF 로 쓴다
근거   BOM 이 있으면 csv 첫 열 이름이 깨진다
      CRLF 면 diff 가 전건 변경으로 보인다
csv    구분자 쉼표.  값에 쉼표가 있으면 큰따옴표로 감싼다
검증   V8-02  출력 파일에 BOM · CRLF 가 없는가
```

### 보관

```
outputs/       지우지 않는다.  마스터가 판단한다
              용량이 문제되면 그때 정책을 만든다 (STEP 155 미확정)
필수           파일을 지우는 코드를 두지 않는다
근거           과거 리포트가 「그때 왜 그 등급이었나」의 증거다
```

### 원자적 쓰기

```
필수   임시 파일에 쓰고 os.replace 로 옮긴다
근거   쓰다 죽으면 반쯤 쓰인 파일이 남는다.  그것을 읽으면 잘못 판단한다
금지   open(path, "w") 로 직접 쓰는 것
```

---

## STEP 92 — 내보내기

### 형식

| 형식 | 용도 | 비고 |
|---|---|---|
| `md` | 사람이 읽는 리포트 | 기본 |
| `csv` | 표 계산 · 외부 분석 | 축별 컬럼 전개 |
| `json` | API 전환 대비 | `ScoreView` 직렬화 |

```
필수   전 형식에 VersionStamp 포함
필수   csv 는 헤더에 배점을 표기한다 — value.market(100) · taste.hud(15)
       ★ 예시를 손으로 적지 않는다.  config/scoring.json 성분에서 읽는다 (개정 412)
       ~~price(200)~~ ★ 폐기 — 개정 329·365 로 배점이 두 번 바뀌었다
금지   화면 전용 문구를 csv·json 에 넣는 것.  값과 코드로 낸다
```

### 파일명

```
{run_id}_{layer}_{target_key|ALL}_{calc_version}.{ext}
예   20260809T0930_L2_KOLEOS_HEV_c3.md
    20260809T0930_L3_ALL_c3.md
```

**전부 `ReportMeta` 에서 나온다.** 파일명 규격과 구조체가 어긋나지 않는다.

**버전이 파일명에 있어야 이전 결과와 섞이지 않는다.**

### 온라인 전환 대비

```
1차   파일 출력 · 로컬 화면
전환   같은 ScoreView 를 API 응답으로 낸다
```

```
필수   Reporter 는 DTO 를 받아 형식만 바꾼다.  DB 를 직접 조회하지 않는다
      → 형식이 늘어나도 조회 로직을 다시 쓰지 않는다
```

---

**9장 종료 (STEP 90–92).**

---



---

## ★★★ 예상 구매비용은 사이트별로 낸다 — 08-18

**마스터 확정 — 「그게 케이카 비용이잖아. 사이트별로 정책이 다를 건데.**
**케이카로 구매 시 가격이고 엔카 구매 시 가격이잖아.**
**제네시스 중고도 10년 보장이라 추가하는데 뭐 같지. 사이트별 총합을 내라」**

```
★ 같은 차라도 어디서 사느냐에 따라 실제로 내는 돈이 다르다
★ 지금은 차량가만 낸다.  그것은 「얼마에 파는가」이지 「얼마를 내는가」가 아니다
```

### 실물

```
K카     차량가 34,300,000 + 이전등록 2,523,000 + K Car Warranty 498,000
        + 기타 385,000 + 배송 무료  =  37,706,000
엔카    차량가만 낸다.  이전등록비는 사는 사람이 따로 계산한다
제네시스 인증중고차   10년 보증이 붙는다 (마스터 지적)
```

### 규격

```
필수 [마스터]   사이트마다 구매비용 구성을 config 에 둔다 — sites.json
                purchase_cost
                  transfer_fee_rule    이전등록비 계산식 (차량가·연식·배기량 기준)
                  warranty_fee         그 사이트 보증 가입비
                  etc_fee              기타
                  delivery_fee         배송비
                  extra_benefit        추가 혜택 (제네시스 10년 보증 같은 것)
필수 [마스터]   매물마다 그 사이트 기준 총액을 낸다
                「K카에서 사면 3,770만 (차량가 3,430 + 이전등록 252 + 보증 50 + 기타 39)」
필수 [마스터]   여러 사이트에 같은 차가 있으면 사이트별로 나란히 낸다
                「엔카 2,990만 → 실제 3,240만 · K카 3,050만 → 실제 3,320만」
                ★ 표시가가 싼 쪽이 실제로 싼 쪽이 아닐 수 있다
필수 [원문]     사이트가 총액을 주면 그것을 쓴다.  우리가 계산하지 않는다
                ★ K카는 화면에 낸다.  받아서 쓴다
필수 [판단]     사이트가 안 주면 우리가 계산하고 「추정」이라 적는다
                근거 — 이전등록비는 법정 요율이라 계산할 수 있다.  ★ 요율 조사 필요
필수 [마스터]   추가 혜택을 따로 낸다 — 「10년 보증 포함」
금지 [마스터]   차량가만 내는 것
금지 [마스터]   사이트가 다른 매물을 표시가로만 견주는 것
검산            V11-120  매물마다 사이트별 총액이 나오는가
                V11-121  여러 사이트에 있는 차는 총액을 나란히 내는가
```

```
★ 점수에는 넣지 않는다 (기존 규격 유지)
  ★ 가격 축과 이중 계산이 된다
★ 다만 화면에서는 이것이 「실제로 내는 돈」이다.  크게 낸다
```

---

## ★ 전액 현금 판정 — 08-18 확정

**마스터 확정 — 「1500보다 싸다는 이야기잖아. 그렇게 해」**

```
필수 [마스터]   표시가 + 부대비용 ≤ config.finance.cash_limit 이면 「전액 현금」
                기본 1,500만원 (선납금)
필수 [마스터]   넘으면 부족액을 낸다 — 「1,740만원 부족」
필수 [기술]     1500 을 코드에 두지 않는다.  config 다 (V4-13)
```


---

## ★★ 리포트를 화면에서 본다 — 08-18

**마스터 확정 — 「목록을 보고 클릭하면 내용을 볼 수 있게 팝업 박스로 만들기.**
**다운로드 누를 때 다운로드」**

```
지금   파일 목록만 낸다.  내려받아야 볼 수 있다
★ 휴대폰에서 내려받으면 볼 도구가 마땅치 않다
```

```
필수 [마스터]   목록에서 파일을 누르면 팝업으로 내용을 낸다
필수 [마스터]   팝업 안에 「다운로드」 단추를 따로 둔다
                ★ 누를 때만 내려받는다.  열자마자 받지 않는다
필수 [기술]     md · csv · json 을 화면에서 읽을 수 있게 낸다
                md    그대로 렌더
                csv   표로
                json  접었다 펴는 트리 또는 그대로
필수 [기술]     큰 파일은 앞부분만 내고 「전체는 내려받으십시오」
                ★ 상한은 config — report_preview_bytes (기본 200KB)
필수 [기술]     팝업은 JS 없이도 닫힌다 — details 또는 별도 경로
금지 [마스터]   목록만 내고 내용을 못 보게 하는 것
검산            V11-122  리포트를 화면에서 읽을 수 있는가
```

---

## ★ 쿼리 탐색의 쓰임 — 08-18 확인

**마스터 — 「쿼리는 네가 보라고 쿼리를 줘서 내가 보려고 만든 창이야.**
**아직 못 쓰지만 raw 데이터 보는 용도는 좋아」**

```
★ 쓰임이 확인됐다 — 가이드가 준 쿼리를 마스터가 붙여넣어 실행한다
```

```
필수 [마스터]   붙여넣기 상자를 크게 둔다.  여러 줄 쿼리가 들어간다
필수 [마스터]   결과를 복사할 수 있게 (탭 구분 · CSV · JSON)  ★ 유지
필수 [판단]     자주 쓰는 쿼리를 저장할 수 있게 한다
                근거 — 같은 것을 매번 붙여넣게 하지 않는다.  ★ 마스터 확인 필요
필수 [기술]     결과가 많으면 앞부분만 내고 건수를 낸다
필수 [기술]     실패하면 왜인지 낸다 — 문법 오류 · 금지 테이블 · 시간 초과
```
