# 소스 색인

**`python3.11 tools/build_index.py` 가 만든다. 손으로 고치지 않는다.**

파일 209개 · 총 75,835줄

| 파일 | 줄 | 무엇 |
|---|--:|---|
| `validate/v0_guide.py` | 6,272 | 가이드 문서 자체를 검사한다 (V0 계열). |
| `validate/v11_web.py` | 5,057 | V11 표현 계층 검증 (14장 STEP 153). |
| `report/screens/build.py` | 4,440 | 화면 데이터 생성. |
| `web/views.py` | 2,842 | 화면 어댑터 (14장 STEP 142 · 152). |
| `validate/v3_logic.py` | 2,329 | V3 로직 검증 — 판정이 작동하는가 · 변별력이 있는가. |
| `store/core.py` | 2,001 | CORE 저장소 (L4).  사이트 무관 공통 스키마. |
| `collect/runner.py` | 1,857 | 수집 실행 규칙. |
| `tests/test_spec_ui.py` | 1,494 | 규격 기준 통합 테스트 (통합테스트_시나리오_규격기준.md). |
| `tests/test_integration.py` | 1,275 | 통합 테스트 — 실제 HTTP 로 전 화면 (통합테스트_시나리오.md). |
| `tools/check_src.py` | 1,156 | CarWatch v2 — 지시서 ↔ 소스 대조 검증기. |
| `report/screens/admin.py` | 1,091 | 관리자 화면 — 표현 계층 (13장 STEP 138 · 138a). |
| `tools/verify_axes.py` | 1,084 | 손계산 대조 — 축마다 표본 3건 (개정 329 전수검증 · V3-66). |
| `store/adminops.py` | 1,057 | 관리자 서버 계층 — 실행 지시 · 쿼리 · API 조회 · 개발 요청 · 미리보기. |
| `report/render.py` | 1,037 | 리포트 생성 (L9). |
| `validate/v10_admin.py` | 934 | V10 관리자 검증. |
| `tests/test_score.py` | 928 | 7장 판정·채점 시험. |
| `validate/v2_load.py` | 919 | V2 적재 검증 — 옮겨졌는가 · 전일 대비 변동이 타당한가. |
| `validate/v1_collect.py` | 910 | V1 수집 검증 — 다 받았는가 · 라벨이 맞는가. |
| `report/screens/views.py` | 898 | 화면 전용 DTO. |
| `tools/trace_fill.py` | 840 | 추적표의 소스 · 화면 · 검사 칸을 기계로 채운다 (`inbox/ORDER_00_trace_fill.md`). |
| `validate/v4_mapping.py` | 785 | V4 매핑 검증 — 이름이 아니라 값으로 검증한다. |
| `tests/test_run.py` | 783 | S0~S3 종단 시험 (모의 응답). |
| `collect/pipeline.py` | 775 | 실행 순서 · 중단 · 재처리 · 재개. |
| `store/watch.py` | 746 | 후보 추적 (11장). |
| `store/admin.py` | 716 | 관리자 — 계정 · 권한 · config 변경 (13장 앞부분). |
| `tools/backfill_from_raw.py` | 663 | ★★★★★ 08-30 (명령서 r974 · 0j 4) — ★ Ⓐ 「이미 오는 것을 읽는다」. |
| `parse/encar/mapping.py` | 625 | 엔카 원문 → CORE 필드 (L3). |
| `store/raw.py` | 617 | RAW 저장소 (L2).  원문 무손실.  삭제 금지. |
| `tools/collect_kbchachacha.py` | 602 | KB차차차 목록 수집 · 총 매물 수 세기 (명령서 `ORDER_20260822_r515.md` 3-2 · 단계 9). |
| `store/dictionary.py` | 591 | 사전 저장소 (L5).  RAW 에서 생성한다. |
| `tests/test_admin_flow.py` | 575 | 관리 화면 동작 시험 (13장 · 14장). |
| `tests/test_admin.py` | 567 | 13장 앞부분 시험 — 계정 · 권한 · config 변경. |
| `tools/check_spec.py` | 557 | CarWatch v2 지시서 자체 점검 — 7종 |
| `web/app.py` | 547 | 화면 조립 (14장 STEP 144 · 147 · 149). |
| `tools/build_index.py` | 536 | 검사 색인 · 소스 색인을 만든다 (규칙 11). |
| `tests/test_web.py` | 522 | 14장 표현 계층 시험 — 템플릿 · 라우팅. |
| `contracts.py` | 481 | 계층 간 계약 — Protocol · DTO. |
| `run.py` | 421 | CarWatch v2 진입점. |
| `report/views.py` | 419 | 리포트 DTO (L9). |
| `web/template.py` | 406 | 최소 템플릿 엔진 (14장 STEP 143). |
| `tests/test_collect.py` | 401 | 2장 수집 시험. |
| `tools/sync_registry.py` | 394 | RAW 경로 전수 → meta_field_usage. |
| `tests/test_pipeline.py` | 388 | 5장 수집 순서 시험. |
| `parse/hyundai_cert/mapping.py` | 374 | 현대·제네시스 인증중고차 목록 카드 → CORE 필드 (L3). |
| `tools/browser_diff.py` | 362 | ★★★★★ 09-01 마스터 지시 — ★ **브라우저로 시안과 화면을 대조한다.** |
| `analyze/axis/state.py` | 355 | ② 상태 150 — 차가 성한가 (docs/ref/F-scoring.md ②). |
| `tools/collect_hyundai_cert.py` | 351 | 현대·제네시스 인증중고차 목록 수집 (명령서 `ORDER_20260822_r515.md` 3장 · 단계 11). |
| `parse/heydealer/mapping.py` | 341 | 헤이딜러 원문 → `core_listing` (명령서 37-3 ② · `docs/HEYDEALER_API.md`). |
| `tools/light_check.py` | 340 | 가벼운 점검 — 4시간마다 (개정 335 · S29-0). |
| `tools/build_dict.py` | 336 | RAW → 사전 생성. |
| `parse/kcar/mapping.py` | 333 | K카 상세 → `core_listing` (`docs/KCAR_API.md` 3장 · `MULTISITE_MAPPING.md` 1장). |
| `tools/render_screens.py` | 331 | 전 화면을 실제로 렌더해 `outputs/render/` 에 남긴다. |
| `tools/load_raw.py` | 327 | 넣기 걸음 — ★ **파일 폴더를 읽어 `raw_response` ＋ `core_listing` 에 넣는다.** |
| `validate/v7_watch.py` | 320 | V7 관심·추적 검증. |
| `validate/v9_multisite.py` | 311 | V9 — 다중 사이트 (`docs/chapters/50-multisite.md`). |
| `tests/test_dict.py` | 293 | 4장 키·코드·사전 시험. |
| `tests/test_screens.py` | 292 | 10장 화면 시험. |
| `store/crosssite.py` | 291 | 다중 사이트 확장 (12장). |
| `tests/test_endtoend.py` | 291 | 종단 시험 — 수집부터 리포트까지 (5장 STEP 47 · 49). |
| `adapters/encar.py` | 290 | 엔카 어댑터 — URL · 헤더 · 쿼리 조립. |
| `tools/check_screens.py` | 285 | 화면 ↔ 시안 대조 (10장 · 14장). |
| `tests/test_fixtures.py` | 284 | 실물 표본 시험 — v1 원문 12건. |
| `tests/test_crosssite.py` | 282 | 12장 다중 사이트 시험. |
| `parse/kbchachacha/mapping.py` | 277 | KB차차차 상세 → `core_listing` (`docs/KBCHACHACHA_API.md` 3장). |
| `tests/test_store.py` | 270 | 3장 테이블 시험. |
| `report/exports/export.py` | 269 | 내보내기. |
| `web/server.py` | 266 | HTTP 서버 (14장 STEP 141 · 150). |
| `tests/test_report.py` | 263 | 9장 리포트 시험. |
| `parse/revolt/mapping.py` | 260 | 리볼트 (revolt.kr) — 전기차 전용 인증중고차 (규격 `docs/REVOLT_API.md` · `S46-200`). |
| `parse/reborncar/mapping.py` | 259 | 리본카 상세 → `core_listing` (명령서 39 · `docs/REBORNCAR_API.md` 1b). |
| `tests/test_watch.py` | 259 | 11장 후보 추적 시험. |
| `tools/collect_kcar.py` | 254 | K카 상세 수집 (명령서 `ORDER_20260822_r515.md` 3-3 · 단계 10). |
| `tools/menu.py` | 254 | 실행 메뉴. |
| `validate/v5_value.py` | 254 | V5 수치 검증 — 기준값이 맞는가 · 보정이 타당한가. |
| `parse/volvo_selekt/mapping.py` | 251 | 볼보 셀렉트 상세 → `core_listing` 칸 (규격 `VOLVO_SELEKT_API.md` 2장). |
| `analyze/axis/taste.py` | 248 | ④ 취향 50점 — HUD 15 · 선루프 10 · 색상 10 · 지정 옵션 15. |
| `tests/test_registry.py` | 245 | 8장 등록부 시험. |
| `tools/collect_volvo.py` | 245 | 볼보 셀렉트 수집 — xhr-results 쪽넘김 (명령서 1a). |
| `tools/undo_wrong_gone.py` | 243 | ★★★★★ 잘못 매긴 `gone` 을 되돌린다 (마스터 0a·0c · 08-30). |
| `analyze/axis/site.py` | 240 | ⑤ 사이트 보증 50 · ⑦ 제조사 보증 50 (일반 20 + 동력계 30). |
| `tests/test_invariants.py` | 239 | 불변식 시험. |
| `tools/collect_reborncar.py` | 230 | 리본카 수집 — 사이트맵 전량 → 우리 쪽에서 거른다 (명령서 39). |
| `tools/repair_facet_chunks.py` | 222 | 낱개로 저장된 facet 조각을 이어붙인다 (개정 307 사고 복구). |
| `tools/collect_bobaedream.py` | 220 | 보배드림 수집 (명령서 7단계 · `docs/BOBAEDREAM_API.md`). |
| `score/scorer.py` | 218 | 채점 · 분모 (L7). |
| `tools/collect_revolt.py` | 215 | 리볼트 수집 (규격 `docs/REVOLT_API.md` · 마스터 확정 09-01 · `S46-200`). |
| `web/context.py` | 213 | 화면 문맥과 오류 (14장 STEP 144 · 148). |
| `validate/base.py` | 212 | 검증 계약. |
| `tools/unknown_split.py` | 210 | 「확인 안 됨」을 ①②③④ 로 가른다 (개정 434 · 435 · V1-27 · V1-28). |
| `tests/seed.py` | 204 | 시험용 씨앗 DB — 운영 DB 를 복사하지 않는다. |
| `tools/migrate.py` | 203 | 스키마 이행 — 기존 DB 를 현재 DDL 에 맞춘다. |
| `parse/bobaedream/mapping.py` | 196 | 보배드림 상세 → `core_listing` (`docs/BOBAEDREAM_API.md` 2·3·1a장). |
| `score/penalty.py` | 196 | 마이너스 점수 (개정 322). |
| `parse/lexus_certified/mapping.py` | 195 | 렉서스 인증중고 목록·상세 → `core_listing` 칸 (규격 `LEXUS_CERTIFIED_API.md` 2장). |
| `tools/collect_heydealer.py` | 186 | 헤이딜러 수집 — 토큰 → 차종별 목록 → 상세 (명령서 37). |
| `parse/kbchachacha/inspection.py` | 183 | KB차차차 성능점검부 → ★ **부위별** (규격 `KBCHACHACHA_API.md` 3장 · 268~269줄). |
| `parse/importer.py` | 182 | 반입 입력 해석 (13장 STEP 136a · 136b). |
| `tools/list_diff_check.py` | 182 | 목록 대조 — ★ **사라진 것은 상세로 확인한 뒤에 죽인다.** |
| `analyze/axis/value.py` | 181 | ① 값 250 — 시세 대비 100 · 신차가 대비 80 · 주행 대비 70. |
| `collect/worker.py` | 180 | 큐 소비기 (13장 STEP 132a · 개정 261). |
| `tools/run_tests.py` | 180 | 시험 전체 실행. |
| `tools/measure_0k.py` | 176 | ★ 0k (명령서 r974 뒤) — ★ **잰다.  안 고친다.** |
| `parse/bmw_bps/mapping.py` | 175 | BMW BPS 상세 파서 (`docs/BMW_BPS_API.md` 08-29 절). |
| `tools/classify_unclassified.py` | 175 | 미분류 경로를 원인별로 가른다 (개정 341 · V4-26 · V4-27). |
| `web/session.py` | 175 | 세션 · CSRF · 정적 파일 (14장 STEP 145~147). |
| `analyze/axis/spec.py` | 172 | 사양 90점 — HUD 20 · 선루프 20 · SVM 10 · SCC 10 · 후측방 5 · 틴팅 5. |
| `tools/sync_target_map.py` | 172 | 차종 대응표 → `dict_enum` (명령서 `ORDER_20260822_r515.md` 2a장 · 개정 540). |
| `tools/collect_lexus.py` | 171 | 렉서스 인증중고 수집 (명령서 1a). |
| `tools/daily_check.py` | 170 | 일일 점검 — 매일 23:00 (개정 334 · S29). |
| `store/pii.py` | 169 | 개인정보 분리 (L4). |
| `tools/collect_kia_cpo.py` | 169 | 기아 인증중고차(CPO) 목록 수집 (명령서 `ORDER_20260822_r515.md` 3-1 · 단계 8). |
| `tools/weekly_check.py` | 163 | 주간 일제 점검 — 금 02:00 · 개발측 몫 (개정 334 · S29). |
| `adapters/kbchachacha.py` | 161 | KB차차차 어댑터 — URL · 헤더 (1장 STEP 11). |
| `tools/collect_bmw.py` | 161 | BMW 바바리안(BPS) 수집 (명령서 1a). |
| `tools/measure_axis_gap.py` | 161 | ★ 3 — ★ 짝이 245 인데 ★ 아홉 사이트 A 가 0 인 까닭을 ★ **잰다**. |
| `tools/refetch_unsourced.py` | 160 | ★★★★★ 찌꺼기를 끊고 ★ 근거 없는 행의 상세를 다시 받는다 (마스터 0e · 08-30). |
| `tools/site_coverage.py` | 160 | 사이트에 몇 대인데 ★ 우리가 몇 대 받았나 — ★ 이걸 아무도 안 셌다. |
| `score/adjust.py` | 157 | 배점 조정 — 비율 재배분과 정수 보정. |
| `report/finance.py` | 156 | 금융 — 점수가 아니라 비용이다. |
| `tools/fetch_missing_catalog.py` | 156 | ★★★★★ 08-31 (로드맵 차례 5 · `V1-23`) — ★ **안 부른 카탈로그를 받는다.** |
| `tools/compress_raw.py` | 155 | 원문(raw_response.body)을 눌러 둔다 (마스터 지시 2026-08-28). |
| `tools/daily_enqueue.py` | 153 | 하루 한 번 스스로 돈다 (STEP 136h · 개정 315). |
| `web/routes.py` | 152 | 라우팅 표 (14장 STEP 142). |
| `store/rawfile.py` | 149 | 1걸음 — ★ **받은 것을 파일로만 쓴다.  ★ DB 를 안 연다.** |
| `tools/classify_registry.py` | 144 | 등록부 미분류 정리 — 근거가 있는 것만 (8장 STEP 87 · V4-11). |
| `analyze/axis/history.py` | 143 | ③ 이력 80 — 어떻게 쓰였나 (docs/ref/F-scoring.md ③). |
| `tools/classify_fields.py` | 139 | 등록부 분류 초안 — 파서가 쓰는 경로를 근거로 자동 분류한다. |
| `tools/check_all.py` | 137 | 실측 DB 회귀 — V1~V5 · V10 전건을 한 번에 돌린다. |
| `tools/fold_out_of_scope.py` | 137 | 이미 들어온 것을 ★ 되돌린다 — ★ 우리 대상이 아닌 것은 ★ 접는다 (명령서 3-3). |
| `parse/classify.py` | 136 | 분류 2단 — target_key 판정. |
| `tools/trace_verify.py` | 136 | 추적표 「상태」를 사실로 (개정 349 · 350 · S34). |
| `tools/fetch_dimensions.py` | 134 | ★★★★★ 제원(전장)을 ★ **브라우저로** 받는다 — 명령서 10번 (`S46-233`). |
| `tools/browser_verify.py` | 129 | ★★★★★ 09-02 — ★ **배포를 브라우저로 확인한다** (`S46-253`). |
| `adapters/heydealer.py` | 127 | 헤이딜러 어댑터 — 토큰 두 걸음 (명령서 37 · `docs/HEYDEALER_API.md` 0장). |
| `score/grade.py` | 127 | 등급 (L7). |
| `analyze/axes.py` | 126 | 축 판정 계약. |
| `tools/recalc_catchup.py` | 126 | 재판정이 밀렸으면 채운다 (명령서 14-3 · 마스터 지시 08-24). |
| `collect/fetcher.py` | 121 | 원문 획득 · 형식 검증. |
| `adapters/kia_cpo.py` | 118 | 기아 인증중고차(CPO) 어댑터 — URL · 헤더 (1장 STEP 11). |
| `parse/kia_cpo/mapping.py` | 118 | 기아 인증중고차(CPO) 원문 → CORE 필드 (L3). |
| `tools/gen_table.py` | 117 | 배점표를 config 에서 생성한다 (개정 512). |
| `adapters/kcar.py` | 115 | K카 어댑터 — URL · 헤더 (12장 · STEP 11). |
| `errors.py` | 115 | 도메인 예외 5종. |
| `tools/raw_lifecycle.py` | 114 | 원문 파일·행의 살림 — ★ 마스터 지시 09-01. |
| `tools/classify_stored.py` | 110 | 저장된 매물을 ★ 갈래에 넣는다 — ★ 사이트 도구가 쓴 줄용 (명령서 37·39). |
| `tools/report_cli.py` | 109 | 리포트 재생성 (9장 STEP 90 · 91a · B-6). |
| `tools/fill_photos.py` | 108 | ★★★ 이미 받아 둔 원문에서 ★ 사진을 채운다 (명령서 73장). |
| `tools/probe_kb_wall.py` | 106 | KB 봇 차단을 ★ 재는 도구 (명령서 08-25 · 마스터 「가려 받지 마라」). |
| `parse/kbchachacha/record.py` | 98 | KB차차차 상세 → `core_record` (명령서 r1007 · 1-5 · 로드맵 차례 1). |
| `tools/daily_collect.py` | 98 | 아홉+한 사이트를 하루 한 번 받는다 (ORDER_20260829 1순위 2 · S46-127). |
| `store/tools.py` | 97 | 관리 도구 (13장 STEP 135). |
| `analyze/verdict.py` | 94 | 판정 엔진 — 순서 무관 put(). |
| `parse/target_rules.py` | 93 | 차종군 + `targets.json` 규칙으로 ★ 갈래를 고른다. |
| `tools/export_cli.py` | 93 | 데이터 내보내기 (9장 STEP 91a · B-6). |
| `tools/link_catalog_key.py` | 92 | ★★★★★ 08-31 (로드맵 차례 2) — ★ `model_catalog_key` 를 아홉 사이트에 잇는다. |
| `tools/setup_check.py` | 92 | 착수 점검 — 실행 전에 무엇이 준비됐는지 한 번에 본다. |
| `analyze/axis/price.py` | 90 | 가격 200점. |
| `analyze/absolute.py` | 88 | E등급 절대조건 10종. |
| `adapters/bobaedream.py` | 87 | 보배드림 어댑터 — URL · 헤더 (1장 STEP 11). |
| `parse/mpark/inspection.py` | 85 | m-park 성능점검 창구 → 우리 꼴 (로드맵 차례 4 · KB 점검표). |
| `analyze/axis/trim.py` | 83 | ④ 사양 45 — 트림 25 · 옵션 20 (docs/ref/F-scoring.md ④). |
| `tools/deploy_check.py` | 81 | 배포 확인 — ★ 「소스가 맞다」와 「마스터 화면이 맞다」는 다른 말이다. |
| `analyze/peer.py` | 80 | 유사군 — 「이런 차가 보통 얼마인가」 (7장 STEP 82e). |
| `report/why_cheap.py` | 80 | 「왜 싼가」 — 싼 이유를 순서대로 찾아 낸다 (개정 299 · V3-52). |
| `store/chunk.py` | 77 | 조각 전송 — 바이트를 나누고 서버가 이어붙인다 (개정 307). |
| `tools/inspect_dict.py` | 75 | 사전 검토 — pending 값과 원문 표본을 본다. |
| `tools/inspect_facet.py` | 74 | facet 원문에 실제로 어떤 축이 왔는지 본다. |
| `analyze/trust.py` | 70 | 플랫폼 신뢰도 — 점검 출처 · 엔카진단 · 엔카보증 (개정 300). |
| `tools/three_numbers.py` | 69 | ★★★★★ 회차마다 낼 세 수 — ★ **화면 기준**으로 센다 (마스터 지시 08-30). |
| `tools/fill_raw_run_id.py` | 65 | 원문에 ★ 빠진 `run_id` 를 채운다 (`V1-19` · A-10 · 개발측 자진 수정). |
| `tools/link_raw_ids.py` | 64 | ★★ 이미 쌓인 원문의 `listing_id` 를 ★ `source_id` 로 이어 채운다. |
| `analyze/curve.py` | 61 | 구간별 점수표 (docs/ref/F-scoring.md). |
| `tools/clear_zero_values.py` | 60 | ★★ 「값이 아닌 0」을 ★ 모름(NULL)으로 되돌린다. |
| `tools/clear_bad_origin.py` | 58 | ★★★★ 「신차가 < 현재값」인 신차가를 지운다 (마스터 지시 2 · 08-30). |
| `analyze/axis/warranty.py` | 56 | 보증 100점 — 일반 50 + 파워트레인 50. |
| `parse/encar/paths.py` | 56 | 파서가 읽는 원문 경로 — 코드에서 뽑는다 (2장 STEP 20). |
| `tools/inspect_requests.py` | 52 | 요청 기록을 본다 — 무엇을 던졌고 무엇이 돌아왔는가. |
| `analyze/axis/_util.py` | 50 | 축 공용 도우미. |
| `analyze/axis/safety.py` | 44 | 안전 40점 — 진단 20 + 보증상품 20. |
| `adapters/base.py` | 36 | 사이트 어댑터 인터페이스. |
| `report/peer.py` | 35 | 유사군 조회 (7장 STEP 82e). |
| `analyze/axis/color.py` | 33 | 색상 축.  ★ 배점은 config/scoring.json (f-table 5장-2a). |
| `analyze/engine.py` | 32 | 판정 실행 (L6).  축 함수를 순서 무관하게 호출한다. |
| `analyze/axis/mileage.py` | 31 | 주행거리 30점. |
| `adapters/__init__.py` | 1 | — |
| `analyze/__init__.py` | 1 | — |
| `analyze/axis/__init__.py` | 1 | — |
| `collect/__init__.py` | 1 | — |
| `parse/__init__.py` | 1 | — |
| `parse/encar/__init__.py` | 1 | — |
| `parse/hyundai_cert/__init__.py` | 1 | — |
| `parse/kia_cpo/__init__.py` | 1 | — |
| `report/__init__.py` | 1 | — |
| `report/exports/__init__.py` | 1 | — |
| `report/screens/__init__.py` | 1 | — |
| `score/__init__.py` | 1 | — |
| `store/__init__.py` | 1 | — |
| `tests/__init__.py` | 1 | — |
| `validate/__init__.py` | 1 | — |
| `parse/bmw_bps/__init__.py` | 0 | — |
| `parse/bobaedream/__init__.py` | 0 | — |
| `parse/heydealer/__init__.py` | 0 | — |
| `parse/kbchachacha/__init__.py` | 0 | — |
| `parse/kcar/__init__.py` | 0 | — |
| `parse/lexus_certified/__init__.py` | 0 | — |
| `parse/mpark/__init__.py` | 0 | — |
| `parse/reborncar/__init__.py` | 0 | — |
| `parse/revolt/__init__.py` | 0 | — |
| `parse/volvo_selekt/__init__.py` | 0 | — |

