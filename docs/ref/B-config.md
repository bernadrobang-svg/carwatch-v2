# 부록 B. `config` 파일 예시

**본문 STEP 6 의 「config 키 전량」 표가 정본이다. 아래는 형태를 보이는 발췌다.**

### config 파일 예시 — 형태를 본문에 둔다

**키 목록만 있으면 구조를 알 수 없다. 중첩·타입·초기값을 함께 낸다.**

```
★ 예시는 발췌다.  값의 정본이 아니다
  targets.json      10차종 중 2건만
  price_curve       STEP 71 표가 정본.  예시는 구간 형태만 보인다
  insurance_cost_curve  STEP 77 표가 정본
  coefficient       10차종 중 3건만

필수   값이 갈리면 STEP 본문 표를 따른다.  예시가 아니다
검사   「예시에 있는데 파일에 없다」만 실패로 본다.  파일이 더 많은 것은 정상
```

#### `config/sites.json`

```json
{
  "encar":       {"label": "엔카",     "status": "active",  "order": 1},
  "kcar":        {"label": "K카",      "status": "planned", "order": 2},
  "kbchachacha": {"label": "KB차차차",  "status": "planned", "order": 3},
  "dealer_site": {"label": "딜러 자체", "status": "planned", "order": 9,
                  "multi_instance": true}
}
```

#### `config/endpoints.json`

```json
{
  "encar": {
    "base_url": "https://api.encar.com",
    "paths": {
      "list":       "/search/car/list/mobile",
      "detail":     "/v1/readside/vehicle/{source_id}",
      "inspection": "/v1/readside/inspection/vehicle/{source_id}",
      "record":     "/v1/readside/record/vehicle/{source_id}/open",
      "diagnosis":  "/v1/readside/diagnosis/vehicle/{source_id}",
      "catalog":    "/v1/readside/vehicles/car/{source_id}/options/choice"
    },
    "headers": {"User-Agent": "<실측 필요>"},
    "interval_sec": [0.1, 0.1],
    "timeout_sec": 15.0,
    "retry_max": 2
  }
}
```

#### `config/targets.json` — 1건만 예시

```json
{
  "G80_25T": {
    "label": "G80 2.5T",
    "collect_group": "encar:G80",
    "site_query": {"encar": {"CarType": "Y", "Manufacturer": "제네시스",
                             "ModelGroup": "G80"}},
    "year_range": "202100..",
    "price_range": "..6000",
    "fuel_match": ["가솔린"],
    "trim_include": ["2.5"],
    "displacement_range": [2400, 2600]
  },
  "MODEL_Y": {
    "label": "테슬라 모델Y",
    "collect_group": "encar:MODEL_Y",
    "site_query": {"encar": {"CarType": "N", "Manufacturer": "테슬라",
                             "ModelGroup": "모델 Y"}},
    "year_range": "202200..",
    "price_range": "..6000",
    "fuel_match": ["전기"],
    "trim_include": [],
    "displacement_range": null
  }
}
```

```
★ CarType   국산 Y · 수입 N.  모델Y 만 N 이다 (STEP 17a)
★ 전기차    displacement_range 는 null.  배기량 분류를 쓰지 않는다 (STEP 46)
★ collect_group  같으면 1회만 수집한다.  G80_25T 와 G80_EV 가 공유한다
```

#### `config/depreciation.json` — 첫 수집 후 생성

```json
{
  "_source": "실수집 결과에서 산출 (STEP 70)",
  "curve": {"0": 0.829, "1": 0.824, "2": 0.788,
            "3": 0.710, "4": 0.620, "5": 0.589},
  "curve_beyond": 0.589,
  "coefficient": {"G80_25T": 1.053, "MODEL_Y": 0.977, "KOLEOS_HEV": 0.970},
  "curve_min_sample": 100,
  "coefficient_change_limit": 0.10,
  "coefficient_min_sample": 30,
  "coefficient_max_iter": 3,
  "coefficient_sane_range": [0.80, 1.20]
}
```

