# 소스 색인

**`python3.11 tools/build_index.py` 가 만든다. 손으로 고치지 않는다.**

파일 121개 · 총 37,246줄

| 파일 | 줄 | 무엇 |
|---|--:|---|
| `validate/v11_web.py` | 2,455 | V11 표현 계층 검증 (14장 STEP 153). |
| `web/views.py` | 1,843 | 화면 어댑터 (14장 STEP 142 · 152). |
| `report/screens/build.py` | 1,548 | 화면 데이터 생성. |
| `tests/test_spec_ui.py` | 1,442 | 규격 기준 통합 테스트 (통합테스트_시나리오_규격기준.md). |
| `collect/runner.py` | 1,232 | 수집 실행 규칙. |
| `tests/test_integration.py` | 1,212 | 통합 테스트 — 실제 HTTP 로 전 화면 (통합테스트_시나리오.md). |
| `validate/v3_logic.py` | 930 | V3 로직 검증 — 판정이 작동하는가 · 변별력이 있는가. |
| `report/screens/admin.py` | 927 | 관리자 화면 — 표현 계층 (13장 STEP 138 · 138a). |
| `store/adminops.py` | 904 | 관리자 서버 계층 — 실행 지시 · 쿼리 · API 조회 · 개발 요청 · 미리보기. |
| `validate/v2_load.py` | 872 | V2 적재 검증 — 옮겨졌는가 · 전일 대비 변동이 타당한가. |
| `tests/test_score.py` | 783 | 7장 판정·채점 시험. |
| `tests/test_run.py` | 749 | S0~S3 종단 시험 (모의 응답). |
| `tools/check_src.py` | 742 | CarWatch v2 — 지시서 ↔ 소스 대조 검증기. |
| `collect/pipeline.py` | 689 | 실행 순서 · 중단 · 재처리 · 재개. |
| `store/watch.py` | 612 | 후보 추적 (11장). |
| `store/admin.py` | 609 | 관리자 — 계정 · 권한 · config 변경 (13장 앞부분). |
| `parse/encar/mapping.py` | 601 | 엔카 원문 → CORE 필드 (L3). |
| `validate/v1_collect.py` | 589 | V1 수집 검증 — 다 받았는가 · 라벨이 맞는가. |
| `store/core.py` | 586 | CORE 저장소 (L4).  사이트 무관 공통 스키마. |
| `validate/v4_mapping.py` | 573 | V4 매핑 검증 — 이름이 아니라 값으로 검증한다. |
| `tests/test_admin_flow.py` | 555 | 관리 화면 동작 시험 (13장 · 14장). |
| `tests/test_admin.py` | 537 | 13장 앞부분 시험 — 계정 · 권한 · config 변경. |
| `validate/v10_admin.py` | 527 | V10 관리자 검증. |
| `tests/test_web.py` | 493 | 14장 표현 계층 시험 — 템플릿 · 라우팅. |
| `report/render.py` | 491 | 리포트 생성 (L9). |
| `store/dictionary.py` | 440 | 사전 저장소 (L5).  RAW 에서 생성한다. |
| `contracts.py` | 433 | 계층 간 계약 — Protocol · DTO. |
| `report/screens/views.py` | 424 | 화면 전용 DTO. |
| `run.py` | 404 | CarWatch v2 진입점. |
| `web/app.py` | 390 | 화면 조립 (14장 STEP 144 · 147 · 149). |
| `tests/test_pipeline.py` | 382 | 5장 수집 순서 시험. |
| `tests/test_collect.py` | 368 | 2장 수집 시험. |
| `tools/check_spec.py` | 354 | CarWatch v2 지시서 자체 점검 — 7종 |
| `tools/sync_registry.py` | 345 | RAW 경로 전수 → meta_field_usage. |
| `report/views.py` | 307 | 리포트 DTO (L9). |
| `tools/build_dict.py` | 298 | RAW → 사전 생성. |
| `adapters/encar.py` | 285 | 엔카 어댑터 — URL · 헤더 · 쿼리 조립. |
| `tests/test_fixtures.py` | 284 | 실물 표본 시험 — v1 원문 12건. |
| `tests/test_dict.py` | 280 | 4장 키·코드·사전 시험. |
| `store/raw.py` | 279 | RAW 저장소 (L2).  원문 무손실.  삭제 금지. |
| `web/template.py` | 278 | 최소 템플릿 엔진 (14장 STEP 143). |
| `tests/test_crosssite.py` | 275 | 12장 다중 사이트 시험. |
| `tests/test_screens.py` | 274 | 10장 화면 시험. |
| `report/exports/export.py` | 271 | 내보내기. |
| `tests/test_watch.py` | 259 | 11장 후보 추적 시험. |
| `tools/render_screens.py` | 255 | 전 화면을 실제로 렌더해 `outputs/render/` 에 남긴다. |
| `tools/menu.py` | 254 | 실행 메뉴. |
| `tests/test_endtoend.py` | 247 | 종단 시험 — 수집부터 리포트까지 (5장 STEP 47 · 49). |
| `tests/test_registry.py` | 245 | 8장 등록부 시험. |
| `validate/v5_value.py` | 242 | V5 수치 검증 — 기준값이 맞는가 · 보정이 타당한가. |
| `tests/test_report.py` | 241 | 9장 리포트 시험. |
| `tests/test_store.py` | 233 | 3장 테이블 시험. |
| `tests/test_invariants.py` | 232 | 불변식 시험. |
| `tools/check_screens.py` | 230 | 화면 ↔ 시안 대조 (10장 · 14장). |
| `store/crosssite.py` | 225 | 다중 사이트 확장 (12장). |
| `tools/build_index.py` | 212 | 검사 색인 · 소스 색인을 만든다 (규칙 11). |
| `web/server.py` | 199 | HTTP 서버 (14장 STEP 141 · 150). |
| `validate/v7_watch.py` | 194 | V7 관심·추적 검증. |
| `parse/importer.py` | 182 | 반입 입력 해석 (13장 STEP 136a · 136b). |
| `web/context.py` | 181 | 화면 문맥과 오류 (14장 STEP 144 · 148). |
| `validate/base.py` | 180 | 검증 계약. |
| `tests/seed.py` | 178 | 시험용 씨앗 DB — 운영 DB 를 복사하지 않는다. |
| `web/session.py` | 175 | 세션 · CSRF · 정적 파일 (14장 STEP 145~147). |
| `tools/migrate.py` | 174 | 스키마 이행 — 기존 DB 를 현재 DDL 에 맞춘다. |
| `analyze/axis/history.py` | 156 | 이력 55점 — 사고 20 · 보험 15 · 렌트 20. |
| `store/pii.py` | 152 | 개인정보 분리 (L4). |
| `analyze/axis/state.py` | 145 | ② 상태 180점 — 사고 70 · 골격 40 · 수리비 30 · 용도 25 · 보증 15. |
| `score/adjust.py` | 145 | 배점 조정 — 비율 재배분과 정수 보정. |
| `parse/classify.py` | 136 | 분류 2단 — target_key 판정. |
| `collect/worker.py` | 132 | 큐 소비기 (13장 STEP 132a · 개정 261). |
| `web/routes.py` | 129 | 라우팅 표 (14장 STEP 142). |
| `analyze/axis/spec.py` | 123 | 사양 90점 — HUD 20 · HDA 20 · 선루프 20 · SVM 10 · SCC 10 · 후측방 5 · 틴팅 5. |
| `collect/fetcher.py` | 121 | 원문 획득 · 형식 검증. |
| `tools/run_tests.py` | 121 | 시험 전체 실행. |
| `tools/classify_fields.py` | 118 | 등록부 분류 초안 — 파서가 쓰는 경로를 근거로 자동 분류한다. |
| `errors.py` | 115 | 도메인 예외 5종. |
| `analyze/axis/site.py` | 114 | ⑤ 사이트 보증 50점 — 우수등급 30 · 점검 출처 12 · 플랫폼 보증 잔여 8. |
| `tools/report_cli.py` | 109 | 리포트 재생성 (9장 STEP 90 · 91a · B-6). |
| `score/scorer.py` | 108 | 채점 · 분모 (L7). |
| `tools/check_all.py` | 107 | 실측 DB 회귀 — V1~V5 · V10 전건을 한 번에 돌린다. |
| `tools/repair_facet_chunks.py` | 107 | 낱개로 저장된 facet 조각을 이어붙인다 (개정 307 사고 복구). |
| `analyze/axes.py` | 103 | 축 판정 계약. |
| `analyze/axis/value.py` | 103 | ① 값 250점 — 시세 대비 120 · 신차가 대비 감가 70 · 주행 대비 60. |
| `store/tools.py` | 97 | 관리 도구 (13장 STEP 135). |
| `report/finance.py` | 95 | 금융 — 점수가 아니라 비용이다. |
| `analyze/axis/taste.py` | 94 | ④ 취향 50점 — HUD 15 · 선루프 10 · 색상 10 · 지정 옵션 15. |
| `analyze/verdict.py` | 94 | 판정 엔진 — 순서 무관 put(). |
| `tools/export_cli.py` | 93 | 데이터 내보내기 (9장 STEP 91a · B-6). |
| `tools/setup_check.py` | 92 | 착수 점검 — 실행 전에 무엇이 준비됐는지 한 번에 본다. |
| `analyze/axis/price.py` | 90 | 가격 200점. |
| `analyze/absolute.py` | 88 | E등급 절대조건 10종. |
| `analyze/peer.py` | 80 | 유사군 — 「이런 차가 보통 얼마인가」 (7장 STEP 82e). |
| `store/chunk.py` | 77 | 조각 전송 — 바이트를 나누고 서버가 이어붙인다 (개정 307). |
| `report/why_cheap.py` | 76 | 「왜 싼가」 — 싼 이유를 순서대로 찾아 낸다 (개정 299 · V3-52). |
| `tools/inspect_dict.py` | 75 | 사전 검토 — pending 값과 원문 표본을 본다. |
| `tools/inspect_facet.py` | 74 | facet 원문에 실제로 어떤 축이 왔는지 본다. |
| `analyze/trust.py` | 70 | 플랫폼 신뢰도 — 점검 출처 · 엔카진단 · 엔카보증 (개정 300). |
| `score/grade.py` | 70 | 등급 (L7). |
| `analyze/axis/trim.py` | 64 | ③ 사양 75점 — 트림 등급 45 · 옵션 합 30. |
| `analyze/axis/warranty.py` | 56 | 보증 100점 — 일반 50 + 파워트레인 50. |
| `tools/inspect_requests.py` | 52 | 요청 기록을 본다 — 무엇을 던졌고 무엇이 돌아왔는가. |
| `analyze/axis/safety.py` | 44 | 안전 40점 — 진단 20 + 보증상품 20. |
| `adapters/base.py` | 36 | 사이트 어댑터 인터페이스. |
| `report/peer.py` | 35 | 유사군 조회 (7장 STEP 82e). |
| `analyze/axis/_util.py` | 33 | 축 공용 도우미. |
| `analyze/axis/color.py` | 33 | 색상 40점. |
| `analyze/axis/mileage.py` | 31 | 주행거리 30점. |
| `analyze/engine.py` | 30 | 판정 실행 (L6).  축 함수를 순서 무관하게 호출한다. |
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

