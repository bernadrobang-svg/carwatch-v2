# 소스 색인

**`python3.11 tools/build_index.py` 가 만든다. 손으로 고치지 않는다.**

파일 131개 · 총 41,733줄

| 파일 | 줄 | 무엇 |
|---|--:|---|
| `validate/v11_web.py` | 3,093 | V11 표현 계층 검증 (14장 STEP 153). |
| `web/views.py` | 1,929 | 화면 어댑터 (14장 STEP 142 · 152). |
| `report/screens/build.py` | 1,630 | 화면 데이터 생성. |
| `tests/test_spec_ui.py` | 1,450 | 규격 기준 통합 테스트 (통합테스트_시나리오_규격기준.md). |
| `collect/runner.py` | 1,317 | 수집 실행 규칙. |
| `tests/test_integration.py` | 1,212 | 통합 테스트 — 실제 HTTP 로 전 화면 (통합테스트_시나리오.md). |
| `validate/v3_logic.py` | 1,134 | V3 로직 검증 — 판정이 작동하는가 · 변별력이 있는가. |
| `report/screens/admin.py` | 1,000 | 관리자 화면 — 표현 계층 (13장 STEP 138 · 138a). |
| `tools/verify_axes.py` | 988 | 손계산 대조 — 축마다 표본 3건 (개정 329 전수검증 · V3-66). |
| `store/core.py` | 937 | CORE 저장소 (L4).  사이트 무관 공통 스키마. |
| `store/adminops.py` | 931 | 관리자 서버 계층 — 실행 지시 · 쿼리 · API 조회 · 개발 요청 · 미리보기. |
| `validate/v2_load.py` | 872 | V2 적재 검증 — 옮겨졌는가 · 전일 대비 변동이 타당한가. |
| `tools/check_src.py` | 814 | CarWatch v2 — 지시서 ↔ 소스 대조 검증기. |
| `tests/test_score.py` | 782 | 7장 판정·채점 시험. |
| `tests/test_run.py` | 754 | S0~S3 종단 시험 (모의 응답). |
| `collect/pipeline.py` | 689 | 실행 순서 · 중단 · 재처리 · 재개. |
| `validate/v1_collect.py` | 670 | V1 수집 검증 — 다 받았는가 · 라벨이 맞는가. |
| `validate/v4_mapping.py` | 624 | V4 매핑 검증 — 이름이 아니라 값으로 검증한다. |
| `parse/encar/mapping.py` | 621 | 엔카 원문 → CORE 필드 (L3). |
| `store/watch.py` | 612 | 후보 추적 (11장). |
| `store/admin.py` | 609 | 관리자 — 계정 · 권한 · config 변경 (13장 앞부분). |
| `report/render.py` | 575 | 리포트 생성 (L9). |
| `tests/test_admin_flow.py` | 566 | 관리 화면 동작 시험 (13장 · 14장). |
| `validate/v10_admin.py` | 541 | V10 관리자 검증. |
| `tests/test_admin.py` | 537 | 13장 앞부분 시험 — 계정 · 권한 · config 변경. |
| `tests/test_web.py` | 497 | 14장 표현 계층 시험 — 템플릿 · 라우팅. |
| `tools/check_spec.py` | 475 | CarWatch v2 지시서 자체 점검 — 7종 |
| `contracts.py` | 450 | 계층 간 계약 — Protocol · DTO. |
| `report/screens/views.py` | 440 | 화면 전용 DTO. |
| `store/dictionary.py` | 440 | 사전 저장소 (L5).  RAW 에서 생성한다. |
| `web/app.py` | 426 | 화면 조립 (14장 STEP 144 · 147 · 149). |
| `run.py` | 404 | CarWatch v2 진입점. |
| `tests/test_pipeline.py` | 382 | 5장 수집 순서 시험. |
| `tests/test_collect.py` | 368 | 2장 수집 시험. |
| `tools/sync_registry.py` | 345 | RAW 경로 전수 → meta_field_usage. |
| `report/views.py` | 322 | 리포트 DTO (L9). |
| `tools/render_screens.py` | 321 | 전 화면을 실제로 렌더해 `outputs/render/` 에 남긴다. |
| `tools/build_dict.py` | 298 | RAW → 사전 생성. |
| `adapters/encar.py` | 285 | 엔카 어댑터 — URL · 헤더 · 쿼리 조립. |
| `store/raw.py` | 285 | RAW 저장소 (L2).  원문 무손실.  삭제 금지. |
| `tests/test_fixtures.py` | 284 | 실물 표본 시험 — v1 원문 12건. |
| `web/template.py` | 284 | 최소 템플릿 엔진 (14장 STEP 143). |
| `tests/test_dict.py` | 280 | 4장 키·코드·사전 시험. |
| `tests/test_crosssite.py` | 275 | 12장 다중 사이트 시험. |
| `tests/test_screens.py` | 274 | 10장 화면 시험. |
| `report/exports/export.py` | 271 | 내보내기. |
| `tests/test_watch.py` | 259 | 11장 후보 추적 시험. |
| `tools/menu.py` | 254 | 실행 메뉴. |
| `tests/test_endtoend.py` | 247 | 종단 시험 — 수집부터 리포트까지 (5장 STEP 47 · 49). |
| `tests/test_registry.py` | 245 | 8장 등록부 시험. |
| `tests/test_report.py` | 244 | 9장 리포트 시험. |
| `validate/v5_value.py` | 242 | V5 수치 검증 — 기준값이 맞는가 · 보정이 타당한가. |
| `tests/test_store.py` | 233 | 3장 테이블 시험. |
| `tests/test_invariants.py` | 232 | 불변식 시험. |
| `tools/check_screens.py` | 230 | 화면 ↔ 시안 대조 (10장 · 14장). |
| `store/crosssite.py` | 225 | 다중 사이트 확장 (12장). |
| `tools/build_index.py` | 212 | 검사 색인 · 소스 색인을 만든다 (규칙 11). |
| `tools/light_check.py` | 208 | 가벼운 점검 — 4시간마다 (개정 335 · S29-0). |
| `validate/base.py` | 207 | 검증 계약. |
| `analyze/axis/state.py` | 203 | ② 상태 150 — 차가 성한가 (docs/ref/F-scoring.md ②). |
| `web/server.py` | 199 | HTTP 서버 (14장 STEP 141 · 150). |
| `validate/v7_watch.py` | 194 | V7 관심·추적 검증. |
| `parse/importer.py` | 182 | 반입 입력 해석 (13장 STEP 136a · 136b). |
| `web/context.py` | 181 | 화면 문맥과 오류 (14장 STEP 144 · 148). |
| `tests/seed.py` | 178 | 시험용 씨앗 DB — 운영 DB 를 복사하지 않는다. |
| `web/session.py` | 175 | 세션 · CSRF · 정적 파일 (14장 STEP 145~147). |
| `tools/migrate.py` | 174 | 스키마 이행 — 기존 DB 를 현재 DDL 에 맞춘다. |
| `tools/daily_check.py` | 170 | 일일 점검 — 매일 23:00 (개정 334 · S29). |
| `tools/weekly_check.py` | 163 | 주간 일제 점검 — 금 02:00 · 개발측 몫 (개정 334 · S29). |
| `validate/v9_multisite.py` | 163 | V9 — 다중 사이트 (`docs/chapters/50-multisite.md`). |
| `store/pii.py` | 152 | 개인정보 분리 (L4). |
| `score/adjust.py` | 145 | 배점 조정 — 비율 재배분과 정수 보정. |
| `tools/repair_facet_chunks.py` | 144 | 낱개로 저장된 facet 조각을 이어붙인다 (개정 307 사고 복구). |
| `score/scorer.py` | 142 | 채점 · 분모 (L7). |
| `tools/classify_registry.py` | 142 | 등록부 미분류 정리 — 근거가 있는 것만 (8장 STEP 87 · V4-11). |
| `parse/classify.py` | 136 | 분류 2단 — target_key 판정. |
| `analyze/axis/history.py` | 132 | ③ 이력 80 — 어떻게 쓰였나 (docs/ref/F-scoring.md ③). |
| `collect/worker.py` | 132 | 큐 소비기 (13장 STEP 132a · 개정 261). |
| `web/routes.py` | 129 | 라우팅 표 (14장 STEP 142). |
| `analyze/axis/spec.py` | 123 | 사양 90점 — HUD 20 · HDA 20 · 선루프 20 · SVM 10 · SCC 10 · 후측방 5 · 틴팅 5. |
| `collect/fetcher.py` | 121 | 원문 획득 · 형식 검증. |
| `tools/run_tests.py` | 121 | 시험 전체 실행. |
| `tools/classify_fields.py` | 118 | 등록부 분류 초안 — 파서가 쓰는 경로를 근거로 자동 분류한다. |
| `errors.py` | 115 | 도메인 예외 5종. |
| `analyze/axes.py` | 111 | 축 판정 계약. |
| `analyze/axis/site.py` | 110 | ⑤ 보증 30 — 제조사 보증 15 · 사이트 우수등급 10 · 점검 출처 5. |
| `tools/report_cli.py` | 109 | 리포트 재생성 (9장 STEP 90 · 91a · B-6). |
| `tools/check_all.py` | 107 | 실측 DB 회귀 — V1~V5 · V10 전건을 한 번에 돌린다. |
| `analyze/axis/value.py` | 106 | ① 값 250 — 시세 대비 100 · 신차가 대비 80 · 주행 대비 70. |
| `store/tools.py` | 97 | 관리 도구 (13장 STEP 135). |
| `tools/daily_enqueue.py` | 97 | 하루 한 번 스스로 돈다 (STEP 136h · 개정 315). |
| `report/finance.py` | 95 | 금융 — 점수가 아니라 비용이다. |
| `analyze/axis/taste.py` | 94 | ④ 취향 50점 — HUD 15 · 선루프 10 · 색상 10 · 지정 옵션 15. |
| `analyze/verdict.py` | 94 | 판정 엔진 — 순서 무관 put(). |
| `tools/export_cli.py` | 93 | 데이터 내보내기 (9장 STEP 91a · B-6). |
| `tools/setup_check.py` | 92 | 착수 점검 — 실행 전에 무엇이 준비됐는지 한 번에 본다. |
| `analyze/axis/price.py` | 90 | 가격 200점. |
| `analyze/absolute.py` | 88 | E등급 절대조건 10종. |
| `score/penalty.py` | 86 | 마이너스 점수 (개정 322). |
| `analyze/peer.py` | 80 | 유사군 — 「이런 차가 보통 얼마인가」 (7장 STEP 82e). |
| `report/why_cheap.py` | 80 | 「왜 싼가」 — 싼 이유를 순서대로 찾아 낸다 (개정 299 · V3-52). |
| `analyze/axis/trim.py` | 78 | ④ 사양 45 — 트림 25 · 옵션 20 (docs/ref/F-scoring.md ④). |
| `store/chunk.py` | 77 | 조각 전송 — 바이트를 나누고 서버가 이어붙인다 (개정 307). |
| `tools/inspect_dict.py` | 75 | 사전 검토 — pending 값과 원문 표본을 본다. |
| `tools/inspect_facet.py` | 74 | facet 원문에 실제로 어떤 축이 왔는지 본다. |
| `analyze/trust.py` | 70 | 플랫폼 신뢰도 — 점검 출처 · 엔카진단 · 엔카보증 (개정 300). |
| `score/grade.py` | 70 | 등급 (L7). |
| `tools/classify_unclassified.py` | 69 | 미분류 경로를 원인별로 가른다 (개정 341 · V4-26 · V4-27). |
| `analyze/curve.py` | 61 | 구간별 점수표 (docs/ref/F-scoring.md). |
| `analyze/axis/warranty.py` | 56 | 보증 100점 — 일반 50 + 파워트레인 50. |
| `tools/inspect_requests.py` | 52 | 요청 기록을 본다 — 무엇을 던졌고 무엇이 돌아왔는가. |
| `analyze/axis/safety.py` | 44 | 안전 40점 — 진단 20 + 보증상품 20. |
| `adapters/base.py` | 36 | 사이트 어댑터 인터페이스. |
| `report/peer.py` | 35 | 유사군 조회 (7장 STEP 82e). |
| `analyze/axis/_util.py` | 33 | 축 공용 도우미. |
| `analyze/axis/color.py` | 33 | 색상 40점. |
| `analyze/engine.py` | 32 | 판정 실행 (L6).  축 함수를 순서 무관하게 호출한다. |
| `analyze/axis/mileage.py` | 31 | 주행거리 30점. |
| `adapters/__init__.py` | 1 | — |
| `analyze/__init__.py` | 1 | — |
| `analyze/axis/__init__.py` | 1 | — |
| `collect/__init__.py` | 1 | — |
| `parse/__init__.py` | 1 | — |
| `parse/encar/__init__.py` | 1 | — |
| `report/__init__.py` | 1 | — |
| `report/exports/__init__.py` | 1 | — |
| `report/screens/__init__.py` | 1 | — |
| `score/__init__.py` | 1 | — |
| `store/__init__.py` | 1 | — |
| `tests/__init__.py` | 1 | — |
| `validate/__init__.py` | 1 | — |

