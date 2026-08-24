# 소스 색인

```
version  SPEC-2026.08.25-r726
follows  ★ 생성물 — `tools/build_index.py` 가 만든다
sources  개정 726 · 실측 08-25
checks   S46-38 · S46-39
```


**`python3.11 tools/build_index.py` 가 만든다. 손으로 고치지 않는다.**

파일 172개 · 총 58,690줄

| 파일 | 줄 | 무엇 |
|---|--:|---|
| `validate/v11_web.py` | 4,882 | V11 표현 계층 검증 (14장 STEP 153). |
| `report/screens/build.py` | 3,121 | 화면 데이터 생성. |
| `web/views.py` | 2,653 | 화면 어댑터 (14장 STEP 142 · 152). |
| `validate/v3_logic.py` | 2,265 | V3 로직 검증 — 판정이 작동하는가 · 변별력이 있는가. |
| `store/core.py` | 1,582 | CORE 저장소 (L4).  사이트 무관 공통 스키마. |
| `collect/runner.py` | 1,491 | 수집 실행 규칙. |
| `tests/test_spec_ui.py` | 1,461 | 규격 기준 통합 테스트 (통합테스트_시나리오_규격기준.md). |
| `tests/test_integration.py` | 1,236 | 통합 테스트 — 실제 HTTP 로 전 화면 (통합테스트_시나리오.md). |
| `tools/check_src.py` | 1,156 | CarWatch v2 — 지시서 ↔ 소스 대조 검증기. |
| `report/screens/admin.py` | 1,086 | 관리자 화면 — 표현 계층 (13장 STEP 138 · 138a). |
| `tools/verify_axes.py` | 1,079 | 손계산 대조 — 축마다 표본 3건 (개정 329 전수검증 · V3-66). |
| `store/adminops.py` | 1,054 | 관리자 서버 계층 — 실행 지시 · 쿼리 · API 조회 · 개발 요청 · 미리보기. |
| `validate/v0_guide.py` | 963 | 가이드 문서 자체를 검사한다 (V0 계열). |
| `validate/v2_load.py` | 919 | V2 적재 검증 — 옮겨졌는가 · 전일 대비 변동이 타당한가. |
| `validate/v10_admin.py` | 895 | V10 관리자 검증. |
| `validate/v1_collect.py` | 888 | V1 수집 검증 — 다 받았는가 · 라벨이 맞는가. |
| `tools/trace_fill.py` | 840 | 추적표의 소스 · 화면 · 검사 칸을 기계로 채운다 (`inbox/ORDER_00_trace_fill.md`). |
| `tests/test_score.py` | 839 | 7장 판정·채점 시험. |
| `report/render.py` | 833 | 리포트 생성 (L9). |
| `tests/test_run.py` | 773 | S0~S3 종단 시험 (모의 응답). |
| `validate/v4_mapping.py` | 772 | V4 매핑 검증 — 이름이 아니라 값으로 검증한다. |
| `store/watch.py` | 746 | 후보 추적 (11장). |
| `collect/pipeline.py` | 730 | 실행 순서 · 중단 · 재처리 · 재개. |
| `report/screens/views.py` | 671 | 화면 전용 DTO. |
| `store/admin.py` | 665 | 관리자 — 계정 · 권한 · config 변경 (13장 앞부분). |
| `parse/encar/mapping.py` | 625 | 엔카 원문 → CORE 필드 (L3). |
| `store/dictionary.py` | 578 | 사전 저장소 (L5).  RAW 에서 생성한다. |
| `tests/test_admin.py` | 566 | 13장 앞부분 시험 — 계정 · 권한 · config 변경. |
| `tests/test_admin_flow.py` | 566 | 관리 화면 동작 시험 (13장 · 14장). |
| `tools/check_spec.py` | 557 | CarWatch v2 지시서 자체 점검 — 7종 |
| `tests/test_web.py` | 514 | 14장 표현 계층 시험 — 템플릿 · 라우팅. |
| `tools/build_index.py` | 492 | 검사 색인 · 소스 색인을 만든다 (규칙 11). |
| `contracts.py` | 466 | 계층 간 계약 — Protocol · DTO. |
| `web/app.py` | 465 | 화면 조립 (14장 STEP 144 · 147 · 149). |
| `run.py` | 412 | CarWatch v2 진입점. |
| `report/views.py` | 391 | 리포트 DTO (L9). |
| `tools/sync_registry.py` | 390 | RAW 경로 전수 → meta_field_usage. |
| `tests/test_pipeline.py` | 388 | 5장 수집 순서 시험. |
| `tests/test_collect.py` | 377 | 2장 수집 시험. |
| `tools/render_screens.py` | 331 | 전 화면을 실제로 렌더해 `outputs/render/` 에 남긴다. |
| `tools/collect_kbchachacha.py` | 330 | KB차차차 목록 수집 · 총 매물 수 세기 (명령서 `ORDER_20260822_r515.md` 3-2 · 단계 9). |
| `web/template.py` | 327 | 최소 템플릿 엔진 (14장 STEP 143). |
| `tools/light_check.py` | 325 | 가벼운 점검 — 4시간마다 (개정 335 · S29-0). |
| `parse/hyundai_cert/mapping.py` | 322 | 현대·제네시스 인증중고차 목록 카드 → CORE 필드 (L3). |
| `validate/v7_watch.py` | 320 | V7 관심·추적 검증. |
| `tools/build_dict.py` | 317 | RAW → 사전 생성. |
| `validate/v9_multisite.py` | 305 | V9 — 다중 사이트 (`docs/chapters/50-multisite.md`). |
| `analyze/axis/state.py` | 302 | ② 상태 150 — 차가 성한가 (docs/ref/F-scoring.md ②). |
| `tools/collect_hyundai_cert.py` | 295 | 현대·제네시스 인증중고차 목록 수집 (명령서 `ORDER_20260822_r515.md` 3장 · 단계 11). |
| `store/crosssite.py` | 291 | 다중 사이트 확장 (12장). |
| `tests/test_endtoend.py` | 291 | 종단 시험 — 수집부터 리포트까지 (5장 STEP 47 · 49). |
| `adapters/encar.py` | 290 | 엔카 어댑터 — URL · 헤더 · 쿼리 조립. |
| `tests/test_dict.py` | 288 | 4장 키·코드·사전 시험. |
| `tests/test_screens.py` | 287 | 10장 화면 시험. |
| `store/raw.py` | 285 | RAW 저장소 (L2).  원문 무손실.  삭제 금지. |
| `tests/test_fixtures.py` | 284 | 실물 표본 시험 — v1 원문 12건. |
| `tests/test_crosssite.py` | 282 | 12장 다중 사이트 시험. |
| `tools/collect_kcar.py` | 276 | K카 상세 수집 (명령서 `ORDER_20260822_r515.md` 3-3 · 단계 10). |
| `report/exports/export.py` | 269 | 내보내기. |
| `tools/check_screens.py` | 264 | 화면 ↔ 시안 대조 (10장 · 14장). |
| `tests/test_report.py` | 263 | 9장 리포트 시험. |
| `tests/test_watch.py` | 259 | 11장 후보 추적 시험. |
| `web/server.py` | 259 | HTTP 서버 (14장 STEP 141 · 150). |
| `tests/test_store.py` | 255 | 3장 테이블 시험. |
| `tools/menu.py` | 254 | 실행 메뉴. |
| `tests/test_registry.py` | 245 | 8장 등록부 시험. |
| `validate/v5_value.py` | 242 | V5 수치 검증 — 기준값이 맞는가 · 보정이 타당한가. |
| `analyze/axis/site.py` | 240 | ⑤ 사이트 보증 50 · ⑦ 제조사 보증 50 (일반 20 + 동력계 30). |
| `tests/test_invariants.py` | 232 | 불변식 시험. |
| `web/context.py` | 213 | 화면 문맥과 오류 (14장 STEP 144 · 148). |
| `validate/base.py` | 212 | 검증 계약. |
| `tools/unknown_split.py` | 208 | 「확인 안 됨」을 ①②③④ 로 가른다 (개정 434 · 435 · V1-27 · V1-28). |
| `tests/seed.py` | 204 | 시험용 씨앗 DB — 운영 DB 를 복사하지 않는다. |
| `parse/kcar/mapping.py` | 190 | K카 상세 → `core_listing` (`docs/KCAR_API.md` 3장 · `MULTISITE_MAPPING.md` 1장). |
| `parse/importer.py` | 182 | 반입 입력 해석 (13장 STEP 136a · 136b). |
| `parse/kbchachacha/mapping.py` | 182 | KB차차차 상세 → `core_listing` (`docs/KBCHACHACHA_API.md` 3장). |
| `tools/classify_unclassified.py` | 175 | 미분류 경로를 원인별로 가른다 (개정 341 · V4-26 · V4-27). |
| `web/session.py` | 175 | 세션 · CSRF · 정적 파일 (14장 STEP 145~147). |
| `tools/migrate.py` | 174 | 스키마 이행 — 기존 DB 를 현재 DDL 에 맞춘다. |
| `parse/bobaedream/mapping.py` | 172 | 보배드림 상세 → `core_listing` (`docs/BOBAEDREAM_API.md` 2·3·1a장). |
| `tools/sync_target_map.py` | 172 | 차종 대응표 → `dict_enum` (명령서 `ORDER_20260822_r515.md` 2a장 · 개정 540). |
| `tools/daily_check.py` | 170 | 일일 점검 — 매일 23:00 (개정 334 · S29). |
| `score/penalty.py` | 166 | 마이너스 점수 (개정 322). |
| `tools/collect_bobaedream.py` | 165 | 보배드림 수집 (명령서 7단계 · `docs/BOBAEDREAM_API.md`). |
| `tools/weekly_check.py` | 163 | 주간 일제 점검 — 금 02:00 · 개발측 몫 (개정 334 · S29). |
| `tools/collect_heydealer.py` | 160 | 헤이딜러 수집 — 토큰 → 차종별 목록 → 상세 (명령서 37). |
| `score/scorer.py` | 159 | 채점 · 분모 (L7). |
| `analyze/axis/value.py` | 156 | ① 값 250 — 시세 대비 100 · 신차가 대비 80 · 주행 대비 70. |
| `report/finance.py` | 153 | 금융 — 점수가 아니라 비용이다. |
| `store/pii.py` | 152 | 개인정보 분리 (L4). |
| `tools/collect_kia_cpo.py` | 152 | 기아 인증중고차(CPO) 목록 수집 (명령서 `ORDER_20260822_r515.md` 3-1 · 단계 8). |
| `collect/worker.py` | 147 | 큐 소비기 (13장 STEP 132a · 개정 261). |
| `score/adjust.py` | 145 | 배점 조정 — 비율 재배분과 정수 보정. |
| `tools/repair_facet_chunks.py` | 144 | 낱개로 저장된 facet 조각을 이어붙인다 (개정 307 사고 복구). |
| `web/routes.py` | 144 | 라우팅 표 (14장 STEP 142). |
| `analyze/axis/history.py` | 143 | ③ 이력 80 — 어떻게 쓰였나 (docs/ref/F-scoring.md ③). |
| `tools/classify_registry.py` | 142 | 등록부 미분류 정리 — 근거가 있는 것만 (8장 STEP 87 · V4-11). |
| `tools/run_tests.py` | 142 | 시험 전체 실행. |
| `adapters/kbchachacha.py` | 141 | KB차차차 어댑터 — URL · 헤더 (1장 STEP 11). |
| `parse/heydealer/mapping.py` | 139 | 헤이딜러 원문 → `core_listing` (명령서 37-3 ② · `docs/HEYDEALER_API.md`). |
| `tools/classify_fields.py` | 139 | 등록부 분류 초안 — 파서가 쓰는 경로를 근거로 자동 분류한다. |
| `parse/classify.py` | 136 | 분류 2단 — target_key 판정. |
| `tools/trace_verify.py` | 136 | 추적표 「상태」를 사실로 (개정 349 · 350 · S34). |
| `tools/daily_enqueue.py` | 134 | 하루 한 번 스스로 돈다 (STEP 136h · 개정 315). |
| `tools/collect_reborncar.py` | 127 | 리본카 수집 — 사이트맵 전량 → 우리 쪽에서 거른다 (명령서 39). |
| `collect/fetcher.py` | 121 | 원문 획득 · 형식 검증. |
| `adapters/heydealer.py` | 120 | 헤이딜러 어댑터 — 토큰 두 걸음 (명령서 37 · `docs/HEYDEALER_API.md` 0장). |
| `adapters/kia_cpo.py` | 118 | 기아 인증중고차(CPO) 어댑터 — URL · 헤더 (1장 STEP 11). |
| `analyze/axes.py` | 118 | 축 판정 계약. |
| `parse/kia_cpo/mapping.py` | 118 | 기아 인증중고차(CPO) 원문 → CORE 필드 (L3). |
| `adapters/kcar.py` | 115 | K카 어댑터 — URL · 헤더 (12장 · STEP 11). |
| `errors.py` | 115 | 도메인 예외 5종. |
| `parse/reborncar/mapping.py` | 115 | 리본카 상세 → `core_listing` (명령서 39 · `docs/REBORNCAR_API.md` 1b). |
| `tools/gen_table.py` | 114 | 배점표를 config 에서 생성한다 (개정 512). |
| `tools/collect_volvo.py` | 111 | 볼보 셀렉트 수집 — xhr-results 쪽넘김 (명령서 1a). |
| `tools/classify_stored.py` | 110 | 저장된 매물을 ★ 갈래에 넣는다 — ★ 사이트 도구가 쓴 줄용 (명령서 37·39). |
| `tools/collect_bmw.py` | 110 | BMW 바바리안(BPS) 수집 (명령서 1a). |
| `tools/report_cli.py` | 109 | 리포트 재생성 (9장 STEP 90 · 91a · B-6). |
| `tools/check_all.py` | 107 | 실측 DB 회귀 — V1~V5 · V10 전건을 한 번에 돌린다. |
| `tools/collect_lexus.py` | 101 | 렉서스 인증중고 수집 (명령서 1a). |
| `store/tools.py` | 97 | 관리 도구 (13장 STEP 135). |
| `analyze/axis/taste.py` | 94 | ④ 취향 50점 — HUD 15 · 선루프 10 · 색상 10 · 지정 옵션 15. |
| `analyze/verdict.py` | 94 | 판정 엔진 — 순서 무관 put(). |
| `tools/recalc_catchup.py` | 94 | 재판정이 밀렸으면 채운다 (명령서 14-3 · 마스터 지시 08-24). |
| `tools/export_cli.py` | 93 | 데이터 내보내기 (9장 STEP 91a · B-6). |
| `tools/setup_check.py` | 92 | 착수 점검 — 실행 전에 무엇이 준비됐는지 한 번에 본다. |
| `analyze/axis/price.py` | 90 | 가격 200점. |
| `analyze/absolute.py` | 88 | E등급 절대조건 10종. |
| `score/grade.py` | 88 | 등급 (L7). |
| `analyze/axis/spec.py` | 87 | 사양 90점 — HUD 20 · 선루프 20 · SVM 10 · SCC 10 · 후측방 5 · 틴팅 5. |
| `analyze/axis/trim.py` | 83 | ④ 사양 45 — 트림 25 · 옵션 20 (docs/ref/F-scoring.md ④). |
| `tools/deploy_check.py` | 81 | 배포 확인 — ★ 「소스가 맞다」와 「마스터 화면이 맞다」는 다른 말이다. |
| `analyze/peer.py` | 80 | 유사군 — 「이런 차가 보통 얼마인가」 (7장 STEP 82e). |
| `report/why_cheap.py` | 80 | 「왜 싼가」 — 싼 이유를 순서대로 찾아 낸다 (개정 299 · V3-52). |
| `store/chunk.py` | 77 | 조각 전송 — 바이트를 나누고 서버가 이어붙인다 (개정 307). |
| `adapters/bobaedream.py` | 75 | 보배드림 어댑터 — URL · 헤더 (1장 STEP 11). |
| `tools/fold_out_of_scope.py` | 75 | 이미 들어온 것을 ★ 되돌린다 — ★ 우리 대상이 아닌 것은 ★ 접는다 (명령서 3-3). |
| `tools/inspect_dict.py` | 75 | 사전 검토 — pending 값과 원문 표본을 본다. |
| `tools/inspect_facet.py` | 74 | facet 원문에 실제로 어떤 축이 왔는지 본다. |
| `analyze/trust.py` | 70 | 플랫폼 신뢰도 — 점검 출처 · 엔카진단 · 엔카보증 (개정 300). |
| `parse/target_rules.py` | 69 | 차종군 + `targets.json` 규칙으로 ★ 갈래를 고른다. |
| `analyze/curve.py` | 61 | 구간별 점수표 (docs/ref/F-scoring.md). |
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

