import json, statistics as st
from collections import Counter

if __name__ == "__main__":
    R=json.load(open('probe/census.json'))
    print("=== 추천순(rank) 이 무엇으로 정렬되는가 — 앞 60건 ===")
    for r in R[:12]:
        print(f" {r['rank']:3d}위 {r['grade']:9s} pct={r['pct']} pt={r['pt']} {r['price']/1e4:6.0f}만 시세차{r['gap']}% {r['model']}")
    pct=[r['pct'] for r in R[:200] if r['pct'] is not None]
    print("앞200건 pct 단조 감소?", all(pct[i]>=pct[i+1] for i in range(len(pct)-1)), "구간", pct[0], pct[-1])
    allp=[r['pct'] for r in R if r['pct'] is not None]
    print("전체 pct 단조 감소?", all(allp[i]>=allp[i+1] for i in range(len(allp)-1)))
    # where does it break
    brk=[i for i in range(len(allp)-1) if allp[i]<allp[i+1]]
    print("역전 지점 수", len(brk), brk[:5])
    print("\n=== 값 막대 없는 507건 ===")
    M=[r for r in R if '값' not in r['bar']]
    print("등급",Counter(r['grade'] for r in M).most_common())
    print("분모675 인 것",sum(1 for r in M if r['den']==675.0),"/ 분모없음",sum(1 for r in M if r['den'] is None))
    print("시세 칸 있는 것",sum(1 for r in M if r['mkt']),"/ 시세차 있는 것",sum(1 for r in M if r['gap'] is not None))
    print("가격 중앙",st.median([r['price'] for r in M])/1e4,"만")
    print("예시 5")
    for r in M[:5]: print("  ",r['id'],r['grade'],r['price']/1e4,"만 mkt",r['mkt'],"gap",r['gap'],"den",r['den'],"pct",r['pct'],"막대",list(r['bar']))
    print("\n=== 미채점 72건 ===")
    N=[r for r in R if r['grade']=='NOT_RATED']
    print("막대",Counter(len(r['bar']) for r in N),"den",Counter(r['den'] for r in N))
    print("\n=== NO_GRADE 72건 ===")
    NG=[r for r in R if r['grade']=='NO_GRADE']
    print("막대",Counter(len(r['bar']) for r in NG),"den",Counter(r['den'] for r in NG),"pct",Counter(r['pct'] for r in NG).most_common(3))

