## STEP 28 — 테이블 목록

```
version  SPEC-2026.08.25-r727
follows  `docs/chapters/30-score/f-table.md`
sources  실측 08-22
checks   S46-38 · S46-39
```


| 테이블 | 군 | 키 | 행 단위 | 보존 |
|---|---|---|---|---|
| `raw_response` | raw | `(listing_id, endpoint, fetched_at)` | 응답 1건 | 영구 |
| `raw_response_reject` | raw | `(id)` | 형식 검증 거부 | 영구 |
| `raw_facet` | raw | `(site, target_key, request_kind, fetched_at)` | **facet 응답 1건** | 영구 |
| `core_listing` | core | `listing_id` | 매물 **현재값** | 영구 |
| `core_listing_change` | core | `(listing_id, changed_at, field)` | **변경 1건** | 영구 |
| `core_vehicle` | core | `vehicle_id` | **실물 차량 1대.** 사이트 간 결합. **`site` 컬럼 없음** — `site_count` 가 대신한다 | 영구 |
| `core_pii` | core | `listing_id` | **개인정보 — 번호판 원본** | 영구 |
| `core_dealer_pii` | core | `(site, dealer_id)` | **개인정보 — 딜러 실명 · 연락처** | 영구 |
| `core_dealer` | core | `(site, dealer_id)` | **딜러 신원 · 현재 지표** (7장 82b·82c) | 영구 |
| `core_dealer_history` | core | `(site, dealer_id, run_id)` | **딜러 지표 시계열.** 4분면 변동 추적 | 영구 |
| `core_inspection` | core | `listing_id` | 점검 1건 | 영구 |
| `core_record` | core | `listing_id` | 이력 1건 | 영구 |
| `core_diagnosis` | core | `listing_id` | 진단 1건 | 영구 |
| `dict_option_code` | dict | `(site, target_key, code)` | 3자리 옵션 | 재생성 |
| `dict_model_option` | dict | `(site, model_catalog_key, option_code)` | 4~5자리 카탈로그 | 재생성 |
| `dict_enum` | dict | `(site, axis, value)` | 연료·색상·트림·부위·상태 | 재생성 |
| `result_axis` | result | `(listing_id, axis, calc_version)` | 축 판정 1건 | 재생성 |
| `result_score` | result | `(listing_id, calc_version)` | 총점·등급 | 재생성 |
| `meta_field_usage` | **meta** | `(site, endpoint, json_path)` | **필드 1개의 사용 구분** | 영구 |
| `depreciation_curve_history` | result | `(id)` | **감가 곡선 산출 이력** (STEP 64) | 영구 |
| `coefficient_history` | result | `(id)` · UK `(site, target_key, changed_at)` | **계수 보정 1건.** 시세 분포가 사이트마다 다르다 | 영구 |
| `account` | admin | `account_id` | **계정 · 역할** (13장) | 영구 |
| `auth_session` | admin | `session_id` | **로그인 세션 (일반·관리자 공통)** | 만료 후 삭제 |
| `config_change` | admin | `change_id` | **설정 변경 이력 · 되돌리기** | 영구 |
| `query_log` | admin | `query_id` | **조회 쿼리 감사** | 90일 |
| `admin_api_snapshot` | admin | `snapshot_id` | **API 응답 저장** | 영구 |
| `dev_request` | admin | `request_id` | **개발 요청** | 영구 |
| `recalc_job` | admin | `job_id` | **재계산 큐** | 90일 |
| `audit_request` | audit | `(id)` | 요청 1건 | 90일 |
| `audit_validation` | audit | `(run_id, phase, item)` | 검증 결과 | 영구 |
| `watch_item` | 활용 | `(watch_id)` · UK `(vehicle_id)` | **관심 등록 · 알림 설정.** 차량 단위 (11장) | 영구 |
| `watch_track` | 활용 | `(listing_id, run_id)` | **관심 매물 시계열** (11장) | 영구 |
| `watch_event` | 활용 | `(id)` | **감지된 변동 · 알림 이력** (11장) | 영구 |
| `watch_query` | 활용 | `(query_id)` | **조건 추적 정의** (11장 117a) | 영구 |
| `watch_query_hit` | 활용 | `(query_id, listing_id)` | **조건 충족 매물** (11장 117a) | 영구 |
| `watch_candidate` | 활용 | `(listing_id)` | 최종 후보 확정 (11장) | 영구 |
| `listing_warning` | 활용 | `(listing_id, warning_code)` | **경고 · 확인 처리** (7장 82d) | 영구 |

