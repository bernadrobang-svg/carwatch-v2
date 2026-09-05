# 소스 색인

**`python3.11 tools/build_index.py` 가 만든다. 손으로 고치지 않는다.**

파일 217개 · 총 80,267줄

| 파일 | 줄 | 무엇 |
|---|--:|---|
| `validate/v0_guide.py` | 7,718 | 가이드 문서 자체를 검사한다 (V0 계열). |
| `validate/v11_web.py` | 5,057 | V11 표현 계층 검증 (14장 STEP 153). |
| `report/screens/build.py` | 4,730 | 화면 데이터 생성. |
| `web/views.py` | 2,939 | 화면 어댑터 (14장 STEP 142 · 152). |
| `validate/v3_logic.py` | 2,329 | V3 로직 검증 — 판정이 작동하는가 · 변별력이 있는가. |
| `store/core.py` | 2,108 | CORE 저장소 (L4).  사이트 무관 공통 스키마. |
| `collect/runner.py` | 2,071 | 수집 실행 규칙. |
| `tests/test_spec_ui.py` | 1,494 | 규격 기준 통합 테스트 (통합테스트_시나리오_규격기준.md). |
| `tests/test_integration.py` | 1,276 | 통합 테스트 — 실제 HTTP 로 전 화면 (통합테스트_시나리오.md). |
| `tools/check_src.py` | 1,201 | CarWatch v2 — 지시서 ↔ 소스 대조 검증기. |
| `report/screens/admin.py` | 1,091 | 관리자 화면 — 표현 계층 (13장 STEP 138 · 138a). |
| `tools/verify_axes.py` | 1,084 | 손계산 대조 — 축마다 표본 3건 (개정 329 전수검증 · V3-66). |
| `store/adminops.py` | 1,057 | 관리자 서버 계층 — 실행 지시 · 쿼리 · API 조회 · 개발 요청 · 미리보기. |
| `report/render.py` | 1,042 | 리포트 생성 (L9). |
| `validate/v10_admin.py` | 936 | V10 관리자 검증. |
| `tests/test_score.py` | 928 | 7장 판정·채점 시험. |
| `report/screens/views.py` | 920 | 화면 전용 DTO. |
| `validate/v2_load.py` | 919 | V2 적재 검증 — 옮겨졌는가 · 전일 대비 변동이 타당한가. |
| `validate/v1_collect.py` | 910 | V1 수집 검증 — 다 받았는가 · 라벨이 맞는가. |
| `tools/trace_fill.py` | 840 | 추적표의 소스 · 화면 · 검사 칸을 기계로 채운다 (`inbox/ORDER_00_trace_fill.md`). |
| `collect/pipeline.py` | 792 | 실행 순서 · 중단 · 재처리 · 재개. |
| `tools/browser_diff.py` | 785 | ★★★★★ 09-01 마스터 지시 — ★ **브라우저로 시안과 화면을 대조한다.** |
| `validate/v4_mapping.py` | 785 | V4 매핑 검증 — 이름이 아니라 값으로 검증한다. |
| `tests/test_run.py` | 783 | S0~S3 종단 시험 (모의 응답). |
| `store/watch.py` | 746 | 후보 추적 (11장). |
| `store/admin.py` | 716 | 관리자 — 계정 · 권한 · config 변경 (13장 앞부분). |
| `store/dictionary.py` | 693 | 사전 저장소 (L5).  RAW 에서 생성한다. |
| `tools/backfill_from_raw.py` | 663 | ★★★★★ 08-30 (명령서 r974 · 0j 4) — ★ Ⓐ 「이미 오는 것을 읽는다」. |
| `tools/collect_kbchachacha.py` | 662 | KB차차차 목록 수집 · 총 매물 수 세기 (명령서 `ORDER_20260822_r515.md` 3-2 · 단계 9). |
| `parse/encar/mapping.py` | 625 | 엔카 원문 → CORE 필드 (L3). |
| `store/raw.py` | 617 | RAW 저장소 (L2).  원문 무손실.  삭제 금지. |
| `tools/build_index.py` | 589 | 검사 색인 · 소스 색인을 만든다 (규칙 11). |
| `tests/test_admin_flow.py` | 575 | 관리 화면 동작 시험 (13장 · 14장). |
| `tests/test_admin.py` | 567 | 13장 앞부분 시험 — 계정 · 권한 · config 변경. |
| `tools/check_spec.py` | 557 | CarWatch v2 지시서 자체 점검 — 7종 |
| `web/app.py` | 555 | 화면 조립 (14장 STEP 144 · 147 · 149). |
| `tests/test_web.py` | 522 | 14장 표현 계층 시험 — 템플릿 · 라우팅. |
| `contracts.py` | 481 | 계층 간 계약 — Protocol · DTO. |
| `run.py` | 476 | CarWatch v2 진입점. |
| `tools/load_raw.py` | 443 | 넣기 걸음 — ★ **파일 폴더를 읽어 `raw_response` ＋ `core_listing` 에 넣는다.** |
| `report/views.py` | 419 | 리포트 DTO (L9). |
| `web/template.py` | 406 | 최소 템플릿 엔진 (14장 STEP 143). |
| `tools/sync_registry.py` | 403 | RAW 경로 전수 → meta_field_usage. |
| `tests/test_collect.py` | 401 | 2장 수집 시험. |
| `tests/test_pipeline.py` | 388 | 5장 수집 순서 시험. |
| `parse/hyundai_cert/mapping.py` | 374 | 현대·제네시스 인증중고차 목록 카드 → CORE 필드 (L3). |
| `analyze/axis/state.py` | 355 | ② 상태 150 — 차가 성한가 (docs/ref/F-scoring.md ②). |
| `tools/collect_hyundai_cert.py` | 351 | 현대·제네시스 인증중고차 목록 수집 (명령서 `ORDER_20260822_r515.md` 3장 · 단계 11). |
| `parse/heydealer/mapping.py` | 348 | 헤이딜러 원문 → `core_listing` (명령서 37-3 ② · `docs/HEYDEALER_API.md`). |
| `tools/light_check.py` | 340 | 가벼운 점검 — 4시간마다 (개정 335 · S29-0). |
| `validate/v7_watch.py` | 338 | V7 관심·추적 검증. |
| `tools/build_dict.py` | 336 | RAW → 사전 생성. |
| `parse/kcar/mapping.py` | 333 | K카 상세 → `core_listing` (`docs/KCAR_API.md` 3장 · `MULTISITE_MAPPING.md` 1장). |
| `tools/render_screens.py` | 331 | 전 화면을 실제로 렌더해 `outputs/render/` 에 남긴다. |
| `validate/v9_multisite.py` | 311 | V9 — 다중 사이트 (`docs/chapters/50-multisite.md`). |
| `parse/revolt/mapping.py` | 294 | 리볼트 (revolt.kr) — 전기차 전용 인증중고차 (규격 `docs/REVOLT_API.md` · `S46-200`). |
| `tests/test_crosssite.py` | 293 | 12장 다중 사이트 시험. |
| `tests/test_dict.py` | 293 | 4장 키·코드·사전 시험. |
| `tests/test_screens.py` | 292 | 10장 화면 시험. |
| `store/crosssite.py` | 291 | 다중 사이트 확장 (12장). |
| `tests/test_endtoend.py` | 291 | 종단 시험 — 수집부터 리포트까지 (5장 STEP 47 · 49). |
| `adapters/encar.py` | 290 | 엔카 어댑터 — URL · 헤더 · 쿼리 조립. |
| `tools/check_screens.py` | 286 | 화면 ↔ 시안 대조 (10장 · 14장). |
| `tests/test_fixtures.py` | 284 | 실물 표본 시험 — v1 원문 12건. |
| `parse/kbchachacha/mapping.py` | 277 | KB차차차 상세 → `core_listing` (`docs/KBCHACHACHA_API.md` 3장). |
| `tests/test_store.py` | 270 | 3장 테이블 시험. |
| `report/exports/export.py` | 269 | 내보내기. |
| `web/server.py` | 266 | HTTP 서버 (14장 STEP 141 · 150). |
| `tests/test_report.py` | 263 | 9장 리포트 시험. |
| `parse/reborncar/mapping.py` | 259 | 리본카 상세 → `core_listing` (명령서 39 · `docs/REBORNCAR_API.md` 1b). |
| `tests/test_watch.py` | 259 | 11장 후보 추적 시험. |
| `tools/collect_kcar.py` | 254 | K카 상세 수집 (명령서 `ORDER_20260822_r515.md` 3-3 · 단계 10). |
| `tools/menu.py` | 254 | 실행 메뉴. |
| `validate/v5_value.py` | 254 | V5 수치 검증 — 기준값이 맞는가 · 보정이 타당한가. |
| `score/scorer.py` | 253 | 채점 · 분모 (L7). |
| `parse/volvo_selekt/mapping.py` | 251 | 볼보 셀렉트 상세 → `core_listing` 칸 (규격 `VOLVO_SELEKT_API.md` 2장). |
| `analyze/axis/taste.py` | 248 | ④ 취향 50점 — HUD 15 · 선루프 10 · 색상 10 · 지정 옵션 15. |
| `tests/test_registry.py` | 245 | 8장 등록부 시험. |
| `tools/collect_volvo.py` | 245 | 볼보 셀렉트 수집 — xhr-results 쪽넘김 (명령서 1a). |
| `tools/undo_wrong_gone.py` | 243 | ★★★★★ 잘못 매긴 `gone` 을 되돌린다 (마스터 0a·0c · 08-30). |
| `analyze/axis/site.py` | 240 | ⑤ 사이트 보증 50 · ⑦ 제조사 보증 50 (일반 20 + 동력계 30). |
| `tests/test_invariants.py` | 239 | 불변식 시험. |
| `tools/raw_lifecycle.py` | 235 | 원문 파일·행의 살림 — ★ 마스터 지시 09-01. |
| `tools/collect_reborncar.py` | 230 | 리본카 수집 — 사이트맵 전량 → 우리 쪽에서 거른다 (명령서 39). |
| `tools/collect_heydealer.py` | 226 | 헤이딜러 수집 — 토큰 → 차종별 목록 → 상세 (명령서 37). |
| `tools/repair_facet_chunks.py` | 222 | 낱개로 저장된 facet 조각을 이어붙인다 (개정 307 사고 복구). |
| `tools/collect_bobaedream.py` | 220 | 보배드림 수집 (명령서 7단계 · `docs/BOBAEDREAM_API.md`). |
| `tools/collect_revolt.py` | 215 | 리볼트 수집 (규격 `docs/REVOLT_API.md` · 마스터 확정 09-01 · `S46-200`). |
| `web/context.py` | 213 | 화면 문맥과 오류 (14장 STEP 144 · 148). |
| `validate/base.py` | 212 | 검증 계약. |
| `tools/unknown_split.py` | 210 | 「확인 안 됨」을 ①②③④ 로 가른다 (개정 434 · 435 · V1-27 · V1-28). |
| `parse/bmw_bps/mapping.py` | 208 | BMW BPS 상세 파서 (`docs/BMW_BPS_API.md` 08-29 절). |
| `tests/seed.py` | 204 | 시험용 씨앗 DB — 운영 DB 를 복사하지 않는다. |
| `tools/migrate.py` | 203 | 스키마 이행 — 기존 DB 를 현재 DDL 에 맞춘다. |
| `parse/bobaedream/mapping.py` | 196 | 보배드림 상세 → `core_listing` (`docs/BOBAEDREAM_API.md` 2·3·1a장). |
| `score/penalty.py` | 196 | 마이너스 점수 (개정 322). |
| `parse/lexus_certified/mapping.py` | 195 | 렉서스 인증중고 목록·상세 → `core_listing` 칸 (규격 `LEXUS_CERTIFIED_API.md` 2장). |
| `tools/sync_target_map.py` | 195 | 차종 대응표 → `dict_enum` (명령서 `ORDER_20260822_r515.md` 2a장 · 개정 540). |
| `analyze/axis/value.py` | 188 | ① 값 250 — 시세 대비 100 · 신차가 대비 80 · 주행 대비 70. |
| `parse/kbchachacha/inspection.py` | 183 | KB차차차 성능점검부 → ★ **부위별** (규격 `KBCHACHACHA_API.md` 3장 · 268~269줄). |
| `parse/importer.py` | 182 | 반입 입력 해석 (13장 STEP 136a · 136b). |
| `tools/list_diff_check.py` | 182 | 목록 대조 — ★ **사라진 것은 상세로 확인한 뒤에 죽인다.** |
| `tools/make_field_map.py` | 182 | ★★★★★★ 09-05 — ★ **사이트별 매핑표를 가이드가 만든다** (마스터 지시). |
| `collect/worker.py` | 180 | 큐 소비기 (13장 STEP 132a · 개정 261). |
| `tools/run_tests.py` | 180 | 시험 전체 실행. |
| `score/grade.py` | 178 | 등급 (L7). |
| `tools/measure_0k.py` | 176 | ★ 0k (명령서 r974 뒤) — ★ **잰다.  안 고친다.** |
| `tools/classify_unclassified.py` | 175 | 미분류 경로를 원인별로 가른다 (개정 341 · V4-26 · V4-27). |
| `web/session.py` | 175 | 세션 · CSRF · 정적 파일 (14장 STEP 145~147). |
| `analyze/axis/spec.py` | 172 | 사양 90점 — HUD 20 · 선루프 20 · SVM 10 · SCC 10 · 후측방 5 · 틴팅 5. |
| `tools/collect_bmw.py` | 171 | BMW 바바리안(BPS) 수집 (명령서 1a). |
| `tools/collect_lexus.py` | 171 | 렉서스 인증중고 수집 (명령서 1a). |
| `tools/daily_check.py` | 170 | 일일 점검 — 매일 23:00 (개정 334 · S29). |
| `store/pii.py` | 169 | 개인정보 분리 (L4). |
| `tools/collect_kia_cpo.py` | 169 | 기아 인증중고차(CPO) 목록 수집 (명령서 `ORDER_20260822_r515.md` 3-1 · 단계 8). |
| `parse/kia_cpo/mapping.py` | 164 | 기아 인증중고차(CPO) 원문 → CORE 필드 (L3). |
| `tools/weekly_check.py` | 163 | 주간 일제 점검 — 금 02:00 · 개발측 몫 (개정 334 · S29). |
| `adapters/kbchachacha.py` | 161 | KB차차차 어댑터 — URL · 헤더 (1장 STEP 11). |
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
| `collect/sweep.py` | 147 | 철학 ② — ★ **팔린 것은 대조하고 치운다** (마스터 확정 09-03 · `S46-267`). |
| `tools/classify_registry.py` | 144 | 등록부 미분류 정리 — 근거가 있는 것만 (8장 STEP 87 · V4-11). |
| `analyze/axis/history.py` | 143 | ③ 이력 80 — 어떻게 쓰였나 (docs/ref/F-scoring.md ③). |
| `collect/fetcher.py` | 141 | 원문 획득 · 형식 검증. |
| `tools/browser_verify.py` | 140 | ★★★★★ 09-02 — ★ **배포를 브라우저로 확인한다** (`S46-253`). |
| `tools/classify_fields.py` | 139 | 등록부 분류 초안 — 파서가 쓰는 경로를 근거로 자동 분류한다. |
| `tools/check_all.py` | 137 | 실측 DB 회귀 — V1~V5 · V10 전건을 한 번에 돌린다. |
| `tools/fold_out_of_scope.py` | 137 | 이미 들어온 것을 ★ 되돌린다 — ★ 우리 대상이 아닌 것은 ★ 접는다 (명령서 3-3). |
| `parse/classify.py` | 136 | 분류 2단 — target_key 판정. |
| `tools/recalc_catchup.py` | 136 | 재판정이 밀렸으면 채운다 (명령서 14-3 · 마스터 지시 08-24). |
| `tools/trace_verify.py` | 136 | 추적표 「상태」를 사실로 (개정 349 · 350 · S34). |
| `tools/fetch_dimensions.py` | 134 | ★★★★★ 제원(전장)을 ★ **브라우저로** 받는다 — 명령서 10번 (`S46-233`). |
| `adapters/heydealer.py` | 127 | 헤이딜러 어댑터 — 토큰 두 걸음 (명령서 37 · `docs/HEYDEALER_API.md` 0장). |
| `analyze/axes.py` | 126 | 축 판정 계약. |
| `tools/mark_shell_raw.py` | 120 | 원문이 `ok` 인데 규격 열쇠가 없는 것을 되돌린다 (09-03). |
| `adapters/kia_cpo.py` | 118 | 기아 인증중고차(CPO) 어댑터 — URL · 헤더 (1장 STEP 11). |
| `tools/gen_table.py` | 117 | 배점표를 config 에서 생성한다 (개정 512). |
| `adapters/kcar.py` | 115 | K카 어댑터 — URL · 헤더 (12장 · STEP 11). |
| `errors.py` | 115 | 도메인 예외 5종. |
| `tools/fix_407_not_found.py` | 111 | 4-4 — ★ **407 이 `not_found` 로 굳은 자리를 푼다** (지시문 r1141 · `S46-267`). |
| `tools/classify_stored.py` | 110 | 저장된 매물을 ★ 갈래에 넣는다 — ★ 사이트 도구가 쓴 줄용 (명령서 37·39). |
| `tools/report_cli.py` | 109 | 리포트 재생성 (9장 STEP 90 · 91a · B-6). |
| `tools/fill_photos.py` | 108 | ★★★ 이미 받아 둔 원문에서 ★ 사진을 채운다 (명령서 73장). |
| `tools/probe_kb_wall.py` | 106 | KB 봇 차단을 ★ 재는 도구 (명령서 08-25 · 마스터 「가려 받지 마라」). |
| `parse/kbchachacha/record.py` | 98 | KB차차차 상세 → `core_record` (명령서 r1007 · 1-5 · 로드맵 차례 1). |
| `tools/daily_collect.py` | 98 | 아홉+한 사이트를 하루 한 번 받는다 (ORDER_20260829 1순위 2 · S46-127). |
| `store/tools.py` | 97 | 관리 도구 (13장 STEP 135). |
| `adapters/generic.py` | 96 | ★★★★★ 09-03 (가이드 지시 ①) — ★ **config 의 길만 읽는 어댑터.** |
| `analyze/verdict.py` | 94 | 판정 엔진 — 순서 무관 put(). |
| `parse/target_rules.py` | 93 | 차종군 + `targets.json` 규칙으로 ★ 갈래를 고른다. |
| `tools/export_cli.py` | 93 | 데이터 내보내기 (9장 STEP 91a · B-6). |
| `tools/link_catalog_key.py` | 92 | ★★★★★ 08-31 (로드맵 차례 2) — ★ `model_catalog_key` 를 아홉 사이트에 잇는다. |
| `tools/setup_check.py` | 92 | 착수 점검 — 실행 전에 무엇이 준비됐는지 한 번에 본다. |
| `analyze/axis/price.py` | 90 | 가격 200점. |
| `analyze/absolute.py` | 88 | E등급 절대조건 10종. |
| `adapters/bobaedream.py` | 87 | 보배드림 어댑터 — URL · 헤더 (1장 STEP 11). |
| `parse/mpark/inspection.py` | 85 | m-park 성능점검 창구 → 우리 꼴 (로드맵 차례 4 · KB 점검표). |
| `tools/sweep_sold.py` | 84 | 철학 ② — ★ **팔린 것을 치운다** (마스터 확정 09-03 · `S46-267`). |
| `analyze/axis/trim.py` | 83 | ④ 사양 45 — 트림 25 · 옵션 20 (docs/ref/F-scoring.md ④). |
| `tools/deploy_check.py` | 81 | 배포 확인 — ★ 「소스가 맞다」와 「마스터 화면이 맞다」는 다른 말이다. |
| `analyze/peer.py` | 80 | 유사군 — 「이런 차가 보통 얼마인가」 (7장 STEP 82e). |
| `report/why_cheap.py` | 80 | 「왜 싼가」 — 싼 이유를 순서대로 찾아 낸다 (개정 299 · V3-52). |
| `store/chunk.py` | 77 | 조각 전송 — 바이트를 나누고 서버가 이어붙인다 (개정 307). |
| `tools/inspect_dict.py` | 75 | 사전 검토 — pending 값과 원문 표본을 본다. |
| `tools/inspect_facet.py` | 74 | facet 원문에 실제로 어떤 축이 왔는지 본다. |
| `tools/backfill_vehicle_id.py` | 71 | ★★★★★ 09-03 (2부 S6) — ★ **차량 키가 빈 매물을 채운다.** |
| `tools/undo_wrong_out_of_scope.py` | 71 | ★ 잘못 내린 `out_of_scope` 를 되돌린다 (09-04 · `tools/undo_wrong_gone.py` 와 같은 꼴). |
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

