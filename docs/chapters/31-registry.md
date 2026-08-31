# 8장. 미사용 · 확장 (STEP 87–89)

```
version  SPEC-2026.09.01-r1035
follows  `docs/chapters/30-score/f-table.md`
sources  실측 08-22
checks   S46-38 · S46-39
```


## 8장 정의서

**「지금 안 쓰는 것」을 「없는 것」으로 만들지 않는다.**
**v1 은 미사용 항목의 정의가 없어서, 실제로 필요한 필드가 「미사용」으로 분류돼 방치됐다.**

### 구조체

```python
@dataclass(frozen=True)
class FieldUsage:
    site: str
    endpoint: str            # list · detail · inspection · record · diagnosis · catalog · facet
    json_path: str           # 원문 경로 또는 facet 축 이름
    core_column: str | None  # CORE 컬럼.  없으면 None
    usage: str               # in_use · display_only · unused_by_policy · deferred · blocked · not_provided
    reason: str              # 사유.  필수
    unblock_condition: str | None   # blocked 일 때 해소 조건
    use_when: str | None            # deferred 일 때 사용 시점
    priority: int | None            # 사용 시 우선순위 (1 이 먼저)
    first_seen: date
    last_seen: date
```

### 함수

| 이름 | 입력 | 출력 | 목적 |
|---|---|---|---|
| `scan_paths` | `endpoint` | `list[str]` | RAW 경로 전수 |
| `sync_registry` | `site` | `RegistrySyncReport` | 경로 ↔ 등록부 동기화 |
| `assert_registered` | `site` | `None` | 미등록 경로 0건 시험 |
| `list_by_usage` | `usage` | `list[FieldUsage]` | 구분별 조회 |

```
sync_registry   신규 경로 → usage='unclassified' 로 적재 + 알림
               사라진 경로 → last_seen 갱신.  삭제하지 않는다
assert_registered  usage='unclassified' 가 있으면 실패
```

### ★ `json_path` 생성 규칙 — 엔드포인트별로 다르다

| endpoint | `json_path` | 근거 |
|---|---|---|
| `list` · `detail` · `inspection` · `record` · `diagnosis` | JSON 경로 (`advertisement.price`) | 2장 평탄화 규칙 |
| `catalog` | 배열 요소 키 (`[].optionCd`) | 루트가 배열 |
| **`facet`** | **`{Name}#{Type}`** (`Price#Aspect` · `Price#RangeAction`) | **중복 이름이 있다** |

```python
def facet_path(node) -> str:
    return f"{node['Name']}#{node['Type']}"
```

```
필수   facet 축은 (Name, Type) 을 합쳐 하나의 json_path 로 만든다
금지   Name 만 쓰는 것
      → Price · Mileage 가 서로를 덮어써 등록부가 2건 유실된다
검증   V4-06 이 RAW 경로 전수와 대조할 때 같은 규칙으로 만든다
```

### 구분 6종

| `usage` | 뜻 | 필수 항목 |
|---|---|---|
| `in_use` | 판정에 쓴다 | `core_column` |
| **`display_only`** | **화면·리포트에만 쓴다** | `core_column` |
| `unused_by_policy` | 판정에 안 쓰기로 **결정** | `reason` |
| `deferred` | 쓸 값이나 **시점이 아님** | `use_when` |
| `blocked` | 쓰고 싶으나 **원문·근거 부족** | `unblock_condition` |
| `not_provided` | 사이트가 **주지 않음** | `reason` |

```
금지   「미사용」 한 단어로 뭉뚱그리는 것
금지   여섯 가지 밖의 임의 구분을 쓰는 것 (「사용 결정」 같은 것)
필수   항목마다 구분과 사유를 함께 적는다
```

**★ 「표시 전용」은 `display_only` 다.** 판정에 안 쓰지만 화면에는 나온다.
**`unused_by_policy` 와 다르다** — 후자는 화면에도 안 쓴다.

---

## STEP 87 — 미사용 등록부

### ★ 등록부는 산문이 아니라 테이블이다

**v1 방치의 근본 원인은 미사용 목록이 문서에만 있었다는 것이다.**
**문서는 기계가 검증할 수 없다.**

