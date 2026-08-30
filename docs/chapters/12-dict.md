# 4장. 키 · 코드 · 사전 (STEP 40–46)

```
version  SPEC-2026.08.29-r977
follows  `docs/chapters/30-score/f-table.md`
sources  실측 08-22
checks   S46-38 · S46-39
```


## 4장 정의서

**본 장은 「같은 값을 같은 것으로 인정하는 규칙」을 확정한다.**
**v1 실패의 절반이 이 층에서 났다** — 휀더/펜더 · 3자리 vs 4자리 · 연료 표기 · 부위 문자열.

### 구조체

```python
@dataclass(frozen=True)
class CodeEntry:
    site: str
    scope: str          # 'global' · 'target' · 'model'
    axis: str           # 'option' · 'fuel' · 'color' · 'panel' · 'panel_rank' ...
    code: str
    display: str
    count_seen: int
    first_seen: date
    last_seen: date
    status: str         # confirmed · pending · retired
```

### 함수

| 이름 | 입력 | 출력 | 목적 |
|---|---|---|---|
| `extract_distinct` | `endpoint, json_path` | `list[tuple[str,int]]` | RAW 에서 값·빈도 |
| `build_dict` | `axis` | `DictBuildReport` | 사전 생성·갱신 |
| `resolve_code` | `axis, code, scope_key` | `CodeEntry \| None` | 코드 → 표시명 |
| `normalize_enum` | `axis, raw_value` | `str \| None` | **관측된 표기 변형만** 정규화 |
| `assert_no_unknown` | `axis` | `None` | 미분류 0건 시험 |

**`resolve_code` 는 `scope_key` 를 반드시 받는다.** 전역 조회를 허용하면 P1 이 무너진다.

### scope → scope_key 생성 규칙

| `scope` | `scope_key` | 예 |
|---|---|---|
| `global` | `site` | `encar` |
| `target` | `site` + `target_key` | `encar/KOLEOS_HEV` |
| `model` | `site` + `model_catalog_key` | `encar/843925820240902` |

```
필수   사전 키는 (scope_key, axis, code) 다.  code 단독으로 유일하지 않다
금지   scope_key 없이 code 만으로 조회하는 API 를 만드는 것
이유   2차 사이트가 붙으면 같은 code 가 다른 사이트에서 다른 뜻이 된다
```

### 사전 항목 상태 4종

**「미관측」과 「unknown」을 구분한다. 섞으면 v1 이 재현된다.**

| 상태 | 뜻 | 발생 | 판정 사용 | 삭제 |
|---|---|---|---|---|
| `confirmed` | 확인 완료 | 사람이 검토 후 | **가능** | 안 함 |
| `pending` | **신규 관측. 미검토** | RAW 에 새 값 등장 | **불가 · 경고** | 안 함 |
| `retired` | 더 이상 안 나옴 | 최근 수집에서 미관측 | 과거 데이터에는 사용 | **안 함** |
| (미관측) | 사전에도 RAW 에도 없음 | — | — | — |

```
신규 관측    →  pending.  unknown 이 아니다.  오류도 아니다
미관측       →  retired.  존재하지 않는 값이 아니다.  이번 표본에 없었을 뿐
retired      →  삭제하지 않는다.  과거 매물 해석에 필요하다
unknown      →  이 상태는 없다.  v1 은 미분류를 unknown 으로 삼켜
                accident_type · seller_type 이 전건 unknown 이 됐다
```

---

## STEP 40 — 코드 체계 실측

**엔카 옵션 코드는 자릿수에 따라 성격이 완전히 다르다. 섞으면 안 된다.**

| 자릿수 | 원천 | 범위 | 실측 |
|---|---|---|---|
| **3자리** | 목록 facet `Options` · 상세 A `options.standard` | **전 차종 공통** | 코드↔이름 충돌 **0건** |
| **4~5자리** | 카탈로그 API · 상세 A `options.choice` · facet `JatoOptions` | **모델별** | **같은 코드가 모델마다 다른 옵션이다** |

