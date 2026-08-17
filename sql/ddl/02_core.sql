-- core_* 스키마.  지시서 3장 STEP 29~35 · STEP 39
-- 사이트 무관 공통 스키마.  사이트 고유값은 site_* 접두 (0장 STEP 4)
-- 공통 컬럼 6종은 전 core_* 에 둔다 (STEP 31)

CREATE TABLE IF NOT EXISTS core_listing (
  -- 식별.  ★ PK 는 뜻이 없다.  자연키는 UNIQUE 로 건다 (STEP 30)
  listing_id             INTEGER PRIMARY KEY AUTOINCREMENT,
  site                   TEXT NOT NULL,
  source_id              TEXT NOT NULL,   -- API 호출용.  키가 아니다
  target_key             TEXT,
  vehicle_id             INTEGER,
  -- 분류 2단 (4장 STEP 46)
  classify_stage         TEXT,
  classify_source        TEXT,
  classify_conflict      INTEGER NOT NULL DEFAULT 0,
  -- 가격.  만원 단위를 원으로 환산해 저장한다 (2장 STEP 20)
  price_current_won      INTEGER,
  price_detail_won       INTEGER,
  price_origin_won       INTEGER,
  price_unit             TEXT,
  -- 차량
  year_month             TEXT,
  form_year              INTEGER,
  mileage_km             INTEGER,
  mileage_detail_km      INTEGER,
  displacement_cc        INTEGER,
  trim_badge             TEXT,
  trim_grade_name        TEXT,
  -- ★ 세부등급 (개정 313).  목록 원문 BadgeDetail — 「트렌디」 · 「시그니처」
  --   Badge 만으로는 「가솔린 2.5 터보 AWD」가 끝이다.  깡통과 풀옵션이 같아진다
  trim_badge_detail      TEXT,
  transmission           TEXT,
  fuel_raw               TEXT,
  fuel_detail            TEXT,
  trade_type             TEXT,
  model_catalog_key      TEXT,
  -- 색상
  color_ext_raw          TEXT,
  color_ext_hex          TEXT,
  color_ext_detail       TEXT,
  color_int_raw          TEXT,
  color_int_hex          TEXT,
  -- 보증
  warranty_body_month    INTEGER,
  warranty_body_km       INTEGER,
  warranty_power_month   INTEGER,
  warranty_power_km      INTEGER,
  warranty_extend        TEXT,
  warranty_deemed        TEXT,
  -- 옵션.  '[]' 와 NULL 을 구분한다 (STEP 32)
  options_standard_json  TEXT,
  options_choice_json    TEXT,
  options_etc_json       TEXT,
  options_tuning_json    TEXT,
  -- 판매 · 딜러
  sell_type              TEXT,
  sales_status           TEXT,
  copy_car               TEXT,
  -- ★ 실명·연락처·주소는 core_dealer_pii 로 간다 (STEP 35)
  --   상호(firm.name)와 실명(dealer.name)은 다른 값이다.  화면은 상호를 쓴다
  dealer_id              INTEGER,   -- core_dealer 대리키
  dealer_shop            TEXT,
  dealer_shop_code       TEXT,
  dealer_region          TEXT,
  dealer_photo           TEXT,
  -- 조건 · 진단
  seizing_cnt            INTEGER,
  pledge_cnt             INTEGER,
  has_record             INTEGER,
  has_resume             INTEGER,
  inspection_formats_json TEXT,
  diagnosis_car          INTEGER,
  advertisement_type     TEXT,
  lease_rent_info_json   TEXT,
  -- 관리
  reg_at                 TEXT,
  first_ad_at            TEXT,
  modify_at              TEXT,
  is_dummy               INTEGER,
  paired_source_id       TEXT,
  view_cnt               INTEGER,
  subscribe_cnt          INTEGER,
  -- 표시
  photo_main             TEXT,
  photo_list_json        TEXT,
  photo_underbody_json   TEXT,
  ad_body_text           TEXT,
  vin                    TEXT,
  -- ★ 번호판 원본은 core_pii 다.  여기는 결합용 해시만 둔다.
  --   마스킹 컬럼을 두지 않는다 — 「확보 여부」는 hash IS NOT NULL 로 충분하다
  plate_hash             TEXT,
  -- 사이트 고유.  어댑터를 통해서만 해석한다
  site_model_group       TEXT,
  site_model             TEXT,
  site_manufacturer      TEXT,
  site_service_marks_json TEXT,
  site_trust_json        TEXT,
  site_condition_json    TEXT,
  site_separation_json   TEXT,
  site_ad_type_json      TEXT,
  site_buy_type_json     TEXT,
  site_home_verify       TEXT,
  site_pass_type         TEXT,
  site_pass_grade        TEXT,
  site_diagnosis_grade   TEXT,
  -- 상태 추적 (STEP 29)
  status                 TEXT NOT NULL,
  first_seen             TEXT NOT NULL,
  last_seen              TEXT NOT NULL,
  gone_at                TEXT,
  last_price_won         INTEGER,
  -- 수집 상태.  요청하지 않음과 요청했으나 없음을 구분한다 (2장 STEP 16)
  detail_status          TEXT,
  inspection_status      TEXT,
  record_status          TEXT,
  diagnosis_status       TEXT,
  -- 개정 296·297 로 늘어난 요청 6종 (docs/ENCAR_API.md 2절).
  -- ★ 인증 없이 200 인 것만이다.  /v2/verification/* 은 401 이라 안 넣는다
  record_summary_status     TEXT,
  inspection_summary_status TEXT,
  platform_check_status        TEXT,
  sellingpoint_status       TEXT,
  ev_battery_status         TEXT,
  extend_warrant_status     TEXT,
  -- 개정 296·297 로 받은 값 (docs/ENCAR_API.md).  ★ 원문에 있는 것만이다
  record_use_code           TEXT,     -- 용도.  렌트 판정에 쓴다
  owner_change_cnt_summary  INTEGER,
  total_loss_cnt_summary    INTEGER,  -- 전손
  flood_total_cnt_summary   INTEGER,  -- 침수(전손)
  flood_part_cnt_summary    INTEGER,  -- 침수(분손)
  robber_cnt_summary        INTEGER,  -- 도난
  loan_flag                 INTEGER,  -- 저당
  business_flag             INTEGER,
  government_flag           INTEGER,
  platform_verified         INTEGER,  -- 플랫폼이 「클린」으로 판정했나
  inspector_name            TEXT,     -- 성능점검을 누가 했나
  ev_battery_known          INTEGER,
  selling_point             TEXT,
  -- 공통 (STEP 31)
  collected_at           TEXT,
  parsed_at              TEXT,
  parse_version          TEXT,
  row_status             TEXT NOT NULL,
  CHECK (status IN ('new','active','gone','relisted','out_of_scope')),
  CHECK (row_status IN ('ok','partial','error')),
  CHECK (classify_stage IS NULL OR classify_stage IN ('provisional','confirmed')),
  CHECK (detail_status IS NULL OR detail_status IN ('ok','empty','not_found','error','not_requested')),
  CHECK (inspection_status IS NULL OR inspection_status IN ('ok','empty','not_found','error','not_requested')),
  CHECK (record_status IS NULL OR record_status IN ('ok','empty','not_found','error','not_requested')),
  CHECK (diagnosis_status IS NULL OR diagnosis_status IN ('ok','empty','not_found','error','not_requested')),
  UNIQUE (site, source_id),
  FOREIGN KEY (vehicle_id) REFERENCES core_vehicle(vehicle_id),
  FOREIGN KEY (dealer_id) REFERENCES core_dealer(dealer_id)
);

CREATE INDEX IF NOT EXISTS ix_listing_target ON core_listing(target_key, status);
CREATE INDEX IF NOT EXISTS ix_listing_vehicle ON core_listing(vehicle_id);

-- 변경분만 쌓는다.  전량 스냅샷을 쌓지 않는다 (STEP 29)
CREATE TABLE IF NOT EXISTS core_listing_change (
  listing_id   INTEGER NOT NULL,
  changed_at   TEXT NOT NULL,
  field        TEXT NOT NULL,
  old_value    TEXT,
  new_value    TEXT,
  change_kind  TEXT NOT NULL,
  cause        TEXT,
  PRIMARY KEY (listing_id, changed_at, field),
  FOREIGN KEY (listing_id) REFERENCES core_listing(listing_id),
  CHECK (change_kind IN ('new','gone','relisted','price','status','anomaly','invariant_violation'))
);

CREATE INDEX IF NOT EXISTS ix_change_listing ON core_listing_change(listing_id, changed_at DESC);
CREATE INDEX IF NOT EXISTS ix_change_kind ON core_listing_change(change_kind, changed_at);

-- 실물 차량.  ★ 식별자는 행이다, 키가 아니다 (STEP 30)
--   번호판이 바뀌면 vehicle_identity 에 행이 하나 늘 뿐이다.
--   vehicle_id 는 그대로라 relist 추적이 끊기지 않는다 (11장 STEP 112)
CREATE TABLE IF NOT EXISTS core_vehicle (
  vehicle_id       INTEGER PRIMARY KEY AUTOINCREMENT,
  site_count       INTEGER NOT NULL,
  listing_count    INTEGER NOT NULL,
  min_price_won    INTEGER,
  max_price_won    INTEGER,
  price_spread_won INTEGER,
  first_seen       TEXT NOT NULL,
  last_seen        TEXT NOT NULL,
  updated_at       TEXT NOT NULL
);

-- 결합은 value_hash 로 찾아 vehicle_id 를 얻는다.
-- ★ 해시는 결합 「입력」이지 키가 아니다.  원본은 core_pii — 조인 경로에 PII 가 없다
CREATE TABLE IF NOT EXISTS vehicle_identity (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  vehicle_id  INTEGER NOT NULL,
  kind        TEXT NOT NULL,
  value_hash  TEXT NOT NULL,
  confidence  TEXT NOT NULL,
  first_seen  TEXT NOT NULL,
  last_seen   TEXT NOT NULL,
  UNIQUE (kind, value_hash),
  FOREIGN KEY (vehicle_id) REFERENCES core_vehicle(vehicle_id),
  CHECK (kind IN ('plate','vin','site_id')),
  CHECK (confidence IN ('confirmed','probable'))
);

-- 딜러는 매물의 속성이 아니라 독립 개체다 (STEP 35)
CREATE TABLE IF NOT EXISTS core_dealer (
  dealer_id          INTEGER PRIMARY KEY AUTOINCREMENT,
  site               TEXT NOT NULL,
  site_dealer_id     TEXT NOT NULL,   -- 사이트 원문 ID.  자연키
  -- ★ dealer_name · phone · address 는 core_dealer_pii 로 갔다 (STEP 35)
  dealer_shop        TEXT,             -- 상호 (firm.name)
  shop_code          TEXT,
  region             TEXT,
  career_years       REAL,
  total_sales        INTEGER,
  recent_year_sales  INTEGER,
  certified          INTEGER,
  listing_count      INTEGER NOT NULL,
  relist_rate        REAL,
  price_up_rate      REAL,
  drop_event_rate    REAL,
  price_volatility   REAL,
  median_dom_days    REAL,
  info_score         REAL,
  sample_sufficient  INTEGER NOT NULL,
  trust_score        REAL,
  quadrant           TEXT,
  calculated_at      TEXT NOT NULL,
  UNIQUE (site, site_dealer_id),
  CHECK (quadrant IS NULL OR quadrant IN ('Q1','Q2','Q3','Q4'))
);

-- 행태 지표는 매 실행 덮어쓴다.  이력이 없으면 어제 값을 못 찾는다
CREATE TABLE IF NOT EXISTS core_dealer_history (
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

-- 점검.  outers 는 원문 배열 그대로.  가공하지 않는다 (2장 STEP 21)
CREATE TABLE IF NOT EXISTS core_inspection (
  listing_id                INTEGER PRIMARY KEY,
  site                      TEXT NOT NULL,
  inspection_vin            TEXT,
  inspection_mileage_km     INTEGER,
  first_registration_date   TEXT,
  inspection_valid_from     TEXT,
  inspection_valid_to       TEXT,
  inspection_issued_at      TEXT,
  check_engine              TEXT,
  check_transmission        TEXT,
  motor_type_code           TEXT,
  inspection_comment        TEXT,
  inspection_accident_flag  TEXT,
  inspection_simple_repair  TEXT,
  inspection_flood          TEXT,
  inspection_tuning         TEXT,
  inspection_recall         TEXT,
  usage_change_types_json   TEXT,
  inspection_panel_json     TEXT,
  inspection_inner_json     TEXT,
  inspection_etc_json       TEXT,
  inspection_image_json     TEXT,
  collected_at              TEXT,
  parsed_at                 TEXT,
  parse_version             TEXT,
  row_status                TEXT NOT NULL,
  FOREIGN KEY (listing_id) REFERENCES core_listing(listing_id),
  CHECK (row_status IN ('ok','partial','error'))
);

-- 이력.  accidents_json 의 type 해석은 Analyzer 가 한다 (2장 STEP 21a)
CREATE TABLE IF NOT EXISTS core_record (
  listing_id                INTEGER PRIMARY KEY,
  site                      TEXT NOT NULL,
  -- ★ 번호판이 세 가지에 쓰인다.  하나만 빼면 나머지가 죽는다 (STEP 35)
  --   렌터카 판정 → plate_use_char · 결합 → record_plate_hash · 확보 여부 → hash NOT NULL
  record_plate_hash         TEXT,
  plate_use_char            TEXT,
  record_first_date         TEXT,
  record_reg_date           TEXT,
  record_open               TEXT,
  accident_my_cnt           INTEGER,
  accident_my_cost          INTEGER,
  accident_other_cnt        INTEGER,
  accident_other_cost       INTEGER,
  accident_total_cnt        INTEGER,
  accidents_json            TEXT,
  owner_change_cnt          INTEGER,
  owner_change_dates_json   TEXT,
  plate_change_cnt          INTEGER,
  plate_history_hash_json   TEXT,   -- 과거 번호도 해시.  합집합 매칭에 쓰인다
  total_loss_cnt            INTEGER,
  total_loss_date           TEXT,
  flood_total_cnt           INTEGER,
  flood_part_cnt            INTEGER,
  flood_date                TEXT,
  robber_cnt                INTEGER,
  robber_date               TEXT,
  use_gov                   TEXT,
  use_business              TEXT,
  loan_cnt                  INTEGER,
  use_cd                    TEXT,
  use1_json                 TEXT,
  use2_json                 TEXT,
  not_join_json             TEXT,
  record_fuel               TEXT,
  record_maker              TEXT,
  collected_at              TEXT,
  parsed_at                 TEXT,
  parse_version             TEXT,
  row_status                TEXT NOT NULL,
  FOREIGN KEY (listing_id) REFERENCES core_listing(listing_id),
  CHECK (row_status IN ('ok','partial','error'))
);

-- 진단 리포트 (2장 STEP 21b).  ★ 판정 근거가 아니라 표시용이다.
--   교환 판정은 core_inspection.outers 가 한다 — 골격까지 보므로 더 넓다.
--   진단 items 와 outers 가 전건 일치함을 582건으로 확인했다 (2026-08-14)
CREATE TABLE IF NOT EXISTS core_diagnosis (   -- ★ 08-14 확정 (STEP 21b·35)
  listing_id          INTEGER PRIMARY KEY,
  diagnosis_no        INTEGER,
  diagnosed_at        TEXT,      -- realDiagnosisDate (시각까지)
  center_code         TEXT,
  center_name         TEXT,
  item_count          INTEGER,   -- resultCode IS NOT NULL 인 것만
  replacement_count   INTEGER,   -- REPLACEMENT 수
  normal_count        INTEGER,
  checker_comment     TEXT,      -- 006039 소견 ★ 사람이 읽을 문장
  outer_panel_comment TEXT,      -- 006040 소견
  row_status          TEXT NOT NULL,
  parse_version       TEXT NOT NULL,
  parsed_at           TEXT NOT NULL,
  FOREIGN KEY (listing_id) REFERENCES core_listing(listing_id)
);

-- ★ 소견은 core_diagnosis 의 컬럼이다.  item 이 아니다.
--   resultCode 가 null 인 것은 부위 판정이 아니다 —
--   item 으로 두면 「10부위 중 2교환」이 되어 수가 틀린다
CREATE TABLE IF NOT EXISTS core_diagnosis_item (
  diagnosis_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
  listing_id        INTEGER NOT NULL,
  item_code         TEXT NOT NULL,   -- "006003"
  part_name         TEXT NOT NULL,   -- FRONT_DOOR_LEFT
  result_code       TEXT NOT NULL,   -- NORMAL · REPLACEMENT
  result_text       TEXT,            -- "교환"
  UNIQUE (listing_id, item_code),
  FOREIGN KEY (listing_id) REFERENCES core_listing(listing_id)
);

CREATE INDEX IF NOT EXISTS idx_diag_item_listing
  ON core_diagnosis_item(listing_id);


-- ★ 「값이 없다」와 「우리가 못 읽었다」는 다르다 (STEP 19a).
--   둘을 섞으면 파서 버그가 「원문이 그렇다」로 묻힌다
CREATE TABLE IF NOT EXISTS core_parse_issue (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  listing_id    INTEGER NOT NULL,
  endpoint      TEXT NOT NULL,
  json_path     TEXT NOT NULL,
  reason        TEXT NOT NULL,
  raw_sample    TEXT,
  parse_version TEXT NOT NULL,
  detected_at   TEXT NOT NULL,
  UNIQUE (listing_id, endpoint, json_path, parse_version),
  FOREIGN KEY (listing_id) REFERENCES core_listing(listing_id),
  CHECK (reason IN ('not_provided','parse_error','type_mismatch'))
);

-- 개인정보 분리 (STEP 35).  get_pii() 로만 읽는다 — 직접 SELECT 금지 (V2-09)
CREATE TABLE IF NOT EXISTS core_pii (
  listing_id         INTEGER PRIMARY KEY,
  plate_no           TEXT,
  plate_history_json TEXT,
  record_plate_no    TEXT,
  created_at         TEXT NOT NULL,
  FOREIGN KEY (listing_id) REFERENCES core_listing(listing_id)
);

-- 딜러 단위.  같은 딜러가 매물 100건이면 연락처가 100번 들어가면 안 된다
CREATE TABLE IF NOT EXISTS core_dealer_pii (
  dealer_id   INTEGER PRIMARY KEY,   -- core_dealer 와 1:1
  dealer_name TEXT,
  phone       TEXT,
  address     TEXT,
  created_at  TEXT NOT NULL,
  FOREIGN KEY (dealer_id) REFERENCES core_dealer(dealer_id)
);

-- core_diagnosis 는 만들지 않는다 (STEP 35)
--   원문 0건이다.  스키마는 재수집 후 확정한다 (2장 STEP 26-1)
--   추정으로 필드를 만들지 않는다.  등록부 blocked 로 둔다 (8장 STEP 87)
--   수집은 한다 — raw_response 에 원문이 쌓이고, core_listing.diagnosis_status 에 상태가 남는다
