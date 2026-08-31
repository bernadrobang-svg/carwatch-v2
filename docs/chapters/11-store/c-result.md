## STEP 36 — `dict_*` 설계

```
version  SPEC-2026.09.01-r1054
follows  `docs/chapters/30-score/f-table.md`
sources  실측 08-22
checks   S46-38 · S46-39
```


**사전은 손으로 적지 않는다. `tools/build_dict.py` 가 RAW 에서 생성한다.**

| 테이블 | 원천 | 키 | 내용 |
|---|---|---|---|
| `dict_option_code` | facet `Options` | `(site, target_key, code)` | 3자리 코드 → 옵션명 |
| `dict_model_option` | `catalog` | `(model_catalog_key, option_code)` | 4자리 → 이름·가격 |
| `dict_enum` | facet 각 축 · 점검부 | `(site, axis, value)` | 연료·색상·트림·부위명·상태값 |

```sql
-- 3종 공통 형태.  scope_key 구성만 다르다 (STEP 40)
CREATE TABLE dict_option_code (        -- scope=target
  site        TEXT NOT NULL,
  target_key  TEXT NOT NULL,
  code        TEXT NOT NULL,
  display     TEXT NOT NULL,
  count_seen  INTEGER,
  status      TEXT NOT NULL,           -- confirmed · pending · retired
  first_seen  TEXT NOT NULL,
  last_seen   TEXT NOT NULL,
  PRIMARY KEY (site, target_key, code),
  CHECK (status IN ('confirmed','pending','retired'))
);

CREATE TABLE dict_model_option (       -- scope=model
  site              TEXT NOT NULL,
  model_catalog_key TEXT NOT NULL,
  option_code       TEXT NOT NULL,
  option_name       TEXT NOT NULL,
  price_manwon      INTEGER,
  description       TEXT,
  status            TEXT NOT NULL,
  first_seen        TEXT NOT NULL,
  last_seen         TEXT NOT NULL,
  PRIMARY KEY (site, model_catalog_key, option_code),
  CHECK (status IN ('confirmed','pending','retired'))
);

CREATE TABLE dict_enum (               -- scope=global
  site            TEXT NOT NULL,
  axis            TEXT NOT NULL,       -- fuel · color_ext · panel · panel_rank …
  value           TEXT NOT NULL,
  display         TEXT NOT NULL,
  count_seen      INTEGER,
  status          TEXT NOT NULL,
  source_endpoint TEXT NOT NULL,
  first_seen      TEXT NOT NULL,
  last_seen       TEXT NOT NULL,
  PRIMARY KEY (site, axis, value),
  CHECK (status IN ('confirmed','pending','retired'))
);
```

**`count_seen` 은 분포 참고용이다. 판정 근거가 아니다** (2장 STEP 23).

### 생성 규칙

```
1  RAW 에서 해당 경로의 distinct 값을 뽑는다
2  기존 사전과 비교한다
3  신규 값이 있으면 「미확인」으로 적재하고 알림
4  사람이 확인한 뒤 매핑을 확정한다
```

**신규 값이 나타났는데 조용히 무시하면 v1 의 「휀더/펜더」가 재현된다.**

```
시험   사전 미분류 0건.  새 값이 나타나면 실패시켜 사람이 보게 한다
```

---

## STEP 37 — `result_*` 설계

```sql
CREATE TABLE result_axis (
  listing_id   TEXT NOT NULL,
  calc_version TEXT NOT NULL,
  dict_version TEXT NOT NULL,        -- 사전 스냅샷 (4장 STEP 45)
  axis         TEXT NOT NULL,
  value        INTEGER,
  source       TEXT NOT NULL,     -- spec_table · installed · classifier · keyword
  prio         INTEGER NOT NULL,
  excluded     INTEGER NOT NULL,  -- 분모 제외 여부
  score        REAL,
  PRIMARY KEY (listing_id, calc_version, axis)
);
```

**`source` · `prio` 는 NOT NULL 이다.** 값만 있고 근거가 없는 행을 스키마가 거부한다.
**v1 은 14축 중 12축의 근거가 전건 NULL 이었고, 값이 왜 그런지 추적할 수 없었다.**

```sql
CREATE TABLE result_score (
  listing_id     TEXT NOT NULL,
  calc_version   TEXT NOT NULL,
  dict_version   TEXT NOT NULL,
  score_total    REAL NOT NULL,
  denominator    REAL NOT NULL,
  grade          TEXT NOT NULL,
  absolute_fail  TEXT,            -- E등급 사유
  earned         REAL NOT NULL,   -- ★ 08-15. 실배점 합.  등급 판정의 분자다
  not_rated_reason TEXT,          -- ★ 08-14. NOT_RATED 사유 3종을 구분한다
  calculated_at  TEXT NOT NULL,
  PRIMARY KEY (listing_id, calc_version)
);
```