### 4~5자리는 모델마다 다른 물건이다 — 실측

```
1026   13가지 이름
         20" 투톤 하이랜드 알로이 휠 & 245/45 R20 저소음 폼 타이어
         새틴 어반 그레이
         증강현실 헤드업 디스플레이(AR-HUD) + 차음 윈드 쉴드 글라스 + 프레임리스 룸미러

10002  12가지 이름
         파노라마 선루프
         새틴 어반 그레이 외장 컬러
         미네랄 코퍼 외장 컬러

1023   11가지     시그니쳐 디자인 셀렉션 II / 파퓰러 패키지 / 컨비니언스 패키지
```

**5자리 코드도 있다 (133건).** 「4자리」로 단정하면 누락된다.

```
필수   자릿수로 판단하지 않는다.  3자리는 전역, 그 외는 모델별로 처리한다
      조회 시 반드시 model_catalog_key 를 함께 넘긴다
금지   4~5자리 코드를 모델 없이 조회하는 것
```

### 3자리는 공통이다 — 실측 근거

```
목록 facet Options   전 차종에서 코드↔이름이 동일.  같은 코드가 다른 이름인 사례 없음
예   010 선루프 · 079 크루즈 컨트롤(어댑티브) · 086 후측방 경보 시스템
     087 360도 어라운드 뷰 · 088 차선이탈 경보(LDWS) · 095 헤드업 디스플레이(HUD)
```

**따라서 3자리 사전은 사이트 단위로 하나면 된다.**
**단 「공통이다」도 실측 결과이므로, 사전 생성 때마다 충돌 검사를 돌린다.**

```
검사   같은 (site, 3자리 code) 에 display 가 2개 이상이면 실패
      새 차종을 추가했을 때 공통성이 깨질 수 있다
```

---

## STEP 41 — 사전 축 목록

| axis | scope | 원천 | 용도 |
|---|---|---|---|
| `option3` | global | facet `Options` | 3자리 코드 → 옵션명 |
| `option_model` | model | catalog API | 4~5자리 → 이름·가격 |
| `fuel` | global | facet `FuelType` | 연료 완전일치 |

```
★ 08-16 — 목록 원문에도 같은 값이 있다
실측   목록 7,631건에서 fuel 5종 · color_ext 23종 · color_int 10종 · trim 68종 관측
       facet 을 못 받아도 사전을 채울 길이 있다는 뜻이다

★ 다만 facet 과 목록은 다르다
  facet   그 사이트가 인정하는 값의 전체 집합
  목록    지금 등록된 매물이 가진 값만
  목록으로 만들면 「아직 매물이 없는 값」이 빠진다
  나중에 그 값이 뜨면 미분류가 된다

필수   facet 이 있으면 facet 이 정본이다
필수   facet 이 없으면 목록에서 관측한 값으로 pending 을 만든다
       confirmed 로 바로 올리지 않는다
필수   그 pending 에 출처를 남긴다 — source='list' · 'facet'
       화면에 「facet 없이 목록에서 관측한 것입니다」를 낸다
필수   나중에 facet 을 받으면 목록 관측분과 대조한다
       facet 에만 있는 값은 새로 pending 으로 들어온다
       목록에만 있는 값은 ★ 확인이 필요하다 — facet 에 없는 값이 왜 매물에 있나
금지   목록 관측만으로 confirmed 를 만드는 것
       「전체 집합을 봤다」가 아니기 때문이다
검산   V3-37  목록 관측이 confirmed 를 자동으로 만들지 않는가
       V3-38  facet 수신 후 목록 관측분과 대조하는가
```

