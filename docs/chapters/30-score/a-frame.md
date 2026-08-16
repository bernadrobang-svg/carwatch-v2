## STEP 67 — 축 설계 원칙

### 축이 되는 조건

```
① 매물마다 값이 다르다        변별력
② 원문에 근거가 있다          추정 아님
③ 구매 판단에 영향을 준다      의미
④ 값의 좋고 나쁨이 명확하다    방향
```

**넷 중 하나라도 빠지면 축으로 만들지 않는다.** `display_only` 로 둔다 (8장 STEP 87).

| 예 | ① | ② | ③ | ④ | 판정 |
|---|:--:|:--:|:--:|:--:|---|
| 가격 | O | O | O | O | 축 |
| 사고 이력 | O | O | O | O | 축 |
| 점검 내부 항목(`inners`) | **X** | O | O | O | **`display_only`** — 대부분 「양호」 |
| 엔카 홈서비스 인증 | O | O | **X** | O | **`unused_by_policy`** — 배송 서비스지 차량 품질이 아니다 |
| 차주 인증 | O | O | **X** | O | `unused_by_policy` |

```
v1 오류   inners 를 축으로 만들려 했다.  전건 「양호」라 변별력이 0이다
         딜러가 팔 매물에 「불량」을 적지 않는다
```

### 변별력 판정은 8차종 통합에서 한다

```
차종 내부 값 종류 1   그 차종의 특성일 수 있다
예   콜레오스 주행거리 전건 만점 — 2024~25년식만 있어서다
금지  차종 내부만 보고 배점을 낮추는 것.  저주행 차종의 강점이 지워진다
```

---

## STEP 68 — 배점 구조

**v1 에서 마스터가 확정한 555 를 승계한다. 단 근거를 이 장에서 재확인한다.**

| 축 (Axis) | 배점 | 비중 | 하위 성분 (Component) | 근거 |
|---|---:|---:|---|---|
| `price` | 200 | 36% | — | STEP 70·71 |
| `warranty` | 100 | 18% | `general` 50 · `power` 50 | STEP 72 |
| `spec` | 90 | 16% | `hud` 20 · `hda` 20 · `sunroof` 20 · `svm` 10 · `scc` 10 · `bsd` 5 · `tinting` 5 | STEP 73~75 |
| `history` | 55 | 10% | `damage` 20 · `insurance` 15 · `rental` 20 | STEP 76~78 |
| `safety` | 40 | 7% | `diagnosis` 20 · `warranty_product` 20 | STEP 79 |
| `color` | 40 | 7% | — | STEP 80 |
| `mileage` | 30 | 5% | — | STEP 81 |
| **합** | **555** | 100% | | |

### ★ Axis 와 Component 를 구분한다

```
Axis        점수 집계 · 화면 표시 단위.  7개
Component   판정 단위.  분모 제외는 Component 단위로 일어난다
```

```
Component 이름은 축 접두를 붙이지 않는다.  전체 키가 '{axis}.{component}' 다
  O  warranty.general · history.damage · safety.diagnosis · spec.hud
  X  warranty.warranty_general       ← 축 이름이 두 번 나온다
축이 하나뿐인 것은 축 이름이 곧 키다
  price · color · mileage

result_axis 에 저장하는 것   Component 단위 (총 17행)
                          axis 컬럼에 'spec.hud' 처럼 점 표기로 계층을 남긴다
집계                      Component → Axis → 총점
분모 제외                  Component 배점 단위로 뺀다
예                       모델Y hud = -1 → spec 분모가 90 → 70
```

**압류·저당은 `safety` 점수에 넣지 않는다.** E등급 절대조건이다 (STEP 82).

```
safety 점수     safety.diagnosis 20 + safety.warranty_product 20
absolute_fail   seizing · pledge          점수 아님.  후보에서 제외
```

### 배점 비중의 근거

