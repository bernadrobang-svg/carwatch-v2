# 11장. 활용 — 후보 추적 (STEP 111–120)

```
version  SPEC-2026.08.29-r979
follows  `docs/chapters/30-score/f-table.md`
sources  실측 08-22
checks   S46-38 · S46-39
```


## 11장 정의서

**「지금 좋은 매물」을 고르는 것과 「관심 매물이 어떻게 되는지 지켜보는 것」은 다른 일이다.**
**9·10장이 앞이고, 11장이 뒤다.**

```
v1 근거   watchlist(7컬럼) · price_history · comparison
방침      구조를 유지하고 v2 규격으로 정리한다.  alert_on_sold 만 재정의한다
```

### 구조체

```python
@dataclass(frozen=True)
class WatchItem:
    listing_id: str
    vehicle_id: int | None        # 같은 차의 재등록을 따라간다 (3장 STEP 30)
    added_at: date
    memo: str | None
    target_price_won: int | None  # 이 값 이하면 알림
    alerts: AlertConfig
    status: str                   # watching · gone · relisted · closed
    closed_reason: str | None     # bought · lost · dropped

@dataclass(frozen=True)
class AlertConfig:
    on_price_drop: bool           # 가격 인하
    on_target_price: bool         # 목표가 도달
    on_gone: bool                 # 목록에서 사라짐   ★ v1 alert_on_sold 대체
    on_relist: bool               # 같은 차 재등록    ★ 신설
    on_grade_change: bool         # 등급 변동         ★ 신설
    on_dom: bool                  # 게시 경과일 초과
    dom_threshold_days: int | None

@dataclass(frozen=True)
class TrackPoint:
    listing_id: str
    observed_at: date
    price_won: int
    status: str
    grade: str
    score_total: float
    versions: VersionStamp        # 점수 비교의 전제

@dataclass(frozen=True)
class TrackEvent:
    listing_id: str
    vehicle_id: int | None
    kind: str                     # price_drop · price_rise · target_hit · gone
                                  # relist · grade_change · dom_exceeded
    before: str | None
    after: str | None
    cause: str                    # listing · dict · calc · coefficient
    occurred_at: datetime
    notified: bool
```

### 함수

| 이름 | 입력 | 출력 | 목적 |
|---|---|---|---|
| `watch_add` | `vehicle_id, primary_listing_id, at, account_id, memo, target_price` | `WatchItem` | 관심 등록 |
| `watch_update` | `watch_id, account_id, AlertConfig` | `WatchItem` | 알림 설정 |
| `watch_close` | `watch_id, account_id, reason` | `WatchItem` | 추적 종료 |
| `track_snapshot` | `run_id` | `list[TrackPoint]` | 실행 시점 기록 |
| `detect_events` | `run_id` | `list[TrackEvent]` | 변동 감지 |
| `classify_cause` | `TrackEvent` | `str` | 변동 원인 분류 |
| `notify` | `list[TrackEvent]` | `NotifyResult` | 알림 발송 |

```
금지   detect_events 가 점수를 계산하는 것.  result_* 를 읽는다
필수   전 이벤트에 cause 를 붙인다 (6장 STEP 65)
```

---

## STEP 111 — `alert_on_sold` 재정의 ★

**v1 은 「팔렸다」를 감지한다고 했으나, 엔카는 판매 여부를 주지 않는다 ★ [추론 — 엔카는 robots `Disallow: /` 라 **우리 창에서 못 두드린다**]** (8장 STEP 87).

```
v1    alert_on_sold   기본값 1.  목록에서 사라지면 「판매됨」으로 알림
사실   사라지는 이유는 여러 가지다
        판매 · 광고 만료 · 딜러 철회 · 재등록 준비 · 사이트 오류
```

| v1 | v2 | 처리 |
|---|---|---|
| `alert_on_sold` | **`on_gone`** | 「목록에서 사라짐」으로 문구 변경 |
| — | **`on_relist`** | 신설. 같은 차가 다시 올라오면 알림 |

