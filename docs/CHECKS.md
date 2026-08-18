# 검사 색인 — 규격 ↔ 코드

**`python3.11 tools/build_index.py` 가 만든다. 손으로 고치지 않는다.**

검사 **316개**

| 갈래 | 몇 개 | 누가 |
|---|--:|---|
| ② 죽은 검사 — 통과도 실패도 한 적 없다 | **62** | 개발측 |
| ④ 규격에 근거가 없는 검사 | **13** | 가이드가 판단 |
| ⑤ ★ 규격에 있는데 코드에 없는 검사 | **33** | 개발측 |

★ ① 중복 · ③ 못 잡는 검사는 기계가 못 가릅니다 — 가이드·테스터 몫입니다 (개정 344).

| 코드 | 무엇 | 등급 | 소스 | 마지막 통과 | 마지막 실패 | 규격 |
|---|---|---|---|---|---|---|
| `S1` | 디렉터리 (STEP 15) | fatal | `tools/check_src.py:163` | **★ 없음** | 없음 | ref/E-attach.md:54 · guide/01_시작.md:213 · guide/03_이력.md:266 |
| `S2` | 구조체 정의 | fatal | `tools/check_src.py:185` | **★ 없음** | 없음 | ref/E-attach.md:55 · guide/03_이력.md:266 · chapters/13-pipeline.md:101 |
| `S3` | 함수 정의 | fatal | `tools/check_src.py:206` | **★ 없음** | 없음 | ref/E-attach.md:55 · guide/03_이력.md:266 · chapters/12-dict.md:175 |
| `S4` | 매물 적재 | fatal | `collect/runner.py:525` | **★ 없음** | 없음 | ref/E-attach.md:56 · guide/03_이력.md:124 · guide/03_이력.md:142 |
| `S5` | config 키 (V4-15) | fatal | `tools/check_src.py:305` | **★ 없음** | 없음 | ref/E-attach.md:57 · guide/01_시작.md:112 · guide/01_시작.md:189 |
| `S6` | 배점 검산 (불변식 ⑤) | fatal | `tools/check_src.py:340` | **★ 없음** | 없음 | ref/E-attach.md:58 · guide/03_이력.md:277 · chapters/13-pipeline.md:105 |
| `S7` | 매직 넘버 (V4-13) | fatal | `tools/check_src.py:395` | **★ 없음** | 없음 | ref/E-attach.md:59 · chapters/13-pipeline.md:106 · chapters/13-pipeline.md:107 |
| `S8` | 접미사 규칙 (STEP 4) | fatal | `tools/check_src.py:402` | **★ 없음** | 없음 | ref/E-attach.md:60 · guide/03_이력.md:80 · chapters/13-pipeline.md:107 |
| `S9` | 금지 근거 (STEP 14) | fatal | `tools/check_src.py:418` | **★ 없음** | 없음 | ref/A-check.md:47 · ref/E-attach.md:61 · guide/03_이력.md:191 |
| `S10` | 도메인 예외 (STEP 3) | fatal | `tools/check_src.py:424` | **★ 없음** | 없음 | ref/E-attach.md:62 · guide/03_이력.md:256 · chapters/13-pipeline.md:111 |
| `S11` | 분석 계층 순수성 (STEP 2) | fatal | `tools/check_src.py:443` | **★ 없음** | 없음 | ref/E-attach.md:63 · guide/01_시작.md:60 · guide/01_시작.md:92 |
| `S12` | 축 파일 STEP 주석 | fatal | `tools/check_src.py:458` | **★ 없음** | 없음 | ref/E-attach.md:64 · guide/01_시작.md:224 · chapters/13-pipeline.md:113 |
| `S13` | 본문 config 예시 대조 | fatal | `tools/check_src.py:525` | **★ 없음** | 없음 | ref/B-config.md:290 · ref/D-update.md:23 · ref/E-attach.md:65 |
| `S14` | 상수 등록·성격 (V4-17) | fatal | `tools/check_src.py:574` | **★ 없음** | 없음 | ref/E-attach.md:66 · chapters/20-verify/c-v3v4.md:201 · chapters/20-verify/c-v3v4.md:207 |
| `S14-1` | 화면에 배점을 박지 않음 (V4-17) | fatal | `tools/check_src.py:607` | **★ 없음** | 없음 | — |
| `S15` | 계층 의존 (STEP 15) | fatal | `tools/check_src.py:485` | **★ 없음** | 없음 | ref/E-attach.md:67 · guide/03_이력.md:108 · chapters/10-collect/00-intro.md:218 |
| `S16` | 검증 코드 대조 | fatal | `tools/check_src.py:655` | **★ 없음** | 없음 | ref/E-attach.md:68 · ref/E-attach.md:207 · guide/03_이력.md:145 |
| `S23` | 실행 환경 (Python 3.11+) | fatal | `tools/check_src.py:662` | **★ 없음** | 없음 | ref/E-attach.md:75 · guide/03_이력.md:249 · chapters/00-standard.md:15 |
| `S24` | 시험 격리 (운영 DB 미사용) | fatal | `tools/check_src.py:681` | **★ 없음** | 없음 | ref/E-attach.md:76 · guide/03_이력.md:253 · chapters/00-standard.md:94 |
| `S25` | 형상 관리 (미커밋 없음) | fatal | `tools/check_src.py:701` | **★ 없음** | 없음 | ref/E-attach.md:77 · guide/01_요구사항.md:829 · guide/01_요구사항.md:838 |
| `S26` | 작업 기록 (6절 · 이름 규칙) | fatal | `tools/check_src.py:729` | **★ 없음** | 없음 | ref/E-attach.md:78 · guide/01_요구사항.md:829 · guide/01_요구사항.md:838 |
| `S27` | 기능마다 화면 (CLI 는 완성이 아니다) | fatal | `tools/check_src.py:788` | **★ 없음** | 없음 | ref/E-attach.md:79 · guide/02_결함대장.md:163 · guide/02_결함대장.md:173 |
| `S28` | 검사 색인 (규격 ↔ 코드) | fatal | `tools/check_src.py:811` | **★ 없음** | 없음 | INDEX.md:14 · SCHEMA.md:7 · ref/E-attach.md:80 |
| `S29-0` | 가벼운 점검 (4시간 · 실제로 돎) | fatal | `tools/check_src.py:842` | **★ 없음** | 없음 | guide/03_원칙지적.md:84 · guide/03_원칙지적.md:94 · guide/03_이력.md:342 |
| `S29-4` | 점검이 찾은 fatal 을 고침 | fatal | `tools/check_src.py:865` | **★ 없음** | 없음 | guide/03_원칙지적.md:98 · guide/03_원칙지적.md:108 · guide/03_이력.md:346 |
| `S34-1` | 표의 규격이 실재 | fatal | `tools/check_src.py:947` | **★ 없음** | 없음 | guide/03_이력.md:356 · chapters/00-standard.md:1531 |
| `S34-2` | 표의 소스·검사가 실재 | fatal | `tools/check_src.py:948` | **★ 없음** | 없음 | chapters/00-standard.md:1532 |
| `S34-3` | 추적표 빈 칸을 센다 | fatal | `tools/check_src.py:899` | **★ 없음** | 없음 | chapters/00-standard.md:1533 · chapters/00-standard.md:1715 · trace/05-score.md:7 |
| `S34-4` | 규격이 표에 있음 | fatal | `tools/check_src.py:958` | **★ 없음** | 없음 | guide/03_이력.md:356 · chapters/00-standard.md:1534 |
| `S35-1` | 자기 칸만 고침 | fatal | `tools/check_src.py:970` | **★ 없음** | 없음 | guide/03_이력.md:357 · chapters/00-standard.md:1563 |
| `S36-1` | 「정식 서비스 착수」 목록이 있음 | fatal | `tools/check_src.py:987` | **★ 없음** | 없음 | guide/03_이력.md:366 · chapters/00-standard.md:1600 · trace/00-standard.md:402 |
| `S37-1` | 파는 쪽 개념이 안 남아 있음 | fatal | `tools/check_src.py:1005` | **★ 없음** | 없음 | guide/03_이력.md:369 · chapters/00-standard.md:1669 · trace/00-standard.md:412 |
| `V0-01` | — | — | **★ 코드에 없다** | — | — | guide/00_버전.md:18 · guide/03_이력.md:337 |
| `V0-02` | — | — | **★ 코드에 없다** | — | — | guide/00_버전.md:43 |
| `V0-03` | — | — | **★ 코드에 없다** | — | — | guide/00_버전.md:65 · guide/03_이력.md:337 |
| `V1-01` | expected == requested + not_requested | run | `validate/v1_collect.py:33` | 2026-08-17 05:33 | 없음 | chapters/00-standard.md:354 · chapters/13-pipeline.md:607 · chapters/20-verify/b-v1v2.md:5 |
| `V1-02` | not_requested == 0 | run | `validate/v1_collect.py:36` | 2026-08-17 05:33 | 없음 | chapters/20-verify/b-v1v2.md:6 · trace/02-collect.md:29 |
| `V1-03` | requested == ok+empty+not_found+error | run | `validate/v1_collect.py:39` | 2026-08-17 05:33 | 없음 | chapters/20-verify/00-intro.md:14 · chapters/20-verify/b-v1v2.md:7 · chapters/20-verify/d-v5.md:213 |
| `V1-04` | 형식 검증 거부 0 | run | `validate/v1_collect.py:42` | 2026-08-17 05:33 | 없음 | chapters/60-admin/b-ops.md:207 · chapters/20-verify/b-v1v2.md:8 · chapters/20-verify/b-v1v2.md:87 |
| `V1-05` | raw_response 신규 == 응답 합 | run | `validate/v1_collect.py:45` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:47 · chapters/20-verify/b-v1v2.md:9 · trace/02-collect.md:57 |
| `V1-06` | 차종별 ok > 0 | target | `validate/v1_collect.py:48` | 2026-08-17 05:33 | 없음 | chapters/20-verify/b-v1v2.md:15 |
| `V1-07` | 매물별 엔드포인트 4종 상태 존재 | listing | `validate/v1_collect.py:51` | **★ 없음** | 2026-08-17 05:33 | chapters/20-verify/00-intro.md:117 · chapters/20-verify/b-v1v2.md:16 · chapters/10-collect/d-record.md:543 |
| `V1-08b` | 엔드포인트별 전량 404 없음 | run | `validate/v1_collect.py:57` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:122 · chapters/20-verify/b-v1v2.md:84 · chapters/10-collect/d-record.md:525 |
| `V1-08` | 동일 코드 실패율 100% 인 엔드포인트 없음 | run | `validate/v1_collect.py:54` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:48 · chapters/13-pipeline.md:500 · chapters/20-verify/00-intro.md:118 |
| `V1-09` | 시간대별 실패율 상승 없음 | run | `validate/v1_collect.py:141` | 2026-08-17 05:33 | 없음 | chapters/20-verify/b-v1v2.md:32 |
| `V1-10` | site_query 키가 전부 q 에 반영됨 | run | `validate/v1_collect.py:138` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:112 · chapters/20-verify/b-v1v2.md:33 · chapters/10-collect/a-endpoint.md:169 |
| `V1-11` | 예외로 종료된 실행이 없음 | run | `validate/v1_collect.py:61` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:117 · chapters/60-admin/b-ops.md:157 · chapters/20-verify/b-v1v2.md:34 |
| `V1-12` | 연속 실패 중단 시 ResumePoint 가 남음 | run | `validate/v1_collect.py:134` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:115 · chapters/20-verify/b-v1v2.md:35 |
| `V1-13` | 껍데기를 거친 실행과 직접 실행의 인자가 같음 | run | `validate/v1_collect.py:112` | 2026-08-17 05:33 | 없음 | guide/01_시작.md:113 · guide/03_이력.md:123 · guide/03_이력.md:211 |
| `V1-14` | diagnosis 호출 대상이 encarDiagnosis == 0 으로 좁혀짐 | run | `validate/v1_collect.py:64` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:170 · guide/03_이력.md:186 · chapters/13-pipeline.md:160 |
| `V1-15` | expected == 요청 대상 수 (skipped 제외) | run | `validate/v1_collect.py:129` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:193 · chapters/13-pipeline.md:160 · chapters/20-verify/b-v1v2.md:38 |
| `V1-16` | 이번 run_id 밖의 행을 보지 않음 | run | `validate/v1_collect.py:124` | **★ 없음** | 2026-08-17 05:33 | guide/03_이력.md:191 · guide/03_이력.md:193 · guide/03_이력.md:195 |
| `V1-17` | diagnosis 가 detail 뒤에 있음 | run | `validate/v1_collect.py:117` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:212 · chapters/20-verify/b-v1v2.md:40 · chapters/10-collect/a-endpoint.md:152 |
| `V1-18` | 빈 DB 에서도 검사가 돈다 | run | `validate/v1_collect.py:121` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:210 · chapters/13-pipeline.md:133 · chapters/20-verify/b-v1v2.md:41 |
| `V1-19` | 이번 실행이 저장한 원문에 run_id 가 있음 | run | `validate/v1_collect.py:107` | 2026-08-17 05:33 | 없음 | — |
| `V1-20` | 카탈로그를 모델당 1회만 받음 | run | `validate/v1_collect.py:102` | 2026-08-17 05:33 | 없음 | — |
| `V1-21` | 받아 두고 안 펼쳐진 원문이 없음 | run | `validate/v1_collect.py:92` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:275 · chapters/13-pipeline.md:205 · chapters/20-verify/b-v1v2.md:42 |
| `V1-22` | — | — | **★ 코드에 없다** | — | — | guide/01_요구사항.md:115 · guide/01_요구사항.md:124 · guide/03_이력.md:303 |
| `V1-23` | 필요한 조합 대비 받은 카탈로그 비율 | run | `validate/v1_collect.py:80` | 2026-08-17 05:33 | 없음 | guide/02_결함대장.md:224 · guide/02_결함대장.md:234 · guide/03_이력.md:334 |
| `V1-24` | 받은 카탈로그가 매물과 이어짐 | run | `validate/v1_collect.py:87` | **★ 없음** | 없음 | guide/02_결함대장.md:224 · guide/02_결함대장.md:234 · guide/03_이력.md:334 |
| `V1-25` | ok 로 저장된 원문이 온전한가 | run | `validate/v1_collect.py:71` | **★ 없음** | 없음 | — |
| `V2-01` | ok 원문 수 == CORE 행 수 | run | `validate/v2_load.py:26` | 2026-08-16 23:59 | 2026-08-17 05:33 | chapters/00-standard.md:354 · chapters/11-store/a-key.md:298 · chapters/20-verify/b-v1v2.md:97 |
| `V2-02` | 필수 컬럼 NOT NULL 위반 없음 | run | `validate/v2_load.py:29` | 2026-08-17 05:33 | 없음 | chapters/20-verify/b-v1v2.md:98 |
| `V2-03` | — | — | **★ 코드에 없다** | — | — | chapters/11-store/a-key.md:339 · chapters/20-verify/b-v1v2.md:99 |
| `V2-04` | status 열거값 위반 없음 | run | `validate/v2_load.py:32` | 2026-08-17 05:33 | 없음 | chapters/20-verify/b-v1v2.md:100 · trace/11-store.md:36 |
| `V2-05` | 단위 — 가격이 만원 단위로 남아 있지 않은가 | run | `validate/v2_load.py:35` | 2026-08-17 05:33 | 없음 | chapters/00-standard.md:653 · chapters/60-admin/b-ops.md:68 · chapters/20-verify/b-v1v2.md:101 |
| `V2-06` | 빈 컨테이너가 NULL 로 저장되지 않았는가 | run | `validate/v2_load.py:38` | 2026-08-17 05:33 | 없음 | chapters/20-verify/b-v1v2.md:102 · chapters/20-verify/b-v1v2.md:140 · chapters/20-verify/b-v1v2.md:143 |
| `V2-07` | 전건 NULL 컬럼 | run | `validate/v2_load.py:41` | 2026-08-17 05:33 | 없음 | chapters/20-verify/b-v1v2.md:103 · chapters/20-verify/b-v1v2.md:140 · chapters/20-verify/b-v1v2.md:144 |
| `V2-08` | 값 종류 1인 컬럼 | run | `validate/v2_load.py:121` | 2026-08-17 05:33 | 없음 | chapters/20-verify/b-v1v2.md:104 · chapters/20-verify/b-v1v2.md:140 · chapters/20-verify/b-v1v2.md:145 |
| `V2-09` | core_pii 를 직접 조회하는 코드 없음 | run | `validate/v2_load.py:44` | 2026-08-17 05:33 | 없음 | SCHEMA.md:37 · guide/03_이력.md:84 · chapters/11-store/b-core.md:480 |
| `V2-10` | core_listing 에 plate_no · dealer_name · phone · address 없음 | run | `validate/v2_load.py:47` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:84 · chapters/20-verify/b-v1v2.md:120 |
| `V2-10b` | core_* 에 마스킹 컬럼 없음 | run | `validate/v2_load.py:57` | 2026-08-17 05:33 | 없음 | chapters/20-verify/b-v1v2.md:121 |
| `V2-11` | plate_hash 가 전건 16자 hex | run | `validate/v2_load.py:118` | 2026-08-17 05:33 | 없음 | chapters/11-store/b-core.md:438 · chapters/20-verify/b-v1v2.md:122 |
| `V2-12` | secrets/plate_hmac.key 가 버전 관리 밖 | run | `validate/v2_load.py:53` | 2026-08-17 05:33 | 없음 | chapters/60-admin/00-intro.md:173 · chapters/20-verify/b-v1v2.md:123 |
| `V2-13` | core_record 에 record_plate_no 원본 없음 | run | `validate/v2_load.py:80` | 2026-08-17 05:33 | 없음 | chapters/11-store/b-core.md:635 · chapters/20-verify/b-v1v2.md:124 |
| `V2-14` | 참조되는 5종 PK 가 단일 INTEGER | run | `validate/v2_load.py:109` | 2026-08-17 05:33 | 없음 | chapters/11-store/a-key.md:151 · chapters/11-store/a-key.md:491 · chapters/60-admin/00-intro.md:139 |
| `V2-15` | 자연키가 UNIQUE 로 걸려 있음 | run | `validate/v2_load.py:112` | 2026-08-17 05:33 | 없음 | chapters/20-verify/b-v1v2.md:126 |
| `V2-16` | PK·FK 컬럼에 개인정보 없음 | run | `validate/v2_load.py:115` | 2026-08-17 05:33 | 없음 | chapters/60-admin/00-intro.md:139 · chapters/20-verify/b-v1v2.md:127 |
| `V2-17` | PII 고아 행 없음 | run | `validate/v2_load.py:60` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:98 · chapters/11-store/b-core.md:466 · chapters/20-verify/b-v1v2.md:128 |
| `V2-18` | parse_rule 재처리 후 전 봉투가 현재 parse_version | run | `validate/v2_load.py:105` | **★ 없음** | 2026-08-17 05:33 | guide/03_이력.md:124 · chapters/13-pipeline.md:336 · chapters/20-verify/b-v1v2.md:129 |
| `V2-19` | 원문 유래 컬럼에 NOT NULL 없음 | run | `validate/v2_load.py:102` | 2026-08-17 05:33 | 없음 | guide/01_요구사항.md:750 · guide/01_요구사항.md:759 · guide/03_이력.md:127 |
| `V2-20` | 파싱 실패 필드가 있는 행도 CORE 에 있음 | run | `validate/v2_load.py:64` | 2026-08-17 05:33 | 없음 | guide/01_요구사항.md:763 · guide/01_요구사항.md:772 · guide/03_이력.md:128 |
| `V2-21` | parse_error · type_mismatch 건수 | run | `validate/v2_load.py:68` | 2026-08-17 05:33 | 없음 | chapters/20-verify/b-v1v2.md:107 |
| `V2-22` | 현재 DB 스키마가 sql/ddl 과 일치 | run | `validate/v2_load.py:84` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:133 · chapters/20-verify/b-v1v2.md:71 · chapters/20-verify/b-v1v2.md:108 |
| `V2-23` | 중간 노드 None 인 매물도 CORE 에 있음 | run | `validate/v2_load.py:87` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:137 · chapters/20-verify/b-v1v2.md:109 · chapters/10-collect/d-record.md:89 |
| `V2-24` | 배열 기대 필드가 전건 list 로 정규화됨 | run | `validate/v2_load.py:91` | 2026-08-17 05:33 | 없음 | chapters/20-verify/b-v1v2.md:110 |
| `V2-25` | 스칼라 null 이 0 으로 저장된 컬럼 없음 | run | `validate/v2_load.py:95` | 2026-08-17 05:33 | 없음 | chapters/20-verify/b-v1v2.md:111 |
| `V2-27` | parse/ 에 원문 연쇄 첨자가 없음 | run | `validate/v2_load.py:98` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:140 · chapters/20-verify/00-intro.md:143 · chapters/20-verify/b-v1v2.md:112 |
| `V2-28` | 파싱 실패해도 남은 필드가 저장됨 | run | `validate/v2_load.py:72` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:228 · chapters/00-standard.md:699 · chapters/20-verify/b-v1v2.md:114 |
| `V2-29` | upsert 가 버린 키를 기록함 | run | `validate/v2_load.py:77` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:229 · chapters/20-verify/b-v1v2.md:115 · chapters/10-collect/b-parse.md:67 |
| `V2-30` | 전 파서가 row_status 를 냄 | run | `validate/v2_load.py:134` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:277 · chapters/20-verify/b-v1v2.md:116 · chapters/10-collect/b-parse.md:88 |
| `V2-31` | target_key NULL 이 판정에 들어가지 않음 | run | `validate/v2_load.py:124` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:278 · chapters/11-store/b-core.md:679 · chapters/20-verify/b-v1v2.md:117 |
| `V2-32` | NULL 매물의 모델명이 화면에서 보임 | run | `validate/v2_load.py:129` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:278 · chapters/11-store/b-core.md:680 · chapters/20-verify/b-v1v2.md:118 |
| `V3-01` | result_axis.source 전건 NOT NULL | axis | `validate/v3_logic.py:41` | 2026-08-17 05:33 | 없음 | chapters/20-verify/c-v3v4.md:37 · chapters/20-verify/c-v3v4.md:118 |
| `V3-02` | result_axis.prio 전건 NOT NULL | axis | `validate/v3_logic.py:44` | 2026-08-17 05:33 | 없음 | chapters/20-verify/c-v3v4.md:38 |
| `V3-03` | 축별 source 값 종류 >= 2 | axis | `validate/v3_logic.py:47` | **★ 없음** | 2026-08-17 05:33 | chapters/00-standard.md:657 · chapters/30-score/c-spec.md:57 · chapters/20-verify/c-v3v4.md:39 |
| `V3-04` | 축별 값 종류 >= 2 | axis | `validate/v3_logic.py:50` | **★ 없음** | 2026-08-17 05:33 | chapters/40-report.md:108 · chapters/40-report.md:324 · chapters/30-score/c-spec.md:9 |
| `V3-05` | 금지 근거가 source 에 없음 | axis | `validate/v3_logic.py:53` | 2026-08-17 05:33 | 없음 | chapters/20-verify/c-v3v4.md:41 |
| `V3-06` | put() 충돌 기록 검토 | run | `validate/v3_logic.py:68` | 2026-08-17 05:33 | 없음 | chapters/20-verify/c-v3v4.md:42 |
| `V3-07` | 축별 -1 비율 | axis | `validate/v3_logic.py:56` | 2026-08-17 05:33 | 없음 | chapters/20-verify/c-v3v4.md:43 |
| `V3-08` | 사전 pending 이 판정에 쓰이지 않음 | run | `validate/v3_logic.py:59` | 2026-08-17 05:33 | 없음 | chapters/20-verify/c-v3v4.md:44 |
| `V3-09` | 축별 excluded 비율 | axis | `validate/v3_logic.py:62` | 2026-08-17 05:33 | 없음 | chapters/20-verify/c-v3v4.md:45 |
| `V3-10` | 재판정 결과가 이전과 동일 | run | `validate/v3_logic.py:71` | 2026-08-17 05:33 | 없음 | chapters/20-verify/c-v3v4.md:130 |
| `V3-11` | put() 순서 셔플 후에도 동일 | run | `validate/v3_logic.py:65` | 2026-08-17 05:33 | 없음 | chapters/00-standard.md:656 · chapters/30-score/a-frame.md:181 · chapters/20-verify/c-v3v4.md:131 |
| `V3-20` | trust_score 가 555 에 합산되지 않음 | run | `validate/v3_logic.py:228` | 2026-08-17 05:33 | 없음 | chapters/20-verify/00-intro.md:142 · chapters/20-verify/c-v3v4.md:80 · chapters/20-verify/c-v3v4.md:118 |
| `V3-21` | 경고가 555 에 합산되지 않음 | run | `validate/v3_logic.py:231` | 2026-08-17 05:33 | 없음 | SCHEMA.md:85 · chapters/20-verify/c-v3v4.md:81 |
| `V3-22` | 경고로 매물이 목록에서 제외되지 않음 | run | `validate/v3_logic.py:234` | 2026-08-17 05:33 | 없음 | chapters/20-verify/c-v3v4.md:82 |
| `V3-23` | 경고로 등급·추천 순위가 바뀌지 않음 | run | `validate/v3_logic.py:74` | 2026-08-17 05:33 | 없음 | chapters/20-verify/c-v3v4.md:83 |
| `V3-24` | acknowledged 가 신호 감지를 멈추지 않음 | run | `validate/v3_logic.py:78` | 2026-08-17 05:33 | 없음 | chapters/20-verify/c-v3v4.md:84 |
| `V3-25` | 소멸한 경고가 삭제되지 않고 남음 | run | `validate/v3_logic.py:81` | 2026-08-17 05:33 | 없음 | chapters/20-verify/c-v3v4.md:85 |
| `V3-27` | 모든 경고에 evidence 존재 | run | `validate/v3_logic.py:237` | 2026-08-17 05:33 | 없음 | chapters/20-verify/c-v3v4.md:87 |
| `V3-28` | PeerGroup 이 확장 단계를 표시 | run | `validate/v3_logic.py:84` | 2026-08-17 05:33 | 없음 | chapters/20-verify/c-v3v4.md:88 |
| `V3-29` | 배점 변경 시 calc_version 이 증가 | run | `validate/v3_logic.py:88` | 2026-08-17 05:33 | 없음 | chapters/20-verify/c-v3v4.md:89 |
| `V3-30` | halt 축의 사전이 비어 있지 않음 | run | `validate/v3_logic.py:102` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:116 · chapters/00-standard.md:202 · chapters/12-dict.md:226 |
| `V3-31` | 딜러 NULL 매물에 dealer_untrusted 없음 | run | `validate/v3_logic.py:223` | 2026-08-17 05:33 | 없음 | guide/01_요구사항.md:789 · guide/01_요구사항.md:798 · guide/03_이력.md:139 |
| `V3-32` | seizing null 매물이 「저당 없음」으로 판정되지 않음 | run | `validate/v3_logic.py:129` | 2026-08-17 05:33 | 없음 | guide/01_요구사항.md:789 · guide/01_요구사항.md:798 · guide/03_이력.md:139 |
| `V3-33` | HDA 판정이 전건 description 근거 | run | `validate/v3_logic.py:121` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:159 · chapters/30-score/c-spec.md:144 · chapters/20-verify/c-v3v4.md:111 |
| `V3-34` | 판정 항목 수 == resultCode IS NOT NULL 인 items 수 | run | `validate/v3_logic.py:115` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:172 · chapters/11-store/b-core.md:224 · chapters/20-verify/c-v3v4.md:112 |
| `V3-35` | conflicts 가 있는 매물이 기록됨 | run | `validate/v3_logic.py:107` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:213 · chapters/30-score/a-frame.md:153 · chapters/11-store/c-result.md:211 |
| `V3-36` | conflicts 건수가 임계 미만 | run | `validate/v3_logic.py:112` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:213 · chapters/00-standard.md:700 · chapters/30-score/a-frame.md:154 |
| `V3-37` | 목록 관측분의 source 가 'list' 임 | run | `validate/v3_logic.py:135` | 2026-08-17 05:33 | 2026-08-16 07:39 | guide/03_이력.md:273 · guide/03_이력.md:276 · chapters/12-dict.md:151 |
| `V3-38` | facet 수신 후 목록 관측분과 대조함 | run | `validate/v3_logic.py:140` | 2026-08-16 23:59 | 2026-08-17 05:33 | guide/03_이력.md:273 · chapters/12-dict.md:152 · chapters/60-admin/c-tools.md:524 |
| `V3-39` | 이론가와 실제 중앙값의 차가 상한 안 | run | `validate/v3_logic.py:161` | **★ 없음** | 2026-08-17 05:33 | guide/01_요구사항.md:31 · guide/01_요구사항.md:41 · guide/03_이력.md:289 |
| `V3-40` | 핵심 축이 excluded 인데 등급을 매기지 않음 | run | `validate/v3_logic.py:151` | 2026-08-17 05:33 | 2026-08-16 23:01 | guide/02_결함대장.md:46 · guide/02_결함대장.md:56 · guide/03_이력.md:294 |
| `V3-41` | 전 매물의 분모가 만점과 같음 | run | `validate/v3_logic.py:145` | **★ 없음** | 2026-08-17 05:33 | guide/02_결함대장.md:60 · guide/02_결함대장.md:70 · guide/03_이력.md:296 |
| `V3-42` | — | — | **★ 코드에 없다** | — | — | guide/01_요구사항.md:73 · guide/01_요구사항.md:83 · guide/03_이력.md:297 |
| `V3-44` | — | — | **★ 코드에 없다** | — | — | guide/02_결함대장.md:74 · guide/02_결함대장.md:84 · guide/03_이력.md:298 |
| `V3-45` | 배점 합이 만점과 같음 | run | `validate/v3_logic.py:220` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:299 · chapters/20-verify/c-v3v4.md:97 |
| `V3-47` | 축별 차종 간 결측률 편차가 상한 안 | run | `validate/v3_logic.py:156` | 2026-08-17 05:33 | 2026-08-17 05:00 | guide/01_요구사항.md:87 · guide/01_요구사항.md:97 · guide/03_이력.md:300 |
| `V3-49` | — | — | **★ 코드에 없다** | — | — | ENCAR_API.md:167 · guide/01_요구사항.md:101 · guide/01_요구사항.md:111 |
| `V3-50` | — | — | **★ 코드에 없다** | — | — | guide/03_이력.md:302 · chapters/30-score/d-history.md:358 · chapters/20-verify/c-v3v4.md:102 |
| `V3-52` | 「싸다」에 이유가 붙어 있음 | run | `validate/v3_logic.py:206` | 2026-08-17 05:33 | 없음 | guide/01_요구사항.md:141 · guide/01_요구사항.md:150 · guide/03_이력.md:306 |
| `V3-53` | 점검 출처가 판정에 반영됨 | run | `validate/v3_logic.py:211` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:307 · chapters/30-score/a-frame.md:614 · trace/05-score.md:82 |
| `V3-54` | 렌트 이력을 세 곳에서 대조 | run | `validate/v3_logic.py:215` | 2026-08-17 05:33 | 2026-08-16 23:01 | guide/03_이력.md:309 · chapters/30-score/a-frame.md:658 · trace/05-score.md:58 |
| `V3-55` | 사이트 보증 축이 config 규칙을 읽는가 | run | `validate/v3_logic.py:179` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:313 · chapters/30-score/f-table.md:403 · trace/05-score.md:81 |
| `V3-56` | 배점 합이 605 | run | `validate/v3_logic.py:184` | 2026-08-17 05:33 | 없음 | chapters/00-standard.md:1322 · chapters/30-score/f-table.md:608 · trace/05-score.md:17 |
| `V3-57` | 등급이 555 기준 | run | `validate/v3_logic.py:187` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:313 · trace/05-score.md:18 |
| `V3-58` | — | — | **★ 코드에 없다** | — | — | guide/03_이력.md:325 · chapters/30-score/a-frame.md:718 · trace/05-score.md:35 |
| `V3-62` | 원문이 없는데 값을 만든 축이 없음 | run | `validate/v3_logic.py:166` | 2026-08-17 05:00 | 2026-08-17 05:33 | guide/02_결함대장.md:116 · guide/02_결함대장.md:126 · guide/03_이력.md:330 |
| `V3-64` | 등급 경계가 절대 기준 | run | `validate/v3_logic.py:171` | 2026-08-17 05:33 | 없음 | guide/01_요구사항.md:195 · guide/01_요구사항.md:205 · guide/03_이력.md:331 |
| `V3-65` | 확인율이 근거 있는 축만 셈 | run | `validate/v3_logic.py:175` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:332 · chapters/30-score/g-absolute.md:136 · trace/05-score.md:20 |
| `V3-66` | — | — | **★ 코드에 없다** | — | — | guide/02_결함대장.md:130 · guide/02_결함대장.md:140 · guide/03_이력.md:333 |
| `V3-67` | — | — | **★ 코드에 없다** | — | — | guide/01_요구사항.md:209 · guide/01_요구사항.md:219 · guide/03_이력.md:335 |
| `V3-68` | 부록 F 전 24축이 구현돼 있음 | run | `validate/v3_logic.py:200` | **★ 없음** | 없음 | guide/01_요구사항.md:223 · guide/01_요구사항.md:233 · guide/03_이력.md:336 |
| `V3-69` | — | — | **★ 코드에 없다** | — | — | guide/03_이력.md:338 · chapters/30-score/a-frame.md:751 |
| `V3-70` | 일반·동력계 보증을 따로 냄 | run | `validate/v3_logic.py:190` | **★ 없음** | 없음 | guide/03_이력.md:372 · chapters/30-score/f-table.md:490 · chapters/20-verify/c-v3v4.md:105 |
| `V3-71` | 보증 잔여가 기간·거리 중 낮은 쪽임 | run | `validate/v3_logic.py:195` | **★ 없음** | 없음 | guide/03_이력.md:372 · chapters/30-score/f-table.md:491 · chapters/20-verify/c-v3v4.md:106 |
| `V4-01` | 매핑 일치율 (A 100% · B 99% · C 80%) | run | `validate/v4_mapping.py:28` | 2026-08-17 05:33 | 없음 | chapters/00-standard.md:654 · chapters/60-admin/c-tools.md:144 · chapters/20-verify/c-v3v4.md:169 |
| `V4-02` | 미매핑 경로 목록 | run | `validate/v4_mapping.py:86` | 2026-08-17 05:33 | 없음 | chapters/20-verify/c-v3v4.md:170 |
| `V4-03` | 오매핑 탐지 — 다른 경로와 더 높은 일치율 | run | `validate/v4_mapping.py:31` | 2026-08-17 05:33 | 없음 | chapters/20-verify/c-v3v4.md:171 · chapters/20-verify/c-v3v4.md:287 |
| `V4-04` | 매핑표에 없는 CORE 컬럼 | run | `validate/v4_mapping.py:89` | 2026-08-17 05:33 | 없음 | chapters/20-verify/c-v3v4.md:172 |
| `V4-05` | 원문 경로 수 변동 | run | `validate/v4_mapping.py:91` | 2026-08-17 05:33 | 없음 | chapters/31-registry.md:295 · chapters/20-verify/c-v3v4.md:173 · chapters/20-verify/c-v3v4.md:300 |
| `V4-06` | RAW 경로가 등록부에 있는가 | run | `validate/v4_mapping.py:34` | 2026-08-17 05:33 | 2026-08-16 23:59 | chapters/31-registry.md:58 · chapters/31-registry.md:203 · chapters/31-registry.md:211 |
| `V4-06b` | 등록부에 있는데 RAW 에 없는 유령 경로 | run | `validate/v4_mapping.py:37` | **★ 없음** | 2026-08-17 05:33 | chapters/31-registry.md:227 · chapters/31-registry.md:244 · chapters/40-report.md:142 |
| `V4-07` | in_use 인데 core_column NULL | run | `validate/v4_mapping.py:40` | 2026-08-17 05:33 | 없음 | chapters/31-registry.md:286 · chapters/60-admin/b-ops.md:121 · chapters/20-verify/c-v3v4.md:176 |
| `V4-08` | blocked 인데 unblock_condition NULL | run | `validate/v4_mapping.py:43` | 2026-08-17 05:33 | 없음 | chapters/31-registry.md:287 · chapters/20-verify/c-v3v4.md:177 · trace/12-dict.md:42 |
| `V4-09` | deferred 인데 use_when NULL | run | `validate/v4_mapping.py:46` | 2026-08-17 05:33 | 없음 | chapters/31-registry.md:288 · chapters/20-verify/c-v3v4.md:178 |
| `V4-10` | display_only 인데 core_column NULL | run | `validate/v4_mapping.py:49` | 2026-08-17 05:33 | 없음 | chapters/31-registry.md:289 · chapters/20-verify/c-v3v4.md:179 |
| `V4-11b` | 판정에 안 쓰는 미분류 경로 | run | `validate/v4_mapping.py:55` | **★ 없음** | 2026-08-17 05:33 | guide/01_요구사항.md:18 · guide/01_요구사항.md:27 · guide/03_이력.md:129 |
| `V4-11` | unclassified 존재 | run | `validate/v4_mapping.py:52` | **★ 없음** | 2026-08-17 05:33 | guide/01_시작.md:214 · guide/01_시작.md:224 · guide/01_요구사항.md:18 |
| `V4-12` | facet 필수 축 집합 존재 | run | `validate/v4_mapping.py:70` | 2026-08-17 05:33 | 없음 | chapters/20-verify/c-v3v4.md:182 |
| `V4-13` | 매직 넘버 없음 (tools/check_src.py S7) | run | `validate/v4_mapping.py:73` | 2026-08-17 05:33 | 없음 | ref/A-check.md:6 · ref/E-attach.md:59 · ref/E-attach.md:107 |
| `V4-19` | 성격(kind)이 없는 Check 가 없음 | run | `validate/v4_mapping.py:94` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:132 · chapters/20-verify/00-intro.md:112 · chapters/20-verify/c-v3v4.md:189 |
| `V4-20` | dict_option_code 에 문장(공백·한글)이 없음 | run | `validate/v4_mapping.py:109` | 2026-08-17 05:33 | 2026-08-16 08:34 | guide/03_이력.md:138 · chapters/20-verify/c-v3v4.md:190 · chapters/10-collect/e-catalog.md:174 |
| `V4-21` | 같은 이름의 공개 함수가 두 모듈에 없음 | run | `validate/v4_mapping.py:105` | 2026-08-16 23:59 | 2026-08-17 05:33 | guide/03_이력.md:144 · chapters/30-score/h-verdict.md:67 · chapters/20-verify/c-v3v4.md:191 |
| `V4-22` | 역방향 · 순환 import 없음 | run | `validate/v4_mapping.py:97` | 2026-08-17 05:33 | 없음 | MAPPING.md:54 · MAPPING.md:88 · guide/03_이력.md:150 |
| `V4-23` | 모듈 최상위에 I/O · 부작용 없음 | run | `validate/v4_mapping.py:100` | 2026-08-17 05:33 | 2026-08-17 03:30 | MAPPING.md:89 · guide/03_이력.md:150 · chapters/41-view.md:574 |
| `V4-24` | 축 함수가 target_config 에서 매물 값을 읽지 않음 | run | `validate/v4_mapping.py:75` | 2026-08-17 05:00 | 2026-08-17 05:33 | guide/03_이력.md:214 · chapters/01-arch.md:215 · chapters/20-verify/c-v3v4.md:194 |
| `V4-25` | 판정에 쓰는 축의 사전이 비어 있지 않음 | run | `validate/v4_mapping.py:81` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:230 · guide/03_이력.md:267 · chapters/00-standard.md:202 |
| `V4-26` | 미분류가 원인별로 갈려 있음 | run | `validate/v4_mapping.py:58` | **★ 없음** | 없음 | guide/01_요구사항.md:640 · guide/01_요구사항.md:650 · guide/03_이력.md:348 |
| `V4-27` | 판정을 막는 것만 막음 | run | `validate/v4_mapping.py:64` | **★ 없음** | 없음 | guide/01_요구사항.md:640 · guide/01_요구사항.md:650 · guide/03_이력.md:348 |
| `V4-28` | — | — | **★ 코드에 없다** | — | — | guide/03_이력.md:374 · chapters/31-registry.md:652 |
| `V4-29` | — | — | **★ 코드에 없다** | — | — | guide/03_이력.md:374 · chapters/31-registry.md:664 |
| `V5-01` | 배점 합계 == config 총점 | run | `validate/v5_value.py:16` | 2026-08-17 05:33 | 없음 | chapters/20-verify/d-v5.md:7 |
| `V5-02` | 표시용 등급 점수가 비율과 일치 | run | `validate/v5_value.py:19` | 2026-08-17 05:33 | 2026-08-16 23:01 | chapters/20-verify/d-v5.md:8 |
| `V5-03` | 분모 시험 A·D·E·G·H·I 통과 | run | `validate/v5_value.py:22` | 2026-08-17 05:33 | 2026-08-16 22:44 | chapters/20-verify/d-v5.md:9 · chapters/20-verify/d-v5.md:20 |
| `V5-04` | 점수 범위 위반 없음 | run | `validate/v5_value.py:25` | 2026-08-17 05:33 | 없음 | chapters/20-verify/d-v5.md:10 |
| `V5-05` | 등급 분포가 극단적이지 않음 | run | `validate/v5_value.py:28` | 2026-08-17 05:33 | 없음 | chapters/00-standard.md:655 · chapters/30-score/h-verdict.md:9 · chapters/60-admin/c-tools.md:146 |
| `V5-06` | 기준값 대비 실측 이탈 | run | `validate/v5_value.py:31` | 2026-08-17 05:33 | 없음 | chapters/30-score/b-price.md:82 · chapters/20-verify/d-v5.md:12 · chapters/20-verify/d-v5.md:45 |
| `V5-07` | 계수 보정 타당성 | run | `validate/v5_value.py:34` | 2026-08-17 05:33 | 없음 | chapters/20-verify/d-v5.md:13 |
| `V5-08` | 계수 산출 입력에 result_* 없음 | run | `validate/v5_value.py:51` | 2026-08-17 05:33 | 없음 | chapters/20-verify/d-v5.md:14 · chapters/20-verify/d-v5.md:115 |
| `V5-09` | 등급이 earned / denominator 로 산출됨 | run | `validate/v5_value.py:41` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:135 · chapters/20-verify/d-v5.md:15 |
| `V5-10` | 같은 비율 · 다른 분모가 같은 등급 | run | `validate/v5_value.py:46` | 2026-08-17 05:33 | 없음 | chapters/20-verify/d-v5.md:16 |
| `V5-11` | 분모 최대값으로도 S 가 불가능한 매물 없음 | run | `validate/v5_value.py:48` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:135 · chapters/20-verify/d-v5.md:17 |
| `V5-12` | NOT_RATED 인데 not_rated_reason 이 NULL 인 행 없음 | run | `validate/v5_value.py:37` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:227 · chapters/11-store/c-result.md:115 · chapters/20-verify/d-v5.md:18 |
| `V6-01` | — | — | **★ 코드에 없다** | — | — | chapters/41-view.md:675 · chapters/61-web.md:328 |
| `V6-07` | ORDER BY 에 4단이 전부 있음 | run | `validate/v3_logic.py:125` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:152 · guide/03_이력.md:206 · chapters/41-view.md:563 |
| `V7-01` | watch_track 에 버전 4종 전건 있음 | run | `validate/v7_watch.py:30` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:147 · chapters/42-watch.md:610 |
| `V7-02` | cause != 'listing' 인 이벤트가 알림되지 않음 | run | `validate/v7_watch.py:34` | 2026-08-17 05:33 | 없음 | chapters/42-watch.md:616 |
| `V7-04` | 같은 이벤트 중복 발송 0건 | run | `validate/v7_watch.py:38` | 2026-08-17 05:33 | 없음 | chapters/42-watch.md:618 · chapters/50-multisite.md:118 · trace/50-multisite.md:22 |
| `V7-05` | gone 매물이 목록에서 삭제되지 않음 | run | `validate/v7_watch.py:40` | 2026-08-17 05:33 | 없음 | chapters/42-watch.md:619 |
| `V7-06` | 검증 실패 실행에서 알림이 나가지 않음 | run | `validate/v7_watch.py:43` | 2026-08-17 05:33 | 없음 | chapters/42-watch.md:620 · chapters/50-multisite.md:110 · trace/50-multisite.md:17 |
| `V7-07` | relist 결합에 identity_kind 기록 | run | `validate/v7_watch.py:47` | 2026-08-17 05:33 | 없음 | chapters/42-watch.md:621 |
| `V7-08` | 구매 체크리스트가 점수·등급에 반영되지 않음 | run | `validate/v7_watch.py:62` | 2026-08-17 05:33 | 없음 | chapters/42-watch.md:622 |
| `V7-09` | 실구매가·총소유비용이 점수에 반영되지 않음 | run | `validate/v7_watch.py:73` | 2026-08-17 05:33 | 없음 | chapters/42-watch.md:623 |
| `V7-10` | 발송 시도 대비 성공률 | run | `validate/v7_watch.py:50` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:153 · chapters/42-watch.md:624 · chapters/50-multisite.md:59 |
| `V7-11` | closed_reason 이 CHECK 안의 값 | run | `validate/v7_watch.py:58` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:175 · guide/03_이력.md:217 · chapters/42-watch.md:185 |
| `V7-12` | 남의 관심 항목을 고치지 못함 | run | `validate/v7_watch.py:54` | 2026-08-17 05:33 | 없음 | guide/01_요구사항.md:393 · guide/01_요구사항.md:403 · guide/03_이력.md:199 |
| `V7-14` | — | — | **★ 코드에 없다** | — | — | guide/03_이력.md:362 · chapters/42-watch.md:427 |
| `V7-15` | 진행 메모를 자유롭게 적을 수 있음 | run | `validate/v7_watch.py:66` | **★ 없음** | 없음 | guide/03_이력.md:369 · chapters/42-watch.md:596 · trace/42-watch.md:83 |
| `V8-01` | 같은 파일명이 두 번 생성되지 않음 | run | `validate/v3_logic.py:92` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:151 · chapters/40-report.md:542 · chapters/41-view.md:695 |
| `V8-02` | 출력 파일에 BOM · CRLF 가 없음 | run | `validate/v3_logic.py:97` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:151 · chapters/40-report.md:571 · chapters/41-view.md:696 |
| `V9-01` | — | — | **★ 코드에 없다** | — | — | guide/03_이력.md:316 · chapters/50-multisite.md:214 · chapters/50-multisite.md:298 |
| `V9-03` | — | — | **★ 코드에 없다** | — | — | guide/03_이력.md:316 · chapters/50-multisite.md:216 · chapters/50-multisite.md:320 |
| `V9-04` | — | — | **★ 코드에 없다** | — | — | guide/03_이력.md:317 · chapters/50-multisite.md:217 · chapters/50-multisite.md:347 |
| `V9-05` | — | — | **★ 코드에 없다** | — | — | guide/03_이력.md:317 · chapters/50-multisite.md:361 · trace/02-collect.md:71 |
| `V9-06` | 매물마다 사이트 배지가 있음 | run | `validate/v9_multisite.py:33` | **★ 없음** | 없음 | guide/01_요구사항.md:449 · guide/01_요구사항.md:459 · guide/03_이력.md:318 |
| `V9-07` | 합친 값에 출처가 붙어 있음 | run | `validate/v9_multisite.py:45` | **★ 없음** | 없음 | guide/01_요구사항.md:449 · guide/01_요구사항.md:459 · guide/03_이력.md:318 |
| `V9-08` | — | — | **★ 코드에 없다** | — | — | guide/01_요구사항.md:168 · guide/01_요구사항.md:178 · guide/03_이력.md:319 |
| `V9-10` | 사이트 보증 항목의 합이 만점과 같음 | run | `validate/v9_multisite.py:39` | **★ 없음** | 없음 | guide/03_이력.md:358 · chapters/30-score/f-table.md:404 · chapters/20-verify/c-v3v4.md:107 |
| `V10-01` | admin 전용을 user 로 호출 시 PolicyError | run | `validate/v10_admin.py:28` | 2026-08-17 05:33 | 없음 | chapters/60-admin/c-tools.md:767 · trace/13-pipeline.md:15 |
| `V10-02` | 서버 권한 검증 존재 (화면 숨김 아님) | run | `validate/v10_admin.py:31` | 2026-08-17 05:33 | 없음 | chapters/60-admin/c-tools.md:768 |
| `V10-03` | run_query 가 SELECT 외를 전건 거부 | run | `validate/v10_admin.py:34` | 2026-08-17 05:33 | 없음 | chapters/60-admin/c-tools.md:769 |
| `V10-04` | run_query 판정이 AST 기반 (정규식 아님) | run | `validate/v10_admin.py:37` | 2026-08-17 05:33 | 없음 | chapters/60-admin/c-tools.md:770 |
| `V10-05` | config 변경이 ConfigChange 없이 안 일어남 | run | `validate/v10_admin.py:40` | 2026-08-17 05:33 | 없음 | chapters/60-admin/c-tools.md:771 · chapters/20-verify/c-v3v4.md:201 · chapters/20-verify/c-v3v4.md:206 |
| `V10-06` | 배점 저장 시 Σ == total_points | run | `validate/v10_admin.py:43` | 2026-08-17 05:33 | 없음 | chapters/60-admin/c-tools.md:772 |
| `V10-07` | 성분 추가가 선택 가능 목록 안에서만 | run | `validate/v10_admin.py:46` | 2026-08-17 05:33 | 없음 | chapters/60-admin/c-tools.md:773 |
| `V10-08` | 관리 도구가 core_* 를 UPDATE 하지 않음 | run | `validate/v10_admin.py:49` | 2026-08-17 05:33 | 없음 | chapters/60-admin/c-tools.md:774 |
| `V10-09` | DevRequest 가 삭제되지 않음 | run | `validate/v10_admin.py:52` | 2026-08-17 05:33 | 없음 | chapters/60-admin/c-tools.md:775 |
| `V10-10` | 문서 뷰어에 편집 경로 없음 | run | `validate/v10_admin.py:55` | 2026-08-17 05:33 | 없음 | chapters/60-admin/c-tools.md:776 |
| `V10-11` | 실행 중 config 변경이 잠김 | run | `validate/v10_admin.py:58` | 2026-08-17 05:33 | 없음 | chapters/60-admin/c-tools.md:777 |
| `V10-12` | 배점 조정 후 0점 성분 없음 | run | `validate/v10_admin.py:61` | 2026-08-17 05:33 | 없음 | chapters/60-admin/c-tools.md:778 |
| `V10-13` | 웹에서 전면 재수집이 큐에 안 들어감 | run | `validate/v10_admin.py:64` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:97 · chapters/60-admin/b-ops.md:217 · chapters/60-admin/c-tools.md:779 |
| `V10-14` | components.{axis}.{component} 경로 읽기·쓰기 | run | `validate/v10_admin.py:67` | 2026-08-17 05:33 | 2026-08-16 23:01 | guide/03_이력.md:103 · chapters/60-admin/a-auth.md:206 · chapters/60-admin/c-tools.md:780 |
| `V10-15` | 저장 전 배점 합 검사 | run | `validate/v10_admin.py:70` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:103 · chapters/60-admin/c-tools.md:781 |
| `V10-16` | must_change_secret 계정이 다른 화면에 접근 못 함 | run | `validate/v10_admin.py:73` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:203 · chapters/60-admin/a-auth.md:59 · chapters/60-admin/c-tools.md:782 |
| `V10-17` | admin 수가 0 이 되는 변경이 거부됨 | run | `validate/v10_admin.py:78` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:166 · guide/03_이력.md:203 · chapters/61-web.md:1947 |
| `V10-18` | core_pii · core_dealer_pii 조회가 거부됨 | run | `validate/v10_admin.py:83` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:200 · chapters/60-admin/c-tools.md:73 · chapters/60-admin/c-tools.md:784 |
| `V10-19` | 중지·비밀번호 변경 후 옛 세션이 anonymous | run | `validate/v10_admin.py:88` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:204 · chapters/60-admin/a-auth.md:79 · chapters/60-admin/c-tools.md:785 |
| `V10-20` | 로그인 실패 상한이 config 대로 돎 | run | `validate/v10_admin.py:136` | 2026-08-17 05:33 | 없음 | ref/B-config.md:386 · guide/03_이력.md:205 · chapters/00-standard.md:696 |
| `V10-22` | queued 를 소비하는 코드가 있음 | run | `validate/v10_admin.py:94` | 2026-08-17 05:33 | 2026-08-17 03:30 | guide/03_이력.md:268 · chapters/60-admin/b-ops.md:295 · chapters/60-admin/c-tools.md:787 |
| `V10-23` | 오래된 queued 가 화면에 표시됨 | run | `validate/v10_admin.py:99` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:268 · chapters/60-admin/b-ops.md:296 · chapters/60-admin/c-tools.md:788 |
| `V10-24` | 사전 확정에 사유가 남음 | run | `validate/v10_admin.py:104` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:274 · chapters/60-admin/c-tools.md:530 · chapters/60-admin/c-tools.md:789 |
| `V10-25` | 'list' 출처가 화면에 표시됨 | run | `validate/v10_admin.py:132` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:274 · chapters/60-admin/c-tools.md:531 · chapters/60-admin/c-tools.md:790 |
| `V10-26` | 목록 저장 후 큐에 작업이 들어감 | run | `validate/v10_admin.py:108` | **★ 없음** | 없음 | guide/01_요구사항.md:613 · guide/01_요구사항.md:623 · guide/03_이력.md:321 |
| `V10-27` | 중간 실패에서 다음 단계로 안 넘어감 | run | `validate/v10_admin.py:113` | **★ 없음** | 없음 | guide/01_요구사항.md:613 · guide/01_요구사항.md:623 · guide/03_이력.md:321 |
| `V10-28` | 타이머가 겹쳐 돌지 않음 | run | `validate/v10_admin.py:117` | **★ 없음** | 없음 | guide/01_요구사항.md:627 · guide/01_요구사항.md:636 · guide/03_이력.md:322 |
| `V10-29` | 목록 저장이 전건 재수집을 안 부름 | run | `validate/v10_admin.py:122` | **★ 없음** | 없음 | guide/01_요구사항.md:182 · guide/01_요구사항.md:191 · guide/03_이력.md:324 |
| `V10-30` | 재판정이 수집 없이 돎 | run | `validate/v10_admin.py:127` | **★ 없음** | 없음 | guide/01_요구사항.md:182 · guide/01_요구사항.md:191 · guide/03_이력.md:324 |
| `V11-01` | web/ 에 SQL 문자열이 없음 | run | `validate/v11_web.py:36` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:149 · chapters/61-web.md:28 · chapters/61-web.md:1516 |
| `V11-02` | 기본 바인딩이 127.0.0.1 | run | `validate/v11_web.py:39` | 2026-08-17 05:33 | 없음 | chapters/61-web.md:99 · chapters/61-web.md:2014 · chapters/61-web.md:2083 |
| `V11-03` | 전 Route 에 role 이 지정됨 | run | `validate/v11_web.py:43` | 2026-08-17 05:33 | 없음 | chapters/61-web.md:167 · chapters/61-web.md:2084 |
| `V11-04` | 템플릿에 산술 연산이 없음 | run | `validate/v11_web.py:45` | 2026-08-17 05:33 | 없음 | chapters/61-web.md:246 · chapters/61-web.md:2059 · chapters/61-web.md:2085 |
| `V11-05` | {{! }} 사용처가 화이트리스트에 있음 | run | `validate/v11_web.py:48` | 2026-08-17 05:33 | 없음 | chapters/61-web.md:263 · chapters/61-web.md:2086 |
| `V11-06` | 정적 경로 탈출이 거부됨 | run | `validate/v11_web.py:53` | 2026-08-17 05:33 | 없음 | chapters/61-web.md:368 · chapters/61-web.md:2087 · trace/41-view.md:34 |
| `V11-07` | 쿠키에 role 문자열이 없음 | run | `validate/v11_web.py:55` | 2026-08-17 05:33 | 없음 | chapters/61-web.md:1315 · chapters/61-web.md:2088 |
| `V11-08` | 상태 변경이 GET 경로에 없음 | run | `validate/v11_web.py:57` | 2026-08-17 05:33 | 없음 | chapters/61-web.md:1351 · chapters/61-web.md:2089 |
| `V11-09` | 미리보기 없이 저장이 안 됨 | run | `validate/v11_web.py:60` | 2026-08-17 05:33 | 없음 | chapters/61-web.md:1379 · chapters/61-web.md:1867 · chapters/61-web.md:2090 |
| `V11-10` | 오류 화면에 스택 트레이스가 없음 | run | `validate/v11_web.py:62` | 2026-08-17 05:33 | 없음 | chapters/61-web.md:1413 · chapters/61-web.md:2091 |
| `V11-11` | result_* 가 비었을 때 안내가 나옴 | run | `validate/v11_web.py:66` | 2026-08-17 05:33 | 없음 | chapters/61-web.md:1442 · chapters/61-web.md:2092 |
| `V11-12` | 라우팅 표의 view 가 10·13장에 실재함 | run | `validate/v11_web.py:163` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:179 · guide/03_이력.md:260 · guide/03_이력.md:265 |
| `V11-13` | app.css 에 토큰 밖의 색값이 없음 | run | `validate/v11_web.py:89` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:202 · guide/03_이력.md:218 · chapters/61-web.md:411 |
| `V11-14` | 숫자 셀에 mono 가 걸려 있음 | run | `validate/v11_web.py:92` | 2026-08-17 05:33 | 없음 | chapters/61-web.md:443 · chapters/61-web.md:2095 |
| `V11-15` | 화면이 빌드 산출물에 의존하지 않음 | run | `validate/v11_web.py:95` | 2026-08-17 05:33 | 없음 | chapters/61-web.md:1258 · chapters/61-web.md:2096 |
| `V11-16` | /why 가 전 Component 를 냄 | run | `validate/v11_web.py:98` | 2026-08-17 05:33 | 없음 | chapters/61-web.md:1464 · chapters/61-web.md:1539 · chapters/61-web.md:2097 |
| `V11-17` | /why 가 조회 상태 절을 냄 | run | `validate/v11_web.py:101` | 2026-08-17 05:33 | 없음 | chapters/61-web.md:1539 · chapters/61-web.md:1593 · chapters/61-web.md:2098 |
| `V11-18` | 축 태그가 전건 필터 링크임 | run | `validate/v11_web.py:104` | 2026-08-17 05:33 | 없음 | chapters/61-web.md:1637 · chapters/61-web.md:2099 |
| `V11-19` | 폴링 실패 시 화면이 안 깨짐 | run | `validate/v11_web.py:107` | 2026-08-17 05:33 | 없음 | chapters/61-web.md:1657 · chapters/61-web.md:2100 |
| `V11-20` | 분모 표시가 있음 | run | `validate/v11_web.py:110` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:225 · chapters/61-web.md:1683 · chapters/61-web.md:2101 |
| `V11-21` | 행동 요청 파라미터가 현재 필터와 일치 | run | `validate/v11_web.py:113` | 2026-08-17 05:33 | 없음 | chapters/61-web.md:1737 · chapters/61-web.md:2102 |
| `V11-22` | excluded 축이 「—/N」 으로 표시됨 | run | `validate/v11_web.py:116` | 2026-08-17 05:33 | 없음 | chapters/61-web.md:1779 · chapters/61-web.md:2103 |
| `V11-23` | 비로그인 관심 POST 가 유도 화면을 냄 | run | `validate/v11_web.py:119` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:226 · chapters/61-web.md:1810 · chapters/61-web.md:2104 |
| `V11-24` | 메뉴 분류가 잠금 단위와 일치 | run | `validate/v11_web.py:122` | 2026-08-17 05:33 | 없음 | chapters/61-web.md:1841 · chapters/61-web.md:2105 |
| `V11-25` | 사유 없이 설정이 저장되지 않음 | run | `validate/v11_web.py:125` | 2026-08-17 05:33 | 없음 | chapters/61-web.md:1867 · chapters/61-web.md:2106 |
| `V11-26` | 되돌릴 수 없는 행동에 확인이 있음 | run | `validate/v11_web.py:128` | 2026-08-17 05:33 | 없음 | chapters/61-web.md:1911 · chapters/61-web.md:2107 |
| `V11-27` | 가입 정책에 따라 화면이 바뀜 | run | `validate/v11_web.py:131` | 2026-08-17 05:33 | 없음 | chapters/61-web.md:1968 · chapters/61-web.md:2108 |
| `V11-28` | 응답 헤더에 비 ASCII 없음 | run | `validate/v11_web.py:69` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:176 · chapters/61-web.md:1392 · chapters/61-web.md:2109 |
| `V11-29` | 렌더된 폼의 csrf_token 이 비어 있지 않음 | run | `validate/v11_web.py:73` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:177 · chapters/61-web.md:353 · chapters/61-web.md:2110 |
| `V11-30` | 시안 ↔ 템플릿 대조 통과 | run | `validate/v11_web.py:77` | 2026-08-17 05:33 | 2026-08-16 23:59 | guide/03_이력.md:178 · chapters/61-web.md:308 · chapters/61-web.md:1492 |
| `V11-31` | must_change_secret=1 에서 /password 가 200 | run | `validate/v11_web.py:80` | 2026-08-17 05:33 | 없음 | chapters/61-web.md:1336 · chapters/61-web.md:2112 |
| `V11-32` | known_issues 의 키가 전부 targets 에 있음 | run | `validate/v11_web.py:85` | 2026-08-17 05:33 | 없음 | ref/B-config.md:369 · guide/03_이력.md:184 · chapters/61-web.md:2113 |
| `V11-33` | POST 가 저장 없이 성공 메시지를 내지 않음 | run | `validate/v11_web.py:134` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:208 · chapters/61-web.md:1992 · chapters/61-web.md:2114 |
| `V11-34` | 화면이 요청당 쿼리 상한을 넘지 않음 | run | `validate/v11_web.py:140` | 2026-08-17 05:33 | 2026-08-16 23:59 | guide/03_이력.md:207 · chapters/00-standard.md:160 · chapters/00-standard.md:694 |
| `V11-35` | 중첩 if 가 안쪽부터 닫힘 | run | `validate/v11_web.py:137` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:221 · chapters/61-web.md:1291 · chapters/61-web.md:2116 |
| `V11-36` | 잘못된 쿼리 파라미터가 500 을 내지 않음 | run | `validate/v11_web.py:144` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:223 · chapters/61-web.md:1300 · chapters/61-web.md:2117 |
| `V11-37` | POST 가 예상 밖 500 을 내지 않음 | run | `validate/v11_web.py:148` | 2026-08-17 05:33 | 없음 | — |
| `V11-38` | 템플릿이 쓰는 값을 뷰가 넘김 | run | `validate/v11_web.py:153` | 2026-08-17 05:33 | 없음 | — |
| `V11-39` | 저장 단추가 실제로 저장함 | run | `validate/v11_web.py:158` | 2026-08-17 05:33 | 없음 | — |
| `V11-40` | 반입분의 origin 이 'import' 임 | run | `validate/v11_web.py:166` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:251 · guide/03_이력.md:259 · chapters/61-web.md:2118 |
| `V11-41` | 반입 뒤 S5~S10 이 이어서 돎 | run | `validate/v11_web.py:171` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:251 · chapters/61-web.md:2119 · chapters/60-admin/c-tools.md:205 |
| `V11-42` | S4 완료 행의 actual 이 'import' 임 | run | `validate/v11_web.py:453` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:252 · chapters/61-web.md:2120 · chapters/60-admin/c-tools.md:287 |
| `V11-43` | 브라우저 수집분의 origin 이 'browser' 임 | run | `validate/v11_web.py:176` | 2026-08-17 05:33 | 없음 | guide/01_요구사항.md:547 · guide/01_요구사항.md:556 · guide/03_이력.md:256 |
| `V11-44` | 사람 확인 없이 저장되지 않음 | run | `validate/v11_web.py:181` | 2026-08-17 05:33 | 없음 | guide/01_요구사항.md:547 · guide/01_요구사항.md:556 · guide/03_이력.md:256 |
| `V11-45` | — | — | **★ 코드에 없다** | — | — | guide/01_요구사항.md:560 · guide/01_요구사항.md:569 · guide/03_이력.md:257 |
| `V11-46` | 반입으로 연 단계의 actual 이 'import' 임 | run | `validate/v11_web.py:448` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:266 · chapters/13-pipeline.md:184 · chapters/61-web.md:2124 |
| `V11-47` | 브라우저 수집이 한 번에 max_form_bytes 를 넘기지 않음 | run | `validate/v11_web.py:434` | 2026-08-17 05:33 | 2026-08-17 03:30 | ref/B-config.md:391 · guide/03_이력.md:270 · chapters/61-web.md:2125 |
| `V11-48` | 전 차종 수집에 확인 절차가 있음 | run | `validate/v11_web.py:440` | 2026-08-17 05:33 | 없음 | guide/01_요구사항.md:573 · guide/01_요구사항.md:582 · guide/03_이력.md:271 |
| `V11-49` | 한 차종 실패가 나머지를 멈추지 않음 | run | `validate/v11_web.py:444` | 2026-08-17 05:33 | 없음 | guide/01_요구사항.md:573 · guide/01_요구사항.md:582 · guide/03_이력.md:271 |
| `V11-51` | 진행 화면이 스스로 갱신됨 | run | `validate/v11_web.py:426` | 2026-08-17 05:33 | 없음 | guide/01_요구사항.md:310 · guide/01_요구사항.md:320 · guide/03_이력.md:279 |
| `V11-52` | 진행 화면에 실행 단추가 없음 | run | `validate/v11_web.py:430` | 2026-08-17 05:33 | 없음 | guide/01_요구사항.md:310 · guide/01_요구사항.md:320 · guide/03_이력.md:279 |
| `V11-53` | 진행 판정이 큐만 보지 않음 | run | `validate/v11_web.py:186` | 2026-08-17 05:33 | 없음 | guide/01_요구사항.md:599 · guide/01_요구사항.md:609 · guide/03_이력.md:280 |
| `V11-54` | 메뉴에 경로가 그대로 나오지 않음 | run | `validate/v11_web.py:192` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:281 · chapters/61-web.md:2131 · trace/14-web.md:128 |
| `V11-55` | 목록에 전체 건수와 쪽이 표시됨 | run | `validate/v11_web.py:197` | 2026-08-17 05:33 | 없음 | chapters/61-web.md:2132 · trace/14-web.md:56 · trace/41-view.md:84 |
| `V11-56` | 대표 사진 경로가 저장됨 | run | `validate/v11_web.py:202` | 2026-08-17 05:33 | 없음 | chapters/61-web.md:504 · chapters/61-web.md:2133 |
| `V11-57` | 사진 없는 매물이 화면을 무너뜨리지 않음 | run | `validate/v11_web.py:206` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:281 · chapters/61-web.md:505 · chapters/61-web.md:2134 |
| `V11-58` | 쪽을 넘겨도 조건이 남음 | run | `validate/v11_web.py:211` | 2026-08-17 05:33 | 없음 | — |
| `V11-59` | 시안의 클래스가 CSS 에 있음 | run | `validate/v11_web.py:215` | 2026-08-17 05:33 | 2026-08-17 05:00 | guide/02_결함대장.md:149 · guide/02_결함대장.md:159 · guide/03_이력.md:282 |
| `V11-60` | 시안 CSS 를 다시 만들지 않음 | run | `validate/v11_web.py:219` | 2026-08-17 05:33 | 없음 | guide/02_결함대장.md:149 · guide/02_결함대장.md:159 · guide/03_이력.md:282 |
| `V11-61` | 이어질 수 있는 값이 링크임 | run | `validate/v11_web.py:223` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:283 · chapters/61-web.md:1159 · chapters/61-web.md:2137 |
| `V11-62` | 코드·줄임말에 title 이 있음 | run | `validate/v11_web.py:227` | 2026-08-17 05:33 | 없음 | chapters/61-web.md:1160 · chapters/61-web.md:2138 · trace/14-web.md:52 |
| `V11-63` | 매물 화면에 원문 링크가 있음 | run | `validate/v11_web.py:231` | 2026-08-17 05:33 | 없음 | chapters/61-web.md:1176 · chapters/61-web.md:2139 · trace/14-web.md:53 |
| `V11-64` | 고를 수 있는 값이 목록으로 제공됨 | run | `validate/v11_web.py:235` | 2026-08-17 05:33 | 없음 | chapters/61-web.md:1198 · chapters/61-web.md:2140 · trace/14-web.md:129 |
| `V11-65` | 기본 정렬이 규격대로임 | run | `validate/v11_web.py:240` | 2026-08-17 05:33 | 없음 | chapters/61-web.md:1219 · chapters/61-web.md:2141 · trace/14-web.md:55 |
| `V11-66` | 필터가 목록 위에 있음 | run | `validate/v11_web.py:244` | 2026-08-17 05:33 | 없음 | chapters/61-web.md:1240 · chapters/61-web.md:2142 · trace/14-web.md:54 |
| `V11-67` | 단추가 켜짐·꺼짐을 오감 | run | `validate/v11_web.py:247` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:283 · chapters/61-web.md:1241 · chapters/61-web.md:2143 |
| `V11-68` | v1 이 낸 열이 v2 에도 있음 | run | `validate/v11_web.py:251` | 2026-08-17 05:00 | 2026-08-17 05:33 | guide/01_요구사항.md:351 · guide/01_요구사항.md:361 · guide/03_이력.md:284 |
| `V11-69` | v1 이 가진 조작이 v2 에도 있음 | run | `validate/v11_web.py:256` | 2026-08-17 05:33 | 없음 | guide/01_요구사항.md:351 · guide/01_요구사항.md:361 · guide/03_이력.md:284 |
| `V11-70` | 좁은 폭에서 값이 사라지지 않음 | run | `validate/v11_web.py:261` | 2026-08-17 05:33 | 없음 | guide/01_요구사항.md:365 · guide/01_요구사항.md:375 · guide/03_이력.md:285 |
| `V11-71` | 가로 스크롤로 떠넘기지 않음 | run | `validate/v11_web.py:269` | 2026-08-17 05:33 | 없음 | guide/01_요구사항.md:365 · guide/01_요구사항.md:375 · guide/03_이력.md:285 |
| `V11-72` | 빈 주소로 가는 링크가 없음 | run | `validate/v11_web.py:273` | 2026-08-17 05:33 | 없음 | — |
| `V11-73` | 화면마다 값이 나옴 | run | `validate/v11_web.py:414` | 2026-08-17 05:33 | 없음 | — |
| `V11-74` | 숫자가 단위와 함께 나옴 | run | `validate/v11_web.py:417` | 2026-08-17 05:33 | 없음 | — |
| `V11-75` | 링크가 유효함 | run | `validate/v11_web.py:420` | 2026-08-17 05:33 | 없음 | — |
| `V11-76` | 화면 크기·시간이 상한 안 | run | `validate/v11_web.py:423` | 2026-08-17 05:33 | 2026-08-16 23:59 | — |
| `V11-77` | 시안의 시각 요소가 렌더 결과에 나옴 | run | `validate/v11_web.py:278` | 2026-08-17 05:33 | 2026-08-16 23:59 | trace/14-web.md:99 · trace/14-web.md:102 · trace/14-web.md:103 |
| `V11-78` | 좁은 폭에서 글자가 세로로 안 떨어짐 | run | `validate/v11_web.py:284` | 2026-08-17 05:33 | 없음 | chapters/00-standard.md:1258 · chapters/00-standard.md:1262 · chapters/00-standard.md:1272 |
| `V11-79` | 축 칸에 맨 숫자가 나오지 않음 | run | `validate/v11_web.py:400` | 2026-08-17 05:33 | 없음 | guide/02_결함대장.md:18 · guide/02_결함대장.md:28 · guide/03_이력.md:287 |
| `V11-80` | 사진이 최소 크기 이상 | run | `validate/v11_web.py:405` | 2026-08-17 05:33 | 없음 | guide/01_요구사항.md:379 · guide/01_요구사항.md:389 · guide/03_이력.md:288 |
| `V11-81` | 신차가 · 시세 · 가격 셋이 함께 나옴 | run | `validate/v11_web.py:409` | 2026-08-17 05:33 | 없음 | guide/01_요구사항.md:45 · guide/01_요구사항.md:55 · guide/03_이력.md:290 |
| `V11-82` | 정적 파일에 버전이 붙음 | run | `validate/v11_web.py:395` | 2026-08-17 05:33 | 없음 | trace/14-web.md:21 |
| `V11-85` | — | — | **★ 코드에 없다** | — | — | guide/02_결함대장.md:32 · guide/02_결함대장.md:42 · guide/03_이력.md:292 |
| `V11-87` | — | — | **★ 코드에 없다** | — | — | guide/01_요구사항.md:59 · guide/01_요구사항.md:69 · guide/03_이력.md:293 |
| `V11-88` | — | — | **★ 코드에 없다** | — | — | guide/01_요구사항.md:407 · guide/01_요구사항.md:417 · guide/03_이력.md:295 |
| `V11-92` | 신차가가 등급기준 + 옵션 합 | run | `validate/v11_web.py:391` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:308 · chapters/30-score/a-frame.md:637 · trace/05-score.md:33 |
| `V11-93` | — | — | **★ 코드에 없다** | — | — | guide/01_요구사항.md:421 · guide/01_요구사항.md:431 · guide/03_이력.md:310 |
| `V11-94` | — | — | **★ 코드에 없다** | — | — | guide/01_요구사항.md:435 · guide/01_요구사항.md:445 · guide/03_이력.md:311 |
| `V11-96` | — | — | **★ 코드에 없다** | — | — | guide/03_이력.md:312 · chapters/61-web.md:765 · chapters/61-web.md:2154 |
| `V11-98` | 큰 원문을 조각으로 보내고 이어붙이는가 | run | `validate/v11_web.py:380` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:314 · chapters/61-web.md:2160 · chapters/60-admin/c-tools.md:847 |
| `V11-99` | 같은 화면에서 여러 번 POST 가 되는가 | run | `validate/v11_web.py:385` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:315 · chapters/61-web.md:2161 · chapters/60-admin/c-tools.md:881 |
| `V11-100` | — | — | **★ 코드에 없다** | — | — | guide/03_이력.md:320 · chapters/00-standard.md:1512 · chapters/61-web.md:675 |
| `V11-103` | — | — | **★ 코드에 없다** | — | — | guide/03_이력.md:323 · chapters/60-admin/c-tools.md:1030 · trace/02-collect.md:47 |
| `V11-104` | 템플릿 문법이 화면에 새지 않음 | run | `validate/v11_web.py:289` | 2026-08-17 05:33 | 없음 | guide/01_요구사항.md:477 · guide/01_요구사항.md:486 · guide/03_이력.md:328 |
| `V11-105` | 화면 위아래가 어긋나지 않음 | run | `validate/v11_web.py:375` | 2026-08-17 05:33 | 없음 | guide/03_이력.md:332 · chapters/30-score/g-absolute.md:137 |
| `V11-106` | 값 자리에 「—」가 없음 | run | `validate/v11_web.py:294` | **★ 없음** | 없음 | chapters/00-standard.md:1321 · chapters/61-web/e-compare.md:46 · trace/14-web.md:61 |
| `V11-107` | 화면별 사진 크기가 부록 G 와 같음 | run | `validate/v11_web.py:370` | **★ 없음** | 없음 | guide/03_이력.md:339 · chapters/61-web/a-common.md:29 · trace/14-web.md:16 |
| `V11-108` | 좁은 폭에서 한 화면에 매물 2개 이상 | run | `validate/v11_web.py:341` | **★ 없음** | 없음 | chapters/61-web/a-common.md:45 · trace/14-web.md:18 |
| `V11-109` | 카드가 부록 G 줄 수 상한을 안 넘음 | run | `validate/v11_web.py:347` | **★ 없음** | 없음 | chapters/00-standard.md:1258 · chapters/00-standard.md:1272 · chapters/61-web/c-recommend.md:37 |
| `V11-110` | 상세 절 순서가 부록 G 와 같음 | run | `validate/v11_web.py:336` | **★ 없음** | 없음 | chapters/61-web/d-detail.md:65 · trace/14-web.md:82 |
| `V11-111` | — | — | **★ 코드에 없다** | — | — | chapters/61-web/e-compare.md:30 |
| `V11-113` | 다섯 폭 스크린샷이 있음 | run | `validate/v11_web.py:301` | **★ 없음** | 없음 | guide/03_이력.md:344 · chapters/61-web/f-width.md:24 · trace/14-web.md:13 |
| `V11-114` | 폭마다 부록 G 의 배치임 | run | `validate/v11_web.py:307` | **★ 없음** | 없음 | chapters/61-web/f-width.md:25 · trace/14-web.md:12 |
| `V11-115` | 어느 폭에서도 글자가 세로로 안 떨어짐 | run | `validate/v11_web.py:313` | **★ 없음** | 없음 | guide/03_이력.md:344 · chapters/61-web/f-width.md:26 · trace/14-web.md:14 |
| `V11-116` | 카드 전체가 상세 링크임 | run | `validate/v11_web.py:319` | **★ 없음** | 없음 | guide/03_이력.md:345 · chapters/61-web/f-width.md:51 · trace/14-web.md:58 |
| `V11-117` | 터치로 미리보기가 뜸 | run | `validate/v11_web.py:325` | **★ 없음** | 없음 | chapters/61-web/f-width.md:52 · trace/14-web.md:59 |
| `V11-118` | — | — | **★ 코드에 없다** | — | — | guide/03_이력.md:345 · chapters/61-web/f-width.md:70 |
| `V11-119` | 화면마다 부록 G 가 정한 차트가 있음 | run | `validate/v11_web.py:330` | **★ 없음** | 없음 | guide/02_결함대장.md:205 · guide/02_결함대장.md:215 · guide/03_이력.md:347 |
| `V11-120` | 매물마다 사이트별 구매 총액이 나옴 | run | `validate/v11_web.py:353` | **★ 없음** | 없음 | guide/03_이력.md:360 · chapters/40-report.md:685 · trace/40-report.md:110 |
| `V11-121` | 여러 사이트에 있는 차는 총액을 나란히 냄 | run | `validate/v11_web.py:359` | **★ 없음** | 없음 | guide/03_이력.md:360 · chapters/40-report.md:686 · trace/40-report.md:112 |
| `V11-122` | 리포트를 화면에서 읽을 수 있음 | run | `validate/v11_web.py:364` | **★ 없음** | 없음 | guide/03_이력.md:364 · chapters/40-report.md:733 · trace/40-report.md:118 |

