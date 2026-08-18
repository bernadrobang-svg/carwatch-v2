# 추적표 — 2장 수집

**기능 요구만 둔다. 금지·규칙은 `docs/trace/RULES.md` 로 옮겼다.**

```
층    수집 · 저장 · 파싱 · 사전 · 판정 · 화면 · 검사 · 운영  (S39)
상태  ○ 완료 · ◐ 진행 · ✗ 미착수 · ! 결함 · ? 확인 필요
★ 08-18 정리 — 금지·규칙을 빼고 문구 중복을 합치고 ID 를 다시 매겼다
```


## 목록 수집

| R | 층 | 요구사항 | 출처 | 규격 | 소스 | 화면 | 검사 | 상태 |
|---|---|---|---|---|---|---|---|:--:|
| CO-001 | `[수집]` | 차종별로 목록을 받는다 | `[마스터]` | `10-collect` | `collect/runner.py` | `/admin/run` | V1-01 | ○ |
| CO-002 | `[수집]` | 엔카 `/search/` 가 서울 IP 에서 407 | `[원문]` 262 | `10-collect` | `adapters/kcar.py:6` | /search/ | S10 · S5 | ○ |
| CO-003 | `[수집]` | **브라우저로 받는다** — 마스터 회선 | `[마스터]` 248 | `STEP 136c` | `adapters/kcar.py:5` | `/admin/collect` | V11-47 | ○ |
| CO-004 | `[수집·화면]` | JS 가 바이트를 재서 나눠 보낸다 | `[마스터]` 263 | `STEP 136c` | `web/templates/admin_collect.html` | `/admin/collect` | V11-47 | ○ |
| CO-005 | `[수집]` | **나눌 수 없는 원문은 조각으로** | `[마스터]` 307 | `STEP 136c` | 미구현 | — | V11-98 | ◐ |
| CO-006 | `[수집]` | 범위 — 차종별 · 전 차종 | `[마스터]` 264 | `STEP 136c` | `collect/runner.py::_trim_ladders` | — | V11-48·49 | ◐ |
| CO-007 | `[수집]` | 간격 0 — 사용자 회선은 안 막힌다 | `[마스터]` 265 | `B-config` | `collect/pipeline.py::envelope_scope` | `/admin/collect` | 검사 없음 | ◐ |
| CO-008 | `[수집]` | **중단해도 이어서 받는다** | `[마스터]` | `STEP 52` | `collect/runner.py` | — | 검사 없음 | ◐ |
| CO-009 | `[수집]` | 기본은 전건 재요청 — `--resume` 만 건너뜀 | `[판단]` | `STEP 52` | `collect/pipeline.py::diagnose` | — | 검사 없음 | ◐ |
| CO-010 | `[수집]` | 사라진 매물을 지우지 않는다 | `[마스터]` | `11-store` | `adapters/encar.py:7` | 해당 없음 | 검사 없음 | ◐ |
| CO-011 | `[수집]` | 목록 수집 — 가격 변동을 남긴다 | `[마스터]` | `11-store` | `collect/runner.py:2` | 목록 「변동」 | 검사 없음 | **!** |

## 상세 수집

| R | 층 | 요구사항 | 출처 | 규격 | 소스 | 화면 | 검사 | 상태 |
|---|---|---|---|---|---|---|---|:--:|
| CO-012 | `[수집]` | 상세 수집 — 상세 4종을 받는다 | `[원문]` | `10-collect` | `collect/runner.py::make_executors` | `/admin/run` | V1-02 | ○ |
| CO-013 | `[수집]` | `?include=` 를 붙이지 않는다 | `[원문]` | `E-attach` | 미구현 | — | 검사 없음 | ✗ |
| CO-014 | `[수집]` | 상세 수집 — **새 5종을 받는다** | `[원문]` 296 | `ENCAR_API` | `collect/runner.py::make_executors` | — | 검사 없음 | ◐ |
| CO-015 | `[수집]` | `record/summary` — 용도 · 전손 · 침수 | `[원문]` 296 | `ENCAR_API` | 미구현 | — | 검사 없음 | ◐ |
| CO-016 | `[수집]` | `clean-encar` — 엔카 진단 | `[원문]` 296 | `ENCAR_API` | `config/endpoints.json::encar.paths.platform_check` | — | 검사 없음 | **!** |
| CO-017 | `[수집]` | `ev-battery` — 배터리 SOH | `[원문]` 318 | `ENCAR_API` | `config/endpoints.json::encar.paths.ev_battery` | — | 검사 없음 | **!** |
| CO-018 | `[수집]` | **로그인 리포트** — 틴팅 · 키 · 타이어 | `[원문]` 296 | `ENCAR_API` | `collect/pipeline.py::run_step` | `/admin/collect` | 검사 없음 | **!** |
| CO-019 | `[수집]` | 카탈로그 — 조합 전수 | `[마스터]` 327 | `10-collect` | `adapters/encar.py::catalog_url` | `/admin/status` | V1-23·24 | **!** |
| CO-020 | `[수집]` | 상세 수집 — 못 받은 사유를 기록 | `[마스터]` 327 | `10-collect` | `collect/runner.py::interpret_failure` | — | 검사 없음 | ◐ |

