# 12장. 후속 — 다중 사이트 확장 (STEP 121–125)

## 12장 정의서

**1차는 엔카 단독이다. 이 장은 2차 사이트를 붙일 때 하는 일이다.**

```
선행   1~11장 완료 · 엔카 결과가 calc_version 으로 얼려져 있을 것
목적   사이트를 추가해도 core_* · Analyzer · Scorer · Reporter 가 바뀌지 않게 한다
```

**앞장에 이미 들어간 것 — 여기서 다루지 않는다**

| 항목 | 위치 |
|---|---|
| 딜러 신뢰도 | 7장 STEP 82b · 82c |
| 경고 신호 11종 | 7장 STEP 82d |
| 유사군 (Peer Group) | 7장 STEP 82e |
| 딜러·경고 화면 | 10장 STEP 103a |
| 비중 조정 · 시뮬레이션 | 10장 STEP 103b |
| 조건 추적 (Watch Query) | 11장 STEP 117a |
| 사이트 상수 · 예약 | 8장 STEP 89 |
| `core_vehicle` · `vehicle_id` | 3장 STEP 30 · 35 |

**1차에서 자리를 만들어 뒀으므로, 이 장은 어댑터와 매핑 작업이다.**

### 구조체

```python
@dataclass(frozen=True)
class CrossSiteMatch:
    vehicle_id: int
    listings: list[tuple[str, str, int]]   # (site, listing_id, price_won)
    price_spread_won: int
    match_source: str           # plate · vin · site_id
    confidence: str             # confirmed · probable
```

### 함수

| 이름 | 입력 | 출력 | 목적 |
|---|---|---|---|
| `match_cross_site` | `vehicle_id` | `CrossSiteMatch \| None` | 사이트 간 동일 차량 |
| `rebuild_core_vehicle` | `run_id` | `int` | `core_vehicle` 집계 갱신 |
| `regression_check` | `calc_version` | `RegressionReport` | 기존 사이트 결과 불변 확인 |

---

## STEP 120a [규격] — 보관과 발송 ★

```
목적    추적 데이터를 언제까지 두고, 알림을 어떻게 보내는지 정한다
원천    watch_track · watch_event
입력    없음
출력    보관 정책 · 발송 계약
값규칙  스냅샷은 지우지 않는다.  이벤트는 발송 여부와 무관하게 남는다
근거    가격 추이는 기간이 길수록 값이 있다
금지    발송 실패를 조용히 넘기는 것
검산    V7-10  발송 시도 대비 성공률
```

### 보관

| 테이블 | 기간 | 근거 |
|---|---|---|
| `watch_track` | **영구** | 가격 추이. 지우면 그래프가 끊긴다 |
| `watch_event` | **영구** | 「그때 알림이 갔나」의 증거 |
| `watch_candidate` | 영구 | 후보 이력 |
| `audit_request` · `query_log` | 90일 | 로그 |

```
필수   영구 표시된 것을 지우는 코드를 두지 않는다
근거   4,700건 × 하루 1행이면 연 170만 행이다.  SQLite 가 감당한다
      용량이 문제되면 그때 정한다
```

### 발송 — 1차는 화면만

```
1차   화면 배지 + L3 리포트.  외부 채널 없음
2차   notify_channel(account_id, kind, target, enabled)
```

```
근거   1인 사용 도구다.  화면에서 보면 충분하다
필수   1차에도 watch_event.notified 를 기록한다
       「화면에 표시했다」도 발송이다.  기록 구조는 지금 만든다
```

### 발송 기록 — 컬럼

```sql
ALTER TABLE watch_event ADD COLUMN notify_attempted_at TEXT;
```

```
notify_attempted_at   시도 시각.  보내기 전에 먼저 쓴다
notified              결과.  성공 시 1
필수   시도 없이 notified=1 이 될 수 없다
근거   「보냈다」를 낙관하면 실패가 묻힌다
```

### 발송 계약 (2차)

```
필수   발송 시도를 먼저 기록하고 보낸다.  결과를 갱신한다
필수   실패해도 이벤트는 남는다.  다시 보낼 수 있어야 한다
재시도  지수 백오프
금지   발송 성공을 낙관해 notified=1 로 먼저 쓰는 것
금지   검증 실패 실행에서 보내는 것 (V7-06)
검증   V7-10
```

### 중복 방지

```
키     (watch_id, event_type, listing_id, 날짜)
필수   재실행해도 중복이 안 난다.  V7-04 가 본다
```

---

## STEP 121 — 착수 조건

**아래가 전부 참이어야 2차 사이트를 붙인다.**

```
[ ] 1차(엔카) 수집·판정·채점이 정상 동작한다
[ ] 그 시점 결과가 calc_version 으로 고정돼 있다 (회귀 시험 기준선)
[ ] config/sites.json 에 대상 사이트가 planned 로 등록돼 있다
[ ] dict_* · coefficient_history 키에 site 가 들어가 있다 (3장)
[ ] core_vehicle 에 site_count 가 있다
    ★ core_vehicle 은 사이트를 가로지르는 개체다.  site 단일 컬럼이 성립하지 않는다
[ ] CORE 컬럼명에 사이트 고유 명칭이 없다 (0장 STEP 4)
```