## 큰 파일 — 무엇이 어디에 (200줄 이상 60개)

### `validate/v11_web.py` — 3,093줄

```
_web_sources:436  run:448  _late_checks:558  _templates_with_form:622  _spec_routes:638  _routing_table_check:660  _count:694  ctx_account:701  _view_exists:707  _tpl:728  _all_templates:733  _screen_checks:738  _query_budget_check:945  _import_origin_check:1016  _import_step4_check:1051  _browser_origin_check:1075  _browser_confirm_check:1093  _browser_chunk_check:1118  _status_screen_checks:1159  _status_liveness_check:1197  _menu_label_check:1235  _listing_paging_checks:1252  _photo_checks:1288  _sian_css_checks:1324  _cell_of:1386  _link_tip_checks:1399  _origin_link_check:1413  _choose_check:1441  _order_filter_checks:1457  _checks_cfg:1500  _photo_size_by_screen_check:1509  _template_leak_check:1533  _em_dash_check:1559  _card_limits:1595  _cells_of:1612  _matches:1640  _place_cards:1659  _card_shape_checks:1781  _why_order_spec:1863  _why_order_check:1880  _width_policy:1915  _width_checks:1922  _screen_contradiction_check:1999  _chunk_check:2021  _csrf_reuse_check:2061  _origin_price_check:2090  _v1_parity_checks:2126  _media_blocks:2201  _responsive_checks:2222  _dead_links:2303  _null_link_check:2317  _sian_visual_check:2377  _cell_squeeze_check:2438  _static_version_check:2493  _axis_state_check:2511  _three_values_check:2549  _photo_size_check:2579  _render_metrics_checks:2602  _browser_scope_checks:2689  _import_opened_steps_check:2710  _import_resume_check:2738  _watch_invite_check:2757  _post_smoke_check:2801  _template_roots:2874  _loop_fields:2884  _context_supplied_check:2906  _first_item:2973  _has_field:2987  _table_counts:2993  _save_button_check:3000  _probe:3057  _scratch:3075
```