## ② 죽은 검사 — 한 번도 안 돌았다

★ 「있다」와 「돈다」는 다릅니다. 안 도는 검사는 지키는 척만 합니다.

- `S1` 디렉터리 (STEP 15) — `tools/check_src.py`
- `S10` 도메인 예외 (STEP 3) — `tools/check_src.py`
- `S11` 분석 계층 순수성 (STEP 2) — `tools/check_src.py`
- `S12` 축 파일 STEP 주석 — `tools/check_src.py`
- `S13` 본문 config 예시 대조 — `tools/check_src.py`
- `S14` 상수 등록·성격 (V4-17) — `tools/check_src.py`
- `S14-1` 화면에 배점을 박지 않음 (V4-17) — `tools/check_src.py`
- `S15` 계층 의존 (STEP 15) — `tools/check_src.py`
- `S16` 검증 코드 대조 — `tools/check_src.py`
- `S2` 구조체 정의 — `tools/check_src.py`
- `S23` 실행 환경 (Python 3.11+) — `tools/check_src.py`
- `S24` 시험 격리 (운영 DB 미사용) — `tools/check_src.py`
- `S25` 형상 관리 (미커밋 없음) — `tools/check_src.py`
- `S26` 작업 기록 (6절 · 이름 규칙) — `tools/check_src.py`
- `S27` 기능마다 화면 (CLI 는 완성이 아니다) — `tools/check_src.py`
- `S28` 검사 색인 (규격 ↔ 코드) — `tools/check_src.py`
- `S29-0` 가벼운 점검 (4시간 · 실제로 돎) — `tools/check_src.py`
- `S29-4` 점검이 찾은 fatal 을 고침 — `tools/check_src.py`
- `S3` 함수 정의 — `tools/check_src.py`
- `S34-1` 표의 규격이 실재 — `tools/check_src.py`
- `S34-2` 표의 소스·검사가 실재 — `tools/check_src.py`
- `S34-3` 추적표 빈 칸을 센다 — `tools/check_src.py`
- `S34-4` 규격이 표에 있음 — `tools/check_src.py`
- `S35-1` 자기 칸만 고침 — `tools/check_src.py`
- `S36-1` 「정식 서비스 착수」 목록이 있음 — `tools/check_src.py`
- `S37-1` 파는 쪽 개념이 안 남아 있음 — `tools/check_src.py`
- `S4` 매물 적재 — `collect/runner.py`
- `S5` config 키 (V4-15) — `tools/check_src.py`
- `S6` 배점 검산 (불변식 ⑤) — `tools/check_src.py`
- `S7` 매직 넘버 (V4-13) — `tools/check_src.py`
- `S8` 접미사 규칙 (STEP 4) — `tools/check_src.py`
- `S9` 금지 근거 (STEP 14) — `tools/check_src.py`
- `V1-24` 받은 카탈로그가 매물과 이어짐 — `validate/v1_collect.py`
- `V1-25` ok 로 저장된 원문이 온전한가 — `validate/v1_collect.py`
- `V10-26` 목록 저장 후 큐에 작업이 들어감 — `validate/v10_admin.py`
- `V10-27` 중간 실패에서 다음 단계로 안 넘어감 — `validate/v10_admin.py`
- `V10-28` 타이머가 겹쳐 돌지 않음 — `validate/v10_admin.py`
- `V10-29` 목록 저장이 전건 재수집을 안 부름 — `validate/v10_admin.py`
- `V10-30` 재판정이 수집 없이 돎 — `validate/v10_admin.py`
- `V11-106` 값 자리에 「—」가 없음 — `validate/v11_web.py`
- `V11-107` 화면별 사진 크기가 부록 G 와 같음 — `validate/v11_web.py`
- `V11-108` 좁은 폭에서 한 화면에 매물 2개 이상 — `validate/v11_web.py`
- `V11-109` 카드가 부록 G 줄 수 상한을 안 넘음 — `validate/v11_web.py`
- `V11-110` 상세 절 순서가 부록 G 와 같음 — `validate/v11_web.py`
- `V11-113` 다섯 폭 스크린샷이 있음 — `validate/v11_web.py`
- `V11-114` 폭마다 부록 G 의 배치임 — `validate/v11_web.py`
- `V11-115` 어느 폭에서도 글자가 세로로 안 떨어짐 — `validate/v11_web.py`
- `V11-116` 카드 전체가 상세 링크임 — `validate/v11_web.py`
- `V11-117` 터치로 미리보기가 뜸 — `validate/v11_web.py`
- `V11-119` 화면마다 부록 G 가 정한 차트가 있음 — `validate/v11_web.py`
- `V11-120` 매물마다 사이트별 구매 총액이 나옴 — `validate/v11_web.py`
- `V11-121` 여러 사이트에 있는 차는 총액을 나란히 냄 — `validate/v11_web.py`
- `V11-122` 리포트를 화면에서 읽을 수 있음 — `validate/v11_web.py`
- `V3-68` 부록 F 전 24축이 구현돼 있음 — `validate/v3_logic.py`
- `V3-70` 일반·동력계 보증을 따로 냄 — `validate/v3_logic.py`
- `V3-71` 보증 잔여가 기간·거리 중 낮은 쪽임 — `validate/v3_logic.py`
- `V4-26` 미분류가 원인별로 갈려 있음 — `validate/v4_mapping.py`
- `V4-27` 판정을 막는 것만 막음 — `validate/v4_mapping.py`
- `V7-15` 진행 메모를 자유롭게 적을 수 있음 — `validate/v7_watch.py`
- `V9-06` 매물마다 사이트 배지가 있음 — `validate/v9_multisite.py`
- `V9-07` 합친 값에 출처가 붙어 있음 — `validate/v9_multisite.py`
- `V9-10` 사이트 보증 항목의 합이 만점과 같음 — `validate/v9_multisite.py`