## 큰 파일 — 무엇이 어디에 (200줄 이상 73개)

### `validate/v11_web.py` — 4,882줄

```
_web_sources:643  run:655  _late_checks:765  _templates_with_form:829  _spec_routes:847  _screen_routes:872  _routing_table_check:896  _count:933  ctx_account:940  _view_exists:946  _tpl:967  _all_templates:972  _screen_checks:977  _query_budget_check:1218  _import_origin_check:1297  _import_step4_check:1332  _browser_origin_check:1356  _browser_confirm_check:1374  _browser_chunk_check:1399  _status_screen_checks:1440  _status_liveness_check:1478  _menu_label_check:1519  _menu_paths:1547  _listing_rows:1572  _cli_caps:1590  _cli_only_check:1604  _stale_notice_check:1649  _trim_detail_check:1685  _option_sum_check:1708  _heart_line_check:1735  _recommend_terms_check:1756  _lease_checks:1775  _pick_filter_checks:1835  _shortfall_check:1874  _cash_limit_check:1893  _py_files:1924  _menu_no_path_check:1938  _listing_paging_checks:1956  _photo_checks:1992  _compare_shape_check:2033  _detail_shape_checks:2083  _filter_shape_checks:2161  _row_shape_checks:2231  _menu_shape_checks:2303  _sian_css_checks:2378  _cell_of:2440  _link_tip_checks:2463  _origin_link_check:2477  _choose_check:2505  _order_filter_checks:2521  _checks_cfg:2564  _photo_size_by_screen_check:2573  _template_leak_check:2597  _em_dash_check:2623  _card_limits:2659  _cells_of:2676  _matches:2704  _grid_areas:2724  _hidden_cells:2754  _brace_block:2779  _place_cards:2793  _card_shape_checks:2915  _why_order_spec:3013  _why_order_check:3030  _width_policy:3065  _width_checks:3072  _chart_check:3160  _row_link_checks:3191  _screen_contradiction_check:3227  _chunk_check:3249  _csrf_reuse_check:3289  _origin_price_check:3333  _v1_parity_checks:3369  _media_blocks:3459  _responsive_checks:3480  _dead_links:3561  _null_link_check:3575  _sian_visual_check:3639  _purchase_cost_checks:3703  _report_popup_check:3790  _detail_photo_check:3864  _raw_shown_checks:3915  _compare_diff_check:4002  _chunk_message_check:4066  _whole_char:4093  _chunk_boundary_check:4106  _cell_squeeze_check:4194  _static_version_check:4249  _axis_state_check:4267  _three_values_check:4310  _photo_size_check:4349  _render_metrics_checks:4375  _browser_scope_checks:4474  _import_opened_steps_check:4495  _import_resume_check:4523  _watch_invite_check:4542  _post_smoke_check:4586  _template_roots:4659  _loop_fields:4669  _context_supplied_check:4691  _first_item:4762  _has_field:4776  _table_counts:4782  _save_button_check:4789  _probe:4846  _scratch:4864
```

