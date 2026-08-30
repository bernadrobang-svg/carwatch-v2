# 헤이딜러 API · 매핑 규격

```
version  SPEC-2026.08.29-r997
follows  `f-table.md` · `MULTISITE_MAPPING.md`
sources  개정 866 · 실측 08-29
checks   S46-5 · S46-31
```

---

# ★★★ 0. 열렸다 — ★ **토큰이 필요했다** (개정 694 · 08-24)

```
★★★ ★ 500 은 ★ **「고장」이 아니라 ★ 「토큰 없이 불렀다」**였다
   ★ ★ 서버가 ★ 인증 실패를 ★ **500 으로** 돌려주어 ★ 가이드가 ★ 두 번 오판했다 (#97)
★ ★ 마스터가 ★ 주소를 주셔서 ★ 화면 본문에서 ★ 부르는 꼴을 찾았다
```


---

# 0a. ★★★ 차종 해시 — ★ 마스터가 열여섯을 주셨다 (개정 695 · 실측 08-24)

```
★ 부르는 법 — ★ `?brand={해시}&model-group={해시}&model={해시}`
★ ★ 셋 다 ★ 여섯 자.  ★ 지어낼 수 없다 — ★ 마스터가 눌러 주셔야 나온다
★ ★ 아래는 ★ 실제로 불러서 ★ 차명과 건수를 ★ 확인한 것이다
```

| 차종 | `brand` | `model-group` | `model` | 건수 | 우리 등록 |
|---|---|---|---|--:|---|
| **더 뉴 그랜저 IG** | `xoKegB` | `rk0Jmy` | `5oqNnp` | 10 | ★ `GRANDEUR_LPG` — ★ **3.0 LPi 있다** |
| **그랜저 IG** | `xoKegB` | `rk0Jmy` | `Yp5PJo` | 10 | 〃 — ★ 3.0 익스클루시브 |
| **더 뉴 스포티지 5세대(NQ5)** | `2oV0gK` | `relJ0M` | `4yyym4` | 2 | `SPORTAGE_LPI` |
| **더 뉴 G70** | `vgm7Do` | `YyGdqe` | `moOK9o` | 5 | `G70_20T` |
| **더 올 뉴 G80 FL** | `vgm7Do` | `zMbV3M` | `o6eYZ3` | 7 | ★ `G80_25T` — ★ **2.5T 맞다** |
| **더 올 뉴 G80** | `vgm7Do` | `zMbV3M` | `23r7Vo` | 10 | 〃 |
| ★ **e-G80** | `vgm7Do` | `zMbV3M` | `EpbKE4` | 2 | ★ `G80_EV` |
| ★ **GV60** | `vgm7Do` | `rk0bBy` | `d4BOG3` | 6 | ★ `GV60` |
| ★ **e-GV70** | `vgm7Do` | `peqqRe` | `Mo7j63` | 1 | ★ `GV70_EV` |
| ★ **그랑 콜레오스** | `xgrX7o` | `1yRqnM` | `4LrrVo` | 10 | ★ `KOLEOS_HEV` — ★ **1.5 E-TECH 있다** |
| ★ **BMW X3 (G01)** | `0W5AWm` | `RyW75y` | `ZokDMp` | 10 | ★ `X3_IMPORT` |
| ★ **렉서스 RX450h 4세대** | `EW3do3` | `relm4k` | `Eoml03` | 1 | ★ `RX_IMPORT` |
| ★ **볼보 XC60 2세대** | `Jo6rOo` | `VMjr8M` | `qpRDG3` | 10 | ★ `XC60_IMPORT` |
| ★ **볼보 S60 3세대** | `Jo6rOo` | `KM5VJy` | `n3Qkxp` | 5 | ★ `S60_IMPORT` |
| ★ **테슬라 모델 Y 주니퍼** | `xozX5g` | `8enPWM` | `4NQQ7p` | 10 | ★ `MODEL_Y` |
| ★ **테슬라 모델 Y** | `xozX5g` | `8enPWM` | `N49KGo` | 10 | 〃 |
| ★ **벤츠 GLC (X254)** | `lgBNgw` | `Vy2JKy` | `4LrBOo` | 2 | ★ `GLC_IMPORT` |
| ★ **벤츠 GLC (X253)** | `lgBNgw` | `Vy2JKy` | `ep8gKo` | 10 | 〃 |
| ★ **아우디 Q5 (FY)** | `RgMAjg` | `aMKvYk` | `5oqano` | 3 | ★ `Q5_IMPORT` |
| ★ **렉서스 NX300h** | `EW3do3` | `1yOzZM` | ★ **없음** | 10 | ★ `NX_HEV` |
| ★ **볼보 V60 크로스컨트리 2세대** | `Jo6rOo` | `0yNNgy` | `Z40d04` | 2 | ★★ **`V60CC_IMPORT`** — 마스터 확정 08-24 |
| ★ **볼보 XC40** | `Jo6rOo` | `zyx6mk` | `wo2dG4` | 10 | ★★ **`XC40_IMPORT`** — 마스터 확정 08-24 |

