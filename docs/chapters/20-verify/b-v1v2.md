## STEP 55 — V1 수집 검증

```
version  SPEC-2026.09.02-r1065
follows  `docs/chapters/30-score/f-table.md`
sources  실측 08-22
checks   S46-38 · S46-39
```


| 코드 | 검사 | 기대 | 등급 |
|---|---|---|---|
| V1-01 | `expected == requested + not_requested` | 일치 | fatal |
| V1-02 | `not_requested == 0` | 0 | fatal |
| V1-03 | `requested == ok + empty + not_found + error` | 일치 | fatal |
| V1-04 | `rejected == 0` | 0 | fatal |
| V1-05 | **RAW 신규 행 합계** == `ok+empty+not_found+error` | 일치 | fatal |

```
★ RAW 는 세 테이블이다 — raw_response · raw_facet · raw_response_reject
  facet 응답은 raw_facet 에 들어간다.  raw_response 만 세면 항상 어긋난다
```
| V1-06 | 차종별 `ok > 0` | 참 | fatal |
| V1-07 | 매물별 엔드포인트 4종 상태 존재 | 전건 | fatal |
| V1-08 | 동일 코드 실패율 100% 인 엔드포인트 없음 | 없음 | fatal |

### ★ V1-08 — `empty` 는 실패가 아니다

```
전량 실패    ok 도 empty 도 0 일 때만 해당한다
근거        empty 는 요청이 성공했고 사이트에 자료가 없는 것이다 (STEP 16)
           실패로 세면 정상 상태가 매번 붉게 뜬다

★ 진단(diagnosis)이 대표 사례다
  「받지 않은 차」가 대부분이라 empty 가 정상이다
  not_found 로 두면 V1-08 이 매번 걸린다
구분        전량 404 는 「전량 실패」가 아니라 「경로 오류」로 따로 표시한다
           조치가 다르다 — 경로 오류는 STEP 25a 실측 요청이다
```
| V1-09 | 시간대별 실패율 상승 없음 | 안정 | warn |
| V1-10 | `site_query` 의 전 키가 조립된 `q` 에 반영됨 | 전건 | fatal |
| V1-11 | 예외로 종료된 실행이 없음 (전부 `halted` 로 끝남) | 0 | fatal |
| V1-12 | 연속 실패 중단 시 `ResumePoint` 가 남음 | 전건 | fatal |
| V1-13 | 껍데기를 거친 실행과 직접 실행의 인자가 같음 | 일치 | fatal |
| V1-14 | `diagnosis` 호출 대상이 `encarDiagnosis == 0` 으로 좁혀짐 | code | fatal |
| V1-15 | `expected` 에서 `skipped` 를 뺌 | code | fatal |
| V1-16 | 검사가 이번 `run_id` 밖의 행을 보지 않음 | code | fatal |
| V1-17 | `diagnosis` 가 `detail` 뒤에 있음 | code | fatal |
| V1-18 | 빈 DB 에서 전 진입점이 예외 없이 끝남 | code | fatal |
| V1-21 | 받아 두고 안 펼쳐진 원문이 없음 | code | fatal |

### ★ 「이번 실행분」은 `run_id` 로 가른다 — 08-14

```
필수   raw_response.run_id · audit_request.run_id 로 이번 실행을 가른다
금지   fetched_at · checked_at 등 시각으로 추정하는 것
근거   --from S9 는 S5 를 안 돈다.  옛 요청 기록이 그대로 남는다
      시각으로 가르면 「안 돈 단계」와 「방금 돈 단계」가 섞인다 (개발측 실측 08-14)
      워커를 늘리면 시각 비교가 더 깨진다
```

```
V1-14 판별
  WHERE run_id = :this_run AND endpoint = 'diagnosis'
  대상이 0 건이면 통과한다.  「안 돌았다」는 실패가 아니다
필수   단계를 안 돈 실행에서 그 단계의 검사는 not_applicable 이다
금지   안 돈 단계를 fatal 로 내는 것.  --from 이 쓸모없어진다
검산   V1-16  검사가 이번 run_id 밖의 행을 보지 않는가
```

