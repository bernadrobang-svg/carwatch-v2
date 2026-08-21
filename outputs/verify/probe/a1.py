import json, statistics as st
R=json.load(open('probe/census.json'))
print("행",len(R))
def cnt(f): return sum(1 for r in R if f(r))
print("파싱 결측 — price",cnt(lambda r:r['price'] is None),"grade",cnt(lambda r:not r['grade']),
      "monthly",cnt(lambda r:r['monthly'] is None),"막대4",cnt(lambda r:len(r['bar'])<4),
      "pt",cnt(lambda r:r['pt'] is None))
from collections import Counter
print("\n등급 분포",Counter(r['grade'] for r in R).most_common())
print("차종",Counter(r['model'] for r in R).most_common())
print("\n=== 예산 ===")
b30=[r for r in R if r['price'] and r['price']<=30000000]
m40=[r for r in R if r['monthly'] and r['monthly']<=400000]
print("3,000만 이하",len(b30),"| 월40만 이하",len(m40))
print("교집합", len({r['id'] for r in b30}&{r['id'] for r in m40}))
print("3천 이하 등급",Counter(r['grade'] for r in b30).most_common())
print("월40 이하 등급",Counter(r['grade'] for r in m40).most_common())
print("월40 최고가", max(r['price'] for r in m40)/1e4,"만")
print("\n=== 첫 화면 50건 (기본 추천순) ===")
f=R[:50]
print("최저가",min(r['price'] for r in f)/1e4,"만 · 최고",max(r['price'] for r in f)/1e4,"만")
print("3천 이하", sum(1 for r in f if r['price']<=30000000))
print("월40 이하", sum(1 for r in f if r['monthly'] and r['monthly']<=400000))
print("등급",Counter(r['grade'] for r in f).most_common())
print("\n=== 등급 vs 가격 ===")
for g in ['A','B','C','D','E','F','G','NO_GRADE','NOT_RATED']:
    v=[r['price'] for r in R if r['grade']==g and r['price']]
    if v: print(f"{g:10s} {len(v):5d}건  중앙 {st.median(v)/1e4:7.0f}만  최저 {min(v)/1e4:6.0f}  최고 {max(v)/1e4:6.0f}")
