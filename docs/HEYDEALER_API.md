# 헤이딜러 API · 매핑 규격

`SPEC-2026.08.22-r517` · 2026-08-22 · **가이드가 직접 실측했다 (원칙 4)**

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
★ `ev_info` 가 있다 — ★ 전기차면 ★ SOH 가점(+30)의 재료일 수 있다.  ★ 표본이 내연이라 null
```

---

# 4. ★★ 신차가 — 여섯 사이트 중 여기와 엔카뿐이다

```
`detail_info.factory_price`  ★ 2000 (만원)
★ 기아 CPO · 현대 인증 · KB · K카 ★ 넷 다 안 준다
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
· 총 매물 수 — ★ 화면에 안 나온다.  ★ 빈 쪽까지 넘겨 센다 (쪽당 10건)
· `model_group_hash_id` 가 ★ 해시라 사람이 못 읽는다 —
  ★ 목록을 받아 ★ 차명과 짝지어 `dict_enum(axis='target')` 을 채운다 (`TARGET_KEY_MAP.md` 5장)
· 조건 검색(차종·가격) 파라미터를 ★ 아직 못 봤다 — ★ `order` 만 확인했다
· `certification` · `heydealer_eye` 의 등급이 갈리는지 ★ 표본 1건으로는 모른다
★ 표본이 ★ 1건이다.  ★ 20건 이상으로 늘려 다시 대조해야 한다 (오판대장 모양 ④)
```