## 큰 파일 — 무엇이 어디에 (200줄 이상 56개)

### `validate/v11_web.py` — 2,455줄

```
_web_sources:375  run:387  _late_checks:497  _templates_with_form:561  _spec_routes:577  _routing_table_check:599  _count:633  ctx_account:640  _view_exists:646  _tpl:667  _all_templates:672  _screen_checks:677  _query_budget_check:884  _import_origin_check:955  _import_step4_check:990  _browser_origin_check:1014  _browser_confirm_check:1032  _browser_chunk_check:1057  _status_screen_checks:1093  _status_liveness_check:1131  _menu_label_check:1169  _listing_paging_checks:1186  _photo_checks:1222  _sian_css_checks:1258  _cell_of:1320  _link_tip_checks:1333  _origin_link_check:1347  _choose_check:1375  _order_filter_checks:1391  _checks_cfg:1434  _chunk_check:1443  _csrf_reuse_check:1483  _origin_price_check:1512  _v1_parity_checks:1548  _media_blocks:1605  _responsive_checks:1621  _dead_links:1677  _null_link_check:1691  _sian_visual_check:1751  _cell_squeeze_check:1812  _static_version_check:1867  _axis_state_check:1885  _three_values_check:1921  _photo_size_check:1947  _render_metrics_checks:1970  _browser_scope_checks:2057  _import_opened_steps_check:2078  _import_resume_check:2106  _watch_invite_check:2125  _post_smoke_check:2169  _template_roots:2242  _loop_fields:2252  _context_supplied_check:2274  _first_item:2341  _has_field:2355  _table_counts:2361  _save_button_check:2368  _probe:2425  _scratch:2443
```