```
필수   알림 문구는 「목록에서 사라졌습니다」다.  「판매되었습니다」가 아니다
필수   함께 마지막 가격(last_price_won)과 gone_at 을 낸다
금지   sold_price · sold_at 컬럼을 만드는 것
승계   v1 DB 의 sold_price·sold_at·listing_days 293건은 이관하지 않는다
      근거 없는 추정값이다.  참고가 필요하면 v1 DB 원본을 보관한다
```

---

## STEP 112 — 추적 대상과 키

```
추적 단위   매물 (listing_id)
연결 단위   차량 (vehicle_id)      같은 차의 재등록을 따라간다
```

### ★ 같은 차량번호 = 재등록이 아니다 — 세 가지를 구분한다

```
실측 (v1)   같은 차량번호 그룹 1,113개
           그중 같은 딜러 1,111 · 다른 딜러 2
           대부분이 active + active 로 동시에 떠 있다
→ 재등록이 아니라 「같은 딜러의 동시 중복 게시」다
```

| 종류 | 판별 | 처리 |
|---|---|---|
| **동시 중복** | 같은 딜러 · 둘 다 `active` · 같은 가격 | **하나로 묶어 1건으로 센다** |
| **재등록** | `gone` 이후 새 `listing_id` 로 등장 | `relist` 이벤트 · 가격 차이가 신호 |
| **딜러 간 중복** | 다른 딜러 · 둘 다 `active` | **양쪽 다 보여준다.** 가격 비교 대상 |

```
필수   세 가지를 같은 것으로 처리하지 않는다
      동시 중복을 relist 로 알리면 「같은 차가 다시 올라왔다」는 거짓 알림이 나간다
판별   시간 축이 가른다 — 겹치는가(중복) · 이어지는가(재등록)
```

### 동시 중복 처리

```
대표    가장 싼 것.  같으면 먼저 관측된 것
표시    「같은 딜러가 N건 게시」 배지.  중복분은 접어 둔다
집계    차종별 매물 수를 셀 때 1건으로 센다
       중복을 그대로 세면 물량이 부풀려진다 (딜러 지표 왜곡)
경고    같은 딜러의 동시 중복이 과도하면 duplicate_ad (STEP 82d)
```

```
★ 「과도한가」의 기준은 첫 수집 분포를 보고 정한다
  실측에서는 1,113그룹이 나왔다.  이것이 정상인지 판단이 필요하다
```

**`vehicle_id` 로 묶는 것이 이 장의 핵심이다.**

```
사례   관심 매물이 gone 되고, 3일 뒤 다른 listing_id 로 같은 차가 올라온다
      가격이 50만 내려가 있다
v1    두 매물을 별개로 본다.  「사라졌다」로 끝난다
v2    vehicle_id 로 묶어 relist 이벤트를 낸다.  가격 차이가 곧 시세 신호다
```

```
결합 규칙   3장 STEP 30 을 그대로 쓴다 (차량번호 → 차대번호 검증)
표시       「같은 차량이 새 매물로 등록되었습니다 (−50만)」
주의       결합 근거를 함께 낸다.  identity_kind 를 표시
```

---

## STEP 112a — 저장소

### ★ 서명이 DDL 을 따른다 — 08-14 정정

```
watch_add(conn, vehicle_id, primary_listing_id, at, account_id, ...) -> WatchItem
```

```
필수   account_id 는 필수 인자다.  기본값을 두지 않는다
근거   DDL 이 account_id NOT NULL · UNIQUE(account_id, vehicle_id) 다
       규격에 인자가 없어 화면에서 INSERT 가 막혔다 (개발측 실측 08-14)
필수   watch_id 는 호출자가 만들지 않는다.  DB 가 부여하고 lastrowid 를 받는다
금지   token_hex 등 문자열 키.  INTEGER PRIMARY KEY 에 넣으면 datatype mismatch
필수   조회·수정·종료는 watch_id 로 한다.  listing_id 가 아니다
근거   관심은 차량 단위다.  대표 매물이 바뀌어도 관심은 유지된다
```