## 자동화

| R | 층 | 요구사항 | 출처 | 규격 | 소스 | 화면 | 검사 | 상태 |
|---|---|---|---|---|---|---|---|:--:|
| CO-021 | `[저장]` | **저장하면 나머지가 이어서 돈다** | `[마스터]` 314 | `STEP 136g` | `store/pii.py::plate_use_char` | `/admin/status` | V10-26·27 | ○ |
| CO-022 | `[운영]` | 자동화 — 매일 04:00 자동 | `[마스터]` 315 | `STEP 136h` | 미구현 | — | V10-28 | ◐ |
| CO-023 | `[운영]` | 목록이 오래되면 알린다 | `[마스터]` 316 | `STEP 136i` | `tools/build_dict.py::build_dict` | 머리말 | V11-103 — 검사 없음(규격에만) | ✗ |
| CO-024 | `[수집]` | **재수집·재파싱·재판정을 가른다** | `[마스터]` 317 | `STEP 136h` | `collect/pipeline.py:36` | `/admin/tools` | V10-29·30 | ○ |
| CO-025 | `[운영]` | 상세는 오래된 것만 다시 | `[판단]` 317 | `B-config` | `web/views.py::listings` | `/listings` | 검사 없음 | ◐ |

## 원문 보존

| R | 층 | 요구사항 | 출처 | 규격 | 소스 | 화면 | 검사 | 상태 |
|---|---|---|---|---|---|---|---|:--:|
| CO-026 | `[수집]` | 받은 그대로 둔다 (P3) | `[마스터]` | `01_raw.sql` | 미구현 | `/watch` | V1-05 | ○ |
| CO-027 | `[수집]` | 밖에서 받은 것은 `run_id` 로 고른다 | `[마스터]` 268 | `10-collect` | `collect/runner.py::FailStreak` | — | V1-21 | ◐ |
| CO-028 | `[수집]` | `origin` 4종 — collector·manual·import·browser | `[마스터]` 252 | `01_raw.sql` | `collect/runner.py::s4` | — | V11-43 | ◐ |
| CO-029 | `[수집]` | 목록 반입 — 밖에서 받은 것을 넣는다 | `[마스터]` 244 | `STEP 136a` | `collect/runner.py::s4` | `/admin/import` | S10 · S5 | ○ |

## 다중 사이트

| R | 층 | 요구사항 | 출처 | 규격 | 소스 | 화면 | 검사 | 상태 |
|---|---|---|---|---|---|---|---|:--:|
| CO-030 | `[수집]` | 어댑터로 사이트를 늘린다 | `[마스터]` | `50-multisite` | `adapters/base.py` | 해당 없음 | 검사 없음 | ◐ |
| CO-031 | `[수집]` | **K카** — 서버에서 200 | `[원문]` | `KCAR_API` | `adapters/kcar.py::KcarAdapter` | — | 검사 없음 | ✗ |
| CO-032 | `[수집]` | 다중 사이트 — K카 XHR 6경로 | `[원문]` | `KCAR_API` | `adapters/kcar.py:4` | — | 검사 없음 | **!** |
| CO-033 | `[수집]` | `source_id` 가 문자를 받는다 | `[원문]` 310 | `50-multisite` | `adapters/kcar.py::KcarAdapter` | 해당 없음 | V9-05 — 검사 없음(규격에만) | ◐ |
| CO-034 | `[저장]` | **차대번호로 같은 차를 잇는다** | `[원문]` | `50-multisite` | `store/core.py::build_identities` | 해당 없음 | 검사 없음 | ✗ |
| CO-035 | `[운영]` | 사이트마다 주는 것이 다르다 | `[판단]` 309 | `50-multisite` | `web/views.py::_watch_invite` | 해당 없음 | V9-01~03 — 검사 없음(규격에만) | ◐ |
| CO-036 | `[화면]` | 다중 사이트 — 화면에 출처를 낸다 | `[마스터]` 311 | `50-multisite` | `config/labels.json::AXIS_LABELS.warranty.site` | 목록 사이트 열 | V9-06·07 | ○ |
| CO-037 | `[운영]` | 다중 사이트 — **K카 직영은 최고급** | `[마스터]` 312 | `50-multisite` | `tools/trace_fill.py::json_key_at` | 해당 없음 | V9-08·09 — 검사 없음(규격에만) | ◐ |