## 큰 파일 — 무엇이 어디에 (200줄 이상 94개)

### `validate/v0_guide.py` — 7,718줄

```
_read:25  s43_2_axis_ids:32  s44_4_scope_written:70  s44_5_site_consistent:102  s45_1_one_version:135  _order_files:158  s44_1_order_exists:171  s44_2_one_order:213  s43_2b_axis_renamed:228  s43_2c_no_hda:254  s45_5_no_axis_scores:308  s45_4_table_generated:346  s45_3_spec_totals:361  s45_2_mock_numbers:435  s44_3_specs_in_order:456  s43_3_version_matches:494  _h_tags:535  s46_21_one_screen_per_file:551  s46_22_section_order:576  _targets:645  s46_23_site_query_filled:651  s46_24_facet_unconfirmed:666  s46_30_index_covers_docs:691  s46_31_spec_sites_in_config:730  s46_32_generated_fresh:751  _req_rows:793  _tokens:805  _named_docs:820  s46_36_dropped_not_alive:832  s46_40_progress_docs_changed:860  s46_41_site_status_known:891  _templates:933  s46_45_spec_not_in_list:938  s46_46_spec_forbidden_ten:958  s46_66_links_encoded:984  s46_65_verdict_fresh:1023  _sian_files:1061  s46_67_sian_names_dont_clash:1070  s46_68_watch_is_mobile_first:1133  s46_74_rows_per_page:1187  s46_75_v4m_common:1233  s46_76_collectors_keep_raw:1273  s46_115_run_screen_still:1311  s46_125_sort_axes_really_sort:1340  s46_118_heart_has_anchor:1371  s46_121_header_rule_in_one_place:1411  s46_116_reasons_in_plain_words:1433  s46_120_registry_key_matches:1460  s46_123_toss_palette_only:1496  s46_122_shared_fragments:1538  s46_128_batch_gives_a_window:1582  s46_127_collector_has_screen_or_timer:1626  s46_124_db_opened_with_pragmas:1674  s46_126_fetch_outside_transaction:1710  s46_117_collectors_sweep_gone:1744  s46_77_kb_is_our_targets_only:1793  s46_78_encar_only_paths_are_scoped:1849  s46_87_request_site_matches_listing:1891  s46_88_encar_blocked_banner:1968  _paired_rows:2033  _grade_order_list:2073  s46_54_grade_two_step:2085  s46_55_price_gap_30:2110  s46_56_accident_split:2136  s46_90_pending_not_graded:2176  _registrable:2225  s46_94_source_url_site_matches:2239  s46_91_raw_vs_stored:2283  s46_97_raw_linked_by_source_id:2355  s46_99_login_then_watch:2423  _logged_opener:2519  _sian_seq:2558  s46_100_sian_word_order:2590  s46_102_electric_only_is_electric:2727  s46_103_sian_values_carried:2779  s46_98_sian_words_on_screen:2820  s46_95_screens_alive:2938  s46_96_site_sells_but_no_code:2994  s46_92_browser_zero_count:3073  s46_161_no_unproven_absence:3142  s46_162_promised_checks_exist:3191  s46_145_numbers_have_meaning:3221  s46_155_screen_spec_has_mockup:3250  s46_163_mockup_has_route:3283  _guide_docs:3314  s46_129_table_sum_counted:3323  s46_132_handover_says_remeasure:3355  s46_140_new_host_has_robots:3369  s46_142_site_count_matches:3388  s46_146_absence_needs_parser_check:3423  s46_154_master_wish_in_registry:3445  s46_131_paging_claim_measured:3467  s46_135_generalisation_has_sample:3489  s46_138_all_claim_needs_source:3506  s46_149_confession_is_closed:3530  s46_156_answer_touches_spec:3557  s46_130_one_tally_per_register:3583  s46_134_target_site_pair:3600  s46_141_filter_claim_measured:3626  s46_143_master_items_are_master:3643  s46_147_absence_needs_ten:3678  s46_150_column_from_ddl:3700  s46_133_check_gap_in_pending:3722  s46_136_warn_number_moves:3740  s46_137_config_key_has_reader:3762  s46_139_field_claim_counted:3791  s46_148_axis_gap_traced:3808  s46_152_dev_rounds_read:3826  s46_159_design_is_doable:3859  s46_144_empty_is_split:3878  s46_153_owner_is_judged:3895  s46_157_perf_claim_is_timed:3927  s46_158_size_claim_is_measured:3945  s46_160_ev_leak_full_mark:3963  s46_164_dev_pending_answered:3980  s46_165_fixable_not_called_unmeasurable:4014  s46_166_decision_reached_chapters:4055  s46_168_check_counts_exceptions:4085  s46_169_gone_has_reason:4124  s46_170_one_architecture:4141  s46_171_yardstick_names_screen:4159  s46_172_absence_read_as_human:4178  s46_173_endpoint_not_wordcount:4202  s46_174_no_endpoint_only_if_probed:4227  s46_175_no_lumped_axes:4254  s46_176_guide_probes_sites:4287  s46_177_catalog_not_site_locked:4315  s46_178_list_field_not_empty_axis:4340  s46_179_no_penalty_without_source:4365  s46_180_code_table_per_site:4379  s46_181_read_stored_before_probing:4406  s46_182_all_sites_before_claiming_all:4425  s46_183_master_only_after_probing:4453  s46_184_unfetched_is_not_absent:4482  s46_185_file_is_the_原本:4510  s46_186_grade_distribution_watched:4540  s46_187_cheaper_scores_higher:4554  s46_188_screen_before_claiming_missing:4581  s46_191_budget_follows_fuel_rule:4605  s46_192_pref_brands_registered:4651  s46_202_no_raw_template_tags:4676  s46_227_absent_only_declared:4689  s46_213_recommend_has_no_sold:4740  s46_203_new_site_has_target_keys:4786  s46_203_collect_writes_files_first:4818  s46_205_no_raw_response_writes:4846  s46_206_pdf_link_only:4881  _retired_s46_207_says_measured:4913  s46_207_commit_title_says_fact:4947  s46_208_market_no_negative:4985  s46_214_photo_uses_space_below:5004  s46_215_collector_respects_active:5029  s46_229_recommend_not_active_off:5055  s46_230_schema_change_counts_one_run:5083  s46_231_all_sites_in_filter:5113  s46_232_budget_curve_is_log:5140  s46_233_size_axis_never_zero:5184  s46_234_top_site_sweeps_gone:5223  s46_235_screen_hides_unsellable:5255  _recommend_rows_once:5297  s46_240_all_indexes_exist:5315  s46_237_recommend_in_budget:5356  s46_236_interior_color_axis:5388  s46_238_trim_not_double_counting:5423  s46_241_regrade_alive_on_deploy:5446  s46_242_mock_has_required_header:5541  s46_243_empty_says_why:5565  s46_244_failed_response_kept:5595  s46_245_each_screen_has_its_parts:5615  s46_246_every_screen_has_a_mock:5650  s46_253_browser_confirms_deploy:5684  s46_247_site_coverage:5754  s46_248_grade_is_realistic:5820  s46_249_budget_pairs_are_masters:5854  s46_250_mock_has_real_shape:5883  s46_251_vehicle_key_per_site:5916  s46_252_admin_write_actually_saves:5946  s46_253_part1_seen_in_browser:5978  s46_254_pair_badge_not_by_order:6021  s46_255_tester_items_listed_one_by_one:6055  v0_01_version_matches_history:6077  v0_02_retired_marks_match:6103  v0_03_points_only_in_appendix:6129  v1_22_site_given_is_not_remade:6171  _file_detail_ids:6214  _rates_in:6232  s46_261_report_matches_deploy:6256  s46_256_blocked_needs_evidence:6356  s46_257_pipeline_not_encar_only:6387  _as_check:6420  results:6434  save:6473  run:6484  s46_258_part_axis_decided:6509  s46_259_master_target_names:6541  s46_260_end_signal_not_empty_pages:6599  s46_262_dev_questions_answered:6624  s46_263_four_states_and_pending:6656  s46_264_deploy_is_up:6695  s46_265_raw_purged_after_load:6738  s46_266_detail_not_refetched:6775  s46_267_sold_swept_after_detail:6797  s46_268_order_is_one_and_current:6822  s46_269_recommend_set_and_chips:6857  s46_270_hidden_text_ruler:6902  s46_273_axis_score_filled:6934  s46_271_screen_checked_in_browser:6984  s46_272_photo_url_only_max20:7044  s46_273_encar_banner_counts_browser:7074  s46_274_default_sort_grade_price_rank:7102  s46_275_axis_score_persisted:7129  s46_276_encar_collect_no_gap:7159  s46_277_admin_query_allows_order_limit:7215  s46_278_kb_saves_blocked_raw:7240  s46_279_kb_fields_filled:7279  s46_280_all_sites_no_gap:7329  s46_281_option_names_collected:7386  s46_282_field_map_by_site:7413
```

