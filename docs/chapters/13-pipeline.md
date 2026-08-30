# 5장. 수집 순서 · 방법 (STEP 47–53)

```
version  SPEC-2026.08.29-r960
follows  `docs/chapters/30-score/f-table.md`
sources  실측 08-22
checks   S46-38 · S46-39
```


## 5장 정의서

### 구조체

```python
@dataclass(frozen=True)
class RunContext:
    run_id: str
    site: str
    started_at: datetime
    parse_version: str
    dict_version: str
    calc_version: str
    endpoint_config_hash: str      # config/endpoints.json
    target_config_hash: str        # config/targets.json
    scoring_config_hash: str       # config/scoring.json
    targets: list[TargetSpec]

@dataclass
class StepReport:
    step: str
    target_key: str | None
    expected: int          # ★ 처리했어야 하는 총량
    requested: int         # 실제로 던진 수
    ok: int
    empty: int
    not_found: int
    error: int
    not_requested: int     # expected - requested
    rejected: int          # ok 중 형식 검증 실패 (ok 의 부분집합)
    elapsed_sec: float
    halted: bool
    halt_reason: str | None

@dataclass(frozen=True)
class ResumePoint:
    step: str
    target_key: str | None
    page: int | None
    source_id: str | None
    endpoint: str | None
```

**`expected` 가 핵심이다.** 이것이 없으면 「애초에 안 던진 것」을 검증할 수 없다.
v1 은 208건 중 76건만 요청하고도 리포트가 정상으로 보였다.

**`rejected` 는 `ok` 의 부분집합이다.** 응답은 200 으로 왔으나 형식 검증에서 거부된 건이다.
별도 상태가 아니라 `ok` 안에서 세는 값이다.

### 버전 · 설정 해시를 남기는 이유

```
질문   「이 매물이 왜 87점인가」
답     그때의 parse_version · dict_version · calc_version
      + endpoints / targets / scoring 설정 해시가 있어야 재현된다
```

**설정 파일이 바뀌었는데 버전을 올리지 않으면 재현이 깨진다.**
**해시를 함께 남겨 「선언한 버전」과 「실제 내용」이 어긋나는 것을 잡는다.**

### 함수

| 이름 | 입력 | 출력 | 목적 |
|---|---|---|---|
| `run_pipeline` | `RunContext` | `list[StepReport]` | 전체 실행 |
| `run_step` | `RunContext, step_name` | `StepReport` | 단계 1회 |
| `precheck` | `RunContext, step_name` | `bool` | 선행 조건 확인 |
| `halt_if` | `StepReport` | `None` | 중단 조건 판정 |
| `resume_point` | `run_id` | `str \| None` | 재개 지점 |

### 재실행 안정성과 결정론성 — 층마다 다르다

**「전 단계 멱등」은 부정확하다. 수집은 새 스냅샷을 만든다.**

| 층 | 성질 | 정의 |
|---|---|---|
| 수집 | **재실행 안정성** | 재실행 시 새 RAW 스냅샷이 추가될 수 있다. **기존 RAW 를 훼손하지 않는다** |
| 파싱 | **결정론성** | 같은 RAW + 같은 `parse_version` → 같은 CORE |
| 판정 | 결정론성 | 같은 CORE + 같은 `dict_version` → 같은 `Verdict` |
| 채점 | 결정론성 | 같은 `Verdict` + 같은 `calc_version` → 같은 점수 |

```
수집    같은 결과를 보장하지 않는다.  시세와 매물이 실제로 변하기 때문이다
       보장하는 것은 「기존 원문을 덮어쓰거나 지우지 않는다」이다
파싱~채점  완전 결정론.  버전이 같으면 결과가 같아야 한다
검증    파싱~채점 재실행 결과가 이전과 다르면 ValidationError
```

**이 구분이 재현성의 전제다** (0장 STEP 8).

---

## STEP 47 — 단계 목록

