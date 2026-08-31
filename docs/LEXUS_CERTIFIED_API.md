# 렉서스 인증중고차 API · 매핑 규격

```
version  SPEC-2026.09.01-r1042
follows  `f-table.md` · `MULTISITE_MAPPING.md`
sources  개정 859 · 실측 08-29
checks   S46-5 · S46-31
```
★ 이 문서는 ★ **그 사이트가 무엇을 주는가**만 적는다.  ★ 판정은 ★ `f-table` 이 한다 (가이드역할 ㉺)


`SPEC-2026.08.23-r534` · 2026-08-23 · **가이드가 직접 실측했다 (원칙 4)**
★ **마스터 지시 — 「수입차 인증중고 직영 사이트」.  ★ 첫 수입 브랜드다**

---

# 0. 결론

```
★★ 목록·상세가 ★ 인증 없이 ★ 평문 JSON 으로 열린다.  ★ 기아 CPO 급이다
★ 총 ★ 74대 · 쪽당 36 · 3쪽 [실측 08-29]
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
· 쪽넘김 파라미터 이름 — ★ **`cur_page`** 다 [실측 08-29 · 눌러 봤다].  ★ `page`·`pageNo` 는 1쪽을 돌려준다
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

---

# 1a. ★★★ 상세 — ★ 표본 1 → **22건** (개정 583 · 밀린일 61·87 끝)

```
목록  GET /api/json/getList_search.json.php?price_area_min=0&price_area_max=99999  → 200 · 21KB
      ★★ ★ **개정 583 정정 (개정 587)** — ★ `search_list` 는 ★ **지점별 dict 가 아니다**
      ★ 응답 메타 ＋ `car_list` 다 —
        `{list_code, title, num_per_page, total_page, cur_page, is_random,
          total_list_num, ★ car_list[36], filter_data}`
      ★ ★ 매물은 ★ `search_list.car_list` ★ 하나에 다 있다.  ★ 「키 9개」는 ★ 지점이 아니라 메타였다
상세  GET /api/json/getData_car_detail.json.php?idx={idx}  → 200 · ★ 칸 59개
헤더  모바일 UA · `Referer: https://certified.lexus.co.kr/car-list/`
★ `robots.txt` 는 ★ 503 이라 못 받았다 — ★ 「없다」가 아니다.  ★ 다시 받아 확인한다
```

## ★ 값이 갈리는가 — 22건 실측

| 칸 | 채움 | 갈리나 | 실측 |
|---|--:|---|---|
| `car_info.number_plate` | 22/22 | ★ 22가지 | ★ 해시해서 넣는다 |
| `mileage` | 22/22 | ★ 22가지 | |
| `price` | 22/22 | ★ 11가지 | 만원 단위 |
| ★ **`release_price`** | 22/22 | ★ **8가지** | ★★ **신차가 — `value.origin`(75)** |
| ★ **`car_info.warranty`** | 22/22 | ★ **10가지** | ★★★ **「2030년 10월까지 (120,000km)」** |
| `car_info.displacement` | 22/22 | ★ 3가지 | 2,487 · 2,393cc |
| `car_info.fuel` | 22/22 | ★ 2가지 | 하이브리드 · 플러그인하이브리드 |
| `car_info.registration_date` | 22/22 | ★ 10가지 | 「2025년 10월」 |
| `car_info.check_date` | 22/22 | ★ 3가지 | 점검 시점 |
| `car_info.color` · `innerColor` | 22/22 | ★ 6 · 4가지 | |
| `branch.title` · `addr` · `tel` · 위경도 | 22/22 | ★ 5가지 | 지점 |
| `isCertified` | 22/22 | ★ **2가지** | ★ **인증 여부가 갈린다** |
| `payment.isLease/isInstalment/isCash` | 22/22 | ★ 2가지씩 | ★ 리스 매물을 가른다 |
| ★ `car_info.accident_history` | 22/22 | ☓ **안 갈린다** | ★ **22/22 「무사고」** |
| `car_info.transmission` | 22/22 | ☓ 안 갈린다 | E-CVT 22 |
| `isCheckComplete` | 22/22 | ☓ 안 갈린다 | True 22 |

```
★★★ ★★ **`warranty` 가 ★ 이 사이트의 값이다** —
   「2030년 10월까지 (120,000km)」 ★ 만료일 ＋ 상한 km 를 ★ 함께 준다.  ★ 10가지로 갈린다
   ★ ★ KB·엔카는 ★ 이것을 ★ 안 준다 ★ [실측 08-29 · 렉서스 목록 **표본 10건**에 보증 칸이 있고 KB 상세 표본 10건엔 값이 없다].  ★ `warranty.site`(36) 를 ★ 진짜로 채울 수 있다
   ★ ★ **밀린일 83 「인증중고차만의 값이 있나」의 ★ 답이다 — ★ 있다**