### `validate/v11_web.py` — 5,057줄

```
_web_sources:644  run:656  _late_checks:766  _templates_with_form:830  _spec_routes:851  _screen_routes:876  _routing_table_check:900  _count:937  ctx_account:944  _view_exists:950  _tpl:971  _all_templates:976  _screen_checks:981  _query_budget_check:1235  _import_origin_check:1314  _import_step4_check:1349  _browser_origin_check:1373  _browser_confirm_check:1391  _browser_chunk_check:1416  _status_screen_checks:1474  _status_liveness_check:1512  _menu_label_check:1561  _menu_paths:1589  _listing_rows:1614  _cli_caps:1632  _cli_only_check:1646  _stale_notice_check:1691  _trim_detail_check:1727  _option_sum_check:1750  _heart_line_check:1777  _recommend_terms_check:1798  _lease_checks:1817  _pick_filter_checks:1877  _shortfall_check:1916  _cash_limit_check:1935  _py_files:1966  _menu_no_path_check:1980  _listing_paging_checks:1998  _photo_checks:2034  _compare_shape_check:2075  _detail_shape_checks:2125  _filter_shape_checks:2203  _row_shape_checks:2273  _menu_shape_checks:2345  _sian_css_checks:2428  _cell_of:2503  _link_tip_checks:2526  _origin_link_check:2540  _origin_opens_bad:2585  _choose_check:2634  _order_filter_checks:2650  _checks_cfg:2693  _photo_size_by_screen_check:2702  _template_leak_check:2726  _em_dash_check:2752  _card_limits:2788  _cells_of:2805  _matches:2833  _grid_areas:2853  _hidden_cells:2883  _brace_block:2908  _place_cards:2922  _card_shape_checks:3044  _why_order_spec:3142  _why_order_check:3159  _width_policy:3194  _width_checks:3201  _chart_check:3300  _row_link_checks:3331  _screen_contradiction_check:3367  _chunk_check:3389  _csrf_reuse_check:3429  _origin_price_check:3473  _with_includes:3509  _v1_parity_checks:3531  _media_blocks:3621  _responsive_checks:3642  _dead_links:3730  _null_link_check:3744  _sian_visual_check:3808  _purchase_cost_checks:3872  _report_popup_check:3965  _detail_photo_check:4039  _raw_shown_checks:4090  _compare_diff_check:4177  _chunk_message_check:4241  _whole_char:4268  _chunk_boundary_check:4281  _cell_squeeze_check:4369  _static_version_check:4424  _axis_state_check:4442  _three_values_check:4485  _photo_size_check:4524  _render_metrics_checks:4550  _browser_scope_checks:4649  _import_opened_steps_check:4670  _import_resume_check:4698  _watch_invite_check:4717  _post_smoke_check:4761  _template_roots:4834  _loop_fields:4844  _context_supplied_check:4866  _first_item:4937  _has_field:4951  _table_counts:4957  _save_button_check:4964  _probe:5021  _scratch:5039
```

