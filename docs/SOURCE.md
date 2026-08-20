# 소스 색인

**`python3.11 tools/build_index.py` 가 만든다. 손으로 고치지 않는다.**

파일 135개 · 총 48,766줄

| 파일 | 줄 | 무엇 |
|---|--:|---|
| `validate/v11_web.py` | 4,191 | V11 표현 계층 검증 (14장 STEP 153). |
| `web/views.py` | 2,206 | 화면 어댑터 (14장 STEP 142 · 152). |
| `report/screens/build.py` | 1,880 | 화면 데이터 생성. |
| `validate/v3_logic.py` | 1,688 | V3 로직 검증 — 판정이 작동하는가 · 변별력이 있는가. |
| `store/core.py` | 1,537 | CORE 저장소 (L4).  사이트 무관 공통 스키마. |
| `tests/test_spec_ui.py` | 1,457 | 규격 기준 통합 테스트 (통합테스트_시나리오_규격기준.md). |
| `collect/runner.py` | 1,423 | 수집 실행 규칙. |
| `tests/test_integration.py` | 1,218 | 통합 테스트 — 실제 HTTP 로 전 화면 (통합테스트_시나리오.md). |
| `tools/check_src.py` | 1,130 | CarWatch v2 — 지시서 ↔ 소스 대조 검증기. |
| `tools/verify_axes.py` | 1,051 | 손계산 대조 — 축마다 표본 3건 (개정 329 전수검증 · V3-66). |
| `store/adminops.py` | 1,037 | 관리자 서버 계층 — 실행 지시 · 쿼리 · API 조회 · 개발 요청 · 미리보기. |
| `report/screens/admin.py` | 1,012 | 관리자 화면 — 표현 계층 (13장 STEP 138 · 138a). |
| `validate/v2_load.py` | 917 | V2 적재 검증 — 옮겨졌는가 · 전일 대비 변동이 타당한가. |
| `validate/v10_admin.py` | 895 | V10 관리자 검증. |
| `tools/trace_fill.py` | 840 | 추적표의 소스 · 화면 · 검사 칸을 기계로 채운다 (`inbox/ORDER_00_trace_fill.md`). |
| `tests/test_score.py` | 800 | 7장 판정·채점 시험. |
| `validate/v1_collect.py` | 775 | V1 수집 검증 — 다 받았는가 · 라벨이 맞는가. |
| `validate/v4_mapping.py` | 770 | V4 매핑 검증 — 이름이 아니라 값으로 검증한다. |
| `tests/test_run.py` | 754 | S0~S3 종단 시험 (모의 응답). |
| `collect/pipeline.py` | 730 | 실행 순서 · 중단 · 재처리 · 재개. |
| `report/render.py` | 723 | 리포트 생성 (L9). |
| `store/watch.py` | 679 | 후보 추적 (11장). |
| `store/admin.py` | 665 | 관리자 — 계정 · 권한 · config 변경 (13장 앞부분). |
| `parse/encar/mapping.py` | 621 | 엔카 원문 → CORE 필드 (L3). |
| `tests/test_admin_flow.py` | 566 | 관리 화면 동작 시험 (13장 · 14장). |
| `tools/check_spec.py` | 557 | CarWatch v2 지시서 자체 점검 — 7종 |
| `tests/test_admin.py` | 554 | 13장 앞부분 시험 — 계정 · 권한 · config 변경. |
| `tests/test_web.py` | 505 | 14장 표현 계층 시험 — 템플릿 · 라우팅. |
| `report/screens/views.py` | 497 | 화면 전용 DTO. |
| `store/dictionary.py` | 466 | 사전 저장소 (L5).  RAW 에서 생성한다. |
| `contracts.py` | 462 | 계층 간 계약 — Protocol · DTO. |
| `web/app.py` | 452 | 화면 조립 (14장 STEP 144 · 147 · 149). |
| `tools/build_index.py` | 420 | 검사 색인 · 소스 색인을 만든다 (규칙 11). |
| `run.py` | 412 | CarWatch v2 진입점. |
| `tools/sync_registry.py` | 390 | RAW 경로 전수 → meta_field_usage. |
| `tests/test_pipeline.py` | 388 | 5장 수집 순서 시험. |
| `report/views.py` | 376 | 리포트 DTO (L9). |
| `tests/test_collect.py` | 368 | 2장 수집 시험. |
| `tools/light_check.py` | 325 | 가벼운 점검 — 4시간마다 (개정 335 · S29-0). |
| `tools/render_screens.py` | 321 | 전 화면을 실제로 렌더해 `outputs/render/` 에 남긴다. |
| `validate/v7_watch.py` | 320 | V7 관심·추적 검증. |
| `tools/build_dict.py` | 317 | RAW → 사전 생성. |
| `validate/v9_multisite.py` | 293 | V9 — 다중 사이트 (`docs/chapters/50-multisite.md`). |
| `store/crosssite.py` | 291 | 다중 사이트 확장 (12장). |
| `tests/test_endtoend.py` | 290 | 종단 시험 — 수집부터 리포트까지 (5장 STEP 47 · 49). |
| `tests/test_dict.py` | 286 | 4장 키·코드·사전 시험. |
| `adapters/encar.py` | 285 | 엔카 어댑터 — URL · 헤더 · 쿼리 조립. |
| `store/raw.py` | 285 | RAW 저장소 (L2).  원문 무손실.  삭제 금지. |
| `tests/test_fixtures.py` | 284 | 실물 표본 시험 — v1 원문 12건. |
| `web/template.py` | 284 | 최소 템플릿 엔진 (14장 STEP 143). |
| `tests/test_crosssite.py` | 275 | 12장 다중 사이트 시험. |
| `tests/test_screens.py` | 274 | 10장 화면 시험. |
| `report/exports/export.py` | 269 | 내보내기. |
| `tests/test_watch.py` | 259 | 11장 후보 추적 시험. |
| `tests/test_store.py` | 254 | 3장 테이블 시험. |
| `tools/menu.py` | 254 | 실행 메뉴. |
| `tests/test_report.py` | 249 | 9장 리포트 시험. |
| `analyze/axis/state.py` | 245 | ② 상태 150 — 차가 성한가 (docs/ref/F-scoring.md ②). |
| `tests/test_registry.py` | 245 | 8장 등록부 시험. |
| `validate/v5_value.py` | 242 | V5 수치 검증 — 기준값이 맞는가 · 보정이 타당한가. |
| `tests/test_invariants.py` | 232 | 불변식 시험. |
| `tools/check_screens.py` | 232 | 화면 ↔ 시안 대조 (10장 · 14장). |
| `validate/base.py` | 212 | 검증 계약. |
| `web/context.py` | 202 | 화면 문맥과 오류 (14장 STEP 144 · 148). |
| `tests/seed.py` | 200 | 시험용 씨앗 DB — 운영 DB 를 복사하지 않는다. |
| `web/server.py` | 199 | HTTP 서버 (14장 STEP 141 · 150). |
| `parse/importer.py` | 182 | 반입 입력 해석 (13장 STEP 136a · 136b). |
| `tools/classify_unclassified.py` | 175 | 미분류 경로를 원인별로 가른다 (개정 341 · V4-26 · V4-27). |
| `web/session.py` | 175 | 세션 · CSRF · 정적 파일 (14장 STEP 145~147). |
| `tools/migrate.py` | 174 | 스키마 이행 — 기존 DB 를 현재 DDL 에 맞춘다. |
| `tools/daily_check.py` | 170 | 일일 점검 — 매일 23:00 (개정 334 · S29). |
| `tools/weekly_check.py` | 163 | 주간 일제 점검 — 금 02:00 · 개발측 몫 (개정 334 · S29). |
| `score/scorer.py` | 157 | 채점 · 분모 (L7). |
| `report/finance.py` | 153 | 금융 — 점수가 아니라 비용이다. |
| `store/pii.py` | 152 | 개인정보 분리 (L4). |
| `analyze/axis/value.py` | 148 | ① 값 250 — 시세 대비 100 · 신차가 대비 80 · 주행 대비 70. |
| `collect/worker.py` | 147 | 큐 소비기 (13장 STEP 132a · 개정 261). |
| `score/adjust.py` | 145 | 배점 조정 — 비율 재배분과 정수 보정. |
| `tools/repair_facet_chunks.py` | 144 | 낱개로 저장된 facet 조각을 이어붙인다 (개정 307 사고 복구). |
| `tools/classify_registry.py` | 142 | 등록부 미분류 정리 — 근거가 있는 것만 (8장 STEP 87 · V4-11). |
| `tools/run_tests.py` | 142 | 시험 전체 실행. |
| `web/routes.py` | 140 | 라우팅 표 (14장 STEP 142). |
| `tools/classify_fields.py` | 139 | 등록부 분류 초안 — 파서가 쓰는 경로를 근거로 자동 분류한다. |
| `parse/classify.py` | 136 | 분류 2단 — target_key 판정. |
| `tools/trace_verify.py` | 136 | 추적표 「상태」를 사실로 (개정 349 · 350 · S34). |
| `analyze/axis/history.py` | 132 | ③ 이력 80 — 어떻게 쓰였나 (docs/ref/F-scoring.md ③). |
| `analyze/axis/spec.py` | 123 | 사양 90점 — HUD 20 · HDA 20 · 선루프 20 · SVM 10 · SCC 10 · 후측방 5 · 틴팅 5. |
| `score/penalty.py` | 123 | 마이너스 점수 (개정 322). |
| `collect/fetcher.py` | 121 | 원문 획득 · 형식 검증. |
| `errors.py` | 115 | 도메인 예외 5종. |
| `analyze/axis/site.py` | 114 | ⑤ 사이트 보증 50 · ⑦ 제조사 보증 50 (일반 20 + 동력계 30). |
| `tools/daily_enqueue.py` | 112 | 하루 한 번 스스로 돈다 (STEP 136h · 개정 315). |
| `analyze/axes.py` | 111 | 축 판정 계약. |
| `tools/report_cli.py` | 109 | 리포트 재생성 (9장 STEP 90 · 91a · B-6). |
| `tools/check_all.py` | 107 | 실측 DB 회귀 — V1~V5 · V10 전건을 한 번에 돌린다. |
| `adapters/kcar.py` | 104 | K카 어댑터 — URL · 헤더 (12장 · STEP 11). |
| `store/tools.py` | 97 | 관리 도구 (13장 STEP 135). |
| `analyze/axis/taste.py` | 94 | ④ 취향 50점 — HUD 15 · 선루프 10 · 색상 10 · 지정 옵션 15. |
| `analyze/verdict.py` | 94 | 판정 엔진 — 순서 무관 put(). |
| `tools/export_cli.py` | 93 | 데이터 내보내기 (9장 STEP 91a · B-6). |
| `tools/setup_check.py` | 92 | 착수 점검 — 실행 전에 무엇이 준비됐는지 한 번에 본다. |
| `analyze/axis/price.py` | 90 | 가격 200점. |
| `analyze/absolute.py` | 88 | E등급 절대조건 10종. |
| `analyze/axis/trim.py` | 83 | ④ 사양 45 — 트림 25 · 옵션 20 (docs/ref/F-scoring.md ④). |
| `analyze/peer.py` | 80 | 유사군 — 「이런 차가 보통 얼마인가」 (7장 STEP 82e). |
| `report/why_cheap.py` | 80 | 「왜 싼가」 — 싼 이유를 순서대로 찾아 낸다 (개정 299 · V3-52). |
| `store/chunk.py` | 77 | 조각 전송 — 바이트를 나누고 서버가 이어붙인다 (개정 307). |
| `tools/inspect_dict.py` | 75 | 사전 검토 — pending 값과 원문 표본을 본다. |
| `tools/inspect_facet.py` | 74 | facet 원문에 실제로 어떤 축이 왔는지 본다. |
| `analyze/trust.py` | 70 | 플랫폼 신뢰도 — 점검 출처 · 엔카진단 · 엔카보증 (개정 300). |
| `score/grade.py` | 70 | 등급 (L7). |
| `analyze/curve.py` | 61 | 구간별 점수표 (docs/ref/F-scoring.md). |
| `analyze/axis/warranty.py` | 56 | 보증 100점 — 일반 50 + 파워트레인 50. |
| `parse/encar/paths.py` | 56 | 파서가 읽는 원문 경로 — 코드에서 뽑는다 (2장 STEP 20). |
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