```
★ 출처와 확정은 다른 것이다 — 08-16 정정
  source_endpoint   어디서 왔나 (facet · list)
  status            지금 무엇인가 (pending · confirmed · retired)
  ★ 둘은 서로 독립이다

  source='list' · status='pending'     목록에서 관측만 함
  source='list' · status='confirmed'   ★ 사람이 확정한 것.  정상이다
  source='facet' · status='pending'    facet 에서 왔지만 아직 미검토

필수   V3-37 은 「자동 확정을 했는가」를 본다
       source 만 보고 판정하지 않는다
필수   사람이 확정했는지는 config_change 이력으로 가른다
       확정에는 사유와 계정이 남는다 (STEP 136e)
금지   source 로 「사람이 했는지」를 추정하는 것
       ★ 가이드가 이 둘을 한 필드로 보게 검사를 썼다.  오탐이 났다 (실측 08-16)
```

```
★ 왜 이것이 중요한가
  지금 AWS 에서 facet 을 못 받으면 S3 가 영원히 막힌다
  목록으로 pending 을 만들면 파이프라인이 끝까지 돈다
  다만 「완전하지 않다」를 잊지 않게 표시한다
```
| `color_ext` · `color_int` | global | facet `Color` · `SeatColor` | 색상명 + hex |
| `trim` | target | **목록 `SearchResults[].Badge`** | 트림. facet 이 아니다 |
| `sell_type` | global | facet `SellType` | 일반·렌트·리스 |
| `condition_flag` | global | facet `Condition` | Record·Inspection·Resume·InspectionDirect |
| `panel` | global | 점검부 `outers[].type.title` | 부위명 (**표시 전용**) |
| `panel_rank` | global | 점검부 `outers[].attributes` | **골격/외판 판정** |
| `panel_status` | global | 점검부 `outers[].statusTypes[].title` | 교환·판금 등 |
| `accident_type` | global | 이력 `accidents[].type` | 사고 유형 |
| `service_mark` · `trust` | global | 목록 배열 | 사이트 배지 |

**축이 늘어나면 이 표에 행을 추가한다. 표에 없는 축은 사전을 만들지 않는다.**

### 축별 특성 — 사전 설계에 영향

### `AxisPolicy(scope, on_new, on_conflict)`

**`on_new`(새 값 등장)와 `on_conflict`(같은 키에 다른 값)는 다른 사건이다.**

| axis | scope | `on_new` | `on_conflict` |
|---|---|---|---|
| `option3` | global | `confirm` | **`halt`** |
| `option_model` | model | `confirm` | `allow` |
| `fuel` · `color_*` · `sell_type` · `condition_flag` · `lease_type` | global | `confirm` | `pending` |
| `trim` | target | `confirm` | `pending` |
| `panel` | global | `pending` | **`halt`** |
| `panel_status` | global | **`halt`** | **`halt`** |
| `panel_rank` | global | **`halt`** | **`halt`** |
| `accident_type` | global | **`halt`** | **`halt`** |

### ★ `halt` 축은 고정 집합을 미리 심는다

```
사고   첫 수집에 사전이 비어 있어 정상값 RANK_ONE 에서 멈췄다
      halt 는 「새 값이 뜨면 규칙을 다시 보라」인데,
      비어 있으면 첫 값이 전부 「새 값」이다
```

```
파일   config/dictionaries/fixed_enums.json
내용   panel_rank · panel_status · accident_type · condition_flag
      지시서가 명시한 고정 집합을 status='confirmed' 로 심는다
시점   S3 사전 생성 전.  비어 있으면 그때 만든다
```

```
금지   halt 를 confirm 으로 바꾸는 것.  그러면 진짜 새 값도 통과한다
근거   고정 집합은 지시서가 정한 것이다.  관측이 아니라 사양이다
검증   V3-30  halt 축의 사전이 비어 있지 않은가 (S9 선행 조건)
```

### `on_new` 를 가르는 기준 — 값의 출처

```
confirm   facet 이 선언한 열거값
          사이트가 정의한 것이라 관측 여부와 무관하다
          Count=0 도 confirmed (STEP 43)

pending   원문에서 관측한 값.  사이트가 목록을 주지 않는다
          panel — 점검 부위명.  차종·연식에 따라 새 표기가 나온다

halt      판정 규칙이 그 값에 직접 걸려 있는 축
          새 값이 뜨면 규칙을 다시 봐야 한다
```

