# 엔카 API — 전수 조사

```
version  SPEC-2026.08.28-r804
follows  ★ 생성물 — `tools/probe_encar.py`
sources  개정 560 · 실측 08-23
checks   S46-31
```
★ 이 문서는 ★ **그 사이트가 무엇을 주는가**만 적는다.  ★ 판정은 ★ `f-table` 이 한다 (가이드역할 ㉺)


**`tools/probe_encar.py` 가 만든다. 손으로 적지 않는다.**

```
★★★ 호스트 — ★ `https://api.encar.com`
★★ robots `Disallow: /` — 마스터 판단 대기 (`ENCAR_ROBOTS.md`)
```

가이드 승인 (`OVERNIGHT_20260817` §2 ① — 「규칙 2 예외 · 이 파일은 만들어도 됩니다」).

조사일 2026-08-17 · 표본 `42112312` (그랜저 GN7 · 220호4056) 외 차종별 10건

---

## 1. 어떻게 찾았나 — 브라우저를 열지 않았다

```
fem.encar.com 의 세 화면이 같은 번들 하나를 쓴다
  /cars/detail/{id}
  /car-verification/report/{id}?fromAdType=AD_NORMAL
  /cars/report/diagnosis/{id}
      → /assets/app-DATxvME_.js   548,080바이트
```

**그 번들에 부르는 주소가 전부 문자열로 들어 있다.** `/vN/` 경로 **47종**을 뽑았다.

```
★ 「시세」 「적정」 「경쟁력」은 번들에 없다 — 응답이 만들어 보내는 문구다
★ 「틴팅」은 15번 나온다 — 항목표가 번들에 있다 (아래 4절)
```

---

## 2. ★ 인증 없이 되는 것 — 지금 서버에서 200

| 경로 | 크기 | 무엇이 오나 | 우리가 쓰나 |
|---|--:|---|:--:|
| `/search/car/list/mobile` | — | 목록 | **쓴다** (서울 IP 407 · 브라우저 수집) |
| `/v1/readside/vehicle/{id}` | ~20KB | 상세 — 보증·신차가·옵션코드·사진 | **쓴다** |
| `/v1/readside/inspection/vehicle/{id}` | 10,184 | 성능점검부 — 항목 103종 | **쓴다** |
| `/v1/readside/record/vehicle/{id}/open` | — | 보험이력 | **쓴다** |
| `/v1/readside/diagnosis/vehicle/{id}` | 1,048 | 엔카진단 — 외판 8부위 | **쓴다** |
| `/v1/readside/vehicles/car/{id}/options/choice` | 1,130 | 선택 옵션 이름·가격 | **쓴다** |
| **`/v1/readside/record/vehicle/{id}/summary`** | 577 | **용도 · 전손 · 침수 · 도난 · 소유자 변경** | ✗ |
| **`/v1/readside/inspection/vehicle/{id}/summary`** | 76~432 | 외판 요약 · **점검자 이름** | ✗ |
| **`/v1/readside/clean-encar/vehicle/{id}`** | 37 | **엔카 클린 판정** `cleaned` | ✗ |
| **`/v1/readside/diagnosis/vehicle/{id}/sellingpoint`** | 381~1,799 | 판매 포인트 (대·중·소 분류) | ✗ |
| **`/v1/readside/vehicle/ev-battery/{id}`** | 69 | 전기차 배터리 (지금 전부 null) | ✗ |
| **`/v1/readside/extend-warrant/vehicle/{id}`** | 82 | **엔카 연장보증 쿠폰·유형** | ✗ |
| **`/v1/readside/vehicles/car/options/standard`** | 28,228 | **기본 옵션 코드 → 이름 (전체 사전)** | ✗ |
| **`/v1/readside/vehicles/car/options/tuning`** | 1,223 | 튜닝 옵션 사전 | ✗ |

### 차종별 실측 (10종 · 표본 1건씩)

| 차종 | inspection/summary | record/summary | clean-encar | sellingpoint | ev-battery | extend-warrant |
|---|:--:|:--:|:--:|:--:|:--:|:--:|
| G70_20T | 200 | 200 | 200 | 200 | 200 | 404 |
| G70_25T | 200 | 200 | 200 | 200 | 200 | 404 |
| G80_25T | 200 | **404** | 200 | 200 | 200 | 404 |
| G80_EV | 200 | 200 | 200 | 200 | 200 | 404 |
| GRANDEUR_LPG | **404** | **404** | 200 | 200 | 200 | 404 |
| GV60 | 200 | 200 | 200 | 200 | 200 | 404 |
| GV70_EV | 200 | 200 | 200 | 200 | 200 | 404 |
| KOLEOS_HEV | **404** | 200 | 200 | 200 | 200 | 404 |
| MODEL_Y | **404** | 200 | 200 | 200 | 200 | 404 |
| SPORTAGE_LPI | **404** | 200 | 200 | 200 | 200 | 404 |

```
★ 404 는 「그 매물에 그 자료가 없다」다.  차종 문제가 아니다
★ extend-warrant 는 표본 42112312 에서만 200 이었다 (쿠폰이 붙은 매물만)
```

### `record/summary` 가 주는 것 — **개정 296 §4·§6 이 여기 있다**

```json
{"carNo":"220호4056", "year":"2023", "use":"3", "fuel":"가솔린",
 "model":"그랜저 (GN7)", "firstDate":"2023-01-11", "displacement":"2497",
 "myAccidentCnt":0, "otherAccidentCnt":0, "ownerChangeCnt":0,
 "robberCnt":0, "totalLossCnt":0, "floodTotalLossCnt":0, "floodPartLossCnt":null,
 "government":0, "business":0, "loan":1, "accidentCnt":0,
 "myAccidentCost":null, "otherAccidentCost":null}
