# 사이트 → `core_listing` 칼럼 매핑

```
version  SPEC-2026.08.29-r899
follows  `docs/INDEX.md`
sources  실측 08-23
checks   S46-38 · S46-39
```


`SPEC-2026.08.23-r537` · 2026-08-22
**★ 이 문서가 사이트 확장의 매핑 정본이다. 앞 사이트 규격 문서의 「우리 축」 표는 ★ 축 대응이지 칼럼이 아니다.**

```
★ 다루는 사이트 여섯 — 엔카(지금) · 기아 CPO · KB차차차 · 현대 인증 · K카 · 헤이딜러
★ K카는 ★ 상세까지 들어왔다 (개정 484 · 마스터가 조사분을 주셨다)
   ★ 값 API 는 `mapi.kcar.com` 이고 ★ 그 호스트에는 robots 문서가 없다
   ★ 우리는 ★ 이미 같은 호스트에서 목록을 받고 있다.  ★ 가이드가 목록·상세에 다른 잣대를 댔다
```

```
★★ 가이드 자백 — 개정 464·473·480·481 에서 ★ 스키마를 안 보고 매핑을 썼다
   ★ ★ **08-29 에 닫는다** — ★ 볼보·BMW·보배·렉서스 절에 ★ 칼럼 매핑을 채웠다 (아래 08-29 절)
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
필수  ★ K카 사고 판정은 ★ 상세 `acdtHistComnt`(무사고·단순수리·사고) 로 한다 (개정 485)
      ★ `smplReprYn`·`acdtHistYn` 으로 가르지 마라 — ★ 실측에서 갈리지 않는다
필수  ★ 목록 `acdtHistCd` 는 ★ 코드다 — ★ `dict_enum(site='kcar', axis='accident')` 에 넣고
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

# 2b-1. ★★ K카 상세 표본 25건 검증 — ★ 경로가 틀렸다 (개정 523)

```
★ 개정 484 는 ★ 마스터가 주신 조사분을 그대로 옮겨 적었다.  ★ 25건으로 다시 쟀다
★★ ★ 응답이 ★ `{"data": {…}}` 로 한 겹 싸여 있다 — ★ 51블록은 ★ `data` 아래다
```

## ★ 경로 정정 — 개정 484 가 적은 것이 틀렸다

| 무엇 | 개정 484 (틀림) | ★ 실측 경로 | 존재율 |
|---|---|---|--:|
| **VIN** | `vin` | ★ **`data.rvo.vin`** | **25/25** |
| 압류·저당 | `master.szrMogeYn` | `data.master.szrMogeYn` | 25/25 (전부 `N`) |
| 보증 잔여(엔진) | `nwcaGurnteEngeSurvDt` | ★ **`data.rvo.nwcaGurnteEngeSurvDt`** | ★ **14/25** |
| 보증 잔여(일반) | 〃 | `data.rvo.nwcaGurnteGnrlSurvDt` | ★ **0/25** |
| 리콜 | `master.recallObjYn` | ★ **`data.carRecallNeedCnt`** (건수) | ★ **25/25** · 0/1/2 |
| ~~계기판~~ | ~~`master.dshbExchgYn`~~ | ★ **쓰지 않는다** (개정 524) | — |
| 타이어 | `tireDtlList` | `data.tireDtlList[].tirResQty` | 25/25 |
| 옵션 | `optList` | `data.optList` | 25/25 |
| 사고 내역 | `carHistoryAccList` | `data.carHistoryAccList` | ★ **16/25** |

```
필수  ★ 파서는 ★ `data` 를 벗기고 시작한다.  ★ 안 벗기면 ★ 전건 NULL 이 된다
      ★ v1 이 `outers[].children[]` 로 전건 NULL 을 낸 것과 같은 꼴이다
```

## ★★ 개정 484 의 판정 셋을 정정한다

```
① ★★ 「`dshbExchgYn` = 계기판 교체」 — ★ 틀렸다.  ★ 쓰지 않는다 (개정 524 확정)
   실측  25/25 가 전부 `1` 인데 ★ 주행거리는 11,665 ~ 92,637 로 제각각이고 정상이다
         `milgStatCd` · `milgInfoEn` 은 ★ 전부 null 이다 — ★ 이상 표시가 따로 없다
   견줌  `vinCnfmYn` 도 25/25 가 `1` · `tirInpCmplYn` 은 `Y` · `szrMogeYn` 은 `N`
         → ★ `1` 은 ★ 「점검항목을 확인했다」는 표시다.  ★ 「교체됨」이 아니다
   필수  ★ `listing_warning` 에 ★ 넣지 마라.  ★ 이 필드는 ★ 쓰지 않는다
   ★ 넣었으면 ★ 25건 전부에 「계기판 교체」 경고가 붙었다

② ★★ 「`recallObjYn` = 리콜 대상」 — ★ 틀렸다.  ★ `carRecallNeedCnt` 를 쓴다 (개정 524)
   실측  `masterInfo.recallObjYn` 은 ★ 25/25 가 ★ null 이다 — ★ 안 쓰는 필드다
         ★ `data.carRecallNeedCnt` 가 ★ 25/25 로 오고 ★ 0 / 1 / 2 로 갈린다 (20 / 3 / 2)
   필수  ★ `core_inspection.inspection_recall` ← ★ `data.carRecallNeedCnt` (건수다)
         ★ 0 이면 ★ 「없음」이다 (확인한 값) · ★ 필드가 없으면 NULL
   ★ `listing_warning` 에 ★ 1 이상일 때만 넣는다.  ★ 점수에 합산하지 않는다 (V3-21·22·23)

③ ★ 「제조사 보증 잔여를 K카가 직접 준다」 — ★ 엔진 14/25 · ★ 일반 0/25 다
   ★ 「준다」가 아니라 ★ 「있는 매물만 준다」다
   ★ 연식 2018·2020 인 매물은 ★ 비어 있다 — ★ 보증이 끝난 것이다
   필수  ★ 비어 있으면 ★ 0 이 아니라 ★ NULL 로 두고 ★ 연식+기간표로 계산한다
         ★ 「없다」와 「끝났다」를 ★ 여기서는 가를 수 없다
