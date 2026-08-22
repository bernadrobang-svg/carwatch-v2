# 현대·제네시스 인증중고차 API — 조사 (★ 미완)

`SPEC-2026.08.22-r480` · 2026-08-22 · **가이드가 직접 실측했다 (원칙 4)**

```
★★★ ★ 목록·상세 ★ 둘 다 뚫렸다.  ★ 인증·토큰 없다.  ★ 개발측에 넘길 수 있다
★ 마스터가 주소 둘을 주셔서 풀렸다 — 상세 `goodsDetail.do?goodsNo=…` · 목록 `/m/search/vehicle`
★ 가이드는 그 전에 ★ 두 번 「목록이 없다」로 멈춰 있었다 (개정 478)
```

---

# 1. 열려 있는 것

```
robots.txt   User-agent: * / Allow: /        ★ 금지 경로가 하나도 없다
홈           https://certified.hyundai.com/                   200
매물 화면    https://certified.hyundai.com/p/display/readyVehicle.do   200 · 335KB
```

## ★ 되는 API — 차종별 시세·건수

```
GET /api/main/modelGroupDistribution?repnCarCd={차종코드}     → 200 · 평문 JSON
{"code":"0000","body":{"mdlMinPric":17500000,"mdlMaxPric":34500000,"mdlCnt":189,
 "vehicleList":[{"salePrice":22500000,"mileage":47282}, …]}}

★ 인증·토큰 없다.  ★ 서버에서 그냥 200 이다
★ 없는 경로는 {"code":"9404","message":"Page not found."} 로 답한다 — 스프링 계열
```

**실측 — 차종별 건수 (2026-08-22)**

| 코드 | 차종 | 건수 | 가격대 | `vehicleList` |
|---|---|--:|---|--:|
| `IG02` | 더 뉴 그랜저(IG) | **189** | 1,750~3,450만 | 60 |
| `GN01` | 그랜저(GN7) | **145** | 2,390~4,660만 | 87 |
| `JX01` | GV80 | 16 | 3,790~5,610만 | 9 |
| `CN01` | 아반떼 | 10 | 1,250~2,490만 | 5 |
| `RG31` | G80 | 0 | — | 0 |

```
★ `vehicleList` 는 ★ `salePrice` 와 `mileage` ★ 둘뿐이다 — ★ 매물번호도 트림도 없다
★ 시세 분포를 그리는 용도다.  ★ 매물 목록이 아니다
★ 화면에는 「Slim 23 · 189대」 「3 · 163대」 「1 · 82대」처럼 ★ 차종별 건수가 나온다
★ 화면 총계는 ★ 164대 (readyVehicle.do 첫 화면)
```

---

# 2. ★ 못 찾은 것 — 매물 목록 API

```
★ 시도한 것
  ① 매물 화면을 브라우저로 열고 ★ 아래로 4~5번 스크롤        → ★ 목록 XHR 이 안 뜬다
  ② 「모두 보기」 · 「전체」 · 「최신순」 · 「필터」 를 눌러 봄  → ★ 안 뜬다
  ③ 경로 후보 7개 직접 호출                                   → ★ 전부 404
     /api/vehicle/list · /api/vehicles · /api/display/vehicleList ·
     /api/search/vehicle · /api/main/vehicleList · /api/vehicle/search ·
     /api/readyVehicle/list
  ④ HTML 안에서 `vhclNo` · `carNo` · `goDetail` · `detail.do` 찾기 → ★ 0회
     `.do` 경로 자체가 HTML 에 ★ 하나도 없다

★ 잡힌 XHR 은 ★ 화면 조각(HTML)뿐이다
  /m/display/hiLabReportView · recentReviewElementView · … → ★ 리뷰·추천 배너다
```

```
★★ 추정 — ★ 매물 목록이 ★ 로그인 뒤에 열리거나 ★ 앱 전용일 수 있다
★ 화면에 「매일 오후 5시! 새로운 현대인증중고차를…」 이라 적혀 있다 — ★ 재고가 적다
★ 그러나 ★ 추정이다.  ★ 지어내지 않는다
```

---

# 2a. ★★ 상세 — 완전히 뚫렸다

