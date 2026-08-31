## STEP 33 — `raw_*` 스키마

```
version  SPEC-2026.09.01-r1032
follows  `docs/chapters/30-score/f-table.md`
sources  실측 08-22
checks   S46-38 · S46-39
```


```sql
CREATE TABLE raw_response (
  id             INTEGER PRIMARY KEY,
  run_id         TEXT NOT NULL,      -- S4 봉투 범위 (5장 STEP 50a)
  site           TEXT NOT NULL,
  listing_id     INTEGER,
  source_id      TEXT,
  endpoint       TEXT NOT NULL,
  request_url    TEXT NOT NULL,
  request_meta   TEXT,               -- 재현에 필요한 요청 정보 (민감 헤더 제외)
  http_code      INTEGER,
  response_meta  TEXT,               -- content_type · encoding · 필요한 응답 헤더
  status         TEXT NOT NULL,      -- ok·empty·not_found·error
  body           TEXT,               -- 원문 그대로
  origin         TEXT NOT NULL,      -- collector · master_manual · import · browser
  fetched_at     TEXT NOT NULL
);
CREATE INDEX ix_raw_lookup ON raw_response(listing_id, endpoint, fetched_at DESC);
```

```
origin='master_manual'   마스터가 PDF 로 회신한 실측 응답 (2장 STEP 25a)
origin='import'          파일·붙여넣기로 반입한 것 (13장 STEP 136a) — 08-16
origin='browser'         브라우저가 사용자 회선으로 받은 것 (13장 STEP 136c) — 08-16

★ 넷을 가르는 이유
  누가 받았는지가 다르면 신뢰 근거가 다르다
  collector 는 서버가 · browser 는 사용자 회선이 · import 는 사람이 옮긴 것이다
  섞으면 「우리가 받았다」가 사실이 아니게 된다
필수   CHECK 에 넷을 다 넣는다.  V11-40 · V11-43 이 이 값을 요구한다
                        원문이므로 RAW 에 넣고 경로 전수 대상에 포함한다
```

### 「무손실」의 범위

```
보존   request_url · 재현에 필요한 요청 정보 · http_code
      content_type · encoding · body · fetched_at · origin
용도   API 응답 형태가 바뀌었는지 사후 확인.  JSON → 다른 형태 전환 감지
```

**민감 정보는 저장하지 않는다.**

```
제외   인증 토큰 · 쿠키 · 세션 · Authorization 헤더
      개인 식별에 쓰일 수 있는 요청 헤더
규칙   저장 전 화이트리스트 필터를 통과시킨다.  블랙리스트 방식 금지
```

### `raw_facet`

```sql
CREATE TABLE raw_facet (
  site          TEXT NOT NULL,
  target_key    TEXT NOT NULL,
  request_kind  TEXT NOT NULL,     -- 'unspecified' (Badge 요청 폐지)
  request_url   TEXT NOT NULL,
  axis_count    INTEGER,           -- 값이 있는 축 수 (Type='Aspect')
  body          TEXT NOT NULL,
  fetched_at    TEXT NOT NULL,
  PRIMARY KEY (site, target_key, request_kind, fetched_at)
);
```

**`request_kind` 는 PK 에 남긴다.** 나중에 다른 축을 명시 요청할 수 있다.
**없으면 같은 초에 저장될 때 PK 가 충돌하거나 하나가 덮인다.**

```sql
CREATE TABLE raw_response_reject (
  id            INTEGER PRIMARY KEY,
  site          TEXT NOT NULL,
  listing_id    TEXT,
  endpoint      TEXT NOT NULL,        -- 라벨.  내용과 어긋난 것
  request_url   TEXT NOT NULL,
  http_code     INTEGER,
  body          TEXT,
  reject_reason TEXT NOT NULL,        -- 어느 required_key 가 없었는가
  fetched_at    TEXT NOT NULL
);
```

**형식 검증(2장 STEP 18) 거부분.** 버리지 않는다 — 쌓이면 URL·응답 변경 신호다.
**버리지 않는다.** 거부가 쌓이면 그 자체가 URL 변경 신호다.

---

## STEP 34 — `core_listing` 설계 원칙

**352컬럼을 다시 만들지 않는다.**

```
포함   판정에 쓰는 필드  +  화면에 쓰는 필드  +  추적에 쓰는 필드
제외   그 외 전부.  원문에 남아 있으므로 필요해지면 재파싱한다
```

**필드를 넣기 전 3장 정의서의 연결표에 행이 있어야 한다.**
**「나중에 쓸 것 같아서」 넣지 않는다.** v1 은 그렇게 50컬럼이 전건 NULL 로 남았다.