### `web/views.py` — 1,929줄

```
_rows_per_page:27  _cfg:31  _versions:36  page:55  listings:78  why:108  notready:139  dashboard:149  admin_home:167  _unclassified_split:179  _rows_of:207  _check_reports:217  admin_audit:240  admin_docs:253  _int_param:277  _manwon:316  _filter_chips:321  _order_menu:372  _carry:378  _order_label:388  ORDERS_LABELS_GET:392  _condition_sentence:396  _query_string:414  _page_links:427  _simple_paging:448  _paging:458  _filter_buttons:488  _filter:521  recommend:558  compare:586  market:601  _first_target:621  dealers:627  watch:647  run_view:661  login:673  _login_again:707  _open_session:722  logout:748  _watch_queries:765  watch_query_post:774  _int_or_none:804  watch_add_post:808  _watch_invite:864  watch_update_post:885  _now:909  _reason_gate:916  _gate:937  _first_flag:976  _all_hours:981  admin_run:1009  _target_rows:1075  admin_dict:1088  admin_status:1122  admin_collect:1137  _take_chunk:1194  _run_stamp:1226  _int_or_none:1237  admin_import:1242  admin_scoring:1314  admin_registry:1367  admin_query:1406  admin_requests:1428  _admin_extra:1490  _config_files:1505  _config_rows:1512  admin_config:1544  _typed:1595  admin_api:1611  _site_query:1661  admin_targets:1674  admin_tools:1772  join:1791  password:1822  admin_users:1837  _account_activity:1889
```