### `web/views.py` — 1,843줄

```
_rows_per_page:27  _cfg:31  _versions:36  page:55  listings:78  why:108  notready:139  dashboard:149  admin_home:167  admin_audit:176  admin_docs:189  _int_param:213  _manwon:252  _filter_chips:257  _order_menu:308  _carry:314  _order_label:324  ORDERS_LABELS_GET:328  _condition_sentence:332  _query_string:350  _page_links:363  _simple_paging:384  _paging:394  _filter_buttons:424  _filter:457  recommend:494  compare:520  market:535  _first_target:555  dealers:561  watch:581  run_view:595  login:607  _login_again:641  _open_session:656  logout:682  _watch_queries:699  watch_query_post:708  _int_or_none:738  watch_add_post:742  _watch_invite:798  watch_update_post:819  _now:843  _reason_gate:850  _gate:871  _first_flag:910  _all_hours:915  admin_run:942  _target_rows:1008  admin_dict:1021  admin_status:1055  admin_collect:1070  _take_chunk:1116  _run_stamp:1143  _int_or_none:1154  admin_import:1159  admin_scoring:1231  admin_registry:1284  admin_query:1320  admin_requests:1342  _admin_extra:1404  _config_files:1419  _config_rows:1426  admin_config:1458  _typed:1509  admin_api:1525  _site_query:1575  admin_targets:1588  admin_tools:1686  join:1705  password:1736  admin_users:1751  _account_activity:1803
```

