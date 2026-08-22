# 기아 인증중고차(CPO) API — 조사

`SPEC-2026.08.22-r473` · 2026-08-22 · **가이드가 직접 실측했다 (원칙 4)**
주소는 **마스터가 주셨다** — `https://cpo.kia.com/` (가이드가 도메인 6개를 찔러 다 틀렸다)

---

# 0. 결론

```
★★ 목록이 ★ 인증 없이 ★ 평문 JSON 으로 완전히 열린다.  ★ 지금까지 본 것 중 가장 쉽다
★ 총 ★ 1,022대 · `size=100` 한 번에 100건씩
★ 다만 ★ 상세 API 를 아직 못 찾았다 — 상세 화면이 값을 안 그린다 (아래 3장)
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

# 3. ★ 상세 — 아직 못 찾았다

```
화면  https://cpo.kia.com/product/{id}/   → 200 · 67,419B
      ★ 그런데 본문에 「성능·사고·보험·보증·압류·저당·침수·주행·옵션」이 ★ 0회다
      ★ 값을 그리는 XHR 도 안 떴다 (`/api/isToken/` · `/api/alert/page/` · `/api/notifications/` 만)
시도  /api/product/{id}/ · /api/products/{id}/ · /api/search/{id}/  → ★ 전부 404

★ 까닭 추정 — ① 로그인해야 상세가 열린다 (`/api/isToken/` 을 부르는 것이 그 흔적)
              ② 또는 상세 경로가 다른 형태다
★★ ★ 지어내지 않는다.  ★ 다음에 ★ 목록에서 카드를 눌러 들어가 다시 잡는다
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
① ★ 상세 API 를 잡는다 — 목록 카드를 눌러 들어가 XHR 을 본다.  로그인 여부도 확인한다
② 잡히면 ★ 항목 대조표를 만든다 (엔카·KB 와 같은 형식)
③ ★ 사이트 검증 축에 ★ 「제조사 인증」 단계를 규격으로 쓴다 —
   현대 인증 · 기아 CPO(LITE/EXCLUSIVE) · K카 직영 · KB진단 · 헤이딜러eye 를 한 표로
```