### 컬럼 그룹

```
식별      listing_id · site · source_id · target_key · vehicle_id
분류      classify_stage · classify_source · classify_conflict
가격      price_current_won · price_origin_won · price_unit
차량      year_month · mileage_km · displacement_cc · trim_badge · trim_grade_name
색상      color_ext_raw · color_ext_hex · color_int_raw · color_int_hex
보증      warranty_body_month/_km · warranty_power_month/_km
옵션      options_standard_json · options_choice_json · model_catalog_key
판매      sell_type · sales_status · dealer_* · dealer_region
상태      status · first_seen · last_seen · gone_at · last_price_won
사이트고유  site_*                       ← 어댑터를 통해서만 해석
수집상태   detail_status · inspection_status · record_status · diagnosis_status
```

**`site_*` 접두를 지킨다.** 2차 사이트에 같은 개념이 없을 수 있다.

---

## STEP 35 — `core_inspection` · `core_record` · `core_diagnosis`

**매물당 1행. `core_listing` 과 분리한다.**

```
이유   ① 없는 매물이 많다.  본 테이블을 NULL 로 채우지 않는다
      ② 재파싱 단위가 다르다.  점검부 규칙만 바꿔 그 테이블만 다시 만든다
```

### `core_vehicle` — 실물 차량 · 사이트 간 결합 ★

**DDL 은 STEP 30 에 있다.** `core_vehicle` + `vehicle_identity` 2종이다.

```
core_vehicle       vehicle_id INTEGER PK.  집계값만
vehicle_identity   (kind, value_hash) UNIQUE.  한 차량에 여러 행
```

```
★ 식별자를 core_vehicle 컬럼으로 두지 않는다
  번호판이 바뀌면 컬럼을 덮어써야 하고, 옛 번호로는 못 찾는다
  행으로 두면 하나 늘 뿐이고 둘 다로 찾힌다
```

```
★ 1차에는 site_count 가 전부 1 이다.  그래도 만든다
  값이 1뿐이어도 테이블과 컬럼이 있으면
  2차 사이트를 붙일 때 Analyzer · Scorer · 화면이 그대로 간다
  없으면 그때 core_* 를 고쳐야 하고, 그것이 「전체를 뒤엎는」 상황이다
```

```
갱신   S6 상세 파싱 후.  같은 vehicle_id 의 매물을 집계한다
금지   추정 결합 (3장 STEP 30 결합 규칙 6단계를 따른다)
표시   site_count == 1 이고 active 사이트가 1개면 「비교 대상 없음」
      site_count == 1 이고 active 사이트가 2개 이상이면 「단독 매물」
```

### 관리자 테이블 7종 (13장)

```sql
CREATE TABLE account (
  account_id          INTEGER PRIMARY KEY,
  role                TEXT NOT NULL,
  login_name          TEXT NOT NULL,          -- 식별용.  중복 불가
  display_name        TEXT NOT NULL,          -- 별명.  비우면 login_name 을 넣는다
  email               TEXT,                   -- 선택.  재설정·알림
  secret_hash         TEXT NOT NULL,          -- 전 행이 비밀번호를 갖는다
  must_change_secret  INTEGER NOT NULL DEFAULT 0,
  created_at          TEXT NOT NULL,
  last_seen_at        TEXT,
  disabled_at         TEXT,
  UNIQUE (login_name),
  CHECK (role IN ('user','admin'))            -- anonymous 는 행이 아니다
);

```

```
★ login_name 과 display_name 을 나눈다
  login_name    로그인·식별.  중복 불가.  바꾸지 않는다
  display_name  화면 표시.  바꿀 수 있다.  중복 허용
근거   실명으로 로그인하되 화면에는 별명을 쓸 수 있어야 한다
      display_name 하나로 두면 바꿀 때 로그인이 깨진다
필수   display_name 이 비면 login_name 을 넣는다.  NULL 로 두지 않는다
★ email 은 선택이다
  없으면 비밀번호 재설정을 관리자가 해준다
  1인 도구로 쓸 때는 필요 없다
금지   email 을 필수로 만드는 것
```