## 큰 파일 — 무엇이 어디에 (200줄 이상 91개)

### `validate/v0_guide.py` — 6,272줄

```
_read:25  s43_2_axis_ids:32  s44_4_scope_written:70  s44_5_site_consistent:102  s45_1_one_version:135  _order_files:158  s44_1_order_exists:171  s44_2_one_order:213  s43_2b_axis_renamed:228  s43_2c_no_hda:254  s45_5_no_axis_scores:308  s45_4_table_generated:346  s45_3_spec_totals:361  s45_2_mock_numbers:432  s44_3_specs_in_order:453  s43_3_version_matches:491  _h_tags:532  s46_21_one_screen_per_file:548  s46_22_section_order:573  _targets:642  s46_23_site_query_filled:648  s46_24_facet_unconfirmed:663  s46_30_index_covers_docs:683  s46_31_spec_sites_in_config:722  s46_32_generated_fresh:743  _req_rows:785  _tokens:797  _named_docs:812  s46_36_dropped_not_alive:824  s46_40_progress_docs_changed:852  s46_41_site_status_known:883  _templates:925  s46_45_spec_not_in_list:930  s46_46_spec_forbidden_ten:950  s46_66_links_encoded:976  s46_65_verdict_fresh:1015  _sian_files:1053  s46_67_sian_names_dont_clash:1062  s46_68_watch_is_mobile_first:1125  s46_74_rows_per_page:1179  s46_75_v4m_common:1225  s46_76_collectors_keep_raw:1265  s46_115_run_screen_still:1303  s46_125_sort_axes_really_sort:1332  s46_118_heart_has_anchor:1363  s46_121_header_rule_in_one_place:1403  s46_116_reasons_in_plain_words:1425  s46_120_registry_key_matches:1452  s46_123_toss_palette_only:1488  s46_122_shared_fragments:1530  s46_128_batch_gives_a_window:1574  s46_127_collector_has_screen_or_timer:1618  s46_124_db_opened_with_pragmas:1666  s46_126_fetch_outside_transaction:1702  s46_117_collectors_sweep_gone:1736  s46_77_kb_is_our_targets_only:1785  s46_78_encar_only_paths_are_scoped:1841  s46_87_request_site_matches_listing:1883  s46_88_encar_blocked_banner:1952  _paired_rows:2017  _grade_order_list:2057  s46_54_grade_two_step:2069  s46_55_price_gap_30:2094  s46_56_accident_split:2120  s46_90_pending_not_graded:2160  _registrable:2209  s46_94_source_url_site_matches:2223  s46_91_raw_vs_stored:2267  s46_97_raw_linked_by_source_id:2339  s46_99_login_then_watch:2407  _logged_opener:2503  _sian_seq:2542  s46_100_sian_word_order:2574  s46_102_electric_only_is_electric:2711  s46_103_sian_values_carried:2763  s46_98_sian_words_on_screen:2804  s46_95_screens_alive:2910  s46_96_site_sells_but_no_code:2966  s46_92_browser_zero_count:3013  s46_161_no_unproven_absence:3082  s46_162_promised_checks_exist:3131  s46_145_numbers_have_meaning:3161  s46_155_screen_spec_has_mockup:3190  s46_163_mockup_has_route:3223  _guide_docs:3254  s46_129_table_sum_counted:3263  s46_132_handover_says_remeasure:3295  s46_140_new_host_has_robots:3309  s46_142_site_count_matches:3328  s46_146_absence_needs_parser_check:3363  s46_154_master_wish_in_registry:3385  s46_131_paging_claim_measured:3407  s46_135_generalisation_has_sample:3429  s46_138_all_claim_needs_source:3446  s46_149_confession_is_closed:3470  s46_156_answer_touches_spec:3497  s46_130_one_tally_per_register:3523  s46_134_target_site_pair:3540  s46_141_filter_claim_measured:3566  s46_143_master_items_are_master:3583  s46_147_absence_needs_ten:3618  s46_150_column_from_ddl:3640  s46_133_check_gap_in_pending:3662  s46_136_warn_number_moves:3680  s46_137_config_key_has_reader:3702  s46_139_field_claim_counted:3731  s46_148_axis_gap_traced:3748  s46_152_dev_rounds_read:3766  s46_159_design_is_doable:3799  s46_144_empty_is_split:3818  s46_153_owner_is_judged:3835  s46_157_perf_claim_is_timed:3867  s46_158_size_claim_is_measured:3885  s46_160_ev_leak_full_mark:3903  s46_164_dev_pending_answered:3920  s46_165_fixable_not_called_unmeasurable:3954  s46_166_decision_reached_chapters:3995  s46_168_check_counts_exceptions:4025  s46_169_gone_has_reason:4064  s46_170_one_architecture:4081  s46_171_yardstick_names_screen:4099  s46_172_absence_read_as_human:4118  s46_173_endpoint_not_wordcount:4142  s46_174_no_endpoint_only_if_probed:4167  s46_175_no_lumped_axes:4194  s46_176_guide_probes_sites:4227  s46_177_catalog_not_site_locked:4255  s46_178_list_field_not_empty_axis:4280  s46_179_no_penalty_without_source:4305  s46_180_code_table_per_site:4319  s46_181_read_stored_before_probing:4346  s46_182_all_sites_before_claiming_all:4365  s46_183_master_only_after_probing:4393  s46_184_unfetched_is_not_absent:4422  s46_185_file_is_the_原本:4450  s46_186_grade_distribution_watched:4480  s46_187_cheaper_scores_higher:4494  s46_188_screen_before_claiming_missing:4521  s46_191_budget_follows_fuel_rule:4545  s46_192_pref_brands_registered:4591  s46_202_no_raw_template_tags:4616  s46_227_absent_only_declared:4629  s46_213_recommend_has_no_sold:4680  s46_203_new_site_has_target_keys:4726  s46_203_collect_writes_files_first:4758  s46_205_no_raw_response_writes:4786  s46_206_pdf_link_only:4821  _retired_s46_207_says_measured:4853  s46_207_commit_title_says_fact:4887  s46_208_market_no_negative:4925  s46_214_photo_uses_space_below:4944  s46_215_collector_respects_active:4969  s46_229_recommend_not_active_off:4995  s46_230_schema_change_counts_one_run:5023  s46_231_all_sites_in_filter:5053  s46_232_budget_curve_is_log:5080  s46_233_size_axis_never_zero:5124  s46_234_top_site_sweeps_gone:5163  s46_235_screen_hides_unsellable:5195  _recommend_rows_once:5237  s46_240_all_indexes_exist:5255  s46_237_recommend_in_budget:5296  s46_236_interior_color_axis:5328  s46_238_trim_not_double_counting:5363  s46_241_regrade_alive_on_deploy:5386  s46_242_mock_has_required_header:5428  s46_243_empty_says_why:5452  s46_244_failed_response_kept:5482  s46_245_each_screen_has_its_parts:5502  s46_246_every_screen_has_a_mock:5537  s46_253_browser_confirms_deploy:5571  s46_247_site_coverage:5629  s46_248_grade_is_realistic:5695  s46_249_budget_pairs_are_masters:5729  s46_250_mock_has_real_shape:5758  s46_251_vehicle_key_per_site:5791  s46_252_admin_write_actually_saves:5821  s46_253_part1_seen_in_browser:5853  s46_254_pair_badge_not_by_order:5888  s46_255_tester_items_listed_one_by_one:5922  _as_check:6185  results:6199  save:6238  run:6249
```

