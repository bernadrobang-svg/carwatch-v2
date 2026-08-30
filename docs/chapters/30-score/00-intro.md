# 7장. 분석 함수 정의 (STEP 67–86)

```
version  SPEC-2026.08.29-r999
follows  ★ 정본 — 배점의 원천은 `config/scoring.json`
sources  실측 08-22
checks   S46-38 · S46-39
```


## 7장 정의서

**이 장은 「무엇을 사실로 인정하고, 그것에 왜 그 점수를 주는가」를 쓴다.**
**배점 숫자만 적으면 v1 과 같아진다. 각 축마다 근거를 함께 쓴다.**

### 구조체

```python
@dataclass(frozen=True)
class AxisSpec:
    axis: str
    max_points: int
    value_domain: tuple          # 허용 값
    excludable: bool             # -1 로 분모 제외 가능한가
    sources: list[tuple[int,str]]  # [(prio, source_name), ...]
    banned: list[str]
    rationale_ref: str           # 이 문서의 STEP 번호

@dataclass(frozen=True)
class AxisContext:
    snapshot: ListingSnapshot
    dicts: DictionarySet
    policy: ScoringPolicy        # config/scoring.json
    target: TargetSpec

@dataclass
class Verdict:
    values: dict[str, int | None]
    sources: dict[str, str]
    prios: dict[str, int]
    excluded: set[str]
    conflicts: list[tuple[str, int, int]]
```

### 함수 — 축 하나당 하나

```python
def analyze_price(ctx: AxisContext, v: Verdict) -> None: ...
def analyze_warranty(ctx: AxisContext, v: Verdict) -> None: ...
def analyze_spec(ctx: AxisContext, v: Verdict) -> None: ...
def analyze_history(ctx: AxisContext, v: Verdict) -> None: ...
def analyze_safety(ctx: AxisContext, v: Verdict) -> None: ...
def analyze_color(ctx: AxisContext, v: Verdict) -> None: ...
def analyze_mileage(ctx: AxisContext, v: Verdict) -> None: ...
```

```
공통   ctx 만 읽는다.  DB · 네트워크 · 시각 · 난수에 접근하지 않는다
      결과는 put() 으로만 기록한다.  v 를 직접 대입하지 않는다
      순수 함수다.  같은 ctx 면 같은 결과다
파일   analyze/axis/{axis}.py 하나.  한 축의 모든 규칙이 그 파일에 있다
주석   파일 상단에 STEP 번호 · 근거 · 금지 근거를 박는다
```

---

