# 부록 E. 동봉물 전문

**이 문서 하나로 착수할 수 있게, 실행 파일과 기대값을 여기 둔다.**

```
필수   아래 코드를 파일로 저장해 쓴다.  문서에서 복사한다
      tools/check_spec.py  ·  tests/fixtures/EXPECTED.json  ·  NOTES.json
금지   문서를 파싱해 코드를 뽑는 것.  파일이 정본이다
```

---

## E-1. `tools/check_spec.py`

**문서 자체 점검 11종. 착수 전과 문서 변경 시마다 돌린다.**

```
python3 tools/check_spec.py <문서.md>      종료코드 0 통과 · 1 실패
```

### ★ 소스 전문은 이 문서에 넣지 않는다

```
이유   검사기 소스에 코드 펜스 문자가 들어 있다
      마크다운 안에 넣으면 그 문자가 블록 종료로 읽혀 잘린다
      실제로 시도했다가 검사 ①·⑪ 이 동시에 걸렸다
결론   실행 파일은 파일로 준다.  문서는 규격만 담는다
```

**동봉 `check_spec.py` 를 `tools/` 에 둔다.**

### 검사 13종 — 규격

| # | 검사 | 판정 |
|:--:|---|---|
| ① | 코드 펜스 짝수 | 미닫힘이 있으면 이후 전 블록의 렌더링이 뒤집힌다 |
| ② | STEP 유형별 필수 항목 | 헤딩의 `[판정]`·`[규격]`·`[수집]` 표기 → 첫 코드 블록의 줄첫머리 라벨 |
| ③ | 참조 무결성 | `STEP N` 참조가 실재 헤딩을 가리키는가 |
| ④ | 구조체 정의 | 필드 타입 · 반환 화살표 · **함수표 「출력」 열** |
| ⑤ | `config` 대조 | 본문 참조 ↔ STEP 6 표 ↔ 부록 B 예시 |
| ⑥ | 접미사 | `_cnt`(원문 집계) 와 `_count`(우리 산출) 혼용 |
| ⑦ | 산술 검산 | Σ 축 배점 == `total_points` · Component 수 == 본문 주장 |
| ⑧ | 컬럼 참조 | `테이블.컬럼` 참조가 DDL 에 있는가 |
| ⑨ | `config` 예시 검산 | 부록 B `scoring.json` 예시 ↔ 본문 배점 표 |
| ⑩ | 영향표 반영 | STEP 125a 표의 각 행이 해당 장에 실제로 있는가 |
| ⑪ | 부록 E 동기화 | 부록 E 의 JSON 블록 ↔ 실제 파일 |
| ⑫ | 검증 코드 연속성 | `V*-N` 결번에 사유가 적혀 있는가 |
| ⑬ | 개정 이력 | 번호 연속 · 개정마다 근거가 있는가 |

### `tools/check_src.py` — 지시서 ↔ 소스 16종

