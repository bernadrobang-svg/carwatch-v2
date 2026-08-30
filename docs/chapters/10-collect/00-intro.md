# 2장. 수집 정의 (STEP 16–27)

```
version  SPEC-2026.08.29-r994
follows  `docs/chapters/30-score/f-table.md`
sources  실측 08-22
checks   S46-38 · S46-39
```


## 2장 정의서

**본 장에서 확정하는 구조체·함수·상수. 로직보다 먼저 고정한다.**

## 구조체

```python
@dataclass(frozen=True)
class Request:
    method: str                  # 'GET'
    url: str
    headers: dict[str, str]
    timeout_sec: float

@dataclass(frozen=True)
class EndpointSpec:
    kind: str                    # 'list'·'detail'·'inspection'·'record'·'diagnosis'·'catalog'·'facet'
    scope: str                   # 'target'·'listing'·'model'
    required_keys: list[str]     # 라벨↔내용 검증
    root_type: str               # 'object'·'array'
    per_call: str                # 무엇 하나당 1회인가

@dataclass(frozen=True)
class FetchResult:
    kind: str
    source_id: str | None
    status: str                  # ok·empty·not_found·error
    raw: dict | list | None
    http_code: int | None
    error: str | None
    fetched_at: datetime

@dataclass(frozen=True)
class TargetSpec:
    target_key: str              # 'KOLEOS_HEV'
    label: str
    site_query: dict             # 사이트별 쿼리 재료. 어댑터가 해석
```

## 함수

| 이름 | 입력 | 출력 | 목적 |
|---|---|---|---|
| `SiteAdapter.list_url` | `TargetSpec, page:int` | `Request` | 목록 요청 조립 |
| `SiteAdapter.detail_urls` | `source_id:str` | `list[Request]` | 매물당 4종 요청 |
| `SiteAdapter.facet_urls` | `TargetSpec` | `list[Request]` | facet 1요청 (축 미지정) |
| `build_q` | `site_query:dict` | `str` | `q` 문자열 조립 (STEP 17a) |

```
★ 요청 조립은 SiteAdapter 의 메서드다 (1장 STEP 11)
  별도 build_* 함수를 두지 않는다.  두면 로직이 갈라진다
  runner 는 어댑터에 위임한다
```
| `build_catalog_request` | `jato_vehicle_id:str` | `Request` | 모델 옵션 카탈로그 |
| `fetch` | `Request, Fetcher` | `FetchResult` | 획득만. 파싱 안 함 |
| `verify_shape` | `FetchResult, EndpointSpec` | `bool` | 라벨↔내용 검증 |
| `save_raw` | `FetchResult` | `None` | RAW 적재 |

**`fetch` 는 전역 상태를 쓰지 않는다. 반환값에 `raw` 를 담는다** (0장 STEP 8-④).

## 상수

```
타임아웃 · 간격 · 재시도는 config/endpoints.json 이다.  코드 상수가 아니다
근거   STEP 6 판별 질문 — 「바꾸면 정책이 바뀌는가」.  타임아웃은 정책이다
```

### ★ 상수 등록 — 형태는 검사기가, 성격은 사람이

```
검사기 (V4-13)   모듈 최상위 · 대문자 · 스칼라이면 통과시킨다
                이름 목록을 검사기가 들고 있지 않는다
V4-17           그 이름이 아래 표에 있는가 · 성격이 「정책」이 아닌가
```

```
근거   예외 목록을 손으로 늘리면, 늘리는 김에 통과시키게 된다
      검사기가 「무엇이 허용인가」를 알아야 하는 구조가 문제다
      → 형태만 보게 하고 판단은 표로 옮긴다
```

### ★ 성격이 「정책」이면 상수표에 못 넣는다

| 성격 | 뜻 | 예 |
|---|---|---|
| 환산 | 바뀌지 않는다 | `MS_PER_SEC` |
| 형식 | 규격이 정한다 | `VIN_LENGTH` 17 · `HASH_HEX_LEN` 16 |
| 구현 | 바꾸면 알고리즘 교체다 | `SECRET_BYTES` · `KEY_BYTES` |
| **정책** | **마스터가 바꿀 만하다** | **→ `config` 로 간다** |