```
★ closed_reason 은 bought · lost · dropped 뿐이다
  「사용자 해제」 같은 문구를 넘기지 않는다 → dropped
검산   V7-11  closed_reason 이 CHECK 안의 값인가
```

### ★ 소유 검사는 서버가 한다 — 08-14

```
필수   watch_update · watch_close 도 account_id 를 받는다
필수   WHERE watch_id=? AND account_id=?  로 건다
필수   영향 0 행이면 PolicyError.  조용히 통과시키지 않는다
근거   watch_id 는 연속된 정수다.  남의 번호를 넣으면 그대로 통과한다 (실측 08-14)
      조회는 계정별인데 쓰기만 뚫려 있었다
금지   화면에서만 거르는 것.  URL 을 직접 치면 무의미하다
검산   V7-12  남의 watch_id 로 수정·종료가 거부되는가
```

### `watch_item` — 관심 등록

```sql
CREATE TABLE watch_item (
  watch_id          INTEGER PRIMARY KEY,
  account_id        INTEGER NOT NULL,        -- ★ 계정별 관심 목록 (13장 STEP 126)
  vehicle_id        INTEGER NOT NULL,
  primary_listing_id INTEGER NOT NULL,          -- 대표 매물 (가장 싼 것 · 갱신됨)
  added_at          TEXT NOT NULL,
  memo              TEXT,
  target_price_won  INTEGER,
  on_price_drop     INTEGER NOT NULL DEFAULT 1,
  on_target_price   INTEGER NOT NULL DEFAULT 1,
  on_gone           INTEGER NOT NULL DEFAULT 1,
  on_relist         INTEGER NOT NULL DEFAULT 1,
  on_grade_change   INTEGER NOT NULL DEFAULT 0,
  on_dom            INTEGER NOT NULL DEFAULT 0,
  dom_threshold_days INTEGER,
  status            TEXT NOT NULL DEFAULT 'watching',
  closed_reason     TEXT,
  closed_at         TEXT,
  UNIQUE (account_id, vehicle_id),        -- ★ 한 사람이 같은 차를 두 번 등록하지 않는다
  FOREIGN KEY (account_id) REFERENCES account(account_id),
  CHECK (status IN ('watching','gone','relisted','closed')),
  CHECK (closed_reason IS NULL OR closed_reason IN ('bought','lost','dropped'))
);
```

```
★ vehicle_id 단독 UNIQUE 를 두지 않는다
  두면 계정이 둘이 되는 순간 두 사람이 같은 차를 관심 등록할 수 없다
  UNIQUE 는 (account_id, vehicle_id) 다
조회   watch_item 은 항상 account_id 로 거른다 (13장 STEP 126)
승계   v1 watchlist 8행은 최초 관리자 계정으로 이관한다 (STEP 119a)
```

### `watch_event` — 감지된 변동

```sql
CREATE TABLE watch_event (
  id           INTEGER PRIMARY KEY,
  listing_id   TEXT NOT NULL,
  vehicle_id  TEXT,
  run_id       TEXT NOT NULL,
  kind         TEXT NOT NULL,
  before_value TEXT,
  after_value  TEXT,
  cause        TEXT NOT NULL,
  occurred_at  TEXT NOT NULL,
  notify_attempted_at TEXT,          -- 보내기 전에 먼저 쓴다 (STEP 120a)
  notified     INTEGER NOT NULL DEFAULT 0,
  CHECK (kind IN ('price_drop','price_rise','target_hit','gone',
                  'relist','grade_change','dom_exceeded')),
  CHECK (cause IN ('listing','dict','calc','coefficient'))
);
```

### ★ `status` 는 네 곳에서 뜻이 다르다

