# 기아 인증중고차(CPO) API — 조사

`SPEC-2026.08.22-r481` · 2026-08-22 · **가이드가 직접 실측했다 (원칙 4)**
주소는 **마스터가 주셨다** — `https://cpo.kia.com/` (가이드가 도메인 6개를 찔러 다 틀렸다)

---

# 0. 결론

```
★★★ ★ 목록·상세 ★ 둘 다 ★ 인증 없이 ★ 평문 JSON.  ★ 지금까지 본 것 중 가장 쉽다
★ 총 ★ 1,022대 · `size=100` 한 번에 100건씩
★★ 상세 ★ `GET /api/product/detail/{id}/` — ★ 우리 축이 거의 다 있다 (3장)
```

---

# 1. 경로 — 전부 `GET` · 인증 없음

| 무엇 | 경로 | 실측 |
|---|---|---|
| **목록** | `/api/search/?size=100` | ★ **200** · 94,714B · **totalElements 1,022** |
| 조건 facet | `/api/search/conditions/` | 200 — 색상·연료·변속·인승·옵션·판매점·키워드·등급 |
| 차종 목록 | `/api/search/category-models/` | 200 |
| 추천 | `/api/recommendation/curation/` · `/api/product/recommendations/?size=10` | 200 |
| 인기 차종 | `/api/main/top-models/` | 200 |

```
헤더  User-Agent · Referer: https://cpo.kia.com/ · ★ x-referer-pathname: /
★ 인증·토큰·암호화 ★ 없다.  ★ 서버에서 그냥 부르면 200 이다 (브라우저 없이 확인)
★ robots.txt 는 ★ 404 다 — 없다.  ★ 금지 규칙 자체가 없다
★ Next.js 라 ★ HTML 에는 값이 없다.  ★ curl 로 홈만 받으면 「매물 0」으로 보인다
   ★ 헤이딜러에서 같은 방식으로 틀렸다 (오판대장 #43).  ★ 되풀이하지 않았다
```

---

# 2. ★ 목록이 주는 것 — 필드 29개 (실측)

| 우리 축 | 배점 | 기아 CPO 필드 | 값 예시 |
|---|--:|---|---|
| — 매물번호 | — | `id` · `plateNumber` | 12392 · 302우6960 |
| 차종 | — | `modelCodeName` · `modelName` · `modelCategory` | 셀토스 · 셀토스 1.6 가솔린 시그니처그래비티 2WD · SUV |
| `taste.trim` 트림 | 59 | `modelTrim` · `modelMission` · `modelDoor` | 시그니처 그래비티 · A/T · 5인승 |
| `value.budget` 예산 | 95 | `price` | 26,830,000 |
| `state.year` 연식 | 80 | `modelYear` · **`firstRegisteredOn`** | 2025 · **2024-10-11** |
| `value.mileage` 주행 | 107 | `drivingDistance` | 32,842 |
| 연료 | — | `modelEngine` | 1.6 가솔린 |
| `taste.color` 색상 | 15 | `exteriorColorCodeName` · `interiorColorCodeName` | 스노우화이트펄 · 블랙 |
| `warranty.site` 사이트 검증 | 36 | ★ `classification` | **LITE / EXCLUSIVE** (등급이 있다) |
| `state.accident` 사고 | 48 | ★ `customKeywords` | **「보험이력없음」** |
| 사진 | — | `exteriorImageUrl` · `interiorImageUrl` | CDN |
| 인기 | — | `wishCount` · `consultationCount` | 67 · 0 |
| 등록일 | — | `displayedAt` | 2026-08-18 |
| 예약 | — | `reserved` | false |

