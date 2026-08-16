# 소스 색인

**`python3.11 tools/build_index.py` 가 만든다. 손으로 고치지 않는다.**

파일 118개 · 총 36,447줄

| 파일 | 줄 | 무엇 |
|---|--:|---|
| `validate/v11_web.py` | 2,339 | V11 표현 계층 검증 (14장 STEP 153). |
| `web/views.py` | 1,802 | 화면 어댑터 (14장 STEP 142 · 152). |
| `report/screens/build.py` | 1,429 | 화면 데이터 생성. |
| `tests/test_spec_ui.py` | 1,414 | 규격 기준 통합 테스트 (통합테스트_시나리오_규격기준.md). |
| `collect/runner.py` | 1,213 | 수집 실행 규칙. |
| `tests/test_integration.py` | 1,212 | 통합 테스트 — 실제 HTTP 로 전 화면 (통합테스트_시나리오.md). |
| `report/screens/admin.py` | 927 | 관리자 화면 — 표현 계층 (13장 STEP 138 · 138a). |
| `store/adminops.py` | 904 | 관리자 서버 계층 — 실행 지시 · 쿼리 · API 조회 · 개발 요청 · 미리보기. |
| `validate/v2_load.py` | 872 | V2 적재 검증 — 옮겨졌는가 · 전일 대비 변동이 타당한가. |
| `validate/v3_logic.py` | 870 | V3 로직 검증 — 판정이 작동하는가 · 변별력이 있는가. |
| `tests/test_score.py` | 781 | 7장 판정·채점 시험. |
| `tests/test_run.py` | 743 | S0~S3 종단 시험 (모의 응답). |
| `tools/check_src.py` | 737 | CarWatch v2 — 지시서 ↔ 소스 대조 검증기. |
| `collect/pipeline.py` | 689 | 실행 순서 · 중단 · 재처리 · 재개. |
| `store/watch.py` | 612 | 후보 추적 (11장). |
| `store/admin.py` | 609 | 관리자 — 계정 · 권한 · config 변경 (13장 앞부분). |
| `parse/encar/mapping.py` | 601 | 엔카 원문 → CORE 필드 (L3). |
| `store/core.py` | 584 | CORE 저장소 (L4).  사이트 무관 공통 스키마. |
| `validate/v4_mapping.py` | 571 | V4 매핑 검증 — 이름이 아니라 값으로 검증한다. |
| `tests/test_admin_flow.py` | 555 | 관리 화면 동작 시험 (13장 · 14장). |
| `validate/v1_collect.py` | 546 | V1 수집 검증 — 다 받았는가 · 라벨이 맞는가. |
| `tests/test_admin.py` | 537 | 13장 앞부분 시험 — 계정 · 권한 · config 변경. |
| `validate/v10_admin.py` | 527 | V10 관리자 검증. |
| `tests/test_web.py` | 493 | 14장 표현 계층 시험 — 템플릿 · 라우팅. |
| `report/render.py` | 491 | 리포트 생성 (L9). |
| `store/dictionary.py` | 440 | 사전 저장소 (L5).  RAW 에서 생성한다. |
| `contracts.py` | 431 | 계층 간 계약 — Protocol · DTO. |
| `report/screens/views.py` | 419 | 화면 전용 DTO. |
| `run.py` | 404 | CarWatch v2 진입점. |
| `tests/test_pipeline.py` | 382 | 5장 수집 순서 시험. |
| `web/app.py` | 371 | 화면 조립 (14장 STEP 144 · 147 · 149). |
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
| `tools/check_screens.py` | 227 | 화면 ↔ 시안 대조 (10장 · 14장). |
| `store/crosssite.py` | 225 | 다중 사이트 확장 (12장). |
| `tools/build_index.py` | 212 | 검사 색인 · 소스 색인을 만든다 (규칙 11). |
| `web/server.py` | 199 | HTTP 서버 (14장 STEP 141 · 150). |
| `validate/v7_watch.py` | 194 | V7 관심·추적 검증. |
| `parse/importer.py` | 182 | 반입 입력 해석 (13장 STEP 136a · 136b). |
| `web/context.py` | 181 | 화면 문맥과 오류 (14장 STEP 144 · 148). |
| `validate/base.py` | 180 | 검증 계약. |
| `tests/seed.py` | 178 | 시험용 씨앗 DB — 운영 DB 를 복사하지 않는다. |
| `tools/migrate.py` | 174 | 스키마 이행 — 기존 DB 를 현재 DDL 에 맞춘다. |
| `analyze/axis/history.py` | 156 | 이력 55점 — 사고 20 · 보험 15 · 렌트 20. |
| `web/session.py` | 156 | 세션 · CSRF · 정적 파일 (14장 STEP 145~147). |
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
| `tools/report_cli.py` | 109 | 리포트 재생성 (9장 STEP 90 · 91a · B-6). |
| `score/scorer.py` | 108 | 채점 · 분모 (L7). |
| `tools/check_all.py` | 107 | 실측 DB 회귀 — V1~V5 · V10 전건을 한 번에 돌린다. |
| `analyze/axis/value.py` | 103 | ① 값 250점 — 시세 대비 120 · 신차가 대비 감가 70 · 주행 대비 60. |
| `analyze/axes.py` | 102 | 축 판정 계약. |
| `store/tools.py` | 97 | 관리 도구 (13장 STEP 135). |
| `report/finance.py` | 95 | 금융 — 점수가 아니라 비용이다. |
| `analyze/axis/taste.py` | 94 | ④ 취향 50점 — HUD 15 · 선루프 10 · 색상 10 · 지정 옵션 15. |
| `analyze/verdict.py` | 94 | 판정 엔진 — 순서 무관 put(). |
| `tools/export_cli.py` | 93 | 데이터 내보내기 (9장 STEP 91a · B-6). |
| `tools/setup_check.py` | 92 | 착수 점검 — 실행 전에 무엇이 준비됐는지 한 번에 본다. |
| `analyze/axis/price.py` | 90 | 가격 200점. |
| `analyze/absolute.py` | 88 | E등급 절대조건 10종. |
| `analyze/peer.py` | 80 | 유사군 — 「이런 차가 보통 얼마인가」 (7장 STEP 82e). |
| `tools/inspect_dict.py` | 75 | 사전 검토 — pending 값과 원문 표본을 본다. |
| `tools/inspect_facet.py` | 74 | facet 원문에 실제로 어떤 축이 왔는지 본다. |
| `report/why_cheap.py` | 73 | 「왜 싼가」 — 싼 이유를 순서대로 찾아 낸다 (개정 299 · V3-52). |
| `analyze/trust.py` | 70 | 플랫폼 신뢰도 — 점검 출처 · 엔카진단 · 엔카보증 (개정 300). |
| `score/grade.py` | 70 | 등급 (L7). |
| `analyze/axis/trim.py` | 64 | ③ 사양 75점 — 트림 등급 45 · 옵션 합 30. |
| `analyze/axis/warranty.py` | 56 | 보증 100점 — 일반 50 + 파워트레인 50. |
| `tools/inspect_requests.py` | 52 | 요청 기록을 본다 — 무엇을 던졌고 무엇이 돌아왔는가. |
| `analyze/axis/safety.py` | 44 | 안전 40점 — 진단 20 + 보증상품 20. |
| `adapters/base.py` | 36 | 사이트 어댑터 인터페이스. |
| `report/peer.py` | 35 | 유사군 조회 (7장 STEP 82e). |
| `analyze/axis/color.py` | 33 | 색상 40점. |
| `analyze/axis/mileage.py` | 31 | 주행거리 30점. |
| `analyze/axis/_util.py` | 29 | 축 공용 도우미. |
| `analyze/engine.py` | 28 | 판정 실행 (L6).  축 함수를 순서 무관하게 호출한다. |
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