## 큰 파일 — 무엇이 어디에 (200줄 이상 65개)

### `validate/v11_web.py` — 4,191줄

```
_web_sources:565  run:577  _late_checks:687  _templates_with_form:751  _spec_routes:769  _routing_table_check:791  _count:828  ctx_account:835  _view_exists:841  _tpl:862  _all_templates:867  _screen_checks:872  _query_budget_check:1105  _import_origin_check:1176  _import_step4_check:1211  _browser_origin_check:1235  _browser_confirm_check:1253  _browser_chunk_check:1278  _status_screen_checks:1319  _status_liveness_check:1357  _menu_label_check:1398  _menu_paths:1426  _listing_rows:1451  _cli_caps:1469  _cli_only_check:1483  _stale_notice_check:1528  _trim_detail_check:1564  _option_sum_check:1587  _heart_line_check:1614  _recommend_terms_check:1637  _shortfall_check:1656  _cash_limit_check:1675  _py_files:1706  _menu_no_path_check:1720  _listing_paging_checks:1738  _photo_checks:1774  _sian_css_checks:1810  _cell_of:1872  _link_tip_checks:1885  _origin_link_check:1899  _choose_check:1927  _order_filter_checks:1943  _checks_cfg:1986  _photo_size_by_screen_check:1995  _template_leak_check:2019  _em_dash_check:2045  _card_limits:2081  _cells_of:2098  _matches:2126  _place_cards:2145  _card_shape_checks:2267  _why_order_spec:2349  _why_order_check:2366  _width_policy:2401  _width_checks:2408  _chart_check:2496  _row_link_checks:2527  _screen_contradiction_check:2563  _chunk_check:2585  _csrf_reuse_check:2625  _origin_price_check:2669  _v1_parity_checks:2705  _media_blocks:2782  _responsive_checks:2803  _dead_links:2884  _null_link_check:2898  _sian_visual_check:2962  _purchase_cost_checks:3026  _report_popup_check:3113  _detail_photo_check:3187  _raw_shown_checks:3238  _compare_diff_check:3325  _chunk_message_check:3389  _whole_char:3416  _chunk_boundary_check:3429  _cell_squeeze_check:3517  _static_version_check:3572  _axis_state_check:3590  _three_values_check:3628  _photo_size_check:3658  _render_metrics_checks:3684  _browser_scope_checks:3783  _import_opened_steps_check:3804  _import_resume_check:3832  _watch_invite_check:3851  _post_smoke_check:3895  _template_roots:3968  _loop_fields:3978  _context_supplied_check:4000  _first_item:4071  _has_field:4085  _table_counts:4091  _save_button_check:4098  _probe:4155  _scratch:4173
```

