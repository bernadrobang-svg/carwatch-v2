# 렉서스 인증중고차 API · 매핑 규격

`SPEC-2026.08.23-r534` · 2026-08-23 · **가이드가 직접 실측했다 (원칙 4)**
★ **마스터 지시 — 「수입차 인증중고 직영 사이트」.  ★ 첫 수입 브랜드다**

---

# 0. 결론

```
★★ 목록·상세가 ★ 인증 없이 ★ 평문 JSON 으로 열린다.  ★ 기아 CPO 급이다
★ 총 ★ 84대 · 쪽당 36 · 3쪽
★★ ★ 신차가(`release_price`)를 ★ 목록에서 준다 — ★ 다섯째 사이트다
★ 주소를 ★ 브랜드 본사(`lexus.co.kr`)의 링크에서 캤다.  ★ 지어내지 않았다
```

---

# 1. 경로

| 무엇 | 경로 | 실측 |
|---|---|---|
| **목록** | `GET certified.lexus.co.kr/api/json/getList_search.json.php?price_area_min=0&price_area_max=99999` | 200 · 21KB |
| **상세** | `GET …/api/json/getData_car_detail.json.php?idx={idx}` | 200 |
| 화면(목록) | `/car-list/` | — |
| 화면(상세) | `/car-detail/?idx={idx}` | — |

```
헤더  모바일 UA · Referer: https://certified.lexus.co.kr/car-list/
★ 인증·토큰·쿠키 ★ 없다.  ★ 서버에서 그냥 200 이다
★ 응답 구조 — `search_list.car_list[]` · `search_list.total_list_num` (★ 한 겹 더 있다)
★ 쪽넘김 — `num_per_page` 36 · `total_page` 3 · `cur_page`
```

---

# 2. 매핑 — `core_listing`

| 칼럼 | 렉서스 | 표본 (`idx=6395`) |
|---|---|---|
| `site` | — | `'lexus_cert'` |
| `source_id` | `idx` | 6395 |
| `price_current_won` | `price` ×10000 | **6,300만** |
| ★ **`price_origin_won`** | ★★ **`release_price`** ×10000 | ★ **7,188만** |
| `year_month` | `year` | 2026 |
| `mileage_km` | `mileage` | 5,242 |
| `trim_badge` | `class_name` · `model_name` | EXECUTIVE · ES 300h |
| `color_ext_raw` | `color.title` · `color.value` | Gray · `#616467` |
| `fuel_raw` | `car_info.fuel` | 하이브리드 |
| `displacement_cc` | `car_info.displacement` | 2,487 |
| `transmission` | `car_info.transmission` | E-CVT |
| ★ `year_month` | ★ **`car_info.registration_date`** | ★ **2025년 10월** → `202510` |
| ★ `state.accident` 사고 | ★ **`car_info.accident_history`** | ★ **무사고** |
| — 점검일 | `car_info.check_date` | 2026년 8월 |
| `color_int_raw` | `car_info.innerColor` | 모브 |
| `plate_hash` | `car_info.number_plate` (해시해서) | 361저 7… |
| ★ **`warranty_body_month`·`_km`** | ★ **`car_info.warranty`** | ★ **2030년 10월까지 (120,000km)** |
| `dealer_shop`·`dealer_region` | `branch.title` · `branch.addr` | 양재점 · 서울 서초 |
| ★ `warranty.site` 사이트 검증 | ★ **`isCertified` · `isCheckComplete`** | **true · true** |
| `options_choice_json` | ★ `spec[]` (갈래별 이름) | 내장 — 시마모쿠 우드 트림 · 세미 아닐린 천연가죽 … |
| `photo_list_json` | `img_url` · `add_images[]` | CDN |

```
★★ ★ `release_price` 가 ★ 신차가다 — ★ 엔카·헤이딜러·KB·리본카에 이어 ★ 다섯째다
   ★ 목록에서 바로 온다.  ★ 상세를 안 열어도 된다
★★ ★ `car_info.warranty` 가 ★ 「2030년 10월까지 (120,000km)」로 ★ 종료 시점을 준다
   → ★ 오늘과 빼서 잔여를 낸다 (현대·기아·헤이딜러는 잔여를 바로 준다)
★ `isCertified` · `isCheckComplete` 가 ★ 불리언이다 — ★ 사이트 검증 축의 근거다
★ `benefit` 에 ★ 「191항목의 철저한 검증」이 온다 — ★ 제조사 인증 단계의 근거다
```

---

# 3. ★ 조심할 것