```sql
CREATE TABLE core_diagnosis (          -- ★ 08-14 확정.  encarDiagnosis == 0 만
  listing_id             INTEGER PRIMARY KEY,
  diagnosis_no           INTEGER,
  diagnosed_at           TEXT,               -- realDiagnosisDate
  center_code            TEXT,
  center_name            TEXT,
  item_count             INTEGER,            -- resultCode IS NOT NULL 인 것만
  replacement_count      INTEGER,            -- REPLACEMENT 수
  normal_count           INTEGER,
  checker_comment        TEXT,               -- 006039 · 소견
  outer_panel_comment    TEXT,               -- 006040 · 소견
  FOREIGN KEY (listing_id) REFERENCES core_listing(listing_id)
);

CREATE TABLE core_diagnosis_item (
  diagnosis_item_id  INTEGER PRIMARY KEY,
  listing_id         INTEGER NOT NULL,
  item_code          TEXT NOT NULL,          -- "006003"
  part_name          TEXT NOT NULL,          -- FRONT_DOOR_LEFT
  result_code        TEXT NOT NULL,          -- NORMAL · REPLACEMENT
  result_text        TEXT,                   -- "교환"
  FOREIGN KEY (listing_id) REFERENCES core_listing(listing_id)
);

CREATE INDEX idx_diag_item_listing ON core_diagnosis_item(listing_id);
```

```
★ 소견은 core_diagnosis 의 컬럼이다.  item 이 아니다
근거   resultCode 가 null 인 것은 부위 판정이 아니다
       item 으로 두면 「10부위 중 2교환」이 되어 수가 틀린다
필수   item_count 는 resultCode IS NOT NULL 인 것만 센다 (V3-34)
★ core_diagnosis 가 없는 매물이 정상이다
  encarDiagnosis 가 0 이 아니면 행이 없다.  결측이 아니다
금지   행이 없다고 사고 축을 감점하는 것
```

```sql
CREATE TABLE auth_login_attempt (   -- ★ 08-15.  로그인 시도 기록
  attempt_id   INTEGER PRIMARY KEY AUTOINCREMENT,
  display_name TEXT NOT NULL,      -- login_name.  존재하지 않는 이름도 남긴다
  succeeded    INTEGER NOT NULL,
  reason       TEXT,               -- 실패 사유 · 잠금 중 거부도 남긴다
  attempted_at TEXT NOT NULL
);

CREATE INDEX idx_attempt_name ON auth_login_attempt(display_name, attempted_at);
```

```
★ 없는 계정에 대한 시도도 남긴다
근거   「누가 어떤 이름을 찔러 봤나」가 신호다
      계정이 없다는 이유로 안 남기면 그 정보가 사라진다
금지   비밀번호나 그 해시를 남기는 것
필수   잠금 중 거부도 succeeded=0 으로 남긴다.  reason 으로 구분한다
검산   V10-20
```

```sql
CREATE TABLE auth_session (                    -- admin_ 이 아니다.  일반도 로그인한다
  session_id  INTEGER PRIMARY KEY,
  account_id  INTEGER NOT NULL,
  created_at  TEXT NOT NULL,
  expires_at  TEXT NOT NULL,
  revoked_at  TEXT,
  FOREIGN KEY (account_id) REFERENCES account(account_id)
);

```

```
★ role CHECK 에서 anonymous 를 뺀다
  행으로 존재하지 않으므로 열거값에도 두지 않는다
  두면 「만들 수 있는 것」으로 읽힌다
★ must_change_secret
  부트스트랩이 임시 비밀번호를 낸 뒤 1 로 둔다
  1 이면 로그인은 되나 비밀번호 변경 화면 외로 못 간다
★ disabled_at
  계정을 지우지 않는다.  watch_item · config_change 가 FK 로 물려 있다
```

```sql

CREATE TABLE config_change (
  change_id     INTEGER PRIMARY KEY,
  account_id    TEXT NOT NULL,
  file          TEXT NOT NULL,
  key_path      TEXT NOT NULL,
  before_value  TEXT,
  after_value   TEXT,
  reason        TEXT,
  applied_at    TEXT NOT NULL,
  reverted_at   TEXT,
  recalc_job_id TEXT
);

CREATE TABLE query_log (
  query_id        INTEGER PRIMARY KEY,
  account_id      TEXT NOT NULL,
  sql_text        TEXT NOT NULL,
  row_count       INTEGER,
  elapsed_ms      INTEGER,
  rejected_reason TEXT,
  executed_at     TEXT NOT NULL
);

CREATE TABLE admin_api_snapshot (
  snapshot_id   INTEGER PRIMARY KEY,
  account_id    TEXT NOT NULL,
  url           TEXT NOT NULL,
  http_code     INTEGER,
  content_type  TEXT,
  body          TEXT,
  note          TEXT,
  fetched_at    TEXT NOT NULL
);

CREATE TABLE dev_request (
  request_id   INTEGER PRIMARY KEY,
  title        TEXT NOT NULL,
  body         TEXT NOT NULL,
  origin       TEXT NOT NULL,
  context_json TEXT,
  status       TEXT NOT NULL,
  direction    TEXT,
  step_ref     TEXT,
  created_at   TEXT NOT NULL,
  exported_at  TEXT,
  updated_at   TEXT NOT NULL,
  CHECK (status IN ('draft','requested','in_progress','applied',
                    'not_applied','misapplied','reopened')),
  CHECK (origin IN ('screen','query','api','config','manual'))
);

CREATE TABLE recalc_job (
  job_id     INTEGER PRIMARY KEY,
  account_id TEXT,
  trigger    TEXT NOT NULL,
  reason     TEXT NOT NULL,
  from_step  TEXT NOT NULL,
  scope      TEXT NOT NULL,
  status     TEXT NOT NULL,
  run_id     TEXT,
  queued_at  TEXT NOT NULL,
  ended_at   TEXT,
  CHECK (trigger IN ('manual','schedule','config_change')),
  CHECK (status IN ('queued','running','done','failed'))
);
```

