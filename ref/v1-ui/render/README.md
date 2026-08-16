# CarWatch 화면 — 실제 렌더 결과

브라우저로 열어보십시오. 배치·색·간격이 그대로 보입니다.

```
why.html          ★ 판정 근거.  이 도구의 존재 이유
listings.html     매물 목록
recommend.html    추천 후보
dashboard.html    현황
compare.html      비교
```

## 주의

- **파일로 연 것**이라 링크·버튼은 동작하지 않습니다
- 데이터는 시연용 30건입니다 (B 7 · C 9 · D 14)
- 실제 화면은 `python -m web.app` 후 `http://127.0.0.1:5001`

## 먼저 볼 것

`why.html` 을 여십시오.

축별 점수와 근거가 어떻게 나오는지가 이 도구의 핵심입니다.
v2 는 `result_axis` 의 `source`·`prio` 로 이보다 정확해집니다.