```sql
CREATE TABLE meta_field_usage (
  site               TEXT NOT NULL,
  endpoint           TEXT NOT NULL,
  json_path          TEXT NOT NULL,
  core_column        TEXT,
  usage              TEXT NOT NULL,
  reason             TEXT NOT NULL,
  unblock_condition  TEXT,
  use_when           TEXT,
  priority           INTEGER,
  first_seen         TEXT NOT NULL,
  last_seen          TEXT NOT NULL,
  PRIMARY KEY (site, endpoint, json_path)
);
```

**3장 테이블 목록에 `meta_*` 군으로 등록한다.**

### ★ 미분류는 그 축만 막는다 — 전체를 멈추지 않는다

```
사고   미분류 1건에 V4-11 fatal 로 전체가 멈췄다
      나머지 16축이 정상인데 아무것도 못 봤다
```

```
바꿈   미분류 경로를 쓰는 축만 excluded
      그 축의 source 에 'unclassified_path' 를 남긴다
      나머지 축은 정상 판정.  등급이 나온다
표시   「N개 경로 미분류 — 그 축은 평가하지 않았습니다」
      분모가 줄었으므로 화면에 함께 낸다 (9장 STEP 91)
```

| 검사 | 대상 | 등급 |
|---|---|---|
| **V4-11** | **판정에 쓰는 축의 경로가 미분류** | **fatal** |
| **V4-11b** | 판정에 안 쓰는 경로가 미분류 | **warn** |

```
★ 판정에 쓰는가로 가른다
  판정에 쓰는 경로가 미분류면 그 축을 못 믿는다  →  그 축만 excluded
  안 쓰는 경로는 분류가 늦어도 판정에 영향이 없다  →  warn
금지   미분류 총건수로 전체를 멈추는 것
근거   외부 데이터에 의존하면서 무결성을 전제할 수 없다 (3장 STEP 31a)
```

```
★ 그래도 분모 최소 기준은 지킨다
  미분류로 빠진 축이 많아 분모가 min_denominator_ratio 미만이면
  그 매물은 NOT_RATED 다 (7장 STEP 83)
  「일부만 보고 등급을 매겼다」가 되지 않는다
```

### ★ 첫 실행에서 미분류가 많으면

```
질문   sync_registry 를 파이프라인에 넣으면 첫 실행이 V4-11 fatal 로 멈춘다
      리포트까지 못 간다.  경험이 나쁘다
```

| 안 | 판정 |
|---|---|
| A. `sync` 후 V4-11 fatal 유지 | **채택 — 단 범위를 좁힌다** |
| B. 첫 실행만 warn 으로 | **금지.** 「fatal 을 임시로 warn 으로」는 STEP 66 위반 |

```
근거   분류 전에는 그 경로를 판정에 쓸 수 없다.  그것이 STEP 87 의 취지다
      한 번 warn 으로 열면 다음 실행에서도 열어 두게 된다

★ 다만 fatal 의 범위는 「판정에 쓰는 축」이다 (V4-11 / V4-11b)
  판정에 안 쓰는 경로가 미분류라고 전체를 멈추지 않는다
  이것은 등급을 낮추는 것이 아니라 대상을 정확히 하는 것이다
```

### 그러나 「멈춤」이 「아무것도 못 봄」이면 안 된다

**중단은 리포트를 막는 것이 아니라 판정을 막는 것이다.**

```
S11 에서 fatal   →  S12 판정 리포트를 내지 않는다
                   그러나 「무엇이 왜 멈췄는가」는 반드시 낸다
```

```
필수   중단 시 halt_report 를 낸다.  빈 화면으로 끝내지 않는다
       ① 어느 검사가 왜 실패했는가
       ② 미분류 경로 전량 — endpoint · json_path · 관측 횟수 · 값 표본 3건
       ③ 분류 후 재실행하면 되는가, 다른 조치가 필요한가
형식   화면 + `config/field_usage.suggested.json`  (분류 후보를 미리 채운 파일)
       정본은 `config/field_usage.json` 이다.  suggested 를 그대로 쓰지 않는다
```