### `web/views.py` — 2,206줄

```
_rows_per_page:27  _cfg:31  _versions:36  page_extras:55  _points:64  page:78  listings:105  why:138  notready:172  dashboard:182  admin_home:200  _unclassified_split:212  _rows_of:240  _check_reports:250  admin_audit:273  admin_docs:286  _int_param:310  _manwon:349  _site_buttons:354  _filter_chips:385  _order_menu:436  _carry:442  _order_label:452  ORDERS_LABELS_GET:456  _condition_sentence:460  _query_string:478  _page_links:491  _simple_paging:512  _paging:522  _filter_buttons:552  _filter:585  recommend:627  compare:655  market:670  _first_target:690  dealers:696  watch:716  _note_kinds:733  _watch_notes:740  run_view:767  login:779  _login_again:813  _open_session:828  logout:854  _watch_queries:871  watch_query_post:880  _int_or_none:910  watch_add_post:914  _watch_note_post:974  _watch_invite:1000  watch_update_post:1021  _now:1045  _reason_gate:1052  _gate:1073  _first_flag:1112  _all_hours:1117  admin_run:1145  _target_rows:1211  admin_dict:1224  admin_status:1258  admin_collect:1273  _take_chunk:1332  _verify_part:1375  _run_stamp:1415  _int_or_none:1426  admin_import:1431  admin_scoring:1503  _decide_cards:1556  admin_registry:1584  admin_query:1632  admin_requests:1654  _admin_extra:1716  _config_files:1731  _config_rows:1738  admin_config:1770  _typed:1821  admin_api:1837  _site_query:1887  admin_targets:1900  admin_tools:1998  join:2017  password:2048  admin_users:2063  _account_activity:2123  reports:2129  report_download:2145
```

