# 1장. 아키텍처

```
version  SPEC-2026.08.29-r970
follows  `docs/chapters/30-score/f-table.md`
sources  실측 08-22
checks   S46-38 · S46-39
```


## STEP 9 — 계층 정의

```
L0  SiteAdapter      사이트별 URL · 인증 · 응답 형태 격리
                    엔카 · K카 · KB차차차 · 딜러 자체 사이트 (다중 인스턴스)
L1  Collector        원문 획득.  파싱하지 않는다
L2  RawStore         원문 무손실 저장.  삭제 금지
L3  Parser           RAW → 정규 필드.  사이트별 매핑
L4  CoreStore        사이트 무관 공통 스키마
L5  Dictionary       코드 · 열거값.  RAW 에서 생성
L6  Analyzer         축별 판정.  put(axis, value, prio, src)
L7  Scorer           배점 · 등급.  축 판정과 분리
L8  Validator        5차 검증
L9  Reporter         화면 · 리포트
```

**L1 과 L3 을 분리하는 이유** — v1 은 수집 함수가 파싱까지 했다.
그래서 파싱 규칙이 바뀔 때마다 재수집이 필요했고, 원문이 남지 않는 경로가 생겼다.
**수집은 받아서 저장만 한다. 해석은 L3 이 한다.**

**L6 과 L7 을 분리하는 이유** — 배점 변경이 판정 로직을 건드리면 안 된다.
`rescore` 는 L7 만 다시 돈다.

## STEP 10 — 데이터 흐름

```
SiteAdapter → Collector → RawStore
                              ↓
                           Parser → CoreStore
                              ↓        ↓
                        Dictionary  Analyzer → Scorer → Reporter
                                        ↑
                                   Validator (전 구간 감시)
```

**역방향 화살표가 없다.** 재처리는 RawStore 부터 다시 흐른다.

```
파싱 규칙 변경   RawStore → Parser → CoreStore → Analyzer → Scorer
판정 규칙 변경   CoreStore → Analyzer → Scorer
배점 변경       Scorer 만
```

**재수집이 필요한 경우는 둘뿐이다** — 원문이 없거나, 매물이 갱신됐을 때.

## STEP 11 — 사이트 어댑터 인터페이스

**사이트 종속 코드를 Adapter 와 Parser 매핑으로 격리한다.**
**CORE · Analyzer · Scorer 는 변경하지 않는 것이 목표다.**

```
사이트 추가 시 필요한 것
  Adapter            URL · 헤더 · 쿼리 조립
  Parser 매핑        응답 경로 → CORE 필드
  EndpointSpec       kind · required_keys · root_type
  Dictionary 매핑    사이트 코드 → CORE 열거값
  Target 매핑        사이트 차종 표현 → target_key
  사이트 전용 검증     그 사이트에만 있는 제약
```

**「어댑터 하나만 바꾸면 된다」가 아니다.** 그렇게 쓰면 개발자가 과도하게 추상화한다.
**바뀌지 않아야 하는 곳을 명시하는 것이 목적이다.**

```python
class SiteAdapter(Protocol):
    site_code: str                       # 'encar' · 'kbchachacha'

    def list_url(self, target: TargetSpec, page: int) -> Request: ...
    def detail_urls(self, source_id: str) -> list[Request]: ...
    def facet_urls(self, target: TargetSpec) -> list[Request]: ...
    def endpoint_schema(self) -> dict[str, EndpointSpec]: ...
```

```python
@dataclass(frozen=True)
class EndpointSpec:
    kind: str                 # 'list' · 'detail' · 'inspection' · 'record' ...
    required_keys: list[str]  # 라벨↔내용 검증용
    is_array: bool
```

**`required_keys` 가 STEP 4 의 형식 검증 근거다.** 어댑터가 스스로 선언한다.

## STEP 12 — 원문 획득 계약

```python
@dataclass(frozen=True)
class FetchResult:
    kind: str
    status: str          # ok / empty / not_found / error
    raw: dict | list | None
    error: str | None
```

**`raw` 는 이 호출의 응답만 담는다. 공유 변수를 쓰지 않는다.**

```python
# 금지 (v1 사고)
self.last_raw = d
save_raw(lid, "record", self.last_raw)

# 필수
res = adapter.fetch(req)
save_raw(lid, res.kind, res.raw, res.status)
```

## STEP 13 — 판정 엔진 계약

```python
@dataclass
class Verdict:
    values: dict[str, int | None]
    sources: dict[str, str]
    prios: dict[str, int]
    excluded: set[str]                    # 분모에서 뺄 축 (STEP 83)
    conflicts: list[tuple[str, int, int]]

def put(v: Verdict, axis: str, value, prio: int, src: str,
        excluded: bool = False) -> None: ...
```

```
prio 1  제조사 사양 · 사이트가 준 코드값 (RANK_* 등)
prio 2  매물 실측 (실장착 옵션 · 점검 결과)
prio 3  전용 판정기
prio 4  키워드 · 문자열 추정
```

