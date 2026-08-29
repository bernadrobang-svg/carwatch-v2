# 소스 색인

**`python3.11 tools/build_index.py` 가 만든다. 손으로 고치지 않는다.**

파일 182개 · 총 65,017줄

| 파일 | 줄 | 무엇 |
|---|--:|---|
| `validate/v11_web.py` | 5,016 | V11 표현 계층 검증 (14장 STEP 153). |
| `report/screens/build.py` | 3,541 | 화면 데이터 생성. |
| `validate/v0_guide.py` | 3,225 | 가이드 문서 자체를 검사한다 (V0 계열). |
| `web/views.py` | 2,710 | 화면 어댑터 (14장 STEP 142 · 152). |
| `validate/v3_logic.py` | 2,270 | V3 로직 검증 — 판정이 작동하는가 · 변별력이 있는가. |
| `store/core.py` | 1,833 | CORE 저장소 (L4).  사이트 무관 공통 스키마. |
| `collect/runner.py` | 1,594 | 수집 실행 규칙. |
| `tests/test_spec_ui.py` | 1,494 | 규격 기준 통합 테스트 (통합테스트_시나리오_규격기준.md). |
| `tests/test_integration.py` | 1,236 | 통합 테스트 — 실제 HTTP 로 전 화면 (통합테스트_시나리오.md). |
| `tools/check_src.py` | 1,156 | CarWatch v2 — 지시서 ↔ 소스 대조 검증기. |
| `report/screens/admin.py` | 1,091 | 관리자 화면 — 표현 계층 (13장 STEP 138 · 138a). |
| `tools/verify_axes.py` | 1,079 | 손계산 대조 — 축마다 표본 3건 (개정 329 전수검증 · V3-66). |
| `store/adminops.py` | 1,057 | 관리자 서버 계층 — 실행 지시 · 쿼리 · API 조회 · 개발 요청 · 미리보기. |
| `report/render.py` | 939 | 리포트 생성 (L9). |
| `validate/v2_load.py` | 919 | V2 적재 검증 — 옮겨졌는가 · 전일 대비 변동이 타당한가. |
| `validate/v1_collect.py` | 901 | V1 수집 검증 — 다 받았는가 · 라벨이 맞는가. |
| `validate/v10_admin.py` | 895 | V10 관리자 검증. |
| `tests/test_score.py` | 857 | 7장 판정·채점 시험. |
| `tools/trace_fill.py` | 840 | 추적표의 소스 · 화면 · 검사 칸을 기계로 채운다 (`inbox/ORDER_00_trace_fill.md`). |
| `tests/test_run.py` | 783 | S0~S3 종단 시험 (모의 응답). |
| `validate/v4_mapping.py` | 780 | V4 매핑 검증 — 이름이 아니라 값으로 검증한다. |
| `collect/pipeline.py` | 775 | 실행 순서 · 중단 · 재처리 · 재개. |
| `store/watch.py` | 746 | 후보 추적 (11장). |
| `report/screens/views.py` | 711 | 화면 전용 DTO. |
| `store/admin.py` | 690 | 관리자 — 계정 · 권한 · config 변경 (13장 앞부분). |
| `parse/encar/mapping.py` | 625 | 엔카 원문 → CORE 필드 (L3). |
| `store/raw.py` | 599 | RAW 저장소 (L2).  원문 무손실.  삭제 금지. |
| `store/dictionary.py` | 578 | 사전 저장소 (L5).  RAW 에서 생성한다. |
| `tests/test_admin.py` | 567 | 13장 앞부분 시험 — 계정 · 권한 · config 변경. |
| `tests/test_admin_flow.py` | 566 | 관리 화면 동작 시험 (13장 · 14장). |
| `tools/check_spec.py` | 557 | CarWatch v2 지시서 자체 점검 — 7종 |
| `tools/collect_kbchachacha.py` | 548 | KB차차차 목록 수집 · 총 매물 수 세기 (명령서 `ORDER_20260822_r515.md` 3-2 · 단계 9). |
| `web/app.py` | 544 | 화면 조립 (14장 STEP 144 · 147 · 149). |
| `tools/build_index.py` | 536 | 검사 색인 · 소스 색인을 만든다 (규칙 11). |
| `tests/test_web.py` | 522 | 14장 표현 계층 시험 — 템플릿 · 라우팅. |
| `contracts.py` | 466 | 계층 간 계약 — Protocol · DTO. |
| `run.py` | 421 | CarWatch v2 진입점. |
| `web/template.py` | 406 | 최소 템플릿 엔진 (14장 STEP 143). |
| `report/views.py` | 405 | 리포트 DTO (L9). |
| `tests/test_collect.py` | 401 | 2장 수집 시험. |
| `tools/sync_registry.py` | 394 | RAW 경로 전수 → meta_field_usage. |
| `tests/test_pipeline.py` | 388 | 5장 수집 순서 시험. |
| `tools/collect_hyundai_cert.py` | 371 | 현대·제네시스 인증중고차 목록 수집 (명령서 `ORDER_20260822_r515.md` 3장 · 단계 11). |
| `tools/collect_kcar.py` | 352 | K카 상세 수집 (명령서 `ORDER_20260822_r515.md` 3-3 · 단계 10). |
| `tools/render_screens.py` | 331 | 전 화면을 실제로 렌더해 `outputs/render/` 에 남긴다. |
| `tools/light_check.py` | 325 | 가벼운 점검 — 4시간마다 (개정 335 · S29-0). |
| `parse/hyundai_cert/mapping.py` | 322 | 현대·제네시스 인증중고차 목록 카드 → CORE 필드 (L3). |
| `tools/build_dict.py` | 321 | RAW → 사전 생성. |
| `validate/v7_watch.py` | 320 | V7 관심·추적 검증. |
| `validate/v9_multisite.py` | 305 | V9 — 다중 사이트 (`docs/chapters/50-multisite.md`). |
| `analyze/axis/state.py` | 302 | ② 상태 150 — 차가 성한가 (docs/ref/F-scoring.md ②). |
| `store/crosssite.py` | 291 | 다중 사이트 확장 (12장). |
| `tests/test_endtoend.py` | 291 | 종단 시험 — 수집부터 리포트까지 (5장 STEP 47 · 49). |
| `adapters/encar.py` | 290 | 엔카 어댑터 — URL · 헤더 · 쿼리 조립. |
| `tests/test_dict.py` | 288 | 4장 키·코드·사전 시험. |
| `tests/test_screens.py` | 287 | 10장 화면 시험. |
| `tests/test_fixtures.py` | 284 | 실물 표본 시험 — v1 원문 12건. |
| `tests/test_crosssite.py` | 282 | 12장 다중 사이트 시험. |
| `parse/kcar/mapping.py` | 278 | K카 상세 → `core_listing` (`docs/KCAR_API.md` 3장 · `MULTISITE_MAPPING.md` 1장). |
| `tools/check_screens.py` | 277 | 화면 ↔ 시안 대조 (10장 · 14장). |
| `report/exports/export.py` | 269 | 내보내기. |
| `tests/test_report.py` | 263 | 9장 리포트 시험. |
| `tests/test_watch.py` | 259 | 11장 후보 추적 시험. |
| `web/server.py` | 259 | HTTP 서버 (14장 STEP 141 · 150). |
| `tools/collect_volvo.py` | 258 | 볼보 셀렉트 수집 — xhr-results 쪽넘김 (명령서 1a). |
| `tools/collect_bobaedream.py` | 256 | 보배드림 수집 (명령서 7단계 · `docs/BOBAEDREAM_API.md`). |
| `tests/test_store.py` | 255 | 3장 테이블 시험. |
| `tools/menu.py` | 254 | 실행 메뉴. |
| `tests/test_registry.py` | 245 | 8장 등록부 시험. |
| `validate/v5_value.py` | 244 | V5 수치 검증 — 기준값이 맞는가 · 보정이 타당한가. |
| `analyze/axis/site.py` | 240 | ⑤ 사이트 보증 50 · ⑦ 제조사 보증 50 (일반 20 + 동력계 30). |
| `tests/test_invariants.py` | 232 | 불변식 시험. |
| `tools/repair_facet_chunks.py` | 222 | 낱개로 저장된 facet 조각을 이어붙인다 (개정 307 사고 복구). |
| `web/context.py` | 213 | 화면 문맥과 오류 (14장 STEP 144 · 148). |
| `validate/base.py` | 212 | 검증 계약. |
| `parse/kbchachacha/mapping.py` | 210 | KB차차차 상세 → `core_listing` (`docs/KBCHACHACHA_API.md` 3장). |
| `tools/unknown_split.py` | 210 | 「확인 안 됨」을 ①②③④ 로 가른다 (개정 434 · 435 · V1-27 · V1-28). |
| `tools/collect_heydealer.py` | 206 | 헤이딜러 수집 — 토큰 → 차종별 목록 → 상세 (명령서 37). |
| `tests/seed.py` | 204 | 시험용 씨앗 DB — 운영 DB 를 복사하지 않는다. |
| `tools/collect_reborncar.py` | 196 | 리본카 수집 — 사이트맵 전량 → 우리 쪽에서 거른다 (명령서 39). |
| `score/scorer.py` | 194 | 채점 · 분모 (L7). |
| `parse/importer.py` | 182 | 반입 입력 해석 (13장 STEP 136a · 136b). |
| `collect/worker.py` | 180 | 큐 소비기 (13장 STEP 132a · 개정 261). |
| `tools/collect_kia_cpo.py` | 180 | 기아 인증중고차(CPO) 목록 수집 (명령서 `ORDER_20260822_r515.md` 3-1 · 단계 8). |
| `tools/classify_unclassified.py` | 175 | 미분류 경로를 원인별로 가른다 (개정 341 · V4-26 · V4-27). |
| `web/session.py` | 175 | 세션 · CSRF · 정적 파일 (14장 STEP 145~147). |
| `tools/migrate.py` | 174 | 스키마 이행 — 기존 DB 를 현재 DDL 에 맞춘다. |
| `parse/bobaedream/mapping.py` | 172 | 보배드림 상세 → `core_listing` (`docs/BOBAEDREAM_API.md` 2·3·1a장). |
| `tools/sync_target_map.py` | 172 | 차종 대응표 → `dict_enum` (명령서 `ORDER_20260822_r515.md` 2a장 · 개정 540). |
| `tools/daily_check.py` | 170 | 일일 점검 — 매일 23:00 (개정 334 · S29). |
| `tools/collect_lexus.py` | 168 | 렉서스 인증중고 수집 (명령서 1a). |
| `score/penalty.py` | 166 | 마이너스 점수 (개정 322). |
| `tools/weekly_check.py` | 163 | 주간 일제 점검 — 금 02:00 · 개발측 몫 (개정 334 · S29). |
| `adapters/kbchachacha.py` | 161 | KB차차차 어댑터 — URL · 헤더 (1장 STEP 11). |
| `analyze/axis/value.py` | 156 | ① 값 250 — 시세 대비 100 · 신차가 대비 80 · 주행 대비 70. |
| `report/finance.py` | 156 | 금융 — 점수가 아니라 비용이다. |
| `tools/compress_raw.py` | 155 | 원문(raw_response.body)을 눌러 둔다 (마스터 지시 2026-08-28). |
| `tools/daily_enqueue.py` | 153 | 하루 한 번 스스로 돈다 (STEP 136h · 개정 315). |
| `store/pii.py` | 152 | 개인정보 분리 (L4). |
| `web/routes.py` | 149 | 라우팅 표 (14장 STEP 142). |
| `tools/collect_bmw.py` | 148 | BMW 바바리안(BPS) 수집 (명령서 1a). |
| `score/adjust.py` | 145 | 배점 조정 — 비율 재배분과 정수 보정. |
| `tools/classify_registry.py` | 144 | 등록부 미분류 정리 — 근거가 있는 것만 (8장 STEP 87 · V4-11). |
| `analyze/axis/history.py` | 143 | ③ 이력 80 — 어떻게 쓰였나 (docs/ref/F-scoring.md ③). |
| `tools/run_tests.py` | 142 | 시험 전체 실행. |
| `parse/heydealer/mapping.py` | 139 | 헤이딜러 원문 → `core_listing` (명령서 37-3 ② · `docs/HEYDEALER_API.md`). |
| `parse/reborncar/mapping.py` | 139 | 리본카 상세 → `core_listing` (명령서 39 · `docs/REBORNCAR_API.md` 1b). |
| `tools/classify_fields.py` | 139 | 등록부 분류 초안 — 파서가 쓰는 경로를 근거로 자동 분류한다. |
| `tools/fold_out_of_scope.py` | 137 | 이미 들어온 것을 ★ 되돌린다 — ★ 우리 대상이 아닌 것은 ★ 접는다 (명령서 3-3). |
| `parse/classify.py` | 136 | 분류 2단 — target_key 판정. |
| `tools/trace_verify.py` | 136 | 추적표 「상태」를 사실로 (개정 349 · 350 · S34). |
| `adapters/heydealer.py` | 127 | 헤이딜러 어댑터 — 토큰 두 걸음 (명령서 37 · `docs/HEYDEALER_API.md` 0장). |
| `score/grade.py` | 127 | 등급 (L7). |
| `tools/check_all.py` | 123 | 실측 DB 회귀 — V1~V5 · V10 전건을 한 번에 돌린다. |
| `collect/fetcher.py` | 121 | 원문 획득 · 형식 검증. |
| `adapters/kia_cpo.py` | 118 | 기아 인증중고차(CPO) 어댑터 — URL · 헤더 (1장 STEP 11). |
| `analyze/axes.py` | 118 | 축 판정 계약. |
| `parse/kia_cpo/mapping.py` | 118 | 기아 인증중고차(CPO) 원문 → CORE 필드 (L3). |
| `adapters/kcar.py` | 115 | K카 어댑터 — URL · 헤더 (12장 · STEP 11). |
| `errors.py` | 115 | 도메인 예외 5종. |
| `tools/gen_table.py` | 114 | 배점표를 config 에서 생성한다 (개정 512). |
| `parse/volvo_selekt/mapping.py` | 112 | 볼보 셀렉트 상세 → `core_listing` 칸 (규격 `VOLVO_SELEKT_API.md` 2장). |
| `tools/classify_stored.py` | 110 | 저장된 매물을 ★ 갈래에 넣는다 — ★ 사이트 도구가 쓴 줄용 (명령서 37·39). |
| `tools/report_cli.py` | 109 | 리포트 재생성 (9장 STEP 90 · 91a · B-6). |
| `tools/fill_photos.py` | 108 | ★★★ 이미 받아 둔 원문에서 ★ 사진을 채운다 (명령서 73장). |
| `tools/probe_kb_wall.py` | 106 | KB 봇 차단을 ★ 재는 도구 (명령서 08-25 · 마스터 「가려 받지 마라」). |
| `store/tools.py` | 97 | 관리 도구 (13장 STEP 135). |
| `analyze/axis/taste.py` | 94 | ④ 취향 50점 — HUD 15 · 선루프 10 · 색상 10 · 지정 옵션 15. |
| `analyze/verdict.py` | 94 | 판정 엔진 — 순서 무관 put(). |
| `tools/recalc_catchup.py` | 94 | 재판정이 밀렸으면 채운다 (명령서 14-3 · 마스터 지시 08-24). |
| `parse/target_rules.py` | 93 | 차종군 + `targets.json` 규칙으로 ★ 갈래를 고른다. |
| `tools/export_cli.py` | 93 | 데이터 내보내기 (9장 STEP 91a · B-6). |
| `tools/setup_check.py` | 92 | 착수 점검 — 실행 전에 무엇이 준비됐는지 한 번에 본다. |
| `tools/daily_collect.py` | 91 | 아홉+한 사이트를 하루 한 번 받는다 (ORDER_20260829 1순위 2 · S46-127). |
| `analyze/axis/price.py` | 90 | 가격 200점. |
| `analyze/absolute.py` | 88 | E등급 절대조건 10종. |
| `adapters/bobaedream.py` | 87 | 보배드림 어댑터 — URL · 헤더 (1장 STEP 11). |
| `analyze/axis/spec.py` | 87 | 사양 90점 — HUD 20 · 선루프 20 · SVM 10 · SCC 10 · 후측방 5 · 틴팅 5. |
| `analyze/axis/trim.py` | 83 | ④ 사양 45 — 트림 25 · 옵션 20 (docs/ref/F-scoring.md ④). |
| `tools/deploy_check.py` | 81 | 배포 확인 — ★ 「소스가 맞다」와 「마스터 화면이 맞다」는 다른 말이다. |
| `analyze/peer.py` | 80 | 유사군 — 「이런 차가 보통 얼마인가」 (7장 STEP 82e). |
| `report/why_cheap.py` | 80 | 「왜 싼가」 — 싼 이유를 순서대로 찾아 낸다 (개정 299 · V3-52). |
| `tools/tmp_contend.py` | 80 | 0 잠금 — ★ 재판정이 도는 동안 ★ 수집기 꼴의 쓰기가 몇 번 죽나 (실측). |
| `store/chunk.py` | 77 | 조각 전송 — 바이트를 나누고 서버가 이어붙인다 (개정 307). |
| `tools/inspect_dict.py` | 75 | 사전 검토 — pending 값과 원문 표본을 본다. |
| `tools/inspect_facet.py` | 74 | facet 원문에 실제로 어떤 축이 왔는지 본다. |
| `analyze/trust.py` | 70 | 플랫폼 신뢰도 — 점검 출처 · 엔카진단 · 엔카보증 (개정 300). |
| `tools/fill_raw_run_id.py` | 65 | 원문에 ★ 빠진 `run_id` 를 채운다 (`V1-19` · A-10 · 개발측 자진 수정). |
| `tools/link_raw_ids.py` | 64 | ★★ 이미 쌓인 원문의 `listing_id` 를 ★ `source_id` 로 이어 채운다. |
| `analyze/curve.py` | 61 | 구간별 점수표 (docs/ref/F-scoring.md). |
| `tools/clear_zero_values.py` | 60 | ★★ 「값이 아닌 0」을 ★ 모름(NULL)으로 되돌린다. |
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
| `parse/bobaedream/__init__.py` | 0 | — |
| `parse/heydealer/__init__.py` | 0 | — |
| `parse/kbchachacha/__init__.py` | 0 | — |
| `parse/kcar/__init__.py` | 0 | — |
| `parse/reborncar/__init__.py` | 0 | — |
| `parse/volvo_selekt/__init__.py` | 0 | — |

