## STEP 63 — V5 수치 검증

```
version  SPEC-2026.09.02-r1075
follows  `docs/chapters/30-score/f-table.md`
sources  실측 08-22
checks   S46-38 · S46-39
```


**점수가 「계산은 됐는데 의미가 틀린」 상태를 잡는다.**

| 코드 | 검사 | 기대 | 등급 |
|---|---|---|---|
| V5-01 | 배점 합계 == `config` 총점 | 일치 | fatal |
| V5-02 | 등급컷이 총점 비율과 일치 | 일치 | fatal |
| V5-03 | **분모 시험 6종 통과** | 전건 | fatal |
| V5-04 | 점수 범위 위반 없음 (음수·초과) | 0 | fatal |
| V5-05 | 등급 분포가 극단적이지 않음 | 통과 | warn |
| V5-06 | 기준값 대비 실측 이탈 | 통과 | warn |
| V5-07 | 계수 보정 타당성 | 통과 | fatal |
| V5-08 | **계수 산출 입력에 `result_*` 가 없음** | 0 | fatal |
| V5-09 | 등급이 `earned / denominator` 로 산출됨 (또는 `score_total / total_points`) | 전건 | fatal |
| V5-10 | 같은 비율 · 다른 분모가 같은 등급 | 일치 | fatal |
| V5-11 | 분모 최대값으로도 `S` 가 불가능한 매물 없음 | 0 | warn |
| V5-12 | `NOT_RATED` 인데 `not_rated_reason` 이 NULL 인 행 없음 | 0 | fatal |

### V5-03 분모 시험 6종 (0장 STEP 7.1)

```
A 전 축 정상            정상 점수
B 한 축 수집 실패        분모 제외 · 산출
C 한 축 구조적 부재      분모 제외 · 산출
D 전 축 수집 실패        점수 생성 금지
E 금지 근거만 존재       점수 생성 금지
F 분모 최소 기준 미만    등급 생성 금지 · '평가 불가'
```

### V5-05 등급 분포

```
경고 조건   S~C 가 0건이고 D·E 만 존재
           한 등급이 90% 초과
```

**v1 은 두 차종 744건이 전부 D·E 였다. 만점을 받아도 C 가 안 나오는 상태였다.**
**등급컷 문제가 아니라 축이 안 붙는 문제였다.**

```
판별   축별 평균을 분해한다.  0 이거나 만점인 축을 먼저 본다
```

### V5-06 기준값 이탈

```
기준값   config 의 임계값 (감가 곡선 · 만점 기준 · 등급컷)
검사     실측 분포가 기준값 근처에 모이는가
예       기대가 ÷ 실매물 중앙값 이 1.0 에서 크게 벗어나면 곡선이 틀렸다
```

---

## STEP 64 — V5 계수 보정

### ★ S8.5 산출 순서 — 3단계. 거꾸로 하면 첫 실행이 멈춘다

```
1  감가 곡선 산출     실매물 price_current_won ÷ price_origin_won 을 연차별 집계
                  ★ 곡선은 계수를 쓰지 않는다.  실측에서 직접 나온다
                  → depreciation_curve_history INSERT
                  → 이상 2종 검사 (잔가율 1.0 초과 · 연차 역전)

2  기저 기대가       calc_base_expected_price(snapshot) = 신차가 × 감가계수
                  ★ 보정계수를 곱하지 않는다

3  차종별 보정계수    median(실매물 가격) ÷ median(기저 기대가)
                  → coefficient_history INSERT
```

```
금지   1 을 건너뛰고 2 를 하는 것.  곡선이 없으면 기대가가 안 나온다
금지   2 에서 보정계수를 곱하는 것.  3 의 분모가 자기 자신이 된다
```

### ★ 계수 부트스트랩 — 첫 실행에 계수가 없다

| 조건 | 동작 |
|---|---|
| 유효 표본 ≥ `coefficient_min_sample` | 측정 → `measured=1` |
| 표본 미달 · 이전 `measured=1` 있음 | **기존 계수 유지.** 신규 행 없음 |
| 표본 미달 · 이전 이력 없음 (최초) | `coefficient=1.00` · `measured=0` · `reason='bootstrap'` |

```
measured 의 뜻   「한 번이라도 측정된 적이 있다」
                「이번에 측정했다」가 아니다.  표본 감소로 되돌리지 않는다
```

```
measured=0 이면   sane_range 검사 면제
                가격 축은 정상 산출한다.  excluded 로 빼지 않는다
                → 첫 실행에서 전 차종이 빠지면 아무것도 못 본다
표시             화면에 「미보정 차종」 배지
                DTO 의 coefficient_measured 로 전달한다
```

### ★ 계수 산출에 판정·채점 결과를 쓰지 않는다

```
계수 = 실매물 가격 중앙값 ÷ 기대가 중앙값
```

| 재료 | 출처 | 필요 단계 |
|---|---|---|
| 실매물 가격 | `core_listing.price_current_won` | **S6 까지면 있다** |
| 기대가 | 신차가 × 감가계수 | **S6 까지면 있다** |
| ~~점수~~ · ~~등급~~ | — | **쓰지 않는다** |

