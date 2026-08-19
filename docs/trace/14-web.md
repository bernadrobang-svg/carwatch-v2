# 추적표 — 14장 화면

**기능 요구만 둔다. 금지·규칙은 `docs/trace/RULES.md` 로 옮겼다.**

```
층    수집 · 저장 · 파싱 · 사전 · 판정 · 화면 · 검사 · 운영  (S39)
상태  ○ 완료 · ◐ 진행 · ✗ 미착수 · ! 결함 · ? 확인 필요
★ 08-18 정리 — 금지·규칙을 빼고 문구 중복을 합치고 ID 를 다시 매겼다
```


## 공통 — 폭 · 크기 · 줄 수

| R | 층 | 요구사항 | 출처 | 규격 | 소스 | 화면 | 검사 | 상태 |
|---|---|---|---|---|---|---|---|:--:|
| WB-001 | `[화면]` | **가변형 반응형** — 값을 버리지 않는다 | `[마스터]` 278 | `61-web/a-common` | 미구현 | 전 화면 | V11-70·71 | ✗ |
| WB-002 | `[화면]` | 세 단계 — 넓음 표 · 중간 묶음 · 좁음 카드 | `[마스터]` 278 | `61-web/a-common` | ~ `web/views.py::recommend` | `/recommend` | V11-114 | **!** |
| WB-003 | `[화면]` | **폭 다섯에서 재고 찍는다** | `[마스터]` 337 | `61-web/f-width` | ~ `report/screens/views.py::Bucket` | 화면 없음 | V11-113 | **!** |
| WB-004 | `[화면]` | 어느 폭에서도 글자가 세로로 안 떨어진다 | `[마스터]` 337 | `61-web/f-width` | ~ `web/templates/recommend.html` | `/recommend` | V11-115 | **!** |
| WB-005 | `[화면]` | 공통 — 폭 · 크기 · 줄 수 — 넓으면 더 보여 준다 | `[마스터]` 278 | `61-web/a-common` | ~ `web/server.py:44` | 화면 없음 | 검사 없음 | ◐ |
| WB-006 | `[판정·화면]` | **사진 크기** — ★ 정본은 `61-web/a-common.md` 사진 크기 표 하나다 | `[마스터]` 332 · 368 · 404 | `61-web/a-common` | ~ `report/screens/build.py::recommend_reason` | 화면 없음 | V11-107 | ◐ |
| WB-007 | `[화면]` | 사진 최소 128px — 좁아도 안 줄인다 | `[마스터]` 281 | `61-web/a-common` | ✓ `web/static/app.css` | 화면 없음 | V11-80 | ◐ |
| WB-008 | `[화면]` | 한 화면에 매물 2개 이상 | `[마스터]` 332 | `61-web/a-common` | ~ `web/views.py::listings` | `/listings` | V11-108 | ◐ |
| WB-009 | `[화면]` | 공통 — 폭 · 크기 · 줄 수 — JS 없이 돈다 | `[기술]` 248 | `61-web` | ~ `web/views.py::_unclassified_split` | 화면 없음 | 검사 없음 | ◐ |
| WB-010 | `[화면]` | 공통 — 폭 · 크기 · 줄 수 — 색 12 · 글꼴 2 | `[기술]` | `61-web` | ✓ `web/static/app.css` | 화면 없음 | 검사 없음 | ◐ |
| WB-011 | `[화면]` | **CSS 에 지문을 붙인다** — 캐시 | `[마스터]` | `61-web` | ✓ `web/app.py::static_version` | 화면 없음 | V11-82 | ◐ |

## 시안 — [마스터] 층

| R | 층 | 요구사항 | 출처 | 규격 | 소스 | 화면 | 검사 | 상태 |
|---|---|---|---|---|---|---|---|:--:|
| WB-012 | `[화면]` | 시안 — [마스터] 층 — **시안이 정본이다** | `[시안]` 275 | `61-web` | ~ `web/views.py::page_extras` | 전 화면 | V11-59 | ◐ |
| WB-013 | `[화면]` | 시안 구조를 표로 바꾸지 않는다 | `[시안]` 275 | `61-web` | ~ `report/screens/build.py::_bulk_spark` | 화면 없음 | V11-60 | ◐ |
| WB-014 | `[화면]` | **v1 원본이 더 앞선다** | `[시안]` 277 | `61-web` | ~ `report/screens/build.py` | 화면 없음 | V11-68·69 | ◐ |
| WB-015 | `[화면]` | v1 22열 · 축을 열로 | `[시안]` 277 | `61-web/b-list` | 미구현 | 목록 | V11-68 | ✗ |
| WB-016 | `[화면]` | v1 조작 — 단추·드롭다운·미리보기 | `[시안]` 277 | `61-web` | ~ `web/views.py::_order_menu` | 화면 없음 | V11-69 | ◐ |