```
★ not_rated_reason — 08-14 신설
  ScoreResult 에는 있는데 저장할 곳이 없었다.  화면이 「왜」를 못 낸다
  값   전 축 수집 실패 · 분모 최소 기준 미만 · 금지 근거만 존재
필수   NOT_RATED 이면 반드시 채운다.  등급만 내지 않는다
검산   V5-12  NOT_RATED 인데 not_rated_reason 이 NULL 인 행이 없는가
```

**`calc_version` 을 키에 넣어 이전 계산 결과를 남긴다.** 배점을 바꿨을 때 무엇이 어떻게 변했는지
비교할 수 있어야 한다. v1 은 덮어써서 비교가 불가능했다.

---

## STEP 38 — `audit_*` 설계

```sql
CREATE TABLE audit_request (
  id          INTEGER PRIMARY KEY,
  run_id      TEXT NOT NULL,
  site        TEXT NOT NULL,
  kind        TEXT NOT NULL,
  source_id   TEXT,
  url         TEXT NOT NULL,
  http_code   INTEGER,
  status      TEXT NOT NULL,
  elapsed_ms  INTEGER,
  attempt     INTEGER NOT NULL DEFAULT 1,
  requested_at TEXT NOT NULL
);
```

`audit_validation` 은 STEP 66 에 정의한다.

**검증 결과를 테이블에 남긴다.** 화면 출력만 하면 어제와 비교할 수 없다.
**6장의 「전일 대비 GAP」이 이 테이블 위에서 돈다.**

---

## STEP 39 — 인덱스 · 제약

```
raw_response      (listing_id, endpoint, fetched_at DESC)
core_listing      (target_key, status) · (vehicle_id) · (site, source_id) UNIQUE
core_listing_change (listing_id, changed_at DESC) · (change_kind, changed_at)
result_axis       (calc_version, axis) · (listing_id)
result_score      (calc_version, grade) · (calc_version, score_total DESC)
dict_enum         (site, axis)
```

### 제약

```
NOT NULL   listing_id · site · endpoint · status · source · prio
UNIQUE     (site, source_id)          같은 매물이 두 행이 되지 않게
FK         core_* → core_listing      고아 행 방지
CHECK      core_listing.status  IN ('new','active','gone','relisted','out_of_scope')
CHECK      watch_item.status    IN ('watching','gone','relisted','closed')
CHECK      watch_track.listing_status IN ('new','active','gone','relisted','out_of_scope')
           → core_listing.status 를 복사하므로 같은 집합을 건다
CHECK      *_status             IN ('ok','empty','not_found','error','not_requested')
           → 세 집합은 서로 다르다.  같은 이름이라고 같은 값이 아니다
CHECK      grade IN ('S','A','B','C','D','E','NOT_RATED')
CHECK      usage IN ('in_use','display_only','unused_by_policy',
                     'deferred','blocked','not_provided','unclassified')
CHECK      account.role       IN ('user','admin')     -- anonymous 는 행이 아니다
CHECK      dev_request.status IN ('draft','requested','in_progress','applied',
                                  'not_applied','misapplied','reopened')
CHECK      recalc_job.status  IN ('queued','running','done','failed')
```

**SQLite 고유 문법을 쓰지 않는다** (0장 STEP 8). 표준 DDL 로 쓴다.

---

**3장 종료 (STEP 28–39).**

---


### `result_axis_conflict` — 축 판정 충돌 ★ 08-15

```sql
CREATE TABLE result_axis_conflict (
  conflict_id  INTEGER PRIMARY KEY AUTOINCREMENT,
  listing_id   INTEGER NOT NULL,
  calc_version TEXT NOT NULL,
  axis         TEXT NOT NULL,
  prio         INTEGER NOT NULL,
  value        TEXT,
  source       TEXT,
  FOREIGN KEY (listing_id) REFERENCES core_listing(listing_id)
);

CREATE INDEX idx_conflict_listing ON result_axis_conflict(listing_id, calc_version);
```

```
★ 같은 우선순위에서 다른 값이 나온 것을 남긴다
근거   첫 값 유지는 임시 조치다.  겹친 규칙을 고쳐야 한다
      기록이 없으면 겹쳤다는 것조차 모른다
필수   화면 · L1 리포트에 「같은 근거 두 값」으로 낸다
검산   V3-35 · V3-36
★ 충돌 0 건이 정상이다.  0 이 아니면 규칙이 겹친 것이다
```

---

---

## ★★★ 불변식 바뀜은 ★ **동시 발생**을 센다 (개정 789 · 08-28)

```
★★ ★ **한 회차에 ★ 함께 바뀐 것**을 센다 — ★ **누적이 아니다**
★ ★ 08-28 실측 — ★ `classify_invariant_change` 가 ★ `_today(parsed)` 가 빈 글자일 때
   ★ ★ `changed_at >= ''` 이라 ★ **역사 전체를 세어** ★ 누적 4＋2 로 문턱 5를 넘어 ★ **S4 가 멈췄다**
★★★ ★ **누적으로 세면 ★ 시간이 갈수록 반드시 넘는다** — ★ 언젠가 꼭 멈춘다
필수  ★ ★ `since = _today(parsed) or str(observed_at)[:10]` — ★ 날이 없으면 ★ **오늘로 본다**
```