### `validate/v11_web.py` — 5,057줄

```
_web_sources:644  run:656  _late_checks:766  _templates_with_form:830  _spec_routes:851  _screen_routes:876  _routing_table_check:900  _count:937  ctx_account:944  _view_exists:950  _tpl:971  _all_templates:976  _screen_checks:981  _query_budget_check:1235  _import_origin_check:1314  _import_step4_check:1349  _browser_origin_check:1373  _browser_confirm_check:1391  _browser_chunk_check:1416  _status_screen_checks:1474  _status_liveness_check:1512  _menu_label_check:1561  _menu_paths:1589  _listing_rows:1614  _cli_caps:1632  _cli_only_check:1646  _stale_notice_check:1691  _trim_detail_check:1727  _option_sum_check:1750  _heart_line_check:1777  _recommend_terms_check:1798  _lease_checks:1817  _pick_filter_checks:1877  _shortfall_check:1916  _cash_limit_check:1935  _py_files:1966  _menu_no_path_check:1980  _listing_paging_checks:1998  _photo_checks:2034  _compare_shape_check:2075  _detail_shape_checks:2125  _filter_shape_checks:2203  _row_shape_checks:2273  _menu_shape_checks:2345  _sian_css_checks:2428  _cell_of:2503  _link_tip_checks:2526  _origin_link_check:2540  _origin_opens_bad:2585  _choose_check:2634  _order_filter_checks:2650  _checks_cfg:2693  _photo_size_by_screen_check:2702  _template_leak_check:2726  _em_dash_check:2752  _card_limits:2788  _cells_of:2805  _matches:2833  _grid_areas:2853  _hidden_cells:2883  _brace_block:2908  _place_cards:2922  _card_shape_checks:3044  _why_order_spec:3142  _why_order_check:3159  _width_policy:3194  _width_checks:3201  _chart_check:3300  _row_link_checks:3331  _screen_contradiction_check:3367  _chunk_check:3389  _csrf_reuse_check:3429  _origin_price_check:3473  _with_includes:3509  _v1_parity_checks:3531  _media_blocks:3621  _responsive_checks:3642  _dead_links:3730  _null_link_check:3744  _sian_visual_check:3808  _purchase_cost_checks:3872  _report_popup_check:3965  _detail_photo_check:4039  _raw_shown_checks:4090  _compare_diff_check:4177  _chunk_message_check:4241  _whole_char:4268  _chunk_boundary_check:4281  _cell_squeeze_check:4369  _static_version_check:4424  _axis_state_check:4442  _three_values_check:4485  _photo_size_check:4524  _render_metrics_checks:4550  _browser_scope_checks:4649  _import_opened_steps_check:4670  _import_resume_check:4698  _watch_invite_check:4717  _post_smoke_check:4761  _template_roots:4834  _loop_fields:4844  _context_supplied_check:4866  _first_item:4937  _has_field:4951  _table_counts:4957  _save_button_check:4964  _probe:5021  _scratch:5039
```