## 목록 /listings

| R | 층 | 요구사항 | 출처 | 규격 | 소스 | 화면 | 검사 | 상태 |
|---|---|---|---|---|---|---|---|:--:|
| WB-017 | `[운영]` | 목록 /listings — **목록은 요약이다** | `[마스터]` 303 | `61-web/b-list` | ~ `web/views.py::listings` | `/listings` | V11-93 — 검사 없음(규격에만) | **!** |
| WB-018 | `[화면]` | 22열 · 폭(px) 지정 | `[시안]` 332 | `61-web/b-list` | ~ `config/labels.json::AXIS_LABELS.taste.picked` | 화면 없음 | 검사 없음 | ◐ |
| WB-019 | `[판정]` | 목록 /listings — **시세 대비 %** | `[마스터]` 283 | `61-web/b-list` | ✓ `report/screens/build.py::_row` | 10열 | 검사 없음 | ◐ |
| WB-020 | `[화면]` | 목록 /listings — **신차가 대비 %** | `[마스터]` 283 | `61-web/b-list` | ~ `web/templates/recommend.html` | 11열 | 검사 없음 | ◐ |
| WB-021 | `[운영]` | 옵션 「4종 715만」 | `[마스터]` 313 | `61-web/b-list` | ~ `tools/verify_axes.py::main` | 18열 | V11-100 — 검사 없음(규격에만) | ◐ |
| WB-022 | `[판정]` | 목록 /listings — 트림에 세부등급 | `[마스터]` 285 | `61-web/b-list` | ✓ `report/screens/build.py::_row` | 7열 | V11-85 — 검사 없음(규격에만) | ◐ |
| WB-023 | `[판정]` | **축은 상태로** — 있음·없음·? | `[마스터]` 280 | `61-web/b-list` | ~ `analyze/axis/state.py:2` | `/admin/import` | V11-79 | ◐ |
| WB-024 | `[판정]` | 목록 /listings — 보증은 남은 기간으로 | `[마스터]` 283 | `61-web/b-list` | ~ `config/scoring.json::components.warranty.general` | — | 검사 없음 | ◐ |
| WB-025 | `[판정]` | 사고는 회수 · 보험은 자차 수리비 | `[마스터]` 283 | `61-web/b-list` | ~ `analyze/absolute.py:19` | — | V3-42 · V3-43 | ◐ |
| WB-026 | `[운영]` | 목록 /listings — **♡ 를 제목 줄에** | `[마스터]` 305 | `61-web/b-list` | ~ `web/views.py::listings` | `/recommend` | V11-96 — 검사 없음(규격에만) | ◐ |
| WB-027 | `[저장·화면]` | 링크 — 딜러·연식·주행·가격·월납·상태 | `[마스터]` 276 | `61-web/b-list` | ~ `web/views.py:384` | 화면 없음 | V11-61 | ◐ |
| WB-028 | `[화면]` | 목록 /listings — 툴팁 — 코드·줄임말 | `[마스터]` 276 | `61-web/b-list` | ~ `web/views.py::listings` | 화면 없음 | V11-62 | ◐ |
| WB-029 | `[화면]` | 목록 /listings — **엔카 원문 링크** | `[마스터]` 276 | `STEP 149q` | ~ `web/views.py::admin_collect` | `/admin/collect` | V11-63 | ◐ |
| WB-030 | `[화면]` | 필터를 위에 · 단추 on/off | `[마스터]` 276 | `STEP 149t` | ~ `web/views.py::listings` | `/listings` | V11-66·67 | ◐ |
| WB-031 | `[화면]` | 기본 정렬 · 「A 이상만」 | `[마스터]` 276 | `STEP 149s` | ~ `web/views.py::listings` | `/listings` | V11-65 | ◐ |
| WB-032 | `[화면]` | 전체 건수 · 쪽 넘김 | `[마스터]` 332 | `61-web/b-list` | ~ `web/views.py::_points` | 화면 없음 | V11-55 | ◐ |
| WB-033 | `[수집]` | 목록 /listings — 사이트 배지 | `[마스터]` 311 | `50-multisite` | ~ `collect/pipeline.py::expected_for` | 21열 | V9-06 | ◐ |
| WB-034 | `[저장]` | **행 어디를 눌러도 상세로** | `[마스터]` 338 | `61-web/f-width` | ✓ `web/templates/listings.html` | `/watch` | V11-116 | **!** |
| WB-035 | `[화면]` | **손대면 미리보기 (터치)** | `[마스터]` 338 | `61-web/f-width` | ✓ `web/templates/listings.html` | 화면 없음 | V11-117 | **!** |
| WB-036 | `[판정·화면]` | 계산식을 목록에 안 낸다 | `[마스터]` 332 | `61-web/e-compare` | ~ `web/templates/listings.html` | `/listings` | 검사 없음 | **!** |
| WB-037 | `[화면]` | 목록 /listings — 「—」 를 안 쓴다 | `[마스터]` 332 | `61-web/e-compare` | ~ `web/views.py::listings` | 화면 없음 | V11-106 | **!** |