## 큰 파일 — 무엇이 어디에 (200줄 이상 79개)

### `validate/v11_web.py` — 5,016줄

```
_web_sources:644  run:656  _late_checks:766  _templates_with_form:830  _spec_routes:851  _screen_routes:876  _routing_table_check:900  _count:937  ctx_account:944  _view_exists:950  _tpl:971  _all_templates:976  _screen_checks:981  _query_budget_check:1235  _import_origin_check:1314  _import_step4_check:1349  _browser_origin_check:1373  _browser_confirm_check:1391  _browser_chunk_check:1416  _status_screen_checks:1474  _status_liveness_check:1512  _menu_label_check:1553  _menu_paths:1581  _listing_rows:1606  _cli_caps:1624  _cli_only_check:1638  _stale_notice_check:1683  _trim_detail_check:1719  _option_sum_check:1742  _heart_line_check:1769  _recommend_terms_check:1790  _lease_checks:1809  _pick_filter_checks:1869  _shortfall_check:1908  _cash_limit_check:1927  _py_files:1958  _menu_no_path_check:1972  _listing_paging_checks:1990  _photo_checks:2026  _compare_shape_check:2067  _detail_shape_checks:2117  _filter_shape_checks:2195  _row_shape_checks:2265  _menu_shape_checks:2337  _sian_css_checks:2415  _cell_of:2490  _link_tip_checks:2513  _origin_link_check:2527  _origin_opens_bad:2572  _choose_check:2621  _order_filter_checks:2637  _checks_cfg:2680  _photo_size_by_screen_check:2689  _template_leak_check:2713  _em_dash_check:2739  _card_limits:2775  _cells_of:2792  _matches:2820  _grid_areas:2840  _hidden_cells:2870  _brace_block:2895  _place_cards:2909  _card_shape_checks:3031  _why_order_spec:3129  _why_order_check:3146  _width_policy:3181  _width_checks:3188  _chart_check:3287  _row_link_checks:3318  _screen_contradiction_check:3354  _chunk_check:3376  _csrf_reuse_check:3416  _origin_price_check:3460  _v1_parity_checks:3496  _media_blocks:3586  _responsive_checks:3607  _dead_links:3695  _null_link_check:3709  _sian_visual_check:3773  _purchase_cost_checks:3837  _report_popup_check:3924  _detail_photo_check:3998  _raw_shown_checks:4049  _compare_diff_check:4136  _chunk_message_check:4200  _whole_char:4227  _chunk_boundary_check:4240  _cell_squeeze_check:4328  _static_version_check:4383  _axis_state_check:4401  _three_values_check:4444  _photo_size_check:4483  _render_metrics_checks:4509  _browser_scope_checks:4608  _import_opened_steps_check:4629  _import_resume_check:4657  _watch_invite_check:4676  _post_smoke_check:4720  _template_roots:4793  _loop_fields:4803  _context_supplied_check:4825  _first_item:4896  _has_field:4910  _table_counts:4916  _save_button_check:4923  _probe:4980  _scratch:4998
```