### `report/screens/build.py` — 1,548줄

```
axis_heads:64  _labels:72  viewer_state:77  chip:87  _stamp:116  _bulk_axes:120  confirm_ratio:141  _bulk_changes:152  _total_points:179  photo_url:191  market_price:222  _days_between:239  _ceil_to:254  _bulk_market:268  _bulk_state:307  not_join_months:337  _left:360  _warranty_state:369  _axis_state:406  _row:465  _view_cfg:600  order_clause:635  _view_str:641  _listings_where:647  count_listings:702  view_listings:714  _high_km:781  _option_prices:790  recommend_funnel:802  _bulk_upside:819  view_recommend:834  recommend_reason:865  excluded_groups:908  view_why:923  view_compare:929  market_trims:960  view_market:979  _web_cfg:1012  _median:1026  _with_height:1031  _price_bins:1046  _group_prices:1067  _by_year:1085  _by_trim:1102  _other_targets:1120  count_dealers:1128  _dealer_targets:1134  _dealer_region:1154  view_dealers:1169  view_run:1205  _rank1_of:1211  view_dashboard:1219  _grade_counts:1313  _e_reasons:1320  _today_changes:1337  _step_rows:1362  _bulk_spark:1379  view_watch:1415  _pending_values:1465  _done_items:1474  view_notready:1500  _unmatched_rows:1535
```

### `tests/test_spec_ui.py` — 1,442줄

```
rec:33  spec_a:43  spec_b:117  spec_c:191  spec_d:231  spec_f:264  spec_g:290  spec_h:338  spec_j:371  spec_m:414  spec_e:482  spec_i:525  spec_k:631  spec_csrf:686  spec_l:713  spec_monkey:752  flow_s1:824  flow_s2:886  flow_s5:969  flow_s3:1082  flow_s4:1157  flow_s6:1228  guide_v132:1284  main:1376  _write:1420
```