| 컬럼 | 열거값 | 뜻 |
|---|---|---|
| `core_listing.status` | `new` · `active` · `gone` · `relisted` · `out_of_scope` | 매물의 게시 상태 |
| `watch_item.status` | `watching` · `gone` · `relisted` · `closed` | **추적 상태** |
| `watch_track.listing_status` | **`core_listing.status` 를 그대로 복사** | 그 시점 게시 상태 |
| `*_status` (수집) | `ok` · `empty` · `not_found` · `error` · `not_requested` | 응답 상태 |

```
금지   같은 이름이라고 같은 값으로 취급하는 것
필수   DDL 의 CHECK 로 집합을 강제한다 (3장 STEP 39)
```

## STEP 113 — 스냅샷

**실행마다 관심 매물의 상태를 기록한다.**

### ★ 점수를 복제하지 않는다 — 참조만 한다

```
result_score 가 이미 (listing_id, calc_version) 로 점수를 갖는다
watch_track 이 score_total · grade · denominator 를 다시 저장하면
같은 값이 두 곳에 생기고, 둘이 어긋날 수 있다
```

```sql
CREATE TABLE watch_track (
  listing_id     TEXT NOT NULL,
  run_id         TEXT NOT NULL,
  observed_at    TEXT NOT NULL,
  -- 그 시점에만 존재하는 값 (result_* 에 없다)
  price_won      INTEGER,
  listing_status TEXT NOT NULL,      -- 그때의 게시 상태
  -- 점수는 참조 키만 갖는다
  calc_version   TEXT NOT NULL,
  dict_version   TEXT NOT NULL,
  parse_version  TEXT NOT NULL,
  coefficient_id INTEGER,
  PRIMARY KEY (listing_id, run_id),
  FOREIGN KEY (listing_id, calc_version) REFERENCES result_score(listing_id, calc_version)
);
```

```
조회   watch_track ⋈ result_score  로 그 시점 점수를 얻는다
필수   result_score 는 calc_version 별로 남는다 (3장 STEP 37).  덮어쓰지 않으므로 조회가 성립한다
금지   score_total · grade · denominator 를 watch_track 에 복제하는 것
근거   복제하면 재채점 시 한쪽만 갱신되어 어긋난다
```

```
저장하는 것   price_won · listing_status
             → 이 둘은 result_* 에 없다.  그 시점 사실이다
저장 안 하는 것 score_total · grade · denominator
             → result_score 에 있다.  버전 키로 조인한다
```

```
계정   watch_item 조회는 항상 account_id 로 거른다 (13장 STEP 126)
      watch_track 은 매물 단위라 계정과 무관하다
      같은 차를 두 계정이 관심 등록해도 스냅샷은 1행이다
대상   watch_item 에 있는 매물만.  전 매물을 스냅샷하지 않는다
근거   전 매물 이력은 core_listing_change 가 이미 담는다 (3장 STEP 29)
```

**버전 4종은 조인 키다.** 없으면 어느 규칙으로 계산된 점수인지 모른다.

---

## STEP 114 — 이벤트 감지

| 종류 | 조건 | 기본 알림 |
|---|---|:--:|
| `price_drop` | 직전 대비 가격 하락 | O |
| `price_rise` | 상승 | X |
| `target_hit` | `target_price_won` 이하 도달 | O |
| `gone` | `status` 가 `gone` 으로 전이 | O |
| `relist` | 같은 `vehicle_id` 가 새 `listing_id` 로 등장 | O |
| `grade_change` | 등급 변동 | 조건부 (아래) |
| `dom_exceeded` | 게시 경과일이 임계 초과 | X |

```
감지 시점   S12 리포트 직전.  검증 V1~V5 통과 후에만 (6장 STEP 66)
이유       검증에 실패한 실행의 점수로 알림을 보내면 안 된다
```

---

## STEP 115 — 변동 원인 분류 ★

**「등급이 B → C 로 떨어졌다」의 원인은 넷이다. 구분하지 않으면 알림이 거짓말이 된다.**

