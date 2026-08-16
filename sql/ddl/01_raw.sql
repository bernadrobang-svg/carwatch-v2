-- raw_* 스키마.  지시서 3장 STEP 33 · STEP 39
-- 원문은 무손실.  삭제 금지.  실패 응답도 원문이다 (5장 STEP 53-⑤)
-- SQLite 고유 문법을 쓰지 않는다 (0장 STEP 8)

CREATE TABLE IF NOT EXISTS raw_response (
  id             INTEGER PRIMARY KEY,
  -- ★ S4 봉투 범위 (5장 STEP 50a).  「이번 실행분」을 가르는 유일한 수단이다.
  --   시각으로 추정하면 --from · 워커 다중화에서 깨진다 (V1-16)
  run_id         TEXT,
  site           TEXT NOT NULL,
  listing_id     TEXT,
  source_id      TEXT,
  endpoint       TEXT NOT NULL,
  -- ★ 반입분은 URL 이 없다.  없는 것을 지어내면 「우리가 받았다」가 된다
  --   (13장 STEP 136b ② — 반입이 못 채우는 칸은 nullable 이어야 한다)
  request_url    TEXT,
  request_meta   TEXT,
  http_code      INTEGER,
  response_meta  TEXT,
  status         TEXT NOT NULL,
  body           TEXT,
  origin         TEXT NOT NULL,
  fetched_at     TEXT NOT NULL,
  CHECK (status IN ('ok','empty','not_found','error')),
  -- import = 밖에서 받아 넣은 목록 (13장 STEP 136a).  collector 와 구분한다
  CHECK (origin IN ('collector','master_manual','import'))
);

CREATE INDEX IF NOT EXISTS ix_raw_lookup
  ON raw_response(listing_id, endpoint, fetched_at DESC);

CREATE TABLE IF NOT EXISTS raw_facet (
  site          TEXT NOT NULL,
  target_key    TEXT NOT NULL,
  request_kind  TEXT NOT NULL,
  -- ★ 반입한 facet 은 URL 이 없다 (13장 STEP 136b ② · 개정 260).
  --   NULL 인 것이 「우리가 부른 것이 아니다」라는 표시다
  request_url   TEXT,
  axis_count    INTEGER,
  body          TEXT NOT NULL,
  fetched_at    TEXT NOT NULL,
  PRIMARY KEY (site, target_key, request_kind, fetched_at),
  CHECK (request_kind IN ('unspecified','Badge'))
);

CREATE TABLE IF NOT EXISTS raw_response_reject (
  id            INTEGER PRIMARY KEY,
  site          TEXT NOT NULL,
  listing_id    TEXT,
  endpoint      TEXT NOT NULL,
  request_url   TEXT NOT NULL,
  http_code     INTEGER,
  body          TEXT,
  reject_reason TEXT NOT NULL,
  fetched_at    TEXT NOT NULL
);