### `report/screens/build.py` — 4,440줄

```
load_config:48  site_badge:119  axis_heads:138  _grade_order:148  _not_ranked:161  _labels:177  viewer_state:181  _unknown_cfg:191  is_unknown:200  chip:216  _stamp:252  _bulk_axes:256  confirm_ratio:277  _bulk_changes:288  _total_points:315  _photo_note:327  photo_urls:349  photo_url:401  market_price:424  _days_between:441  _ceil_to:456  _bulk_market:471  _bulk_state:510  not_join_months:543  _left:566  _warranty_state:575  _axis_state:613  _sites_cfg:681  _row:694  _pen_rows:954  _pen_axes:965  _pen_sum:985  _pen_words:993  _ym_parts:1006  _age_label:1018  _km_per_year:1039  _pen_top:1059  _view_cfg:1073  _grade_rank_sql:1087  _sold_words:1142  _order_sold:1160  order_clause:1175  _site_detail_urls:1190  _source_url:1199  _view_str:1229  _lease_kinds:1234  excluded_hidden:1241  lease_hidden:1257  _option_blind_sites:1279  _option_group_match:1296  fuel_groups:1310  _fuel_where:1321  _paused_sites:1347  _listings_where:1359  model_counts:1614  count_listings:1641  view_listings:1658  _market_gap_label:1816  _score_bars:1832  _group_caps:1863  _view_list:1884  _view_dict:1889  _soh_low:1894  _view_int:1903  _bucket:1908  _high_km:1915  _option_prices:1924  recommend_funnel:1936  _bulk_upside:1954  view_recommend:1969  recommend_reason:2004  excluded_groups:2049  view_why:2067  _compare_conclusion:2077  view_compare:2100  market_trims:2167  view_market:2189  _web_cfg:2225  _median:2239  _with_height:2244  _price_bins:2259  _group_prices:2280  _by_year:2298  _year_line:2315  _by_trim:2341  _other_targets:2359  count_dealers:2368  _dealer_targets:2374  region_of:2394  _region_short:2421  _dealer_region:2441  view_dealers:2456  view_run:2492  _rank1_of:2498  view_dashboard:2506  _bars:2643  _grade_counts:2658  _relax_sim:2676  _axis_shortfall:2697  _progress:2716  _gone_and_watch:2731  _e_reasons:2774  _today_changes:2792  _step_rows:2817  _bulk_spark:2834  view_watch:2870  _man:2970  _mmdd:2984  _chg:2997  _gap:3012  _days_since:3027  _pending_values:3052  _done_items:3061  view_notready:3087  _unmatched_rows:3128  _report_files:3173  view_reports:3205  _warranty_until:3261  _verdict_lines:3310  _manwon_str:3352  _unknown_lines:3359  _price_history:3391  _alternatives:3408  _rep_flt:3444  view_detail:3450  _quartiles_by_target:3492  market_by_target:3516  _grade_order:3553  _grade_step:3568  _miss_axes_bulk:3574  _sold_int:3622  _sold_where:3630  _days_between:3640  view_sold:3655  _sold_bins:3730  _pair_rows:3788  _lease_words:3834  view_track:3848  _accident_bulk:3976  duplicate_listings:3991  _today_counts:4043  _notready_counts:4067  axis_zero_rates:4087  _recommend_models:4127  _active_targets:4183  view_recommend_tabs:4202  _ym_dash:4372  _first_photo:4380  _site_labels:4390  _recommend_axes:4397  _axis_labels:4431
```