### `report/screens/build.py` — 1,630줄

```
site_badge:61  axis_heads:81  _labels:89  viewer_state:94  chip:104  _stamp:133  _bulk_axes:137  confirm_ratio:158  _bulk_changes:169  _total_points:196  photo_url:208  market_price:239  _days_between:256  _ceil_to:271  _bulk_market:286  _bulk_state:325  not_join_months:358  _left:381  _warranty_state:390  _axis_state:428  _row:487  _view_cfg:651  order_clause:686  _view_str:692  _listings_where:698  count_listings:753  view_listings:765  _soh_low:838  _view_int:847  _bucket:853  _high_km:860  _option_prices:869  recommend_funnel:881  _bulk_upside:898  view_recommend:913  recommend_reason:944  excluded_groups:987  view_why:1002  view_compare:1008  market_trims:1039  view_market:1061  _web_cfg:1094  _median:1108  _with_height:1113  _price_bins:1128  _group_prices:1149  _by_year:1167  _by_trim:1184  _other_targets:1202  count_dealers:1210  _dealer_targets:1216  _dealer_region:1236  view_dealers:1251  view_run:1287  _rank1_of:1293  view_dashboard:1301  _grade_counts:1395  _e_reasons:1402  _today_changes:1419  _step_rows:1444  _bulk_spark:1461  view_watch:1497  _pending_values:1547  _done_items:1556  view_notready:1582  _unmatched_rows:1617
```

### `tests/test_spec_ui.py` — 1,450줄

```
rec:33  spec_a:43  spec_b:121  spec_c:195  spec_d:239  spec_f:272  spec_g:298  spec_h:346  spec_j:379  spec_m:422  spec_e:490  spec_i:533  spec_k:639  spec_csrf:694  spec_l:721  spec_monkey:760  flow_s1:832  flow_s2:894  flow_s5:977  flow_s3:1090  flow_s4:1165  flow_s6:1236  guide_v132:1292  main:1384  _write:1428
```

### `collect/runner.py` — 1,317줄

```
CollectGroup:67  load_targets:91  collect_groups:104  facet_axes:132  aspect_names:153  check_facet_axes:157  interpret_failure:171  collect_check:200  FailStreak:267  _sleep:301  _log_request:307  _save_issues:318  make_executors:329  _group_of:831  _fuel_of:846  _badge_of:852  _pages_for:858  _dicts:872  _market_medians:908  _trim_ladders:937  _option_base:954  _site_grade_rules:984  _listing_config:994  _listing_values:1019  _option_money:1038  _owned_months:1057  _market_of:1069  make_score_executors:1079  make_validate_executor:1246  make_registry_executor:1288
```

### `tests/test_integration.py` — 1,212줄

```
rec:31  Client:41  text:96  links:101  start_server:105  seed_admin:149  m1:165  m2:253  m3:327  m4:631  s3:696  unit:749  gaps:778  flows:886  guide7:987  _account_id:1116  make_users:1123  main:1141  _write_table:1190
```

### `validate/v3_logic.py` — 1,134줄

```
_file_output_checks:244  _conflict_checks:297  _diagnosis_count_check:321  _hda_source_check:337  _sort_determinism:348  _warning_contract_checks:365  _list_observed_source_check:460  _facet_reconcile_check:490  _denominator_check:513  _core_axis_check:541  _rental_cross_check:559  _why_cheap_check:597  _source_before_value_check:638  _absolute_cut_check:665  _spec_files:691  _confirm_ratio_check:701  _spec_axis_check:751  _site_axis_checks:792  _rendered_why:840  _rendered_listings:850  _fill_gap_check:860  _points_sum_check:893  _market_gap_check:910  run:966  _shuffle_check:1077  _halt_dict_check:1102  _ensure_tmp:1131
```