```

```
use            용도 — 렌트 판정
totalLossCnt   전손 · floodTotalLossCnt 침수 · robberCnt 도난   ★ 특수 사고이력
ownerChangeCnt 소유자 변경 회수
loan           저당
```

---

## 3. ★★ 로그인이 필요한 것 — 401

| 경로 | 코드 | 무엇이 오나 |
|---|:--:|---|
| `/v2/verification/{id}/unified-report/free` | **401** | 항목별 점검 리포트 · **시세 막대** |
| `/v2/verification/{id}/unified-report/lite` | **401** | 〃 |
| `/v2/verification/{id}/unified-report/paid` | **401** | 〃 |
| `/v2/verification/{id}/report-analysis/performance-inspection` | **401** | 성능점검 AI 분석 |
| `/v2/verification/{id}/report-analysis/options` | **401** | **유료 옵션 합계** |
| `/v2/verification/{id}/report-analysis/insurance-history` | **401** | 보험이력 AI 분석 |

```
★ 401 Unauthorized 다.  407(IP 차단)이 아니다
  {"status":401,"error":"Unauthorized","path":"/v2/verification/…/unified-report/free"}
★ 마스터는 로그인해서 보이고 우리는 안 해서 안 보인다
→ /admin/collect 브라우저 수집으로 받을 수 있다 (마스터 회선 · 로그인 세션)
```

---

## 4. 번들이 알려 준 항목표 — 마스터가 본 그것

```js
{ 성능점검기록부 : {category:"etc",      id:235},
  기타정비내역   : {category:"etc",      id:239},
  "차량 키 수량" : {category:"basic",    id:10},
  "제조사 매뉴얼" : {category:"basic",    id:11},
  "틴팅 (정면 유리)": {category:"basic",  id:16},
  "리페어 장비"  : {category:"exterior", id:186},
  소화기        : {category:"exterior", id:189} }

탭  기본정보 BASIC · 등화장치 · 실내 INTERIOR · 외관 EXTERIOR · 휠타이어 STATE · 옵션
```

**이 값들은 3절의 401 리포트에만 있다.** 우리가 받는 6종에는 없다 (확인함).

---

## 5. 못 찾은 것

```
시세 막대 「3,831만 ── ● 적정 ── 4,056만」
  ★ 번들 47경로에 시세·가격 경로가 없다
  ★ 「시세」 「적정」 문구도 번들에 없다 — 응답이 문구까지 만들어 준다
  → 3절의 unified-report 안에 있을 가능성이 가장 크다.  401 을 풀면 확인된다
