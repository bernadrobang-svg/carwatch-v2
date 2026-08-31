# 리볼트 (revolt.kr) — 전기차 전용 인증중고차

```
version  SPEC-2026.09.02-r1082
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

```
★★★★ **이 문서의 건수는 ★ 규격이 아니다** — ★ 잰 날의 수다.  ★ 날마다 변한다
   ★ ★ 규격은 ★ **창구 주소 · 열쇠 · 칸 이름**이다.  ★ 그것만 못을 박는다
   ★ ★ ★ **개발측 수가 다르면 ★ 나중에 잰 것이 맞다** — ★ 불일치로 세지 마라
```

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

---

# ★★★★★ 09-01 마스터 확정 — ★ **보배를 빼고 리볼트를 넣는다.  ★ 최우선**

```
★★★ 마스터 — 「★ **보배를 빼고 여기 것 쓰자 ★ 지금 우선 작업으로.
   ★ 하고 빨리 수집하고 ★ 화면도 만들고 빨리**」
```

## ★ 전체를 쟀다 [실측 09-01]

| | |
|---|--:|
| ★ 매물 전체 | ★ **220건** (한 쪽 20건 × 11쪽) |
| 연료 | ★ **전기 212 · 수소 8** — ★ **전건 전기·수소** |
| 사고 | ★ **`complete_no_accident` 179 · `simple_exchange_no_accident` 41** — ★ **전건 무사고** |
| 브랜드 | **22** — ★ **해시가 헤이딜러와 똑같다** (볼보 `Jo6rOo` · BMW `0W5AWm` · 테슬라 `xozX5g`) |

```
★ 우리 대상이 여럿 있다 [표본] — ★ **폴스타2 · 폭스바겐 ID.4 · 테슬라 Model 3 · BMW i5 ·
   기아 EV6 · 현대 IONIQ 5 · KONA EV · 아우디 e-tron**
★ ★ 차종 이름은 ★ `car_info.brand_name` ＋ `car_info.model_name` ＋ `model_hash_id` 다
★★ ★ **몰아치면 500 이 난다** — ★ 한 번에 여러 건을 부르면 막힌다.  ★ **사이를 두어라**
```

## ★★★ 넣는 법 — ★ **헤이딜러 파서를 베낀다**

```
필수  ★ `parse/revolt/` 를 ★ **`parse/heydealer/` 에서 베껴** 만든다 — ★ 칸 이름이 같다
      `accident_repairs` · `carhistory.has_rent_use_record` · `owner_changed_count` ·
      `flooded_count`·`stolen_count`·`total_loss_count` · `accident_repairs_summary`
필수  ★ `new_car_price` → `value.origin` · ★ `car_number` → ★ **`plate_hash`**(짝이 바로 생긴다)
필수  ★ `manufacturer_warranty.items` 의 ★ 「N년 N개월 / N km 남음」을 ★ 그대로 읽는다
필수  ★ `f-table` 3a·3b(부위·수리 코드)는 ★ **헤이딜러 표를 그대로 쓴다** — ★ 같은 회사다
      ★ ★ 다만 ★ **표에 없는 코드가 나오면 미확인 0점 ＋ 나에게 올려라**
금지  ★ ★ `App-Os`·`App-Type`·`App-Version` 헤더 — ★ **500 이 난다**
금지  ★ 몰아쳐 부르는 것 — ★ **500 이 난다**.  ★ 사이를 둔다
```

## ★ 보배는 ★ **뺀다**

```
★ 마스터 확정 — 「★ 보배를 빼고 여기 것 쓰자」
★ ★ 까닭 (앞서 잰 것) — ★ 성능점검이 ★ **이미지**다 · ★ 사고 라벨이 ★ **31/223 건뿐**이고
   ★ ★ 값이 ★ **딜러가 쓴 자유 문장**이다 · ★ 「진짜 검증할 방법이 없다」(마스터 08-29)
필수  ★ 수집을 ★ **멈춘다**.  ★ 이미 받은 것은 ★ **지우지 않는다** (P3 · 화면에서 뺀다)
필수  ★ 사이트 갈래 표에서 ★ 보배를 빼고 ★ **리볼트를 「상품화·보증」에 넣는다**
```

---

# ★★★★★ 09-01 — ★ **차종 해시를 뽑았다** (마스터 지적)

```
★★★ 마스터 — 「★ **넌 리볼트 256건 중 6건만 대상이라는데 ★ 네가 매핑표를 뭘 준 거야?
   ★ 설마 KB 것을 준 거니?  ★ 리볼트도 헤이딜러처럼 차종이 해시값이라서 발라내야 하는데
   ★ 그걸 했니?**」
★ ★ ★ **안 했다.  ★ `site_query.revolt` 가 ★ 한 종도 없었다** — ★ 옳은 지적이다
```

## ★ 어디서 뽑나 — ★ **`/brands/` 안에 `models[]` 가 있다**

```
GET /customers/web/brands/   ★ 200 · 브랜드 22 · ★ 차종 합 93
  [{ "hash_id":"Jo6rOo", "name":"Volvo",
     "models":[{ "hash_id":"Z40wEp", "name":"XC40 Recharge" }, …] }, …]
★★★ ★ **거르개는 `?model_hash_id=` 다**
   ★ ★ ★ **`?model=` 은 안 걸린다** — ★ 전건(100건)이 그대로 온다.  ★ 내가 처음에 그렇게 세었다
   ★ ★ 번들에서 찾았다 — `{model_hash_id:n}:{brand_hash_id:e}`