### `halt` 3축 — 왜 중단인가

```
panel_rank      5값 고정 (RANK_ONE·TWO·A·B·C)
                골격/외판 판정이 이 값에 걸려 있다 (STEP 76)
                새 값 = 점검 양식 변경.  분류를 다시 해야 한다

panel_status    4값 (교환(교체)·판금/용접·용접,절단·손상)
                감점 대상 여부가 이 값에 걸려 있다
                새 값이 뜨면 감점인지 아닌지 알 수 없다

accident_type   3값 (1·2·3)
                1·2 = 내 차 피해 · 3 = 타 차 가해 (STEP 77)
                새 값이 뜨면 어느 쪽인지 모른다.  금액 집계가 통째로 틀린다
```

```
★ panel 만 pending 인 이유
  부위명은 표시 전용이다.  판정은 attributes(panel_rank) 가 한다 (STEP 44)
  새 부위명이 떠도 랭크가 있으면 판정은 정상이다
  v1 에서 실제로 새 표기(휀더)가 나온 축이라 halt 로 두면 자주 멈춘다
```

---

## STEP 42 — 사전 생성 규칙

**손으로 적지 않는다. RAW 에서 뽑는다.**

```
1  RAW 에서 해당 경로의 distinct 값과 빈도를 추출
2  기존 사전과 대조
3  신규 값 → status='pending' 으로 적재 + 알림
4  사람이 확인 → status='confirmed'
5  더 이상 안 나오는 값 → status='retired'.  삭제하지 않는다
```

**`pending` 값이 있으면 그 축을 쓰는 판정은 경고와 함께 돈다. 조용히 무시하지 않는다.**

### v1 실사고 — 손으로 적어서 무너졌다

```
사전    프론트펜더 · 앞펜더 · 리어펜더
원문    프론트 휀더(좌) · 프론트 휀더(우)
결과    가장 흔한 부위 344건이 미분류
```

**「휀더」와 「펜더」를 사람이 예측할 수 없다. 원문에서 뽑으면 애초에 생기지 않는 문제다.**

### `normalize_enum` — 정규화와 추정의 경계

```
normalize_enum 은 관측된 표기 변형만 정규화한다.
의미 추론 · 분류 · 대체값 생성은 하지 않는다.
```

| 입력 | 처리 | 판정 |
|---|---|---|
| `"가솔린+전기"` | → 사전의 confirmed 값 | 정규화 |
| `"가솔린 + 전기"` (공백 변형) | **양쪽 다 RAW 에서 관측된 경우에만** 같은 값으로 | 정규화 |
| `"하이브리드"` | **추정. 금지** | 사전에 없으면 `pending` |

```
금지   사전에 없는 값을 「비슷하니까」 기존 값으로 매핑
      대체값 · 기본값 반환.  None 을 돌려주고 pending 에 적재한다
필수   표기 변형은 RAW 에서 두 표기가 모두 관측됐을 때만 동일시한다
      한쪽만 관측됐으면 그것은 변형이 아니라 새 값이다
```

**`하이브리드` 는 실제로 `record` API 에서 관측된다.** 그러나 그것은
「목록의 `가솔린+전기` 와 같은 값」이 아니라 **다른 API 의 다른 사전 항목**이다 (STEP 43).

### 표기 흔들림 — 정규화하지 않는다

```
금지   공백 제거 · 괄호 제거 · 유사 문자 치환으로 억지 매칭
      → 서로 다른 값이 같은 것으로 합쳐진다
필수   원문 값을 그대로 키로 쓴다.  display 만 사람이 읽기 좋게 둔다
```

**예** — `라디에이터 서포트(볼트체결부품)` 는 괄호까지 포함해 하나의 값이다.
**괄호를 떼면 다른 부위와 구분이 안 될 수 있다.**

---

## STEP 43 — 열거형 완전 일치

**부분 문자열 검색을 금지한다.**

