## STEP 19 — `list` 응답 → 필드

```
version  SPEC-2026.09.02-r1079
follows  `docs/chapters/30-score/f-table.md`
sources  실측 08-22
checks   S46-38 · S46-39
```


**아래는 `SearchResults[]` 요소의 경로다.** 봉투(`Count`)는 STEP 18a 참조.
**원문 29경로. 배열 요소는 `[]` 로 한 경로로 센다.**

| 원문 | 변환 | CORE 필드 | 비고 |
|---|---|---|---|
| `Id` | — | `source_id` | |
| `ModelGroup` | — | `site_model_group` | 사이트 원문값 |
| `Model` | — | `site_model` | |
| `Manufacturer` | — | `site_manufacturer` | |
| `Badge` | — | `trim_badge` | 트림 1순위 |
| `FuelType` | — | `fuel_raw` | **완전일치 사전.** 부분 검색 금지 |
| `Year` | `ym` | `year_month` | `202603.0` → `2026-03` |
| `FormYear` | — | `form_year` | |
| `Mileage` | int | `mileage_km` | |
| `Price` | `×10000` | `price_current_won` | **만원 단위** |
| `Color` · `ColorExpression` | — | `color_ext_raw` · `color_ext_hex` | hex 는 `#fff;#fff` |
| `SeatColor` · `SeatColorExpression` | — | `color_int_raw` · `color_int_hex` | |
| `Transmission` | — | `transmission` | |
| `SellType` | — | `sell_type` | 일반·렌트·리스 |
| `SalesStatus` | — | `sales_status` | `CONTRACT` 등 |
| `ServiceCopyCar` | — | `copy_car` | ORIGINAL·DUPLICATION |
| `OfficeCityState` | — | **`dealer_region`** | ★ v1 은 `dealer_shop` 에 넣었다 |
| `DealerPhoto` | — | `dealer_photo` | |
| `Photo` · `Photos[]` | json | `photo_main` · `photo_list_json` | |
| `ServiceMark[]` | json | `site_service_marks_json` | `EncarDiagnosisP0/P1/P2` |
| `Trust[]` | json | `site_trust_json` | Warranty·ExtendWarranty·HomeService |
| `Condition[]` | json | `site_condition_json` | Record·Inspection·Resume·InspectionDirect |
| `Separation[]` · `AdType[]` · `BuyType[]` | json | `site_*_json` | |
| `HomeServiceVerification` | — | `site_home_verify` | 판정 미사용 (8장) |

**★ `OfficeCityState` 는 지역이다.** v1 은 딜러 상사명 컬럼(`dealer_shop`)에 넣어
전건이 오염됐다. 상사명은 `detail` 의 `partnership.dealer.firm.name` 이다.

```
사이트 고유값은 site_* 접두를 붙인다.
2차 사이트에 같은 개념이 없을 수 있다.  CORE 공통 필드와 섞지 않는다.
```

---


### ★ 한 필드가 죽어도 매물을 버리지 않는다 — 08-14

```
실측   originPrice 에 문자열이 오자 남은 필드가 2개(site·source_id)뿐이었다
      warranty · options · gradeName 이 전부 사라졌다
원인   파서 전체를 try 로 감싸고 실패하면 빈 dict 를 반환한다
```

```
필수   필드마다 safe_field 로 감싼다.  한 필드가 죽어도 나머지는 남긴다
필수   죽은 필드는 core_parse_issue 에 (endpoint, path, reason, 표본) 으로 남긴다
금지   파서 전체를 try 로 감싸고 빈 dict 를 반환하는 것
근거   코드 주석에 「그 매물이 사라져 다른 16축도 못 본다」고 스스로 적어 두고
      safe_field 를 만들었으나 호출처가 0 이었다 (실측 08-14)
검산   V2-28  파싱 실패 매물의 필드 수가 2 인 행이 없는가
```

### ★ 적재에서 버려지는 키를 센다

```
필수   parsed 에 있는데 컬럼에 없는 키를 센다.  0 이 아니면 경고한다
예외   _pii_* · _site_* 접두는 의도된 것이다
근거   파서가 새 필드를 만들어도 DDL 을 안 고쳤으면 로그 없이 사라진다
검산   V2-29
```

---



---

## ★ 파서가 내야 할 공통 필드 — 08-16

```
근거   실측.  parse_diagnosis 가 row_status 를 안 내
      core_diagnosis NOT NULL 위반으로 S6 이 통째로 죽었다
      다른 파서 셋은 내는데 하나만 빠져 있었다
```

```
필수   모든 파서가 row_status 를 낸다
필수   같은 자리를 여러 번 쓸 때는 「전부가 내는가」를 검사한다
       하나씩 보면 빠진 것이 안 보인다
검산   V2-30  전 파서가 row_status 를 내는가
```

```
★ 이런 결함은 사람 눈으로 못 잡는다
  파서 넷을 각각 보면 셋은 맞고 하나만 틀리다
  「넷을 한 줄에 놓고 비교하는」 검사가 있어야 한다
```
