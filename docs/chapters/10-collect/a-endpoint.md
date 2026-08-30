## STEP 16 — 수집 계층 원칙

```
version  SPEC-2026.08.29-r995
follows  `docs/chapters/30-score/f-table.md`
sources  실측 08-22
checks   S46-38 · S46-39
```


```
수집은 받아서 저장만 한다.  해석하지 않는다.
```

| 금지 | 이유 |
|---|---|
| 수집 함수 안에서 파싱 | 파싱 규칙이 바뀔 때마다 재수집이 된다 |
| 응답 일부만 저장 | 나중에 필요한 필드가 없어 전량 재수집 |
| `include` 류 파라미터로 블록 선별 | 화이트리스트라 나머지가 조용히 잘린다 |
| 조건 보고 요청 건너뛰기 | 그 조건 값 자체가 틀릴 수 있다 |
| 전역 변수로 원문 전달 | v1: 원문 2,183건이 잘못된 라벨로 저장 |

**빈 응답·404 도 결과다.** 「요청하지 않음」과 「요청했으나 없음」을 반드시 구분한다.

```
status   ok · empty · not_found · error · not_requested
```

**`not_requested` 가 남은 매물은 수집 완료로 세지 않는다.**

---

## STEP 17 — 엔드포인트 목록 (엔카 · 실측 확인)

**아래는 v1 RAW 원문에서 확인된 것이다. 추정 없음.**

| # | kind | scope | per_call | v1 상태 |
|:--:|---|---|---|---|
| 1 | `list` | target | 차종 × 페이지 | 확보 |
| 2 | `detail` | listing | 매물 1 | 확보 |
| 3 | `inspection` | listing | 매물 1 | 확보 |
| 4 | `record` | listing | 매물 1 | **대부분 오염** ★ |
| 5 | `diagnosis` | listing | 매물 1 | **미수집** ★ |
| 6 | `catalog` | model | **대표 매물 1건** (STEP 21c) | 확보 |
| 7 | `facet` | target | **`collect_group` 1** (축 미지정) | 확보 |

### ★ `record` 원문 오염

```
v1 에서 endpoint='record' 로 저장된 원문의 대부분이 점검부 응답이었다.
공유 변수(last_raw)가 원인이다 (STEP 25a).
```

```
결과   이력 축(사고 · 보험 · 렌트)의 원문 근거가 사실상 없다
조치   이력은 재수집이 선행된다.  등록부 blocked (8장 STEP 87)
방지   저장 직전 라벨↔내용 형식 검증 (STEP 18)
      불일치는 raw_response_reject 로 간다.  사후에 세지 않는다
```

**`diagnosis` 는 수집된 적이 없다.**
**두 엔드포인트는 재수집이 선행돼야 한다** (STEP 26).

## URL

```
list        GET  /search/car/list/mobile
                 ?count=true&sr=|MobileModifiedDate|{offset}|{limit}&q={query}
detail      GET  /v1/readside/vehicle/{source_id}
inspection  GET  /v1/readside/inspection/vehicle/{source_id}
record      GET  /v1/readside/record/vehicle/{source_id}/open      ★ /open 필수
diagnosis   GET  /v1/readside/diagnosis/vehicle/{source_id}
catalog     GET  /v1/readside/vehicles/car/{source_id}/options/choice
facet       GET  (list 와 동일) + &inav=|Metadata|
```

```
금지   detail 에 include 파라미터 부착
      → 화이트리스트로 동작해 5개 응답 블록이 조용히 사라진다 (v1 실측)
필수   record 는 /open 접미사.  없으면 404
필수   facet 은 collect_group 당 1회.  inav=|Metadata| (축 미지정)
      → 트림은 목록 SearchResults[].Badge 에서 받는다 (STEP 23)
      → 축을 열거하는 것도 금지.  나중에 필요한 축이 빠져 재수집이 된다
```

---

## STEP 17a [수집] — `q` 쿼리 문법 ★

```
목적    site_query 를 엔카 q 문자열로 조립한다
원천    v1 raw_facet 의 iNav.BreadCrumbs[].RemoveAction  (실측 · 추정 없음)
입력    TargetSpec.site_query · collect_group
출력    q 문자열 (URL 인코딩 전)
값규칙  조건이 하나도 없으면 조립하지 않는다.  전체 매물을 받게 된다
근거    RemoveAction 은 「이 조건을 뺀 쿼리」라 문법 전체를 담는다
금지    추측으로 구분자를 만드는 것.  아래 문법 외의 형태를 쓰는 것
검산    조립한 q 로 받은 BreadCrumbs 가 site_query 와 일치하는가
```

