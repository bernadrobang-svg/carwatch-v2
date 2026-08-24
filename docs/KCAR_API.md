# K카 API — 목록 · 상세 정본

```
version  SPEC-2026.08.24-r670
follows  `f-table.md` · `MULTISITE_MAPPING.md`
sources  개정 626 · 실측 08-24
checks   S46-5 · S46-31
```
★ 이 문서는 ★ **그 사이트가 무엇을 주는가**만 적는다.  ★ 판정은 ★ `f-table` 이 한다 (가이드역할 ㉺)


`SPEC-2026.08.22-r485` · 2026-08-22 · **가이드가 직접 실측했다 (원칙 4)**
**★ 개정 485 — 마스터 확정 「상세를 받는다」. 개정 467·468(목록만)을 갈아엎는다**
**★ 옛 `docs/KCAR_LIST_API.md` 는 이 파일에 합치고 지웠다 (원칙 1 — 고쳐라, 덧붙이지 마라)**

---

---

# 0a. ★★★ 목록이 뚫렸다 — ★ 마스터가 직접 두드려 찾으셨다 (개정 626 · 08-24)

```
★★★ ★ 이 문서가 ★ 「목록은 ★ enc 라 못 부른다」로 적어 둔 것이 ★ **틀렸다**
★ ★ 그것은 ★ `www.kcar.com` 의 ★ 한 경로(`/bc/search/list/drct`)일 뿐이었다
★ ★ 다른 호스트에 ★ 평문 JSON 목록이 ★ 열려 있었다
```

## ★ 부르는 법

```
GET  https://mapi.kcar.com/bc/stockCar/list?pageSize=527
     → 200 · ★ 961,752B · ★ 평문 JSON · ★ enc 없음 · ★ 헤더·토큰 불필요 · 1초
     → `data.listCount` = ★ 527   ★ 이것이 총건수다
     → ★ `carCd` ★ 527개 · ★ 중복 0
★ robots 허용 · sitemap 등재 — ★ 우회가 아니다 (마스터 확인)
```

| 먹는 것 | 안 먹는 것 |
|---|---|
| ★ `pageSize` (15 → 100 → **527**) | `page` · `pageNum` · `pageIndex` · `rowsPerPage` · `listCnt` |
| ★ 527 이상은 ★ 527 에서 멈춘다 | ★ `mnuftrCd` · `modelGrpCd` — ★ **차종 좁히기가 안 된다** |

```
필수  ★ 527건을 ★ 다 받아 ★ 우리 쪽에서 거른다.  ★ 527이면 부담이 없다
필수  ★ `listCount` 를 ★ 총건수로 읽는다 — ★ 쪽마다 더하지 마라
```

## ★★ 한 매물에 ★ 94칸이 온다 — ★ 상세를 덜 불러도 된다

```
carCd · mnuftrNm · modelNm · grdNm · grdDtlNm · prc · dcPrc · milg · prdcnYr · mfgDt ·
fuelNm · trnsmsnNm · extrColorNm · colorNm · engdispmnt · ★ acdtHistCnts(사고 이력 수) ·
cno(차량번호) · cntrNm · cntrAddr · gmCertYn · sellDcd · statCd · carRegDttm · trffPrice · mgtCost …
★ ★ 목록만으로 ★ 차종·값·주행·연식·색상·연료·변속기·차량번호가 ★ 다 채워진다
```

## ★★ 527건 중 ★ 우리 대상 (08-24 실측 · 이름 기준)

| 이름이 맞는 것 | 건수 |
|---|--:|
| 그랜저 | ★ **47** |
| G80 | ★ **18** |
| G70 | ★ **17** |
| 스포티지 | ★ **13** |
| GV70 | ★ **8** |
| GLC · X3 | 2 · 2 |
| XC60 | 1 |
| ★ **합 (이름 기준)** | ★ **108** |

```
★★ ★ 「이름이 맞는 것」이지 ★ 「우리 갈래가 맞는 것」이 아니다
   ★ 그랜저 47건 중 ★ LPG 가 몇인지 · 스포티지 13건 중 LPi 가 몇인지는 ★ 연료로 걸러야 한다
   ★ ★ 현대·기아와 같은 자리다 (명령서 14-2)
★ 제조사 분포 — 현대 199 · 기아 156 · 제네시스 65 · BMW 24 · 벤츠 18 · 아우디 14 · 볼보 …
★ 이 숫자는 ★ 날마다 바뀐다 — ★ 잰 날을 함께 적는다 (08-24)
```

