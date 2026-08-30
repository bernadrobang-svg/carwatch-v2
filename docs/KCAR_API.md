# K카 API — 목록 · 상세 정본

```
version  SPEC-2026.08.29-r958
follows  `f-table.md` · `MULTISITE_MAPPING.md`
sources  개정 862 · 실측 08-29
checks   S46-5 · S46-31
```
★ 이 문서는 ★ **그 사이트가 무엇을 주는가**만 적는다.  ★ 판정은 ★ `f-table` 이 한다 (가이드역할 ㉺)


`SPEC-2026.08.29-r958` · 2026-08-22 · **가이드가 직접 실측했다 (원칙 4)**
**★ 개정 485 — 마스터 확정 「상세를 받는다」. 개정 467·468(목록만)을 갈아엎는다**
**★ 옛 `docs/KCAR_LIST_API.md` 는 이 파일에 합치고 지웠다 (원칙 1 — 고쳐라, 덧붙이지 마라)**

---

---

# 0b. ★★★ 차종 계층 코드 — ★ 마스터가 주셨다 (개정 714 · 08-24)

```
★★ 마스터 주소 — `m.kcar.com/bc/search/CarList?searchCond={JSON}`
```

## ★★ 얻은 것 — ★ **다섯 층 코드다**

```
★ 이름 — ★ `wr_in_multi_mnuftr_modelGrp_model_grd_grdDtl`
   ★ ★ 이름 자체가 ★ **층을 말한다** — ★ 제조사 · 차종군 · 모델 · 등급 · 세부등급
★ 값  — ★ 쉼표로 층 · ★ **`|` 로 여럿**
```

| 차 | 코드 | `carType` |
|---|---|:--:|
| ★ 제네시스 G80 (RG3 F/L) 가솔린 터보 2.5 **2WD** | `007,002,015,001,001` | KOR |
| ★ 〃 **4WD** | `007,002,015,001,002` | KOR |
| ★ 볼보 V60 크로스컨트리 2세대 가솔린 4WD | `017,017,029,001` | ★ **IMP** |

```
★ ★ 볼보는 ★ **네 층**이다 (`_grd` 까지) — ★ 세부등급이 없으면 ★ 이름도 짧아진다
★ ★ 그러므로 ★ **이름이 층 수에 따라 바뀐다** —
   `wr_in_multi_mnuftr_modelGrp` (2층) · `…_model_grd` (4층) · `…_grd_grdDtl` (5층)
★ ★ 짝이 되는 이름도 함께 바뀐다 — ★ `noquery_grdDtl` · `carType_grdDtl` · `noquery_grd` · `carType_grd`
```

## ★★★ 못 얻은 것 — ★ **서버에서 부를 길이 없다**

| 두드린 것 | 결과 |
|---|---|
| `mapi/bc/stockCar/list` ＋ `searchCond` | ★ **526 그대로** — 무시 |
| 〃 ＋ 계층 이름 직접 | ★ 526 그대로 |
| `mapi/bc/search/CarList` · `/bc/car/list` · `/bc/stockCar/searchList` | ★ **404** |
| ★ `mapi/bc/search/list` **GET** | ★ **405** — ★ **있다.  ★ POST 를 기다린다** |
| ★ 〃 **POST** (JSON · form · 빈 몸 넷) | ★ **500** — ★ 규격의 ★ `enc` 경로다 |
| `m.kcar.com/bc/search/CarList` | 200 · 2.17MB · ★ **매물번호 0** (JS 렌더) |

```
★★★ ★ **`/bc/search/list` 이 ★ 그 API 다** — ★ 405 가 ★ 있다는 뜻이다
   ★ ★ 그러나 ★ **요청 본문이 ★ `enc` 로 암호화돼 있다** (규격 0장 그대로)
   ★ ★ 넷을 다 500 으로 되돌린다 — ★ 암호를 못 푸니 ★ 못 부른다
금지  ★ ★ **`enc` 를 푸는 것 · 우회를 만드는 것** (그대로다)
```

