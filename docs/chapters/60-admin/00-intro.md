# 13장. 관리자 (STEP 126–140)

```
version  SPEC-2026.09.01-r1030
follows  `docs/chapters/30-score/f-table.md`
sources  실측 08-22
checks   S46-38 · S46-39
```


## 13장 정의서

**「누가 무엇을 할 수 있는가」와 「바꾼 것이 어떻게 반영되는가」를 정한다.**

```
비로그인   조회만
일반       조회 + 개인화 (관심 매물 · 가격 추이)
관리자     전부.  1차는 단일 계정
```

```
★ 관리자 화면에서 하는 일은 전부 config 변경 또는 실행 지시다
  코드를 고치는 일은 여기 없다.  그런 것은 개발 요청으로 간다 (STEP 137)
```

### 구조체

```python
@dataclass(frozen=True)
class Account:
    account_id: str
    role: str                    # anonymous · user · admin
    display_name: str
    created_at: datetime
    last_seen_at: datetime | None

@dataclass(frozen=True)
class ConfigChange:
    change_id: str
    account_id: str
    file: str                    # scoring.json 등
    key_path: str                # axis_rules.color.grade_points
    before: str                  # JSON 직렬화
    after: str
    reason: str | None
    applied_at: datetime
    reverted_at: datetime | None
    recalc_run_id: str | None    # 이 변경이 유발한 재계산

@dataclass(frozen=True)
class QueryLog:
    query_id: str
    account_id: str
    sql: str
    row_count: int
    elapsed_ms: int
    executed_at: datetime
    rejected_reason: str | None

@dataclass(frozen=True)
class DevRequest:
    request_id: str
    title: str
    body: str                    # 무엇이 없는가 · 무엇을 하고 싶은가
    origin: str                  # screen · query · api · config · manual
    context_json: str            # 발생 화면 · 시도한 값
    status: str                  # draft · requested · in_progress
                                 # applied · not_applied · misapplied · reopened
    direction: str | None        # 개발 방향 (지시서 반영 후 기재)
    step_ref: str | None         # 반영된 STEP 번호
    created_at: datetime
    exported_at: datetime | None
    updated_at: datetime

@dataclass(frozen=True)
class QueryResult:
    columns: list[str]
    rows: list[tuple]
    row_count: int
    truncated: bool              # 상한에 걸려 잘렸는가
    elapsed_ms: int

@dataclass(frozen=True)
class ApiSnapshot:
    snapshot_id: str
    url: str
    http_code: int | None
    content_type: str | None
    body: str | None
    paths: list[str]             # 응답에서 추출한 경로 전수
    fetched_at: datetime

@dataclass(frozen=True)
class ScoringPreview:
    before: dict[str, int]       # components
    after: dict[str, int]
    grade_before: dict[str, int] # 등급 → 건수
    grade_after: dict[str, int]
    rank_changed: int            # 상위 N 중 순위가 바뀐 건수
    entered: list[str]           # 새로 A 이상이 된 listing_id
    exited: list[str]
    axis_contribution: dict[str, float]

@dataclass(frozen=True)
class RecalcJob:
    job_id: str
    trigger: str                 # manual · schedule · config_change
    reason: str                  # 재처리 결정표의 「바뀐 것」 (STEP 50a)
    from_step: str               # S6 · S8.5 · S9 · S10
    scope: str                   # all · target_key 목록
    status: str                  # queued · running · done · failed
    run_id: str | None
```

### 함수

| 이름 | 입력 | 출력 | 목적 |
|---|---|---|---|
| `authenticate` | `credential` | `Account` | 로그인 |
| `require_role` | `Account, role` | `None` | 권한 확인. 미달 시 예외 |
| `apply_config` | `Account, file, key_path, value, reason` | `ConfigChange` | 설정 변경 |
| `revert_config` | `Account, change_id` | `ConfigChange` | 되돌리기 |
| `preview_scoring` | `제안 배점` | `ScoringPreview` | 영향 미리보기 |
| `run_query` | `Account, sql` | `QueryResult` | 조회 전용 |
| `fetch_api` | `Account, url` | `ApiSnapshot` | 외부 응답 저장 |
| `create_dev_request` | `Account, title, body, origin, context` | `DevRequest` | 개발 요청 |
| `export_dev_requests` | `status 필터` | `bytes` | md 내보내기 |
| `enqueue_recalc` | `Account, reason, scope` | `RecalcJob` | 재계산 지시 |

---

## STEP 125a [목록] — 1~12장 영향 ★

```
목적    13장 요건이 앞장의 무엇을 바꾸는지 한 곳에 모은다
근거    개발진이 「어디를 손대야 하나」를 찾아다니지 않게 한다
금지    이 표에 없는 장을 13장 때문에 고치는 것.  고쳐야 하면 이 표에 추가한다
검산    아래 각 항목이 해당 STEP 에 반영됐는가
```

### 실제로 고쳐야 하는 것