```
★ `firstRegisteredOn` 이 ★ 날짜로 온다 — 연식 축을 ★ 월 단위로 잴 수 있다 (엔카는 연·월)
★ `classification` 이 ★ LITE / EXCLUSIVE 로 갈린다 — ★ 사이트 검증 단계의 재료다
★ `customKeywords` 에 ★ 「보험이력없음」 같은 판정이 온다 — ★ 사이트가 이력을 요약해 준다
★ 조건 facet 에 ★ `options` · `customKeywords` · `classifications` 가 있다 — 필터를 그대로 쓸 수 있다
```

## 목록만으로 채워지는 축

```
채워진다  트림 59 · 연식 80 · 주행 107 · 예산 95 · 색상 15 · 사이트검증 36 ·
          사고 48(`보험이력없음` 키워드 기준)                      ★ 합 440 / 910
못 채운다 신차가 75 · 시세 30 · 옵션 43 · HUD 18 · 지정옵션 18 · 선루프 12 ·
          골격 40 · 외판 26 · 수리비 26 · 특수사고 20 · 소모품 14 · 누유 14 ·
          진정성 7 · 압류저당 7 · 용도 21 · 소유자변경 10 · 자차미가입 17 · 보증 54
★ 옵션이 목록에 ★ 안 온다 (facet 에는 있다) — ★ 상세에 있을 것이다
```

---

# 3. ★★ 상세 — `GET /api/product/detail/{id}/`

```
GET https://cpo.kia.com/api/product/detail/{id}/     → ★ 200 · 9,636B · 평문 JSON
헤더  User-Agent · Referer: https://cpo.kia.com/products/ · x-referer-pathname: /products/
★ 인증·토큰 ★ 없다.  ★ 서버에서 그냥 200 이다
★ `{id}` 는 ★ 목록 `/api/search/` 의 `id` 를 그대로 쓴다 — ★ 목록과 상세가 이어진다
★ 상세 화면 주소는 `/products/{id}/` 인데 ★ 404 다.  ★ API 로만 받는다
★ 시도해 실패한 경로 — `/api/product/{id}/` · `/api/products/{id}/` · `…/inspection/` 등 ★ 전부 404
```

## 최상위 블록 25개

```
id · reservation · car · ★ performanceRecord · ★ insuranceRecord · ★ warranties ·
★ merchandising · benefit · mainOptions · optionPrice · optionCount · recentPrice ·
productSeller · orderable · discount · kcs · displayChannel · salesOffice ·
consultationCount · classification · customKeywords · ★ performanceReportPdfUrl …
```

## ★ 우리 축과 맞춰 본 것 (표본 `id=10831` · 카니발 1.6 HEV 시그니처)

| 우리 축 | 배점 | 기아 CPO | 값 |
|---|--:|---|---|
| `state.frame` 골격 · `state.outer` 외판 | 43+28 | ★ `performanceRecord.panelOrExchange` | **0** (판금·교환 건수) |
| `state.accident` 사고 | 51 | ★ `insuranceRecord.damaged` | **0** |
| `history.use` 용도 | 22 | ★ `insuranceRecord.changeOfUse` | **0** |
| `warranty.general` 일반 | 22 | ★ `warranties` `BA`·`AC`·`CM` | **잔여 12개월 / 20,000km** |
| `warranty.power` 동력계 | 32 | ★ `warranties` `EG`·`PT`·`EM` | **잔여 29개월 / 68,514km** |
| `state.consumable` 소모품 | 15 | ★★ `merchandising.items` | **엔진오일·오일필터·에어크리너 교환 · 에어컨필터 교환 · 워셔액/부동액 보충** |
| — 정비 이력 | — | 〃 | 광택 · **전면유리 복원** · **운전석 뒤 도어 복원** · 가니쉬 교환 |
| `taste.option` 옵션 | 43 | `mainOptions` (13종 · 이름) | LEATHER_SEATS · NAVIGATION · **SUNROOF** · ADAS … |
| `taste.sunroof` 선루프 | 12 | 〃 `SUNROOF` | true |
| `taste.trim` 트림 | 59 | `car.trim` · `car.modelName` | 시그니처 |
| `state.year` 연식 | 80 | `car.firstRegisteredOn` | **2024-02-19** (날짜) |
| `value.mileage` 주행 | 107 | `car.drivingDistance` | 31,486 |
| `value.budget` 예산 | 95 | `car.price` · `discount.discountedPrice` | 4,789만 → **4,693만** (96만 할인) |
| `taste.color` 색상 | 15 | `car.color` | 스노우화이트펄 / 토프 |
| `warranty.site` 사이트 검증 | 36 | ★ `classification` | **PREMIUM** (LITE · EXCLUSIVE 외에 ★ PREMIUM 도 있다) |
| — 옵션가 | — | `optionPrice` · `optionCount` | 600만 · 102개 |
| — 판매자 | — | `productSeller` · `salesOffice` | 안기태 · 경기 평택 · 지점/층/구역 |
| — 사진 | — | `car.images` | **63장** |
| — 혜택 | — | `benefit` | 포인트 5만 · **정기점검 6회(2032-02-19까지)** · **무상연장 2029-02-19** |
| — ★ 성능점검 원본 | — | ★ `performanceReportPdfUrl` | ★ **PDF 주소를 준다** |