## ★ 그러므로 — ★ ~~전량 526건~~ ★ **이 창구가 주는 487건을 받아 거른다** [실측 08-29 · `stockCar/list?pageSize=1000` · `listCount` 487 · **전량이 아니다**(오판 180)]

```
★ ★ 다행히 ★ `mapi/bc/stockCar/list?pageSize=1000` 이 ★ **전량을 준다**
★ ★ 526건이면 ★ 1초다.  ★ 좁힐 까닭이 ★ 크지 않다
필수  ★ ★ **저장할 때 거른다** (`COLLECT_STRATEGY` 6장 ⓒ)
      ★ ★ 상세를 열어 ★ 차종이 안 맞으면 ★ `core_listing` 에 안 넣는다
★★ ★ **계층 코드는 ★ 버리지 않는다** — ★ 아래에 적어 둔다
   ★ ★ 개발측이 ★ XHR 를 찾거나 ★ `enc` 가 풀리면 ★ 그때 쓴다
   ★ ★ 그리고 ★ **차종을 알아보는 데** 쓸 수 있다 — ★ 상세의 `modelGrpCd` 와 맞대어 본다
```

---

# 0a. ★★★ 목록이 뚫렸다 — ★ 마스터가 직접 두드려 찾으셨다 (개정 626 · 08-24)

```
★★★ ★ 이 문서가 ★ 「목록은 ★ enc 라 못 부른다」로 적어 둔 것이 ★ **틀렸다**
★ ★ 그것은 ★ `www.kcar.com` 의 ★ 한 경로(`/bc/search/list/drct`)일 뿐이었다
★ ★ 다른 호스트에 ★ 평문 JSON 목록이 ★ 열려 있었다
```

## ★ 부르는 법

```
GET  https://mapi.kcar.com/bc/stockCar/list?pageSize=1000
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
필수  ★ 472건 (★ 실측 08-27 · ★ 매물은 날마다 바뀐다)을 ★ 다 받아 ★ 우리 쪽에서 거른다.  ★ 527이면 부담이 없다
필수  ★ `listCount` 를 ★ 총건수로 읽는다 — ★ 쪽마다 더하지 마라
```

## ★★ 한 매물에 ★ 94칸이 온다 — ★ 상세를 덜 불러도 된다

```
carCd · mnuftrNm · modelNm · grdNm · grdDtlNm · prc · dcPrc · milg · prdcnYr · mfgDt ·
fuelNm · trnsmsnNm · extrColorNm · colorNm · engdispmnt · ★ acdtHistCnts(사고 이력 수) ·
cno(차량번호) · cntrNm · cntrAddr · gmCertYn · sellDcd · statCd · carRegDttm · trffPrice · mgtCost …
★ ★ 목록만으로 ★ 차종·값·주행·연식·색상·연료·변속기·차량번호가 ★ 다 채워진다
```

## ★★ 08-29 재측 — ★ 전량 **487건** · 우리 대상 **105건** [실측 08-29 · 가이드]

```
`pageSize=1000` → `listCount` 487 · `list` 487건 · 889,533B
`pageSize=2000` → 487 그대로다.  ★ 487 이 전량이다
`pageSize=100`  → listCount 487 · 받은 100 — ★ `listCount` 는 총건수이고 `list` 는 그 쪽이다

★ 우리 대상 105건 (파서와 등록부를 그대로 돌려 세었다)
  그랜저 52 · G80 19 · 스포티지 12 · G70 12 · GV70 6
  그랑 콜레오스 HEV 1 · GLC 1 · X3 1 · ★ **XC60 1**
★★ ★ 마스터께서 보시는 볼보는 ★ K카에 ★ **XC60 한 대뿐**이다

★★★ 그런데 ★ 화면에 저장된 K카는 ★ **159건**이다 (배포 실측 08-29)
   ★ ★ 목록에 없는 것이 ★ **54건** 살아 있다 [추론 — DB 를 못 봤다]
   ★ ★ 까닭은 아래 「팔린 차」 절이다
```