| `cause` | 판별 | 알림 |
|---|---|:--:|
| `listing` | 가격·상태가 실제로 바뀜 | **O** |
| `dict` | `dict_version` 이 다름 | X (표시만) |
| `calc` | `calc_version` 이 다름 | X (표시만) |
| `coefficient` | `coefficient_id` 가 다름 | X (표시만) |

```python
def classify_cause(prev: TrackPoint, cur: TrackPoint) -> str:
    if prev.versions.dict_version  != cur.versions.dict_version:  return "dict"
    if prev.versions.calc_version  != cur.versions.calc_version:  return "calc"
    if prev.versions.coefficient_id != cur.versions.coefficient_id: return "coefficient"
    return "listing"
```

```
필수   cause != 'listing' 이면 알림을 보내지 않는다.  화면에만 표시한다
금지   규칙이 바뀐 것을 매물이 바뀐 것처럼 알리는 것
표시   「배점 개정으로 등급이 조정되었습니다 (매물 변동 없음)」
```

**`grade_change` 알림은 `cause='listing'` 일 때만 나간다.**

---

## STEP 116 — 알림

```
1차    화면 배지 + 리포트.  외부 채널 없음
2차    계정별 채널 설정.  account 에 컬럼을 추가하지 않고 별도 테이블로 둔다
       notify_channel(account_id, kind, target, enabled)
       kind — email · push · webhook
근거   1인 사용 도구다.  화면에서 보면 충분하다
       채널을 넣으면 발송 실패·재시도·수신 거부가 따라온다
채널   1차는 화면 배지 + 리포트.  외부 채널은 config 로 확장
저장   TrackEvent.notified 로 중복 발송 차단
빈도   실행당 1회.  같은 이벤트를 반복 발송하지 않는다
```

```
필수   알림 본문에 근거를 넣는다 — 무엇이 · 얼마에서 얼마로 · 언제
금지   「좋은 매물입니다」 같은 판단 문구.  사실만 낸다
```

**알림 문구 규격**

```
price_drop    3,470만 → 3,420만 (−50만)
target_hit    목표가 3,400만 도달 (현재 3,380만)
gone          목록에서 사라짐.  마지막 3,420만 · 2026-08-09
relist        같은 차량이 새 매물로 등록 (−50만).  결합 근거 차량번호
grade_change  B → A.  원인 매물 변동 (가격 인하)
```

---

## STEP 117 — `/watch` 화면

**v1 구성을 유지하고 항목을 보강한다.**

| 열 | v1 | v2 |
|---|---|---|
| 매물 | O | + `vehicle_id` 묶음 표시 |
| 등급 · 점수 | O | + 분모 · 버전 |
| 가격 | O | + 추이 스파크라인 (`watch_track`) |
| 목표가 | — | **신설** `target_price_won` |
| 메모 | O | O |
| 알림 설정 | 3종 | **6종** (`drop`·`target`·`gone`·`relist`·`grade`·`dom`) |
| 상태 | — | **신설** watching · gone · relisted · closed |
| 최근 이벤트 | — | **신설** 최근 3건 |

```
필수   gone 매물을 목록에서 지우지 않는다.  상태로 구분해 남긴다
필수   같은 vehicle_id 는 묶어서 보여준다.  같은 차를 두 줄로 세지 않는다
필수 [마스터] 08-18 — 묶되 「N번 재등록」을 표시한다
       ★ 내렸다 다시 올린 것은 그 자체가 정보다
       ★ 값이 바뀌었으면 함께 낸다 — 「2번 재등록 · 3,200만 → 2,990만」
검산   V7-14  재등록 횟수가 화면에 나오는가
```

---

## STEP 117a — 조건 추적 (Watch Query)

**11장은 「이 매물」을 추적한다. 여기서는 「이런 차」를 추적한다.**

```sql
CREATE TABLE watch_query (
  query_id        INTEGER PRIMARY KEY,
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

CREATE TABLE watch_query_hit (
  query_id    TEXT NOT NULL,
  listing_id  TEXT NOT NULL,
  first_hit_at TEXT NOT NULL,
  notified    INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (query_id, listing_id)
);
```