| 단계 | 이름 | 대상 | 선행 조건 | 산출 |
|:--:|---|---|---|---|
| S0 | 백업 | DB | — | 스냅샷 파일 |
| S1 | 목록 수집 | 차종 × 페이지 | S0 | `raw_response(list)` |
| S2 | facet 수집 | 차종 **× 2요청** | — (독립) | `raw_facet` 2행/차종 |
| S3 | 사전 생성 | 축별 | S1 · S2 (필수 축 집합 통과) | `dict_*` |
| S4 | 목록 파싱 | RAW | S1 · S3 | `core_listing` (provisional) |
| S5 | 상세 수집 | 매물 | S4 | `raw_response(detail 외 3종)` |
| S6 | 상세 파싱 | RAW | S5 · S3 | `core_*` · 분류 confirmed |
| S7 | 카탈로그 수집 | 모델 | S6 | `raw_response(catalog)` |
| S8 | 카탈로그 사전 | RAW | S7 | `dict_model_option` |
| **S8.5** | **계수 산출** | 차종 | S6 | `coefficient_history` · `config/depreciation.json` |
| | ↳ 판정·채점을 쓰지 않는다. 아래 참조 | | | |
| S9 | 판정 | CORE | S6 · S8 · **S8.5** | `result_axis` |
| S10 | 채점 | 판정 | S9 | `result_score` |
| S11 | 검증 | 전 구간 | 각 단계 직후 | `audit_validation` |
| S12 | 리포트 | 결과 | S10 · S11 | 화면 · 파일 |

```
★ 실행 지시는 RecalcJob 이 만든다 (13장 STEP 132)
  관리자 화면 · 스케줄 · config 변경이 전부 RecalcJob 을 거쳐 run_pipeline 을 부른다
  자동 전용 경로를 따로 두지 않는다
필수   같은 scope 의 작업이 running 이면 새로 큐에 넣지 않는다
```

**S2 는 읽기 전용이라 S0 승인과 무관하게 먼저 돌 수 있다.**

---

### ★ 첫 실행에서 죽지 않는다 — 08-14

```
필수   빈 DB 에서 전 도구가 돈다.  검사 · 화면 · 리포트 전부
근거   실측 08-14.  check_all 이 MIN(fetched_at) → None 에서 TypeError 로 죽었다
      수집 전에 검사를 못 돌리면 「먼저 검사하고 수집한다」가 불가능하다
필수   집계 함수의 NULL 을 전제한다.  COUNT 는 0, MIN·MAX 는 None 이다
검산   V1-18  빈 DB 에서 전 진입점이 예외 없이 끝나는가
```

### ★ 진입점은 하나다 — 08-14

```
필수   run.py 가 전 명령을 받는다.  migrate · collect · web · admin
근거   실측 08-14.  run.py migrate 가 사용법만 내고 tools/menu.py 로만 됐다
      안내 문서와 실물이 갈렸다
필수   run.bat 은 껍데기다.  거기서만 되는 명령을 만들지 않는다
★ 08-16 개정 — 화면에서만 되는 명령도 만들지 않는다
  화면과 진입점이 같은 기능을 낸다.  다만 사람은 화면만 쓴다 (STEP 136d)
검산   V1-13  껍데기와 직접 실행의 인자가 같은가 (이미 있다.  미구현이다)
```

### ★ 건너뛴 요청은 `skipped` 다 — 08-14

```
not_requested   부르려 했는데 못 불렀다      ← 미완성 매물
skipped         조건에 안 맞아 안 불렀다      ← 정상
```

```
필수   조건부 엔드포인트는 skipped 로 센다 (diagnosis · encarDiagnosis == 0)
필수   expected 에서 skipped 를 뺀다.  전량 호출을 가정하지 않는다
금지   건너뛴 것을 「미완성」으로 세는 것.  전 매물이 미완성이 된다
근거   진단은 14.3% 만 호출한다.  나머지 85.7% 는 정상이다 (실측 08-14)
검산   V1-14 · V1-15  expected == 요청 대상 수 (skipped 제외)
```

---

## STEP 48 — 선행 조건

**조건 미충족 시 그 단계를 건너뛰지 않는다. 중단하고 보고한다.**

| 단계 | 조건 |
|---|---|
| S1 | 백업 완료 · `endpoints.json` · `targets.json` 로드 · `q` 조립 성공 |
| S3 | S1·S2 의 `rejected = 0` · **facet 필수 축 집합 통과** (2장 STEP 23) |

