-- 활용 테이블.  지시서 11장 STEP 112a · 113 · 117a · 118 · 7장 STEP 82d
-- ★ status 는 네 곳에서 뜻이 다르다.  DDL 의 CHECK 로 집합을 강제한다

-- 경고.  점수에 합산하지 않는다.  목록에서 제외하지 않는다 (V3-21·22·23)
CREATE TABLE IF NOT EXISTS listing_warning (
  listing_id    INTEGER NOT NULL,
  warning_code  TEXT NOT NULL,
  severity      TEXT NOT NULL,
  evidence      TEXT NOT NULL,
  detected_at   TEXT NOT NULL,
  acknowledged  INTEGER NOT NULL DEFAULT 0,
  resolved_at   TEXT,
  PRIMARY KEY (listing_id, warning_code),
  FOREIGN KEY (listing_id) REFERENCES core_listing(listing_id)
);

-- 관심 등록.  ★ 차량 단위다.  같은 차를 두 번 등록하지 않는다
CREATE TABLE IF NOT EXISTS watch_item (
  watch_id           INTEGER PRIMARY KEY AUTOINCREMENT,
  account_id         INTEGER NOT NULL,   -- ★ 계정별 관심 목록 (13장 STEP 126)
  vehicle_id         INTEGER NOT NULL,
  primary_listing_id INTEGER NOT NULL,
  added_at           TEXT NOT NULL,
  memo               TEXT,
  target_price_won   INTEGER,
  on_price_drop      INTEGER NOT NULL DEFAULT 1,
  on_target_price    INTEGER NOT NULL DEFAULT 1,
  on_gone            INTEGER NOT NULL DEFAULT 1,
  on_relist          INTEGER NOT NULL DEFAULT 1,
  on_grade_change    INTEGER NOT NULL DEFAULT 0,
  on_dom             INTEGER NOT NULL DEFAULT 0,
  dom_threshold_days INTEGER,
  status             TEXT NOT NULL DEFAULT 'watching',
  closed_reason      TEXT,
  closed_at          TEXT,
  -- ★ 한 사람이 같은 차를 두 번 등록하지 않는다.  vehicle_key 단독이 아니다
  UNIQUE (account_id, vehicle_id),
  FOREIGN KEY (account_id) REFERENCES account(account_id),
  CHECK (status IN ('watching','gone','relisted','closed')),
  CHECK (closed_reason IS NULL OR closed_reason IN ('bought','lost','dropped'))
);

-- 스냅샷.  ★ 점수를 복제하지 않는다.  버전 키로 result_score 를 조인한다
CREATE TABLE IF NOT EXISTS watch_track (
  listing_id     INTEGER NOT NULL,
  run_id         TEXT NOT NULL,
  observed_at    TEXT NOT NULL,
  price_won      INTEGER,
  listing_status TEXT NOT NULL,
  calc_version   TEXT NOT NULL,
  dict_version   TEXT NOT NULL,
  parse_version  TEXT NOT NULL,
  coefficient_id INTEGER,
  PRIMARY KEY (listing_id, run_id),
  CHECK (listing_status IN ('new','active','gone','relisted','out_of_scope'))
);

CREATE TABLE IF NOT EXISTS watch_event (
  id           INTEGER PRIMARY KEY,
  listing_id   INTEGER NOT NULL,
  vehicle_id   INTEGER,
  run_id       TEXT NOT NULL,
  kind         TEXT NOT NULL,
  before_value TEXT,
  after_value  TEXT,
  cause        TEXT NOT NULL,
  occurred_at  TEXT NOT NULL,
  notified            INTEGER NOT NULL DEFAULT 0,
  -- ★ 시도를 먼저 기록한다.  성공을 낙관하지 않는다 (STEP 120a · V7-10)
  notify_attempted_at TEXT,
  CHECK (kind IN ('price_drop','price_rise','target_hit','gone',
                  'relist','grade_change','dom_exceeded')),
  CHECK (cause IN ('listing','dict','calc','coefficient'))
);