```
① ★ `car_info.accident_history` 가 ★ 「무사고」로 온다 — ★ 사이트 판정이다
   ★ 그러나 ★ 부위별 판금·교환 · 보험 금액 · 압류저당 · 소유자변경은 ★ 없다
   필수  ★ 골격·외판·누유·수리비·압류저당·소유자변경·용도는 ★ NULL 이다.  ★ 0 이 아니다
   ★ 기아 CPO 는 `performanceRecord` 를 주는데 ★ 렉서스는 「무사고」 한 마디뿐이다
   ★ 표본 1건이라 ★ 「무사고」 말고 다른 값이 오는지 ★ 아직 모른다 (리본카는 「단순수리」가 나왔다)
② ★ VIN 이 없다
③ ★★ `year` 는 ★ 모델연도다 (2026) — ★ 연식은 ★ `car_info.registration_date` 다 (2025년 10월)
   필수  ★ `year_month` 는 ★ `registration_date` 에서 낸다.  ★ `year` 를 쓰면 틀린다
   ★ `form_year` 에 ★ `year` 를 넣는다
④ ★ 84대뿐이다 — ★ 표본이 작다.  ★ 그러나 ★ 마스터 후보 렉서스 NX·RX 가 여기 있다
⑤ ★ `isCertified` 가 ★ 전건 true 인지 ★ 표본을 늘려 확인한다
   ★ 보배드림 「실차확인」 · 현대 「소유자 변경」이 ★ 전건 같은 값이었다 (개정 485·531)
```

---

# 4. 우리 규격에서의 자리

```
★ 제조사 인증이다 — ★ f-table 「사이트 검증 36점」 ★ 최고 단계
   ★ 다만 개정 520 대로 ★ `isCertified`·`isCheckComplete` 가 ★ 참일 때만 준다
★ 채워지는 축 — 예산 · 주행 · 연식 · 트림 · 색상 · 옵션 · ★ 신차가 · 보증 · 사이트검증 · ★ 사고(한 마디)
★ 못 채우는 축 — ★ 골격 · 외판 · 누유 · 수리비 · 소모품 · 압류저당 · 소유자변경 · 용도
★★ ★ 상태·이력이 통째로 비므로 ★ 다른 사이트와 나란히 줄 세우면 ★ 불리하다
   → ★ 화면에 ★ 「렉서스 인증은 191항목 검증으로 갈음한다」고 밝힌다
```

---

# 5. ★ 아직 모르는 것

```
· ~~`year` 가 연식인가~~ ★ 모델연도다.  연식은 `registration_date` (3장 ③)
· `sell_type` · `group_type` · `event_type` 의 뜻 — ★ 전부 0 이다
· 쪽넘김 파라미터 이름 — ★ `cur_page` 로 보이나 ★ 안 눌러 봤다
· `getList_recent_info.json.php?carIdxList[]=` — ★ 무엇을 주는지 안 봤다
★ 표본이 ★ 1건이다.  ★ 20건 이상으로 늘려 다시 대조해야 한다 (오판대장 모양 ④)
★ BMW · 벤츠 · 아우디 · 볼보는 ★ 아직 주소를 못 찾았다 (6장)
```

---

# 6. ★ 다른 수입 브랜드 — 주소를 못 찾았다

```
BMW Premium Selection   ★ `bmw-premiumselection.co.kr` · `premiumselection.bmw.co.kr` ★ 도메인 없음
                        ★ `bmw.co.kr` 링크 187개에 ★ 중고 관련이 0건
벤츠 인증중고            ★ `certified.mercedes-benz.co.kr` 없음 · 본사 페이지 ★ 503
아우디 인증중고          ★ `audi.co.kr/…/approvedplus.html` ★ 403
볼보 셀렉트              ★ `volvocars.com/kr/selekt/` ★ 403 · `selekt.volvocars.co.kr` ★ 503
포르쉐 어프루브드        ★ `finder.porsche.com` ★ 429
미니                    ★ `mini-nextgeneration.co.kr` ★ 도메인 없음

★★ ★ 403·429·503 은 ★ 우리 IP 차단일 수 있다 (다나와와 같은 자리 · 개정 529)
★ 도메인 없음은 ★ 내가 이름을 지어낸 것이다 — ★ 렉서스는 본사 링크에서 캤다
★ ★ 마스터께 청한다 — ★ BMW · 벤츠 · 아우디 · 볼보 인증중고차 ★ 주소를 주십시오
   ★ 오늘 여섯 사이트가 ★ 그렇게 풀렸다
```