```
★ 08-16 개정 — 반입 경로에서는 S1·S2 를 반입이 대신할 수 있다
근거   실측.  AWS 서울 IP 에서 /search/ 가 407 이라 S1·S2 를 서버가 못 돈다
      S4 만 「반입이 대신했다」로 열면 S3 가 영원히 막힌다
필수   S1 · S2 도 audit_validation 에 반입 완료를 남길 수 있다
       code='STEP53-S1' · passed=1 · actual='import'
       (S4 와 같은 방식 — STEP 136b ④)
필수   그때는 무엇을 반입했는지 samples 에 남긴다
       목록이면 rows · facet 이면 축 이름과 값 수
금지   반입 없이 S1·S2 를 통과로 치는 것.  근거 없이 열지 않는다
검산   V11-46  반입으로 연 단계의 actual 이 'import' 인가
```

```
★ facet 도 반입 대상이다 — 08-16
근거   실측.  V4-25 가 지목한 color_ext · color_int · fuel 이 전부 facet 축이다
      상세를 아무리 받아도 이 사전은 안 채워진다
필수   /admin/import 가 facet 응답 JSON 도 받는다 (형식 ④)
필수   받은 facet 으로 S2 완료를 남기고 S3 가 그것으로 사전을 만든다
```

```
★ 밖에서 받아 온 봉투를 시각으로 가르지 않는다 — 08-16
근거   실측.  S4 가 「이번 실행분」을 fetched_at 으로 골랐다
      브라우저·반입분은 실행 시각이 다르므로 0건이 펼쳐졌다
      392쪽을 받아 두고도 아무 일이 안 일어났다
      화면은 「저장했습니다」를 냈다 — 사실이지만 뜻이 없었다
필수   단계가 처리할 원문을 run_id 로 고른다.  시각으로 고르지 않는다
필수   origin 이 무엇이든 아직 안 펼친 것은 펼친다
필수   「받았다」와 「쓰였다」를 화면에서 가른다
       raw_response 행 수와 core_listing 행 수를 함께 낸다
검산   V1-21  받아 두고 안 펼쳐진 원문이 있는가
```
| S4 | 사전 `pending` 축이 분류에 쓰이지 않음 |
| S5 | `core_listing` 에 `status='active'` 매물 존재 |
| S6 | S5 의 `rejected = 0` |
| S8.5 | S6 완료 · 차종별 표본이 `coefficient_min_sample` 이상 |
| S9 | **판정에 쓰는 전 축의 사전이 `confirmed`** · S8.5 계수 반영 |
| S10 | S9 의 `source` · `prio` 전건 NOT NULL |
| S12 | S11 의 V1~V5 전부 통과 |

```
금지   조건 미충족을 경고만 남기고 진행하는 것
      v1 은 사전 미분류를 unknown 으로 삼키고 계속 돌았다
```

---

## STEP 49 — 실행 순서 원칙

### 차종 완주

```
한 차종을 끝내고 다음 차종으로 간다.
끝나면 즉시 검증하고 리포트를 낸다.
```

**이유** — 8차종을 동시에 돌리면 실패 원인이 섞인다.
**차종 하나가 끝나야 그 차종의 분포를 보고 이상을 판정할 수 있다.**

### 매물 단위 완결

```
매물 1건 = detail + inspection + record + diagnosis      4종 전건
한 종이라도 not_requested 면 그 매물은 미완성이다
```

**중간에 중단되면 미완성 매물이 남는다. 재개 시 그 매물부터 다시 한다** (STEP 52).

### 파싱은 수집과 분리

```
S5 상세 수집   원문 저장만
S6 상세 파싱   저장된 원문을 읽어 CORE 적재
```

**수집 중에 파싱하지 않는다** (1장 STEP 9).
**파싱 규칙이 바뀌면 S6 만 다시 돌린다. 재수집이 아니다.**

---

## STEP 50 — 중단 조건

**아래가 발생하면 즉시 중단한다. 다음 단계로 넘어가지 않는다.**

| # | 조건 | 판정 | 조치 |
|:--:|---|---|---|
| 1 | 백업 실패 | 치명 | 리셋·수집 금지 |
| 2 | **형식 검증 거부 1건 이상** | 치명 | URL·응답 변경 의심 (2장 STEP 25a) |
| 3 | **전량 오류** (같은 코드 100%) | 치명 | 마스터에게 URL 검증 요청 |
| 4 | **수집 0건** | 치명 | 쿼리 오류. 매물 없음으로 단정 금지 |
| 5 | 미분류 5% 초과 | 치명 | 사전·분류 조건 확인 |
| 6 | 사전 `pending` 이 판정 축에 존재 | 치명 | 사람 검토 후 재개 |
| 7 | `result_axis` 의 `source` NULL 발생 | 치명 | `put()` 미경유 |
| 8 | 불변 필드 변경 감지 | 경고 | 원인 분류 후 판정 (3장 STEP 29) |
| 9 | 시간이 지나며 실패율 상승 | 경고 | 간격 조정 후 재확인 |