## 추천 /recommend

| R | 층 | 요구사항 | 출처 | 규격 | 소스 | 화면 | 검사 | 상태 |
|---|---|---|---|---|---|---|---|:--:|
| WB-038 | `[판정·화면]` | 추천 /recommend — **추천 이유를 낸다** | `[마스터]` 304 | `61-web/c-recommend` | ~ `web/views.py::recommend` | `/recommend` | V11-95 | ◐ |
| WB-039 | `[판정]` | 추천 /recommend — 조건을 한 줄로 | `[마스터]` 304 | `61-web/c-recommend` | ✓ `web/templates/recommend.html` | `/recommend` | V11-94 — 검사 없음(규격에만) | ◐ |
| WB-040 | `[화면]` | 이유를 못 대면 추천 안 한다 | `[마스터]` 304 | `61-web/c-recommend` | ✓ `report/screens/build.py::view_recommend` | `/recommend` | V11-109 | ○ |
| WB-041 | `[판정·화면]` | 추천 /recommend — 순위·차종 단추 | `[시안]` 304 | `61-web/c-recommend` | ~ `web/views.py::recommend` | `/listings` | 검사 없음 | ◐ |
| WB-042 | `[판정·화면]` | 추천 /recommend — 사진이 목록보다 작다 (`a-common` 표 — 80/72/64) | `[마스터]` 332 · 368 | `61-web/a-common` | ~ `web/views.py::recommend` | 화면 없음 | V11-107 | ◐ |
| WB-043 | `[판정·화면]` | 추천 /recommend — 카드 8줄 이내 | `[마스터]` 332 | `61-web/c-recommend` | ~ `web/views.py::recommend` | 화면 없음 | V11-109 | ◐ |

## 상세 /why

| R | 층 | 요구사항 | 출처 | 규격 | 소스 | 화면 | 검사 | 상태 |
|---|---|---|---|---|---|---|---|:--:|
| WB-044 | `[운영]` | 상세 /why — 절 순서 10개 | `[마스터]` 332 | `61-web/d-detail` | ~ `web/views.py:318` | — | V11-110 | ◐ |
| WB-045 | `[화면]` | 상세 /why — **② 값이 가장 크다** | `[마스터]` 332 | `61-web/d-detail` | ~ `report/screens/build.py:59` | 화면 없음 | 검사 없음 | ◐ |
| WB-046 | `[화면]` | 상세 /why — **왜 싼가 절** | `[마스터]` 299 | `61-web/d-detail` | ~ `report/views.py::ScoreView` | 화면 없음 | V3-52 | ◐ |
| WB-047 | `[수집]` | 조회 표 — 안 부른 것 ↔ 못 받은 것 | `[마스터]` | `61-web/d-detail` | ✓ `store/core.py::raw_sections` | `/admin/collect` | 검사 없음 | ◐ |
| WB-048 | `[판정]` | 상세 /why — 축별 24축 | `[마스터]` 329 | `61-web/d-detail` | ✓ `report/render.py::render_listing` | — | 검사 없음 | ◐ |
| WB-049 | `[판정]` | 확인율은 근거 있는 축만 | `[마스터]` 325 | `61-web/d-detail` | ~ `score/scorer.py::score` | — | V3-65 | **!** |
| WB-050 | `[판정]` | 상세 /why — 옵션 전체 · 가격 | `[마스터]` 313 | `61-web/d-detail` | ~ `analyze/axis/trim.py:10` | — | V11-101 | ◐ |
| WB-051 | `[판정·화면]` | 상세 /why — **시세 위치 차트** | `[마스터]` 340 | `61-web/g-chart` | ~ `report/render.py::render_listing` | 화면 없음 | V11-119 | **!** |
| WB-052 | `[판정·화면]` | 상세 /why — 감가 곡선 위의 점 | `[마스터]` 340 | `61-web/g-chart` | ~ `report/views.py::ScoreView` | `/why/{listing_id}` | V11-119 | **!** |

## 차트