---

# 0. 결론

```
★ 목록  POST mapi.kcar.com/bc/search/list/drct  — 요청만 암호화 · 응답 평문 JSON
★ 상세  GET  mapi.kcar.com/bc/car-info-detail-of-ng?i_sCarCd=  — ★ 평문 JSON · 1,050 필드
★ 화면 경로(`/bc/detail/carInfoDtl?`)는 ★ robots 금지다.  ★ 그 주소는 두드리지 않는다
★ 값은 ★ 화면이 아니라 ★ mapi 가 준다.  ★ mapi 에는 robots 문서가 없다 (404)
```

---

# 1. robots — 실측 2026-08-22

| 호스트 | robots | 우리 경로 |
|---|---|---|
| `m.kcar.com` · `www.kcar.com` | 200 · 442B | ★ `Disallow: /bc/detail/carInfoDtl?` — **막혀 있다** |
| **`mapi.kcar.com`** | ★ **404 — 문서가 없다** | ★ 규칙이 없다 |

```
필수  ★ 화면 경로 `/bc/detail/carInfoDtl?` · `/br/detail/BrandCarInfoDtl?` · `/ur/RentDtl?`
      ★ 이 셋은 ★ 어떤 경우에도 두드리지 않는다
필수  ★ 값은 `mapi.kcar.com` 에서만 받는다
금지  ★ 목록 요청의 `enc` 를 푸는 것.  ★ 우회를 만드는 것
근거  ★ sitemap.xml 22개 주소에 매물 상세가 한 건도 없다 — 화면을 색인시키지 않겠다는 뜻이다
      ★ 그러나 막은 것은 2.2MB 짜리 껍데기 HTML 이고 `carInfo` 는 `null` 이다.  ★ 값이 없다
마스터 확정 08-22 — 「받는다」
```

---

# 2. 경로

| 무엇 | 방식 | 경로 | 비고 |
|---|---|---|---|
| **목록(직영)** | `POST` | `https://mapi.kcar.com/bc/search/list/drct` | 본문 `{"enc":"…"}` · ★ 브라우저가 보내게 한다 |
| **목록(제휴·인증)** | `POST` | `/bc/search/list/acm` | ★ 직영이 아니다 |
| ★ **상세** | `GET` | `/bc/car-info-detail-of-ng?i_sCarCd={carCd}` | ★ **80KB · 51블록 · 헤더 불필요** |
| 성능점검 사진 | `GET` | `/bc/car-insp/photo/cm?i_sCarCd=` | ★ **jpg 경로만** — 값 아님 |
| 3D 사진 | `GET` | `/bc/car-elan-path?i_sCarCd=` | |
| 코드표 | `GET` | `/bc/sub-codelist?sMstCode=CAR_OPTION2%2CCENTER_REGION%2CSELL_CL_CD` | |

## 2-1. ★ 없는 매물도 200 을 준다

```
실측  EC99999999 → 200 · 3,186B · `data.rvo` 없음
필수  ★ `data.rvo.carCd` 가 있는지로 가른다.  ★ 상태코드로 가르지 마라
필수  ★ 본문 10,000B 미만은 ★ 「없음」이 아니라 ★ 「못 받음」으로 남기고 재시도한다
      (KB차차차 봇페이지 2,759B 와 같은 함정이다 — 오판대장 #43)
```

---

# 3. 상세가 주는 것 — 실측 (표본 12건 · `EC61377663` 외)

## 3-1. 매물 · 차종 — `data.rvo`

| 뜻 | 필드 | 값 예시 |
|---|---|---|
| 매물번호 | `carCd` · `carId` | `EC61377663` |
| ★ **차대번호** | ★ `vin` | `KMTGA41CBSU251014` |
| ★ **차량번호** | ★ `cno` | `211러2161` |
| 제조사·모델 | `mnuftrNm` · `modelNm` · `modelGrpCd` | 제네시스 · G80 (RG3 F/L) |
| 트림 | `grdNm` · `grdDtlNm` · `grdFullNm` | 가솔린 터보 2.5 / 스포츠 패키지 2WD |
| 판매가(만원) | `salprc` | 5170 |
| 판매가(원) | `npriceFullType` | 51700000 |
| 연식·최초등록 | `mfgDt` · `regModelyr` · `fstCarRegYm` | 202406 · 2025 |
| 주행 | `milg` | 14187 |
| 연료·배기·마력·구동 | `fuelTypecdNm` · `engdispmnt` · `hrspow` · `drvgYnNm` | 가솔린 · 2497 · 304 · 후륜 |
| 색상 | `extrColorNm` · `extrColorCd` | 검정색 · COLOR0040 |
| 판매유형 | `sellDcd`(목록) · `csgmtYn` · `cntrNm` | 직영 · N · 홈서비스 메가센터 |
| ★ **제조사 보증 잔여** | ★ `nwcaGurnteEngeSurvDt` · `nwcaGurnteGnrlSurvDt` · `…Milg` | **2029-06-16 · 10만km** |
| 진단 | `dgnosDt` · `master.efctDt` · `jindanCenterName` | 20260624 · 2028-06-16 · 이천지점 |