### 분류를 사람이 처음부터 하지 않게 한다

```
자동 제안   sync_registry 가 usage 후보를 붙여 suggested.json 을 낸다
           값이 전건 동일        →  unused_by_policy 후보 (변별력 0)
           값이 전건 null·false  →  not_provided 후보
           매핑표에 있는 경로     →  in_use 후보
           그 외                →  unclassified.  사람이 판단
검토       사람은 후보를 확인·수정만 한다.  빈 표에서 시작하지 않는다
금지       제안을 그대로 적용하는 것.  suggested → field_usage 로 옮기는 것은 사람이 한다
```

```
★ 수백 건이 부담인 것은 맞다.  그래서 후보를 붙인다
  분류가 어려운 것이 아니라, 아무 단서 없이 422줄을 보는 것이 어렵다
```

### ★ 미등록이 곧 미분류가 아니다 — 표기 불일치부터 본다

```
사고   V4-06 이 10건을 「미등록」으로 잡았는데,
      전부 파서가 실제로 쓰는 경로였다.  표기가 달랐을 뿐이다

  inspection:outers[].type.title        파서는 outers[] 를 통째로 저장
  detail:category.yearMonth             파서는 year_month 로 기록
```

```
필수   V4-06 이 잡으면 먼저 2장 매핑표에 그 경로가 있는지 본다
      있으면 표기 불일치다.  분류할 것이 아니라 표기를 통일한다
표기   배열은 [] 로 한 경로.  하위는 [].키
      매핑표와 등록부가 같은 규칙을 쓴다
금지   표기가 다르다는 이유로 in_use 를 하나씩 찍는 것
      다음 수집에서 또 미등록이 뜬다
```

### ★ 유령 경로 — 등록부에만 있는 항목

```
사고   초판 시드에 advertisement.isVerifyOwner 를 넣었으나 응답에 없다
      「미사용으로 분류했다」고 안심하게 만드는데, 그 필드는 애초에 없었다
```

```
검사   V4-06b  등록부에 있으나 RAW 경로 전수에 없는 항목  →  warn
처리   3회 연속 미관측이면 usage='not_provided' 로 전환하고 사유에 기록
금지   시드를 손으로 적어 넣는 것.  sync_registry 가 RAW 에서 만든다
```

### ★ 오염된 원문을 등록부에 넣지 않는다

```
사고   v1 raw_response endpoint='record' 를 그대로 훑으면 142경로가 나온다
      실제 record 경로는 49개다.  나머지는 점검부 오염분이다
      등록부에 넣으면 record 에 master · outers 가 있는 것으로 기록된다
```

```
필수   sync_registry 는 형식 검증을 통과한 원문만 훑는다
      endpoint 라벨이 아니라 내용으로 판정한다 (2장 STEP 18 required_keys)
금지   endpoint 컬럼만 믿고 경로를 추출하는 것
검증   V4-06b 역방향 검사가 유령 경로를 잡지만, 오염분은 「있는 것처럼」 보인다
      역방향으로는 안 잡힌다.  입력 단계에서 걸러야 한다
```

```
적재 규모 참고   list 41 · detail 142 · inspection 93 · record 49 · catalog 4
                ★ v1 관측이다.  검증 기대값이 아니다 (STEP 5.5)
```

### ★ 한 차종 관측으로 변별력을 판정하지 않는다

```
사고   첫 수집(KOLEOS 1종)에서 「전건 동일」로 보인 것이
      전 차종에서는 값이 갈렸다

  spec.bodyName        'SUV' 만      →  3종 (SUV · 대형차 · 중형차)
  spec.seatCount       5 만          →  4종
  category.formYear    2025·2026 만  →  7종
  spec.customColor     null 만       →  33종  ★ 유료 색상 표기였다
  spec.tradeOwnerType  null 만       →  5종
```

```
금지   한 차종 관측으로 unused_by_policy 를 붙이는 것
필수   전 차종 수집 전에는 deferred 로 둔다
       해소 조건 = 「전 차종 수집 후 분포 확인」
근거   변별력은 모집단 전체에서 정해진다.  부분 표본으로는 판정할 수 없다
```

