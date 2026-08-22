# 사이트 → `core_listing` 칼럼 매핑

`SPEC-2026.08.22-r484` · 2026-08-22
**★ 이 문서가 사이트 확장의 매핑 정본이다. 앞 사이트 규격 문서의 「우리 축」 표는 ★ 축 대응이지 칼럼이 아니다.**

```
★ 다루는 사이트 여섯 — 엔카(지금) · 기아 CPO · KB차차차 · 현대 인증 · K카 · 헤이딜러
★ K카는 ★ 상세까지 들어왔다 (개정 484 · 마스터가 조사분을 주셨다)
   ★ 값 API 는 `mapi.kcar.com` 이고 ★ 그 호스트에는 robots 문서가 없다
   ★ 우리는 ★ 이미 같은 호스트에서 목록을 받고 있다.  ★ 가이드가 목록·상세에 다른 잣대를 댔다
```

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
| `price_origin_won` | `origin_total_won` | ★ **없다** | ★ **비율만 준다** | ★ **없다** | ★ **없다** (`npriceFullType` 은 ★ 판매가다 — **착각 주의**) |
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

# 2a. ★★ 기아 CPO 표본 30건 검증 — ★ 1건일 때 못 본 것 넷

```
★ 개정 481 은 ★ 표본 1건으로 썼다.  ★ 30건으로 늘려 다시 쟀다 (모양 ④)
```

## ① ★★ `panelOrExchange` 와 `merchandising` 이 ★ 다른 것을 센다 — 가장 크다

```
실측  `performanceRecord.panelOrExchange` — 30건 중 ★ 0 이 29건 · 1 이 1건
      그런데 ★ 같은 매물들의 `merchandising.items` 에
        ★ 판금 12건 · ★ 도장 44건 이 있다
      예 — 「외관 및 내장 · ★ 판금 · 조수석 앞 도어」 인데 `panelOrExchange=0`

★★ 뜻 — `panelOrExchange` 는 ★ 「사고로 인한 판금·교환」(성능점검기록부)이고
        `merchandising` 은 ★ 「기아가 상품화하며 손본 것」이다.  ★ 둘은 다르다
★ 그러므로 ★ merchandising 의 판금·도장을 ★ 사고로 세면 안 된다
```

| 우리 축 | 무엇을 쓰나 |
|---|---|
| `state.frame` 골격 · `state.outer` 외판 | ★ `performanceRecord.panelOrExchange` **만** |
| `state.consumable` 소모품 | ★ `merchandising` 중 **`category='기능수리 및 소모품'`** 만 |
| — 상품화 이력 (점수 아님) | `merchandising` 중 `외관 및 내장` · `휠 타이어` → ★ **화면에만 낸다** |

```
필수  ★ `merchandising` 을 ★ 통째로 소모품으로 쓰지 마라.  ★ category 로 가른다
      실측 category — 외관 및 내장 129 · 기능수리 및 소모품 118 · 휠 타이어 16
      실측 type — 교환 94 · 보충 60 · 도장 44 · 광택 30 · 복원 23 · ★ 판금 12
필수  ★ 화면에 「기아가 상품화하며 판금·도장한 부위」를 ★ 밝힌다 — 사고는 아니지만 손댄 곳이다
금지  ★ merchandising 의 판금·도장을 ★ 사고·골격 축에 넣는 것
```

## ② `warranties` 는 ★ 연료에 따라 개수가 다르다

```
실측  6개 21건 · 5개 7건 · 4개 2건
      ★ 5개 — `CM`(소모품 보증)이 빠진다 (가솔린 여럿)
      ★ 4개 — ★ 전기차다.  `EG`(엔진)·`EM`(배기)이 ★ 없다.  ★ 당연하다
필수  ★ 없는 kind 를 ★ 0 으로 넣지 마라.  ★ NULL 이다 — ★ 그 차에 없는 보증이다
      ★ 전기차에 엔진 보증 0점을 주면 ★ 전기차가 통째로 손해를 본다 (개정 289·434)
필수  `warranty_power_*` — EV 는 `PT`(동력전달)로 잰다.  내연은 `EG`·`PT` 중 긴 것
```

## ③ `classification` 은 ★ LITE 가 가장 많다

```
실측  LITE 16 · PREMIUM 13 · EXCLUSIVE 1
★ f-table 은 PREMIUM·EXCLUSIVE 36 · LITE 32 로 두었다 — ★ 절반이 32점이다.  그대로 둔다
```

## ④ `discount` 는 ★ 5/30 뿐이다