### `report/screens/build.py` — 3,121줄

```
site_badge:75  axis_heads:95  _grade_order:105  _not_ranked:118  _labels:132  viewer_state:137  _unknown_cfg:147  is_unknown:158  chip:174  _stamp:210  _bulk_axes:214  confirm_ratio:235  _bulk_changes:246  _total_points:273  photo_urls:286  photo_url:318  market_price:349  _days_between:366  _ceil_to:381  _bulk_market:396  _bulk_state:435  not_join_months:468  _left:491  _warranty_state:500  _axis_state:538  _sites_cfg:602  _row:615  _pen_rows:827  _pen_axes:838  _pen_sum:859  _pen_words:867  _view_cfg:876  order_clause:925  _view_str:931  _lease_kinds:937  excluded_hidden:945  lease_hidden:961  _option_group_match:983  _listings_where:998  count_listings:1176  view_listings:1188  _score_bars:1302  _group_caps:1322  _view_list:1340  _view_dict:1345  _soh_low:1350  _view_int:1359  _bucket:1365  _high_km:1372  _option_prices:1381  recommend_funnel:1393  _bulk_upside:1411  view_recommend:1426  recommend_reason:1461  excluded_groups:1504  view_why:1522  _compare_conclusion:1528  view_compare:1551  market_trims:1618  view_market:1640  _web_cfg:1676  _median:1690  _with_height:1695  _price_bins:1710  _group_prices:1731  _by_year:1749  _year_line:1766  _by_trim:1792  _other_targets:1810  count_dealers:1818  _dealer_targets:1824  _dealer_region:1844  view_dealers:1859  view_run:1895  _rank1_of:1901  view_dashboard:1909  _bars:2045  _grade_counts:2060  _relax_sim:2078  _axis_shortfall:2099  _progress:2118  _gone_and_watch:2133  _e_reasons:2176  _today_changes:2194  _step_rows:2219  _bulk_spark:2236  view_watch:2272  _days_since:2363  _pending_values:2388  _done_items:2397  view_notready:2423  _unmatched_rows:2464  _report_files:2509  view_reports:2541  _warranty_until:2597  _verdict_lines:2646  _manwon_str:2688  _unknown_lines:2695  _price_history:2727  _alternatives:2744  _rep_flt:2780  view_detail:2786  _quartiles_by_target:2828  market_by_target:2852  _grade_order:2889  _grade_step:2904  _miss_axes:2910  view_track:2930  _accident_split:2999  duplicate_listings:3012  _today_counts:3053  _notready_counts:3077  axis_zero_rates:3097
```