```
치명   해당 단계 중단.  이후 단계 실행 금지
경고   기록하고 계속.  단 리포트에 반드시 표시
```

**「조용히 넘어가기」를 금지한다.** v1 은 모든 사고가 조용히 지나간 뒤 발견됐다.

---

## STEP 50a [규격] — 재처리 결정표 ★ 단일 출처

```
목적    「무엇이 바뀌면 어디부터 다시 도는가」를 한 표로 고정한다
원천    이 표.  다른 곳에 같은 판단을 두지 않는다
입력    바뀐 것 (사이트 응답 · 매물 · 파싱 규칙 · 사전 · 계수 · 배점)
출력    from_step · 재수집 여부 · 대상 범위
값규칙  표에 없는 사유는 거부한다.  ValueError
근거    42곳에 흩어져 있으면 개발자가 매번 다르게 판단한다
금지    「확실하지 않으니 처음부터」.  4,700건 × 4엔드포인트가 다시 나간다
검산    재처리 후 해당 버전 미달 행이 0 인가
```

| 바뀐 것 | 버전 | 재실행 범위 | 재수집 |
|---|---|---|:--:|
| 사이트 응답 형태 | — | **S1 부터 전부** | **O** |
| 매물이 갱신됨 (가격·상태) | — | S5 (그 매물만) → S6 → S9 → S10 | **O** |
| RAW 가 없다 (`not_requested`·`error`) | — | S5 (그 매물만) → 이하 동일 | **O** |
| 파싱 규칙 | `parse_version` | S6 → S9 → S10 | X |
| 사전 (코드·열거값) | `dict_version` | S9 → S10 | X |
| 판정 규칙 (우선순위·`-1`) | `dict_version` | S9 → S10 | X |
| 보정계수 | `coefficient_id` | S8.5 → S9 → S10 | X |
| ~~배점 · 등급컷~~ | `calc_version` | ~~**S10 만**~~ | X | ★ 폐기 — 개정 426 |
| **배점 (갈래·축)** | `calc_version` | **★ S9 → S10** | X |
| **등급 컷만** | `calc_version` | **S10 만** | X |
| **축 온·오프 (취향 설정)** | `calc_version` | **★ S9 → S10** | X |

```
★★ 08-21 정정 (개정 426) — 개발측 v189 지적.  가이드 규격이 틀렸다

  「배점이 바뀌어도 S10 만 돌리면 된다」는 ★ 축 점수가 충족률로 저장돼 있을 때만 맞다
  실측 — result_axis.value 는 **절대점수**다 (sql/ddl/04_result.sql:4)
        value.market −100~+100 · state.accident 0~40 · taste.color 3~10
        전부 그 축의 배점 범위다
  실측 — score 칸은 92,184건 ★ 전부 NULL.  DDL 에만 있고 아무도 안 쓴다
        collect/runner.py:1237 의 INSERT 가 score 를 안 넣는다
  실측 — 축 함수가 배점을 직접 읽어 점수를 만든다
        state.py::_frame  r["frame_points"][key]
        taste.py::_fitting  ctx.policy.comp(comp)
        value.py::by_percent  config 의 per_percent · min · max
  ★ 따라서 배점이 바뀌면 축 점수 자체가 바뀐다.  S9 부터 돌려야 한다

★ 등급 컷만 바뀌면 S10 만으로 맞다.  둘을 갈라 적는다
```

```
실측 시간 (v189 · 전건 3,841매물 · 92,184축 · 수집 없음)
  S9 판정   7.1초
  S10 등급  2.9초
  ★ 합 약 10초.  「돌려야 하나」를 고민할 값이 아니다
```

```
★ 축 온·오프 — 마스터 확정 08-21 「B 로 해」
필수   끈 축을 config 에 저장하고 ★ S9 부터 다시 돌린다 (10초)
금지   ★ 화면에서만 다시 더해 보여주는 것 (미리보기)
근거   [마스터]  화면과 DB 가 다른 등급을 말하면
        그것이 이 프로젝트가 막으려는 「선언과 실제의 괴리」다
검산   V13-08  ★ 신설 — 화면 등급과 result_score.grade 가 다른 매물이 있는가
```