| R | 층 | 요구사항 | 출처 | 규격 | 소스 | 화면 | 검사 | 상태 |
|---|---|---|---|---|---|---|---|:--:|
| WB-053 | `[화면]` | 차트 — 가격 분포 히스토그램 | `[시안]` 275 | `61-web/g-chart` | ~ `web/context.py::PageContext` | `/market` | V11-77 | ◐ |
| WB-054 | `[판정·화면]` | 차트 — **감가 곡선** | `[마스터]` 340 | `61-web/g-chart` | ✓ `report/render.py::_curve_points` | `/market` | V11-119 | **!** |
| WB-055 | `[판정·화면]` | 차트 — **등급 분포 · 차종별** | `[마스터]` 340 | `61-web/g-chart` | ~ `web/templates/dashboard.html` | `/` | V11-119 | **!** |
| WB-056 | `[화면]` | 차트 — 딜러 4분면 | `[시안]` 275 | `61-web/g-chart` | ~ `web/templates/dealers.html` | `/dealers` | V11-77 | ◐ |
| WB-057 | `[화면]` | 차트 — 가격 추이 선 | `[시안]` 275 | `61-web/g-chart` | ~ `web/templates/watch.html` | `/watch` | V11-77 | ◐ |
| WB-058 | `[판정·화면]` | 차트 — 후보 점수 막대 | `[시안]` 275 | `61-web/g-chart` | ~ `web/templates/dashboard.html` | `/recommend` | V11-77 | ◐ |
| WB-059 | `[화면]` | 차트가 없으면 왜 없는지 | `[마스터]` 340 | `61-web/g-chart` | ~ `report/render.py::_market_pos` | 화면 없음 | V11-119 | ◐ |

## 시세 · 딜러 · 관심 · 비교

| R | 층 | 요구사항 | 출처 | 규격 | 소스 | 화면 | 검사 | 상태 |
|---|---|---|---|---|---|---|---|:--:|
| WB-060 | `[판정]` | **시세를 제조사·차종·트림으로 고른다** | `[마스터]` | `61-web` | ~ `analyze/axis/value.py::_market` | `/market` | V11-83 | ◐ |
| WB-061 | `[판정·화면]` | 시세 · 딜러 · 관심 · 비교 — 트림별로 시세를 낸다 | `[마스터]` 285 | `61-web` | ~ `report/screens/views.py::ListingRow` | `/market` | V11-86 | ◐ |
| WB-062 | `[판정]` | 시세 · 딜러 · 관심 · 비교 — **딜러 보유 차종** | `[마스터]` 276 | `41-view` | ~ `analyze/peer.py:8` | `/dealers` | 검사 없음 | **!** |
| WB-063 | `[판정·화면]` | 시세 · 딜러 · 관심 · 비교 — **관심에 사진·차종** | `[마스터]` 284 | `42-watch` | ~ `web/templates/recommend.html` | `/watch` | V7-12 | **!** |
| WB-064 | `[판정·화면]` | 관심 행 전체가 상세 링크 | `[마스터]` 284 | `42-watch` | ~ `web/views.py::_points` | 화면 없음 | V7-13 | ◐ |
| WB-065 | `[화면]` | 시세 · 딜러 · 관심 · 비교 — **비교는 차이만** | `[마스터]` 313 | `61-web/e-compare` | ✓ `web/templates/compare.html` | `/compare` | V11-102 | ○ |
| WB-066 | `[사전]` | 매물 화면 다섯이 같은 값 | `[마스터]` 284 | `61-web` | ✓ `report/screens/views.py::AxisChip` | — | V11-84 | ○ |

## 관리 화면

| R | 층 | 요구사항 | 출처 | 규격 | 소스 | 화면 | 검사 | 상태 |
|---|---|---|---|---|---|---|---|:--:|
| WB-067 | `[화면]` | 관리 화면 — 메뉴에 이름을 낸다 | `[마스터]` 276 | `60-admin` | ~ `web/app.py:52` | 전 화면 | V11-54 | ◐ |
| WB-068 | `[화면]` | **차종 추가를 드롭다운으로** | `[마스터]` 276 | `STEP 149r` | ~ `web/views.py::admin_targets` | `/admin/targets` | V11-64 | **!** |
| WB-069 | `[사전·화면]` | **사전 확정을 축별로 접는다** | `[마스터]` 276 | `STEP 136e` | ~ `web/templates/admin_dict.html` | `/admin/dict` | V11-78 | ◐ |
| WB-070 | `[화면]` | 관리 표를 좁은 폭에서 카드로 | `[마스터]` 276 | `60-admin` | ~ `web/templates/market.html` | `/market` | 검사 없음 | ◐ |
| WB-071 | `[화면]` | 관리 화면 — 관리 화면에 툴팁 | `[마스터]` 276 | `60-admin` | ✓ `web/templates/admin.html` | 화면 없음 | V11-62 | **!** |
| WB-072 | `[저장]` | 진행 모니터는 읽기 전용 | `[마스터]` 272 | `STEP 136f` | ~ `store/adminops.py::preview_import` | `/admin/status` | V11-51 | ◐ |
| WB-073 | `[화면]` | 관리 화면 — 큐만 보지 않는다 | `[마스터]` 273 | `STEP 136f` | ✓ `report/screens/admin.py::view_status` | `/admin/status` | V11-53 | ○ |
