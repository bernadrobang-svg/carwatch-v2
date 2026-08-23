# 엔카 robots · 407 — ★ 실측 규격

`SPEC-2026.08.23-r563` · 2026-08-23 · **가이드가 직접 실측했다 (원칙 4)**

```
★★ 마스터 지시 08-23 — 「엔카 407 도 다시 봐봐.  ★ 우회나 다른 방법이 있을 거야」
★ 재 보았다.  ★ 407 은 ★ 뚫을 것이 아니었다 — ★ 두드리지 말았어야 할 문이다
★ 그리고 ★ 다른 방법은 ★ 있다.  ★ robots 가 ★ 스스로 열어 둔 문이 셋이다
★ 왜 이 파일인가 — ★ `ENCAR_API.md` 는 ★ `tools/probe_encar.py` 가 만든다.  ★ 손으로 안 적는다
```

---

# 1. ★★ 호스트마다 robots 가 다르다 — ★ 넷을 전부 받았다

| 호스트 | robots | 우리에게 |
|---|---|---|
| `api.encar.com` | ★★★ **`User-agent: * / Disallow: /`** (26B) | ★ **전면 금지** |
| `car.encar.com` | `Allow: /` · ★ **`Disallow: /v1/readside/`** · `Disallow: /api` · `GPTBot Disallow: /` | ★ **상세 경로를 콕 집어 금지** |
| `www.encar.com` | `Allow: /` · 금지 36줄 (`/dc/dc_cardetailview.do` · `/cars/` · `/catalog/` …) · ★ **Sitemap 둘** | 목록 화면은 허용 |
| `m.encar.com` | `Allow: /` · 금지는 ★ **`/co/` · `/my/` 둘뿐** | ★ **거의 다 열려 있다** |

```
필수  ★ robots 는 ★ 호스트마다 받는다.  ★ 한 곳을 보고 다른 곳을 짐작하지 않는다
      ★ 같은 회사인데 ★ 넷이 전부 다르다 — ★ 하나는 전면 금지, 하나는 거의 전면 허용
```

---

# 2. ★★ 407 은 누가 냈나 — 실측

```
GET https://api.encar.com/search/car/list/premium?count=true&q=(And.Hidden.N.)
  → ★ 407 · 본문 ★ 0B · ★ `via: … .cloudfront.net (CloudFront)` · ★ `server` 헤더 없음
GET https://api.encar.com/v1/readside/vehicle/40000000
  → ★ 404 (★ 407 이 아니다) · ★ 같은 CloudFront

★ 즉 ★ IP 차단이 아니다 — ★ `/search/` 경로에만 걸린 ★ 문지기다
★ 다나와·벤츠의 503 과는 ★ 다르다 —
  저쪽은 ★ 본문이 `upstream connect error` 이고 ★ 우리 조사창 프록시가 냈다 (오판 #63)
  ★ 이쪽은 ★ CloudFront 가 냈다.  ★ 엔카 쪽이다
```

```
★★★ ★ 그러나 ★ 그 호스트는 ★ robots 가 ★ 전면 금지다.  ★ 뚫는 것은 ★ 우회다
필수  ★ 407 을 ★ 「막혔다」로 적지 말고 ★ 「금지된 문이다」로 적는다
금지  ★ 407 을 ★ 우회하려는 ★ 모든 시도 (기준서 3-3 · 명령서 금지 13)
★ 마스터께서 「우회나 다른 방법」이라 하셨다 —
  ★ 우회는 ★ 안 만든다.  ★ 다른 방법은 ★ 3장에 있다
```

---

# 3. ★★★ 다른 방법 — ★ robots 가 열어 둔 문 셋

| | 문 | 실측 08-23 |
|:--:|---|---|
| ⓐ | `https://www.encar.com/sitemap-car.xml` ★ **robots 가 스스로 가리킨다** | 200 · 518KB · **`<loc>` 1,166** |
| ⓑ | `https://car.encar.com/sitemap.xml` ★ **〃** | 200 · 359KB · **`<loc>` 2,008** |
| ⓒ | `https://m.encar.com/` ★ 금지는 `/co/`·`/my/` 둘뿐 | 200 · 183KB · **Next.js `__NEXT_DATA__`** |

```
★ ⓐⓑ 의 `<loc>` 는 ★ 검색 조건이 박힌 ★ 목록 주소다 —
  car.encar.com/list/car?page=1&search={"type":"car",
    "action":"(And.Hidden.N._.CarType.A._.Service.EncarDiagnosis.)","sort":"MobileModifiedDate"}
  ★ 우리가 쓰던 ★ `q=(And.Hidden.N.)` 문법과 ★ 같은 꼴이다
  ★ 차종별 주소도 있다 — `car.encar.com/list/car/현대`
★ ⓒ 는 ★ `__NEXT_DATA__` 에 ★ `vehicleId` 37회 · `price` 29회 · buildId 가 있다
★★ ★ 리본카가 정확히 이 꼴이었다 — ★ robots 가 사이트맵을 가리키고 있었다 (개정 552)
★★★ ★ 이것은 ★ 우회가 아니다.  ★ 사이트가 ★ 「여기로 오라」고 ★ 적어 둔 문이다
```

```
★ 아직 안 잰 것 — ★ 지어내지 않는다
  · ⓒ 의 `_next/data/{buildId}/…` 가 ★ 목록 JSON 을 주는가
  · ⓐⓑ 의 목록 주소가 ★ 브라우저 없이 매물을 주는가 (JS 가 그릴 수 있다)
  · 상세를 ★ 허용된 경로로 받을 수 있는가 — ★ `car.encar.com` 이 `/v1/readside/` 를 금지했다
```