```
판별   「이 값을 바꿀 이유가 생기면 코드를 고치는가, 설정을 고치는가」
      설정  →  정책.  상수표에 못 넣는다

예     SESSION_HOURS 12       → config.admin.session_hours
      「12시간이 짧다」고 느끼면 바꾼다
      HASH_ROUNDS            → config.admin.hash_rounds
      하드웨어가 빨라지면 올린다.  PBKDF2 는 라운드를 해시에 함께 저장하므로
      바꿔도 옛 해시가 깨지지 않는다.  바꿀 수 있으면 정책이다

반례   COEFFICIENT_SANE_MAX 1.20   대문자지만 임계값이다
      이름만 붙여 상수로 우회하는 것을 이 판별이 막는다
```

### 상수 · 예약어 — 세 갈래로 나눈다

**대문자 표기가 곧 코드 상수는 아니다. 어디에 사는지가 다르다.**

| 식별자 | 실제 위치 | 성격 |
|---|---|---|
| `BANNED_SOURCES` | **코드 상수** | 금지 근거 4종. 도메인 규칙이라 코드가 맞다 (STEP 6) |
| `REQUIRED_FACET_AXES` | **코드 상수** | 「이것만은 반드시 있어야 한다」는 규칙 |
| `SPEC_DEFAULT_ON` · `SPEC_DEFAULT_OFF` | **`config/targets.json`** | 차종이 늘면 바뀐다. 정책값 |
| `TINT_KEYWORDS` | **`config/dictionaries/`** | **사전이다. RAW·운영에서 갱신된다** (4장 STEP 42) |
| `AXIS_LABELS` · `GRADE_LABELS` · `VALUE_LABELS` · `STATUS_LABELS` | **`config/labels.json`** | 화면 문구 |

### 수치 상수 — `V4-17` 검사 대상

**`V4-13` 은 형태만 본다. 이 표에 없으면 `V4-17` 이 잡는다.**

| 이름 | 값 | 성격 | 근거 |
|---|---|---|---|
| `PRIO_MANUFACTURER` · `PRIO_OBSERVED` · `PRIO_CLASSIFIER` · `PRIO_KEYWORD` | 1 · 2 · 3 · 4 | **도메인 규칙** | 근거 우선순위 (1장 STEP 13) |
| `HTTP_OK_FLOOR` · `HTTP_REDIRECT_FLOOR` · `HTTP_NOT_FOUND` | 200 · 300 · 404 | 형식 | HTTP 규격 |
| `VIN_LENGTH` | 17 | 형식 | VIN 표준 (3장 STEP 30) |
| `HASH_HEX_LEN` | 16 | 형식 | `plate_hash` 자릿수 |
| `KEY_BYTES` | 32 | 구현 | HMAC 키 길이 |
| `TEMP_SECRET_BYTES` | 9 | 구현 | 임시 비밀번호 |
| `FILE_MODE_OWNER_ONLY` | `0o600` | 형식 | `secrets/` 권한 |
| `FLOAT_EPSILON` | `1e-9` | 형식 | 부동소수 비교 |
| `PROGRESS_EVERY` | 20 | 형식 | 진행 표시 주기 |
| `PROGRESS_DETAIL_WIDTH` | 44 | 형식 | 진행 줄 문구 폭 |
| `PROGRESS_LINE_PAD` | 20 | 형식 | 덮어쓰기 여백 |
| `{단위}_PER_{단위}` | — | 환산 | 이름 규칙으로 자동 통과 |

```
★ 「정책」 성격은 이 표에 없다.  전부 config 다
  session_hours · hash_rounds · page_size · 임계값 · 배점
필수   새 수치 상수를 만들면 이 표에 이름과 성격을 추가한다
      성격이 「정책」이면 표가 아니라 config 로 간다
검증   V4-17  코드의 수치 상수가 전건 이 표에 있는가
```