### 문법

```
전체       (And.{항}._.{항}._.{항})
계층 묶음   (C.{상위}._.{하위}.)
범위       {축}.range({하한}..{상한})     한쪽 생략 가능
단일       {축}.{값}.
구분자     ._.
```

**실측 예 — G80**

```
(And.Hidden.N._.MultiViewHidden.N._.Year.range(202100..)._.Price.range(..6000)._.(C.CarType.Y._.(C.Manufacturer.제네시스._.ModelGroup.G80.)))
```

```
Hidden.N · MultiViewHidden.N   숨김 매물 제외.  전 차종 공통
Year.range(202100..)           2021년식 이상
Price.range(..6000)            6,000만 이하
(C.CarType.Y._.(C.Manufacturer.제네시스._.ModelGroup.G80.))
                               국산 → 제네시스 → G80.  중첩 계층
```

### ★ 값 이스케이프 — 괄호가 들어가는 값

```
실측   르노코리아(삼성)  →  르노코리아(삼성_)
```

```
규칙   값 안의 닫는 괄호 ) 앞에 _ 를 넣는다
근거   ) 가 계층 종료 기호와 충돌한다
검증   조립 후 다시 파싱해 원래 값이 나오는가 (왕복 시험)
금지   URL 인코딩만으로 해결하려는 것.  문법 수준의 이스케이프다
```

### 차종별 실측 조건

| collect_group | CarType | Manufacturer | ModelGroup | Year |
|---|:--:|---|---|---|
| `encar:G80` | Y | 제네시스 | G80 | 202100.. |
| `encar:G70` | Y | 제네시스 | G70 | 202100.. |
| `encar:GV70` | Y | 제네시스 | GV70 | 202200.. |
| `encar:GV60` | Y | 제네시스 | GV60 | 202200.. |
| `encar:KOLEOS` | Y | 르노코리아(삼성) | 그랑 콜레오스 | 202400.. |
| `encar:SPORTAGE` | Y | 기아 | 스포티지 | 202200.. |
| `encar:GRANDEUR` | Y | 현대 | 그랜저 | 202300.. |
| `encar:MODEL_Y` | **N** | 테슬라 | 모델 Y | 202200.. |

```
Price   전 차종 ..6000  (6,000만 이하)
공통    Hidden.N · MultiViewHidden.N
★ CarType  국산 Y · 수입 N.  모델Y 만 N 이다.  빠뜨리면 0건이 된다

★ 엔드포인트 순서가 판정에 쓰인다 — 08-14
  detail 이 먼저 와야 encarDiagnosis 를 읽고 diagnosis 를 걸지 정한다
  순서를 바꾸면 조용히 전량 skip 된다 (실측 위험)
필수   LISTING_ENDPOINTS 에 순서 의존을 주석이 아니라 assert 로 박는다
검산   V1-17  diagnosis 가 detail 뒤인가
연식·가격   config/targets.json 의 값이다.  마스터가 바꾼다
```

### ★ 지정한 조건이 조용히 빠지면 안 된다

```
결함   계층 목록이 (CarType · Manufacturer · ModelGroup) 3단계로 고정돼 있으면
      site_query 에 Model 을 넣어도 조용히 사라진다
      잘못된 URL 이 만들어지고, 조립은 「성공」으로 보인다
```

```
필수   계층 목록에 없는 키가 site_query 에 있으면 PolicyError
금지   모르는 키를 무시하고 넘어가는 것
근거   지정한 조건이 사라지는 것은 이 문서가 계속 막아온 유형이다
      「조용히 지나감」은 v1 이 무너진 방식이다 (0장)
검증   V1-10  site_query 의 전 키가 조립된 q 에 반영됐는가
```

### 조립 순서 — 고정한다

```
1  Hidden.N · MultiViewHidden.N
2  Year.range · Price.range        범위 조건
3  (C.CarType._.(C.Manufacturer._.ModelGroup.))   계층 조건
```

```
근거   순서가 다르면 같은 조건이라도 문자열이 달라진다
      캐시 키 · 로그 대조가 어긋난다
검증   같은 site_query 로 두 번 조립하면 같은 문자열인가
```

---

## STEP 18 — 라벨↔내용 형식 검증