### `web/views.py` — 2,653줄

```
_rows_per_page:27  _cfg:31  _versions:36  page_extras:55  _points:64  page:86  listings:113  why:178  detail:230  _grade_help:263  notready:270  dashboard:280  admin_home:302  _unclassified_split:314  _rows_of:342  _check_reports:352  admin_audit:375  admin_docs:388  _int_param:412  _manwon:451  _site_buttons:456  _filter_chips:499  _order_menu:550  _carry:556  _order_label:566  ORDERS_LABELS_GET:570  _condition_sentence:574  _query_string:592  _page_links:605  _simple_paging:626  _paging:636  _filter_buttons:666  _model_menu:699  _pick_state:713  _option_name_buttons:772  _judge_buttons:825  _split_top:853  _distinct_options:858  _km_options:870  _grade_options:878  _keep_query:885  _carry_pick:910  _lease_hidden:920  _excluded_hidden:926  _excluded_why:933  _filter:943  recommend:1019  track:1047  compare:1064  market:1086  _first_target:1106  dealers:1112  watch:1132  _note_kinds:1149  _watch_notes:1156  run_view:1183  login:1195  _login_again:1237  _open_session:1253  logout:1294  _watch_queries:1311  watch_query_post:1320  _int_or_none:1350  watch_add_post:1354  _watch_note_post:1414  _watch_invite:1440  watch_update_post:1463  _now:1487  _reason_gate:1494  _gate:1515  _first_flag:1554  _all_hours:1559  admin_run:1587  _target_rows:1653  admin_dict:1666  admin_status:1703  admin_collect:1718  _take_chunk:1777  _verify_part:1820  _run_stamp:1860  _int_or_none:1871  admin_import:1876  admin_scoring:1948  _decide_cards:2001  admin_registry:2029  admin_query:2077  admin_requests:2099  _admin_extra:2161  _config_files:2176  _config_rows:2183  admin_config:2215  _typed:2266  admin_api:2282  _site_query:2332  admin_targets:2345  admin_tools:2443  join:2462  password:2493  admin_users:2508  _account_activity:2568  reports:2574  report_download:2590
```

### `validate/v3_logic.py` — 2,265줄

```
_file_output_checks:384  _conflict_checks:437  _diagnosis_count_check:461  _sort_determinism:478  _warning_contract_checks:495  _list_observed_source_check:590  _facet_reconcile_check:620  _record_mismatch_check:664  _curve_table_check:694  _special_null_check:761  _grade_base_checks:789  _checks_cfg:882  _labels_cfg:896  _unknown_mark_checks:904  _grade_cut_checks:955  _points_cap_checks:1065  _worse_of_checks:1117  _checks_json:1179  _value_curve_checks:1190  _group_sum_checks:1280  _mapped_other_check:1391  _denominator_check:1418  _core_axis_check:1446  _rental_cross_check:1467  _why_cheap_check:1505  _source_before_value_check:1546  _absolute_cut_check:1581  _spec_files:1611  _confirm_ratio_check:1621  _warranty_checks:1671  _spec_axis_check:1705  _site_axis_checks:1746  _rendered_why:1795  _rendered_listings:1805  _fill_gap_check:1815  _points_sum_check:1848  _market_gap_check:1865  _bonus_checks:1921  _trim_price_check:2025  run:2073  _shuffle_check:2208  _halt_dict_check:2233  _ensure_tmp:2262
```