```
금지   if "LPG" in fuel:        →  LPG(일반인 구입) · 가솔린+LPG 를 구분 못 한다
      if "하이브리드" in fuel:   →  엔카는 가솔린+전기 로 준다.  0건이 된다
필수   fuel in ("가솔린+전기",)   완전 일치 + 사전 기반
```

### ★ facet 열거값에는 `Count=0` 인 것이 있다

```
연료 축 실측 — 값 12종.  그중 관측된 것은 6종
  관측  가솔린 · 가솔린+전기 · 전기 · 디젤 · LPG(일반인 구입) · 가솔린+LPG
  Count=0  LPG+가솔린 · LPG+전기 · 가솔린+CNG · 디젤+전기 · 수소 · 기타
```

```
★ Count=0 은 「그 값이 없다」가 아니라 「이 쿼리 범위에 없다」다
  사이트가 정의한 열거값이므로 사전에 등록한다
필수   Count 와 무관하게 facet 의 전 값을 사전에 넣는다
      status='confirmed'.  Count=0 이라고 pending 이나 retired 로 두지 않는다
근거   다른 차종·다른 시점에 나타날 수 있다
      사전에 없으면 그때 pending 이 뜨고 판정이 멈춘다
금지   Count>0 인 것만 사전에 넣는 것
```

### 관측된 6종 — 차종별 분포

```
스포티지   가솔린 · 가솔린+전기 · 디젤 · LPG(일반인 구입)
그랜저     가솔린 · 가솔린+전기 · LPG(일반인 구입)
콜레오스    가솔린+전기 · 가솔린 · 가솔린+LPG
모델Y      전기 (단일)
```

```
스포티지   가솔린 556 · 가솔린+전기 439 · 디젤 264 · LPG(일반인 구입) 165
그랜저     가솔린 730 · 가솔린+전기 613 · LPG(일반인 구입) 250
콜레오스    가솔린+전기 210 · 가솔린 53 · 가솔린+LPG 1
모델Y      전기 489 (단일)
```

**`LPG` 로 쓰면 0건이 된다. `하이브리드` 로 써도 0건이다.**

### API 별 표기가 다르다 — 실측

| 차량 | 필드 | 목록·상세 A | 이력(`record`) |
|---|---|---|---|
| 콜레오스 | 연료 | `가솔린+전기` | **`하이브리드`** |
| 콜레오스 | 제조사 | `르노코리아(삼성)` | **`삼성`** |
| 모델Y | 제조사 | `테슬라` | **`null`** |

```
금지   record 의 fuel · maker 로 차종을 분류하거나 역매칭
용도   교차검증 로그.  불일치 시 경고만 남기고 목록·상세 A 값을 채택
필수   maker null 가드 (테슬라)
```

**사전은 API 별로 분리한다.** 같은 개념이라도 표기가 다르면 다른 사전이다.

---

## STEP 44 — 코드값이 있으면 문자열을 쓰지 않는다

**이 장에서 가장 중요한 규칙이다.**

```
사이트가 코드값으로 알려주는 것을 문자열 매칭으로 다시 판정하지 않는다.
```

### 실측 — `attributes` 는 부위 분류 코드다

| `attributes` | 분류 | 부위 |
|---|---|---|
| `RANK_ONE` | **외판 1랭크** | 휀더 · 도어 · 후드 · 트렁크 리드 · 라디에이터 서포트 |
| `RANK_TWO` | **외판 2랭크** | 쿼터 패널 · 사이드실 패널 · 루프 패널 |
| `RANK_A` | **골격 A** | 리어 패널 · 트렁크 플로어 · 인사이드 패널 · 프론트 패널 |
| `RANK_B` | **골격 B** | 사이드 멤버 · 휠하우스 · 필러 패널 |
| `RANK_C` | **골격 C** | 플로어 패널 |

```
골격 판정   RANK_A · RANK_B · RANK_C 존재 여부
외판 판수   RANK_ONE · RANK_TWO 개수
부위명      표시 전용.  판정에 쓰지 않는다
```