## ★★★★ 팔린 차 — ★ K카는 ★ **매기는 길이 막혀 있다** [실측 코드 08-29]

```
`tools/collect_kcar.py:176`
  todo = [o for o in want if o["source_id"] not in done]
  done = detail_status='ok' 인 것

★ 그러니 ★ **이미 상세를 받은 매물은 ★ 다시 안 두드린다**
★ `mark_gone` 은 ★ 그 `todo` 를 돌다 ★ 상세가 「없는 매물」일 때만 부른다 (`:191`)
★ ★ 곧 ★ **한 번 저장된 매물은 ★ 영영 `gone` 이 안 된다**

★★ 그리고 ★ 마스터께서 ★ 오판 160 에서 못 박으셨다 —
   「★ **건별로 확인하지 말고 ★ 목록을 수집할 때 걸러야지**」
   ★ ★ K카는 ★ 아직 ★ **건별 404** 다.  ★ 그 건별조차 ★ 새 매물에만 돈다

★ 고칠 자리 — ★ 목록 487건의 `source_id` 집합을 만들어 ★ `sweep_gone_groups` 로 ★ 한 번에 매긴다
  ★ 보배(`collect_bobaedream.py:238`)·KB(`collect_kbchachacha.py:405`)가 ★ 이미 그 꼴이다

★★ 검사 `S46-117` 은 ★ 이것을 ★ **안 잡는다** — ★ 스스로 「부르는가만 본다」고 적어 두었다
   ★ ★ 「제대로 매겼는가」는 ★ 사람이 숫자로 본다 — ★ 08-29 에 세었다
```

---

## ★ 옛 표 — 527건 중 우리 대상 (08-24 실측 · 이름 기준 · ★ 위가 정본이다)

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
   ★ ★ `mapi.kcar.com/bc/stockCar/list?pageSize=1000` 로 ★ **527건이 열린다**
   ★ ★ 「마스터가 `carCd` 를 주신다」는 ★ **폐기다** (요구 추적표 79번)
금지  ★ `enc` 를 푸는 것 · ★ 우회를 만드는 것 (그대로다)
```

---

# ★ 0c. ★★ K카는 ★ **목록도 상세도 받는다** (개정 814 · `S44-5`)

```
★★ ★ **한 가지로 적는다** — ★ 「목록만」·「상세만」이 ★ 섞여 있었다
   ★ 목록 ★ `m.kcar.com/bc/search/CarList?searchCond={JSON}` (마스터 08-28)
   ★ 상세 ★ `m.kcar.com/bc/detail/carInfoDtl?i_sCarCd={carCd}` (마스터 08-28)
★ ★ 둘 다 ★ **받는다.**  ★ 어느 하나만 받는 것이 아니다
```

---

# ★★★ 2. 상세 — ★ **주소를 아직 못 찾았다** (실측 08-28 · 개정 790)

```
★★★ ★ **규격에 「상세를 받는다」를 ★ 열아홉 번 적어 놓고
   ★ ★ 「어떤 주소로」를 ★ 한 번도 안 적었다** — ★ 가이드 잘못이다 (오판 146)
   ★ ★ 그래서 ★ 개발측이 ★ **못 만든 것이 당연하다**
```

## ★ 알아낸 것 (실측)

```
매물번호 칸은 `carCd` 다.
```

## ★ 두드려 본 것 — ★ **열이 다 404**

| 주소 | |
|---|:--:|
| `mapi/bc/stockCar/detail?carCd=` · `/view` · `/info` · `/detailInfo` | ★ 404 |
| `mapi/bc/stockCar/{carCd}` · `mapi/bc/carDetail/info?carCd=` | ★ 404 |
| `www/bc/detail/carDetail?i_sCarCd=` · `/bc/carDetail?carCd=` | ★ 404 |
| `www/carDetail/{carCd}` · `www/bc/detail?carCd=` | ★ 404 |

```
★ ★ `www.kcar.com` 첫 화면은 ★ **200**(2.1MB)인데 ★ **상세 링크가 없다**
   ★ ★ 화면을 눌러야 ★ 주소가 생기는 꼴로 보인다 (SPA)
