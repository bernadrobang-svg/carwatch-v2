# 현대·제네시스 인증중고차 API — 조사 (★ 미완)

`SPEC-2026.08.22-r478` · 2026-08-22 · **가이드가 직접 실측했다 (원칙 4)**

```
★★ 이 문서는 ★ 미완이다.  ★ 매물 목록 API 를 ★ 아직 못 찾았다
★ 개발측에 ★ 아직 넘기지 않는다 — ★ 지어내게 되기 때문이다 (원칙 1-c)
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

# 3. 우리 규격에서의 값

```
★ 제조사가 직접 검사·보증한다 → ★ 사이트 검증 36점 ★ 최고 단계에 이미 넣었다 (f-table)
★ 제네시스도 같은 사이트다 — 마스터 후보(G80·G70·GV60·GV70·G80_EV)와 겹친다
   ★ 다만 실측에서 ★ G80(`RG31`) 이 ★ 0대다.  ★ 지금은 재고가 없다
★ 그랜저는 ★ 334대(IG 189 + GN7 145) 있다 — ★ 마스터 등록 차종 GRANDEUR_LPG 와 겹친다
★ ★ Hi-LAB 리포터 — 「오늘의 시세보다 저렴한 차량을 추천」.  ★ 사이트가 시세 판정을 준다
```

---

# 4. 다음 (가이드 몫)

```
① ★ 매물 카드를 ★ 직접 눌러 상세로 들어가 본다 — 주소 꼴을 알면 목록도 짚을 수 있다
② ★ 로그인이 필요한지 확인한다 (기아 CPO 도 `/api/isToken/` 을 부른다)
③ ★ 안 되면 ★ 마스터께 청한다 — ★ 앱에서 매물 하나를 열어 주소를 알려 주시는 것
★ 그 전에는 ★ 개발측에 넘기지 않는다
```