### `report/screens/admin.py` — 1,000줄

```
AdminMenuItem:32  AdminHome:62  SaveGate:78  AuditTab:92  AuditView:100  DocView:107  menu_for:118  view_admin_home:130  _todos:155  _recent_runs:195  _recent_changes:226  save_gate:237  view_audit:245  view_docs:291  _doc_files:322  Todo:343  RunRow:357  ChangeRow:367  _cfg_rows:387  config_history:397  query_history:409  db_tables:423  api_snapshots:464  account_activity:475  make_target_key:493  target_choices:512  target_rows:531  parse_import_text:562  status_view:577  _catalog_state:651  _light_result:683  _live_window:723  _live_progress:732  run_progress:779  collect_state:829  received_vs_used:886  dict_state:907  import_state:934  job_log:971  validation_runs:985
```

### `tools/verify_axes.py` — 988줄

```
_spec_text:26  spec_tables:58  _num:81  pick:99  _flag:113  hand_market:121  _median_for:132  hand_mileage:152  _years:165  conn_now:174  lookup:179  hand_accident:203  hand_repair:213  hand_owner:221  hand_maker_warranty:229  _km_per_month:256  residual_spec:272  _json:298  hand_option_won:311  hand_depreciation:348  hand_frame:378  hand_outer:399  _leak_states:419  hand_leak:431  hand_lien:446  hand_not_join:456  hand_trim:486  hand_special:506  spec_section:516  spec_head_points:524  lookup_label:531  hand_integrity:539  hand_special_points:565  _taste_points:574  _has_option:585  hand_color:620  hand_usage:644  hand_site_grade:668  hand_inspection_src:688  hand_hud:701  hand_sunroof:710  hand_picked:719  _has_table:732  _option_prices:738  hand_options:756  survey:794  main:857
```

### `store/core.py` — 937줄

```
resolve_listing_id:38  resolve_dealer_id:56  serialize_container:72  record_change:83  split_pii:105  flush_dealer_pii:152  _record_dropped:164  classify_invariant_change:199  _lookback:239  _source_history:253  _schema_change_min:279  _current:293  _today:299  upsert_core:303  mark_gone:388  load_snapshot:405  build_identities:496  resolve_vehicle_id:522  merge_conflict:554  upsert_vehicle:565  upsert_dealer:586  upsert_child:613  _flag:634  _not_join_months:648  state_counts:673  current_versions:703  diagnosis_of:733  target_counts:746  top_target:753  vehicle_of:758  collect_scale:765  our_fault:785  catalog_coverage:794  _walk:838  _sample_bodies:854  observed:867  known_leaves:883  has_unclassified:898  classify_unclassified:905
```

### `store/adminops.py` — 931줄

```
QueryLog:51  QueryResult:64  ApiSnapshot:73  DevRequest:84  RecalcJob:99  ScoringPreview:110  ImportPreview:122  ImportResult:139  preview_import:148  import_listings:174  _import_facet:240  BrowserCatch:275  save_browser_catch:283  mark_step_imported:333  pending_enums:364  pending_axis_summary:392  apply_dict_decision:413  _strip_sql:457  sql_reject_reason:464  _opened_tables:495  run_query:503  fetch_api:542  create_dev_request:576  update_dev_status:598  export_dev_requests:612  enqueue_recalc:642  enqueue_after_list_save:668  job_progress:693  db_progress:707  preview_scoring:717  _pt:760  registry_rows:764  registry_counts:775  write_dev_requests:781  dev_request_rows:801  save_api_snapshot:819  get_api_snapshot:842  path_table:861  halt_job:897
```

### `validate/v2_load.py` — 872줄

```
DayGapReport:151  GapCause:164  run:170  _surrogate_key_checks:304  _not_null_check:387  _chained_subscript_check:404  _Boom:452  _salvage_check:460  _table_exists:501  _exception_shape_checks:507  _schema_sync_check:573  _pii_access_check:610  gap_alerts:647  diff_prev_day:663  explain_gap:685  _pii_column_check:717  _secret_key_check:735  _parser_common_fields_check:773  _null_target_not_judged_check:824  _null_target_visible_check:849
```

### `tools/check_src.py` — 814줄

```
_spec_files:33  _read_spec:51  say:62  py_files:76  chapter_of:116  _declared_chapters:126  split_done:146  _illustration:165  _retired_config_keys:229  _git:652
```

### `tests/test_score.py` — 782줄

```
check:36  fx:42  snap:46  ctx:66  full_verdict:87  test_denominator:100  test_components_form:144  test_grade:190  test_order_independent:252  panels_of:275  test_history_real:280  test_rental_real:315  test_insurance:357  test_safety_real:382  test_spec_gate:425  test_price_real:485  test_color:544  test_price_pending:564  test_absolute_real:583  test_null_safe:623  test_empty_array_meaning:640  test_peer_group:665  test_damage_by_status:707  test_repair_cost_ratio:733  test_hda_gate:742
```

