# 챕터 · 디렉터리 매핑

```
version  SPEC-2026.08.25-r727
follows  `docs/INDEX.md`
sources  실측 08-22
checks   S46-38 · S46-39
```


**소스 구조는 1장 STEP 15 가 정본이다. 이 문서는 「어느 챕터를 보면 되나」를 잇는다.**

```
★ 08-14 정정 — 실물 소스에 맞췄다
  이전 판이 src/ 아래 모노레포를 상정했으나 그런 구조가 아니다
```

---

## 매핑

| 챕터 문서 | 소스 | 무엇 |
|---|---|---|
| `00-standard` | — | 개발 표준. 처음 한 번 |
| `01-arch` | `contracts.py` · `errors.py` | 계약 · 예외 · 계층 |
| `10-collect` | `collect/` · `adapters/` | 수집 · 요청 · 봉투 |
| `11-store` | `store/` · `sql/ddl/` | 스키마 · 저장 · PII |
| `12-dict` | `store/dict.py` · `config/dictionaries/` | 사전 · 열거값 |
| `13-pipeline` | `collect/runner.py` · `run.py` | 실행 순서 · 재처리 |
| `20-verify` | `validate/` | 검증 V1~V11 |
| `30-score` | `analyze/` · `score/` | 판정 · 배점 · 등급 |
| `31-registry` | `store/registry.py` · `tools/` | 필드 등록부 |
| `40-report` | `report/exports/` | 리포트 · 파일 출력 |
| `41-view` | `report/screens/` | 화면 데이터 |
| `42-watch` | `store/watch.py` | 추적 · 알림 |
| `50-multisite` | `adapters/` | 사이트 어댑터 |
| `60-admin` | `store/adminops.py` · `web/` | 관리자 |
| `61-web` | `web/` | 라우팅 · 템플릿 |

---

## 계층 — `LAYER_ALLOW` 가 정본

```
errors        ←  없음
contracts     ←  errors
adapters      ←  contracts · errors
store         ←  contracts · errors
parse         ←  contracts · errors · store
analyze       ←  contracts · errors                    ★ store 를 못 부른다
score         ←  contracts · errors · analyze          ★ store 를 못 부른다
report        ←  contracts · errors · store · analyze · score · parse
web           ←  contracts · errors · store · score · report
collect       ←  위 전부 + validate · tools            ★ 오케스트레이터
validate      ←  전부 (읽기만)
tools         ←  전부 (독립 실행)
```

```
★ analyze · score 는 store 를 못 부른다
근거   판정은 순수 함수다.  조회는 호출자가 하고 결과를 인자로 넘긴다
검산   V4-22  역방향 · 순환 import 없음

★ collect 가 위를 부르는 것은 역방향이 아니다
근거   오케스트레이터다.  파이프라인 순서를 아는 유일한 층이다
       그래서 LAYER_ALLOW 에 명시로 열려 있다

★ validate · tools 는 순환 대상이 아니다
근거   전부 읽는 것이 그 층의 일이다
```

---

## 작업 순서 — 의존이 없는 것부터

```
1차   errors · contracts → store → adapters · collect
2차   parse → store/dict
3차   analyze → score
4차   report → web
5차   validate (각 단계마다 그 단계 것만 붙인다)
```

```
★ validate 를 마지막에 몰아 붙이지 않는다
  V1·V2 는 collect·store 와 함께.  V3 는 analyze 와 함께
근거   나중에 몰면 33개가 비어 있는 사고가 다시 난다
```

---

## 간섭 방지

```
1  한 작업은 한 디렉터리만 건드린다        규칙
2  LAYER_ALLOW                          ★ 강제 (V4-22)
3  V4-23  모듈 최상위 부작용 금지
```

```
★ 2·3 이 강제다.  규칙만으로는 안 지켜진다
근거   v1 에서 역방향 의존 21건이 나왔다
```
