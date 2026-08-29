## STEP 79 — 안전  ★ 배점은 `f-table` 5장-2a

```
version  SPEC-2026.08.29-r931
follows  ★ 정본 — 배점의 원천은 `config/scoring.json`
sources  실측 08-22
checks   S46-38 · S46-39
```


### 구성

```
진단 20 + 보증상품 20
```

### 근거 우선순위

```
1  차종 상품 구조         전기차 보증상품 부재 → -1
2  advertisement.diagnosisCar       엔카진단 여부
3  view.encarDiagnosis              진단 등급 (-1 · 1 · 2)
4  advertisement.encarPassCategoryType   진단 통과 판정 (CLEAR 등)
5  목록 Trust                       엔카보증 가입 여부
```

### 진단 — 두 축이 다르다

```
diagnosisCar / ServiceMark   「진단을 받았나」
encarPassCategoryType        「통과했나」
```

**「받고 통과했나」가 실제 품질 신호다.** v1 은 「받았나」 하나로만 매겼다.

```
★ 미확정   encarPassCategoryType 의 값 종류가 CLEAR 1건만 관측됐다
          진단 API 원문 0건이라 세분화 불가 (STEP 86)
현행       diagnosis_car 0/1 로 판정.  세분화는 원문 확보 후
```

### 전기차 보증상품 `−1` ★ 2026-08-09 근거 재정의

**근거 필드를 facet 에서 매물 단위 원문으로 교체한다. 대상은 4종이 맞다.**

```
초판 근거   facet Trust 의 0 건수를 인용했다
문제 ①     0 인 것은 Warranty 가 아니라 ExtendWarranty 였다
문제 ②     G80_EV · GV70_EV facet 은 EV 로 좁혀지지 않았다
          BreadCrumbs 가 ModelGroup.G80 / GV70 뿐이고 연료 조건이 없다
문제 ③     애초에 facet 은 BANNED_SOURCES 다.  근거로 쓴 것 자체가 위반이었다
```

### 매물 단위 실측 — `advertisement`

```
내연 차종   deemedExtendWarranty 가 상당수 채워진다
전기 4종   extendWarranty · deemedExtendWarranty 두 필드 모두 전건 0
          MODEL_Y · GV60 · G80_EV · GV70_EV
          그 조건 모집단 전수 확인 (0장 STEP 5.2a)
```

**착수 시 재확인한다.** 전기차 상품 구조가 바뀌면 이 판정도 바뀐다.

**표본** — `detail_ev_tesla` 의 `extendWarranty` · `deemedExtendWarranty` 가 둘 다 `false` 다.
`detail_gasoline_genesis` 와 대조하면 차이가 보인다.

### 확정 — `−1` 대상 4종

| 차종 | 판정 | 근거 |
|---|---|---|
| `MODEL_Y` · `GV60` · `G80_EV` · `GV70_EV` | **`−1`** | `extendWarranty` · `deemedExtendWarranty` 매물 전건 0 |

```
축 정의   safety.warranty_product 는
         advertisement.extendWarranty + deemedExtendWarranty 를 본다
         facet Trust 를 근거로 쓰지 않는다 (BANNED_SOURCES)
결과      내연 20 + 20 = 40 (분모 40)
         전기 20 + (-1)       (분모 20)
```

**`Warranty`(엔카 기본 보증)는 전기차에도 있다. `-1` 의 근거가 아니다.**

### ★ facet 을 근거로 쓸 때의 함정

```
facet 은 그 쿼리의 집계다.  쿼리가 무엇을 담았는지 확인하지 않으면 오독한다
필수   BreadCrumbs 를 함께 저장하고, 쿼리 조건을 리포트에 표시한다
금지   target_key 이름만 보고 그 쿼리가 그 차종만 담았다고 가정하는 것
```

**`G80_25T` 와 `G80_EV` 는 같은 `ModelGroup.G80` 쿼리다.**
**연료로 좁히려면 `q` 에 `FuelType` 조건이 들어가야 한다** (2장 STEP 17).

### 압류 · 저당

```
seizingCount > 0  or  pledgeCount > 0   →  점수가 아니라 E등급 절대조건 (STEP 82)
```

---

## STEP 80 [판정] — 색상  ★ 배점은 `f-table` 5장-2a

```
목적    재판매성을 본다.  선호 색상은 되팔 때 유리하다
원천    상세 A spec.colorName · 목록 Color · facet Metadata.Expression (hex)
값규칙  색상 미확보 시 NULL + excluded.  0 점이 아니다
근거    hex 는 표기 흔들림이 없어 색상명 문자열보다 정확하다
금지    유료 색상 금액을 점수에 넣는 것.  참조만 한다
검산    값 종류가 2 이하이면 변별력 경고 (V3-04)
```

