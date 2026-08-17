# 검사 색인 — 규격 ↔ 코드

**`python3.11 tools/build_index.py` 가 만든다. 손으로 고치지 않는다.**

검사 268개 · 규격이 요구했는데 코드에 없는 것 **14개** · 코드에 있는데 규격에 없는 것 **15개**

| 코드 | 무엇 | 등급 | 소스 | 규격 |
|---|---|---|---|---|
| `S1` | 디렉터리 (STEP 15) | fatal | `tools/check_src.py:159` | ref/E-attach.md:54 · guide/01_시작.md:213 · guide/03_이력.md:266 |
| `S2` | 구조체 정의 | fatal | `tools/check_src.py:181` | ref/E-attach.md:55 · guide/03_이력.md:266 · chapters/13-pipeline.md:101 |
| `S3` | 함수 정의 | fatal | `tools/check_src.py:202` | ref/E-attach.md:55 · guide/03_이력.md:266 · chapters/12-dict.md:175 |
| `S4` | 매물 적재 | fatal | `collect/runner.py:521` | ref/E-attach.md:56 · guide/03_이력.md:124 · guide/03_이력.md:142 |
| `S5` | config 키 (V4-15) | fatal | `tools/check_src.py:264` | ref/E-attach.md:57 · guide/01_시작.md:112 · guide/01_시작.md:189 |
| `S6` | 배점 검산 (불변식 ⑤) | fatal | `tools/check_src.py:294` | ref/E-attach.md:58 · guide/03_이력.md:277 · chapters/13-pipeline.md:105 |
| `S7` | 매직 넘버 (V4-13) | fatal | `tools/check_src.py:349` | ref/E-attach.md:59 · chapters/13-pipeline.md:106 · chapters/13-pipeline.md:107 |
| `S8` | 접미사 규칙 (STEP 4) | fatal | `tools/check_src.py:356` | ref/E-attach.md:60 · guide/03_이력.md:80 · chapters/13-pipeline.md:107 |
| `S9` | 금지 근거 (STEP 14) | fatal | `tools/check_src.py:372` | ref/A-check.md:47 · ref/E-attach.md:61 · guide/03_이력.md:191 |
| `S10` | 도메인 예외 (STEP 3) | fatal | `tools/check_src.py:378` | ref/E-attach.md:62 · guide/03_이력.md:256 · chapters/13-pipeline.md:111 |
| `S11` | 분석 계층 순수성 (STEP 2) | fatal | `tools/check_src.py:397` | ref/E-attach.md:63 · guide/01_시작.md:60 · guide/01_시작.md:92 |
| `S12` | 축 파일 STEP 주석 | fatal | `tools/check_src.py:412` | ref/E-attach.md:64 · guide/01_시작.md:224 · chapters/13-pipeline.md:113 |
| `S13` | 본문 config 예시 대조 | fatal | `tools/check_src.py:479` | ref/B-config.md:290 · ref/D-update.md:23 · ref/E-attach.md:65 |
| `S14` | 상수 등록·성격 (V4-17) | fatal | `tools/check_src.py:528` | ref/E-attach.md:66 · chapters/20-verify/c-v3v4.md:196 · chapters/20-verify/c-v3v4.md:202 |
| `S15` | 계층 의존 (STEP 15) | fatal | `tools/check_src.py:439` | ref/E-attach.md:67 · guide/03_이력.md:108 · chapters/10-collect/00-intro.md:218 |
| `S16` | 검증 코드 대조 | fatal | `tools/check_src.py:575` | ref/E-attach.md:68 · ref/E-attach.md:196 · guide/03_이력.md:145 |
| `S23` | 실행 환경 (Python 3.11+) | fatal | `tools/check_src.py:582` | ref/E-attach.md:75 · guide/03_이력.md:249 · chapters/00-standard.md:15 |
| `S24` | 시험 격리 (운영 DB 미사용) | fatal | `tools/check_src.py:601` | ref/E-attach.md:76 · guide/03_이력.md:253 · chapters/00-standard.md:94 |
| `S25` | 형상 관리 (미커밋 없음) | fatal | `tools/check_src.py:621` | ref/E-attach.md:77 · guide/03_이력.md:264 · chapters/00-standard.md:166 |
| `S26` | 작업 기록 (6절 · 이름 규칙) | fatal | `tools/check_src.py:649` | ref/E-attach.md:78 · guide/03_이력.md:264 · chapters/00-standard.md:190 |
| `S27` | 기능마다 화면 (CLI 는 완성이 아니다) | fatal | `tools/check_src.py:708` | ref/E-attach.md:79 · guide/03_이력.md:286 · chapters/00-standard.md:143 |
| `S28` | 검사 색인 (규격 ↔ 코드) | fatal | `tools/check_src.py:731` | — |
| `V1-01` | expected == requested + not_requested | run | `validate/v1_collect.py:25` | chapters/00-standard.md:354 · chapters/13-pipeline.md:607 · chapters/20-verify/b-v1v2.md:5 |
| `V1-02` | not_requested == 0 | run | `validate/v1_collect.py:28` | chapters/20-verify/b-v1v2.md:6 |
| `V1-03` | requested == ok+empty+not_found+error | run | `validate/v1_collect.py:31` | chapters/20-verify/00-intro.md:14 · chapters/20-verify/b-v1v2.md:7 · chapters/20-verify/d-v5.md:213 |
| `V1-04` | 형식 검증 거부 0 | run | `validate/v1_collect.py:34` | chapters/60-admin/b-ops.md:207 · chapters/20-verify/b-v1v2.md:8 · chapters/20-verify/b-v1v2.md:87 |
| `V1-05` | raw_response 신규 == 응답 합 | run | `validate/v1_collect.py:37` | guide/03_이력.md:47 · chapters/20-verify/b-v1v2.md:9 |
| `V1-06` | 차종별 ok > 0 | target | `validate/v1_collect.py:40` | chapters/20-verify/b-v1v2.md:15 |
| `V1-07` | 매물별 엔드포인트 4종 상태 존재 | listing | `validate/v1_collect.py:43` | chapters/20-verify/00-intro.md:117 · chapters/20-verify/b-v1v2.md:16 · chapters/10-collect/d-record.md:543 |
| `V1-08b` | 엔드포인트별 전량 404 없음 | run | `validate/v1_collect.py:49` | guide/03_이력.md:122 · chapters/20-verify/b-v1v2.md:84 · chapters/10-collect/d-record.md:525 |
| `V1-08` | 동일 코드 실패율 100% 인 엔드포인트 없음 | run | `validate/v1_collect.py:46` | guide/03_이력.md:48 · chapters/13-pipeline.md:500 · chapters/20-verify/00-intro.md:118 |
| `V1-09` | 시간대별 실패율 상승 없음 | run | `validate/v1_collect.py:106` | chapters/20-verify/b-v1v2.md:32 |
| `V1-10` | site_query 키가 전부 q 에 반영됨 | run | `validate/v1_collect.py:103` | guide/03_이력.md:112 · chapters/20-verify/b-v1v2.md:33 · chapters/10-collect/a-endpoint.md:169 |
| `V1-11` | 예외로 종료된 실행이 없음 | run | `validate/v1_collect.py:53` | guide/03_이력.md:117 · chapters/60-admin/b-ops.md:157 · chapters/20-verify/b-v1v2.md:34 |
| `V1-12` | 연속 실패 중단 시 ResumePoint 가 남음 | run | `validate/v1_collect.py:99` | guide/03_이력.md:115 · chapters/20-verify/b-v1v2.md:35 |
| `V1-13` | 껍데기를 거친 실행과 직접 실행의 인자가 같음 | run | `validate/v1_collect.py:77` | guide/01_시작.md:113 · guide/03_이력.md:123 · guide/03_이력.md:211 |
| `V1-14` | diagnosis 호출 대상이 encarDiagnosis == 0 으로 좁혀짐 | run | `validate/v1_collect.py:56` | guide/03_이력.md:170 · guide/03_이력.md:186 · chapters/13-pipeline.md:160 |
| `V1-15` | expected == 요청 대상 수 (skipped 제외) | run | `validate/v1_collect.py:94` | guide/03_이력.md:193 · chapters/13-pipeline.md:160 · chapters/20-verify/b-v1v2.md:38 |
| `V1-16` | 이번 run_id 밖의 행을 보지 않음 | run | `validate/v1_collect.py:89` | guide/03_이력.md:191 · guide/03_이력.md:193 · guide/03_이력.md:195 |
| `V1-17` | diagnosis 가 detail 뒤에 있음 | run | `validate/v1_collect.py:82` | guide/03_이력.md:212 · chapters/20-verify/b-v1v2.md:40 · chapters/10-collect/a-endpoint.md:152 |
| `V1-18` | 빈 DB 에서도 검사가 돈다 | run | `validate/v1_collect.py:86` | guide/03_이력.md:210 · chapters/13-pipeline.md:133 · chapters/20-verify/b-v1v2.md:41 |
| `V1-19` | 이번 실행이 저장한 원문에 run_id 가 있음 | run | `validate/v1_collect.py:72` | — |
| `V1-20` | 카탈로그를 모델당 1회만 받음 | run | `validate/v1_collect.py:67` | — |
| `V1-21` | 받아 두고 안 펼쳐진 원문이 없음 | run | `validate/v1_collect.py:61` | guide/03_이력.md:275 · chapters/13-pipeline.md:205 · chapters/20-verify/b-v1v2.md:42 |
| `V1-22` | — | — | **★ 코드에 없다** | guide/03_이력.md:303 · chapters/30-score/a-frame.md:641 |
| `V2-01` | ok 원문 수 == CORE 행 수 | run | `validate/v2_load.py:26` | chapters/00-standard.md:354 · chapters/11-store/a-key.md:298 · chapters/20-verify/b-v1v2.md:97 |
| `V2-02` | 필수 컬럼 NOT NULL 위반 없음 | run | `validate/v2_load.py:29` | chapters/20-verify/b-v1v2.md:98 |
| `V2-03` | — | — | **★ 코드에 없다** | chapters/11-store/a-key.md:339 · chapters/20-verify/b-v1v2.md:99 |
| `V2-04` | status 열거값 위반 없음 | run | `validate/v2_load.py:32` | chapters/20-verify/b-v1v2.md:100 |
| `V2-05` | 단위 — 가격이 만원 단위로 남아 있지 않은가 | run | `validate/v2_load.py:35` | chapters/00-standard.md:653 · chapters/60-admin/b-ops.md:68 · chapters/20-verify/b-v1v2.md:101 |
| `V2-06` | 빈 컨테이너가 NULL 로 저장되지 않았는가 | run | `validate/v2_load.py:38` | chapters/20-verify/b-v1v2.md:102 · chapters/20-verify/b-v1v2.md:140 · chapters/20-verify/b-v1v2.md:143 |
| `V2-07` | 전건 NULL 컬럼 | run | `validate/v2_load.py:41` | chapters/20-verify/b-v1v2.md:103 · chapters/20-verify/b-v1v2.md:140 · chapters/20-verify/b-v1v2.md:144 |
| `V2-08` | 값 종류 1인 컬럼 | run | `validate/v2_load.py:121` | chapters/20-verify/b-v1v2.md:104 · chapters/20-verify/b-v1v2.md:140 · chapters/20-verify/b-v1v2.md:145 |
| `V2-09` | core_pii 를 직접 조회하는 코드 없음 | run | `validate/v2_load.py:44` | guide/03_이력.md:84 · chapters/11-store/b-core.md:480 · chapters/60-admin/00-intro.md:173 |
| `V2-10` | core_listing 에 plate_no · dealer_name · phone · address 없음 | run | `validate/v2_load.py:47` | guide/03_이력.md:84 · chapters/20-verify/b-v1v2.md:120 |
| `V2-10b` | core_* 에 마스킹 컬럼 없음 | run | `validate/v2_load.py:57` | chapters/20-verify/b-v1v2.md:121 |
| `V2-11` | plate_hash 가 전건 16자 hex | run | `validate/v2_load.py:118` | chapters/11-store/b-core.md:438 · chapters/20-verify/b-v1v2.md:122 |
| `V2-12` | secrets/plate_hmac.key 가 버전 관리 밖 | run | `validate/v2_load.py:53` | chapters/60-admin/00-intro.md:173 · chapters/20-verify/b-v1v2.md:123 |
| `V2-13` | core_record 에 record_plate_no 원본 없음 | run | `validate/v2_load.py:80` | chapters/11-store/b-core.md:635 · chapters/20-verify/b-v1v2.md:124 |
| `V2-14` | 참조되는 5종 PK 가 단일 INTEGER | run | `validate/v2_load.py:109` | chapters/11-store/a-key.md:151 · chapters/11-store/a-key.md:491 · chapters/60-admin/00-intro.md:139 |
| `V2-15` | 자연키가 UNIQUE 로 걸려 있음 | run | `validate/v2_load.py:112` | chapters/20-verify/b-v1v2.md:126 |
| `V2-16` | PK·FK 컬럼에 개인정보 없음 | run | `validate/v2_load.py:115` | chapters/60-admin/00-intro.md:139 · chapters/20-verify/b-v1v2.md:127 |
| `V2-17` | PII 고아 행 없음 | run | `validate/v2_load.py:60` | guide/03_이력.md:98 · chapters/11-store/b-core.md:466 · chapters/20-verify/b-v1v2.md:128 |
| `V2-18` | parse_rule 재처리 후 전 봉투가 현재 parse_version | run | `validate/v2_load.py:105` | guide/03_이력.md:124 · chapters/13-pipeline.md:336 · chapters/20-verify/b-v1v2.md:129 |
| `V2-19` | 원문 유래 컬럼에 NOT NULL 없음 | run | `validate/v2_load.py:102` | guide/03_이력.md:127 · chapters/11-store/a-key.md:407 · chapters/11-store/a-key.md:491 |
| `V2-20` | 파싱 실패 필드가 있는 행도 CORE 에 있음 | run | `validate/v2_load.py:64` | guide/03_이력.md:128 · chapters/20-verify/b-v1v2.md:106 · chapters/10-collect/d-record.md:50 |
| `V2-21` | parse_error · type_mismatch 건수 | run | `validate/v2_load.py:68` | chapters/20-verify/b-v1v2.md:107 |
| `V2-22` | 현재 DB 스키마가 sql/ddl 과 일치 | run | `validate/v2_load.py:84` | guide/03_이력.md:133 · chapters/20-verify/b-v1v2.md:71 · chapters/20-verify/b-v1v2.md:108 |
| `V2-23` | 중간 노드 None 인 매물도 CORE 에 있음 | run | `validate/v2_load.py:87` | guide/03_이력.md:137 · chapters/20-verify/b-v1v2.md:109 · chapters/10-collect/d-record.md:89 |
| `V2-24` | 배열 기대 필드가 전건 list 로 정규화됨 | run | `validate/v2_load.py:91` | chapters/20-verify/b-v1v2.md:110 |
| `V2-25` | 스칼라 null 이 0 으로 저장된 컬럼 없음 | run | `validate/v2_load.py:95` | chapters/20-verify/b-v1v2.md:111 |
| `V2-27` | parse/ 에 원문 연쇄 첨자가 없음 | run | `validate/v2_load.py:98` | guide/03_이력.md:140 · chapters/20-verify/00-intro.md:143 · chapters/20-verify/b-v1v2.md:112 |
| `V2-28` | 파싱 실패해도 남은 필드가 저장됨 | run | `validate/v2_load.py:72` | guide/03_이력.md:228 · chapters/00-standard.md:699 · chapters/20-verify/b-v1v2.md:114 |
| `V2-29` | upsert 가 버린 키를 기록함 | run | `validate/v2_load.py:77` | guide/03_이력.md:229 · chapters/20-verify/b-v1v2.md:115 · chapters/10-collect/b-parse.md:67 |
| `V2-30` | 전 파서가 row_status 를 냄 | run | `validate/v2_load.py:134` | guide/03_이력.md:277 · chapters/20-verify/b-v1v2.md:116 · chapters/10-collect/b-parse.md:88 |
| `V2-31` | target_key NULL 이 판정에 들어가지 않음 | run | `validate/v2_load.py:124` | guide/03_이력.md:278 · chapters/11-store/b-core.md:679 · chapters/20-verify/b-v1v2.md:117 |
| `V2-32` | NULL 매물의 모델명이 화면에서 보임 | run | `validate/v2_load.py:129` | guide/03_이력.md:278 · chapters/11-store/b-core.md:680 · chapters/20-verify/b-v1v2.md:118 |
| `V3-01` | result_axis.source 전건 NOT NULL | axis | `validate/v3_logic.py:32` | chapters/20-verify/c-v3v4.md:37 · chapters/20-verify/c-v3v4.md:113 |
| `V3-02` | result_axis.prio 전건 NOT NULL | axis | `validate/v3_logic.py:35` | chapters/20-verify/c-v3v4.md:38 |
| `V3-03` | 축별 source 값 종류 >= 2 | axis | `validate/v3_logic.py:38` | chapters/00-standard.md:657 · chapters/30-score/c-spec.md:57 · chapters/20-verify/c-v3v4.md:39 |
| `V3-04` | 축별 값 종류 >= 2 | axis | `validate/v3_logic.py:41` | chapters/40-report.md:108 · chapters/40-report.md:324 · chapters/30-score/c-spec.md:9 |
| `V3-05` | 금지 근거가 source 에 없음 | axis | `validate/v3_logic.py:44` | chapters/20-verify/c-v3v4.md:41 |
| `V3-06` | put() 충돌 기록 검토 | run | `validate/v3_logic.py:59` | chapters/20-verify/c-v3v4.md:42 |
| `V3-07` | 축별 -1 비율 | axis | `validate/v3_logic.py:47` | chapters/20-verify/c-v3v4.md:43 |
| `V3-08` | 사전 pending 이 판정에 쓰이지 않음 | run | `validate/v3_logic.py:50` | chapters/20-verify/c-v3v4.md:44 |
| `V3-09` | 축별 excluded 비율 | axis | `validate/v3_logic.py:53` | chapters/20-verify/c-v3v4.md:45 |
| `V3-10` | 재판정 결과가 이전과 동일 | run | `validate/v3_logic.py:62` | chapters/20-verify/c-v3v4.md:125 |
| `V3-11` | put() 순서 셔플 후에도 동일 | run | `validate/v3_logic.py:56` | chapters/00-standard.md:656 · chapters/30-score/a-frame.md:181 · chapters/20-verify/c-v3v4.md:126 |
| `V3-20` | trust_score 가 555 에 합산되지 않음 | run | `validate/v3_logic.py:190` | chapters/20-verify/00-intro.md:142 · chapters/20-verify/c-v3v4.md:80 · chapters/20-verify/c-v3v4.md:113 |
| `V3-21` | 경고가 555 에 합산되지 않음 | run | `validate/v3_logic.py:193` | chapters/30-score/g-absolute.md:148 · chapters/20-verify/c-v3v4.md:81 |
| `V3-22` | 경고로 매물이 목록에서 제외되지 않음 | run | `validate/v3_logic.py:196` | chapters/20-verify/c-v3v4.md:82 |
| `V3-23` | 경고로 등급·추천 순위가 바뀌지 않음 | run | `validate/v3_logic.py:65` | chapters/20-verify/c-v3v4.md:83 |
| `V3-24` | acknowledged 가 신호 감지를 멈추지 않음 | run | `validate/v3_logic.py:69` | chapters/20-verify/c-v3v4.md:84 |
| `V3-25` | 소멸한 경고가 삭제되지 않고 남음 | run | `validate/v3_logic.py:72` | chapters/20-verify/c-v3v4.md:85 |
| `V3-27` | 모든 경고에 evidence 존재 | run | `validate/v3_logic.py:199` | chapters/20-verify/c-v3v4.md:87 |
| `V3-28` | PeerGroup 이 확장 단계를 표시 | run | `validate/v3_logic.py:75` | chapters/30-score/g-absolute.md:427 · chapters/20-verify/c-v3v4.md:88 |
| `V3-29` | 배점 변경 시 calc_version 이 증가 | run | `validate/v3_logic.py:79` | chapters/20-verify/c-v3v4.md:89 |
| `V3-30` | halt 축의 사전이 비어 있지 않음 | run | `validate/v3_logic.py:93` | guide/03_이력.md:116 · chapters/00-standard.md:202 · chapters/12-dict.md:226 |
| `V3-31` | 딜러 NULL 매물에 dealer_untrusted 없음 | run | `validate/v3_logic.py:185` | guide/03_이력.md:139 · chapters/20-verify/c-v3v4.md:104 · chapters/10-collect/d-record.md:185 |
| `V3-32` | seizing null 매물이 「저당 없음」으로 판정되지 않음 | run | `validate/v3_logic.py:120` | guide/03_이력.md:139 · chapters/20-verify/c-v3v4.md:105 · chapters/10-collect/d-record.md:221 |
| `V3-33` | HDA 판정이 전건 description 근거 | run | `validate/v3_logic.py:112` | guide/03_이력.md:159 · chapters/30-score/c-spec.md:144 · chapters/20-verify/c-v3v4.md:106 |
| `V3-34` | 판정 항목 수 == resultCode IS NOT NULL 인 items 수 | run | `validate/v3_logic.py:106` | guide/03_이력.md:172 · chapters/11-store/b-core.md:224 · chapters/20-verify/c-v3v4.md:107 |
| `V3-35` | conflicts 가 있는 매물이 기록됨 | run | `validate/v3_logic.py:98` | guide/03_이력.md:213 · chapters/30-score/a-frame.md:153 · chapters/11-store/c-result.md:211 |
| `V3-36` | conflicts 건수가 임계 미만 | run | `validate/v3_logic.py:103` | guide/03_이력.md:213 · chapters/00-standard.md:700 · chapters/30-score/a-frame.md:154 |
| `V3-37` | 목록 관측분의 source 가 'list' 임 | run | `validate/v3_logic.py:126` | guide/03_이력.md:273 · guide/03_이력.md:276 · chapters/12-dict.md:151 |
| `V3-38` | facet 수신 후 목록 관측분과 대조함 | run | `validate/v3_logic.py:131` | guide/03_이력.md:273 · chapters/12-dict.md:152 · chapters/60-admin/c-tools.md:524 |
| `V3-39` | 이론가와 실제 중앙값의 차가 상한 안 | run | `validate/v3_logic.py:152` | guide/03_이력.md:289 · chapters/61-web.md:966 |
| `V3-40` | 핵심 축이 excluded 인데 등급을 매기지 않음 | run | `validate/v3_logic.py:142` | guide/03_이력.md:294 · chapters/30-score/g-absolute.md:635 · chapters/20-verify/c-v3v4.md:92 |
| `V3-41` | 전 매물의 분모가 만점과 같음 | run | `validate/v3_logic.py:136` | guide/03_이력.md:296 · chapters/00-standard.md:867 · chapters/30-score/a-frame.md:239 |
| `V3-42` | — | — | **★ 코드에 없다** | guide/03_이력.md:297 · chapters/30-score/a-frame.md:309 · chapters/20-verify/c-v3v4.md:94 |
| `V3-44` | — | — | **★ 코드에 없다** | guide/03_이력.md:298 · chapters/30-score/a-frame.md:354 · chapters/20-verify/c-v3v4.md:96 |
| `V3-45` | 배점 합이 만점과 같음 | run | `validate/v3_logic.py:182` | guide/03_이력.md:299 · chapters/30-score/a-frame.md:464 · chapters/20-verify/c-v3v4.md:97 |
| `V3-47` | 축별 차종 간 결측률 편차가 상한 안 | run | `validate/v3_logic.py:147` | guide/03_이력.md:300 · chapters/30-score/a-frame.md:525 · chapters/20-verify/c-v3v4.md:99 |
| `V3-49` | — | — | **★ 코드에 없다** | guide/03_이력.md:301 · chapters/30-score/d-history.md:331 · chapters/20-verify/c-v3v4.md:101 |
| `V3-50` | — | — | **★ 코드에 없다** | guide/03_이력.md:302 · chapters/30-score/d-history.md:358 · chapters/20-verify/c-v3v4.md:102 |
| `V3-52` | 「싸다」에 이유가 붙어 있음 | run | `validate/v3_logic.py:168` | guide/03_이력.md:306 · chapters/30-score/a-frame.md:686 |
| `V3-53` | 점검 출처가 판정에 반영됨 | run | `validate/v3_logic.py:173` | guide/03_이력.md:307 · chapters/30-score/a-frame.md:713 |
| `V3-54` | 렌트 이력을 세 곳에서 대조 | run | `validate/v3_logic.py:177` | guide/03_이력.md:309 · chapters/30-score/a-frame.md:757 |
| `V3-55` | 사이트 보증 축이 config 규칙을 읽는가 | run | `validate/v3_logic.py:157` | guide/03_이력.md:313 · chapters/30-score/a-frame.md:834 |
| `V3-56` | 배점 합이 605 | run | `validate/v3_logic.py:162` | chapters/30-score/a-frame.md:835 |
| `V3-57` | 등급이 555 기준 | run | `validate/v3_logic.py:165` | guide/03_이력.md:313 · chapters/30-score/a-frame.md:836 |
| `V4-01` | 매핑 일치율 (A 100% · B 99% · C 80%) | run | `validate/v4_mapping.py:28` | chapters/00-standard.md:654 · chapters/60-admin/c-tools.md:144 · chapters/20-verify/c-v3v4.md:164 |
| `V4-02` | 미매핑 경로 목록 | run | `validate/v4_mapping.py:74` | chapters/20-verify/c-v3v4.md:165 |
| `V4-03` | 오매핑 탐지 — 다른 경로와 더 높은 일치율 | run | `validate/v4_mapping.py:31` | chapters/20-verify/c-v3v4.md:166 · chapters/20-verify/c-v3v4.md:282 |
| `V4-04` | 매핑표에 없는 CORE 컬럼 | run | `validate/v4_mapping.py:77` | chapters/20-verify/c-v3v4.md:167 |
| `V4-05` | 원문 경로 수 변동 | run | `validate/v4_mapping.py:79` | chapters/31-registry.md:295 · chapters/20-verify/c-v3v4.md:168 · chapters/20-verify/c-v3v4.md:295 |
| `V4-06` | RAW 경로가 등록부에 있는가 | run | `validate/v4_mapping.py:34` | chapters/31-registry.md:58 · chapters/31-registry.md:203 · chapters/31-registry.md:211 |
| `V4-06b` | 등록부에 있는데 RAW 에 없는 유령 경로 | run | `validate/v4_mapping.py:37` | chapters/31-registry.md:227 · chapters/31-registry.md:244 · chapters/40-report.md:142 |
| `V4-07` | in_use 인데 core_column NULL | run | `validate/v4_mapping.py:40` | chapters/31-registry.md:286 · chapters/60-admin/b-ops.md:121 · chapters/20-verify/c-v3v4.md:171 |
| `V4-08` | blocked 인데 unblock_condition NULL | run | `validate/v4_mapping.py:43` | chapters/31-registry.md:287 · chapters/20-verify/c-v3v4.md:172 |
| `V4-09` | deferred 인데 use_when NULL | run | `validate/v4_mapping.py:46` | chapters/31-registry.md:288 · chapters/20-verify/c-v3v4.md:173 |
| `V4-10` | display_only 인데 core_column NULL | run | `validate/v4_mapping.py:49` | chapters/31-registry.md:289 · chapters/20-verify/c-v3v4.md:174 |
| `V4-11b` | 판정에 안 쓰는 미분류 경로 | run | `validate/v4_mapping.py:55` | guide/03_이력.md:129 · chapters/31-registry.md:127 · chapters/31-registry.md:160 |
| `V4-11` | unclassified 존재 | run | `validate/v4_mapping.py:52` | guide/01_시작.md:214 · guide/01_시작.md:224 · guide/03_이력.md:129 |
| `V4-12` | facet 필수 축 집합 존재 | run | `validate/v4_mapping.py:58` | chapters/20-verify/c-v3v4.md:177 |
| `V4-13` | 매직 넘버 없음 (tools/check_src.py S7) | run | `validate/v4_mapping.py:61` | ref/A-check.md:6 · ref/E-attach.md:59 · ref/E-attach.md:96 |
| `V4-19` | 성격(kind)이 없는 Check 가 없음 | run | `validate/v4_mapping.py:82` | guide/03_이력.md:132 · chapters/20-verify/00-intro.md:112 · chapters/20-verify/c-v3v4.md:184 |
| `V4-20` | dict_option_code 에 문장(공백·한글)이 없음 | run | `validate/v4_mapping.py:97` | guide/03_이력.md:138 · chapters/20-verify/c-v3v4.md:185 · chapters/10-collect/e-catalog.md:174 |
| `V4-21` | 같은 이름의 공개 함수가 두 모듈에 없음 | run | `validate/v4_mapping.py:93` | guide/03_이력.md:144 · chapters/30-score/h-verdict.md:67 · chapters/20-verify/c-v3v4.md:186 |
| `V4-22` | 역방향 · 순환 import 없음 | run | `validate/v4_mapping.py:85` | MAPPING.md:54 · MAPPING.md:88 · guide/03_이력.md:150 |
| `V4-23` | 모듈 최상위에 I/O · 부작용 없음 | run | `validate/v4_mapping.py:88` | MAPPING.md:89 · guide/03_이력.md:150 · chapters/41-view.md:574 |
| `V4-24` | 축 함수가 target_config 에서 매물 값을 읽지 않음 | run | `validate/v4_mapping.py:63` | guide/03_이력.md:214 · chapters/01-arch.md:215 · chapters/20-verify/c-v3v4.md:189 |
| `V4-25` | 판정에 쓰는 축의 사전이 비어 있지 않음 | run | `validate/v4_mapping.py:69` | guide/03_이력.md:230 · guide/03_이력.md:267 · chapters/00-standard.md:202 |
| `V5-01` | 배점 합계 == config 총점 | run | `validate/v5_value.py:16` | chapters/20-verify/d-v5.md:7 |
| `V5-02` | 표시용 등급 점수가 비율과 일치 | run | `validate/v5_value.py:19` | chapters/20-verify/d-v5.md:8 |
| `V5-03` | 분모 시험 A·D·E·G·H·I 통과 | run | `validate/v5_value.py:22` | chapters/30-score/g-absolute.md:490 · chapters/20-verify/d-v5.md:9 · chapters/20-verify/d-v5.md:20 |
| `V5-04` | 점수 범위 위반 없음 | run | `validate/v5_value.py:25` | chapters/20-verify/d-v5.md:10 |
| `V5-05` | 등급 분포가 극단적이지 않음 | run | `validate/v5_value.py:28` | chapters/00-standard.md:655 · chapters/30-score/h-verdict.md:9 · chapters/60-admin/c-tools.md:146 |
| `V5-06` | 기준값 대비 실측 이탈 | run | `validate/v5_value.py:31` | chapters/30-score/b-price.md:82 · chapters/20-verify/d-v5.md:12 · chapters/20-verify/d-v5.md:45 |
| `V5-07` | 계수 보정 타당성 | run | `validate/v5_value.py:34` | chapters/20-verify/d-v5.md:13 |
| `V5-08` | 계수 산출 입력에 result_* 없음 | run | `validate/v5_value.py:51` | chapters/20-verify/d-v5.md:14 · chapters/20-verify/d-v5.md:115 |
| `V5-09` | 등급이 earned / denominator 로 산출됨 | run | `validate/v5_value.py:41` | guide/03_이력.md:135 · chapters/20-verify/d-v5.md:15 |
| `V5-10` | 같은 비율 · 다른 분모가 같은 등급 | run | `validate/v5_value.py:46` | chapters/20-verify/d-v5.md:16 |
| `V5-11` | 분모 최대값으로도 S 가 불가능한 매물 없음 | run | `validate/v5_value.py:48` | guide/03_이력.md:135 · chapters/20-verify/d-v5.md:17 |
| `V5-12` | NOT_RATED 인데 not_rated_reason 이 NULL 인 행 없음 | run | `validate/v5_value.py:37` | guide/03_이력.md:227 · chapters/11-store/c-result.md:115 · chapters/20-verify/d-v5.md:18 |
| `V6-01` | — | — | **★ 코드에 없다** | chapters/41-view.md:669 · chapters/61-web.md:328 |
| `V6-07` | ORDER BY 에 4단이 전부 있음 | run | `validate/v3_logic.py:116` | guide/03_이력.md:152 · guide/03_이력.md:206 · chapters/41-view.md:563 |
| `V7-01` | watch_track 에 버전 4종 전건 있음 | run | `validate/v7_watch.py:29` | guide/03_이력.md:147 · chapters/42-watch.md:580 |
| `V7-02` | cause != 'listing' 인 이벤트가 알림되지 않음 | run | `validate/v7_watch.py:33` | chapters/42-watch.md:586 |
| `V7-04` | 같은 이벤트 중복 발송 0건 | run | `validate/v7_watch.py:37` | chapters/42-watch.md:588 · chapters/50-multisite.md:118 |
| `V7-05` | gone 매물이 목록에서 삭제되지 않음 | run | `validate/v7_watch.py:39` | chapters/42-watch.md:589 |
| `V7-06` | 검증 실패 실행에서 알림이 나가지 않음 | run | `validate/v7_watch.py:42` | chapters/42-watch.md:590 · chapters/50-multisite.md:110 |
| `V7-07` | relist 결합에 identity_kind 기록 | run | `validate/v7_watch.py:46` | chapters/42-watch.md:591 |
| `V7-08` | 구매 체크리스트가 점수·등급에 반영되지 않음 | run | `validate/v7_watch.py:61` | chapters/42-watch.md:592 |
| `V7-09` | 실구매가·총소유비용이 점수에 반영되지 않음 | run | `validate/v7_watch.py:65` | chapters/42-watch.md:593 |
| `V7-10` | 발송 시도 대비 성공률 | run | `validate/v7_watch.py:49` | guide/03_이력.md:153 · chapters/42-watch.md:594 · chapters/50-multisite.md:59 |
| `V7-11` | closed_reason 이 CHECK 안의 값 | run | `validate/v7_watch.py:57` | guide/03_이력.md:175 · guide/03_이력.md:217 · chapters/42-watch.md:185 |
| `V7-12` | 남의 관심 항목을 고치지 못함 | run | `validate/v7_watch.py:53` | guide/03_이력.md:199 · guide/03_이력.md:291 · chapters/42-watch.md:197 |
| `V8-01` | 같은 파일명이 두 번 생성되지 않음 | run | `validate/v3_logic.py:83` | guide/03_이력.md:151 · chapters/40-report.md:542 · chapters/41-view.md:689 |
| `V8-02` | 출력 파일에 BOM · CRLF 가 없음 | run | `validate/v3_logic.py:88` | guide/03_이력.md:151 · chapters/40-report.md:571 · chapters/41-view.md:690 |
| `V10-01` | admin 전용을 user 로 호출 시 PolicyError | run | `validate/v10_admin.py:20` | chapters/60-admin/c-tools.md:767 |
| `V10-02` | 서버 권한 검증 존재 (화면 숨김 아님) | run | `validate/v10_admin.py:23` | chapters/60-admin/c-tools.md:768 |
| `V10-03` | run_query 가 SELECT 외를 전건 거부 | run | `validate/v10_admin.py:26` | chapters/60-admin/c-tools.md:769 |
| `V10-04` | run_query 판정이 AST 기반 (정규식 아님) | run | `validate/v10_admin.py:29` | chapters/60-admin/c-tools.md:770 |
| `V10-05` | config 변경이 ConfigChange 없이 안 일어남 | run | `validate/v10_admin.py:32` | chapters/60-admin/c-tools.md:771 · chapters/20-verify/c-v3v4.md:196 · chapters/20-verify/c-v3v4.md:201 |
| `V10-06` | 배점 저장 시 Σ == total_points | run | `validate/v10_admin.py:35` | chapters/60-admin/c-tools.md:772 |
| `V10-07` | 성분 추가가 선택 가능 목록 안에서만 | run | `validate/v10_admin.py:38` | chapters/60-admin/c-tools.md:773 |
| `V10-08` | 관리 도구가 core_* 를 UPDATE 하지 않음 | run | `validate/v10_admin.py:41` | chapters/60-admin/c-tools.md:774 |
| `V10-09` | DevRequest 가 삭제되지 않음 | run | `validate/v10_admin.py:44` | chapters/60-admin/c-tools.md:775 |
| `V10-10` | 문서 뷰어에 편집 경로 없음 | run | `validate/v10_admin.py:47` | chapters/60-admin/c-tools.md:776 |
| `V10-11` | 실행 중 config 변경이 잠김 | run | `validate/v10_admin.py:50` | chapters/60-admin/c-tools.md:777 |
| `V10-12` | 배점 조정 후 0점 성분 없음 | run | `validate/v10_admin.py:53` | chapters/60-admin/c-tools.md:778 |
| `V10-13` | 웹에서 전면 재수집이 큐에 안 들어감 | run | `validate/v10_admin.py:56` | guide/03_이력.md:97 · chapters/60-admin/b-ops.md:217 · chapters/60-admin/c-tools.md:779 |
| `V10-14` | components.{axis}.{component} 경로 읽기·쓰기 | run | `validate/v10_admin.py:59` | guide/03_이력.md:103 · chapters/60-admin/a-auth.md:206 · chapters/60-admin/c-tools.md:780 |
| `V10-15` | 저장 전 배점 합 검사 | run | `validate/v10_admin.py:62` | guide/03_이력.md:103 · chapters/60-admin/c-tools.md:781 |
| `V10-16` | must_change_secret 계정이 다른 화면에 접근 못 함 | run | `validate/v10_admin.py:65` | guide/03_이력.md:203 · chapters/60-admin/a-auth.md:59 · chapters/60-admin/c-tools.md:782 |
| `V10-17` | admin 수가 0 이 되는 변경이 거부됨 | run | `validate/v10_admin.py:70` | guide/03_이력.md:166 · guide/03_이력.md:203 · chapters/61-web.md:1870 |
| `V10-18` | core_pii · core_dealer_pii 조회가 거부됨 | run | `validate/v10_admin.py:75` | guide/03_이력.md:200 · chapters/60-admin/c-tools.md:73 · chapters/60-admin/c-tools.md:784 |
| `V10-19` | 중지·비밀번호 변경 후 옛 세션이 anonymous | run | `validate/v10_admin.py:80` | guide/03_이력.md:204 · chapters/60-admin/a-auth.md:79 · chapters/60-admin/c-tools.md:785 |
| `V10-20` | 연속 로그인 실패 상한을 넘으면 거부됨 | run | `validate/v10_admin.py:104` | ref/B-config.md:386 · guide/03_이력.md:205 · chapters/00-standard.md:696 |
| `V10-22` | queued 를 소비하는 코드가 있음 | run | `validate/v10_admin.py:86` | guide/03_이력.md:268 · chapters/60-admin/b-ops.md:295 · chapters/60-admin/c-tools.md:787 |
| `V10-23` | 오래된 queued 가 화면에 표시됨 | run | `validate/v10_admin.py:91` | guide/03_이력.md:268 · chapters/60-admin/b-ops.md:296 · chapters/60-admin/c-tools.md:788 |
| `V10-24` | 사전 확정에 사유가 남음 | run | `validate/v10_admin.py:96` | guide/03_이력.md:274 · chapters/60-admin/c-tools.md:530 · chapters/60-admin/c-tools.md:789 |
| `V10-25` | 'list' 출처가 화면에 표시됨 | run | `validate/v10_admin.py:100` | guide/03_이력.md:274 · chapters/60-admin/c-tools.md:531 · chapters/60-admin/c-tools.md:790 |
| `V11-01` | web/ 에 SQL 문자열이 없음 | run | `validate/v11_web.py:35` | guide/03_이력.md:149 · chapters/61-web.md:28 · chapters/61-web.md:1439 |
| `V11-02` | 기본 바인딩이 127.0.0.1 | run | `validate/v11_web.py:38` | chapters/61-web.md:99 · chapters/61-web.md:1937 · chapters/61-web.md:2006 |
| `V11-03` | 전 Route 에 role 이 지정됨 | run | `validate/v11_web.py:42` | chapters/61-web.md:167 · chapters/61-web.md:2007 |
| `V11-04` | 템플릿에 산술 연산이 없음 | run | `validate/v11_web.py:44` | chapters/61-web.md:246 · chapters/61-web.md:1982 · chapters/61-web.md:2008 |
| `V11-05` | {{! }} 사용처가 화이트리스트에 있음 | run | `validate/v11_web.py:47` | chapters/61-web.md:263 · chapters/61-web.md:2009 |
| `V11-06` | 정적 경로 탈출이 거부됨 | run | `validate/v11_web.py:52` | chapters/61-web.md:368 · chapters/61-web.md:2010 |
| `V11-07` | 쿠키에 role 문자열이 없음 | run | `validate/v11_web.py:54` | chapters/61-web.md:1238 · chapters/61-web.md:2011 |
| `V11-08` | 상태 변경이 GET 경로에 없음 | run | `validate/v11_web.py:56` | chapters/61-web.md:1274 · chapters/61-web.md:2012 |
| `V11-09` | 미리보기 없이 저장이 안 됨 | run | `validate/v11_web.py:59` | chapters/61-web.md:1302 · chapters/61-web.md:1790 · chapters/61-web.md:2013 |
| `V11-10` | 오류 화면에 스택 트레이스가 없음 | run | `validate/v11_web.py:61` | chapters/61-web.md:1336 · chapters/61-web.md:2014 |
| `V11-11` | result_* 가 비었을 때 안내가 나옴 | run | `validate/v11_web.py:65` | chapters/61-web.md:1365 · chapters/61-web.md:2015 |
| `V11-12` | 라우팅 표의 view 가 10·13장에 실재함 | run | `validate/v11_web.py:162` | guide/03_이력.md:179 · guide/03_이력.md:260 · guide/03_이력.md:265 |
| `V11-13` | app.css 에 토큰 밖의 색값이 없음 | run | `validate/v11_web.py:88` | guide/03_이력.md:202 · guide/03_이력.md:218 · chapters/61-web.md:411 |
| `V11-14` | 숫자 셀에 mono 가 걸려 있음 | run | `validate/v11_web.py:91` | chapters/61-web.md:443 · chapters/61-web.md:2018 |
| `V11-15` | 화면이 빌드 산출물에 의존하지 않음 | run | `validate/v11_web.py:94` | chapters/61-web.md:1181 · chapters/61-web.md:2019 |
| `V11-16` | /why 가 전 Component 를 냄 | run | `validate/v11_web.py:97` | chapters/61-web.md:1387 · chapters/61-web.md:1462 · chapters/61-web.md:2020 |
| `V11-17` | /why 가 조회 상태 절을 냄 | run | `validate/v11_web.py:100` | chapters/61-web.md:1462 · chapters/61-web.md:1516 · chapters/61-web.md:2021 |
| `V11-18` | 축 태그가 전건 필터 링크임 | run | `validate/v11_web.py:103` | chapters/61-web.md:1560 · chapters/61-web.md:2022 |
| `V11-19` | 폴링 실패 시 화면이 안 깨짐 | run | `validate/v11_web.py:106` | chapters/61-web.md:1580 · chapters/61-web.md:2023 |
| `V11-20` | 분모 표시가 있음 | run | `validate/v11_web.py:109` | guide/03_이력.md:225 · chapters/61-web.md:1606 · chapters/61-web.md:2024 |
| `V11-21` | 행동 요청 파라미터가 현재 필터와 일치 | run | `validate/v11_web.py:112` | chapters/61-web.md:1660 · chapters/61-web.md:2025 |
| `V11-22` | excluded 축이 「—/N」 으로 표시됨 | run | `validate/v11_web.py:115` | chapters/61-web.md:1702 · chapters/61-web.md:2026 |
| `V11-23` | 비로그인 관심 POST 가 유도 화면을 냄 | run | `validate/v11_web.py:118` | guide/03_이력.md:226 · chapters/61-web.md:1733 · chapters/61-web.md:2027 |
| `V11-24` | 메뉴 분류가 잠금 단위와 일치 | run | `validate/v11_web.py:121` | chapters/61-web.md:1764 · chapters/61-web.md:2028 |
| `V11-25` | 사유 없이 설정이 저장되지 않음 | run | `validate/v11_web.py:124` | chapters/61-web.md:1790 · chapters/61-web.md:2029 |
| `V11-26` | 되돌릴 수 없는 행동에 확인이 있음 | run | `validate/v11_web.py:127` | chapters/61-web.md:1834 · chapters/61-web.md:2030 |
| `V11-27` | 가입 정책에 따라 화면이 바뀜 | run | `validate/v11_web.py:130` | chapters/61-web.md:1891 · chapters/61-web.md:2031 |
| `V11-28` | 응답 헤더에 비 ASCII 없음 | run | `validate/v11_web.py:68` | guide/03_이력.md:176 · chapters/61-web.md:1315 · chapters/61-web.md:2032 |
| `V11-29` | 렌더된 폼의 csrf_token 이 비어 있지 않음 | run | `validate/v11_web.py:72` | guide/03_이력.md:177 · chapters/61-web.md:353 · chapters/61-web.md:2033 |
| `V11-30` | 시안 ↔ 템플릿 대조 통과 | run | `validate/v11_web.py:76` | guide/03_이력.md:178 · chapters/61-web.md:308 · chapters/61-web.md:1415 |
| `V11-31` | must_change_secret=1 에서 /password 가 200 | run | `validate/v11_web.py:79` | chapters/61-web.md:1259 · chapters/61-web.md:2035 |
| `V11-32` | known_issues 의 키가 전부 targets 에 있음 | run | `validate/v11_web.py:84` | ref/B-config.md:369 · guide/03_이력.md:184 · chapters/61-web.md:2036 |
| `V11-33` | POST 가 저장 없이 성공 메시지를 내지 않음 | run | `validate/v11_web.py:133` | guide/03_이력.md:208 · chapters/61-web.md:1915 · chapters/61-web.md:2037 |
| `V11-34` | 화면이 요청당 쿼리 상한을 넘지 않음 | run | `validate/v11_web.py:139` | guide/03_이력.md:207 · chapters/00-standard.md:160 · chapters/00-standard.md:694 |
| `V11-35` | 중첩 if 가 안쪽부터 닫힘 | run | `validate/v11_web.py:136` | guide/03_이력.md:221 · chapters/61-web.md:1214 · chapters/61-web.md:2039 |
| `V11-36` | 잘못된 쿼리 파라미터가 500 을 내지 않음 | run | `validate/v11_web.py:143` | guide/03_이력.md:223 · chapters/61-web.md:1223 · chapters/61-web.md:2040 |
| `V11-37` | POST 가 예상 밖 500 을 내지 않음 | run | `validate/v11_web.py:147` | — |
| `V11-38` | 템플릿이 쓰는 값을 뷰가 넘김 | run | `validate/v11_web.py:152` | — |
| `V11-39` | 저장 단추가 실제로 저장함 | run | `validate/v11_web.py:157` | — |
| `V11-40` | 반입분의 origin 이 'import' 임 | run | `validate/v11_web.py:165` | guide/03_이력.md:251 · guide/03_이력.md:259 · chapters/61-web.md:2041 |
| `V11-41` | 반입 뒤 S5~S10 이 이어서 돎 | run | `validate/v11_web.py:170` | guide/03_이력.md:251 · chapters/61-web.md:2042 · chapters/60-admin/c-tools.md:205 |
| `V11-42` | S4 완료 행의 actual 이 'import' 임 | run | `validate/v11_web.py:347` | guide/03_이력.md:252 · chapters/61-web.md:2043 · chapters/60-admin/c-tools.md:287 |
| `V11-43` | 브라우저 수집분의 origin 이 'browser' 임 | run | `validate/v11_web.py:175` | guide/03_이력.md:256 · guide/03_이력.md:259 · chapters/61-web.md:2044 |
| `V11-44` | 사람 확인 없이 저장되지 않음 | run | `validate/v11_web.py:180` | guide/03_이력.md:256 · chapters/61-web.md:2045 · chapters/60-admin/c-tools.md:338 |
| `V11-45` | — | — | **★ 코드에 없다** | guide/03_이력.md:257 · chapters/00-standard.md:142 · chapters/61-web.md:2046 |
| `V11-46` | 반입으로 연 단계의 actual 이 'import' 임 | run | `validate/v11_web.py:342` | guide/03_이력.md:266 · chapters/13-pipeline.md:184 · chapters/61-web.md:2047 |
| `V11-47` | 브라우저 수집이 한 번에 max_form_bytes 를 넘기지 않음 | run | `validate/v11_web.py:328` | ref/B-config.md:391 · guide/03_이력.md:270 · chapters/61-web.md:2048 |
| `V11-48` | 전 차종 수집에 확인 절차가 있음 | run | `validate/v11_web.py:334` | guide/03_이력.md:271 · chapters/61-web.md:2049 · chapters/60-admin/c-tools.md:414 |
| `V11-49` | 한 차종 실패가 나머지를 멈추지 않음 | run | `validate/v11_web.py:338` | guide/03_이력.md:271 · chapters/61-web.md:2050 · chapters/60-admin/c-tools.md:415 |
| `V11-51` | 진행 화면이 스스로 갱신됨 | run | `validate/v11_web.py:320` | guide/03_이력.md:279 · chapters/61-web.md:2051 · chapters/60-admin/c-tools.md:606 |
| `V11-52` | 진행 화면에 실행 단추가 없음 | run | `validate/v11_web.py:324` | guide/03_이력.md:279 · chapters/61-web.md:2052 · chapters/60-admin/c-tools.md:607 |
| `V11-53` | 진행 판정이 큐만 보지 않음 | run | `validate/v11_web.py:185` | guide/03_이력.md:280 · chapters/61-web.md:2053 · chapters/60-admin/c-tools.md:608 |
| `V11-54` | 메뉴에 경로가 그대로 나오지 않음 | run | `validate/v11_web.py:191` | guide/03_이력.md:281 · chapters/61-web.md:2054 |
| `V11-55` | 목록에 전체 건수와 쪽이 표시됨 | run | `validate/v11_web.py:196` | chapters/61-web.md:2055 |
| `V11-56` | 대표 사진 경로가 저장됨 | run | `validate/v11_web.py:201` | chapters/61-web.md:504 · chapters/61-web.md:2056 |
| `V11-57` | 사진 없는 매물이 화면을 무너뜨리지 않음 | run | `validate/v11_web.py:205` | guide/03_이력.md:281 · chapters/61-web.md:505 · chapters/61-web.md:2057 |
| `V11-58` | 쪽을 넘겨도 조건이 남음 | run | `validate/v11_web.py:210` | — |
| `V11-59` | 시안의 클래스가 CSS 에 있음 | run | `validate/v11_web.py:214` | guide/03_이력.md:282 · chapters/61-web.md:536 · chapters/61-web.md:2058 |
| `V11-60` | 시안 CSS 를 다시 만들지 않음 | run | `validate/v11_web.py:218` | guide/03_이력.md:282 · chapters/61-web.md:537 · chapters/61-web.md:2059 |
| `V11-61` | 이어질 수 있는 값이 링크임 | run | `validate/v11_web.py:222` | guide/03_이력.md:283 · chapters/61-web.md:1082 · chapters/61-web.md:2060 |
| `V11-62` | 코드·줄임말에 title 이 있음 | run | `validate/v11_web.py:226` | chapters/61-web.md:1083 · chapters/61-web.md:2061 |
| `V11-63` | 매물 화면에 원문 링크가 있음 | run | `validate/v11_web.py:230` | chapters/61-web.md:1099 · chapters/61-web.md:2062 |
| `V11-64` | 고를 수 있는 값이 목록으로 제공됨 | run | `validate/v11_web.py:234` | chapters/61-web.md:1121 · chapters/61-web.md:2063 |
| `V11-65` | 기본 정렬이 규격대로임 | run | `validate/v11_web.py:239` | chapters/61-web.md:1142 · chapters/61-web.md:2064 |
| `V11-66` | 필터가 목록 위에 있음 | run | `validate/v11_web.py:243` | chapters/61-web.md:1163 · chapters/61-web.md:2065 |
| `V11-67` | 단추가 켜짐·꺼짐을 오감 | run | `validate/v11_web.py:246` | guide/03_이력.md:283 · chapters/61-web.md:1164 · chapters/61-web.md:2066 |
| `V11-68` | v1 이 낸 열이 v2 에도 있음 | run | `validate/v11_web.py:250` | guide/03_이력.md:284 · chapters/61-web.md:597 · chapters/61-web.md:2067 |
| `V11-69` | v1 이 가진 조작이 v2 에도 있음 | run | `validate/v11_web.py:255` | guide/03_이력.md:284 · chapters/61-web.md:598 · chapters/61-web.md:2068 |
| `V11-70` | 좁은 폭에서 값이 사라지지 않음 | run | `validate/v11_web.py:260` | guide/03_이력.md:285 · chapters/61-web.md:993 · chapters/61-web.md:2069 |
| `V11-71` | 가로 스크롤로 떠넘기지 않음 | run | `validate/v11_web.py:265` | guide/03_이력.md:285 · chapters/61-web.md:994 · chapters/61-web.md:2070 |
| `V11-72` | 빈 주소로 가는 링크가 없음 | run | `validate/v11_web.py:269` | — |
| `V11-73` | 화면마다 값이 나옴 | run | `validate/v11_web.py:308` | — |
| `V11-74` | 숫자가 단위와 함께 나옴 | run | `validate/v11_web.py:311` | — |
| `V11-75` | 링크가 유효함 | run | `validate/v11_web.py:314` | — |
| `V11-76` | 화면 크기·시간이 상한 안 | run | `validate/v11_web.py:317` | — |
| `V11-77` | 시안의 시각 요소가 렌더 결과에 나옴 | run | `validate/v11_web.py:274` | — |
| `V11-78` | 좁은 폭에서 글자가 세로로 안 떨어짐 | run | `validate/v11_web.py:280` | — |
| `V11-79` | 축 칸에 맨 숫자가 나오지 않음 | run | `validate/v11_web.py:294` | guide/03_이력.md:287 · chapters/61-web.md:712 · chapters/61-web.md:2071 |
| `V11-80` | 사진이 최소 크기 이상 | run | `validate/v11_web.py:299` | guide/03_이력.md:288 · chapters/61-web.md:767 · chapters/61-web.md:2072 |
| `V11-81` | 신차가 · 시세 · 가격 셋이 함께 나옴 | run | `validate/v11_web.py:303` | guide/03_이력.md:290 · chapters/61-web.md:795 · chapters/61-web.md:2073 |
| `V11-82` | 정적 파일에 버전이 붙음 | run | `validate/v11_web.py:289` | — |
| `V11-85` | — | — | **★ 코드에 없다** | guide/03_이력.md:292 · chapters/61-web.md:838 · chapters/61-web.md:2079 |
| `V11-87` | — | — | **★ 코드에 없다** | guide/03_이력.md:293 · chapters/61-web.md:921 · chapters/61-web.md:2081 |
| `V11-88` | — | — | **★ 코드에 없다** | guide/03_이력.md:295 · chapters/61-web.md:886 · chapters/61-web.md:2082 |
| `V11-92` | 신차가가 등급기준 + 옵션 합 | run | `validate/v11_web.py:285` | guide/03_이력.md:308 · chapters/30-score/a-frame.md:736 |
| `V11-93` | — | — | **★ 코드에 없다** | guide/03_이력.md:310 · chapters/61-web.md:633 · chapters/61-web.md:2074 |
| `V11-94` | — | — | **★ 코드에 없다** | guide/03_이력.md:311 · chapters/61-web.md:666 · chapters/61-web.md:2075 |
| `V11-96` | — | — | **★ 코드에 없다** | guide/03_이력.md:312 · chapters/61-web.md:688 · chapters/61-web.md:2077 |