```

## 그 밖 실측

```
★ 목록 총 ★ 7,737대 · 쪽당 30건 (`data.totalCnt`) — 개정 467 의 「쪽당 10건」은 조건이 달랐다
★ 매물번호는 ★ 목록의 `carCd` 다 (`EC61368665` 꼴) → 상세 `i_sCarCd` 에 그대로 넣는다
★ 빈 껍데기(3,186B) ★ 0건 — 25건 전부 정상이었다.  ★ 그래도 크기 검사는 남긴다
★ VIN 중복 ★ 없음 — 25건이 다 다른 차다
★ `carJatoOptList` 22/25 — 신차가 매칭 열쇠 후보인데 ★ 셋은 없다
```

---

# 2c. ★★ 헤이딜러 — ★ 뚫렸다. 토큰은 ★ 세션 쿠키다

```
① GET https://www.heydealer.com/          ← ★ 한 번 연다.  ★ 서버가 쿠키를 준다
   Set-Cookie: ★ customer_web_session=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9…
② GET https://market-api.heydealer.com/v2/customers/web/market/cars/
      ?order=recommendation&view_type=compact&page=N
   헤더  ★ authorization: Bearer {그 쿠키 값}  ·  app-os: web
         Referer: https://www.heydealer.com/  ·  Origin: 같음
   → ★ 200 · 54,373B · 평문 JSON
★ 로그인이 아니다.  ★ 손님용 세션을 서버가 스스로 발급한다
★ 토큰을 훔치거나 흉내 낸 것이 아니다 — ★ 정상 발급 경로를 찾은 것이다
★ 응답은 ★ 배열(list)이다.  ★ dict 가 아니다 — 파서 주의
```

## ★ 우리 축과 맞춰 본 것 (표본 BMW 520i · 3,250만)

| `core_*` 칼럼 | 헤이딜러 필드 | 표본 값 |
|---|---|---|
| `core_listing.source_id` | `hash_id` | `EQrxmKyg` |
| `core_listing.price_current_won` | `price` ×10000 | 3,250만 |
| `core_listing.price_detail_won` | `previous_price` | 3,290만 (내린 값) |
| **`core_listing.price_origin_won`** | ★★ `factory_price` ×10000 | **6,580만** ← ★ **신차가를 준다** |
| `core_listing.year_month` | `initial_registration_date` | 2021-04-29 → `202104` |
| `core_listing.form_year` | `year` | 2021 |
| `core_listing.mileage_km` | `mileage` | 91,243 |
| `core_listing.trim_badge` | `grade_name` · `grade_part_name` | 520i M 스포츠 |
| `core_listing.color_ext_raw`·`_hex` | `exterior_description`·`exterior_color_codes` | 카본 블랙 · `#221772` |
| `core_listing.color_int_raw`·`_hex` | `interior_description`·`interior_color_codes` | 검정 다코타 가죽 · `#000000` |
| `core_listing.options_choice_json` | ★ `options[]` `{name, choice, availability}` | 선루프 loaded · 통풍시트 **absent** |
| `core_listing.model_catalog_key` | `model_hash_id` · `model_group_hash_id` | `23ryQ4` · `aMKrwk` |
| `core_listing.photo_list_json` | `image_urls` · `inside_image_urls` | S3 |
| `core_listing.subscribe_cnt` | `stars_count` | 75 |
| `core_listing.sales_status` | `sale_status` | `listed` |
| `core_record.accident_total_cnt`·`accident_my_cost` | ★ `rich_view_tags` 「보험 2건 ∙ 452만원」 | 2건 · 452만 |
| `core_record.owner_change_cnt` | ★ `tags` 「1인 소유」 | 1 |
| `warranty.site` 사이트 검증 | ★ `tags` 「**eye 인증**」 | 있음 |
| — 사고 등급 | ★ `tags` 「**완전무사고**」 / 「무사고」 | 두 단계다 |

```
★★★ ★ `factory_price` — ★ 신차가를 주는 ★ 유일한 사이트다
   ★ 엔카 말고는 아무 데도 안 주던 값이다.  ★ `value.depreciation` 75점이 여기서 산다
   ★ 그리고 ★ 다른 사이트 매물에 ★ 붙여 쓸 수 있다 (f-table 「사이트별 채우기」 ③)
★★ `options[].choice` 가 ★ loaded / absent 로 온다 — ★ 「없다」를 ★ 명시한다
   ★ 우리 「없음 0 · 모름 NULL」과 정확히 맞는다.  ★ absent 는 0 이고 NULL 이 아니다
★ `availability` 도 있다 — default(기본옵션) · available(선택가능) · unavailable(그 차엔 없음)
   ★ unavailable 은 ★ 그 차종에 없는 옵션이다.  ★ 감점하면 안 된다
★ 「완전무사고」와 「무사고」가 ★ 다른 딱지다.  ★ dict_enum 으로 갈라 받는다
★ 「eye 인증」이 ★ 사이트 검증 최고 단계다 (f-table 개정 428)
```

---

# 2d. ★ 현대 인증 표본 30건 검증 — ★ 1건일 때 못 본 것 셋

```
★ 매물번호는 ★ `data-favContsNo` 다 — ★ 개정 480 에 `data-id` 라 적은 것은 ★ 틀렸다
   `data-favContsNo="([A-Z]{3}\d{12})"` 로 뽑는다
```

| 필드 | 존재율 | 값 분포 |
|---|--:|---|
| 최초등록일 · 주행 · 배기량 · 외관컬러 | **30/30** | — |
| 내차피해이력 | **30/30** | 0건 14 · 1건 12 · 2건 2 · **5건 2** |
| **소유자 변경** | 30/30 | ★ **전부 「있음」** |
| 압류·저당 | 30/30 | 전부 「없음/없음」 |
| 정밀점검 항목 수 | 30/30 | ★ **272개 16 · 287개 12 · 268개 1 · 277개 1** |
| 성능점검기록부 | 30/30 | 전부 발행완료 |
| 보증 잔여(년·개월) | ★ **11/30** | — |
| 보증 잔여(km) | 29/30 | — |