### 동작

```
매 실행 후   활성 쿼리를 돌린다
신규 매물     watch_query_hit 에 적재 + 알림
기존 매물     가격이 바뀌면 알림 (notify_on_price)
```

```
예   「그랑 콜레오스 1.5 E-TECH · 2025년식 이상 · 3만km 이하 · 3,400만 이하 · B등급 이상」
    조건에 맞는 차가 새로 올라오면 알린다
```

```
필수   조건은 config 가 아니라 데이터다.  사용자가 화면에서 만든다
금지   쿼리를 코드에 박는 것
```

---

## STEP 118 — 최종 후보 확정

**추적의 끝은 「이 차를 산다」다.**

```sql
CREATE TABLE watch_candidate (
  listing_id     INTEGER PRIMARY KEY,
  vehicle_id    TEXT,
  decided_at     TEXT NOT NULL,
  decision       TEXT NOT NULL,   -- shortlist · final · rejected · contracted
  reason         TEXT,
  score_snapshot TEXT NOT NULL,   -- 결정 시점 ScoreView 직렬화
  cost_snapshot  TEXT,            -- 결정 시점 실구매가 내역 (STEP 83)
  versions       TEXT NOT NULL,
  checklist_json TEXT,            -- 구매 실행 체크리스트 (STEP 118a)
  contacted_at   TEXT,
  inspected_at   TEXT,
  contracted_at  TEXT,
  CHECK (decision IN ('shortlist','final','rejected','contracted'))
);
```

```
필수   결정 시점의 점수를 통째로 얼려 저장한다
이유   나중에 배점이 바뀌어도 「그때 왜 이걸 골랐나」가 남아야 한다
표시   현재 점수와 결정 시점 점수를 나란히 보여준다.  다르면 원인을 분류해 표시
```

**10장 `/` 현황의 「최종후보」 블록이 이 테이블을 읽는다.**

---

## STEP 118a [목록] — 구매 실행 체크리스트

**추적의 끝은 「샀다」다. 점수와 무관하게 실물 확인이 남는다.**

```
목적    후보를 확정한 뒤 계약까지의 확인 항목을 빠뜨리지 않는다
항목    아래 4단계.  각 항목에 완료 여부와 메모를 남긴다
```

### 1단계 — 연락 전 (문서로 확인)

```
[ ] 성능점검기록부 원본과 화면 표시가 일치하는가
[ ] 보험이력의 사고 건수 · 금액이 화면과 같은가
[ ] 경고(listing_warning)를 전부 읽었는가
[ ] 딜러 신뢰도 · 4분면을 확인했는가
[ ] 같은 차가 다른 매물로도 올라와 있는가 (vehicle_id)
[ ] 실구매가를 계산했는가 (표시가 + 부대비용)
```

### 2단계 — 연락 시 (딜러에게 확인)

```
[ ] 매물이 실재하는가.  「방금 팔렸다」면 미끼 신호다
[ ] 표시가에서 추가되는 비용이 있는가 (탁송 · 이전 대행 · 수수료)
[ ] 성능보증 가입 여부와 범위
[ ] 실차 확인이 가능한가.  언제 · 어디서
[ ] 시운전이 가능한가
```

```
★ 「방금 팔렸다 · 다른 차를 보여주겠다」는 전형적 미끼 응대다
  그 매물의 listing_warning 에 기록한다.  다음 판단의 근거가 된다
```

### 3단계 — 실차 확인 (현장)

```
[ ] 차대번호가 서류 · 매물 정보와 일치하는가
[ ] 주행거리가 점검부 기록과 맞는가 (조작 확인)
[ ] 외판 상태가 점검부 표시와 맞는가
[ ] 옵션이 광고와 일치하는가 (HUD · 선루프)
[ ] 하부 · 엔진룸 누유
[ ] 시운전 — 변속 · 제동 · 소음 · 경고등
```