```
★★★ ★ **열여섯이 ★ 다 우리 등록 차종이다** — ★ 마스터가 ★ 「★ 둘 다 대상으로 추가해.  ★ 전 사이트 대상이야」 하셨다
   ★ ★ 차종이 ★ **18 → 20종**이 됐다 (`XC40_IMPORT` · `V60CC_IMPORT`)
★ ★ 브랜드 해시 — 현대 `xoKegB` · 기아 `2oV0gK` · 제네시스 `vgm7Do` · ★ 테슬라 `xozX5g` · ★ 벤츠 `lgBNgw` · ★ 아우디 `RgMAjg` ·
   르노코리아 `xgrX7o` · BMW `0W5AWm` · 렉서스 `EW3do3` · 볼보 `Jo6rOo`
★ ★ 한 쪽에 ★ **10건**이 상한이다 — ★ 10 이면 ★ 다음 쪽이 있다.  ★ `page` 를 올려라
★★ ★ **갈래가 섞여 온다** — ★ 그랜저에 ★ 2.5 가솔린과 ★ 3.0 LPi 가 함께 있다
   ★ ★ `fuel_match` 로 ★ 우리 쪽에서 걸러라 (마스터 「제외해」 · `UI_REVIEW` 9a)
필수  ★ 이 표를 ★ `config/targets.json` 의 ★ `site_query.heydealer` 에 넣어라
필수  ★ V60 크로스컨트리 · XC40 도 ★ **받는다** — ★ 마스터 확정 08-24.  ★ `targets.json` 에 넣었다
★★ ★ **08-25 — ★ 여섯을 더 받아 ★ 19/20 종이 됐다** (★ `EX60` 만 빠졌다 — ★ 아직 매물이 없다)
   ★ ★ **`model` 이 없는 것도 있다** — ★ 렉서스 NX 는 ★ `brand`＋`model-group` 만으로 걸린다
   ★ ★ **한 차종에 ★ 해시가 여럿일 수 있다** — ★ 세대가 다르면 (GLC X253·X254 · 모델Y 주니퍼)
```

---

## 0-1. ★ 여는 법 — ★ 두 걸음

```
① 토큰 받기
   POST  https://api.heydealer.com/v2/customers/web/initialize_app/
   헤더   Content-Type: application/json · App-Os: web
   본문   {"referrer_url": "https://www.heydealer.com/"}     ★ ← 없으면 400
   →     {"token": "eyJhbGciOi…"}                          ★ JWT

② 목록 받기
   GET   https://market-api.heydealer.com/v2/customers/web/market/cars/
         ?order=recommendation&view_type=compact&page=1
   헤더   App-Os: web
         Authorization: Bearer {token}                      ★ ← 없으면 500
   →     200 · 평문 JSON · ★ **리스트로 온다** (감싸는 객체가 없다)
```

```
★ `view_type` 은 ★ **`image` · `rich` · `compact`** 셋뿐이다 (★ 서버가 오류로 알려 준다)
★ ★ `compact` 가 ★ 가장 가볍다.  ★ 표본 ★ 55,336B
★ 좁히기 — ★ `?brand={해시}&model={해시}&model-group={해시}` (★ 여섯 자 해시 · 세 층)
★ `filters/` 는 ★ 토큰 없이도 200 — ★ 연료·차형·가격·주행·연식 목록을 준다
```

## 0-2. ★★ 한 건에 ★ 상세가 통째로 온다 — ★ 상세를 따로 안 불러도 된다

| 무엇 | 칸 |
|---|---|
| 열쇠 | `hash_id` |
| 차종·트림 | `model_part_name` · `grade_part_name` · `grade_name` · `detail_name` |
| ★ **값** | `price` · ★ **`previous_price`**(전 가격) · ★ **`factory_price`**(신차가) · `savings_total` |
| 제원 | `year` · `mileage` · `initial_registration_date` |
| 색 | `exterior_description` · `interior_description` ＋ 색상 코드 |
| ★★ **옵션** | ★ 이름(한글) ＋ `choice`(`loaded`·`absent`·`loaded_aftermarket`) ＋ `availability`(`default`·`available`·`unavailable`) |
| 사고 | `tags` — 「완전무사고」·「무사고」·★ 「보험 1건 ∙ 595만원」 |
| 사진 | `image_urls` · `inside_image_urls`(실내) |
| 상태 | `sale_status` = `listed` · `offered_at` |

```
★★★ ★ **옵션이 ★ 우리가 가장 못 채우던 축이다**
   ★ 엔카는 ★ 코드만 준다.  ★ 헤이딜러는 ★ **한글 이름 ＋ 장착 여부**를 준다
   ★ ★ 실측에 ★ 「고속도로 주행 보조2」(옵션 이름 · 원문 그대로)·「헤드업 디스플레이(HUD)」가 ★ 이름으로 왔다
★★ ★ **`previous_price` 가 있다** — ★ 가격 변동을 ★ 원문에서 바로 읽는다
   ★ ★ 다른 사이트는 ★ 우리가 두 번 받아 견줘야 안다
★ ★ `factory_price` 는 ★ 신차가다 — ★ `value.depreciation` 이 바로 채워진다
```

## 0-3. ★ 지킬 것

```
필수  ★ 토큰은 ★ **바퀴마다 새로 받는다** — ★ JWT 라 ★ 만료가 있다
필수  ★ `App-Os: web` 헤더를 ★ 빠뜨리지 마라
필수  ★ 응답이 ★ **리스트**다.  ★ `results`·`data` 로 감싸여 있지 않다 — ★ 벗기지 마라
필수  ★ `choice=absent` 는 ★ **「없다」**다.  ★ `availability=unavailable` 은 ★ 「그 트림에 없는 옵션」이다
      ★ ★ 둘을 섞지 마라 — ★ 「없다」와 「해당 없음」은 다르다 (개정 325)
금지  ★ 토큰을 ★ 저장소에 적는 것 — ★ 매번 받는다
★ 아래 옛 판정(★ 「고장났다」)은 ★ **틀렸다.  ★ 기록으로만 남긴다**
```


```
version  SPEC-2026.08.24-r670
follows  `f-table.md` · `MULTISITE_MAPPING.md`
sources  개정 585 · 실측 08-23
checks   S46-29 · S46-31
```
★ 이 문서는 ★ **그 사이트가 무엇을 주는가**만 적는다.  ★ 판정은 ★ `f-table` 이 한다 (가이드역할 ㉺)