### `store/core.py` — 1,582줄

```
resolve_listing_id:38  resolve_dealer_id:56  serialize_container:72  record_change:83  split_pii:105  flush_dealer_pii:152  _record_dropped:164  classify_invariant_change:199  _lookback:239  _source_history:253  _schema_change_min:279  _current:293  _today:299  upsert_core:303  mark_gone:388  load_snapshot:405  build_identities:514  resolve_vehicle_id:540  merge_conflict:572  upsert_vehicle:583  upsert_dealer:604  upsert_child:631  _flag:652  _not_join_months:666  state_counts:691  current_versions:721  diagnosis_of:751  target_counts:764  top_target:771  vehicle_of:776  collect_scale:783  our_fault:803  catalog_coverage:812  _walk:856  _sample_bodies:872  hits_of:885  key_seen:904  stored_hits:919  sample_bodies:935  observed:957  known_leaves:995  has_unclassified:1010  classify_unclassified:1017  _card_limit:1060  _value_chars:1065  _admin_cfg:1070  unclassified_cards:1087  _peek:1143  _short:1190  _blocking_paths:1201  _raw_rows_max:1221  used_endpoints:1231  raw_sections:1240  _flatten:1279  option_diff:1303  _option_names:1341  blocking_keys:1357  full_hits:1375  axis_paths_empty:1400  blocking_rows:1437  record_mismatch_sql:1499  record_mismatch_count:1505  relist_counts:1531  listing_models:1548  filter_options:1568
```

### `collect/runner.py` — 1,491줄

```
CollectGroup:67  load_targets:91  collect_groups:104  facet_axes:144  aspect_names:165  check_facet_axes:169  interpret_failure:183  collect_check:212  FailStreak:279  _sleep:313  _log_request:319  _save_issues:330  make_executors:341  classify_in_group:880  _group_of:901  _fuel_of:916  _badge_of:922  _pages_for:928  _dicts:942  _option_medians:978  _market_medians:1024  _trim_ladders:1053  _option_base:1070  _site_grade_rules:1100  _listing_config:1116  _listing_values:1141  _option_money:1160  _owned_months:1179  _option_of:1191  _market_of:1199  _group_sums:1209  make_score_executors:1236  make_validate_executor:1420  make_registry_executor:1462
```

### `tests/test_spec_ui.py` — 1,461줄

```
rec:33  spec_a:43  spec_b:121  spec_c:195  spec_d:239  spec_f:272  spec_g:298  spec_h:346  spec_j:379  spec_m:422  spec_e:490  spec_i:533  spec_k:646  spec_csrf:701  spec_l:728  spec_monkey:763  flow_s1:835  flow_s2:904  flow_s5:988  flow_s3:1101  flow_s4:1176  flow_s6:1247  guide_v132:1303  main:1395  _write:1439
```

### `tests/test_integration.py` — 1,236줄

```
rec:31  Client:41  text:96  links:101  start_server:105  seed_admin:149  m1:165  m2:255  m3:329  m4:634  s3:705  unit:761  gaps:796  flows:904  guide7:1007  _account_id:1140  make_users:1147  main:1165  _write_table:1214
```

### `tools/check_src.py` — 1,156줄

```
_spec_files:44  _read_spec:62  say:73  py_files:87  chapter_of:127  _declared_chapters:137  split_done:157  _illustration:176  _retired_config_keys:240  _git:701
```

### `report/screens/admin.py` — 1,086줄

```
AdminMenuItem:32  AdminHome:80  SaveGate:106  AuditTab:120  AuditView:128  DocView:135  menu_for:146  view_admin_home:158  _todos:185  _recent_runs:225  _recent_changes:256  save_gate:267  view_audit:275  view_docs:321  _doc_files:352  Todo:373  RunRow:387  ChangeRow:397  _cfg_rows:417  config_history:427  query_history:439  db_tables:453  api_snapshots:494  account_activity:505  make_target_key:523  target_choices:542  target_rows:561  parse_import_text:592  status_view:607  _catalog_state:681  _light_result:713  _live_window:753  _live_progress:762  run_progress:809  collect_state:859  received_vs_used:916  dict_state:937  import_state:964  job_log:1001  validation_runs:1015  blocking_set:1033  _menu_groups:1057  _menu_by_group:1076
```

### `tools/verify_axes.py` — 1,079줄

```
_spec_text:26  _grade_order:59  _not_ranked:72  spec_tables:86  _num:109  pick:127  _flag:141  hand_market:149  _median_for:160  hand_mileage:180  _years:193  conn_now:202  lookup:207  hand_accident:231  hand_repair:241  hand_owner:249  _warranty_left:257  hand_warranty_general:278  hand_warranty_power:283  hand_site_warranty:289  hand_maker_warranty:319  _km_per_month:346  residual_spec:362  _json:388  hand_option_won:401  hand_depreciation:438  hand_frame:468  hand_outer:489  _leak_states:509  hand_leak:521  hand_lien:536  hand_not_join:546  hand_trim:576  hand_special:596  spec_section:606  spec_head_points:614  lookup_label:621  hand_integrity:629  hand_special_points:655  _taste_points:664  _has_option:675  hand_color:710  hand_usage:734  hand_site_grade:758  hand_inspection_src:778  hand_hud:791  hand_sunroof:800  hand_picked:809  _has_table:822  _option_prices:828  hand_options:846  survey:884  main:947
```

### `store/adminops.py` — 1,054줄

```
QueryLog:55  QueryResult:68  ApiSnapshot:93  DevRequest:104  RecalcJob:119  ScoringPreview:130  ImportPreview:142  ImportResult:159  preview_import:168  import_listings:194  _import_facet:260  BrowserCatch:295  save_browser_catch:303  mark_step_imported:353  pending_enums:384  pending_axis_summary:421  apply_dict_decision:449  _strip_sql:494  sql_reject_reason:501  _opened_tables:535  reject_kind_of:550  columns_hint:560  reap_stale_jobs:583  run_query:618  fetch_api:665  create_dev_request:699  update_dev_status:721  export_dev_requests:735  enqueue_recalc:765  enqueue_after_list_save:791  job_progress:816  db_progress:830  preview_scoring:840  _pt:883  registry_rows:887  registry_counts:898  write_dev_requests:904  dev_request_rows:924  save_api_snapshot:942  get_api_snapshot:965  path_table:984  halt_job:1020
```