```
★ 문자열 상수는 검사하지 않는다
  AXIS = "color" · FAIL_FRAME 같은 것은 도메인 이름이지 임계값이 아니다
```

### ★ 같은 값이 코드와 `config` 에 함께 있으면 안 된다

```
사고   PAGE_SIZE_DEFAULT 가 코드에 있고 config.report.page_size 에도 있었다
      두 곳이 갈리면 화면마다 다른 값을 쓴다.  어느 쪽이 정본인지 모른다
```

```
필수   config 에 있는 키와 같은 뜻의 코드 상수를 만들지 않는다
확인   새 상수를 만들기 전에 STEP 6 config 표를 본다
검증   V4-18  상수표의 이름과 config 키가 같은 뜻으로 겹치지 않는가
      기계로 완전히 잡기 어렵다.  표를 볼 때 사람이 함께 본다
```

```
★ 대문자로 쓰되 코드 상수가 아닌 것이 있다
  문서에서 대문자로 표기하는 이유는 「고정된 집합」임을 드러내기 위해서다
  실제 저장 위치는 위 표가 정본이다
```

### 단위 환산 상수 — 표에 등록하지 않는다

```
MS_PER_SEC = 1000 · SECONDS_PER_DAY = 86400 · KM_PER_MONTH = 1250 …
```

```
성격   물리적 환산이다.  정책도 도메인 규칙도 아니다
      바뀌지 않는다.  1초는 언제나 1000밀리초다
위치   쓰는 모듈의 최상위.  config 로 빼지 않는다
등록   상수표에 넣지 않는다.  표가 환산으로 채워지면 진짜 상수가 묻힌다
```

```
★ KM_PER_MONTH 1250 은 환산이 아니다
  「연 15,000km 로 본다」는 정책이다  →  config/scoring.json (STEP 72)
판별   그 숫자를 마스터가 바꿀 수 있는가
      바꿀 수 있다  →  config
      바꿀 수 없다  →  환산 상수.  코드에 둔다
```

```
필수   새 식별자를 만들면 이 표에 위치와 함께 추가한다
      단 단위 환산은 제외한다
금지   임계값 · 배점 · 세율 · 키워드를 코드 상수로 두는 것 (V4-13)
검증   V4-17  이 표에 없는 대문자 식별자가 코드에 있는가
      단위 환산 상수는 이름이 {단위}_PER_{단위} 형태면 통과시킨다
```

**간격 · 재시도 횟수는 상수가 아니라 정책값이다.** `config/endpoints.json` 에 둔다.

```
404   재시도하지 않는다.  실패가 아니라 not_found 결과다
```

---

## STEP 15a [규격] — 계층 의존 ★

```
목적    표현 계층이 저장 계층의 타입에 의존하지 않게 한다
원천    import 문
입력    소스 트리
출력    위반 목록
값규칙  타입(대문자 이름) import 는 금지.  함수 호출은 허용
근거    화면이 데이터를 읽는 것은 정상이다.  DTO 정의를 저장 계층에서 받는 것이 문제다
금지    report/ 가 store/ 에서 대문자 이름을 import 하는 것
검산    S15 — 되돌려서 실패하는지 확인한다
```

### 판별 — 넘는 것만 `contracts.py` 로

```
실사고   Account 가 store/admin.py 에 있어
        report/screens/build.py 가 store.admin 을 import 했다
        require_role 도 I/O 없는 순수 판정인데 같이 끌려갔다
```

| DTO | 쓰이는 계층 | 위치 |
|---|---|---|
| `Account` · `require_role` · `ROLE_*` | 화면 · 관리자 · 추적 | **`contracts.py`** |
| `ConfigChange` · `QueryLog` · `QueryResult` · `ApiSnapshot` · `DevRequest` · `RecalcJob` · `ScoringPreview` | 저장 계층 안 | `store/` 유지 |