### `web/views.py` — 2,842줄

```
_rows_per_page:30  _cfg:34  _versions:39  page_extras:58  _points:67  page:89  sold:116  listings:135  why:192  detail:244  _grade_help:277  notready:284  dashboard:294  admin_home:316  _unclassified_split:328  _rows_of:356  _check_reports:366  admin_audit:389  admin_docs:402  _int_param:426  _manwon:465  _site_buttons:470  _fallback_sites:531  _filter_chips:543  _order_menu:597  _carry:603  _order_label:613  ORDERS_LABELS_GET:617  _condition_sentence:621  _query_string:639  _page_links:652  _simple_paging:673  _paging:683  _filter_buttons:713  _model_menu:746  _pick_state:763  _option_name_buttons:825  _color_menus:886  _judge_buttons:901  _split_top:929  _fuel_options:935  _distinct_options:946  _km_options:958  _grade_options:966  _keep_query:973  _carry_pick:998  _lease_hidden:1008  _excluded_hidden:1014  _excluded_why:1021  _filter:1031  recommend:1118  _recommend_old:1153  track:1186  compare:1203  market:1225  _first_target:1245  dealers:1251  watch:1271  _note_kinds:1288  _watch_notes:1295  run_view:1322  login:1334  _login_again:1376  _open_session:1392  logout:1433  _watch_queries:1450  watch_query_post:1459  _int_or_none:1489  watch_add_post:1493  _watch_note_post:1553  _watch_invite:1579  watch_update_post:1602  _now:1626  _reason_gate:1633  _gate:1654  _first_flag:1693  _all_hours:1698  admin_run:1726  _target_rows:1794  admin_dict:1807  admin_status:1844  admin_collect:1859  _take_chunk:1929  _verify_part:1972  _run_stamp:2012  _int_or_none:2023  admin_import:2028  admin_scoring:2100  _decide_cards:2168  _unclassified_count:2196  admin_registry:2205  admin_query:2265  admin_requests:2287  _admin_extra:2349  _config_files:2364  _config_rows:2371  admin_config:2403  _typed:2454  admin_api:2470  _site_query:2520  admin_targets:2533  admin_tools:2631  join:2650  password:2681  admin_users:2696  _account_activity:2756  reports:2762  report_download:2778
```

### `validate/v3_logic.py` — 2,329줄

```
_file_output_checks:384  _conflict_checks:437  _diagnosis_count_check:461  _sort_determinism:478  _warning_contract_checks:500  _list_observed_source_check:595  _facet_reconcile_check:625  _record_mismatch_check:669  _curve_table_check:699  _special_null_check:772  _grade_base_checks:800  _checks_cfg:893  _labels_cfg:907  _unknown_mark_checks:915  _grade_cut_checks:966  _points_cap_checks:1089  _worse_of_checks:1141  _checks_json:1203  _value_curve_checks:1214  _group_sum_checks:1319  _mapped_other_check:1430  _denominator_check:1457  _core_axis_check:1485  _rental_cross_check:1506  _why_cheap_check:1544  _source_before_value_check:1585  _absolute_cut_check:1620  _spec_files:1650  _confirm_ratio_check:1660  _warranty_checks:1710  _spec_axis_check:1744  _site_axis_checks:1785  _rendered_why:1842  _rendered_listings:1852  _fill_gap_check:1862  _points_sum_check:1895  _market_gap_check:1920  _bonus_checks:1976  _trim_price_check:2080  run:2137  _shuffle_check:2272  _halt_dict_check:2297  _ensure_tmp:2326
```

### `store/core.py` — 2,001줄

```
resolve_listing_id:38  resolve_dealer_id:56  serialize_container:72  record_change:83  split_pii:111  flush_dealer_pii:163  _record_dropped:175  classify_invariant_change:210  _lookback:271  _source_history:285  _schema_change_min:314  _current:328  _today:334  _drop_non_values:348  origin_dropped:360  _drop_impossible_origin:365  _note_skipped:394  upsert_core:415  mark_gone:528  sweep_gone:545  sweep_gone_groups:589  load_snapshot:631  build_identities:744  resolve_vehicle_id:770  merge_conflict:802  upsert_vehicle:813  upsert_dealer:834  dealer_trust:861  _trust_cfg:954  upsert_child:971  _flag:992  _not_join_months:1006  state_counts:1031  current_versions:1071  diagnosis_of:1101  target_counts:1114  top_target:1121  vehicle_of:1126  collect_scale:1133  our_fault:1153  catalog_coverage:1162  _walk:1206  _sample_bodies:1222  hits_of:1235  key_seen:1254  stored_hits:1269  sample_bodies:1285  observed:1307  known_leaves:1345  has_unclassified:1360  classify_unclassified:1367  _card_limit:1410  _value_chars:1415  _admin_cfg:1420  unclassified_cards:1437  _peek:1493  _short:1540  _blocking_paths:1551  _raw_rows_max:1571  used_endpoints:1581  raw_sections:1590  _flatten:1629  option_diff:1653  _option_names:1691  blocking_keys:1707  full_hits:1725  axis_paths_empty:1750  blocking_rows:1787  record_mismatch_sql:1849  record_mismatch_count:1855  relist_counts:1881  listing_models:1898  filter_options:1918  site_counts:1935  unscored_count:1948  photo_ready_sites:1965  unclassified_fields:1990
```

### `collect/runner.py` — 1,857줄

```
CollectGroup:67  load_targets:91  collect_groups:104  facet_axes:172  aspect_names:193  check_facet_axes:197  interpret_failure:211  collect_check:240  FailStreak:310  _sleep:344  _log_request:350  _save_issues:361  make_executors:372  classify_in_group:1026  _query_key:1055  _group_of:1063  _fuel_of:1078  _badge_of:1084  _pages_for:1090  _dicts:1104  _option_medians:1146  _lease_types:1192  _market_medians:1206  _trim_ladders:1263  _option_base:1280  _site_grade_rules:1310  _cfg_num:1329  _dimensions:1345  _listing_config:1374  _listing_values:1401  _option_money:1420  _owned_months:1439  _option_of:1451  _market_of:1459  _group_sums:1469  _origin_lend_table:1497  _origin_keys:1527  _origin_lent:1546  make_score_executors:1566  make_validate_executor:1786  make_registry_executor:1828
```

### `tests/test_spec_ui.py` — 1,494줄

```
rec:33  spec_a:43  spec_b:121  spec_c:195  spec_d:239  spec_f:281  spec_g:316  spec_h:364  spec_j:397  spec_m:440  spec_e:508  spec_i:551  spec_k:664  spec_csrf:719  spec_l:746  spec_monkey:788  flow_s1:860  flow_s2:929  flow_s5:1013  flow_s3:1126  flow_s4:1201  flow_s6:1272  guide_v132:1328  main:1428  _write:1472
```

### `tests/test_integration.py` — 1,275줄

```
rec:31  Client:41  text:96  links:101  start_server:105  seed_admin:149  m1:165  m2:261  m3:335  m4:664  s3:735  unit:800  gaps:835  flows:943  guide7:1046  _account_id:1179  make_users:1186  main:1204  _write_table:1253
```

### `tools/check_src.py` — 1,156줄

```
_spec_files:44  _read_spec:62  say:73  py_files:87  chapter_of:127  _declared_chapters:137  split_done:157  _illustration:176  _retired_config_keys:240  _git:701
```