---

## STEP 29 — 이력 보존 구조

### 무엇이 변하는가 — 실측 전제

```
1차 수집 항목(차량 제원 · 연식 · 주행거리 · 트림 · 색상 · 옵션)은 변하지 않는다.
변하는 것은 판매 가격과 게시 상태뿐이다.
그리고 팔렸다가 다시 올라오는 경우가 있다.
```

**따라서 전량 스냅샷을 쌓을 이유가 없다. 가격과 상태만 추적한다.**

| 방식 | 하루 증가 | 채택 |
|---|---|:--:|
| 일자별 전량 스냅샷 | 4,700행 (대부분 동일 값 복제) | X |
| **현재값 + 변경분** | **가격·상태가 바뀐 것만** | **O** |

### 테이블 2개

```
core_listing          매물의 지금 값.  매물당 1행
core_listing_change   바뀐 항목만.  변경당 1행
```

### 추적 대상 — 좁게 잡는다

```
필수   price_current_won        가격.  거의 유일한 변동 항목
      sales_status             CONTRACT · 판매완료
      status                   new · active · gone · relisted

제외   조회수 · 구독수 · 수정시각 · 광고문구
      제원 · 연식 · 주행거리 · 트림 · 색상 · 옵션
        → 변하지 않는다.  바뀌었다면 그것은 변경이 아니라 이상이다
```

**제원이 바뀌면 변경 이력이 아니라 검증 실패로 처리한다** (6장 V2).

```
같은 listing_id 인데 displacement_cc 가 바뀜   →  ValidationError
                                              조용히 덮어쓰지 않는다
```

**「변경 = 무조건 오류」가 아니다. 원인을 분류한 뒤 판정한다.**

| 원인 | 판별 | 조치 |
|---|---|---|
| ① 파싱 오류 | 같은 원문을 다시 읽으면 이전 값이 나옴 | 파서 수정 · 재파싱 |
| ② 원문 수정 | 원문이 실제로 바뀜 (딜러 오기입 정정) | 변경 수용 · 이력 기록 |
| ③ 매물 교체 | `source_id` 재사용 · `vin`/`plate` 불일치 | 별도 매물로 분리 |
| ④ 사이트 스키마 변경 | 여러 매물에서 동시 발생 | 수집 중단 · 매핑 갱신 |

```
판별 순서   ① 이전 원문과 현재 원문을 비교한다   →  같으면 ①, 다르면 ②③④
           ② 동시 발생 건수를 본다             →  다수면 ④
           ③ vin · plate 를 대조한다           →  불일치면 ③
기록       core_listing_change 에 change_kind='invariant_violation' + 원인
금지       원인 분류 없이 새 값으로 덮어쓰는 것
```

### 상태 전이

```
new        처음 관측
active     계속 보임
gone       목록에서 사라짐.  삭제하지 않는다
relisted   gone 이후 같은 차가 다시 나타남
```

**`relisted` 는 두 경우다.**

```
같은 listing_id 로 재등장    →  같은 광고가 되살아남
다른 listing_id · 같은 차량   →  딜러가 새로 올림.  vehicle_id 로 묶는다 (STEP 30)
```

**후자가 실제로 더 많다.** 딜러는 광고를 내리고 새 번호로 다시 올린다.
**이 경우 가격이 바뀌어 있고, 그 차이가 시세 하락의 직접 증거다** (11장 후보 추적).

### `core_listing_change`

```
listing_id      매물
changed_at      감지 시각
field           price_current_won · sales_status · status
old_value       이전
new_value       이후
change_kind     new · gone · relisted · price · status
```

```
gone_at         core_listing 에 별도 컬럼.  마지막으로 보인 시각
                「얼마에 팔렸나」의 근거다.  삭제하면 영원히 모른다
```

## STEP 30 [규격] — 키 체계 ★ 대리키

```
목적    모든 테이블의 PK 를 의미 없는 내부 번호로 만든다
원천    없음.  DB 가 생성한다
입력    자연키 (site · source_id · 차량번호 · 코드 …)
출력    대리키 (INTEGER)
값규칙  PK 는 INTEGER AUTOINCREMENT.  자연키는 UNIQUE 제약으로 건다
근거    의미 있는 값을 PK 로 쓰면 그 값이 바뀔 때 전 테이블이 흔들린다
       차량번호를 키로 쓰면 개인정보가 조인 경로에 박힌다
금지    자연키를 PK 로 쓰는 것.  PK 를 문자열로 조립하는 것
검산    전 테이블 PK 가 단일 INTEGER 인가 (V2-14)
```