```
★ watch_item 에 account_id 를 추가한다 (STEP 125a)
  계정별 관심 목록.  판정 결과는 계정과 무관하다
```

### ★ CORE 쓰기는 단계 단위 트랜잭션

```
BATCH_STEPS   S4 · S6 · S6a · S8 · S9 · S10       단계 끝에 한 번 커밋
제외          S1 · S2 · S5 · S7                   원문은 건별 커밋 (P3)
```

```
근거   커밋은 fsync 다.  31,000건을 건별로 커밋하면 그것이 병목이다
      CORE 는 RAW 에서 재파싱으로 복구된다.  중간에 죽어도 잃을 것이 없다
금지   RAW 쓰기를 배치로 묶는 것.  원문이 사라지면 복구가 안 된다
설정   journal_mode=WAL · synchronous=NORMAL
```

```
★ 배치 중 실패하면 그 단계 전체가 롤백된다
  재실행하면 처음부터 다시 파싱한다.  upsert 라 멱등이다 (STEP 50a)
```

### `core_pii` — 개인정보 분리 ★

```
결정   별도 테이블로 관리하고 나중에 암호화한다 (마스터 확정)
지금   컬럼 분리 + 접근 경로 단일화까지.  알고리즘·키 관리는 미룬다
```

**키 단위가 달라 두 테이블로 나눈다.**

```sql
CREATE TABLE core_pii (                    -- 매물 단위
  listing_id         INTEGER PRIMARY KEY,
  plate_no           TEXT,                 -- 상세 A 원본
  plate_history_json TEXT,                 -- 과거 번호 원본
  record_plate_no    TEXT,                 -- 이력 carNo 원본
  created_at         TEXT NOT NULL,
  FOREIGN KEY (listing_id) REFERENCES core_listing(listing_id)
);

CREATE TABLE core_dealer_pii (             -- 딜러 단위
  dealer_id   INTEGER PRIMARY KEY,          -- core_dealer 와 1:1
  dealer_name TEXT,                         -- 개인 실명
  phone       TEXT,
  address     TEXT,
  created_at  TEXT NOT NULL,
  FOREIGN KEY (dealer_id) REFERENCES core_dealer(dealer_id)
);
```

```
★ 딜러 연락처를 core_pii 에 두지 않는다
  같은 딜러가 매물 100건이면 연락처가 100번 들어간다
```

**`core_listing` 에는 결합용·표시용만 둔다.**

```
plate_hash     HMAC 해시.  vehicle_id 결합 · 중복 판정 · 확보 여부 표시
dealer_shop    상호.  화면에 쓴다
```

### ★ 상호와 실명은 다른 값이다

```
O  오토핸즈 · (주)굿카 · 하이카     상호.  공개 정보다.  core_listing
X  홍원택 · 홍석기                 개인 실명.  core_dealer_pii
```

```
원문   partnership.dealer.firm.name   상호
      partnership.dealer.name        실명
필수   파싱에서 가른다.  v1 은 한 컬럼에 섞여 있었다
화면   ListingRow 는 dealer_shop 을 쓴다.  실명이 필요한 자리가 없다
      → 마스킹 규칙 자체가 필요 없어진다
```

### `plate_hash` — HMAC

```
방식   HMAC-SHA256(key, plate_no) 앞 16자 hex
키     secrets/plate_hmac.key    config 가 아니다.  .gitignore 필수
      없으면 부트스트랩이 생성한다
```

