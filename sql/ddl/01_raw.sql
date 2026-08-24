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
  -- import  = 밖에서 받아 넣은 목록 (13장 STEP 136a)
  -- browser = 브라우저가 사용자 회선으로 받은 것 (13장 STEP 136c)
  -- ★ 셋을 섞지 않는다.  「누가 받았나」가 판정의 근거를 가른다
  CHECK (origin IN ('collector','master_manual','import','browser'))
);

CREATE INDEX IF NOT EXISTS ix_raw_lookup
  ON raw_response(listing_id, endpoint, fetched_at DESC);

-- ★★ 「마지막으로 목록을 받은 때」를 묻는 자리가 넷이다 (store/core.py 266·709 ·
--   collect/runner.py 519 · tools/daily_enqueue.py 99).  ★ 매물 번호가 없어
--   ix_raw_lookup 을 못 탄다 — ★ 14만 7천 행을 통째로 훑고 있었다.
--   ★★ 실측 08-26 — ★ 페이지 캐시를 비우고 재니 ★ 현황 한 화면에서 ★ **15.2초**였다.
--     ★ 몸통(body)이 큰 표라 한 번 훑는 값이 크다 (파일 1.1GB 의 대부분이 여기다)
--   ★ 이 색인이면 ★ 몸통을 안 읽고 색인만 본다
CREATE INDEX IF NOT EXISTS ix_raw_endpoint
  ON raw_response(endpoint, status, fetched_at);

-- ★★ 반입 화면(/admin/import)이 「밖에서 받아 넣은 것」만 최근 것부터 본다.
--   ★ origin 에 색인이 없어 ★ 14만 3천 행을 뒤에서부터 훑으며 ★ **몸통까지 읽었다**.
--   ★★ 실측 08-26 — ★ 한 쿼리에 ★ **31.7초**.  ★ origin='import' 는 ★ 딱 1건인데도다
--   ★ 관리 수집 화면(/admin/collect)은 같은 origin 안에서 endpoint 로 센다
CREATE INDEX IF NOT EXISTS ix_raw_origin
  ON raw_response(origin, id);
CREATE INDEX IF NOT EXISTS ix_raw_origin_endpoint
  ON raw_response(origin, endpoint);

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