### 등록 범위 — 예외 없다

```
CORE 컬럼이 없는 경로도 등록한다.
「매핑표에 없으니 등록도 안 한다」가 v1 방치의 경로였다.
sync_registry 가 RAW 경로 전수를 훑어 자동 적재한다.  사람이 고르지 않는다
```

### 검증

```
V4-06  RAW 경로 전수 ↔ meta_field_usage 대조
       미등록 경로 = usage 'unclassified'  →  fatal
V4-07  usage='in_use' 인데 core_column 이 NULL  →  fatal
V4-08  usage='blocked' 인데 unblock_condition 이 NULL  →  fatal
V4-09  usage='deferred' 인데 use_when 이 NULL          →  fatal
V4-10  usage='display_only' 인데 core_column 이 NULL   →  fatal
V4-11  usage='unclassified' 가 존재                    →  fatal
```

**6분류 전부에 필수 항목 검사가 걸린다. 무검증 구분을 두지 않는다.**

**6장 V4-05 「신규 경로는 미사용 목록에 등록」이 이 테이블 위에서 기계적으로 돈다.**

### 등록 예 — 아래는 초기 시드다

**전량은 `sync_registry` 가 RAW 에서 생성한다. 아래는 판정이 필요한 것만이다.**

| endpoint | json_path | core_column | usage | reason / 조건 |
|---|---|---|---|---|
| list | `HomeServiceVerification` | `site_home_verify` | `unused_by_policy` | 엔카 배송 서비스 이용 여부. 차량 품질이 아니다 |
| list | `Advances` · `Deposit` · `MonthLease*` | — | `unused_by_policy` | 리스 금융. 구매 대상이 아니다 |
| list | `Photos[].updatedDate` | — | `unused_by_policy` | 사진 갱신 시각 |
| detail | `advertisement.preVerified` | — | `unused_by_policy` | 엔카 마케팅 배지 |
| detail | `advertisement.isVerifyOwner` | — | ~~`unused_by_policy`~~ | **응답에 없음. 유령 경로 — 등록 취소** |
| detail | `advertisement.encarCheck` | — | `not_provided` | **전건 `False`. 변별력 0** |
| detail | `advertisement.meetGo` · `homeService` | — | `unused_by_policy` | 거래 방식 |
| detail | `manage.viewCount` · `subscribeCount` | `view_cnt` · `subscribe_cnt` | `display_only` | 인기도. 화면 표시 |
| detail | `advertisement.underBodyPhotos[]` | `photo_underbody_json` | `display_only` | 하부 사진 |
| inspection | `inners[]` | `inspection_inner_json` | `display_only` | 내부 점검 40종. **전건 「양호」로 변별력 0** (STEP 67) |
| inspection | `master.detail.comments` | `inspection_comment` | `display_only` | 점검 소견 텍스트 |
| inspection | `master.detail.motorType` | `motor_type_code` | `in_use` | **차종 검증 전용.** 점수 축이 아니다 |
| inspection | `etcs[]` | `inspection_etc_json` | `deferred` | `use_when`: 8차종 수집 완료 후 경로 전수 · `priority` 3 |
| — | 판매가 · 판매일 | — | `not_provided` | **엔카는 판매 결과를 주지 않는다** ★ [추론 — 엔카는 robots `Disallow: /` 라 **우리 창에서 못 두드린다**] (아래) |
| — | 실거래가 | — | `not_provided` | 호가만 제공. 감가 곡선의 한계로 명시 (STEP 70) |
| — | 틴팅 시공 여부 | — | `not_provided` | `contents.text` 키워드로 대체 (STEP 75) |

### ★ `blocked` — 해소 조건이 있어야 등록된다

**해소 조건에 붙는 관측 수치는 `meta_field_usage.unblock_condition` 의 값이다.**
**문서가 아니라 테이블 행에 적는다** (0장 STEP 5.5 예외).