`SPEC-2026.08.22-r518` · 2026-08-22 · **가이드가 직접 실측했다 (원칙 4)**

```
★★ 여섯 사이트 중 ★ 가장 풍부하다 — ★ 신차가 · 부위별 사고 · 보험 금액 · 타이어 · 틴팅까지
★ 가이드가 ★ 조사(개정 486)를 해 놓고 ★ 문서를 안 써서 명령서에서 빠져 있었다.  ★ 그것을 닫는다
```

---

# 1. 토큰 — ★ 로그인이 아니다.  ★ 세션 쿠키다

```
① GET https://www.heydealer.com/       ← ★ 한 번 연다
   Set-Cookie: ★ customer_web_session=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9…
② 그 값을 ★ authorization: Bearer {값} 으로 쓴다
★ 서버가 ★ 손님용으로 ★ 스스로 발급한다.  ★ 훔치거나 흉내 내는 것이 아니다
★ robots.txt — `User-Agent: * / Allow: /`.  ★ 금지 경로가 없다
```

---

# 2. 경로

| 무엇 | 경로 | 실측 |
|---|---|---|
| **목록** | `GET market-api.heydealer.com/v2/customers/web/market/cars/?order=recommendation&page=N` | 200 · ★ **쪽당 10건** |
| **상세** | `GET …/market/cars/{hash_id}/` | 200 · ★ **필드 33개** |
| 곁들이 | `…/market/cars/recommendation_meta/` | 200 |

```
헤더  authorization: Bearer {쿠키값} · app-os: web ·
      Referer: https://www.heydealer.com/ · Origin: 같음
★ 응답이 ★ 배열(list)이다.  ★ dict 가 아니다 — 파서 주의
★ 목록은 ★ 필드 14개뿐이다 (`view_type` 을 빼도 같다).  ★ 값은 ★ 상세에 있다
★ `hash_id` 가 매물번호다 (`NQp2wWyP` 꼴 · 영숫자 8)
```

---

# 3. ★ 매핑 — `core_*` 칼럼 단위

## 3-1. `core_listing`

| 칼럼 | 헤이딜러 | 표본 값 |
|---|---|---|
| `site` | — | `'heydealer'` |
| `source_id` | `hash_id` | `NQp2wWyP` |
| `plate_hash` | `carhistory.car_number` (해시해서) | 148라9486 |
| `price_current_won` | `price` ×10000 | 1,705만 |
| `price_detail_won` | `previous_price` ×10000 | 1,750만 (내린 값) |
| **`price_origin_won`** | ★★ `detail_info.factory_price` ×10000 | ★ **2,000만** |
| `year_month` | `initial_registration_date` → `YYYYMM` | 2023-08-03 → `202308` |
| `form_year` | `detail_info.year` | 2024 |
| `mileage_km` | `detail_info.mileage` | 12,223 |
| `displacement_cc` | `displacement` | 998 |
| `trim_badge` · `_detail` | `grade_name` · `grade_part_name` | 1.0 터보 인스퍼레이션 |
| `fuel_raw` · `fuel_detail` | `fuel_display` · `fuel` | 휘발유 · gasoline |
| `transmission` | `transmission_display` | 오토(A/T) |
| `color_ext_raw` · `_int_raw` | `color_and_trim.exterior_description` · `interior_…` | 톰보이 카키 · 다크 그레이 |
| `options_choice_json` | ★ `options[]` `{name, choice, availability}` | 선루프 loaded |
| `model_catalog_key` | `model_hash_id` · `grade_hash_id` | `ZoDjr4` · `6WD0wp` |
| `photo_list_json` | `images` · `inside_image_url` · `inside_360` | S3 |
| `sales_status` | `sale_status` · `is_reserved` | listed |
| `subscribe_cnt` | `stars_count` · `visits_count` | 34 · 357 |
| `reg_at` | `offered_at` | 2026-07-24 |

## 3-2. `core_record` — ★ 이력이 통째로 온다

| 우리 | `carhistory` 필드 | 표본 |
|---|---|---|
| `accident_my_cnt` | ★ `my_car_accident_count` | 1 |
| `accident_my_cost` | ★ `my_car_accident_cost` | **2,938,600원** |
| `accident_other_cnt` | `other_car_accident_count` | 1 |
| — 사고 내역 | ★ `my_car_accident_list` · `other_car_accident_list` | 날짜·유형·부품·보험금 |
| `owner_change_cnt` | `owner_changed_count` · `owner_changed_list` | 1 · 날짜 |
| `use_business` · `use_gov` · 렌트 | ★ `has_business_use_record` · `has_public_use_record` · `has_rent_use_record` | false·false·false |
| `flood_total_cnt` | `flooded_count` | 0 |
| `total_loss_cnt` | `total_loss_count` · `loss_count` | 0 |
| — 도난 | `stolen_count` | 0 |
| — 번호판 변경 | `car_number_changed_count` | 0 |

```
★★ 렌트·영업용·관용을 ★ 셋으로 갈라 준다 — ★ 우리 `history.use` 축과 정확히 맞는다
★ ★ `my_car_accident_cost` 가 ★ 원 단위 금액이다 — 우리 `state.my_cost` 축이 그대로 산다
★ `undecided_my_car_accident_count` — ★ 「아직 안 정해진 사고」다.  ★ 0 과 다르다
```

## 3-3. `core_inspection` — ★ 부위별로 온다

