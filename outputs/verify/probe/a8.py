import sys,re
sys.path.insert(0,'probe'); from p0 import get
GRP={'차량':['압류·저당','자차 미가입','소유자 변경','용도','사고','소모품','골격','진정성','누유','외판','보험 수리비','특수 사고'],
     '값':['신차가 대비','시세 대비','주행'],
     '보증':['일반 보증','보증','사이트 보증'],
     '취향':['옵션','트림','색상','HUD','지정 옵션','선루프']}
for i in (7781,1261,5836,7162):
    s,t,d=get(f"/detail/{i}")
    ax=dict((n,(float(a),float(b))) for n,a,b in re.findall(r'>([^<>]{2,12})</[a-z]+>\s*<b[^>]*>([\d.]+)\s*/\s*([\d.]+)</b>', d))
    if not ax:
        ax=dict((n.strip(),(float(a),float(b))) for n,a,b in re.findall(r'<span[^>]*>([^<]+)</span>\s*<b[^>]*>([\d.]+)\s*/\s*([\d.]+)</b>', d))
    bars=dict((k,float(a)) for k,a,b in re.findall(r'title="(차량|값|보증|취향) ([\d.]+) / ([\d.]+)점"', d))
    m=re.search(r'([\d.]+) / 675 점입니다', d)
    print(f"\n=== detail/{i} · 배지 {m.group(1) if m else '?'} · 막대합 {sum(bars.values()):.1f} · 축 {len(ax)}개 ===")
    for g,names in GRP.items():
        sub=sum(ax[n][0] for n in names if n in ax)
        cap=sum(ax[n][1] for n in names if n in ax)
        print(f"  {g:4s} 막대 {bars.get(g,0):6.1f} | 축합 {sub:6.1f} / {cap:5.1f}  {'✔' if abs(sub-bars.get(g,0))<0.05 else '✗'}")
    miss=[n for n in ax if not any(n in v for v in GRP.values())]
    print("  묶음 밖 축:", {n:ax[n] for n in miss})