```
실측  할인 있는 것 5건 (69만~300만) · ★ 마감 시각이 전부 `2026-08-25T12:00:00` — 기간 행사다
필수  `price_discount_won` 은 ★ NULL 이 기본이다.  ★ 0 이 아니다
필수  ★ 할인은 ★ 사라진다.  `price_current_won` 은 ★ 할인 뒤 값으로 갱신한다
```

## ⑤ 그 밖 — 존재율 30/30

```
car.price · firstRegisteredOn · drivingDistance · trim · mission ·
performanceRecord · insuranceRecord · optionPrice · optionCount ·
classification · ★ performanceReportPdfUrl     ★ 전부 30/30
car.displacement 만 28/30 — ★ 빠진 둘은 ★ 전기차다.  ★ NULL 이 맞다
mainOptions 13종 고정 — ADAS · AUTOMATIC_TRUNK · HEATED_SEATS · HIPASS · ★ HUD ·
  LEATHER_SEATS · NAVIGATION · PARKING_DISTANCE_WARNING · REAR_VIEW_CAMERA ·
  SMART_KEY · ★ SUNROOF · VENTILATED_SEATS · WIRELESS_CHARGING
  ★ HUD 13/30 · ★ 우리 taste.hud 18점 · taste.sunroof 12점이 바로 붙는다
customKeywords — 보험이력없음 17 · 오토할부혜택 9 · 짧은km 4 · 세제혜택 4
  ★ 「오토할부혜택」·「세제혜택」은 ★ 차 상태가 아니다.  ★ 점수에 넣지 마라
insuranceRecord.damaged — 0이 22 · 1이 6 · 2가 2   changeOfUse — 0이 19 · ★ 1이 11
  ★ 용도 이력이 있는 매물이 ★ 3분의 1이다.  ★ 렌트·영업용 감점이 실제로 걸린다
```

---

# 2b. ★★ K카 상세 — `mapi.kcar.com/bc/car-info-detail-of-ng?i_sCarCd=`

**★ 마스터가 조사분을 주셨다 (`outputs/sites/_K카상세_20260822.md`). 개정 468 「직영이라 믿고 준다」가 ★ 실측으로 바뀐다.**

```
GET https://mapi.kcar.com/bc/car-info-detail-of-ng?i_sCarCd={번호}  → 200 · 80KB · 평문 JSON · 51블록 · 1,050필드
★ 헤더·토큰·쿠키 없다 · 0.5초 · ★ 목록과 달리 암호화도 없다
★★ 함정 — ★ 없는 매물번호도 ★ 200 에 ★ 3,186B 빈 껍데기를 준다
   ★ KB 봇페이지 2,759B 와 같은 꼴이다 (오판 #43).  ★ 크기로 갈라라.  ★ 「없음」으로 저장하지 마라
```

| `core_*` 칼럼 | K카 상세 필드 | 표본 값 |
|---|---|---|
| **`core_listing.vin`** | ★ `vin` | `KMTGA41CBSU251014` |
| `core_listing.plate_hash` | `cno` (해시해서) | 211러2161 |
| `core_listing.seizing_cnt`·`pledge_cnt` | `master.szrMogeYn` | `N` → 0 |
| `core_listing.warranty_power_month`·`_km` | ★ `nwcaGurnteEngeSurvDt`·`…Milg` | **2029-06-16 · 10만km** |
| `core_listing.warranty_body_month`·`_km` | ★ `nwcaGurnteGnrlSurvDt`·`…Milg` | 〃 |
| `core_listing.options_choice_json` | ★ `optList` (45개 · 이름) | HUD · 360어라운드뷰 · 통풍시트 |
| `core_listing.model_catalog_key` | ★ `carJatoOptList.vehicleId` (JATO 연번) | ★ 신차가 매칭 열쇠 후보 · **미검증** |
| **`core_record.owner_change_cnt`** | `carhistory.ownrChngCnt` | 1 |
| `core_record.owner_change_dates_json` | ★ `carOwnrChngHistList` | 신조→매매업자 · 평택 50대 |
| `core_record.accident_my_cost` | ★ `carHistoryAccList` 부품·공임·도장 | 85만 (8.2+24.0+52.6) |
| `core_record.total_loss_cnt` | `carhistory.gnrlTtlsAcdtCnt`·`rbrTtlsAcdtCnt` | 0 |
| `core_record.flood_total_cnt` | `carhistory.fldgAcdtCnt` | 0 |
| `core_record.use_business`·`use_gov` | `rentHistYn`·`bizuseHistYn`·`instnHistYn` | N·N·N |
| `core_record.not_join_json` | `carhistory.rsltCd`·`insrHistIqyEn` | 000 · 1 (조회됨) |
| `core_inspection.inspection_vin` | `master.vinCnfmYn`·`rvo.vinStatCd` | 확인 |
| `core_inspection.inspection_recall` | ★ `master.recallObjYn` | **1 — 리콜 대상** |
| `core_inspection.inspection_car_state` | ★ `master.dshbExchgYn` | **1 — 계기판 교체** |
| `core_inspection.inspection_comment` | `acdtHistComnt` · `smplReprYn` | 「무사고」 |
| `core_inspection.inspection_valid_to` | `efctDt` | 20280616 |
| `core_inspection.inspection_issued_at` | `dgnosDt` | 20260624 |
| `core_inspection.inspection_image_json` | ★ `/bc/car-insp/photo/cm?i_sCarCd=` | ★ **사진 경로만** |
| ★ `state.consumable` (소모품) | ★ `tireDtlList` 4짝 잔량·규격·생산주차 | 5.6/5.5/6.2/6.2mm · 24년 |