### ★ 왜 바꾸는가

```
v1·초판   listing_id = 'encar_42436127'   ← 사이트가 ID 체계를 바꾸면 전건 마이그레이션
         vehicle_id = 'plate:12가3456'  ← 개인정보가 PK 다.  조인마다 PII 를 만진다
                                          번호판이 바뀌면 같은 차가 다른 키가 된다
결과      마스킹 · 해시 · 원본 셋으로 갈려 「어디를 쓰나」가 매번 판단이 됐다
```

```
대리키   PK 는 뜻이 없다.  바뀌지 않는다
자연키   UNIQUE 로 건다.  바뀌면 그 행만 고친다
PII     식별자 테이블로 내보낸다.  조인 경로에서 사라진다
```

### 키 목록

| 키 | 형식 | 성격 |
|---|---|---|
| **`listing_id`** | **INTEGER PK** | 매물 대리키 |
| | `(site, source_id)` UNIQUE | 자연키 |
| **`vehicle_id`** | **INTEGER PK** | 실물 차량 대리키 |
| **`dealer_id`** | **INTEGER PK** | 딜러 대리키 |
| | `(site, site_dealer_id)` UNIQUE | 자연키 |
| `site` | `encar` · … | 사이트 코드 |
| `source_id` | 사이트 원문 ID | API 호출용. 키가 아니다 |
| `target_key` | `KOLEOS_HEV` | **자연키 유지.** 사람이 읽고 `config` 가 정한다 |
| `model_catalog_key` | `jatoVehicleId` | **자연키 유지.** 사이트가 준다 |
| `calc_version` · `dict_version` | `c1` · `d3` | **자연키 유지.** 버전 라벨이다 |

```
★ target_key · 버전은 대리키로 바꾸지 않는다
  사람이 읽는 라벨이고 config 가 정한다.  바뀌면 그 자체가 사건이다
  PII 도 아니고 사이트가 바꾸지도 않는다
```

### 복합 PK 도 대리키로 바꾼다

```
전   PRIMARY KEY (site, dealer_id)
후   dealer_id INTEGER PRIMARY KEY AUTOINCREMENT
    UNIQUE (site, site_dealer_id)
```

```
근거   복합 PK 는 FK 를 걸 때마다 컬럼이 여럿 따라간다
      core_dealer_history 가 (site, dealer_id, run_id) 3컬럼을 물고 있었다
      대리키면 dealer_id 하나다
필수   자연키는 UNIQUE 로 남긴다.  중복 방지는 그대로 작동한다
```

### ★ 예외 — 대리키를 두지 않는 것

| 테이블 | PK 유지 | 이유 |
|---|---|---|
| `result_axis` · `result_score` | `(listing_id, calc_version[, axis])` | **버전별 다중 행이 설계다.** 대리키를 두면 「이 매물의 이 버전」을 매번 조회해야 한다 |
| `watch_track` | `(listing_id, run_id)` | 같음. 시계열이다 |
| `audit_validation` | `(run_id, phase, code, target_key)` | 로그다. 참조되지 않는다 |
| `meta_field_usage` | `(site, endpoint, json_path)` | 등록부. 경로가 곧 정체성이다 |
| `dict_*` | `(site, scope…, code)` | 사전. 코드가 곧 정체성이다 |
| `raw_facet` | `(site, target_key, request_kind, fetched_at)` | 원문. 시각이 정체성이다 |
| `listing_warning` | `(listing_id, warning_code)` | 매물당 코드별 1행. 참조되지 않는다 |
| `watch_query_hit` | `(query_id, listing_id)` | 교차 테이블 |
| `core_dealer_history` | `(dealer_id, run_id)` | 시계열 |

```
판별   다른 테이블이 FK 로 참조하는가
      참조된다  →  대리키.  참조 컬럼이 하나가 된다
      안 된다   →  자연키 유지.  대리키가 이득이 없다
```

**참조되는 것만 바꾼다: `core_listing` · `core_vehicle` · `core_dealer` · `account` · `watch_item`.**

### `vehicle_identity` — 식별자는 행이다, 키가 아니다