★★★ ★ **08-28 마스터께서 ★ 목록 주소를 주셨다** — ★ 아래 3장에 적었다
★ ★ 상세는 ★ **아직 못 찾았다** — ★ `m.kcar.com` 도 ★ 다섯이 다 404 다
★ ★ 목록 화면이 ★ **스크립트로 그려져** ★ 서버 HTML 에 ★ 상세 링크가 없다
```

## ★★ 마스터께 청하는 것

```
★ ★ **K카에서 차 하나를 눌러 ★ 주소창의 주소를 그대로 주십시오**
★ ★ **GLC 때 그렇게 한 방에 풀렸다** (개정 776 — `ModelGroup` 이 「GLC-클래스」였다)
★ ★ 그 한 줄이면 ★ 상세가 열리고 ★ **등급이 채워진다**
```

---

# ★★★ 3. 마스터께서 주신 목록 주소 (08-28 · 개정 791)

```
★★ ★ **`m.kcar.com`** 이다 — ★ 가이드가 ★ `www` 와 `mapi` 만 두드렸다 (오판 147)

GET https://m.kcar.com/bc/search/CarList?searchCond={JSON}
```

## ★ `searchCond` 안 (실측 · 마스터 주소를 푼 것)

| 열쇠 | 값 | 뜻 |
|---|---|---|
| `wr_in_multi_mnuftr_modelGrp` | `017,017｜017,016` | ★ **제조사,차종군** — 볼보 V60 · XC60 |
| `wr_in_multi_mnuftr_modelGrp_model` | `013,003,083` | 제조사,차종군,차종 — 벤츠 CLS C257 |
| `wr_in_multi_mnuftr_modelGrp_model_grd` | `091,001,001,001｜012,007,100,001｜007,006,017,001` | ★ **네 층** — 폴스타2 · BMW X3(G45) · GV70 |
| `noquery_modelGrp` | `볼보 V60｜볼보 XC60` | ★ **사람이 읽는 이름** |
| `carType_modelGrp` | `IMP｜IMP` | ★ 수입(IMP) · 국산(KOR) |
| `wr_eq_sell_dcd` | `ALL` | 판매 갈래 |

```
★★★ ★ **볼보 = `017`** · ★ XC60 = `017,016` · V60 = `017,017`
★ ★ BMW = `012` (X3 G45 = `012,007,100,001`) · ★ 제네시스 = `007` (GV70 = `007,006,017,001`)
★ ★ 폴스타 = `091`
★★ ★ **여러 차종을 ★ `|` 로 잇는다** — ★ 한 번에 다 받을 수 있다
★ ★ 층이 다르면 ★ **열쇠 이름이 다르다** (`_modelGrp` · `_model` · `_model_grd`)
```

```
필수  ★ ★ **이 주소로 ★ 우리 22종을 ★ 한 번에 받아라**
      ★ ★ `noquery_*` 는 ★ 화면 글자라 ★ **안 보내도 된다** (넣어도 해롭지 않다)
필수  ★ ★ `carType_*` 을 ★ 층마다 짝맞춰 보내라 (IMP · KOR)
★ ★ 그러면 ★ `stockCar/list?pageSize=1000`(전량 472) 보다 ★ **좁게 받는다**
```

## ★★★ 4. 상세 — ★ **`carInfoDtl` 이다** (마스터 08-28 · 개정 792)

```
★★★ ★ **GET `https://m.kcar.com/bc/detail/carInfoDtl?i_sCarCd={carCd}`**
   ★ ★ 보기 — `?i_sCarCd=EC61366120`
   ★ ★ 실측 ★ **200 · 2.2MB** · ★ 사고 ○ · 보증 ○ · 성능 ○ · 주행 ○ · 옵션 ○