```
★ raw_response.run_id 는 NOT NULL 이다
근거   「어느 실행에서 받았나」를 모르는 원문은 재현에 쓸 수 없다
필수   migrate 는 옛 행에 그 실행의 run_id 를 채워 넣고 NOT NULL 을 건다
      채울 수 없으면 'unknown' 이 아니라, 그 원문의 fetched_at 이 속한
      audit_request 의 run_id 를 찾아 넣는다
금지   migrate 가 막힌다는 이유로 제약을 푸는 것
      제약은 데이터가 맞다는 약속이다.  구현 사정으로 바꾸지 않는다
검산   V2-22  현재 스키마 == sql/ddl
```

### ★ `V1-16` 의 대상 — 「이번 실행」을 묻는 검사만

```
대상    v1_collect — 이번 실행에서 무엇을 받았나
제외    V4-* 매핑률 — 누적을 본다
근거   매핑률은 「지금까지 받은 원문 중 몇 %를 매핑했나」다
      run_id 를 걸면 이번 실행에서 안 받은 것이 분모에서 빠져 100% 가 된다
필수   검사마다 「이번 실행분인가 누적인가」를 Check 에 적는다
금지   전 검사에 run_id 를 일괄로 거는 것.  누적 검사가 무의미해진다
```
| V1-08b | 엔드포인트별 전량 404 가 없음 | 없음 | fatal |

```
V1-04 형식 검증 거부   1건이라도 있으면 URL·응답 변경 신호 (2장 STEP 25a)
V1-08 전량 실패        코드 문제로 가정.  차단으로 단정하지 않는다
```

---

## STEP 56 — V2 적재 검증 · 기본

| 코드 | 검사 | 기대 | 등급 |
|---|---|---|---|
| V2-01 | `ok` 원문 수 == CORE 행 수 | 일치 | fatal |
| V2-02 | 필수 컬럼 NOT NULL 위반 없음 | 0 | fatal |
| V2-03 | 타입 위반 없음 (숫자 컬럼에 문자 등) | 0 | fatal |
| V2-04 | `status` 열거값 위반 없음 | 0 | fatal |
| V2-05 | 단위 검사 — 가격이 만원 단위로 남아 있지 않은가 | 통과 | fatal |
| V2-06 | 빈 컨테이너가 NULL 로 저장되지 않았는가 | `'[]' > 0` | fatal |
| V2-07 | 전건 NULL 컬럼 목록 | 없음 또는 설명됨 | warn |
| V2-08 | 값 종류 1인 컬럼 목록 | 없음 또는 설명됨 | warn |
| V2-19 | 원문 유래 컬럼에 `NOT NULL` 이 없음 | 0 | fatal |
| V2-20 | 파싱 실패 필드가 있는 행도 CORE 에 있음 | 전건 | fatal |
| V2-21 | `parse_error` · `type_mismatch` 건수 | 감시 | warn |
| V2-22 | 현재 DB 스키마가 `sql/ddl` 과 일치 (STEP 32b) | 일치 | fatal |
| V2-23 | 중간 노드 `None` 인 매물도 CORE 에 있음 | 전건 | fatal |
| V2-24 | 배열 기대 필드가 전건 `list` 로 정규화됨 | 전건 | fatal |
| V2-25 | 스칼라 `null` 이 `0` 으로 저장된 컬럼 없음 | 0 | fatal |
| V2-26 | ~~파서에 중첩 직접 접근 없음~~ → V2-27 로 통합 | — | — |
| V2-27 | `parse/` 에 원문 연쇄 첨자가 없음 (AST · `parse/` 만) | 0 | fatal |
| V2-28 | 파싱 실패 매물의 필드 수가 2 인 행 없음 | 0 | fatal |
| V2-29 | `parsed` 키 중 저장 안 된 것이 접두 예외 외에 없음 | 0 | fatal |
| V2-30 | 전 파서가 `row_status` 를 냄 | code | fatal |
| V2-31 | `target_key` NULL 이 판정에 들어가지 않음 | code | fatal |
| V2-32 | NULL 매물의 모델명이 화면에서 보임 | code | warn |
| V2-09 | **`core_pii` 를 직접 조회하는 코드 없음** (`get_pii` 경유) | 0 | fatal |
| V2-10 | `core_listing` 에 `plate_no` · `dealer_name` · `phone` · `address` 없음 | 0 | fatal |
| V2-10b | 마스킹 컬럼이 `core_*` 에 없음 (`*_masked`) | 0 | fatal |
| V2-11 | `plate_hash` 가 전건 16자 hex | 전건 | fatal |
| V2-12 | `secrets/plate_hmac.key` 가 버전 관리에 없음 | 0 | fatal |
| V2-13 | `core_record` 에 `record_plate_no` 원본 없음 | 0 | fatal |
| V2-14 | **참조되는 테이블 5종의 PK 가 단일 INTEGER** (`core_listing`·`core_vehicle`·`core_dealer`·`account`·`watch_item`) | 전건 | fatal |
| V2-15 | 자연키가 `UNIQUE` 로 걸려 있음 (`(site, source_id)` 등) | 전건 | fatal |
| V2-16 | PK · FK 컬럼에 개인정보가 없음 (번호판 · 실명 · 연락처) | 0 | fatal |
| V2-17 | `core_pii` · `core_dealer_pii` 에 대응 CORE 행 없는 고아 없음 | 0 | fatal |
| V2-18 | `parse_rule` 재처리 후 전 봉투가 현재 `parse_version` | 전건 | fatal |