## ⑤ ★ 규격이 요구했는데 코드에 없는 검사

- `V0-01` — guide/00_버전.md:18 · guide/03_이력.md:337
- `V0-02` — guide/00_버전.md:43
- `V0-03` — guide/00_버전.md:65 · guide/03_이력.md:337
- `V1-22` — guide/01_요구사항.md:115 · guide/01_요구사항.md:124 · guide/03_이력.md:303
- `V11-100` — guide/03_이력.md:320 · chapters/00-standard.md:1512 · chapters/61-web.md:675
- `V11-103` — guide/03_이력.md:323 · chapters/60-admin/c-tools.md:1030 · trace/02-collect.md:47
- `V11-111` — chapters/61-web/e-compare.md:30
- `V11-118` — guide/03_이력.md:345 · chapters/61-web/f-width.md:70
- `V11-45` — guide/01_요구사항.md:560 · guide/01_요구사항.md:569 · guide/03_이력.md:257
- `V11-85` — guide/02_결함대장.md:32 · guide/02_결함대장.md:42 · guide/03_이력.md:292
- `V11-87` — guide/01_요구사항.md:59 · guide/01_요구사항.md:69 · guide/03_이력.md:293
- `V11-88` — guide/01_요구사항.md:407 · guide/01_요구사항.md:417 · guide/03_이력.md:295
- `V11-93` — guide/01_요구사항.md:421 · guide/01_요구사항.md:431 · guide/03_이력.md:310
- `V11-94` — guide/01_요구사항.md:435 · guide/01_요구사항.md:445 · guide/03_이력.md:311
- `V11-96` — guide/03_이력.md:312 · chapters/61-web.md:765 · chapters/61-web.md:2154
- `V2-03` — chapters/11-store/a-key.md:339 · chapters/20-verify/b-v1v2.md:99
- `V3-42` — guide/01_요구사항.md:73 · guide/01_요구사항.md:83 · guide/03_이력.md:297
- `V3-44` — guide/02_결함대장.md:74 · guide/02_결함대장.md:84 · guide/03_이력.md:298
- `V3-49` — ENCAR_API.md:167 · guide/01_요구사항.md:101 · guide/01_요구사항.md:111
- `V3-50` — guide/03_이력.md:302 · chapters/30-score/d-history.md:358 · chapters/20-verify/c-v3v4.md:102
- `V3-58` — guide/03_이력.md:325 · chapters/30-score/a-frame.md:718 · trace/05-score.md:35
- `V3-66` — guide/02_결함대장.md:130 · guide/02_결함대장.md:140 · guide/03_이력.md:333
- `V3-67` — guide/01_요구사항.md:209 · guide/01_요구사항.md:219 · guide/03_이력.md:335
- `V3-69` — guide/03_이력.md:338 · chapters/30-score/a-frame.md:751
- `V4-28` — guide/03_이력.md:374 · chapters/31-registry.md:652
- `V4-29` — guide/03_이력.md:374 · chapters/31-registry.md:664
- `V6-01` — chapters/41-view.md:675 · chapters/61-web.md:328
- `V7-14` — guide/03_이력.md:362 · chapters/42-watch.md:427
- `V9-01` — guide/03_이력.md:316 · chapters/50-multisite.md:214 · chapters/50-multisite.md:298
- `V9-03` — guide/03_이력.md:316 · chapters/50-multisite.md:216 · chapters/50-multisite.md:320
- `V9-04` — guide/03_이력.md:317 · chapters/50-multisite.md:217 · chapters/50-multisite.md:347
- `V9-05` — guide/03_이력.md:317 · chapters/50-multisite.md:361 · trace/02-collect.md:71
- `V9-08` — guide/01_요구사항.md:168 · guide/01_요구사항.md:178 · guide/03_이력.md:319