```
근거   무염 sha256 은 안 된다.  번호판은 전국 유한 집합이고 형식이 정해져 있다
      rainbow 가 아니라 전수 대조로 뚫린다
필수   키가 없으면 시작하지 않는다
      임시 키로 돌리면 다음 실행과 결합이 깨진다
복구   키 유출 시 재계산.  plate_hash 는 3곳(core_listing · core_vehicle ·
      vehicle_duplicate)이고 재파싱으로 복구된다 (STEP 50a)
검증   V2-11  plate_hash 가 전건 16자 hex 인가
```

### ★ 번호판은 결합 키다 — 암호화하면 비교가 안 된다

```
필수   원본과 결합용 해시를 나눈다.  해시는 결정적이어야 한다
필수   plate_history_json 의 과거 번호도 같은 처리를 한다
      합집합 매칭에 쓰이므로 원본만 두면 결합이 깨진다 (STEP 30)
금지   결합 키를 가역 암호화하는 것.  매번 복호화해야 비교가 된다
```

### ★ 대리키가 정해진 뒤에 PII 를 저장한다

```
문제   core_pii · core_dealer_pii 의 PK 가 INTEGER 대리키다
      파싱 시점에는 아직 대리키가 없다.  자연키로는 넣을 수 없다
```

```
1  split_pii(parsed)      PII 를 떼어 메모리에 보관.  CORE 딕셔너리에서 제거
2  resolve_*_id(...)      대리키 확정
3  flush_pii(id, held)    확정된 대리키로 저장
```

```
필수   1 에서 뗀 값이 CORE 로 새지 않는다.  같은 딕셔너리를 재사용하지 않는다
필수   2 가 실패하면 3 을 하지 않는다.  PII 만 남는 고아 행을 만들지 않는다
검증   V2-17  core_pii · core_dealer_pii 에 대응 CORE 행이 없는 고아가 0 인가
```

### 접근 경로 단일화

```python
def get_pii(scope: str, key: tuple, field: str) -> str | None: ...
#   scope = 'listing'  →  key = (listing_id,)
#   scope = 'dealer'   →  key = (site, dealer_id)
```

```
필수   PII 는 이 함수로만 읽는다.  core_pii 를 직접 SELECT 하지 않는다
근거   나중에 이 함수 안에서만 복호화하면 된다.  호출부를 안 고친다
검증   V2-09  core_pii 를 직접 조회하는 코드가 없는가 (AST · 문자열 상수만)
```

### RAW 는 예외다

```
raw_response 에는 원문이 그대로 남는다 (P3 무손실)
암호화 대상에서 제외하고 접근 통제로 관리한다
STEP 133 이 이미 「raw_* body 는 길이만 표시」로 반쯤 해두었다
```

```
★ 실측 — dealer_name 에 개인 실명이 섞여 있다
  홍원택 · 홍석기 (개인) 와 오토핸즈 (상호) 가 같은 컬럼에 있다
```

### `core_dealer` · `core_dealer_history` — 딜러 ★

**딜러는 매물의 속성이 아니라 독립 개체다.** 한 딜러에 여러 매물이 물린다.

```sql
CREATE TABLE core_dealer (
  dealer_id          INTEGER PRIMARY KEY AUTOINCREMENT,
  site               TEXT NOT NULL,
  site_dealer_id     TEXT NOT NULL,
  -- 신원 (사이트가 주는 값).  실명·연락처는 core_dealer_pii
  dealer_shop        TEXT,              -- 상호 (firm.name)
  shop_code          TEXT,
  region             TEXT,              -- OfficeCityState 계열
  career_years       REAL,
  total_sales        INTEGER,
  recent_year_sales  INTEGER,
  certified          INTEGER,
  -- 행태 지표 (우리 수집 이력에서 산출)
  listing_count      INTEGER NOT NULL,
  relist_rate        REAL,
  price_up_rate      REAL,
  drop_event_rate    REAL,
  price_volatility   REAL,
  median_dom_days    REAL,
  info_score         REAL,
  -- 종합
  sample_sufficient  INTEGER NOT NULL,
  trust_score        REAL,              -- sample_sufficient=0 이면 NULL
  quadrant           TEXT,              -- Q1~Q4
  calculated_at      TEXT NOT NULL,
  UNIQUE (site, site_dealer_id),
  CHECK (quadrant IS NULL OR quadrant IN ('Q1','Q2','Q3','Q4'))
);

CREATE TABLE core_dealer_history (
  dealer_id         INTEGER NOT NULL,
  run_id            TEXT NOT NULL,
  observed_at       TEXT NOT NULL,
  listing_count     INTEGER NOT NULL,
  trust_score       REAL,
  quadrant          TEXT,
  sample_sufficient INTEGER NOT NULL,
  PRIMARY KEY (dealer_id, run_id),
  FOREIGN KEY (dealer_id) REFERENCES core_dealer(dealer_id)
);
```