```
GET /m/goods/goodsDetail.do?goodsNo={goodsNo}    → ★ 200 · 204,390B
헤더  모바일 UA · Referer: https://certified.hyundai.com/
★ 인증·토큰·암호화 ★ 없다.  ★ 서버에서 그냥 200 이다 (브라우저 없이 확인)
★ 매물번호 꼴 — `GJJ260317025652` (영문 3 + 숫자 12)
```

## 실측 — 표본 `GJJ260317025652` (2025 G80 RG3 F/L 가솔린 2.5T AWD 스탠다드)

| 우리 축 | 배점 | 현대 인증 원문 | 값 |
|---|--:|---|---|
| 차종·트림 | — | 제목 | 2025 G80 (RG3 F/L) 가솔린 2.5 터보 AWD **스탠다드 디자인** |
| `state.year` 연식 | 80 | **최초등록일** | **2024.07.24** (24년 07월 · 25년형) |
| `value.mileage` 주행 | 107 | 주행거리 | 20,565km |
| `value.budget` 예산 | 95 | 판매가 | **5,090만** (5,590만에서 ★ 500만 할인) |
| `taste.color` 색상 | 15 | 외관컬러 · 내장컬러 | 비크 블랙 · 블랙원톤 |
| 연료·배기량 | — | 연료 · 배기량 | 가솔린 · 2,497cc |
| `state.accident` 사고 | 51 | **내차피해이력** | **1건** |
| `history.owner` 소유자 변경 | 11 | **소유자 변경** | **있음** |
| `history.seizing` 압류·저당 | 8 | **압류 / 저당** | **없음 / 없음** |
| `warranty.general` 일반 | 22 | ★ **잔여 보증 — 차체·일반·냉난방** | ★ **2년 10개월 남음 · 2029년 7월까지 · 79,435km 남음** |
| `warranty.power` 동력계 | 32 | ★ **엔진 및 동력전달 부품** | 〃 |
| `warranty.site` 사이트 검증 | 36 | ★ **정밀점검 287개 항목 · 성능점검기록부 발행완료 · 책임환불 3일 · 커넥티드 1년** | ★ **제조사 인증 = 만점** |
| `taste.option` 옵션 | 43 | ★ **이름으로** | 내비게이션 · 하이패스 · 열선/통풍/전동시트 · 가죽시트 · 전동트렁크 |
| `taste.sunroof` 선루프 | 12 | 〃 | **선루프** |
| `taste.hud` HUD | 18 | 〃 | **헤드업 디스플레이** |
| 월납 | — | 할부 | 월 63만 (선수금 30% · 금리 2.5% · 60개월) |

```
★★ 「잔여 보증」이 ★ 년·월·km 로 ★ 남은 양을 그대로 준다 — ★ 우리가 계산할 필요가 없다
   ★ 엔카는 날짜를 주고 우리가 잰다.  ★ KB 는 「보증종료」 판정만 준다.  ★ 현대가 가장 낫다
★ 옵션이 ★ 이름으로 온다 (엔카 숫자 코드 문제 없음)
★ 「정밀점검 287개 항목」 — ★ 사이트 검증 최고 단계의 근거다
★ 「내차피해이력 1건」 · 「소유자 변경 있음」 — ★ 우리 이력 축과 바로 맞는다
★ 할인 표시가 있다 — 5,590만 → 5,090만.  ★ 표시가는 ★ 할인 뒤 값을 쓴다
```

## 못 채우는 축

```
✘ `value.origin` 신차가 — ★ 화면에 없다.  ★ 차종·트림 표에서 보충한다 (f-table 「사이트별 채우기」 ③)
✘ `value.market` 시세 — 우리 산출로 채운다 (④)
✘ `state.frame` 골격 · `state.outer` 외판 — ★ 「성능점검기록부」 안에 있을 것이다.  ★ 아직 안 열었다
✘ `state.consumable` 소모품 — 엔카·KB 도 안 준다
✘ `history.not_join` 자차 미가입 · `history.use` 용도 — ★ 「통합이력 조회하기」 안일 수 있다
```

---

# 3. 우리 규격에서의 값