### `validate/v11_web.py` — 2,339줄

```
_web_sources:364  run:376  _late_checks:486  _templates_with_form:550  _spec_routes:566  _routing_table_check:588  _count:622  ctx_account:629  _view_exists:635  _tpl:656  _all_templates:661  _screen_checks:666  _query_budget_check:873  _import_origin_check:944  _import_step4_check:979  _browser_origin_check:1003  _browser_confirm_check:1021  _browser_chunk_check:1046  _status_screen_checks:1082  _status_liveness_check:1120  _menu_label_check:1158  _listing_paging_checks:1175  _photo_checks:1211  _sian_css_checks:1247  _cell_of:1309  _link_tip_checks:1322  _origin_link_check:1336  _choose_check:1364  _order_filter_checks:1380  _origin_price_check:1423  _v1_parity_checks:1442  _media_blocks:1489  _responsive_checks:1505  _dead_links:1561  _null_link_check:1575  _sian_visual_check:1635  _cell_squeeze_check:1696  _static_version_check:1751  _axis_state_check:1769  _three_values_check:1805  _photo_size_check:1831  _render_metrics_checks:1854  _browser_scope_checks:1941  _import_opened_steps_check:1962  _import_resume_check:1990  _watch_invite_check:2009  _post_smoke_check:2053  _template_roots:2126  _loop_fields:2136  _context_supplied_check:2158  _first_item:2225  _has_field:2239  _table_counts:2245  _save_button_check:2252  _probe:2309  _scratch:2327
```