## ④ 코드에 있는데 규격에 안 적힌 검사

- `S14-1` 화면에 배점을 박지 않음 (V4-17) — `tools/check_src.py`
- `V1-19` 이번 실행이 저장한 원문에 run_id 가 있음 — `validate/v1_collect.py`
- `V1-20` 카탈로그를 모델당 1회만 받음 — `validate/v1_collect.py`
- `V1-25` ok 로 저장된 원문이 온전한가 — `validate/v1_collect.py`
- `V11-37` POST 가 예상 밖 500 을 내지 않음 — `validate/v11_web.py`
- `V11-38` 템플릿이 쓰는 값을 뷰가 넘김 — `validate/v11_web.py`
- `V11-39` 저장 단추가 실제로 저장함 — `validate/v11_web.py`
- `V11-58` 쪽을 넘겨도 조건이 남음 — `validate/v11_web.py`
- `V11-72` 빈 주소로 가는 링크가 없음 — `validate/v11_web.py`
- `V11-73` 화면마다 값이 나옴 — `validate/v11_web.py`
- `V11-74` 숫자가 단위와 함께 나옴 — `validate/v11_web.py`
- `V11-75` 링크가 유효함 — `validate/v11_web.py`
- `V11-76` 화면 크기·시간이 상한 안 — `validate/v11_web.py`