```sql
CREATE TABLE core_vehicle (
  vehicle_id   INTEGER PRIMARY KEY AUTOINCREMENT,
  site_count   INTEGER NOT NULL,
  listing_count INTEGER NOT NULL,
  min_price_won INTEGER,
  max_price_won INTEGER,
  price_spread_won INTEGER,
  first_seen   TEXT NOT NULL,
  last_seen    TEXT NOT NULL,
  updated_at   TEXT NOT NULL
);

CREATE TABLE vehicle_identity (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  vehicle_id  INTEGER NOT NULL,
  kind        TEXT NOT NULL,          -- plate · vin · site_id
  value_hash  TEXT NOT NULL,          -- HMAC.  원본은 core_pii
  confidence  TEXT NOT NULL,          -- confirmed · probable
  first_seen  TEXT NOT NULL,
  last_seen   TEXT NOT NULL,
  UNIQUE (kind, value_hash),
  FOREIGN KEY (vehicle_id) REFERENCES core_vehicle(vehicle_id),
  CHECK (kind IN ('plate','vin','site_id')),
  CHECK (confidence IN ('confirmed','probable'))
);
```

```
★ 한 차량에 식별자가 여러 개다
  번호판이 바뀌면 행이 하나 는다.  vehicle_id 는 그대로다
  → relist 추적이 끊기지 않는다 (11장 STEP 112)
결합   value_hash 로 찾아 vehicle_id 를 얻는다
      해시는 결합 「입력」이지 키가 아니다
PII    원본은 core_pii.  조인 경로에 개인정보가 없다
```

### `vehicle_id` — 증거를 모아 확정한다

**「1순위니까 바로 확정」이 아니다. 후보를 모으고 증거를 대조한 뒤 확정한다.**

```
후보 수집   plate_no · plate_history · vin · site_vehicle_id
   ↓
증거 대조   서로 모순이 없는가
   ↓
확정       vehicle_id + identity_kind
모순 시     결합하지 않고 conflict 로 남긴다
```

**근거의 우선순위 (확정 절차가 아니라 신뢰도 순서다)**

```
1순위   차량번호        plate_no          공적 식별자.  확보율 최고
2순위   차대번호        vin               불변.  결합 검증자
3순위   사이트 고유 ID   site_vehicle_id   위 둘이 없을 때만
없으면   매물 단위로만 다룬다.  추정 결합 금지
```

### ★ 원문 기준과 컬럼 기준을 구분한다

```
v1 사고   차량번호가 상세 A 원문에는 전건 있는데 컬럼에는 절반이 없었다
         「확보율 부족」으로 보여 수집 문제로 오인됐다.  실제는 파싱 유실이다
         vin 은 반대로 컬럼이 원문보다 많았다 — 다른 엔드포인트가 섞였다
```

```
필수   확보율은 「원문 기준」과 「컬럼 기준」을 나눠 낸다
검증   6장 V2-01 (ok 원문 수 == CORE 행 수) 이 이것을 잡는다
```

**상세 A 를 받은 매물은 차량번호가 전건 있다. 1순위 근거로 충분하다.**
**차대번호는 상세 A 에도 없는 매물이 있어 단독 1순위로 쓸 수 없다.**

**같은 차량번호를 가진 매물이 다수 존재한다** — 「같은 차의 여러 매물」이다.
묶지 않으면 같은 차를 여러 번 검토하게 된다.

### 번호판 변경 — 1순위의 약점

```
실측   번호판 변경 이력 보유 매물 769건
       소유자가 바뀌면 번호가 바뀔 수 있다
```

**따라서 차량번호 매칭에는 변경 이력을 함께 넣는다.**

```
매칭 대상   plate_no  ∪  plate_history_json 의 과거 번호
검증       vin 이 양쪽에 있으면 일치 여부를 확인한다
          불일치하면 결합하지 않고 conflict 로 기록
```

**`vin` 은 절대 바뀌지 않으므로 결합 판정의 검증자로 쓴다.**
**단 확보율이 62%라 단독 1순위로 쓰면 38%가 묶이지 않는다.**

### ★ VIN 검증 — 17자리가 아니면 쓰지 않는다

```
원문 실측   상세 A  vin 17자리 411 · 없음 89        정상
           점검부  vin 17자리 418 · 6자리 50 · 11자리 7 · 16자리 1   ★ 오염 있음
v1 컬럼     0 · 000556 · 001940 …                  ★ 파싱이 망가뜨렸다
```