### `report/screens/build.py` — 3,541줄

```
load_config:48  site_badge:107  axis_heads:126  _grade_order:136  _not_ranked:149  _labels:165  viewer_state:169  _unknown_cfg:179  is_unknown:188  chip:204  _stamp:240  _bulk_axes:244  confirm_ratio:265  _bulk_changes:276  _total_points:303  photo_urls:315  photo_url:347  market_price:378  _days_between:395  _ceil_to:410  _bulk_market:425  _bulk_state:464  not_join_months:497  _left:520  _warranty_state:529  _axis_state:567  _sites_cfg:631  _row:644  _pen_rows:873  _pen_axes:884  _pen_sum:904  _pen_words:912  _view_cfg:921  _grade_rank_sql:935  _sold_words:990  _order_sold:1008  order_clause:1023  _site_detail_urls:1038  _source_url:1047  _view_str:1055  _lease_kinds:1060  excluded_hidden:1067  lease_hidden:1083  _option_blind_sites:1105  _option_group_match:1122  fuel_groups:1136  _fuel_where:1147  _listings_where:1173  model_counts:1403  count_listings:1430  view_listings:1447  _market_gap_label:1568  _score_bars:1584  _group_caps:1615  _view_list:1636  _view_dict:1641  _soh_low:1646  _view_int:1655  _bucket:1660  _high_km:1667  _option_prices:1676  recommend_funnel:1688  _bulk_upside:1706  view_recommend:1721  recommend_reason:1756  excluded_groups:1799  view_why:1817  _compare_conclusion:1827  view_compare:1850  market_trims:1917  view_market:1939  _web_cfg:1975  _median:1989  _with_height:1994  _price_bins:2009  _group_prices:2030  _by_year:2048  _year_line:2065  _by_trim:2091  _other_targets:2109  count_dealers:2118  _dealer_targets:2124  _dealer_region:2144  view_dealers:2159  view_run:2195  _rank1_of:2201  view_dashboard:2209  _bars:2346  _grade_counts:2361  _relax_sim:2379  _axis_shortfall:2400  _progress:2419  _gone_and_watch:2434  _e_reasons:2477  _today_changes:2495  _step_rows:2520  _bulk_spark:2537  view_watch:2573  _man:2673  _mmdd:2687  _chg:2700  _gap:2715  _days_since:2730  _pending_values:2755  _done_items:2764  view_notready:2790  _unmatched_rows:2831  _report_files:2876  view_reports:2908  _warranty_until:2964  _verdict_lines:3013  _manwon_str:3055  _unknown_lines:3062  _price_history:3094  _alternatives:3111  _rep_flt:3147  view_detail:3153  _quartiles_by_target:3195  market_by_target:3219  _grade_order:3256  _grade_step:3271  _miss_axes_bulk:3277  view_track:3307  _accident_bulk:3406  duplicate_listings:3421  _today_counts:3473  _notready_counts:3497  axis_zero_rates:3517
```

