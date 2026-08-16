# 부록 C. 실물 표본 (fixtures)

**동봉 `BJY_v2_실물표본.tar.gz` 를 `tests/fixtures/` 에 푼다.**
**본문 STEP 6a 가 사용 규칙을, 아래가 표본 내용을 담는다.**

### 표본 12건 — 무엇을 고정하는가

| 파일 | 특성 | 이것이 깨지면 |
|---|---|---|
| `inspection_clean` | `outers` 0판 · **`usageChangeTypes` 렌트** | 사고와 렌트가 독립 축임이 무너짐 |
| `inspection_frame` | `RANK_B` 1 · 외판 4판 | **골격 E등급**이 외판보다 우선하지 않음 |
| `inspection_outer_swap` | 교환 5판 · 골격 없음 | 사고 20점이 0점이 되지 않음 |
| `inspection_outer_paint` | 판금/용접만 | 판금을 감점하게 됨 |
| `inspection_weld` | 「용접,절단」+「판금/용접」 | 미정의 값이 조용히 통과함 |
| `record_clean` | `accidents` 빈 배열 | 빈 배열이 NULL 로 저장됨 |
| `record_with_accident` | **`type` 3 만 1건** | **`type` 3 이 감점에 들어감** |
| `detail_ev_tesla` | `displacement` 180 · 보증 96/192000 | 전기차에 배기량 분류가 걸림 |
| `detail_gasoline_genesis` | `displacement` 2497 | 2단 확정이 안 됨 |
| `detail_hybrid_renault` | **콜레오스인데 1969 · 가솔린** | **2.0 가솔린이 `KOLEOS_HEV` 로 들어감** |
| `detail_lpg_hyundai` | `LPG(일반인 구입)` | 연료 완전일치가 깨짐 |
| `catalog` | 4자리 코드 9건 | 카탈로그 파싱이 깨짐 |

### `EXPECTED.json` — 기대값

```
파일별로 파싱 결과의 기대값이 들어 있다.  assert 에 그대로 쓴다
_core 접미사   변환 후 값 (예: firstRegistrationDate_core = 2021-06-15)
              시험이 변환 로직을 다시 구현하지 않게 하기 위한 것이다
```

```
★ 시험이 구현을 복제하면 둘 다 틀려도 통과한다
필수   변환 결과는 EXPECTED 의 _core 값과 직접 비교한다
```

### `NOTES.json` — 각 표본이 무엇을 검증하는지

```
표본을 늘릴 때 이 파일에도 한 줄 추가한다
「무엇을 고정하는 표본인가」가 없으면 나중에 지워도 아무도 모른다
```

### ★ 표본을 늘리는 기준

```
넣는다   원문 구조가 예상과 달랐던 것
        판정이 갈리는 경계 사례 (골격/외판 · type 1·2/3 · 전기/내연)
        미정의 값이 실제로 나온 것 (용접,절단)

안 넣는다  같은 구조의 반복
         「많이 넣으면 안전하다」는 오해.  시험 시간만 늘고 의미가 없다
```

```
필수   새 표본은 v1 원문 또는 실수집 원문에서 뽑는다.  손으로 만들지 않는다
금지   모의 응답을 fixtures 에 넣는 것
      모의는 tests/ 안에서 경계 조건용으로만 쓴다
```

---


---