```
★ 제조사가 직접 검사·보증한다 → ★ 사이트 검증 36점 ★ 최고 단계에 이미 넣었다 (f-table)
★ 제네시스도 같은 사이트다 — 마스터 후보(G80·G70·GV60·GV70·G80_EV)와 겹친다
   ★ 다만 실측에서 ★ G80(`RG31`) 이 ★ 0대다.  ★ 지금은 재고가 없다
★ 그랜저는 ★ 334대(IG 189 + GN7 145) 있다 — ★ 마스터 등록 차종 GRANDEUR_LPG 와 겹친다
★ ★ Hi-LAB 리포터 — 「오늘의 시세보다 저렴한 차량을 추천」.  ★ 사이트가 시세 판정을 준다
```

---

# 5. ★★ 목록 — 뚫렸다

```
POST https://certified.hyundai.com/m/search/results/selling      ★ 판매중
POST https://certified.hyundai.com/m/search/results/coming       입고예정
GET  https://certified.hyundai.com/api/search/vehicle/count/selling?{조건}   ★ 건수만

헤더  모바일 UA · Content-Type: application/json ·
      Referer: …/m/search/vehicle?srchType=srchFilter · X-Requested-With: XMLHttpRequest
★ 응답은 ★ HTML 조각이다 (JSON 아님).  ★ 매물번호는 `data-id` 에 있다
```

## 요청 본문 (브라우저가 보내는 것 그대로)

```json
{"type":null,"sortType":"popularity","srchType":"srchFilter","recentYn":"N",
 "tmnlId":"","mbrNo":null,"siteNo":null,"saleCorpCd":null,
 "rowsPerPage":100,"pageIdx":1,
 "startNo":null,"listCnt":null,"searchWord":null,
 "lowPrice":null,"highPrice":null,"lowMileage":null,"highMileage":null,
 "lowModelYear":2017,"highModelYear":null,"sdStatCd":null}
```

```
★ `tmnlId` 는 ★ 빈 문자열이어도 된다 — ★ 토큰이 필요 없다 (실측)
★ `rowsPerPage` 를 ★ 100 으로 키우면 ★ 한 번에 100건 온다 (기본 20)
★ `pageIdx` 로 쪽을 넘긴다 — 1·2·3·4 에서 각각 20건, 누적 80건 확인
★ `sortType` — popularity · 최근 연식순 · 낮은 가격순 · 높은 가격순 · 할인금액 높은순 ·
              최근 등록순 · 짧은 주행거리순
★ 조건 — lowPrice/highPrice · lowMileage/highMileage · lowModelYear/highModelYear · searchWord
```

## 매물번호 뽑기

```
★ data-favContsNo="GJJ260317025652"   ← ★ 이것이 매물번호다 (개정 485 정정)
★ ~~data-id~~ 는 ★ 없다 — 개정 480 이 잘못 적었다
꼴  영문 3 + 숫자 12
정규식  data-favContsNo="([A-Z]{3}\d{12})"
→ ★ 그대로 `goodsDetail.do?goodsNo={번호}` 에 넣으면 상세가 200 이다
```

## 목록 한 카드에 보이는 것 (실측)

```
2019 그랜저(IG) 가솔린 2.4 프리미엄 · 19년 02월 · 62,776km · 294저1103 · 군산
1,710만 (1,850만에서 ★ 140만 할인) · 할부 월 21만 · 찜 157
★ 차종·트림·연식·주행·지역·가격·할인·월납이 ★ 목록에서 다 온다
```

## 건수

```
GET /api/search/vehicle/count/selling?srchType=srchFilter&mdlGrpList=1171
  → {"code":"0000","body":166,"totalCount":0}      ★ body 가 건수다
★ 조건 없이 부르면 전체 건수가 나온다 — ★ 끝 쪽까지 받는 기준으로 쓴다
```

---

# 6. ★ 판정 — 붙일 수 있다

```
★ 목록  POST /m/search/results/selling  (토큰 없음 · 100건/쪽 · 쪽넘김)
★ 상세  GET  /m/goods/goodsDetail.do?goodsNo={data-id}  (인증 없음 · 204KB)
★ 둘 다 ★ 서버에서 브라우저 없이 200 이다
★ robots 는 ★ 금지 경로가 하나도 없다
★★ 엔카와 달리 ★ 목록도 열린다.  ★ KB·기아 CPO 와 같은 급으로 붙일 수 있다
★ 잔여 보증을 ★ 년·월·km 로 주는 것은 ★ 네 사이트 중 현대뿐이다
```