### `web/views.py` — 1,802줄

```
_rows_per_page:27  _cfg:31  _versions:36  page:55  listings:78  why:108  notready:139  dashboard:149  admin_home:164  admin_audit:173  admin_docs:186  _int_param:210  _manwon:249  _filter_chips:254  _order_menu:305  _carry:311  _order_label:321  ORDERS_LABELS_GET:325  _condition_sentence:329  _query_string:347  _page_links:360  _simple_paging:381  _paging:391  _filter_buttons:421  _filter:453  recommend:490  compare:512  market:527  _first_target:547  dealers:553  watch:573  run_view:587  login:599  _login_again:633  _open_session:648  logout:674  _watch_queries:691  watch_query_post:700  _int_or_none:730  watch_add_post:734  _watch_invite:790  watch_update_post:811  _now:835  _reason_gate:842  _gate:863  _first_flag:902  _all_hours:907  admin_run:934  _target_rows:1000  admin_dict:1013  admin_status:1047  admin_collect:1062  _run_stamp:1102  _int_or_none:1113  admin_import:1118  admin_scoring:1190  admin_registry:1243  admin_query:1279  admin_requests:1301  _admin_extra:1363  _config_files:1378  _config_rows:1385  admin_config:1417  _typed:1468  admin_api:1484  _site_query:1534  admin_targets:1547  admin_tools:1645  join:1664  password:1695  admin_users:1710  _account_activity:1762
```

### `report/screens/build.py` — 1,429줄

```
axis_heads:61  _labels:69  viewer_state:74  chip:84  _stamp:113  _bulk_axes:117  confirm_ratio:138  _bulk_changes:149  _total_points:176  photo_url:188  market_price:219  _days_between:236  _ceil_to:251  _bulk_market:267  _bulk_state:306  _left:333  _warranty_state:342  _axis_state:378  _row:418  _view_cfg:538  order_clause:573  _view_str:579  _listings_where:585  count_listings:640  view_listings:652  _option_prices:714  recommend_funnel:726  _bulk_upside:743  view_recommend:758  excluded_groups:791  view_why:806  view_compare:812  market_trims:843  view_market:862  _web_cfg:895  _median:909  _with_height:914  _price_bins:929  _group_prices:950  _by_year:968  _by_trim:985  _other_targets:1003  count_dealers:1011  _dealer_targets:1017  _dealer_region:1037  view_dealers:1052  view_run:1088  _rank1_of:1094  view_dashboard:1102  _grade_counts:1194  _e_reasons:1201  _today_changes:1218  _step_rows:1243  _bulk_spark:1260  view_watch:1296  _pending_values:1346  _done_items:1355  view_notready:1381  _unmatched_rows:1416
```