| json_path | unblock_condition | priority |
|---|---|---|
| `diagnosis.*` 전 경로 | 진단 API 원문 확보 후 경로 전수 | 1 |
| `record.*` 정상 응답 경로 | 이력 재수집. 유효 원문 비율은 등록 시점 실측값 | 1 |
| `outers[].statusTypes` 「용접,절단」 | 판금과 동일시할지 판정. 관측 건수는 등록 시점 실측값 | 2 |
| `outers[].statusTypes` 「손상」 | 표본 확대. 관측 건수는 등록 시점 실측값 | 3 |
| `category.warranty.transmissionMonth` (제네시스 전동화) | GV60·GV70_EV·G80_EV 상세 A 확보 | 1 |
| `master.detail.engineCheck` · `trnsCheck` | 값 분포 확인 후 안전 축 편입 판단 | 2 |

```
필수   해소 조건 텍스트에 그 시점 실측값을 함께 적는다 (등록부 행에)
      「용접,절단 — 판금과 동일시할지 판정 · 2026-08-09 기준 14건」
금지   본문 표에 수치를 박는 것.  수집이 늘면 즉시 틀린 값이 된다
초기값  등록 시점 실측값을 그 행에 적는다
```

**「용접,절단」과 「손상」은 별건이다.** 해소 조건이 다르므로 한 줄로 묶지 않는다.

### ★ 「판매가」는 도출할 수 없다 — 정정

```
v1 가정   gone = 팔렸다  →  마지막 가격 = 판매가
사실      gone 은 「목록에서 사라졌다」일 뿐이다 (3장 STEP 29)
         광고 만료 · 딜러 철회 · 재등록 준비도 gone 이 된다
         엔카는 판매 여부·판매가를 주지 않는다 ★ [추론 — 엔카는 robots `Disallow: /` 라 **우리 창에서 못 두드린다**]
```

| 항목 | 처리 |
|---|---|
| `gone_at` | 마지막으로 보인 시각. **사실** |
| `last_price_won` | 사라지기 직전 가격. **사실** |
| ~~`sold_price`~~ · ~~`sold_at`~~ | **만들지 않는다.** 근거 없는 추정 |

```
활용   같은 vehicle_id 가 다시 나타나면(relisted) 가격 차이를 비교한다
      그것은 「재등록 시 가격 변동」이지 「판매가」가 아니다 (11장)
표시   화면에 「판매됨」이라 쓰지 않는다.  「목록에서 사라짐」이다
```

---

## STEP 88 — facet 미분석 축

### 모집단 — 세 가지를 구분한다

| 구분 | 뜻 | 용도 |
|---|---|---|
| 응답 노드 | `Facets` 유무와 무관한 전 노드 | — |
| **차종별 축** | 그 차종 응답에 값이 있는 축 | 수집 검증 |
| **축 목록 (합집합)** | 전 차종 응답의 합집합 | 등록 · 분류 · 사전 설계 |
| 별도 요청 축 | `Badge` — 축 미지정 응답에 없다 (2장 STEP 23) | 사전 |

```
축 식별 키   (Name, Type='Aspect')     Name 만으로 훑으면 중복에서 어긋난다
```

### ★ 축 수와 목록을 문서에 적지 않는다

```
사실   차종마다 축 수가 다르다.  새 차종을 넣으면 합집합이 늘어난다
금지   「합집합 N = 사전 a + 미분석 b」 같은 산식을 본문에 두는 것
      v1 에서 이 형태를 박았다가 세 번 어긋났다
      목록을 적으면 개발자가 화이트리스트로 쓴다 (카탈로그 34건 사고와 같은 경로)

정본   meta_field_usage.  sync_registry 가 (Name, Type='Aspect') 로 자동 적재
검증   축 개수가 아니라 필수 축 집합 포함 여부 (2장 STEP 23)
신규   등록부가 unclassified 로 잡는다 (STEP 87)
조회   현재 축 목록 · 차종별 차이가 필요하면 등록부를 조회한다
```

### 사전으로 쓰는 축

```
Options · JatoOptions · FuelType · Color · SeatColor
Condition · SellType · LeaseType          축 미지정 응답에서
Badge                                     별도 요청으로
```

