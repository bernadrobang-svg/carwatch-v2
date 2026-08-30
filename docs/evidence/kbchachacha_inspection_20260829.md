# KB차차차 — 성능점검 상세 [실측 2026-08-29]

```
version  SPEC-2026.08.29-r957
checks   S46-161
```

★ **결론 — ★ KB 는 성능점검을 ★ 준다.**  ★ 앞서 「경로를 못 찾았다」로 적은 것은 ★ 틀렸다 (오판 204)

## ① 언제
2026-08-29 (가이드 회차 r909)

## ② 어느 주소
```
목록    GET  https://www.kbchachacha.com/public/search/car/list/dt/ajax?...
상세    GET  https://www.kbchachacha.com/public/car/detail.kbc?carSeq={id}
★ 점검  상세 HTML 안의  <a ... data-link-url="{주소}">
        갈래 셋 (표본 10건) —
          http://autocafe.co.kr/ASSO/CarCheck_Form.asp?OnCarNo={번호}      8건
          https://ai.carinfo.co.kr/view/carinfo?check_id={id}              2건
          https://ck.carmodoo.com/carCheck/carmodooPrint.do?print=…&checkNum=…  2건
```

## ③ 무슨 응답
```
상세      200 · ok       (표본 10건 중 링크가 있는 것 ★ 9건 · 없는 것 1건)
점검 문서 200 · ok       (autocafe 갈래를 두드림)
```

## ④ 몇 바이트
```
점검 문서 첫 건       58,016B
표본 5건 크기        49,766 · 49,519 · 49,522 · 49,695 · 49,791B
★★ ★ **크기가 다 다르다** — ★ 매물마다 값이 갈린다 (안내문이 아니다)

들어 있는 낱말 (첫 건) — 판금 8 · 교환 5 · 용접 4 · 골격 3 · 외판 5 · 누유 24
```

## ⑤ 표본 몇 건
```
링크 유무   10건
문서 열기   5건 (다 200)
```

## ★ 아직 못 잰 것
```
★ `ai.carinfo` · `ck.carmodoo` 갈래는 ★ **안 두드렸다** — ★ autocafe 만 열어 봤다
★ ★ 판마다의 등급을 ★ 어떤 꼴로 주는지는 ★ **아직 안 갈랐다** — ★ 낱말만 세었다 (오판 192)
```
