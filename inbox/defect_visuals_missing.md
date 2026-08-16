# ★★ 시안의 시각 표현이 거의 전부 빠졌다

**2026-08-16 · 마스터 지적 — 시안과 실물이 다르다**

---

# 1. 마스터 지적이 맞습니다

```
시세   시안   세로 막대 히스토그램 (.hist · .histx)
       실물   표 하나
```

**제가 검사에서 「절 이름」만 봤습니다. 「어떻게 보이는가」를 안 봤습니다.**

---

# 2. 전수 대조 결과

| 시안 클래스 | 화면 | 무엇 | 실물 |
|---|---|---|:--:|
| `hist` · `histx` | market | 가격 분포 세로 막대 | **없음** |
| `quad` | dealers | 딜러 4분면 | **없음** |
| `spark` · `sparkx` | watch | 관심 가격 추이 선 | **없음** |
| `pbar` | recommend | 후보 점수 막대 | **없음** |
| `thumb-none` | listings | 사진 자리 | **없음** |
| `savebar` | admin_config · registry · scoring | 저장 바 | **없음** |
| `edbar` | admin_query | 편집 바 | **없음** |

**실물 CSS 에 있는 시각 요소는 `.bar` 하나뿐입니다.**

---

# 3. ★ 왜 제 검사가 못 잡았나

```
check_screens   시안 ↔ 템플릿 짝 · 절 이름 · 렌더 여부
                → 「가격 분포」 절이 있으면 통과
                → 그것이 표인지 그래프인지는 안 봄
```

**「절이 있다」와 「시안대로 보인다」는 다릅니다.**

```
필수   시안의 클래스가 실물 CSS 에 있는가를 본다
       시안에서 .hist 를 쓰면 실물에도 .hist 가 있어야 한다
필수   시안의 구조를 본다 — 표인가 그래프인가
검산   V11-59  시안이 쓰는 클래스가 실물 CSS 에 있는가
```

---

# 4. 무엇을 만들어야 하나

## `/market` — 가격 분포 히스토그램

```css
.hist   { display:flex; align-items:flex-end; gap:3px; height:130px }
.hist .b { flex:1; background:var(--line2); border-radius:2px 2px 0 0;
           min-height:3px; cursor:pointer }
.hist .b.mine { background:var(--amber) }
.hist .b .n   { position:absolute; top:-16px; ... }
.histx  { display:flex; gap:3px; font-family:var(--mono); font-size:10px }
```

**시안에 CSS 가 그대로 있습니다. 옮기면 됩니다.**

```
★ 막대를 누르면 그 구간 매물로 — 이미 filter_url 이 있습니다
★ 「내 매물이 있는 구간」을 amber 로 (.b.mine)
```

## 나머지

```
dealers    quad   딜러 4분면 (정직도 × 표본)
watch      spark  가격 추이 선
recommend  pbar   후보 점수 막대
listings   thumb  사진 (개정 274)
admin      savebar  저장 바 — 변경이 있을 때만 뜨는 것
```

---

# 5. 지시

```
1  ref/screens/ 의 시안 23개를 열어 CSS 를 전부 뽑아라
   시안에 있는데 실물 app.css 에 없는 클래스를 목록으로

2  그 목록을 나에게 보고해라
   ★ 한꺼번에 다 만들지 마라.  무엇이 빠졌는지 먼저 세어야 한다

3  V11-59 를 구현해라
   시안이 쓰는 클래스가 실물 CSS 에 있는가
   ★ 이것이 있으면 다음에 화면을 만들 때 또 빠뜨리지 않는다

4  그 다음 순서대로 만들어라
   급한 순서는 내가 정하겠다
```

---

# 6. 지금 밀린 것 — 다시

```
1  .chips 스타일         ★★ 목록을 못 씁니다
2  사진 (개정 274)       ★★ 차가 안 보입니다
3  쪽 넘김 + 전체 건수
4  ★ 시안 시각 요소 목록 보고    ← 이번
5  메뉴 이름 4개
6  후보 1건 · V4-20 · 응답 시간
```

**1·2·3 을 먼저 하고, 4 는 목록만 보고하십시오.**
**만드는 것은 그 뒤에 순서를 정합니다.**