### `report/screens/build.py` — 4,730줄

```
load_config:48  site_badge:119  axis_heads:138  _grade_order:148  _not_ranked:161  _labels:177  viewer_state:181  _unknown_cfg:191  is_unknown:200  chip:216  _stamp:252  _bulk_axes:256  confirm_ratio:277  _bulk_changes:288  _total_points:315  _photo_note:327  photo_urls:363  photo_url:415  _deploy_is_https:454  _blocked_by_https:468  market_price:477  _days_between:494  _ceil_to:509  _bulk_market:524  _bulk_state:563  not_join_months:596  _left:619  _warranty_state:628  _axis_state:666  _sites_cfg:734  _row:747  _pen_rows:1007  _pen_axes:1018  _pen_sum:1038  _pen_words:1046  _ym_parts:1059  _age_label:1071  _km_per_year:1092  _pen_top:1112  _view_cfg:1126  _grade_rank_sql:1140  _sold_words:1195  _order_sold:1213  order_clause:1228  _site_detail_urls:1258  _source_url:1295  _view_str:1325  _lease_kinds:1330  paused_hidden:1337  _topic:1374  paired_count:1385  excluded_hidden:1408  lease_hidden:1424  _option_blind_sites:1446  _option_group_match:1463  fuel_groups:1477  _fuel_where:1488  _paused_sites:1514  _listings_where:1543  model_counts:1823  count_listings:1850  view_listings:1867  _market_gap_label:2031  _score_bars:2047  _group_caps:2078  _view_list:2099  _view_dict:2104  _soh_low:2109  _view_int:2118  _bucket:2123  _high_km:2130  _option_prices:2139  recommend_funnel:2151  _bulk_upside:2169  view_recommend:2184  recommend_reason:2219  excluded_groups:2264  view_why:2282  _compare_conclusion:2292  view_compare:2315  market_trims:2382  view_market:2404  _web_cfg:2440  _median:2454  _with_height:2459  _price_bins:2474  _group_prices:2495  _by_year:2513  _year_line:2530  _by_trim:2556  _other_targets:2574  count_dealers:2583  _dealer_targets:2589  region_of:2609  _region_short:2636  _dealer_region:2656  view_dealers:2671  view_run:2707  _rank1_of:2713  view_dashboard:2721  _bars:2858  _grade_counts:2873  _relax_sim:2891  _axis_shortfall:2912  _progress:2931  _gone_and_watch:2946  _e_reasons:2989  _today_changes:3007  _step_rows:3032  _bulk_spark:3049  view_watch:3085  _man:3185  _mmdd:3199  _chg:3212  _gap:3227  _days_since:3242  _pending_values:3267  _done_items:3276  view_notready:3302  _unmatched_rows:3343  _report_files:3388  view_reports:3420  _warranty_until:3476  _verdict_lines:3525  _manwon_str:3567  _unknown_lines:3574  _price_history:3606  _alternatives:3623  _rep_flt:3659  view_detail:3665  _quartiles_by_target:3707  market_by_target:3731  _grade_order:3768  _grade_step:3783  _miss_axes_bulk:3789  _sold_int:3837  _sold_where:3845  _days_between:3855  view_sold:3870  _sold_bins:3948  _pair_rows:4006  _lease_words:4052  view_track:4066  _accident_bulk:4194  duplicate_listings:4209  _today_counts:4261  _notready_counts:4285  axis_zero_rates:4305  _recommend_year_from:4345  _recommend_models:4357  _active_targets:4429  view_recommend_tabs:4448  _ym_dash:4662  _first_photo:4670  _site_labels:4680  _recommend_axes:4687  _axis_labels:4721
```