```
★ 3단계에서 광고와 다른 점이 나오면 그 자체가 경고다
  차량 문제가 아니라 딜러 문제일 수 있다
```

### 4단계 — 계약

```
[ ] 계약서에 차대번호 · 주행거리 · 성능보증이 명시됐는가
[ ] 표시가와 계약가가 같은가.  다르면 사유
[ ] 명의이전 일정과 책임 주체
[ ] 인수 시점과 방법 (직접 · 탁송)
[ ] 리콜 미이행 항목이 있는가
```

```
★★★ 08-18 폐기 — 마스터 지적

```
마스터  「내가 엔카랑 직거래를 하기 위한 용도지 판매 대행 용도가 아닌데 뭘까?」
★ 계약 4단계는 판매를 대행하는 쪽이 쓰는 것이다
★ 마스터는 사는 사람이다.  대행하지 않는다
★ 가이드가 쓰는 사람을 잘못 잡았다
```

### 대신 — 사는 사람의 진행

```
필수 [마스터]   담아 둔 매물에 진행을 적을 수 있게 한다
                연락함      언제 · 누구에게 · 무슨 말을 들었나
                보러 감     언제 · 무엇을 봤나
                끝          샀다 · 안 샀다 · 왜
필수 [마스터]   단계를 강제하지 않는다.  건너뛸 수 있다
                ★ 전화만 하고 끝날 수도 있다
필수 [마스터]   메모가 본체다.  단계는 메모를 정리하는 이름일 뿐이다
필수 [기술]     결정 시점의 점수를 얼려 둔다 (기존 유지)
                ★ 왜 그때 골랐는지는 남아야 한다
금지 [마스터]   계약·대행 절차를 넣는 것
금지 [마스터]   체크리스트를 점수에 반영하는 것 (기존 유지)
검산            V7-15  진행 메모를 자유롭게 적을 수 있는가
```

~~필수   각 단계 완료 시각과 메모를 watch_candidate 에 남긴다~~
근거   나중에 문제가 생겼을 때 무엇을 확인했고 무엇을 못 했는지가 남아야 한다
금지   체크리스트를 점수에 반영하는 것.  이것은 절차이지 평가가 아니다
```

---

## STEP 119 — 추적 검증

| 코드 | 검사 | 등급 |
|---|---|---|
| V7-01 | `watch_track` 에 `parse_version`·`dict_version`·`calc_version` NOT NULL · `coefficient_id` 존재 | fatal |

```
★ coefficient 는 버전 문자열이 아니라 coefficient_history 행이다
  컬럼명은 coefficient_id.  「버전 4종」이라 적으면 _version 으로 읽힌다
```
| V7-02 | `cause != 'listing'` 인 이벤트가 알림 발송되지 않음 | fatal |
| ~~V7-03~~ | 「판매됨」 문구 검사 → **V6-06 으로 통합** (10장) | — |
| V7-04 | 같은 이벤트 중복 발송 0건 | fatal |
| V7-05 | `gone` 매물이 목록에서 삭제되지 않음 | fatal |
| V7-06 | 검증 실패 실행에서 알림이 나가지 않음 | fatal |
| V7-07 | `relist` 결합에 `identity_kind` 기록 | warn |
| V7-08 | 구매 체크리스트가 점수·등급에 반영되지 않음 | fatal |
| V7-09 | 실구매가·총소유비용이 점수에 반영되지 않음 | fatal |
| V7-10 | 발송 시도 대비 성공률 (2차) | warn |
| V7-11 | `closed_reason` 이 CHECK 안의 값 | code | fatal |
| V7-12 | 남의 `watch_id` 로 수정·종료가 거부됨 | contract | fatal |

---

## STEP 119a — v1 승계 규칙 ★ 한 곳에 모은다

**마이그레이션 스크립트가 한 절만 보면 되도록 한다.**