| # | 검사 | 대상 |
|:--:|---|---|
| S1 | 디렉터리 | STEP 15 트리 |
| S2 · S3 | 구조체 · 함수 정의 | 정의서 |
| S4 | 테이블 DDL | STEP 28 |
| S5 | `config` 키 | V4-15 |
| S6 | 배점 검산 | 불변식 ⑤ |
| S7 | 매직 넘버 | V4-13 |
| S8 | 접미사 | STEP 4 |
| S9 | 금지 근거 | STEP 14 |
| S10 | 도메인 예외 | STEP 3 |
| S11 | 분석 계층 순수성 | STEP 2 |
| S12 | 축 파일 STEP 주석 | 7장 |
| S13 | 본문 `config` 예시 대조 | 부록 B |
| S14 | 상수 등록·성격 | V4-17 |
| S15 | 계층 의존 | STEP 15a |
| **S16** | **검증 코드 대조** — 지시서의 `V*-N` 이 소스에 있는가 | **6장** |
| **S17** | **검사 대상 대조** — 장 파일 수 == `CW_CHAPTERS` 길이 | **부록 E** |
| **S18** | **config 예시 유일성** — 같은 파일의 JSON 블록이 문서 전체에 1개 | **부록 B** |
| **S19** | **검증 코드 정규식 범위** — 지시서의 전 차수를 덮는가 | **6장** |
| **S20** | **유형 표기 필수** — 태그 없는 STEP 이 없는가 | **0장** |
| **S21** | **불변식 전건** — 0장 불변식 6개가 시험에 있는가 | **0장** |
| **S22** | **정적 검사** — `ruff --select F821,F811,B905` 가 0 인가 | **0장** |
| **S23** | **실행 환경** — 인터프리터가 Python 3.11 이상인가 | **0장** |
| **S24** | **시험 격리** — 시험이 운영 DB 를 읽지 않는가 | **0장** |
| **S25** | **형상 관리** — 커밋되지 않은 변경이 없는가 | **0장** |
| **S26** | **작업 기록** — 작업마다 `outputs/` 기록이 있는가 | **0장** |
| **S27** | **화면이 본체** — 기능마다 화면이 있는가 | **0장** |
| **S28** | **가이드 작업 규칙** — 정본 하나 · 폐기 표시 · 스크린샷 대조 | **0장** |
| **S29** | **정기 점검** — 작업·일일·주간(금 02:00) · 서로 점검 | **0장** |
| **S30** | **검사 정리** — 중복 · 죽은 검사 · 규격만 있는 검사 | **0장** |
| **S31** | **테스터** — 검사가 못 잡는 것을 찾는다 · 소스를 안 본다 | **0장** |
| **S32** | **규격 출처** — `[마스터]·[시안]·[원문]·[조사]·[판단]` | **0장** |
| **S33** | **요구사항 대장** — 마스터 지시를 한 곳에 · 상태 추적 | **0장** |
| **S34** | **추적표** — 요구→규격→소스→화면→검사→테스트→결함 한 줄 | **0장** |
| **S35** | **역할** — 자기 칸만 채운다 | **0장** |
| **S36** | **보안은 정식 서비스 전에** — 지금은 최소만 | **0장** |
| **S37** | **사는 사람을 위한 것** — 판매·대행 개념 금지 | **0장** |
| **S38** | **「완료」의 뜻** — 네 칸이 다 차야 ○ | **0장** |
| **S39** | **층** — 수집·저장·파싱·사전·판정·화면·검사·운영 | **0장** |

### ★ 검사 도구가 없으면 실패다 — 08-16

```
금지   도구가 없을 때 통과로 세는 것
      _ruff_ok() 가 「ruff 가 없으면 True」를 반환하고 있었다 (실측 08-16)
      B905 · F821 등 6종이 무검사인 채 「통과」로 집계됐다
근거   S22 를 만든 이유가 바로 그것이다 — 「훅에 없으면 아무도 안 돌린다」
      같은 파일 주석에 그렇게 적어 두고 코드가 그것을 어겼다
필수   도구가 없으면 실패다.  「설치하십시오」를 화면에 낸다
필수   「건너뜀」과 「통과」를 가른다.  건너뛴 것을 통과로 세지 않는다
검산   S22  — 도구 부재 시 실패를 내는가
```

```
CW_CHAPTERS   착수 선언 장.  미착수와 실패를 가른다
근거          장별로 만드는 동안 전건 실패가 뜨면 사람이 검사를 끈다 (V4-13)
자기 제외      check_spec · check_src · validate/v*_*.py
```

### ★ 정적 검사기를 돌린다 — 08-14

```
필수   ruff check --select F821,F811,B905,DTZ 를 pre-commit 에 건다
근거   실측 08-14.  F821 「미정의 이름」 6건이 있었다.
      web/views.py 의 ROLE_USER 3건은 가입 POST 가 그 줄에서 죽는다
      도구가 1초에 잡는 것을 사람이 못 봤다
필수   F821 · F811 · B905 는 fatal.  나머지는 참고
금지   noqa 로 F821 을 덮는 것.  이름이 없으면 실행하면 죽는다
검산   S22
```

```
★ zip(strict=) 를 강제한다 (B905)
근거   길이가 다르면 조용히 잘린다.  예외가 안 난다
      collect/runner.py 의 엔드포인트 zip 이 그렇다
```