**v1 최대 사고의 재발 방지 장치다. 저장 직전에 건다.**

| kind | `required_keys` — **전부 있어야 통과** | `root_type` |
|---|---|---|
| `list` | **`Count` · `SearchResults`** ★ | object |
| `detail` | `category` · `manage` | object |
| `inspection` | `master` · `outers` | object |
| `record` | `carNo` · `openData` | object |
| `diagnosis` | (원문 확보 후 확정) ★ | 미정 |
| `catalog` | `optionCd` (요소) | **array** |

```python
def verify_shape(res: FetchResult, spec: EndpointSpec) -> bool:
    if res.status != "ok":
        return True                              # empty·not_found 는 검증 대상 아님
    body = res.raw
    if spec.root_type == "array":
        if not isinstance(body, list):
            return False
        if not body:
            return True                          # 빈 배열은 정상 (STEP 32)
        return all(k in body[0] for k in spec.required_keys)
    return isinstance(body, dict) and all(k in body for k in spec.required_keys)
```

**`all` 이다. `any` 가 아니다.**

```
실측 근거   record 유효 27건 전부 carNo · openData 를 동시에 보유
           inspection 표본 500건 전부 master · outers 를 동시에 보유
           → 한쪽만 있는 응답은 관측되지 않았다.  all 이 성립한다
```

**`any` 로 쓰면 v1 사고가 재현된다.** 점검부 응답에도 `master` 가 있으므로
`record` 라벨로 저장돼도 `any` 는 통과시킨다. **키 하나로는 라벨을 구분하지 못한다.**

```
주의   required_keys 는 「그 kind 를 다른 kind 와 구분하는 최소 집합」이다
      많이 넣을수록 안전하지만, 조건부로만 나타나는 키를 넣으면 정상 응답을 거부한다
      → 표본 300건 이상에서 100% 출현하는 키만 넣는다

**불일치 시** — `raw_response_reject` 로 보내고 `FormatError` 를 기록한다. **조용히 버리지 않는다.**

```
검증 효과   v1 은 2,183건이 오염된 뒤에야 발견됐다.
           이 검증이 있었으면 첫 건에서 걸린다.
```

---

## STEP 18a [수집] — 목록 응답은 봉투다 ★

```
목적    목록 응답을 통째로 저장한다.  매물 단위로 쪼개지 않는다
원천    /search/car/list/mobile 응답 루트
값규칙  봉투(envelope)에 Count 와 SearchResults 가 있다
       SearchResults[] 의 요소가 매물이다
근거    P3 — 원문 무손실.  쪼개면 봉투의 정보가 사라진다
금지    매물 단위로 나눠 저장하는 것
검산    raw_response(list) 1행 == 요청 1회.  매물 수가 아니다
```

### ★ v1 사고 — 쪼개서 저장했다

```
v1 실측   raw_response endpoint='list' 3,326행이 전부 매물 1건씩이다
         봉투가 하나도 남아 있지 않다

잃은 것   Count       그 쿼리의 전체 매물 수.  페이지네이션의 근거
         페이지 경계   몇 번째 요청의 결과인지
         응답 순서    정렬 결과가 사라진다
결과     「몇 건 있어야 하는가」를 응답에서 알 수 없다
        expected 를 추정으로 세게 된다 (V1-01 이 무의미해진다)
```

```
필수   봉투 1건 = raw_response 1행.  request_url · page 와 함께 저장
파싱   S4 에서 SearchResults[] 를 펼쳐 core_listing 에 넣는다
      펼치는 것은 파싱이다.  저장이 아니다 (1장 STEP 9)
```

### 페이지네이션

```
Count        그 쿼리의 전체 매물 수
sr 파라미터   |MobileModifiedDate|{offset}|{limit}
종료 조건     offset + len(SearchResults) >= Count
             또는 SearchResults 가 빈 배열
```

```
검산   Σ len(SearchResults) == Count 인가
       어긋나면 수집 도중 매물이 바뀐 것이다.  로그에 남긴다
금지   Count 를 무시하고 빈 응답이 나올 때까지 도는 것
      → 마지막 페이지를 놓쳐도 알 수 없다
```

### `required_keys` 정정

```
list   Count · SearchResults      ← 봉투 기준
       Id · ModelGroup 이 아니다.  그것은 요소 기준이다
```

```
★ 형식 검증은 저장하는 단위에 맞춘다
  봉투를 저장하면서 요소 키로 검증하면 전건 거부된다
```

---