```
★ 이력이 없으면 「어제 Q1 이던 딜러가 오늘 Q4」를 설명할 수 없다
  행태 지표는 매 실행 재산출되는 값이라, 저장하지 않으면 변동 원인을 못 찾는다
```

### 이것은 복제가 아니다 — `watch_track` 과 다른 이유

```
result_score      calc_version 별로 남는다.  같은 버전이면 값이 같다
                  → watch_track 이 복제하면 어긋날 수 있다.  참조가 맞다

core_dealer       매 실행 upsert 로 덮어쓴다.  과거 값이 사라진다
                  → history 가 없으면 어제 값을 어디서도 못 찾는다.  저장이 맞다
```

```
판별 기준   원본이 이력을 남기는가
           남긴다  →  참조한다 (watch_track → result_score)
           덮어쓴다 →  스냅샷을 저장한다 (core_dealer_history)
```

**`core_listing`(덮어씀) → `core_listing_change`(저장)도 같은 구조다.**

```
갱신    S6 상세 파싱 후 → 딜러 단위 집계 → core_dealer upsert + history insert
근거    신원은 사이트가 준다.  행태 지표는 우리가 관측한다 (7장 STEP 82b)
표시    sample_sufficient=0 이면 trust_score 를 표시하지 않는다 (V3-26)
```

### `core_inspection`

```
listing_id · inspection_vin · inspection_mileage_km
first_registration_date            ← 보증 경과월 기준
inspection_valid_from / _to · inspection_issued_at
check_engine · check_transmission · motor_type_code
inspection_accident_flag · inspection_simple_repair · inspection_flood
inspection_tuning · inspection_recall
inspection_panel_json              ← outers 원문 배열 그대로
inspection_inner_json · inspection_etc_json · inspection_image_json
```

**`inspection_panel_json` 은 가공하지 않는다.** 골격/외판 해석은 Analyzer 가 한다.

### `core_record`

```
listing_id · record_plate_hash · plate_use_char
record_first_date
accident_my_cnt · accident_my_cost · accident_other_cnt · accident_other_cost
owner_change_cnt · owner_change_dates_json
plate_change_cnt · plate_history_json
total_loss_cnt · flood_total_cnt · flood_part_cnt · robber_cnt
use_gov · use_business · loan_cnt
not_join_json                      ← notJoinDate 1~5 배열
accidents_json                     ← 원문 배열 그대로 (type·금액)
```

### ★ `record_plate_no` — 원본은 `core_pii` 로. 파생 3종을 남긴다

**번호판이 세 가지에 쓰인다. 하나만 빼면 나머지가 죽는다.**

| 용도 | 필요한 것 | 컬럼 |
|---|---|---|
| 렌터카 판정 | **허 · 하 · 호 한 글자** | `plate_use_char` |
| `vehicle_id` 결합 | 해시 | `record_plate_hash` |
| 「번호 확보」 표시 | **해시 존재 여부** | (컬럼 없음) |

```
core_record   record_plate_hash · plate_use_char
core_pii      record_plate_no    원본
```

```
★ 마스킹 컬럼을 두지 않는다
  「확보 여부」는 hash IS NOT NULL 로 충분하다
  실제 번호가 필요하면 get_pii() 로 원본을 본다 (관리자 권한 · query_log)
  중간값을 저장하면 PII 판단이 원본/마스킹/해시 셋으로 갈려 어디를 쓸지 헷갈린다
  나중에 필요해지면 get_pii() 안에서 만든다
```

```
★ plate_use_char 가 판정용 파생값이다.  is_rental_plate 불리언이 아니다
  불리언이면 나중에 「허와 하가 다른가」를 물을 때 재파싱해야 한다
  한 글자는 원본이 아니고, 판정에 필요한 전부다
값     '허' · '하' · '호' · NULL (그 외 문자)
근거   7장 STEP 78 렌트 판정 1순위 보조 근거
```

```
★ 상세 A 와 같은 키로 해시한다
  두 해시가 다르면 상세 A 와 이력의 번호판이 다른 것이다.  그 자체가 신호다
검증   V2-13  core_record 에 record_plate_no 원본이 없음
```

**`accidents_json` 도 원문 그대로 둔다.** `type` 해석은 Analyzer 가 한다.

### `core_diagnosis` — ★ 08-14 확정

**DDL 은 위에 있다.** 원문 실측(08-14)으로 작성했다 — 2장 STEP 21b.