**v1 은 부위명 문자열로 골격/외판을 판정하려다 344건을 놓쳤다.**
**엔카는 처음부터 코드값으로 주고 있었다.**

```
점검   새 축을 만들 때 「사이트가 코드로 주는가」를 먼저 확인한다
      코드가 있으면 문자열 경로를 만들지 않는다
```

---

### ★ 사전이 비어 있는 것도 실패다 — 08-14

```
실측   dict_enum 0 행인데 assert_no_unknown 이 통과했다
      색상 · 연료가 미분류인 채 판정이 끝났다
원인   pending 만 본다.  「사전 자체가 없다」는 안 본다
```

```
필수   판정에 쓰는 축의 dict_enum 이 0 행이면 그것도 실패다
근거   v1 이 accident_type 전건 unknown 이 된 것과 같은 자리다
검산   V4-25  판정에 쓰는 축의 사전이 비어 있지 않은가
```

---

## STEP 45 — 사전 미분류 0건 시험

```
assert_no_unknown(axis)
  RAW 의 distinct 값이 전부 사전에 있는가
  status='pending' 이 있으면 목록과 함께 실패
```

**적용 축** — `fuel` · `color_*` · `panel` · `panel_rank` · `panel_status` · `accident_type` · `option3`

```
실패 시   그 축을 쓰는 판정을 중단한다.  기본값으로 넘어가지 않는다
이유     v1 은 미분류를 조용히 unknown 으로 처리해
        accident_type 전건 unknown · seller_type 전건 unknown 이 됐다
```

### 신규 값 발생 시 절차

```
1  pending 적재 + 알림
2  원문 표본 3건 확인
3  기존 값의 표기 변형인가, 진짜 새 값인가 판정
4  판정 결과를 사전에 반영하고 confirmed
5  해당 축 재판정 (재파싱 아님 — 사전만 바뀜)
```

---

### 사전 버전 · 재현성 ★

```
문제   오늘의 사전으로 과거 데이터를 다시 해석하면 과거 점수가 재현되지 않는다
      사전이 바뀌면 같은 원문이 다른 판정을 낸다
```

**`dict_version` 을 도입한다.**

```
dict_version    사전 스냅샷 식별자.  사전이 변경될 때마다 증가
저장            result_axis · result_score 에 함께 기록
                (listing_id, calc_version, dict_version) 으로 재현 단위가 완성된다
```

| 버전 | 무엇이 바뀌면 | 재처리 범위 |
|---|---|---|
| `parse_version` | 파싱 규칙 | RAW → CORE → 판정 → 채점 |
| **`dict_version`** | **사전 항목** | CORE → 판정 → 채점 |
| `calc_version` | 배점 · 등급컷 | 채점만 |

```
재현     과거 점수를 다시 만들려면 그때의 dict_version 사전으로 돌린다
보존     사전은 버전별로 스냅샷을 남긴다.  덮어쓰지 않는다
retired  과거 dict_version 에서는 confirmed 였던 값을 그대로 해석해야 한다
```

**11장 후보 추적은 「어제 점수 vs 오늘 점수」를 비교한다.**
**사전이 바뀐 것을 매물이 바뀐 것으로 오인하면 안 된다.**

```
비교 시   dict_version 이 다르면 「사전 변경으로 인한 차이」를 먼저 분리한다
표시     점수 변동 사유를 매물 변경 / 사전 변경 / 배점 변경으로 나눠 보여준다
```

### 사전 충돌 처리 ★

**같은 `(scope_key, axis, code)` 에 서로 다른 `display` 가 관측되는 경우.**

| 상황 | 판정 | 조치 |
|---|---|---|
| 3자리 코드에 이름 2개 | **공통성 가정이 깨졌다** | 사전 생성 실패 · 중단 · 보고 |
| 4~5자리 코드에 이름 2개 (다른 모델) | 정상 | `scope=model` 이므로 충돌 아님 |
| 4~5자리 코드에 이름 2개 (**같은 모델**) | 사이트 데이터 변경 | `pending` 적재 · 사람 검토 |
| 표기만 다름 (공백 · 괄호) | **추정 금지** | 양쪽 다 `pending`. 자동 병합하지 않는다 |