## ★ 규격이 요구했는데 코드에 없는 검사

- `V1-22` — guide/03_이력.md:303 · chapters/30-score/a-frame.md:641
- `V11-45` — guide/03_이력.md:257 · chapters/00-standard.md:142 · chapters/61-web.md:2046
- `V11-85` — guide/03_이력.md:292 · chapters/61-web.md:838 · chapters/61-web.md:2079
- `V11-87` — guide/03_이력.md:293 · chapters/61-web.md:921 · chapters/61-web.md:2081
- `V11-88` — guide/03_이력.md:295 · chapters/61-web.md:886 · chapters/61-web.md:2082
- `V11-93` — guide/03_이력.md:310 · chapters/61-web.md:633 · chapters/61-web.md:2074
- `V11-94` — guide/03_이력.md:311 · chapters/61-web.md:666 · chapters/61-web.md:2075
- `V11-96` — guide/03_이력.md:312 · chapters/61-web.md:688 · chapters/61-web.md:2077
- `V2-03` — chapters/11-store/a-key.md:339 · chapters/20-verify/b-v1v2.md:99
- `V3-42` — guide/03_이력.md:297 · chapters/30-score/a-frame.md:309 · chapters/20-verify/c-v3v4.md:94
- `V3-44` — guide/03_이력.md:298 · chapters/30-score/a-frame.md:354 · chapters/20-verify/c-v3v4.md:96
- `V3-49` — guide/03_이력.md:301 · chapters/30-score/d-history.md:331 · chapters/20-verify/c-v3v4.md:101
- `V3-50` — guide/03_이력.md:302 · chapters/30-score/d-history.md:358 · chapters/20-verify/c-v3v4.md:102
- `V6-01` — chapters/41-view.md:669 · chapters/61-web.md:328