**하나라도 아니면 1차를 먼저 정리한다.** 그러지 않으면 2차를 붙이며 CORE 를 고치게 된다.

---

## STEP 122 — 사이트 추가 작업

**8장 STEP 89 절차 7단계를 그대로 따른다.**

```
1  원문 확보        일반 필드 300건+ · 조건부는 모집단 전수 · 희귀값은 미관측 명시
2  경로 전수 추출    사이트별 매핑표 (2장 규격)
3  EndpointSpec    required_keys 를 응답에서 도출.  추정 금지
4  사전 생성        RAW 에서 distinct 추출 (4장)
5  매핑 검증        값 대조.  A등급 필드 100% (6장 V4)
6  분류 매핑        사이트 차종 표현 → target_key
7  회귀 시험        기존 사이트 결과가 바뀌지 않는지 확인
```

**대상 사이트**

```
kcar          K카
kbchachacha   KB차차차
dealer_site   딜러 자체 사이트 3~5곳.  인스턴스 형식 dealer_site:{slug}
```

```
주의   딜러 자체 사이트는 점검부·이력 API 가 없을 수 있다
      수집 가능한 엔드포인트 집합을 EndpointSpec 으로 선언한다
      → 분모가 달라진다.  점수를 직접 비교하지 않는다
```

---

## STEP 123 — 타 사이트 동일 차량 ★

**`vehicle_id` 로 사이트를 가로질러 묶는다** (3장 STEP 30).

### 판정

| 결과 | 표시 |
|---|---|
| **`active` 사이트가 1개뿐** | **「비교 대상 없음 (수집 사이트 1곳)」** |
| 활성 사이트 중 엔카에만 존재 | **「엔카 단독 매물」** |
| 2개 이상 사이트 | **「N개 사이트에 게시 · 가격차 M만」** |
| 결합 근거 불명 | 표시하지 않는다. 추정 결합 금지 |

```
★ 1차는 active 사이트가 엔카 하나다
  「엔카 단독 매물」이라고 쓰면 거짓이 된다.  비교하지 않았을 뿐이다
필수   config/sites.json 의 active 개수를 보고 문구를 고른다
```

```
필수   match_source (plate · vin · site_id) 와 confidence 를 함께 낸다
필수   가격차를 평균 내지 않는다.  각 사이트 가격을 그대로 나열한다
```

### 가격차가 뜻하는 것

```
같은 차 · 다른 가격   →  낮은 쪽이 협상 여지의 근거
큰 가격차            →  한쪽 정보가 오래됐거나, 조건이 다르다.  확인 대상
사이트 하나만        →  비교 근거가 없다.  유사군(STEP 125)으로 대신한다
```

```
★ 사이트별 점수를 직접 비교하지 않는다 (8장 STEP 89)
  수집 항목이 달라 분모가 다르다.  가격만 비교한다
```

---

## STEP 123a — 12장 검증

| 코드 | 검사 | 등급 |
|---|---|---|
| V9-01 | `CrossSiteMatch` 가 `match_source`·`confidence` 를 표시 | fatal |
| V9-02 | 사이트 간 점수 직접 비교 없음 | fatal |
| V9-03 | `active` 사이트가 1개면 「단독 매물」로 표기하지 않음 | fatal |
| V9-04 | 사이트 추가 후 기존 사이트 결과 불변 (STEP 124) | fatal |

---

## STEP 124 — 회귀 시험 ★

**사이트를 추가했는데 엔카 점수가 바뀌면 CORE 가 오염된 것이다.**

```
기준선   1차 완료 시점의 calc_version 결과
방법     새 사이트 추가 후 같은 calc_version 으로 엔카만 재채점
기대     전 매물의 score_total · grade 가 동일
```

| 결과 | 판정 |
|---|---|
| 완전 일치 | 통과 |
| 일부 변동 | **fatal.** CORE 또는 사전이 오염됐다 |
| 분모 변동 | **fatal.** 사이트별 엔드포인트 집합이 섞였다 |

```
금지   「새 사이트 때문에 조금 바뀐 것」으로 넘기는 것
      바뀌었다면 사이트 격리가 깨진 것이다
```

---

## STEP 125 — 12장 미확정

| # | 항목 | 상태 |
|:--:|---|---|
| 1 | K카 · KB차차차 엔드포인트 | 미확인. 원문 확보 후 |
| 2 | 딜러 자체 사이트 목록 | 미정. 3~5곳 예정 |
| 3 | 사이트별 수집 범위 차이 | 원문 확보 후 |
| 4 | 사이트 간 우선순위 | 같은 차가 여러 곳에 있을 때 어느 매물을 대표로 볼지 |

```
원칙   미확정은 착수하지 않는다.  추정으로 어댑터를 만들지 않는다
```

---

**12장 종료 (STEP 121–125).**

---