```
★ ① 「소유자 변경」이 ★ 30/30 전부 「있음」이다 — ★ 건수가 아니라 ★ 유무만 준다
   ★ `owner_change_cnt` 에 ★ 1 로 넣으면 틀린다.  ★ NULL + 「있음」 플래그가 맞다
   ★ 인증중고차는 ★ 반드시 현대차가 한 번 소유하므로 ★ 늘 「있음」이다 — ★ 변별력이 없다
★ ② 정밀점검이 ★ 272 · 287 · 268 · 277 로 ★ 다르다 — ★ 「287개 고정」이 아니다
   ★ 차종·연식에 따라 항목 수가 다르다.  ★ 숫자를 그대로 저장한다
★ ③ ★ 보증 잔여가 ★ 11/30 뿐이다 — ★ 19건은 ★ 보증이 끝났다
   ★ 끝난 것은 ★ 0 이다 (확인한 값) · ★ 안 받은 것은 NULL.  ★ 가른다
★ 내차피해 ★ 5건짜리도 있다 — ★ 인증중고차라고 무사고가 아니다
```

---

# 3. ★ 보증 — 사이트마다 꼴이 다르다

| 사이트 | 원문 | `warranty_*_month` · `_km` 로 넣는 법 |
|---|---|---|
| 엔카 | 보증 종료일(날짜) | 오늘과 빼서 잔여 개월 계산 |
| **기아 CPO** | ★ `warranties[]` `{kind, remainingPeriod, remainingDistance}` | ★ **그대로** — `BA`·`AC`·`CM`→body · `EG`·`PT`·`EM`→power |
| **현대 인증** | ★ 「2년 10개월 남음 · 79,435km 남음」 | ★ 개월로 환산해 그대로 |
| KB차차차 | 「보증종료」 판정만 | ★ 종료면 **0** · 잔여를 모르면 **NULL** |
| K카 | ★ **`nwcaGurnteEngeSurvDt`·`GnrlSurvDt`·`…Milg`** | ★ **원문 그대로 — 계산하지 않는다 (개정 485)** |

```
필수  `warranty_body_month` · `warranty_body_km` · `warranty_power_month` · `warranty_power_km`
      ★ 네 칼럼이 이미 있다.  ★ 새로 만들지 마라
필수  기아 `kind` 는 ★ `dict_enum(site='kia_cpo', axis='warranty_kind')` 에 넣는다
      BA 차체 · AC 에어컨 · EG 엔진 · PT 동력전달 · EM 배기 · CM 소모품 (실측)
필수  ★ KB 「보증종료」는 ★ 0 이지 NULL 이 아니다.  ★ 확인한 것이다
      ★ K카는 ★ 상세를 받는다 (개정 485) — `tireDtlList` 잔량까지 온다
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
③ 우리 축(`taste.sunroof` · `taste.hud` · `taste.picked`)으로 옮기는 것은
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

## ③a. ★★ 참/거짓을 ★ `bool()` 로 가르지 마라 (개정 537)

```
★★ 08-23 실측 — `core_listing.warranty_extend` 가 ★ 문자열이었다 ('0' 3,836 · '1' 43)
   `bool(have)` 로 갈랐는데 ★ `bool('0')` 은 ★ 참이다
   → ★ 522건이 ★ 「엔카진단++」 ★ 만점을 받고 있었다 (개정 536 · 개발측이 찾았다)
★ 파이썬에서 ★ 빈 문자열만 거짓이다 — ★ '0' · 'N' · 'false' · 'null' 은 ★ 전부 참이다
```

## ★ 사이트마다 꼴이 다르다 (실측)

| 사이트 | 필드 | 오는 꼴 | 위험 |
|---|---|---|:--:|
| **엔카** | `warranty_extend` | ★ **문자열 `'0'` / `'1'`** | ★★ **터졌다** |
| **K카** | `szrMogeYn` · `fmltStruChngYn` · `ilgltStruChngYn` | ★ **문자열 `'N'`** | ★★ **위험** |
| **K카** | `dshbExchgYn` · `vinCnfmYn` | ★ **문자열 `'1'`** | ★★ **위험** |
| **K카** | `tirInpCmplYn` | ★ **문자열 `'Y'`** | ★★ **위험** |
| 기아 CPO | `reservation` · `orderable` | 진짜 불리언 | 안전 |
| 헤이딜러 | `is_starred` · `is_estimated_accident` | 진짜 불리언 | 안전 |
| 헤이딜러 | `is_time_deal` | `None` | 안전 |

```
★★ ★ K카는 ★ `Yn` 으로 끝나는 필드가 ★ 전부 문자열이다 —
   ★ `'N'` 을 `bool()` 로 재면 ★ 「압류 있음」이 된다.  ★ 정반대다
★ 기아·헤이딜러는 ★ 진짜 불리언이라 안전하다 — ★ 그래도 파서에서 가르지 않는다

필수  ★ `_truthy()` 하나로 ★ 모든 사이트를 지나게 한다
      거짓으로 볼 것 — `None` · `''` · `'0'` · `'n'` · `'no'` · `'false'` · `'none'` · `'null'`
      ★ 숫자는 ★ `!= 0`
      ★ 대소문자·앞뒤 공백을 ★ 없애고 본다
금지  ★ `bool(value)` · `if value:` 로 ★ 원문을 가르는 것
금지  ★ `value == 'Y'` 처럼 ★ 한 사이트 꼴에 맞추는 것 — ★ 다른 사이트에서 깨진다
검산  ★ 사이트를 붙일 때 ★ `Yn`·`is_`·`_flag` 로 끝나는 필드의 ★ 실제 값을 세어 본다
      ★ 25건이 전부 같은 값이면 ★ 뜻을 다시 본다 (K카 `dshbExchgYn` 이 그랬다 · 개정 524)
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
필수  ★ 기아 `merchandising` 의 판금·도장은 ★ 사고에 넣지 마라 (개정 485)
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

---

# ★★★ 08-23 추가 — ★ 다섯 사이트 ★ 칼럼 단위 매핑 (개정 574)

```
★★ 마스터 지적 08-23 — 「조사한 것 다 규격과 지침에 업데이트 하고 ★ DDL 매핑도 완료한 거지?」
★ 재 보니 ★ 안 돼 있었다 — ★ 보배·리본카·렉서스·볼보·벤츠·아우디가 ★ 이 문서에 ★ 0회였다
★ ★ 오판 #44 「받는 그릇을 안 보고 매핑한다」의 ★ 재발이다 (오판 #68)
★ `sql/ddl/02_core.sql` 을 열었다 — ★ `core_listing` ★ 117칼럼 · `core_record` ★ 37칼럼
```

## ① 리본카 (`REBORNCAR_API.md`) — ★ 모바일 UA 필수