```
★ 지금 넘지 않는 것을 미리 옮기지 않는다
  contracts.py 가 13장 저장 구조체로 채워진다
판별   기계로 뽑는다 — 어느 계층이 그 이름을 import 하는가
```

### 허용 · 금지

```
허용   from store.admin import running_job     함수 호출.  DB 조회다
금지   from store.admin import Account         타입 정의
      from store.admin import ROLE_ADMIN      상수 정의
```

### ★ 의존 방향 — 아래로만

```
web/  →  report/  →  score/  →  analyze/  →  parse/  →  store/
adapters/  →  collect/  →  store/                →  contracts · errors
```

| 층 | 부를 수 있는 것 | 못 부르는 것 |
|---|---|---|
| `contracts` · `errors` | (없음) | 전부 |
| `store` | `contracts` · `errors` | 그 위 전부 |
| `parse` | `store` · 아래 | `analyze` 이상 |
| **`analyze`** | **`contracts` · `errors` 만** | **`store` 포함 전부** ★ |
| `score` | `analyze` · 아래 | `report` 이상 |
| `report` | `score` · 아래 | `web` |
| `web` | `report` · `store`(조회) | `parse` · `analyze` 직접 |
| `collect` | `adapters` · `store` | `analyze` 이상 |
| `validate` | 전부 (읽기만) | — |

```
★ analyze 만 예외다.  store 도 못 부른다
근거   판정은 순수 함수다.  DB 를 모른다 (0장 STEP 2)
      조회는 호출자가 하고 결과를 인자로 넘긴다 (7장 STEP 82e)
검증   S11 이 이것을 본다
```

### 같은 층끼리

```
금지   parse/encar/detail.py 가 parse/encar/record.py 를 부르는 것
필수   공통이 필요하면 parse/common.py 로 내린다
근거   상호 참조는 순환이 되기 쉽고 어느 쪽이 먼저인지 불명확하다
검증   V4-22  역방향 · 순환 import 가 없는가
```

### 진입점

```
run.py           유일한 진입점.  인자를 해석한다
                 ★ 08-16 — 사람이 쓰는 것은 화면이다.  진입점은 화면이 부른다
tools/*.py       독립 실행.  run.py 를 부르지 않는다
web/server.py    run.py web 이 부른다.  직접 실행하지 않는다
```

```
필수   모듈에 실행 코드를 두지 않는다.  import 만으로 아무 일도 안 일어난다
       if __name__ == "__main__": 는 run.py · tools/ 에만
근거   import 시 부작용이 있으면 시험이 예측 불가능해진다
검증   V4-23  모듈 최상위에 I/O · 부작용이 없는가
```

---



---

# ★★★ 카탈로그는 조합 전수를 받는다 — 08-17

**마스터 지적 — 「카탈로그가 왜 없어. 수집하다가 버린 거겠지. 가중치 미반영에」**

## 실측

```
카탈로그   08-16 21건 → 전 차종 수집 후 147건
매물      3,470건
★ 카탈로그는 「모델·연식·트림」 조합 단위다
★ 그 조합이 몇 개인지를 센 적이 없다
```

```
★ 그래서 옵션 축이 통째로 0점인 매물이 많다
★ 그런데 화면은 「확인율 100%」라고 한다 (개정 325)
```

## 규격

```
필수   필요한 조합을 먼저 센다
       core_listing 에서 (model_cd, form_year, trim_code) 를 distinct 로
       ★ 그 수가 받아야 할 카탈로그 수다
필수   전수를 받는다.  매물에서 나온 것만 받지 않는다
필수   못 받은 조합을 기록한다 — 왜 못 받았는지
       not_called    안 불렀다        ★ 우리 잘못이다
       http_404      그 조합이 없다
       http_error    다른 오류
       parse_failed  받았는데 못 읽었다
필수   매칭 키를 검사한다
       ★ 받았는데 매물과 안 이어지면 받은 것이 아니다
       카탈로그 147건 중 매물에 이어진 것이 몇 건인가
필수   조합별 매물 수를 함께 낸다
       ★ 매물 300건이 걸린 조합과 1건짜리는 급한 정도가 다르다
금지   조합 수를 모르는 채로 「카탈로그 147건」이라고만 하는 것
검산   V1-23  필요한 조합 대비 받은 비율이 나오는가
       V1-24  받은 카탈로그가 매물과 이어지는가
```

