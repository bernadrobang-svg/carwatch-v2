import sys,re,html

if __name__ == "__main__":
    sys.path.insert(0,'probe'); from p0 import get
    for i in (7781,1261):
        s,t,d=get(f"/detail/{i}")
        m=re.search(r'24축 전부(.*?)</details>', d, re.S)
        seg=m.group(1) if m else d
        txt=re.sub(r'<[^>]+>','\n',seg); txt=html.unescape(txt)
        L=[' '.join(x.split()) for x in txt.split('\n')]; L=[x for x in L if x]
        print(f"===== detail/{i} 24축 원문 =====")
        print(' / '.join(L[:60]))
        print()