| 장 | STEP | 무엇이 바뀌나 | 이유 |
|---|---|---|---|
| **3** | 28 | **테이블 7종 추가** — `account` · `config_change` · `query_log` · `dev_request` · `recalc_job` · `admin_api_snapshot` · `auth_session` | 13장 저장소 |
| **3** | 34 | `watch_item` 에 `account_id` | 일반 계정 개인화 (STEP 126) |
| **3** | 30 | **전 테이블 대리키** · `vehicle_identity` · `V2-14`~`V2-16` | 87 · 88 |
| **11** | 112 | `vehicle_id` 로 재등록 추적 | 88 |
| **3** | 39 | `CHECK` 3종 추가 — `role` · `dev_request.status` · `recalc_job.status` | 열거값 강제 |
| **0** | 6 | `config` 에 `admin` 블록 — `query_row_limit` · `query_timeout_sec` · `schedule` | STEP 133 · 132 |
| **0** | 6 | `scoring.json` `components` 에 `skipped` 플래그 (부록 B 예시) | 성분 스킵 (STEP 128) |
| **5** | 47 | `RecalcJob` 이 `run_pipeline` 을 부른다 | 웹에서 실행 지시 (STEP 132) |
| **5** | 50a | 「무엇이 바뀌었나 → `from_step`」 조회 함수 노출 | 관리자가 단계를 직접 고르지 않는다 |
| **7** | 68 | 배점이 `config` 에서만 온다 (이미 그러함) · **정수 보정 규칙 추가** | STEP 128 비율 재배분 |
| **8** | 87 | 등록부 분류를 웹에서 바꾼다 · `field_usage.json` 쓰기 경로 | STEP 131 |
| **10** | 93 | 화면에 로그인 상태 · 역할 표시 | STEP 126 |
| **10** | 105 | 화면이 `Account` 를 받는다 | 권한별 표시 분기 |
| **11** | 112a | `watch_item` 조회에 `account_id` 필터 | 계정별 관심 목록 |

### 14장이 앞장에 미치는 영향

| 장 | STEP | 무엇이 바뀌나 |
|---|---|---|
| **0** | 6 | `config/web.json` 신설 |
| **0** | 15 | `web/` 디렉터리 |
| **10** | 105 | `view_*` 가 `PageContext.body` 로 들어간다 |
| **13** | 138 | 관리자 화면이 라우팅 표에 등재된다 |

```
★ 10장·13장 화면 함수는 그대로다.  14장이 그것을 감싼다
필수   view_* 시그니처를 바꾸지 않는다
```

### 13장 외 — 같은 시점에 반영할 것

**아래 3건은 13장 요건이 아니다. 개정 72·74·75번으로 별도 확정된 것이다.**
**착수 시점이 같아 여기 함께 적는다.**

| 장 | STEP | 무엇이 바뀌나 | 개정 |
|---|---|---|---|
| **3** | 28 · 35 | **`core_pii` · `core_dealer_pii` 신설** · `get_pii()` · `V2-09`~`V2-12` | 72 · 82 |
| **3** | 35 | `core_listing` 에서 PII 컬럼 제거 · `dealer_shop` 신설 | 83 |
| **3** | 35 | `plate_hash` HMAC · `secrets/` | 84 |
| **3** | 35 | `core_record` PII 분리 · `plate_use_char` · 마스킹 컬럼 없음 | 85 · 86 |
| **10** | 105 | `ListingRow` · `DealerRow` 가 `dealer_shop` 을 쓴다 | 83 |
| **3** | 28 | **`depreciation_curve_history` 신설** · `coefficient_history` 확장 | 75 |
| **0** | 6 | `curve_min_sample` | 74 |
| **7** | 70 | 곡선 표본 미달 시 미산출 · 보간 금지 | 74 |
| **6** | 64 | S8.5 3단계 순서 · 계수 부트스트랩 · `bootstrap` | 73 |
| **9** | 91 | `coefficient_measured` | 73 |

```
★ 영향표는 「13장이 앞장에 미치는 영향」이었다
  그래서 13장 밖의 변경이 표에 없었고, check_spec ⑩ 이 못 잡았다
필수   앞장을 고치는 결정은 장 소속과 무관하게 이 표에 행을 추가한다
      표에 없으면 ⑩ 이 검사하지 않는다
```

### 영향이 없는 것 — 확인용

| 장 | 이유 |
|---|---|
| 1 아키텍처 | 관리자는 Presentation 계층이다. L0~L9 구조가 바뀌지 않는다 |
| 2 수집 | 실행 지시 주체만 바뀐다. 수집 로직은 동일 |
| 4 사전 | 사전 생성은 자동이다. 관리자가 사전을 직접 쓰지 않는다 |
| 6 검증 | V1~V9 는 그대로. V10 이 추가될 뿐이다 |
| 9 리포트 | `ScoreView` 는 계정과 무관하다. 같은 차는 누가 봐도 같은 등급이다 |
| 12 다중 사이트 | 사이트 추가는 여전히 세션 작업이다 |

### ★ 바뀌지 않아야 하는 것

```
판정 결과가 계정별로 달라지는 것        금지
  같은 차는 누가 봐도 같은 등급이다.  개인화는 「무엇을 보는가」이지 「점수」가 아니다

관리자가 데이터를 직접 고치는 것         금지
  쿼리는 SELECT 전용 (STEP 133)
  도구는 config 변경 또는 재계산 지시만 (STEP 135)
  고쳐야 할 데이터가 있으면 그것은 파싱·판정 결함이다.  재처리로 푼다

웹에서 지시서를 고치는 것               금지
  뷰어는 읽기 전용 (STEP 136).  지시서는 세션에서 갱신된다
```

---