### `report/screens/build.py` — 1,880줄

```
site_badge:70  axis_heads:90  _labels:98  viewer_state:103  chip:113  _stamp:142  _bulk_axes:146  confirm_ratio:167  _bulk_changes:178  _total_points:205  photo_urls:218  photo_url:250  market_price:281  _days_between:298  _ceil_to:313  _bulk_market:328  _bulk_state:367  not_join_months:400  _left:423  _warranty_state:432  _axis_state:470  _sites_cfg:528  _row:541  _view_cfg:717  order_clause:761  _view_str:767  _listings_where:773  count_listings:840  view_listings:852  _soh_low:928  _view_int:937  _bucket:943  _high_km:950  _option_prices:959  recommend_funnel:971  _bulk_upside:988  view_recommend:1003  recommend_reason:1034  excluded_groups:1077  view_why:1092  view_compare:1098  market_trims:1139  view_market:1161  _web_cfg:1197  _median:1211  _with_height:1216  _price_bins:1231  _group_prices:1252  _by_year:1270  _year_line:1287  _by_trim:1313  _other_targets:1331  count_dealers:1339  _dealer_targets:1345  _dealer_region:1365  view_dealers:1380  view_run:1416  _rank1_of:1422  view_dashboard:1430  _bars:1526  _grade_counts:1541  _e_reasons:1548  _today_changes:1565  _step_rows:1590  _bulk_spark:1607  view_watch:1643  _pending_values:1708  _done_items:1717  view_notready:1743  _unmatched_rows:1778  _report_files:1802  view_reports:1834
```

### `validate/v3_logic.py` — 1,688줄

```
_file_output_checks:322  _conflict_checks:375  _diagnosis_count_check:399  _hda_source_check:415  _sort_determinism:426  _warning_contract_checks:443  _list_observed_source_check:538  _facet_reconcile_check:568  _record_mismatch_check:612  _curve_table_check:642  _value_curve_checks:692  _group_sum_checks:762  _mapped_other_check:833  _denominator_check:860  _core_axis_check:888  _rental_cross_check:906  _why_cheap_check:944  _source_before_value_check:985  _absolute_cut_check:1012  _spec_files:1042  _confirm_ratio_check:1052  _warranty_checks:1102  _spec_axis_check:1136  _site_axis_checks:1177  _rendered_why:1226  _rendered_listings:1236  _fill_gap_check:1246  _points_sum_check:1279  _market_gap_check:1296  _bonus_checks:1352  _trim_price_check:1456  run:1504  _shuffle_check:1631  _halt_dict_check:1656  _ensure_tmp:1685
```

### `store/core.py` — 1,537줄

```
resolve_listing_id:38  resolve_dealer_id:56  serialize_container:72  record_change:83  split_pii:105  flush_dealer_pii:152  _record_dropped:164  classify_invariant_change:199  _lookback:239  _source_history:253  _schema_change_min:279  _current:293  _today:299  upsert_core:303  mark_gone:388  load_snapshot:405  build_identities:506  resolve_vehicle_id:532  merge_conflict:564  upsert_vehicle:575  upsert_dealer:596  upsert_child:623  _flag:644  _not_join_months:658  state_counts:683  current_versions:713  diagnosis_of:743  target_counts:756  top_target:763  vehicle_of:768  collect_scale:775  our_fault:795  catalog_coverage:804  _walk:848  _sample_bodies:864  hits_of:877  key_seen:896  stored_hits:911  sample_bodies:927  observed:949  known_leaves:987  has_unclassified:1002  classify_unclassified:1009  _card_limit:1052  _value_chars:1057  _admin_cfg:1062  unclassified_cards:1079  _peek:1135  _short:1182  _blocking_paths:1193  _raw_rows_max:1213  used_endpoints:1223  raw_sections:1232  _flatten:1271  option_diff:1295  _option_names:1333  blocking_keys:1349  full_hits:1367  axis_paths_empty:1392  blocking_rows:1429  record_mismatch_sql:1491  record_mismatch_count:1497  relist_counts:1523
```

### `tests/test_spec_ui.py` — 1,457줄

```
rec:33  spec_a:43  spec_b:121  spec_c:195  spec_d:239  spec_f:272  spec_g:298  spec_h:346  spec_j:379  spec_m:422  spec_e:490  spec_i:533  spec_k:646  spec_csrf:701  spec_l:728  spec_monkey:767  flow_s1:839  flow_s2:901  flow_s5:984  flow_s3:1097  flow_s4:1172  flow_s6:1243  guide_v132:1299  main:1391  _write:1435
```

### `collect/runner.py` — 1,423줄