```
★ 배점 변경 후 S12 리포트는 다시 돈다.  점수가 바뀌었으므로
  단 11장 알림은 cause='calc' 로 분류되어 발송되지 않는다 (STEP 115)
```
| 화면 문구 · 라벨 | — | 없음 (조회 시 반영) | X |

```
필수   위 9가지 외의 이유로 재수집하지 않는다
필수   버전이 있는 것은 버전을 올린다.  올리지 않으면 이전 결과를 덮어쓴다
금지   「확실하지 않으니 처음부터」  →  4,700건 × 4엔드포인트가 다시 나간다
```

### ★ S4 가 훑는 봉투 범위

```
관찰   S4 expected 가 257 → 513 으로 늘었다
원인   raw_response 에 이전 실행 봉투가 남아 있어 다시 펼친다
영향   결과는 같다 (upsert).  전 차종 · 여러 날이면 계속 쌓인다
```

| 사유 | S4 가 훑는 봉투 |
|---|---|
| 신규 수집 (`listing_updated` · `raw_missing`) | **이번 `run_id` 만** |
| 파싱 규칙 변경 (`parse_rule`) | **전체** |
| 사이트 응답 형태 (`site_response_shape`) | 전체 |

```
근거   신규 수집은 새 봉투만 펼치면 된다.  옛 봉투는 이미 CORE 에 있다
      파싱 규칙이 바뀌면 옛 봉투도 다시 펼쳐야 한다.  그것이 재파싱의 목적이다
필수   결정표에 「어느 봉투를 훑는가」를 함께 적는다
      이것이 없으면 매번 다르게 판단한다
검증   V2-18  parse_rule 재처리 후 전 봉투가 현재 parse_version 인가
```

### 부분 재처리 — 대상 선별

```sql
-- 버전이 낮은 행만 고른다.  전건을 다시 돌리지 않는다
SELECT listing_id FROM core_listing WHERE parse_version <> :current;
SELECT listing_id FROM result_axis  WHERE dict_version  <> :current;
SELECT listing_id FROM result_score WHERE calc_version  <> :current;
```

```
근거   3장 STEP 31 이 전 테이블에 버전 컬럼을 둔 이유가 이것이다
검증   재처리 후 해당 버전 미달 행이 0 인가
```

### 재실행 시 기존 결과 처리

| 테이블 | 처리 | 이유 |
|---|---|---|
| `raw_*` | **추가만.** 덮어쓰지 않는다 | 원문은 무손실 (P3) |
| `core_*` | upsert | 현재 상태를 담는다 |
| `core_*_change` · `*_history` | 추가만 | 이력이다 |
| `result_*` | **버전별 추가.** 같은 버전이면 덮어쓴다 | 버전이 다르면 다른 결과다 |
| `audit_*` | 추가만 | 로그다 |

```
보존   audit_request 90일 (3장 STEP 28) · audit_validation 영구
근거   요청 로그는 양이 크고 최근 것만 쓸모 있다
      검증 결과는 전일 대비 GAP 이 참조하므로 지운다
```

```
금지   result_* 를 버전 무시하고 덮어쓰는 것
      → 「배점을 바꾸기 전에는 얼마였나」를 잃는다 (11장 STEP 115)
```

---

## STEP 50b [규격] — 결함을 한 번에 모은다 ★

```
목적    한 번 돌면서 전 결함을 모은다.  하나 고치고 다시 도는 것을 없앤다
원천    각 단계의 검증 결과
입력    run_id
출력    DefectReport — 결함 목록 + 의존 관계
값규칙  fatal 을 만나도 그 단계까지는 기록하고 다음 단계로 간다
       산출이 없으면 뒤 단계는 「선행 없음」으로 건너뛴다
근거    고치고 다시 돌기를 반복하면 수집이 매번 다시 나간다
금지    이 모드의 결과를 판정에 쓰는 것.  calc_version 을 올리지 않는다
검산    한 실행에서 나온 결함 수 == DefectReport 행 수
```

```
python3 run.py collect --diagnose
```

### 재수집하지 않는다