| 우리 | 헤이딜러 | 표본 |
|---|---|---|
| `state.frame` 골격 · `state.outer` 외판 | ★ `accident_repairs[]` `{part, repair}` | hood·**exchange** / radiator_support·exchange / trunk_lid·**weld** |
| — 사고 요약 | ★ `accident_repairs_summary_display` | **단순교환 무사고** |
| — 판금 건수 | ★ `simple_repair_info` | count 3 · door 0 · hood_fender 1 · etc 2 |
| `state.consumable` 소모품 | ★ `condition.items` | **타이어 앞 65% 뒤 80% 남음** |
| — 틴팅 | ★ 〃 | **앞 28% 옆 14% 뒤 10%** |
| `warranty.site` 사이트 검증 | ★ `heydealer_eye` (영상) · `certification` | ★ **eye 인증** |
| — 성능점검 원본 | `inspection_records` · `inspection_records_image_urls` | 사진 |

```
★★ `accident_repairs` 가 ★ 부위(part) 와 ★ 무엇(repair: exchange/weld) 을 따로 준다
   ★ 엔카 `outers` 와 같은 급이다 — ★ 판금과 용접을 가를 수 있다 (개정 351)
★ 「단순교환 무사고」와 「완전무사고」가 ★ 다른 딱지다 — `dict_enum` 으로 갈라 받는다
★ ★ 틴팅 농도를 ★ 숫자로 준다.  ★ 여섯 사이트 중 유일하다
```

## 3-4. 보증 — 종류별 잔여

```
warranty_info.manufacturer_warranties[]
  {"name":"차체/일반 부품", "description":"보증기간 종료",        "is_active":false, "remaining_rate":0.0}
  {"name":"엔진/주요 부품", "description":"87,777km / 1년 11개월 남음", "is_active":true,  "remaining_rate":0.389}

`warranty_body_month`·`_km`   ← 「차체/일반 부품」    ★ 종료면 ★ 0 (확인한 값이다)
`warranty_power_month`·`_km`  ← 「엔진/주요 부품」    ★ 87,777km / 23개월
★ `remaining_rate` 까지 준다 — ★ 우리가 계산할 필요가 없다
★ `warranty_info.description` 은 ★ 헤이딜러 자체 보증이다 (「6개월ㆍ1만km까지」) — ★ 사이트 검증 축
★ `ev_info` — ★ SOH 는 ★ 없다.  ★ 가점 재료가 아니다 (3a장 ④)
```

---

# 3a. ★★ 표본 25건 검증 — ★ 1건일 때 못 본 것 넷 (개정 518)

```
★ 개정 517 은 ★ 표본 1건으로 썼다.  ★ 25건으로 늘려 다시 쟀다 (모양 ④)
```

## 필드 존재율

| 필드 | 25건 중 | 뜻 |
|---|--:|---|
| `factory_price` · `carhistory` · `condition` · `options` · `warranty_info` · `total_info` · `initial_registration_date` | **25** | ★ 늘 온다 |
| `inspector_comment` | 19 | 없을 수 있다 |
| ★ `accident_repairs` | **14** | ★ **무사고면 빈 배열이다** |
| ★ `heydealer_eye` | **12** | ★ **절반만 붙는다 — 사이트 검증 축이 갈린다** |
| ★ `ev_info` | **6** | ★ **전기차만** |

## ① ★ `accident_repairs` 가 14/25 인 것은 ★ 결손이 아니다

```
사고 요약  ★ 「단순교환 무사고」 14 · ★ 「완전무사고」 11   ★ 합 25
★ 「완전무사고」인 11건은 ★ accident_repairs 가 ★ 빈 배열이다 — ★ 어긋나지 않는다
★★ 그러므로 ★ 빈 배열을 ★ 「우리가 못 받았다」로 저장하지 마라.  ★ 「없음」(0)이다
필수  `accident_repairs_summary_display` 를 함께 보고 가른다 —
      「완전무사고」 + 빈 배열 → ★ 0 (확인한 값)
      필드 자체가 없음        → ★ NULL (안 받았다)
```

## ② ★ 부위·수리 종류가 실측으로 드러났다

```
repair  ★ weld 13 · exchange 5   ★ 판금(용접)이 더 많다
part    ★ 10가지 — door_rear_passenger · fender_rear_passenger · fender_front_driver ·
        door_rear_driver · side_sil_panel_passenger · door_front_driver · trunk_lid ·
        fender_rear_driver · fender_front_passenger · door_front_passenger
★ 앞뒤·좌우가 이름에 들어 있다 (front/rear · driver/passenger)
★ `dict_enum(site='heydealer', axis='part')` 에 넣는다.  ★ 우리말로 옮기지 마라 — 원문이 정본
```

## ③ ★★ `warranty_info` 가 ★ 연료에 따라 갈린다

| 보증 이름 | 25건 중 |
|---|--:|
| 차체/일반 부품 | **25** |
| 엔진/주요 부품 | **24** |
| ★ 고전압 배터리 | **10** |
| ★ 전기차 전용 부품 | 5 |
| ★ 하이브리드 전용 부품 | 4 |

```
★ 「엔진/주요 부품」이 24 다 — ★ 하나는 ★ 순수 전기차라 엔진 보증이 없다
★★ 없는 보증을 ★ 0 으로 넣지 마라.  ★ NULL 이다 — ★ 그 차에 없는 보증이다
   ★ 기아 CPO 에서와 같은 자리다 (개정 483 ②)
필수  `warranty_power_*` — EV 는 ★ 「고전압 배터리」로 잰다.  내연은 「엔진/주요 부품」
```

## ④ ★★ `ev_info` — 전기차 여섯 건에 ★ 배터리 정보가 온다