```
실측   encarDiagnosis == 0 인 매물만 200.  1 · 2 는 404
검산   진단 97건 · 부위 776행 · 집계 불일치 0
```

```
★ 이 절이 「원문 미확보」로 남아 있어 검사가 미착수로 잡았다 (개발측 발견)
필수   미확정이 해소되면 본문 서술도 함께 고친다.  표만 고치지 않는다
검산   S16  지시서의 이름이 소스에 있는가
```

---



---

## ★ `target_key` 가 NULL 인 매물 — 08-16

```
실측   전 차종 수집 7,661건 중 4,188건(54%)이 target_key NULL
      차종 8종을 골라 받았는데 절반 이상이 붙지 않았다
```

```
필수   저장은 한다.  원문은 무손실이다 (P3)
필수   target_key 가 NULL 이면 판정 대상이 아니다
       판정에 넣지 않는다.  「차종 미정」으로 가른다
필수   화면에서 갈라서 낸다 — 「범위 안 N건 · 차종 미정 N건」
       섞어서 「매물 N건」으로만 내지 않는다
필수   ★ 왜 안 붙었는지 알 수 있어야 한다
       모델명·배지 원문을 화면에서 볼 수 있게 한다
       그것으로 사람이 targets.json 을 고치거나 규칙을 고친다
금지   NULL 을 조용히 버리는 것
금지   NULL 을 임의의 차종에 넣는 것
검산   V2-31  target_key NULL 이 판정에 들어가지 않는가
       V2-32  NULL 매물의 모델명이 화면에서 보이는가
```

```
★ 54% 가 안 붙는 것은 그 자체가 결함 신호다
  ① 목록 쿼리가 차종을 안 걸었나
  ② 응답에 다른 차종이 섞였나
  ③ 분류 규칙이 안 맞나
  셋 중 무엇인지 가려야 한다.  「미정으로 두면 된다」로 넘기지 않는다
```


---

## 확보율 — 둘 다 내되 화면은 하나 · 08-18

**★ 마스터께 여쭸다가 「이게 뭐야? 내가 알아야 해?」를 들었다. 가이드가 정할 일이다.**

```
필수 [판단]   둘 다 계산한다
              원문 기준   받은 엔드포인트 수 ÷ 불러야 할 수
              컬럼 기준   채워진 컬럼 수 ÷ 전체 컬럼 수
필수 [판단]   ★ 화면에는 「컬럼 기준」만 낸다
              근거 — 사람이 보는 것은 「이 차에 대해 얼마나 아는가」다
                    엔드포인트를 받았어도 안이 비어 있으면 모르는 것이다
필수 [판단]   원문 기준은 관리 화면에만 — 수집이 잘 됐는지 보는 값이다
금지          한 화면에 둘을 나란히 내는 것.  사람이 어느 쪽인지 헷갈린다
```

---

# ★★★★ STEP 82c [규격] — ★ **딜러 정직도를 이렇게 잰다** (개정 822 · 08-29)

```
★★★ 마스터 — 「★ **미친 이렇게 선언만 하고 규격 없는데 뭐야**」
★ ★ **가이드가 축과 거르개를 만들어 놓고 ★ 셈 규칙을 한 줄도 안 적었다** (오판 156)
   ★ ★ 그래서 ★ 딜러 **1,182곳이 다 `NULL`** 이고 ★ 거르개가 ★ 늘 0건이다
★ ★ 표 칸은 ★ **이미 다 있다** — ★ 넷을 어떻게 세는지만 없었다
```

## ★ 재는 것 넷 — ★ 다 ★ **우리가 이미 가진 것**으로 센다

| 칸 | 무엇을 세나 | ★ 어디서 |
|---|---|---|
| ★ `drop_event_rate` | ★ **올렸다 내린 비율** | `core_listing.status` 가 `gone` 이 된 것 ÷ 전체 |
| ★ `price_volatility` | ★ **값을 얼마나 자주 바꾸나** | `core_listing_history` 의 값 바뀜 수 ÷ 매물 수 |
| ★ `median_dom_days` | ★ **며칠 만에 팔리나** (가운데값) | `first_seen` ~ `gone` 까지의 날 |
| ★ `info_score` | ★ **얼마나 적어 주나** | 사진·사고·보증·옵션 중 ★ **채운 칸 ÷ 넷** |

```
★★ ★ **넷 다 ★ 우리가 날마다 보는 것**이다 — ★ 새로 받을 것이 없다
```

## ★★★ `sample_sufficient` — ★ **몇 건부터 재나**

