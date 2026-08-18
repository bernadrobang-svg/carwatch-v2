-- 관리자 저장소.  지시서 13장 STEP 126~137 · 3장 STEP 28
-- ★ 관리자 화면에서 하는 일은 전부 config 변경 또는 실행 지시다

CREATE TABLE IF NOT EXISTS account (
  account_id          INTEGER PRIMARY KEY AUTOINCREMENT,
  role                TEXT NOT NULL,
  -- ★ login_name 과 display_name 을 나눈다 (STEP 34).
  --   display_name 하나로 두면 별명을 바꿀 때 로그인이 깨진다
  login_name          TEXT NOT NULL,
  display_name        TEXT NOT NULL,
  -- 선택.  없으면 비밀번호 재설정을 관리자가 해준다
  email               TEXT,
  secret_hash         TEXT NOT NULL,
  must_change_secret  INTEGER NOT NULL DEFAULT 0,
  created_at          TEXT NOT NULL,
  last_seen_at        TEXT,
  disabled_at         TEXT,
  UNIQUE (login_name),
  -- anonymous 는 행이 아니다.  메모리에서 만든다 (STEP 126).
  -- ★ pending 은 「승인 전」이다 — 로그인은 되나 관심 등록은 못 한다.
  --   이 값이 없으면 승인제(approval)를 켠 순간 아무도 가입 못 한다
  --   (실측 08-15 · 가이드 3절)
  CHECK (role IN ('user','admin','pending'))
);

CREATE TABLE IF NOT EXISTS auth_session (
  session_id  TEXT PRIMARY KEY,
  account_id  INTEGER NOT NULL,
  created_at  TEXT NOT NULL,
  expires_at  TEXT NOT NULL,
  revoked_at  TEXT,
  FOREIGN KEY (account_id) REFERENCES account(account_id)
);

-- config 에도 버전이 필요하다.  result_* 가 calc_version 을 갖는 것과 같다
CREATE TABLE IF NOT EXISTS config_change (
  change_id     TEXT PRIMARY KEY,
  account_id    INTEGER NOT NULL,
  file          TEXT NOT NULL,
  key_path      TEXT NOT NULL,
  before_value  TEXT,
  after_value   TEXT,
  reason        TEXT,
  applied_at    TEXT NOT NULL,
  reverted_at   TEXT,
  recalc_job_id TEXT
);

CREATE TABLE IF NOT EXISTS query_log (
  query_id        TEXT PRIMARY KEY,
  account_id      INTEGER NOT NULL,
  sql_text        TEXT NOT NULL,
  row_count       INTEGER,
  elapsed_ms      INTEGER,
  rejected_reason TEXT,
  -- 거부 갈래 (개정 391) — compile(사용자 오타) · policy(정책 위반).
  -- ★ 둘을 한 자리에 쌓으면 거부 통계가 오염된다.
  --   컴파일 실패는 정책 위반이 아니다.  사용자 오타다
  reject_kind    TEXT,
  executed_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dev_request (
  request_id   TEXT PRIMARY KEY,
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

-- 관리자가 단계를 직접 고르지 않는다.  재처리 결정표가 from_step 을 준다
CREATE TABLE IF NOT EXISTS recalc_job (
  job_id     TEXT PRIMARY KEY,
  account_id INTEGER,
  trigger    TEXT NOT NULL,
  reason     TEXT NOT NULL,
  from_step  TEXT NOT NULL,
  scope      TEXT NOT NULL,
  status     TEXT NOT NULL,
  run_id     TEXT,
  -- ★ 진행 상태.  status 4종만으로는 「어디까지 갔는지」를 알 수 없다
  --   화면이 멈춘 것과 도는 것을 구분하지 못한다 (STEP 132)
  current_step TEXT,
  step_done    INTEGER,
  step_total   INTEGER,
  detail       TEXT,
  updated_at   TEXT,
  queued_at  TEXT NOT NULL,
  ended_at   TEXT,
  CHECK (trigger IN ('manual','schedule','config_change')),
  CHECK (status IN ('queued','running','done','failed'))
);

CREATE TABLE IF NOT EXISTS admin_api_snapshot (
  -- ★ 지시서 STEP 134 가 INTEGER PRIMARY KEY 다.  TEXT 면 자동 채번이 안 돼
  --   snapshot_id 가 NULL 로 들어간다 (실측 08-15)
  snapshot_id   INTEGER PRIMARY KEY AUTOINCREMENT,
  account_id    INTEGER NOT NULL,
  url           TEXT NOT NULL,
  http_code     INTEGER,
  content_type  TEXT,
  body          TEXT,
  note          TEXT,
  fetched_at    TEXT NOT NULL
);


-- 로그인 시도 (13장 STEP 126).  ★ 거부도 남긴다 — 누가 언제 시도했는지가 신호다
-- 금지   계정을 영구 잠그는 것.  1인 도구라 스스로 못 풀면 CLI 로 가야 한다
CREATE TABLE IF NOT EXISTS auth_login_attempt (
  attempt_id   INTEGER PRIMARY KEY AUTOINCREMENT,
  display_name TEXT NOT NULL,
  succeeded    INTEGER NOT NULL,
  reason       TEXT,
  attempted_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_login_attempt_name
  ON auth_login_attempt(display_name, attempted_at);
