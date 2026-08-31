# SCHEMA — DB 색인

**`python3.11 tools/build_index.py` 가 만든다. 손으로 고치지 않는다.**

```
읽는 법   이 표에서 찾고 sql/ddl/*.sql 을 연다
검산     S28-10  DDL 의 표가 이 파일과 같은가
```

## `sql/ddl/01_raw.sql` — 표 3개

> raw_* 스키마.  지시서 3장 STEP 33 · STEP 39 / 원문은 무손실.  삭제 금지.  실패 응답도 원문이다 (5장 STEP 53-⑤)

| 표 | 열 | 무엇 |
|---|--:|---|
| `raw_response` | 14 | SQLite 고유 문법을 쓰지 않는다 (0장 STEP 8) |
| `raw_facet` | 7 |  |
| `raw_response_reject` | 9 |  |

## `sql/ddl/02_core.sql` — 표 13개

> core_* 스키마.  지시서 3장 STEP 29~35 · STEP 39 / 사이트 무관 공통 스키마.  사이트 고유값은 site_* 접두 (0장 STEP 4)

| 표 | 열 | 무엇 |
|---|--:|---|
| `core_listing` | 120 | 공통 컬럼 6종은 전 core_* 에 둔다 (STEP 31) |
| `core_listing_change` | 7 | 변경분만 쌓는다.  전량 스냅샷을 쌓지 않는다 (STEP 29) |
| `core_vehicle` | 9 | vehicle_id 는 그대로라 relist 추적이 끊기지 않는다 (11장 STEP 112) |
| `vehicle_identity` | 7 | ★ 해시는 결합 「입력」이지 키가 아니다.  원본은 core_pii — 조인 경로에 PII 가 없다 |
| `core_dealer` | 21 | 딜러는 매물의 속성이 아니라 독립 개체다 (STEP 35) |
| `core_dealer_history` | 7 | 행태 지표는 매 실행 덮어쓴다.  이력이 없으면 어제 값을 못 찾는다 |
| `core_inspection` | 28 | 점검.  outers 는 원문 배열 그대로.  가공하지 않는다 (2장 STEP 21) |
| `core_record` | 37 | 이력.  accidents_json 의 type 해석은 Analyzer 가 한다 (2장 STEP 21a) |
| `core_diagnosis` | 13 | 진단 items 와 outers 가 전건 일치함을 582건으로 확인했다 (2026-08-14) |
| `core_diagnosis_item` | 6 | item 으로 두면 「10부위 중 2교환」이 되어 수가 틀린다 |
| `core_parse_issue` | 8 | 둘을 섞으면 파서 버그가 「원문이 그렇다」로 묻힌다 |
| `core_pii` | 5 | 개인정보 분리 (STEP 35).  get_pii() 로만 읽는다 — 직접 SELECT 금지 (V2-09) |
| `core_dealer_pii` | 5 | 딜러 단위.  같은 딜러가 매물 100건이면 연락처가 100번 들어가면 안 된다 |

## `sql/ddl/03_dict.sql` — 표 3개

> dict_* 스키마.  지시서 3장 STEP 36 · 4장 STEP 40~45 / 사전은 손으로 적지 않는다.  RAW 에서 생성한다

| 표 | 열 | 무엇 |
|---|--:|---|
| `dict_option_code` | 9 | 상태 4종.  retired 는 삭제하지 않는다 — 과거 매물 해석에 필요하다 |
| `dict_model_option` | 10 |  |
| `dict_enum` | 11 |  |

## `sql/ddl/04_result.sql` — 표 5개

> result_* 스키마.  지시서 3장 STEP 37 · 6장 STEP 64 · 7장 STEP 83·84 / result_* 는 버려도 된다.  버전이 다르면 다른 결과다 — 덮어쓰지 않는다

| 표 | 열 | 무엇 |
|---|--:|---|
| `result_axis` | 10 | result_* 는 버려도 된다.  버전이 다르면 다른 결과다 — 덮어쓰지 않는다 |
| `result_score` | 20 |  |
| `depreciation_curve_history` | 6 | 감가 곡선 산출 이력.  곡선이 어떻게 나왔는지 남지 않으면 재현이 안 된다 |
| `coefficient_history` | 9 | 계수 보정 이력.  남기지 않으면 점수 변동 원인을 사후에 못 찾는다 |
| `result_axis_conflict` | 7 | 금지   충돌을 무시하고 넘어가는 것.  v1 의 사고가 전부 그렇게 시작했다 |

## `sql/ddl/05_meta.sql` — 표 1개

> meta_* 스키마.  지시서 8장 STEP 87 / ★ 등록부는 산문이 아니라 테이블이다.  문서는 기계가 검증할 수 없다

| 표 | 열 | 무엇 |
|---|--:|---|
| `meta_field_usage` | 14 | v1 방치의 근본 원인은 미사용 목록이 문서에만 있었다는 것이다 |

## `sql/ddl/06_audit.sql` — 표 2개

> audit_* 스키마.  지시서 3장 STEP 38 · 6장 STEP 66 / 검증 결과를 테이블에 남긴다.  화면 출력만 하면 어제와 비교할 수 없다

| 표 | 열 | 무엇 |
|---|--:|---|
| `audit_request` | 11 | 검증 결과를 테이블에 남긴다.  화면 출력만 하면 어제와 비교할 수 없다 |
| `audit_validation` | 11 |  |

## `sql/ddl/07_watch.sql` — 표 9개

> 활용 테이블.  지시서 11장 STEP 112a · 113 · 117a · 118 · 7장 STEP 82d / ★ status 는 네 곳에서 뜻이 다르다.  DDL 의 CHECK 로 집합을 강제한다

| 표 | 열 | 무엇 |
|---|--:|---|
| `listing_warning` | 7 | 경고.  점수에 합산하지 않는다.  목록에서 제외하지 않는다 (V3-21·22·23) |
| `watch_item` | 17 | 관심 등록.  ★ 차량 단위다.  같은 차를 두 번 등록하지 않는다 |
| `watch_track` | 9 | 스냅샷.  ★ 점수를 복제하지 않는다.  버전 키로 result_score 를 조인한다 |
| `watch_event` | 11 |  |
| `watch_query` | 11 | 금지   쿼리를 코드에 박는 것.  조건은 config 가 아니라 데이터다 |
| `watch_query_hit` | 4 |  |
| `watch_candidate` | 5 |  |
| `vehicle_duplicate` | 6 | 동시 중복 게시.  ★ 재등록이 아니다 (STEP 112) |
| `watch_note` | 6 | 순서도 없고, 앞 단계 없이 'done' 을 적어도 된다 |

## `sql/ddl/08_admin.sql` — 표 8개

> 관리자 저장소.  지시서 13장 STEP 126~137 · 3장 STEP 28 / ★ 관리자 화면에서 하는 일은 전부 config 변경 또는 실행 지시다

| 표 | 열 | 무엇 |
|---|--:|---|
| `account` | 10 | ★ 관리자 화면에서 하는 일은 전부 config 변경 또는 실행 지시다 |
| `auth_session` | 5 |  |
| `config_change` | 10 | config 에도 버전이 필요하다.  result_* 가 calc_version 을 갖는 것과 같다 |
| `query_log` | 8 |  |
| `dev_request` | 11 |  |
| `recalc_job` | 15 | 관리자가 단계를 직접 고르지 않는다.  재처리 결정표가 from_step 을 준다 |
| `admin_api_snapshot` | 8 |  |
| `auth_login_attempt` | 5 | 금지   계정을 영구 잠그는 것.  1인 도구라 스스로 못 풀면 CLI 로 가야 한다 |

**표 44개.**