```
★ ★ **매물 `dealer_trust.min_listings`(★ 10)건 이상**이면 ★ `sample_sufficient = 1`
   ★ ★ **상수는 ★ `config/scoring.json` `dealer_trust` 에 있다** (개정 825)
   ★ ★ 그 아래는 ★ **0** 이고 ★ `trust_score` 는 ★ **`NULL` 그대로**
★ ★ 까닭 — ★ 세 건 파는 딜러의 ★ 「팔림 비율」은 ★ **뜻이 없다**
★ ★ **추정으로 채우지 않는다** — ★ 개발측이 지킨 그대로다 (`f-table` ⑤)
```

## ★★ `trust_score` — ★ **넷을 더한다** (0~100)

```
trust_score = ★ 25×(1 − drop_event_rate)
            ＋ ★ 25×(1 − min(price_volatility, 1))
            ＋ ★ 25×dom_점수      ← ★ `dom_full_days`(30) 이하 만점 · `dom_zero_days`(120) 이상 0
            ＋ ★ 25×info_score

★ ★ **넷이 똑같이 25씩**이다 — ★ 어느 하나가 세지 않다
★ ★ 값이 없으면 ★ **그 25 를 뺀 나머지로 나눈다** (★ 분모를 줄인다)
```

## ★ `quadrant` — ★ 넷으로 나눈다

| | 매물이 많다 | 매물이 적다 |
|---|---|---|
| ★ 점수 높다 | ★ **Q1** (큰 곳 · 믿을 만하다) | ★ **Q2** (작은 곳 · 믿을 만하다) |
| ★ 점수 낮다 | ★ **Q3** (큰 곳 · 조심) | ★ **Q4** (작은 곳 · 조심) |

```
★ ★ 가름 — ★ 매물 수 ★ **중앙값** · 점수 ★ **`quadrant_score_cut`(60)**
```

## ★★★★ `trust_score` 는 ★ **910 에 안 들어간다** (마스터 확정 08-29)

```
★★★ 마스터 — 「★ **910 에서 빼.  ★ 대신 계산은 해.
   ★ 딜러 상세 페이지에서 ★ 평가 점수 보기**」

★ ★ **26축 어디에도 딜러가 없다** (실측 08-29) — ★ 그대로 둔다
★ ★ **910 은 안 바뀐다** — ★ 다른 축에서 뺄 것이 없다
★★ ★ **그래도 ★ 셈은 한다** — ★ `core_dealer.trust_score` 에 넣는다
```

## ★★★ 어디에 보이나 — ★ **딜러 상세 하나**

```
★ ★ **`/dealers/{dealer_id}`** — ★ 딜러 상세 (★ `41-view` STEP 99 아래)
★ ★ 거기에 ★ **넷을 다 보인다** —
   ★ `trust_score` **0~100** · ★ `quadrant` Q1~Q4
   ★ 올렸다 내린 비율 · 값 바꾸는 잦기 · 며칠 만에 팔리나 · 얼마나 적어 주나
★ ★ **매물이 몇 건인지**도 함께 (★ `sample_sufficient` 의 까닭)

★ ★ **매물 카드에는 ★ 딜러 이름만** 낸다 — ★ 점수를 카드에 안 낸다
   ★ ★ 이름을 누르면 ★ **딜러 상세로 간다**
★ ★ 목록 거르개 「정직도」는 ★ **그대로 둔다** — ★ 거르는 데는 쓴다
```

```
필수  ★ ★ **점수(910)에 넣지 마라** — ★ 마스터 확정이다
필수  ★ ★ `/dealers/{id}` 를 ★ **만들어라** — ★ 지금 `/dealers` 목록만 있다
필수  ★ ★ 카드의 ★ **딜러 이름을 ★ 누를 수 있게** 하라
검산  ★ ★ **`S46-110`** — ★ `trust_score` 가 ★ `result_score` 에 들어가면 ★ **실패**
```

## ★★ 화면이 ★ 말해야 하는 것

```
필수  ★ ★ `sample_sufficient=0` 인 딜러는 ★ **「매물이 적어 아직 못 잽니다」**
필수  ★ ★ 거르개 「정직도」가 ★ **0건이면 ★ 그 까닭을 낸다**
      ★ ★ 지금은 ★ **0건만 내서 ★ 「죽었다」로 보인다**
금지  ★ ★ **빈칸을 추정으로 채우는 것** (STEP 82c 옛 규칙 그대로)
검산  ★ ★ **`S46-108`** — ★ `sample_sufficient=1` 인데 ★ `trust_score` 가 `NULL` 이면 실패
```