★★ ★ `accident_history` 는 ★ 22/22 「무사고」다 → ★ 판정값이 아니다 → ★ 사이트 보장(②)
   ★ 렉서스 인증 조건이 무사고인 것으로 ★ 보이나 ★ 22건으로 단정하지 않는다
금지  ★ `state.accident` 에 ★ 만점을 지어 주는 것 (금지 12).  ★ 아직 정하지 않았다
```

---

# 1b. ★ `core_listing` 칼럼 매핑

| 원문 | 칼럼 |
|---|---|
| `idx` | `source_id` |
| — | `site` = `'lexus_certified'` |
| `price` (만원) | `price_current_won` ★ ×10,000 |
| ★ `release_price` | ★ `price_origin_won` |
| `mileage` | `mileage_km` |
| `year` · `car_info.registration_date` | `form_year` · `reg_at` |
| `car_info.displacement` | `displacement_cc` |
| `car_info.fuel` · `transmission` | `fuel_raw` · `transmission` |
| `car_info.color` · `innerColor` | `color_ext_raw` · `color_int_raw` |
| `car_info.number_plate` | `plate_hash` ★ 해시 |
| `branch.title` · `addr` | `dealer_shop` · `dealer_region` |
| ★ `car_info.warranty` | ★ `warranty_site_until` · `warranty_site_km` (문장을 갈라 넣는다) |
| `payment.isLease` | `sell_type` ★ 리스 제외에 태운다 |
| `isCertified` · `isCheckComplete` · `check_date` | `site_pass_grade` · `site_condition_json` |
| `accident_history` | `site_condition_json` ★ **축에 안 쓴다** (전건 동일) |

---

# 1c. ★★ 전수 — ★ **74건 · 3쪽**이다 [실측 08-29 · 가이드]

```
★★★ 08-29 정정 — ★ 아래 「36건」은 ★ **1쪽만 센 것**이다 (오판 173)
   ★ 쪽넘김 열쇠는 ★ **`cur_page`** 다.  ★ `page` · `pageNo` 는 ★ **조용히 1쪽을 돌려준다**
     `&page=2`    → car_list 36 · ★ `cur_page` 응답값 **1** · 첫 idx 6404 (1쪽과 같다)
     `&pageNo=2`  → 〃
     `&cur_page=2`→ car_list 36 · ★ `cur_page` 응답값 **2** · 첫 idx 6343 (다른 매물)
   ★ 개정 587 이 ★ 「`page=2` 도 36건」을 보고 ★ 「전수 36」으로 적었다 —
     ★ ★ 규격 자신이 ★ **「`cur_page` 로 보이나 ★ 안 눌러 봤다」**(1b)고 적어 두었는데
     ★ ★ 그 위에 ★ 전수를 확정으로 쌓았다