### `validate/v0_guide.py` — 3,225줄

```
_read:25  s43_2_axis_ids:32  s44_4_scope_written:70  s44_5_site_consistent:102  s45_1_one_version:135  _order_files:158  s44_1_order_exists:171  s44_2_one_order:213  s43_2b_axis_renamed:228  s43_2c_no_hda:254  s45_5_no_axis_scores:308  s45_4_table_generated:346  s45_3_spec_totals:361  s45_2_mock_numbers:427  s44_3_specs_in_order:448  s43_3_version_matches:486  _h_tags:526  s46_21_one_screen_per_file:542  s46_22_section_order:567  _targets:636  s46_23_site_query_filled:642  s46_24_facet_unconfirmed:657  s46_30_index_covers_docs:674  s46_31_spec_sites_in_config:713  s46_32_generated_fresh:734  _req_rows:776  _tokens:788  _named_docs:803  s46_36_dropped_not_alive:815  s46_40_progress_docs_changed:843  s46_41_site_status_known:874  _templates:916  s46_45_spec_not_in_list:921  s46_46_spec_forbidden_ten:941  s46_66_links_encoded:967  s46_65_verdict_fresh:1006  _sian_files:1044  s46_67_sian_names_dont_clash:1053  s46_68_watch_is_mobile_first:1116  s46_74_rows_per_page:1170  s46_75_v4m_common:1216  s46_76_collectors_keep_raw:1256  s46_115_run_screen_still:1284  s46_125_sort_axes_really_sort:1313  s46_118_heart_has_anchor:1344  s46_121_header_rule_in_one_place:1384  s46_116_reasons_in_plain_words:1406  s46_120_registry_key_matches:1433  s46_123_toss_palette_only:1469  s46_122_shared_fragments:1511  s46_128_batch_gives_a_window:1555  s46_127_collector_has_screen_or_timer:1599  s46_124_db_opened_with_pragmas:1647  s46_126_fetch_outside_transaction:1683  s46_117_collectors_sweep_gone:1717  s46_77_kb_is_our_targets_only:1751  s46_78_encar_only_paths_are_scoped:1806  s46_87_request_site_matches_listing:1848  s46_88_encar_blocked_banner:1917  _paired_rows:1982  _grade_order_list:2022  s46_54_grade_two_step:2034  s46_55_price_gap_30:2059  s46_56_accident_split:2085  s46_90_pending_not_graded:2125  _registrable:2174  s46_94_source_url_site_matches:2188  s46_91_raw_vs_stored:2232  s46_97_raw_linked_by_source_id:2304  s46_99_login_then_watch:2372  _logged_opener:2468  _sian_seq:2507  s46_100_sian_word_order:2539  s46_102_electric_only_is_electric:2676  s46_103_sian_values_carried:2728  s46_98_sian_words_on_screen:2769  s46_95_screens_alive:2875  s46_96_site_sells_but_no_code:2931  s46_92_browser_zero_count:2971  _as_check:3152  results:3166  save:3191  run:3202
```

### `web/views.py` — 2,710줄

```
_rows_per_page:30  _cfg:34  _versions:39  page_extras:58  _points:67  page:89  listings:116  why:173  detail:225  _grade_help:258  notready:265  dashboard:275  admin_home:297  _unclassified_split:309  _rows_of:337  _check_reports:347  admin_audit:370  admin_docs:383  _int_param:407  _manwon:446  _site_buttons:451  _filter_chips:501  _order_menu:555  _carry:561  _order_label:571  ORDERS_LABELS_GET:575  _condition_sentence:579  _query_string:597  _page_links:610  _simple_paging:631  _paging:641  _filter_buttons:671  _model_menu:704  _pick_state:721  _option_name_buttons:783  _color_menus:844  _judge_buttons:859  _split_top:887  _fuel_options:893  _distinct_options:904  _km_options:916  _grade_options:924  _keep_query:931  _carry_pick:956  _lease_hidden:966  _excluded_hidden:972  _excluded_why:979  _filter:989  recommend:1069  track:1097  compare:1114  market:1136  _first_target:1156  dealers:1162  watch:1182  _note_kinds:1199  _watch_notes:1206  run_view:1233  login:1245  _login_again:1287  _open_session:1303  logout:1344  _watch_queries:1361  watch_query_post:1370  _int_or_none:1400  watch_add_post:1404  _watch_note_post:1464  _watch_invite:1490  watch_update_post:1513  _now:1537  _reason_gate:1544  _gate:1565  _first_flag:1604  _all_hours:1609  admin_run:1637  _target_rows:1705  admin_dict:1718  admin_status:1755  admin_collect:1770  _take_chunk:1829  _verify_part:1872  _run_stamp:1912  _int_or_none:1923  admin_import:1928  admin_scoring:2000  _decide_cards:2053  admin_registry:2081  admin_query:2134  admin_requests:2156  _admin_extra:2218  _config_files:2233  _config_rows:2240  admin_config:2272  _typed:2323  admin_api:2339  _site_query:2389  admin_targets:2402  admin_tools:2500  join:2519  password:2550  admin_users:2565  _account_activity:2625  reports:2631  report_download:2647
```