| v1 | v2 | 처리 |
|---|---|---|
| `watchlist` 8행 | `watch_item` | 이관. `alert_on_sold=1` → **`on_gone=1`** |
| `watchlist.alert_on_drop` | `on_price_drop` | 그대로 |
| `watchlist.alert_on_dom` · `dom_threshold` | `on_dom` · `dom_threshold_days` | 그대로 |
| `watchlist.memo` · `added_date` | `memo` · `added_at` | 그대로 |
| — | `target_price_won` · `on_target_price` · `on_relist` · `on_grade_change` | 신설. `config` 기본값 |
| `price_history` | `watch_track` | **이관하지 않는다.** 점수·버전이 없어 시계열로 쓸 수 없다 |
| | `core_listing_change` | 가격 변동만 이관 가능 (선택) |
| `sold_price` · `sold_at` · `listing_days` 293건 | — | **이관하지 않는다.** 근거 없는 추정값 (8장 STEP 87) |
| `comparison` | `watch_candidate` | 비교 이력이 있으면 `decision='shortlist'` 로 |

```
원칙   근거가 없는 값은 이관하지 않는다.  참고가 필요하면 v1 DB 원본을 보관한다
검증   이관 후 watch_item 행수 == v1 watchlist 행수
```

## STEP 120 — 추적 미확정

| # | 항목 | 상태 |
|:--:|---|---|
| 1 | 외부 알림 채널 | **1차는 화면 배지만.** 계정별 채널 설정은 2차 (아래) |
| 2 | `dom_threshold_days` 기본값 | v1 은 NULL. 근거 없음 → `config` |
| 3 | `relist` 판정 유예 기간 | `gone` 후 며칠까지를 재등록으로 볼지 미정 |
| 4 | 목표가 알림 반복 | 도달 후 재하락 시 다시 알릴지 |
| 5 | v1 `watchlist` 8행 승계 | `alert_on_sold=1` → `on_gone` 으로 매핑. 나머지 기본값 |

```
원칙   미확정은 config 기본값으로 돌리되 리포트에 「미확정」으로 표시한다
```

---

**11장 종료 (STEP 111–120).**
**11장 종료. 12장은 2차 사이트 착수 시점에 시작한다.**

---



---

## ★ 관심 목록 화면 — 08-16

**마스터 지적 — 「차종이랑 사진이 없으면 내가 어떻게 판단하나」**

```
실측 08-16
  <img> 0 · 차종 열 없음 · /why 링크 1개
  열   등급 · 트림 · 연식 · 가격 · 목표가 · 상태 · 가격 추이
```

```
★ 트림만 있고 차종이 없다
  「가솔린 2.5 터보 AWD」만 보고 무슨 차인지 모른다
★ 사진이 없다
  관심에 담아 둔 차를 며칠 뒤에 보면 어느 차인지 기억이 안 난다
```

```
필수   사진을 낸다.  ★ 크기는 `61-web/a-common.md` 표의 「관심」 행이다
       ~~최소 128px~~ ★ 폐기 — 개정 368 (개정 404)
필수   차종을 낸다.  트림만 내지 않는다
필수   행 전체가 그 매물의 상세로 간다
       ★ 사진 · 차종 · 트림 · 가격 어디를 눌러도 /why 로
필수   툴팁에 요약을 낸다
       차종 · 트림 · 연식 · 주행 · 가격 · 등급 · 강점
       ★ 목록의 미리보기(#peek)와 같은 것을 쓴다
필수   엔카 원문 링크도 낸다 (STEP 149q)
금지   상세로 가는 길이 한 곳뿐인 것
       ★ 「근거」 글자 하나만 링크면 손가락으로 누르기 어렵다
검산   V7-12  관심 목록에 사진과 차종이 있는가
       V7-13  행에서 상세로 갈 수 있는가
```

```
★ 관심 목록은 「내가 고른 차들」이다
  목록 화면보다 더 자세해야지 덜하면 안 된다
  지금은 목록보다 정보가 적다
```