```
★★ `npriceFullType` 은 ★ 신차가가 ★ 아니다 — ★ 판매가(원)다.  `salprc` × 10,000 이다
   ★ 실측으로 확인했다 (5170만 → 51700000 · 2070만 → 20700000).  ★ 여기 걸리지 마라
★ 신차가는 ★ K카 어디에도 없다 — ★ f-table 갈래 ③ 으로 채운다 (차종·트림 속성)
★ `carJatoOptList.vehicleId` 가 JATO 카탈로그 연번이다 — ★ 신차가 매칭 열쇠 후보.  ★ 미검증
```

## 3-2. ★ 사고 — `acdtHistComnt` 를 쓴다

**표본 12건 실측 대조**

| `acdtHistComnt` | `smplReprYn` | 건수 | 뜻 |
|---|:--:|--:|---|
| **무사고** | 1 | 4 | 골격·외판 교환 없음 |
| **단순수리** | 2 | 7 | 판금·도장 수준 |
| **사고** | 2 | 1 | 교환 있음 |

```
필수  ★ 판정은 `acdtHistComnt`(평문 한글)로 한다
금지  ★ `smplReprYn` 으로 가르는 것 — ★ 단순수리와 사고가 ★ 둘 다 2 다 (실측)
금지  ★ `acdtHistYn` 으로 가르는 것 — ★ 표본 12건 전부 1 이다.  변별력이 없다
필수  ★ 셋을 `dict_enum(site='kcar', axis='accident')` 에 넣고 ★ 새 값이 오면 멈추고 묻는다
```

| 뜻 | 필드 | 값 예시 |
|---|---|---|
| 내차 피해 건수·금액 | `carhistory.owncarDmgeAcdtCnt` · `owncarDmgeInsrAmtSum` | 1건 · 850,010원 |
| ★ **수리비 분해** | ★ `carHistoryAccList[].reprEstmCost·cmpntCost·lbrCost·pntCost` | 85만 = 부품8.2 + 공임24.0 + 도장52.6 |
| 상대차 피해 | `othrcarWrdgAcdtCnt` · `othrcarWrdgInsrAmtSum` | 0 |
| **전손·침수·도난** | `gnrlTtlsAcdtCnt` · `fldgAcdtCnt` · `rbrTtlsAcdtCnt` · `master.speclAcdtHistDcd` | 0·0·0·0 |
| 구조변경 | `master.fmltStruChngYn` · `ilgltStruChngYn` | N · N |
| ★ **압류·저당** | ★ `master.szrMogeYn` | N |
| 계기판 교체 · 리콜 | `master.dshbExchgYn` · `recallObjYn` · `carRecallNeedCnt` | 1 · 1 · 0 |

## 3-3. ★ 이력 — `carhistory` · `carOwnrChngHistList`

| 뜻 | 필드 | 값 예시 |
|---|---|---|
| 조회 성공 여부 | `carhistory.rsltCd` · `iqyDt` | `000` · 20260814 |
| ★ **렌트 이력** | ★ `rentHistYn` | ★ **Y 인 직영 매물이 실재한다 (12건 중 5건)** |
| 영업용·관용 | `bizuseHistYn` · `instnHistYn` | N · N |
| 소유자 변경 | `ownrChngCnt` · `useChngCnt` | 1 (최대 6 관측) |
| 소유자 이력 | `carOwnrChngHistList[]` — `title` · `regDt` · `addr` · `corpType` · `age` | 신규등록(신조차) 평택 → 명의이전 매매업자 |

```
★★ 개정 468 의 「직영은 렌트·영업용을 직영으로 팔지 않는다」는 ★ 틀렸다 (오판대장 #45)
★ 실측 12건 중 5건이 `rentHistYn=Y` 다.  ★ 믿음으로 21점을 주고 있었다
```