```
필수   RAW 가 있으면 S4 부터 돈다.  S1 · S5 를 다시 던지지 않는다
근거   결함은 대부분 파싱 이후에 있다.  수집은 이미 끝났다
       6분짜리 S5 를 결함 수만큼 반복할 이유가 없다
예외   RAW 자체가 문제일 때만 --refetch 를 함께 준다
```

### 결함 누적 리포트

```python
@dataclass(frozen=True)
class Defect:
    code: str               # 검사 코드 또는 예외 종류
    step: str
    severity: str           # fatal · warn
    count: int
    samples: list[str]      # 3건
    action: str             # Check.action (9장 STEP 90)
    root: str | None        # 이 결함의 뿌리 코드.  같으면 한 번에 고쳐진다

@dataclass(frozen=True)
class DefectReport:
    run_id: str
    steps: list[StepReport]     # 실행 · 건너뜀 · 사유
    defects: list[Defect]
    roots: dict[str, list[str]] # 뿌리 → 파생 결함 목록
```

### ★ 뿌리를 묶는다

```
문제   결함 11건이 따로 보고됐는데 뿌리는 4개였다
      「지정한 것이 조용히 사라진다」 하나가 5건으로 나타났다
```

```
필수   같은 뿌리에서 나온 결함을 묶어 낸다
방법   같은 코드가 여러 단계에서 나면 하나로
      같은 예외 종류가 여러 필드에서 나면 하나로
       매핑표 표기 불일치는 전건이 한 뿌리다
표시   「뿌리 4개 · 파생 11건.  A 를 고치면 5건이 함께 풀린다」
```

```
★ 뿌리 판정을 기계가 완전히 하지는 못한다
  후보를 묶어 내고, 사람이 확인한다
  묶이지 않은 것은 개별로 남긴다.  묶으려다 놓치지 않는다
```

### 진단 모드가 하지 않는 것

```
금지   결함을 자동으로 고치는 것
금지   result_* 를 쓰는 것.  판정 결과를 남기지 않는다
금지   config 를 바꾸는 것
근거   진단은 읽기다.  고치는 것은 사람이 판단한 뒤다
```

---

## STEP 51 — 재조회 규칙

| `status` | 재조회 | 이유 |
|---|:--:|---|
| `not_requested` | **한다** | 아직 안 던졌다 |
| `error` | **한다** | 실패했다 |
| `empty` | 안 한다 | 사이트에 자료가 없다 |
| `not_found` | 안 한다 | 404. 없는 자원이다 |
| `ok` | 안 한다 | 이미 있다 |

```
예외   매물 갱신 감지 시 (가격·상태 변경)  →  detail 만 재조회
      원문 자체가 없는 경우 (v1 record 오염)  →  전건 재수집
```

**소급 수집은 하지 않는다.** 단 **규칙이 바뀌기 전에 건너뛴 매물은 1회 소급 대상이다.**

### 재수집 vs 재파싱 vs 재채점

```
새 판정 축이 필요       →  재파싱 (S6)
파싱 규칙 오류         →  재파싱 (S6)
사전 변경             →  재판정 (S9)
배점 · 등급컷 변경      →  재채점 (S10)
원문이 없다            →  재수집 (S5)
매물이 갱신됐다         →  재수집 (S5)
```

**위 6개 외에 재수집하지 않는다.**

---

## STEP 52 — 재개 · 멱등

```
진행 상태   audit_request 에 매 요청을 남긴다
재개 지점   ResumePoint 로 좌표까지 특정한다
저장        같은 매물을 다시 수집해도 raw_response 에 새 행이 추가될 뿐
           기존 원문을 덮어쓰지 않는다.  CORE 는 upsert
```

### ★ 연속 실패 즉시 중단 — 단계 끝을 기다리지 않는다

```
문제   S5 는 31,000요청이다.  중간부터 403 이 나도 V1-08 이 단계 끝에서만 잡는다
      그때는 이미 수만 요청을 던진 뒤다
```

```
규칙   같은 http_code 로 연속 config.endpoints.fail_streak_limit 회 실패
      → 즉시 중단.  ResumePoint 를 남긴다
초기값  20.  0.1초 간격이면 2초.  낭비는 20요청뿐이다
```