### `collect/runner.py` — 1,232줄

```
CollectGroup:67  load_targets:91  collect_groups:104  facet_axes:132  aspect_names:153  check_facet_axes:157  interpret_failure:171  collect_check:200  FailStreak:267  _sleep:301  _log_request:307  _save_issues:318  make_executors:329  _group_of:820  _fuel_of:835  _badge_of:841  _pages_for:847  _dicts:861  _market_medians:897  _trim_ladders:926  _site_grade_rules:943  _listing_config:953  _listing_values:978  _market_of:997  make_score_executors:1007  make_validate_executor:1161  make_registry_executor:1203
```

### `tests/test_integration.py` — 1,212줄

```
rec:31  Client:41  text:96  links:101  start_server:105  seed_admin:149  m1:165  m2:253  m3:327  m4:631  s3:696  unit:749  gaps:778  flows:886  guide7:987  _account_id:1116  make_users:1123  main:1141  _write_table:1190
```

### `validate/v3_logic.py` — 930줄

```
_file_output_checks:216  _conflict_checks:269  _diagnosis_count_check:293  _hda_source_check:309  _sort_determinism:320  _warning_contract_checks:337  _list_observed_source_check:432  _facet_reconcile_check:462  _denominator_check:485  _core_axis_check:513  _rental_cross_check:531  _why_cheap_check:569  _site_axis_checks:608  _rendered_listings:656  _fill_gap_check:666  _points_sum_check:699  _market_gap_check:716  run:772  _shuffle_check:879  _halt_dict_check:904
```

### `report/screens/admin.py` — 927줄

```
AdminMenuItem:32  AdminHome:62  SaveGate:78  AuditTab:92  AuditView:100  DocView:107  menu_for:118  view_admin_home:130  _todos:155  _recent_runs:195  _recent_changes:226  save_gate:237  view_audit:245  view_docs:291  _doc_files:322  Todo:343  RunRow:357  ChangeRow:367  _cfg_rows:387  config_history:397  query_history:409  db_tables:423  api_snapshots:464  account_activity:475  make_target_key:493  target_choices:512  target_rows:531  parse_import_text:562  status_view:577  _live_window:650  _live_progress:659  run_progress:706  collect_state:756  received_vs_used:813  dict_state:834  import_state:861  job_log:898  validation_runs:912
```

### `store/adminops.py` — 904줄

```
QueryLog:51  QueryResult:64  ApiSnapshot:73  DevRequest:84  RecalcJob:99  ScoringPreview:110  ImportPreview:122  ImportResult:139  preview_import:148  import_listings:174  _import_facet:240  BrowserCatch:275  save_browser_catch:283  mark_step_imported:330  pending_enums:361  pending_axis_summary:389  apply_dict_decision:410  _strip_sql:454  sql_reject_reason:461  _opened_tables:492  run_query:500  fetch_api:539  create_dev_request:573  update_dev_status:595  export_dev_requests:609  enqueue_recalc:639  job_progress:666  db_progress:680  preview_scoring:690  _pt:733  registry_rows:737  registry_counts:748  write_dev_requests:754  dev_request_rows:774  save_api_snapshot:792  get_api_snapshot:815  path_table:834  halt_job:870
```

### `validate/v2_load.py` — 872줄

```
DayGapReport:151  GapCause:164  run:170  _surrogate_key_checks:304  _not_null_check:387  _chained_subscript_check:404  _Boom:452  _salvage_check:460  _table_exists:501  _exception_shape_checks:507  _schema_sync_check:573  _pii_access_check:610  gap_alerts:647  diff_prev_day:663  explain_gap:685  _pii_column_check:717  _secret_key_check:735  _parser_common_fields_check:773  _null_target_not_judged_check:824  _null_target_visible_check:849
```

### `tests/test_score.py` — 783줄

