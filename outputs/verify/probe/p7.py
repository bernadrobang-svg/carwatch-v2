import sys,re,html

if __name__ == "__main__":
    sys.path.insert(0,'probe'); from p0 import get
    for path in ["/notready","/market"]:
        s,t,b=get(path)
        t2=re.sub(r'<script.*?</script>','',b,flags=re.S); t2=re.sub(r'<style.*?</style>','',t2,flags=re.S)
        t2=re.sub(r'<[^>]+>','\n',t2); t2=html.unescape(t2)
        L=[' '.join(x.split()) for x in t2.split('\n')]; L=[x for x in L if x]
        print(f"########## {path}  HTTP{s}  {t:.1f}s")
        print('\n'.join(L[8:80]))
        print()