★ ★ 가이드는 ★ `CarDetail`·`carDetail`·`detail`·`view`·`info` 를 두드렸다 — ★ **다 404**
   ★ ★ 참 이름은 ★ **`carInfoDtl`** 이다.  ★ 짐작으로 못 맞힐 이름이었다

★★ ★ **JSON API 는 없다** — ★ `mapi` 쪽 셋이 다 404 다
   ★ ★ **HTML 이 정본**이다.  ★ 거기서 뽑아야 한다
```

```
매물번호 칸은 `carCd` 다.
필수  ★ ★ **`Referer: https://m.kcar.com/bc/search/CarList`** 를 붙인다
필수  ★ ★ 2.2MB 다 — ★ **필요한 자리만 뽑고 ★ 원문은 `raw_response` 에 남긴다**
필수  ★ ★ **뽑을 것** — 사고 · 보증 · 성능(정비) · 주행 · 옵션
      ★ ★ **없는 것** — 소유자 변경 · 용도 · 압류·저당 · 색상 (★ 화면 글에 없다)
      ★ ★ 그 넷은 ★ `f-table` ⑤(아무 데도 없다)로 둔다
```

---

# ★★ 5. 볼보 전량 — ★ 1층으로 받는다 (마스터 08-28)

```
GET https://m.kcar.com/bc/search/CarList?searchCond={
  "wr_eq_sell_dcd":"ALL",
  "wr_in_multi_mnuftr":"017",        ← ★ 1층 · 제조사만
  "carType_mnuftr":"IMP" }

★★ ★ **1층 열쇠는 ★ `wr_in_multi_mnuftr`** 다 — ★ 볼보 전량이 온다
★ ★ 층마다 이름이 다르다 —
   1층 `wr_in_multi_mnuftr` · 2층 `_modelGrp` · 3층 `_model` · 4층 `_model_grd`
★ ★ `carType_` 도 ★ 층마다 짝맞춘다 (`carType_mnuftr` · `carType_modelGrp` …)
```

---

# ★★ 전기차 — ★ K카에는 ★ **0대**다 [실측 08-29 · 가이드]

```
목록이 ★ `fuelNm` 을 준다 — ★ 상세가 없어도 갈린다
★ 우리 대상 105건의 연료 — ★ 가솔린 80 · 디젤 14 · ★ **가솔린+전기(HEV) 11**
★★ ★ **순수 전기는 0대**다 — ★ 폴스타·EX30·C40·모델Y·GV60·G80_EV·GV70_EV ★ 다 없다
★ 전량 487건에서 「전기」가 든 것은 28건인데 ★ 27건이 하이브리드이고
  ★ 순수 전기는 ★ 「현대 아이오닉 5」 ★ 한 대뿐 — ★ 우리 26종이 아니다
★ 「없다」가 아니라 ★ **08-29 재고가 0**이다.  ★ 매물은 날마다 바뀐다
```

---

# ★★★★★ 08-29 정정 — ★ 「전량 487」은 ★ **이 창구가 주는 487**이다 (마스터가 주소를 주심)

```
★ 마스터께서 주신 주소 —
  `m.kcar.com/bc/search/CarList?searchCond={"wr_in_fuel_cd":"009",
     "wr_eq_sell_dcd":"ALL","wr_in_multi_columns":"cntr_rgn_cd|cntr_cd"}`

★★ ★ **`wr_eq_sell_dcd=ALL`** 이 ★ 거기 있다 — ★ 파는 갈래를 ★ **다** 고른다는 뜻이다
   ★ ★ 그런데 ★ `stockCar/list` 487건은 ★ `sellDcd` 가 ★ **전부 `None`** 이다 (실측 08-29)
   ★ ★ 곧 ★ 이 창구는 ★ **`sellDcd` 칸으로는 안 가른다** — ★ 487 이 전량인지 ★ **못 가른다**

