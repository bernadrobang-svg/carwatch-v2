import json,sys,re
sys.path.insert(0,'probe'); from p0 import get
R=json.load(open('probe/census.json'))
N=[r for r in R if r['grade']=='NOT_RATED'][:5]
print("=== NOT_RATED 막대 값 ===")
for r in N: print(" ",r['id'],r['price']/1e4,"만",r['bar'],"pct",r['pct'])
print("\n=== 값 막대 없는 행의 원문 (id 7086) ===")
s,t,b=get("/listings?page=1")
# find a value-less row on any page: fetch detail instead
for i in (7086, 2101):
    s,t,d=get(f"/detail/{i}")
    m=re.search(r'값 — 이 가격이 맞나.*?</section>', d, re.S)
    txt=re.sub(r'<[^>]+>',' ',m.group(0)) if m else 'NOSEC'
    print(f"\n--- detail/{i} ②절 ---")
    print(' '.join(txt.split())[:600])
    m2=re.search(r'판정.*?</section>', d, re.S)
    bars=re.findall(r'title="(차량|값|보증|취향) ([\d.]+) / ([\d.]+)점"', d)
    print("  막대:",bars)
    m3=re.search(r'([\d.]+) / ([\d.]+) 점입니다', d)
    print("  총점:", m3.group(0) if m3 else None)