### `validate/v0_guide.py` — 963줄

```
_read:24  s43_2_axis_ids:31  s44_4_scope_written:69  s44_5_site_consistent:101  s45_1_one_version:134  _order_files:157  s44_1_order_exists:170  s44_2_one_order:212  s43_2b_axis_renamed:227  s43_2c_no_hda:253  s45_5_no_axis_scores:299  s45_4_table_generated:337  s45_3_spec_totals:352  s45_2_mock_numbers:408  s44_3_specs_in_order:429  s43_3_version_matches:467  _h_tags:492  s46_21_one_screen_per_file:508  s46_22_section_order:533  _targets:574  s46_23_site_query_filled:580  s46_24_facet_unconfirmed:595  s46_30_index_covers_docs:612  s46_31_spec_sites_in_config:651  s46_32_generated_fresh:672  _req_rows:714  _tokens:726  _named_docs:741  s46_36_dropped_not_alive:753  s46_40_progress_docs_changed:781  s46_41_site_status_known:812  _templates:854  s46_45_spec_not_in_list:859  s46_46_spec_forbidden_ten:879  run:937
```

### `validate/v2_load.py` — 919줄

```
DayGapReport:151  GapCause:164  run:170  _surrogate_key_checks:347  _not_null_check:432  _chained_subscript_check:449  _Boom:497  _salvage_check:505  _table_exists:546  _exception_shape_checks:552  _schema_sync_check:618  _pii_access_check:655  gap_alerts:694  diff_prev_day:710  explain_gap:732  _pii_column_check:764  _secret_key_check:782  _parser_common_fields_check:820  _null_target_not_judged_check:871  _null_target_visible_check:896
```

### `validate/v10_admin.py` — 895줄

```
_sources:212  _admin_guard_checks:233  _sql_strings:278  _schedule_checks:290  _query_error_checks:333  run:432  _session_checks:538  _pii_query_check:618  _scratch:665  _dict_reason_check:680  _dict_source_shown_check:696  _automation_checks:714  _queue_consumer_check:847  _queue_stale_shown_check:876  _ensure_tmp:892
```

### `validate/v1_collect.py` — 888줄

```
_unknown_split_checks:171  _axis_empty_check:257  run:287  _endpoint_order_check:421  _empty_db_check:433  _sql_groups:460  _cumulative_codes:496  _run_scope_check:506  _ctx_started:544  _has_run_id:552  _expected_scope_check:557  _diagnosis_scope_check:578  _diagnosis_none_count:616  _query_key_check:639  _entrypoint_parity_check:676  _enclosing_def:705  _run_id_filled_check:714  _catalog_key_check:734  _whole_probe:756  _whole_body_check:767  _catalog_checks:798  _unparsed_envelope_check:845  _ensure_tmp:885
```

### `tools/trace_fill.py` — 840줄

```
spec_lines:94  anchor_step:112  build_symbols:131  enclosing:166  build_texts:176  _stem:214  tokens:223  _best_in:253  _rows:290  layers_of:303  layer_pool:310  _rare_hit:322  axis_words:346  json_key_at:367  _place:394  _hints:405  find_in_layer:421  _best_step_in:469  _layers:500  derive_state:520  src_mark:546  relayer:559  restate:574  fill_file:597  move_to_rules:665  survey:708  lists:736  write_index:757  main:796
```

### `tests/test_score.py` — 839줄

```
check:36  fx:42  snap:46  ctx:66  full_verdict:87  test_denominator:100  test_components_form:144  test_grade:195  test_order_independent:282  panels_of:305  test_history_real:310  test_rental_real:345  test_insurance:387  test_safety_real:412  test_spec_gate:461  test_price_real:530  test_color:600  test_price_pending:621  test_absolute_real:640  test_null_safe:680  test_empty_array_meaning:697  test_peer_group:722  test_damage_by_status:764  test_repair_cost_ratio:790  test_hda_gate:799
```

### `report/render.py` — 833줄

```
_labels:30  _stamp:35  _curve_points:50  _encar_url:93  _why_cheap_of:102  _scoring:143  _penalty_rows:151  _market_pos:165  _site_badge:209  _axis_why:216  _raw_sections:246  _photo_urls:256  _purchase_costs:279  render_listing:307  axis_mark:444  source_label:465  _option_rows:513  _fetch_views:573  _strengths:588  _weaknesses:595  _pending_best:602  _cost_rows:635  _known_issues:656  _diagnosis_view:674  render_target:685  render_run:766  render_halt:808  _j:826
```

### `tests/test_run.py` — 773줄

```
check:36  StubEncar:92  Clock:241  setup:246  test_envelope:284  test_last_page_exact:312  test_facet:319  test_facet_missing_axis:333  test_dict_step:342  test_all_groups:364  test_parse_pipeline:375  test_score_pipeline:479  test_validate:551  test_registry_gate:594  test_target_scope:651  test_catalog_key:683  test_wrapper_args:701  test_unclassified_listing:740
```

### `validate/v4_mapping.py` — 772줄

```
_paths:143  _layer_of:190  _unclassified_split:195  _layer_checks:233  _name_collision_check:329  _key:363  _decide_material_check:369  _blocking_list_check:433  run:490  _mapping_coverage_checks:631  _our_columns:661  _listing_value_scope_check:689  _dict_filled_check:709  _kind_check:720  propose_fix:734  _option_code_check:749  _is_sentence:766
```

### `store/watch.py` — 746줄

```
AlertConfig:58  WatchItem:71  TrackPoint:86  TrackEvent:101  WatchEvent:115  _cross_site_order:130  classify_duplicates:149  sync_duplicates:202  deduped_count:226  watch_add:236  assert_owner:275  watch_update:290  watch_close:310  note_add:331  notes_of:356  note_delete:374  track_snapshot:389  track_points:418  classify_cause:427  detect_events:439  message:497  notify:525  _grade_order:596  _not_ranked:609  add_watch_query:623  run_watch_queries:658  watch_query_rows:714  close_watch_query:728
```