```
★★ 얻는 것 — ★ 실측 근거 495 → 755점.  ★ 「믿음으로 준 것」이 220 → 36 (직영 사이트검증만)
★★ ★ VIN 이 온다 — ★ 교차 사이트 중복 제거가 풀린다 (7장 ② 가 닫힌다)
★ 제조사 보증 잔여를 ★ K카가 직접 준다.  ★ 연식으로 계산할 필요가 없다
★ 새 경고 둘 — ★ `recallObjYn`(리콜 대상) · `dshbExchgYn`(계기판 교체)
   → ★ `listing_warning` 에 넣는다.  ★ 점수에 합산하지 않는다 (V3-21·22·23)

★ 못 채우는 것 155점
  골격 40 · 외판 26 · 누유 14 = 80  → ★ 성능점검이 ★ 사진뿐이다.  부위별 값이 JSON 에 없다
  신차가 75                       → ★ 없다.  ★ `npriceFullType` 은 ★ 판매가다.  ★ 착각 주의
★ 부위별 등급은 ★ 사진 OCR 없이는 못 낸다.  ★ 지어내지 않는다
```

---

# 2c. 헤이딜러 — 목록만 (토큰 미해결)

| `core_listing` 칼럼 | 헤이딜러 |
|---|---|
| `site` | `'heydealer'` |
| `source_id` | `/market/cars/{code}` 의 code (`2yM82GlW`) |
| 사고 | 「무사고」 · 「단순교환 무사고」 · 「사고 구분」 · 「보험 내차피해」 |
| 배터리 | ★ 「배터리 정상」 → SOH 가점(+30) 재료 |