### `report/screens/admin.py` — 1,091줄

```
AdminMenuItem:33  AdminHome:81  SaveGate:107  AuditTab:121  AuditView:129  DocView:136  menu_for:147  view_admin_home:159  _todos:186  _recent_runs:226  _recent_changes:257  save_gate:268  view_audit:276  view_docs:322  _doc_files:353  Todo:374  RunRow:388  ChangeRow:398  _cfg_rows:418  config_history:428  query_history:440  db_tables:454  api_snapshots:495  account_activity:506  make_target_key:524  target_choices:543  target_rows:562  parse_import_text:593  status_view:608  _catalog_state:682  _light_result:714  _live_window:754  _live_progress:763  run_progress:810  collect_state:860  received_vs_used:920  dict_state:941  import_state:968  job_log:1006  validation_runs:1020  blocking_set:1038  _menu_groups:1062  _menu_by_group:1081
```

### `tools/verify_axes.py` — 1,084줄

```
_spec_text:26  _grade_order:59  _not_ranked:72  spec_tables:86  _num:109  pick:127  _flag:141  hand_market:149  _median_for:160  hand_mileage:180  _years:193  conn_now:202  lookup:207  hand_accident:231  hand_repair:241  hand_owner:249  _warranty_left:257  hand_warranty_general:278  hand_warranty_power:283  hand_site_warranty:289  hand_maker_warranty:319  _km_per_month:346  residual_spec:362  _json:388  hand_option_won:401  hand_depreciation:438  hand_frame:468  hand_outer:489  _leak_states:509  hand_leak:521  hand_lien:536  hand_not_join:546  hand_trim:576  hand_special:596  spec_section:606  spec_head_points:614  lookup_label:621  hand_integrity:629  hand_special_points:655  _taste_points:664  _has_option:675  hand_color:715  hand_usage:739  hand_site_grade:763  hand_inspection_src:783  hand_hud:796  hand_sunroof:805  hand_picked:814  _has_table:827  _option_prices:833  hand_options:851  survey:889  main:952
```

### `store/adminops.py` — 1,057줄

```
QueryLog:55  QueryResult:68  ApiSnapshot:93  DevRequest:104  RecalcJob:119  ScoringPreview:130  ImportPreview:142  ImportResult:159  preview_import:168  import_listings:194  _import_facet:260  BrowserCatch:295  save_browser_catch:303  mark_step_imported:353  pending_enums:384  pending_axis_summary:421  apply_dict_decision:449  _strip_sql:494  sql_reject_reason:501  _opened_tables:535  reject_kind_of:550  columns_hint:560  reap_stale_jobs:583  run_query:618  fetch_api:665  create_dev_request:699  update_dev_status:721  export_dev_requests:735  enqueue_recalc:765  enqueue_after_list_save:791  job_progress:816  db_progress:830  preview_scoring:840  _pt:883  registry_rows:887  registry_counts:898  write_dev_requests:904  dev_request_rows:924  save_api_snapshot:945  get_api_snapshot:968  path_table:987  halt_job:1023
```

### `report/render.py` — 1,037줄

```
_labels:30  _site_blind_axes:35  _stamp:76  _curve_points:91  source_detail_url:134  _why_cheap_of:155  _scoring:196  _record_cols:207  record_rows:216  _penalty_rows:270  _market_pos:284  _site_badge:328  _axis_why:335  _raw_sections:365  _photo_why:375  _photo_urls:396  _purchase_costs:419  _unknown_axis_cfg:447  render_listing:470  axis_mark:648  source_label:669  _option_rows:717  _fetch_views:777  _strengths:792  _weaknesses:799  _pending_best:806  _cost_rows:839  _known_issues:860  _diagnosis_view:878  render_target:889  render_run:970  render_halt:1012  _j:1030
```

### `validate/v10_admin.py` — 934줄

```
_sources:212  _admin_guard_checks:233  _sql_strings:278  _schedule_checks:290  _query_error_checks:333  run:432  _session_checks:577  _pii_query_check:657  _scratch:704  _dict_reason_check:719  _dict_source_shown_check:735  _automation_checks:753  _queue_consumer_check:886  _queue_stale_shown_check:915  _ensure_tmp:931
```

### `tests/test_score.py` — 928줄

```
check:36  fx:42  snap:46  ctx:66  full_verdict:87  test_denominator:100  test_components_form:151  test_grade:202  test_order_independent:291  panels_of:314  test_history_real:319  test_rental_real:354  test_insurance:396  test_safety_real:421  test_spec_gate:470  test_price_real:549  test_color:663  test_price_pending:710  test_absolute_real:729  test_null_safe:769  test_empty_array_meaning:786  test_peer_group:811  test_damage_by_status:853  test_repair_cost_ratio:879  test_hda_gate:888
```

### `validate/v2_load.py` — 919줄

```
DayGapReport:151  GapCause:164  run:170  _surrogate_key_checks:347  _not_null_check:432  _chained_subscript_check:449  _Boom:497  _salvage_check:505  _table_exists:546  _exception_shape_checks:552  _schema_sync_check:618  _pii_access_check:655  gap_alerts:694  diff_prev_day:710  explain_gap:732  _pii_column_check:764  _secret_key_check:782  _parser_common_fields_check:820  _null_target_not_judged_check:871  _null_target_visible_check:896
```

### `validate/v1_collect.py` — 910줄

```
_unknown_split_checks:171  _axis_empty_check:257  run:287  _endpoint_order_check:421  _empty_db_check:433  _sql_groups:460  _cumulative_codes:496  _run_scope_check:506  _ctx_started:544  _has_run_id:552  _expected_scope_check:557  _diagnosis_scope_check:578  _diagnosis_none_count:618  _query_key_check:643  _entrypoint_parity_check:689  _enclosing_def:718  _run_id_filled_check:727  _catalog_key_check:747  _whole_probe:769  _whole_body_check:780  _catalog_checks:816  _unparsed_envelope_check:863  _ensure_tmp:907
```

### `report/screens/views.py` — 898줄

```
AxisChip:30  ScoreBar:55  AxisPoint:71  ListingRow:87  ListingFilter:269  WatchRow:358  TargetStat:401  RelaxRow:410  MarketRow:417  ChangeRow:429  AttentionItem:439  ViewerState:447  DashboardView:461  CompareView:498  TrackPair:516  TrackView:555  MarketView:581  DealerRow:596  SoldBin:617  SoldRow:633  SoldView:658  NotReadyView:678  TodayChange:709  StepRow:721  _min_sample:733  PendingValue:751  Bucket:764  ExcludedGroup:784  ReportFile:793  ReportsView:805  RecommendAxis:827  RecommendRow:837  RecommendView:880
```

### `tools/trace_fill.py` — 840줄

```
spec_lines:94  anchor_step:112  build_symbols:131  enclosing:166  build_texts:176  _stem:214  tokens:223  _best_in:253  _rows:290  layers_of:303  layer_pool:310  _rare_hit:322  axis_words:346  json_key_at:367  _place:394  _hints:405  find_in_layer:421  _best_step_in:469  _layers:500  derive_state:520  src_mark:546  relayer:559  restate:574  fill_file:597  move_to_rules:665  survey:708  lists:736  write_index:757  main:796
```

### `validate/v4_mapping.py` — 785줄

```
_paths:143  _layer_of:190  _unclassified_split:195  _layer_checks:233  _name_collision_check:329  _key:363  _decide_material_check:369  _blocking_list_check:433  run:490  _mapping_coverage_checks:639  _our_columns:669  _listing_value_scope_check:702  _dict_filled_check:722  _kind_check:733  propose_fix:747  _option_code_check:762  _is_sentence:779
```

### `tests/test_run.py` — 783줄

```
check:36  StubEncar:92  Clock:241  setup:246  test_envelope:284  test_last_page_exact:314  test_facet:321  test_facet_missing_axis:335  test_dict_step:344  test_all_groups:366  test_parse_pipeline:377  test_score_pipeline:481  test_validate:553  test_registry_gate:596  test_target_scope:653  test_catalog_key:685  test_wrapper_args:703  test_unclassified_listing:750
```

### `collect/pipeline.py` — 775줄

```
envelope_scope:41  Reprocess:91  refetch_all:121  reprocess_plan:131  should_refetch:148  expected_for:160  step_report:194  halt_if:210  precheck:243  resume_point:297  config_hash:317  build_run_context_fields:323  stale_rows:332  save_step_report:347  rss_mb:371  run_step:390  _execute:428  completed_steps:447  run_pipeline:459  print_progress:508  silent_progress:527  from_step_for:541  web_reasons:571  check_recalc_origin:576  plan_recalc:588  _current:605  run_recalc:611  Defect:632  DefectReport:643  diagnose:664  _DiagCtx:688  _collect_defects:698  format_defects:752
```

### `store/watch.py` — 746줄

```
AlertConfig:58  WatchItem:71  TrackPoint:86  TrackEvent:101  WatchEvent:115  _cross_site_order:130  classify_duplicates:149  sync_duplicates:202  deduped_count:226  watch_add:236  assert_owner:275  watch_update:290  watch_close:310  note_add:331  notes_of:356  note_delete:374  track_snapshot:389  track_points:418  classify_cause:427  detect_events:439  message:497  notify:525  _grade_order:596  _not_ranked:609  add_watch_query:623  run_watch_queries:658  watch_query_rows:714  close_watch_query:728
```