### `web/views.py` — 2,939줄

```
_rows_per_page:31  _cfg:35  _versions:40  page_extras:59  _points:68  page:90  sold:117  listings:136  why:199  detail:251  _grade_help:284  notready:291  dashboard:301  admin_home:323  _unclassified_split:335  _rows_of:363  _check_reports:373  admin_audit:396  admin_docs:409  _int_param:433  _manwon:472  _site_buttons:477  _fallback_sites:538  _filter_chips:550  _order_menu:604  _carry:610  _order_label:620  ORDERS_LABELS_GET:624  _condition_sentence:628  _query_string:646  _page_links:659  _simple_paging:680  _paging:690  _filter_buttons:720  _model_menu:753  _pick_state:770  _option_name_buttons:836  _color_menus:897  _judge_buttons:912  _split_top:940  _fuel_options:946  _distinct_options:957  _km_options:969  _grade_options:977  _keep_query:984  _carry_pick:1009  _lease_hidden:1019  _paused_note:1025  _paired_url:1045  _paired_n:1054  _excluded_hidden:1060  _excluded_why:1067  _filter:1077  recommend:1168  _recommend_old:1204  track:1237  compare:1254  market:1276  _first_target:1296  dealers:1302  watch:1322  _note_kinds:1339  _watch_notes:1346  run_view:1373  login:1385  _login_again:1427  _open_session:1443  logout:1484  _watch_queries:1501  watch_query_post:1510  _int_or_none:1540  watch_add_post:1544  _watch_note_post:1604  _watch_invite:1630  watch_update_post:1653  _now:1677  _reason_gate:1684  _said:1709  _gate:1714  _first_flag:1753  _all_hours:1758  admin_run:1786  _target_rows:1854  admin_dict:1867  admin_status:1904  admin_collect:1919  _take_chunk:1989  _verify_part:2032  _run_stamp:2072  _int_or_none:2083  admin_import:2088  admin_scoring:2160  _decide_cards:2228  _unclassified_count:2256  admin_registry:2265  admin_query:2362  admin_requests:2384  _admin_extra:2446  _config_files:2461  _config_rows:2468  admin_config:2500  _typed:2551  admin_api:2567  _site_query:2617  admin_targets:2630  admin_tools:2728  join:2747  password:2778  admin_users:2793  _account_activity:2853  reports:2859  report_download:2875
```