### ★ 태그 없는 STEP 을 건너뛰지 않는다 — 08-14

```
문제   TYPE_LABELS 에 없는 태그는 continue 로 넘어간다
      205 STEP 중 126 개가 유형 표기 없이 통과했다 (실측 08-14)
      「유형 표기 STEP 72개 · 누락 0」이 나왔지만 133 개를 안 본 것이다
필수   전 STEP 이 아래 6종 중 하나를 단다.  태그가 없으면 실패다
      [판정] [규격] [수집]   정의서 8항목 필수
      [검증] [목록]          표 자체가 내용이다 — 항목 면제
      [설명]                 서술형 — 항목 면제 ★ 08-15 신설

★ [설명] 을 둔 이유
  「3티어 구조」처럼 계층 그림과 이유로 된 STEP 이 있다
  「원천」·「입력」·「출력」이 있을 자리가 아니다
  없는 것을 지어 붙이는 것이 「수를 손으로 적지 않는다」와 같은 위반이다
금지   [설명] 에 값 규칙을 쓰는 것.  규칙이 있으면 [규격] 이다
금지   8항목을 쓰기 싫어서 [설명] 을 다는 것
      판단 기준 — 이 STEP 이 코드의 무엇을 정하는가.  정하면 [규격] 이다
근거   태그가 없으면 정의서 8항목 검사가 안 걸린다.
      규격을 쓰면서 검산을 빠뜨려도 아무도 모른다
검산   S20
```

### ★ config 예시는 부록 B 한 곳에만 — 08-14

```
필수   같은 config 파일의 JSON 블록은 문서 전체에 1개다
필수   본문(장 파일)에는 키 표만 둔다
근거   web.json 예시가 본문과 부록 양쪽에 있었고 내용이 갈렸다
      검사가 두 블록을 보고 4건을 오탐했다 (개발측 실측 08-14)
금지   「본문에도 두면 읽기 편하다」.  갈리면 어느 쪽이 정본인지 알 수 없다
검산   S18
```

```
★ 검사기는 파일별로 읽는다.  합쳐 읽지 않는다
근거   합쳐 읽으면 절 경계를 정규식으로 잡아야 하고,
      「### config/web.json」이 앞 절에 붙는 사고가 났다 (실측 08-14)
필수   문서 하나를 읽고 그 안에서만 절을 가른다
금지   전 문서를 이어 붙인 뒤 정규식으로 자르는 것
       구분자를 넣어 해결하려 하지 않는다.  세 번 고쳐도 안 잡혔다
```

### ★ 검사가 보는 문서 — 08-14 확정

```
대상   docs/chapters/**/*.md      장별 파일 전부
금지   단일 통합본을 대상으로 두는 것
근거   통합본이 옛 판이면 검사가 옛 규격으로 판정한다
      실제로 「미착수 1건」이 그렇게 나왔다 — 소스에는 있는데 옛 본에 없었다
필수   경로를 코드에 박지 않는다.  config/checks.json 에 둔다
검산   S17  검사 대상 경로가 실재하고 장 수가 CW_CHAPTERS 와 맞는가
```

```json
"spec_glob": "docs/chapters/**/*.md",
"chapters":  [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14]
```

```
★ 기본값을 코드에 박지 않는다 — 08-14
  "0,1" 이 코드에 박혀 있어 선언 없이 돌면 미착수 166 이 나왔다 (실측)
  숫자가 커서 「결함 166건」으로 보였으나 「선언을 안 했다」는 뜻이었다
필수   config/checks.json 의 chapters 가 정본이다
필수   환경변수 없이 돌아야 한다.  검사를 돌리는 데 사전 준비가 필요하면 안 돈다
금지   기본값을 좁게 잡는 것.  「전부 미착수」가 정상 출력이 된다
★ 미착수 수가 100 을 넘으면 선언 누락을 먼저 의심한다
  실제 미착수가 세 자리면 그건 착수를 안 한 것이지 결함이 아니다

★ CW_CHAPTERS 누락도 사고다
  14 를 빠뜨려 구조체 4 · 함수 5 가 미착수로 잡혔다 (실측 08-14)
  전건 통과였는데 「9건 미착수」로 보였다
필수   장을 하나 끝내면 그 자리에서 CW_CHAPTERS 에 넣는다
필수   check_spec 이 장 파일 수와 CW_CHAPTERS 길이를 대조한다 (S17)
금지   「나중에 한꺼번에」.  그 사이 검사 결과를 못 믿는다
```

