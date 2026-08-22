# K카 목록 API · 매핑 규격

`SPEC-2026.08.22-r467` · 2026-08-22 · **가이드가 직접 실측했다 (원칙 4)**
`docs/KCAR_API.md`(개발측 08-17 1차 조사)를 잇는다 — **1차가 못 찾은 XHR 을 찾았다**

---

# 0. 결론

```
★★ 목록은 ★ 완전히 뚫렸다 — ★ 응답이 평문 JSON 이고 항목이 매우 풍부하다
★ 요청 본문만 암호화되어 있다 ({"enc":"…"})  ★ 응답은 암호화가 아니다
★ 상세(`/bc/detail/carInfoDtl?`)는 ★ robots 금지다.  ★ 목록은 허용이다
```

---

# 1. 경로

| 무엇 | 방식 | 경로 | robots |
|---|---|---|:--:|
| **목록(직영)** | `POST` | `https://mapi.kcar.com/bc/search/list/drct` | ★ 허용 |
| **목록(제휴·인증)** | `POST` | `https://mapi.kcar.com/bc/search/list/acm` | ★ 허용 |
| 관심여부 | `POST` | `/bc/wish-yn-list` — body 에 `carList:["EC61366001",…]` | 허용 |
| 지역·센터 | `GET` | `/bc/region-center` | 허용 |
| 코드표 | `GET` | `/bc/sub-codelist?sMstCode=CAR_OPTION2%2CCENTER_REGION%2CSELL_CL_CD` | 허용 |
| ~~상세~~ | ~~GET~~ | ~~`/bc/detail/carInfoDtl?i_sCarCd=…`~~ | ★ **금지** |

```
★ 호스트는 ★ mapi.kcar.com 이다.  ★ api.kcar.com 도 www 도 아니다
★ 개발측 1차 조사(`docs/KCAR_API.md`)가 「값이 HTML 에 없다 · XHR 을 더 찾아야 한다」로 끝난 그 XHR 이다
```

## 1-1. ★ 요청 본문이 암호화되어 있다

```json
POST https://mapi.kcar.com/bc/search/list/drct
{"enc":"Nowc5u4sSePQWry7DUNHGk0AC0Hw+juIruZbsqp91H+mq/iQqHxlAvlmIRGNOvSCPoLNOz+R6OZhLIFVcIWge60g…"}
```

```
★ 조건(차종·가격·쪽)이 enc 한 덩어리에 들어 있다.  ★ 평문 파라미터가 없다
★★ 가이드는 ★ 이 암호를 풀지 않는다.  ★ 우회를 만들지 않는다
★ 대신 ★ 브라우저를 몰아 ★ 사이트가 스스로 보내게 하고 ★ 응답만 읽었다
   (마스터가 브라우저로 보시는 것과 같다.  ★ 조건은 화면에서 고른다)
```

---

# 2. ★ 응답 — 평문 JSON · 항목이 풍부하다

```json
{"data":{"totalCnt":798,"pageNo":1,"limit":10,"totalPageCnt":80,"rows":[ … ]}}
```

```
★ 총건수 · 쪽 수를 ★ 그대로 준다 (KB차차차는 안 준다)
★ 쪽당 10건 (KB 는 40건 · 엔카는 50건)
```

## 한 매물이 주는 것 — 실측 (표본 `EC61366001`)