### `tests/test_spec_ui.py` — 1,414줄

```
rec:33  spec_a:43  spec_b:117  spec_c:191  spec_d:231  spec_f:264  spec_g:290  spec_h:338  spec_j:371  spec_m:414  spec_e:482  spec_i:525  spec_k:631  spec_l:686  spec_monkey:725  flow_s1:797  flow_s2:859  flow_s5:942  flow_s3:1055  flow_s4:1130  flow_s6:1201  guide_v132:1257  main:1349  _write:1392
```

### `collect/runner.py` — 1,213줄

```
CollectGroup:67  load_targets:91  collect_groups:104  facet_axes:132  aspect_names:153  check_facet_axes:157  interpret_failure:171  collect_check:200  FailStreak:267  _sleep:301  _log_request:307  _save_issues:318  make_executors:329  _group_of:820  _fuel_of:835  _badge_of:841  _pages_for:847  _dicts:861  _market_medians:897  _trim_ladders:926  _listing_config:943  _listing_values:965  _market_of:984  make_score_executors:994  make_validate_executor:1142  make_registry_executor:1184
```

### `tests/test_integration.py` — 1,212줄

```
rec:31  Client:41  text:96  links:101  start_server:105  seed_admin:149  m1:165  m2:253  m3:327  m4:631  s3:696  unit:749  gaps:778  flows:886  guide7:987  _account_id:1116  make_users:1123  main:1141  _write_table:1190
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

### `validate/v3_logic.py` — 870줄

```
_file_output_checks:205  _conflict_checks:258  _diagnosis_count_check:282  _hda_source_check:298  _sort_determinism:309  _warning_contract_checks:326  _list_observed_source_check:421  _facet_reconcile_check:451  _denominator_check:474  _core_axis_check:502  _rental_cross_check:520  _why_cheap_check:558  _rendered_listings:597  _fill_gap_check:607  _points_sum_check:640  _market_gap_check:657  run:713  _shuffle_check:819  _halt_dict_check:844
```

### `tests/test_score.py` — 781줄

```
check:36  fx:42  snap:46  ctx:62  full_verdict:83  test_denominator:96  test_components_form:140  test_grade:185  test_order_independent:238  panels_of:261  test_history_real:266  test_rental_real:301  test_insurance:341  test_safety_real:364  test_spec_gate:406  test_price_real:466  test_color:530  test_price_pending:550  test_absolute_real:567  test_null_safe:607  test_empty_array_meaning:624  test_peer_group:647  test_damage_by_status:689  test_repair_cost_ratio:716  test_hda_gate:725
```

### `tests/test_run.py` — 743줄

```
check:36  StubEncar:92  Clock:236  setup:241  test_envelope:279  test_last_page_exact:307  test_facet:314  test_facet_missing_axis:328  test_dict_step:337  test_all_groups:359  test_parse_pipeline:370  test_score_pipeline:474  test_validate:523  test_registry_gate:566  test_target_scope:623  test_catalog_key:655  test_wrapper_args:673  test_unclassified_listing:710
```

### `tools/check_src.py` — 737줄

```
_spec_files:32  _read_spec:50  say:61  py_files:75  chapter_of:115  _declared_chapters:125  split_done:145  _illustration:164  _git:607
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

### `store/core.py` — 584줄

```
resolve_listing_id:35  resolve_dealer_id:53  serialize_container:69  record_change:80  split_pii:102  flush_dealer_pii:149  _record_dropped:161  upsert_core:180  mark_gone:257  load_snapshot:274  build_identities:352  resolve_vehicle_id:378  merge_conflict:410  upsert_vehicle:421  upsert_dealer:442  upsert_child:469  state_counts:486  current_versions:512  diagnosis_of:542  target_counts:555  top_target:562  vehicle_of:567  collect_scale:574
```

