-- dict_* 스키마.  지시서 3장 STEP 36 · 4장 STEP 40~45
-- 사전은 손으로 적지 않는다.  RAW 에서 생성한다
-- 상태 4종.  retired 는 삭제하지 않는다 — 과거 매물 해석에 필요하다

CREATE TABLE IF NOT EXISTS dict_option_code (
  site        TEXT NOT NULL,
  target_key  TEXT NOT NULL,
  code        TEXT NOT NULL,
  display     TEXT NOT NULL,
  count_seen  INTEGER,
  status      TEXT NOT NULL,
  dict_version TEXT NOT NULL,
  first_seen  TEXT NOT NULL,
  last_seen   TEXT NOT NULL,
  PRIMARY KEY (site, target_key, code),
  CHECK (status IN ('confirmed','pending','retired'))
);

CREATE TABLE IF NOT EXISTS dict_model_option (
  site              TEXT NOT NULL,
  model_catalog_key TEXT NOT NULL,
  option_code       TEXT NOT NULL,
  -- ★ 원문에서 온다.  사이트가 안 주면 없는 것이다 (STEP 31a)
  option_name       TEXT,
  price_manwon      INTEGER,
  description       TEXT,
  status            TEXT NOT NULL,
  dict_version      TEXT NOT NULL,
  first_seen        TEXT NOT NULL,
  last_seen         TEXT NOT NULL,
  PRIMARY KEY (site, model_catalog_key, option_code),
  CHECK (status IN ('confirmed','pending','retired'))
);

CREATE TABLE IF NOT EXISTS dict_enum (
  site            TEXT NOT NULL,
  axis            TEXT NOT NULL,
  value           TEXT NOT NULL,
  display         TEXT NOT NULL,
  count_seen      INTEGER,
  status          TEXT NOT NULL,
  source_endpoint TEXT NOT NULL,
  dict_version    TEXT NOT NULL,
  first_seen      TEXT NOT NULL,
  last_seen       TEXT NOT NULL,
  PRIMARY KEY (site, axis, value),
  CHECK (status IN ('confirmed','pending','retired'))
);

CREATE INDEX IF NOT EXISTS ix_dict_enum_axis ON dict_enum(site, axis);