```
금지   충돌을 최신 값으로 덮어쓰는 것
      조회 빈도가 높은 쪽을 채택하는 것
필수   충돌 사실을 남기고 사람이 판정한다.  판정 전까지 그 코드는 판정에 쓰지 않는다
```

**3자리 충돌은 특히 중요하다.** 「전 차종 공통」이 이 시스템의 전제인데,
그것이 깨졌다는 뜻이므로 **조용히 넘기면 P1 전체가 무너진다.**

## STEP 46 — 분류 2단 · 코드 사전과의 관계

**분류(`target_key` 판정)는 사전을 쓰지만 사전이 분류를 결정하지 않는다.**

```
1단 잠정   목록 필드만으로 (FuelType · Badge)      classify_stage='provisional'
2단 확정   상세 A 제조사 사양으로                   classify_stage='confirmed'
```

**목록 응답에는 배기량이 없다** (29경로 실측).
**배기량만으로 분류하면 상세 A 미확보분이 전부 미분류가 된다** (v1 실측 1,364건 · 28.7%).

| 근거 | 신뢰도 | 확보 시점 |
|---|---|---|
| `spec.displacement` | **제조사 사양** | 상세 A |
| `spec.fuelName` · `FuelType` | 딜러 입력 | 목록 |
| `Badge` · `gradeName` | 딜러 입력 | 목록 · 상세 A |

### ★ 전기차에는 배기량 분류를 쓰지 않는다

```
실측   모델Y 의 spec.displacement 가 22종이다
      0 · 1 · 11 · 62 · 70 · 100 · 111 · 126 · 158 · 160 · 173 · 180 · 200
      208 · 230 · 236 · 237 · 239 · 300 · 360 · 400 · 1000 · 2000
      같은 차종인데 값이 제각각이다.  딜러 입력값이고 의미가 없다
```

**표본** — `detail_ev_tesla` 의 `displacement` 는 180 이다. 모델Y 전체로는 22종이 나온다.

```
필수   fuel_match 가 「전기」인 target 은 displacement_range 를 null 로 둔다
      2단 확정을 건너뛰고 provisional 을 confirmed 로 올린다
근거   전기차에는 배기량이 없다.  사이트가 받는 칸이 있을 뿐이다
금지   전기차에 displacement_range 를 걸어 분류하는 것
      → 값이 22종이라 대부분 미분류가 된다
검산   target 의 fuel_match 에 「전기」가 있으면 displacement_range 는 null 인가
```

### 실측 — 콜레오스

```
1499 · 가솔린+전기   214   정상 (1.5 E-TECH 하이브리드)
1969 · 가솔린         49   정상 (2.0 가솔린 · 제외 대상)
1969 · 가솔린+전기     3   딜러 오등록 유력
1499 · 가솔린+LPG      1   배기량은 대상 · 연료는 제외   →  conflict
(NULL) · 가솔린+전기  27   상세 A 미확보                →  provisional 유지
```

**표본 시험** — `detail_hybrid_renault` 는 `modelGroupName` 이 「그랑 콜레오스」인데
`displacement` 1969 · `fuelName` 「가솔린」이다. **2.0 가솔린이지 1.5 하이브리드가 아니다.**
목록 필드만으로는 통과하고, 2단 확정에서 걸러진다.

```
충돌 시   conflict 로 표시하고 통과시킨다.  배제하지 않는다
기록      classify_stage · classify_source · classify_conflict
금지      임의 필터를 승인 없이 추가하는 것
         v1 은 trim_exclude:("2.0",) 를 추측으로 넣었다가 철회했다
```

**「엔카가 잘못 줬다」가 아니다. 엔카는 배기량으로 정확히 구분해 줬고 그 필드를 안 썼을 뿐이다.**

---

**4장 종료 (STEP 40–46).**

---