### `tests/test_run.py` — 754줄

```
check:36  StubEncar:92  Clock:236  setup:241  test_envelope:279  test_last_page_exact:307  test_facet:314  test_facet_missing_axis:328  test_dict_step:337  test_all_groups:359  test_parse_pipeline:370  test_score_pipeline:474  test_validate:534  test_registry_gate:577  test_target_scope:634  test_catalog_key:666  test_wrapper_args:684  test_unclassified_listing:721
```

### `collect/pipeline.py` — 689줄

```
envelope_scope:41  Reprocess:91  reprocess_plan:110  should_refetch:127  expected_for:139  step_report:173  halt_if:189  precheck:222  resume_point:276  config_hash:296  build_run_context_fields:302  stale_rows:311  save_step_report:326  run_step:350  _execute:388  completed_steps:405  run_pipeline:417  print_progress:453  silent_progress:472  from_step_for:486  web_reasons:492  check_recalc_origin:497  plan_recalc:509  _current:526  run_recalc:532  Defect:546  DefectReport:557  diagnose:578  _DiagCtx:602  _collect_defects:612  format_defects:666
```

### `validate/v1_collect.py` — 670줄

```
run:141  _endpoint_order_check:274  _empty_db_check:286  _run_scope_check:313  _ctx_started:338  _has_run_id:346  _expected_scope_check:351  _diagnosis_scope_check:372  _diagnosis_none_count:410  _query_key_check:433  _entrypoint_parity_check:458  _enclosing_def:487  _run_id_filled_check:496  _catalog_key_check:516  _whole_probe:538  _whole_body_check:549  _catalog_checks:580  _unparsed_envelope_check:627  _ensure_tmp:667
```

### `validate/v4_mapping.py` — 624줄

```
_paths:126  _layer_of:173  _unclassified_split:178  _layer_checks:216  _name_collision_check:310  _key:344  run:350  _mapping_coverage_checks:485  _our_columns:515  _listing_value_scope_check:541  _dict_filled_check:561  _kind_check:572  propose_fix:586  _option_code_check:601  _is_sentence:618
```

### `parse/encar/mapping.py` — 621줄

```
_get:30  _json:42  _won:53  _ym:73  _date10:83  _int:99  _bool:105  unpack_envelope:116  parse_list_item:124  parse_detail:171  parse_inspection:247  parse_record:291  _sample_chars:345  safe_field:359  parse_with_issues:381  _salvage:399  _parses:442  dig:449  as_list:472  _diag_comment:500  parse_diagnosis:507  parse_diagnosis_items:539  _text:547  parse_record_summary:557  parse_platform_check:583  parse_inspection_summary:590  parse_ev_battery:595  parse_sellingpoint:615
```

### `store/watch.py` — 612줄

```
AlertConfig:55  WatchItem:68  TrackPoint:83  TrackEvent:98  WatchEvent:112  classify_duplicates:124  sync_duplicates:164  deduped_count:187  watch_add:197  assert_owner:236  watch_update:251  watch_close:271  track_snapshot:283  track_points:312  classify_cause:321  detect_events:333  message:391  notify:419  add_watch_query:489  run_watch_queries:524  watch_query_rows:580  close_watch_query:594
```

### `store/admin.py` — 609줄

```
_admin_cfg:46  ConfigChange:68  running_job:86  hash_secret:96  _split:104  create_account:109  account_count:143  needs_bootstrap:147  _recent_failures:155  _log_attempt:174  authenticate:183  open_session:216  session_account:236  change_secret:253  revoke_sessions:277  _walk:288  get_path:312  set_path:317  _atomic_write:324  apply_config:334  _validate_blob:398  revert_config:411  history:435  classify_field:459  account_rows:512  admin_count:523  set_role:530  set_disabled:547  add_config_key:567
```

### `report/render.py` — 575줄

```
_labels:29  _stamp:34  _curve_points:49  _encar_url:92  _why_cheap_of:101  _scoring:142  _penalty_rows:150  _site_badge:161  render_listing:168  _option_rows:265  _fetch_views:316  _strengths:331  _weaknesses:338  _pending_best:345  _cost_rows:377  _known_issues:398  _diagnosis_view:416  render_target:427  render_run:508  render_halt:550  _j:568
```

### `tests/test_admin_flow.py` — 566줄

```
check:32  _env:38  _cfg:55  _post:60  _get:65  flow_config:71  flow_scoring:107  _rescore:163  _sum:224  _dist:231  flow_targets:238  flow_registry:273  flow_run:313  flow_query:346  flow_api:372  flow_tools:409  flow_users:431  flow_requests:476  flow_permission:518  main:531
```

### `validate/v10_admin.py` — 541줄

```
_sources:142  _admin_guard_checks:163  _sql_strings:208  run:220  _session_checks:326  _pii_query_check:397  _scratch:444  _dict_reason_check:459  _dict_source_shown_check:475  _queue_consumer_check:493  _queue_stale_shown_check:522  _ensure_tmp:538
```

