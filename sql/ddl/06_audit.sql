-- audit_* 스키마.  지시서 3장 STEP 38 · 6장 STEP 66
-- 검증 결과를 테이블에 남긴다.  화면 출력만 하면 어제와 비교할 수 없다

CREATE TABLE IF NOT EXISTS audit_request (
  id           INTEGER PRIMARY KEY,
  run_id       TEXT NOT NULL,
  site         TEXT NOT NULL,
  kind         TEXT NOT NULL,
  source_id    TEXT,
  url          TEXT NOT NULL,
  http_code    INTEGER,
  status       TEXT NOT NULL,
  elapsed_ms   INTEGER,
  attempt      INTEGER NOT NULL DEFAULT 1,
  requested_at TEXT NOT NULL,
  CHECK (status IN ('ok','empty','not_found','error','not_requested'))
);

CREATE INDEX IF NOT EXISTS ix_request_run ON audit_request(run_id, kind);

CREATE TABLE IF NOT EXISTS audit_validation (
  run_id      TEXT NOT NULL,
  phase       TEXT NOT NULL,
  code        TEXT NOT NULL,
  target_key  TEXT,
  expected    TEXT NOT NULL,
  actual      TEXT NOT NULL,
  passed      INTEGER NOT NULL,
  severity    TEXT NOT NULL,
  samples     TEXT,
  -- ★ 이번 실행에서 그 단계를 돌았는가 (A-7 · V1-16).
  --   --from S9 로 돌면 S5 검사는 볼 것이 없다.  통과로 남기면
  --   전일 비교가 「어제 통과, 오늘도 통과」로 읽는다 — 실은 안 돈 것이다
  applicable  INTEGER NOT NULL DEFAULT 1,
  checked_at  TEXT NOT NULL,
  PRIMARY KEY (run_id, phase, code, target_key),
  CHECK (severity IN ('fatal','warn')),
  CHECK (applicable IN (0,1))
);