```

---

## 6. 우리 대상이 아닌 경로 (참고)

```
/v1/partnership/*   딜러 정산      /v2/orders/*  /v3/order/*   주문·결제
/v2/coupons/my      쿠폰          /v2/untact/judgements
/v1/readside/user/* 로그인 사용자
/v1/readside/nonstandard/*  광고 지표 (500)
```

---

## 7. 검토 22 가 물은 둘 — 엔카 원문에 있는가 (08-17 실측)

### ① 차대번호 — **있습니다.** 크로스사이트가 됩니다

```
core_listing.vin        2,772 / 7,697   상세 원문 vin
core_inspection.vin     1,587 / 1,914   성능점검부 vin
서로 대조   같은 것 1,407 · 다른 것 6
서로 다른 차대번호  1,689개
예   KNMP5B2U2SP014939
```

```
★ K카가 KNMP5B2U7SP045300 을 공개하는 것과 같은 형식입니다
★ 다만 엔카는 36% 만 옵니다 (2,772/7,697) —
  차대번호가 없는 매물은 다른 값으로 가려야 합니다 (8장 STEP 30 2순위)
★ 상세와 점검부가 어긋난 6건은 따로 봐야 합니다
```

### ② 자차 미가입 기간 — **있습니다.** 개정 294 · `V3-49` 가 돌 수 있습니다

```
원문   record 의 notJoinDate1~5  →  core_record.not_join_json
형식   ["202412~202502", null, null, null, null]

기간이 있는 매물   1,308 / 2,243  (58.3%)
구간 수            1,352건
기간 중앙값        34개월 · 최장 64개월
```

```
★ K카 화면의 「2025.07~2026.05 (10개월)」과 같은 값입니다
★ 받아서 저장까지 돼 있었고 판정·화면이 안 쓰고 있었습니다
  — 보증·신차가·옵션가 때와 같은 모양입니다 (2절)
```

---

# ★★★ 볼보 전기 — ★ **셋으로 갈린다** (마스터 실측 08-28 · 개정 803)

```
★★ 마스터께서 ★ **네 매물 주소를 주셨다** — ★ `fem.encar.com/cars/detail/{id}`
★ ★ 상세는 ★ `api.encar.com/v1/readside/vehicle/{id}` 로 ★ **다 열린다** (200)
```

| 매물 | `ModelGroup` | 트림 | 연료 | 연식 |
|---|---|---|---|---|
| 42395759 | ★ **C40** | 트윈 얼티메이트 | 전기 | 2022-04 |
| 41758618 | ★ **C40** | 트윈 얼티메이트 | 전기 | 2022-04 |
| 42152084 | ★ **XC40** | 트윈 얼티메이트 | ★ **전기** | 2024-08 |
| 42519599 | ★★ **EX30** | 울트라 | 전기 | 2025-05 |

```
★★★ ★ **엔카는 볼보 전기를 ★ 셋으로 나눈다** —
   ★ ★ **`C40`** — ★ 옛 C40 리차지 (지금 EC40)
   ★ ★ **`XC40`** — ★ **전기가 섞여 있다** (EX40 · 옛 XC40 리차지)
      ★ ★ 이름이 안 갈린다.  ★ **`fuel_match` 로 갈라야 한다**
   ★ ★ **`EX30`** — ★ **따로 있다.  ★ 우리 차종에 없었다**

필수  ★ ★ **`EX30` 을 넣었다** — ★ 차종 **23종**
필수  ★ ★ **`C40` 은 ★ 코드가 맞았다** — ★ 0건인 까닭은 ★ **마스터께서 목록을 안 받아 주셔서**다
      ★ ★ 엔카 수입은 ★ **브라우저 수집으로만** 온다 (407)
필수  ★ ★ `XC40_IMPORT` 180건 중 ★ **전기를 세어 적어라** — ★ 그것이 EX40 이다

## ★★ 마스터께서 주신 C40 목록 주소 (08-28)

```
action=(And.Hidden.N._.(C.CarType.N._.(C.Manufacturer.볼보._.(C.ModelGroup.C40._.Model.C40 리차지.))))
title = 볼보 C40 리차지(22년~현재)
```

```
★★ ★ **`ModelGroup=C40` 이 맞다** — ★ 가이드 코드가 옳았다
★ ★ 그 아래 ★ **`Model=C40 리차지`** 층이 하나 더 있다
★ ★ 우리는 ★ **`ModelGroup` 까지만 쓴다** — ★ 세대를 안 가른다 (개정 776 그대로)
★ ★ `toggle.modelGroup=1` 은 ★ **화면 접힘 상태**다 — ★ 안 보낸다
```
```