### `tests/test_admin.py` — 537줄

```
_spec_menu_paths:31  check:46  setup:52  test_bootstrap:64  test_auth:94  test_apply_config:136  test_value_validation:174  test_revert:194  test_no_direct_edit:220  test_classify_field:248  test_run_query:322  test_dev_request:358  test_recalc_and_lock:388  test_admin_screens:422  test_v10:501
```

### `tests/test_web.py` — 497줄

```
check:21  test_routes:28  test_template:77  test_no_logic_in_template:118  test_static_escape:133  test_session_cookie:145  test_error_page:163  test_layout:190  test_filters:219  test_empty_state:242  test_menu_by_role:269  test_guard_and_csrf:286  _call:328  test_screens_render:345  test_sketch_match:428  test_account_policy:443
```

### `tools/check_spec.py` — 475줄

```
_read_spec:10  _refs_source:73  _spec_files:284  _guide_files:368  _sections:373
```

### `contracts.py` — 450줄

```
Response:24  Clock:34  Fetcher:39  Rng:44  Request:52  EndpointSpec:60  FetchResult:71  TargetSpec:84  ListingSnapshot:135  AxisResult:214  Account:233  require_role:250  RunContext:267  StepReport:287  ResumePoint:311  clean_vin:332  total_of:343  RegressionReport:356  json_paths:367  shape_ok:415  shape_violations:448
```

### `report/screens/views.py` — 440줄

```
AxisChip:30  ListingRow:52  ListingFilter:169  WatchRow:195  TargetStat:213  RelaxRow:222  MarketRow:229  ChangeRow:241  AttentionItem:251  ViewerState:259  DashboardView:273  CompareView:297  MarketView:308  DealerRow:321  NotReadyView:342  TodayChange:360  StepRow:372  _min_sample:384  PendingValue:402  Bucket:415  ExcludedGroup:435
```

### `store/dictionary.py` — 440줄

```
CodeEntry:31  AxisPolicy:57  policy:97  scope_key:105  seed_fixed_enums:130  upsert_enum:166  _handle_conflict:216  upsert_option3:237  retire_unseen:273  resolve_code:288  installed_option_names:326  normalize_enum:344  assert_no_unknown:360  bump_dict_version:403  list_pending:413  confirm_enum:421
```

### `web/app.py` — 426줄

```
menu_items:22  _tip:89  _label:94  empty_state:105  _list_stale:146  static_version:172  build_page:200  check_post:221  redirect:240  take_flashes:251  _display_now:264  make_app:290  _Denied:402  build_context:410  _title_of:425
```

### `run.py` — 404줄

```
load:51  make_context:56  _filter_targets:70  _steps_from:89  cmd_collect:103  _grade_summary:171  cmd_admin_create:186  _collect_urls:203  _page_url:240  cmd_web:259  make_worker_ctx:290  make_worker_executors:296  cmd_delegate:326  _api_fetch:337  cmd_setup:347
```

### `tests/test_pipeline.py` — 382줄

```
check:37  db:43  test_expected:49  test_halt:61  test_reprocess:82  test_refetch:107  test_precheck:115  test_resume_and_version:161  test_run_pipeline:189  test_recalc:224  test_pii_orphan:259  test_exception_becomes_halt:292  test_fixed_enum_bootstrap:313  test_envelope_scope:343
```

### `tests/test_collect.py` — 368줄

```
check:34  R:40  test_verify_shape:45  _Stub:80  _Clock:88  test_fetch_status:93  test_interpret_failure:106  test_facet_axes:118  test_collect_groups:146  test_build_q:158  test_collect_check:208  test_save_raw:223  test_fail_streak:252  test_all_fail_sample:294  test_diagnosis_scope:338
```

### `tools/sync_registry.py` — 345줄

```
FieldUsage:31  RegistrySyncReport:48  facet_path:66  scan_paths:74  shape_ok:79  _walk_values:92  collect_values:106  collect_paths:130  _seed_for:153  sync_registry:164  suggest_usage:246  write_suggested:258  halt_report:285  list_by_usage:308  assert_registered:315
```

### `report/views.py` — 322줄

```
VersionStamp:18  ReportMeta:30  AxisView:40  FinanceView:52  DiagnosisView:74  FetchView:86  CostRow:100  ScoreView:109  CollectSummary:170  ClassifySummary:177  PriceSummary:184  AxisStat:193  CoefficientChange:203  DictChangeSummary:213  TargetReport:221  RunStep:233  RunReport:248  HaltReport:259  FixAction:276  NotifyResult:286  ExportResult:299  display_value:308  display_points:318
```

### `tools/render_screens.py` — 321줄

```
_shot_widths:32  _tmp_root:57  main:81  shot_paths:162  _localize_images:187  shoot:224
```

### `tools/build_dict.py` — 298줄

```
DictBuildReport:63  extract_distinct:78  _facet_values:106  _walk_path:122  load_fixed_enums:149  build_dict:157  _mark_facet_substituted:208  build_catalog_dict:232  build_late_dict:270
```

### `adapters/encar.py` — 285줄

