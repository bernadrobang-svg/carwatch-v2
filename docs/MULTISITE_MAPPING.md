# 사이트 → `core_listing` 칼럼 매핑

`SPEC-2026.08.22-r482` · 2026-08-22
**★ 이 문서가 사이트 확장의 매핑 정본이다. 앞 사이트 규격 문서의 「우리 축」 표는 ★ 축 대응이지 칼럼이 아니다.**

```
★★ 가이드 자백 — 개정 464·473·480·481 에서 ★ 스키마를 안 보고 매핑을 썼다
   「기아 car.price → 우리 예산 축」처럼 ★ 축 이름만 대응시켰다
   ★ 어느 테이블 어느 칼럼에 어떤 타입으로 넣는지 ★ 안 정했다
   ★ 개발측이 그대로 만들면 붙일 데가 없어 다시 물어야 했다.  ★ 이 문서가 그것을 닫는다
★ 마스터 지적 — 「테이블 구조는 다 아니. 옵션 스펙 코드는 이해하고 매핑하고 있니?」
```

---

# 0. 스키마가 이미 다사이트를 받게 되어 있다

```
`core_listing`      117칼럼 · ★ `site` + `source_id` 로 사이트를 가른다
                    「사이트 무관 공통 스키마.  사이트 고유값은 site_* 접두」 (0장 STEP 4)
`dict_option_code`  PK (site, target_key, code)   ★ 사이트마다 코드 체계가 달라도 된다
`dict_enum`         PK (site, axis, value) + `mapped`  ★ 사이트 값 → 우리 값 대응표
`dict_model_option` PK (site, model_catalog_key, option_code)
`raw_response`      원문 무손실.  ★ 삭제 금지 (STEP 33)

★ 그러므로 ★ 새 칼럼을 만들 필요가 거의 없다.  ★ 기존 칼럼에 넣는다
★ 옵션 코드는 ★ 통일하지 않는다 — ★ `dict_option_code` 가 사이트별로 받는다
   ★ 우리 축으로 옮기는 것은 ★ `dict_enum.mapped` 가 한다
```

---

# 1. 공통 — 네 사이트가 같이 쓰는 칼럼

| `core_listing` 칼럼 | 엔카 (지금) | 기아 CPO | KB차차차 | 현대 인증 | K카 |
|---|---|---|---|---|---|
| `site` | `'encar'` | `'kia_cpo'` | `'kbchachacha'` | `'hyundai_cert'` | `'kcar'` |
| `source_id` | carid | `id` (12392) | `carSeq` | `data-id` (GJJ260317025652) | `i_sCarCd` (EC61366001) |
| `price_current_won` | ×10000 | `car.price` **원 단위** | 판매가 ×10000 | 판매가 ×10000 | `prc` ×10000 |
| `price_detail_won` | 상세가 | `discount.discountedPrice` | — | 할인 뒤 가격 | — |
| `price_origin_won` | `origin_total_won` | ★ **없다** | ★ **비율만 준다** | ★ **없다** | ★ **없다** |
| `year_month` | `yearMonth` | `car.firstRegisteredOn`→`YYYYMM` | 「18년11월」 파싱 | 「24년 07월」 파싱 | `mfgDt` (201801) |
| `form_year` | 년형 | `car.modelYear` | 「18년형」 | 「25년형」 | `prdcnYr` |
| `mileage_km` | `mileage` | `car.drivingDistance` | 「43,110km」 | 「20,565km」 | `milg` |
| `displacement_cc` | — | `car.displacement` | — | 「2,497cc」 | `engdispmnt` |
| `trim_badge` | Badge | `car.trim` | 트림명 | 트림명 | `grdNm` |
| `trim_badge_detail` | BadgeDetail | `car.modelName` | — | 제목 트림 | `grdDtlNm` |
| `transmission` | — | `car.mission` | — | — | `trnsmsnNm` |
| `fuel_raw` | `fuelType` | `car.engine` | 연료 | 「가솔린」 | `fuelNm` |
| `fuel_detail` | — | `car.fuelType` (HYBRID) | — | — | — |
| `color_ext_raw` | `color` | `car.color.exteriorCodeName` | 「검정색」 | 「비크 블랙」 | `extrColorNm` |
| `color_int_raw` | — | `car.color.interiorCodeName` | 「정보없음」 다수 | 「블랙원톤」 | — |
| `dealer_shop` | 상사명 | `salesOffice.place` | 딜러 상호 | 지역 | `cntrNm` |
| `dealer_region` | 지역 | `salesOffice.place` | 매매단지 | 「군산」 | `cntrRgnNm` |
| `photo_main` | 사진 | `car.images[0].url` | 썸네일 | 썸네일 | `lsizeImgPath` |
| `photo_list_json` | 배열 | `car.images` (63장) | — | — | — |
| `sales_status` | 상태 | `reserved`→예약 | 게시중 | 판매중/입고예정 | `sellDcd` |
| `reg_at` | 등록일 | `displayedAt` | — | — | — |