```
{"battery_manufacturer":"삼성 SDI", "battery_type":…, "range":412, "international_range":538,
 "wheel_drive":"4WD", "zero_hundred":5.4, "charging_cost_description":"100km 운행에 약 6천원",
 "factory_name":"🇩🇪 독일 Bayern Dingolfing 공장"}

실측  BYD Blade · LG 에너지솔루션 · 삼성 SDI · SK온+LG · CATL   ★ 제조사가 갈린다
★★ 다만 ★ SOH(배터리 잔량)는 ★ 없다.  ★ `range` 는 ★ 카탈로그 주행거리다
   → ★ 우리 SOH 가점(+30)의 재료가 ★ 아니다.  ★ 「배터리 정상」으로 읽지 마라
   ★ 개정 486 에서 「배터리 정상 → SOH 재료」라 적은 것은 ★ 목록 딱지를 본 것이다.  ★ 정정한다
★ `battery_manufacturer` 는 ★ 화면에 낼 값이다 — 점수에 넣지 않는다 (마스터 확정 전)
```

## ⑤ 그 밖

```
연료      휘발유 12 · ★ 전기 6 · 하이브리드 4 · 경유 3   ★ 전기차가 24% 다
판매상태   listed 25 — ★ 팔린 매물은 목록에 없다
listing_type  stock 19 · ★ revolt 6 — ★ 무엇이 다른지 ★ 아직 모른다 (밀린일)
condition  ★ 늘 셋이다 — 타이어 · 틴팅 · ★ 차 키
사고 금액   14/25 건에 온다 · 401,840원 ~ ★ 12,259,420원
```

---

# 4. ★★ 신차가 — 여섯 사이트 중 여기와 엔카뿐이다

```
`detail_info.factory_price`  ★ 2000 (만원)
★ ~~기아 CPO · 현대 인증 · KB · K카 넷 다 안 준다~~
★★★★ **08-29 정정 — ★ 현대 인증은 준다** [실측 08-29 · 상세 **표본 8건 전건**]
   ★ 「신차 가격 대비 **26,200,000**」처럼 ★ **매물마다 다른 값**이 온다 (8/8 이 서로 다르다)
   ★ ★ K카는 ★ **안 준다** [실측 08-29 · 상세 표본 8건 · `newCar*` 칸 **0/8**]
   ★ ★ **기아 CPO 는 안 준다** [실측 08-29 · `/api/search/` `content` **표본 100건** ·
      ★ 항목 칸 29개에 ★ `price` 뿐이고 ★ `new*`·`origin*`·`release*` 가 **0개**]
   ★ ★ **KB 는 준다** — ★ 파서가 `price_origin_won` 을 이미 넣는다 (표본 10건 전건 · 개정 870)
★ `value.origin` 75점이 ★ 여기서 산다
★★ 그리고 ★ 다른 사이트 매물에 ★ 붙여 쓸 수 있다 —
   ★ 신차가는 ★ 매물이 아니라 ★ 차종·트림의 속성이다 (f-table 「사이트별 채우기」 ③)
   ★ 매칭 키 — `brand_name` · `model_part_name` · `grade_name` · `year`
```

---

# 5. 저장

```
필수  `site='heydealer'` · `source_id`=`hash_id` · 엔카와 ★ 같은 표
필수  ★ 가격은 ★ 만원이다 → ★ ×10000 해서 원으로 저장한다
필수  ★ `initial_registration_date` 는 ★ 날짜다 → ★ `YYYYMM` 6자리로
필수  ★ 원문을 그대로 남긴다 (`raw_response`)
필수  ★ VIN 이 없다 — ★ K카와 묶을 수 없다.  ★ 합치지 않는다 (개정 484 ⑦)
```

---

# 6. ★ 아직 모르는 것 — 지어내지 마라

```
· 총 매물 수 — ★ 화면에 안 나온다.  ★★ 그러나 ★ 다 세지 않는다 —
  ★ 마스터 확정 08-23 「전량을 받지 않는다」.  ★ 상한 20쪽(200건)까지만 (명령서 3-0)
· `model_group_hash_id` 가 ★ 해시라 사람이 못 읽는다 —
  ★ 목록을 받아 ★ 차명과 짝지어 `dict_enum(axis='target')` 을 채운다 (`TARGET_KEY_MAP.md` 5장)
· 조건 검색(차종·가격) 파라미터를 ★ 아직 못 봤다 — ★ `order` 만 확인했다
· `certification` · `heydealer_eye` 의 등급이 갈리는지 ★ 표본 1건으로는 모른다
★ ~~표본 1건~~ → ★ 25건으로 검증했다 (3a장 · 개정 518)
· ★ `listing_type` 의 `stock` 과 `revolt` 가 무엇이 다른지 ★ 모른다
```

---


---


---


---

# ★★★ 08-24 · 갈렸다 — ★ **회선이 아니다.  ★ `cars/` 만 죽었다** (개정 693)

```
★★ 마스터가 ★ 주소를 ★ 하나 더 주셨다 —
   `www.heydealer.com/?brand=Jo6rOo&model=Epbm5o&model-group=KM5VJy`
★ ★ 그 덕에 ★ **결정적인 것**을 찾았다
```

## ★★★ 같은 서버의 ★ 다른 경로는 ★ **200 이다**

| 경로 | 결과 |
|---|---|
| ★ `…/market/filters/` | ★★ **200 · 1,209B · 평문 JSON** |
| `…/market/cars/` | ★ **500** (파라미터 여섯 꼴 다) |
| `…/market/cars/count/` | ★ 500 |
| `brands/` · `models/` · `options/` · `search/` | 404 |

```
★★★ ★ **`market-api.heydealer.com` 은 ★ 우리에게 열려 있다**
   ★ ★ `filters/` 가 ★ 200 으로 ★ 평문 JSON 을 준다
★ ★ 그러므로 ★ **회선 차단이 아니다** — ★ 엔카 407 과 ★ 다르다
★ ★ **`cars/` 그 하나만 ★ 500 이다**
★ ★ 오판 97 을 ★ 다시 정정한다 — ★ 「고장났다」가 ★ 결국 맞았다.  ★ 다만 ★ **API 하나만**이다
```