```
escape_value:126  unescape_value:136  _nest:141  load_site_config:152  EncarAdapter:171
```

### `store/raw.py` — 285줄

```
batch:36  commit:62  open_db:68  _safe_headers:85  save_raw:92  save_import_raw:141  save_browser_raw:174  save_browser_facet:209  save_import_facet:235  save_facet:265
```

### `tests/test_fixtures.py` — 284줄

```
check:33  fx:39  test_inspection:53  test_frame_vs_outer:84  test_record:123  test_detail:152  test_classify_real:172  test_catalog:207  test_diagnosis:219
```

### `web/template.py` — 284줄

```
f_won:48  f_km:64  f_pct:68  f_date:72  f_num:83  f_gradecls:90  f_count:96  f_signcls:104  f_signwon:114  _index_key:141  _step:156  _lookup:168  _truthy:177  render_str:181  render:269
```

### `tests/test_dict.py` — 280줄

```
check:39  db:45  test_scope_key:51  test_count_zero:73  test_axis_policy:97  test_conflict:140  test_catalog:172  test_status_version:196  test_classify:213  test_review:242
```

### `tests/test_crosssite.py` — 275줄

```
check:34  db:40  add:45  test_vin:63  test_vin_parse:107  test_cross_site:129  test_regression:168  test_readiness:200  v9_04_site_isolation:222
```

### `tests/test_screens.py` — 274줄

```
check:42  _pipeline:48  test_chip:60  test_listings:83  test_compare:131  test_dashboard_notready:148  test_static_rules:188  test_account:220
```

### `report/exports/export.py` — 271줄

```
filename:26  _stamp_lines:32  listing_md:38  listing_csv:78  halt_md:95  target_md:116  run_md:138  _asdict:188  export:196  output_path:235  write_export:243
```

### `tests/test_watch.py` — 259줄

```
check:30  db:36  add:41  watch:64  test_same_dealer:78  test_cross_dealer:97  test_relist:112  tp:124  test_cause:133  _two_runs:145  test_snapshot:162  test_events:177  test_cause_gate:198  test_message:212
```

### `tools/menu.py` — 254줄

```
_fix_console:28  run:44  cmd_status:52  cmd_setup:56  cmd_dry:74  cmd_collect:81  cmd_facet:118  cmd_dict:123  cmd_screens:128  cmd_migrate:133  cmd_checkall:138  cmd_requests:143  cmd_check_spec:150  cmd_check_src:154  cmd_test:159  main:192
```

### `tests/test_endtoend.py` — 247줄

```
check:31  _run:37  flow_pipeline:52  flow_validation:105  flow_config_effect:119  flow_report:164  main:230
```

### `tests/test_registry.py` — 245줄

```
check:33  fx:39  db:43  put_raw:48  test_paths:57  test_contamination:69  test_seed:95  test_ghost:140  test_v4_06:168  test_seed_reapply:180  test_unclassified_severity:202
```

### `tests/test_report.py` — 244줄

```
check:33  test_finance:40  test_display:92  _pipeline:108  test_layers:119  test_halt_layer:155  test_export:197
```

### `validate/v5_value.py` — 242줄

```
run:60  _grade_ratio_checks:151  _denominator_suite:193
```

### `tests/test_store.py` — 233줄

```
check:39  seed:45  base:51  db:69  test_schema:75  test_key:108  test_null_three:119  test_change_history:126  test_invariant_violation:147  test_snapshot:165  test_dictionary:184
```

### `tests/test_invariants.py` — 232줄

```
check:35  inv1_order_independent:42  inv1_shuffle_100:72  inv2_banned:95  inv5_points:113  put_contract:126  excluded_contract:143  inv3_source_not_null:169  inv4_label_shape:188  inv6_no_unclassified:204
```

### `tools/check_screens.py` — 230줄

```
_pairs:23  say:70  _text:79  check_pairs:86  check_phrases:99  _heads:124  check_sections:143  check_nav:165  check_render:181  main:213
```

### `store/crosssite.py` — 225줄

```
CrossSiteMatch:31  ReadinessReport:41  active_sites:51  match_cross_site:56  rebuild_core_vehicle:92  regression_check:111  snapshot_baseline:142  readiness:166  load_sites:205  site_addition_regression:210
```

### `tools/build_index.py` — 212줄

```
_py_files:35  _checks_in_code:50  _checks_in_docs:82  build_checks:115  _outline:156  build_source:167  main:199
```

### `tools/light_check.py` — 208줄

```
_cfg:39  _run:44  collecting:50  screen_counts:71  db_counts:97  measure:111  changed:128  _worse:144  main:148
```

### `validate/base.py` — 207줄

```
_cfg:24  Check:55  CheckResult:88  _short:113  result:126  not_applicable:135  save_results:140  gate:157  run_phase:166  canon_files:188  canon_text:201
```

### `analyze/axis/state.py` — 203줄

```
_panels:37  _rank_worst:41  _accident:53  _frame:66  _outer:81  _repair:98  _special:109  leak_state:121  _leak:143  _consumable:153  _integrity:169  analyze_state:195
```