```
LeaseType 은 사용 중이다.  7장 STEP 82 에서 E등급 근거로 확정됐고
6장 V4 의 A등급(100% 일치) 대상이다

주의   facet 축 LeaseType 과 목록 필드 LeaseType 은 다른 것이다
      facet   그 차종에 어떤 리스 유형이 몇 건 있는가        분포
      목록     이 매물의 리스 유형                           판정 근거
      판정에는 목록 필드를 쓴다.  facet 은 분포 확인용이다
```

### 미분석 축

```
정본   meta_field_usage 에서 usage != 'in_use' 인 endpoint='facet' 행
       sync_registry 가 (Name, Type='Aspect') 키로 자동 적재한다
참고   관측 목록은 실행 결과에서 조회한다
```

**★ 축 목록을 본문에 나열하지 않는다.**

```
이유   새 차종을 넣으면 합집합이 늘어난다.  본문이 즉시 틀린다
      v1 에서 「39 = 8 + 31」을 본문에 박았다가 세 번 어긋났다
검증   축 수가 아니라 REQUIRED_FACET_AXES 포함 여부로 본다 (2장 STEP 23)
```

### 검토 대상

**facet 은 판정 근거가 아니다.** 아래는 분포 확인·결과 대조 용도로만 검토한다.

| 축 | 용도 | `usage` |
|---|---|---|
| `Accident` | 사고 분포. 이력 축 **결과 대조용** | `deferred` |
| `RentCompanyNm` | 렌터카 업체 분포. 렌트 판정 **결과 대조용** | `deferred` |
| `Mileage` · `Price` | 분포 파악. 계수 검증 보조 | `deferred` |
| `DealerShipNm` · `Trust` · `ServiceMark` | 분포 | `deferred` |
| `Transmission` · `SeatingCapacity` · `CarType` · `Category` | 차종 검증 보조 | `deferred` |
| `CityState` · `OfficeCityState` | 지역 분포 | `deferred` |

**`unused_by_policy` 로 분류하는 축**

| 축 | 사유 |
|---|---|
| `Hotmarks` · `Promotion` · `Service` · `MeetgoCenterNm` · `Lease` · `LeaseBenefits` | 마케팅 · 거래 방식 |
| `Hidden` · `MultiViewHidden` · `MultiView2Hidden` · `MultiViewAdType` · `AdType` | 노출 제어 내부값 |
| `Separation` · `ServiceCopyCar` · `CertifiedBrandNm` · `BuyType` · `GreenType` · `ModelCarType` · `AttributeType` | 사이트 내부 분류 |

```
★ 판정 근거로 승격하지 않는다
   facet Count 는 BANNED_SOURCES 다 (7장 STEP 69)
   「결과 대조」는 판정이 아니다.  put() 에 넣지 않는다
   실측 근거   모델Y 어댑티브 크루즈 facet 미체크 다수 (실제는 전 차량 기본)
```

### `CreatedDate` — 축이 아니다

```
노드는 있으나 값이 비어 있다.  축 모집단 밖이다
쿼리 파라미터로만 쓴다 (CreatedDate.range).  사전 대상이 아니다
```

```
원칙   저장은 계속한다.  분석 여부와 저장 여부는 별개다 (P3)
단일 출처   이 목록은 참고다.  meta_field_usage 가 정본이다 (STEP 87)
          sync_registry 가 endpoint='facet' 축을 (Name, Type) 키로 자동 적재한다
```

---

## STEP 89 — 다중 사이트 확장

**1차는 엔카 전용이다. 2차 사이트를 붙일 때 무엇을 바꾸고 무엇을 안 바꾸는지 정한다.**

### 바꾸는 것

| 대상 | 내용 |
|---|---|
| `adapters/{site}/` | URL · 헤더 · 쿼리 조립 · 인증 |
| `EndpointSpec` | `kind` · `required_keys` · `root_type` |
| `parse/{site}/` | 응답 경로 → CORE 필드 매핑 |
| `dict_*` 매핑 | 사이트 코드 → CORE 열거값 |
| `config/targets.json` | 사이트별 차종 표현 → `target_key` |
| 사이트 전용 검증 | 그 사이트에만 있는 제약 |

### 바꾸지 않는 것 — 목표

```
core_* 스키마 · Analyzer · Scorer · Validator · Reporter
```