```
가격 36%    구매 결정에서 가장 큰 변수다.  다른 축이 좋아도 예산을 넘으면 못 산다
보증 18%    잔여 보증은 향후 수리비 리스크를 직접 줄인다.  금액으로 환산 가능한 유일한 축
사양 16%    마스터 필수 스펙(HUD·HDA)이 여기 있다.  대체 불가 항목
이력 10%    사고는 E등급 절대조건으로도 걸리므로 배점은 보조 역할
안전 7%     진단·압류.  대부분 정상이라 변별력이 낮다
색상 7%     재판매성에 영향.  값 종류가 적어 변별력 제한
주행 5%     연식과 상관이 높아 독립 기여가 작다
```

### 배점 변경 — 정수 보정

```
축 총점을 바꾸면 성분을 비율로 재배분한다.  전부 정수다
1  각 성분 = round(기존 × 새 총점 ÷ 기존 총점)
2  잔여 = 새 총점 − Σ(반올림 결과)
3  잔여를 배점이 가장 큰 성분에 더한다.  같으면 이름 순 첫 번째
4  Σ components == total_points 를 저장 전에 검산한다
```

```
금지   소수점 배점.  47.5점은 비교를 어렵게 한다
금지   0 이 되는 성분을 만드는 것.  스킵과 다르다 (13장 STEP 128)
검산   check_spec ⑦ 이 Σ components == total_points 를 본다
```

**★ 미확정 — 이 비중은 v1 승계값이다.**
**8차종 수집 완료 후 축별 실제 변별력(값 종류 · 분산)을 측정해 재검토한다** (STEP 86).

```
재검토 기준   축의 표준편차가 배점 대비 지나치게 작으면 배점을 낮춘다
             v1 실측: 주행 30점이 콜레오스에서 전건 만점 → 기여 0
금지         근거 없이 숫자를 바꾸는 것.  측정 결과와 함께 바꾼다
```

---

## STEP 69 — 판정 엔진

```python
def put(v: Verdict, axis: str, value, prio: int, src: str,
        excluded: bool = False) -> None:
    if src in BANNED_SOURCES:
        raise ValidationError(f"banned source: {src}")
    if value is None and not excluded:
        return                                   # 값도 없고 제외도 아니면 기록하지 않는다
    cur = v.prios.get(axis)
    if cur is not None:
        if cur < prio:  return                   # 강한 근거가 이긴다
        if cur == prio and v.values.get(axis) != value:
            v.conflicts.append((axis, prio, value))
            return                               # 첫 값 유지
    v.values[axis], v.prios[axis], v.sources[axis] = value, prio, src
    if excluded: v.excluded.add(axis)
    else:        v.excluded.discard(axis)
```

### ★ `excluded` 는 판정의 결과다 — 채점이 추측하지 않는다

```

### ★ `conflicts` 를 버리지 않는다 — 08-14

```
필수   판정 후 v.conflicts 가 비어 있지 않으면 기록한다
저장   result_axis_conflict (listing_id · calc_version · axis · prio · value · source)
필수   화면 · L1 리포트에 「같은 근거 두 값」으로 낸다
근거   실측 08-14.  구조는 있는데 아무도 읽지 않았다.  조용히 사라진다
      같은 우선순위에서 다른 값이 나온 것은 규칙이 겹쳤다는 뜻이다.
      첫 값을 유지하는 것은 임시 조치이고, 겹친 규칙을 고쳐야 한다
금지   충돌을 무시하고 넘어가는 것 — v1 의 사고가 전부 그렇게 시작했다
검산   V3-35  conflicts 가 있는 매물이 기록되는가
      V3-36  conflicts 건수가 임계를 넘으면 warn (규칙이 겹쳤다는 신호)
```

```
★ 충돌이 나면 판정을 멈추지는 않는다
근거   첫 값 유지가 결정적이라 결과는 재현된다.
      다만 「왜 두 값이 나왔나」를 사람이 봐야 한다.  그래서 기록이다