---

# ★ 못 받은 것이 점수에 미치는 영향을 낸다 — 08-17

```
필수   축이 근거 없어 0점일 때 그 배점을 「미확인 점수」로 합산한다
       「미확인 30점 — 카탈로그를 못 받았습니다」
필수   미확인 점수가 큰 순으로 관리 화면에 낸다
       ★ 「옵션 축 미확인이 2,900건 · 87,000점」
         → 카탈로그를 받으면 그만큼이 살아난다
필수   무엇을 받으면 무엇이 살아나는지 잇는다
       카탈로그 → 옵션 30 · 사양 축
       엔카진단 → ~~우수등급 30~~ ★ 폐기 — ⑤ 사이트 보증 50 (개정 351 · 392)
       record  → 사고 70 · 보험 30 · 용도 25
       ★ 「무엇을 먼저 받아야 하나」가 이 표에서 나온다
검산   V3-67  미확인 점수가 집계되는가
```

```
★ 마스터 지적의 뒷부분 — 「가중치 미반영에」
  30점짜리 축이 통째로 빠졌는데 화면이 그것을 안 말한다
  ★ 배점이 큰 축이 빠지면 크게 말해야 한다
```

---

# ★★★★★ 08-29 수집 방식 리포트 (마스터 지시)

```
★★★ 마스터 — 「★ **KB 는 목록을 받고 그걸 기반으로 상세를 받는 구조인가,
   ★ 아니면 모든 걸 다 통으로 받는 구조인가?  ★ 엔카처럼 목록을 받고 그 목록으로 상세를 받는지 …
   ★ 그 구조와 방식을 먼저 확인해 주고, ★ 제대로 지켜지는지, ★ 과연 효율적인지 …
   ★ 쓸데없이 모든 데이터를 받아서 스팸이 되는 경우도 있잖아.  ★ 리포트를 해 줘**」
```

## ★ ① 열한 사이트의 구조 [실측 코드 08-29]

| 사이트 | 구조 | 목록에서 좁히나 | 받는 양 → 우리 대상 | 상세 |
|---|---|---|---|---|
| ★ **KB차차차** | ★ **목록 → 상세** (엔카와 같다) | ○ 31묶음 (제조사·차종·세대) | 4,320 → **4,320** | 건별 · **회차당 10건** |
| 엔카 | 목록 → 상세 | ○ facet | — | 건별 |
| K카 | ★ **목록 통으로 → 대상만 상세** | ✘ 조건을 안 받는다 | **487 → 105** | 105만 |
| 보배드림 | 목록 → 대상만 상세 | ○ `maker_no` 열 | **1,861 → 222** | 222만 |
| 헤이딜러 | 목록 → 상세 | ○ 차종 해시 | 199 → 199 | 전건 |
| 현대인증 | 목록 → 상세 | ○ `mdlGrpList`＋`fuelList` | 1,143 → **198** | 198만 |
| ★ **리본카** | ★ **사이트맵 통으로 → 전건 상세** | ★ **✘ 못 좁힌다** | ★ **1,082 → 모른다** | ★ **1,082 전건** |
| 볼보 셀렉트 | 목록만 | ✘ (슬러그로 거른다) | 223 → 149 | ★ **안 받는다** |
| BMW | 목록만 | ✘ | 364 → 23 | ★ **안 받는다** |
| 렉서스 | 목록만 | ✘ | 74 → 53 | ★ **안 받는다** |

## ★★ ② 스팸이 되는 자리 — ★ **둘이다**

