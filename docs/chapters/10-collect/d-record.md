## STEP 21 — `inspection` 응답 → 필드

```
version  SPEC-2026.09.01-r1042
follows  `docs/chapters/30-score/f-table.md`
sources  실측 08-22
checks   S46-38 · S46-39
```


| 원문 | 변환 | CORE 필드 |
|---|---|---|
| `master.detail.vin` | — | `inspection_vin` |
| `master.detail.mileage` | — | `inspection_mileage_km` |
| `master.detail.firstRegistrationDate` | date | `first_registration_date` | **보증 경과월 기준** |
| `master.detail.validityStartDate` / `EndDate` | date | `inspection_valid_from` / `_to` |
| `master.detail.issueDate` | date | `inspection_issued_at` |
| `master.detail.engineCheck` / `trnsCheck` | — | `check_engine` / `check_transmission` |
| `master.detail.motorType` | — | `motor_type_code` | 차종 검증 |
| `master.detail.comments` | — | `inspection_comment` | 표시 전용 |
| `master.accdient` (원문 철자) | — | `inspection_accident_flag` |
| `master.simpleRepair` | — | `inspection_simple_repair` |
| `master.detail.waterlog` | — | `inspection_flood` |
| `master.detail.tuning` · `recall` | — | `inspection_tuning` · `_recall` |
| **`outers[]`** | **json 전량** | **`inspection_panel_json`** | ★ v1 전건 NULL |
| `inners[]` | json 전량 | `inspection_inner_json` | 표시 전용 (8장) |
| `etcs[]` | json 전량 | `inspection_etc_json` | 미분석 (8장) |
| `images[]` | json | `inspection_image_json` | 표시 전용 |

## `outers[]` 요소 구조 — 실측

```json
{"type":       {"code":"P022", "title":"프론트 휀더(우)"},
 "statusTypes":[{"code":"X", "title":"교환(교체)"}],
 "attributes": ["RANK_ONE"]}
```

**v1 은 `outers[].children[].statusType` 이라는 존재하지 않는 경로를 읽었다.**
그래서 `inspection_panel_json` 이 전건 NULL 이었고 **사고 20점이 한 번도 작동하지 않았다.**

```
필수   outers 를 요소 원문 그대로 배열로 저장한다.  가공하지 않는다
       해석(골격/외판 판정)은 7장 Analyzer 가 한다
```

---

## STEP 19a [규격] — 파싱은 필드 단위로 실패한다 ★

```
목적    필드 하나를 못 읽어도 나머지가 저장되게 한다
원천    원문
입력    RAW 1건
출력    CORE 행 + 필드별 실패 기록
값규칙  필드 하나가 실패하면 그 필드만 NULL.  행 전체를 버리지 않는다
근거    한 필드 오류로 매물 전체가 사라지면, 그 매물의 다른 16축도 못 본다
금지    필드 하나의 예외가 매물 파싱을 중단시키는 것
검산    V2-20 — 파싱 실패 필드가 있는 행도 CORE 에 있는가
```

### 원문 이상 4종

**아래는 「이런 형태가 온다」는 사양이다. 비율은 적지 않는다 (0장 STEP 5.5).**

| 종류 | 형태 | 처리 |
|---|---|---|
| **구조체가 `null`** | `partnership.dealer` · `inspection:price` 등 중간 노드가 통째로 `null` | 안전 조회 |
| **타입 혼재** | 목록 배열 필드가 값 1개면 `str`, 여러 개면 `array` | `as_list()` 정규화 |
| **빈 배열** | `outers` · `options.*` 등 | `'[]'` 로 저장. 축별로 뜻이 다르다 |
| **스칼라 `null`** | `originPrice` · `seizing.*` · `contents.text` 등 | 그 축만 excluded |

