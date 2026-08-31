# 리볼트 (revolt.kr) — 전기차 전용 인증중고차

```
version  SPEC-2026.09.01-r1029
follows  ★ 정본 — 가이드 문서
sources  실측 09-01
checks   S46-200
```

★★★ **마스터께서 주소를 주셨다 09-01** — `https://www.revolt.kr/cars/JlVNPOlE`

---

# 1. ★ 무엇을 파는 곳인가

```
★ 사이트 소개 글 (인용) — 「★ **오직, 전기차를 위한 기술 인증 중고차**」 · 「★ 전기차 기술 점검(창구 — `GET /cars/{hash}/inspection_records/` · 2장)을 통해
   ★ **배터리 정상 ・ 무사고 차만 선별해서 판매합니다**」
★ ★ 만든 곳이 ★ **PRND** 다 — ★ **헤이딜러와 같은 회사**다
   ★ ★ ★ 그래서 ★ **창구 꼴이 헤이딜러와 거의 같다** (아래)
★★ ★ 마스터께서 찾으시는 것과 ★ **정확히 겹친다** — ★ 전기차 · 무사고 · 인증
```

---

# 2. ★★★★ 창구 [실측 09-01 · 표본 `JlVNPOlE`]

```
바탕  ★ **`https://api.revolt.kr/customers/web`**
      ★ (번들 `assets/index-*.js` 의 `baseURL = new URL("/customers/web/", "https://api.revolt.kr")`)
헤더  ★ **User-Agent · Referer · Accept 만** — ★ 토큰이 필요 없다
      ★ ★ ★ **`App-Os`·`App-Type`·`App-Version` 을 넣으면 ★ 500 이 난다** — ★ 넣지 마라
```

| 창구 | 상태 | 무엇이 오나 |
|---|:--:|---|
| `/cars/{hash}/` | ★ **200 · 43,047B** | 상세 전부 |
| `GET /cars/{hash}/carhistory/` | 200 | 보험 내력 — ★ 이 주소가 창구다 |
| `GET /cars/{hash}/inspection_records/` | 200 | 성능점검 부위별 (창구 = 이 주소다) |
| ★ `/cars/{hash}/ev_info/` | 200 | ★ **배터리·주행거리** |
| `/cars/?page=N` | ★ **200 · 20건** | 목록 |
| 〃 `/brands/` · `/models/{id}/grades/` | — | (아직 안 잼) |

---

# 3. ★★★ 우리 축과 이어 보면 — ★ **거의 다 준다**

| 우리 축 | 리볼트 칸 | 표본 값 |
|---|---|---|
| ★ `value.origin` 신차가 | ★ **`new_car_price`** | **4229** |
| ★ `state.accident` 사고 | ★ **`accident_repairs_summary`** | `complete_no_accident` |
| ★ `state.frame`·`outer` | ★ **`inspection_records.accident_repairs`** | `[]` (무사고) |
| `history.use` 용도 | `has_rent/business/public_use_record` | — |
| `history.owner` 소유자 | `owner_changed_count` | — |
| `state.special` 특수 | `flooded_count`·`stolen_count`·`total_loss_count` | — |
| `warranty.maker` | `manufacturer_warranty.items` | 「차체/일반 부품 **2년 6개월 / 60,390km 남음**」 |
| ★ 짝 | ★ **`car_number`** | ★ **「69모6840」** — ★ **차량번호를 그대로 준다** |
| ★ **EV 전용** | `battery_capacity` **72.0** · `battery_manufacturer` ★ **「BYD」** · `range` **433** · `efficiency` **5.0** · `zero_hundred` **8.1** · `wheel_drive` 「2WD」 | |

```
★★★★ ★ **헤이딜러와 칸 이름이 똑같다** (`accident_repairs`·`carhistory`·`has_rent_use_record`)
   ★ ★ ★ 곧 ★ **헤이딜러 파서를 거의 그대로 쓸 수 있다** — ★ 새로 짓지 않아도 된다
★★ ★ **차량번호를 준다** — ★ 짝(`plate_hash`)이 바로 생긴다
★ ★ ★ **배터리 제조사·용량을 준다** — ★ 우리 축에 아직 없는 것이다 (마스터께서 정하실 자리)
```

---

# 4. ★ 마스터께 여쭐 것

```
① ★ **대상에 넣을까** — ★ 전기차 인증중고차이고 ★ 마스터 조건과 겹친다 (★ 창구는 2장에 다 적었다 — `GET /cars/{hash}/inspection_records/` 등)
   ★ ★ 헤이딜러 파서를 거의 그대로 써서 ★ **품이 적다**
② ★ 넣는다면 ★ **차종을 어떻게 고를까** — ★ `/brands/`·`/models/{id}/grades/` 를 내가 잰다
③ ★ **배터리(용량·제조사·SOH)를 점수로 볼까** — ★ 지금 우리 축에 없다
   ★ ★ 리본카 `initAqiCheckList` 에도 SOH 자리가 있었다 (개정 968)
```