★ 빈 쪽까지 걸어 센 것 [실측 08-29]
   cur_page=1 → 36 · =2 → 36 · =3 → 2 · =4 → 0
   ★★ 전수 ★ **74건** · `num_per_page` 36 · `total_page` 3 · `total_list_num` 74 (이번엔 맞았다)
   ★ 세는 법 — `idx` 를 집합으로 모았다.  ★ 쪽마다 더하지 않았다

★ 모델 분포 [실측 08-29] — ES 33 · UX 17 · NX 14 · RX 6 · LX 3 · LS 1
★★ ★ 우리 등록 대상(ES·NX·RX)은 ★ **53건**이다 — ★ 아래 「10건」은 죽은 수다

★★★★ 그리고 ★ `tools/collect_lexus.py:115` 가 ★ `_done = bool(cars)` 다 —
   ★ ★ **1쪽 36건만 받고 「끝까지 받았다」로 `sweep_gone_groups` 를 부른다.**
   ★ ★ 그러면 ★ 2·3쪽 38건이 ★ **팔리지도 않았는데 `gone` 이 된다** (코드 실측 08-29)
   ★ ★ 「렉서스가 10 → 0 으로 줄었다」가 ★ 이 자리일 수 있다 [추론 08-29 — DB 를 못 봤다]
```

---

# 1c-옛. ★ 개정 587 의 36건 (★ 1쪽만 센 것 — ★ 위가 정본이다)

```
★ 조건을 다섯 꼴로 바꿔 두드렸다 —
  기본(0~99999) · 범위 넓힘(0~999999) · group_type=all · page=2   → ★ 넷 다 ★ 36건
  조건 없음 → ★ JSON 이 아니다 (필수 파라미터다)
★ `total_list_num` 이 ★ 0 으로 온 적이 있다 — ★ 이 값을 총계로 믿지 마라.  ★ `car_list` 를 세라
```

## 모델 분포 (실측 08-23 · 1쪽만)

| 모델 | 건수 |
|---|--:|
| ES 300h | 18 |
| ★ **NX 350h** | ★ **7** |
| UX 300h | 5 |
| ★ **NX 450h+** | ★ **2** |
| LM 500h | 2 |
| UX 250h | 1 |
| ★ **RX 450h+** | ★ **1** |
| **합** | **36** |

```
★★ ★ 우리 등록 대상은 ★ NX ＋ RX = ★ **10건**이다
   ★ ★ KB 는 ★ NX 90 + RX 53 = ★ **143건** — ★ **14배**다
★★★ ★ 그런데 ★ 건수만으로 정하지 않는다 —
   ★ 렉서스 인증만 ★ `warranty` 만료일 ＋ 상한 km 를 준다 (1a장)
   ★ ★ KB 는 ★ 그 값을 ★ 안 준다 ★ [실측 08-29 · KB 상세 **표본 10건** · 매물마다 다른 보증 값 **0/8**].  ★ 채우는 축이 ★ 다르다
   ★ ★ 그러므로 ★ 「KB 로 건수를 채우고 · 렉서스로 보증 축을 채운다」가 ★ 옳다
   ★ 같은 차를 ★ 두 사이트가 낼 때 ★ 어느 쪽을 남길지는 ★ 중복 제거 규칙이 정한다
```

---

# ★★★★★ 08-29 — ★ **상세가 있다.  ★ 「살아 있나」를 가를 수 있다** (개발측 물음에 답한다)

```
★ 개발측 — 「★ 렉서스 gone 3건 — ★ **상세가 없다**(규격 1c).  ★ 「살아 있나」를 못 가른다.
   ★ **짐작으로 안 되돌렸다**」  → ★ **짐작 안 한 것이 옳다.  ★ 그리고 상세는 있다**

★ 가이드가 두드렸다 [실측 08-29 · 다섯 이름] —
  `/api/json/getData_car_detail.json.php?idx={idx}`  → ★ **200 · 12,585B**
  `/api/json/getView_car.json.php` · `getData_car.json.php` · `/car/view/{idx}`
  · `getDetail.json.php`                              → ★ 다 **406**