```
check:36  fx:42  snap:46  ctx:62  full_verdict:83  test_denominator:96  test_components_form:140  test_grade:186  test_order_independent:240  panels_of:263  test_history_real:268  test_rental_real:303  test_insurance:343  test_safety_real:366  test_spec_gate:408  test_price_real:468  test_color:532  test_price_pending:552  test_absolute_real:569  test_null_safe:609  test_empty_array_meaning:626  test_peer_group:649  test_damage_by_status:691  test_repair_cost_ratio:718  test_hda_gate:727
```

### `tests/test_run.py` — 749줄

```
check:36  StubEncar:92  Clock:236  setup:241  test_envelope:279  test_last_page_exact:307  test_facet:314  test_facet_missing_axis:328  test_dict_step:337  test_all_groups:359  test_parse_pipeline:370  test_score_pipeline:474  test_validate:529  test_registry_gate:572  test_target_scope:629  test_catalog_key:661  test_wrapper_args:679  test_unclassified_listing:716
```

### `tools/check_src.py` — 742줄

```
_spec_files:32  _read_spec:50  say:61  py_files:75  chapter_of:115  _declared_chapters:125  split_done:145  _illustration:164  _git:612
```

### `collect/pipeline.py` — 689줄

```
envelope_scope:41  Reprocess:91  reprocess_plan:110  should_refetch:127  expected_for:139  step_report:173  halt_if:189  precheck:222  resume_point:276  config_hash:296  build_run_context_fields:302  stale_rows:311  save_step_report:326  run_step:350  _execute:388  completed_steps:405  run_pipeline:417  print_progress:453  silent_progress:472  from_step_for:486  web_reasons:492  check_recalc_origin:497  plan_recalc:509  _current:526  run_recalc:532  Defect:546  DefectReport:557  diagnose:578  _DiagCtx:602  _collect_defects:612  format_defects:666
```

### `store/watch.py` — 612줄

```
AlertConfig:55  WatchItem:68  TrackPoint:83  TrackEvent:98  WatchEvent:112  classify_duplicates:124  sync_duplicates:164  deduped_count:187  watch_add:197  assert_owner:236  watch_update:251  watch_close:271  track_snapshot:283  track_points:312  classify_cause:321  detect_events:333  message:391  notify:419  add_watch_query:489  run_watch_queries:524  watch_query_rows:580  close_watch_query:594
```

### `store/admin.py` — 609줄

```
_admin_cfg:46  ConfigChange:68  running_job:86  hash_secret:96  _split:104  create_account:109  account_count:143  needs_bootstrap:147  _recent_failures:155  _log_attempt:174  authenticate:183  open_session:216  session_account:236  change_secret:253  revoke_sessions:277  _walk:288  get_path:312  set_path:317  _atomic_write:324  apply_config:334  _validate_blob:398  revert_config:411  history:435  classify_field:459  account_rows:512  admin_count:523  set_role:530  set_disabled:547  add_config_key:567
```

### `parse/encar/mapping.py` — 601줄

```
_get:30  _json:42  _won:53  _ym:73  _date10:83  _int:99  _bool:105  unpack_envelope:116  parse_list_item:124  parse_detail:168  parse_inspection:244  parse_record:284  _sample_chars:338  safe_field:352  parse_with_issues:374  _salvage:392  _parses:435  dig:442  as_list:465  _diag_comment:493  parse_diagnosis:500  parse_diagnosis_items:532  _text:540  parse_record_summary:550  parse_platform_check:576  parse_inspection_summary:583  parse_ev_battery:588  parse_sellingpoint:595
```

### `validate/v1_collect.py` — 589줄

```
run:119  _endpoint_order_check:251  _empty_db_check:263  _run_scope_check:290  _ctx_started:315  _has_run_id:323  _expected_scope_check:328  _diagnosis_scope_check:349  _diagnosis_none_count:387  _query_key_check:410  _entrypoint_parity_check:435  _enclosing_def:464  _run_id_filled_check:473  _catalog_key_check:493  _whole_probe:515  _whole_body_check:526  _unparsed_envelope_check:552
```

### `store/core.py` — 586줄