```
★ S16 의 한계
  이름이 소스 어딘가에 있으면 통과한다
  잡는 것은 「지시서에 있는데 소스에 아예 없다」다.  그것이 실제 사고였다
  「이름만 남고 알맹이가 빠진 것」은 이 검사로 못 잡는다.  시험이 잡는다
★ 검사 대상 범위
  V10-* 은 validate/ 에 있고, V4-14~18 은 check_* 안에 있다
  자기 제외를 넓게 잡으면 이것들이 검사 밖으로 나간다.  파일 단위로 좁게 연다
```

```
fatal   ①②③④⑤⑦⑧⑨⑩⑪ 전건
참고    유형별 필수 항목 중 [검증]·[목록] 은 검사하지 않는다
```

### 새 검사를 만들 때

```
「이 검사가 금지 조항 자체를 잡는가」   →  정적 검사는 문자열 상수만 본다
「정상 코드에서 걸리는가」             →  걸리면 규칙이 잘못된 것이다
```

**두 방향의 실패는 부록 A 머리에 있다.**

---

## E-2. `tests/fixtures/EXPECTED.json`

**표본 12건의 파싱 기대값. `assert` 에 그대로 쓴다.**

```
_core 접미사   변환 후 값.  시험이 변환 로직을 다시 구현하지 않게 한다
```