```
필수  `price_unit` 은 ★ 'won' 으로 적는다 — ★ 기아는 원 단위로 오고 나머지는 만원이다
      ★ 만원으로 오는 사이트는 ★ 파서에서 ×10000 한다.  ★ 저장은 늘 원이다
필수  `year_month` 는 ★ 'YYYYMM' 6자리다.  ★ 사이트 표기(「18년11월」)를 그대로 넣지 않는다
필수  `source_id` 는 ★ 문자열이다.  ★ 기아 `id` 는 숫자지만 ★ TEXT 로 넣는다
금지  ★ 사이트마다 새 칼럼을 만드는 것.  ★ 기존 칼럼에 넣는다 (0장 STEP 4)
```

---

# 2. 상태·이력 — `core_inspection` · `core_record`

| 우리 | 엔카 | 기아 CPO | KB차차차 | 현대 인증 | K카 |
|---|---|---|---|---|---|
| 판금·교환 | `inspection.outers[]` | ★ `performanceRecord.panelOrExchange` **건수** | 부위별 판금/용접·교환 | 성능점검기록부 | ✘ |
| 사고 | `record.accidents[]` | ★ `insuranceRecord.damaged` **건수** | 「보험사고정보 사고없음」 | 「내차피해이력 1건」 | `acdtHistCd` **코드** |
| 용도 이력 | `record_use` | ★ `insuranceRecord.changeOfUse` | 「용도이력 없음」 | ✘ | ✘ |
| 소유자 변경 | `ownerChangeCnt` | ✘ | 「소유자변경 3회」 | 「소유자 변경 있음」 | ✘ |
| 압류·저당 | `detail_seizing` | ✘ | 「압류 없음 / 저당 없음」 | 「압류 없음 / 저당 없음」 | ✘ |
| 자차 미가입 | `notJoinDate1~5` | ✘ | ✘ | ✘ | ✘ |
| ★ 소모품 | ✘ | ★★ `merchandising.items[]` | ✘ | ✘ | ✘ |

```
필수  `seizing_cnt` · `pledge_cnt` 는 ★ 건수(INTEGER)다.  ★ 「없음」은 ★ 0 이다
      ★ 「안 받았다」는 ★ NULL 이다.  ★ 둘을 섞지 마라 (STEP 32 · 개정 289)
필수  기아 `panelOrExchange` · `damaged` · `changeOfUse` 는 ★ 이미 건수다.  ★ 그대로 넣는다
필수  ★ K카 `acdtHistCd` 는 ★ 코드다 — ★ `dict_enum(site='kcar', axis='accident')` 에 넣고
      ★ `/bc/sub-codelist` 로 표를 받아 `mapped` 를 채운다.  ★ 뜻을 지어내지 마라
필수  ★ 기아 `merchandising.items[]` 는 ★ `core_inspection` 에 원문 배열 그대로 (STEP 21)
      ★ category/type/name 을 가공하지 않는다
```

---

# 3. ★ 보증 — 사이트마다 꼴이 다르다

| 사이트 | 원문 | `warranty_*_month` · `_km` 로 넣는 법 |
|---|---|---|
| 엔카 | 보증 종료일(날짜) | 오늘과 빼서 잔여 개월 계산 |
| **기아 CPO** | ★ `warranties[]` `{kind, remainingPeriod, remainingDistance}` | ★ **그대로** — `BA`·`AC`·`CM`→body · `EG`·`PT`·`EM`→power |
| **현대 인증** | ★ 「2년 10개월 남음 · 79,435km 남음」 | ★ 개월로 환산해 그대로 |
| KB차차차 | 「보증종료」 판정만 | ★ 종료면 **0** · 잔여를 모르면 **NULL** |
| K카 | ✘ | 연식 + 제조사 보증 기간표로 계산 |

```
필수  `warranty_body_month` · `warranty_body_km` · `warranty_power_month` · `warranty_power_km`
      ★ 네 칼럼이 이미 있다.  ★ 새로 만들지 마라
필수  기아 `kind` 는 ★ `dict_enum(site='kia_cpo', axis='warranty_kind')` 에 넣는다
      BA 차체 · AC 에어컨 · EG 엔진 · PT 동력전달 · EM 배기 · CM 소모품 (실측)
필수  ★ KB 「보증종료」는 ★ 0 이지 NULL 이 아니다.  ★ 확인한 것이다
      ★ K카는 ★ NULL 이다 — ★ 안 받았다
```

---

# 4. ★★ 옵션 — 통일하지 않는다. 사이트별로 받는다

```
★ 사이트마다 꼴이 다르다
  엔카      숫자 코드      "1039" · "1060" · "001"
  기아 CPO  영문 enum      LEATHER_SEATS · NAVIGATION · SUNROOF · ADAS   (13종 + optionCount 102)
  KB차차차  한글 이름      「내비게이션(순정)」 「통풍시트」 「선루프(일반)」
  현대 인증 한글 이름      「내비게이션」 「헤드업 디스플레이」 「선루프」
  K카       한글 이름 문자열  "ABS|내비게이션|가죽시트|HUD"  (`optnNm` · 파이프 구분)
```