```
CollectGroup:67  load_targets:91  collect_groups:104  facet_axes:132  aspect_names:153  check_facet_axes:157  interpret_failure:171  collect_check:200  FailStreak:267  _sleep:301  _log_request:307  _save_issues:318  make_executors:329  _group_of:866  _fuel_of:881  _badge_of:887  _pages_for:893  _dicts:907  _option_medians:943  _market_medians:989  _trim_ladders:1018  _option_base:1035  _site_grade_rules:1065  _listing_config:1078  _listing_values:1103  _option_money:1122  _owned_months:1141  _option_of:1153  _market_of:1161  make_score_executors:1171  make_validate_executor:1352  make_registry_executor:1394
```

### `tests/test_integration.py` — 1,218줄

```
rec:31  Client:41  text:96  links:101  start_server:105  seed_admin:149  m1:165  m2:253  m3:327  m4:631  s3:702  unit:755  gaps:784  flows:892  guide7:993  _account_id:1122  make_users:1129  main:1147  _write_table:1196
```

### `tools/check_src.py` — 1,130줄

```
_spec_files:44  _read_spec:62  say:73  py_files:87  chapter_of:127  _declared_chapters:137  split_done:157  _illustration:176  _retired_config_keys:240  _git:697
```

### `tools/verify_axes.py` — 1,051줄

```
_spec_text:26  spec_tables:58  _num:81  pick:99  _flag:113  hand_market:121  _median_for:132  hand_mileage:152  _years:165  conn_now:174  lookup:179  hand_accident:203  hand_repair:213  hand_owner:221  _warranty_left:229  hand_warranty_general:250  hand_warranty_power:255  hand_site_warranty:261  hand_maker_warranty:291  _km_per_month:318  residual_spec:334  _json:360  hand_option_won:373  hand_depreciation:410  hand_frame:440  hand_outer:461  _leak_states:481  hand_leak:493  hand_lien:508  hand_not_join:518  hand_trim:548  hand_special:568  spec_section:578  spec_head_points:586  lookup_label:593  hand_integrity:601  hand_special_points:627  _taste_points:636  _has_option:647  hand_color:682  hand_usage:706  hand_site_grade:730  hand_inspection_src:750  hand_hud:763  hand_sunroof:772  hand_picked:781  _has_table:794  _option_prices:800  hand_options:818  survey:856  main:919
```

### `store/adminops.py` — 1,037줄

```
QueryLog:55  QueryResult:68  ApiSnapshot:93  DevRequest:104  RecalcJob:119  ScoringPreview:130  ImportPreview:142  ImportResult:159  preview_import:168  import_listings:194  _import_facet:260  BrowserCatch:295  save_browser_catch:303  mark_step_imported:353  pending_enums:384  pending_axis_summary:412  apply_dict_decision:433  _strip_sql:477  sql_reject_reason:484  _opened_tables:518  reject_kind_of:533  columns_hint:543  reap_stale_jobs:566  run_query:601  fetch_api:648  create_dev_request:682  update_dev_status:704  export_dev_requests:718  enqueue_recalc:748  enqueue_after_list_save:774  job_progress:799  db_progress:813  preview_scoring:823  _pt:866  registry_rows:870  registry_counts:881  write_dev_requests:887  dev_request_rows:907  save_api_snapshot:925  get_api_snapshot:948  path_table:967  halt_job:1003
```

### `report/screens/admin.py` — 1,012줄

```
AdminMenuItem:32  AdminHome:62  SaveGate:78  AuditTab:92  AuditView:100  DocView:107  menu_for:118  view_admin_home:130  _todos:155  _recent_runs:195  _recent_changes:226  save_gate:237  view_audit:245  view_docs:291  _doc_files:322  Todo:343  RunRow:357  ChangeRow:367  _cfg_rows:387  config_history:397  query_history:409  db_tables:423  api_snapshots:464  account_activity:475  make_target_key:493  target_choices:512  target_rows:531  parse_import_text:562  status_view:577  _catalog_state:651  _light_result:683  _live_window:723  _live_progress:732  run_progress:779  collect_state:829  received_vs_used:886  dict_state:907  import_state:934  job_log:971  validation_runs:985  blocking_set:1003
```

### `validate/v2_load.py` — 917줄

```
DayGapReport:151  GapCause:164  run:170  _surrogate_key_checks:347  _not_null_check:432  _chained_subscript_check:449  _Boom:497  _salvage_check:505  _table_exists:546  _exception_shape_checks:552  _schema_sync_check:618  _pii_access_check:655  gap_alerts:692  diff_prev_day:708  explain_gap:730  _pii_column_check:762  _secret_key_check:780  _parser_common_fields_check:818  _null_target_not_judged_check:869  _null_target_visible_check:894
```

### `validate/v10_admin.py` — 895줄

```
_sources:212  _admin_guard_checks:233  _sql_strings:278  _schedule_checks:290  _query_error_checks:333  run:432  _session_checks:538  _pii_query_check:618  _scratch:665  _dict_reason_check:680  _dict_source_shown_check:696  _automation_checks:714  _queue_consumer_check:847  _queue_stale_shown_check:876  _ensure_tmp:892
```

### `tools/trace_fill.py` — 840줄

```
spec_lines:94  anchor_step:112  build_symbols:131  enclosing:166  build_texts:176  _stem:214  tokens:223  _best_in:253  _rows:290  layers_of:303  layer_pool:310  _rare_hit:322  axis_words:346  json_key_at:367  _place:394  _hints:405  find_in_layer:421  _best_step_in:469  _layers:500  derive_state:520  src_mark:546  relayer:559  restate:574  fill_file:597  move_to_rules:665  survey:708  lists:736  write_index:757  main:796
```