★★★★ 08-29 재정정 (마스터 — 「★ **직거래가 포함되어 있다구?**」) — ★ **아니다.  ★ 전부 K카 것이다**
```
★ 487건을 ★ 칸으로 세었다 [실측 08-29] —
  `cntrNm` ★ **474 = 「…직영점」** (분당용인·영등포·안양·서초·경인·안성 …)
            ★ **13 = 「홈서비스 메가센터」** ← ★ K카 자기 센터다
  `csgmtYn`(위탁)  ★ **487 전부 `N`**
  `selerNm`·`usrNm`·`membCd`·`chnlType` ★ **487 전부 `None`** — ★ 파는 사람이 없다
★★ ★ 곧 ★ **개인 직거래 매물은 ★ 한 건도 없다.  ★ 487 이 다 K카 재고다**
★ ★ 내가 「직영/제휴를 안 가른다」고 적은 것은 ★ 규격 214·215행(`drct`·`acm`)을 ★ **옮겨 적은 것**이지
  ★ ★ 이 응답을 ★ **센 것이 아니었다** (오판 181)
★ ★ 아직 못 아는 것 — ★ `sell_dcd=ALL` 이 ★ **제휴·인증(`/acm`)을 더 주는가**.  ★ `enc` 라 못 잰다
```
★ 내가 08-29 에 적은 「전량 487」은 ★ **「이 창구가 주는 487」**로 고친다 (오판 180)
```

## ★ 조건을 안 받는다 — ★ 여섯 꼴을 두드렸다 [실측 08-29]

| 붙인 것 | 응답 |
|---|---|
| (없음) · `fuelType=009` · `fuelTypes=009` · `wr_in_fuel_cd=009` · `sellDcd=ALL` · `searchCond={…}` | ★ 여섯 다 **200 · 889,533B · 487건** |

```
★★ ★ **한 바이트도 같다** — ★ 「200 이 왔다」가 ★ 「좁혀졌다」가 아니다 (기준서 ㉮)
★ `m.kcar.com/bc/search/CarList` 는 ★ 2.1MB SPA 껍데기다 — ★ 매물이 JS 로 그려진다
★ `mapi.kcar.com/bc/search/list/{drct,acm}` 에 ★ 평문 JSON 을 POST 하면 ★ **500** 이다
  ★ ★ 규격대로 ★ 요청 본문이 ★ `enc` 다.  ★★ **풀지 않는다** (금지)
```

## ★★ 연료 코드표를 얻었다 [실측 08-29 · 마스터가 주신 주소에서]

| 코드 | 연료 | 487건 중 |
|--:|---|--:|
| `001` | 가솔린 | 309 |
| `002` | 디젤 | 147 |
| `006` | 가솔린+전기 (HEV) | 27 |
| `003` | LPG | 3 |
| ★ **`009`** | ★ **전기** | ★ **1** (현대 아이오닉 5) |

```
★ 마스터께서 주신 `wr_in_fuel_cd=009` 가 ★ **전기**임이 확인됐다
★ 이 창구 안에서는 ★ 전기가 ★ 아이오닉5 한 대뿐이고 ★ 우리 26종이 아니다
★★ ★ 그러나 ★ **`sell_dcd=ALL` 쪽에 더 있는지는 ★ 못 쟀다** —
   ★ ★ `enc` 를 안 풀고는 ★ 가이드가 못 잰다.  ★ 개발측이 잰다
★ ★ 그래서 ★ 「K카 전기 0대」가 아니라 ★ **「이 창구에는 0대 · ALL 쪽은 못 쟀다」**로 적는다
```

## ★ 화면 159 vs 우리 대상 105 — ★ 까닭이 둘일 수 있다

```
① 팔린 차를 안 거른다 (`collect_kcar.py:176` — 오판 175 · 명령서 1b)
② ★ 이 창구 **밖**의 매물이 저장돼 있다 (`sell_dcd=ALL`)
★★ ★ **둘을 못 가른다** — ★ ①만이라고 단정하지 않는다 (모양 ⑫)
```