### `validate/v3_logic.py` — 2,329줄

```
_file_output_checks:384  _conflict_checks:437  _diagnosis_count_check:461  _sort_determinism:478  _warning_contract_checks:500  _list_observed_source_check:595  _facet_reconcile_check:625  _record_mismatch_check:669  _curve_table_check:699  _special_null_check:772  _grade_base_checks:800  _checks_cfg:893  _labels_cfg:907  _unknown_mark_checks:915  _grade_cut_checks:966  _points_cap_checks:1089  _worse_of_checks:1141  _checks_json:1203  _value_curve_checks:1214  _group_sum_checks:1319  _mapped_other_check:1430  _denominator_check:1457  _core_axis_check:1485  _rental_cross_check:1506  _why_cheap_check:1544  _source_before_value_check:1585  _absolute_cut_check:1620  _spec_files:1650  _confirm_ratio_check:1660  _warranty_checks:1710  _spec_axis_check:1744  _site_axis_checks:1785  _rendered_why:1842  _rendered_listings:1852  _fill_gap_check:1862  _points_sum_check:1895  _market_gap_check:1920  _bonus_checks:1976  _trim_price_check:2080  run:2137  _shuffle_check:2272  _halt_dict_check:2297  _ensure_tmp:2326
```

### `store/core.py` — 2,108줄

```
resolve_listing_id:38  resolve_dealer_id:56  serialize_container:72  record_change:83  split_pii:111  flush_dealer_pii:163  _record_dropped:175  classify_invariant_change:210  _lookback:271  _source_history:285  _schema_change_min:314  _current:328  _today:334  _photo_max:351  _cap_photos:369  _drop_non_values:393  origin_dropped:405  _drop_impossible_origin:410  _note_skipped:439  upsert_core:460  mark_gone:588  mark_relisted:612  sweep_gone:639  sweep_gone_groups:683  load_snapshot:725  build_identities:838  resolve_vehicle_id:864  merge_conflict:896  upsert_vehicle:907  upsert_dealer:928  dealer_trust:955  _trust_cfg:1048  upsert_child:1065  _flag:1086  _not_join_months:1100  state_counts:1125  current_versions:1178  diagnosis_of:1208  target_counts:1221  top_target:1228  vehicle_of:1233  collect_scale:1240  our_fault:1260  catalog_coverage:1269  _walk:1313  _sample_bodies:1329  hits_of:1342  key_seen:1361  stored_hits:1376  sample_bodies:1392  observed:1414  known_leaves:1452  has_unclassified:1467  classify_unclassified:1474  _card_limit:1517  _value_chars:1522  _admin_cfg:1527  unclassified_cards:1544  _peek:1600  _short:1647  _blocking_paths:1658  _raw_rows_max:1678  used_endpoints:1688  raw_sections:1697  _flatten:1736  option_diff:1760  _option_names:1798  blocking_keys:1814  full_hits:1832  axis_paths_empty:1857  blocking_rows:1894  record_mismatch_sql:1956  record_mismatch_count:1962  relist_counts:1988  listing_models:2005  filter_options:2025  site_counts:2042  unscored_count:2055  photo_ready_sites:2072  unclassified_fields:2097
```

### `collect/runner.py` — 2,071줄

```
CollectGroup:67  load_targets:91  collect_groups:104  facet_axes:172  aspect_names:193  check_facet_axes:197  interpret_failure:211  _detail_calls:240  collect_check:254  FailStreak:324  _sleep:358  _log_request:373  _save_issues:384  _master_line_only:395  make_executors:410  classify_in_group:1226  _query_key:1255  _group_of:1263  _fuel_of:1278  _badge_of:1284  _pages_for:1290  _dicts:1304  _option_medians:1346  _lease_types:1392  _market_medians:1406  _trim_ladders:1463  _option_base:1480  _site_grade_rules:1510  _cfg_num:1529  _dimensions:1545  _listing_config:1574  _listing_values:1601  _option_money:1620  _owned_months:1639  _option_of:1651  _market_of:1659  _group_sums:1669  _origin_lend_table:1697  _origin_keys:1727  _origin_lent:1746  make_score_executors:1766  make_validate_executor:2000  make_registry_executor:2042
```

### `tests/test_spec_ui.py` — 1,494줄

```
rec:33  spec_a:43  spec_b:121  spec_c:195  spec_d:239  spec_f:281  spec_g:316  spec_h:364  spec_j:397  spec_m:440  spec_e:508  spec_i:551  spec_k:664  spec_csrf:719  spec_l:746  spec_monkey:788  flow_s1:860  flow_s2:929  flow_s5:1013  flow_s3:1126  flow_s4:1201  flow_s6:1272  guide_v132:1328  main:1428  _write:1472
```

### `tests/test_integration.py` — 1,276줄

```
rec:31  Client:41  text:96  links:101  start_server:105  seed_admin:149  m1:165  m2:261  m3:335  m4:664  s3:735  unit:801  gaps:836  flows:944  guide7:1047  _account_id:1180  make_users:1187  main:1205  _write_table:1254
```

### `tools/check_src.py` — 1,201줄

