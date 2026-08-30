## STEP 22 — `catalog` 응답 → 사전

```
version  SPEC-2026.08.29-r944
follows  `docs/chapters/30-score/f-table.md`
sources  실측 08-22
checks   S46-38 · S46-39
```


**루트가 배열이다. 매물이 아니라 모델(`jatoVehicleId`) 단위다.**

```json
[{"optionCd":"1009",
  "optionName":"BOSE 서라운드 사운드 시스템(10 스피커) + 액티브 노이즈 캔슬레이션",
  "price":129,
  "description":null}]
```

| 원문 | CORE | 저장처 |
|---|---|---|
| `optionCd` | `option_code` | `dict_model_option` |
| `optionName` | `option_name` | 〃 |
| `price` | `price_manwon` | 〃 |
| `description` | `description` | 〃 |

```
키      (site, model_catalog_key, option_code)
용도    코드 → 이름 · 가격 조회.  사전 전용
금지    이 목록을 그 매물의 장착으로 취급          ← v1 사고
        모델이 파는 옵션 전량이라 전 매물이 '있음' 이 된다
판별    조회 함수는 그 매물의 options.choice 코드만 인자로 받는다
        빈 codes 에 빈 목록을 반환하지 않으면 위반
```

---

## STEP 23 — `facet` 응답 → 사전

```
GET (list URL) + &inav=|Metadata|          축 미지정
```

### ★ 축 미지정은 「전부」가 아니다 — 2026-08-09 실측

```
축 미지정 응답   노드 55개 · 값이 있는 축 39개
누락            Badge 는 축 미지정 응답에 없다.  전 차종에서 없다
→ 「축을 지정하지 않으면 전부 온다」는 전제가 틀렸다
```

### ★ 트림은 facet 이 아니라 목록에서 온다 — 초판 정정

```
초판 서술   「미지정만으로는 Badge 가 오지 않는다.  별도 요청이 필요하다」
실측       facet 이 주는 것은 BadgeGroup 이다.  Badge 가 아니다
          v1 실측이 BadgeGroup 을 Badge 로 읽은 것으로 보인다
```

| 값 | 어디에 | 내용 |
|---|---|---|
| **`Badge`** | **목록 `SearchResults[]`** | **`가솔린 2.5 터보 AWD` · `1.5 E-TECH 아이코닉 2WD`** |
| `BadgeGroup` | facet (Model 지정 시) | `가솔린 4WD` · `디젤 2WD` — **묶음. 배기량이 없다** |
| `BadgeDetail` | 목록 | `프레스티지` · `시그니처` — 세부 등급 |

```
★ trim_include 는 "2.5" · "1.5 E-TECH" 다.  Badge 에만 있다
  BadgeGroup 에는 배기량이 없어 분류에 쓸 수 없다
결론   facet Badge 요청을 폐지한다.  트림은 목록 요소에서 받는다
근거   요청이 collect_group 당 2회 → 1회로 준다
```

```
BadgeGroup 은 별도 축이다
  「등급필터」 묶음이고 트림이 아니다.  Model 을 지정해야 나온다
  Refinements 안에 중첩돼 있다
  쓸지 말지는 미정.  등록부에 unclassified 로 남긴다 (8장 STEP 87)
```

### 요청

| 요청 | 얻는 것 |
|---|---|
| `inav=|Metadata|` | 값이 있는 축.  **개수는 차종에 따라 다르다** |
| ~~`inav=|Metadata|Badge`~~ | **폐지.** 트림은 목록에서 온다 |

```
필수   collect_group 당 1회.  축 미지정만
저장   raw_facet 에 request_kind='unspecified' 로 1행
확장   다른 축도 미지정 응답에 없을 수 있다.  신규 축 필요 시 명시 요청으로 확인
```

### ★ 검증은 축 수가 아니라 필수 축 집합으로 한다

```
금지   축 수 == 39 인가          →  38축 차종 3종에서 fatal 이 난다
필수   REQUIRED_FACET_AXES 가 전부 있는가
```

```python
REQUIRED_FACET_AXES = {          # 사전으로 쓰는 8축 (미지정 응답)
    "Options", "JatoOptions", "FuelType", "Color", "SeatColor",
    "Condition", "SellType", "LeaseType",
}
# REQUIRED_BADGE_AXIS 폐지 — 트림은 목록에서 온다 (위 정정)
```

| 검사 | 기대 | 등급 |
|---|---|---|
| 미지정 응답에 `REQUIRED_FACET_AXES` 전건 존재 | 참 | fatal |

| 축 수가 직전 수집과 크게 다름 | 없음 | warn (사이트 변경 신호) |
| 신규 축 등장 | 등록부 `unclassified` 적재 | warn |

