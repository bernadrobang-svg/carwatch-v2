-- meta_* 스키마.  지시서 8장 STEP 87
-- ★ 등록부는 산문이 아니라 테이블이다.  문서는 기계가 검증할 수 없다
-- v1 방치의 근본 원인은 미사용 목록이 문서에만 있었다는 것이다

CREATE TABLE IF NOT EXISTS meta_field_usage (
  site               TEXT NOT NULL,
  endpoint           TEXT NOT NULL,
  json_path          TEXT NOT NULL,
  core_column        TEXT,
  usage              TEXT NOT NULL,
  reason             TEXT NOT NULL,
  unblock_condition  TEXT,
  use_when           TEXT,
  priority           INTEGER,
  -- ★ 관측 — 값이 실제로 몇 번 왔나 (개정 413).
  -- 화면이 매번 원문을 다시 열지 않게 여기 적어 둔다.  sync_registry 가 쓴다
  observed_hits   INTEGER,
  observed_total  INTEGER,
  miss_streak        INTEGER NOT NULL DEFAULT 0,   -- 연속 미관측 (유령 경로)
  first_seen         TEXT NOT NULL,
  last_seen          TEXT NOT NULL,
  PRIMARY KEY (site, endpoint, json_path),
  CHECK (usage IN ('in_use','display_only','unused_by_policy',
                   'deferred','blocked','not_provided','unclassified'))
);