### `collect/pipeline.py` — 730줄

```
envelope_scope:41  Reprocess:91  refetch_all:121  reprocess_plan:131  should_refetch:148  expected_for:160  step_report:194  halt_if:210  precheck:243  resume_point:297  config_hash:317  build_run_context_fields:323  stale_rows:332  save_step_report:347  run_step:371  _execute:409  completed_steps:426  run_pipeline:438  print_progress:487  silent_progress:506  from_step_for:520  web_reasons:526  check_recalc_origin:531  plan_recalc:543  _current:560  run_recalc:566  Defect:587  DefectReport:598  diagnose:619  _DiagCtx:643  _collect_defects:653  format_defects:707
```

### `report/screens/views.py` — 671줄

```
AxisChip:30  ScoreBar:55  ListingRow:71  ListingFilter:225  WatchRow:304  TargetStat:338  RelaxRow:347  MarketRow:354  ChangeRow:366  AttentionItem:376  ViewerState:384  DashboardView:398  CompareView:435  TrackPair:453  TrackView:476  MarketView:493  DealerRow:508  NotReadyView:529  TodayChange:560  StepRow:572  _min_sample:584  PendingValue:602  Bucket:615  ExcludedGroup:635  ReportFile:644  ReportsView:656
```

### `store/admin.py` — 665줄

```
_admin_cfg:46  ConfigChange:68  running_job:86  hash_secret:96  _split:104  create_account:109  account_count:145  needs_bootstrap:149  _recent_failures:161  _log_attempt:180  is_locked:190  unlock_account:205  authenticate:233  open_session:269  session_account:289  change_secret:306  revoke_sessions:330  _walk:341  get_path:365  set_path:370  _atomic_write:377  apply_config:387  _validate_blob:451  revert_config:464  history:488  classify_field:512  account_rows:565  admin_count:579  set_role:586  set_disabled:603  add_config_key:623
```

### `parse/encar/mapping.py` — 625줄

```
_get:30  _json:42  _won:53  _ym:73  _date10:83  _int:99  _bool:105  unpack_envelope:116  parse_list_item:124  parse_detail:171  parse_inspection:247  parse_record:295  _sample_chars:349  safe_field:363  parse_with_issues:385  _salvage:403  _parses:446  dig:453  as_list:476  _diag_comment:504  parse_diagnosis:511  parse_diagnosis_items:543  _text:551  parse_record_summary:561  parse_platform_check:587  parse_inspection_summary:594  parse_ev_battery:599  parse_sellingpoint:619
```

### `store/dictionary.py` — 578줄

```
CodeEntry:31  AxisPolicy:57  policy:101  scope_key:109  seed_fixed_enums:134  target_map:175  target_key_of:198  fuel_normalize:214  collect_group_of:237  match_target_name:242  known_model_names:259  known_model_of:276  mapped_of:281  upsert_enum:302  _handle_conflict:354  upsert_option3:375  retire_unseen:411  resolve_code:426  installed_option_names:464  normalize_enum:482  assert_no_unknown:498  bump_dict_version:541  list_pending:551  confirm_enum:559
```

### `tests/test_admin.py` — 566줄

```
_spec_menu_paths:31  check:46  setup:52  test_bootstrap:64  test_auth:94  test_apply_config:136  test_value_validation:174  test_revert:194  test_no_direct_edit:220  test_classify_field:249  test_run_query:323  test_dev_request:376  test_recalc_and_lock:406  test_admin_screens:440  test_v10:530
```

### `tests/test_admin_flow.py` — 566줄

```
check:32  _env:38  _cfg:55  _post:60  _get:65  flow_config:71  flow_scoring:107  _rescore:163  _sum:224  _dist:231  flow_targets:238  flow_registry:273  flow_run:313  flow_query:346  flow_api:372  flow_tools:409  flow_users:431  flow_requests:476  flow_permission:518  main:531
```

### `tools/check_spec.py` — 557줄

```
_read_spec:10  _refs_source:73  _spec_files:284  _guide_files:368  _sections:373  _md:468
```

### `tests/test_web.py` — 514줄

```
check:21  test_routes:28  test_template:77  test_no_logic_in_template:118  test_static_escape:133  test_session_cookie:145  test_error_page:163  test_layout:190  test_filters:219  test_empty_state:242  test_menu_by_role:269  test_guard_and_csrf:290  _call:337  test_screens_render:354  test_sketch_match:445  test_account_policy:460
```

### `tools/build_index.py` — 492줄

```
_py_files:48  _checks_in_code:73  _checks_in_docs:108  last_runs:141  _run_time:170  sort_checks:180  build_checks:197  _outline:269  build_source:280  build_schema:312  build_doc_index:371  check_fresh:436  main:469
```

### `contracts.py` — 466줄

```
Response:24  Clock:34  Fetcher:39  Rng:44  Request:52  EndpointSpec:60  FetchResult:71  TargetSpec:84  ListingSnapshot:141  AxisResult:230  Account:249  require_role:266  RunContext:283  StepReport:303  ResumePoint:327  clean_vin:348  total_of:359  RegressionReport:372  json_paths:383  shape_ok:431  shape_violations:464
```

### `web/app.py` — 465줄

```
menu_items:22  _tip:104  _label:109  empty_state:120  banner_of:139  _list_stale:173  static_version:199  build_page:227  check_post:248  redirect:270  take_flashes:290  _display_now:303  make_app:329  _Denied:441  build_context:449  _title_of:464
```

### `run.py` — 412줄

```
load:51  make_context:56  _filter_targets:70  _steps_from:89  cmd_collect:103  _grade_summary:171  cmd_admin_create:186  _collect_urls:203  _page_url:240  cmd_web:259  make_worker_ctx:290  make_worker_executors:296  cmd_delegate:334  _api_fetch:345  cmd_setup:355
```

### `report/views.py` — 391줄

```
VersionStamp:18  ReportMeta:30  AxisView:40  FinanceView:64  PurchaseCostItem:85  PurchaseCostView:94  DiagnosisView:118  FetchView:130  CostRow:144  ScoreView:153  CollectSummary:239  ClassifySummary:246  PriceSummary:253  AxisStat:262  CoefficientChange:272  DictChangeSummary:282  TargetReport:290  RunStep:302  RunReport:317  HaltReport:328  FixAction:345  NotifyResult:355  ExportResult:368  display_value:377  display_points:387
```

### `tools/sync_registry.py` — 390줄