### ★ 축은 `Type='Aspect'` 인 노드다

```
사양   응답 노드에는 이름이 중복되는 것이 있다.  Type 이 다르다

      Price   Type=RangeAction   범위 입력 UI.  Facets 없음
      Price   Type=Aspect        집계.  Facets 있음
```

```
필수   축 = Type 이 'Aspect' 인 노드.  Name 만으로 훑지 않는다
금지   Name 을 키로 하는 dict 에 담는 것
      → RangeAction 이 Aspect 를 덮어쓰거나 중복 등록된다
키     (Name, Type)   사전 · 등록부 · 검증 전부 이 키를 쓴다
```

### ★ 축 목록을 문서에 적지 않는다

```
이유   축 수와 목록은 차종·시점에 따라 다르다
      새 차종을 넣으면 늘어난다.  적어두면 개발자가 화이트리스트로 쓴다
      v1 에서 「39 = 8 + 31」을 본문에 박았다가 세 번 어긋났다

정본   meta_field_usage.  sync_registry 가 (Name, Type='Aspect') 로 자동 적재
검증   축 수가 아니라 필수 축 집합 포함 여부로 본다 (위 REQUIRED_FACET_AXES)
조회   현재 축 목록이 필요하면 등록부를 조회한다
```

### ★ `collect_group` — 같은 쿼리를 여러 target 이 공유한다

```
실측   G80_25T 와 G80_EV 는 ModelGroup.G80 하나의 쿼리다
      G70_25T 와 G70_20T 도 같다.  연료 조건이 없다
문제   target 별로 요청하면 같은 매물을 두 번 받는다
```

```json
"G80_25T": { "collect_group": "encar:G80", "fuel_match": ["가솔린"], ... }
"G80_EV":  { "collect_group": "encar:G80", "fuel_match": ["전기"],   ... }
```

```
수집    collect_group 단위로 1회.  target 수가 아니다
분류    받은 뒤 fuel_match · displacement 로 target 을 가른다 (STEP 46 2단 분류)
검증    expected 산출 시 collect_group 수로 센다 (5장 STEP 53)
효과    요청 수가 줄고, 같은 매물이 두 target 에 중복 적재되지 않는다
```

```
★ facet 도 collect_group 단위다
  「G80_EV 의 facet」은 존재하지 않는다.  G80 전체의 facet 이다
  → 이것을 EV 근거로 쓰면 안 된다 (7장 STEP 79 실사고)
```

### 사전으로 쓰는 축

| 축 | 용도 | 요청 |
|---|---|---|
| `Options` | **3자리 코드 → 옵션명.** 전 차종 공통 · 코드↔이름 충돌 없음 | 미지정 |
| `JatoOptions` | 4~5자리 패키지. **일부 제조사에만 값이 있다** | 미지정 |

```
★ options.etc 는 코드가 아니라 자유 텍스트다
  '20인치인덕션휠 민테리어 블랙앤화이트' · '앞바퀴 타이어 컨티넨탈>던롭 교체'
금지   etc 를 dict_option_code 에 넣는 것.  사전이 오염된다
금지   etc 를 옵션 판정 근거로 쓰는 것
용도   display_only
검증   V4-20  dict_option_code 에 공백·한글 문장이 없는가
```
| `FuelType` | 연료 열거값. 완전일치 사전 | 미지정 |
| `Color` · `SeatColor` | 색상명 + `Metadata.Expression` hex | 미지정 |
| `Condition` | Record · Inspection · Resume · InspectionDirect | 미지정 |
| `SellType` | 일반 · 렌트 · 리스 | 미지정 |
| `LeaseType` | **4값** — 렌트승계 · 운용리스 · 장기렌트 · 금융리스. **E등급 근거** | 미지정 |
| ~~`Badge`~~ | 목록에서 온다 | facet 요청 폐지 |

**나머지는 미분석이다** (8장 STEP 88). 목록은 등록부에서 조회한다.

```
용도   사전 · 열거값 확보 · 분포 참고
금지   Count 로 개별 매물의 사양을 판정          ← v1 사고
      딜러 체크값이라 양방향으로 틀린다
      실측: 모델Y 어댑티브 크루즈 미체크 다수 (전 차량 기본인데) · HUD 오체크 존재 (없는 옵션인데)
저장   응답 원문 전량 → raw_facet.  축을 골라 저장하지 않는다
```

### ★ 축 목록은 손으로 적지 않는다

```
sync_registry 가 endpoint='facet' 의 축을 (Name, Type) 키로 적재한다 (8장 STEP 87)
문서의 축 목록은 참고다.  단일 출처는 meta_field_usage 테이블이다
```