```
★ 위 숫자는 v1 관측 초기값이다.  첫 실수집 후 STEP 64 절차로 재산출한다
★ 계수가 sane_range 밖이면 그 차종의 가격 축을 excluded 로 둔다 (STEP 70)
```

#### `config/finance.json` — 마스터 확정

```json
{
  "down_payment_won": 15000000,
  "loan_months": 48,
  "loan_rate_annual": 0.055,
  "repay_method": "equal_installment",
  "tax_acquisition_rate": 0.07,
  "bond_table": {},
  "fee_stamp": 0,
  "fee_transfer": 0,
  "fee_delivery": 0,
  "fee_tinting": 0,
  "ev_tax_exempt": ["MODEL_Y", "GV60", "G80_EV", "GV70_EV"],
  "hold_months": 48,
  "_estimated": ["bond_table", "fee_stamp", "fee_transfer",
                 "fee_delivery", "fee_tinting"]
}
```

```
★ 선납금은 취득 부대비용을 포함한다 (9장 금융)
  선납금을 부대비용에 먼저 배분한다.  차값 선납 = 선납금 − 부대비용
  할부 원금 = 표시가 − 차값 선납
★ _estimated 에 든 키는 화면에 「미확정」으로 표시한다
```

#### `config/scoring.json` — 구조만

```json
{
  "calc_version": "c1",
  "total_points": 910,
  "components": {
    "_note": "값이 배점. {\"points\": N, \"skipped\": true} 형태도 허용",
    "price": 200,
    "warranty.general": 50, "warranty.power": 50,
    "spec.hud": 20, "spec.sunroof": 20,
    "spec.svm": 10, "spec.scc": 10, "spec.bsd": 5, "spec.tinting": 5,
    "history.damage": 20, "history.insurance": 15, "history.rental": 20,
    "safety.diagnosis": 20, "safety.warranty_product": 20,
    "color": 40, "mileage": 30
  },
  "_component_form": "값이 배점. {\"points\": N, \"skipped\": true} 형태도 허용 (STEP 128)",
  "admin": {
    "query_row_limit": 1000,
    "query_timeout_sec": 10,
    "schedule": {"collect": "daily 06:00"}
  },
  "grade_cuts": {"S": 0.90, "A": 0.80, "B": 0.70, "C": 0.60},
  "min_denominator_ratio": 0.60,
  "price_curve": [[-0.25, 200], [-0.15, 160], [-0.05, 120],
                  [0.0, 100], [0.05, 70], [0.10, 40], [0.15, 10],
                  [0.25, -40]],
  "peer_year_window": 1,
  "peer_mileage_window": 10000,
  "peer_min_sample": 10,
  "axis_rules": {
    "warranty": {"full_months": 24, "expire_penalty": -15, "km_per_month": 1250},
    "history":  {"insurance_cost_curve": [[0.0, 15], [0.02, 13], [0.04, 11],
                                          [0.07, 8], [0.10, 5], [0.15, 2]],
                 "insurance_cap_by_count": {"0": 15, "1": 12, "2": 9, "3": 6}},
    "mileage":  {"full_km": 40000, "zero_km": 100000},
    "safety":   {"warranty_product_na_targets":
                 ["MODEL_Y", "GV60", "G80_EV", "GV70_EV"]},
    "absolute_fail": {"repair_cost_ratio": 0.139,
                      "frame_ranks": ["RANK_A", "RANK_B", "RANK_C"],
                      "outer_ranks": ["RANK_ONE", "RANK_TWO"]}
  }
}
```

```
★ components 17개.  합이 total_points 와 같아야 한다 (check_spec ⑦)
★ repair_cost_ratio 0.139 는 p90 이다.  「상위 10% 를 뺀다」가 정책이다
  전 차종 수집 후 같은 분위수로 재산출한다 (STEP 82)
```

#### `config/warnings.json` — 첫 수집 후