**이것이 바뀌면 설계가 잘못된 것이다.**

### ★ 사이트 상수를 1차부터 선언한다 — 나중에 뒤엎지 않기 위해

**예정 사이트를 미리 등록해 둔다. 구현은 나중에, 자리는 지금.**

```python
# config/sites.json  ← 코드가 아니라 설정이다
{
  "encar":        {"label": "엔카",       "status": "active",  "order": 1},
  "kcar":         {"label": "K카",        "status": "planned", "order": 2},
  "kbchachacha":  {"label": "KB차차차",    "status": "planned", "order": 3},
  "dealer_site":  {"label": "딜러 자체",   "status": "planned", "order": 9,
                   "multi_instance": true}
}
```

```
status   active   수집·판정 대상
        planned  자리만 있다.  수집하지 않는다
        paused   일시 중단.  기존 데이터는 유지
```

**`dealer_site` 는 여러 업체가 각자 운영한다.** 하나의 사이트 코드가 아니라 **인스턴스가 여럿**이다.

```
site 값 형식   {site_code}            단일 사이트     encar · kcar · kbchachacha
              {site_code}:{slug}      다중 인스턴스   dealer_site:autoplus
필수          site 컬럼은 이 형식을 담을 수 있어야 한다 (TEXT · 길이 여유)
금지          site 를 enum 이나 고정 길이로 선언하는 것.  나중에 스키마를 고치게 된다
```

### 1차부터 지켜야 하는 것 — 이것만 지키면 뒤엎지 않는다

| 항목 | 1차에서 | 이유 |
|---|---|---|
| `site` 컬럼 | **전 테이블에 이미 있다** (3장 STEP 31) | 나중에 추가하면 전 데이터 마이그레이션 |
| 키 형식 | `listing_id = {site}_{source_id}` | 사이트가 늘어도 충돌 없음 |
| `vehicle_id` | 사이트 무관 (차량번호 → 차대번호) | 사이트 간 결합의 유일한 축 |
| CORE 컬럼명 | 사이트 고유 명칭 금지 (0장 STEP 4) | `insp_outer_json` 같은 이름을 쓰면 2차에서 못 쓴다 |
| `EndpointSpec` | 어댑터가 선언 | 사이트마다 엔드포인트가 다르다 |
| `dict_*` scope_key | `site` 를 포함 (4장 STEP 40) | 같은 코드가 사이트마다 다른 뜻 |
| `config/sites.json` | **지금 만든다** | 사이트 목록을 코드에 박지 않는다 |

```
★ 이 7개가 1차에 들어가 있으면, 사이트 추가는 어댑터 + 매핑 작업으로 끝난다
  하나라도 빠지면 그때 전체를 뒤엎게 된다
```

### 사이트별 수집 범위는 다를 수 있다

```
엔카        목록 · 상세 · 점검부 · 이력 · 진단 · 카탈로그 · facet
K카         (미확인)
KB차차차     (미확인)
딜러 자체    대개 목록 + 상세만.  점검부·이력 API 가 없을 수 있다
```

```
필수   사이트마다 「수집 가능한 엔드포인트 집합」을 EndpointSpec 으로 선언한다
결과   분모가 사이트마다 다르다 → 점수를 직접 비교하지 않는다 (아래)
표시   「엔카 기준 A / K카 기준 B」처럼 출처를 병기한다
```

### 사이트 추가 절차

```
1  원문 확보        일반 필드 300건 이상 · 조건부 필드는 그 조건 모집단 전수
                 희귀값은 전수 + 「N건에서 미관측」 명시 (0장 STEP 5.2a)
2  경로 전수 추출    사이트별 매핑표 작성 (2장 규격)
3  EndpointSpec    required_keys 를 응답에서 도출.  추정 금지
4  사전 생성        RAW 에서 distinct 추출 (4장)
5  매핑 검증        값 대조.  A등급 필드 100% (6장 V4)
6  분류 매핑        사이트 차종 표현 → target_key
7  회귀 시험        기존 사이트 결과가 바뀌지 않는지 확인
```