```

## ★★ 우리 차종 아홉 — ★ **다 찾았다** [실측 09-01]

| 우리 차종 | 브랜드 | ★ `model_hash_id` | 리볼트 이름 | ★ 건수 |
|---|---|---|---|--:|
| `MODEL_Y` | Tesla `xozX5g` | ★ **`N49KGo`** ＋ **`4NQQ7p`** | Model Y ＋ ★ **Model Y Juniper** | 38 → 42 [날마다 다르다] |
| `ID4_EV` | Volkswagen `LZY3JW` | `eojn2o` | ID.4 | **4** |
| `IX3_EV` | BMW `0W5AWm` | `dpYgk3` | iX3 | **3** |
| `POLESTAR4_EV` | Polestar `RWlnAZ` | `ojxxB4` | Polestar 4 | **3** |
| `GV70_EV` | GENESIS `vgm7Do` | `Mo7j63` | Electrified GV70 | **2** |
| `XC40_EV` | Volvo `Jo6rOo` | `Z40wEp` | ★ **XC40 Recharge** | 0 |
| `C40_EV` | Volvo `Jo6rOo` | `N491G4` | ★ **C40 Recharge** | 0 |
| `ID5_EV` | Volkswagen `LZY3JW` | `oxmmrp` | ID.5 | 0 |
| `EV4_EV` | KIA `2oV0gK` | `oqk6k4` | EV4 | 0 |
| **합** | | | | ★ **50 / 220** |

```
★★ ★ **브랜드 해시가 헤이딜러와 똑같다** — 볼보 `Jo6rOo` · BMW `0W5AWm` · 테슬라 `xozX5g`
   ★ ★ 다만 ★ **폴스타는 다르다** — 리볼트 `RWlnAZ` ↔ 헤이딜러 계열과 견줘 봐야 한다
★ ★ ★ **차종은 있는데 매물이 0 인 것이 넷**이다 (XC40·C40 Recharge · ID.5 · EV4)
   ★ ★ **「리볼트가 안 판다」가 아니다** — ★ 지금 재고가 없는 것이다.  ★ 들어오면 걸린다
★★ ★ **모델 Y 는 해시가 둘이다** — ★ `Model Y` 와 ★ `Model Y Juniper`(신형).  ★ 둘 다 넣었다
```

## ★★★★ 09-01 정정 — ★ **29 가 아니라 50 이다**

```
★ 마스터 — 「★ **넌 리볼트 256건 중 6건만 대상이라는데**」
★ ★ **6 도 29 도 아니다.  ★ 다시 세니 ★ 50 이다** [실측 09-01 · 쪽을 끝까지 넘겼다]
★ ★ ★ 내가 ★ **한 쪽(20건)만 보고 세었다** — ★ 모델 Y 가 ★ 17 → ★ **38** 이었다
```

| 차종 | 건수 |
|---|--:|
| ★ **`MODEL_Y`** | ★ **42** (★ 09-02 재측 · 09-01 엔 38 이었다) |
| `ID4_EV` | 4 |
| `IX3_EV` · `POLESTAR4_EV` | 3 · 3 |
| `GV70_EV` | 2 |
| `XC40_EV` · `C40_EV` · `ID5_EV` · `EV4_EV` | ★ **0** |
| **합** | ★ **54 / 270** (★ 09-02 재측) |

```
★ ★ **220건 중 50건이 우리 대상**이다 — ★ 23% 다
★ ★ ★ 나머지 170건은 ★ **아이오닉5 · 코나 · EV6 · 레이 EV · 봉고Ⅲ EV** 등이다
★★ ★ **넷은 차종 해시가 있는데 매물이 0** 이다 — ★ 「안 판다」가 아니라 ★ **지금 재고가 없다**
   ★ ★ 들어오면 ★ 열쇠가 이미 있어 ★ **바로 걸린다**
★ ★ ★ **쪽을 끝까지 넘겨 세라** — ★ 한 쪽은 20건이 상한이다 (★ 내가 그것에 걸렸다)
```

## ★★ 09-02 재측 — ★ **수는 움직인다.  ★ 규격에 못을 박지 않는다**

```
★ 개발측 — 「★ 리볼트 54건 중 ★ MODEL_Y 가 42 다.  ★ 규격은 38 이라 했다 —
   ★ 나흘 사이에 늘었다.  ★ 규격 표를 고칠지는 ★ 가이드 몫이라 안 건드렸다」
★ ★ **다시 쟀다.  ★ 42 가 맞다** — `N49KGo` **17** ＋ `4NQQ7p`(Juniper) **25**
★ ★ ★ **개발측이 옳다.  ★ 안 건드린 것도 옳다** (규격은 가이드 몫이다)

필수  ★ 규격의 건수는 ★ **잰 날을 함께 적는다** — 「42건 [09-02]」
필수  ★ ★ **건수가 다르다고 검사를 실패시키지 마라** — ★ 매물은 날마다 는다
      ★ ★ 검사는 ★ **열쇠가 맞는가**를 본다.  ★ 몇 건인가는 ★ 그날의 수다
★ ★ 곧 ★ **개발측이 낸 수가 규격보다 크면 ★ 그것이 맞다** — ★ 나중에 잰 것이다
```