| 원문 라벨 | `core_listing` 칼럼 | 타입 | 비고 |
|---|---|---|---|
| 매물코드 `C26081900017` | `source_id` | TEXT | 사이트맵에서 온다 |
| — | `site` | TEXT | `'reborncar'` 고정 |
| 연식 | `year_month` | TEXT | `YYYYMM` 로 정규화 |
| 주행거리 | `mileage_km` | INTEGER | `,`·`km` 제거 |
| 배기량 | `displacement_cc` | INTEGER | |
| 연료 | `fuel_raw` | TEXT | |
| 색상 | `color_ext_raw` | TEXT | |
| 차량번호 | `plate_hash` | TEXT | ★ 해시해서 넣는다 |
| **신차출고가** | **`price_origin_won`** | INTEGER | ★ 「7,110만원」 → 71,100,000 |
| 차량가격 | `price_current_won` | INTEGER | |
| **용도변경** | `core_record.use_business` / `use_gov` | INTEGER | ★ **있음 52%** — 갈린다 |
| 사고여부 | `core_record.accident_total_cnt` | INTEGER | 무사고=0 · 단순수리는 ★ 건수 미상 |
| 침수여부 | `core_record.flood_total_cnt` | INTEGER | 25/25 「없음」 |
| 안심환불 8일 | `site_service_marks_json` | TEXT | ★ 사이트 보장(②) |
| 냄새등급 | `site_condition_json` | TEXT | 양호·보통 |

```
★ 「신차가격대비 %」는 ★ 칼럼을 만들지 않는다 — ★ `price_origin_won` 과 `price_current_won` 으로 우리가 낸다
★ 「단순수리」를 ★ `accident_total_cnt` 몇으로 넣을지 ★ 아직 못 정했다 — ★ 원문에 건수가 없다
```

## ② 볼보 셀렉트 (`VOLVO_SELEKT_API.md`) — ★ 표본 12건 (개정 580)

| 원문 | `core_listing` 칼럼 | 비고 |
|---|---|---|
| 상세 슬러그 `ultra-b5-awd--dkbbgbb` | `source_id` | ★ 숫자가 아니다 |
| — | `site` | `'volvo_selekt'` |
| 가격 `62,000,000원` | `price_current_won` | ★ 원 단위 그대로 |
| 주행거리 `3,071 km` | `mileage_km` | |
| 모델 년도 | `form_year` | |
| 색상 · 내부 색상 | `color_ext_raw` · `color_int_raw` | |
| 연료 유형 | `fuel_raw` | ★ XC60 표본은 12/12 가솔린 |
| 전시장 | `dealer_shop` · `dealer_region` | 「에이치모터스 볼보 SELEKT 수원 전시장」 |
| 제조사 인증 | `site_pass_grade` | 180가지 점검 · `config/sites.json` 이 등급을 정한다 |
| ★ 사고이력 · 보증기간 | ★ **넣지 않는다** | ★ **딜러 소개글 자유 문장 · 12건 중 2건** |

```
★★★ ★ 사고·보증을 ★ 소개글에서 뽑지 않는다 — ★ 10/12 가 빈다.  ★ 「모름(NULL)」이다
★ 실측 문장이 ★ 「무사고 / ★ 보험이력 650만원 단순교환」이다 — ★ 무사고가 아니다
★ 검산 `S46-7`
```

## ③ BMW BPS (`BMW_BPS_API.md`)

| 원문 라벨 | 칼럼 | 비고 |
|---|---|---|
| 상품번호 | `source_id` | `it_id` |
| — | `site` | `'bmw_bps'` |
| 차량 등록일 `2025/04` | `reg_at` | ★ `YYYYMM` |
| 연식 | `form_year` | |
| 주행거리 | `mileage_km` | |
| 배기량 | `displacement_cc` | |
| 연료 · 변속기 | `fuel_raw` · `transmission` | 변속기 26/26 자동 |
| 외관색상 | `color_ext_raw` | |
| 차량번호 | `plate_hash` | ★ 해시 |
| 전시장 | `dealer_shop` · `dealer_region` | 「BPS 인천전시장」 |
| 사고유무 · 72가지 점검 | `site_condition_json` | ★ **전건 동일 — 축에 안 쓴다** (2a장) |
| ★ **가격** | **`price_current_won`** | ★★ **목록 카드 마지막 칸** (2d장).  ★ 만원 단위 → ×10,000 |
| ★ **「리스승계」** | `sell_type` · `price_current_won` ★ **NULL** | ★ **87건 중 37건(42.5%)** |
| 「판매완료」 | `sales_status` · `status` | 4건 |
| 리스 조건 | `lease_rent_info_json` · `sell_type` | 인수비용·월리스료·잔여개월·유예금 |

```
★★ ★ 가격을 못 읽으면 ★ `value.budget`(95)·`value.origin`(75) 이 빈다
★ ★ 리스 매물은 ★ `sell_type` 으로 갈라 ★ 리스·렌트 제외 규칙에 태운다
```

## ④ KB차차차 수입 일곱 — ★ 좁히는 코드만 더한다

```
★ 칼럼 매핑은 ★ `KBCHACHACHA_API.md` 3장이 이미 정한 것을 ★ 그대로 쓴다 —
  ★ 수입이라고 ★ 다른 칼럼이 필요하지 않다.  ★ `makerCode`·`classCode` 는 ★ 부르는 법이지 칼럼이 아니다
★ `site_manufacturer` 에 ★ 브랜드가 들어간다 (BMW·벤츠·아우디·볼보·렉서스)
★ `target_key` 는 ★ `dict_enum(axis='target')` 이 붙인다 — ★ X3·GLC·Q5·XC60·S60·NX·RX
```

## ⑤ 현대 인증 — ★ 잔여 보증 두 축 (`HYUNDAI_CERTIFIED_API.md` 2b)

| 원문 블록 | 칼럼 |
|---|---|
| 차체 및 일반부품 — 잔여 개월 | `warranty_body_month` |
| 〃 — 잔여 km | `warranty_body_km` |
| 동력전달 주요부품 — 잔여 개월 | `warranty_power_month` |
| 〃 — 잔여 km | `warranty_power_km` |

```
★★★ ★ 칼럼이 ★ 네 개로 이미 나뉘어 있다 — ★ DDL 을 열어 확인했다
★ ★ 그러므로 ★ 「일반과 동력이 같다」고 적은 개정 480 은 ★ 그릇과도 어긋났다
★ 「만료」 → ★ 0 · 못 읽음 → ★ NULL (2b-②)
```