### `tests/test_score.py` — 800줄

```
check:36  fx:42  snap:46  ctx:66  full_verdict:87  test_denominator:100  test_components_form:144  test_grade:190  test_order_independent:252  panels_of:275  test_history_real:280  test_rental_real:315  test_insurance:357  test_safety_real:382  test_spec_gate:429  test_price_real:489  test_color:562  test_price_pending:582  test_absolute_real:601  test_null_safe:641  test_empty_array_meaning:658  test_peer_group:683  test_damage_by_status:725  test_repair_cost_ratio:751  test_hda_gate:760
```

### `validate/v1_collect.py` — 775줄

```
_axis_empty_check:157  run:187  _endpoint_order_check:320  _empty_db_check:332  _sql_groups:359  _cumulative_codes:395  _run_scope_check:405  _ctx_started:443  _has_run_id:451  _expected_scope_check:456  _diagnosis_scope_check:477  _diagnosis_none_count:515  _query_key_check:538  _entrypoint_parity_check:563  _enclosing_def:592  _run_id_filled_check:601  _catalog_key_check:621  _whole_probe:643  _whole_body_check:654  _catalog_checks:685  _unparsed_envelope_check:732  _ensure_tmp:772
```

### `validate/v4_mapping.py` — 770줄

```
_paths:143  _layer_of:190  _unclassified_split:195  _layer_checks:233  _name_collision_check:327  _key:361  _decide_material_check:367  _blocking_list_check:431  run:488  _mapping_coverage_checks:629  _our_columns:659  _listing_value_scope_check:687  _dict_filled_check:707  _kind_check:718  propose_fix:732  _option_code_check:747  _is_sentence:764
```

### `tests/test_run.py` — 754줄

```
check:36  StubEncar:92  Clock:236  setup:241  test_envelope:279  test_last_page_exact:307  test_facet:314  test_facet_missing_axis:328  test_dict_step:337  test_all_groups:359  test_parse_pipeline:370  test_score_pipeline:474  test_validate:534  test_registry_gate:577  test_target_scope:634  test_catalog_key:666  test_wrapper_args:684  test_unclassified_listing:721
```

### `collect/pipeline.py` — 730줄

```
envelope_scope:41  Reprocess:91  refetch_all:121  reprocess_plan:131  should_refetch:148  expected_for:160  step_report:194  halt_if:210  precheck:243  resume_point:297  config_hash:317  build_run_context_fields:323  stale_rows:332  save_step_report:347  run_step:371  _execute:409  completed_steps:426  run_pipeline:438  print_progress:487  silent_progress:506  from_step_for:520  web_reasons:526  check_recalc_origin:531  plan_recalc:543  _current:560  run_recalc:566  Defect:587  DefectReport:598  diagnose:619  _DiagCtx:643  _collect_defects:653  format_defects:707
```

### `report/render.py` — 723줄

```
_labels:29  _stamp:34  _curve_points:49  _encar_url:92  _why_cheap_of:101  _scoring:142  _penalty_rows:150  _market_pos:161  _site_badge:205  _axis_why:212  _raw_sections:242  _photo_urls:252  _purchase_costs:270  render_listing:298  _option_rows:413  _fetch_views:464  _strengths:479  _weaknesses:486  _pending_best:493  _cost_rows:525  _known_issues:546  _diagnosis_view:564  render_target:575  render_run:656  render_halt:698  _j:716
```

### `store/watch.py` — 679줄

```
AlertConfig:55  WatchItem:68  TrackPoint:83  TrackEvent:98  WatchEvent:112  classify_duplicates:124  sync_duplicates:164  deduped_count:187  watch_add:197  assert_owner:236  watch_update:251  watch_close:271  note_add:292  notes_of:317  note_delete:335  track_snapshot:350  track_points:379  classify_cause:388  detect_events:400  message:458  notify:486  add_watch_query:556  run_watch_queries:591  watch_query_rows:647  close_watch_query:661
```

### `store/admin.py` — 665줄

```
_admin_cfg:46  ConfigChange:68  running_job:86  hash_secret:96  _split:104  create_account:109  account_count:145  needs_bootstrap:149  _recent_failures:161  _log_attempt:180  is_locked:190  unlock_account:205  authenticate:233  open_session:269  session_account:289  change_secret:306  revoke_sessions:330  _walk:341  get_path:365  set_path:370  _atomic_write:377  apply_config:387  _validate_blob:451  revert_config:464  history:488  classify_field:512  account_rows:565  admin_count:579  set_role:586  set_disabled:603  add_config_key:623
```

### `parse/encar/mapping.py` — 621줄

```
_get:30  _json:42  _won:53  _ym:73  _date10:83  _int:99  _bool:105  unpack_envelope:116  parse_list_item:124  parse_detail:171  parse_inspection:247  parse_record:291  _sample_chars:345  safe_field:359  parse_with_issues:381  _salvage:399  _parses:442  dig:449  as_list:472  _diag_comment:500  parse_diagnosis:507  parse_diagnosis_items:539  _text:547  parse_record_summary:557  parse_platform_check:583  parse_inspection_summary:590  parse_ev_battery:595  parse_sellingpoint:615
```

### `tests/test_admin_flow.py` — 566줄