```
★ 중첩 접근 한 줄이면 그 매물이 통째로 사라진다
  구조체 null 은 드물지 않다.  얼마나 드문지는 수집 시점마다 다르다
★ 배열 필드에 문자열이 오면 순회 시 글자 단위로 돈다
  '일반' → ['일','반'].  조용히 틀린 값이 들어간다
★ 부모가 null 이면 하위 경로를 결측으로 세지 않는다
  안 그러면 등록부에 유령 경로가 쌓인다
```

```python
def as_list(v):
    if v is None: return []
    if isinstance(v, list): return v
    return [v]

def dig(o, path):          # 중간 None 안전
    for k in path.split("."):
        if not isinstance(o, dict): return None
        o = o.get(k)
    return o
```

```
금지   raw["a"]["b"]["c"] 직접 접근
금지   isinstance 검사 없이 배열 필드를 순회하는 것
검증   V2-23 ~ V2-26 (6장 STEP 56)
```

### ★ 「값이 없다」와 「우리가 못 읽었다」는 다르다

```sql
CREATE TABLE core_parse_issue (
  id          INTEGER PRIMARY KEY,
  listing_id  INTEGER NOT NULL,
  endpoint    TEXT NOT NULL,
  json_path   TEXT NOT NULL,
  reason      TEXT NOT NULL,     -- not_provided · parse_error · type_mismatch
  raw_sample  TEXT,              -- 원문 값 표본
  parse_version TEXT NOT NULL,
  detected_at TEXT NOT NULL,
  CHECK (reason IN ('not_provided','parse_error','type_mismatch'))
);
```

| `reason` | 뜻 | 결함인가 |
|---|---|:--:|
| `not_provided` | 원문에 그 경로가 없다 | **아니다.** 사이트가 안 준 것이다 |
| `parse_error` | 있는데 못 읽었다 | **결함.** 리포트에 남는다 |
| `type_mismatch` | 있는데 형이 다르다 | **결함.** 원문 변경 신호일 수도 |

```
★ 둘을 섞으면 파서 버그가 「원문이 그렇다」로 묻힌다
필수   parse_error · type_mismatch 는 L3 실행 리포트 최상단에 낸다
       건수가 늘면 원문 구조가 바뀐 것이다
금지   전부 NULL 로만 남기고 사유를 버리는 것
```

### ★ 원문 접근은 `parse/` 안에서만 · 연쇄 첨자 금지

```
금지   parse/ 안에서 원문 변수에 연쇄 첨자 — raw["a"]["b"]["c"]
허용   dig(raw, "a.b.c")  ·  as_list(raw.get("x"))
근거   중간 노드가 null 이면 TypeError.  그 매물이 통째로 사라진다
```

```
검사 범위   parse/ 디렉터리만
근거       원문 접근은 parse/ 에서만 한다.  다른 계층은 CORE 를 읽는다
          범위를 좁히면 dict 리터럴 · config 조회 오탐이 없다
금지       전 소스를 AST 로 훑는 것.  오탐이 나오면 예외 목록이 생기고
          그 목록이 구멍이 된다 (6장 V4-13 함정)
검증       V2-27  parse/ 에 원문 연쇄 첨자가 없는가   code · fatal
```

### ★ 예외 처리는 후행에 영향을 준다 — 먼저 본다

**「안전하게 고친다」가 뒤를 흔든다. 고치기 전에 영향을 적는다.**

| 변경 | 후행 영향 | `from_step` |
|---|---|---|
| 중간 노드 안전 조회 | `dealer_id` NULL 발생 → 딜러 집계에서 빠짐 | S6 |
| 배열 정규화 | **저장된 형이 바뀐다** · 사전 오염 가능 · 등록부 경로 변경 | S6 (오염 시 S9) |
| 빈 배열의 뜻 확정 | **점수가 오른다** (무사고 excluded → 만점) · 분모 증가 | S9 |
| 스칼라 `null` 규칙 | `price` excluded 증가 · E등급 판정 대상 감소 | S9 |