★ ★ 곧 ★ **이름 하나뿐이다.  ★ 「없다」가 아니라 「이 이름이다」**
```

## ★★ 「살아 있나」를 가르는 법 [실측 08-29]

| | 응답 |
|---|---|
| ★ 살아 있다 (`idx=6047`) | 200 · **12,585B** · 키 `status·message·**car_detail**·related_list·contact_us` |
| ★ 없다 (`idx=999999` · `idx=1`) | 200 · ★ **71B** · `car_detail` 이 **없다** |

```
필수  ★ **`car_detail` 이 있으면 살아 있다**.  ★ 없으면 `gone` 이다
필수  ★ **200 으로 가르지 마라** — ★ 없는 것도 200 을 준다 (K카와 같은 꼴)
필수  ★ 크기로도 가를 수 있다(12KB ↔ 71B) — ★ 다만 ★ **키로 가르는 것이 낫다**
★ ★ 규격 1c 의 「목록이 매물의 전부다」는 ★ **08-29 에 물린다** — ★ 상세가 있다
★ 목록 전량 ★ **73건** [실측 08-29 · 빈 쪽까지]
```

---

# ★★★★★ 08-29 — ★ **렉서스를 내가 직접 열었다** (「열두 축이 다 없다」를 물린다)

```
★★★ 마스터 — 「★ **렉서스가 왜 내 몫이지?**」
★ ★ **옳다.  ★ 내가 안 재고 마스터께 넘겼다** — ★ 오판이다
★ ★ 열어 보니 ★ **내가 「없다」고 한 것 중 여럿이 있다**
```

## ★ `car_detail` — ★ 실측 08-29

| 우리 축 | 점 | ★ 칸 | 값 (표본) |
|---|--:|---|---|
| ★ `value.origin` 신차가 | **75** | ★ **`release_price`** | ★ **7613** (현재가 7000) |
| ★ `warranty.general`·`power` | **54** | ★ **`car_info.warranty`** | ★ **「2031년 1월까지 (120,000km)」** |
| ★ `taste.option` 옵션 | **43** | ★ **`spec[].list[].txt`** | 「오픈포어 우드 인테리어 트림」 … |
| `taste.color` 색상 | 15 | `color.title`·`value` | Black · `#000000` |
| `state.year` 연식 | 80 | `year` | 2026 |
| `value.mileage` 주행 | 107 | `mileage` | 4748 |
| `warranty.site` 사이트검증 | 36 | `isCertified` · `isCheckComplete` · `benefit` 「191항목」 | true |
| — | — | ★ `car_info.number_plate` | ★ **「334오 8104」** ← 차량번호를 준다 |
| ★ 사고·골격·외판·자차·용도·소유자·미가입·특수·누유 | ★ **207** | ★ **없다** | ★ **정말 없다** |

```
★★★ ★ **내가 「열두 축이 다 없다」고 한 것은 틀렸다** — ★ 없는 것은 ★ **아홉 축 207점**이고
   ★ ★ ★ **신차가 75 · 보증 54 · 옵션 43 = 172점은 ★ 이미 오고 있다**
★ ★ 파서가 없어서 ★ **하나도 안 읽고 있었다** (`parse/lexus_certified` 가 없다)
★★ ★ **차량번호를 준다** — ★ 다만 ★ **인증 직영이라 다른 사이트에 안 올라간다**
   ★ ★ 짝이 안 생기니 ★ 나머지 **207점**(사고 51 · 골격 43 · 외판 28 · 자차 28 · 용도 22 · 소유자 11 · 미가입 18 · 특수 21 · 누유 15)은 ★ **성능점검부를 따로 받아야 한다**
```

★ **다음에 잴 것 (내 몫)** — ★ 렉서스가 ★ **성능점검부를 어디에 두는지**.
  ★ `benefit` 의 「191항목 검증」이 ★ 그 자리일 수 있다 — ★ 아직 안 열어 봤다.