### V2-05 단위 검사

```
가격 컬럼이 1,000,000 미만인 행이 존재하면 만원 단위가 남아 있다
단   실제로 100만원 미만 매물이 있을 수 있으므로 분포로 판정한다
기준  중앙값이 1,000,000 미만이면 fatal
금지  값 크기로 단위를 추정해 되돌리는 보정 (2장 STEP 20)
```

### V2-06 · V2-07 · V2-08 — v1 사고 직결

```
V2-06   options.choice '[]' 가 0건이면 falsy → None 버그다
V2-07   insp_outer_json 이 전건 NULL 이었다.  사고 20점이 죽어 있었다
V2-08   accident_type 전건 unknown · is_rental 전건 0 · damage_outer 전건 0
```

**「전건 NULL」과 「값 종류 1」은 결함일 수도, 원본이 그런 것일 수도 있다.**
**따라서 warn 이되 반드시 원인을 기록한다** (2장 STEP 24 항목 0·NULL 안내 규격).

```
(a) 원문에 경로가 있고 값도 비었다   →  원본이 그렇다.  설명하고 통과
(b) 원문에 값이 있다                →  파싱 결함.  fatal 로 승격
(c) 원문에 경로가 없다              →  그 엔드포인트가 안 준다.  설명하고 통과
```

---

## STEP 57 — V2 적재 검증 · 전일 대비 GAP

**「어제와 오늘이 왜 다른가」를 설명하지 못하면 데이터를 믿을 수 없다.**

### 변동 4종

| 종류 | 정의 | 정상 여부 |
|---|---|---|
| `increase` | 신규 매물 | 정상 |
| `decrease` | 매물 소멸 (`gone`) | 정상 |
| `change` | 가격 · 판매상태 변경 | 정상 |
| **`anomaly`** | **같은 매물인데 불변 필드가 바뀜** | **보정 대상** |

```
불변 필드   제원 · 연식 · 주행거리 · 트림 · 색상 · 옵션 · vin · plate
           변하면 anomaly (3장 STEP 29)
```

### GAP 리포트 항목

```
전일 총건수 → 금일 총건수
신규 N · 소멸 M · 가격변경 K · 상태변경 L · 이상 X
차종별 동일 항목
```

### 이상 판정 기준

| 지표 | 기준 | 등급 |
|---|---|---|
| 총건수 변동률 | ±30% 초과 | fatal |
| 신규 비율 | 20% 초과 | warn |
| 소멸 비율 | 20% 초과 | warn |
| `anomaly` 건수 | 1건 이상 | warn (원인 분류 필수) |
| 특정 차종 0건 | 발생 | fatal |

```
총건수 ±30%   수집 실패 또는 쿼리 변경을 의심한다.  시장이 하루에 30% 변하지 않는다
차종 0건      쿼리 오류다.  매물 없음으로 단정하지 않는다 (2장 STEP 24)
```

---

