import sys,re; sys.path.insert(0,'probe'); from p0 import get
for i in (7086,2101,8427):
    s,t,d=get(f"/detail/{i}")
    hs=[' '.join(re.sub(r'<[^>]+>','',m.group(2)).split()) for m in re.finditer(r'<(h1|h3)[^>]*>(.*?)</\1>',d,re.S)]
    sm=re.findall(r'<summary[^>]*>(.*?)</summary>',d,re.S)
    print(f"detail/{i}  HTTP{s}  절 {len(hs)}개 + summary {len(sm)}")
    for h in hs: print("   ",h)