```json
{
  "price_anomaly_sigma": null,
  "price_low_pct": null,
  "relist_count": null,
  "relist_window_days": null,
  "dealer_trust_floor": null
}
```

```
★ null 이면 그 경고를 발생시키지 않는다.  0 으로 채우지 않는다
  분포를 봐야 임계가 정해진다 (STEP 82d)
```

#### `config/field_usage.json` — 등록부 시드 (8장 STEP 87)

```json
{
  "seed": {
    "list:HomeServiceVerification": {
      "usage": "unused_by_policy",
      "reason": "엔카 배송 서비스 이용 여부. 차량 품질이 아니다"
    },
    "inspection:inners[]": {
      "usage": "display_only",
      "reason": "내부 점검 40종. 전건 「양호」로 변별력 0"
    },
    "diagnosis:*": {
      "usage": "blocked",
      "reason": "진단 API 원문 0건",
      "unblock_condition": "진단 API 재수집 후 경로 전수"
    }
  },
  "default": "unclassified",
  "ghost_miss_limit": 3
}
```

```
★ field_usage.suggested.json 은 생성물이다.  sync_registry 가 낸다
  사람이 확인·수정해 이 파일로 옮긴다.  코드가 옮기지 않는다
```

#### `config/dealer_trust.json` — 첫 수집 후

```json
{
  "weights": {
    "relist_rate": null,
    "price_up_rate": null,
    "drop_event_rate": null,
    "price_volatility": null,
    "median_dom_days": null,
    "info_score": null
  },
  "min_sample": null
}
```

```
★ null 이면 trust_score 를 산출하지 않는다.  0 으로 채우지 않는다
  지표 분포를 봐야 가중치가 정해진다 (7장 STEP 82c)
```

#### `config/dictionaries/` — 생성물

```
tint_keywords.json      틴팅 브랜드 (7장 STEP 75)
option3.json            3자리 코드 → 옵션명
enum_{axis}.json        연료 · 색상 · 트림 · 부위 · 상태
```

```
★ tools/build_dict.py 가 RAW 에서 만든다.  손으로 적지 않는다 (4장 STEP 42)
  status 4종 — confirmed · pending · retired · (unknown 은 없다)
```

#### `config/web.json`

```json
{
  "host": "127.0.0.1",
  "port": 8765,
  "session_cookie": "cw_session",
  "session_max_age_sec": 43200,
  "signup_policy": "closed",
  "static_max_age_sec": 3600,
  "flash_max": 5,
  "max_form_bytes": 65536,
  "rows_per_page": 200,
  "max_queries_per_request": 20
}
```

```
★ 09 키.  14장 STEP 141 의 키 표와 같아야 한다
필수   키를 늘리면 양쪽을 함께 고친다
검산   S13  본문 키 표 == 부록 예시 키
```

```
★ host 기본값을 0.0.0.0 으로 두지 않는다 (14장 STEP 150)
  관리자 화면이 DB 를 조회하고 config 를 바꾼다
```

#### `config/labels.json` — 화면 문구

```json
{
  "VALUE_LABELS": {"1": "있음", "0": "없음",
                   "na": "해당 없음", "unknown": "미확인"},
  "GRADE_LABELS": {"S": "S", "A": "A", "B": "B", "C": "C",
                   "D": "D", "E": "E", "NOT_RATED": "평가 불가"},
  "STATUS_LABELS": {"gone": "목록에서 사라짐", "relisted": "재등록"}
}
```

```
★ 전 화면이 이 문구를 쓴다.  목록과 상세가 다르게 쓰면 안 된다 (10장 STEP 93)
```



#### `config/checks.json` — 검사 대상 · 08-14 신설

```json
{
  "spec_glob": "docs/chapters/**/*.md",
  "ref_glob":  "docs/ref/*.md",
  "chapters":  [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14],
  "self_exclude": [
    "tools/check_spec.py",
    "tools/check_src.py",
    "tools/check_screens.py",
    "validate/v*_*.py"
  ],
  "screens_dir": "ref/screens"
}
```