```
_spec_files:45  _read_spec:63  _record:86  say:117  py_files:132  chapter_of:172  _declared_chapters:182  split_done:202  _illustration:221  _retired_config_keys:285  _git:746
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

### `report/render.py` — 1,042줄

```
_labels:31  _site_blind_axes:36  _stamp:77  _curve_points:92  source_detail_url:135  _why_cheap_of:156  _scoring:197  _record_cols:208  record_rows:217  _penalty_rows:271  _market_pos:285  _site_badge:329  _axis_why:336  _raw_sections:366  _photo_why:376  _photo_urls:397  _purchase_costs:420  _unknown_axis_cfg:448  render_listing:471  axis_mark:649  source_label:674  _option_rows:722  _fetch_views:782  _strengths:797  _weaknesses:804  _pending_best:811  _cost_rows:844  _known_issues:865  _diagnosis_view:883  render_target:894  render_run:975  render_halt:1017  _j:1035
```

### `validate/v10_admin.py` — 936줄

```
_sources:212  _admin_guard_checks:233  _sql_strings:278  _schedule_checks:290  _query_error_checks:333  run:434  _session_checks:579  _pii_query_check:659  _scratch:706  _dict_reason_check:721  _dict_source_shown_check:737  _automation_checks:755  _queue_consumer_check:888  _queue_stale_shown_check:917  _ensure_tmp:933
```

### `tests/test_score.py` — 928줄

```
check:36  fx:42  snap:46  ctx:66  full_verdict:87  test_denominator:100  test_components_form:151  test_grade:202  test_order_independent:291  panels_of:314  test_history_real:319  test_rental_real:354  test_insurance:396  test_safety_real:421  test_spec_gate:470  test_price_real:549  test_color:663  test_price_pending:710  test_absolute_real:729  test_null_safe:769  test_empty_array_meaning:786  test_peer_group:811  test_damage_by_status:853  test_repair_cost_ratio:879  test_hda_gate:888
```

### `report/screens/views.py` — 920줄

```
AxisChip:30  ScoreBar:55  AxisPoint:71  ListingRow:87  ListingFilter:269  WatchRow:369  TargetStat:412  RelaxRow:421  MarketRow:428  ChangeRow:440  AttentionItem:450  ViewerState:458  DashboardView:472  CompareView:509  TrackPair:527  TrackView:566  MarketView:592  DealerRow:607  SoldBin:628  SoldRow:644  SoldView:674  NotReadyView:694  TodayChange:725  StepRow:737  _min_sample:749  PendingValue:767  Bucket:780  ExcludedGroup:800  ReportFile:809  ReportsView:821  RecommendAxis:843  RecommendRow:853  RecommendView:902
```

### `validate/v2_load.py` — 919줄

```
DayGapReport:151  GapCause:164  run:170  _surrogate_key_checks:347  _not_null_check:432  _chained_subscript_check:449  _Boom:497  _salvage_check:505  _table_exists:546  _exception_shape_checks:552  _schema_sync_check:618  _pii_access_check:655  gap_alerts:694  diff_prev_day:710  explain_gap:732  _pii_column_check:764  _secret_key_check:782  _parser_common_fields_check:820  _null_target_not_judged_check:871  _null_target_visible_check:896
```

### `validate/v1_collect.py` — 910줄

```
_unknown_split_checks:171  _axis_empty_check:257  run:287  _endpoint_order_check:421  _empty_db_check:433  _sql_groups:460  _cumulative_codes:496  _run_scope_check:506  _ctx_started:544  _has_run_id:552  _expected_scope_check:557  _diagnosis_scope_check:578  _diagnosis_none_count:618  _query_key_check:643  _entrypoint_parity_check:689  _enclosing_def:718  _run_id_filled_check:727  _catalog_key_check:747  _whole_probe:769  _whole_body_check:780  _catalog_checks:816  _unparsed_envelope_check:863  _ensure_tmp:907
```

### `tools/trace_fill.py` — 840줄

```
spec_lines:94  anchor_step:112  build_symbols:131  enclosing:166  build_texts:176  _stem:214  tokens:223  _best_in:253  _rows:290  layers_of:303  layer_pool:310  _rare_hit:322  axis_words:346  json_key_at:367  _place:394  _hints:405  find_in_layer:421  _best_step_in:469  _layers:500  derive_state:520  src_mark:546  relayer:559  restate:574  fill_file:597  move_to_rules:665  survey:708  lists:736  write_index:757  main:796
```

### `collect/pipeline.py` — 792줄

```
envelope_scope:41  Reprocess:91  refetch_all:121  reprocess_plan:131  should_refetch:148  expected_for:160  step_report:194  halt_if:210  precheck:260  resume_point:314  config_hash:334  build_run_context_fields:340  stale_rows:349  save_step_report:364  rss_mb:388  run_step:407  _execute:445  completed_steps:464  run_pipeline:476  print_progress:525  silent_progress:544  from_step_for:558  web_reasons:588  check_recalc_origin:593  plan_recalc:605  _current:622  run_recalc:628  Defect:649  DefectReport:660  diagnose:681  _DiagCtx:705  _collect_defects:715  format_defects:769
```

### `tools/browser_diff.py` — 785줄

```
pairs:35  look:48  main:298  hidden_text_report:464  _site_report:598  encar_collect_report:658  kb_collect_report:751  all_sites_report:775
```

### `validate/v4_mapping.py` — 785줄

```
_paths:143  _layer_of:190  _unclassified_split:195  _layer_checks:233  _name_collision_check:329  _key:363  _decide_material_check:369  _blocking_list_check:433  run:490  _mapping_coverage_checks:639  _our_columns:669  _listing_value_scope_check:702  _dict_filled_check:722  _kind_check:733  propose_fix:747  _option_code_check:762  _is_sentence:779
```

### `tests/test_run.py` — 783줄

```
check:36  StubEncar:92  Clock:241  setup:246  test_envelope:284  test_last_page_exact:314  test_facet:321  test_facet_missing_axis:335  test_dict_step:344  test_all_groups:366  test_parse_pipeline:377  test_score_pipeline:481  test_validate:553  test_registry_gate:596  test_target_scope:653  test_catalog_key:685  test_wrapper_args:703  test_unclassified_listing:750
```

### `store/watch.py` — 746줄

```
AlertConfig:58  WatchItem:71  TrackPoint:86  TrackEvent:101  WatchEvent:115  _cross_site_order:130  classify_duplicates:149  sync_duplicates:202  deduped_count:226  watch_add:236  assert_owner:275  watch_update:290  watch_close:310  note_add:331  notes_of:356  note_delete:374  track_snapshot:389  track_points:418  classify_cause:427  detect_events:439  message:497  notify:525  _grade_order:596  _not_ranked:609  add_watch_query:623  run_watch_queries:658  watch_query_rows:714  close_watch_query:728
```

### `store/admin.py` — 716줄

```
_admin_cfg:46  ConfigChange:68  running_job:86  hash_secret:96  _split:104  create_account:109  account_count:145  needs_bootstrap:149  _recent_failures:161  _log_attempt:180  is_locked:190  unlock_account:205  authenticate:233  open_session:269  session_account:289  change_secret:306  revoke_sessions:330  _under_seed:353  _walk:361  get_path:385  set_path:390  _atomic_write:397  apply_config:407  _validate_blob:473  revert_config:495  history:519  classify_field:543  account_rows:616  admin_count:630  set_role:637  set_disabled:654  add_config_key:674
```

### `store/dictionary.py` — 693줄

```
CodeEntry:31  AxisPolicy:57  policy:122  scope_key:130  seed_fixed_enums:155  _with_site_query:214  target_map:257  target_key_of:294  fuel_normalize:329  collect_group_of:352  match_target_name:357  known_model_names:374  known_model_of:391  mapped_of:396  upsert_enum:417  _handle_conflict:469  upsert_option3:490  retire_unseen:526  resolve_code:541  installed_option_names:579  normalize_enum:597  assert_no_unknown:613  bump_dict_version:656  list_pending:666  confirm_enum:674
```

### `tools/backfill_from_raw.py` — 663줄

```
_now:28  latest_details:32  heydealer:44  kbchachacha:124  hyundai_cert:210  reborncar:259  out_of_scope:292  bmw_bps:328  kcar:366  _record_site:397  kb_record:424  volvo:434  volvo_detail:443  lexus_detail:471  kb_detail:500  _latest:566  mpark_inspection:578  main:644
```

### `tools/collect_kbchachacha.py` — 662줄

```
_now:104  _get:108  fetch_ok:117  page_ids:134  load_filters:144  walk_group:233  count_all:275  probe_detail:301  store_details:320  fetch_details:349  load_details:417  main:516
```

### `parse/encar/mapping.py` — 625줄

```
_get:30  _json:42  _won:53  _ym:73  _date10:83  _int:99  _bool:105  unpack_envelope:116  parse_list_item:124  parse_detail:171  parse_inspection:247  parse_record:295  _sample_chars:349  safe_field:363  parse_with_issues:385  _salvage:403  _parses:446  dig:453  as_list:476  _diag_comment:504  parse_diagnosis:511  parse_diagnosis_items:543  _text:551  parse_record_summary:561  parse_platform_check:587  parse_inspection_summary:594  parse_ev_battery:599  parse_sellingpoint:619
```

### `store/raw.py` — 617줄

```
_compress_cfg:59  pack_body:70  raw_body:91  _text_of:107  batch:134  tick:164  commit:199  _batch_commit_rows:226  _batch_commit_pause_ms:236  _busy_timeout_ms:261  connect_db:272  open_db:300  link_raws:311  _safe_headers:337  save_raw:344  proc_run_id:402  save_site_raw:412  save_import_raw:467  save_browser_raw:500  save_browser_facet:541  save_import_facet:567  save_facet:597
```

### `tools/build_index.py` — 589줄

```
guide_check_owners:48  _py_files:99  _checks_in_code:124  _guide_checks:170  _checks_in_docs:203  last_runs:236  _run_time:265  sort_checks:275  build_checks:292  _outline:366  build_source:377  build_schema:409  build_doc_index:468  check_fresh:533  main:566
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

### `web/app.py` — 555줄

```
menu_items:22  _tip:107  _label:112  empty_state:123  banner_of:142  _encar_blocked:203  _list_stale:242  static_version:268  build_page:296  check_post:317  redirect:339  take_flashes:359  _display_now:372  make_app:398  _Denied:531  build_context:539  _title_of:554
```

