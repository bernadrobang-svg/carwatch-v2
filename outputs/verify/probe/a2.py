import json, statistics as st
from collections import Counter
R=json.load(open('probe/census.json'))
def corr(xs,ys):
    n=len(xs); mx=sum(xs)/n; my=sum(ys)/n
    sx=(sum((x-mx)**2 for x in xs)/n)**.5; sy=(sum((y-my)**2 for y in ys)/n)**.5
    return sum((x-mx)*(y-my) for x,y in zip(xs,ys))/(n*sx*sy)
F=[r for r in R if len(r['bar'])==4 and r['price']]
print("막대4 완비",len(F),"/ 결손",len(R)-len(F))
miss=Counter()
for r in R:
    if len(r['bar'])<4:
        for k in ['차량','값','보증','취향']:
            if k not in r['bar']: miss[k]+=1
print("빠진 막대",miss.most_common())
print("\n=== 가격 상관 ===")
p=[r['price'] for r in F]
for k in ['값','차량','보증','취향']:
    print(f"가격↔{k}  r={corr(p,[r['bar'][k][0] for r in F]):+.3f}   만점 {F[0]['bar'][k][1]}  실측최고 {max(r['bar'][k][0] for r in F)}")
tot=[sum(r['bar'][k][0] for k in r['bar']) for r in F]
print(f"가격↔4축합 r={corr(p,tot):+.3f}")
G=[r for r in F if r['pct'] is not None]
print(f"가격↔비율%  r={corr([r['price'] for r in G],[r['pct'] for r in G]):+.3f}  ({len(G)}건)")
print("\n=== 가격대별 축 평균 ===")
bands=[(0,25e6),(25e6,30e6),(30e6,35e6),(35e6,45e6),(45e6,55e6),(55e6,9e9)]
print(f"{'가격대':>14} {'건수':>5} {'값/250':>8} {'차량/150':>9} {'보증/130':>9} {'취향/145':>9} {'비율%':>7}")
for lo,hi in bands:
    S=[r for r in F if lo<=r['price']<hi]
    if not S: continue
    pcs=[r['pct'] for r in S if r['pct'] is not None]
    print(f"{lo/1e4:>6.0f}~{hi/1e4 if hi<9e9 else 9999:<7.0f} {len(S):5d} "
          f"{st.mean(r['bar']['값'][0] for r in S):8.1f} {st.mean(r['bar']['차량'][0] for r in S):9.1f} "
          f"{st.mean(r['bar']['보증'][0] for r in S):9.1f} {st.mean(r['bar']['취향'][0] for r in S):9.1f} "
          f"{st.mean(pcs) if pcs else 0:7.1f}")
print("\n=== 분모 종류 ===")
print(Counter(r['den'] for r in R).most_common())
print("\n=== A등급 69건 가격분포 ===")
A=sorted([r['price'] for r in R if r['grade']=='A'])
print("최저",A[0]/1e4,"25%",A[len(A)//4]/1e4,"중앙",st.median(A)/1e4,"최고",A[-1]/1e4)
print("\n=== 예산 안 B 11건 ===")
for r in sorted([r for r in R if r['grade']=='B' and r['price']<=30000000], key=lambda x:x['price']):
    print(f"  {r['id']:5d} {r['price']/1e4:6.0f}만 월{(r['monthly'] or 0)/1e4:3.0f}만 {r['model']:14s} {r['year']} {r['km']:7d}km "
          f"값{r['bar'].get('값',(0,))[0]:6.1f} 차량{r['bar'].get('차량',(0,))[0]:6.1f} 보증{r['bar'].get('보증',(0,))[0]:6.1f} 취향{r['bar'].get('취향',(0,))[0]:6.1f} {r['pct']}%")