### `store/admin.py` — 716줄

```
_admin_cfg:46  ConfigChange:68  running_job:86  hash_secret:96  _split:104  create_account:109  account_count:145  needs_bootstrap:149  _recent_failures:161  _log_attempt:180  is_locked:190  unlock_account:205  authenticate:233  open_session:269  session_account:289  change_secret:306  revoke_sessions:330  _under_seed:353  _walk:361  get_path:385  set_path:390  _atomic_write:397  apply_config:407  _validate_blob:473  revert_config:495  history:519  classify_field:543  account_rows:616  admin_count:630  set_role:637  set_disabled:654  add_config_key:674
```

### `tools/backfill_from_raw.py` — 663줄

```
_now:28  latest_details:32  heydealer:44  kbchachacha:124  hyundai_cert:210  reborncar:259  out_of_scope:292  bmw_bps:328  kcar:366  _record_site:397  kb_record:424  volvo:434  volvo_detail:443  lexus_detail:471  kb_detail:500  _latest:566  mpark_inspection:578  main:644
```

### `parse/encar/mapping.py` — 625줄

```
_get:30  _json:42  _won:53  _ym:73  _date10:83  _int:99  _bool:105  unpack_envelope:116  parse_list_item:124  parse_detail:171  parse_inspection:247  parse_record:295  _sample_chars:349  safe_field:363  parse_with_issues:385  _salvage:403  _parses:446  dig:453  as_list:476  _diag_comment:504  parse_diagnosis:511  parse_diagnosis_items:543  _text:551  parse_record_summary:561  parse_platform_check:587  parse_inspection_summary:594  parse_ev_battery:599  parse_sellingpoint:619
```

### `store/raw.py` — 617줄

```
_compress_cfg:59  pack_body:70  raw_body:91  _text_of:107  batch:134  tick:164  commit:199  _batch_commit_rows:226  _batch_commit_pause_ms:236  _busy_timeout_ms:261  connect_db:272  open_db:300  link_raws:311  _safe_headers:337  save_raw:344  proc_run_id:402  save_site_raw:412  save_import_raw:467  save_browser_raw:500  save_browser_facet:541  save_import_facet:567  save_facet:597
```

### `tools/collect_kbchachacha.py` — 602줄

```
_now:93  _get:97  fetch_ok:106  page_ids:123  load_filters:133  walk_group:199  count_all:241  probe_detail:267  store_details:286  fetch_details:315  load_details:383  main:462
```

### `store/dictionary.py` — 591줄

```
CodeEntry:31  AxisPolicy:57  policy:114  scope_key:122  seed_fixed_enums:147  target_map:188  target_key_of:211  fuel_normalize:227  collect_group_of:250  match_target_name:255  known_model_names:272  known_model_of:289  mapped_of:294  upsert_enum:315  _handle_conflict:367  upsert_option3:388  retire_unseen:424  resolve_code:439  installed_option_names:477  normalize_enum:495  assert_no_unknown:511  bump_dict_version:554  list_pending:564  confirm_enum:572
```

### `tests/test_admin_flow.py` — 575줄

```
check:32  _env:38  _cfg:55  _post:60  _get:65  flow_config:71  flow_scoring:107  _rescore:172  _sum:233  _dist:240  flow_targets:247  flow_registry:282  flow_run:322  flow_query:355  flow_api:381  flow_tools:418  flow_users:440  flow_requests:485  flow_permission:527  main:540
```

### `tests/test_admin.py` — 567줄

```
_spec_menu_paths:31  check:47  setup:53  test_bootstrap:65  test_auth:95  test_apply_config:137  test_value_validation:175  test_revert:195  test_no_direct_edit:221  test_classify_field:250  test_run_query:324  test_dev_request:377  test_recalc_and_lock:407  test_admin_screens:441  test_v10:531
```

### `tools/check_spec.py` — 557줄

```
_read_spec:10  _refs_source:73  _spec_files:284  _guide_files:368  _sections:373  _md:468
```

### `web/app.py` — 547줄

```
menu_items:22  _tip:107  _label:112  empty_state:123  banner_of:142  _encar_blocked:203  _list_stale:234  static_version:260  build_page:288  check_post:309  redirect:331  take_flashes:351  _display_now:364  make_app:390  _Denied:523  build_context:531  _title_of:546
```

### `tools/build_index.py` — 536줄

```
_py_files:48  _checks_in_code:73  _guide_checks:119  _checks_in_docs:152  last_runs:185  _run_time:214  sort_checks:224  build_checks:241  _outline:313  build_source:324  build_schema:356  build_doc_index:415  check_fresh:480  main:513
```

### `tests/test_web.py` — 522줄

```
check:21  test_routes:28  test_template:85  test_no_logic_in_template:126  test_static_escape:141  test_session_cookie:153  test_error_page:171  test_layout:198  test_filters:227  test_empty_state:250  test_menu_by_role:277  test_guard_and_csrf:298  _call:345  test_screens_render:362  test_sketch_match:453  test_account_policy:468
```

### `contracts.py` — 481줄

```
Response:24  Clock:34  Fetcher:39  Rng:44  Request:52  EndpointSpec:60  FetchResult:71  TargetSpec:84  ListingSnapshot:141  AxisResult:244  Account:263  require_role:280  RunContext:297  StepReport:317  ResumePoint:341  clean_vin:362  total_of:373  RegressionReport:386  json_paths:397  shape_ok:446  shape_violations:479
```

### `run.py` — 421줄

```
load:51  make_context:56  _filter_targets:70  _steps_from:89  cmd_collect:103  _grade_summary:171  cmd_admin_create:186  _collect_urls:203  _page_url:240  cmd_web:259  make_worker_ctx:299  make_worker_executors:305  cmd_delegate:343  _api_fetch:354  cmd_setup:364
```

### `report/views.py` — 419줄

```
VersionStamp:18  ReportMeta:30  AxisView:40  FinanceView:64  PurchaseCostItem:85  PurchaseCostView:94  DiagnosisView:118  FetchView:130  CostRow:144  ScoreView:153  CollectSummary:267  ClassifySummary:274  PriceSummary:281  AxisStat:290  CoefficientChange:300  DictChangeSummary:310  TargetReport:318  RunStep:330  RunReport:345  HaltReport:356  FixAction:373  NotifyResult:383  ExportResult:396  display_value:405  display_points:415
```

### `web/template.py` — 406줄

```
f_won:55  f_km:71  f_pct:75  f_date:79  f_num:90  f_gradecls:97  f_gradelabel:110  _grade_classes:125  f_count:134  f_signcls:142  f_signwon:152  f_url:160  _index_key:198  _step:213  _lookup:225  _truthy:234  render_str:238  strip_comments:345  expand_includes:350  render:387
```

### `tests/test_collect.py` — 401줄

```
_target_count:35  check:51  R:57  test_verify_shape:62  _Stub:97  _Clock:105  test_fetch_status:110  test_interpret_failure:123  test_facet_axes:135  test_collect_groups:163  test_build_q:191  test_collect_check:241  test_save_raw:256  test_fail_streak:285  test_all_fail_sample:327  test_diagnosis_scope:371
```

### `tools/sync_registry.py` — 394줄

```
FieldUsage:31  RegistrySyncReport:48  facet_path:66  scan_paths:74  shape_ok:79  _walk_values:92  collect_values:106  collect_paths:132  _has_value:173  _seed_for:189  sync_registry:200  suggest_usage:295  write_suggested:307  halt_report:334  list_by_usage:357  assert_registered:364
```

### `tests/test_pipeline.py` — 388줄

```
check:37  db:43  test_expected:49  test_halt:61  test_reprocess:82  test_refetch:107  test_precheck:115  test_resume_and_version:167  test_run_pipeline:195  test_recalc:230  test_pii_orphan:265  test_exception_becomes_halt:298  test_fixed_enum_bootstrap:319  test_envelope_scope:349
```

### `parse/hyundai_cert/mapping.py` — 374줄

```
_int:48  cards:57  _fuel_of:82  _model_group:93  parse_card:111  _json:183  detail_text:190  _one:197  parse_detail:202  parse_detail_all:208  _num:278  _warranty:285  _months_since:339  _months_left:351  _options:368
```

### `tools/browser_diff.py` — 362줄

```
pairs:35  look:48  main:298
```

### `analyze/axis/state.py` — 355줄

```
_panels:43  _rank_worst:47  insurance_trace:59  panel_trace:68  worse_step:80  _accident:87  _frame:109  _outer:129  _repair:151  _special:162  leak_state:174  _is_ev:196  _ev_words:218  _leak:236  _site_never:253  _sites_table:265  _consumable:283  _integrity:311  analyze_state:347
```

### `tools/collect_hyundai_cert.py` — 351줄

```
target_of:79  _now:95  _post:99  _get:109  fetch_detail:120  load_filters:133  total_count:171  walk:184  main:216
```

### `parse/heydealer/mapping.py` — 341줄

