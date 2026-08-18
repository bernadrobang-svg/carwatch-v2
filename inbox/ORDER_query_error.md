# ★★★ 개정 391 — 쿼리 탐색 · 오류 분류가 틀렸다

**마스터 실측 08-19 07:15 — `/admin/query`**

```
아직 저장할 수 없습니다
SQL 을 해석할 수 없다: no such column: created_at.
데이터를 고칠 일이 있으면 개발 요청으로 낸다 (STEP 137)
화면의 안내대로 절차를 마친 뒤 다시 누른다
```

`SPEC-2026.08.19-r393`

---

# 1. 원인

| # | 파일 · 줄 | 무슨 일 |
|:--:|---|---|
| 1 | `store/adminops.py:479-481` | `EXPLAIN` 컴파일 실패를 `REJECT_COMPILE` 로 되돌린다 |
| 2 | `store/adminops.py:518` | 그것을 **`PolicyError`** 로 던진다 — 쓰기 시도 · PII 조회와 **같은 예외** |
| 3 | `web/context.py:168-171` | `PolicyError` → 제목 「아직 저장할 수 없습니다」 · 안내 「화면의 안내대로 절차를 마친 뒤 다시 누른다」 |

```
★ 마스터는 「조회」를 누르셨는데 화면이 「저장」이라 한다
★ 컬럼 이름 하나 틀린 것에 「개발 요청으로 낸다 (STEP 137)」이 붙는다
★ 마칠 절차가 없는데 「절차를 마친 뒤」라 한다
  ★ errors.py CarWatchError.__init__ 주석이 바로 이것을 경고한다 —
    「없으면 화면이 일반 문구를 낸다.  마칠 절차가 없으면 사용자가 갇힌다 (실측 08-15)」
★ query_log.rejected_reason 에 오타와 정책 위반이 같은 자리에 쌓인다.  거부 통계가 오염된다
```

**컴파일 실패는 정책 위반이 아니다. 사용자 오타다. 갈라야 한다.**

---

# 2. 고칠 것

| | 무엇 | 출처 |
|:--:|---|---|
| 필수 | `REJECT_COMPILE` 은 `ValidationError` 로 던진다 | `[판단]` 예외 5종 정의상 「검증 단계 위반」이다 |
| 필수 | 제목을 「**쿼리를 고치십시오**」로 | `[판단]` 「저장」이 아니다 |
| 필수 | `action` 에 **그 표의 실제 컬럼 목록**을 넣는다 | `[판단]` 고칠 재료를 준다 (개정 367) |
| 필수 | 「개발 요청으로 낸다 (STEP 137)」은 **쓰기 · PII 거부에만** | `[판단]` |
| 필수 | `query_log` 에 `reject_kind` 를 나눈다 — `compile` · `policy` | `[판단]` |

## 2-1. action 문구

```
쿼리를 고치십시오
  no such column: created_at
  raw_response 의 컬럼 — id · run_id · site · endpoint · request_url
                        · http_code · status · body · origin · fetched_at
```

```
필수   sqlite_master 에서 그 표의 컬럼을 읽어 그대로 낸다
필수   ★ 표 이름을 못 찾으면 「어느 표를 보려 하셨습니까」와 표 목록을 낸다
근거   ★ 마스터는 「무엇을 하라는 말이지」를 이미 지적하셨다 (개정 367).
       고치라 하면서 무엇으로 고치는지를 안 주면 같은 잘못이다
금지   컬럼 이름을 짐작해 「~를 쓰시려던 것 같습니다」라 하는 것
```

## 2-2. 예외 갈래

| 거부 사유 | 예외 | 제목 | STEP 137 문구 |
|---|---|---|:--:|
| 컴파일 실패 (오타 · 없는 컬럼/표) | `ValidationError` | 쿼리를 고치십시오 | ✗ |
| SELECT 가 아님 · 여러 문장 | `ValidationError` | 쿼리를 고치십시오 | ✗ |
| 쓰기 연산 | `PolicyError` | 이 쿼리는 막혀 있습니다 | ○ |
| PII 표 조회 | `PolicyError` | 이 쿼리는 막혀 있습니다 | ○ |

```
검산   V10-33  컴파일 실패가 PolicyError 로 가는가 (가면 실패)
       V10-34  거부 응답의 action 이 비어 있는가 (비면 실패)
       V10-35  query_log.reject_kind 가 compile · policy 로 갈리는가
```

---

# 3. 함께 볼 것

```
★ created_at 은 표마다 있고 없다.  실측 —
  있다   core_pii · auth_session · dev_request · watch_* · admin 계정
  없다   raw_response · raw_facet · result_score · result_axis
★ 쿼리 예시(QUERY_EXAMPLES) 넷은 created_at 을 쓰지 않는다.
  마스터가 직접 치신 것이다 — 화면이 컬럼을 안 보여 주니 칠 수밖에 없다
필수  화면에 표별 컬럼을 펼쳐 둔다.  db_tables 는 이미 넘어가고 있다
검산  V10-36  표를 누르면 컬럼이 보이는가
```