```
필수   변경 전에 --diagnose 로 현재 상태를 본다 (5장 STEP 50b)
      사전이 오염됐는가 · 저장된 형이 무엇인가 · 등록부에 옛 경로가 있는가
금지   넷을 한꺼번에 바꾸는 것.  무엇이 등급을 바꿨는지 못 가른다
순서   파싱 계열(1·2) 먼저 → 결과 확인 → 판정 계열(3·4)
```

### ★ 「이미 안전한가」를 먼저 본다

```
실사고   예외 4건 중 3건이 이미 안전했다
        사전 오염 없음 · str 저장 없음 · 경로 이중화 없음
        진단 없이 고쳤으면 재파싱·재판정을 헛되이 했다
        1건(seizing null)만 진짜였고, 그것은 진단이 찾았다
```

```
필수   「고쳐야 한다」 전에 「지금 어떤가」를 본다
      규격이 없어서 위험한 것과, 규격은 없지만 코드가 이미 맞는 것은 다르다
조치   이미 맞으면 규격만 명시한다.  재처리하지 않는다
      dict_version · calc_version 을 올리지 않는다
근거   버전을 올리면 result_* 가 통째로 다시 쌓인다.  이유 없이 올리지 않는다
```

### ★ 딜러 없는 매물

```
차량 판정과 딜러는 다른 축이다 (7장 STEP 82a)
→ 딜러가 없어도 ★ 판정은 정상.  등급이 나온다
```

```
표시   「딜러 정보 없음」.  trust_score 자리는 비운다
금지   딜러 없음을 dealer_untrusted 로 판정하는 것
      모르는 것을 나쁘다고 하지 않는다
집계   core_dealer.listing_count 에 세지 않는다
검증   V3-31  딜러 NULL 매물에 dealer_untrusted 경고가 없는가
```

### ★ 빈 배열의 뜻은 축마다 다르다

| 필드 | 빈 배열 | 축 처리 |
|---|---|---|
| `outers` | **손상 없음** | `history.damage` 만점 |
| `accidents` | **사고 없음** | `history.insurance` 만점 |
| `inners` · `etcs` | 점검 기록 없음 | 결측. 판정 안 씀 |
| `options.choice` | 선택 옵션 없음 | `standard` 도 함께 본다 |

```
금지   빈 배열을 일괄 결측 처리하는 것
      무사고가 「평가 불가」가 된다.  가장 좋은 상태인데 분모에서 빠진다
```

### ★ 판정 결과는 3값이다 — 「모른다」가 반환에 있어야 한다

```python
def absolute_check(ctx) -> tuple[list[str], list[str]]:
    return fails, unknown       # 걸림 · 판정 못 함
```

```
fails    근거가 있고 조건에 걸렸다   →  E등급
unknown  근거가 null 이라 판정 못 했다  →  E 가 아니다.  경고로 남긴다
없음     근거가 있고 조건에 안 걸렸다  →  통과
```

```
사고   if s.seizing_cnt:  →  None 이 falsy 라 「저당 없음」으로 지나갔다
      「모른다」가 「안전」이 됐다
필수   반환에 unknown 을 둔다.  bool 두 값으로는 표현할 수 없다
경고   unknown 마다 listing_warning 을 남긴다 — {조건}_unknown · warn
      「이 조건은 확인하지 못했습니다」
검증   V3-32 가 이것을 본다
```

### ★ 「모른다」를 「안전」으로 바꾸지 않는다

```
seizing.* 가 null 이면 저당 판정을 하지 않는다
0 으로 보면 「저당 없음」이 되어 E 를 놓친다
```

```
검증   V3-32  seizing null 매물이 「저당 없음」으로 판정되지 않는가
같은 규칙  전손 · 침수 · 골격 — 근거가 null 이면 판정하지 않는다 (7장 STEP 82)
```

### 축은 그만큼만 빠진다