```
FieldUsage:31  RegistrySyncReport:48  facet_path:66  scan_paths:74  shape_ok:79  _walk_values:92  collect_values:106  collect_paths:130  _has_value:169  _seed_for:185  sync_registry:196  suggest_usage:291  write_suggested:303  halt_report:330  list_by_usage:353  assert_registered:360
```

### `tests/test_pipeline.py` — 388줄

```
check:37  db:43  test_expected:49  test_halt:61  test_reprocess:82  test_refetch:107  test_precheck:115  test_resume_and_version:167  test_run_pipeline:195  test_recalc:230  test_pii_orphan:265  test_exception_becomes_halt:298  test_fixed_enum_bootstrap:319  test_envelope_scope:349
```

### `tests/test_collect.py` — 377줄

```
check:34  R:40  test_verify_shape:45  _Stub:80  _Clock:88  test_fetch_status:93  test_interpret_failure:106  test_facet_axes:118  test_collect_groups:146  test_build_q:167  test_collect_check:217  test_save_raw:232  test_fail_streak:261  test_all_fail_sample:303  test_diagnosis_scope:347
```

### `tools/render_screens.py` — 331줄

```
_shot_widths:32  _tmp_root:57  main:81  shot_paths:172  _localize_images:197  shoot:234
```

### `tools/collect_kbchachacha.py` — 330줄

```
_now:53  _get:57  fetch_ok:66  page_ids:83  load_filters:93  walk_group:108  count_all:143  probe_detail:169  store_details:188  main:251
```

### `web/template.py` — 327줄

```
f_won:48  f_km:64  f_pct:68  f_date:72  f_num:83  f_gradecls:90  _grade_classes:103  f_count:112  f_signcls:120  f_signwon:130  _index_key:157  _step:172  _lookup:184  _truthy:193  render_str:197  strip_comments:304  render:309
```

### `tools/light_check.py` — 325줄

```
_repair_max:45  _cfg:63  _run:68  collecting:74  screen_counts:95  db_counts:121  measure:139  index_counts:161  changed:185  _worse:203  failing:207  repair:220  main:253
```

### `parse/hyundai_cert/mapping.py` — 322줄

```
_int:31  cards:40  _fuel_of:65  _model_group:76  parse_card:94  _json:166  detail_text:173  _one:180  parse_detail:185  parse_detail_all:191  _num:249  _warranty:256  _months_left:299  _options:316
```

### `validate/v7_watch.py` — 320줄

```
_cols:85  _reads:89  _progress_note_check:117  _relist_check:201  run:227
```

### `tools/build_dict.py` — 317줄

```
DictBuildReport:63  extract_distinct:78  _facet_values:106  facet_value_set:122  _walk_path:141  load_fixed_enums:168  build_dict:176  _mark_facet_substituted:227  build_catalog_dict:251  build_late_dict:289
```

### `validate/v9_multisite.py` — 305줄

```
_sites:69  live_sites:75  _labels:83  _badge_check:98  _hardcoded_badges:133  _origin_check:156  _warranty_sum_check:186  _tie_break_check:223  _axis_site_check:261  run:301
```

### `analyze/axis/state.py` — 302줄

```
_panels:43  _rank_worst:47  insurance_trace:59  panel_trace:68  worse_step:80  _accident:87  _frame:109  _outer:129  _repair:151  _special:162  leak_state:174  _leak:196  _site_never:206  _sites_table:218  _consumable:236  _integrity:258  analyze_state:294
```

### `tools/collect_hyundai_cert.py` — 295줄

```
target_of:69  _now:85  _post:89  _get:99  fetch_detail:110  load_filters:119  total_count:151  walk:164  main:191
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

### `store/raw.py` — 285줄

```
batch:36  commit:62  open_db:68  _safe_headers:85  save_raw:92  save_import_raw:141  save_browser_raw:174  save_browser_facet:209  save_import_facet:235  save_facet:265
```

### `tests/test_fixtures.py` — 284줄

```
check:33  fx:39  test_inspection:53  test_frame_vs_outer:84  test_record:123  test_detail:152  test_classify_real:172  test_catalog:207  test_diagnosis:219
```

### `tests/test_crosssite.py` — 282줄

```
check:34  db:40  add:45  test_vin:63  test_vin_parse:107  test_cross_site:129  test_regression:175  test_readiness:207  v9_04_site_isolation:229
```

### `tools/collect_kcar.py` — 276줄

```
_now:43  fetch:47  classify:61  accident_of:76  fetch_stock:85  collect_list:104  main:190
```

### `report/exports/export.py` — 269줄

```
filename:26  _stamp_lines:32  listing_md:38  listing_csv:76  halt_md:93  target_md:114  run_md:136  _asdict:186  export:194  output_path:233  write_export:241
```

### `tools/check_screens.py` — 264줄

```
_pairs:23  say:72  _text:81  check_pairs:88  check_phrases:101  _sian_heads:133  _heads:151  check_sections:170  check_nav:193  check_render:213  main:247
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

### `validate/v5_value.py` — 242줄

```
run:60  _grade_ratio_checks:151  _denominator_suite:193
```

### `analyze/axis/site.py` — 240줄

```
remaining_months:26  warranty_points:39  _truthy:73  warranty_grade:89  _seller_only:115  _one_step_down:124  _site:136  _maker:169  _maker_default:201  analyze_site:238
```

### `tests/test_invariants.py` — 232줄

```
check:35  inv1_order_independent:42  inv1_shuffle_100:72  inv2_banned:95  inv5_points:113  put_contract:126  excluded_contract:143  inv3_source_not_null:169  inv4_label_shape:188  inv6_no_unclassified:204
```

### `web/context.py` — 213줄

```
MenuItem:31  Banner:42  PageContext:55  ErrorPage:92  _is_permission:135  _is_conflict:140  _clean:145  _is_sql_typo:156  error_page:166
```

### `validate/base.py` — 212줄

```
_cfg:24  Check:55  CheckResult:93  _short:118  result:131  not_applicable:140  save_results:145  gate:162  run_phase:171  canon_files:193  canon_text:206
```

### `tools/unknown_split.py` — 208줄

```
_cfg:35  _walk:41  classify:51  main:125
```

### `tests/seed.py` — 204줄

```
_cfg:46  build_seed_db:51  _confirm_dict:103  seed_db_path:119  _ensure_secrets:132  _seed_unclassified:148
```