```
필수   VIN 은 17자리 · 영숫자 · I·O·Q 미포함 이어야 한다
      형식 위반이면 NULL 로 둔다.  결합에 쓰지 않는다
금지   길이 검증 없이 결합 검증자로 쓰는 것
      → 6자리 값이 우연히 겹쳐 다른 차를 같은 차로 묶는다
근거   VIN 은 표준 형식이다.  검증이 가능한 유일한 결합 키다
검산   vin IS NOT NULL 인 행이 전건 17자리인가 (V2-03 타입 검사)
```

```
★ 점검부 vin 에도 짧은 값이 섞여 있다.  원문이 그런 것이다
  상세 A 를 1순위로, 점검부를 보조로 쓰되 양쪽 다 형식 검증한다
  둘 다 있고 다르면 결합하지 않고 conflict 로 남긴다
```

### 결합 규칙

```
1  plate_no 또는 plate_history 가 일치      →  결합 후보
2  vin 이 양쪽에 있고 일치                   →  결합 확정
3  vin 이 양쪽에 있고 불일치                 →  결합 취소 · conflict 기록
4  vin 이 한쪽에만 있거나 없음               →  결합 유지 (차량번호 근거)
5  차량번호·차대번호 둘 다 없음               →  site_vehicle_id
6  셋 다 없음                              →  결합하지 않는다
```

```
금지   차종 · 연식 · 주행거리가 비슷하다는 이유로 같은 차로 묶는 것
기록   identity_kind 컬럼에 plate · vin · site_id 중 무엇으로 묶였는지 남긴다
```

**엔카의 중복 매물 표시(`dummyVehicleId`)도 여기에 연결한다.**
같은 차를 딜러가 여러 번 올린 경우 사이트가 스스로 알려주는 경우가 있다.

## STEP 31 — 공통 컬럼

**모든 `core_*` 테이블에 둔다.**

```
listing_id        조인 키
site              사이트
collected_at      원문 수집 시각
parsed_at         파싱 시각
parse_version     파싱 규칙 버전
row_status        ok · partial · error
```

**`result_*` 에는 추가로**

```
dict_version      사전 스냅샷 버전 (4장 STEP 45)
calc_version      점수 규칙 버전
calculated_at
```

```
재현 단위   (listing_id, parse_version, dict_version, calc_version)
           네 개가 같으면 같은 점수가 나와야 한다
```

**버전이 낮은 행만 골라 재처리한다.** 재수집이 아니라 재파싱 · 재채점이다.

---

## STEP 31a [규격] — `NOT NULL` 은 우리가 만드는 값에만 ★

```
목적    외부 데이터가 불완전해도 저장이 멈추지 않게 한다
원천    없음.  설계 규칙이다
입력    컬럼
출력    NOT NULL 여부
값규칙  우리가 만드는 값만 NOT NULL.  원문에서 온 값은 전부 NULL 허용
근거    엔카가 필드 하나를 안 주면 우리가 멈춘다.  그것은 우리 결함이 아니다
금지    원문 유래 컬럼에 NOT NULL 을 거는 것
검산    V2-19 — 매핑표에 원천 경로가 있는 컬럼이 NOT NULL 인가
```

### ★ 무결성을 전제하지 않는다

```
사고   판정은 「모르면 뺀다」(excluded)로 정해 놓고
      저장은 「모르면 멈춘다」(NOT NULL)로 두었다.  앞뒤가 안 맞았다
```

| 구분 | 예 | `NOT NULL` |
|---|---|:--:|
| **우리가 만든다** | `listing_id` · `site` · `fetched_at` · `parse_version` · `status` | **O** |
| | 없으면 코드 결함이다 | |
| **원문에서 온다** | `price_current_won` · `mileage_km` · `warranty_*` · `plate_hash` | **X** |
| | 사이트가 안 주면 없는 것이다.  그것도 사실이다 | |
| **집계값** | `listing_count` · `site_count` | **O** (기본 0) |
| **원문 통째** | `raw_facet.body` · `raw_response.body` | **X** ★ |
| | 빈 응답도 사실이다.  형식 검증이 따로 본다 | |

```
★ raw_facet.body 를 NOT NULL 로 두면 빈 응답을 저장할 수 없다
  「받았는데 비었다」와 「안 받았다」가 구분되지 않는다 (STEP 16 status)
```