## ⑥ 보배드림 (`BOBAEDREAM_API.md`) — ★ 끝 (개정 584 · 표본 20건)

```
★ 칼럼 표는 ★ `BOBAEDREAM_API.md` 1a 가 정본이다 — ★ 그릇을 열고 썼다
★★★ ★ 「무사고」 문구는 ★ 20건 중 ★ 4건뿐인 ★ 판매자 글이다 — ★ 쓰지 않는다
   ★ ★ 대신 ★ 머리 요약줄의 ★ **「수리이력 N · 보험이력 N」** 이 ★ 구조화된 값이다
   → `core_record.repair_cnt` · `core_record.insurance_cnt`
★★ ★ 가격·지역은 ★ 라벨 뒤가 아니라 ★ 머리 요약줄에 있다 — ★ 라벨로만 찾으면 ★ 0/20 이다
★ ★ `자동 Array단` 은 ★ 사이트가 낸 깨진 값이다 — ★ 그대로 저장하고 정규화에서 거른다
```

## ⑦ 렉서스 인증 (`LEXUS_CERTIFIED_API.md`) — ★ 끝 (개정 583 · 표본 22건)

```
★ 칼럼 표는 ★ `LEXUS_CERTIFIED_API.md` 1b 가 정본이다 — ★ 그릇을 열고 썼다
★★★ ★ `car_info.warranty` 「2030년 10월까지 (120,000km)」 —
   ★ 만료일 ＋ 상한 km 를 함께 준다.  ★ 22건에서 ★ 10가지로 갈린다
   → `warranty_site_until` · `warranty_site_km`
   ★ ★ KB·엔카가 ★ 안 주는 값이다 — ★ `warranty.site`(36) 를 진짜로 채운다
★ `release_price` → `price_origin_won` (★ 신차가 · `value.origin` 75)
★ `accident_history` 는 ★ 22/22 「무사고」다 → ★ 축에 안 쓴다 (사이트 보장 후보)
★ `payment.isLease` → `sell_type` 으로 리스 제외에 태운다
```

---

# ★ 아직 매핑을 안 쓴 것 — ★ 정직하게 적는다