```
필드 실패  →  그 필드를 쓰는 Component 만 NULL + excluded
          →  나머지 Component 는 정상 판정
          →  분모가 그만큼 준다 (STEP 83)
```

**매물이 사라지는 것이 아니라 축 하나가 빠지는 것이다.**

---

## STEP 20a [규격] — 날짜 형식 정규화

```
목적    엔드포인트마다 다른 날짜 표기를 CORE 에서 하나로 만든다
원천    detail  2026-03-05T11:22:33  (ISO)
       점검부   20210615             (구분자 없음)
       이력     20260203             (구분자 없음)
입력    원문 문자열
출력    _date 는 YYYY-MM-DD · _at 은 ISO 8601
값규칙  변환 불가 시 NULL.  추측으로 채우지 않는다
근거    같은 개념에 두 형식이 섞이면 보증 경과월 계산이 어긋난다
금지    RAW 를 변환해 저장하는 것.  원문은 그대로다
검산    CORE 의 _date 컬럼이 전건 YYYY-MM-DD 인가
```

### ★ 원문 보존과 정규화는 층이 다르다

```
RAW      원문 그대로.  20210615 는 20210615 로 남는다        P3
CORE     정규화.  2021-06-15                              STEP 4 명명 규칙
```

**둘은 충돌하지 않는다.** 재파싱하면 RAW 에서 다시 만들어진다.

```
필수   정규화는 파싱 계층(L3)에서 한다.  수집 계층(L1)이 아니다
검증   RAW 원문에 변환 흔적이 없는가 (V4-01 값 대조가 이것을 잡는다)
```

### 시험 기대값 처리

```
EXPECTED.json 은 원문값이다  →  RAW 검증에 그대로 쓴다
CORE 검증은 변환 후 값과 비교한다  →  시험에서 변환해 비교하는 것이 맞다
```

**개발측 조치가 정확하다. 되돌리지 않는다.**

```
★ 다만 EXPECTED.json 에 변환 후 값을 함께 적어두면
  시험 코드가 변환 로직을 다시 구현하지 않아도 된다
  시험이 구현을 복제하면 둘 다 틀려도 통과한다
```

---

## STEP 21a — `record` 응답 → 필드

**v1 원문이 오염돼 표본이 적다. 아래는 정상 응답 27건에서 확인한 것이다.**

| 원문 | 변환 | CORE 필드 |
|---|---|---|
| `carNo` | — | `record_plate_no` | 비마스킹 |
| `firstDate` | date | `record_first_date` |
| `myAccidentCnt` · `myAccidentCost` | — | `accident_my_cnt` · `accident_my_cost` |
| `otherAccidentCnt` · `otherAccidentCost` | — | `accident_other_cnt` · `accident_other_cost` |
| `accidentCnt` | — | `accident_total_cnt` |
| **`accidents[]`** | **json 원문 그대로** | **`accidents_json`** |
| `carInfoChanges[]` | json 원문 그대로 | `plate_history_json` |
| `ownerChanges[]` | json 원문 그대로 | `owner_change_dates_json` |
| `notJoinDate1~5` | 배열로 묶어 json | `not_join_json` |
| `ownerChangeCnt` · `ownerChanges[]` | — · json | `owner_change_cnt` · `owner_change_dates_json` |
| `carNoChangeCnt` · `carInfoChanges[]` | — · json | `plate_change_cnt` · `plate_history_json` |
| `totalLossCnt` · `totalLossDate` | — | `total_loss_cnt` · `total_loss_date` |
| `floodTotalLossCnt` · `floodPartLossCnt` · `floodDate` | — | `flood_total_cnt` · `flood_part_cnt` · `flood_date` |
| `robberCnt` · `robberDate` | — | `robber_cnt` · `robber_date` |
| `government` · `business` · `loan` | — | `use_gov` · `use_business` · `loan_cnt` |
| `use` · `carInfoUse1s[]` · `carInfoUse2s[]` | — · json | `use_cd` · `use1_json` · `use2_json` |
| `notJoinDate1~5` | json 배열 | `not_join_json` |
| `openData` | — | `record_open` |
| `regDate` | date | `record_reg_date` |
| `fuel` · `maker` | — | **저장하되 분류에 쓰지 않는다** (STEP 43) |