```
check:32  _env:38  _cfg:55  _post:60  _get:65  flow_config:71  flow_scoring:107  _rescore:163  _sum:224  _dist:231  flow_targets:238  flow_registry:273  flow_run:313  flow_query:346  flow_api:372  flow_tools:409  flow_users:431  flow_requests:476  flow_permission:518  main:531
```

### `tools/check_spec.py` — 557줄

```
_read_spec:10  _refs_source:73  _spec_files:284  _guide_files:368  _sections:373  _md:468
```

### `tests/test_admin.py` — 554줄

```
_spec_menu_paths:31  check:46  setup:52  test_bootstrap:64  test_auth:94  test_apply_config:136  test_value_validation:174  test_revert:194  test_no_direct_edit:220  test_classify_field:248  test_run_query:322  test_dev_request:375  test_recalc_and_lock:405  test_admin_screens:439  test_v10:518
```

### `tests/test_web.py` — 505줄

```
check:21  test_routes:28  test_template:77  test_no_logic_in_template:118  test_static_escape:133  test_session_cookie:145  test_error_page:163  test_layout:190  test_filters:219  test_empty_state:242  test_menu_by_role:269  test_guard_and_csrf:286  _call:328  test_screens_render:345  test_sketch_match:436  test_account_policy:451
```

### `report/screens/views.py` — 497줄

```
AxisChip:30  ListingRow:52  ListingFilter:179  WatchRow:210  TargetStat:233  RelaxRow:242  MarketRow:249  ChangeRow:261  AttentionItem:271  ViewerState:279  DashboardView:293  CompareView:317  MarketView:332  DealerRow:347  NotReadyView:368  TodayChange:386  StepRow:398  _min_sample:410  PendingValue:428  Bucket:441  ExcludedGroup:461  ReportFile:470  ReportsView:482
```

### `store/dictionary.py` — 466줄

```
CodeEntry:31  AxisPolicy:57  policy:97  scope_key:105  seed_fixed_enums:130  mapped_of:169  upsert_enum:190  _handle_conflict:242  upsert_option3:263  retire_unseen:299  resolve_code:314  installed_option_names:352  normalize_enum:370  assert_no_unknown:386  bump_dict_version:429  list_pending:439  confirm_enum:447
```

### `contracts.py` — 462줄

```
Response:24  Clock:34  Fetcher:39  Rng:44  Request:52  EndpointSpec:60  FetchResult:71  TargetSpec:84  ListingSnapshot:141  AxisResult:226  Account:245  require_role:262  RunContext:279  StepReport:299  ResumePoint:323  clean_vin:344  total_of:355  RegressionReport:368  json_paths:379  shape_ok:427  shape_violations:460
```

### `web/app.py` — 452줄

```
menu_items:22  _tip:94  _label:99  empty_state:110  banner_of:129  _list_stale:160  static_version:186  build_page:214  check_post:235  redirect:257  take_flashes:277  _display_now:290  make_app:316  _Denied:428  build_context:436  _title_of:451
```

### `tools/build_index.py` — 420줄

```
_py_files:48  _checks_in_code:63  _checks_in_docs:95  last_runs:128  _run_time:157  sort_checks:167  build_checks:184  _outline:246  build_source:257  build_schema:289  build_doc_index:348  main:399
```

### `run.py` — 412줄

```
load:51  make_context:56  _filter_targets:70  _steps_from:89  cmd_collect:103  _grade_summary:171  cmd_admin_create:186  _collect_urls:203  _page_url:240  cmd_web:259  make_worker_ctx:290  make_worker_executors:296  cmd_delegate:334  _api_fetch:345  cmd_setup:355
```

### `tools/sync_registry.py` — 390줄

```
FieldUsage:31  RegistrySyncReport:48  facet_path:66  scan_paths:74  shape_ok:79  _walk_values:92  collect_values:106  collect_paths:130  _has_value:169  _seed_for:185  sync_registry:196  suggest_usage:291  write_suggested:303  halt_report:330  list_by_usage:353  assert_registered:360
```

### `tests/test_pipeline.py` — 388줄

```
check:37  db:43  test_expected:49  test_halt:61  test_reprocess:82  test_refetch:107  test_precheck:115  test_resume_and_version:167  test_run_pipeline:195  test_recalc:230  test_pii_orphan:265  test_exception_becomes_halt:298  test_fixed_enum_bootstrap:319  test_envelope_scope:349
```

### `report/views.py` — 376줄

```
VersionStamp:18  ReportMeta:30  AxisView:40  FinanceView:56  PurchaseCostItem:77  PurchaseCostView:86  DiagnosisView:110  FetchView:122  CostRow:136  ScoreView:145  CollectSummary:224  ClassifySummary:231  PriceSummary:238  AxisStat:247  CoefficientChange:257  DictChangeSummary:267  TargetReport:275  RunStep:287  RunReport:302  HaltReport:313  FixAction:330  NotifyResult:340  ExportResult:353  display_value:362  display_points:372
```

### `tests/test_collect.py` — 368줄

```
check:34  R:40  test_verify_shape:45  _Stub:80  _Clock:88  test_fetch_status:93  test_interpret_failure:106  test_facet_axes:118  test_collect_groups:146  test_build_q:158  test_collect_check:208  test_save_raw:223  test_fail_streak:252  test_all_fail_sample:294  test_diagnosis_scope:338
```

### `tools/light_check.py` — 325줄