### `validate/v3_logic.py` — 2,270줄

```
_file_output_checks:384  _conflict_checks:437  _diagnosis_count_check:461  _sort_determinism:478  _warning_contract_checks:500  _list_observed_source_check:595  _facet_reconcile_check:625  _record_mismatch_check:669  _curve_table_check:699  _special_null_check:766  _grade_base_checks:794  _checks_cfg:887  _labels_cfg:901  _unknown_mark_checks:909  _grade_cut_checks:960  _points_cap_checks:1070  _worse_of_checks:1122  _checks_json:1184  _value_curve_checks:1195  _group_sum_checks:1285  _mapped_other_check:1396  _denominator_check:1423  _core_axis_check:1451  _rental_cross_check:1472  _why_cheap_check:1510  _source_before_value_check:1551  _absolute_cut_check:1586  _spec_files:1616  _confirm_ratio_check:1626  _warranty_checks:1676  _spec_axis_check:1710  _site_axis_checks:1751  _rendered_why:1800  _rendered_listings:1810  _fill_gap_check:1820  _points_sum_check:1853  _market_gap_check:1870  _bonus_checks:1926  _trim_price_check:2030  run:2078  _shuffle_check:2213  _halt_dict_check:2238  _ensure_tmp:2267
```

### `store/core.py` — 1,833줄

```
resolve_listing_id:38  resolve_dealer_id:56  serialize_container:72  record_change:83  split_pii:105  flush_dealer_pii:152  _record_dropped:164  classify_invariant_change:199  _lookback:249  _source_history:263  _schema_change_min:292  _current:306  _today:312  _drop_non_values:326  upsert_core:334  mark_gone:435  sweep_gone:452  sweep_gone_groups:484  load_snapshot:523  build_identities:632  resolve_vehicle_id:658  merge_conflict:690  upsert_vehicle:701  upsert_dealer:722  dealer_trust:749  _trust_cfg:842  upsert_child:859  _flag:880  _not_join_months:894  state_counts:919  current_versions:959  diagnosis_of:989  target_counts:1002  top_target:1009  vehicle_of:1014  collect_scale:1021  our_fault:1041  catalog_coverage:1050  _walk:1094  _sample_bodies:1110  hits_of:1123  key_seen:1142  stored_hits:1157  sample_bodies:1173  observed:1195  known_leaves:1233  has_unclassified:1248  classify_unclassified:1255  _card_limit:1298  _value_chars:1303  _admin_cfg:1308  unclassified_cards:1325  _peek:1381  _short:1428  _blocking_paths:1439  _raw_rows_max:1459  used_endpoints:1469  raw_sections:1478  _flatten:1517  option_diff:1541  _option_names:1579  blocking_keys:1595  full_hits:1613  axis_paths_empty:1638  blocking_rows:1675  record_mismatch_sql:1737  record_mismatch_count:1743  relist_counts:1769  listing_models:1786  filter_options:1806  site_counts:1823
```

### `collect/runner.py` — 1,594줄

```
CollectGroup:67  load_targets:91  collect_groups:104  facet_axes:144  aspect_names:165  check_facet_axes:169  interpret_failure:183  collect_check:212  FailStreak:282  _sleep:316  _log_request:322  _save_issues:333  make_executors:344  classify_in_group:961  _query_key:990  _group_of:998  _fuel_of:1013  _badge_of:1019  _pages_for:1025  _dicts:1039  _option_medians:1075  _market_medians:1121  _trim_ladders:1150  _option_base:1167  _site_grade_rules:1197  _listing_config:1213  _listing_values:1238  _option_money:1257  _owned_months:1276  _option_of:1288  _market_of:1296  _group_sums:1306  make_score_executors:1333  make_validate_executor:1523  make_registry_executor:1565
```

### `tests/test_spec_ui.py` — 1,494줄

```
rec:33  spec_a:43  spec_b:121  spec_c:195  spec_d:239  spec_f:281  spec_g:316  spec_h:364  spec_j:397  spec_m:440  spec_e:508  spec_i:551  spec_k:664  spec_csrf:719  spec_l:746  spec_monkey:788  flow_s1:860  flow_s2:929  flow_s5:1013  flow_s3:1126  flow_s4:1201  flow_s6:1272  guide_v132:1328  main:1428  _write:1472
```

### `tests/test_integration.py` — 1,236줄

```
rec:31  Client:41  text:96  links:101  start_server:105  seed_admin:149  m1:165  m2:255  m3:329  m4:634  s3:705  unit:761  gaps:796  flows:904  guide7:1007  _account_id:1140  make_users:1147  main:1165  _write_table:1214
```

### `tools/check_src.py` — 1,156줄

```
_spec_files:44  _read_spec:62  say:73  py_files:87  chapter_of:127  _declared_chapters:137  split_done:157  _illustration:176  _retired_config_keys:240  _git:701
```

### `report/screens/admin.py` — 1,091줄

```
AdminMenuItem:33  AdminHome:81  SaveGate:107  AuditTab:121  AuditView:129  DocView:136  menu_for:147  view_admin_home:159  _todos:186  _recent_runs:226  _recent_changes:257  save_gate:268  view_audit:276  view_docs:322  _doc_files:353  Todo:374  RunRow:388  ChangeRow:398  _cfg_rows:418  config_history:428  query_history:440  db_tables:454  api_snapshots:495  account_activity:506  make_target_key:524  target_choices:543  target_rows:562  parse_import_text:593  status_view:608  _catalog_state:682  _light_result:714  _live_window:754  _live_progress:763  run_progress:810  collect_state:860  received_vs_used:920  dict_state:941  import_state:968  job_log:1006  validation_runs:1020  blocking_set:1038  _menu_groups:1062  _menu_by_group:1081
```

### `tools/verify_axes.py` — 1,079줄