### `accidents[]` 요소

```json
{"type": "2", "date": "2026-02-03",
 "insuranceBenefit": 19440000, "partCost": 13342600,
 "laborCost": 1521500, "paintingCost": 1838900}
```

```
필수   배열 원문 그대로 저장한다.  type 해석은 Analyzer 가 한다 (7장 STEP 77)
금지   파싱 단계에서 type 을 합산하거나 필터링하는 것
```

### ★ 배열 필드는 원문 그대로 저장한다

```
대상   accidents[] · carInfoChanges[] · ownerChanges[] · notJoinDate1~5
       inspection 의 outers[] · inners[] · etcs[]
       detail 의 options.standard · choice · etc · tuning
```

```
필수   파싱 단계에서 배열을 가공하지 않는다.  직렬화만 한다
       해석(집계 · 필터 · 판정)은 Analyzer 가 한다
근거   판정 규칙이 바뀌면 재파싱만으로 복구된다.  재수집이 필요 없다 (P3)
v1 사고 outers 를 가공해서 저장하려다 존재하지 않는 경로를 읽어 전건 NULL 이 됐다

이름   {개념}_json.  원문 필드명이 아니라 CORE 개념명을 쓴다
       carInfoChanges → plate_history_json  (사이트 무관 이름, 0장 STEP 4)
```

### 존재하지 않는 필드 — 주의

```
usageChangeTypes    record 에 없다.  점검부 master.detail 에 있다 (STEP 21)
                   v1 은 record 에서 찾다가 「존재하지 않는 필드」로 금지했다
```

### 표본 한계

```
v1 정상 원문이 극소수다.  위 매핑은 그 범위에서 확인된 것이다
착수 시   재수집 후 경로 전수를 다시 뽑아 이 표를 검증한다 (등록부 blocked)
금지     이 표를 완전한 것으로 간주하고 나머지 경로를 버리는 것
```

---

## STEP 21b [규격] — `diagnosis` 응답 → 필드 ★ 실측 확정 08-14

```
목적    엔카 자체진단 원문을 CORE 로 옮긴다
원천    GET /v1/readside/diagnosis/vehicle/{source_id}
입력    source_id
출력    core_diagnosis · core_diagnosis_item
값규칙  encarDiagnosis == 0 인 매물만 호출한다.  1 · 2 는 404 다
근거    실측 3요청 (08-14)
금지    encarDiagnosis 가 1 · 2 · -1 인 매물에 호출하는 것
검산    V1-14  호출 대상이 encarDiagnosis == 0 으로 좁혀졌는가
```

### 실측 — 3요청이 답을 냈다

| `encarDiagnosis` | `diagnosisCar` | 요청 | 결과 |
|:--:|:--:|---|---|
| **0** | True | `42016736` | **200 · JSON** |
| 1 | True | `41869188` | 404 |
| 2 | True | `42505009` | 404 |
| −1 | False | — | 호출 안 함 |

```
★ 경로는 맞았다.  조건이 틀렸다
  v1 이 원문 0건이 된 이유가 이것이다 — 전량을 호출하고 전량 404 를 받았다
```

```
분포 (v1 상세 3,386건)
  -1  812   진단 안 받음        호출 안 함
   0  484   ★ 진단 결과 있음     호출 대상
   1 1,634  404                미확정 B-1
   2  456   404                미확정 B-1
```