### 목적

```
재판매성.  선호 색상은 되팔 때 유리하고 기피 색상은 값이 떨어진다.
```

### 근거 우선순위

```
1  상세 A spec.colorName             원천 (P2 — 개별 차량 페이지)
2  목록 Color                        상세 미확보 시
보조 facet Color 의 Metadata.Expression   hex "#ffffff;#ffffff"
```

**hex 를 색상명 문자열보다 우선한다.** 표기 흔들림이 없다.

### 등급 — 실측 분포 기반

**재판매성은 「흔한가」로 근사한다. 흔한 색이 되팔기 쉽다.**

| 등급 | 색상 | 점수 | 근거 |
|---|---|---:|---|
| **선호** | 흰색 · 검정색 · 쥐색 | 40 | 상위 3색이 전체의 84% |
| **중립** | 청색 · 은회색 · 은색 | 25 | 92~96% 구간 |
| **기피** | 그 외 전량 | 10 | 각 1% 미만. 되팔 때 대상이 좁다 |

```
실측 분포   흰색 38.0% · 검정 29.4% · 쥐색 16.3%  →  누적 83.7%
           청색 8.5% · 은회색 2.6% · 은색 1.3%    →  누적 96.1%
           나머지 24색이 3.9%
```

```
★ 0 점을 주지 않는다.  기피색도 차의 가치를 없애지 않는다
  낮은 점수는 「이 축에서 손해」이지 「가치 없음」이 아니다
설정   config.scoring.axis_rules.color.grade_points
       마스터가 선호 색을 바꾸면 이 목록만 고친다
근거   분포는 v1 관측이다.  등급 구성이 정책이고, 분포는 그 근거다
```

### 내장 색상 — 별도 축으로 두지 않는다

```
실측   검정 41% · 갈색 33.5% · 베이지 13.2%  →  3색이 88%
판정   외장 등급에 흡수한다.  별도 배점을 두지 않는다
근거   내장은 사진으로 확인되고, 외장만큼 재판매성을 가르지 않는다
표시   화면에는 낸다 (color_int_raw · color_int_hex)
```

```
방식   위 3등급.  hex 로 판정하고 색상명은 표시용
유료   카탈로그 가격으로 참조만.  점수에 넣지 않는다
```

### 변별력

```
콜레오스 30/40 · 값 4종
색상은 원래 값 종류가 적다.  흰색·검정·회색이 대부분이고 그것이 실제 시장이다
차종 간에는 차이가 난다 — 모델Y 는 흰색 비중이 압도적
재검토   8차종 통합 후 (STEP 86)
```

---

## STEP 81 [판정] — 주행거리  ★ 배점은 `f-table` 5장-2a

```
목적    주행이 적을수록 남은 수명이 길다.  연식과 함께 차량 소모를 본다
원천    목록 Mileage · 상세 A spec.mileage · 점검부 master.detail.mileage
값규칙  주행 불명은 0 점이다.  excluded 가 아니다
근거    전 매물에 있어야 하는 값이라, 없으면 그것이 결함 신호다
금지    차종 내부 변별력이 0 이라는 이유로 배점을 낮추는 것
검산    점검부 주행 < 이전 관측 주행이면 조작 경고 (STEP 82d)
```

### 근거 우선순위

```
1  목록 Mileage
2  상세 A spec.mileage
검증 점검부 master.detail.mileage 와 대조.  불일치 시 로그
```

### 배점

| 주행거리 | 점수 |
|---|---:|
| 4만 이하 | 30 |
| 4만~10만 | 선형 |
| 10만 초과 | 0 |
| 불명 | 0 |

### 근거 — 실측 분포

```
0~2만    914      2~4만    889      4~6만    960
6~8만    764      8~10만   549      10~12만  288
12만+    356
```

```
4만 만점    전체의 38% 가 4만 이하.  「저주행」의 실질 기준선
10만 0점    12% 만 10만 초과.  이 구간은 가격이 이미 크게 낮다
근거        국내 연 15,000km 기준 4만km = 약 2.7년.  보증 잔여와 겹치는 구간
```

### 변별력 경고

```
연식이 좁은 차종은 전건 만점이 나온다 (콜레오스 30/30 · 값 8종)
결함이 아니다.  그 차종이 실제로 저주행이다
금지   차종 내부 변별력 0 을 이유로 배점을 낮추는 것
      저주행 차종의 실제 강점이 지워진다
재검토  8차종 통합 분포에서 판단 (STEP 86)
```

---