```
_spec_text:26  _grade_order:59  _not_ranked:72  spec_tables:86  _num:109  pick:127  _flag:141  hand_market:149  _median_for:160  hand_mileage:180  _years:193  conn_now:202  lookup:207  hand_accident:231  hand_repair:241  hand_owner:249  _warranty_left:257  hand_warranty_general:278  hand_warranty_power:283  hand_site_warranty:289  hand_maker_warranty:319  _km_per_month:346  residual_spec:362  _json:388  hand_option_won:401  hand_depreciation:438  hand_frame:468  hand_outer:489  _leak_states:509  hand_leak:521  hand_lien:536  hand_not_join:546  hand_trim:576  hand_special:596  spec_section:606  spec_head_points:614  lookup_label:621  hand_integrity:629  hand_special_points:655  _taste_points:664  _has_option:675  hand_color:710  hand_usage:734  hand_site_grade:758  hand_inspection_src:778  hand_hud:791  hand_sunroof:800  hand_picked:809  _has_table:822  _option_prices:828  hand_options:846  survey:884  main:947
```

### `store/adminops.py` — 1,057줄

```
QueryLog:55  QueryResult:68  ApiSnapshot:93  DevRequest:104  RecalcJob:119  ScoringPreview:130  ImportPreview:142  ImportResult:159  preview_import:168  import_listings:194  _import_facet:260  BrowserCatch:295  save_browser_catch:303  mark_step_imported:353  pending_enums:384  pending_axis_summary:421  apply_dict_decision:449  _strip_sql:494  sql_reject_reason:501  _opened_tables:535  reject_kind_of:550  columns_hint:560  reap_stale_jobs:583  run_query:618  fetch_api:665  create_dev_request:699  update_dev_status:721  export_dev_requests:735  enqueue_recalc:765  enqueue_after_list_save:791  job_progress:816  db_progress:830  preview_scoring:840  _pt:883  registry_rows:887  registry_counts:898  write_dev_requests:904  dev_request_rows:924  save_api_snapshot:945  get_api_snapshot:968  path_table:987  halt_job:1023
```

### `report/render.py` — 939줄

```
_labels:30  _site_blind_axes:35  _stamp:76  _curve_points:91  source_detail_url:134  _why_cheap_of:155  _scoring:196  _penalty_rows:204  _market_pos:218  _site_badge:262  _axis_why:269  _raw_sections:299  _photo_urls:309  _purchase_costs:332  _unknown_axis_cfg:360  render_listing:383  axis_mark:550  source_label:571  _option_rows:619  _fetch_views:679  _strengths:694  _weaknesses:701  _pending_best:708  _cost_rows:741  _known_issues:762  _diagnosis_view:780  render_target:791  render_run:872  render_halt:914  _j:932
```

### `validate/v2_load.py` — 919줄

```
DayGapReport:151  GapCause:164  run:170  _surrogate_key_checks:347  _not_null_check:432  _chained_subscript_check:449  _Boom:497  _salvage_check:505  _table_exists:546  _exception_shape_checks:552  _schema_sync_check:618  _pii_access_check:655  gap_alerts:694  diff_prev_day:710  explain_gap:732  _pii_column_check:764  _secret_key_check:782  _parser_common_fields_check:820  _null_target_not_judged_check:871  _null_target_visible_check:896
```

### `validate/v1_collect.py` — 901줄

```
_unknown_split_checks:171  _axis_empty_check:257  run:287  _endpoint_order_check:421  _empty_db_check:433  _sql_groups:460  _cumulative_codes:496  _run_scope_check:506  _ctx_started:544  _has_run_id:552  _expected_scope_check:557  _diagnosis_scope_check:578  _diagnosis_none_count:618  _query_key_check:643  _entrypoint_parity_check:680  _enclosing_def:709  _run_id_filled_check:718  _catalog_key_check:738  _whole_probe:760  _whole_body_check:771  _catalog_checks:807  _unparsed_envelope_check:854  _ensure_tmp:898
```

### `validate/v10_admin.py` — 895줄

```
_sources:212  _admin_guard_checks:233  _sql_strings:278  _schedule_checks:290  _query_error_checks:333  run:432  _session_checks:538  _pii_query_check:618  _scratch:665  _dict_reason_check:680  _dict_source_shown_check:696  _automation_checks:714  _queue_consumer_check:847  _queue_stale_shown_check:876  _ensure_tmp:892
```

### `tests/test_score.py` — 857줄

```
check:36  fx:42  snap:46  ctx:66  full_verdict:87  test_denominator:100  test_components_form:144  test_grade:195  test_order_independent:284  panels_of:307  test_history_real:312  test_rental_real:347  test_insurance:389  test_safety_real:414  test_spec_gate:463  test_price_real:532  test_color:618  test_price_pending:639  test_absolute_real:658  test_null_safe:698  test_empty_array_meaning:715  test_peer_group:740  test_damage_by_status:782  test_repair_cost_ratio:808  test_hda_gate:817
```

### `tools/trace_fill.py` — 840줄

```
spec_lines:94  anchor_step:112  build_symbols:131  enclosing:166  build_texts:176  _stem:214  tokens:223  _best_in:253  _rows:290  layers_of:303  layer_pool:310  _rare_hit:322  axis_words:346  json_key_at:367  _place:394  _hints:405  find_in_layer:421  _best_step_in:469  _layers:500  derive_state:520  src_mark:546  relayer:559  restate:574  fill_file:597  move_to_rules:665  survey:708  lists:736  write_index:757  main:796
```

### `tests/test_run.py` — 783줄

```
check:36  StubEncar:92  Clock:241  setup:246  test_envelope:284  test_last_page_exact:314  test_facet:321  test_facet_missing_axis:335  test_dict_step:344  test_all_groups:366  test_parse_pipeline:377  test_score_pipeline:481  test_validate:553  test_registry_gate:596  test_target_scope:653  test_catalog_key:685  test_wrapper_args:703  test_unclassified_listing:750
```

### `validate/v4_mapping.py` — 780줄

```
_paths:143  _layer_of:190  _unclassified_split:195  _layer_checks:233  _name_collision_check:329  _key:363  _decide_material_check:369  _blocking_list_check:433  run:490  _mapping_coverage_checks:639  _our_columns:669  _listing_value_scope_check:697  _dict_filled_check:717  _kind_check:728  propose_fix:742  _option_code_check:757  _is_sentence:774
```

### `collect/pipeline.py` — 775줄

```
envelope_scope:41  Reprocess:91  refetch_all:121  reprocess_plan:131  should_refetch:148  expected_for:160  step_report:194  halt_if:210  precheck:243  resume_point:297  config_hash:317  build_run_context_fields:323  stale_rows:332  save_step_report:347  rss_mb:371  run_step:390  _execute:428  completed_steps:447  run_pipeline:459  print_progress:508  silent_progress:527  from_step_for:541  web_reasons:571  check_recalc_origin:576  plan_recalc:588  _current:605  run_recalc:611  Defect:632  DefectReport:643  diagnose:664  _DiagCtx:688  _collect_defects:698  format_defects:752
```

### `store/watch.py` — 746줄

```
AlertConfig:58  WatchItem:71  TrackPoint:86  TrackEvent:101  WatchEvent:115  _cross_site_order:130  classify_duplicates:149  sync_duplicates:202  deduped_count:226  watch_add:236  assert_owner:275  watch_update:290  watch_close:310  note_add:331  notes_of:356  note_delete:374  track_snapshot:389  track_points:418  classify_cause:427  detect_events:439  message:497  notify:525  _grade_order:596  _not_ranked:609  add_watch_query:623  run_watch_queries:658  watch_query_rows:714  close_watch_query:728
```