## ★★ `filters/` 가 준 것 — ★ **쓸 수 있다**

```json
fuel        휘발유 gasoline · 경유 diesel · LPG lpg · 바이퓨얼 bifuel
            전기 electric · 수소 hydrogen · 하이브리드 hybrid
car_shape   경∙소형 small · 세단 sedan · SUV∙RV suv_rv · 쿠페 coupe
            리무진 limousine · 컨버터블 convertible · 해치백 hatchback
price       100 ~ 10000 (만원 · 38칸)
mileage     10000 ~ 100000 (10칸)
year        2015 ~ …
```

```
★★ ★ **연료 낱말이 ★ 영문 값으로 나온다** — ★ `lpg` · `electric` · `hybrid`
   ★ ★ 우리 갈래(LPG · LPi · EV)와 ★ 짝지을 수 있다
필수  ★ 이 표를 ★ `dict_enum` 사전에 ★ 미리 넣어라 — ★ 사이트가 살아나면 ★ 바로 쓴다
```

## ★ 차종 해시 — ★ 세 층이다

```
`?brand={해시}&model={해시}&model-group={해시}`
   실측 — 브랜드 `Jo6rOo` · 차종 `Epbm5o` · 차종군 `KM5VJy`
★ ★ 셋 다 ★ **여섯 자**다.  ★ 세 층 다 ★ 화면 본문에 들어 있다
★ ★ 코드표 경로(`brands/`·`models/`)는 ★ **404** — ★ 화면에서 뽑아야 한다
```

## ★ 그러므로 — ★ 할 것

```
필수  ★ **뒤로 미룬다.**  ★ `cars/` 가 살아나야 받는다
필수  ★ 바퀴마다 ★ **한 번만** 두드린다 — ★ `filters/` 는 200 이니 ★ `cars/` 만 본다
필수  ★ `filters/` 의 ★ 연료·차형 낱말을 ★ 사전에 ★ 미리 넣어라
필수  ★ 마스터께서 ★ 차종마다 주소를 주시면 ★ 해시를 모은다 (★ 지금 셋)
금지  ★ 우회를 만드는 것 — ★ 막힌 것이 아니라 ★ 그 API 가 죽은 것이다
검산  ★ `S46-52` — ★ `cars/` 가 200 을 주면 ★ 알린다
```

---

# ★★★ 08-24 · 마스터가 주소를 주셨다 — ★ 얻은 것과 ★ 남은 것 (개정 692)

```
★★ 마스터 주소 — `https://www.heydealer.com/?brand=Jo6rOo&model-group=KM5VJy`
```

## ★★ 얻은 것 — ★ **차종을 좁히는 꼴**

```
★ 경로가 ★ **`/` 다.**  ★ `/market/cars` 가 ★ 아니다 — ★ 가이드가 틀린 곳을 두드리고 있었다
★ ★ 좁히는 법 — ★ **쿼리 파라미터**
     `?brand={해시}&model-group={해시}`
     ★ 실측 — 브랜드 `Jo6rOo` · 차종군 `KM5VJy`
★ ★ 숫자 코드가 ★ 아니라 ★ **여섯 자 해시**다 — ★ 지어낼 수 없다
필수  ★ 우리 대상 차종의 ★ 해시를 ★ 모아야 한다
      ★ ★ 마스터께서 ★ 차종마다 한 번씩 눌러 ★ 주소를 주시면 ★ 다 나온다 (★ K카와 같다)
```

## ★ 그 화면이 부르는 API — ★ 우리가 아는 것과 ★ 같다

```
`market-api.heydealer.com/v2/customers/web/market/cars/?…`
`api.heydealer.com/v2/customers/web/initialize_app/`
★ ★ 화면 자체는 ★ **200 · 243KB** 로 온다.  ★ 매물번호는 ★ 0개 (JS 가 뒤에 부른다)
```

## ★★★ 남은 것 — ★ 목록 API 가 ★ 여전히 500

```
★ 파라미터를 붙여 다시 두드렸다 (08-24) —
   `?brand=Jo6rOo&model-group=KM5VJy`      → ★ 500
   `?brand=…&model_group=…` (밑줄)          → ★ 500
   `?model-group=…` 만 · `?brand=…` 만       → ★ 500
   `?order=recommendation&page=1&brand=…`   → ★ 500
   조건 없음                                 → ★ 500
★★ ★ **여섯 꼴 다 500 이다.  ★ 파라미터 탓이 아니다**
```

## ★ 그러므로 — ★ **둘 중 하나다.  ★ 아직 못 가른다**

| | 무엇 | 어떻게 가리나 |
|:--:|---|---|
| ⓐ | ★ **우리 회선을 막는다** (엔카 407 과 같은 자리) | ★ **마스터 회선에서 200 이 오는가** |
| ⓑ | ★ 사이트가 ★ 그 API 만 고장 | 〃 |

```
필수  ★ **`/admin/collect` 「브라우저 수집」으로 ★ 마스터 회선에서 재 본다**
      ★ ★ 200 이면 ⓐ — ★ 엔카와 같은 길로 받는다
      ★ ★ 500 이면 ⓑ — ★ 뒤로 미룬다