**낮은 숫자가 이긴다. 호출 순서는 결과에 영향을 주지 않는다.**
**같은 prio 로 다른 값이 오면 `conflicts` 에 기록하고 첫 값을 유지한다.**

## STEP 14 — 금지 근거 등록

```python
BANNED_SOURCES = {
    "catalog_full_list",   # 모델 전체 옵션 목록 — 매물 장착이 아니다
    "facet_count",         # 집계값 — 매물 단위 사실이 아니다
    "record_fuel",         # API 별 표기 상이 — 분류에 쓰면 안 된다
    "part_name_string",    # 부위명 문자열 — 표기 흔들림에 무너진다
}
```

**`put()` 에 들어오면 `ValidationError` 를 던진다.** 주석이 아니라 코드가 막는다.

**`part_name_string` 이 v1 의 실사고다** — 사전이 「프론트펜더」, 원문이 「프론트 휀더(우)」여서
가장 흔한 부위 344건이 미분류였다. **엔카는 `attributes` 로 골격/외판을 코드값으로 준다.**

### 14.1 데이터 생명주기 허용·금지 매트릭스

**「금지 근거」는 전면 금지가 아니다. 계층마다 허용 여부가 다르다.**

| 데이터 | RAW 저장 | CORE 변환 | Dictionary | Analyzer | Scorer | Report |
|---|:--:|:--:|:--:|:--:|:--:|:--:|
| 목록 응답 | O | O | — | O | — | O |
| 상세 A | O | O | — | O | — | O |
| 점검부 | O | O | O (부위·상태 사전) | O | — | O |
| 이력 | O | O | — | O | — | O |
| **카탈로그 전체목록** | **O** | **O** | **O** ★ | **X** | X | O (가격 표시) |
| **facet Count** | **O** | O | **O** ★ | **X** | X | O (분포 표시) |
| 진단 | O | O | — | O | — | O |

**★ 카탈로그·facet 은 Dictionary 로는 허용된다.**

```
허용   코드 → 이름 · 가격 조회
      installed_option_names(codes)   codes 는 그 매물의 choice 만
      facet Options → 3자리 코드 사전 (전 차종 공통, 실측 확인)

금지   장착 여부 판정
      카탈로그 전체 목록을 그 매물의 장착으로 취급
      facet Count 로 개별 매물 사양을 추정
```

**「사전으로 쓰는 것」과 「근거로 쓰는 것」의 경계가 v1 에서 두 번 무너졌다.**
전면 금지로 처리하면 옵션 이름을 알 방법이 없어진다. **계층별로 나눈다.**

**판별법** — `codes` 인자가 그 매물의 것인가, 모델 전체 목록인가.
빈 `codes` 에 빈 목록을 반환하지 않으면 금지 위반이다.

## STEP 15 — 디렉터리 구조

```
carwatch_v2/
  errors.py        도메인 예외 5종 (STEP 3)
  contracts.py     Protocol · 계층 횡단 DTO (STEP 2 · 11 · 12)
                   Account · require_role 포함 — 화면·관리자·추적이 다 쓴다
  web/             routes.py · server.py · templates/ · static/   (14장)
  adapters/        encar.py · base.py
  collect/         runner.py · fetcher.py
  store/           raw.py · core.py · dict.py
  parse/           encar/  (엔드포인트별)
  analyze/         axis/   (축별) · verdict.py
  score/           scorer.py · grade.py
  validate/        v1_collect.py ~ v5_value.py
  report/          screens/ · exports/
  config/          *.json
  sql/             ddl/ · queries/
  tools/           build_dict.py · derive_mapping.py
  tests/
```

### ★ 판정에 쓰는 값은 `ListingSnapshot` 에 있어야 한다 — 08-14

```
필수   축 함수가 읽는 매물 값은 전부 ListingSnapshot 필드다
금지   target_config 에 매물 값을 담는 것.  그것은 차종 설정이다
근거   실측 08-14.  6개가 target_config 에 있었다 —
      diagnosis_car · advertisement_type · lease_rent_info ·
      usage_change_types_json · warranty_extend · warranty_deemed
      dict 에 숨기면 「어떤 값이 판정에 쓰이나」를 시그니처로 알 수 없다.
      352컬럼 Row 를 dict 하나로 바꾼 것과 같다 (STEP 1)
필수   축을 추가하려면 DTO 를 먼저 고친다
검산   V4-24  축 함수가 target_config 에서 매물 값을 읽지 않는가
```

**`analyze/axis/` 는 축 하나당 파일 하나다.** 한 축의 모든 규칙이 그 파일에 있다.
**파일 상단에 지시서 STEP 번호 · 근거 · 금지 근거를 주석으로 박는다.**

---

**0장 · 1장 종료 (STEP 1–15).**

---