### `report/screens/views.py` — 711줄

```
AxisChip:30  ScoreBar:55  ListingRow:71  ListingFilter:232  WatchRow:319  TargetStat:362  RelaxRow:371  MarketRow:378  ChangeRow:390  AttentionItem:400  ViewerState:408  DashboardView:422  CompareView:459  TrackPair:477  TrackView:507  MarketView:533  DealerRow:548  NotReadyView:569  TodayChange:600  StepRow:612  _min_sample:624  PendingValue:642  Bucket:655  ExcludedGroup:675  ReportFile:684  ReportsView:696
```

### `store/admin.py` — 690줄

```
_admin_cfg:46  ConfigChange:68  running_job:86  hash_secret:96  _split:104  create_account:109  account_count:145  needs_bootstrap:149  _recent_failures:161  _log_attempt:180  is_locked:190  unlock_account:205  authenticate:233  open_session:269  session_account:289  change_secret:306  revoke_sessions:330  _under_seed:353  _walk:361  get_path:385  set_path:390  _atomic_write:397  apply_config:407  _validate_blob:473  revert_config:486  history:510  classify_field:534  account_rows:590  admin_count:604  set_role:611  set_disabled:628  add_config_key:648
```

### `parse/encar/mapping.py` — 625줄

```
_get:30  _json:42  _won:53  _ym:73  _date10:83  _int:99  _bool:105  unpack_envelope:116  parse_list_item:124  parse_detail:171  parse_inspection:247  parse_record:295  _sample_chars:349  safe_field:363  parse_with_issues:385  _salvage:403  _parses:446  dig:453  as_list:476  _diag_comment:504  parse_diagnosis:511  parse_diagnosis_items:543  _text:551  parse_record_summary:561  parse_platform_check:587  parse_inspection_summary:594  parse_ev_battery:599  parse_sellingpoint:619
```

### `store/raw.py` — 599줄

```
_compress_cfg:59  pack_body:70  raw_body:91  batch:116  tick:146  commit:181  _batch_commit_rows:208  _batch_commit_pause_ms:218  _busy_timeout_ms:243  connect_db:254  open_db:282  link_raws:293  _safe_headers:319  save_raw:326  proc_run_id:384  save_site_raw:394  save_import_raw:449  save_browser_raw:482  save_browser_facet:523  save_import_facet:549  save_facet:579
```

### `store/dictionary.py` — 578줄

```
CodeEntry:31  AxisPolicy:57  policy:101  scope_key:109  seed_fixed_enums:134  target_map:175  target_key_of:198  fuel_normalize:214  collect_group_of:237  match_target_name:242  known_model_names:259  known_model_of:276  mapped_of:281  upsert_enum:302  _handle_conflict:354  upsert_option3:375  retire_unseen:411  resolve_code:426  installed_option_names:464  normalize_enum:482  assert_no_unknown:498  bump_dict_version:541  list_pending:551  confirm_enum:559
```

### `tests/test_admin.py` — 567줄

```
_spec_menu_paths:31  check:47  setup:53  test_bootstrap:65  test_auth:95  test_apply_config:137  test_value_validation:175  test_revert:195  test_no_direct_edit:221  test_classify_field:250  test_run_query:324  test_dev_request:377  test_recalc_and_lock:407  test_admin_screens:441  test_v10:531
```

### `tests/test_admin_flow.py` — 566줄

```
check:32  _env:38  _cfg:55  _post:60  _get:65  flow_config:71  flow_scoring:107  _rescore:163  _sum:224  _dist:231  flow_targets:238  flow_registry:273  flow_run:313  flow_query:346  flow_api:372  flow_tools:409  flow_users:431  flow_requests:476  flow_permission:518  main:531
```

### `tools/check_spec.py` — 557줄

```
_read_spec:10  _refs_source:73  _spec_files:284  _guide_files:368  _sections:373  _md:468
```

### `tools/collect_kbchachacha.py` — 548줄

```
_now:85  _get:89  fetch_ok:98  page_ids:115  load_filters:125  walk_group:185  count_all:227  probe_detail:253  store_details:272  fetch_details:301  load_details:375  main:440
```

### `web/app.py` — 544줄

```
menu_items:22  _tip:104  _label:109  empty_state:120  banner_of:139  _encar_blocked:200  _list_stale:231  static_version:257  build_page:285  check_post:306  redirect:328  take_flashes:348  _display_now:361  make_app:387  _Denied:520  build_context:528  _title_of:543
```

### `tools/build_index.py` — 536줄

```
_py_files:48  _checks_in_code:73  _guide_checks:119  _checks_in_docs:152  last_runs:185  _run_time:214  sort_checks:224  build_checks:241  _outline:313  build_source:324  build_schema:356  build_doc_index:415  check_fresh:480  main:513
```

### `tests/test_web.py` — 522줄

```
check:21  test_routes:28  test_template:85  test_no_logic_in_template:126  test_static_escape:141  test_session_cookie:153  test_error_page:171  test_layout:198  test_filters:227  test_empty_state:250  test_menu_by_role:277  test_guard_and_csrf:298  _call:345  test_screens_render:362  test_sketch_match:453  test_account_policy:468
```

### `contracts.py` — 466줄

```
Response:24  Clock:34  Fetcher:39  Rng:44  Request:52  EndpointSpec:60  FetchResult:71  TargetSpec:84  ListingSnapshot:141  AxisResult:230  Account:249  require_role:266  RunContext:283  StepReport:303  ResumePoint:327  clean_vin:348  total_of:359  RegressionReport:372  json_paths:383  shape_ok:431  shape_violations:464
```

### `run.py` — 421줄

```
load:51  make_context:56  _filter_targets:70  _steps_from:89  cmd_collect:103  _grade_summary:171  cmd_admin_create:186  _collect_urls:203  _page_url:240  cmd_web:259  make_worker_ctx:299  make_worker_executors:305  cmd_delegate:343  _api_fetch:354  cmd_setup:364
```

### `web/template.py` — 406줄

```
f_won:55  f_km:71  f_pct:75  f_date:79  f_num:90  f_gradecls:97  f_gradelabel:110  _grade_classes:125  f_count:134  f_signcls:142  f_signwon:152  f_url:160  _index_key:198  _step:213  _lookup:225  _truthy:234  render_str:238  strip_comments:345  expand_includes:350  render:387
```

### `report/views.py` — 405줄

