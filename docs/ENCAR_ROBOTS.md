# 엔카 robots · 407 — ★ 실측 규격

`SPEC-2026.08.23-r560` · 2026-08-23 · **가이드가 직접 실측했다 (원칙 4)**

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