```
★ 단일 통합본을 대상으로 두지 않는다
근거   통합본이 옛 판이면 검사가 옛 규격으로 판정한다 (실측 08-14)
필수   ref_glob 을 따로 둔다.  부록이 별권이라 chapters 만 읽으면 못 찾는다
필수   장을 하나 끝내면 그 자리에서 chapters 에 넣는다
검산   S17  장 파일 수 == chapters 길이
```

#### `config/known_issues.json` — 차종별 알려진 결함

```json
{
  "KOLEOS_HEV": [
    {"level": "critical", "text": "변속기 보호모드 — 교체비 약 800만"},
    {"level": "major",    "text": "인포테인먼트 설정 초기화"},
    {"level": "major",    "text": "파워트레인 부품 수급 지연"},
    {"level": "minor",    "text": "루프랙 갈변"},
    {"level": "minor",    "text": "테일램프 크랙"}
  ],
  "G80_25T": []
}
```

| `level` | 화면 | 뜻 |
|---|:--:|---|
| `critical` | 🔴 | 치명적 결함 · 큰 수리비 |
| `major` | 🟠 | 구매 판단에 직결 |
| `minor` | ⚪ | 일반 참고 |

```
★ 사람이 넣는다.  수집으로 얻는 값이 아니다
금지   이것을 점수에 반영하는 것.  화면에 참고로만 낸다
근거   근거 없는 수치를 만들지 않는다 (0장)
      다만 「살지 말지」에는 영향이 크므로 화면에는 낸다 (14장 STEP 149c)
필수   차종 키가 없으면 그 절을 내지 않는다.  빈 배열은 「없음」이다
금지   차종 키를 코드에 박는 것.  targets.json 의 키와 같아야 한다
검산   V11-32  known_issues 의 키가 전부 targets 에 있는가
```


#### `config/admin.json` — 08-15 신설

```json
{
  "login_fail_limit": 10,
  "login_lock_sec": 300,
  "min_secret_length": 8
}
```

```
★ 계정을 영구 잠그지 않는다.  PC 가 없어 CLI 로 못 푼다 (08-16)
  시간이 지나면 스스로 풀린다.  관리자가 화면에서도 푼다
검산   V10-20
```

---

| `browser_collect_rows` | 브라우저 수집이 한 번에 부르는 건수 | `20` | 08-16 · V11-47 |
| `browser_interval_sec` | 브라우저 수집 호출 간격 (초) | `0` | 08-16 · 사용자 회선은 안 막힌다 |
| `status_poll_sec` | 진행 모니터 갱신 간격 (초) | `5` | 08-16 · STEP 136f |
| `collect_daily_at` | 매일 자동 수집 시각 | `04:00` | 08-17 · STEP 136h |
| `list_stale_days` | 목록이 오래됐다고 보는 날 수 | `1` | 08-17 · STEP 136i |
| `detail_refresh_days` | 상세를 다시 받는 기준 날 수 | `7` | 08-17 · STEP 136h |
| `check_light_every_h` | 가벼운 점검 간격 (시간) | `4` | 08-17 · S29 |
| `collect_daily_at` | 자동 수집 시각 | `13:00` | 08-18 · 마스터 — 사람 손이 필요해서 |
| `check_light_budget_sec` | 가벼운 점검 시간 예산 (초) | `180` | 08-17 · 실측 155초 |
| `finance.cash_limit` | 전액 현금 판정 기준 (원) | `15000000` | 08-18 · 마스터 |
| `view.page_size_max` | 목록 한 쪽 상한 | `200` | 08-18 · 마스터 |
| `report_preview_bytes` | 리포트 미리보기 상한 | `204800` | 08-18 |
| `check_daily_at` | 일일 점검 시각 | `23:00` | 08-17 · S29 |
| `check_weekly_at` | 주간 일제 점검 시각 | `FRI 02:00` | 08-17 · S29 |