```json
{
 "inspection_clean.json": {
  "outers_len": 0,
  "ranks": {},
  "statusTypes": {},
  "외판교환_판수": 0,
  "골격": false,
  "usageChangeTypes": [
   {
    "code": "1",
    "title": "렌트"
   }
  ],
  "firstRegistrationDate": "20231215",
  "mileage": 61133,
  "firstRegistrationDate_core": "2023-12-15"
 },
 "inspection_frame.json": {
  "outers_len": 5,
  "ranks": {
   "RANK_ONE": 3,
   "RANK_B": 1,
   "RANK_TWO": 1
  },
  "statusTypes": {
   "교환(교체)": 5,
   "용접,절단": 1
  },
  "외판교환_판수": 4,
  "골격": true,
  "usageChangeTypes": [],
  "firstRegistrationDate": "20210615",
  "mileage": 109551,
  "firstRegistrationDate_core": "2021-06-15"
 },
 "inspection_outer_paint.json": {
  "outers_len": 1,
  "ranks": {
   "RANK_TWO": 1
  },
  "statusTypes": {
   "판금/용접": 1
  },
  "외판교환_판수": 0,
  "골격": false,
  "usageChangeTypes": [
   {
    "code": "1",
    "title": "렌트"
   }
  ],
  "firstRegistrationDate": "20210827",
  "mileage": 42120,
  "firstRegistrationDate_core": "2021-08-27"
 },
 "inspection_outer_swap.json": {
  "outers_len": 7,
  "ranks": {
   "RANK_ONE": 6,
   "RANK_TWO": 1
  },
  "statusTypes": {
   "교환(교체)": 5,
   "판금/용접": 2
  },
  "외판교환_판수": 5,
  "골격": false,
  "usageChangeTypes": [],
  "firstRegistrationDate": "20250818",
  "mileage": 17094,
  "firstRegistrationDate_core": "2025-08-18"
 },
 "inspection_weld.json": {
  "outers_len": 1,
  "ranks": {
   "RANK_TWO": 1
  },
  "statusTypes": {
   "판금/용접": 1,
   "용접,절단": 1
  },
  "외판교환_판수": 0,
  "골격": false,
  "usageChangeTypes": [],
  "firstRegistrationDate": "20230703",
  "mileage": 13880,
  "firstRegistrationDate_core": "2023-07-03"
 },
 "record_clean.json": {
  "carNo": "112거7801",
  "accidents_len": 0,
  "types": [],
  "type12_합": 0,
  "myAccidentCost": 0,
  "myAccidentCnt": 0,
  "otherAccidentCnt": 0
 },
 "record_with_accident.json": {
  "carNo": "29소2618",
  "accidents_len": 1,
  "types": [
   "3"
  ],
  "type12_합": 0,
  "myAccidentCost": 0,
  "myAccidentCnt": 0,
  "otherAccidentCnt": 1
 },
 "detail_ev_tesla.json": {
  "modelGroupName": "모델 Y",
  "originPrice": 5299,
  "displacement": 180,
  "fuelName": "전기",
  "warranty": {
   "bodyMonth": 48,
   "transmissionMonth": 96,
   "transmissionMileage": 192000
  },
  "extendWarranty": false,
  "deemedExtendWarranty": false,
  "options_choice_len": 0,
  "dealer_firm": "솔카"
 },
 "detail_gasoline_genesis.json": {
  "modelGroupName": "G80",
  "originPrice": 6258,
  "displacement": 2497,
  "fuelName": "가솔린",
  "warranty": {
   "bodyMonth": 60,
   "transmissionMonth": 60,
   "transmissionMileage": 100000
  },
  "extendWarranty": false,
  "deemedExtendWarranty": false,
  "options_choice_len": 0,
  "dealer_firm": null
 },
 "detail_hybrid_renault.json": {
  "modelGroupName": "그랑 콜레오스",
  "originPrice": 3881,
  "displacement": 1969,
  "fuelName": "가솔린",
  "warranty": {
   "bodyMonth": 36,
   "transmissionMonth": 60,
   "transmissionMileage": 100000
  },
  "extendWarranty": false,
  "deemedExtendWarranty": true,
  "options_choice_len": 1,
  "dealer_firm": "굿카대표[P]"
 },
 "detail_lpg_hyundai.json": {
  "modelGroupName": "그랜저",
  "originPrice": 4349,
  "displacement": 3470,
  "fuelName": "LPG(일반인 구입)",
  "warranty": {
   "bodyMonth": 36,
   "transmissionMonth": 60,
   "transmissionMileage": 100000
  },
  "extendWarranty": false,
  "deemedExtendWarranty": false,
  "options_choice_len": 5,
  "dealer_firm": "남덕모터스"
 },
 "catalog.json": {
  "len": 9,
  "first": {
   "optionCd": "1009",
   "optionName": "BOSE 서라운드 사운드 시스템(10 스피커) + 액티브 노이즈 캔슬레이션",
   "price": 129,
   "description": null
  }
 }
}
```

---

## E-3. `tests/fixtures/NOTES.json`

**각 표본이 무엇을 검증하는지. 표본을 늘릴 때 여기에도 한 줄 추가한다.**

```json
{
 "inspection_clean.json": "outers 0 (무사고) 인데 usageChangeTypes 에 렌트. 두 축이 독립임을 보여준다",
 "inspection_frame.json": "RANK_B 1건 = 골격 → E등급. 외판교환 4판이지만 골격이 우선",
 "inspection_outer_swap.json": "외판교환 5판 · 골격 없음 → 사고 20점 0점",
 "inspection_outer_paint.json": "판금/용접만 → 감점 없음. 교환이 아니다",
 "inspection_weld.json": "「용접,절단」+「판금/용접」 동시. 미정의 항목 (STEP 86)",
 "record_clean.json": "accidents 빈 배열. myAccidentCnt 0",
 "record_with_accident.json": "type 3 만 1건 → myAccidentCost 0 · otherAccidentCnt 1. type 3 제외 규칙의 직접 검산",
 "detail_ev_tesla.json": "displacement 180 — 전기차 쓰레기값. 배기량 분류 금지 (STEP 46)",
 "detail_gasoline_genesis.json": "displacement 2497 → G80_25T. 2단 확정 정상 사례",
 "detail_hybrid_renault.json": "★ modelGroupName 그랑 콜레오스인데 displacement 1969 · 가솔린 = 2.0 가솔린. KOLEOS_HEV 가 아니다",
 "detail_lpg_hyundai.json": "displacement 3470 · LPG(일반인 구입)",
 "catalog.json": "9개 옵션. optionCd 1009 = BOSE. 4자리 코드",
 "diagnosis.json": "encarDiagnosis == 0 인 매물의 진단. items 에 판정(resultCode 있음)과 소견(null)이 섞여 있다 — 소견을 부위로 세면 수가 틀린다 (STEP 21b)"
}
```