```
★ 같은 코드일 때만 센다
  404 가 20건 연속인 것은 「그 매물들이 없는 것」일 수 있다.  그건 결과다
  403 · 429 · 5xx 가 연속이면 차단 · 과부하다
필수   ok 가 하나라도 나오면 카운터를 0 으로 되돌린다
금지   전체 실패율로 판정하는 것.  앞이 성공했으면 비율이 안 오른다
기록   중단 사유에 http_code 와 연속 횟수를 남긴다 (STEP 25a 판별 재료)
```

### 재개 좌표

```python
ResumePoint(step="S5", target_key="GV70_EV",
            page=None, source_id="encar_42473896", endpoint="inspection")
```

**단계 이름만으로는 재개할 수 없다.** 수집 단위가 차종 × 페이지, 매물 × 엔드포인트이기 때문이다.

| 단계 | 좌표 |
|---|---|
| S1 목록 | `target_key` + `page` |
| S5 상세 | `target_key` + `source_id` + `endpoint` |
| S6 파싱 | `target_key` + `source_id` |
| S7 카탈로그 | `model_catalog_key` |
| S9·S10 | `target_key` + `source_id` |

```
산출   audit_request 의 마지막 성공 행에서 계산한다
검증   재개 후 expected 가 남은 분량과 일치하는가
금지   진행 상태를 메모리·전역 변수에만 두는 것 (0장 STEP 8-④)
```

```
필수   중단되어도 처음부터 다시 돌리지 않는다
      4,700건 수집 중 4,000건에서 끊겼는데 처음부터 하면 시간과 요청이 낭비된다
금지   진행 상태를 메모리·전역 변수에만 두는 것 (0장 STEP 8-④)
```

### 워커 다중화 대비

```
1차    단일 프로세스
전환   매물 단위로 분할 가능하도록 설계한다
       매물 처리는 서로 독립이어야 한다
금지   매물 간 공유 상태 (v1 last_raw 사고)
```

---

## STEP 53 — 단계별 산출 보고

**각 단계 종료 시 `StepReport` 를 남긴다. 화면 출력만 하지 않는다.**

```
requested · ok · empty · not_found · error · not_requested · rejected
elapsed · halted · halt_reason
```

### 자동 점검 — 단계 종료 즉시

```
① expected == requested + not_requested              ★ 안 던진 것이 있는가
② requested == ok + empty + not_found + error        응답 수가 맞는가
③ rejected == 0        (rejected ⊆ ok)               형식 검증
④ ok > 0                                             수집 0건이 아닌가
⑤ raw_response 신규 행 == ok + empty + not_found + error
                                                     ★ 저장 누락 없는가
⑥ not_requested == 0                                 ★ 미완성 매물이 없는가
```

**하나라도 어긋나면 `halted=True`. 다음 단계를 실행하지 않는다.**

### ①⑥ 이 핵심이다 — v1 사고의 직접 차단

```
v1    208건 중 76건만 요청.  나머지는 skip_done 으로 건너뜀
      기존 검증식(requested == ok + ...)은 76건 기준으로 통과했다
      「애초에 안 던진 것」을 아무도 세지 않았다
```

**`expected` 산출 규칙**

| 단계 | `expected` |
|---|---|
| S1 목록 | **`collect_group` 수 × 페이지 수** |
| | ↳ 첫 요청의 `Count` 로 페이지 수를 확정한다 (STEP 18a) |
| | ↳ `expected` 를 요청 전에 못 정한다.  1페이지 후 갱신 |
| **S2 facet** | **`collect_group` 수** (축 미지정 · 2장 STEP 23) |
| S3 사전 | 사전 축 수 |
| S5 상세 | `status='active'` 매물 수 × 엔드포인트 4종 (진단 포함) |
| S6 파싱 | 해당 `status='ok'` 원문 수 |
| S7 카탈로그 | 캐시에 없는 `model_catalog_key` 수 |
| S8.5 계수 | 표본이 `coefficient_min_sample` 이상인 차종 수 |
| S9 판정 | `core_listing` 매물 수 × **Component 수** |
| S10 채점 | `core_listing` 매물 수 |

```
★ S2 를 빠뜨리면 facet 요청 누락이 V1-01 을 통과한다
검증   raw_facet 행 수 == collect_group 수 인가
```

**`expected` 를 코드가 스스로 계산한다. 사람이 입력하지 않는다.**

### ⑤ — `raw_response` 는 실패도 저장한다