**7 이 중요하다.** 사이트를 추가했는데 엔카 점수가 바뀌면 CORE 가 오염된 것이다.

### 사이트 간 비교 — 주의

```
같은 차가 두 사이트에 있으면 vehicle_id 로 묶인다 (3장 STEP 30)
가격이 다르면 그 자체가 정보다.  평균 내지 않는다
점수는 사이트별로 따로 낸다.  수집 항목이 다르면 분모가 다르기 때문이다
```

```
★★ 08-18 폐기 — 개정 351
   마스터  「분모가 605이잖아.  사이트 보증 점수가 있으니
            K카는 무조건 보증이니 50점이고 엔카는 …」
   ★ 사이트 차이를 ⑤ 사이트 보증 50점이 담는다.  분모를 나누지 않는다
~~금지   사이트가 다른 매물의 점수를 같은 등급표로 직접 비교하는 것~~
필수   분모(수집 가능 항목)가 같은 매물끼리만 비교한다
표시   「엔카 기준 A / 사이트B 기준 B」처럼 출처를 함께 보여준다
```

### 언어 이식 시점

```
1차   Python 로컬 배치
전환   Java 등 온라인 서비스
```

```
이식 대상   Analyzer · Scorer  (순수 함수라 그대로 옮겨진다)
재작성      Collector · Store  (I/O 계층)
불변        config/*.json · sql/*.sql · 사전 데이터
```

**설정과 사전이 코드 밖에 있으면 이식 시 정책을 다시 만들지 않아도 된다** (0장 STEP 6).

---

**8장 종료 (STEP 87–89).**

---



---

## ★★★ 사람에게 물을 때는 판단할 재료를 준다 — 08-18

**마스터 지적 — 「이걸 보고 내가 무엇을 하라는 말이지? 뭔지도 모르겠는데」**

```
지금 화면
  detail:advertisement.verification
  제안: 사람이 봐야 합니다 · 관측 200/200
★ 원문 필드 경로일 뿐이다.  무엇인지도 무엇을 고르라는지도 없다
★ 그러면 아무도 못 정한다.  판정이 영영 막힌다
```

### 규격 — 한 항목에 이 다섯이 있어야 한다

```
필수   ① 실제 값과 분포
       「true 180건 · false 20건」
       「"우수" 130 · "일반" 45 · null 25」
       ★ 값을 보면 무엇인지 짐작이 된다

필수   ② 판정에 쓰이는가
       「지금 안 쓰임」 · 「warranty.site 에 쓸 수 있음」
       ★ 안 쓰는 것은 굳이 지금 안 정해도 된다

필수   ③ 원문에서 어디에 있었나
       엔드포인트 · 형제 필드 두셋
       「detail 의 advertisement 아래.  옆에 price · status 가 있다」
       ★ 옆을 보면 뜻이 잡힌다

필수   ④ 고를 것을 단추로
       [쓴다]  [안 쓴다]  [나중에]
       ★ 「사람이 봐야 합니다」는 선택지가 아니다

필수   ⑤ 안 정하면 무엇이 막히나
       「판정이 막힙니다」 · 「막지 않습니다 — 그냥 안 씁니다」

금지   경로만 내고 「사람이 봐야 합니다」라 하는 것
검산   V4-28  미분류 항목에 값 분포와 선택지가 있는가
```

### ★ 판정에 쓰는 것만 먼저 낸다

```
필수   기본 화면은 「판정을 막는 것」만 낸다 (32건)
필수   나머지는 접어 둔다 — 「지금 안 봐도 되는 것 88건」
       ★ 120건을 한꺼번에 보라 하면 아무도 안 본다
필수   많이 관측된 순으로
필수   같은 뜻으로 보이는 것을 묶어 한 번에 정할 수 있게
       「advertisement.verification 계열 4개를 함께 정합니다」
검산   V4-29  기본 화면이 판정 막는 것만 내는가
```

```
★ 왜 이것이 중요한가
  마스터가 못 정하면 V4-11 이 영영 열려 있다
  ★ 「사람이 정할 일」이라고 넘기는 것만으로는 일이 안 끝난다
    정할 수 있게 만들어 줘야 한다
```