**넣는 법 — 이미 있는 표를 쓴다**

```
① `core_listing.options_choice_json` · `options_standard_json`
   → ★ 사이트 원문 그대로 직렬화한다.  ★ 가공 금지 (encar/mapping.py 와 같다)
② `dict_option_code(site, target_key, code, display, …)`
   → ★ 사이트별 코드를 그대로 쌓는다.  ★ PK 가 (site, target_key, code) 라 충돌하지 않는다
     encar     code='1039'          display='선루프'
     kia_cpo   code='SUNROOF'       display='선루프'
     kcar      code='선루프'         display='선루프'      ← 이름이 곧 코드다
   ★ status 는 처음에 'pending'.  ★ 사람이 확인하면 'confirmed' (STEP 40~45)
③ 우리 축(`taste.sunroof` · `taste.hud` · `taste.fitting`)으로 옮기는 것은
   → ★ `dict_enum(site, axis='option', value=code, mapped='sunroof')` 가 한다
   ★ `mapped` 가 비면 ★ 그 축은 0점 + 「미확인」.  ★ 짐작으로 채우지 마라
```

```
금지  ★ 사이트 옵션 코드를 ★ 엔카 숫자 코드로 억지로 바꾸는 것
      ★ 「SUNROOF 는 1039 겠지」는 ★ 짐작이다.  ★ dict 로 잇는다
금지  ★ 옵션 이름을 문자열 비교로 맞추는 것 (「선루프」 in name)
      ★ 「선루프(일반)」 「파노라마 선루프」가 섞인다.  ★ dict 에 등록해 쓴다
필수  ★ K카 `optnNm` 은 ★ 파이프(|)로 쪼개 ★ 각각을 code 로 넣는다
필수  ★ 기아 `mainOptions[].has=false` 는 ★ 「없음」이다 — ★ 안 넣는 것과 다르다
```

---

# 5. 사이트 검증 · 등급

| 사이트 | 원문 | 어디에 |
|---|---|---|
| 엔카 | 진단++ / + / 진단 | `diagnosis_car` + `core_diagnosis` |
| **기아 CPO** | ★ `classification` PREMIUM·EXCLUSIVE·LITE | ★ `dict_enum(site='kia_cpo', axis='classification')` |
| KB차차차 | 진단 · 스타픽 · 홈배송 | ★ `dict_enum(site='kbchachacha', axis='badge')` |
| 현대 인증 | 정밀점검 287항목 · 책임환불 3일 | 제조사 인증 = 만점 |
| K카 | `sellDcd` GNRL(직영) / 제휴 | ★ `dict_enum(site='kcar', axis='sell_type')` |

```
필수  점수 단계는 ★ `f-table.md` 「사이트 검증 36점」 표가 정본이다.  ★ 여기 옮겨 적지 않는다
필수  ★ 사이트가 준 값을 ★ 그대로 저장하고, ★ 점수로 바꾸는 것은 ★ Analyzer 가 한다
```

---

# 6. ★ 새로 필요한 칼럼 — ★ 둘뿐이다

```
① `core_listing.performance_report_url`  TEXT
   ★ 기아 `performanceReportPdfUrl` · 현대 성능점검기록부 · KB 성능점검 원본
   ★ 지금 칼럼이 없다.  ★ 원문 주소를 잃으면 다시 못 받는다
② `core_listing.price_discount_won`      INTEGER
   ★ 기아 `discount.discountAmount` · 현대 「140만 할인」
   ★ 지금은 `price_current_won` 과 `price_detail_won` 으로 둘을 다 표현할 수 없다
   ★ 할인 전/후를 구분해야 「할인금액 높은순」 정렬과 값 축이 맞는다

★ 그 밖에는 ★ 기존 칼럼으로 다 된다.  ★ 117칼럼이 이미 넓다
★ 이 둘은 ★ 마스터 확정 뒤에 DDL 을 고친다 — ★ 개발측이 임의로 만들지 않는다
```

---

# 7. ★ 아직 안 정한 것 — 정직하게 적는다

```
① `target_key` — 사이트마다 차종을 뭐라 부르는지 ★ 대응표가 없다
   엔카 `ModelGroup` · 기아 `modelCode`(SU) · 현대 `mdlGrpList`(1171) · K카 `modelGrpNm`
   → ★ `dict_enum(axis='target')` 로 잇는다.  ★ facet 을 받아 채운다.  ★ 지어내지 마라
② `vehicle_id` — ★ 같은 차가 여러 사이트에 있을 때 묶을 근거가 없다
   ★ 차대번호를 주는 사이트가 없다.  ★ 지금은 ★ 합치지 않는다 (개정 464)
③ 표본 — ★ 기아 상세 1건 · 현대 1건 · K카 1건 · KB 25건으로 쓴 것이다
   ★ 각 20건 이상으로 늘려 ★ 이 표를 다시 대조해야 한다 (오판대장 모양 ④)
```
