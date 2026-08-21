import sys,re,json
sys.path.insert(0,'probe'); from p0 import get
R=json.load(open('probe/census.json'))
tgt=[r for r in R if r['id'] in (1261,5836,7162,7781)]
for r in tgt: print("census",r['id'],"pt",r['pt'],"막대",{k:v[0] for k,v in r['bar'].items()},"합",round(sum(v[0] for v in r['bar'].values()),1))
print()
for i in (1261,5836,7162,7781):
    s,t,d=get(f"/detail/{i}")
    bars=re.findall(r'title="(차량|값|보증|취향) ([\d.]+) / ([\d.]+)점"', d)
    m=re.search(r'([\d.]+) / ([\d.]+) 점입니다', d)
    ax=re.findall(r'<b[^>]*>([\d.]+)\s*/\s*([\d.]+)</b>', d)
    tot=sum(float(a) for a,b in ax)
    print(f"detail/{i}: 막대 {[(k,a) for k,a,b in bars]} 합 {sum(float(a) for k,a,b in bars):.1f} | 배지 {m.group(0) if m else None} | 24축합 {tot:.1f} ({len(ax)}축)")