```
VersionStamp:18  ReportMeta:30  AxisView:40  FinanceView:64  PurchaseCostItem:85  PurchaseCostView:94  DiagnosisView:118  FetchView:130  CostRow:144  ScoreView:153  CollectSummary:253  ClassifySummary:260  PriceSummary:267  AxisStat:276  CoefficientChange:286  DictChangeSummary:296  TargetReport:304  RunStep:316  RunReport:331  HaltReport:342  FixAction:359  NotifyResult:369  ExportResult:382  display_value:391  display_points:401
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

### `tools/collect_hyundai_cert.py` — 371줄

```
target_of:73  _now:89  _post:93  _get:103  fetch_detail:114  load_filters:127  total_count:159  walk:172  main:204
```

### `tools/collect_kcar.py` — 352줄

```
_now:45  fetch:49  classify:71  accident_of:86  fetch_stock:95  collect_list:120  main:252
```

### `tools/render_screens.py` — 331줄

```
_shot_widths:32  _tmp_root:57  main:81  shot_paths:172  _localize_images:197  shoot:234
```

### `tools/light_check.py` — 325줄

```
_repair_max:45  _cfg:63  _run:68  collecting:74  screen_counts:95  db_counts:121  measure:139  index_counts:161  changed:185  _worse:203  failing:207  repair:220  main:253
```

### `parse/hyundai_cert/mapping.py` — 322줄

```
_int:31  cards:40  _fuel_of:65  _model_group:76  parse_card:94  _json:166  detail_text:173  _one:180  parse_detail:185  parse_detail_all:191  _num:249  _warranty:256  _months_left:299  _options:316
```

### `tools/build_dict.py` — 321줄

```
DictBuildReport:63  extract_distinct:78  _facet_values:108  facet_value_set:124  _walk_path:143  load_fixed_enums:170  build_dict:178  _mark_facet_substituted:229  build_catalog_dict:253  build_late_dict:293
```

### `validate/v7_watch.py` — 320줄

```
_cols:85  _reads:89  _progress_note_check:117  _relist_check:201  run:227
```

### `validate/v9_multisite.py` — 305줄

```
_sites:69  live_sites:75  _labels:83  _badge_check:98  _hardcoded_badges:133  _origin_check:156  _warranty_sum_check:186  _tie_break_check:223  _axis_site_check:261  run:301
```

### `analyze/axis/state.py` — 302줄

```
_panels:43  _rank_worst:47  insurance_trace:59  panel_trace:68  worse_step:80  _accident:87  _frame:109  _outer:129  _repair:151  _special:162  leak_state:174  _leak:196  _site_never:206  _sites_table:218  _consumable:236  _integrity:258  analyze_state:294
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

### `tests/test_dict.py` — 288줄

```
check:39  db:45  test_scope_key:51  test_count_zero:73  test_axis_policy:97  test_conflict:145  test_catalog:180  test_status_version:204  test_classify:221  test_review:250
```

### `tests/test_screens.py` — 287줄

```
check:42  _pipeline:48  test_chip:60  test_listings:83  test_compare:144  test_dashboard_notready:161  test_static_rules:201  test_account:233
```

### `tests/test_fixtures.py` — 284줄

```
check:33  fx:39  test_inspection:53  test_frame_vs_outer:84  test_record:123  test_detail:152  test_classify_real:172  test_catalog:207  test_diagnosis:219
```

### `tests/test_crosssite.py` — 282줄

```
check:34  db:40  add:45  test_vin:63  test_vin_parse:107  test_cross_site:129  test_regression:175  test_readiness:207  v9_04_site_isolation:229
```

### `parse/kcar/mapping.py` — 278줄

```
_int:24  yn:32  _months_until:45  _model_group:59  parse_detail:69  _photos:157  parse_list_item:170  accident_of:220  record_of:228
```

### `tools/check_screens.py` — 277줄

```
_pairs:23  say:81  _text:90  check_pairs:97  check_phrases:110  _sian_heads:142  _heads:160  check_sections:179  check_nav:206  check_render:226  main:260
```

### `report/exports/export.py` — 269줄

```
filename:26  _stamp_lines:32  listing_md:38  listing_csv:76  halt_md:93  target_md:114  run_md:136  _asdict:186  export:194  output_path:233  write_export:241
```

### `tests/test_report.py` — 263줄

```
check:33  test_finance:40  test_display:97  _pipeline:113  test_layers:124  test_halt_layer:160  test_export:202
```

### `tests/test_watch.py` — 259줄

```
check:30  db:36  add:41  watch:64  test_same_dealer:78  test_cross_dealer:97  test_relist:112  tp:124  test_cause:133  _two_runs:145  test_snapshot:162  test_events:177  test_cause_gate:198  test_message:212
```

### `web/server.py` — 259줄

```
load_web_config:47  guard:60  _drain_chunk:92  TOO_LARGE:96  make_handler:105  serve:234
```

### `tools/collect_volvo.py` — 258줄

```
_known_name:44  load_slugs:60  _now:89  _get:93  main:108
```

### `tools/collect_bobaedream.py` — 256줄

```
_now:39  _get:43  target_names:53  wanted:62  _elapsed:70  load_filters:77  _walk_plan:104  main:115
```

### `tests/test_store.py` — 255줄

```
check:40  seed:46  base:52  db:70  test_schema:76  test_key:124  test_null_three:135  test_change_history:142  test_invariant_violation:163  test_snapshot:181  test_dictionary:206
```

### `tools/menu.py` — 254줄

```
_fix_console:28  run:44  cmd_status:52  cmd_setup:56  cmd_dry:74  cmd_collect:81  cmd_facet:118  cmd_dict:123  cmd_screens:128  cmd_migrate:133  cmd_checkall:138  cmd_requests:143  cmd_check_spec:150  cmd_check_src:154  cmd_test:159  main:192
```

### `tests/test_registry.py` — 245줄

```
check:33  fx:39  db:43  put_raw:48  test_paths:57  test_contamination:69  test_seed:95  test_ghost:140  test_v4_06:168  test_seed_reapply:180  test_unclassified_severity:202
```

### `validate/v5_value.py` — 244줄

```
run:60  _grade_ratio_checks:151  _denominator_suite:195
```

### `analyze/axis/site.py` — 240줄

```
remaining_months:26  warranty_points:39  _truthy:73  warranty_grade:89  _seller_only:115  _one_step_down:124  _site:136  _maker:169  _maker_default:201  analyze_site:238
```

### `tests/test_invariants.py` — 232줄

```
check:35  inv1_order_independent:42  inv1_shuffle_100:72  inv2_banned:95  inv5_points:113  put_contract:126  excluded_contract:143  inv3_source_not_null:169  inv4_label_shape:188  inv6_no_unclassified:204
```

### `tools/repair_facet_chunks.py` — 222줄

```
meta_of:37  fix_meta:66  groups:87  join:101  main:114
```

### `web/context.py` — 213줄

```
MenuItem:31  Banner:42  PageContext:55  ErrorPage:92  _is_permission:135  _is_conflict:140  _clean:145  _is_sql_typo:156  error_page:166
```

### `validate/base.py` — 212줄

```
_cfg:24  Check:55  CheckResult:93  _short:118  result:131  not_applicable:140  save_results:145  gate:162  run_phase:171  canon_files:193  canon_text:206
```

### `parse/kbchachacha/mapping.py` — 210줄

```
_text:43  _int:48  ld_json:55  _yes_no:67  _model_of:97  parse_detail:117  _photos:199
```

### `tools/unknown_split.py` — 210줄

```
_cfg:35  _walk:41  classify:51  main:127
```

### `tools/collect_heydealer.py` — 206줄

```
_now:34  _get:38  _targets:50  walk:68  main:113
```

### `tests/seed.py` — 204줄

```
_cfg:46  build_seed_db:51  _confirm_dict:103  seed_db_path:119  _ensure_secrets:132  _seed_unclassified:148
```

