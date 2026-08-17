# K카 API — 1차 조사

**`ORDER_multisite_kcar` §4-① · `ASK_kcar_feasible` §1 (가이드 지시 08-17).**
`docs/ENCAR_API.md` 와 같은 형식입니다. 규칙 2 예외 — 이 파일은 개발측이 만듭니다.

조사일 2026-08-17 · 표본 `EC61393706` · 서버(43.201.16.78)에서 직접

---

## 1. ★ 마스터 물음에 대한 답 — 「그래서 수집 가능해 아니야」

```
② 브라우저 수집이 필요합니다  ← 가 아닙니다
① 됩니다 — 서버에서             ← 에 가깝습니다.  다만 조건이 있습니다
```

**정확히는 이렇습니다.**

```
★ 서버 IP 가 막혀 있지 않습니다.  엔카와 결정적으로 다릅니다
  엔카   /search/car/list/mobile  →  407 (서울 IP 차단)  → 브라우저 수집이 필요했다
  K카    목록 · 상세 둘 다        →  200               → 서버에서 부를 수 있다

★ 다만 값이 HTML 에 없습니다.  XHR 경로를 더 찾아야 합니다
```

---

## 2. 실측 — 세 가지 (가이드 §1 그대로)

| 확인 | 주소 | 결과 |
|---|---|---|
| ① 목록 | `https://m.kcar.com/bc/search/CarList` | **200** · 2,163,861바이트 |
| ② 상세 | `https://m.kcar.com/bc/detail/carInfoDtl?i_sCarCd=EC61393706` | **200** · 2,200,494바이트 |
| ② 상세(PC) | `https://www.kcar.com/bc/detail/carInfoDtl?i_sCarCd=…` | **200** · 2,162,950바이트 |
| ③ 형식 | — | **HTML** (Nuxt SSR) |

```
★ 403 도 407 도 아닙니다.  서버에서 그냥 열립니다
★ 2.2MB 인데 그 대부분이 CSS 와 JS 입니다.  매물 값은 그 안에 없습니다
```

---

## 3. ★ 값이 어디 있나 — HTML 이 아니라 XHR

```js
window.__NUXT__ = (function(a,b,c,d){ return {
  layout:"LayoutCarDtl",
  state:{ page:{ carInfo:b, searchInfo:b, … } },   // ← b 는 null 이다
  serverRendered:d, routePath:"/bc/detail/carInfoDtl"
}}(void 0, null, "", true));
```

```
★ carInfo 가 null 입니다.  껍데기만 SSR 이고 값은 JS 가 나중에 채웁니다
★ 엔카는 상세가 JSON 하나였습니다.  K카는 화면이 조각조각 부릅니다
```

### 번들에서 뽑은 것

`m.kcar.com` 상세 화면이 부르는 번들 **9개** (2.7MB 짜리 하나 포함).

```
API 호스트
  marketm-api.kcar.com/api/v1     C2C(개인거래) — axios 기본 baseURL
  api.kcar.com/api/v1             공통
  m.kcar.com/bc/…                 화면과 같은 호스트의 상대 경로

실제 호출 예 (번들 원문)
  $AxiosBuilder.params({i_sCarCd: carCd}).build().get("/bc/car-insp/photo/cm")
  $axios.get("/bc/car-elan-path?i_sCarCd=" + route.query.i_sCarCd)
  $AsyncAxiosBuilder.params(searchCondition).build().get("/bc/car-info-detail-of-ng")
```

### 엔카 4종에 대응할 만한 것 (경로 이름 기준 · 아직 미검증)

| 엔카 | K카 후보 |
|---|---|
| 상세 | `/bc/car-info-detail-of-ng` · `/bc/detail/popup/CarBasInfo` |
| 성능점검 | `/bc/detail/popup/CarInsp` · `CarInspContent` · `/bc/car-insp/photo/cm` |
| 보험이력 | `/bc/detail/insu` · `/bc/detail/popup/InsuHistSmry` · `InsuHistInfoDtl` |
| 진단 | `/bc/detail/popup/DgnosSmry` · `DgnosDtl` · `DgnosDtlBas` |
| 옵션 | `/bc/car-option` |
| 주행거리 | `/bc/detail/popup/MilgSmry` |
| 소유이력 | `/bc/detail/hist/list` · `/bc/detail/gov/bas` |

```
★ /bc/car-info-detail-of-ng?i_sCarCd=… 는 404 였습니다.
  params 가 i_sCarCd 가 아니라 searchCondition 입니다 (번들 원문 확인)
★ 나머지는 아직 안 눌러 봤습니다 — 다음 차례
```

---

## 4. ★ 「우수등급」을 무엇으로 아는가 (개정 306 `site_grade_rule`)

**마스터 지시 — 「K카는 등록된 것 자체가 우수등급」**

```
따라서   config/sites.json  kcar.site_grade_rule = {"all_of": {}}
        조건이 비면 「등록된 것 자체」다 — 이미 그렇게 넣어 뒀습니다
★ 확인할 것 — K카 안에도 「진단」 팝업이 따로 있습니다 (DgnosSmry).
  등급이 갈리면 규칙을 그때 좁힙니다.  지금은 마스터 지시대로 둡니다
```

---

## 5. ★ 크로스사이트 — 같은 차를 가릴 수 있는가

```
아직 모릅니다.  상세 XHR 을 못 열어 차대번호·차량번호를 못 봤습니다
★ 없으면 「같은 차」를 못 가립니다.  그것도 결과입니다 (지시서 §5)
```

---

## 6. 다음에 할 것

```
1  /bc/detail/popup/* 를 서버에서 눌러 200/JSON 인지 본다
   ★ Referer 와 i_sCarCd 를 함께 보낸다
2  차종을 어떻게 고르는가 — 엔카의 q= 에 해당하는 것
   /api/v1/ds/getModelListCount · getGrdListCount 가 실마리다
3  차대번호·차량번호가 오는지 (크로스사이트)
4  그 뒤 adapters/kcar.py
```

---

## 7. 이 조사에서 확실한 것 · 아닌 것

```
확실   서버 IP 가 막히지 않았다 — 엔카와 다르다.  브라우저 수집이 「필요」하지 않다
확실   값은 HTML 에 없다.  XHR 을 따라가야 한다
확실   K카 우수등급 규칙은 「등록됨」이다 (마스터 지시)
아직   어느 XHR 이 매물 값을 주는지
아직   차대번호가 오는지 — 크로스사이트가 되는지
```