```
★ 1 · 2 가 무엇인지는 아직 모른다
  「진단 예약」 · 「진단 진행 중」 · 「진단 결과 비공개」 셋 중 하나로 보이나 근거가 없다
  diagnosisCar=True 이면서 결과가 없다는 사실만 확정이다
필수   미확정에 남긴다.  추정으로 뜻을 붙이지 않는다
```

### 응답 경로 — 전수

| 경로 | 형 | 표본 | 쓰는 곳 |
|---|---|---|---|
| `vehicleId` | int | `42016736` | 대조용 |
| `diagnosisDate` | str | `2026-07-15T00:00:00` | 진단일 |
| `realDiagnosisDate` | str | `2026-07-15T00:00:00` | 실제 진단일 |
| `diagnosisNo` | int | `1125` | 진단 번호 |
| `ordNo` | int | `26152661` | 주문 번호 · 사용 안 함 |
| `centerCode` | str | `"146"` | 센터 코드 |
| `reservationCenterName` | str | `"김포 국민차2층"` | 센터명 |
| `items[]` | array | 10개 | 부위별 판정 |
| `items[].code` | str | `"006003"` | 항목 코드 |
| `items[].name` | str | `"FRONT_DOOR_LEFT"` | **영문 열거값** |
| `items[].result` | str | `"교환"` · 긴 문장 | 결과 또는 소견 |
| `items[].resultCode` | str·null | `"REPLACEMENT"` · `null` | **판정 코드** |

```
required_keys   vehicleId · items
              나머지는 없어도 행을 만든다
```

### ★ `items` 는 두 종류가 섞여 있다

```
판정 항목    resultCode 가 있다      NORMAL · REPLACEMENT · …
소견 항목    resultCode 가 null 이다  result 가 긴 문장이다
```

```
006039  CHECKER_COMMENT       진단사 종합 소견
006040  OUTER_PANEL_COMMENT   외판 상세 소견
```

```
필수   resultCode IS NULL 로 가른다.  code 로 가르지 않는다
근거   소견 코드가 더 있을 수 있다.  006039 · 006040 만으로 단정하지 않는다
금지   소견을 부위 판정으로 세는 것.  「2개 교환」이 「4개」가 된다
검산   V3-34  판정 항목 수 == resultCode IS NOT NULL 인 items 수
```

### ★ 점검부와 같은 사실을 말한다 — 실측 대조

```
진단 (42016736)              점검부 outers
  FRONT_FENDER_LEFT  교환  ↔  프론트 휀더(좌)  교환(교체)
  FRONT_DOOR_LEFT    교환  ↔  프론트 도어(좌)  교환(교체)
  나머지 6부위 정상          ↔  (정상은 outers 에 없다)
```

```
★ 두 원천이 같은 결과를 낸다.  진단이 점검부를 반박하지 않는다
필수   사고 축은 점검부로 판정한다.  진단은 보강 근거다
근거   점검부는 1,890건 · 진단은 484건.  분모가 큰 쪽이 축이다
금지   진단이 있는 매물만 다르게 채점하는 것.  분모가 갈린다
```

```
★ 진단은 「정상」도 낸다.  점검부는 이상만 낸다
  이것이 진단의 값어치다 — 「확인했는데 정상」과 「언급 없음」이 갈린다
용도   safety.diagnosis 축의 근거를 세분한다 (7장 STEP 79)
      지금  diagnosis_car 0/1 로만 20점
      이후  진단 결과 있음 · 정상 확인 부위 수를 근거로 낸다 (미확정 B-2)
```

### 영문 열거값 — 언어팩

```
NORMAL · REPLACEMENT   지금까지 관측된 2종
★ 완전값 정확 매칭.  부분 문자열 금지 (4장 STEP 42)
필수   처음 보는 resultCode 는 사전 미검토로 멈춘다
```

| `name` | 부위 |
|---|---|
| `HOOD` | 후드 |
| `FRONT_FENDER_LEFT` · `_RIGHT` | 프론트 휀더 |
| `FRONT_DOOR_LEFT` · `_RIGHT` | 프론트 도어 |
| `BACK_DOOR_LEFT` · `_RIGHT` | 리어 도어 |
| `TRUNK_LID` | 트렁크 리드 |