```
resolve_listing_id:35  resolve_dealer_id:53  serialize_container:69  record_change:80  split_pii:102  flush_dealer_pii:149  _record_dropped:161  upsert_core:180  mark_gone:257  load_snapshot:274  build_identities:354  resolve_vehicle_id:380  merge_conflict:412  upsert_vehicle:423  upsert_dealer:444  upsert_child:471  state_counts:488  current_versions:514  diagnosis_of:544  target_counts:557  top_target:564  vehicle_of:569  collect_scale:576
```

### `validate/v4_mapping.py` — 573줄

```
_paths:114  _layer_of:161  _layer_checks:166  _name_collision_check:260  _key:294  run:300  _mapping_coverage_checks:434  _our_columns:464  _listing_value_scope_check:490  _dict_filled_check:510  _kind_check:521  propose_fix:535  _option_code_check:550  _is_sentence:567
```

### `tests/test_admin_flow.py` — 555줄

```
check:32  _env:38  _cfg:55  _post:60  _get:65  flow_config:71  flow_scoring:107  _rescore:161  _dist:220  flow_targets:227  flow_registry:262  flow_run:302  flow_query:335  flow_api:361  flow_tools:398  flow_users:420  flow_requests:465  flow_permission:507  main:520
```

### `tests/test_admin.py` — 537줄

```
_spec_menu_paths:31  check:46  setup:52  test_bootstrap:64  test_auth:94  test_apply_config:136  test_value_validation:174  test_revert:194  test_no_direct_edit:220  test_classify_field:248  test_run_query:322  test_dev_request:358  test_recalc_and_lock:388  test_admin_screens:422  test_v10:501
```

### `validate/v10_admin.py` — 527줄

```
_sources:134  _admin_guard_checks:155  _sql_strings:200  run:212  _session_checks:318  _pii_query_check:389  _scratch:436  _dict_reason_check:451  _dict_source_shown_check:467  _queue_consumer_check:485  _queue_stale_shown_check:514
```

### `tests/test_web.py` — 493줄

```
check:21  test_routes:28  test_template:77  test_no_logic_in_template:118  test_static_escape:133  test_session_cookie:145  test_error_page:163  test_layout:190  test_filters:219  test_empty_state:238  test_menu_by_role:265  test_guard_and_csrf:282  _call:324  test_screens_render:341  test_sketch_match:424  test_account_policy:439
```

### `report/render.py` — 491줄

```
_labels:29  _stamp:34  _curve_points:49  _encar_url:92  render_listing:101  _option_rows:181  _fetch_views:232  _strengths:247  _weaknesses:254  _pending_best:261  _cost_rows:293  _known_issues:314  _diagnosis_view:332  render_target:343  render_run:424  render_halt:466  _j:484
```

### `store/dictionary.py` — 440줄

```
CodeEntry:31  AxisPolicy:57  policy:97  scope_key:105  seed_fixed_enums:130  upsert_enum:166  _handle_conflict:216  upsert_option3:237  retire_unseen:273  resolve_code:288  installed_option_names:326  normalize_enum:344  assert_no_unknown:360  bump_dict_version:403  list_pending:413  confirm_enum:421
```

### `contracts.py` — 433줄

```
Response:24  Clock:34  Fetcher:39  Rng:44  Request:52  EndpointSpec:60  FetchResult:71  TargetSpec:84  ListingSnapshot:135  AxisResult:197  Account:216  require_role:233  RunContext:250  StepReport:270  ResumePoint:294  clean_vin:315  total_of:326  RegressionReport:339  json_paths:350  shape_ok:398  shape_violations:431
```

### `report/screens/views.py` — 424줄

```
AxisChip:30  ListingRow:52  ListingFilter:153  WatchRow:179  TargetStat:197  RelaxRow:206  MarketRow:213  ChangeRow:225  AttentionItem:235  ViewerState:243  DashboardView:257  CompareView:281  MarketView:292  DealerRow:305  NotReadyView:326  TodayChange:344  StepRow:356  _min_sample:368  PendingValue:386  Bucket:399  ExcludedGroup:419
```

### `run.py` — 404줄