금지  ★ 어느 쪽인지 ★ 가리기 전에 ★ 단정하는 것 (오판 97)
★ ★ 규격(칸·매핑)은 ★ 살아 있다 — ★ 08-18 실측이다
```

---

# ★★★ 08-24 재측 — ★ 다섯을 다 두드렸다 (밀린일 89 · 개정 690)

```
★★ 마스터 지시 — 「★ 「못 한다·없다」로 단정한 자리를 ★ 다시 두드려라」 (명령서 24-1)
★ ★ 08-23 에는 ★ **세 꼴만** 두드렸다 (order+page · 조건 없음 · page 만) — ★ 모자랐다
★ ★ 이번에 ★ 기준서 0-1 ★ **다섯을 다** 두드렸다
```

| # | 무엇을 바꿨나 | 결과 |
|:--:|---|---|
| ① | ★ **호스트** — `market-api` · `api` · `www` · `m` · `heydealer.com` | ★ **500 · 500 · 404 · 403 · 404** |
| ② | ★ **UA** — 데스크톱 ↔ 모바일 | ★ **둘 다 500** |
| ③ | ★ **경로·버전** — `v1` · `v3` · `/market/cars/` · 끝 슬래시 · `limit` | ★ **v1·v3 은 404** · 나머지 **500** · `/v2/customers/market/cars/` 는 ★ **401** |
| ④ | ★ **헤더** — `Origin` 붙임 · 최소 헤더 | ★ **둘 다 500** |
| ⑤ | ★ **세 번 이어** (일시적인가) | ★ **세 번 다 500** |

## ★★★ ~~답 — 사이트가 고장난 것이다~~ ★ **정정 08-24 (개정 691)**

```
★★ 마스터 — 「★ **헤이딜러는 나는 되는데 ★ 너는 왜 안 되지.  ★ 모바일로 들어갔어?**」
★ ★ **마스터 회선에서는 ★ 된다.**  ★ 가이드 창에서만 ★ 500 이다
★★★ ★ **그러므로 ★ 「고장났다」가 ★ 아니다.  ★ 또 단정했다** (오판 97)
   ★ ★ 엔카 ★ 407 과 ★ 같은 구조일 수 있다 — ★ **서버 회선을 막는 것**
```

## ★ 가이드가 ★ 더 두드린 것 (08-24 · 조합)

| 무엇 | 결과 |
|---|---|
| ★ `m.heydealer.com` × ★ **PC · iPhone · Android** | ★ **셋 다 403** |
| ★ `www.heydealer.com` × PC / iPhone / Android | ★ **200** · 151KB / **319KB** / 313KB |
| ★ `/market/cars` (모바일 UA) | ★ **200 · 66KB** · ★ 매물번호 **0개** |
| ★ `/v2/customers/app/market/cars/` | 404 |
| ★ 모바일 홈이 부르는 주소 | ★ `api.heydealer.com/v2/customers/web/initialize_app/` · `image.heydealer.com` ★ **목록 API 는 없다** |

```
★ ★ 화면은 ★ 모바일 UA 에서 ★ **319KB 로 커진다** — ★ 사람에게는 ★ 다르게 보인다
★ ★ 그런데 ★ 목록 API 는 ★ 어느 조합에서도 ★ 500 이다
```

## ★★★ 그러므로 — ★ **마스터 회선으로만 확인된다**

```
필수  ★ **`/admin/collect` 「브라우저 수집」으로 재 본다** — ★ 엔카와 같은 길이다
      ★ ★ 마스터 회선에서 ★ 200 이 오면 ★ **서버 회선이 막힌 것**이다
      ★ ★ 거기서도 500 이면 ★ 그때 ★ 「고장났다」가 맞다
필수  ★ 마스터께서 ★ 헤이딜러 매물 화면을 여실 때 ★ **주소 하나만** 주시면
      ★ ★ 그 꼴로 ★ 목록 경로를 ★ 다시 찾는다 (★ K카가 그렇게 열렸다)
금지  ★ ★ **「고장났다」로 단정하는 것** — ★ 마스터 회선에서 되는 것을 ★ 확인했다
★ ★ 규격(칸·매핑)은 ★ 살아 있다 — ★ 08-18 실측이다
검산  ★ `S46-52` — ★ 헤이딜러가 200 을 주면 알린다 (알림)
```

## ~~옛 판정~~ — ★ 기록으로만 남긴다

```
★ 500 의 본문이 ★ **한국어로 온다** —
   `{"toast":{"message":"서버 오류가 발생했습니다.\n계속 오류가 발생하면
     스크린샷과 함께 ★ **채팅문의로 알려주세요!**","type":"default"}}`
★★ ★ **봇 차단이면 ★ 이런 말을 안 한다.**  ★ 「스크린샷을 보내 달라」는 ★ 사람에게 하는 말이다
★ ★ 그리고 ★ **상세도 500 이다** — ★ 08-23 에는 ★ 상세가 돌았다.  ★ 그 뒤에 깨졌다
★ ★ 사람이 보는 화면(`/market/cars`)은 ★ **200** 이나 ★ 매물번호가 ★ **0개**다
   ★ ★ 그 화면도 ★ 같은 API 를 부른다 — ★ **사람에게도 안 보인다**
```

## ★ 그러므로

```
필수  ★ **우회를 만들지 마라.**  ★ 막힌 것이 아니라 ★ 고장난 것이다
필수  ★ 헤이딜러는 ★ **뒤로 미룬다** — ★ 다른 사이트가 먼저다
필수  ★ 바퀴마다 ★ **한 번만** 두드려 본다 — ★ 고쳐지면 ★ 그때 받는다
      ★ ★ `GET market-api.heydealer.com/v2/customers/web/market/cars/?page=1` → ★ 200 이면 살아난 것
금지  ★ 「막혔다」로 적는 것 — ★ **「사이트가 고장났다」**가 맞다.  ★ 뜻이 다르다
★ ★ 이 문서의 ★ 규격(칸·매핑)은 ★ **살아 있다** — ★ 08-18 에 실측한 것이다
   ★ ★ 사이트가 돌아오면 ★ 그대로 쓴다