```
_repair_max:45  _cfg:63  _run:68  collecting:74  screen_counts:95  db_counts:121  measure:139  index_counts:161  changed:185  _worse:203  failing:207  repair:220  main:253
```

### `tools/render_screens.py` — 321줄

```
_shot_widths:32  _tmp_root:57  main:81  shot_paths:162  _localize_images:187  shoot:224
```

### `validate/v7_watch.py` — 320줄

```
_cols:85  _reads:89  _progress_note_check:117  _relist_check:201  run:227
```

### `tools/build_dict.py` — 317줄

```
DictBuildReport:63  extract_distinct:78  _facet_values:106  facet_value_set:122  _walk_path:141  load_fixed_enums:168  build_dict:176  _mark_facet_substituted:227  build_catalog_dict:251  build_late_dict:289
```

### `validate/v9_multisite.py` — 293줄

```
_sites:69  live_sites:75  _labels:83  _badge_check:98  _hardcoded_badges:133  _origin_check:156  _warranty_sum_check:186  _tie_break_check:211  _axis_site_check:249  run:289
```

### `store/crosssite.py` — 291줄

```
CrossSiteMatch:31  ReadinessReport:41  active_sites:51  match_cross_site:56  site_prices_of:92  rebuild_core_vehicle:109  regression_check:128  snapshot_baseline:159  readiness:183  axes_by_site:227  site_only_axes:249  load_sites:271  site_addition_regression:276
```

### `tests/test_endtoend.py` — 290줄

```
check:31  _own_fields:37  _run:61  flow_pipeline:82  flow_validation:135  flow_config_effect:149  flow_report:207  main:273
```

### `tests/test_dict.py` — 286줄

```
check:39  db:45  test_scope_key:51  test_count_zero:73  test_axis_policy:97  test_conflict:143  test_catalog:178  test_status_version:202  test_classify:219  test_review:248
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

### `tests/test_crosssite.py` — 275줄

```
check:34  db:40  add:45  test_vin:63  test_vin_parse:107  test_cross_site:129  test_regression:168  test_readiness:200  v9_04_site_isolation:222
```

### `tests/test_screens.py` — 274줄

```
check:42  _pipeline:48  test_chip:60  test_listings:83  test_compare:131  test_dashboard_notready:148  test_static_rules:188  test_account:220
```

### `report/exports/export.py` — 269줄

```
filename:26  _stamp_lines:32  listing_md:38  listing_csv:76  halt_md:93  target_md:114  run_md:136  _asdict:186  export:194  output_path:233  write_export:241
```

### `tests/test_watch.py` — 259줄

```
check:30  db:36  add:41  watch:64  test_same_dealer:78  test_cross_dealer:97  test_relist:112  tp:124  test_cause:133  _two_runs:145  test_snapshot:162  test_events:177  test_cause_gate:198  test_message:212
```

### `tests/test_store.py` — 254줄

```
check:40  seed:46  base:52  db:70  test_schema:76  test_key:123  test_null_three:134  test_change_history:141  test_invariant_violation:162  test_snapshot:180  test_dictionary:205
```

### `tools/menu.py` — 254줄

```
_fix_console:28  run:44  cmd_status:52  cmd_setup:56  cmd_dry:74  cmd_collect:81  cmd_facet:118  cmd_dict:123  cmd_screens:128  cmd_migrate:133  cmd_checkall:138  cmd_requests:143  cmd_check_spec:150  cmd_check_src:154  cmd_test:159  main:192
```

### `tests/test_report.py` — 249줄

```
check:33  test_finance:40  test_display:97  _pipeline:113  test_layers:124  test_halt_layer:160  test_export:202
```

### `analyze/axis/state.py` — 245줄

```
_panels:43  _rank_worst:47  _accident:59  _frame:72  _outer:87  _repair:104  _special:115  leak_state:127  _leak:149  _site_never:159  _sites_table:171  _consumable:189  _integrity:211  analyze_state:237
```

### `tests/test_registry.py` — 245줄

```
check:33  fx:39  db:43  put_raw:48  test_paths:57  test_contamination:69  test_seed:95  test_ghost:140  test_v4_06:168  test_seed_reapply:180  test_unclassified_severity:202
```

### `validate/v5_value.py` — 242줄

```
run:60  _grade_ratio_checks:151  _denominator_suite:193
```

### `tests/test_invariants.py` — 232줄

```
check:35  inv1_order_independent:42  inv1_shuffle_100:72  inv2_banned:95  inv5_points:113  put_contract:126  excluded_contract:143  inv3_source_not_null:169  inv4_label_shape:188  inv6_no_unclassified:204
```

### `tools/check_screens.py` — 232줄

```
_pairs:23  say:70  _text:79  check_pairs:86  check_phrases:99  _heads:124  check_sections:143  check_nav:165  check_render:181  main:215
```

### `validate/base.py` — 212줄

```
_cfg:24  Check:55  CheckResult:93  _short:118  result:131  not_applicable:140  save_results:145  gate:162  run_phase:171  canon_files:193  canon_text:206
```

### `web/context.py` — 202줄

```
MenuItem:31  Banner:42  PageContext:51  ErrorPage:88  _is_permission:124  _is_conflict:129  _clean:134  _is_sql_typo:145  error_page:155
```

### `tests/seed.py` — 200줄

```
_cfg:46  build_seed_db:51  _confirm_dict:99  seed_db_path:115  _ensure_secrets:128  _seed_unclassified:144
```