## STEP 32 — NULL 3종 구분

**같은 NULL 이 세 가지 뜻을 가지면 판정이 무너진다. 컬럼 하나로 구분할 수 없으므로 상태 컬럼을 함께 둔다.**

| 의미 | 값 | 상태 컬럼 | 분모 |
|---|---|---|---|
| 값이 없음 (원본이 비어 있음) | `0` 또는 `'[]'` | `ok` | **포함** |
| 수집 실패 | `NULL` | `error` · `not_requested` | 제외 |
| 구조적 부재 (그 차종에 없는 사양) | `NULL` | `na` | **제외 · 분모 축소** |

```
예   options.choice = []       →  '[]' 저장.  '선택 옵션 없음'.  값 0
     options.choice 필드 없음   →  NULL.  수집 실패
     모델Y 의 HUD              →  NULL + na.  차종 미제공
```

**v1 은 `_js()` 가 falsy 를 전부 `None` 으로 만들어 「없음」이 「실패」로 저장됐다.**
**분모에서 빠져 사양 점수가 부풀려졌다.**

```
금지   if not v: return None
필수   빈 컨테이너는 그대로 직렬화.  None 은 「없었다」일 때만
검증   '[]' 건수 + NULL 건수 = 전체.  '[]' 가 0건이면 이 버그를 의심한다
```

---

## STEP 32a — 테이블 정의 형식

**두 가지를 쓴다. 어느 쪽인지 기준을 정해 둔다.**

| 형식 | 대상 | 이유 |
|---|---|---|
| **DDL 전문** | 컬럼 20개 미만 · 제약이 중요한 것 | 그대로 옮겨 쓴다 |
| **컬럼 그룹 서술** | `core_listing` 등 컬럼이 많은 것 | 전문을 쓰면 읽히지 않는다 |

```
그룹 서술 대상   core_listing · core_listing_change · core_inspection
               core_record · core_diagnosis
근거           판정에 쓰는 컬럼이 수십 개다.  그룹으로 묶어야 무엇을 위한 컬럼인지 보인다
필수           그룹 서술이어도 아래는 반드시 명시한다
                 PK · 필수 NOT NULL · CHECK 열거값 · FK
DDL 위치       sql/ddl/*.sql 이 정본이다 (0장 STEP 6)
              문서는 설계 의도를 담고, 실행 가능한 DDL 은 파일에 둔다
```

**문서의 DDL 은 참고다. 코드가 문서를 파싱하지 않는다.**

## STEP 32b [규격] — 스키마 이행 ★

```
목적    DDL 을 고쳤을 때 기존 DB 를 따라가게 한다
원천    sql/ddl/*.sql
입력    현재 DB 스키마
출력    이행 목록 + 적용
값규칙  데이터를 지우지 않는다.  표를 재작성해 옮긴다
근거    CREATE TABLE IF NOT EXISTS 는 기존 테이블을 바꾸지 않는다
       DDL 만 고치면 기존 DB 는 옛 스키마로 남는다
금지    DROP TABLE 후 재생성.  RAW 가 사라지면 복구가 안 된다 (P3)
검산    이행 후 V2-19 · V2-14~16 이 통과하는가
```

```
python3 run.py migrate
```

### 이행 대상

| 종류 | 처리 |
|---|---|
| 신규 테이블 | `CREATE` |
| 신규 컬럼 | `ALTER TABLE ADD COLUMN` |
| **제약 변경** (`NOT NULL` 해제 · `UNIQUE` 변경) | **표 재작성** |
| PK 변경 | 표 재작성 |

```
표 재작성   1  새 이름으로 CREATE
          2  INSERT INTO 새표 SELECT ... FROM 옛표
          3  DROP 옛표 · RENAME
          4  트랜잭션 하나로 묶는다
필수       재작성 전 행 수를 세고, 후에 같은지 확인한다
```

### ★ 실측에서 잡힌 사례

```
DDL       dict_model_option.option_name 의 NOT NULL 을 제거했다
기존 DB    IF NOT EXISTS 라 옛 제약이 남아 있었다
V2-19     실측 DB 에서 이것을 잡았다
```

```
★ 검사를 실측 DB 로 돌려야 잡힌다
  새 DB 로만 시험하면 DDL 대로 만들어져 통과한다
필수   migrate 후 실측 DB 로 전 검사를 돌린다 (개발측 원칙 1)
```

---