## 3-4. ★ 소모품 — `tireDtlList` (엔카·KB 에 없는 값)

| 뜻 | 필드 | 값 예시 |
|---|---|---|
| 타이어 4짝 잔량(mm) | `tirResQty` | 5.6 / 5.5 / 6.2 / 6.2 |
| 규격 | `tirSidWidth` · `tirFlatRt` · `tirInch` | 245/40R20 · 275/35R20 |
| 생산 연·주차 | `tirPrdcnYr` · `tirPrdcnWkcnt` | 24년 4~9주 |

## 3-5. 옵션 — `optList` · `mainOptList`

```
★ 이름으로 온다 (`optnNm`) — 45개.  ★ 엔카 숫자 코드 문제가 없다
   LED 헤드라이트 · 헤드업 디스플레이(HUD) · 360도 어라운드 뷰 · 통풍시트 · 스마트 크루즈컨트롤 …
필수  ★ `dict_enum(site='kcar', axis='option')` 에 ★ 이름을 코드로 넣는다 (MULTISITE_MAPPING 4장)
★ `carJatoOptList` 는 ★ 패키지 옵션이다 — `optNm`「파퓰러 패키지」· `optPrc` 370만
```

## 3-6. ★ 성능점검 — 사진뿐이다

```
`/bc/car-insp/photo/cm` → {"inspDetail":{"cno","acdtHistYn","smplReprYn","imgList":[jpg…]}}
★★ 부위별 등급(교환·판금)이 ★ JSON 에 없다.  ★ 성능점검기록부 ★ 사진만 준다
★ 마스터 확정 08-22 — 「★ 나중.  상세부터 붙이고 본다」  → ★ OCR 은 이번 회차에 하지 않는다
```

---

# 4. ★★ 축 채우기 — 배점은 `f-table.md` 5장-2a 를 그대로 쓴다

**★ 여기에 숫자를 옮겨 적지 않는다 (원칙 1-a). 갈래만 정한다.**

| 축 | 갈래 | 무엇으로 |
|---|:--:|---|
| 트림 · 연식 · 주행 · 예산 · 색상 · 옵션 · HUD · 지정옵션 · 선루프 | ① | 목록 · 상세 원문 |
| ★ 특수사고 · 압류저당 · 용도 · 소유자 · 자차미가입 · 자차수리비 · 진정성 | ★ ① | ★ **상세 원문 (개정 468 의 「믿음」을 갈아엎는다)** |
| ★ 소모품 | ★ ① | ★ `tireDtlList` 잔량 |
| ★ 제조사 보증 (동력·일반) | ★ ① | ★ `nwcaGurnte*SurvDt` · `…Milg` — ★ 계산하지 않는다 |
| 사이트 검증 | ② | ★ **직영(`sellDcd` GNRL)만** — 제휴·인증(`/acm`)에는 안 준다 |
| ★ 골격 · 외판 · 누유 | ★ ②/미확인 | ★ **4-1 표대로** (성능점검이 사진이라 OCR 전이다) |
| 신차가 | ③ | 차종·트림 표에서 (제조사·모델·트림·연식 매칭) |
| 시세 | ④ | 우리 산출 |

## 4-1. ★ 골격 · 외판 · 누유 — OCR 전 잠정 규칙

| `acdtHistComnt` | 골격 | 외판 | 누유 | 화면 표기 |
|---|---|---|---|---|
| **무사고** | ② 보장 | ② 보장 | ② 보장 | 「K카 직영 무사고 판정으로 채움 (성능점검 사진 미판독)」 |
| **단순수리** | ② 보장 | ★ **0점 + 미확인** | ② 보장 | 「단순수리 — 외판은 사진 미판독」 |
| **사고** | ★ **0점 + 미확인** | ★ **0점 + 미확인** | ② 보장 | 「사고 — 골격·외판은 사진 미판독」 |

```
금지  ★ 사진을 안 읽고 ★ 골격 판금 감점을 주는 것.  ★ 지어내지 않는다
금지  ★ 사고차에 ★ 조용히 만점을 주는 것 (개정 325 · V11-165)
필수  ★ 자차수리비는 ★ 실측(`owncarDmgeInsrAmtSum`)으로 채운다 — 무사고여도 금액이 있으면 반영한다
      ★ 표본 `EC61377663` 이 그 경우다 — 「무사고」인데 내차 피해 85만
필수  ★ 렌트·영업용 감점은 ★ 실측(`rentHistYn`·`bizuseHistYn`)이므로 ★ 그대로 적용한다
```