```
★ `authorization: Bearer` 토큰이 필요하다.  ★ 발급 경로 미확정 — ★ 개발측에 넘기지 않는다
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

# 5a. ★★ 정규화 — 여섯 사이트를 한 표에 담을 때 어긋나는 곳

**★ 매핑은 「어디에 넣나」다. 정규화는 「같은 뜻인가」다. ★ 아래가 정규화가 필요한 자리다.**

## ① 단위 — ★ 저장은 늘 원(WON)

| 사이트 | 원문 | 파서에서 |
|---|---|---|
| 엔카 · KB · 현대 · K카 | **만원** | ★ ×10000 |
| 기아 CPO | ★ **원** | 그대로 |

```
필수  `price_unit` = 'won' 고정.  ★ 사이트 단위를 칼럼에 남기지 않는다
검산  ★ 100만 미만 가격이 있으면 ★ 환산을 빠뜨린 것이다
```

## ② 날짜 — ★ `year_month` 는 YYYYMM 6자리

```
엔카      "202409"          → 그대로
기아 CPO  "2024-02-19"      → "202402"   ★ 일(日)은 버린다
현대      "24년 07월(25년형)" → "202407" + form_year=2025
KB        "18년11월(18년형)" → "201811" + form_year=2018
K카       mfgDt "201801"     → 그대로
금지  ★ 사이트 표기를 그대로 넣는 것.  ★ 「18년11월」은 값이 아니다
```

## ③ ★ 「없음」 · 「모름」 · 「안 받았다」 — ★ 셋을 가른다

| 뜻 | 저장 | 보기 |
|---|---|---|
| **없음** (확인해 보니 0) | ★ **0** | KB 「보증종료」 · 기아 `damaged=0` · K카 `szrMogeYn='N'` |
| **모름** (사이트가 안 줌) | ★ **NULL** | K카 골격·외판 · 기아 압류저당 |
| **안 받았다** (수집 실패) | ★ **NULL + `row_status`** | KB 봇페이지 · K카 빈 껍데기 |

```
★★ 이것이 가장 중요하다 (개정 289·434 · 오판 #43)
필수  KB 응답 ★ 10KB 미만 또는 「로봇 여부 확인」 → ★ 수집 실패.  ★ 재시도 3회
필수  K카 상세 ★ 3,186B 빈 껍데기 → ★ 수집 실패.  ★ 「없음」으로 저장 금지
필수  기아 `warranties` 에 ★ 없는 kind → ★ NULL.  ★ 0 이 아니다 (전기차 EG·EM)
```

## ④ ★ 사고 — 사이트마다 세는 것이 다르다

| 사이트 | 필드 | 무엇을 세나 |
|---|---|---|
| 엔카 | `accidents[]` | 보험 처리 건 |
| 기아 CPO | `insuranceRecord.damaged` | 보험 내차피해 건수 |
| 기아 CPO | ★ `performanceRecord.panelOrExchange` | ★ **사고로 인한** 판금·교환 |
| 기아 CPO | ★ `merchandising` 판금·도장 | ★ **상품화하며 손본 것** — ★ 사고 아님 |
| KB | 「보험사고정보 사고없음」 | 판정 문구 |
| 현대 | 「내차피해이력 1건」 | 건수 |
| K카 | `carHistoryAccList` + `acdtHistComnt` | 금액 분해 + 문구 |

```
필수  `accident_my_cnt` = ★ 내 차 피해 건수 · `accident_other_cnt` = 상대 차
필수  ★ 기아 `merchandising` 의 판금·도장은 ★ 사고에 넣지 마라 (개정 483)
필수  ★ 문구(「무사고」)를 ★ 건수 0 으로 바꾸지 마라 — ★ `inspection_comment` 에 원문으로
```

## ⑤ 옵션 — ★ 통일하지 않는다. `dict_option_code` 가 받는다

```
엔카      숫자 "1039"                   기아  영문 "SUNROOF"
KB·현대   한글 「선루프(일반)」            K카   파이프 "ABS|내비게이션|HUD"  → ★ 쪼개서 각각
필수  `dict_enum(site, axis='option', value=code, mapped='sunroof')` 로 우리 축에 잇는다
필수  ★ `mapped` 가 비면 ★ 0점 + 「미확인」.  ★ 짐작으로 채우지 마라
금지  ★ 문자열 비교로 맞추는 것 (「선루프」 in name) — 「파노라마 선루프」가 섞인다
```

## ⑥ ★ 보증 — 잔여를 주는 곳과 계산해야 하는 곳

| 사이트 | 원문 | 정규화 |
|---|---|---|
| 기아 CPO | `remainingPeriod`·`remainingDistance` | ★ 그대로 |
| 현대 | 「2년 10개월 · 79,435km 남음」 | ★ 개월로 환산 |
| K카 | `nwcaGurnte…SurvDt` (종료일) | ★ 오늘과 빼서 개월 |
| 엔카 | 종료일 | 〃 |
| KB | 「보증종료」 판정만 | ★ 0 |

```
필수  `warranty_body_*` · `warranty_power_*` ★ 네 칼럼에 담는다.  ★ 새 칼럼 금지
필수  ★ EV 는 `PT`(동력전달)로 동력계를 잰다.  ★ 엔진 보증이 없다고 0 을 주지 마라
```

## ⑦ ★ 교차 사이트 동일차 — ★ VIN 이 있는 쪽만 묶는다

```
K카      ★ `vin` 을 준다 (개정 484)
그 밖    ✘ VIN 없음
필수  `vehicle_identity` 로 잇되 ★ VIN 이 있는 쪽끼리만.  ★ 없으면 ★ 합치지 않는다
금지  ★ 차종+연식+주행+색으로 「같은 차겠지」 하는 것.  ★ 짐작이다
```

## ⑧ 경고 — ★ 점수에 합산하지 않는다

```
K카   ★ `recallObjYn`(리콜 대상) · `dshbExchgYn`(계기판 교체)
필수  ★ `listing_warning` 에 넣는다.  ★ 점수에 합산하지 않고 목록에서 빼지도 않는다 (V3-21·22·23)
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
② `vehicle_id` — ★ 풀렸다 (개정 484)
   ★ K카가 ★ `vin` 을 준다 (`KMTGA41CBSU251014`).  ★ `core_listing.vin` · `vehicle_identity` 로 잇는다
   ★ 다른 사이트는 아직 VIN 이 없다 — ★ VIN 이 있는 쪽끼리만 묶는다.  ★ 없으면 합치지 않는다
③ 표본 — ★ 기아 ★ 30건으로 늘려 검증했다 (2a장).  ★ 현대 1건 · K카 1건은 ★ 아직이다
   ★ 둘도 20건 이상으로 늘려 다시 대조해야 한다 (오판대장 모양 ④)
```