```
★ 8부위가 전부인지 모른다.  이 매물이 8개였을 뿐이다
필수   부위명도 언어팩에 둔다.  처음 보는 name 은 사전 미검토
```

### 호출 조건

```
S5   encarDiagnosis == 0 인 매물만
     484 / 3,386 = 14.3%.  전량 호출의 1/7 이다
필수   조건을 코드에 박지 않는다.  config/endpoints.json 에 둔다
검산   V1-14
```

```json
"diagnosis": {
  "path": "/v1/readside/diagnosis/vehicle/{source_id}",
  "when": { "field": "view.encarDiagnosis", "equals": 0 },
  "required_keys": ["vehicleId", "items"]
}
```

---

### ★ `V1-08` 을 엔드포인트별로도 본다

```
문제   S5 는 4엔드포인트가 섞여 있다.  한 종이 전량 404 여도 희석된다
      diagnosis 204/204 실패가 「816 중 276」에 묻혔다
```

```
필수   전량 실패 판정을 (단계 · 엔드포인트) 단위로 한다
검증   V1-08b  엔드포인트별 전량 404 가 없는가
```

### ★ 규격 미정 상태에서 수집은 한다

**「매핑을 못 만든다」와 「수집하지 않는다」는 다르다.**

| 단계 | 진단 처리 |
|---|---|
| S5 수집 | **던진다.** 매물당 4종에 포함 (STEP 25) |
| 저장 | **`raw_response`에 원문 저장.** 형식 검증은 통과 처리 |
| S6 파싱 | **건너뛴다.** `core_diagnosis` 가 없으므로 |
| 상태 | `diagnosis_status` 는 기록한다 (`ok`·`empty`·`not_found`) |

```
필수   원문을 먼저 모은다.  모여야 경로 전수를 뽑아 규격을 만든다
금지   규격이 없다고 수집을 건너뛰는 것
      → 규격을 만들 원문이 영원히 안 모인다.  v1 이 이 상태였다
검증   V1-07 (매물별 엔드포인트 4종 상태 존재) 는 진단도 포함한다
      not_requested 가 남으면 fatal
형식 검증 예외
      diagnosis 의 required_keys 는 원문 확보 전까지 빈 목록이다
      빈 목록이면 verify_shape 는 통과시킨다 (all() 은 공집합에 참)
      → 이 예외를 코드 주석에 남긴다.  나중에 required_keys 를 채우면 자동으로 걸린다
```

---

## STEP 21c [수집] — `catalog` 호출 키 ★

```
목적    카탈로그를 모델당 1회만 받는다
원천    /v1/readside/vehicles/car/{source_id}/options/choice
입력    model_catalog_key 별 대표 매물 1건
출력    raw_response(catalog) 1행
값규칙  {source_id} 는 매물 ID 다.  jatoVehicleId 가 아니다
근거    car 는 매물을 가리킨다.  모델 식별자를 넣으면 404 다
금지    jatoVehicleId 로 호출하는 것
검산    같은 model_catalog_key 로 두 번 호출하지 않는다
```

### ★ 호출 키와 중복 제거 키가 다르다

```
호출       모델당 대표 매물 1건의 source_id
저장·중복   model_catalog_key (jatoVehicleId)
근거       응답이 모델-연식 카탈로그다.  매물별 실장착이 아니다
          그래서 모델당 1회면 충분하다
```

```
실측   매물 ID 41765232              →  JSON.  옵션 목록 + description
      jatoVehicleId 817440020…      →  404
```

```
대표 선정   그 모델의 매물 중 먼저 관측된 것.  기준을 고정한다
필수       선정 기준을 바꾸면 캐시가 무효가 된다
```

---