```
★★★ ★ **리본카** — ★ 목록(사이트맵)에 ★ **차종이 없다**.  ★ 그래서 ★ **1,082건 상세를 다 받아야**
   ★ ★ 그중 우리 차종이 몇인지 안다.  ★ 건당 1초 = ★ **18분** · ★ 버리는 것이 ★ 90% 넘는다
   ★ ★ 이것이 ★ 마스터께서 말씀하신 ★ **「쓸데없이 모든 데이터를 받아 스팸이 되는」** 자리다
   ★ 가이드 안 — ★ 사이트맵 `<loc>` 에 ★ **`lastmod`** 가 있으면 ★ **바뀐 것만** 받는다.  ★ 아직 안 쟀다

★★ ★ **KB** — ★ 목록은 잘 좁힌다(31묶음).  ★ 그런데 ★ **4,320건 상세를 다 받으려 한다**
   ★ ★ 회차당 10건이라 ★ **432회차**다.  ★ 그 근거였던 봇 차단이 ★ 08-29 에 0건이다
   ★ 가이드 안 — ★ **화면에 뜨는 것부터** 받는다.  ★ 값·주행·연식은 ★ **목록에 이미 있다**

★ ★ 반대로 ★ **볼보·BMW·렉서스는 상세를 아예 안 받는다** — ★ 덜 받아서 문제다.
   ★ ★ 볼보 상세에 ★ 성능·점검·사고가 ★ 5/5 있다 (개정 887)
```

## ★★★ ③ 지금 원문은 ★ **파일이 아니라 DB 에 넣는다**

```
★ `store/raw.save_site_raw` → ★ `raw_response` 테이블 (★ zlib 압축 · 3.6배)
★★ ★ 마스터께서 ★ 「★ **파일로 수집 후 DB 에 적재**」를 ★ 두 번 말씀하셨다 —
   ★ ★ 08-29 「KB 는 수집해서 파일로 저장 후 DB 에 넣으면서」 · ★ 오늘 「파일로 수집 후 명령을 내려」
★ ★ **지금 꼴은 그것이 아니다.**  ★ 규격을 아래로 정한다
```

## ★★★★ ④ 정한다 — ★ 파일 자리와 이름 [가이드 규격 08-29]

```
자리   raw/{site}/{endpoint}/{YYYY-MM-DD}/{source_id}.json      ★ 매물이 있는 것
       raw/{site}/{endpoint}/{YYYY-MM-DD}/page-{NNNN}.json      ★ 목록처럼 매물번호가 없는 것
       ★ 뿌리는 `config/deploy.json` 의 `work_dir` 아래 `raw/` 다.  ★ 코드에 안 박는다

이름   site      config/sites.json 의 키 그대로 (kbchachacha · kcar …)
       endpoint  list · detail · inspection · stock_list  ★ endpoints.json 의 키 그대로
       날짜      받은 날 (UTC).  ★ 하루치가 한 폴더다 — ★ 되돌리기가 쉽다
       확장자    .json  ★ HTML 도 .json 에 담는다 — `{"url":…, "status":…, "body":"…"}`

한 파일 안   {"site","endpoint","source_id","url","status","fetched_at","body"}
             ★ body 는 ★ 원문 그대로.  ★ 자르지 않는다 (P3 무손실)

지킬 것  ★ 받기 걸음은 ★ **파일만 쓴다.  ★ DB 를 안 연다** — ★ 잠금이 아예 안 생긴다
         ★ 넣기 걸음은 ★ **그 폴더를 읽어** `raw_response` ＋ `core_listing` 에 넣는다
         ★ 이미 넣은 파일은 ★ 건너뛴다 (`fetched_at` 을 `parsed_at` 과 대본다)
금지     ★ 파일을 지우는 것.  ★ 원문은 남는다 (STEP 33)
```

★ **그다음이 검증이다** — ★ 파일이 쌓이면 ★ **가이드가 그 파일을 열어 ★ 파싱이 맞는지 잰다**.
  ★ ★ 지금은 ★ DB 안에 있어 ★ 가이드가 못 본다.  ★ **그것이 오늘까지 못 잰 까닭이다**