## 코드에 있는데 규격에 안 적힌 검사

- `S28` 검사 색인 (규격 ↔ 코드) — `tools/check_src.py`
- `V1-19` 이번 실행이 저장한 원문에 run_id 가 있음 — `validate/v1_collect.py`
- `V1-20` 카탈로그를 모델당 1회만 받음 — `validate/v1_collect.py`
- `V11-37` POST 가 예상 밖 500 을 내지 않음 — `validate/v11_web.py`
- `V11-38` 템플릿이 쓰는 값을 뷰가 넘김 — `validate/v11_web.py`
- `V11-39` 저장 단추가 실제로 저장함 — `validate/v11_web.py`
- `V11-58` 쪽을 넘겨도 조건이 남음 — `validate/v11_web.py`
- `V11-72` 빈 주소로 가는 링크가 없음 — `validate/v11_web.py`
- `V11-73` 화면마다 값이 나옴 — `validate/v11_web.py`
- `V11-74` 숫자가 단위와 함께 나옴 — `validate/v11_web.py`
- `V11-75` 링크가 유효함 — `validate/v11_web.py`
- `V11-76` 화면 크기·시간이 상한 안 — `validate/v11_web.py`
- `V11-77` 시안의 시각 요소가 렌더 결과에 나옴 — `validate/v11_web.py`
- `V11-78` 좁은 폭에서 글자가 세로로 안 떨어짐 — `validate/v11_web.py`
- `V11-82` 정적 파일에 버전이 붙음 — `validate/v11_web.py`