```
금지   채점 단계에서 value is None 을 보고 분모를 줄이는 것 (STEP 83)
필수   판정기가 「이 차종에 없는 사양이다」를 알고 excluded=True 로 기록한다

put(v,"spec.hud",     -1,  1, "spec_table", excluded=True)   모델Y HUD
put(v,"spec.tinting", None,4, "unknown",    excluded=True)   언급 없음
put(v,"spec.sunroof",  0,  2, "installed")                   미장착.  제외 아님
```

### 우선순위 4단

```
prio 1   제조사 사양 · 사이트 코드값     SPEC_DEFAULT_ON · RANK_* · displacement
prio 2   매물 실측                     options.standard/choice · 점검 결과 · 이력
prio 3   전용 판정기                   classify_hud · classify_hda
prio 4   키워드 · 문자열                contents.text · 트림명
```

```
불변식   호출 순서를 뒤섞어도 결과가 같다 (0장 STEP 7-①)
검증     표본 100건에 셔플 시험 (6장 V3-11)
```

### 금지 근거

```python
BANNED_SOURCES = {
    "catalog_full_list",   # 모델 전체 옵션 목록 — 매물 장착이 아니다
    "facet_count",         # 집계 — 매물 단위 사실이 아니다
    "record_fuel",         # API 별 표기 상이 — 분류에 쓰면 안 된다
    "part_name_string",    # 부위명 문자열 — 표기 흔들림에 무너진다
}
```

**주석이 아니라 코드가 막는다.** v1 은 넷 다 실제로 사고를 냈다.

---



---

## ★★★ 분모는 고정이다 — 08-16

**마스터 지적 — 「못 찾은 것은 니 사정이지. 왜 평가를 왜곡하니」**

```
지금까지
  축을 못 보면 분모에서 뺐다
  → 못 볼수록 비율이 올라간다
  → 못 찾을수록 좋은 등급을 받는다
★ 우리가 못 받은 것을 그 매물의 장점으로 만들었다
```

```
실측 08-16
  330/350 = 94.3%  →  S
  330/555 = 59.5%  →  D
  같은 차가 분모에 따라 등급이 갈린다
```

### 규격

```
필수   분모는 만점 그대로다.  555 다.  예외 없다
필수   못 본 축은 0점이다
       ★ 「우리가 못 받았다」는 그 차의 사정이 아니라 우리 사정이다
         그것으로 평가를 바꾸지 않는다
필수   왜 0점인지는 화면에 낸다 — 사람이 판단할 재료다
       missing               우리가 못 받았다
       no_mention            원문이 말하지 않았다
       expected_unavailable  원래 없는 것이다
필수   「확인 못 한 것 N점」을 함께 낸다
       「555점 중 330점.  205점은 확인하지 못했습니다」
       ★ 그러면 사람이 「정보가 부족한 차구나」를 안다
금지   분모를 줄이는 것.  어떤 사유로도
금지   excluded 를 분모 조정에 쓰는 것
       ★ excluded 는 「왜 0점인가」의 사유로만 남긴다
검산   V3-41  전 매물의 분모가 만점과 같은가
       ★ 하나라도 다르면 fatal
```

```
★ 이것이 뜻하는 것
  정보가 적은 매물은 낮은 점수를 받는다.  그것이 맞다
  「모르는 차」와 「좋은 차」는 다르다
  판매자가 정보를 안 주는 것도 그 매물의 성질이다
★ 등급이 전반적으로 내려간다.  그것도 맞다
  지금 등급이 부풀려져 있었을 뿐이다
필수   등급 경계(S · A · B …)를 다시 잡는다
       ★ 분모가 바뀌면 경계도 바뀌어야 한다.  실측으로 정한다
```

---

## ★ 차종 특성상 받을 수 없는 축 — 08-16 미확정

```
예   전기차에 엔진보증 · 디젤에 LPG 관련 축
```

```
★ 이것도 0점으로 하면 그 차종이 통째로 불리해진다
★ 그렇다고 분모를 줄이면 위 규격을 어긴다
미확정   배점 설계를 차종별로 둘 것인가
        아니면 전 차종 공통 축만 쓸 것인가
필수    정해질 때까지는 0점으로 둔다.  분모를 줄이지 않는다
```