```
★ 기대가는 판정이 아니다.  가격 축 점수를 매기기 전 단계의 산술이다
  그래서 S8.5 가 S9 앞에 온다.  순환이 아니다
금지   계수 산출에 score_total · grade · result_* 를 쓰는 것
      → 점수로 계수를 만들고 그 계수로 다시 점수를 내면 순환이다
검증   V5-08  계수 산출 입력에 result_* 가 없는가
```


**계수 보정은 정상 동작이다. 버그 수정이 아니다.**

```
목적   기대가 곡선을 실제 시세에 맞춘다
방법   차종별 실매물 중앙값 ÷ 기대가 중앙값
적용   STEP S9 판정 전.  자동
```

### 가드 — 보정이 오히려 왜곡을 만드는 경우

| 조건 | 판정 | 조치 | config 키 |
|---|---|---|---|
| 직전 대비 변동률 초과 | 의심 | 중단 · 알림 | `coefficient_change_limit` |
| 표본 부족 | 신뢰 불가 | 보정 생략 · 이전 계수 유지 | `coefficient_min_sample` |
| 수집 실패 직후 | 표본 왜곡 | 보정 생략 | — |
| 반복 후 미수렴 | 곡선 자체가 틀림 | fatal · 곡선 재검토 | `coefficient_max_iter` |

```
값은 config 에 둔다.  본문에 숫자를 박지 않는다 (0장 STEP 5.5)
초기값은 config 에 둔다.  첫 수집 결과를 보고 조정한다
```

```
이유   수집이 실패해 표본이 줄면 중앙값이 흔들린다
      그것을 시세 변동으로 오인해 계수를 바꾸면 점수가 통째로 틀어진다
```

### 계수 이력

```
coefficient_history   target_key · 이전 계수 · 새 계수 · 표본수 · 사유 · 시각
```

```sql
CREATE TABLE depreciation_curve_history (
  id           INTEGER PRIMARY KEY,
  run_id       TEXT NOT NULL,
  curve_json   TEXT NOT NULL,        -- 연차 → 잔가율
  sample_json  TEXT NOT NULL,        -- 연차별 표본 수
  anomalies    TEXT,                 -- 잔가율 1.0 초과 · 연차 역전
  created_at   TEXT NOT NULL
);

CREATE TABLE coefficient_history (
  id            INTEGER PRIMARY KEY,
  site          TEXT NOT NULL,
  target_key    TEXT NOT NULL,
  before_value  REAL,
  after_value   REAL NOT NULL,
  sample_size   INTEGER NOT NULL,
  measured      INTEGER NOT NULL,    -- 1 측정 · 0 부트스트랩
  reason        TEXT NOT NULL,
  changed_at    TEXT NOT NULL,
  UNIQUE (site, target_key, changed_at)
);
```

```
★ measured 는 「한 번이라도 측정됐는가」다 (STEP 64)
  0 이면 sane_range 검사를 면제하고 화면에 「미보정 차종」을 표시한다
```

**남기지 않으면 점수 변동 원인을 사후에 못 찾는다.**
**`VersionStamp.coefficient_id` 가 이 테이블의 `id` 를 가리킨다** (9장).

---

## STEP 65 — 점수 변동 원인 분리

**「어제 87점, 오늘 82점」의 원인은 네 가지다. 섞으면 안 된다.**

| 원인 | 판별 | 표시 |
|---|---|---|
| 매물 변경 | 가격·상태가 바뀜 | 「가격 50만 인하」 |
| **사전 변경** | `dict_version` 이 다름 | 「사전 갱신으로 재판정」 |
| **배점 변경** | `calc_version` 이 다름 | 「배점 개정」 |
| **계수 보정** | 계수가 바뀜 | 「시세 반영」 |

```
비교 규칙   같은 (dict_version, calc_version) 끼리 비교하는 것이 원칙
           다르면 차이를 먼저 분리해 표시한다
금지       사전·배점이 바뀐 것을 매물이 바뀐 것처럼 보여주는 것
```

**11장 후보 추적이 이 위에서 돈다.**

---

## STEP 66 — 검증 결과 저장 · Gate

```sql
CREATE TABLE audit_validation (
  run_id      TEXT NOT NULL,
  phase       TEXT NOT NULL,     -- V1~V5
  code        TEXT NOT NULL,     -- V1-03
  target_key  TEXT,
  expected    TEXT NOT NULL,
  actual      TEXT NOT NULL,
  passed      INTEGER NOT NULL,
  severity    TEXT NOT NULL,     -- fatal · warn
  applicable  INTEGER NOT NULL DEFAULT 1,  -- ★ 08-14. 0 이면 미실행 — 통과로 세지 않는다
  samples     TEXT,              -- 위반 사례 최대 20건
  checked_at  TEXT NOT NULL,
  PRIMARY KEY (run_id, phase, code, target_key)
);
```

```
저장   화면 출력만 하지 않는다.  전일 비교(STEP 57)가 이 테이블 위에서 돈다
샘플   위반 사례 listing_id 를 최대 20건 남긴다.  「몇 건 위반」만으로는 못 고친다
```

### Gate

```
fatal 1건이라도 실패   →  다음 단계 실행 금지
warn                →  진행하되 리포트 최상단에 표시
전건 통과            →  다음 단계
```

```
금지   fatal 을 임시로 warn 으로 낮춰 통과시키는 것
      필요하면 검사 자체를 폐지하되, 사유를 문서에 남긴다
```

---

**6장 종료 (STEP 54–66).**

---