---

# 5. 저장

```
site           'kcar'
source_id      carCd (`EC61377663`)  ★ 문자 포함 — 정수로 넣지 마라 (50-multisite 350행)
원문 보관       ★ 목록 응답 · ★ 상세 응답 ★ 둘 다 통째로 남긴다
중복 제거       ★ vin · cno 로 엔카·KB·기아 CPO 와 맞춘다 (STEP 123)
필수           ★ 상세 응답에 `data.rvo` 가 없으면 ★ 「못 받음」이다.  ★ 「없음」으로 저장하지 마라
```

```
★ 칼럼 단위 매핑은 ★ `docs/MULTISITE_MAPPING.md` 가 정본이다 — ★ `core_listing` 칼럼으로 적혀 있다
★★ ★ `Yn` 필드는 ★ 전부 문자열이다.  ★ `bool('N')` 은 ★ 참이다 — ★ `bool()` 로 가르지 마라
★ ★ 응답이 `{"data":{…}}` 로 싸여 있다.  ★ `data` 를 벗기지 않으면 ★ 전건 NULL 이다 (오판 #52)
```

---

# ★★★ 모바일 화면 — ★ 마스터가 주소를 주셨다 (개정 625 · 08-24)

```
★★ 마스터 08-24 — ★ `m.kcar.com` 주소 다섯을 주셨다
★ ★ 가이드가 재 봤다 — ★ 얻은 것과 ★ 못 얻은 것이 갈린다
```

## ① ★ 얻은 것 — ★ 차종을 좁히는 조건 (★ 이것이 크다)

```
목록  https://m.kcar.com/bc/search/CarList?searchCond={JSON}
      ★ GET 이다.  ★ 쿼리에 JSON 을 실어 보낸다 — ★ enc 가 아니다
```

| 칸 | 뜻 | 실측 값 |
|---|---|---|
| `wr_eq_sell_dcd` | 판매 갈래 | `ALL` |
| `wr_in_multi_columns` | 지역 칸 | `cntr_rgn_cd\|cntr_cd` |
| ★ **`wr_in_multi_mnuftr_modelGrp`** | ★ **제조사·차종 코드** | ★ BMW X3 = `012,007` · 제네시스 G90 = `007,004` |
| ★ **`noquery_modelGrp`** | ★ **차종 이름** | `BMW X3` · `제네시스 G90` |
| ★ **`carType_modelGrp`** | ★ **국산/수입** | ★ `KOR` · `IMP` |

```
★★ ★ 이 조건 꼴을 ★ 몰랐다.  ★ 규격에 없던 것이다
필수  ★ 우리 대상 열 종의 ★ `wr_in_multi_mnuftr_modelGrp` 코드를 ★ 모아야 한다
      ★ 마스터께서 ★ 차종마다 한 번씩 눌러 ★ 주소를 주시면 ★ 코드가 다 나온다
```

## ② ★ 마스터가 주신 매물 번호 셋

```
EC61398174 · EC61385373 · EC61391672
상세  https://m.kcar.com/bc/detail/carInfoDtl?i_sCarCd={번호}
```

## ③ ★★ 못 얻은 것 — ★ 서버에서 부르면 ★ 껍데기다

```
목록 → 200 · ★ 2,170,685B · ★ 매물번호 ★ 0개
상세 → 200 · ★ 2,204,789B · ★ 매물번호 ★ 0개
★ ★ `__NUXT__` 안에 ★ 데이터가 없다 — ★ 화면 뼈대와 사전만 있다
★ ★ 브라우저가 ★ 그 뒤에 ★ XHR 로 데이터를 부른다
★★ ★ 그러므로 ★ 모바일 주소로도 ★ 서버에서는 목록을 못 받는다
   ★★ ★ **08-24 정정 — 그 말은 ★ 틀렸다.  ★ 0a장을 보라**
   ★ ★ `m.kcar.com` 화면은 껍데기가 맞으나 ★ `mapi.kcar.com` 에 ★ 평문 목록이 있다
```

```
★★★ ★ **08-24 — ★ 이 절은 ★ 끝났다.  ★ 0a장이 답이다**
   ★ ★ `mapi.kcar.com/bc/stockCar/list?pageSize=527` 로 ★ **527건이 열린다**
   ★ ★ 「마스터가 `carCd` 를 주신다」는 ★ **폐기다** (요구 추적표 79번)
금지  ★ `enc` 를 푸는 것 · ★ 우회를 만드는 것 (그대로다)
```