검산  ★ `S46-52` — ★ 헤이딜러가 ★ 200 을 주면 ★ 알린다 (★ 실패가 아니라 ★ 알림)
```

---

# ★ 08-23 재실측 — ★ 목록 API 가 ★ 500 이다

```
robots  www.heydealer.com → `User-Agent: * / Allow: /`  ★ 막힌 것이 없다
홈      https://www.heydealer.com/ → ★ 200
목록    GET market-api.heydealer.com/v2/customers/web/market/cars/… → ★ **500**
        본문 — {"code":null,"message":null,"toast":{"message":"서버 오류가 발생했습니다…"}}
        ★ 세 꼴을 두드렸다 (order+page · 조건 없음 · page 만) — ★ 셋 다 500
★★ ★ 이것은 ★ 사이트가 낸 ★ 애플리케이션 오류다 (JSON 본문이 한국어다)
   ★ 우리 창 프록시가 아니다 (오판 #63 의 가르는 법 — `upstream connect error` 가 아니다)
★ ★ 규격이 적은 ★ Bearer 토큰이 ★ 이제 필요한 것일 수 있다 — ★ 아직 못 가렸다
★ ★ 「좁히는 파라미터」는 ★ 목록이 살아야 잰다.  ★ 못 쟀다 — ★ 「없다」가 아니다
```

---

# ★★ 08-29 재측 — ★ 전량 · 전기차 [실측 08-29 · 가이드]

```
`tools/collect_heydealer.py --dry` — ★ 차종 19종 · ★ 목록 합 **199건** (겹친 것을 뺀 수)
  그랜저 50 · 모델Y 33 · G80 19 · GLC 18 · NX 16 · XC40 12 · XC60 10 · X3 9
  콜레오스 8 · G70 6＋6 · S60 5 · GV60 3 · Q5 3 · V60CC 2 · G80_EV 2 · GV70_EV 2
  스포티지 1 · RX 1
★ 화면 저장은 ★ **96건**이다 (배포 실측 08-29) — ★ 어긋난다.  ★ 다시 돌리면 붙는다
```

## ★ 전기차 — ★ 볼보 브랜드 전량을 세었다

```
`brand=Jo6rOo`(볼보)로 ★ 빈 쪽까지 — ★ **35건**
  XC40 10 · XC60 9 · S60 5 · S90 4 · XC90 2 · V40 2 · V60 크로스 컨트리 2 · V60 1
★★ ★ **EX30 · C40 은 ★ 0건이다** — ★ 「없다」가 아니라 ★ **지금 재고가 0**이다
   ★ ★ `targets.json` 에 ★ `EX30_EV`·`C40_EV` 의 `heydealer` 질의가 없는 것은
     ★ ★ 지금은 손해가 아니다.  ★ 나오면 그때 해시를 넣는다
★ 폴스타 2·3·4 — ★ 브랜드 해시를 ★ 아직 못 찾았다.  ★ 「없다」로 적지 않는다
```

---

# ★★★★ 폴스타를 찾았다 — ★ `fuel=electric` [실측 08-29 · 가이드]

```
★ 브랜드 해시를 ★ 못 찾았다 — ★ 다섯을 두드린 기록 —
  `/v2/customers/web/market/brands/`        → ★ 404
  `/v2/customers/web/market/cars/filters/`  → ★ 404
  `/v2/customers/web/market/car_filters/`   → ★ 404
  `/v2/customers/web/market/filters/`       → ★ 200 · 1,269B — ★ **브랜드 칸이 없다**
  ★ 목록 항목 키 14개에도 · ★ 상세에도 ★ 브랜드 해시가 ★ 없다
★ ★ 그러므로 ★ **「해시를 못 찾았다」**로 적는다 — ★ 「없다」가 아니다

★★ ★ 대신 ★ `filters/` 가 ★ **`fuel` 을 준다** —
   `[휘발유 gasoline · 경유 diesel · LPG lpg · 바이퓨얼 bifuel
     · ★ 전기 electric · 수소 hydrogen · 하이브리드 hybrid]`
★ ★ `…/cars/?…&fuel=electric` → ★ **200건** (빈 쪽까지 · 실측 08-29)
```

## ★ 전기 200건에 무엇이 있나 [실측 08-29]

```
레이EV 23 · 모델Y 15＋12 · e-트론 10 · 모델3 8 · 토레스EVX 8 · 아이오닉5 7
SEALION7 7 · EV6 7 · EV9 6 · … · ★ **폴스타4 3 · 폴스타2 3** · e-G80 2 · e-GV70 1
★★ ★ **EX30 · C40 · 폴스타3 은 ★ 0건이다** — ★ 「없다」가 아니라 ★ 지금 재고가 0이다
```

## ★★ 그런데 ★ 지금 넣으면 ★ 전량을 끌어온다 — ★ 안 넣었다

```
`tools/collect_heydealer.py:77`
  pick = {k: q[k] for k in ("brand", "model-group", "model") if q.get(k)}
★ ★ `fuel` 이 ★ 그 셋에 없다 → ★ `pick` 이 **빈 dict** → ★ **조건 없는 전량**이 온다
★ 실측 08-29 — ★ `targets.json` 에 넣고 `--dry` 를 돌리니
  ★ ★ 다섯 차종이 ★ **각각 374~381건**을 끌어와 ★ 합이 **1,330건**이 됐다 (평소 207)
  ★ ★ 마스터 확정 「전량을 받지 않는다」에 ★ 정면으로 어긋난다 — ★ **그 자리에서 되돌렸다**

★★ 차례 — ★ ① 개발측이 `pick` 에 `fuel` 을 더한다 ② ★ 그다음 `targets.json` 에 넣는다
   ★ ★ 순서를 바꾸면 ★ 전량 수집이 한 번 돈다
★ 등록부에는 ★ 먼저 넣어 두었다 — `target_map.json` `by_site.heydealer` 의
  ★ `폴스타2` → `POLESTAR2_EV` · `폴스타4` → `POLESTAR4_EV` (★ 이것만으로는 안 돈다)
```