### `validate/v4_mapping.py` — 571줄

```
_paths:114  _layer_of:161  _layer_checks:166  _name_collision_check:260  _key:294  run:300  _mapping_coverage_checks:434  _our_columns:464  _listing_value_scope_check:488  _dict_filled_check:508  _kind_check:519  propose_fix:533  _option_code_check:548  _is_sentence:565
```

### `tests/test_admin_flow.py` — 555줄

```
check:32  _env:38  _cfg:55  _post:60  _get:65  flow_config:71  flow_scoring:107  _rescore:161  _dist:220  flow_targets:227  flow_registry:262  flow_run:302  flow_query:335  flow_api:361  flow_tools:398  flow_users:420  flow_requests:465  flow_permission:507  main:520
```

### `validate/v1_collect.py` — 546줄

```
run:114  _endpoint_order_check:245  _empty_db_check:257  _run_scope_check:284  _ctx_started:309  _has_run_id:317  _expected_scope_check:322  _diagnosis_scope_check:343  _diagnosis_none_count:381  _query_key_check:404  _entrypoint_parity_check:429  _enclosing_def:458  _run_id_filled_check:467  _catalog_key_check:487  _unparsed_envelope_check:509
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

### `contracts.py` — 431줄

```
Response:24  Clock:34  Fetcher:39  Rng:44  Request:52  EndpointSpec:60  FetchResult:71  TargetSpec:84  ListingSnapshot:135  AxisResult:195  Account:214  require_role:231  RunContext:248  StepReport:268  ResumePoint:292  clean_vin:313  total_of:324  RegressionReport:337  json_paths:348  shape_ok:396  shape_violations:429
```

### `report/screens/views.py` — 419줄

```
AxisChip:30  ListingRow:52  ListingFilter:148  WatchRow:174  TargetStat:192  RelaxRow:201  MarketRow:208  ChangeRow:220  AttentionItem:230  ViewerState:238  DashboardView:252  CompareView:276  MarketView:287  DealerRow:300  NotReadyView:321  TodayChange:339  StepRow:351  _min_sample:363  PendingValue:381  Bucket:394  ExcludedGroup:414
```

### `run.py` — 404줄

```
load:51  make_context:56  _filter_targets:70  _steps_from:89  cmd_collect:103  _grade_summary:171  cmd_admin_create:186  _collect_urls:203  _page_url:240  cmd_web:259  make_worker_ctx:290  make_worker_executors:296  cmd_delegate:326  _api_fetch:337  cmd_setup:347
```

### `tests/test_pipeline.py` — 382줄

```
check:37  db:43  test_expected:49  test_halt:61  test_reprocess:82  test_refetch:107  test_precheck:115  test_resume_and_version:161  test_run_pipeline:189  test_recalc:224  test_pii_orphan:259  test_exception_becomes_halt:292  test_fixed_enum_bootstrap:313  test_envelope_scope:343
```

### `web/app.py` — 371줄

```
menu_items:22  _tip:89  _label:94  empty_state:101  static_version:136  build_page:164  check_post:185  redirect:198  take_flashes:209  _display_now:222  make_app:248  _Denied:347  build_context:355  _title_of:370
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

### `tools/check_screens.py` — 227줄

```
_pairs:23  say:67  _text:76  check_pairs:83  check_phrases:96  _heads:121  check_sections:140  check_nav:162  check_render:178  main:210
```

### `store/crosssite.py` — 225줄

```
CrossSiteMatch:31  ReadinessReport:41  active_sites:51  match_cross_site:56  rebuild_core_vehicle:92  regression_check:111  snapshot_baseline:142  readiness:166  load_sites:205  site_addition_regression:210
```

### `tools/build_index.py` — 212줄

```
_py_files:35  _checks_in_code:50  _checks_in_docs:82  build_checks:115  _outline:156  build_source:167  main:199
```