---

# 3a. ★★★ B 검토 — ★ 재 보았다.  ★ 지금은 성립하지 않는다

```
★★ 마스터 지시 08-23 — 「B 로 하기 위한 검토를 해봐」
★ 3장에서 ★ 「열린 문 셋」이라 적은 것을 ★ 하나씩 두드렸다.  ★ 결과를 그대로 적는다
```

## ① 문마다 ★ 무엇이 나오는가 (실측)

| 문 | robots | 결과 | 매물이 나오나 |
|---|:--:|---|---|
| `car.encar.com/list/car?search={…}` | 허용 | 200 · **1,664B** | ★ **껍데기** — `__NEXT_DATA__` 없음 |
| `car.encar.com/sitemap.xml` 의 `<loc>` | 허용 | 200 · 2,008 loc | ★ **검색조건 주소뿐** · 그 주소가 위 껍데기 |
| `www.encar.com/sitemap-car.xml` 의 `<loc>` | 허용 | 200 · 1,166 loc | 〃 |
| `m.encar.com/` 홈 `__NEXT_DATA__` | 허용 | 200 · **매물 15건** | ★ **칸이 셋뿐** — 아래 ② |
| `m.encar.com/_next/data/{buildId}/…` | 허용 | ★ **502** | ✘ |
| `www.encar.com/dc/dc_cardetailview.do?carid=` | ★ **금지** | 200 · 2,515B | ★ 껍데기 · **carid 등장 0회** |

## ② ★ 홈에서 나오는 매물 15건이 가진 것

```json
{"vehicleId": 42526253, "ordering": 1, "lowerPriceRate": 39}
```

```
★ 칸이 ★ 셋뿐이다 — ★ 우리 26축 중 ★ 하나도 못 채운다
★ 값·차량·보증·취향 ★ 넷 다 비고 ★ 등급을 매길 수 없다
```

## ③ ★ 상세 — ★ 이름 다섯을 두드렸다 (모양 ⑲ 대로)

```
진짜 매물번호를 ★ 허용된 문(m.encar 홈)에서 뽑아 썼다 — `41359860`
  car.encar.com/cars/detail/{id}       → 404
  car.encar.com/detail/car/{id}        → 404
  car.encar.com/cars/{id}              → 404
  m.encar.com/cars/detail/{id}         → 404
  m.encar.com/car/{id}                 → 404
  car.encar.com/list/car/detail/{id}   → 200 ★ 1,664B (★ 같은 껍데기)
★ 「못 찾았다」다.  ★ 「없다」가 아니다 — ★ 브라우저로 열면 주소가 보일 수 있다
```

## ④ ★★★ 판정

```
★ robots 가 허용한 문은 ★ 전부 ★ 사람이 보는 화면이다
★ 그 화면의 데이터는 ★ JS 가 ★ `api.encar.com` 을 불러서 채운다 —
  ★ 즉 ★ 허용된 문으로 들어가도 ★ 데이터 원천은 ★ 같은 금지 호스트다
★★ ★ 그러므로 ★ B 는 ★ 「다른 데이터원으로 옮기는 것」이 ★ 아니다
   ★ 「브라우저로 화면을 렌더링해서 긁는 것」이 된다 —
   ★ 훨씬 무겁고 · ★ 부르는 곳은 ★ 그대로다
★ 상세는 ★ 다섯을 두드려 ★ 전부 404 다.  ★ 27축을 채울 길을 ★ 못 찾았다

★ 결론 — ★ **B 는 지금 성립하지 않는다.**  ★ 재기 전에 「대안」이라 부른 것이 성급했다 (오판 #65)
★ 남은 길 — ★ 브라우저로 열어 ★ 화면이 부르는 주소를 보는 것.  ★ 아직 안 했다
   ★ 다만 ★ 그 주소가 `api.encar.com` 이면 ★ 같은 자리로 돌아온다
```

---

# 4. ★★★ 급한 것 — ★ 지금 우리가 ★ 금지 호스트를 쓰고 있다

```
★ `config/endpoints.json` 의 ★ encar `base_url` = ★ `https://api.encar.com`
★ 그 호스트 robots 는 ★ `Disallow: /` 다
★ 상세 경로 `/v1/readside/` 는 ★ `car.encar.com` robots 가 ★ 한 줄로 따로 금지한다
★ 지금 붙어 있는 ★ 엔카 매물 ★ 8,478건이 ★ 그 문으로 들어왔다
★ 그리고 ★ 우리 기준서 3-3 이 ★ 「금지된 경로는 두드리지 않는다」를 ★ 필수로 적어 두었다
```

```
★★★ ★ 이것은 ★ 가이드가 정할 일이 아니다 — ★ 마스터께 올린다 (`04_질의`)
★ 가이드가 한 것   ★ 사실을 재서 적고 · ★ 대안 셋(3장)을 찾아 두었다
★ 가이드가 안 한 것 ★ 수집을 멈추는 것 · ★ `base_url` 을 바꾸는 것 · ★ 우회를 만드는 것
                  ★ 셋 다 ★ 마스터가 정하신다
```

---

# 5. 검산

```
S46-4 ★ 신설 — ★ `config/endpoints.json` 의 ★ 모든 `base_url` 에 대해
      ★ 그 호스트 robots 를 받아 ★ 우리가 쓰는 경로가 ★ 금지되어 있으면 ★ 실패
      ★ 지금 돌리면 ★ 엔카에서 ★ 실패가 난다 — ★ 그것이 이 검산의 첫 일이다
★ 만들면 ★ 일부러 깨서 ★ 잡는 것을 본다 (원칙 6)
```