| 우리 축 | 배점 | K카 필드 | 값 예시 |
|---|--:|---|---|
| — 매물번호 | — | (`wish-yn-list` 의 `carList`) | `EC61366001` |
| `taste.trim` 트림 | 59 | `grdNm` · `grdDtlNm` | `3.3 GDI AWD` · `프레스티지` |
| 차종 | — | `mnuftrNm` · `modelGrpNm` · `modelNm` | 제네시스 · G80 · G80 |
| `value.budget` 예산 | 95 | `prc` (만원) | `2070` |
| `state.year` 연식 | 80 | `mfgDt` · `prdcnYr` | `201801` · `2018` |
| `value.mileage` 주행 | 107 | `milg` | `70539` |
| 연료 | — | `fuelNm` · `engdispmnt` | 가솔린 · 3342 |
| `taste.color` 색상 | 15 | `extrColorNm` · `extrColorCd` | 쥐색 · COLOR0220 |
| `taste.option` 옵션 | 43 | ★ `optnNm` **이름으로** · `optnCd` | ABS\|내비게이션\|가죽시트\|HUD… |
| `state.accident` 사고 | 48 | `acdtHistCd` | `300` (코드 — 표 필요) |
| 변속 · 인승 · 차급 | — | `trnsmsnNm` · `pasngrCnt` · `carctgrNm` | 오토 · 5 · 대형차 |
| 판매점 | — | `cntrNm` · `cntrRgnNm` | 홈서비스 메가센터 |
| 딜러 | — | `selerNm` · `selerSafeTno` | 김병준 · 0504-… |
| 사진 | — | `lsizeImgPath` · `view3dFg` | ★ **3D** 지원 |
| 딜러 설명 | — | `simcDesc` | `개인명의★LED라이트★HUD★어뷰…` |
| 특징 태그 | — | `hotmarkNm` | `특옵션;4WD;주행보조` |
| 할부 | — | `instAmt` | 34 (만원/월) |
| 판매 구분 | — | `sellDcd` · `regType` · `csgmtYn` | GNRL · SELL |

```
★★ 옵션이 ★ 이름으로 온다 (`optnNm`) — ★ 엔카 숫자 코드 문제(밀린일 #6)가 여기도 없다
★ 사고이력이 `acdtHistCd` 코드로 온다 — ★ 코드표를 `/bc/sub-codelist` 에서 받아야 한다
★ 신차가는 ★ 없다.  `value.origin` 75점을 목록만으로는 못 매긴다
```

---

# 3. ★ 목록만으로 채울 수 있는 축

```
채워진다  트림 59 · 연식 80 · 주행 107 · 예산 95 · 색상 15 · 옵션 43 · HUD 18 ·
          지정옵션 18 · 선루프 12 · 사고(코드 해석 뒤) 48        ★ 합 495 / 910
못 채운다 신차가 75 · 시세 30 · 골격 40 · 외판 26 · 자차수리비 26 · 특수사고 20 ·
          소모품 14 · 누유 14 · 진정성 7 · 압류저당 7 · 용도 21 · 자차미가입 17 ·
          소유자변경 10 · 보증 90                              ★ 합 397 / 910
★ 즉 ★ 목록만 쓰면 ★ 절반이 0점이다 — ★ 등급이 낮게 깔린다
★ 개정 289·434 대로 0점 + 분모 910 유지.  ★ 조용히 빼지 않는다
★★ 그러므로 ★ 목록만으로 K카를 엔카·KB 와 ★ 같은 표에서 줄 세우면 ★ K카가 통째로 불리하다
   → ★ 화면에 「K카는 상세를 못 받아 절반이 0점」이라고 ★ 밝혀야 한다 (V11-165)
```

---

# 4. ★ 상세 — 하지 않는다

```
robots.txt   ★ Disallow: /bc/detail/carInfoDtl?
             ★ Disallow: /br/detail/brandCarInfoDtl?
요청         목록조차 본문을 암호화해 두었다
★★ 두 겹으로 「기계로 부르지 말라」는 표시다.  ★ 우회를 만들지 않는다
★ 마스터가 ★ 브라우저로 직접 보시는 것은 아무 문제가 없다 —
  ★ 최종 확인은 사이트에서 한다 (개정 427 · V11-63).  ★ 우리 규격이 원래 그렇다
★ 정식으로 풀려면 ★ K카에 제휴·데이터 이용 문의를 넣는다.  ★ 마스터 판단이다
```

---

# 5. 아직 모르는 것

```
· `acdtHistCd` 300 이 무슨 뜻인가 — ★ `/bc/sub-codelist` 코드표를 받아 푼다
· `sellDcd` GNRL · `csgmtYn` B · `reqStsCd` 30 — 같은 코드표
· 조건 검색 — enc 를 안 푸는 이상 ★ 차종별로 못 부른다
  → ★ 브라우저에서 차종을 고른 뒤 응답을 읽는 방식이라 ★ 사람이 한 번 눌러야 한다
· 총 798건은 ★ 그때 화면 조건(직영·기본)의 수다.  ★ 전체 수가 아니다
```