---

## E-4. 표본 원문 12건

**원문은 이 문서에 넣지 않는다.** 184KB 라 본문의 절반이 되고, JSON 이 마크다운 안에 있으면
`EXPECTED.json` 대조가 문자 단위로 어긋난다.

```
동봉   BJY_v2_실물표본.tar.gz  →  tests/fixtures/ 에 푼다
없으면  아래로 다시 뽑는다 (v1 DB 필요)
```

### 재생성 스크립트

```python
# tools/make_fixtures.py — v1 DB 에서 표본 12건을 다시 뽑는다
import sqlite3, json, os, collections

DB  = "car_monitor.db"          # v1 DB 경로
OUT = "tests/fixtures"
os.makedirs(OUT, exist_ok=True)
c = sqlite3.connect(DB)

# ① inspection 5종 — 손상 유형별로 하나씩
seen = collections.Counter()
for lid, b in c.execute("SELECT listing_id, body FROM raw_response WHERE endpoint='inspection'"):
    try: o = json.loads(b)
    except Exception: continue
    ranks, sts = set(), set()
    for x in (o.get("outers") or []):
        ranks |= set(x.get("attributes") or [])
        sts   |= {s.get("title") for s in (x.get("statusTypes") or [])}
    tag = ("clean"       if not ranks else
           "frame"       if ranks & {"RANK_A","RANK_B","RANK_C"} else
           "weld"        if "용접,절단" in sts else
           "outer_swap"  if "교환(교체)" in sts else
           "outer_paint" if sts else None)
    if tag and seen[tag] == 0:
        seen[tag] += 1
        json.dump(o, open(f"{OUT}/inspection_{tag}.json", "w"),
                  ensure_ascii=False, indent=1)

# ② detail 4종 — 연료·제조사별
for tk, tag in {"MODEL_Y":"ev_tesla", "G80_25T":"gasoline_genesis",
                "KOLEOS_HEV":"hybrid_renault", "GRANDEUR_LPG":"lpg_hyundai"}.items():
    r = c.execute("""SELECT r.body FROM raw_response r JOIN listings l USING(listing_id)
                     WHERE r.endpoint='vehicle' AND l.target_key=? LIMIT 1""", (tk,)).fetchone()
    if r:
        json.dump(json.loads(r[0]), open(f"{OUT}/detail_{tag}.json", "w"),
                  ensure_ascii=False, indent=1)

# ③ record 2종 — 사고 유무
done = set()
for b, in c.execute("SELECT body FROM raw_response WHERE endpoint='record'"):
    try: o = json.loads(b)
    except Exception: continue
    if not (isinstance(o, dict) and set(o) & {"carNo","openData"}): continue
    tag = "with_accident" if (o.get("accidents") or []) else "clean"
    if tag in done: continue
    done.add(tag)
    json.dump(o, open(f"{OUT}/record_{tag}.json", "w"), ensure_ascii=False, indent=1)

# ④ catalog 1종
r = c.execute("SELECT body FROM raw_response WHERE endpoint='catalog' LIMIT 1").fetchone()
json.dump(json.loads(r[0]), open(f"{OUT}/catalog.json", "w"), ensure_ascii=False, indent=1)
```

```
★ 실수집이 끝나면 v1 DB 가 아니라 새 DB 에서 다시 뽑는다
  표본은 「원문 구조가 예상과 달랐던 것」이다 (0장 STEP 6a)
  새 사이트를 붙이면 그 사이트 표본도 같은 방식으로 추가한다
```

---

**부록 E 종료.**

---

**부록 종료.**