```
저장 대상   ok · empty · not_found · error       전부
not_requested 는 저장하지 않는다.  요청 자체를 안 했기 때문이다
           대신 core_listing 의 *_status 에 남는다
```

**실패 응답도 원문이다.** 나중에 「왜 실패했나」를 보려면 body 가 필요하다.

### 차종별 리포트

```
차종 · 수집 건수 · 상세 확보율 · 점검부/이력/진단 확보율
분류 provisional / confirmed / conflict 건수
사전 pending 건수
축별 값 종류 수        ← 1이면 변별력 0. 경고
```

**「값 종류 1」은 v1 에서 반복된 신호다.** `accident_type` 전건 unknown ·
`is_rental` 전건 0 · `damage_outer` 전건 0 이 전부 이 형태였다.

---

**5장 종료 (STEP 47–53).**

---

---

# ★★★ 재판정 — ★ 하루 한 번 · ★ **못 돌면 네 시간 뒤 다시** (마스터 정정 08-25 · 개정 736)

```
★★ 마스터 — 「★ **재판정 4시간은 그런 뜻이 아니다.
   ★ 재판정을 ★ 13시에 못할 경우 ★ 4시간 단위로 다시 하라는 뜻이야.
   ★ 엔카 말고는 ★ 수집은 하루에 한 번 하라는 뜻이야**」
★ ★ **가이드가 ★ 「네 시간마다 채우기」로 잘못 읽었다** (오판 117)
```

## ★★★ 두 가지다 — ★ 섞지 마라

| | 언제 | 무엇을 |
|---|---|---|
| ★ **수집** | ★ **하루 한 번** | ★ 엔카 말고는 ★ 전부.  ★ 더 자주 받지 않는다 |
| ★ **재판정** | ★ **13:00 한 번** | ★ 전량 |
| ★★ **재시도** | ★ **13:00 에 ★ 못 돌았으면** ★ 네 시간 뒤 | ★ **다시 그 재판정을 한다** |

```
★★★ ★ **「네 시간마다」가 ★ 아니다.  ★ 「못 돌았을 때만 ★ 네 시간 뒤」다**
   ★ ★ 13:00 에 ★ 돌았으면 ★ **17:00 에 안 돈다.  ★ 다음 날 13:00 이다**
   ★ ★ 13:00 에 ★ 못 돌았으면 ★ 17:00 에 ★ 다시 → ★ 그래도 못 돌면 ★ 21:00 …
★ ★ 「못 돌았다」란 —
   ① ★ 서버가 꺼져 있었다 · ② ★ 앞 작업이 안 끝나 밀렸다 · ③ ★ 오류로 끊겼다
```

## ★ 수집은 ★ 하루 한 번

```
★★ ★ **엔카만 ★ 다르다** — ★ 매물이 가장 많고 ★ 가장 빨리 바뀐다
★ ★ 나머지 열은 ★ **하루 한 번**이면 된다
   ★ ★ 현대 181 · 기아 75 · KB 1,726 · K카 526 · 보배 3,233 · 리본카 1,038 …
   ★ ★ 하루에 몇 건 안 바뀐다.  ★ 자주 받으면 ★ 사이트에 부담만 준다
필수  ★ ★ **엔카 말고는 ★ 하루 한 번** (마스터 확정 08-25)
필수  ★ 엔카는 ★ 마스터 회선(`/admin/collect`)이라 ★ **마스터께서 여실 때** 받는다
금지  ★ ★ **네 시간마다 수집하는 것**
```

## ★ 어떻게 만드나

```
★ `carwatch-daily.timer` — ★ **13:00 그대로** (수집 ＋ 재판정)
★★ ★ **재시도는 ★ 타이머를 새로 만들지 않는다**
   ★ ★ `carwatch-daily.service` 에 ★ **`Restart=on-failure` ＋ `RestartSec=4h`**
   ★ ★ 또는 ★ 13:00 실행이 ★ **판본을 안 남겼으면** ★ 네 시간 뒤 한 번 더
필수  ★ ★ **성공하면 ★ 그날은 더 안 돈다**
필수  ★ 재시도할 때 ★ 감사에 남긴다 — 「13:00 실패 · 17:00 재시도」
검산  ★ `S46-65` — ★ 판본이 ★ **하루 넘게** 오래됐으면 ★ 알린다 (★ 네 시간이 아니다)
```