```
_int:22  _won:29  _ym:34  _model_group:42  parse_list_item:60  parse_detail:89  fuel_efficiency_kmpl:117  options_of:124  record_of:153  warranty_of:206  _months_since:240  part_enums:252  panels_of:303
```

### `tools/light_check.py` — 340줄

```
_repair_max:45  _cfg:63  _run:77  collecting:89  screen_counts:110  db_counts:136  measure:154  index_counts:176  changed:200  _worse:218  failing:222  repair:235  main:268
```

### `tools/build_dict.py` — 336줄

```
DictBuildReport:63  extract_distinct:78  _facet_values:123  facet_value_set:139  _walk_path:158  load_fixed_enums:185  build_dict:193  _mark_facet_substituted:244  build_catalog_dict:268  build_late_dict:308
```

### `parse/kcar/mapping.py` — 333줄

```
_int:25  yn:33  _months_until:46  _model_group:60  parse_detail:70  _photos:158  parse_list_item:171  accident_of:221  record_of:229  _not_join_spans:322
```

### `tools/render_screens.py` — 331줄

```
_shot_widths:32  _tmp_root:57  main:81  shot_paths:172  _localize_images:197  shoot:234
```

### `tools/load_raw.py` — 327줄

```
_now:60  query_target:64  body_target:103  _rows_from:129  main:203
```

### `validate/v7_watch.py` — 320줄

```
_cols:85  _reads:89  _progress_note_check:117  _relist_check:201  run:227
```

### `validate/v9_multisite.py` — 311줄

```
_sites:69  live_sites:75  _labels:83  _badge_check:98  _hardcoded_badges:133  _origin_check:156  _warranty_sum_check:186  _tie_break_check:229  _axis_site_check:267  run:307
```

### `tests/test_dict.py` — 293줄

```
check:39  db:45  test_scope_key:51  test_count_zero:73  test_axis_policy:97  test_conflict:150  test_catalog:185  test_status_version:209  test_classify:226  test_review:255
```

### `tests/test_screens.py` — 292줄

```
check:42  _pipeline:48  test_chip:60  test_listings:83  test_compare:149  test_dashboard_notready:166  test_static_rules:206  test_account:238
```

### `store/crosssite.py` — 291줄

```
CrossSiteMatch:31  ReadinessReport:41  active_sites:51  match_cross_site:56  site_prices_of:92  rebuild_core_vehicle:109  regression_check:128  snapshot_baseline:159  readiness:183  axes_by_site:227  site_only_axes:249  load_sites:271  site_addition_regression:276
```

### `tests/test_endtoend.py` — 291줄

```
check:31  _own_fields:37  _run:61  flow_pipeline:82  flow_validation:135  flow_config_effect:149  flow_report:208  main:274
```

### `adapters/encar.py` — 290줄

```
escape_value:126  unescape_value:136  _nest:141  load_site_config:152  EncarAdapter:171
```

### `tools/check_screens.py` — 285줄

```
_pairs:23  say:89  _text:98  check_pairs:105  check_phrases:118  _sian_heads:150  _heads:168  check_sections:187  check_nav:214  check_render:234  main:268
```

### `tests/test_fixtures.py` — 284줄

```
check:33  fx:39  test_inspection:53  test_frame_vs_outer:84  test_record:123  test_detail:152  test_classify_real:172  test_catalog:207  test_diagnosis:219
```

### `tests/test_crosssite.py` — 282줄

```
check:34  db:40  add:45  test_vin:63  test_vin_parse:107  test_cross_site:129  test_regression:175  test_readiness:207  v9_04_site_isolation:229
```

### `parse/kbchachacha/mapping.py` — 277줄

```
_text:43  _int:48  ld_json:55  _yes_no:67  _model_of:97  _options:128  _warranty:156  parse_detail:172  _photos:266
```

### `tests/test_store.py` — 270줄

```
check:40  seed:46  base:52  db:70  test_schema:76  test_key:124  test_null_three:135  test_change_history:142  test_invariant_violation:163  test_snapshot:196  test_dictionary:221
```

### `report/exports/export.py` — 269줄

```
filename:26  _stamp_lines:32  listing_md:38  listing_csv:76  halt_md:93  target_md:114  run_md:136  _asdict:186  export:194  output_path:233  write_export:241
```

### `web/server.py` — 266줄

```
load_web_config:47  guard:60  _drain_chunk:92  TOO_LARGE:96  make_handler:105  serve:241
```

### `tests/test_report.py` — 263줄

```
check:33  test_finance:40  test_display:97  _pipeline:113  test_layers:124  test_halt_layer:160  test_export:202
```

### `parse/revolt/mapping.py` — 260줄

```
_int:37  _won:44  _ym:49  parse_list_item:54  parse_detail:85  options_of:130  warranty_of:141  _months_since:174  record_of:185  panels_of:228
```

### `parse/reborncar/mapping.py` — 259줄

```
_txt:25  _int:29  fields:37  title_name:50  parse_detail:56  _photos:104  seats_of:119  kmpl_of:124  seats:130  marks:135  panels_of:174  counts_of:199  option_keys:227  options_of:234
```

### `tests/test_watch.py` — 259줄

```
check:30  db:36  add:41  watch:64  test_same_dealer:78  test_cross_dealer:97  test_relist:112  tp:124  test_cause:133  _two_runs:145  test_snapshot:162  test_events:177  test_cause_gate:198  test_message:212
```

### `tools/collect_kcar.py` — 254줄

```
_now:57  fetch:61  classify:83  accident_of:98  fetch_stock:107  collect_list:132  main:180
```

### `tools/menu.py` — 254줄

```
_fix_console:28  run:44  cmd_status:52  cmd_setup:56  cmd_dry:74  cmd_collect:81  cmd_facet:118  cmd_dict:123  cmd_screens:128  cmd_migrate:133  cmd_checkall:138  cmd_requests:143  cmd_check_spec:150  cmd_check_src:154  cmd_test:159  main:192
```

### `validate/v5_value.py` — 254줄

```
run:60  _grade_ratio_checks:156  _denominator_suite:200
```

### `parse/volvo_selekt/mapping.py` — 251줄

```
_txt:37  _int:41  fields:48  options:73  warranty:88  parse_detail:116  photos:169  photos_json:185  record_of:205  parse_list_item:236
```

### `analyze/axis/taste.py` — 248줄

```
_off:36  _fitting:41  color_grade_of:68  _color:90  _picked:113  _length_mm:133  _size:160  _on_curve:189  _color_int:211  analyze_taste:241
```

### `tests/test_registry.py` — 245줄

```
check:33  fx:39  db:43  put_raw:48  test_paths:57  test_contamination:69  test_seed:95  test_ghost:140  test_v4_06:168  test_seed_reapply:180  test_unclassified_severity:202
```

### `tools/collect_volvo.py` — 245줄

```
_known_name:43  load_slugs:59  _now:92  _get:96  main:111
```

### `tools/undo_wrong_gone.py` — 243줄

```
_now:41  _get:47  probe:63  probe_body:155  main:198
```

### `analyze/axis/site.py` — 240줄

```
remaining_months:26  warranty_points:39  _truthy:73  warranty_grade:89  _seller_only:115  _one_step_down:124  _site:136  _maker:169  _maker_default:201  analyze_site:238
```

### `tests/test_invariants.py` — 239줄

```
check:35  inv1_order_independent:42  inv1_shuffle_100:72  inv2_banned:95  inv5_points:113  put_contract:133  excluded_contract:150  inv3_source_not_null:176  inv4_label_shape:195  inv6_no_unclassified:211
```

### `tools/collect_reborncar.py` — 230줄

```
_now:47  _option_body:54  _options_old:82  _get:129  codes:144  main:159
```

### `tools/repair_facet_chunks.py` — 222줄

```
meta_of:37  fix_meta:66  groups:87  join:101  main:114
```

### `tools/collect_bobaedream.py` — 220줄

```
_now:45  _get:49  target_names:59  wanted:68  _elapsed:76  load_filters:83  _walk_plan:116  main:127
```

### `score/scorer.py` — 218줄

```
ScoreResult:27  _certified_credit:64  score:83  _bonuses:202  _penalties:211
```

### `tools/collect_revolt.py` — 215줄

```
_now:59  _get:63  _targets:78  main:108
```

### `web/context.py` — 213줄

```
MenuItem:31  Banner:42  PageContext:55  ErrorPage:92  _is_permission:135  _is_conflict:140  _clean:145  _is_sql_typo:156  error_page:166
```

### `validate/base.py` — 212줄

```
_cfg:24  Check:55  CheckResult:93  _short:118  result:131  not_applicable:140  save_results:145  gate:162  run_phase:171  canon_files:193  canon_text:206
```

### `tools/unknown_split.py` — 210줄

```
_cfg:35  _walk:41  classify:51  main:127
```

### `tests/seed.py` — 204줄

```
_cfg:46  build_seed_db:51  _confirm_dict:103  seed_db_path:119  _ensure_secrets:132  _seed_unclassified:148
```

### `tools/migrate.py` — 203줄

```
_table_sql:26  drop_not_null:33  rebuild_to_ddl:66  _norm:95  main:103
```

