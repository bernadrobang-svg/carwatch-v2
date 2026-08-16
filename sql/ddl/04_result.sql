-- result_* 스키마.  지시서 3장 STEP 37 · 6장 STEP 64 · 7장 STEP 83·84
-- result_* 는 버려도 된다.  버전이 다르면 다른 결과다 — 덮어쓰지 않는다

CREATE TABLE IF NOT EXISTS result_axis (
  listing_id   INTEGER NOT NULL,
  calc_version TEXT NOT NULL,
  dict_version TEXT NOT NULL,
  axis         TEXT NOT NULL,
  value        INTEGER,
  source       TEXT NOT NULL,
  prio         INTEGER NOT NULL,
  excluded     INTEGER NOT NULL,
  max_points   REAL,
  score        REAL,
  PRIMARY KEY (listing_id, calc_version, axis),
  FOREIGN KEY (listing_id) REFERENCES core_listing(listing_id),
  CHECK (prio IN (1,2,3,4))
);

CREATE INDEX IF NOT EXISTS ix_axis_version ON result_axis(calc_version, axis);
CREATE INDEX IF NOT EXISTS ix_axis_listing ON result_axis(listing_id);

CREATE TABLE IF NOT EXISTS result_score (
  listing_id     INTEGER NOT NULL,
  calc_version   TEXT NOT NULL,
  dict_version   TEXT NOT NULL,
  score_total    REAL NOT NULL,   -- 555 환산.  ★ 등급 판정에 쓰지 않는다
  -- ★ 실배점 합.  denominator 와 같은 자다 — 등급은 이것으로 잰다 (E-1)
  earned         REAL,
  denominator    REAL NOT NULL,
  grade          TEXT NOT NULL,
  absolute_fail  TEXT,            -- E등급 사유
  -- ★ 08-14. NOT_RATED 사유 3종을 구분한다 (V5-12)
  not_rated_reason TEXT,
  -- ★ 08-17 개정 292.  등급은 취향(④ 50점)을 뺀 505 로 매긴다.
  --   555 로 잰 비율을 화면에 내면 등급과 어긋난다 — 둘 다 남긴다
  grade_earned   REAL,
  grade_base     REAL,
  calculated_at  TEXT NOT NULL,
  PRIMARY KEY (listing_id, calc_version),
  FOREIGN KEY (listing_id) REFERENCES core_listing(listing_id),
  CHECK (grade IN ('S','A','B','C','D','E','NOT_RATED'))
);

CREATE INDEX IF NOT EXISTS ix_score_grade ON result_score(calc_version, grade);
CREATE INDEX IF NOT EXISTS ix_score_total ON result_score(calc_version, score_total DESC);

-- 감가 곡선 산출 이력.  곡선이 어떻게 나왔는지 남지 않으면 재현이 안 된다
CREATE TABLE IF NOT EXISTS depreciation_curve_history (
  id           INTEGER PRIMARY KEY,
  run_id       TEXT NOT NULL,
  curve_json   TEXT NOT NULL,
  sample_json  TEXT NOT NULL,
  anomalies    TEXT,
  created_at   TEXT NOT NULL
);

-- 계수 보정 이력.  남기지 않으면 점수 변동 원인을 사후에 못 찾는다
CREATE TABLE IF NOT EXISTS coefficient_history (
  id            INTEGER PRIMARY KEY,
  site          TEXT NOT NULL,
  target_key    TEXT NOT NULL,
  before_value  REAL,
  after_value   REAL NOT NULL,
  sample_size   INTEGER NOT NULL,
  measured      INTEGER NOT NULL DEFAULT 1,   -- 1 측정 · 0 부트스트랩 (STEP 64)
  reason        TEXT NOT NULL,
  changed_at    TEXT NOT NULL,
  UNIQUE (site, target_key, changed_at)
);


-- 축 판정 충돌 (7장 STEP 82 · 08-14).
-- ★ 같은 우선순위에서 다른 값이 나온 것은 규칙이 겹쳤다는 뜻이다.
--   첫 값 유지는 임시 조치다 — 기록이 없으면 겹쳤다는 것조차 모른다
-- 금지   충돌을 무시하고 넘어가는 것.  v1 의 사고가 전부 그렇게 시작했다
CREATE TABLE IF NOT EXISTS result_axis_conflict (
  conflict_id  INTEGER PRIMARY KEY AUTOINCREMENT,
  listing_id   INTEGER NOT NULL,
  calc_version TEXT NOT NULL,
  axis         TEXT NOT NULL,
  prio         INTEGER NOT NULL,
  value        TEXT,
  source       TEXT,
  FOREIGN KEY (listing_id) REFERENCES core_listing(listing_id)
);

CREATE INDEX IF NOT EXISTS idx_axis_conflict_listing
  ON result_axis_conflict(listing_id, calc_version);