```
볼보 — ★ **끝 (개정 580 · 표본 12건)**
보배드림 · 렉서스 인증 — ★ ⑥⑦ 에 ★ 「왜 아직 못 썼는가」를 적어 두었다
  보배 — ★ 그릇을 열고 다시 쓴다 · 렉서스 — ★ 표본이 1건이라 20건으로 늘린 뒤에 쓴다
★ ★ 「규격 완」이라 부르지 않는다 (오판 #44 · #52 · #59)
검산  S46-5 ★ 신설 — ★ `docs/*_API.md` 마다 ★ `core_listing` 칼럼명이 ★ 한 번은 나오는가
      ★ 안 나오면 ★ 「우리 축 대응」만 하고 ★ 그릇을 안 본 것이다
```

---

# ★★★ `warranty.site` (36) — ★ 사이트별로 ★ 무엇을 주는가 (개정 588)

```
★ 축이 묻는 것 — 「★ 이 차를 사면 ★ 보증이 ★ 얼마나 남아 있는가」
★ ★ 사이트마다 ★ 주는 것이 ★ 전혀 다르다.  ★ 한 줄로 모아 둔다
```

| 사이트 | 무엇을 주나 | 채울 수 있나 | 근거 |
|---|---|:--:|---|
| ★ **렉서스 인증** | ★ **「2030년 10월까지 (120,000km)」** — 만료일 ＋ 상한 km | ★★ **된다** | 22/22 · 10가지 |
| ★ **현대 인증** | ★ **일반·동력 잔여 개월 ＋ 잔여 km** (블록 여섯) | ★★ **된다** | 65건 · 66.2% 가 다름 |
| 볼보 셀렉트 | 「보증기간 : 2031.01.29」 ★ **딜러 소개글** | ✘ **안 된다** | 12건 중 **2건** |
| BMW BPS | ★ 아직 못 쟀다 | ? | 밀린일 85 |
| 기아 CPO | 규격 3장 참조 | ? | — |
| 리본카 | ★ 「안심환불 8일」 — ★ 보증이 아니다 | ✘ | 25/25 동일 |
| KB차차차 · K카 · 엔카 · 보배 | ★ **안 준다** ★ [실측 08-29 · K카 상세 표본 8건 `newCar*` 0/8 · 보배 원문 칸 1/10] | ✘ | — |

```
★★★ ★ 여기서 나오는 판단 —
   ★ 인증중고 사이트(렉서스·현대)는 ★ 건수가 작아도 ★ 값이 있다
   ★ ★ `warranty.site` 36점은 ★ 그 사이트에서만 ★ 진짜로 채워진다
   ★ ★ 나머지 사이트는 ★ **「모름(NULL)」이다 — ★ 0점이 아니다** (개정 325)
금지  ★ 「인증중고차니까 보증이 있겠지」로 ★ 만점을 지어 주는 것 (명령서 금지 12)
      ★ 볼보가 정확히 그 함정이다 — ★ 소개글에 「무사고」라 적혀 있는데
        ★ 같은 문장에 ★ 「보험이력 650만원 단순교환」이 있다
필수  ★ `config/sites.json` `site_grade_rule` 에 ★ 사이트별 근거를 적는다 —
      ★ ★ 이 문서에 ★ 점수를 적지 않는다.  ★ 배점은 마스터 몫이다 (원칙 1-a)
검산  S46-8 ★ 신설 — `warranty.site` 가 채워진 매물의 `site` 가
      ★ 렉서스·현대·기아 CPO 밖이면 ★ 실패 (지어낸 것이다)
```

---

# ★★★ 사이트 열하나 — ★ 매핑이 빠진 곳 (개정 703 · 마스터 지시 08-24)

```
★★ 08-24 — ★ 사이트가 ★ **열하나**가 됐다.  ★ 이 문서는 ★ **아홉**만 담고 있다
★ ★ 빠진 것 — ★ **보배드림 · 렉서스 인증**
★ ★ 그리고 ★ 새로 뚫린 넷(헤이딜러·리본카·볼보·BMW)은 ★ 칸이 얕게 적혀 있다
```

## ★ 개발측이 채운다 — ★ 가이드는 ★ 무엇을 채울지 정한다

| 사이트 | 지금 | 할 것 |
|---|:--:|---|
| ★ **보배드림** | ★ **없다** | ★ 칸을 열어 ★ `core_listing` 매핑을 적어라 |
| ★ **렉서스 인증** | ★ **없다** | 〃 · ★ `car_info.warranty` 가 만료일＋상한km 를 준다 |
| ★ **헤이딜러** | 얕다 | ★★ **옵션이 ★ 이름 ＋ `choice` ＋ `availability`** 로 온다 · ★ `previous_price` |
| ★ **리본카** | 얕다 | ★ **승차정원**을 준다 (「5인승」) |
| ★ **볼보** | 얕다 | ★ VIN 이 있는지 ★ 재서 적어라 — ★ 없으면 짝짓지 않는다 |
| ★ **BMW** | 얕다 | ★ 가격이 ★ **목록 카드에** 있다 (상세에 없다) |

```
필수  ★ 사이트마다 ★ **원문 칸 → `core_listing` 칼럼**을 ★ 한 줄씩 적어라
필수  ★ ★ **어느 칸에도 안 들어가는 값**은 ★ 따로 모아 적어라
      ★ ★ 그것이 ★ **DDL 에 칸을 더할 목록**이다 (★ 제원 두 칸이 그랬다)
필수  ★ 값이 ★ **안 오는 칸**은 ★ 「없다」가 아니라 ★ **`—`(안 준다)**로 적는다 (`UI_REVIEW` 12장)
금지  ★ 칸 이름만 세고 ★ 값이 오는지 안 보는 것 (오판 98)
검산  ★ `S46-53` — ★ `config/sites.json` 의 사이트가 ★ 이 문서에 다 있는가
```

## ★★★ 그리고 — ★ 사이트마다 ★ **무엇을 주는지**를 표로

```
★ 지금은 ★ 사이트별로 ★ 흩어져 있다
★ ★ **한 표에 모아야** ★ 「이 축은 어느 사이트가 주나」가 보인다
★ ★ 그것이 ★ 견주는 일(`CROSS_SITE_COMPARE.md`)의 ★ 바탕이다

필수  ★ 표를 ★ **축 × 사이트**로 만든다 — ★ 26축 × 11사이트
      ★ ★ 칸에는 ★ `○`(준다) · `—`(안 준다) · `?`(못 읽었다) 셋만
필수  ★ 이 표는 ★ **개발측이 실측으로 채운다**.  ★ 가이드가 짐작해 적지 않는다
```

---

# ★★★★★ 08-29 — ★ 성능점검 여섯 축은 ★ **원문에 있는데 파서가 안 뽑는다** (마스터 지시)

```
★★★ 마스터 — 「★ **앵커만큼 정보를 다 나는 확인했다고 보는데 ★ 왜 여전히 못 찾고 있는지
   ★ 이건 수집의 문제가 되지 않을까 싶어.  ★ 파서에서 갖고 오는 부분을 추가로 찾아야 되는 게 맞을 것 같아**」

★ **마스터 말씀이 맞다.  ★ 재서 확인했다** [실측 08-29]
```

## ★ ① 그 여섯 축이 ★ 어느 칼럼을 읽나 (코드에서 확인)

| 축 | 점 | 읽는 칼럼 | 코드 |
|---|--:|---|---|
| 골격 | 30 | `inspection_panels` | `analyze/axis/state.py:109` `_frame` |
| 외판 | 20 | `inspection_panels` | `:129` `_outer` |
| 누유 | 10 | `inspection_inner_json` | `:196` `_leak` |
| 보험 수리비 | 20 | `accident_my_cost` | `:151` `_repair` |
| 특수 사고 | 15 | `total_loss_cnt` · `flood_total_cnt` · `flood_part_cnt` | `:162` `_special` |
| 진정성 | 5 | 〃 계열 | 〃 |

## ★★ ② 그 칼럼을 ★ **어느 파서가 넣나** — ★ 세었다

| 칼럼 | 넣는 파서 |
|---|---|
| ★ ~~`inspection_panels` 하나도 없다~~ | ★ **08-29 정정 — 칼럼 이름은 `inspection_panel_json` 이고 ★ 엔카가 넣는다** (아래 절) |
| ★ `inspection_inner_json` | ★ **엔카 하나** |
| `accident_my_cost` | 엔카 · K카 |
| `total_loss_cnt` · `flood_total_cnt` | 엔카 · K카 · KB |

```
★★★ ★ 곧 ★ **골격 30 ＋ 외판 20 = 50점이 ★ 엔카에서도 파서로는 안 들어온다**
   ★ ★ `inspection_panels` 를 ★ **아무 파서도 안 채운다**
★ ★ 누유 10 은 ★ **엔카만** 채운다 — ★ 아홉 사이트가 다 0점이다
```

## ★★★ ③ 원문에는 있나 — ★ 표본 5건씩 두드려 셌다 [실측 08-29]

| 사이트 | 판금 | 교환 | 용접 | 골격 | 누유 | 성능 | 부식 | 보험이력 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| ★ **KB차차차** | ★ 5/5 | 5/5 | ★ 5/5 | ★ 5/5 | — | 5/5 | 5/5 | ★ 5/5 |
| ★ **리본카** | ★ 5/5 | 5/5 | ★ 5/5 | — | 1/5 | 5/5 | 5/5 | — |
| K카 | — | 2/5 | — | — | 3/5 | 3/5 | 3/5 | 1/5 |
| 헤이딜러 | 1/5 | — | — | — | — | 5/5 | — | — |

```
★ K카는 ★ 별도 경로가 ★ 따로 있다 — `GET /bc/car-insp/photo/cm?i_sCarCd={id}`
   ★ ★ 실측 08-29 — 200 · 462B · `inspDetail` 에 ★ `acdtHistYn`·`smplReprYn`·`pfmncNewVerYn`·`imgList`
   ★ ★ **우리 수집기가 이 경로를 안 부른다**

★★★★ ★ **결론 — ★ 「사이트가 안 준다」가 아니다.  ★ 우리가 안 뽑는다**
   ★ ★ KB·리본카는 ★ **판금·용접·골격이 5/5 다 원문에 있다**
   ★ ★ 그러므로 ★ 이 여섯 축은 ★ **갈래 ⑥(80%)이 아니다.  ★ ⓐ 우리 결함이다**
★ ★ 아직 못 잰 곳 — ★ 볼보·렉서스·BMW·보배·현대인증.  ★ 다음 바퀴에 잰다
```

---

# ★★★★★ 08-29 전체 점검 — ★ **누가 잘못인가** (마스터 지시)

```
★★★ 마스터 — 「★ **수집 쪽하고 파서 쪽에 대해서 전체적으로 한번 체크를 해 줘야 될 것 같은데,
   ★ 아무리 봐도 개발팀이 실수를 했든지 ★ 아니면 규격을 엉망으로 만들었든지**」

★ **쟀다.  ★ 답은 ★ 규격 잘못이다 — ★ 개발측이 아니다**
```

## ★ ① 원문에는 다 있다 — ★ 다섯 사이트를 마저 뚫었다 [실측 08-29 · 표본 5건씩]

| 사이트 | 성능 | 점검 | 사고 | 판금 | 교환 | 용접 | 보험이력 |
|---|--:|--:|--:|--:|--:|--:|--:|
| 보배드림 | 5/5 | 5/5 | 5/5 | — | 2/5 | — | 5/5 |
| 현대인증 | 5/5 | 5/5 | 5/5 | — | — | — | — |
| ★ 볼보(상세) | 5/5 | 5/5 | 5/5 | 2/5 | 3/5 | — | 2/5 |
| BMW(상세) | 1/5 | 5/5 | 5/5 | — | 1/5 | — | 2/5 |
| 렉서스 | — | 5/5 | — | — | 5/5 | — | — |

```
★ 앞서 잰 것 — KB 판금·용접·골격 5/5 · 리본카 판금·용접 5/5 · K카 별도 경로 200
★★ ★ 곧 ★ **열한 사이트 원문에 ★ 성능점검이 다 있다.  ★ 「사이트가 안 준다」는 ★ 없다**
★ ★ 볼보만 ★ **목록 카드에는 없고 ★ 상세에 있다** — ★ 그런데 우리는 ★ 상세를 안 받는다
```

## ★★ ② 파서가 채우는 칼럼 수 — ★ `core_listing` 119칼럼 대비

| 파서 | 채우는 칼럼 |
|---|--:|
| ★ 엔카 | ★ **91 / 119** |
| K카 | 32 | 
| KB · 현대인증 | 26 |
| 기아 CPO | 23 |
| 헤이딜러 | 20 |
| 리본카 | 17 |
| 보배 | 16 |
| ★ 볼보 | ★ **14** |

```
★★ ★ **엔카가 91 이고 나머지는 14~32 다.**  ★ 이것이 ★ 「앵커만 등급이 나오는」 뿌리다
★ ★ 아무 파서도 안 넣는 칼럼이 ★ **21개**다 —
   `inspection_status` · `record_status` · `inspection_summary_status` ·
   `ev_battery_status` · `parsed_at` · `parse_version` … ★ 그리고 ★ `plate_hash`
```

## ★★★★ ③ 판정 — ★ **규격이 안 적어서다**

| 규격 절 | 성능점검 칼럼이 적혀 있나 |
|---|---|
| 헤이딜러 (2c) | `accident_my_cost` 하나 |
| 리본카 (①) | `flood_total_cnt` 하나 |
| ★ 볼보 (②) | ★ **없다** |
| ★ BMW (③) | ★ **없다** |
| ★ 보배 (⑥) | ★ **없다** |
| ★ 렉서스 (⑦) | ★ **없다** |

```
★★★ ★ **개발측은 규격대로 만들었다.**  ★ 규격이 ★ 그 칼럼을 ★ **안 적었다**
   ★ ★ 이 문서 머리에 ★ 가이드가 이미 자백해 두었다 —
     「★ 개정 464·473·480·481 에서 ★ **스키마를 안 보고 매핑을 썼다** …
       ★ 어느 테이블 어느 칼럼에 어떤 타입으로 넣는지 ★ **안 정했다**」
   ★ ★ **그 자백이 닫히지 않았다.**  ★ 사이트 절 넷이 아직 그 상태다
★ ★ 그리고 ★ `inspection_panels` 는 ★ **엔카 규격에도 없다** — ★ 그래서 ★ 엔카조차 0점이다
★ ★ 곧 ★ **골격 30 ＋ 외판 20 = 50점이 ★ 열한 사이트 전부 0점**이다
```

★ **할 일** — ★ 가이드가 ★ 사이트 절 넷(볼보·BMW·보배·렉서스)에 ★ **칼럼 매핑을 채운다**.
  ★ ★ 그다음 ★ 개발측이 파서를 고친다.  ★ **규격이 먼저다** (명령서 1c)

---

# ★★★★★ 08-29 정정 — ★ **앞 절의 「판금 5/5」는 틀렸다** (마스터 지적)

```
★★★ 마스터 — 「★ **판금은 대부분 없네.  ★ 어떻게 할까.  ★ 엔카는 제대로 주나?**」

★ **둘 다 다시 쟀다.  ★ 앞 절이 두 군데 틀렸다** (오판 192)
```

## ★ ① 엔카는 ★ **제대로 준다** — ★ 내가 칼럼 이름을 틀렸다

```
★ 앞 절에 ★ 「`inspection_panels` 를 채우는 파서가 하나도 없다」고 적었다.  ★ **틀렸다**
★ ★ `inspection_panels` 는 ★ **스냅샷 이름**이고 ★ DB 칼럼은 ★ **`inspection_panel_json`** 이다
   `parse/encar/mapping.py:286`  `"inspection_panel_json": _json(body.get("outers"))`
   `store/core.py:571`           `inspection_panels=jload("inspection_panel_json")`
★ ★ 곧 ★ **엔카는 `outers` 를 그대로 넣고 있다.  ★ 골격·외판이 엔카에서는 채워진다**
★ ★ 그래서 ★ **A 등급 166건이 전부 엔카**인 것이다 (개정 881) — ★ 앞뒤가 맞는다
```

| 칼럼 | 넣는 파서 |
|---|---|
| `inspection_panel_json` (골격·외판) | ★ **엔카만** |
| `inspection_inner_json` (누유) | ★ **엔카만** |
| `accident_my_cost` (보험 수리비) | 엔카 · K카 |

## ★★ ② 「판금 5/5」는 ★ **매물 값이 아니라 안내문이었다**

```
★ KB 상세에서 ★ 「판금」이 나온 자리를 ★ 열어 보니 —
   「★ 자동차관리법 시행규칙에 의해 ★ 주요 골격 부위에 대한 ★ **판금, 용접 수리 교환**을
     했을 경우에 사고로 판정됩니다」 ← ★ **접힌 안내 팝업**이다.  ★ 매물마다 똑같다
★★ ★ 곧 ★ 내가 센 「판금 5/5 · 용접 5/5」는 ★ **그 안내문을 센 것**이다.  ★ 값이 아니다
★ ★ **낱말을 세면 안 된다** — ★ 기준서 ㉮ 「200 이 왔다와 제대로 왔다는 다르다」의 ★ 낱말 판이다
```

## ★★★ ③ 그러면 KB 는 무엇을 주나 — ★ 구조로 봤다

```
★ 매물마다 다른 ★ **판정 한 줄**을 준다 —
   「★ 해당 차량은 ★ **프레임 정상**과 ★ **외부패널 정상**을 진단받은 무사고 차량입니다」
★ 그리고 ★ 목록·상세 머리에 ★ 「성능점검 **상세보기**」 · 「보험이력 **2건**」이 있다
★★ ★ **판마다의 등급(엔카 `outers` 같은 배열)은 ★ 그 「상세보기」 안에 있다** —
   ★ ★ 우리는 ★ **그 화면을 안 받는다**.  ★ 경로를 아직 못 찾았다 [08-29 · 못 찾음]

★ 그러므로 ★ 지금 KB 에서 ★ 채울 수 있는 것은 —
   ○ ★ **프레임 정상 / 외부패널 정상** ← ★ 골격·외판을 ★ **두 단계로는** 채운다
   ✘ ★ 판마다의 판금 몇 장인지는 ★ **아직 못 받는다**
```

★ **못 찾은 것을 「없다」로 적지 않는다** — ★ KB 「성능점검 상세보기」 경로는 ★ 다음 바퀴에 찾는다

---

# ★★★★ 08-29 — ★ 사이트 절 넷에 ★ **칼럼 매핑을 채운다** (밀린일 G12 · 오판 191)

```
★ 오판 191 — ★ 볼보·BMW·보배·렉서스 절에 ★ **성능점검 칼럼이 아예 없었다**.
   ★ ★ 개발측은 ★ 규격대로 만들었다 — ★ 규격에 없는 칼럼은 못 만든다
★ ★ 여기서 채운다.  ★ **표본으로 잰 것만 적는다.  ★ 못 잰 칸은 「못 잼」이라 적는다**
```

## ★ ① 볼보 셀렉트 — ★ 상세를 받아야 한다

| 원문 | `core_listing` 칼럼 | 실측 |
|---|---|---|
| 카드 `27,000,000원` | `price_current_won` | ★ 12/12 (카드) |
| 카드 주행 · 연식 | `mileage_km` · `year_month` | ★ 있다 |
| 상세 「성능·점검·사고」 | `inspection_panel_json` ★ **꼴 미확인** | ★ 5/5 (낱말) |
| 상세 「판금」 2/5 · 「교환」 3/5 | 〃 | ★ **값인지 안내문인지 못 쟀다** |
| 슬러그 | `site_model` · `site_model_group` | ○ |

```
★ ★ **지금 상세를 아예 안 받는다** (`tools/collect_volvo.py`) — ★ 명령서 1b-n
★ ★ 「판금 2/5」가 ★ **매물마다 다른 값인지** ★ 다시 재야 한다 (리본카가 안내문이었다 · 오판 192)
```

## ★ ② BMW BPS — ★ 값·주행·연식이 상세에 있다

| 원문 | 칼럼 | 실측 |
|---|---|---|
| `판매가:` · `차량가격 :` · `판매 가격 :` | `price_current_won` | ★ **꼴이 셋** · 3/3 |
| `주행거리 ([\d,]+) km` | `mileage_km` | ★ 3/3 (27,300·34,119·24,130) |
| `연식 (\d{4})` · `차량 등록일 ([\d/]+)` | `form_year` · `year_month` · `reg_at` | ★ 3/3 |
| `사고유무 (\S+)` | `accident_history_summary` | ★ 3/3 (「무」) |
| `(\d+) 가지 점검 (\S+)` | `site_pass_type` · `site_pass_grade` | ★ 3/3 (「72가지·없음」) |
| `(압류 \d+건, 저당 \d+건)` | `seizing_cnt` · `pledge_cnt` | 2/5 |

```
★ 함정 둘 — ★ 「신차가: 약 …」은 ★ **판매가가 아니다** · ★ 쪽 아래 거르개 「1500 만원 …」을 값으로 잡지 마라
★ 503 이 잦다 — ★ **네 번 재시도** (규격 08-29 절)
```

## ★ ③ 보배드림 — ★ 파서가 못 읽는 자리 둘

| 원문 | 칼럼 | 실측 |
|---|---|---|
| `연식` 칸 `YY/MM/DD` · ★ `YYYY/MM` | `year_month` · `form_year` | ★ **10/10 오는데 파서가 8** |
| ★ `신차가격: 15,953 만원` | ★ `price_origin_won` | ★ **1/10 · 읽는 줄이 없다** |
| `수리이력 N` · `보험이력 N` | `core_record.repair_cnt` · `insurance_cnt` | 5/5 |
| 「성능점검 상세보기」 | ★ **경로를 못 찾았다** | — |

## ★ ④ 렉서스 인증 — ★ 목록이 거의 다 준다

| 원문 (`car_list[]`) | 칼럼 | 실측 |
|---|---|---|
| `price` | `price_current_won` | ★ 10/10 |
| ★ `release_price` | ★ `price_origin_won` | ★ **10/10** |
| `year` · `mileage` | `form_year` · `mileage_km` | ★ 10/10 |
| `model_name` · `class_name` | `site_model` · `site_model_group` | 10/10 |
| `branch` · `color` · `sell_type` | `dealer_shop` · `color_ext_raw` · `sell_type` | 10/10 |
| 상세 「교환」 5/5 · 「점검」 5/5 | ★ **꼴 미확인** | ★ 못 쟀다 |

```
★★ ★ **넷 다 ★ 성능점검의 「꼴」을 아직 못 쟀다** — ★ 낱말만 봤다.
   ★ ★ **파일이 쌓이면 그 자리에서 센다** (설계 2걸음).  ★ 그 전에 파서를 만들지 않는다
★ ★ 값·주행·연식·신차가는 ★ **지금 바로 만들 수 있다** — ★ 위 표가 자리를 다 짚었다
```