-- 조건 추적 (11장 STEP 117a).
-- ★ 「이 매물」이 아니라 「이런 차」를 추적한다.
--   매물은 사라진다.  조건은 남는다
-- 금지   쿼리를 코드에 박는 것.  조건은 config 가 아니라 데이터다
CREATE TABLE IF NOT EXISTS watch_query (
  query_id        INTEGER PRIMARY KEY AUTOINCREMENT,
  account_id      INTEGER NOT NULL,
  name            TEXT NOT NULL,
  conditions_json TEXT NOT NULL,
  min_grade       TEXT,
  max_price_won   INTEGER,
  notify_on_new   INTEGER NOT NULL DEFAULT 1,
  notify_on_price INTEGER NOT NULL DEFAULT 1,
  created_at      TEXT NOT NULL,
  last_run_at     TEXT,
  active          INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS watch_query_hit (
  query_id     INTEGER NOT NULL,
  listing_id   INTEGER NOT NULL,
  first_hit_at TEXT NOT NULL,
  -- ★ 알렸는가.  안 알린 것만 다음 실행에서 알린다
  notified     INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (query_id, listing_id)
);

CREATE TABLE IF NOT EXISTS watch_candidate (
  listing_id     INTEGER PRIMARY KEY,
  decided_at     TEXT NOT NULL,
  decision       TEXT NOT NULL,
  checklist_json TEXT,
  note           TEXT,
  FOREIGN KEY (listing_id) REFERENCES core_listing(listing_id)
);

-- 동시 중복 게시.  ★ 재등록이 아니다 (STEP 112)
CREATE TABLE IF NOT EXISTS vehicle_duplicate (
  vehicle_id          INTEGER NOT NULL,
  listing_id          INTEGER NOT NULL,
  kind                TEXT NOT NULL,
  representative      INTEGER NOT NULL DEFAULT 0,
  peer_count          INTEGER NOT NULL,
  detected_at         TEXT NOT NULL,
  PRIMARY KEY (vehicle_id, listing_id),
  -- ★ concurrent_cross_site — ★ 사이트 사이다 (docs/DEDUP_CROSS_SITE.md 2-3).
  --   ★ 앞 셋은 ★ 「한 사이트 안에서」를 가리킨다 — ★ 사이트 사이가 없었다.
  --   ★ 그래야 ★ 「엔카에도 KB 에도 있다」와 ★ 「한 딜러가 두 번 올렸다」를 가른다
  CHECK (kind IN ('concurrent_same_dealer','concurrent_cross_dealer','relist',
                  'concurrent_cross_site'))
);

-- 진행 메모 (11장 STEP 118 · 개정 362 · V7-15).
-- ★★ 계약 4단계를 폐기하고 이것이 대신 들어왔다.
--    마스터 지적 — 이 도구는 엔카와 직거래를 하기 위한 것이지
--    파는 쪽을 대신해 주는 것이 아니다.  폐기된 4단계는 그쪽이 쓰던 것이다
-- ★ 메모가 본체다.  kind 는 메모를 정리하는 이름일 뿐이다
-- ★ 단계를 강제하지 않는다 — 전화만 하고 끝날 수도 있다.
--   순서도 없고, 앞 단계 없이 'done' 을 적어도 된다
CREATE TABLE IF NOT EXISTS watch_note (
  note_id      INTEGER PRIMARY KEY AUTOINCREMENT,
  account_id   INTEGER NOT NULL,   -- ★ 계정별이다 (13장 STEP 126)
  listing_id   INTEGER NOT NULL,
  kind         TEXT NOT NULL,      -- contacted · visited · done
  body         TEXT NOT NULL,      -- ★ 본체.  비워 둘 수 없다
  noted_at     TEXT NOT NULL,
  FOREIGN KEY (account_id) REFERENCES account(account_id),
  FOREIGN KEY (listing_id) REFERENCES core_listing(listing_id),
  CHECK (kind IN ('contacted','visited','done')),
  CHECK (body <> '')
);

CREATE INDEX IF NOT EXISTS ix_watch_note_who
  ON watch_note(account_id, listing_id, noted_at);