### `tests/test_web.py` — 522줄

```
check:21  test_routes:28  test_template:85  test_no_logic_in_template:126  test_static_escape:141  test_session_cookie:153  test_error_page:171  test_layout:198  test_filters:227  test_empty_state:250  test_menu_by_role:277  test_guard_and_csrf:298  _call:345  test_screens_render:362  test_sketch_match:453  test_account_policy:468
```

### `contracts.py` — 481줄

```
Response:24  Clock:34  Fetcher:39  Rng:44  Request:52  EndpointSpec:60  FetchResult:71  TargetSpec:84  ListingSnapshot:141  AxisResult:244  Account:263  require_role:280  RunContext:297  StepReport:317  ResumePoint:341  clean_vin:362  total_of:373  RegressionReport:386  json_paths:397  shape_ok:446  shape_violations:479
```

### `run.py` — 476줄

```
load:51  make_context:56  _filter_targets:70  _steps_from:89  _adapter_for:119  cmd_collect:137  _grade_summary:218  cmd_admin_create:233  _collect_urls:250  _page_url:287  cmd_web:306  make_worker_ctx:346  make_worker_executors:352  cmd_delegate:397  _api_fetch:408  cmd_setup:418
```

### `tools/load_raw.py` — 443줄

```
_now:76  query_target:80  body_target:119  _rows_from:145  _envs_from_db:225  main:269
```

### `report/views.py` — 419줄

```
VersionStamp:18  ReportMeta:30  AxisView:40  FinanceView:64  PurchaseCostItem:85  PurchaseCostView:94  DiagnosisView:118  FetchView:130  CostRow:144  ScoreView:153  CollectSummary:267  ClassifySummary:274  PriceSummary:281  AxisStat:290  CoefficientChange:300  DictChangeSummary:310  TargetReport:318  RunStep:330  RunReport:345  HaltReport:356  FixAction:373  NotifyResult:383  ExportResult:396  display_value:405  display_points:415
```

### `web/template.py` — 406줄

```
f_won:55  f_km:71  f_pct:75  f_date:79  f_num:90  f_gradecls:97  f_gradelabel:110  _grade_classes:125  f_count:134  f_signcls:142  f_signwon:152  f_url:160  _index_key:198  _step:213  _lookup:225  _truthy:234  render_str:238  strip_comments:345  expand_includes:350  render:387
```

### `tools/sync_registry.py` — 403줄

```
FieldUsage:40  RegistrySyncReport:57  facet_path:75  scan_paths:83  shape_ok:88  _walk_values:101  collect_values:115  collect_paths:141  _has_value:182  _seed_for:198  sync_registry:209  suggest_usage:304  write_suggested:316  halt_report:343  list_by_usage:366  assert_registered:373
```

### `tests/test_collect.py` — 401줄

```
_target_count:35  check:51  R:57  test_verify_shape:62  _Stub:97  _Clock:105  test_fetch_status:110  test_interpret_failure:123  test_facet_axes:135  test_collect_groups:163  test_build_q:191  test_collect_check:241  test_save_raw:256  test_fail_streak:285  test_all_fail_sample:327  test_diagnosis_scope:371
```

### `tests/test_pipeline.py` — 388줄

```
check:37  db:43  test_expected:49  test_halt:61  test_reprocess:82  test_refetch:107  test_precheck:115  test_resume_and_version:167  test_run_pipeline:195  test_recalc:230  test_pii_orphan:265  test_exception_becomes_halt:298  test_fixed_enum_bootstrap:319  test_envelope_scope:349
```

### `parse/hyundai_cert/mapping.py` — 374줄

```
_int:48  cards:57  _fuel_of:82  _model_group:93  parse_card:111  _json:183  detail_text:190  _one:197  parse_detail:202  parse_detail_all:208  _num:278  _warranty:285  _months_since:339  _months_left:351  _options:368
```

### `analyze/axis/state.py` — 355줄

```
_panels:43  _rank_worst:47  insurance_trace:59  panel_trace:68  worse_step:80  _accident:87  _frame:109  _outer:129  _repair:151  _special:162  leak_state:174  _is_ev:196  _ev_words:218  _leak:236  _site_never:253  _sites_table:265  _consumable:283  _integrity:311  analyze_state:347
```

### `tools/collect_hyundai_cert.py` — 351줄

```
target_of:79  _now:95  _post:99  _get:109  fetch_detail:120  load_filters:133  total_count:171  walk:184  main:216
```

### `parse/heydealer/mapping.py` — 348줄

```
_int:22  _won:29  _ym:34  _model_group:42  parse_list_item:60  parse_detail:89  fuel_efficiency_kmpl:117  options_of:124  record_of:153  warranty_of:206  _months_since:240  part_enums:252  panels_of:310
```

### `tools/light_check.py` — 340줄

```
_repair_max:45  _cfg:63  _run:77  collecting:89  screen_counts:110  db_counts:136  measure:154  index_counts:176  changed:200  _worse:218  failing:222  repair:235  main:268
```

### `validate/v7_watch.py` — 338줄

```
_scratch:25  _cols:100  _reads:104  _progress_note_check:132  _relist_check:219  run:245
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

### `validate/v9_multisite.py` — 311줄

```
_sites:69  live_sites:75  _labels:83  _badge_check:98  _hardcoded_badges:133  _origin_check:156  _warranty_sum_check:186  _tie_break_check:229  _axis_site_check:267  run:307
```

### `parse/revolt/mapping.py` — 294줄

```
_int:37  _won:44  _ym:49  _photo_field:57  parse_list_item:76  parse_detail:119  options_of:164  warranty_of:175  _months_since:208  record_of:219  panels_of:262
```

### `tests/test_crosssite.py` — 293줄

```
check:34  db:40  add:45  test_vin:63  test_vin_parse:107  test_cross_site:129  test_regression:175  test_readiness:207  v9_04_site_isolation:229
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

### `tools/check_screens.py` — 286줄

```
_pairs:23  say:90  _text:99  check_pairs:106  check_phrases:119  _sian_heads:151  _heads:169  check_sections:188  check_nav:215  check_render:235  main:269
```

### `tests/test_fixtures.py` — 284줄

```
check:33  fx:39  test_inspection:53  test_frame_vs_outer:84  test_record:123  test_detail:152  test_classify_real:172  test_catalog:207  test_diagnosis:219
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

### `score/scorer.py` — 253줄

```
ScoreResult:27  _certified_credit:64  axis_points:83  score:118  _bonuses:237  _penalties:246
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

### `tools/raw_lifecycle.py` — 235줄

```
_file_keys:46  _next_page:62  purge_bodies:69  vacuum:134  _today:148  main:152
```

### `tools/collect_reborncar.py` — 230줄

```
_now:47  _option_body:54  _options_old:82  _get:129  codes:144  main:159
```

### `tools/collect_heydealer.py` — 226줄

```
_now:45  _get:49  _targets:61  walk:83  main:128
```

### `tools/repair_facet_chunks.py` — 222줄

```
meta_of:37  fix_meta:66  groups:87  join:101  main:114
```

### `tools/collect_bobaedream.py` — 220줄

```
_now:45  _get:49  target_names:59  wanted:68  _elapsed:76  load_filters:83  _walk_plan:116  main:127
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

### `parse/bmw_bps/mapping.py` — 208줄

```
_text:47  _int:52  parse_detail:59  record_of:131  inspect_of:156  parse_list_item:165  list_photos:197
```

### `tests/seed.py` — 204줄

```
_cfg:46  build_seed_db:51  _confirm_dict:103  seed_db_path:119  _ensure_secrets:132  _seed_unclassified:148
```

### `tools/migrate.py` — 203줄

```
_table_sql:26  drop_not_null:33  rebuild_to_ddl:66  _norm:95  main:103
```