```
load:51  make_context:56  _filter_targets:70  _steps_from:89  cmd_collect:103  _grade_summary:171  cmd_admin_create:186  _collect_urls:203  _page_url:240  cmd_web:259  make_worker_ctx:290  make_worker_executors:296  cmd_delegate:326  _api_fetch:337  cmd_setup:347
```

### `web/app.py` — 390줄

```
menu_items:22  _tip:89  _label:94  empty_state:101  static_version:136  build_page:164  check_post:185  redirect:204  take_flashes:215  _display_now:228  make_app:254  _Denied:366  build_context:374  _title_of:389
```

### `tests/test_pipeline.py` — 382줄

```
check:37  db:43  test_expected:49  test_halt:61  test_reprocess:82  test_refetch:107  test_precheck:115  test_resume_and_version:161  test_run_pipeline:189  test_recalc:224  test_pii_orphan:259  test_exception_becomes_halt:292  test_fixed_enum_bootstrap:313  test_envelope_scope:343
```

### `tests/test_collect.py` — 368줄

```
check:34  R:40  test_verify_shape:45  _Stub:80  _Clock:88  test_fetch_status:93  test_interpret_failure:106  test_facet_axes:118  test_collect_groups:146  test_build_q:158  test_collect_check:208  test_save_raw:223  test_fail_streak:252  test_all_fail_sample:294  test_diagnosis_scope:338
```

### `tools/check_spec.py` — 354줄

```
_read_spec:10  _refs_source:73  _spec_files:284
```

### `tools/sync_registry.py` — 345줄

```
FieldUsage:31  RegistrySyncReport:48  facet_path:66  scan_paths:74  shape_ok:79  _walk_values:92  collect_values:106  collect_paths:130  _seed_for:153  sync_registry:164  suggest_usage:246  write_suggested:258  halt_report:285  list_by_usage:308  assert_registered:315
```

### `report/views.py` — 307줄

```
VersionStamp:18  ReportMeta:30  AxisView:40  FinanceView:52  DiagnosisView:74  FetchView:86  CostRow:100  ScoreView:109  CollectSummary:155  ClassifySummary:162  PriceSummary:169  AxisStat:178  CoefficientChange:188  DictChangeSummary:198  TargetReport:206  RunStep:218  RunReport:233  HaltReport:244  FixAction:261  NotifyResult:271  ExportResult:284  display_value:293  display_points:303
```

### `tools/build_dict.py` — 298줄

```
DictBuildReport:63  extract_distinct:78  _facet_values:106  _walk_path:122  load_fixed_enums:149  build_dict:157  _mark_facet_substituted:208  build_catalog_dict:232  build_late_dict:270
```

### `adapters/encar.py` — 285줄

```
escape_value:126  unescape_value:136  _nest:141  load_site_config:152  EncarAdapter:171
```

### `tests/test_fixtures.py` — 284줄

```
check:33  fx:39  test_inspection:53  test_frame_vs_outer:84  test_record:123  test_detail:152  test_classify_real:172  test_catalog:207  test_diagnosis:219
```

### `tests/test_dict.py` — 280줄

```
check:39  db:45  test_scope_key:51  test_count_zero:73  test_axis_policy:97  test_conflict:140  test_catalog:172  test_status_version:196  test_classify:213  test_review:242
```

### `store/raw.py` — 279줄

```
batch:36  commit:62  open_db:68  _safe_headers:85  save_raw:92  save_import_raw:141  save_browser_raw:174  save_browser_facet:205  save_import_facet:229  save_facet:259
```

### `web/template.py` — 278줄

```
f_won:42  f_km:58  f_pct:62  f_date:66  f_num:77  f_gradecls:84  f_count:90  f_signcls:98  f_signwon:108  _index_key:135  _step:150  _lookup:162  _truthy:171  render_str:175  render:263
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

### `tools/render_screens.py` — 255줄

```
_tmp_root:44  main:62  shot_paths:143  shoot:163
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

### `validate/v5_value.py` — 242줄

```
run:60  _grade_ratio_checks:151  _denominator_suite:193
```

### `tests/test_report.py` — 241줄

```
check:33  test_finance:40  test_display:92  _pipeline:108  test_layers:119  test_halt_layer:155  test_export:197
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