```
★★ `merchandising` 이 ★ 소모품 축을 채운다 — ★ 엔카·KB·현대 ★ 어디도 안 주는 값이다
   ★ 기아가 ★ 무엇을 교환·보충·복원했는지 ★ 항목으로 준다.  ★ 우리 `state.consumable` 15점이 산다
★★ `warranties` 가 ★ 종류별로 ★ 잔여 개월·km 를 준다 (BA 차체 · AC 에어컨 · EG 엔진 ·
   PT 동력전달 · EM 배기 · CM 소모품).  ★ 현대와 같은 급이다
★ `classification` 이 ★ LITE · EXCLUSIVE · ★ PREMIUM ★ 셋이다 — f-table 단계를 고쳐야 한다 (5장)
★ `performanceReportPdfUrl` — ★ 성능점검기록부 원본 PDF 주소.  ★ 골격·외판을 더 캘 수 있다
```

## 못 채우는 축

```
✘ `value.origin` 신차가 — 없다.  ★ 차종·트림 표에서 보충 (f-table 「사이트별 채우기」 ③)
✘ `value.market` 시세 — 우리 산출 (④)
✘ `history.not_join` 자차 미가입 · `history.owner` 소유자 변경 · `history.seizing` 압류·저당
   → ★ 성능점검 PDF 안에 있을 수 있다.  ★ 아직 안 열었다
```

---

# 4. 우리 규격에서의 값

```
★ 기아 인증중고차는 ★ 제조사가 직접 검사·보증한다
   → ★ 사이트 검증 축 최고 단계 자리다 (K카 직영 · KB진단 · 현대 인증과 나란히)
   → ★ `classification` LITE / EXCLUSIVE 로 ★ 단계를 더 가를 수 있다
★ 마스터 후보와 겹치는 것 — ★ 스포티지 · EV6 · EV5 · 셀토스 …
   ★ 등록 차종 SPORTAGE_LPI 와 바로 겹친다
★ 1,022대는 ★ 엔카(3,916) 다음으로 큰 표본이다.  ★ KB·K카보다 붙이기 쉽다
```

---

# 5. 다음 (가이드 몫)

```
① ~~상세 API 를 잡는다~~ ★ 끝 — `/api/product/detail/{id}/` (3장)
② ★ `classification` 이 ★ 셋이다 (LITE · EXCLUSIVE · ★ PREMIUM) — ★ f-table 사이트 검증 단계를 고친다
③ ★ `performanceReportPdfUrl` 을 열어 ★ 골격·외판·압류저당·소유자 변경이 있는지 본다
④ 표본을 늘려 ★ `panelOrExchange` · `damaged` 가 0 이 아닌 매물도 확인한다
```
